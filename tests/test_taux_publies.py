"""Tests de l'inscription des taux au catalogue et dans les fiches (T101, ADR-0278, ADR-0279).

L'inscription est éprouvée sur une copie du catalogue livré, avec un rapport construit à la main
qui porte de vraies règles ; la rubrique des fiches, sur une copie des fiches.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from test_banc import REGLES, RESULTATS, doc_de

from banc import fiches, inscription, sortie
from banc.corpus import Partie
from banc.evaluation import mesurer
from banc.inscription import Inscription, InscriptionRefusee
from banc.mesures import Taux
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes

pytestmark = pytest.mark.exigence("NF-09")

LIVRE = inscription.CATALOGUE


@pytest.fixture
def copie(tmp_path: Path) -> Path:
    dossier = tmp_path / "catalogue"
    shutil.copytree(LIVRE, dossier)
    return dossier


def _empreinte(dossier: Path) -> str:
    return catalogues.charger(manifestes.decouvrir(), dossier).version.empreinte


def _regle(identifiant: str, categorie: str, taux: Taux) -> dict[str, Any]:
    return {"identifiant": identifiant, "categorie": categorie, "faux_positifs": taux.vers_dict()}


def _rapport(empreinte: str, *regles: dict[str, Any], **champs: Any) -> dict[str, Any]:
    return {
        "publiable": True,
        "date": "2026-11-27T01:02:03Z",
        "corpus": {"nom": "reference", "version": "1.0.0"},
        "versions": {"catalogue": {"empreinte": empreinte, "fourni_par_utilisateur": False}},
        "regles": list(regles),
    } | champs


def _regles(dossier: Path, module: str) -> dict[str, dict[str, Any]]:
    texte = (dossier / "regles" / f"{module}.toml").read_text(encoding="utf-8")
    return {r["identifiant"]: r for r in tomllib.loads(texte)["regle"]}


# Inscriptions tirées d'un rapport


def test_inscriptions_des_indices_mesures(copie: Path) -> None:
    rapport = _rapport(
        _empreinte(copie),
        _regle("R-C2PA-004", "indice", Taux(0, 400)),
        _regle("R-C2PA-005", "indice", Taux(1, 100)),
        _regle("R-C2PA-006", "indice", Taux(0, 0)),  # sans effectif : pas d'évaluation
        _regle("R-C2PA-001", "preuve", Taux(0, 400)),  # une preuve n'a pas de niveau
    )
    fort, faible = inscription.inscriptions(rapport, _empreinte(copie))
    assert (fort.identifiant, fort.niveau, fort.effectif) == ("R-C2PA-004", "fort", 400)
    assert (fort.corpus, fort.date, fort.taux) == ("reference-1.0.0", date(2026, 11, 27), 0.0)
    assert fort.borne == Taux(0, 400).borne_superieure
    assert (faible.identifiant, faible.niveau, faible.taux) == ("R-C2PA-005", "faible", 0.01)


@pytest.mark.parametrize(
    ("champs", "attendu"),
    [
        pytest.param({"publiable": False}, "rapport non publiable", id="non-publiable"),
        pytest.param(
            {"versions": {"catalogue": {"empreinte": "0" * 64, "fourni_par_utilisateur": False}}},
            "autre catalogue",
            id="autre-empreinte",
        ),
        pytest.param(
            {"versions": {"catalogue": {"empreinte": "E", "fourni_par_utilisateur": True}}},
            "autre catalogue",
            id="fourni",
        ),
    ],
)
def test_inscriptions_refusees(champs: dict[str, Any], attendu: str) -> None:
    with pytest.raises(InscriptionRefusee, match=attendu):
        inscription.inscriptions(_rapport("E", **champs), "E")


# Écriture au catalogue


def _inscription(identifiant: str, borne: float, taux: float = 0.0) -> Inscription:
    return Inscription(
        identifiant,
        taux=taux,
        effectif=400,
        borne=borne,
        corpus="reference-1.0.0",
        date=date(2026, 11, 27),
    )


def test_inscrire(copie: Path) -> None:
    avant = _regles(copie, "c2pa")
    texte_avant = (copie / "regles" / "c2pa.toml").read_text(encoding="utf-8")
    modifies = inscription.inscrire(
        [
            _inscription("R-C2PA-004", 0.009),
            _inscription("R-C2PA-006", 0.04, taux=0.01),  # règle sans sous-table
            _inscription("R-DOUBLEJPEG-001", 0.2, taux=0.1),  # règle à sous-tables
        ],
        copie,
    )
    assert modifies == ["regles/c2pa.toml", "regles/doublejpeg.toml"]
    apres = _regles(copie, "c2pa")
    assert apres["R-C2PA-004"]["niveau"] == "fort"
    assert apres["R-C2PA-006"]["niveau"] == "modere"
    assert int(apres["R-C2PA-004"]["version"]) == int(avant["R-C2PA-004"]["version"]) + 1
    assert apres["R-C2PA-004"]["evaluation"] == {
        "taux_faux_positifs": 0.0,
        "effectif": 400,
        "borne_superieure": 0.009,
        "corpus": "reference-1.0.0",
        "date": "2026-11-27",
    }
    # Les autres règles et le reste du fichier ne changent pas.
    assert apres["R-C2PA-005"] == avant["R-C2PA-005"]
    texte = (copie / "regles" / "c2pa.toml").read_text(encoding="utf-8")
    assert texte.startswith(texte_avant.split("[[regle]]", 1)[0])
    assert texte.count("\n\n[[regle]]") == texte_avant.count("\n\n[[regle]]")
    assert texte.endswith("\n")
    assert not texte.endswith("\n\n")
    double = _regles(copie, "doublejpeg")["R-DOUBLEJPEG-001"]
    assert (double["niveau"], double["evaluation"]["taux_faux_positifs"]) == ("faible", 0.1)
    assert "calibrage" in double
    assert "condition" in double
    evaluees = {i for i, r in avant.items() if "evaluation" in r} | {"R-C2PA-004", "R-C2PA-006"}
    # Le catalogue modifié reste valide ; une seconde inscription remplace la première.
    inscription.inscrire([_inscription("R-C2PA-004", 0.03, taux=0.02)], copie)
    regle = _regles(copie, "c2pa")["R-C2PA-004"]
    assert (regle["niveau"], regle["evaluation"]["borne_superieure"]) == ("modere", 0.03)
    assert int(regle["version"]) == int(avant["R-C2PA-004"]["version"]) + 2
    assert texte.count("[regle.evaluation]") == len(evaluees)
    texte = (copie / "regles" / "c2pa.toml").read_text(encoding="utf-8")
    assert texte.count("[regle.evaluation]") == len(evaluees)
    assert "\n\n\n" not in texte


def test_inscription_refusee_ne_change_rien(copie: Path) -> None:
    avant = {f.name: f.read_bytes() for f in (copie / "regles").iterdir()}
    with pytest.raises(InscriptionRefusee, match="règles absentes du catalogue : R-ABSENT-001"):
        inscription.inscrire(
            [_inscription("R-C2PA-004", 0.009), _inscription("R-ABSENT-001", 0.009)], copie
        )
    assert {f.name: f.read_bytes() for f in (copie / "regles").iterdir()} == avant


def test_regle_sans_version_ni_niveau(copie: Path) -> None:
    fichier = copie / "regles" / "c2pa.toml"
    texte = fichier.read_text(encoding="utf-8")
    debut = texte.index('identifiant = "R-C2PA-004"')
    fin = texte.index("[[regle]]", debut)
    bloc = texte[debut:fin]
    sans_niveau = re.sub(r'(?m)^niveau = "[a-z]+"\n', "", bloc)
    fichier.write_text(texte.replace(bloc, sans_niveau), encoding="utf-8")
    with pytest.raises(InscriptionRefusee, match="clé « niveau » absente"):
        inscription.inscrire([_inscription("R-C2PA-004", 0.009)], copie)
    sans_version = "\n".join(ligne for ligne in bloc.split("\n") if not ligne.startswith("version"))
    fichier.write_text(texte.replace(bloc, sans_version), encoding="utf-8")
    with pytest.raises(InscriptionRefusee, match="R-C2PA-004 : version absente"):
        inscription.inscrire([_inscription("R-C2PA-004", 0.009)], copie)


def test_commande_inscription(
    copie: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rapport = tmp_path / "evaluation.json"
    contenu = _rapport(
        _empreinte(copie),
        _regle("R-C2PA-004", "indice", Taux(0, 400)),
        _regle("R-C2PA-005", "indice", Taux(0, 100)),
        _regle("R-C2PA-006", "indice", Taux(9, 100)),
    )
    rapport.write_text(json.dumps(contenu), encoding="utf-8")
    assert inscription.main([str(rapport), "--catalogue", str(copie)]) == 0
    assert capsys.readouterr().out == (
        "3 indices évalués ; 1 au niveau « fort », 1 au niveau « modéré », les autres « faible »\n"
    )
    # Le catalogue a changé : le même rapport ne peut pas être inscrit deux fois.
    assert inscription.main([str(rapport), "--catalogue", str(copie)]) == 2
    assert "rapport écrit avec un autre catalogue" in capsys.readouterr().err
    assert inscription.main([str(tmp_path / "absent.json"), "--catalogue", str(copie)]) == 2
    assert capsys.readouterr().err.startswith("inscription : ")


def test_niveau_absent_avant_les_sous_tables(copie: Path) -> None:
    fichier = copie / "regles" / "doublejpeg.toml"
    texte = fichier.read_text(encoding="utf-8")
    fichier.write_text(texte.replace('niveau = "faible"\n', "", 1), encoding="utf-8")
    with pytest.raises(InscriptionRefusee, match="clé « niveau » absente"):
        inscription.inscrire([_inscription("R-DOUBLEJPEG-001", 0.2)], copie)


def test_module_lance_par_python_m(tmp_path: Path) -> None:
    fini = subprocess.run(
        [sys.executable, "-m", "banc.inscription", str(tmp_path / "absent.json")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).resolve().parent.parent,
        env=os.environ | {"PYTHONUTF8": "1"},
        check=False,
    )
    assert fini.returncode == 2
    assert fini.stderr.startswith("inscription : ")


def test_commande_inscription_sur_le_catalogue_des_sources(
    monkeypatch: pytest.MonkeyPatch, copie: Path, tmp_path: Path
) -> None:
    monkeypatch.setattr(inscription, "CATALOGUE", copie)
    rapport = tmp_path / "evaluation.json"
    contenu = _rapport(_empreinte(copie), _regle("R-C2PA-004", "indice", Taux(0, 400)))
    rapport.write_text(json.dumps(contenu), encoding="utf-8")
    assert inscription.main([str(rapport)]) == 0
    assert _regles(copie, "c2pa")["R-C2PA-004"]["niveau"] == "fort"


# Rubrique « Taux d'erreur » des fiches


def _doc_exif() -> dict[str, Any]:
    """Rapport du banc dont l'unique technique, « alpha », est renommée en « exif »."""
    doc = doc_de(mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], ()))
    texte = json.dumps(doc).replace('"alpha"', '"exif"').replace("R-ALPHA", "R-EXIF")
    renomme: dict[str, Any] = json.loads(texte)
    return renomme


def test_bloc_des_taux() -> None:
    doc = _doc_exif()
    bloc = fiches.bloc_des_taux("exif", doc, "../rapport.md")
    lignes = bloc.split("\n")
    assert (lignes[0], lignes[-1]) == (fiches.DEBUT, fiches.FIN)
    assert "corpus test 2.0 ([rapport](../rapport.md)) : module `exif` 0.1.0" in bloc
    assert "| Authentiques | 5 | 1 | 1/4 : 25,0 % [4,6 % ; 69,9 %] |" in bloc
    assert "Aucune règle de preuve ou d'indice" in bloc
    regles = doc_de(mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES))
    avec = fiches.bloc_des_taux("alpha", regles, "r.md")
    assert "| R-ALPHA-001 v1 | indice | origine_ia | 1/3 : 33,3 %" in avec
    assert "| R-ALPHA-004" not in avec  # information neutre : pas de taux
    assert "| R-ALPHA-003 v1 | preuve | retouche | 0/3 : 0,0 % [0,0 % ; 56,1 %] | — | — |" in avec


def test_taux_ecrits_dans_les_fiches(tmp_path: Path) -> None:
    source = tmp_path / "techniques"
    shutil.copytree(fiches.SOURCE, source)
    rapport = tmp_path / "evaluations" / "evaluation.md"
    doc = _doc_exif()
    assert fiches.inscrire_taux(doc, rapport, source) == ["metadonnees-exif.md"]
    texte = (source / "metadonnees-exif.md").read_text(encoding="utf-8")
    bloc = fiches.bloc_des_taux("exif", doc, "../evaluations/evaluation.md")
    assert f"## Taux d'erreur\n\n{bloc}\n\n" in texte
    # Le reste de la fiche, rubrique rédigée comprise, est intact.
    origine = (fiches.SOURCE / "metadonnees-exif.md").read_text(encoding="utf-8")
    assert texte.replace(f"{bloc}\n\n", "") == origine
    # Une seconde écriture remplace le bloc.
    doc["date"] = "2027-01-01T00:00:00Z"
    fiches.inscrire_taux(doc, rapport, source)
    texte = (source / "metadonnees-exif.md").read_text(encoding="utf-8")
    assert texte.count(fiches.DEBUT) == 1
    assert "Mesurés le 2027-01-01" in texte


@pytest.mark.parametrize(
    ("contenu", "attendu"),
    [
        pytest.param(
            "# Fiche\n\nRien.\n", "rubrique « Taux d'erreur » absente", id="sans-rubrique"
        ),
        pytest.param(
            f"# Fiche\n\n## Taux d'erreur\n\n{fiches.DEBUT}\n", "marqueur de fin", id="sans-fin"
        ),
    ],
)
def test_fiche_sans_place_pour_les_taux(tmp_path: Path, contenu: str, attendu: str) -> None:
    source = tmp_path / "techniques"
    source.mkdir()
    (source / "metadonnees-exif.md").write_text(contenu, encoding="utf-8")
    with pytest.raises(ValueError, match=f"metadonnees-exif.md : {attendu}"):
        fiches.inscrire_taux(_doc_exif(), tmp_path / "r.md", source)


def test_rapport_non_publiable(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="rapport non publiable"):
        fiches.inscrire_taux(_doc_exif() | {"publiable": False}, tmp_path / "r.md", tmp_path)


def test_commande_fiches_taux(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source, copie = tmp_path / "techniques", tmp_path / "fiches"
    shutil.copytree(fiches.SOURCE, source)
    monkeypatch.setattr(fiches, "SOURCE", source)
    monkeypatch.setattr(fiches, "COPIE", copie)
    rapport = tmp_path / "evaluation.json"
    rapport.write_text(json.dumps(_doc_exif()), encoding="utf-8")
    assert fiches.main(["--taux", str(rapport)]) == 0
    assert "](../evaluation.md)" in (copie / "metadonnees-exif.md").read_text(encoding="utf-8")
    assert fiches.main(["--taux", str(tmp_path / "absent.json")]) == 2
    assert capsys.readouterr().err.startswith("fiches : ")


# Rapports publiés par T101 (ADR-0280)

RACINE = Path(__file__).resolve().parent.parent
EVALUATIONS = RACINE / "docs" / "verification" / "evaluations"
PREMIERE = EVALUATIONS / "reference-1.0.0-catalogue-0.20.1"
SECONDE = EVALUATIONS / "reference-1.0.0-catalogue-0.21.0"


def _publie(dossier: Path) -> dict[str, Any]:
    document: dict[str, Any] = json.loads((dossier / "evaluation.json").read_text(encoding="utf-8"))
    return document


@pytest.mark.exigence("ES-22")
def test_rapports_publies_sur_le_corpus_de_reference() -> None:
    manifeste = RACINE / "banc" / "reference" / "corpus.toml"
    empreinte = hashlib.sha256(manifeste.read_bytes()).hexdigest()
    for dossier in (PREMIERE, SECONDE):
        doc = _publie(dossier)
        assert doc["publiable"] is True
        assert doc["corpus"]["empreinte"] == empreinte
        assert doc["reseau"]["tentatives"] == 0
        # Le Markdown publié est celui que le banc rend du JSON, sans retouche.
        rendu = sortie.markdown(doc)
        assert (dossier / "evaluation.md").read_text(encoding="utf-8") == rendu
    assert _publie(PREMIERE)["versions"]["catalogue"]["version"] == "0.20.1"


def test_seconde_passe_avec_le_catalogue_livre() -> None:
    doc = _publie(SECONDE)
    assert doc["versions"]["catalogue"]["empreinte"] == _empreinte(LIVRE)
    assert not doc["versions"]["catalogue"]["fourni_par_utilisateur"]
    # Aucun indice au-dessus de sa mesure (guide du catalogue, §5).
    assert not [e for e in doc["ecarts"] if e.startswith("l'indice ")]


def test_niveaux_sans_effet_sur_les_taux_des_regles() -> None:
    """Les niveaux ne changent pas les constats (ADR-0278) : mêmes taux par règle et par
    technique dans les deux passes ; seul le taux par fichier peut changer."""
    premiere, seconde = _publie(PREMIERE), _publie(SECONDE)

    def taux(doc: dict[str, Any]) -> dict[str, Any]:
        return {r["identifiant"]: r["faux_positifs"] for r in doc["regles"]}

    assert taux(premiere) == taux(seconde)
    assert premiere["techniques"] == seconde["techniques"]
    assert premiere["fichiers"]["total"] == seconde["fichiers"]["total"]


def test_catalogue_livre_inscrit_d_apres_la_premiere_passe() -> None:
    doc = _publie(PREMIERE)
    attendues = {
        i.identifiant: i
        for i in inscription.inscriptions(doc, doc["versions"]["catalogue"]["empreinte"])
    }
    livre = catalogues.charger(manifestes.decouvrir()).regles
    evaluees = {r.identifiant: r for r in livre if r.evaluation is not None}
    assert set(evaluees) == set(attendues)
    for identifiant, regle in evaluees.items():
        attendue = attendues[identifiant]
        assert regle.evaluation is not None
        assert regle.niveau is not None
        assert regle.niveau.value == attendue.niveau
        assert (regle.evaluation.effectif, regle.evaluation.corpus) == (
            attendue.effectif,
            attendue.corpus,
        )
        assert regle.evaluation.borne_superieure == attendue.borne
        assert regle.evaluation.taux_faux_positifs == attendue.taux


@pytest.mark.exigence("NF-09")
def test_fiches_accordees_au_rapport_publie() -> None:
    doc = _publie(SECONDE)
    noms = {m.identifiant: f"{m.fiche}.md" for m in manifestes.decouvrir()}
    assert set(doc["versions"]["techniques"]) == set(noms)
    for module, nom in noms.items():
        texte = (fiches.SOURCE / nom).read_text(encoding="utf-8")
        lien = "../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md"
        assert fiches.bloc_des_taux(module, doc, lien) in texte, nom
