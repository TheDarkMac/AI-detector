"""Contexte remis à chaque module : lecture du fichier et réception des résultats (ADR-0061).

Les résultats d'un module restent dans son contexte jusqu'à ce qu'il rende la main ; s'il lève
une exception, ils sont écartés (ADR-0060). Le contexte construit les objets du modèle, qui
vérifient leurs invariants, et numérote les observations ``<module>/<n>``.

Un module analyse une partie du fichier à la fois (ADR-0071) : il la lit comme un fichier
autonome, positions comptées depuis son début, et le contexte ramène les plages d'octets de
ses localisations à des positions dans le fichier entier.
"""

import dataclasses
from collections.abc import Collection, Mapping, Sequence

from voight_kampff._protocole import TAILLE_MAX_LECTURE, TAILLE_MAX_MESSAGE, encoder
from voight_kampff._travail import garde
from voight_kampff._travail.fichier import Fichier
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
    Constat,
    Direction,
    Fondement,
    Graduation,
    Localisation,
    NonMenee,
    Observation,
    Partie,
    Phrase,
    Plage,
    RaisonNonMenee,
    ReferenceRegle,
    Scalaire,
)

__all__ = ["RAISONS_D_UN_MODULE", "Contexte", "LimiteDepassee"]

RAISONS_D_UN_MODULE = frozenset(
    {
        RaisonNonMenee.FORMAT_PARTIEL,
        RaisonNonMenee.FICHIER_TRONQUE,
        RaisonNonMenee.REFERENCE_MANQUANTE,
        RaisonNonMenee.RESEAU_DESACTIVE,
    }
)
"""Raisons qu'un module peut donner lui-même ; les autres sont produites par le moteur."""


class LimiteDepassee(Exception):
    """Résultats d'un module au-delà des tailles permises par le protocole."""


class Contexte:
    """Ce qu'un module voit du fichier et de l'analyse en cours."""

    __slots__ = (
        "_budget",
        "_debut",
        "_depasse",
        "_directions",
        "_fichier",
        "_lignes",
        "_numero",
        "_observations",
        "_taille_lignes",
        "format_reel",
        "module",
        "partie",
        "taille",
    )

    def __init__(
        self,
        module: str,
        directions: Collection[Direction],
        fichier: Fichier,
        partie: Partie,
        budget: int,
        numero: int = 0,
    ) -> None:
        garde.exiger()
        self.module = module
        self.format_reel = partie.format
        """Format de la partie analysée, identifié par le contenu (ADR-0070)."""
        self.taille = partie.octets.longueur
        """Taille de la partie en octets."""
        self.partie = partie.rang
        """Rang de la partie dans le fichier ; 1 pour le format réel."""
        self._debut = partie.octets.debut
        self._directions = frozenset(directions)
        self._fichier = fichier
        self._budget = budget
        self._lignes: list[bytes] = []
        self._taille_lignes = 0
        self._numero = numero
        self._observations: set[str] = set()
        self._depasse = False

    # Lecture

    def lire(self, position: int, taille: int) -> bytes:
        """Au plus ``taille`` octets de la partie à partir de ``position`` ; moins en fin."""
        if position < 0 or not 0 <= taille <= TAILLE_MAX_LECTURE:
            raise ValueError("lecture : position ou taille hors bornes")
        taille = min(taille, max(0, self.taille - position))
        return self._fichier.lire(self._debut + position, taille)

    # Résultats

    def observer(
        self,
        nom: str,
        valeur: Scalaire | Sequence[Scalaire],
        *,
        unite: str | None = None,
        localisation: Localisation | None = None,
        identifiante: CategorieIdentifiante | None = None,
    ) -> str:
        """Enregistre une observation et renvoie son identifiant, à citer dans un constat."""
        identifiant = f"{self.module}/{self._numero + 1}"
        observation = Observation(
            identifiant,
            self.module,
            nom,
            valeur if isinstance(valeur, str | int | float | bool) else tuple(valeur),
            unite=unite,
            localisation=self._dans_le_fichier(localisation),
            identifiante=identifiante,
            partie=self.partie,
        )
        self._ajouter({"type": "observation", "observation": observation.vers_dict()})
        self._numero += 1
        self._observations.add(identifiant)
        return identifiant

    def constater(
        self,
        phrase: Phrase,
        donnees: Sequence[str],
        regle: ReferenceRegle,
        *,
        fondement: Fondement,
        categorie: Categorie,
        direction: Direction,
        graduation: Graduation | None = None,
        localisation: Localisation | None = None,
    ) -> None:
        """Enregistre un constat ; ses données sont des observations de ce module."""
        if direction not in self._directions:
            raise ValueError("constat : direction non permise par la fiche technique")
        if not set(donnees) <= self._observations:
            raise ValueError("constat.donnees : observation inconnue de ce module")
        constat = Constat(
            phrase,
            tuple(donnees),
            regle,
            self.module,
            fondement,
            categorie,
            direction,
            graduation=graduation,
            localisation=self._dans_le_fichier(localisation),
            partie=self.partie,
        )
        self._ajouter({"type": "constat", "constat": constat.vers_dict()})

    def non_mener(
        self, raison: RaisonNonMenee, *, localisation: Localisation | None = None
    ) -> None:
        """Signale une partie de l'analyse que le module n'a pas pu mener."""
        if raison not in RAISONS_D_UN_MODULE:
            raise ValueError("non_menee.raison : réservée au moteur")
        non_menee = NonMenee(raison, self.module, self._dans_le_fichier(localisation), self.partie)
        self._ajouter({"type": "non_menee", "non_menee": non_menee.vers_dict()})

    def _dans_le_fichier(self, localisation: Localisation | None) -> Localisation | None:
        """Plage d'octets relative à la partie ramenée à une position dans le fichier."""
        if localisation is None or localisation.octets is None or not self._debut:
            return localisation
        octets = Plage(self._debut + localisation.octets.debut, localisation.octets.longueur)
        return dataclasses.replace(localisation, octets=octets)

    # Pour le moteur

    @property
    def numero(self) -> int:
        """Numéro de la dernière observation ; la partie suivante continue à partir de lui."""
        return self._numero

    @property
    def depasse(self) -> bool:
        """Vrai si le module a dépassé une limite, même s'il a intercepté l'exception."""
        return self._depasse

    @property
    def lignes(self) -> tuple[bytes, ...]:
        """Messages encodés, dans l'ordre où le module les a produits."""
        return tuple(self._lignes)

    def _ajouter(self, message: Mapping[str, object]) -> None:
        if self._depasse:
            raise LimiteDepassee
        ligne = encoder(message)
        if len(ligne) > TAILLE_MAX_MESSAGE or self._taille_lignes + len(ligne) > self._budget:
            self._depasse = True
            raise LimiteDepassee
        self._lignes.append(ligne)
        self._taille_lignes += len(ligne)
