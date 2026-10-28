"""Comparaison de deux rapports d'un même fichier : reproductibilité (NF-06, T18).

Deux analyses du même fichier, dans les conditions de la garantie (ADR-0023) : mêmes versions
de l'outil, de l'interpréteur, du catalogue et des dépendances, même extension, aucune analyse
interrompue, doivent donner le même rapport, à la date et au nom du fichier près (ADR-0108).
:func:`comparer` relève chaque écart entre deux exports JSON et le classe (ADR-0112) :

- **condition** : une condition de la garantie diffère ; les résultats peuvent alors différer ;
- **environnement** : l'isolation obtenue, propre au poste ; elle ne doit changer aucun résultat ;
- **résultat** : tout le reste ; un écart de résultat dans la garantie est un défaut.

Les données masquées dans l'un des deux exports ne sont comparées dans aucun des deux : un
écart ne révèle ainsi aucune donnée masquée. Un écart ne porte que son chemin dans le document,
jamais les valeurs comparées, qui peuvent être identifiantes (ES-14).

Ce module n'importe pas ``jsonschema`` : seule :func:`lire`, qui valide un fichier, le charge.
"""

import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from voight_kampff._protocole import MessageInvalide, decoder
from voight_kampff.rapport.modele import CategorieIdentifiante, verifier_masquage

__all__ = [
    "TAILLE_MAX_RAPPORT",
    "Comparaison",
    "Ecart",
    "Nature",
    "RapportIllisible",
    "comparer",
    "lire",
]

TAILLE_MAX_RAPPORT = 256 << 20
"""Taille maximale d'un export relu : quatre fois ce que les messages d'une analyse portent au
plus (``TAILLE_MAX_SORTIE``), pour l'indentation et l'échappement de l'export."""


class Nature(StrEnum):
    """Nature d'un écart entre deux rapports (ADR-0112)."""

    CONDITION = "condition"
    ENVIRONNEMENT = "environnement"
    RESULTAT = "resultat"


type Chemin = tuple[str | int, ...]

# Hors comparaison : la date change à chaque analyse ; le nom n'est pas le contenu du fichier,
# et l'extension qui en est tirée est comparée comme une condition ; le masquage est traité à
# part.
_IGNORES: frozenset[Chemin] = frozenset(
    {("identification", "date_analyse"), ("identification", "nom"), ("masquage",)}
)
_CONDITIONS: tuple[Chemin, ...] = (
    ("identification", "empreinte"),
    ("identification", "extension"),
    ("versions",),
    ("interrompue",),
)
_ENVIRONNEMENT: tuple[Chemin, ...] = (("isolation",),)


@dataclass(frozen=True, slots=True)
class Ecart:
    """Un champ qui diffère, ou qui n'existe que dans l'un des deux rapports."""

    chemin: str
    """Chemin du champ dans le document, par exemple ``constats[0].phrase.parametres``."""
    nature: Nature


@dataclass(frozen=True, slots=True)
class Comparaison:
    """Écarts entre deux rapports, et ce qu'ils disent de la garantie (ADR-0023, ADR-0112)."""

    ecarts: tuple[Ecart, ...]
    interrompue: bool
    """Au moins une des deux analyses est interrompue : hors garantie (NF-08)."""
    non_comparees: tuple[CategorieIdentifiante, ...]
    """Catégories masquées dans au moins un des deux exports, nom du fichier excepté, qui n'est
    jamais comparé : leurs données ne le sont pas non plus."""

    def nature(self, nature: Nature) -> tuple[Ecart, ...]:
        return tuple(ecart for ecart in self.ecarts if ecart.nature is nature)

    @property
    def meme_fichier(self) -> bool:
        """Même fichier établi : empreintes comparées, donc levées dans les deux exports."""
        return CategorieIdentifiante.EMPREINTE not in self.non_comparees

    @property
    def garantie(self) -> bool:
        """Les deux analyses sont dans les conditions de la garantie de reproductibilité."""
        return self.meme_fichier and not self.interrompue and not self.nature(Nature.CONDITION)

    @property
    def identiques(self) -> bool:
        """Aucun écart de résultat."""
        return not self.nature(Nature.RESULTAT)

    @property
    def defaut(self) -> bool:
        """Résultats différents dans les conditions de la garantie : défaut de l'outil."""
        return self.garantie and not self.identiques


class RapportIllisible(ValueError):
    """Fichier qui n'est pas un export JSON valide. Le message ne cite jamais son contenu."""


def lire(chemin: str | os.PathLike[str]) -> dict[str, Any]:
    """Lit et valide un export JSON (ADR-0095) ; lève :class:`RapportIllisible`."""
    from voight_kampff.rapport import export  # jsonschema : seulement à l'appel

    try:
        with open(chemin, "rb") as fichier:
            contenu = fichier.read(TAILLE_MAX_RAPPORT + 1)
    except OSError as erreur:
        raise RapportIllisible(f"fichier illisible ({erreur.strerror})") from None
    if len(contenu) > TAILLE_MAX_RAPPORT:
        raise RapportIllisible(f"plus de {TAILLE_MAX_RAPPORT >> 20} Mio : pas un rapport")
    try:
        document = decoder(contenu)
    except MessageInvalide:
        raise RapportIllisible("pas un objet JSON strict") from None
    try:
        export.valider(document)
    except ValueError as erreur:  # DocumentInvalide en est une
        raise RapportIllisible(f"pas un rapport de cette version de l'outil : {erreur}") from None
    return document


def comparer(a: Mapping[str, Any], b: Mapping[str, Any]) -> Comparaison:
    """Compare deux exports JSON déjà validés, à la date et au nom du fichier près."""
    caches = _masquees(a) | _masquees(b)
    gauche, droite = _sans_masquees(a, caches), _sans_masquees(b, caches)
    return Comparaison(
        ecarts=tuple(
            Ecart(_texte(chemin), _nature(chemin)) for chemin in _ecarts(gauche, droite, ())
        ),
        interrompue=bool(a["interrompue"] or b["interrompue"]),
        non_comparees=tuple(
            categorie
            for categorie in CategorieIdentifiante
            if categorie in caches and categorie is not CategorieIdentifiante.NOM_DE_FICHIER
        ),
    )


def _masquees(document: Mapping[str, Any]) -> frozenset[CategorieIdentifiante]:
    masquage = document.get("masquage")
    return frozenset() if masquage is None else verifier_masquage(masquage)


def _sans_masquees(
    document: Mapping[str, Any], caches: frozenset[CategorieIdentifiante]
) -> dict[str, Any]:
    """Copie du document sans les données d'aucune catégorie de ``caches`` (ADR-0095)."""
    copie = dict(document)
    identification = dict(copie["identification"])
    if CategorieIdentifiante.EMPREINTE in caches:
        identification.pop("empreinte", None)
    copie["identification"] = identification
    observations = []
    for observation in copie["observations"]:
        if observation.get("identifiante") in caches:
            observation = {cle: v for cle, v in observation.items() if cle != "valeur"}
        observations.append(observation)
    copie["observations"] = observations
    return copie


_ABSENT = object()
"""Valeur d'un champ qui n'existe que dans l'un des deux documents."""


def _ecarts(a: Any, b: Any, chemin: Chemin) -> Iterator[Chemin]:
    if chemin in _IGNORES:
        return
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        for cle in [*a, *(cle for cle in b if cle not in a)]:
            yield from _ecarts(a.get(cle, _ABSENT), b.get(cle, _ABSENT), (*chemin, cle))
    elif isinstance(a, list) and isinstance(b, list):
        for rang in range(max(len(a), len(b))):
            gauche = a[rang] if rang < len(a) else _ABSENT
            droite = b[rang] if rang < len(b) else _ABSENT
            yield from _ecarts(gauche, droite, (*chemin, rang))
    elif a is _ABSENT or b is _ABSENT or _scalaire(a) != _scalaire(b):
        yield chemin


def _scalaire(valeur: Any) -> tuple[type, Any]:
    """Valeur et type JSON : 1, 1.0 et true sont égaux en Python, pas dans un rapport. Une
    énumération du modèle vaut la chaîne qu'elle devient en JSON."""
    for nature in (bool, int, float, str):
        if isinstance(valeur, nature):
            return nature, nature(valeur)
    return type(valeur), valeur


def _nature(chemin: Chemin) -> Nature:
    if any(chemin[: len(prefixe)] == prefixe for prefixe in _CONDITIONS):
        return Nature.CONDITION
    if any(chemin[: len(prefixe)] == prefixe for prefixe in _ENVIRONNEMENT):
        return Nature.ENVIRONNEMENT
    return Nature.RESULTAT


def _texte(chemin: Chemin) -> str:
    texte = ""
    for element in chemin:
        texte += f"[{element}]" if isinstance(element, int) else f".{element}" if texte else element
    return texte
