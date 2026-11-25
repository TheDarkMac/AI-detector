"""Publication du catalogue et des fiches techniques (T95, NF-19, ADR-0268 à ADR-0271).

Tout est public (ADR-0019) : chaque fiche est livrée dans le paquet, identique à sa source
``docs/techniques`` ; ``vk --fiche MODULE`` l'affiche, ``vk --regle IDENTIFIANT`` affiche une
règle dans la forme des fichiers du catalogue ; la couverture du rapport HTML cite la commande
de la fiche de chaque technique livrée.
"""

import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from conftest import construire_rapport
from test_rapport import analyse_de

from banc import fiches
from voight_kampff import __version__, _publication
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes
from voight_kampff._regles import Regle
from voight_kampff.cli import main
from voight_kampff.rapport._presentation import neutraliser, texte, textes
from voight_kampff.rapport.export import exporter_html

pytestmark = pytest.mark.exigence("NF-19")

RACINE = Path(__file__).resolve().parent.parent
_ENTETE_REGLES = 3
"""Lignes de commentaire avant la première règle : le catalogue, puis les deux de textes.toml."""


@pytest.fixture(scope="module")
def livre() -> catalogues.Catalogue:
    return catalogues.charger(manifestes.decouvrir(), None)


# Fiches livrées dans le paquet (ADR-0268)


def test_chaque_module_livre_a_sa_fiche_dans_le_paquet() -> None:
    assert fiches.ecarts() == []
    noms = sorted(p.name for p in fiches.COPIE.iterdir())
    assert noms == fiches.attendues()
    assert len(noms) == len(manifestes.decouvrir())


def test_fiches_lues_depuis_le_paquet() -> None:
    """Le paquet installé lit sa propre copie, identique à la source."""
    for manifeste in manifestes.decouvrir():
        source = (fiches.SOURCE / f"{manifeste.fiche}.md").read_text(encoding="utf-8")
        assert _publication.fiche(manifeste) == source


def test_fiches_sans_caractere_invisible() -> None:
    """La neutralisation de l'affichage (ES-12) ne change aucune fiche livrée."""
    for manifeste in manifestes.decouvrir():
        for ligne in _publication.fiche(manifeste).splitlines():
            assert neutraliser(ligne) == ligne


def _dossiers(tmp_path: Path) -> tuple[Path, Path]:
    source, copie = tmp_path / "source", tmp_path / "copie"
    source.mkdir()
    for nom in fiches.attendues():
        (source / nom).write_bytes((fiches.SOURCE / nom).read_bytes())
    return source, copie


def test_recopie_et_ecarts(tmp_path: Path) -> None:
    source, copie = _dossiers(tmp_path)
    nom = fiches.attendues()[0]
    assert fiches.ecarts(source, copie) == [f"{n} : absente du paquet" for n in fiches.attendues()]
    copie.mkdir()
    (copie / "retiree.md").write_text("module plus livré", encoding="utf-8")
    (copie / nom).write_text("ancienne version", encoding="utf-8")
    fiches.recopier(source, copie)
    assert fiches.ecarts(source, copie) == []
    assert not (copie / "retiree.md").exists()
    (copie / nom).write_text("autre", encoding="utf-8")
    (copie / "orpheline.md").write_text("x", encoding="utf-8")
    (source / fiches.attendues()[1]).unlink()
    assert fiches.ecarts(source, copie) == [
        f"{nom} : copie du paquet différente de la source",
        f"{fiches.attendues()[1]} : fiche absente de {source}",
        "orpheline.md : dans le paquet sans module livré",
    ]


def test_ecarts_sans_copie(tmp_path: Path) -> None:
    source, copie = _dossiers(tmp_path)
    assert len(fiches.ecarts(source, copie)) == len(fiches.attendues())


def test_commande_du_depot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source, copie = _dossiers(tmp_path)
    monkeypatch.setattr(fiches, "SOURCE", source)
    monkeypatch.setattr(fiches, "COPIE", copie)
    assert fiches.main(["--verifier"]) == 1
    assert "lancer « python -m banc.fiches »" in capsys.readouterr().err
    assert fiches.main([]) == 0
    assert fiches.main(["--verifier"]) == 0
    (source / fiches.attendues()[0]).unlink()
    assert fiches.main([]) == 2
    assert f"absentes de {source} : {fiches.attendues()[0]}" in capsys.readouterr().err


def test_copie_du_depot_a_jour() -> None:
    """Comme la CI la vérifie, par les tests : ``python -m banc.fiches --verifier``."""
    resultat = subprocess.run(
        [sys.executable, "-m", "banc.fiches", "--verifier"],
        cwd=RACINE,
        capture_output=True,
        text=True,
        check=False,
    )
    assert (resultat.returncode, resultat.stderr) == (0, "")


# vk --fiche MODULE


def test_vk_fiche(capsys: pytest.CaptureFixture[str]) -> None:
    manifeste = next(m for m in manifestes.decouvrir() if m.identifiant == "ela")
    assert main(["--fiche", "ela"]) == 0
    lignes = capsys.readouterr().out.splitlines()
    assert lignes[0] == texte(
        "publication.entete_fiche", module="ela", version=manifeste.version, outil=__version__
    )
    assert lignes[1] == ""
    assert lignes[2:] == _publication.fiche(manifeste).splitlines()
    assert lignes[2] == "# Fiche technique — Niveau d'erreur de recompression (ELA)"


def test_vk_fiche_neutralise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "ela.md").write_text("titre\u202e\nsuite\n", encoding="utf-8")
    monkeypatch.setattr(_publication, "fiches", lambda: tmp_path)
    assert main(["--fiche", "ela"]) == 0
    assert capsys.readouterr().out.splitlines()[2:] == ["titre⟨U+202E⟩", "suite"]


def test_vk_fiche_absente_du_paquet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(_publication, "fiches", lambda: tmp_path)
    with pytest.raises(SystemExit) as sortie:
        main(["--fiche", "ela"])
    assert sortie.value.code == 2
    assert "fiche du module ela absente de ce paquet" in capsys.readouterr().err


def test_vk_fiche_module_inconnu(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--fiche", "bruit\u202e"])
    assert sortie.value.code == 2
    erreur = capsys.readouterr().err
    assert "module inconnu : bruit⟨U+202E⟩ ; modules livrés : " in erreur
    assert "ela" in erreur


@pytest.mark.parametrize(
    "autres",
    [["x.jpg"], ["--regles"], ["--catalogue", "c"], ["--regle", "R-ELA-001"], ["--texte"]],
    ids=["fichier", "regles", "catalogue", "regle", "texte"],
)
def test_vk_fiche_s_emploie_seule(autres: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--fiche", "ela", *autres])
    assert sortie.value.code == 2
    assert "--fiche s'emploie seule" in capsys.readouterr().err


# vk --regle IDENTIFIANT (ADR-0269)


def test_toml_redonne_chaque_regle_du_catalogue(livre: catalogues.Catalogue) -> None:
    document = tomllib.loads(_publication.en_toml(livre.regles, ["en-tête"]))
    assert document["regle"] == [regle.vers_dict() for regle in livre.regles]
    assert tuple(Regle.depuis_dict(regle) for regle in document["regle"]) == livre.regles


def test_toml_d_une_regle_a_seuil(livre: catalogues.Catalogue) -> None:
    regle = next(r for r in livre.regles if r.identifiant == "R-DOUBLEJPEG-001")
    lignes = _publication.en_toml([regle]).splitlines()
    assert lignes[0] == "[[regle]]"
    assert 'seuil = { operateur = ">=", valeur = 4 }' in lignes
    assert "[[regle.condition]]" in lignes
    debut = lignes.index("limites = [")
    assert lignes[debut + 1].startswith('    "Seuils fixés à la main')
    assert lignes[debut + len(regle.limites) + 1] == "]"


def test_toml_echappe_ce_qu_un_terminal_n_affiche_pas(livre: catalogues.Catalogue) -> None:
    """Contrôle, mise en forme, séparateurs : ``\\u`` ; la valeur relue est la même (ES-12)."""
    origine = next(r for r in livre.regles if r.identifiant == "R-DOUBLEJPEG-001")
    titre = 'a"b\\c\td\ne\rf\bg\fh\x7fi\u202ej\u2028k\U000e0041l'
    regle = Regle.depuis_dict({**origine.vers_dict(), "titre": titre})
    ecrit = _publication.en_toml([regle])
    ligne = next(ligne for ligne in ecrit.splitlines() if ligne.startswith("titre = "))
    assert ligne == ('titre = "a\\"b\\\\c\\td\\ne\\rf\\bg\\fh\\u007Fi\\u202Ej\\u2028k\\U000E0041l"')
    assert ligne.isprintable()
    assert tomllib.loads(ecrit)["regle"][0]["titre"] == titre


def test_toml_valeurs() -> None:
    assert _publication._valeur(True) == "true"
    assert _publication._valeur(False) == "false"
    assert _publication._valeur(3) == "3"
    assert _publication._valeur(1e-05) == "1e-05"
    assert _publication._valeur({}) == "{}"
    assert _publication._valeur({"clé à espace": 1}) == '{ "clé à espace" = 1 }'
    assert _publication._valeur([]) == "[]"
    with pytest.raises(TypeError, match="valeur sans écriture TOML : NoneType"):
        _publication._valeur(None)
    assert tomllib.loads(f"x = {_publication._valeur(1e16)}")["x"] == 1e16


def test_vk_regle(livre: catalogues.Catalogue, capsys: pytest.CaptureFixture[str]) -> None:
    demandees = ["R-DWTDCT-001", "R-DOUBLEJPEG-001", "R-DWTDCT-001"]
    assert main([f"--regle={i}" for i in demandees]) == 0
    sortie = capsys.readouterr().out
    lignes = sortie.splitlines()
    version = livre.version
    assert lignes[0] == (
        f"# catalogue : {version.version} du {version.date.isoformat()}, "
        f"empreinte {version.empreinte}"
    )
    entete = textes()["publication"]["entete_regles"]
    assert lignes[1:_ENTETE_REGLES] == [f"# {ligne}" for ligne in entete]
    assert "vk --fiche MODULE" in entete[1]
    regles = tomllib.loads(sortie)["regle"]
    assert [r["identifiant"] for r in regles] == ["R-DWTDCT-001", "R-DOUBLEJPEG-001"]


def test_vk_regle_d_un_catalogue_fourni(
    livre: catalogues.Catalogue, capsys: pytest.CaptureFixture[str]
) -> None:
    dossier = RACINE / "src" / "voight_kampff" / "donnees" / "catalogue"
    assert main(["--catalogue", str(dossier), "--regle", livre.regles[0].identifiant]) == 0
    premiere = capsys.readouterr().out.splitlines()[0]
    assert premiere.endswith(f"fourni par l'utilisateur, empreinte {livre.version.empreinte}")


def test_vk_regle_inconnue(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--regle", "R-DWTDCT-001", "--regle", "R-INCONNUE-001\u202e"])
    assert sortie.value.code == 2
    erreur = capsys.readouterr().err
    assert "règle absente du catalogue employé : R-INCONNUE-001⟨U+202E⟩ ; vk --regles" in erreur


@pytest.mark.parametrize(
    "autres",
    [["x.jpg"], ["--regles"], ["--modules"], ["--texte"], ["--rapport", "r"], ["--journal", "j"]],
    ids=["fichier", "regles", "modules", "texte", "rapport", "journal"],
)
def test_vk_regle_s_emploie_seule(autres: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--regle", "R-DWTDCT-001", *autres])
    assert sortie.value.code == 2
    assert "--regle s'emploie seule, ou avec --catalogue" in capsys.readouterr().err


# Rapport HTML : la couverture cite la fiche de chaque technique livrée (ADR-0270)


def test_couverture_cite_les_fiches() -> None:
    analyse = analyse_de(construire_rapport())
    document = exporter_html(analyse)
    section = re.search(r'<section id="couverture".*?</section>', document)
    assert section is not None
    tableau = re.search(r"<table><caption>Techniques.*?</table>", section.group(0))
    assert tableau is not None
    assert '<th scope="col">Fiche technique</th>' in tableau.group(0)
    lignes = re.findall(r"<tr>(.*?)</tr>", tableau.group(0))[1:]
    dernieres = [re.findall(r"<td>(.*?)</td>", ligne)[-1] for ligne in lignes]
    attendues = [
        "" if t.version is None else f"vk --fiche {t.module}" for t in analyse.couverture.techniques
    ]
    assert dernieres == attendues
    assert "" in dernieres  # la technique hors de cette version n'a pas de fiche
    assert "vk --regle IDENTIFIANT" in section.group(0)


# Ce que le paquet publie ne renvoie qu'à des documents qui existent


def test_chemins_docs_cites_par_le_paquet_existent() -> None:
    """Un chemin ``docs/…`` cité par un fichier livré désigne un document du dépôt."""
    paquet = RACINE / "src" / "voight_kampff"
    cites = set()
    for chemin in paquet.rglob("*"):
        if chemin.suffix in {".toml", ".py", ".json"} and chemin.is_file():
            cites |= set(re.findall(r"docs/[\w./-]+\.md", chemin.read_text(encoding="utf-8")))
    assert "docs/catalogue/inventaire-des-marquages.md" in cites
    assert sorted(c for c in cites if not (RACINE / c).is_file()) == []
