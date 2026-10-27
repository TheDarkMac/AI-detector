"""Restrictions sous macOS (ADR-0035, ADR-0079).

- Profil Seatbelt (``sandbox_init``) : tout est refusé, sauf la lecture de l'installation de
  Python et du paquet (un module peut encore importer à la demande) et l'écriture sur
  ``/dev/null``, où part la sortie d'erreur. Le fichier et les tubes, déjà ouverts, restent
  utilisables. Réseau, écriture, exécution d'un programme : refusés.
- Temps processeur (``RLIMIT_CPU``) et vidages (``RLIMIT_CORE`` à zéro).
- Mémoire : macOS n'applique pas de limite fiable ; le processus principal la surveille
  (``_orchestration/surveillance.py``). Elle n'est donc pas comptée ici parmi les manques.

``sandbox_init`` est marquée obsolète par Apple depuis 2011 mais reste la seule interface sans
privilège, employée par les navigateurs : si elle disparaît, les manques le disent.
"""

import ctypes
import os
import sys
from collections.abc import Iterable
from pathlib import Path

from voight_kampff._limites import TEMPS_PROCESSEUR
from voight_kampff._travail.restrictions.posix import limiter
from voight_kampff.rapport.modele import ManqueIsolation

__all__ = ["appliquer", "dossiers_lisibles", "profil"]

_MANQUES_SANS_SEATBELT = frozenset(
    {
        ManqueIsolation.RESEAU,
        ManqueIsolation.LECTURE,
        ManqueIsolation.ECRITURE,
        ManqueIsolation.NOUVEAUX_PROGRAMMES,
    }
)


def _chaine(texte: str) -> str:
    """Chaîne du langage des profils, guillemets et barres obliques inverses protégés."""
    return '"' + texte.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dossiers_lisibles() -> tuple[str, ...]:
    """Installation de Python et dossier du paquet, chemins réels (``/private/…`` compris)."""
    import voight_kampff

    candidats = (
        sys.prefix,
        sys.base_prefix,
        sys.exec_prefix,
        os.path.dirname(sys.executable),
        str(Path(voight_kampff.__file__).parent),
    )
    return tuple(dict.fromkeys(os.path.realpath(dossier) for dossier in candidats))


def profil(dossiers: Iterable[str]) -> str:
    """Profil Seatbelt : refus par défaut, lecture des seuls ``dossiers``."""
    lectures = " ".join(f"(subpath {_chaine(dossier)})" for dossier in dossiers)
    return "\n".join(
        (
            "(version 1)",
            "(deny default)",
            f"(allow file-read* {lectures})",
            '(allow file-write-data (literal "/dev/null"))',
            "(allow sysctl-read)",
        )
    )


def _seatbelt() -> bool:  # pragma: no cover - exécuté par la CI macOS
    try:
        bibliotheque = ctypes.CDLL("/usr/lib/libsandbox.1.dylib")
        initialiser = bibliotheque.sandbox_init
        liberer = bibliotheque.sandbox_free_error
    except (OSError, AttributeError):
        return False
    initialiser.argtypes = (ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p))
    initialiser.restype = ctypes.c_int
    liberer.argtypes = (ctypes.c_char_p,)
    erreur = ctypes.c_char_p()
    if initialiser(profil(dossiers_lisibles()).encode(), 0, ctypes.byref(erreur)):
        liberer(erreur)
        return False
    return True


def appliquer() -> set[ManqueIsolation]:  # pragma: no cover - exécuté par la CI macOS
    """Applique les restrictions ; renvoie celles qui manquent."""
    import resource

    manques: set[ManqueIsolation] = set()
    if not limiter(resource.RLIMIT_CPU, TEMPS_PROCESSEUR, marge=1):
        manques.add(ManqueIsolation.TEMPS)
    if not limiter(resource.RLIMIT_CORE, 0):
        manques.add(ManqueIsolation.VIDAGE_MEMOIRE)
    if not _seatbelt():
        manques |= _MANQUES_SANS_SEATBELT
    return manques
