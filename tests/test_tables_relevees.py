"""Tables relevées du complément de T40 : Photoshop et appareils, nommés par leur empreinte
(F-30, ADR-0191 à ADR-0196).

Les tables en clair, leurs comptes et leurs sources sont dans ``banc/releves/tables-T40c/``
(``tables.toml``, ``fichiers.csv``) ; ces tests reconstruisent chaque jeu de tables, en
vérifient l'empreinte et les règles qui le nomment.
"""

import csv
import re
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from metadonnees import app1_exif, ascii_, dqt, jpeg_image, tiff
from test_signatures import CATALOGUE, constats

from voight_kampff._regles import Application
from voight_kampff._travail import garde
from voight_kampff.modules import image
from voight_kampff.rapport.modele import Categorie, Direction, Fondement, Niveau

pytestmark = pytest.mark.exigence("F-30")

RELEVE = Path(__file__).resolve().parent.parent / "banc" / "releves" / "tables-T40c"
TABLES: list[dict[str, Any]] = tomllib.loads((RELEVE / "tables.toml").read_text())["tables"]
REGLES = {
    r.identifiant: r
    for r in CATALOGUE.regles
    if r.module == "image" and r.identifiant >= "R-IMAGE-008"
}
NIVEAUX = (3, 5, 6, 7, 8, 9, 10, 11, 12)
MARQUES = ("Apple", "Canon", "Kodak", "Olympus", "Panasonic", "Sony")
REGLE_DE: dict[tuple[str, int | str], str] = {
    ("photoshop", n): f"R-IMAGE-{8 + i:03d}" for i, n in enumerate(NIVEAUX)
} | {("appareil", m): f"R-IMAGE-{17 + i:03d}" for i, m in enumerate(MARQUES)}
LICENCES_LIBRES = re.compile(
    r"CC (BY|BY-SA) [234]\.[05]( [a-z]{2})?|CC0|Public domain|No restrictions|Attribution"
    r"|Copyrighted free use|GFDL( 1\.2)?|FAL|OGL 3"
)
"""Licences libres de Wikimedia Commons, telles que l'API les nomme (``LicenseShortName``)."""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def tables_de(entree: dict[str, Any]) -> image.Tables:
    return {
        int(cle.removeprefix("table_")): (False, tuple(valeurs))
        for cle, valeurs in entree.items()
        if cle.startswith("table_")
    }


def cle(entree: dict[str, Any]) -> tuple[str, int | str]:
    valeur: int | str = entree["niveau"] if "niveau" in entree else entree["marque"]
    return entree["famille"], valeur


def jpeg(entree: dict[str, Any], *segments: bytes) -> bytes:
    tables = tables_de(entree)
    return jpeg_image(
        640, 480, *segments, tables=dqt(*((i, v) for i, (_, v) in sorted(tables.items())))
    )


@pytest.mark.parametrize("entree", TABLES, ids=lambda e: e["empreinte"][:12])
def test_empreinte_des_tables_relevees(entree: dict[str, Any]) -> None:
    # ADR-0181 : l'empreinte se recalcule à partir des tables en clair, hors du fichier source.
    tables = tables_de(entree)
    assert all(len(v) == 64 and all(1 <= x <= 255 for x in v) for _, v in tables.values())
    assert image.empreinte_tables(tables) == entree["empreinte"]
    # Aucune n'est celle d'un encodeur que le module reconnaît déjà (ADR-0196).
    assert image.encodeur(tables) == {}


@pytest.mark.parametrize("entree", TABLES, ids=lambda e: e["empreinte"][:12])
def test_regle_des_tables_relevees(entree: dict[str, Any]) -> None:
    # Une seule règle par jeu ; sans condition sur les métadonnées (ADR-0192) : un JPEG qui
    # porte un EXIF donne le même constat qu'un JPEG dépouillé.
    regle = REGLE_DE[cle(entree)]
    regles = tuple(CATALOGUE.regles)
    assert constats("image", jpeg(entree), "jpeg", regles) == {regle: {}}
    avec_exif = jpeg(entree, app1_exif(tiff((ascii_(0x010F, "Canon"),))))
    assert constats("image", avec_exif, "jpeg", regles) == {regle: {}}


def test_chaque_regle_nomme_ses_tables() -> None:
    attendues: dict[str, set[str]] = {}
    for entree in TABLES:
        attendues.setdefault(REGLE_DE[cle(entree)], set()).add(entree["empreinte"])
    assert set(attendues) == set(REGLES) == set(REGLE_DE.values())
    for identifiant, regle in REGLES.items():
        (condition,) = regle.conditions
        assert condition.observation == "image.jpeg.empreinte_tables"
        assert set(condition.parmi or ()) == attendues[identifiant]
    # Une empreinte n'est nommée que par une règle.
    nommees = Counter(e for r in REGLES.values() for e in r.conditions[0].parmi or ())
    assert max(nommees.values()) == 1


@pytest.mark.exigence("ES-20")
def test_nature_des_regles() -> None:
    # ADR-0191 : indice faible, vérification déterministe ; Photoshop vers la transformation,
    # appareil vers l'authenticité.
    for (famille, _), identifiant in REGLE_DE.items():
        regle = REGLES[identifiant]
        assert regle.application is Application.MOTEUR
        assert regle.categorie is Categorie.INDICE
        assert (regle.niveau, regle.evaluation) == (Niveau.FAIBLE, None)
        assert regle.fondement is Fondement.VERIFICATION_DETERMINISTE
        attendue = Direction.TRANSFORMATION if famille == "photoshop" else Direction.AUTHENTICITE
        assert regle.direction is attendue
        assert regle.version == "1"


def test_concordance_du_releve() -> None:
    # ADR-0193 : au moins 3 fichiers versés par au moins 2 comptes ; chaque fichier source est
    # cité avec sa page et une licence libre.
    with (RELEVE / "fichiers.csv").open(encoding="utf-8", newline="") as fichier:
        sources = list(csv.DictReader(fichier))
    par_empreinte = Counter(source["empreinte"] for source in sources)
    comptes: dict[str, set[str]] = {}
    for source in sources:
        comptes.setdefault(source["empreinte"], set()).add(source["compte"])
        assert source["page"].startswith("https://commons.wikimedia.org/wiki/File:")
        assert LICENCES_LIBRES.fullmatch(source["licence"]), source["licence"]
    for entree in TABLES:
        assert entree["fichiers"] == par_empreinte[entree["empreinte"]] >= 3
        assert entree["comptes"] == len(comptes[entree["empreinte"]]) >= 2
    assert len({s["page"] for s in sources}) == len(sources)


def test_appareils_d_une_seule_marque() -> None:
    # ADR-0194 : une empreinte d'appareil n'est vue que sur une marque, jamais sur Photoshop.
    with (RELEVE / "fichiers.csv").open(encoding="utf-8", newline="") as fichier:
        sources = [s for s in csv.DictReader(fichier) if s["famille"] == "appareil"]
    marques: dict[str, set[str]] = {}
    for source in sources:
        marques.setdefault(source["empreinte"], set()).add(source["niveau_ou_marque"])
    assert all(len(m) == 1 for m in marques.values())
    photoshop = {e["empreinte"] for e in TABLES if e["famille"] == "photoshop"}
    assert not photoshop & set(marques)
