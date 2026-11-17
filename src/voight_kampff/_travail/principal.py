"""Déroulé du processus de travail (ADR-0036) et acheminement vers les modules (ADR-0042).

1. Importer les modules livrés, tant que le système de fichiers est accessible.
2. Appliquer les restrictions du système (ADR-0035, ADR-0079 à ADR-0081), se déclarer
   verrouillé, envoyer l'état de l'isolation : aucun octet du fichier n'a encore été lu.
3. Lire la configuration : modules actifs, dans l'ordre d'exécution, règles du catalogue qui
   relèvent d'eux (ADR-0084) et ancres de la liste de confiance C2PA (ADR-0171).
4. Identifier les formats et envoyer les parties reconnues (ADR-0070, ADR-0071). Un texte collé
   (``--texte``) suit la configuration sur l'entrée standard ; il est une seule partie « texte »
   s'il est de l'UTF-8, aucune sinon (ADR-0233).
5. Pour chaque partie du périmètre, exécuter chaque module actif, lui appliquer ses règles
   « moteur », envoyer ses résultats puis son message « module » (ADR-0062).
6. Reconnaître les contenus que des modules ont extraits de ces parties, envoyer les parties
   extraites, puis les analyser de la même façon (ADR-0224). Une partie extraite ne l'est pas
   à son tour.
7. Envoyer les versions des bibliothèques des modules actifs, puis l'empreinte du fichier
   recalculée en fin d'analyse (ES-08).

Une exception dans un module ne touche que ce module (NF-03, ADR-0060) ; une limite comptée
dépassée le rend non mené pour ``limite_depassee``, la mémoire du système épuisée pour
``memoire_depassee`` (ADR-0078). Toute autre erreur arrête le processus, et le processus
principal en fait une analyse non menée.
"""

import argparse
import importlib
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata
from typing import BinaryIO
from xml.parsers import expat

from voight_kampff import modules
from voight_kampff._limites import OCTETS_EXTRAITS_MAX, TAILLE_MAX_TEXTE
from voight_kampff._protocole import (
    TAILLE_MAX_CONFIGURATION,
    TAILLE_MAX_SORTIE,
    encoder,
)
from voight_kampff._regles import Regle
from voight_kampff._travail import garde, identification, restrictions
from voight_kampff._travail.contexte import Ancres, Contexte, Extraction, LimiteDepassee
from voight_kampff._travail.fichier import Fichier, FichierEnMemoire, ouvrir_herite
from voight_kampff.rapport.modele import (
    NOMBRE_MAX_EXTRAITES,
    VERSION_SCHEMA,
    Direction,
    EtatIsolation,
    Localisation,
    NonMenee,
    Origine,
    Partie,
    Plage,
    RaisonNonMenee,
)

__all__ = [
    "Analyseur",
    "Configuration",
    "Identifieur",
    "ModuleConfigure",
    "Reconnaisseur",
    "Restricteur",
    "canal_du_protocole",
    "importer",
    "lire_configuration",
    "lire_texte",
    "principal",
    "versions_des_bibliotheques",
]

type Analyseur = Callable[[Contexte], None]
type Identifieur = Callable[[Fichier, int], tuple[Partie, ...]]
type Restricteur = Callable[[], EtatIsolation]
type Reconnaisseur = Callable[[Fichier, int, int], tuple[str, int | None, bool] | None]

_RESERVE = 64 << 10
"""Part de la sortie gardée pour les messages du moteur après le dernier module."""


@dataclass(frozen=True, slots=True)
class ModuleConfigure:
    """Module actif, tel que le processus principal l'a lu dans son manifeste validé."""

    identifiant: str
    formats: frozenset[str]
    directions: frozenset[Direction]
    regles: tuple[Regle, ...] = ()
    """Règles du catalogue qui relèvent du module, dans l'ordre de leurs identifiants."""
    bibliotheques: frozenset[str] = frozenset()
    """Bibliothèques qui lisent le fichier pour le module (ADR-0120)."""
    extrait: frozenset[str] = frozenset()
    """Formats des contenus qu'il peut extraire de sa partie (ADR-0224)."""


@dataclass(frozen=True, slots=True)
class Configuration:
    """Configuration envoyée par le processus principal, une fois l'isolation annoncée."""

    modules: tuple[ModuleConfigure, ...]
    """Modules actifs, dans l'ordre d'exécution."""
    ancres: Ancres
    """Ancres de la liste de confiance C2PA, remises à chaque module (ADR-0171)."""
    texte: int | None = None
    """Octets du texte collé qui suivent la configuration ; ``None`` pour un fichier (ADR-0233)."""


def versions_des_bibliotheques() -> dict[str, str]:
    """Version réelle de chaque bibliothèque qu'un manifeste peut citer (ADR-0120).

    Lue avant les restrictions, comme les modules : après, rien n'est plus chargé du disque.
    La version de ``c2pa-python`` est celle de son paquet installé, lue sans charger sa
    bibliothèque native ; chaque version embarque une seule version de c2pa-rs (ADR-0164).
    """
    return {
        "c2pa-python": metadata.version("c2pa-python"),
        "expat": ".".join(str(n) for n in expat.version_info),
        "numpy": metadata.version("numpy"),
    }


def canal_du_protocole() -> BinaryIO:
    """Réserve la sortie standard au protocole et renvoie le flux qui y écrit.

    Un module qui afficherait du texte écrirait ensuite sur la sortie d'erreur, que le processus
    principal ne lit pas (ES-15) : il ne peut pas glisser une ligne dans le protocole.
    """
    canal = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    return canal


def importer() -> tuple[dict[str, Analyseur], frozenset[str]]:
    """Importe les modules livrés ; renvoie leurs analyseurs et ceux qui n'ont pas pu l'être.

    Appelé avant les restrictions : après, le code ne peut plus être lu sur le disque. Un
    module importe donc à son chargement tout ce dont il aura besoin (ADR-0079).
    """
    analyseurs: dict[str, Analyseur] = {}
    echecs: set[str] = set()
    for dossier in modules.dossiers():
        try:
            code = importlib.import_module(f"{modules.__name__}.{dossier.name}")
            analyseur = code.analyser
            if not callable(analyseur):
                raise TypeError("analyser n'est pas appelable")
        except Exception:
            # Le module en échec sera non mené ; les autres continuent (NF-03).
            echecs.add(dossier.name)
        else:
            analyseurs[dossier.name] = analyseur
    return analyseurs, frozenset(echecs)


def lire_configuration(entree: BinaryIO) -> Configuration:
    """Lit la configuration envoyée par le processus principal (ADR-0065).

    Elle vient d'un processus de confiance : une configuration mal formée est un défaut de
    l'outil, qui arrête le processus de travail. Les règles, déjà validées par le principal, sont
    reconstruites ici, ce qui compile de nouveau leurs motifs (ADR-0039).
    """
    ligne = entree.readline(TAILLE_MAX_CONFIGURATION + 1)
    if not ligne.endswith(b"\n") or len(ligne) > TAILLE_MAX_CONFIGURATION:
        raise ValueError("configuration : absente ou trop longue")
    document = json.loads(ligne)
    if document["version_schema"] != VERSION_SCHEMA:
        raise ValueError("configuration : version de schéma différente")
    regles: dict[str, list[Regle]] = {}
    for regle in map(Regle.depuis_dict, document["regles"]):
        regles.setdefault(regle.module, []).append(regle)
    modules = tuple(
        ModuleConfigure(
            identifiant=str(module["identifiant"]),
            formats=frozenset(str(f) for f in module["formats"]),
            directions=frozenset(Direction(d) for d in module["directions"]),
            regles=tuple(regles.get(str(module["identifiant"]), ())),
            bibliotheques=frozenset(str(b) for b in module["bibliotheques"]),
            extrait=frozenset(str(f) for f in module["extrait"]),
        )
        for module in document["modules"]
    )
    confiance = document["confiance"]
    ancres = Ancres(str(confiance["signataires"]), str(confiance["horodatage"]))
    texte = document.get("texte")
    if texte is not None and (type(texte) is not int or not 0 < texte <= TAILLE_MAX_TEXTE):
        raise ValueError("configuration : longueur du texte collé hors bornes")
    return Configuration(modules, ancres, texte)


def lire_texte(entree: BinaryIO, longueur: int) -> bytes:
    """Lit le texte collé qui suit la configuration : exactement ``longueur`` octets."""
    morceaux: list[bytes] = []
    reste = longueur
    while reste and (morceau := entree.read(reste)):
        morceaux.append(morceau)
        reste -= len(morceau)
    if reste:
        raise ValueError("texte collé : incomplet")
    return b"".join(morceaux)


class _Canal:
    """Sortie du protocole : une ligne par message, comptée contre la taille maximale."""

    __slots__ = ("_sortie", "envoye")

    def __init__(self, sortie: BinaryIO) -> None:
        self._sortie = sortie
        self.envoye = 0

    def envoyer(self, lignes: Sequence[bytes]) -> None:
        for ligne in lignes:
            self._sortie.write(ligne)
            self.envoye += len(ligne)
        self._sortie.flush()

    def message(self, message: Mapping[str, object]) -> None:
        self.envoyer((encoder(message),))


@dataclass(frozen=True, slots=True)
class _Execution:
    """Ce que le moteur garde d'un module exécuté sur une partie."""

    numero: int
    """Numéro de sa dernière observation ; la partie suivante continue à partir de lui."""
    extractions: tuple[Extraction, ...] = ()
    """Contenus à acheminer ; aucun si ses résultats ont été écartés (ADR-0060)."""
    refusee: Localisation | None = None
    """Première extraction refusée faute de place (ADR-0226)."""


def _executer(
    module: ModuleConfigure,
    analyseur: Analyseur | None,
    fichier: Fichier,
    partie: Partie,
    canal: _Canal,
    numero: int,
    ancres: Ancres,
    places: tuple[int, int],
) -> _Execution:
    """Exécute le module sur une partie ; renvoie ce qu'il laisse au moteur.

    ``places`` : parties extraites que le fichier peut encore recevoir, et octets avant leur
    seuil (ADR-0226).
    """
    raison: RaisonNonMenee | None = RaisonNonMenee.ERREUR_MODULE
    contexte: Contexte | None = None
    if analyseur is not None:
        budget = TAILLE_MAX_SORTIE - canal.envoye - _RESERVE
        contexte = Contexte(
            module.identifiant,
            module.directions,
            fichier,
            partie,
            budget,
            numero,
            module.regles,
            ancres,
            module.extrait,
            *places,
        )
        try:
            analyseur(contexte)
            contexte.appliquer_catalogue()
        except LimiteDepassee:
            raison = RaisonNonMenee.LIMITE_DEPASSEE
        except MemoryError:  # limite du système (ADR-0077) : hors garantie (ADR-0078)
            raison = RaisonNonMenee.MEMOIRE_DEPASSEE
        except Exception:  # NF-03 : seul ce module est touché
            raison = RaisonNonMenee.ERREUR_MODULE
        else:
            raison = RaisonNonMenee.LIMITE_DEPASSEE if contexte.depasse else None
    if raison is None and contexte is not None:
        canal.envoyer(contexte.lignes)
        return _Execution(contexte.numero, contexte.extractions, contexte.refusee)
    # Résultats écartés (ADR-0060) : rien de ce que le module a produit n'est envoyé.
    raison = raison or RaisonNonMenee.ERREUR_MODULE
    non_menee = NonMenee(raison, module.identifiant, partie=partie.rang)
    canal.message({"type": "non_menee", "non_menee": non_menee.vers_dict()})
    return _Execution(numero if contexte is None else contexte.numero)


class _Deroule:
    """Exécution des modules actifs, partie par partie, et acheminement des extractions."""

    def __init__(
        self,
        configuration: Configuration,
        analyseurs: Mapping[str, Analyseur],
        echecs: frozenset[str],
        fichier: Fichier,
        canal: _Canal,
        reconnaitre: Reconnaisseur,
        premier_rang: int,
    ) -> None:
        self._configuration = configuration
        self._analyseurs = analyseurs
        self._echecs = echecs
        self._fichier = fichier
        self._canal = canal
        self._reconnaitre = reconnaitre
        self._premier_rang = premier_rang
        """Rang de la première partie extraite : à la suite des parties reconnues."""
        self._numeros = dict.fromkeys((m.identifiant for m in configuration.modules), 0)
        self.extraites: list[Partie] = []
        self._declarees = 0
        """Contenus acceptés par un contexte, reconnus ou non : ils comptent contre les places."""
        self._octets = 0
        """Leurs octets, cumulés contre ``OCTETS_EXTRAITS_MAX``."""

    def partie(self, partie: Partie) -> None:
        """Chaque module actif sur une partie du périmètre ; les contenus extraits d'une partie
        reconnue sont reconnus aussitôt, et rangés pour être analysés après toutes les autres."""
        for module in self._configuration.modules:
            applicable = partie.format in module.formats
            if applicable:
                analyseur = (
                    None
                    if module.identifiant in self._echecs
                    else self._analyseurs.get(module.identifiant)
                )
                places = (
                    (0, 0)
                    if partie.origine
                    else (
                        NOMBRE_MAX_EXTRAITES - self._declarees,
                        OCTETS_EXTRAITS_MAX - self._octets,
                    )
                )
                execution = _executer(
                    module,
                    analyseur,
                    self._fichier,
                    partie,
                    self._canal,
                    self._numeros[module.identifiant],
                    self._configuration.ancres,
                    places,
                )
                self._numeros[module.identifiant] = execution.numero
                self._acheminer(module.identifiant, partie, execution)
            self._canal.message(
                {
                    "type": "module",
                    "module": module.identifiant,
                    "partie": partie.rang,
                    "applicable": applicable,
                }
            )

    def _acheminer(self, module: str, contenant: Partie, execution: _Execution) -> None:
        """Reconnaît chaque contenu extrait dans sa plage ; ceux qui ne sont pas du format
        attendu sont déclarés non menés pour format partiel (ADR-0224)."""
        for extraction in execution.extractions:
            plage = extraction.octets
            self._declarees += 1
            self._octets += plage.longueur
            reconnu = self._reconnaitre(self._fichier, plage.debut, plage.longueur)
            if reconnu is None or reconnu[0] != extraction.format:
                self._non_mener(RaisonNonMenee.FORMAT_PARTIEL, extraction.localisation, contenant)
                continue
            nature, longueur, tronquee = reconnu
            self.extraites.append(
                Partie(
                    self._premier_rang + len(self.extraites),
                    nature,
                    Plage(plage.debut, plage.longueur if longueur is None else longueur),
                    fin_connue=longueur is not None,
                    tronquee=tronquee,
                    origine=Origine(contenant.rang, module, extraction.localisation),
                )
            )
        if execution.refusee is not None:
            self._non_mener(RaisonNonMenee.LIMITE_DEPASSEE, execution.refusee, contenant)

    def _non_mener(
        self, raison: RaisonNonMenee, localisation: Localisation, contenant: Partie
    ) -> None:
        non_menee = NonMenee(raison, None, localisation, contenant.rang)
        self._canal.message({"type": "non_menee", "non_menee": non_menee.vers_dict()})


def principal(
    argv: Sequence[str],
    entree: BinaryIO,
    sortie: BinaryIO,
    *,
    analyseurs: Mapping[str, Analyseur] | None = None,
    identifier: Identifieur = identification.identifier,
    identifier_texte: Identifieur = identification.identifier_texte,
    reconnaitre: Reconnaisseur = identification.reconnaitre,
    restreindre: Restricteur = restrictions.appliquer,
) -> int:
    """Analyse le fichier transmis par le processus principal ; renvoie le code de sortie.

    ``analyseurs``, ``identifier`` et ``reconnaitre`` remplacent, pour les tests, les modules
    livrés, l'identification du format et celle d'un contenu extrait ; ``restreindre``, les
    restrictions, que les tests du déroulé ne peuvent pas appliquer à leur propre processus.
    """
    arguments = argparse.ArgumentParser(prog="voight_kampff._travail")
    source = arguments.add_mutually_exclusive_group(required=True)
    source.add_argument("--descripteur", type=int)
    source.add_argument("--texte", action="store_true")
    lus = arguments.parse_args(argv)

    echecs: frozenset[str] = frozenset()
    if analyseurs is None:
        analyseurs, echecs = importer()
    bibliotheques = versions_des_bibliotheques()

    isolation = restreindre()
    garde.verrouiller()
    canal = _Canal(sortie)
    canal.message(
        {"type": "isolation", "version_schema": VERSION_SCHEMA, "isolation": isolation.vers_dict()}
    )

    configuration = lire_configuration(entree)
    if lus.texte != (configuration.texte is not None):
        raise ValueError("configuration : texte collé annoncé sans --texte, ou l'inverse")
    if configuration.texte is not None:
        fichier: Fichier = FichierEnMemoire(lire_texte(entree, configuration.texte))
        parties = identifier_texte(fichier, fichier.taille())
    else:
        fichier = Fichier(ouvrir_herite(lus.descripteur))
        parties = identifier(fichier, fichier.taille())
    canal.message({"type": "identification", "parties": [p.vers_dict() for p in parties]})
    deroule = _Deroule(
        configuration, analyseurs, echecs, fichier, canal, reconnaitre, len(parties) + 1
    )
    for partie in parties:
        if partie.dans_perimetre:  # sinon déclarée non analysée par le processus principal
            deroule.partie(partie)
    extraites = tuple(deroule.extraites)
    if extraites:
        canal.message({"type": "extraction", "parties": [p.vers_dict() for p in extraites]})
        for extraite in extraites:
            deroule.partie(extraite)
    # Versions des bibliothèques des modules actifs, dans l'ordre de leurs noms (ADR-0120).
    noms = sorted({nom for module in configuration.modules for nom in module.bibliotheques})
    dependances = [{"nom": nom, "version": bibliotheques[nom]} for nom in noms]
    canal.message({"type": "versions", "dependances": dependances})
    # Empreinte de ce qui a été analysé, recalculée après les modules (ES-08).
    empreinte, _taille = fichier.empreinte()
    canal.message({"type": "fin", "empreinte": empreinte})
    return 0
