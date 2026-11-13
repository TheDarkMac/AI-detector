"""Propriétés d'un document bureautique : valeurs tirées du XML, puis observées (ADR-0140).

Commun aux modules ``ooxml`` et ``odf``. Une propriété est rangée sous son nom ; écrite plusieurs
fois, elle devient une liste, dans l'ordre du document. Un texte vide n'est pas observé. Les
valeurs que le schéma type (entier, booléen, réel de XML Schema) sont lues dans ce type ; une
écriture que le type n'admet pas reste un texte, telle qu'écrite (ADR-0118).

Les espaces de noms inconnus prennent ``ns1``, ``ns2``… dans l'ordre de première apparition,
et leur adresse est observée sous ``<famille>.espace.ns<k>``, comme pour XMP (ADR-0117).
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.rapport.modele import CategorieIdentifiante, Localisation, Scalaire

__all__ = ["Proprietes", "booleen", "entier", "reel"]

_ENTIER = re.compile(r"[+-]?[0-9]+")
_REEL = re.compile(r"[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?|[+-]?INF|NaN")


def entier(texte: str) -> Scalaire:
    """Entier de XML Schema (espaces autour admis), sinon le texte tel qu'écrit."""
    nettoye = texte.strip()
    return valeurs.entier(int(nettoye)) if _ENTIER.fullmatch(nettoye) else texte


def booleen(texte: str) -> Scalaire:
    """Booléen de XML Schema : ``true``, ``false``, ``1``, ``0`` ; sinon le texte."""
    nettoye = texte.strip()
    if nettoye in ("true", "1"):
        return True
    if nettoye in ("false", "0"):
        return False
    return texte


def reel(texte: str) -> Scalaire:
    """Réel de XML Schema (``1.5``, ``-2E3``, ``INF``, ``NaN``), sinon le texte."""
    nettoye = texte.strip()
    if not _REEL.fullmatch(nettoye):
        return texte
    return valeurs.nombre(float(nettoye.replace("INF", "inf")))


@dataclass(slots=True)
class _Propriete:
    valeurs: list[Scalaire]
    tableau: bool
    localisation: Localisation
    identifiante: CategorieIdentifiante | None


@dataclass(slots=True)
class Proprietes:
    """Propriétés relevées, par nom, dans l'ordre de leur première apparition."""

    famille: str
    connus: Mapping[str, str]
    """Préfixe usuel de chaque espace de noms connu de la famille."""
    _proprietes: dict[str, _Propriete] = field(default_factory=dict)
    _tailles: list[tuple[str, int, Localisation, CategorieIdentifiante | None]] = field(
        default_factory=list
    )
    _inconnus: dict[str, tuple[str, Localisation]] = field(default_factory=dict)

    def prefixe(self, espace: str, localisation: Localisation) -> str:
        """Préfixe d'un espace : usuel s'il est connu, ``ns<k>`` sinon."""
        connu = self.connus.get(espace)
        if connu is not None:
            return connu
        prefixe = f"ns{len(self._inconnus) + 1}"
        return self._inconnus.setdefault(espace, (prefixe, localisation))[0]

    def composant(self, espace: str, nom: str, localisation: Localisation) -> str:
        """``préfixe:nom`` d'un élément ou d'un attribut, nom passé par la règle des composants."""
        return f"{self.prefixe(espace, localisation)}:{valeurs.composant(nom)}"

    def ajouter(
        self,
        nom: str,
        valeur: Scalaire | list[Scalaire],
        localisation: Localisation,
        identifiante: CategorieIdentifiante | None = None,
    ) -> None:
        """Ajoute une valeur, ou les éléments d'une liste ; un texte vide est ignoré."""
        elements = valeur if isinstance(valeur, list) else [valeur]
        elements = [e for e in elements if e != ""]
        if not elements:
            return
        nom = valeurs.borner(f"{self.famille}.{nom}")
        propriete = self._proprietes.setdefault(
            nom, _Propriete([], isinstance(valeur, list), localisation, identifiante)
        )
        propriete.valeurs.extend(elements)

    def taille(
        self,
        nom: str,
        octets: int,
        localisation: Localisation,
        identifiante: CategorieIdentifiante | None = None,
    ) -> None:
        """Donnée binaire, observée par sa taille (ADR-0118)."""
        nom = valeurs.borner(f"{self.famille}.{nom}")
        self._tailles.append((f"{nom}.taille", octets, localisation, identifiante))

    def observer(self, contexte: Contexte) -> None:
        for nom, propriete in self._proprietes.items():
            liste = propriete.tableau or len(propriete.valeurs) > 1
            valeurs.observer(
                contexte,
                nom,
                propriete.valeurs if liste else propriete.valeurs[0],
                localisation=propriete.localisation,
                identifiante=propriete.identifiante,
            )
        for nom, octets, localisation, identifiante in self._tailles:
            valeurs.observer(
                contexte,
                nom,
                octets,
                unite="octets",
                localisation=localisation,
                identifiante=identifiante,
            )
        for adresse, (prefixe, localisation) in self._inconnus.items():
            valeurs.observer(
                contexte, f"{self.famille}.espace.{prefixe}", adresse, localisation=localisation
            )
