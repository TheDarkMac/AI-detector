"""Protocole entre le processus principal et le processus de travail (ADR-0036, ADR-0065).

Lignes JSON, une par message, dans les deux processus. Ce module n'importe que la bibliothèque
standard : le processus de travail s'en sert sans charger ``jsonschema``.

Les tailles sont **provisoires** : T14 fixe les limites (ES-03).
"""

import json
import math
from collections.abc import Mapping
from typing import Any, NoReturn

__all__ = [
    "TAILLE_MAX_CONFIGURATION",
    "TAILLE_MAX_LECTURE",
    "TAILLE_MAX_MESSAGE",
    "TAILLE_MAX_SORTIE",
    "MessageInvalide",
    "decoder",
    "encoder",
]

TAILLE_MAX_MESSAGE = 1 << 20
"""Taille maximale d'une ligne envoyée par le processus de travail, saut de ligne compris."""
TAILLE_MAX_SORTIE = 64 << 20
"""Taille maximale de l'ensemble des messages d'une analyse."""
TAILLE_MAX_CONFIGURATION = 16 << 20
"""Taille maximale de la configuration envoyée par le processus principal."""
TAILLE_MAX_LECTURE = 16 << 20
"""Taille maximale d'une lecture du fichier par un module."""


class MessageInvalide(ValueError):
    """Ligne qui n'est pas un objet JSON strict. Le message ne cite jamais la ligne reçue."""


def encoder(message: Mapping[str, Any]) -> bytes:
    """Une ligne JSON en UTF-8, terminée par un saut de ligne ; aucun NaN ni infini."""
    texte = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return texte.encode("utf-8") + b"\n"


def _refuser_constante(_constante: str) -> NoReturn:
    raise MessageInvalide("message : NaN ou infini")


def _reel_fini(texte: str) -> float:
    valeur = float(texte)
    if not math.isfinite(valeur):  # 1e400 donne un infini sans passer par parse_constant
        raise MessageInvalide("message : nombre hors des réels finis")
    return valeur


def _sans_doublon(paires: list[tuple[str, Any]]) -> dict[str, Any]:
    objet = dict(paires)
    if len(objet) != len(paires):
        raise MessageInvalide("message : clé en double")
    return objet


def decoder(ligne: bytes) -> dict[str, Any]:
    """Décode une ligne en objet JSON, strictement (modèle de données, §7).

    Refusés : UTF-8 invalide, NaN et infinis, clés en double, tout ce qui n'est pas un objet.
    """
    try:
        document = json.loads(
            ligne.decode("utf-8"),
            parse_constant=_refuser_constante,
            parse_float=_reel_fini,
            object_pairs_hook=_sans_doublon,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise MessageInvalide("message : JSON invalide") from None
    if not isinstance(document, dict):
        raise MessageInvalide("message : objet JSON attendu")
    return document
