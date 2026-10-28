"""Modèle de données du rapport : observations, constats, analyses non menées, couverture.

Contrat décrit dans ``docs/modele-de-donnees/modele-de-donnees.md`` (T11, ADR-0054 à ADR-0059).
Les JSON Schema de :mod:`voight_kampff.schemas` portent les mêmes règles, sauf les renvois
entre objets, que seul ce module vérifie ; les tests confrontent les deux.

Ce module n'importe que la bibliothèque standard et le vocabulaire des formats : le processus
de travail s'en sert pour construire ses résultats sans charger ``jsonschema``.

Les messages d'erreur ne recopient jamais une valeur reçue : elle peut venir d'un fichier
hostile (ES-04, ES-15).
"""

import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from voight_kampff import formats

__all__ = [
    "LONGUEUR_MAX_IDENTIFIANT",
    "LONGUEUR_MAX_TEXTE",
    "LONGUEUR_MAX_UNITE",
    "LONGUEUR_MAX_VERSION",
    "NOMBRE_MAX_DONNEES",
    "NOMBRE_MAX_ELEMENTS",
    "NOMBRE_MAX_PARAMETRES",
    "NOMBRE_MAX_PARTIES",
    "RAISONS_D_INTERRUPTION",
    "RAISONS_D_UNE_PARTIE",
    "RAISONS_PROPRES_A_UNE_TECHNIQUE",
    "VERSION_SCHEMA",
    "Categorie",
    "CategorieIdentifiante",
    "Constat",
    "Couverture",
    "Dependance",
    "Direction",
    "EtatIsolation",
    "EtatTechnique",
    "Fondement",
    "Graduation",
    "Identification",
    "Intervalle",
    "Localisation",
    "ManqueIsolation",
    "Niveau",
    "NiveauIsolation",
    "NonMenee",
    "Observation",
    "Partie",
    "Phrase",
    "Plage",
    "RaisonNonMenee",
    "Rapport",
    "ReferenceRegle",
    "Scalaire",
    "TechniqueCouverte",
    "Valeur",
    "VersionCatalogue",
    "Versions",
    "Zone",
    "plages_non_reconnues",
    "verifier_masquage",
    "verifier_parties",
    "verifier_resultats",
]

VERSION_SCHEMA = "0.2.0"
"""Version commune du modèle, du schéma du rapport et de celui des messages (ADR-0036)."""

# Bornes de structure (ES-04). Les limites de taille d'un message et d'un rapport relèvent de T14.
LONGUEUR_MAX_IDENTIFIANT = 128
LONGUEUR_MAX_VERSION = 64
LONGUEUR_MAX_TEXTE = 4096
LONGUEUR_MAX_UNITE = 32
NOMBRE_MAX_ELEMENTS = 4096
NOMBRE_MAX_DONNEES = 256
NOMBRE_MAX_PARAMETRES = 32
NOMBRE_MAX_PARTIES = 16
_ENTIER_MIN = -(2**63)
_ENTIER_MAX = 2**63 - 1

# Expressions sans répétition imbriquée : temps linéaire, appliquées après le contrôle de longueur.
_IDENTIFIANT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+!_-]*")
_EMPREINTE = re.compile(r"[0-9a-f]{64}")
_FORMAT_DATE_HEURE = "%Y-%m-%dT%H:%M:%SZ"

type Scalaire = str | int | float | bool
type Valeur = Scalaire | tuple[Scalaire, ...]
type Document = dict[str, Any]


class Categorie(StrEnum):
    """Classement d'un constat (F-80, ADR-0021)."""

    PREUVE = "preuve"
    INDICE = "indice"
    INFORMATION_NEUTRE = "information_neutre"


class Direction(StrEnum):
    """Hypothèse vers laquelle pointe un constat (F-81 reformulée, ADR-0055)."""

    ORIGINE_IA = "origine_ia"
    RETOUCHE = "retouche"
    TRANSFORMATION = "transformation"
    AUTHENTICITE = "authenticite"
    RIEN_DE_PARTICULIER = "rien_de_particulier"


class Niveau(StrEnum):
    """Niveau fixe d'une règle d'indice (ADR-0018)."""

    FAIBLE = "faible"
    MODERE = "modere"
    FORT = "fort"


class Fondement(StrEnum):
    """Ce sur quoi repose un constat ; seule une vérification fonde une preuve (ES-20)."""

    VERIFICATION_CRYPTOGRAPHIQUE = "verification_cryptographique"
    VERIFICATION_DETERMINISTE = "verification_deterministe"
    DECLARATION = "declaration"
    MESURE = "mesure"


class CategorieIdentifiante(StrEnum):
    """Catégories de données identifiantes, masquées par défaut (ES-13, ADR-0057)."""

    METADONNEE_NOMINATIVE = "metadonnee_nominative"
    NUMERO_DE_SERIE = "numero_de_serie"
    GPS = "gps"
    NOM_DE_FICHIER = "nom_de_fichier"
    EMPREINTE = "empreinte"


class RaisonNonMenee(StrEnum):
    """Raisons, en liste fermée, d'une analyse non menée (F-82, ADR-0056)."""

    HORS_V1 = "hors_v1"
    HORS_PERIMETRE = "hors_perimetre"
    MODULE_DESACTIVE = "module_desactive"
    FORMAT_PARTIEL = "format_partiel"
    FICHIER_TRONQUE = "fichier_tronque"
    REFERENCE_MANQUANTE = "reference_manquante"
    RESEAU_DESACTIVE = "reseau_desactive"
    ERREUR_MODULE = "erreur_module"
    LIMITE_DEPASSEE = "limite_depassee"
    MEMOIRE_DEPASSEE = "memoire_depassee"
    DELAI_DEPASSE = "delai_depasse"
    ARRET_PROCESSUS = "arret_processus"
    MESSAGE_INVALIDE = "message_invalide"


RAISONS_PROPRES_A_UNE_TECHNIQUE = frozenset(
    {
        RaisonNonMenee.HORS_V1,
        RaisonNonMenee.MODULE_DESACTIVE,
        RaisonNonMenee.REFERENCE_MANQUANTE,
        RaisonNonMenee.RESEAU_DESACTIVE,
        RaisonNonMenee.ERREUR_MODULE,
    }
)
"""Raisons qui désignent toujours une technique : la non menée nomme alors son module."""

RAISONS_D_UNE_PARTIE = frozenset({RaisonNonMenee.HORS_PERIMETRE})
"""Raisons qui désignent une partie du fichier, jamais une technique (ADR-0071)."""

RAISONS_D_INTERRUPTION = frozenset(
    {
        RaisonNonMenee.MEMOIRE_DEPASSEE,
        RaisonNonMenee.DELAI_DEPASSE,
        RaisonNonMenee.ARRET_PROCESSUS,
        RaisonNonMenee.MESSAGE_INVALIDE,
    }
)
"""Raisons qui rendent l'analyse interrompue, donc hors garantie de reproductibilité (ADR-0023)."""


class EtatTechnique(StrEnum):
    """État d'une technique dans la couverture du rapport (F-25, F-82, ADR-0059)."""

    APPLIQUEE = "appliquee"
    PARTIELLE = "partielle"
    NON_MENEE = "non_menee"
    NON_APPLICABLE = "non_applicable"


class NiveauIsolation(StrEnum):
    """Isolation du processus de travail (ADR-0028, ADR-0035)."""

    COMPLETE = "complete"
    REDUITE = "reduite"


class ManqueIsolation(StrEnum):
    """Restriction absente quand l'isolation est réduite (architecture, §5)."""

    RESEAU = "reseau"
    ECRITURE = "ecriture"
    LECTURE = "lecture"
    NOUVEAUX_PROGRAMMES = "nouveaux_programmes"
    MEMOIRE = "memoire"
    TEMPS = "temps"
    VIDAGE_MEMOIRE = "vidage_memoire"


# Contrôles communs. Le nom du champ vient du code, jamais du document reçu.


def _identifiant(valeur: str, champ: str) -> None:
    if not 0 < len(valeur) <= LONGUEUR_MAX_IDENTIFIANT or _IDENTIFIANT.fullmatch(valeur) is None:
        raise ValueError(f"{champ} : identifiant invalide")


def _version(valeur: str, champ: str) -> None:
    if not 0 < len(valeur) <= LONGUEUR_MAX_VERSION or _VERSION.fullmatch(valeur) is None:
        raise ValueError(f"{champ} : version invalide")


def _empreinte(valeur: str, champ: str) -> None:
    if len(valeur) != 64 or _EMPREINTE.fullmatch(valeur) is None:
        raise ValueError(f"{champ} : empreinte SHA-256 invalide")


def _texte(valeur: str, champ: str, longueur_max: int = LONGUEUR_MAX_TEXTE) -> None:
    if len(valeur) > longueur_max:
        raise ValueError(f"{champ} : texte trop long")
    try:
        valeur.encode("utf-8")
    except UnicodeEncodeError:
        # Substitut isolé : l'export échouerait plus tard (T16).
        raise ValueError(f"{champ} : texte non encodable en UTF-8") from None


def _entier(valeur: int, champ: str, minimum: int = _ENTIER_MIN) -> None:
    if isinstance(valeur, bool) or not minimum <= valeur <= _ENTIER_MAX:
        raise ValueError(f"{champ} : entier hors bornes")


def _reel(valeur: float, champ: str) -> None:
    # Mêmes bornes que les entiers : le schéma ne distingue pas un réel d'un entier (1.0 = 1).
    if isinstance(valeur, bool) or not math.isfinite(valeur):
        raise ValueError(f"{champ} : nombre non fini")
    if not _ENTIER_MIN <= valeur <= _ENTIER_MAX:
        raise ValueError(f"{champ} : nombre hors bornes")


def _scalaire(valeur: Scalaire, champ: str) -> None:
    if isinstance(valeur, bool):
        return
    if isinstance(valeur, int):
        _entier(valeur, champ)
    elif isinstance(valeur, float):
        _reel(valeur, champ)
    elif isinstance(valeur, str):
        _texte(valeur, champ)
    else:
        raise TypeError(f"{champ} : type de valeur non admis")


def _uniques(valeurs: Iterable[object], champ: str) -> None:
    vues: set[object] = set()
    for valeur in valeurs:
        if valeur in vues:
            raise ValueError(f"{champ} : doublon")
        vues.add(valeur)


def _sans_none(document: Document) -> Document:
    """Les champs facultatifs absents sont omis du JSON, jamais écrits à ``null``."""
    return {cle: valeur for cle, valeur in document.items() if valeur is not None}


def _lire_scalaire(valeur: Any) -> Scalaire:
    if isinstance(valeur, str | int | float | bool):
        return valeur
    raise TypeError("valeur : type de valeur non admis")


# Localisation (A-46)


@dataclass(frozen=True, slots=True)
class Plage:
    """Plage d'octets du fichier analysé."""

    debut: int
    longueur: int

    def __post_init__(self) -> None:
        _entier(self.debut, "plage.debut", minimum=0)
        _entier(self.longueur, "plage.longueur", minimum=1)

    def vers_dict(self) -> Document:
        return {"debut": self.debut, "longueur": self.longueur}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Plage":
        return cls(debut=document["debut"], longueur=document["longueur"])


@dataclass(frozen=True, slots=True)
class Zone:
    """Rectangle d'une image, en pixels, origine en haut à gauche."""

    x: int
    y: int
    largeur: int
    hauteur: int

    def __post_init__(self) -> None:
        _entier(self.x, "zone.x", minimum=0)
        _entier(self.y, "zone.y", minimum=0)
        _entier(self.largeur, "zone.largeur", minimum=1)
        _entier(self.hauteur, "zone.hauteur", minimum=1)

    def vers_dict(self) -> Document:
        return {"x": self.x, "y": self.y, "largeur": self.largeur, "hauteur": self.hauteur}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Zone":
        return cls(
            x=document["x"],
            y=document["y"],
            largeur=document["largeur"],
            hauteur=document["hauteur"],
        )


@dataclass(frozen=True, slots=True)
class Intervalle:
    """Intervalle de temps d'un flux audio ou vidéo, en secondes depuis son début."""

    debut: float
    fin: float

    def __post_init__(self) -> None:
        _reel(self.debut, "intervalle.debut")
        _reel(self.fin, "intervalle.fin")
        if not 0 <= self.debut <= self.fin:
            raise ValueError("intervalle : bornes incohérentes")

    def vers_dict(self) -> Document:
        return {"debut": self.debut, "fin": self.fin}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Intervalle":
        return cls(debut=document["debut"], fin=document["fin"])


@dataclass(frozen=True, slots=True)
class Localisation:
    """Où se trouve, dans le fichier, ce qui a été observé ; au moins un élément."""

    chemin: str | None = None
    """Chemin dans la structure du format : segment, bloc, objet PDF, propriété XMP."""
    octets: Plage | None = None
    page: int | None = None
    """Page d'un PDF, ou rang d'une image dans un fichier qui en a plusieurs ; à partir de 1."""
    zone: Zone | None = None
    intervalle: Intervalle | None = None

    def __post_init__(self) -> None:
        if all(
            element is None
            for element in (self.chemin, self.octets, self.page, self.zone, self.intervalle)
        ):
            raise ValueError("localisation : vide")
        if self.chemin is not None:
            if not self.chemin:
                raise ValueError("localisation.chemin : vide")
            _texte(self.chemin, "localisation.chemin")
        if self.page is not None:
            _entier(self.page, "localisation.page", minimum=1)

    def vers_dict(self) -> Document:
        return _sans_none(
            {
                "chemin": self.chemin,
                "octets": self.octets.vers_dict() if self.octets else None,
                "page": self.page,
                "zone": self.zone.vers_dict() if self.zone else None,
                "intervalle": self.intervalle.vers_dict() if self.intervalle else None,
            }
        )

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Localisation":
        octets = document.get("octets")
        zone = document.get("zone")
        intervalle = document.get("intervalle")
        return cls(
            chemin=document.get("chemin"),
            octets=Plage.depuis_dict(octets) if octets is not None else None,
            page=document.get("page"),
            zone=Zone.depuis_dict(zone) if zone is not None else None,
            intervalle=Intervalle.depuis_dict(intervalle) if intervalle is not None else None,
        )


def _localisation(document: Mapping[str, Any]) -> Localisation | None:
    localisation = document.get("localisation")
    return Localisation.depuis_dict(localisation) if localisation is not None else None


# Observation (ADR-0058)


@dataclass(frozen=True, slots=True)
class Observation:
    """Donnée relevée par un module : valeur d'un champ ou mesure, sans interprétation.

    C'est le seul objet du modèle qui porte des valeurs tirées du fichier.
    """

    identifiant: str
    """Unique dans le rapport ; les constats y renvoient."""
    module: str
    nom: str
    """Nom de la donnée dans le vocabulaire du module, par exemple ``exif.ifd0.Make``."""
    valeur: Valeur
    unite: str | None = None
    localisation: Localisation | None = None
    identifiante: CategorieIdentifiante | None = None
    """Catégorie de donnée identifiante, fixée par le module ; masquée par défaut (ES-13)."""
    partie: int = 1
    """Rang de la partie du fichier analysée par le module (ADR-0071)."""

    def __post_init__(self) -> None:
        _identifiant(self.identifiant, "observation.identifiant")
        _entier(self.partie, "observation.partie", minimum=1)
        _identifiant(self.module, "observation.module")
        _identifiant(self.nom, "observation.nom")
        if isinstance(self.valeur, tuple):
            if len(self.valeur) > NOMBRE_MAX_ELEMENTS:
                raise ValueError("observation.valeur : trop d'éléments")
            for element in self.valeur:
                _scalaire(element, "observation.valeur")
        else:
            _scalaire(self.valeur, "observation.valeur")
        if self.unite is not None:
            if not self.unite:
                raise ValueError("observation.unite : vide")
            _texte(self.unite, "observation.unite", LONGUEUR_MAX_UNITE)

    def vers_dict(self) -> Document:
        valeur = list(self.valeur) if isinstance(self.valeur, tuple) else self.valeur
        return _sans_none(
            {
                "identifiant": self.identifiant,
                "module": self.module,
                "nom": self.nom,
                "valeur": valeur,
                "unite": self.unite,
                "localisation": self.localisation.vers_dict() if self.localisation else None,
                "identifiante": self.identifiante,
                "partie": self.partie,
            }
        )

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Observation":
        brute = document["valeur"]
        valeur: Valeur = (
            tuple(_lire_scalaire(element) for element in brute)
            if isinstance(brute, list)
            else _lire_scalaire(brute)
        )
        identifiante = document.get("identifiante")
        return cls(
            identifiant=document["identifiant"],
            module=document["module"],
            nom=document["nom"],
            valeur=valeur,
            unite=document.get("unite"),
            localisation=_localisation(document),
            identifiante=CategorieIdentifiante(identifiante) if identifiante else None,
            partie=document["partie"],
        )


# Constat (§6 du cahier, A-46, A-47, ADR-0058)


@dataclass(frozen=True, slots=True)
class ReferenceRegle:
    """Règle du catalogue qui a produit le constat, avec sa version (A-47)."""

    identifiant: str
    version: str

    def __post_init__(self) -> None:
        _identifiant(self.identifiant, "regle.identifiant")
        _version(self.version, "regle.version")

    def vers_dict(self) -> Document:
        return {"identifiant": self.identifiant, "version": self.version}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "ReferenceRegle":
        return cls(identifiant=document["identifiant"], version=document["version"])


@dataclass(frozen=True, slots=True)
class Phrase:
    """Phrase en langage courant : gabarit identifié, rédigé hors du code (ADR-0020).

    Chaque paramètre renvoie à une observation du constat : la phrase ne contient aucun texte
    venu du processus de travail, et le masquage des observations s'applique aussi à elle.
    """

    gabarit: str
    parametres: Mapping[str, str] = field(default_factory=dict)
    """Nom du paramètre dans le gabarit → identifiant d'une observation du constat."""

    def __post_init__(self) -> None:
        _identifiant(self.gabarit, "phrase.gabarit")
        if len(self.parametres) > NOMBRE_MAX_PARAMETRES:
            raise ValueError("phrase.parametres : trop de paramètres")
        for nom, observation in self.parametres.items():
            _identifiant(nom, "phrase.parametres")
            _identifiant(observation, "phrase.parametres")
        # Copie figée : l'objet reste immuable même si l'appelant modifie son dictionnaire.
        object.__setattr__(self, "parametres", MappingProxyType(dict(self.parametres)))

    def vers_dict(self) -> Document:
        return {"gabarit": self.gabarit, "parametres": dict(self.parametres)}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Phrase":
        return cls(gabarit=document["gabarit"], parametres=dict(document["parametres"]))


@dataclass(frozen=True, slots=True)
class Graduation:
    """Niveau d'un indice, fixé par sa règle (ADR-0018)."""

    niveau: Niveau
    evaluee: bool
    """Faux si le taux de faux positifs de la règle n'est pas mesuré : niveau faible imposé."""

    def __post_init__(self) -> None:
        if not self.evaluee and self.niveau is not Niveau.FAIBLE:
            raise ValueError("graduation : une règle non évaluée est au niveau faible")

    def vers_dict(self) -> Document:
        return {"niveau": self.niveau, "evaluee": self.evaluee}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Graduation":
        return cls(niveau=Niveau(document["niveau"]), evaluee=document["evaluee"])


_FONDEMENTS_DE_PREUVE = frozenset(
    {Fondement.VERIFICATION_CRYPTOGRAPHIQUE, Fondement.VERIFICATION_DETERMINISTE}
)


@dataclass(frozen=True, slots=True)
class Constat:
    """Ce qu'une règle tire d'une ou plusieurs observations (§6 du cahier, ADR-0058).

    Les limites connues et le taux de la règle sont lus dans le catalogue à partir de
    :attr:`regle`, pas recopiés ici ; la source d'une preuve est portée par ses observations.
    """

    phrase: Phrase
    donnees: tuple[str, ...]
    """Identifiants des observations sur lesquelles repose le constat ; au moins une."""
    regle: ReferenceRegle
    module: str
    """Technique dont relève la règle."""
    fondement: Fondement
    categorie: Categorie
    direction: Direction
    graduation: Graduation | None = None
    """Présente pour un indice, absente sinon."""
    localisation: Localisation | None = None
    partie: int = 1
    """Rang de la partie analysée ; celle de toutes ses données (ADR-0071)."""

    def __post_init__(self) -> None:
        _entier(self.partie, "constat.partie", minimum=1)
        if not self.donnees:
            raise ValueError("constat.donnees : aucune donnée observée")
        if len(self.donnees) > NOMBRE_MAX_DONNEES:
            raise ValueError("constat.donnees : trop de données")
        for identifiant in self.donnees:
            _identifiant(identifiant, "constat.donnees")
        _uniques(self.donnees, "constat.donnees")
        if not set(self.phrase.parametres.values()) <= set(self.donnees):
            raise ValueError("constat.phrase : paramètre hors des données du constat")
        _identifiant(self.module, "constat.module")
        match self.categorie:
            case Categorie.PREUVE:
                if self.fondement not in _FONDEMENTS_DE_PREUVE:
                    raise ValueError("constat : une preuve repose sur une vérification")
                if self.graduation is not None:
                    raise ValueError("constat : une preuve n'a pas de niveau")
            case Categorie.INDICE:
                if self.graduation is None:
                    raise ValueError("constat : un indice a un niveau")
                if self.direction is Direction.RIEN_DE_PARTICULIER:
                    raise ValueError("constat : un indice pointe vers une hypothèse")
            case _:  # Categorie.INFORMATION_NEUTRE, la seule autre valeur
                if self.graduation is not None:
                    raise ValueError("constat : une information neutre n'a pas de niveau")
                if self.direction is not Direction.RIEN_DE_PARTICULIER:
                    raise ValueError("constat : une information neutre ne pointe vers rien")

    def vers_dict(self) -> Document:
        return _sans_none(
            {
                "phrase": self.phrase.vers_dict(),
                "donnees": list(self.donnees),
                "regle": self.regle.vers_dict(),
                "module": self.module,
                "fondement": self.fondement,
                "categorie": self.categorie,
                "direction": self.direction,
                "graduation": self.graduation.vers_dict() if self.graduation else None,
                "localisation": self.localisation.vers_dict() if self.localisation else None,
                "partie": self.partie,
            }
        )

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Constat":
        graduation = document.get("graduation")
        return cls(
            phrase=Phrase.depuis_dict(document["phrase"]),
            donnees=tuple(document["donnees"]),
            regle=ReferenceRegle.depuis_dict(document["regle"]),
            module=document["module"],
            fondement=Fondement(document["fondement"]),
            categorie=Categorie(document["categorie"]),
            direction=Direction(document["direction"]),
            graduation=Graduation.depuis_dict(graduation) if graduation is not None else None,
            localisation=_localisation(document),
            partie=document["partie"],
        )


# Analyses non menées et couverture (F-25, F-82, ADR-0056, ADR-0059)


@dataclass(frozen=True, slots=True)
class NonMenee:
    """Analyse non menée ; la phrase affichée est le gabarit associé à la raison (ADR-0056)."""

    raison: RaisonNonMenee
    module: str | None = None
    """Technique concernée ; absente quand c'est l'analyse du fichier entier qui n'a pas abouti."""
    localisation: Localisation | None = None
    """Endroit du fichier concerné, par exemple la deuxième image d'un HEIC (A-25)."""
    partie: int | None = None
    """Rang de la partie concernée ; obligatoire avec un module (ADR-0071)."""

    def __post_init__(self) -> None:
        if self.partie is not None:
            _entier(self.partie, "non_menee.partie", minimum=1)
        if self.module is not None:
            _identifiant(self.module, "non_menee.module")
            if self.raison in RAISONS_D_UNE_PARTIE:
                raise ValueError("non_menee.module : raison propre à une partie")
            if self.partie is None:
                raise ValueError("non_menee.partie : obligatoire avec un module")
        elif self.raison in RAISONS_PROPRES_A_UNE_TECHNIQUE:
            raise ValueError("non_menee.module : raison propre à une technique")
        elif self.raison in RAISONS_D_UNE_PARTIE and self.partie is None:
            raise ValueError("non_menee.partie : raison propre à une partie")

    def vers_dict(self) -> Document:
        return _sans_none(
            {
                "raison": self.raison,
                "module": self.module,
                "localisation": self.localisation.vers_dict() if self.localisation else None,
                "partie": self.partie,
            }
        )

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "NonMenee":
        return cls(
            raison=RaisonNonMenee(document["raison"]),
            module=document.get("module"),
            localisation=_localisation(document),
            partie=document.get("partie"),
        )


_ETATS_HORS_VERSION = frozenset({EtatTechnique.NON_MENEE, EtatTechnique.NON_APPLICABLE})
"""États possibles d'une technique hors de cette version, donc sans version (ADR-0087)."""


@dataclass(frozen=True, slots=True)
class TechniqueCouverte:
    """Une technique et ce qu'elle est devenue pour ce fichier."""

    module: str
    etat: EtatTechnique
    version: str | None = None
    """Absente seulement pour une technique hors de cette version de l'outil (ADR-0012) : non
    menée sur une partie d'un de ses formats, non applicable sur les autres (ADR-0087)."""
    partie: int = 1
    """Rang de la partie du fichier : une technique figure une fois par partie analysée."""

    def __post_init__(self) -> None:
        _identifiant(self.module, "technique.module")
        _entier(self.partie, "technique.partie", minimum=1)
        if self.version is not None:
            _version(self.version, "technique.version")
        elif self.etat not in _ETATS_HORS_VERSION:
            raise ValueError("technique.version : absente seulement hors de cette version")

    def vers_dict(self) -> Document:
        return _sans_none(
            {
                "module": self.module,
                "etat": self.etat,
                "version": self.version,
                "partie": self.partie,
            }
        )

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "TechniqueCouverte":
        return cls(
            module=document["module"],
            etat=EtatTechnique(document["etat"]),
            version=document.get("version"),
            partie=document["partie"],
        )


@dataclass(frozen=True, slots=True)
class Couverture:
    """Techniques et marquages recherchés : bornent la portée d'un résultat négatif (F-25)."""

    techniques: tuple[TechniqueCouverte, ...]
    marquages_recherches: tuple[str, ...]
    """Identifiants, dans le catalogue, des marquages recherchés (F-25)."""

    def __post_init__(self) -> None:
        _uniques(
            ((technique.module, technique.partie) for technique in self.techniques),
            "couverture.techniques",
        )
        for marquage in self.marquages_recherches:
            _identifiant(marquage, "couverture.marquages_recherches")
        _uniques(self.marquages_recherches, "couverture.marquages_recherches")

    def vers_dict(self) -> Document:
        return {
            "techniques": [technique.vers_dict() for technique in self.techniques],
            "marquages_recherches": list(self.marquages_recherches),
        }

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Couverture":
        return cls(
            techniques=tuple(TechniqueCouverte.depuis_dict(t) for t in document["techniques"]),
            marquages_recherches=tuple(document["marquages_recherches"]),
        )


# Identification, versions, isolation (§6 du cahier, ADR-0023, ADR-0059)


@dataclass(frozen=True, slots=True)
class Partie:
    """Format reconnu dans le fichier et plage d'octets qu'il occupe (F-02, ES-07, ADR-0071)."""

    rang: int
    """À partir de 1, dans l'ordre des débuts ; la partie 1 donne le format réel."""
    format: str
    octets: Plage
    """Du début du format à sa fin logique, ou à la fin du fichier si elle n'est pas connue."""
    fin_connue: bool
    """Faux si la fin logique n'a pas pu être établie (structure non parcourue ou tronquée)."""
    tronquee: bool = False
    """Vrai si la structure s'interrompt avant sa fin : fichier tronqué ou corrompu (ADR-0071)."""

    def __post_init__(self) -> None:
        _entier(self.rang, "partie.rang", minimum=1)
        if self.format not in formats.FORMATS:
            raise ValueError("partie.format : format inconnu")
        if self.tronquee and self.fin_connue:
            raise ValueError("partie.tronquee : une partie tronquée n'a pas de fin connue")

    @property
    def dans_perimetre(self) -> bool:
        """Vrai si le format est analysé ; sinon la partie est déclarée non analysée."""
        return self.format in formats.PERIMETRE

    @property
    def fin(self) -> int:
        """Position qui suit le dernier octet de la partie."""
        return self.octets.debut + self.octets.longueur

    def vers_dict(self) -> Document:
        return {
            "rang": self.rang,
            "format": self.format,
            "octets": self.octets.vers_dict(),
            "fin_connue": self.fin_connue,
            "tronquee": self.tronquee,
        }

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Partie":
        return cls(
            rang=document["rang"],
            format=document["format"],
            octets=Plage.depuis_dict(document["octets"]),
            fin_connue=document["fin_connue"],
            tronquee=document["tronquee"],
        )


def verifier_parties(parties: tuple[Partie, ...], taille: int) -> None:
    """Rangs consécutifs dans l'ordre des débuts, plages dans le fichier (ADR-0071).

    Une partie dont la fin n'est pas connue s'étend jusqu'à la fin du fichier. Les plages
    peuvent se chevaucher : un PDF peut commencer à l'intérieur d'un JPEG.
    """
    if len(parties) > NOMBRE_MAX_PARTIES:
        raise ValueError("parties : trop de parties")
    debut_precedent = 0
    for numero, partie in enumerate(parties, start=1):
        if partie.rang != numero:
            raise ValueError("parties : rangs non consécutifs")
        if partie.octets.debut < debut_precedent:
            raise ValueError("parties : ordre des débuts non respecté")
        if partie.fin > taille or (not partie.fin_connue and partie.fin != taille):
            raise ValueError("parties : plage hors du fichier")
        debut_precedent = partie.octets.debut


def plages_non_reconnues(parties: tuple[Partie, ...], taille: int) -> tuple[Plage, ...]:
    """Plages du fichier qu'aucune partie ne couvre, dans l'ordre."""
    trous: list[Plage] = []
    position = 0
    for partie in sorted(parties, key=lambda p: p.octets.debut):
        if partie.octets.debut > position:
            trous.append(Plage(position, partie.octets.debut - position))
        position = max(position, partie.fin)
    if position < taille:
        trous.append(Plage(position, taille - position))
    return tuple(trous)


@dataclass(frozen=True, slots=True)
class Identification:
    """Rubrique « Identification » ; nom et empreinte sont identifiants (ADR-0014, ADR-0031).

    Les signalements de F-03 et ES-07 en sont tirés (ADR-0072) : extension et concordance,
    parties reconnues, octets qu'aucune ne couvre, dont ceux qui suivent la fin logique.
    """

    nom: str
    """Nom du fichier seul, sans chemin (ES-14)."""
    format_reel: str
    """Format identifié par le contenu (F-02) : celui de la partie 1."""
    taille: int
    """Taille en octets."""
    empreinte: str
    """SHA-256 du fichier entier, en hexadécimal minuscule (ADR-0040)."""
    date_analyse: datetime
    """En UTC, à la seconde (ES-14)."""
    parties: tuple[Partie, ...]
    """Formats reconnus, au moins un du périmètre ; plusieurs pour un polyglotte (ADR-0071)."""

    def __post_init__(self) -> None:
        if not self.nom or "/" in self.nom or "\\" in self.nom or "\x00" in self.nom:
            raise ValueError("identification.nom : nom de fichier sans chemin attendu")
        _texte(self.nom, "identification.nom")
        _entier(self.taille, "identification.taille", minimum=0)
        _empreinte(self.empreinte, "identification.empreinte")
        if self.date_analyse.utcoffset() != timedelta(0):
            raise ValueError("identification.date_analyse : heure UTC attendue")
        if self.date_analyse.microsecond:
            raise ValueError("identification.date_analyse : précision à la seconde attendue")
        if not self.parties:
            raise ValueError("identification.parties : aucun format reconnu")
        verifier_parties(self.parties, self.taille)
        if self.format_reel != self.parties[0].format:
            raise ValueError("identification.format_reel : format de la partie 1 attendu")
        if not any(partie.dans_perimetre for partie in self.parties):
            raise ValueError("identification.parties : aucun format du périmètre")

    @property
    def extension(self) -> str | None:
        """Extension du nom, en minuscules ; elle n'est pas identifiante, le nom l'est."""
        return formats.extension(self.nom)

    @property
    def extension_concordante(self) -> bool | None:
        """Concordance de l'extension avec le format réel (F-03) ; ``None`` sans extension."""
        extension = self.extension
        return None if extension is None else formats.concordante(extension, self.format_reel)

    @property
    def octets_non_reconnus(self) -> tuple[Plage, ...]:
        """Plages qu'aucune partie ne couvre ; la dernière suit la fin logique (ES-07)."""
        return plages_non_reconnues(self.parties, self.taille)

    def vers_dict(self) -> Document:
        return _sans_none(
            {
                "nom": self.nom,
                "format_reel": self.format_reel,
                "taille": self.taille,
                "empreinte": self.empreinte,
                "date_analyse": self.date_analyse.strftime(_FORMAT_DATE_HEURE),
                "parties": [partie.vers_dict() for partie in self.parties],
                "extension": self.extension,
                "extension_concordante": self.extension_concordante,
                "octets_non_reconnus": [plage.vers_dict() for plage in self.octets_non_reconnus],
            }
        )

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Identification":
        date_analyse = datetime.strptime(document["date_analyse"], _FORMAT_DATE_HEURE)
        identification = cls(
            nom=document["nom"],
            format_reel=document["format_reel"],
            taille=document["taille"],
            empreinte=document["empreinte"],
            date_analyse=date_analyse.replace(tzinfo=UTC),
            parties=tuple(Partie.depuis_dict(partie) for partie in document["parties"]),
        )
        # Champs déduits : présents pour le lecteur du JSON, vérifiés à la relecture.
        deduits = identification.vers_dict()
        for champ in ("extension", "extension_concordante", "octets_non_reconnus"):
            if document.get(champ) != deduits.get(champ):
                raise ValueError(f"identification.{champ} : incohérent avec le nom ou les parties")
        return identification


@dataclass(frozen=True, slots=True)
class Dependance:
    """Bibliothèque qui décode ou analyse le fichier, avec sa version réelle (ADR-0023)."""

    nom: str
    version: str

    def __post_init__(self) -> None:
        _identifiant(self.nom, "dependance.nom")
        _version(self.version, "dependance.version")

    def vers_dict(self) -> Document:
        return {"nom": self.nom, "version": self.version}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Dependance":
        return cls(nom=document["nom"], version=document["version"])


@dataclass(frozen=True, slots=True)
class VersionCatalogue:
    """Catalogue de règles employé (ADR-0029, NF-07)."""

    version: str
    date: date
    empreinte: str
    fourni_par_utilisateur: bool
    """Vrai si l'utilisateur a remplacé le catalogue livré ; le rapport le signale (ADR-0029)."""

    def __post_init__(self) -> None:
        _version(self.version, "catalogue.version")
        _empreinte(self.empreinte, "catalogue.empreinte")

    def vers_dict(self) -> Document:
        return {
            "version": self.version,
            "date": self.date.isoformat(),
            "empreinte": self.empreinte,
            "fourni_par_utilisateur": self.fourni_par_utilisateur,
        }

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "VersionCatalogue":
        return cls(
            version=document["version"],
            date=date.fromisoformat(document["date"]),
            empreinte=document["empreinte"],
            fourni_par_utilisateur=document["fourni_par_utilisateur"],
        )


@dataclass(frozen=True, slots=True)
class Versions:
    """Rubrique « Versions » (§6 du cahier, ADR-0023)."""

    outil: str
    catalogue: VersionCatalogue
    dependances: tuple[Dependance, ...] = ()

    def __post_init__(self) -> None:
        _version(self.outil, "versions.outil")
        _uniques((dependance.nom for dependance in self.dependances), "versions.dependances")

    def vers_dict(self) -> Document:
        return {
            "outil": self.outil,
            "catalogue": self.catalogue.vers_dict(),
            "dependances": [dependance.vers_dict() for dependance in self.dependances],
        }

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Versions":
        return cls(
            outil=document["outil"],
            catalogue=VersionCatalogue.depuis_dict(document["catalogue"]),
            dependances=tuple(Dependance.depuis_dict(d) for d in document["dependances"]),
        )


@dataclass(frozen=True, slots=True)
class EtatIsolation:
    """Isolation obtenue par le processus de travail, envoyée avant toute lecture du fichier."""

    niveau: NiveauIsolation
    manques: tuple[ManqueIsolation, ...] = ()

    def __post_init__(self) -> None:
        _uniques(self.manques, "isolation.manques")
        if (self.niveau is NiveauIsolation.COMPLETE) != (not self.manques):
            raise ValueError("isolation : réduite si et seulement si une restriction manque")

    def vers_dict(self) -> Document:
        return {"niveau": self.niveau, "manques": list(self.manques)}

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "EtatIsolation":
        return cls(
            niveau=NiveauIsolation(document["niveau"]),
            manques=tuple(ManqueIsolation(manque) for manque in document["manques"]),
        )


# Rapport (§6 du cahier, ADR-0059)


def verifier_masquage(masquage: Mapping[str, Any]) -> frozenset[CategorieIdentifiante]:
    """Catégories masquées d'un export, chacune masquée ou levée une fois (ES-13, ADR-0095)."""
    masquees = [CategorieIdentifiante(categorie) for categorie in masquage["masquees"]]
    levees = [CategorieIdentifiante(categorie) for categorie in masquage["levees"]]
    toutes = masquees + levees
    if len(toutes) != len(set(toutes)) or set(toutes) != set(CategorieIdentifiante):
        raise ValueError("masquage : chaque catégorie masquée ou levée, une seule fois")
    return frozenset(masquees)


_ETATS_AVEC_RESULTATS = frozenset({EtatTechnique.APPLIQUEE, EtatTechnique.PARTIELLE})
_ETATS_AVEC_NON_MENEE = frozenset({EtatTechnique.PARTIELLE, EtatTechnique.NON_MENEE})


def verifier_resultats(
    identification: Identification,
    couverture: Couverture,
    observations: tuple[Observation, ...],
    constats: tuple[Constat, ...],
    non_menees: tuple[NonMenee, ...],
) -> None:
    """Renvois entre les objets d'une analyse, que les schémas ne vérifient pas.

    Une technique figure une fois pour chaque partie du périmètre. Ce que l'identification n'a
    pas pu analyser est déclaré non mené : partie hors périmètre (``hors_perimetre``), partie
    tronquée (``fichier_tronque``), plage non reconnue (``format_partiel``) (ADR-0071). Les
    résultats d'une technique portent sur une partie où elle est appliquée ou partielle ; un
    constat ne cite que des observations de sa technique et de sa partie.
    """
    rangs = {partie.rang for partie in identification.parties}
    analysees = {partie.rang for partie in identification.parties if partie.dans_perimetre}

    par_identifiant = {observation.identifiant: observation for observation in observations}
    _uniques((observation.identifiant for observation in observations), "observations")
    for constat in constats:
        citees = [par_identifiant.get(donnee) for donnee in constat.donnees]
        if any(observation is None for observation in citees):
            raise ValueError("constats : renvoi vers une observation absente")
        if any(
            o is not None and (o.module, o.partie) != (constat.module, constat.partie)
            for o in citees
        ):
            raise ValueError("constats : observation d'une autre technique ou partie")

    techniques = {(t.module, t.partie): t for t in couverture.techniques}
    modules = {technique.module for technique in couverture.techniques}
    if set(techniques) != {(module, rang) for module in modules for rang in analysees}:
        raise ValueError("couverture : une entrée par technique et par partie analysée")
    portees = [(o.module, o.partie) for o in observations] + [
        (c.module, c.partie) for c in constats
    ]
    for cle in portees:
        technique = techniques.get(cle)
        if technique is None or technique.etat not in _ETATS_AVEC_RESULTATS:
            raise ValueError("résultat d'une technique ni appliquée ni partielle")

    raisons: dict[tuple[str, int], set[RaisonNonMenee]] = {}
    hors_perimetre: list[int] = []
    for non_menee in non_menees:
        if non_menee.partie is not None and non_menee.partie not in rangs:
            raise ValueError("non_menees : partie absente de l'identification")
        if non_menee.raison is RaisonNonMenee.HORS_PERIMETRE:
            hors_perimetre.append(non_menee.partie or 0)
        if non_menee.module is None:
            continue
        cle = (non_menee.module, non_menee.partie or 0)
        if cle not in techniques:
            raise ValueError("non_menees : technique absente de la couverture")
        raisons.setdefault(cle, set()).add(non_menee.raison)
    if sorted(hors_perimetre) != sorted(rangs - analysees):
        raise ValueError("non_menees : une non menée « hors_perimetre » par partie non analysée")
    du_fichier = {
        (n.raison, n.partie, n.localisation.octets if n.localisation else None)
        for n in non_menees
        if n.module is None
    }
    for partie in identification.parties:
        if partie.tronquee and not any(
            (RaisonNonMenee.FICHIER_TRONQUE, partie.rang) == cle[:2] for cle in du_fichier
        ):
            raise ValueError("non_menees : « fichier_tronque » attendu pour une partie tronquée")
    for plage in identification.octets_non_reconnus:
        if (RaisonNonMenee.FORMAT_PARTIEL, None, plage) not in du_fichier:
            raise ValueError("non_menees : « format_partiel » attendu pour une plage non reconnue")
    for cle, technique in techniques.items():
        if (technique.etat in _ETATS_AVEC_NON_MENEE) != (cle in raisons):
            raise ValueError("couverture : état incohérent avec les non menées")
        # Sans version : non menée pour la seule raison hors_v1, ou non applicable (ADR-0087).
        hors_version = raisons.get(cle) == {RaisonNonMenee.HORS_V1}
        sans_version = hors_version or technique.etat is EtatTechnique.NON_APPLICABLE
        if hors_version and technique.version is not None:
            raise ValueError("couverture : version absente seulement si hors V1")
        if technique.version is None and not sans_version:
            raise ValueError("couverture : version absente seulement si hors V1")


@dataclass(frozen=True, slots=True)
class Rapport:
    """Rapport d'analyse d'un fichier : données, sans mise en forme ni masquage.

    Le résumé, l'avertissement et le masquage sont produits à l'export à partir de ces
    données (T16, :mod:`voight_kampff.rapport.export`) ; ils ne sont pas stockés ici.
    """

    identification: Identification
    versions: Versions
    isolation: EtatIsolation
    couverture: Couverture
    observations: tuple[Observation, ...] = ()
    constats: tuple[Constat, ...] = ()
    non_menees: tuple[NonMenee, ...] = ()

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

    def vers_dict(self) -> Document:
        return {
            "version_schema": VERSION_SCHEMA,
            "identification": self.identification.vers_dict(),
            "versions": self.versions.vers_dict(),
            "isolation": self.isolation.vers_dict(),
            "couverture": self.couverture.vers_dict(),
            "observations": [observation.vers_dict() for observation in self.observations],
            "constats": [constat.vers_dict() for constat in self.constats],
            "non_menees": [non_menee.vers_dict() for non_menee in self.non_menees],
            "interrompue": self.interrompue,
        }

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Rapport":
        """Reconstruit un rapport à partir d'un document déjà validé par son schéma.

        Un export masqué n'a plus toutes ses données : il est refusé (ADR-0095).
        """
        if document["version_schema"] != VERSION_SCHEMA:
            raise ValueError("rapport : version de schéma non prise en charge")
        masquage = document.get("masquage")
        if masquage is not None and verifier_masquage(masquage):
            raise ValueError("rapport : export masqué, ses données identifiantes manquent")
        rapport = cls(
            identification=Identification.depuis_dict(document["identification"]),
            versions=Versions.depuis_dict(document["versions"]),
            isolation=EtatIsolation.depuis_dict(document["isolation"]),
            couverture=Couverture.depuis_dict(document["couverture"]),
            observations=tuple(Observation.depuis_dict(o) for o in document["observations"]),
            constats=tuple(Constat.depuis_dict(c) for c in document["constats"]),
            non_menees=tuple(NonMenee.depuis_dict(n) for n in document["non_menees"]),
        )
        if document["interrompue"] != rapport.interrompue:
            raise ValueError("rapport.interrompue : incohérent avec les non menées")
        return rapport
