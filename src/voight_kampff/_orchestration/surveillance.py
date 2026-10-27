"""Mémoire du processus de travail surveillée par le processus principal, sous macOS (ADR-0080).

macOS n'applique pas de limite fiable à la mémoire d'un processus (ADR-0035). Le processus
principal mesure donc l'empreinte physique du travail (``proc_pid_rusage``, celle qu'emploie le
système pour arbitrer la mémoire) pendant qu'il attend ses messages, et l'arrête au-delà de la
limite. C'est une surveillance, pas une limite stricte : entre deux mesures, le travail peut
dépasser la limite de ce qu'il alloue en une période.

Linux et Windows limitent la mémoire eux-mêmes (ADR-0079, ADR-0081) : rien n'y est surveillé.
"""

import ctypes
import sys
from collections.abc import Callable

from voight_kampff._limites import MEMOIRE_MAX

__all__ = ["PERIODE", "memoire_depassee"]

PERIODE = 0.1
"""Intervalle entre deux mesures, en secondes."""

_RUSAGE_INFO_V0 = 0


class _Ressources(ctypes.Structure):
    """``struct rusage_info_v0`` (``sys/resource.h`` de macOS)."""

    _fields_ = (
        ("uuid", ctypes.c_uint8 * 16),
        ("temps_utilisateur", ctypes.c_uint64),
        ("temps_systeme", ctypes.c_uint64),
        ("reveils_inactifs", ctypes.c_uint64),
        ("reveils_interruption", ctypes.c_uint64),
        ("pages_lues", ctypes.c_uint64),
        ("memoire_verrouillee", ctypes.c_uint64),
        ("memoire_residente", ctypes.c_uint64),
        ("empreinte_physique", ctypes.c_uint64),
        ("debut", ctypes.c_uint64),
        ("fin", ctypes.c_uint64),
    )


def memoire_depassee(pid: int) -> Callable[[], bool] | None:
    """Fonction qui dit si le processus ``pid`` dépasse la limite de mémoire.

    ``None`` hors macOS, où le système limite la mémoire, ou si la mesure est impossible : le
    processus principal note alors la mémoire parmi les restrictions manquantes.
    """
    if sys.platform != "darwin":
        return None
    return _sous_macos(pid)  # pragma: no cover - exécuté par la CI macOS


def _sous_macos(pid: int) -> Callable[[], bool] | None:  # pragma: no cover - CI macOS
    try:
        mesurer = ctypes.CDLL(None, use_errno=True).proc_pid_rusage
    except (OSError, AttributeError):
        return None
    mesurer.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.POINTER(_Ressources))
    mesurer.restype = ctypes.c_int

    def depassee() -> bool:
        ressources = _Ressources()
        if mesurer(pid, _RUSAGE_INFO_V0, ctypes.byref(ressources)):
            return False  # processus déjà terminé : la lecture de sa sortie le constatera
        return bool(ressources.empreinte_physique > MEMOIRE_MAX)

    if mesurer(pid, _RUSAGE_INFO_V0, ctypes.byref(_Ressources())):
        return None
    return depassee
