"""Marquages du catalogue : ce que l'outil recherche, et ce qu'il ne recherche pas (F-24, F-25).

Un marquage est un signal lisible par machine, posé exprès pour dire l'origine d'un contenu :
manifeste C2PA, déclaration IPTC, filigrane invisible (ADR-0176). Le catalogue inscrit chacun,
avec le module qui le recherche, ou la raison pour laquelle aucun ne le recherche (ADR-0175,
ADR-0177). Pour un fichier, :func:`couvrir` en tire la couverture : un marquage qui pourrait se
trouver dans l'une de ses parties analysées y est recherché, ou non recherché avec sa raison
(ADR-0178).

Ce module n'importe que la bibliothèque standard et le modèle du rapport.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any

from voight_kampff.rapport.modele import (
    EtatTechnique,
    MarquageNonRecherche,
    Partie,
    RaisonNonRecherche,
    TechniqueCouverte,
)

__all__ = ["RAISONS_DU_CATALOGUE", "Marquage", "Nature", "couvrir"]

RAISONS_DU_CATALOGUE = frozenset(RaisonNonRecherche) - {RaisonNonRecherche.TECHNIQUE_NON_MENEE}
"""Raisons qu'une entrée du catalogue peut porter ; la dernière n'est constatée qu'à l'analyse."""

_RECHERCHE: frozenset[EtatTechnique | None] = frozenset(
    {EtatTechnique.APPLIQUEE, EtatTechnique.PARTIELLE}
)


class Nature(StrEnum):
    """Nature d'un marquage (ADR-0175)."""

    MANIFESTE = "manifeste"
    DECLARATION = "declaration"
    FILIGRANE = "filigrane"


@dataclass(frozen=True, slots=True)
class Marquage:
    """Entrée du catalogue : un marquage connu, recherché par ``module`` ou non pour ``raison``."""

    identifiant: str
    nom: str
    nature: Nature
    description: str
    formats: tuple[str, ...]
    """Formats où il peut se trouver : il ne figure qu'à la couverture d'un fichier qui en a."""
    references: tuple[str, ...]
    verifie: date
    """Date à laquelle l'inventaire a vérifié l'entrée (ERR-0002)."""
    module: str | None = None
    raison: RaisonNonRecherche | None = None

    def __post_init__(self) -> None:
        if (self.module is None) == (self.raison is None):
            raise ValueError("un module ou une raison, l'un des deux seulement")
        if self.raison is not None and self.raison not in RAISONS_DU_CATALOGUE:
            raise ValueError("raison constatée à l'analyse, pas inscrite au catalogue")

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Marquage":
        """Entrée d'un fichier ``marquages.toml`` déjà validé par son schéma."""
        raison = document.get("raison")
        return cls(
            identifiant=document["identifiant"],
            nom=document["nom"],
            nature=Nature(document["nature"]),
            description=document["description"],
            formats=tuple(document["formats"]),
            references=tuple(document["references"]),
            verifie=date.fromisoformat(document["verifie"]),
            module=document.get("module"),
            raison=None if raison is None else RaisonNonRecherche(raison),
        )


def couvrir(
    marquages: Iterable[Marquage],
    parties: Iterable[Partie],
    techniques: Iterable[TechniqueCouverte],
) -> tuple[tuple[str, ...], tuple[MarquageNonRecherche, ...]]:
    """Marquages recherchés et non recherchés dans un fichier, dans l'ordre des identifiants.

    Seuls comptent les marquages qui pourraient se trouver dans une partie analysée : les autres
    ne disent rien de ce fichier. Un marquage est recherché si son module a été appliqué, même
    en partie, à l'une de ces parties ; sinon il n'est pas recherché, pour la raison du
    catalogue, ou parce que son module n'y a pas été appliqué (ADR-0178).
    """
    formats = {partie.rang: partie.format for partie in parties if partie.dans_perimetre}
    etats = {(technique.module, technique.partie): technique.etat for technique in techniques}
    recherches: list[str] = []
    non_recherches: list[MarquageNonRecherche] = []
    for marquage in sorted(marquages, key=lambda marquage: marquage.identifiant):
        rangs = [rang for rang, format_ in formats.items() if format_ in marquage.formats]
        if not rangs:
            continue
        module = marquage.module
        if marquage.raison is not None or module is None:  # l'un ou l'autre, jamais les deux
            raison = marquage.raison or RaisonNonRecherche.TECHNIQUE_NON_MENEE
            non_recherches.append(MarquageNonRecherche(marquage.identifiant, raison))
        elif any(etats.get((module, rang)) in _RECHERCHE for rang in rangs):
            recherches.append(marquage.identifiant)
        else:
            non_recherches.append(
                MarquageNonRecherche(marquage.identifiant, RaisonNonRecherche.TECHNIQUE_NON_MENEE)
            )
    return tuple(recherches), tuple(non_recherches)
