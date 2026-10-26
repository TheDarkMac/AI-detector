"""Déroulé du processus de travail (ADR-0036) et acheminement vers les modules (ADR-0042).

1. Importer les modules livrés, tant que le système de fichiers est accessible.
2. Appliquer les restrictions (T14), se déclarer verrouillé, envoyer l'état de l'isolation :
   aucun octet du fichier n'a encore été lu.
3. Lire la configuration : modules actifs, dans l'ordre d'exécution.
4. Recalculer l'empreinte, identifier le format (T13), exécuter chaque module actif, envoyer
   ses résultats puis son message « module » (ADR-0062), et enfin les versions et la fin.

Une exception dans un module ne touche que ce module (NF-03, ADR-0060) ; toute autre erreur
arrête le processus, et le processus principal en fait une analyse non menée.
"""

import argparse
import importlib
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import BinaryIO

from voight_kampff import modules
from voight_kampff._protocole import (
    TAILLE_MAX_CONFIGURATION,
    TAILLE_MAX_SORTIE,
    encoder,
)
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte, LimiteDepassee
from voight_kampff._travail.fichier import Fichier, ouvrir_herite
from voight_kampff.rapport.modele import (
    VERSION_SCHEMA,
    Direction,
    EtatIsolation,
    ManqueIsolation,
    NiveauIsolation,
    NonMenee,
    RaisonNonMenee,
)

__all__ = [
    "Analyseur",
    "ModuleConfigure",
    "canal_du_protocole",
    "importer",
    "lire_configuration",
    "principal",
]

type Analyseur = Callable[[Contexte], None]

_RESERVE = 64 << 10
"""Part de la sortie gardée pour les messages du moteur après le dernier module."""


@dataclass(frozen=True, slots=True)
class ModuleConfigure:
    """Module actif, tel que le processus principal l'a lu dans son manifeste validé."""

    identifiant: str
    formats: frozenset[str]
    directions: frozenset[Direction]


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

    Appelé avant les restrictions : après, le code ne peut plus être lu sur le disque.
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
    l'outil, qui arrête le processus de travail.
    """
    ligne = entree.readline(TAILLE_MAX_CONFIGURATION + 1)
    if not ligne.endswith(b"\n") or len(ligne) > TAILLE_MAX_CONFIGURATION:
        raise ValueError("configuration : absente ou trop longue")
    document = json.loads(ligne)
    if document["version_schema"] != VERSION_SCHEMA:
        raise ValueError("configuration : version de schéma différente")
    return tuple(
        ModuleConfigure(
            identifiant=str(module["identifiant"]),
            formats=frozenset(str(f) for f in module["formats"]),
            directions=frozenset(Direction(d) for d in module["directions"]),
        )
        for module in document["modules"]
    )


def _identifier(_fichier: Fichier) -> str | None:
    """Format réel du fichier ; aucun avant T13, donc aucun module n'est applicable."""
    return None


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
    format_reel: str,
    taille: int,
    canal: _Canal,
) -> None:
    raison: RaisonNonMenee | None = RaisonNonMenee.ERREUR_MODULE
    contexte: Contexte | None = None
    if analyseur is not None:
        budget = TAILLE_MAX_SORTIE - canal.envoye - _RESERVE
        contexte = Contexte(
            module.identifiant, module.directions, fichier, format_reel, taille, budget
        )
        try:
            analyseur(contexte)
        except LimiteDepassee:
            raison = RaisonNonMenee.LIMITE_DEPASSEE
        except Exception:  # NF-03 : seul ce module est touché
            raison = RaisonNonMenee.ERREUR_MODULE
        else:
            raison = RaisonNonMenee.LIMITE_DEPASSEE if contexte.depasse else None
    if raison is None and contexte is not None:
        canal.envoyer(contexte.lignes)
    else:
        # Résultats écartés (ADR-0060) : rien de ce que le module a produit n'est envoyé.
        non_menee = NonMenee(raison or RaisonNonMenee.ERREUR_MODULE, module.identifiant)
        canal.message({"type": "non_menee", "non_menee": non_menee.vers_dict()})


def principal(
    argv: Sequence[str],
    entree: BinaryIO,
    sortie: BinaryIO,
    *,
    analyseurs: Mapping[str, Analyseur] | None = None,
    identifier: Callable[[Fichier], str | None] = _identifier,
) -> int:
    """Analyse le fichier transmis par le processus principal ; renvoie le code de sortie.

    ``analyseurs`` et ``identifier`` remplacent, pour les tests, les modules livrés et
    l'identification du format.
    """
    arguments = argparse.ArgumentParser(prog="voight_kampff._travail")
    arguments.add_argument("--descripteur", type=int, required=True)
    descripteur = arguments.parse_args(argv).descripteur

    echecs: frozenset[str] = frozenset()
    if analyseurs is None:
        analyseurs, echecs = importer()

    # Restrictions du système : T14. Jusque-là, aucune n'est appliquée et le rapport le dit.
    isolation = EtatIsolation(NiveauIsolation.REDUITE, tuple(ManqueIsolation))
    garde.verrouiller()
    canal = _Canal(sortie)
    canal.message(
        {"type": "isolation", "version_schema": VERSION_SCHEMA, "isolation": isolation.vers_dict()}
    )

    configures = lire_configuration(entree)
    fichier = Fichier(ouvrir_herite(descripteur))
    empreinte, taille = fichier.empreinte()
    format_reel = identifier(fichier)
    for module in configures:
        applicable = format_reel is not None and format_reel in module.formats
        if format_reel is not None and applicable:
            analyseur = None if module.identifiant in echecs else analyseurs.get(module.identifiant)
            _executer(module, analyseur, fichier, format_reel, taille, canal)
        canal.message({"type": "module", "module": module.identifiant, "applicable": applicable})
    # Versions des bibliothèques qui lisent le fichier : avec le premier module qui en emploie.
    canal.message({"type": "versions", "dependances": []})
    canal.message({"type": "fin", "empreinte": empreinte})
    return 0
