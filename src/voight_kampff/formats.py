"""Vocabulaire des formats et extensions attendues (F-01 à F-03, ADR-0012, ADR-0070).

Commun aux deux processus et au modèle : rien ici ne lit de fichier. Les formats du
périmètre sont ceux du §3 du cahier, tous acceptés en V1 ; les autres sont reconnus pour être
nommés dans un refus ou dans un fichier polyglotte, jamais analysés (ADR-0071).
"""

from collections.abc import Mapping
from pathlib import PurePosixPath
from types import MappingProxyType

__all__ = [
    "EXTENSIONS",
    "FORMATS",
    "HORS_PERIMETRE",
    "LONGUEUR_MAX_EXTENSION",
    "PERIMETRE",
    "concordante",
    "extension",
]

PERIMETRE = frozenset(
    {
        # Image
        "jpeg",
        "png",
        "webp",
        "heic",
        # Audio
        "wav",
        "mp3",
        "aac",
        "m4a",
        "flac",
        "ogg",
        # Vidéo
        "mp4",
        "mov",
        "webm",
        # Document
        "pdf",
        # Texte
        "texte",
        "docx",
        "odt",
    }
)
"""Formats analysés ; ce sont les seuls que le manifeste d'un module peut citer."""

HORS_PERIMETRE = frozenset(
    {
        "gif",
        "bmp",
        "tiff",
        "avif",
        "heif",
        "avi",
        "matroska",
        "3gp",
        "zip",
        "gzip",
        "7z",
        "rar",
        "exe",
        "elf",
    }
)
"""Formats reconnus mais hors périmètre : nommés dans le refus ou la partie non analysée."""

FORMATS = PERIMETRE | HORS_PERIMETRE

EXTENSIONS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "jpeg": frozenset({"jpg", "jpeg", "jpe", "jfif"}),
        "png": frozenset({"png"}),
        "webp": frozenset({"webp"}),
        "heic": frozenset({"heic", "heif", "hif"}),
        "wav": frozenset({"wav", "wave"}),
        "mp3": frozenset({"mp3"}),
        "aac": frozenset({"aac", "adts"}),
        "m4a": frozenset({"m4a", "m4b"}),
        "flac": frozenset({"flac"}),
        "ogg": frozenset({"ogg", "oga", "ogv", "opus", "spx"}),
        "mp4": frozenset({"mp4", "m4v"}),
        "mov": frozenset({"mov", "qt"}),
        "webm": frozenset({"webm"}),
        "pdf": frozenset({"pdf"}),
        "texte": frozenset({"txt", "text", "md", "csv", "tsv", "log"}),
        "docx": frozenset({"docx"}),
        "odt": frozenset({"odt"}),
        "gif": frozenset({"gif"}),
        "bmp": frozenset({"bmp", "dib"}),
        "tiff": frozenset({"tif", "tiff"}),
        "avif": frozenset({"avif"}),
        "heif": frozenset({"heif", "heifs", "hif"}),
        "avi": frozenset({"avi"}),
        "matroska": frozenset({"mkv", "mka", "mks", "mk3d"}),
        "3gp": frozenset({"3gp", "3g2"}),
        "zip": frozenset({"zip"}),
        "gzip": frozenset({"gz", "tgz"}),
        "7z": frozenset({"7z"}),
        "rar": frozenset({"rar"}),
        "exe": frozenset({"exe", "dll"}),
        "elf": frozenset({"elf", "so", "o"}),
    }
)
"""Extensions usuelles de chaque format, en minuscules et sans point."""

LONGUEUR_MAX_EXTENSION = 32
"""Au-delà, la fin du nom n'est pas tenue pour une extension."""


def extension(nom: str) -> str | None:
    """Extension du nom de fichier, en minuscules et sans point ; ``None`` s'il n'en a pas.

    Un nom qui commence par un point (``.profil``) n'a pas d'extension.
    """
    suffixe = PurePosixPath(nom).suffix[1:].lower()
    if not suffixe or len(suffixe) > LONGUEUR_MAX_EXTENSION:
        return None
    return suffixe


def concordante(extension_du_nom: str, format_reel: str) -> bool:
    """Vrai si l'extension est l'une de celles du format réel (F-03)."""
    return extension_du_nom in EXTENSIONS.get(format_reel, frozenset())
