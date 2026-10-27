"""Manifestes des modules : lecture, validation, ordre, désactivation (ADR-0042, ADR-0064).

Les manifestes sont lus et validés sans importer le code des modules. Ils sont livrés avec
l'outil : un manifeste invalide est un défaut de l'outil, qui arrête l'analyse avec un message
explicite, comme un catalogue invalide (ADR-0029). La liste des techniques hors de cette version
est lue de la même façon, à côté d'eux (ADR-0087).
"""

import tomllib
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Literal

from voight_kampff import modules, schemas
from voight_kampff.modules import MANIFESTE, dossiers
from voight_kampff.rapport.modele import Direction

__all__ = [
    "Manifeste",
    "ManifesteInvalide",
    "ModuleInconnu",
    "TechniqueHorsV1",
    "decouvrir",
    "hors_v1",
    "lire",
    "selectionner",
]


class ManifesteInvalide(ValueError):
    """Manifeste d'un module livré illisible, non conforme ou incohérent avec les autres."""


class ModuleInconnu(ValueError):
    """Module à désactiver absent de cette version de l'outil."""


@dataclass(frozen=True, slots=True)
class Manifeste:
    """Ce que le processus principal sait d'un module sans importer son code."""

    identifiant: str
    """Nom du dossier du module, donc nom d'import."""
    version: str
    formats: tuple[str, ...]
    """Formats réels traités ; le module n'est appliqué qu'à ceux-là (T13)."""
    exigences: tuple[str, ...]
    regles: tuple[str, ...]
    """Règles du catalogue employées ; leur existence est vérifiée avec le catalogue (T15)."""
    fiche: str
    """Fiche technique ``docs/techniques/<fiche>.md`` (NF-09)."""
    directions: tuple[Direction, ...]
    """Directions permises par la fiche technique (ADR-0022)."""
    requiert: tuple[str, ...] = ()
    """Modules exécutés avant celui-ci, dans le même processus de travail."""


@dataclass(frozen=True, slots=True)
class TechniqueHorsV1:
    """Technique hors de cette version de l'outil, inscrite non menée à la couverture."""

    identifiant: str
    tache: str
    exigences: tuple[str, ...]
    statut: Literal["candidate_v2", "sans_engagement"]
    """Statut fixé par ADR-0012."""
    formats: tuple[str, ...]
    """Formats où elle s'appliquerait : une entrée de couverture par partie de ces formats."""


def lire(dossier: Traversable) -> Manifeste:
    """Lit et valide le manifeste d'un dossier de module."""
    nom = dossier.name
    try:
        document = tomllib.loads((dossier / MANIFESTE).read_text(encoding="utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise ManifesteInvalide(f"module {nom} : manifeste illisible") from None
    try:
        schemas.valider("manifeste", document)
    except schemas.DocumentInvalide as erreur:
        raise ManifesteInvalide(f"module {nom} : {erreur}") from None
    if document["identifiant"] != nom:
        raise ManifesteInvalide(f"module {nom} : l'identifiant doit être le nom du dossier")
    return Manifeste(
        identifiant=document["identifiant"],
        version=document["version"],
        formats=tuple(document["formats"]),
        exigences=tuple(document["exigences"]),
        regles=tuple(document["regles"]),
        fiche=document["fiche"],
        directions=tuple(Direction(direction) for direction in document["directions"]),
        requiert=tuple(document["requiert"]),
    )


def decouvrir(racine: Traversable | None = None) -> tuple[Manifeste, ...]:
    """Manifestes des modules livrés, dans l'ordre d'exécution.

    Un module vient après ceux qu'il requiert ; à rang égal, l'ordre est celui des
    identifiants, pour que deux analyses exécutent les modules dans le même ordre (NF-06).
    """
    manifestes = {manifeste.identifiant: manifeste for manifeste in map(lire, dossiers(racine))}
    for manifeste in manifestes.values():
        for requis in manifeste.requiert:
            if requis == manifeste.identifiant or requis not in manifestes:
                raise ManifesteInvalide(
                    f"module {manifeste.identifiant} : module requis absent ou lui-même"
                )
    return _ordonner(manifestes)


def hors_v1(
    livres: Iterable[Manifeste], racine: Traversable | None = None
) -> tuple[TechniqueHorsV1, ...]:
    """Techniques hors de cette version (ADR-0087), dans l'ordre du fichier.

    Une technique hors V1 ne peut pas porter l'identifiant d'un module livré : le rapport
    dirait à la fois qu'elle est menée et qu'elle ne l'est pas.
    """
    racine = files(modules.__name__) if racine is None else racine
    try:
        document = tomllib.loads((racine / modules.HORS_V1).read_text(encoding="utf-8"))
        schemas.valider("hors_v1", document)
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, schemas.DocumentInvalide) as erreur:
        detail = erreur if isinstance(erreur, schemas.DocumentInvalide) else "fichier illisible"
        raise ManifesteInvalide(f"{modules.HORS_V1} : {detail}") from None
    techniques = tuple(
        TechniqueHorsV1(
            identifiant=technique["identifiant"],
            tache=technique["tache"],
            exigences=tuple(technique["exigences"]),
            statut=technique["statut"],
            formats=tuple(technique["formats"]),
        )
        for technique in document["technique"]
    )
    identifiants = [technique.identifiant for technique in techniques]
    if len(set(identifiants)) != len(identifiants):
        raise ManifesteInvalide(f"{modules.HORS_V1} : technique inscrite deux fois")
    livrees = sorted(set(identifiants) & {manifeste.identifiant for manifeste in livres})
    if livrees:
        raise ManifesteInvalide(f"{modules.HORS_V1} : module livré inscrit hors V1 : {livrees[0]}")
    return techniques


def _ordonner(manifestes: dict[str, Manifeste]) -> tuple[Manifeste, ...]:
    restants = {identifiant: set(m.requiert) for identifiant, m in manifestes.items()}
    ordre: list[Manifeste] = []
    while restants:
        prets = sorted(identifiant for identifiant, requis in restants.items() if not requis)
        if not prets:
            cycle = ", ".join(sorted(restants))
            raise ManifesteInvalide(f"modules {cycle} : dépendance circulaire")
        for identifiant in prets:
            ordre.append(manifestes[identifiant])
            del restants[identifiant]
        for requis in restants.values():
            requis.difference_update(prets)
    return tuple(ordre)


def selectionner(
    manifestes: Iterable[Manifeste], desactives: Collection[str]
) -> tuple[tuple[Manifeste, ...], tuple[Manifeste, ...]]:
    """Sépare les modules actifs des modules désactivés par l'utilisateur, ordre conservé.

    Un module qui en requiert un désactivé est désactivé lui aussi : il ne pourrait pas
    s'exécuter. ``manifestes`` doit être dans l'ordre d'exécution (:func:`decouvrir`).
    """
    manifestes = tuple(manifestes)
    connus = {manifeste.identifiant for manifeste in manifestes}
    inconnus = sorted(set(desactives) - connus)
    if inconnus:
        raise ModuleInconnu(f"module inconnu : {', '.join(inconnus)}")
    eteints = set(desactives)
    for manifeste in manifestes:
        if eteints.intersection(manifeste.requiert):
            eteints.add(manifeste.identifiant)
    actifs = tuple(m for m in manifestes if m.identifiant not in eteints)
    return actifs, tuple(m for m in manifestes if m.identifiant in eteints)
