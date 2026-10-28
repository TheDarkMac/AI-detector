"""Tests des manifestes des modules : lecture, validation, ordre, désactivation (T12)."""

import re
from pathlib import Path

import pytest

from voight_kampff import modules
from voight_kampff._orchestration.manifestes import (
    Manifeste,
    ManifesteInvalide,
    ModuleInconnu,
    decouvrir,
    hors_v1,
    selectionner,
)
from voight_kampff.formats import PERIMETRE
from voight_kampff.rapport.modele import Direction

pytestmark = pytest.mark.exigence("NF-10", "P-06")

RACINE_DU_DEPOT = Path(__file__).resolve().parents[1]


def toml(nom: str, requiert: tuple[str, ...] = (), **remplacements: str) -> str:
    champs = {
        "identifiant": f'"{nom}"',
        "version": '"1.0.0"',
        "formats": '["jpeg", "png"]',
        "exigences": '["F-10", "NF-09"]',
        "regles": '["R-META-001"]',
        "fiche": '"metadonnees-image"',
        "directions": '["origine_ia", "rien_de_particulier"]',
        "requiert": "[" + ", ".join(f'"{r}"' for r in requiert) + "]",
        "bibliotheques": "[]",
    } | remplacements
    return "".join(f"{cle} = {valeur}\n" for cle, valeur in champs.items() if valeur)


def ecrire(racine: Path, dossier: str, contenu: str | bytes) -> None:
    (racine / dossier).mkdir()
    manifeste = racine / dossier / modules.MANIFESTE
    if isinstance(contenu, bytes):
        manifeste.write_bytes(contenu)
    else:
        manifeste.write_text(contenu, encoding="utf-8")


def identifiants(manifestes: tuple[Manifeste, ...]) -> list[str]:
    return [manifeste.identifiant for manifeste in manifestes]


def test_manifeste_lu(tmp_path: Path) -> None:
    ecrire(tmp_path, "exif", toml("exif"))
    (manifeste,) = decouvrir(tmp_path)
    assert manifeste == Manifeste(
        identifiant="exif",
        version="1.0.0",
        formats=("jpeg", "png"),
        exigences=("F-10", "NF-09"),
        regles=("R-META-001",),
        fiche="metadonnees-image",
        directions=(Direction.ORIGINE_IA, Direction.RIEN_DE_PARTICULIER),
        requiert=(),
    )


def test_seuls_les_dossiers_avec_manifeste(tmp_path: Path) -> None:
    ecrire(tmp_path, "exif", toml("exif"))
    (tmp_path / "vide").mkdir()
    (tmp_path / "fichier.toml").write_text(toml("fichier"))
    assert identifiants(decouvrir(tmp_path)) == ["exif"]


def test_ordre_d_execution(tmp_path: Path) -> None:
    ecrire(tmp_path, "a", toml("a", requiert=("c",)))
    ecrire(tmp_path, "b", toml("b"))
    ecrire(tmp_path, "c", toml("c"))
    ecrire(tmp_path, "d", toml("d", requiert=("a", "b")))
    # c avant a qui le requiert ; à rang égal, ordre des identifiants.
    assert identifiants(decouvrir(tmp_path)) == ["b", "c", "a", "d"]


@pytest.mark.parametrize(
    ("contenu", "attendu"),
    [
        pytest.param("identifiant = ", "illisible", id="toml-invalide"),
        pytest.param(b"\xff\xfe", "illisible", id="utf8-invalide"),
        pytest.param(toml("m", version=""), "required", id="champ-manquant"),
        pytest.param(toml("m") + "en_plus = 1\n", "additionalProperties", id="champ-en-plus"),
        pytest.param(toml("m", formats="[]"), "minItems", id="aucun-format"),
        pytest.param(toml("m", exigences='["X-1"]'), "pattern", id="exigence"),
        pytest.param(toml("m", directions='["inconnue"]'), "enum", id="direction"),
        pytest.param(toml("m", fiche='"Fiche/../x"'), "pattern", id="fiche"),
        pytest.param(toml("m", bibliotheques='["zlib"]'), "enum", id="bibliotheque"),
        pytest.param(toml("m", formats='["a", "a"]'), "uniqueItems", id="doublon"),
        pytest.param(toml("m", identifiant='"autre"'), "nom du dossier", id="identifiant"),
        pytest.param(toml("m", requiert=("m",)), "requis", id="se-requiert"),
        pytest.param(toml("m", requiert=("absent",)), "requis", id="requis-absent"),
    ],
)
def test_manifeste_refuse(tmp_path: Path, contenu: str | bytes, attendu: str) -> None:
    ecrire(tmp_path, "m", contenu)
    with pytest.raises(ManifesteInvalide, match=attendu):
        decouvrir(tmp_path)


def test_identifiant_en_majuscules_refuse(tmp_path: Path) -> None:
    ecrire(tmp_path, "Exif", toml("Exif"))
    with pytest.raises(ManifesteInvalide, match="pattern"):
        decouvrir(tmp_path)


def test_dependance_circulaire(tmp_path: Path) -> None:
    ecrire(tmp_path, "a", toml("a", requiert=("b",)))
    ecrire(tmp_path, "b", toml("b", requiert=("a",)))
    ecrire(tmp_path, "c", toml("c"))
    with pytest.raises(ManifesteInvalide, match="modules a, b : dépendance circulaire"):
        decouvrir(tmp_path)


# Désactivation


def test_selection(tmp_path: Path) -> None:
    ecrire(tmp_path, "a", toml("a"))
    ecrire(tmp_path, "b", toml("b", requiert=("a",)))
    ecrire(tmp_path, "c", toml("c", requiert=("b",)))
    ecrire(tmp_path, "d", toml("d"))
    livres = decouvrir(tmp_path)
    actifs, eteints = selectionner(livres, ())
    assert (identifiants(actifs), eteints) == (["a", "d", "b", "c"], ())
    # b désactivé : c, qui le requiert, l'est aussi ; a et d restent actifs.
    actifs, eteints = selectionner(livres, {"b"})
    assert (identifiants(actifs), identifiants(eteints)) == (["a", "d"], ["b", "c"])


def test_selection_module_inconnu(tmp_path: Path) -> None:
    ecrire(tmp_path, "a", toml("a"))
    with pytest.raises(ModuleInconnu, match="omega, zeta"):
        selectionner(decouvrir(tmp_path), {"zeta", "omega", "a"})


# Modules livrés


def test_modules_livres_valides() -> None:
    for manifeste in decouvrir():
        fiche = RACINE_DU_DEPOT / "docs" / "techniques" / f"{manifeste.fiche}.md"
        assert fiche.is_file(), manifeste.identifiant


def entete_de_fiche(fiche: str) -> dict[str, str]:
    """Champs « - **Nom** : valeur » de l'en-tête d'une fiche technique."""
    texte = (RACINE_DU_DEPOT / "docs" / "techniques" / f"{fiche}.md").read_text(encoding="utf-8")
    champs = re.findall(r"^- \*\*(.+?)\*\* : (.+)$", texte.split("\n## ", 1)[0], re.MULTILINE)
    return dict(champs)


def liste(valeur: str) -> tuple[str, ...]:
    return () if valeur == "aucune" else tuple(v.strip(" `") for v in valeur.split(","))


@pytest.mark.exigence("NF-09")
def test_fiche_et_manifeste_concordent() -> None:
    # ADR-0064 : la fiche répète le manifeste ; ce test vérifie qu'ils disent la même chose.
    for manifeste in decouvrir():
        entete = entete_de_fiche(manifeste.fiche)
        assert entete["Module"] == f"`{manifeste.identifiant}` (version {manifeste.version})"
        assert liste(entete["Exigences"]) == manifeste.exigences
        assert liste(entete["Formats"]) == manifeste.formats
        assert liste(entete["Directions permises"]) == manifeste.directions
        assert liste(entete["Règles"]) == manifeste.regles
        assert liste(entete["Bibliothèques"]) == manifeste.bibliotheques


def test_modules_de_metadonnees_livres() -> None:
    # T20 : un module par famille de métadonnées d'image (ADR-0114).
    livres = {manifeste.identifiant: manifeste for manifeste in decouvrir()}
    assert sorted(livres) == ["exif", "iptc", "textepng", "xmp"]
    assert livres["iptc"].formats == ("jpeg",)
    assert livres["textepng"].formats == ("png",)
    assert livres["xmp"].bibliotheques == ("expat",)
    for manifeste in livres.values():
        assert "F-10" in manifeste.exigences
        assert manifeste.directions == (Direction.RIEN_DE_PARTICULIER,)


# Techniques hors de cette version (T15, ADR-0087)


def test_techniques_hors_v1_livrees() -> None:
    techniques = hors_v1(decouvrir())
    identifiants = [technique.identifiant for technique in techniques]
    assert {"ela", "stylometrie"} <= set(identifiants)
    assert all(set(technique.formats) <= PERIMETRE for technique in techniques)
    # ENF, stylométrie, références : hors V1 sans engagement (ADR-0012).
    sans_engagement = {t.tache for t in techniques if t.statut == "sans_engagement"}
    assert sans_engagement == {"T62", "T82", "T83"}


HORS_V1 = """
[[technique]]
identifiant = "ela"
tache = "T42"
exigences = ["F-32"]
statut = "candidate_v2"
formats = ["jpeg"]
"""


@pytest.mark.parametrize(
    ("contenu", "attendu"),
    [
        pytest.param(HORS_V1 + HORS_V1, "deux fois", id="en-double"),
        pytest.param(HORS_V1.replace('"jpeg"', '"gif"'), "document non conforme", id="format"),
        pytest.param("technique = [", "fichier illisible", id="illisible"),
        pytest.param(b"\xff", "fichier illisible", id="non-utf8"),
    ],
)
def test_techniques_hors_v1_refusees(tmp_path: Path, contenu: str | bytes, attendu: str) -> None:
    fichier = tmp_path / modules.HORS_V1
    fichier.write_bytes(contenu.encode() if isinstance(contenu, str) else contenu)
    with pytest.raises(ManifesteInvalide, match=attendu):
        hors_v1((), tmp_path)


def test_module_livre_inscrit_hors_v1(tmp_path: Path) -> None:
    (tmp_path / modules.HORS_V1).write_text(HORS_V1, encoding="utf-8")
    livre = Manifeste("ela", "1.0", ("jpeg",), ("F-32",), (), "ela", (Direction.RETOUCHE,))
    assert [t.identifiant for t in hors_v1((), tmp_path)] == ["ela"]
    with pytest.raises(ManifesteInvalide, match="module livré inscrit hors V1 : ela"):
        hors_v1((livre,), tmp_path)
