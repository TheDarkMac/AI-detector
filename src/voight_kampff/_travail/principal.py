"""Déroulé du processus de travail (ADR-0036) et acheminement vers les modules (ADR-0042).

1. Importer les modules livrés, tant que le système de fichiers est accessible.
2. Appliquer les restrictions du système (ADR-0035, ADR-0079 à ADR-0081), se déclarer
   verrouillé, envoyer l'état de l'isolation : aucun octet du fichier n'a encore été lu.
3. Lire la configuration : modules actifs, dans l'ordre d'exécution, et règles du catalogue
   qui relèvent d'eux (ADR-0084).
4. Identifier les formats et envoyer les parties reconnues (ADR-0070, ADR-0071).
5. Pour chaque partie du périmètre, exécuter chaque module actif, lui appliquer ses règles
   « moteur », envoyer ses résultats puis son message « module » (ADR-0062).
6. Envoyer les versions des bibliothèques des modules actifs, puis l'empreinte du fichier
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
from typing import BinaryIO
from xml.parsers import expat

from voight_kampff import modules
from voight_kampff._protocole import (
    TAILLE_MAX_CONFIGURATION,
    TAILLE_MAX_SORTIE,
    encoder,
)
from voight_kampff._regles import Regle
from voight_kampff._travail import garde, identification, restrictions
from voight_kampff._travail.contexte import Contexte, LimiteDepassee
from voight_kampff._travail.fichier import Fichier, ouvrir_herite
from voight_kampff.rapport.modele import (
    VERSION_SCHEMA,
    Direction,
    EtatIsolation,
    NonMenee,
    Partie,
    RaisonNonMenee,
)

__all__ = [
    "Analyseur",
    "Identifieur",
    "ModuleConfigure",
    "Restricteur",
    "canal_du_protocole",
    "importer",
    "lire_configuration",
    "principal",
    "versions_des_bibliotheques",
]

type Analyseur = Callable[[Contexte], None]
type Identifieur = Callable[[Fichier, int], tuple[Partie, ...]]
type Restricteur = Callable[[], EtatIsolation]

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


def versions_des_bibliotheques() -> dict[str, str]:
    """Version réelle de chaque bibliothèque qu'un manifeste peut citer (ADR-0120).

    Lue avant les restrictions, comme les modules : après, rien n'est plus chargé du disque.
    """
    return {"expat": ".".join(str(n) for n in expat.version_info)}


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


def lire_configuration(entree: BinaryIO) -> tuple[ModuleConfigure, ...]:
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
    return tuple(
        ModuleConfigure(
            identifiant=str(module["identifiant"]),
            formats=frozenset(str(f) for f in module["formats"]),
            directions=frozenset(Direction(d) for d in module["directions"]),
            regles=tuple(regles.get(str(module["identifiant"]), ())),
            bibliotheques=frozenset(str(b) for b in module["bibliotheques"]),
        )
        for module in document["modules"]
    )


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


def _executer(
    module: ModuleConfigure,
    analyseur: Analyseur | None,
    fichier: Fichier,
    partie: Partie,
    canal: _Canal,
    numero: int,
) -> int:
    """Exécute le module sur une partie ; renvoie le numéro de sa dernière observation."""
    raison: RaisonNonMenee | None = RaisonNonMenee.ERREUR_MODULE
    contexte: Contexte | None = None
    if analyseur is not None:
        budget = TAILLE_MAX_SORTIE - canal.envoye - _RESERVE
        contexte = Contexte(
            module.identifiant, module.directions, fichier, partie, budget, numero, module.regles
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
    else:
        # Résultats écartés (ADR-0060) : rien de ce que le module a produit n'est envoyé.
        raison = raison or RaisonNonMenee.ERREUR_MODULE
        non_menee = NonMenee(raison, module.identifiant, partie=partie.rang)
        canal.message({"type": "non_menee", "non_menee": non_menee.vers_dict()})
    return numero if contexte is None else contexte.numero


def principal(
    argv: Sequence[str],
    entree: BinaryIO,
    sortie: BinaryIO,
    *,
    analyseurs: Mapping[str, Analyseur] | None = None,
    identifier: Identifieur = identification.identifier,
    restreindre: Restricteur = restrictions.appliquer,
) -> int:
    """Analyse le fichier transmis par le processus principal ; renvoie le code de sortie.

    ``analyseurs`` et ``identifier`` remplacent, pour les tests, les modules livrés et
    l'identification du format ; ``restreindre``, les restrictions, que les tests du
    déroulé ne peuvent pas appliquer à leur propre processus.
    """
    arguments = argparse.ArgumentParser(prog="voight_kampff._travail")
    arguments.add_argument("--descripteur", type=int, required=True)
    descripteur = arguments.parse_args(argv).descripteur

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

    configures = lire_configuration(entree)
    fichier = Fichier(ouvrir_herite(descripteur))
    parties = identifier(fichier, fichier.taille())
    canal.message({"type": "identification", "parties": [p.vers_dict() for p in parties]})
    numeros = dict.fromkeys((module.identifiant for module in configures), 0)
    for partie in parties:
        if not partie.dans_perimetre:
            continue  # déclarée non analysée par le processus principal
        for module in configures:
            applicable = partie.format in module.formats
            if applicable:
                analyseur = (
                    None if module.identifiant in echecs else analyseurs.get(module.identifiant)
                )
                numeros[module.identifiant] = _executer(
                    module, analyseur, fichier, partie, canal, numeros[module.identifiant]
                )
            canal.message(
                {
                    "type": "module",
                    "module": module.identifiant,
                    "partie": partie.rang,
                    "applicable": applicable,
                }
            )
    # Versions des bibliothèques des modules actifs, dans l'ordre de leurs noms (ADR-0120).
    noms = sorted({nom for module in configures for nom in module.bibliotheques})
    dependances = [{"nom": nom, "version": bibliotheques[nom]} for nom in noms]
    canal.message({"type": "versions", "dependances": dependances})
    # Empreinte de ce qui a été analysé, recalculée après les modules (ES-08).
    empreinte, _taille = fichier.empreinte()
    canal.message({"type": "fin", "empreinte": empreinte})
    return 0
