"""Contexte remis à chaque module : lecture du fichier et réception des résultats (ADR-0061).

Les résultats d'un module restent dans son contexte jusqu'à ce qu'il rende la main ; s'il lève
une exception, ils sont écartés (ADR-0060). Le contexte construit les objets du modèle, qui
vérifient leurs invariants, et numérote les observations ``<module>/<n>``.

Un module analyse une partie du fichier à la fois (ADR-0071) : il la lit comme un fichier
autonome, positions comptées depuis son début, et le contexte ramène les plages d'octets de
ses localisations à des positions dans le fichier entier.

Le contexte tient aussi le budget du module sur sa partie (ES-03, ADR-0076, ADR-0078) : octets
décompressés, objets parcourus, dimensions déclarées, imbrication, nombre de résultats
(ADR-0121). Ces limites sont comptées, pas chronométrées : un même fichier les dépasse ou non
sur toutes les machines.

Il porte enfin les règles du catalogue qui relèvent du module (ADR-0084, ADR-0090) : le module
cite une règle « module » par son identifiant, et le catalogue fixe ce que dit le constat ; après
lui, le moteur applique les règles « moteur » aux observations qu'il a produites.
"""

import contextlib
import dataclasses
import zlib
from collections.abc import Collection, Iterator, Mapping, Sequence
from typing import Literal

from voight_kampff._limites import (
    OBJETS_MAX,
    PIXELS_MAX,
    PROFONDEUR_MAX,
    RAPPORT_COMPRESSION_MAX,
    RESULTATS_MAX,
    SEUIL_RAPPORT_COMPRESSION,
    TAILLE_MAX_DECOMPRESSEE,
)
from voight_kampff._protocole import TAILLE_MAX_LECTURE, TAILLE_MAX_MESSAGE, encoder
from voight_kampff._regles import Application, Regle, appliquer
from voight_kampff._travail import garde
from voight_kampff._travail.fichier import Fichier
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    Constat,
    Direction,
    Localisation,
    NonMenee,
    Observation,
    Partie,
    Plage,
    RaisonNonMenee,
    Scalaire,
)

__all__ = ["RAISONS_D_UN_MODULE", "Compression", "Contexte", "LimiteDepassee"]

type Compression = Literal["zlib", "deflate", "gzip"]
"""Flux que :meth:`Contexte.decompresser` sait lire : zlib, deflate brut (ZIP), gzip."""

_FENETRES: dict[Compression, int] = {"zlib": 15, "deflate": -15, "gzip": 31}
_BLOC = 1 << 20

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
    """Module au-delà d'une limite comptée : taille des résultats ou budget (ES-03)."""


class Contexte:
    """Ce qu'un module voit du fichier et de l'analyse en cours."""

    __slots__ = (
        "_budget",
        "_compresses",
        "_debut",
        "_decompresses",
        "_depasse",
        "_directions",
        "_fichier",
        "_lignes",
        "_numero",
        "_objets",
        "_observations",
        "_profondeur",
        "_regles",
        "_releves",
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
        regles: Sequence[Regle] = (),
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
        self._releves: list[Observation] = []
        """Observations du module, dans l'ordre : le moteur leur applique ses règles."""
        self._regles = {regle.identifiant: regle for regle in regles}
        """Règles du catalogue qui relèvent de ce module, par identifiant."""
        self._depasse = False
        self._compresses = 0
        self._decompresses = 0
        self._objets = 0
        self._profondeur = 0

    # Lecture

    def lire(self, position: int, taille: int) -> bytes:
        """Au plus ``taille`` octets de la partie à partir de ``position`` ; moins en fin."""
        if position < 0 or not 0 <= taille <= TAILLE_MAX_LECTURE:
            raise ValueError("lecture : position ou taille hors bornes")
        taille = min(taille, max(0, self.taille - position))
        return self._fichier.lire(self._debut + position, taille)

    # Budget (ES-03, ADR-0078)

    def compter_objets(self, nombre: int = 1) -> None:
        """Compte des objets parcourus : entrées d'archive, objets PDF, blocs, balises."""
        if nombre < 0:
            raise ValueError("objets : nombre négatif")
        self._objets += nombre
        if self._objets > OBJETS_MAX:
            self._depasser()

    def verifier_dimensions(self, largeur: int, hauteur: int) -> None:
        """Refuse une image déclarée trop grande, avant de la décoder."""
        if largeur < 0 or hauteur < 0:
            raise ValueError("dimensions : valeur négative")
        if largeur * hauteur > PIXELS_MAX:
            self._depasser()

    @contextlib.contextmanager
    def imbrication(self) -> Iterator[None]:
        """Un niveau d'imbrication de plus, le temps du bloc ``with``."""
        self._profondeur += 1
        try:
            if self._profondeur > PROFONDEUR_MAX:
                self._depasser()
            yield
        finally:
            self._profondeur -= 1

    def compter_decompression(self, compresses: int, decompresses: int) -> None:
        """Déclare des octets décompressés par une bibliothèque, à mesure qu'ils sortent.

        Le cumul est borné, et au-delà d'un seuil, le rapport entre octets décompressés et
        compressés aussi : une bombe de décompression est arrêtée avant d'occuper la mémoire.
        """
        if compresses < 0 or decompresses < 0:
            raise ValueError("décompression : nombre d'octets négatif")
        self._compresses += compresses
        self._decompresses += decompresses
        if self._decompresses > TAILLE_MAX_DECOMPRESSEE or (
            self._decompresses > SEUIL_RAPPORT_COMPRESSION
            and self._decompresses > RAPPORT_COMPRESSION_MAX * max(self._compresses, 1)
        ):
            self._depasser()

    def decompresser(self, donnees: bytes, methode: Compression) -> bytes:
        """Décompresse un flux par blocs, en comptant chaque bloc contre le budget.

        Lève ``zlib.error`` si le flux est invalide ou incomplet ; les octets qui suivent la fin
        du flux sont ignorés.
        """
        flux = zlib.decompressobj(_FENETRES[methode])
        morceaux: list[bytes] = []
        entree = donnees
        while True:
            morceau = flux.decompress(entree, _BLOC)
            self.compter_decompression(len(entree) - len(flux.unconsumed_tail), len(morceau))
            morceaux.append(morceau)
            entree = flux.unconsumed_tail
            if flux.eof:
                return b"".join(morceaux)
            if not entree and len(morceau) < _BLOC:
                raise zlib.error("flux compressé incomplet")

    def _depasser(self) -> None:
        self._depasse = True
        raise LimiteDepassee

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
        self._releves.append(observation)
        return identifiant

    def constater(
        self,
        regle: str,
        donnees: Sequence[str],
        parametres: Mapping[str, str] | None = None,
        *,
        localisation: Localisation | None = None,
    ) -> None:
        """Enregistre le constat d'une règle « module » du catalogue, citée par son identifiant.

        Gabarit, catégorie, direction, fondement et niveau sont ceux de la règle (ADR-0090) ;
        ``parametres`` associe chaque paramètre de sa phrase à une observation de ``donnees``.
        """
        trouvee = self._regles.get(regle)
        if trouvee is None:
            raise ValueError("constat.regle : absente du catalogue pour ce module")
        if trouvee.application is not Application.MODULE:
            raise ValueError("constat.regle : appliquée par le moteur, pas par le module")
        parametres = dict(parametres or {})
        if set(parametres) != set(trouvee.noms_des_parametres):
            raise ValueError("constat.phrase : paramètres différents de ceux de la règle")
        self._constater(trouvee, donnees, parametres, localisation)

    def _constater(
        self,
        regle: Regle,
        donnees: Sequence[str],
        parametres: Mapping[str, str],
        localisation: Localisation | None,
    ) -> None:
        if regle.direction not in self._directions:
            raise ValueError("constat : direction non permise par la fiche technique")
        if not set(donnees) <= self._observations:
            raise ValueError("constat.donnees : observation inconnue de ce module")
        constat = Constat(
            regle.phrase(parametres),
            tuple(donnees),
            regle.reference,
            self.module,
            regle.fondement,
            regle.categorie,
            regle.direction,
            graduation=regle.graduation,
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

    def appliquer_catalogue(self) -> None:
        """Applique les règles « moteur » du module à ses observations, une fois qu'il a fini.

        Les règles sont prises dans l'ordre de leurs identifiants ; leurs constats suivent ceux
        du module et comptent contre son budget.
        """
        for regle, donnees, parametres in appliquer(self._regles.values(), self._releves):
            self._constater(regle, donnees, parametres, None)

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
        if (
            len(ligne) > TAILLE_MAX_MESSAGE
            or self._taille_lignes + len(ligne) > self._budget
            or len(self._lignes) == RESULTATS_MAX
        ):
            self._depasser()
        self._lignes.append(ligne)
        self._taille_lignes += len(ligne)
