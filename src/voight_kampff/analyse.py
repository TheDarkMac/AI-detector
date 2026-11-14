"""Interface publique d'analyse : un fichier, analysé par un processus de travail (ES-17).

Une analyse rend l'identification, les résultats validés, les versions du catalogue et de la liste
de confiance employés, les règles que citent ses constats et les marquages que cite sa couverture
(ADR-0073, ADR-0097, ADR-0171, ADR-0178) ; le
rapport en est construit par :meth:`Analyse.rapport`, et exporté, masqué par défaut, par
:mod:`voight_kampff.rapport.export` (T16). Ce module n'importe le processus principal qu'à l'appel
de :func:`analyser` : le processus de travail, qui importe le paquet, n'en charge rien.
"""

import os
import platform
import sys
from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import version

from voight_kampff._limites import TAILLE_MAX_FICHIER
from voight_kampff._marquages import Marquage
from voight_kampff._regles import Regle, conforme
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
    RaisonNonRecherche,
    Rapport,
    VersionCatalogue,
    VersionConfiance,
    Versions,
    verifier_resultats,
)

__all__ = ["Analyse", "AnalyseRefusee", "MotifRefus", "analyser", "interpreteur"]


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


def interpreteur() -> Dependance:
    """Interpréteur de ce processus, qui lance le processus de travail (ADR-0111).

    Le processus de travail est lancé par ``sys.executable`` (ADR-0036) : c'est le même
    interpréteur, implémentation et version.
    """
    return Dependance(sys.implementation.name, platform.python_version())


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
    catalogue: VersionCatalogue
    """Catalogue de règles employé : version, date, empreinte, livré ou fourni (ADR-0029)."""
    confiance: VersionConfiance
    """Liste de confiance C2PA employée : nom, version, date, empreinte, livrée ou fournie
    (ADR-0171)."""
    regles: tuple[Regle, ...] = ()
    """Règles du catalogue que citent les constats : titre, phrase, limites, évaluation, lus
    par l'export (ADR-0097). Chaque constat est conforme à la sienne."""
    marquages: tuple[Marquage, ...] = ()
    """Marquages du catalogue que cite la couverture, et eux seuls : nom et description, lus
    par l'export (ADR-0178)."""

    def __post_init__(self) -> None:
        verifier_resultats(
            self.identification,
            self.couverture,
            self.observations,
            self.constats,
            self.non_menees,
        )
        par_reference = {regle.reference: regle for regle in self.regles}
        if len(par_reference) != len(self.regles):
            raise ValueError("analyse.regles : doublon")
        for constat in self.constats:
            regle = par_reference.get(constat.regle)
            if regle is None or not conforme(regle, constat):
                raise ValueError("analyse.regles : règle d'un constat absente ou non conforme")
        self._verifier_marquages()

    def _verifier_marquages(self) -> None:
        """Chaque marquage cité est au catalogue, recherché s'il a un module, et la raison d'un
        marquage non recherché est la sienne ou, s'il a un module, « technique_non_menee »."""
        par_identifiant = {marquage.identifiant: marquage for marquage in self.marquages}
        couverture = self.couverture
        cites = [*couverture.marquages_recherches]
        cites += [marquage.identifiant for marquage in couverture.marquages_non_recherches]
        if len(par_identifiant) != len(self.marquages) or set(cites) != set(par_identifiant):
            raise ValueError("analyse.marquages : ceux de la couverture, une fois chacun")
        for identifiant in couverture.marquages_recherches:
            if par_identifiant[identifiant].module is None:
                raise ValueError("analyse.marquages : recherché sans module")
        for non_recherche in couverture.marquages_non_recherches:
            marquage = par_identifiant[non_recherche.identifiant]
            attendue = marquage.raison or RaisonNonRecherche.TECHNIQUE_NON_MENEE
            if non_recherche.raison is not attendue:
                raise ValueError("analyse.marquages : raison d'un marquage non recherché")

    def marquage(self, identifiant: str) -> Marquage:
        """Marquage du catalogue que cite la couverture."""
        return next(m for m in self.marquages if m.identifiant == identifiant)

    def regle(self, constat: Constat) -> Regle:
        """Règle du catalogue qui a produit ce constat."""
        return next(regle for regle in self.regles if regle.reference == constat.regle)

    def rapport(self) -> Rapport:
        """Rapport de l'analyse : données complètes, sans masquage (ADR-0059).

        Le masquage est fait à l'export (:mod:`voight_kampff.rapport.export`) : ce rapport porte
        le nom et l'empreinte du fichier, et ne doit pas être affiché ni transmis tel quel.
        """
        return Rapport(
            identification=self.identification,
            versions=Versions(
                outil=version("voight-kampff-forensics"),
                interpreteur=interpreteur(),
                catalogue=self.catalogue,
                confiance=self.confiance,
                dependances=self.dependances,
            ),
            isolation=self.isolation,
            couverture=self.couverture,
            observations=self.observations,
            constats=self.constats,
            non_menees=self.non_menees,
        )

    @property
    def interrompue(self) -> bool:
        """Analyse interrompue, hors garantie de reproductibilité (ADR-0023, NF-08)."""
        return any(non_menee.raison in RAISONS_D_INTERRUPTION for non_menee in self.non_menees)


def analyser(
    chemin: str | os.PathLike[str],
    *,
    desactiver: Collection[str] = (),
    catalogue: str | os.PathLike[str] | None = None,
    confiance: str | os.PathLike[str] | None = None,
) -> Analyse:
    """Analyse un fichier dans un processus de travail neuf et isolé (ADR-0036).

    ``desactiver`` nomme des modules à ne pas exécuter (ADR-0063) ; un nom inconnu lève
    ``ModuleInconnu`` avant toute lecture. ``catalogue`` nomme le dossier d'un catalogue fourni
    par l'utilisateur, qui remplace le catalogue livré (ADR-0086) ; un catalogue invalide lève
    ``CatalogueInvalide`` avant toute lecture. ``confiance`` nomme le dossier d'une liste de
    confiance C2PA fournie par l'utilisateur, qui remplace la liste livrée (ADR-0171) ; une liste
    invalide lève ``ConfianceInvalide`` avant toute lecture. Un fichier refusé lève
    :class:`AnalyseRefusee`.
    """
    from voight_kampff._orchestration import soumission  # importé ici : voir le docstring

    return soumission.soumettre(chemin, desactiver, catalogue=catalogue, confiance=confiance)
