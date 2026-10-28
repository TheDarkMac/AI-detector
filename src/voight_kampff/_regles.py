"""Règles du catalogue : forme, compilation des motifs, évaluation (ADR-0039, ADR-0084, ADR-0089).

Commun aux deux processus. Le processus principal construit les règles en lisant le catalogue,
ce qui compile chaque motif : un motif que RE2 refuse rend le catalogue invalide (ADR-0039). Il
ne les applique jamais à une donnée du fichier. Le processus de travail les reconstruit depuis
la configuration et applique celles du moteur aux observations d'un module, après lui.

Une règle « moteur » est une conjonction de conditions, chacune sur une observation nommée ;
une règle « module » est appliquée par le code de son module, qui la cite par son identifiant.
Dans les deux cas, c'est le catalogue qui fixe ce que dit le constat : gabarit et texte de la
phrase, catégorie, direction, fondement et niveau (ADR-0090, ADR-0091).
"""

import math
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import re2

from voight_kampff._limites import MEMOIRE_MAX_MOTIF, PROGRAMME_MAX_MOTIF
from voight_kampff.rapport.modele import (
    LONGUEUR_MAX_TEXTE,
    NOMBRE_MAX_ELEMENTS,
    NOMBRE_MAX_PARAMETRES,
    Categorie,
    Constat,
    Direction,
    Fondement,
    Graduation,
    Niveau,
    Observation,
    Phrase,
    ReferenceRegle,
    Scalaire,
    Valeur,
)

__all__ = [
    "BORNE_FORT",
    "BORNE_MODERE",
    "Application",
    "Calibrage",
    "Comparaison",
    "Condition",
    "Evaluation",
    "Methode",
    "Regle",
    "Seuil",
    "appliquer",
    "conforme",
    "emplacements",
    "niveau_permis",
    "remplir",
]

type Document = dict[str, Any]

LONGUEUR_MAX_MOTIF = 1024
LONGUEUR_MAX_PHRASE = 1024
CONDITIONS_MAX = 16
LIMITES_MAX = 32
LANGUES = ("fr",)
"""Langues des phrases : le français seul en V1 (ADR-0020) ; en ajouter une change le format."""
BORNE_FORT = 0.01
BORNE_MODERE = 0.05
"""Bornes des niveaux (ADR-0101) : la borne supérieure de l'intervalle de Wilson à 95 % du taux
de faux positifs d'une règle permet « fort » jusqu'à 1 %, « modéré » jusqu'à 5 %."""

# Expressions du code, fixes, sans répétition imbriquée : temps linéaire (ADR-0039).
_IDENTIFIANT_REGLE = re.compile(r"R-[A-Z][A-Z0-9]*-[0-9]{3}")
_VERSION_REGLE = re.compile(r"[1-9][0-9]{0,5}")
_MODULE = re.compile(r"[a-z][a-z0-9]*")
_GABARIT = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
_NOM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*")
_VERSION_CORPUS = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+!_-]*")
_EMPLACEMENT = re.compile(r"\{([^{}]*)\}")


class Application(StrEnum):
    """Qui applique la règle (ADR-0084)."""

    MOTEUR = "moteur"
    """Le moteur, d'après les conditions écrites dans le catalogue."""
    MODULE = "module"
    """Le code du module, pour une vérification qu'aucune condition ne sait écrire (C2PA)."""


class Comparaison(StrEnum):
    """Opérateur d'un seuil."""

    INFERIEUR = "<"
    INFERIEUR_OU_EGAL = "<="
    SUPERIEUR = ">"
    SUPERIEUR_OU_EGAL = ">="


class Methode(StrEnum):
    """Origine d'un seuil (ADR-0016)."""

    MANUELLE = "manuelle"
    CORPUS = "corpus"


def _verifier(motif: re.Pattern[str], valeur: object, longueur: int, champ: str) -> None:
    if not isinstance(valeur, str) or not 0 < len(valeur) <= longueur:
        raise ValueError(f"{champ} : valeur invalide")
    if motif.fullmatch(valeur) is None:
        raise ValueError(f"{champ} : syntaxe invalide")


def _texte(valeur: object, champ: str, longueur: int = LONGUEUR_MAX_TEXTE) -> None:
    if not isinstance(valeur, str) or not 0 < len(valeur) <= longueur:
        raise ValueError(f"{champ} : texte vide ou trop long")


def _scalaire(valeur: object, champ: str) -> None:
    if isinstance(valeur, bool):
        return
    if isinstance(valeur, str):
        _texte(valeur, champ)
    elif isinstance(valeur, int | float):
        if not math.isfinite(valeur) or not -(2**63) <= valeur <= 2**63 - 1:
            raise ValueError(f"{champ} : nombre fini attendu")
    else:
        raise ValueError(f"{champ} : texte, nombre ou booléen attendu")


def emplacements(texte: str) -> tuple[str, ...]:
    """Noms des paramètres d'un texte de phrase, dans l'ordre : ``{nom}`` (ADR-0091).

    Une accolade hors d'un emplacement ``{nom}`` rend le texte invalide : le texte n'a aucun
    moyen d'en écrire une littéralement.
    """
    noms = _EMPLACEMENT.findall(texte)
    reste = _EMPLACEMENT.sub("", texte)
    if "{" in reste or "}" in reste:
        raise ValueError("regle.phrase : accolade hors d'un emplacement {parametre}")
    for nom in noms:
        _verifier(_NOM, nom, 128, "regle.phrase")
    return tuple(noms)


def remplir(texte: str, valeurs: Mapping[str, str]) -> str:
    """Texte de phrase dont chaque ``{nom}`` est remplacé par ``valeurs[nom]``.

    Remplacement littéral, sans interprétation de la valeur ni du nom (pas de ``str.format``,
    qui suivrait un attribut écrit ``{a.b}``).
    """
    return _EMPLACEMENT.sub(lambda emplacement: valeurs[emplacement.group(1)], texte)


def _cle(valeur: Scalaire) -> tuple[str, Scalaire]:
    """Clé de comparaison : un booléen n'est jamais égal à un nombre, ni un nombre à un texte.

    Python tient ``True == 1`` ; le catalogue non. Entier et réel de même valeur sont égaux.
    """
    if isinstance(valeur, bool):
        return ("booleen", valeur)
    if isinstance(valeur, str):
        return ("texte", valeur)
    return ("nombre", valeur)


def _compiler(motif: str) -> Any:
    """Compile un motif RE2 ; le refuse si RE2 le refuse ou si son programme est trop grand."""
    options = re2.Options()
    options.log_errors = False  # sinon RE2 écrit sur la sortie d'erreur de l'utilisateur
    options.max_mem = MEMOIRE_MAX_MOTIF
    options.never_capture = True
    try:
        compile_ = re2.compile(motif, options)
    except re2.error:
        raise ValueError("condition.motif : refusé par RE2") from None
    if compile_.programsize > PROGRAMME_MAX_MOTIF:
        raise ValueError("condition.motif : programme compilé trop grand")
    return compile_


@dataclass(frozen=True, slots=True)
class Seuil:
    operateur: Comparaison
    valeur: int | float

    def __post_init__(self) -> None:
        if isinstance(self.valeur, bool):
            raise ValueError("condition.seuil.valeur : nombre attendu")
        _scalaire(self.valeur, "condition.seuil.valeur")

    def atteint(self, valeur: int | float) -> bool:
        match self.operateur:
            case Comparaison.INFERIEUR:
                return valeur < self.valeur
            case Comparaison.INFERIEUR_OU_EGAL:
                return valeur <= self.valeur
            case Comparaison.SUPERIEUR:
                return valeur > self.valeur
            case _:  # Comparaison.SUPERIEUR_OU_EGAL, la seule autre valeur
                return valeur >= self.valeur


@dataclass(frozen=True, slots=True)
class Condition:
    """Test sur une observation nommée ; un seul des tests est donné (ADR-0089).

    Une observation dont la valeur est une liste satisfait la condition si l'un de ses
    éléments la satisfait. ``presente`` est satisfaite par toute observation du nom donné.
    """

    observation: str
    """Nom de l'observation, dans le vocabulaire du module (sa fiche technique)."""
    egal: Scalaire | None = None
    parmi: tuple[Scalaire, ...] | None = None
    motif: str | None = None
    """Expression RE2, cherchée n'importe où dans un texte : ``^`` et ``$`` l'ancrent."""
    seuil: Seuil | None = None
    presente: bool = False
    parametre: str | None = None
    """Nom du paramètre de la phrase qui renvoie à l'observation retenue."""
    _compile: Any = field(default=None, init=False, repr=False, compare=False)
    _cles: frozenset[tuple[str, Scalaire]] = field(
        default=frozenset(), init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        _verifier(_NOM, self.observation, 128, "condition.observation")
        tests = (
            self.egal is not None,
            self.parmi is not None,
            self.motif is not None,
            self.seuil is not None,
            self.presente,
        )
        if sum(tests) != 1:
            raise ValueError("condition : un test et un seul attendu")
        if self.egal is not None:
            _scalaire(self.egal, "condition.egal")
        if self.parmi is not None:
            if not 0 < len(self.parmi) <= NOMBRE_MAX_ELEMENTS:
                raise ValueError("condition.parmi : de 1 à 4096 valeurs attendues")
            for valeur in self.parmi:
                _scalaire(valeur, "condition.parmi")
            object.__setattr__(self, "_cles", frozenset(map(_cle, self.parmi)))
        if self.motif is not None:
            _texte(self.motif, "condition.motif", LONGUEUR_MAX_MOTIF)
            object.__setattr__(self, "_compile", _compiler(self.motif))
        if self.parametre is not None:
            _verifier(_NOM, self.parametre, 128, "condition.parametre")

    def satisfaite(self, valeur: Valeur) -> bool:
        if self.presente:
            return True
        if isinstance(valeur, tuple):
            return any(map(self._element, valeur))
        return self._element(valeur)

    def _element(self, valeur: Scalaire) -> bool:
        if self.egal is not None:
            return _cle(valeur) == _cle(self.egal)
        if self.parmi is not None:
            return _cle(valeur) in self._cles
        if self.motif is not None:
            return isinstance(valeur, str) and self._compile.search(valeur) is not None
        if self.seuil is not None and not isinstance(valeur, bool | str):
            return self.seuil.atteint(valeur)
        return False

    def vers_dict(self) -> Document:
        document: Document = {"observation": self.observation}
        if self.egal is not None:
            document["egal"] = self.egal
        if self.parmi is not None:
            document["parmi"] = list(self.parmi)
        if self.motif is not None:
            document["motif"] = self.motif
        if self.seuil is not None:
            document["seuil"] = {"operateur": self.seuil.operateur, "valeur": self.seuil.valeur}
        if self.presente:
            document["presente"] = True
        if self.parametre is not None:
            document["parametre"] = self.parametre
        return document

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Condition":
        seuil = document.get("seuil")
        parmi = document.get("parmi")
        return cls(
            observation=document["observation"],
            egal=document.get("egal"),
            parmi=None if parmi is None else tuple(parmi),
            motif=document.get("motif"),
            seuil=None
            if seuil is None
            else Seuil(Comparaison(seuil["operateur"]), seuil["valeur"]),
            presente=document.get("presente", False),
            parametre=document.get("parametre"),
        )


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Taux de faux positifs mesuré sur la partie évaluation du corpus (ADR-0016, ADR-0018).

    Publié avec son effectif et la borne supérieure de son intervalle de confiance (A-54), que
    calcule le banc d'évaluation (ADR-0104) ; c'est cette borne qui fixe le niveau permis.
    """

    taux_faux_positifs: float
    effectif: int
    """Nombre de fichiers sur lequel le taux est mesuré."""
    borne_superieure: float
    """Borne supérieure de l'intervalle de Wilson à 95 % du taux (ADR-0101)."""
    corpus: str
    """Version du corpus d'évaluation."""
    date: date

    def __post_init__(self) -> None:
        taux, borne = self.taux_faux_positifs, self.borne_superieure
        for valeur in (taux, borne):
            if isinstance(valeur, bool) or not isinstance(valeur, int | float):
                raise ValueError("evaluation : taux et borne entre 0 et 1 attendus")
        if not 0 <= taux <= borne <= 1:
            raise ValueError("evaluation : 0 ≤ taux ≤ borne supérieure ≤ 1 attendu")
        if isinstance(self.effectif, bool) or not isinstance(self.effectif, int):
            raise ValueError("evaluation.effectif : entier attendu")
        if self.effectif < 1:
            raise ValueError("evaluation.effectif : au moins un fichier")
        _verifier(_VERSION_CORPUS, self.corpus, 64, "evaluation.corpus")

    def vers_dict(self) -> Document:
        return {
            "taux_faux_positifs": self.taux_faux_positifs,
            "effectif": self.effectif,
            "borne_superieure": self.borne_superieure,
            "corpus": self.corpus,
            "date": self.date.isoformat(),
        }


def niveau_permis(borne_superieure: float) -> Niveau:
    """Niveau le plus élevé que permet la borne supérieure d'un taux de faux positifs."""
    if borne_superieure <= BORNE_FORT:
        return Niveau.FORT
    if borne_superieure <= BORNE_MODERE:
        return Niveau.MODERE
    return Niveau.FAIBLE


_RANG_DES_NIVEAUX = {Niveau.FAIBLE: 0, Niveau.MODERE: 1, Niveau.FORT: 2}


@dataclass(frozen=True, slots=True)
class Calibrage:
    """Origine des seuils de la règle (ADR-0016)."""

    methode: Methode
    procedure: str
    corpus: str | None = None
    """Version du corpus de calibrage, pour un seuil calibré."""

    def __post_init__(self) -> None:
        _texte(self.procedure, "calibrage.procedure")
        if (self.methode is Methode.CORPUS) != (self.corpus is not None):
            raise ValueError("calibrage.corpus : obligatoire pour un seuil calibré, sinon absent")
        if self.corpus is not None:
            _verifier(_VERSION_CORPUS, self.corpus, 64, "calibrage.corpus")

    def vers_dict(self) -> Document:
        document: Document = {"methode": self.methode, "procedure": self.procedure}
        if self.corpus is not None:
            document["corpus"] = self.corpus
        return document


@dataclass(frozen=True, slots=True)
class Regle:
    """Règle du catalogue, versionnée (A-47) ; publique, limites comprises (ADR-0019)."""

    identifiant: str
    version: str
    """Entier positif écrit en texte ; il augmente à chaque changement de la règle (ADR-0085)."""
    module: str
    titre: str
    description: str
    gabarit: str
    textes: Mapping[str, str]
    """Texte de la phrase par langue (``phrase`` dans le catalogue, ADR-0091) : les ``{nom}``
    sont les paramètres, remplacés par la valeur de leur observation à l'export (T16)."""
    categorie: Categorie
    direction: Direction
    fondement: Fondement
    limites: tuple[str, ...]
    application: Application
    conditions: tuple[Condition, ...] = ()
    """Toutes requises ; pour une règle du moteur seulement."""
    parametres: tuple[str, ...] = ()
    """Paramètres de la phrase d'une règle du module ; ceux d'une règle du moteur sont portés
    par ses conditions."""
    niveau: Niveau | None = None
    """Pour un indice seulement ; « faible » tant que la règle n'est pas évaluée (ADR-0018)."""
    evaluation: Evaluation | None = None
    calibrage: Calibrage | None = None

    def __post_init__(self) -> None:
        _verifier(_IDENTIFIANT_REGLE, self.identifiant, 40, "regle.identifiant")
        _verifier(_VERSION_REGLE, self.version, 6, "regle.version")
        _verifier(_MODULE, self.module, 32, "regle.module")
        _texte(self.titre, "regle.titre", 120)
        _texte(self.description, "regle.description")
        _verifier(_GABARIT, self.gabarit, 128, "regle.gabarit")
        if set(self.textes) != set(LANGUES):
            raise ValueError("regle.phrase : une phrase en français attendue (ADR-0020)")
        if not 0 < len(self.limites) <= LIMITES_MAX:
            raise ValueError("regle.limites : de 1 à 32 limites connues attendues (ADR-0019)")
        for limite in self.limites:
            _texte(limite, "regle.limites", 1024)
        if self.application is Application.MOTEUR:
            if not 0 < len(self.conditions) <= CONDITIONS_MAX or self.parametres:
                raise ValueError(
                    "regle.condition : de 1 à 16 conditions, paramètres portés par elles"
                )
        elif self.conditions:
            raise ValueError("regle.condition : aucune condition pour une règle du module")
        noms = self.noms_des_parametres
        if len(noms) > NOMBRE_MAX_PARAMETRES or len(set(noms)) != len(noms):
            raise ValueError("regle.parametres : 32 au plus, sans doublon")
        for nom in self.parametres:
            _verifier(_NOM, nom, 128, "regle.parametres")
        for texte in self.textes.values():
            _texte(texte, "regle.phrase", LONGUEUR_MAX_PHRASE)
            if set(emplacements(texte)) != set(noms):
                raise ValueError("regle.phrase : emplacements différents des paramètres déclarés")
        # Copie figée : la règle reste immuable même si l'appelant modifie son dictionnaire.
        object.__setattr__(self, "textes", MappingProxyType(dict(self.textes)))
        if self.categorie is not Categorie.INDICE and (self.niveau or self.evaluation):
            raise ValueError("regle.niveau : réservé aux indices (ADR-0018)")
        if self.niveau is not None and self.evaluation is not None:
            permis = niveau_permis(self.evaluation.borne_superieure)
            if _RANG_DES_NIVEAUX[self.niveau] > _RANG_DES_NIVEAUX[permis]:
                raise ValueError("regle.niveau : plus élevé que ne le permet l'évaluation")
        seuils = any(condition.seuil is not None for condition in self.conditions)
        if seuils and self.calibrage is None:
            raise ValueError("regle.calibrage : obligatoire pour une règle à seuil (ADR-0016)")
        # Les combinaisons de catégorie, fondement, direction et niveau sont celles d'un constat :
        # le modèle les vérifie ; une règle qui ne produirait aucun constat valide est refusée.
        Constat(
            self.phrase(dict.fromkeys(noms, "regle/1")),
            ("regle/1",),
            self.reference,
            self.module,
            self.fondement,
            self.categorie,
            self.direction,
            graduation=self.graduation,
        )

    @property
    def reference(self) -> ReferenceRegle:
        return ReferenceRegle(self.identifiant, self.version)

    @property
    def graduation(self) -> Graduation | None:
        """Graduation des constats de la règle : son niveau, évaluée si un taux est mesuré."""
        if self.categorie is not Categorie.INDICE or self.niveau is None:
            return None
        return Graduation(self.niveau, evaluee=self.evaluation is not None)

    @property
    def noms_des_parametres(self) -> tuple[str, ...]:
        if self.application is Application.MODULE:
            return self.parametres
        return tuple(c.parametre for c in self.conditions if c.parametre is not None)

    def phrase(self, parametres: Mapping[str, str]) -> Phrase:
        return Phrase(self.gabarit, parametres)

    def vers_dict(self) -> Document:
        """Forme du catalogue : celle du fichier TOML, envoyée aussi au processus de travail."""
        document: Document = {
            "identifiant": self.identifiant,
            "version": self.version,
            "module": self.module,
            "titre": self.titre,
            "description": self.description,
            "gabarit": self.gabarit,
            "phrase": dict(self.textes),
            "categorie": self.categorie,
            "direction": self.direction,
            "fondement": self.fondement,
            "limites": list(self.limites),
            "application": self.application,
        }
        if self.conditions:
            document["condition"] = [condition.vers_dict() for condition in self.conditions]
        if self.parametres:
            document["parametres"] = list(self.parametres)
        if self.niveau is not None:
            document["niveau"] = self.niveau
        if self.evaluation is not None:
            document["evaluation"] = self.evaluation.vers_dict()
        if self.calibrage is not None:
            document["calibrage"] = self.calibrage.vers_dict()
        return document

    @classmethod
    def depuis_dict(cls, document: Mapping[str, Any]) -> "Regle":
        """Construit une règle d'un document déjà validé par le schéma ``regles``."""
        evaluation = document.get("evaluation")
        calibrage = document.get("calibrage")
        niveau = document.get("niveau")
        return cls(
            identifiant=document["identifiant"],
            version=document["version"],
            module=document["module"],
            titre=document["titre"],
            description=document["description"],
            gabarit=document["gabarit"],
            textes=dict(document["phrase"]),
            categorie=Categorie(document["categorie"]),
            direction=Direction(document["direction"]),
            fondement=Fondement(document["fondement"]),
            limites=tuple(document["limites"]),
            application=Application(document["application"]),
            conditions=tuple(map(Condition.depuis_dict, document.get("condition", ()))),
            parametres=tuple(document.get("parametres", ())),
            niveau=None if niveau is None else Niveau(niveau),
            evaluation=None
            if evaluation is None
            else Evaluation(
                evaluation["taux_faux_positifs"],
                evaluation["effectif"],
                evaluation["borne_superieure"],
                evaluation["corpus"],
                date.fromisoformat(evaluation["date"]),
            ),
            calibrage=None
            if calibrage is None
            else Calibrage(
                Methode(calibrage["methode"]), calibrage["procedure"], calibrage.get("corpus")
            ),
        )


def _retenues(
    regle: Regle, par_nom: Mapping[str, Sequence[Observation]]
) -> tuple[tuple[str, ...], dict[str, str]] | None:
    """Données et paramètres du constat si chaque condition est satisfaite, sinon ``None``.

    Pour chaque condition, la première observation qui la satisfait, dans l'ordre où le module
    les a produites, est retenue : deux analyses retiennent les mêmes (NF-06).
    """
    donnees: dict[str, None] = {}
    parametres: dict[str, str] = {}
    for condition in regle.conditions:
        retenue = next(
            (o for o in par_nom.get(condition.observation, ()) if condition.satisfaite(o.valeur)),
            None,
        )
        if retenue is None:
            return None
        donnees[retenue.identifiant] = None
        if condition.parametre is not None:
            parametres[condition.parametre] = retenue.identifiant
    # Au plus 16 conditions (CONDITIONS_MAX), donc 16 données : sous la borne du modèle.
    return tuple(donnees), parametres


def appliquer(
    regles: Iterable[Regle], observations: Sequence[Observation]
) -> Iterator[tuple[Regle, tuple[str, ...], dict[str, str]]]:
    """Règles du moteur satisfaites par ces observations, avec données et paramètres.

    Une règle donne au plus un constat par module et par partie, dans l'ordre des règles reçu.
    """
    par_nom: dict[str, list[Observation]] = {}
    for observation in observations:
        par_nom.setdefault(observation.nom, []).append(observation)
    for regle in regles:
        if regle.application is not Application.MOTEUR:
            continue
        retenues = _retenues(regle, par_nom)
        if retenues is not None:
            yield regle, *retenues


def conforme(regle: Regle, constat: Constat) -> bool:
    """Vrai si le constat dit ce que fixe sa règle : le processus principal le vérifie."""
    return (
        constat.regle == regle.reference
        and constat.module == regle.module
        and constat.phrase.gabarit == regle.gabarit
        and set(constat.phrase.parametres) == set(regle.noms_des_parametres)
        and constat.categorie is regle.categorie
        and constat.direction is regle.direction
        and constat.fondement is regle.fondement
        and constat.graduation == regle.graduation
    )
