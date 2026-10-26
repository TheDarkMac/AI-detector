"""Manifestes des modules : lecture, validation, ordre, désactivation (ADR-0042, ADR-0064).

Les manifestes sont lus et validés sans importer le code des modules. Ils sont livrés avec
l'outil : un manifeste invalide est un défaut de l'outil, qui arrête l'analyse avec un message
explicite, comme un catalogue invalide (ADR-0029).
"""

import tomllib
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from importlib.resources.abc import Traversable

from voight_kampff import schemas
from voight_kampff.modules import MANIFESTE, dossiers
from voight_kampff.rapport.modele import Direction

__all__ = ["Manifeste", "ManifesteInvalide", "ModuleInconnu", "decouvrir", "lire", "selectionner"]


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
