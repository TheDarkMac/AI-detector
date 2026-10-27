"""Interface publique d'analyse : un fichier, analysé par un processus de travail (ES-17).

Avant le catalogue (T15) et le rapport (T16), une analyse rend l'identification et les
résultats validés, sans rapport complet ni masquage (ADR-0073). Ce module n'importe le
processus principal qu'à l'appel de :func:`analyser` : le processus de travail, qui importe
le paquet, n'en charge rien.
"""

import os
from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum

from voight_kampff._limites import TAILLE_MAX_FICHIER
from voight_kampff.rapport.modele import (
    RAISONS_D_INTERRUPTION,
    Constat,
    Couverture,
    Dependance,
    EtatIsolation,
    Identification,
    NonMenee,
    Observation,
    RaisonNonMenee,
    verifier_resultats,
)

__all__ = ["Analyse", "AnalyseRefusee", "MotifRefus", "analyser"]


class MotifRefus(StrEnum):
    """Raisons pour lesquelles un fichier n'a pas de résultat (F-04, ES-08, ADR-0075)."""

    ILLISIBLE = "illisible"
    NON_REGULIER = "non_regulier"
    VIDE = "vide"
    HORS_LIMITES = "hors_limites"
    FORMAT_INCONNU = "format_inconnu"
    HORS_PERIMETRE = "hors_perimetre"
    FICHIER_MODIFIE = "fichier_modifie"
    ANALYSE_IMPOSSIBLE = "analyse_impossible"


_MESSAGES = {
    MotifRefus.ILLISIBLE: "fichier illisible",
    MotifRefus.NON_REGULIER: (
        "pas un fichier régulier (dossier, périphérique, tube) : seul un fichier régulier "
        "est analysé"
    ),
    MotifRefus.VIDE: "fichier vide : aucun format à identifier",
    MotifRefus.HORS_LIMITES: (
        f"fichier trop volumineux : l'outil analyse au plus {TAILLE_MAX_FICHIER >> 30} Gio"
    ),
    MotifRefus.FORMAT_INCONNU: "format non reconnu : il n'est pas dans le périmètre de l'outil",
    MotifRefus.HORS_PERIMETRE: "format hors du périmètre de l'outil",
    MotifRefus.FICHIER_MODIFIE: (
        "le fichier a changé pendant l'analyse : son empreinte n'est plus la même, aucun "
        "résultat n'est livré"
    ),
    MotifRefus.ANALYSE_IMPOSSIBLE: "analyse arrêtée avant l'identification du format",
}


class AnalyseRefusee(Exception):
    """Fichier refusé, ou dont l'analyse ne peut rien livrer, avec un message explicite (F-04).

    Le message ne cite jamais le chemin ni le nom du fichier, qui sont identifiants (ES-14).
    """

    def __init__(
        self,
        motif: MotifRefus,
        *,
        formats: tuple[str, ...] = (),
        raison: RaisonNonMenee | None = None,
        detail: str | None = None,
    ) -> None:
        self.motif = motif
        self.formats = formats
        """Formats reconnus, pour un fichier hors périmètre."""
        self.raison = raison
        """Raison de l'arrêt, pour une analyse arrêtée avant l'identification."""
        message = _MESSAGES[motif]
        if formats:
            message += f" ({', '.join(formats)})"
        if raison is not None:
            message += f" ({raison})"
        if detail:
            message += f" : {detail}"
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class Analyse:
    """Ce qu'une analyse établit pour un fichier, vérifié comme le serait un rapport."""

    identification: Identification
    isolation: EtatIsolation
    couverture: Couverture
    observations: tuple[Observation, ...]
    constats: tuple[Constat, ...]
    non_menees: tuple[NonMenee, ...]
    dependances: tuple[Dependance, ...]
    """Bibliothèques qui ont lu le fichier, avec leur version réelle (ADR-0023)."""

    def __post_init__(self) -> None:
        verifier_resultats(
            self.identification,
            self.couverture,
            self.observations,
            self.constats,
            self.non_menees,
        )

    @property
    def interrompue(self) -> bool:
        """Analyse interrompue, hors garantie de reproductibilité (ADR-0023, NF-08)."""
        return any(non_menee.raison in RAISONS_D_INTERRUPTION for non_menee in self.non_menees)


def analyser(chemin: str | os.PathLike[str], *, desactiver: Collection[str] = ()) -> Analyse:
    """Analyse un fichier dans un processus de travail neuf et isolé (ADR-0036).

    ``desactiver`` nomme des modules à ne pas exécuter (ADR-0063) ; un nom inconnu lève
    ``ModuleInconnu`` avant toute lecture. Un fichier refusé lève :class:`AnalyseRefusee`.
    """
    from voight_kampff._orchestration import soumission  # importé ici : voir le docstring

    return soumission.soumettre(chemin, desactiver)
