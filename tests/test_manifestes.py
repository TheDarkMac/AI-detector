"""Tests des manifestes des modules : lecture, validation, ordre, désactivation (T12)."""

from pathlib import Path

import pytest

from voight_kampff import modules
from voight_kampff._orchestration.manifestes import (
    Manifeste,
    ManifesteInvalide,
    ModuleInconnu,
    decouvrir,
    selectionner,
)
from voight_kampff.rapport.modele import Direction

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


def test_aucun_module_livre_en_t12() -> None:
    # À retirer avec le premier module (T13) : il rappelle que la couverture est vide.
    assert decouvrir() == ()
