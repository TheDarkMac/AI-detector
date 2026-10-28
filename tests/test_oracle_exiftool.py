"""Oracle exiftool : les modules relèvent ce qu'exiftool relève (ADR-0043, ADR-0122).

Les échantillons de ``donnees/metadonnees/`` ont été écrits par exiftool, qui les a relus dans
``exiftool.json`` (``generer.sh``). Le test compare, dans les deux sens, les étiquettes EXIF
(par numéro et répertoire), les propriétés XMP (par nom local), les jeux de données IPTC et les
blocs texte PNG (par nom), et leurs valeurs, ramenées à une forme commune : exiftool écrit une
liste de nombres en texte séparé par des espaces, une latitude en degrés décimaux, un tableau
d'un seul élément comme une valeur simple.

exiftool n'est ni livré ni appelé par l'outil. S'il est installé dans la même version que celle
qui a produit ``exiftool.json``, un dernier test vérifie que sa sortie n'a pas changé.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from metadonnees import resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff.modules.exif import etiquettes

pytestmark = pytest.mark.exigence("F-10")

DOSSIER = Path(__file__).parent / "donnees" / "metadonnees"
ORACLE = json.loads((DOSSIER / "exiftool.json").read_text(encoding="utf-8"))
FORMATS = {".jpg": "jpeg", ".png": "png", ".webp": "webp", ".heic": "heic"}
REPERTOIRES = {
    "IFD0": "ifd0",
    "IFD1": "ifd1",
    "ExifIFD": "exif",
    "GPS": "gps",
    "InteropIFD": "interop",
}
MODULES = ("exif", "xmp", "iptc", "textepng")
GENERALES = frozenset({"present", "blocs", "ordre", "photoshop"})
"""Observations des modules sans équivalent chez exiftool : présence, nombre de blocs…"""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def lu_par_les_modules(fichier: str) -> dict[str, Any]:
    contenu = (DOSSIER / fichier).read_bytes()
    format_ = FORMATS[Path(fichier).suffix]
    lues: dict[str, Any] = {}
    for module in MODULES:
        lues |= valeurs_de(resultats(module, contenu, format_))
    return {nom: valeur for nom, valeur in lues.items() if nom.split(".")[1] not in GENERALES}


def lu_par_exiftool(fichier: str) -> dict[str, dict[str, Any]]:
    [entree] = [e for e in ORACLE if e["SourceFile"] == fichier]
    return {cle: valeur for cle, valeur in entree.items() if cle != "SourceFile"}


def attendu(nom_exiftool: str, entree: dict[str, Any]) -> str | None:
    """Nom de l'observation qui correspond à une valeur d'exiftool ; ``None`` hors du périmètre."""
    groupe, _, nom = nom_exiftool.partition(":")
    identifiant = entree["id"]
    if groupe in REPERTOIRES:
        repertoire = REPERTOIRES[groupe]
        return f"exif.{repertoire}.{etiquettes.nom(repertoire, identifiant)}"
    if groupe.startswith("XMP-"):
        return f":{identifiant}"  # nom local : le préfixe d'exiftool n'est pas celui de l'outil
    if groupe == "IPTC":
        return f"iptc.{nom}"
    if groupe == "PNG" and isinstance(identifiant, str) and len(identifiant) != 4:
        return f"textepng.{identifiant}"  # mot-clé ; les blocs de quatre lettres sont des types
    return None


def degres(valeur: list[float]) -> float:
    return valeur[0] + valeur[1] / 60 + valeur[2] / 3600


def concordent(notre: Any, sienne: Any) -> bool:
    if isinstance(notre, list) and isinstance(sienne, str) and sienne.replace(" ", "").isdigit():
        return notre == [int(n) for n in sienne.split()]
    if isinstance(notre, list) and len(notre) == 3 and isinstance(sienne, float):
        return abs(degres(notre) - sienne) < 1e-4
    if isinstance(notre, list) and not isinstance(sienne, list):
        return notre == [sienne]
    if isinstance(sienne, list) and not isinstance(notre, list):
        return [notre] == sienne
    if isinstance(notre, float) or isinstance(sienne, float):
        return abs(float(notre) - float(sienne)) < 1e-9
    return bool(notre == sienne)


def trouver(lues: dict[str, Any], cle: str) -> str | None:
    if cle.startswith(":"):
        return next((nom for nom in lues if nom.startswith("xmp.") and nom.endswith(cle)), None)
    return cle if cle in lues else None


@pytest.mark.parametrize("fichier", [entree["SourceFile"] for entree in ORACLE])
def test_les_modules_relevent_ce_que_releve_exiftool(fichier: str) -> None:
    lues = lu_par_les_modules(fichier)
    retrouvees: set[str] = set()
    for nom_exiftool, entree in lu_par_exiftool(fichier).items():
        cle = attendu(nom_exiftool, entree)
        if cle is None:
            continue
        nom = trouver(lues, cle)
        assert nom is not None, f"{fichier} : {nom_exiftool} non relevé"
        assert concordent(lues[nom], entree["val"]), (fichier, nom_exiftool, lues[nom])
        retrouvees.add(nom)
    # Dans l'autre sens : rien de relevé qu'exiftool ne connaisse.
    assert set(lues) == retrouvees, f"{fichier} : {sorted(set(lues) - retrouvees)}"


def test_oracle_couvre_les_quatre_formats_et_familles() -> None:
    assert sorted(FORMATS[Path(e["SourceFile"]).suffix] for e in ORACLE) == [
        "heic",
        "jpeg",
        "png",
        "webp",
    ]
    groupes = {cle.partition(":")[0] for entree in ORACLE for cle in entree}
    assert {"IFD0", "ExifIFD", "GPS", "IPTC", "XMP-dc", "PNG"} <= groupes


def version_d_exiftool() -> str | None:
    executable = shutil.which("exiftool")
    if executable is None:
        return None
    sortie = subprocess.run([executable, "-ver"], capture_output=True, check=True, text=True)
    return sortie.stdout.strip()


@pytest.mark.skipif(
    version_d_exiftool() != str(ORACLE[0]["ExifTool:ExifToolVersion"]["val"]),
    reason="exiftool absent, ou d'une autre version que celle de l'oracle",
)
def test_sortie_d_exiftool_inchangee() -> None:
    commande = ["exiftool", "-j", "-a", "-G1", "-n", "-D", "-struct"]
    commande += ["-x", "System:all", "-x", "File:all", "-x", "Composite:all"]
    commande += [entree["SourceFile"] for entree in ORACLE]
    sortie = subprocess.run(commande, capture_output=True, check=True, cwd=DOSSIER)
    assert json.loads(sortie.stdout) == ORACLE
