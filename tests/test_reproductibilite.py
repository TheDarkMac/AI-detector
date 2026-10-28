"""Tests de reproductibilité : deux analyses du même fichier, mêmes résultats (NF-06, T18).

Le rapport entier est comparé, à la date et au nom du fichier près (ADR-0108), par la
comparaison de l'outil (ADR-0112). Les analyses varient tout ce qui ne doit rien changer :
chemin et nom du fichier, dossier courant, graine de hachage, fuseau horaire, langue, rang dans
un lot, processus de travail (ADR-0110). La comparaison entre systèmes et versions de Python
est faite par la CI, sur le corpus d'essai.
"""

import dataclasses
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest
from catalogues import CATALOGUE
from echantillons import PDF, docx, jpeg, odt, png

from voight_kampff import Analyse, analyser
from voight_kampff import analyse as module_analyse
from voight_kampff._orchestration import soumission
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff.cli import main
from voight_kampff.rapport import comparaison, export
from voight_kampff.rapport.comparaison import Nature, RapportIllisible, comparer, lire
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    Dependance,
    Direction,
    EtatIsolation,
    EtatTechnique,
    ManqueIsolation,
    NiveauIsolation,
    NonMenee,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("NF-06", "P-05")

FACTICE = Path(__file__).with_name("travail_factice.py")
TOUT = list(CategorieIdentifiante)
SAUF_NOM = [c for c in CategorieIdentifiante if c is not CategorieIdentifiante.NOM_DE_FICHIER]
CONTENU = b"VKFT" + bytes(range(256)) * 4
ECHANTILLONS = {
    ".jpg": jpeg(),
    ".png": png(),
    ".pdf": PDF,
    ".docx": docx(),
    ".odt": odt(),
    ".bin": jpeg() + PDF,  # polyglotte, sans extension connue
}


def manifeste(identifiant: str, formats: tuple[str, ...] = ("jpeg",)) -> Manifeste:
    directions = (Direction.RIEN_DE_PARTICULIER,)
    return Manifeste(identifiant, "1.0", formats, ("F-10",), (), "test", directions)


# alpha constate, beta échoue, gamma ne s'applique pas, delta est partiel, theta dépasse une
# limite comptée : tous les cas d'un rapport, chacun déterministe.
MODULES = tuple(
    manifeste(nom, formats)
    for nom, formats in (
        ("alpha", ("jpeg",)),
        ("beta", ("jpeg",)),
        ("gamma", ("pdf",)),
        ("delta", ("jpeg",)),
        ("theta", ("jpeg",)),
    )
)


def factice(scenario: str) -> Callable[[int], list[str]]:
    def commande(descripteur: int) -> list[str]:
        script = [str(FACTICE), scenario, "--descripteur", str(descripteur)]
        return [sys.executable, "-I", "-B", *script]

    return commande


def document(analyse: Analyse, reveler: list[CategorieIdentifiante] = TOUT) -> dict[str, Any]:
    return export.document(analyse, reveler)


def analyse_factice(chemin: Path, modules: tuple[Manifeste, ...] = MODULES) -> Analyse:
    return soumission.soumettre(
        chemin, catalogue=CATALOGUE, manifestes=modules, hors_v1=(), commande=factice("modules")
    )


@pytest.fixture
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "f.jpg"
    chemin.write_bytes(CONTENU)
    return chemin


@pytest.fixture
def reference(fichier: Path) -> Analyse:
    return analyse_factice(fichier)


# Analyses répétées (ADR-0110)


def test_analyses_repetees_identiques(fichier: Path, reference: Analyse) -> None:
    # Le rapport de référence a de tout : constats, dont un du moteur, module en erreur, module
    # non applicable, partiel, limite comptée dépassée. Chaque processus de travail a sa propre
    # graine de hachage : l'environnement lui est retiré (ADR-0065).
    assert {c.regle.identifiant for c in reference.constats} == {"R-TEST-001", "R-TEST-003"}
    assert {(n.raison, n.module) for n in reference.non_menees} == {
        (RaisonNonMenee.ERREUR_MODULE, "beta"),
        (RaisonNonMenee.FORMAT_PARTIEL, "delta"),
        (RaisonNonMenee.LIMITE_DEPASSEE, "theta"),
    }
    assert {t.module: t.etat for t in reference.couverture.techniques} == {
        "alpha": EtatTechnique.APPLIQUEE,
        "beta": EtatTechnique.NON_MENEE,
        "gamma": EtatTechnique.NON_APPLICABLE,
        "delta": EtatTechnique.PARTIELLE,
        "theta": EtatTechnique.NON_MENEE,
    }
    assert not reference.interrompue  # une limite comptée n'interrompt pas (ADR-0076)
    attendu = document(reference)
    for _ in range(3):
        resultat = comparer(attendu, document(analyse_factice(fichier)))
        assert resultat.ecarts == ()
        assert resultat.garantie
        assert resultat.identiques
        assert not resultat.defaut


def test_polyglotte_repete(tmp_path: Path) -> None:
    chemin = tmp_path / "f.bin"
    chemin.write_bytes(CONTENU)

    def une_analyse() -> Analyse:
        return soumission.soumettre(
            chemin,
            catalogue=CATALOGUE,
            manifestes=(manifeste("alpha"), manifeste("gamma", ("pdf",))),
            hors_v1=(),
            commande=factice("polyglotte"),
        )

    premiere = une_analyse()
    assert len(premiere.identification.parties) == 3
    resultat = comparer(document(premiere), document(une_analyse()))
    assert resultat.ecarts == ()
    assert resultat.garantie


def test_module_non_reproductible_detecte(fichier: Path) -> None:
    # Le test doit savoir échouer : kappa observe le numéro de son processus.
    modules = (manifeste("kappa"),)
    resultat = comparer(
        document(analyse_factice(fichier, modules)), document(analyse_factice(fichier, modules))
    )
    assert resultat.ecarts == (comparaison.Ecart("observations[0].valeur", Nature.RESULTAT),)
    assert resultat.garantie
    assert resultat.defaut


def test_vrais_processus_de_travail(tmp_path: Path) -> None:
    for extension, contenu in ECHANTILLONS.items():
        chemin = tmp_path / f"echantillon{extension}"
        chemin.write_bytes(contenu)
        resultat = comparer(document(analyser(chemin)), document(analyser(chemin)))
        assert (extension, resultat.ecarts) == (extension, ())


# Conditions qui ne doivent rien changer, par la ligne de commande (ADR-0110)


def lancer(fichiers: list[Path], dossier: Path, cwd: Path, env: Mapping[str, str]) -> None:
    options = [f"--reveler={categorie}" for categorie in SAUF_NOM]
    commande = [sys.executable, "-m", "voight_kampff", "--rapport", str(dossier), *options]
    subprocess.run(
        [*commande, *map(str, fichiers)],
        cwd=cwd,
        env=dict(os.environ) | dict(env),
        check=True,
        capture_output=True,
        timeout=600,
    )


DATES = {".json": 1, ".html": 2}  # le HTML la donne à l'identification et dans son en-tête


def sans_date(chemin: Path) -> bytes:
    """Contenu du rapport, date de l'analyse remplacée : seul champ qui change (ADR-0108)."""
    motif = rb"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\dZ?"
    remplace, nombre = re.subn(motif, b"DATE", chemin.read_bytes())
    assert nombre == DATES[chemin.suffix]
    return remplace


@pytest.mark.exigence("ES-14")
def test_rapports_identiques_quelles_que_soient_les_conditions(tmp_path: Path) -> None:
    extensions = list(ECHANTILLONS)
    a, b = tmp_path / "a", tmp_path / "b"
    for racine in (a, b):
        (racine / "fichiers").mkdir(parents=True)
        (racine / "courant").mkdir()
    # Autres dossiers, autres noms (même extension), ordre inverse dans le lot.
    premiers = [a / "fichiers" / f"original{e}" for e in extensions]
    seconds = [b / "fichiers" / f"copie renommée {rang}{e}" for rang, e in enumerate(extensions)]
    for chemin, extension in [
        *zip(premiers, extensions, strict=True),
        *zip(seconds, extensions, strict=True),
    ]:
        chemin.write_bytes(ECHANTILLONS[extension])
    commun = {"PYTHONIOENCODING": "utf-8"}
    lancer(
        premiers,
        a / "rapports",
        a / "courant",
        commun | {"PYTHONHASHSEED": "1", "TZ": "UTC", "LC_ALL": "C", "LANG": "C"},
    )
    lancer(
        seconds[::-1],
        b / "rapports",
        b / "courant",
        commun
        | {
            "PYTHONHASHSEED": "4242",
            "TZ": "Pacific/Kiritimati",
            "LC_ALL": "fr_FR.UTF-8",
            "LANG": "fr_FR.UTF-8",
        },
    )
    nombre = len(extensions)
    for rang in range(1, nombre + 1):
        autre = nombre + 1 - rang
        for extension in DATES:
            premier = a / "rapports" / f"{rang}{extension}"
            second = b / "rapports" / f"{autre}{extension}"
            # Octet pour octet, à la date près : le nom du fichier est masqué dans les deux.
            assert sans_date(premier) == sans_date(second), (extensions[rang - 1], extension)
        resultat = comparer(
            lire(a / "rapports" / f"{rang}.json"), lire(b / "rapports" / f"{autre}.json")
        )
        assert resultat.ecarts == ()
        assert resultat.garantie


# Comparaison (ADR-0112)


def test_date_et_nom_ignores(reference: Analyse) -> None:
    autre = dataclasses.replace(
        reference,
        identification=dataclasses.replace(
            reference.identification,
            nom="autre nom.jpg",
            date_analyse=reference.identification.date_analyse.replace(year=2030),
        ),
    )
    resultat = comparer(document(reference), document(autre))
    assert resultat.ecarts == ()
    assert resultat.garantie
    assert resultat.meme_fichier


def ecarts_de(a: Mapping[str, Any], b: Mapping[str, Any]) -> list[tuple[str, Nature]]:
    return [(e.chemin, e.nature) for e in comparer(a, b).ecarts]


def test_ecart_de_resultat_dans_la_garantie(reference: Analyse) -> None:
    a = document(reference)
    b = json.loads(json.dumps(a))
    b["observations"][0]["valeur"] = "autre"
    b["constats"].pop()
    b["couverture"]["marquages_recherches"].append("c2pa")
    resultat = comparer(a, b)
    assert ecarts_de(a, b) == [
        ("couverture.marquages_recherches[0]", Nature.RESULTAT),
        ("observations[0].valeur", Nature.RESULTAT),
        ("constats[1]", Nature.RESULTAT),
    ]
    assert resultat.garantie
    assert not resultat.identiques
    assert resultat.defaut


@pytest.mark.parametrize(
    ("chemin", "valeur", "attendu"),
    [
        (("versions", "outil"), "9.9.9", "versions.outil"),
        (("versions", "interpreteur", "version"), "3.99.0", "versions.interpreteur.version"),
        (("versions", "catalogue", "version"), "9.9.9", "versions.catalogue.version"),
        (("identification", "empreinte"), "b" * 64, "identification.empreinte"),
        (("identification", "extension"), "jpeg", "identification.extension"),
    ],
)
def test_condition_differente_hors_garantie(
    reference: Analyse, chemin: tuple[str, ...], valeur: str, attendu: str
) -> None:
    a = document(reference)
    b = json.loads(json.dumps(a))
    cible = b
    for cle in chemin[:-1]:
        cible = cible[cle]
    cible[chemin[-1]] = valeur
    b["constats"] = []  # résultats différents : expliqués par la condition
    resultat = comparer(a, b)
    assert (attendu, Nature.CONDITION) in ecarts_de(a, b)
    assert not resultat.garantie
    assert not resultat.identiques
    assert not resultat.defaut


def test_analyse_interrompue_hors_garantie(reference: Analyse) -> None:
    interrompue = dataclasses.replace(
        reference, non_menees=(*reference.non_menees, NonMenee(RaisonNonMenee.DELAI_DEPASSE))
    )
    for a, b in [(reference, interrompue), (interrompue, interrompue)]:
        resultat = comparer(document(a), document(b))
        assert resultat.interrompue
        assert not resultat.garantie
        assert not resultat.defaut
    resultat = comparer(document(reference), document(interrompue))
    assert ("interrompue", Nature.CONDITION) in [(e.chemin, e.nature) for e in resultat.ecarts]


def test_isolation_differente_sans_effet_sur_la_garantie(reference: Analyse) -> None:
    reduite = dataclasses.replace(
        reference, isolation=EtatIsolation(NiveauIsolation.REDUITE, (ManqueIsolation.RESEAU,))
    )
    complete = dataclasses.replace(reference, isolation=EtatIsolation(NiveauIsolation.COMPLETE))
    resultat = comparer(document(reduite), document(complete))
    assert {e.nature for e in resultat.ecarts} == {Nature.ENVIRONNEMENT}
    assert resultat.garantie
    assert resultat.identiques


def test_donnees_masquees_non_comparees(reference: Analyse) -> None:
    a = document(reference)
    b = json.loads(json.dumps(a))
    b["identification"]["empreinte"] = "b" * 64
    masque = document(reference, [])
    # Masquée dans l'un : l'empreinte n'est comparée dans aucun, le même fichier n'est pas établi.
    resultat = comparer(masque, b)
    assert resultat.ecarts == ()
    assert resultat.non_comparees == tuple(SAUF_NOM)
    assert not resultat.meme_fichier
    assert not resultat.garantie
    assert resultat.identiques


def test_valeur_d_une_observation_masquee_non_comparee(reference: Analyse) -> None:
    a = document(reference)
    b = json.loads(json.dumps(a))
    a["observations"][0]["identifiante"] = b["observations"][0]["identifiante"] = "gps"
    b["observations"][0]["valeur"] = "autre"
    b["masquage"] = {"masquees": ["gps"], "levees": [c for c in TOUT if c != "gps"]}
    del b["observations"][0]["valeur"]
    resultat = comparer(a, b)
    assert resultat.ecarts == ()
    assert resultat.non_comparees == (CategorieIdentifiante.GPS,)
    assert resultat.garantie


def test_types_et_cles_compares(reference: Analyse) -> None:
    a = document(reference)
    for valeur in (1.0, True, None):
        b = json.loads(json.dumps(a))
        a["observations"][0]["valeur"] = 1
        b["observations"][0]["valeur"] = valeur
        assert ecarts_de(a, b) == [("observations[0].valeur", Nature.RESULTAT)]
    a["observations"][0]["valeur"] = None  # null : égal à lui-même seulement
    assert ecarts_de(a, json.loads(json.dumps(a))) == []
    b = json.loads(json.dumps(a))
    del b["observations"][0]["nom"]
    b["constats"][0]["localisation"] = {"page": 1}
    assert ecarts_de(a, b) == [
        ("observations[0].nom", Nature.RESULTAT),
        ("constats[0].localisation", Nature.RESULTAT),
    ]


def test_interpreteur_au_rapport(reference: Analyse, monkeypatch: pytest.MonkeyPatch) -> None:
    versions = reference.rapport().versions
    assert versions.interpreteur == Dependance(
        sys.implementation.name, ".".join(map(str, sys.version_info[:3]))
    )
    avant = document(reference)
    monkeypatch.setattr(module_analyse, "interpreteur", lambda: Dependance("pypy", "3.12.0"))
    resultat = comparer(avant, document(reference))
    assert ("versions.interpreteur.nom", Nature.CONDITION) in [
        (e.chemin, e.nature) for e in resultat.ecarts
    ]
    assert "pypy 3.12.0" in export.exporter_html(reference)


# Lecture d'un export


def test_lire_un_export(tmp_path: Path, reference: Analyse) -> None:
    chemin = tmp_path / "1.json"
    chemin.write_text(export.exporter_json(reference), encoding="utf-8")
    assert lire(chemin) == json.loads(chemin.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("contenu", "message"),
    [
        (b'{"a": 1, "a": 2}', "pas un objet JSON strict"),
        (b"[]", "pas un objet JSON strict"),
        (b'{"version_schema": "0.2.0"}', "pas un rapport de cette version de l'outil"),
    ],
)
def test_export_illisible(tmp_path: Path, contenu: bytes, message: str) -> None:
    chemin = tmp_path / "1.json"
    chemin.write_bytes(contenu)
    with pytest.raises(RapportIllisible, match=message):
        lire(chemin)


def test_export_trop_grand_ou_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chemin = tmp_path / "1.json"
    chemin.write_bytes(b"{}" + b" " * 10)
    monkeypatch.setattr(comparaison, "TAILLE_MAX_RAPPORT", 8)
    with pytest.raises(RapportIllisible, match="plus de 0 Mio"):
        lire(chemin)
    with pytest.raises(RapportIllisible, match="fichier illisible"):
        lire(tmp_path / "absent.json")


# vk --comparer


def ecrire(dossier: Path, nom: str, document_: Mapping[str, Any]) -> Path:
    chemin = dossier / nom
    chemin.write_text(json.dumps(document_), encoding="utf-8")
    return chemin


def test_commande_resultats_identiques(
    tmp_path: Path, reference: Analyse, capsys: pytest.CaptureFixture[str]
) -> None:
    a = ecrire(tmp_path, "a.json", document(reference))
    b = ecrire(tmp_path, "b.json", document(reference))
    assert main(["--comparer", str(a), str(b)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "Résultats identiques : mêmes parties, couverture, observations, constats et analyses "
        "non menées, à la date et au nom du fichier près.",
        "Conditions de la garantie de reproductibilité réunies : même fichier, même extension, "
        "mêmes versions, analyses non interrompues.",
    ]


def test_commande_defaut_de_reproductibilite(
    tmp_path: Path, reference: Analyse, capsys: pytest.CaptureFixture[str]
) -> None:
    a = document(reference)
    # Isolation fixée des deux côtés : celle de l'analyse dépend du système (réduite sous Windows).
    a["isolation"] = {"niveau": "complete", "manques": []}
    b = json.loads(json.dumps(a))
    b["observations"][0]["valeur"] = "autre"
    b["isolation"] = {"niveau": "reduite", "manques": ["reseau"]}
    masque = [c for c in TOUT if c != "gps"]
    for d in (a, b):
        d["masquage"] = {"masquees": ["gps"], "levees": masque}
    code = main(["--comparer", str(ecrire(tmp_path, "a", a)), str(ecrire(tmp_path, "b", b))])
    assert code == 1
    assert capsys.readouterr().out.splitlines() == [
        "Résultats différents : 1 écart(s).",
        "Conditions de la garantie de reproductibilité réunies : même fichier, même extension, "
        "mêmes versions, analyses non interrompues.",
        "Défaut de reproductibilité : dans les conditions de la garantie, les résultats "
        "devraient être identiques. À signaler au projet, avec les deux rapports.",
        "Isolation différente d'un poste à l'autre : elle ne doit changer aucun résultat.",
        "Non comparées, car masquées dans au moins un rapport : coordonnées GPS.",
        "écart (environnement) : isolation.niveau",
        "écart (environnement) : isolation.manques[0]",
        "écart (résultat) : observations[0].valeur",
    ]


def test_commande_hors_garantie(
    tmp_path: Path, reference: Analyse, capsys: pytest.CaptureFixture[str]
) -> None:
    a = document(reference)
    b = json.loads(json.dumps(a))
    b["identification"]["extension"] = "jpeg"
    b["versions"]["outil"] = "9.9.9"
    b["interrompue"] = True  # incohérent, mais seule la comparaison le lit ici
    b["observations"] = [dict(o, nom=f"autre.{rang}") for rang, o in enumerate(a["observations"])]
    b["observations"] *= 20
    c = document(reference, [])
    chemins = [ecrire(tmp_path, n, d) for n, d in (("a", a), ("b", b), ("c", c))]
    assert main(["--comparer", str(chemins[0]), str(chemins[1])]) == 1
    sortie = capsys.readouterr().out.splitlines()
    assert sortie[1] == (
        "Hors garantie de reproductibilité : extensions différentes, versions différentes "
        "(outil, interpréteur, catalogue ou dépendances), analyse interrompue. Des résultats "
        "différents s'expliquent alors."
    )
    assert sortie[-1].startswith("… et ")
    assert len(sortie) == 2 + 50 + 1
    assert main(["--comparer", str(chemins[0]), str(chemins[2])]) == 0
    sortie = capsys.readouterr().out.splitlines()
    assert sortie[1] == (
        "Hors garantie de reproductibilité : même fichier non établi (empreinte masquée). Des "
        "résultats différents s'expliquent alors."
    )
    assert sortie[-1] == (
        "Empreinte masquée : rien n'établit qu'il s'agit du même fichier ; écrire les rapports "
        "avec --reveler empreinte."
    )


def test_commande_rapport_illisible(
    tmp_path: Path, reference: Analyse, capsys: pytest.CaptureFixture[str]
) -> None:
    a = ecrire(tmp_path, "a.json", document(reference))
    assert main(["--comparer", str(a), str(tmp_path / "absent.json")]) == 2
    assert capsys.readouterr().err.startswith("rapport 2 : fichier illisible")


def test_commande_comparer_seule(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--comparer", "a.json", "b.json", "fichier.jpg"])
    assert sortie.value.code == 2
    assert "--comparer s'emploie seule" in capsys.readouterr().err
