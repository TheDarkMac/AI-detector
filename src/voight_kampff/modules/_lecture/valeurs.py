"""Valeurs tirées du fichier, ramenées à ce qu'une observation admet (ADR-0118).

Un texte garde au plus 4 096 caractères ; une liste, au plus 4 096 éléments et 32 768 caractères
en tout. Au-delà, l'observation garde le début, et une observation ``<nom>.longueur`` dit la
longueur entière : en caractères pour un texte, en éléments pour une liste. Un nombre réel non
fini ou hors des bornes du modèle est rendu en texte.
"""

import math
from collections.abc import Sequence

from voight_kampff._travail.contexte import Contexte
from voight_kampff.rapport.modele import (
    LONGUEUR_MAX_IDENTIFIANT,
    LONGUEUR_MAX_TEXTE,
    NOMBRE_MAX_ELEMENTS,
    CategorieIdentifiante,
    Localisation,
    Scalaire,
)

__all__ = ["CARACTERES_MAX_LISTE", "borner", "composant", "nombre", "observer"]

CARACTERES_MAX_LISTE = 32768
"""Caractères d'une liste, tous éléments compris : une observation tient dans une ligne."""

_BORNE = 2.0**63
_SUFFIXE = ".longueur"


_PERMIS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-")


def composant(texte: str) -> str:
    """Partie d'un nom d'observation tirée du fichier : tout autre caractère devient ``-``.

    Le point, qui sépare les parties d'un nom, en fait partie (ADR-0117).
    """
    return "".join(c if c in _PERMIS else "-" for c in texte)


def borner(nom: str) -> str:
    """Nom d'observation coupé pour que ``<nom>.longueur`` reste un identifiant valide."""
    return nom[: LONGUEUR_MAX_IDENTIFIANT - len(_SUFFIXE)]


def nombre(valeur: float) -> Scalaire:
    """Réel, ou son écriture si le modèle ne l'admet pas comme nombre."""
    if math.isfinite(valeur) and -_BORNE < valeur < _BORNE:
        return valeur
    return repr(valeur)


def observer(
    contexte: Contexte,
    nom: str,
    valeur: Scalaire | Sequence[Scalaire],
    *,
    localisation: Localisation | None = None,
    identifiante: CategorieIdentifiante | None = None,
    unite: str | None = None,
    total: int | None = None,
) -> None:
    """Observe une valeur, coupée au besoin, et sa longueur entière si elle l'a été.

    ``total`` donne le nombre d'éléments d'une liste dont seul le début a été lu.
    """
    if isinstance(valeur, str):
        if len(valeur) > LONGUEUR_MAX_TEXTE:
            contexte.observer(
                nom,
                valeur[:LONGUEUR_MAX_TEXTE],
                localisation=localisation,
                identifiante=identifiante,
            )
            _longueur(contexte, nom, len(valeur), "caractères", localisation)
            return
        contexte.observer(
            nom, valeur, unite=unite, localisation=localisation, identifiante=identifiante
        )
        return
    if isinstance(valeur, int | float | bool):
        contexte.observer(
            nom, valeur, unite=unite, localisation=localisation, identifiante=identifiante
        )
        return
    gardes: list[Scalaire] = []
    caracteres = 0
    coupee = False
    for element in valeur:
        if isinstance(element, str):
            if len(element) > LONGUEUR_MAX_TEXTE:
                element, coupee = element[:LONGUEUR_MAX_TEXTE], True
            caracteres += len(element)
        if len(gardes) == NOMBRE_MAX_ELEMENTS or caracteres > CARACTERES_MAX_LISTE:
            coupee = True
            break
        gardes.append(element)
    contexte.observer(
        nom, gardes, unite=unite, localisation=localisation, identifiante=identifiante
    )
    total = len(valeur) if total is None else total
    if coupee or total > len(gardes):
        _longueur(contexte, nom, total, "éléments", localisation)


def _longueur(
    contexte: Contexte, nom: str, longueur: int, unite: str, localisation: Localisation | None
) -> None:
    contexte.observer(f"{nom}{_SUFFIXE}", longueur, unite=unite, localisation=localisation)
