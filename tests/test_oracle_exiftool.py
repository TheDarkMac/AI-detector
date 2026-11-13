"""Oracle exiftool : les modules relèvent ce qu'exiftool relève (ADR-0043, ADR-0122, ADR-0135).

Les échantillons de ``donnees/metadonnees/`` ont été écrits par exiftool ou ffmpeg, puis relus
par exiftool dans ``exiftool.json`` (``generer.sh``, ``generer_pdf.sh``, ``generer_media.sh``,
``relire.sh``). Le test compare, dans les deux sens, les étiquettes EXIF (par numéro et
répertoire), les propriétés XMP (par nom local), les jeux de données IPTC, les blocs texte PNG,
les entrées du dictionnaire Info d'un PDF et les balises audio et vidéo (par identifiant), et
leurs valeurs, ramenées à une forme commune : exiftool écrit une liste de nombres en texte
séparé par des espaces, une latitude en degrés décimaux, un tableau d'un seul élément comme une
valeur simple, une date à sa façon, des mots-clés PDF en liste, un nombre XMP en nombre, un
texte RIFF en Latin-1, la date et l'heure de ``bext`` ensemble.

exiftool n'est ni livré ni appelé par l'outil. S'il est installé dans la même version que celle
qui a produit ``exiftool.json``, un dernier test vérifie que sa sortie n'a pas changé.
"""

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from metadonnees import resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules.exif import etiquettes

pytestmark = pytest.mark.exigence("F-10")

DOSSIER = Path(__file__).parent / "donnees" / "metadonnees"
ORACLE = json.loads((DOSSIER / "exiftool.json").read_text(encoding="utf-8"))
FORMATS = {
    ".jpg": "jpeg",
    ".png": "png",
    ".webp": "webp",
    ".heic": "heic",
    ".pdf": "pdf",
    ".wav": "wav",
    ".mp3": "mp3",
    ".aac": "aac",
    ".m4a": "m4a",
    ".flac": "flac",
    ".ogg": "ogg",
    ".opus": "ogg",
    ".mp4": "mp4",
    ".mov": "mov",
    ".webm": "webm",
}
REPERTOIRES = {
    "IFD0": "ifd0",
    "IFD1": "ifd1",
    "ExifIFD": "exif",
    "GPS": "gps",
    "InteropIFD": "interop",
}
MODULES = {
    "jpeg": ("exif", "xmp", "iptc"),
    "png": ("exif", "xmp", "textepng"),
    "webp": ("exif", "xmp"),
    "heic": ("exif", "xmp"),
    "pdf": ("infopdf", "xmp"),
    "wav": ("id3", "infowav", "xmp"),
    "mp3": ("id3",),
    "aac": ("id3",),
    "m4a": ("quicktime", "xmp"),
    "flac": ("id3", "vorbis"),
    "ogg": ("vorbis",),
    "mp4": ("quicktime", "xmp"),
    "mov": ("quicktime", "xmp"),
    "webm": ("matroska",),
}
GENERALES = frozenset({"present", "blocs", "ordre", "photoshop", "chiffre", "version"})
"""Observations des modules sans équivalent chez exiftool : présence, nombre de blocs…"""
STRUCTURE_PDF = frozenset({"Version", "_linearized", "Count", "PageMode", "Lang", "Marked"})
"""Groupe « PDF » d'exiftool hors du dictionnaire Info : en-tête, catalogue, pages (T50)."""
ID3V1 = {3: "Title", 33: "Artist", 63: "Album", 93: "Year", 97: "Comment", 126: "Track"}
ID3V1 |= {127: "Genre"}
BEXT = {
    "Description": "Description",
    "Originator": "Originator",
    "OriginatorReference": "OriginatorReference",
    "DateTimeOriginal": "OriginationDate OriginationTime",
    "TimeReference": "TimeReference",
    "BWFVersion": "Version",
    "BWF_UMID": "UMID",
    "CodingHistory": "CodingHistory",
}
"""Champs du bloc ``bext``, nommés par exiftool ; il joint la date et l'heure."""
INFO_MATROSKA = {0x3BA9: "Title", 0x0D80: "MuxingApp", 0x1741: "WritingApp", 0x0461: "DateUTC"}
"""Éléments d'``Info``, identifiés par exiftool sans les bits de longueur de l'identifiant."""
DATE = re.compile(r"(D:)?\d{4}[-:]?\d\d[-:]?\d\d([T ]?\d\d:?\d\d:?\d\d.*)?")
EPOQUES = {
    "quicktime.mvhd.CreationTime": (datetime(1904, 1, 1, tzinfo=UTC), 1),
    "quicktime.mvhd.ModificationTime": (datetime(1904, 1, 1, tzinfo=UTC), 1),
    "matroska.DateUTC": (datetime(2001, 1, 1, tzinfo=UTC), 10**9),
}
"""Dates observées telles qu'écrites, en unités depuis une origine (ADR-0133)."""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def lu_par_les_modules(fichier: str) -> dict[str, Any]:
    contenu = (DOSSIER / fichier).read_bytes()
    format_ = FORMATS[Path(fichier).suffix]
    lues: dict[str, Any] = {}
    for module in MODULES[format_]:
        lues |= valeurs_de(resultats(module, contenu, format_))
    if "infowav.bext.OriginationDate" in lues:
        date, heure = (
            lues.pop("infowav.bext.OriginationDate"),
            lues.pop("infowav.bext.OriginationTime"),
        )
        lues["infowav.bext.OriginationDate OriginationTime"] = f"{date} {heure}"
    for nom, (origine, par_seconde) in EPOQUES.items():
        if nom in lues:
            date = origine + timedelta(seconds=lues[nom] / par_seconde)
            lues[nom] = date.strftime("%Y:%m:%d %H:%M:%S")
    return {nom: valeur for nom, valeur in lues.items() if nom.split(".")[1] not in GENERALES}


def lu_par_exiftool(fichier: str) -> dict[str, dict[str, Any]]:
    [entree] = [e for e in ORACLE if e["SourceFile"] == fichier]
    return {cle: valeur for cle, valeur in entree.items() if cle != "SourceFile"}


def attendus(nom_exiftool: str, entree: dict[str, Any]) -> tuple[str, ...]:
    """Noms possibles de l'observation qui correspond à une valeur d'exiftool ; aucun hors du
    périmètre. Un nom qui commence par ``:`` est le nom local d'une propriété XMP."""
    groupe, *_, nom = nom_exiftool.split(":")  # « Groupe:Copy1:Nom » pour une copie
    identifiant = entree["id"]
    if groupe in REPERTOIRES:
        repertoire = REPERTOIRES[groupe]
        return (f"exif.{repertoire}.{etiquettes.nom(repertoire, identifiant)}",)
    if groupe.startswith("XMP-"):
        return (f":{identifiant}",)  # nom local : le préfixe d'exiftool n'est pas celui de l'outil
    if groupe == "IPTC":
        return (f"iptc.{nom}",)
    if groupe == "PNG" and isinstance(identifiant, str) and len(identifiant) != 4:
        return (f"textepng.{identifiant}",)  # mot-clé ; les blocs de quatre lettres sont des types
    if groupe == "PDF" and identifiant not in STRUCTURE_PDF:
        return (f"infopdf.{identifiant}",)
    return attendus_media(groupe, nom, identifiant)


def attendus_media(groupe: str, nom: str, identifiant: Any) -> tuple[str, ...]:
    """Balises audio et vidéo ; les en-têtes de flux et les pistes sont de la structure (T71,
    T72), hors du périmètre (ADR-0132)."""
    if groupe.startswith("ID3v2_"):
        trame, _, description = str(identifiant).partition("_")  # « TXXX_description »
        suite = f".{valeurs.composant(description)}" if description else ""
        return (f"id3.{trame}{suite}",)
    if groupe == "ID3v1":
        return (f"id3.v1.{ID3V1[identifiant]}",)
    if groupe == "RIFF" and isinstance(identifiant, str):
        return (f"infowav.{identifiant}",)
    if groupe == "RIFF" and nom in BEXT:
        return (f"infowav.bext.{BEXT[nom]}",)
    if groupe in ("ItemList", "UserData"):
        lieu = "ilst" if groupe == "ItemList" else "udta"
        return (f"quicktime.{lieu}.{identifiant.replace('?', '-')}",)  # « ? » pour « © »
    if groupe == "Keys":
        cles = (identifiant, f"com.apple.quicktime.{identifiant}")
        return tuple(f"quicktime.mdta.{valeurs.composant(cle)}" for cle in cles)
    if groupe == "QuickTime" and nom in ("CreateDate", "ModifyDate"):
        return (f"quicktime.mvhd.{'Creation' if nom == 'CreateDate' else 'Modification'}Time",)
    if groupe == "Vorbis" and isinstance(identifiant, str):
        return (f"vorbis.{identifiant}",)
    if groupe == "Matroska" and isinstance(identifiant, str):
        return tuple(f"matroska.{cible}.{identifiant}" for cible in ("tag", "piste", "cible"))
    if groupe == "Matroska" and identifiant in INFO_MATROSKA:
        return (f"matroska.{INFO_MATROSKA[identifiant]}",)
    return ()


def degres(valeur: list[float]) -> float:
    return valeur[0] + valeur[1] / 60 + valeur[2] / 3600


def chiffres(date: str) -> str:
    return "".join(c for c in date if c.isdigit())


def concordent(notre: Any, sienne: Any) -> bool:
    if isinstance(notre, str) and isinstance(sienne, str) and DATE.fullmatch(notre):
        return chiffres(notre) == chiffres(sienne)  # D:AAAAMMJJ…, ISO 8601 ou AAAA:MM:JJ
    if isinstance(notre, str) and isinstance(sienne, list):
        return notre.split(", ") == sienne  # mots-clés PDF : exiftool les sépare
    if isinstance(notre, str) and type(sienne) is int:
        return notre == str(sienne)  # nombre XMP ou année ID3v1 écrits en texte
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


def en_utf8(texte: str) -> str:
    """Texte RIFF qu'exiftool lit en Latin-1, relu en UTF-8 comme le fait ``infowav``."""
    try:
        return texte.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texte


def vide(nom_exiftool: str, valeur: Any) -> bool:
    """Valeur qu'exiftool relève et que les modules n'observent pas : texte vide, genre ID3v1
    255 (« aucun »), UMID nul."""
    if valeur == "":
        return True
    if nom_exiftool.startswith("ID3v1:") and nom_exiftool.endswith(":Genre"):
        return bool(valeur == 255)
    return nom_exiftool.endswith(":BWF_UMID") and not str(valeur).strip("0")


def trouver(lues: dict[str, Any], cles: tuple[str, ...], sienne: Any) -> str | None:
    """Premier nom observé parmi ``cles`` dont la valeur concorde, sinon le premier observé."""
    noms = [
        nom
        for cle in cles
        for nom in lues
        if (nom.startswith("xmp.") and nom.endswith(cle) if cle.startswith(":") else nom == cle)
    ]
    return next((n for n in noms if concordent(lues[n], sienne)), noms[0] if noms else None)


@pytest.mark.parametrize("fichier", [entree["SourceFile"] for entree in ORACLE])
def test_les_modules_relevent_ce_que_releve_exiftool(fichier: str) -> None:
    lues = lu_par_les_modules(fichier)
    retrouvees: set[str] = set()
    for nom_exiftool, entree in lu_par_exiftool(fichier).items():
        cles = attendus(nom_exiftool, entree)
        sienne = entree["val"]
        if not cles or vide(nom_exiftool, sienne):
            continue
        if nom_exiftool.startswith("RIFF:") and isinstance(sienne, str):
            sienne = en_utf8(sienne)
        nom = trouver(lues, cles, sienne)
        assert nom is not None, f"{fichier} : {nom_exiftool} non relevé"
        assert concordent(lues[nom], sienne), (fichier, nom_exiftool, lues[nom])
        retrouvees.add(nom)
    # Dans l'autre sens : rien de relevé qu'exiftool ne connaisse.
    assert set(lues) == retrouvees, f"{fichier} : {sorted(set(lues) - retrouvees)}"


def test_oracle_couvre_les_formats_et_familles() -> None:
    assert sorted(FORMATS[Path(e["SourceFile"]).suffix] for e in ORACLE) == [
        "aac",
        "flac",
        "heic",
        "jpeg",
        "m4a",
        "mov",
        "mp3",
        "mp4",
        "ogg",
        "ogg",
        "pdf",
        "pdf",
        "png",
        "wav",
        "webm",
        "webp",
    ]
    groupes = {cle.partition(":")[0] for entree in ORACLE for cle in entree}
    assert {"IFD0", "ExifIFD", "GPS", "IPTC", "XMP-dc", "PNG", "PDF", "XMP-pdf"} <= groupes
    medias = {"ID3v2_4", "ID3v1", "RIFF", "Vorbis", "ItemList", "UserData", "Keys", "Matroska"}
    assert medias <= groupes


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
    # Même commande que relire.sh.
    commande = ["exiftool", "-j", "-a", "-G1:4", "-n", "-D", "-struct"]
    commande += ["-x", "System:all", "-x", "File:all", "-x", "Composite:all"]
    commande += [entree["SourceFile"] for entree in ORACLE]
    sortie = subprocess.run(commande, capture_output=True, check=True, cwd=DOSSIER)
    assert json.loads(sortie.stdout) == ORACLE
