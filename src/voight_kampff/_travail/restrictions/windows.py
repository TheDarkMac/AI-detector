"""Restrictions sous Windows (ADR-0035, ADR-0081).

- Job Object, auquel le processus de travail s'affecte lui-même : un seul processus actif,
  mémoire et temps processeur limités, arrêt à la première exception non traitée, aucun accès
  au presse-papiers ni au bureau des autres processus.
- Niveau d'intégrité abaissé à « bas » : l'écriture est refusée presque partout (sauf dans
  les rares dossiers marqués « bas », ``LocalLow`` par exemple).
- Rapport d'erreur Windows sans fenêtre (``SetErrorMode``).

Manquent toujours : le réseau (seul un conteneur d'application le bloque), la lecture (le
niveau bas n'interdit que l'écriture vers un niveau plus haut) et les vidages mémoire, que ces
réglages n'empêchent pas de façon vérifiable (ADR-0081).

L'interpréteur d'un environnement virtuel est un lanceur qui démarre le véritable
interpréteur : le Job Object couvre ce dernier, qui lit le fichier ; le lanceur, qui ne lit
rien, n'y est pas, et l'arrêt du lanceur entraîne celui du travail (ADR-0081).
"""

import ctypes
import sys
from ctypes import wintypes

from voight_kampff._limites import MEMOIRE_MAX, TEMPS_PROCESSEUR
from voight_kampff.rapport.modele import ManqueIsolation

__all__ = ["MANQUES_PERMANENTS", "appliquer", "limites_du_job"]

MANQUES_PERMANENTS = frozenset(
    {ManqueIsolation.RESEAU, ManqueIsolation.LECTURE, ManqueIsolation.VIDAGE_MEMOIRE}
)

# Job Object (winnt.h)
_JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
_JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_UILIMIT_ALL = 0x000000FF
_JOB_OBJECT_BASIC_UI_RESTRICTIONS = 4
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_CENTAINES_DE_NANOSECONDES = 10_000_000

# Jeton (winnt.h)
_TOKEN_QUERY = 0x0008
_TOKEN_ADJUST_DEFAULT = 0x0080
_TOKEN_INTEGRITY_LEVEL = 25
_SE_GROUP_INTEGRITY = 0x00000020
_NIVEAU_BAS = "S-1-16-4096"

# SetErrorMode
_SEM_FAILCRITICALERRORS = 0x0001
_SEM_NOGPFAULTERRORBOX = 0x0002
_SEM_NOOPENFILEERRORBOX = 0x8000


class _LimitesDeBase(ctypes.Structure):
    _fields_ = (
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    )


class _CompteursES(ctypes.Structure):
    _fields_ = tuple(
        (nom, ctypes.c_uint64)
        for nom in (
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        )
    )


class _LimitesEtendues(ctypes.Structure):
    """``JOBOBJECT_EXTENDED_LIMIT_INFORMATION``."""

    _fields_ = (
        ("BasicLimitInformation", _LimitesDeBase),
        ("IoInfo", _CompteursES),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    )


def _bibliotheque(nom: str) -> ctypes.CDLL:  # pragma: no cover - exécuté par la CI Windows
    """Bibliothèque de Windows, convention d'appel ``stdcall`` ; mypy tourne sous Linux."""
    dll: ctypes.CDLL = ctypes.WinDLL(nom, use_last_error=True)  # type: ignore[attr-defined,unused-ignore]
    return dll


class _SidEtAttributs(ctypes.Structure):
    _fields_ = (("Sid", ctypes.c_void_p), ("Attributes", ctypes.c_uint32))


def limites_du_job() -> _LimitesEtendues:
    """Limites posées sur le Job Object, en unités de Windows."""
    limites = _LimitesEtendues()
    base = limites.BasicLimitInformation
    base.LimitFlags = (
        _JOB_OBJECT_LIMIT_PROCESS_TIME
        | _JOB_OBJECT_LIMIT_ACTIVE_PROCESS
        | _JOB_OBJECT_LIMIT_PROCESS_MEMORY
        | _JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION
        | _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    base.ActiveProcessLimit = 1
    base.PerProcessUserTimeLimit = TEMPS_PROCESSEUR * _CENTAINES_DE_NANOSECONDES
    limites.ProcessMemoryLimit = MEMOIRE_MAX
    return limites


_job: int | None = None
"""Handle du Job Object, gardé ouvert jusqu'à la fin du processus (``KILL_ON_JOB_CLOSE``)."""


def _job_object() -> bool:  # pragma: no cover - exécuté par la CI Windows
    global _job  # handle propre au processus, ouvert une seule fois
    noyau = _bibliotheque("kernel32")
    noyau.CreateJobObjectW.restype = wintypes.HANDLE
    noyau.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    noyau.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    noyau.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    noyau.GetCurrentProcess.restype = wintypes.HANDLE
    job = noyau.CreateJobObjectW(None, None)
    if not job:
        return False
    limites = limites_du_job()
    interface = wintypes.DWORD(_JOB_OBJECT_UILIMIT_ALL)
    if not (
        noyau.SetInformationJobObject(
            job,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limites),
            ctypes.sizeof(limites),
        )
        and noyau.SetInformationJobObject(
            job,
            _JOB_OBJECT_BASIC_UI_RESTRICTIONS,
            ctypes.byref(interface),
            ctypes.sizeof(interface),
        )
        and noyau.AssignProcessToJobObject(job, noyau.GetCurrentProcess())
    ):
        noyau.CloseHandle(job)
        return False
    _job = job
    return True


def _niveau_bas() -> bool:  # pragma: no cover - exécuté par la CI Windows
    noyau = _bibliotheque("kernel32")
    securite = _bibliotheque("advapi32")
    noyau.GetCurrentProcess.restype = wintypes.HANDLE
    securite.OpenProcessToken.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    securite.ConvertStringSidToSidW.argtypes = (wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p))
    securite.GetLengthSid.argtypes = (ctypes.c_void_p,)
    securite.GetLengthSid.restype = wintypes.DWORD
    securite.SetTokenInformation.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    noyau.LocalFree.argtypes = (ctypes.c_void_p,)
    jeton = wintypes.HANDLE()
    if not securite.OpenProcessToken(
        noyau.GetCurrentProcess(), _TOKEN_QUERY | _TOKEN_ADJUST_DEFAULT, ctypes.byref(jeton)
    ):
        return False
    sid = ctypes.c_void_p()
    try:
        if not securite.ConvertStringSidToSidW(_NIVEAU_BAS, ctypes.byref(sid)):
            return False
        try:
            etiquette = _SidEtAttributs(sid.value, _SE_GROUP_INTEGRITY)
            taille = ctypes.sizeof(etiquette) + securite.GetLengthSid(sid)
            return bool(
                securite.SetTokenInformation(
                    jeton, _TOKEN_INTEGRITY_LEVEL, ctypes.byref(etiquette), taille
                )
            )
        finally:
            noyau.LocalFree(sid)
    finally:
        noyau.CloseHandle(jeton)


def appliquer() -> set[ManqueIsolation]:  # pragma: no cover - exécuté par la CI Windows
    """Applique les restrictions ; renvoie celles qui manquent."""
    if sys.platform != "win32":
        raise OSError("restrictions de Windows hors de Windows")
    noyau = _bibliotheque("kernel32")
    noyau.SetErrorMode(_SEM_FAILCRITICALERRORS | _SEM_NOGPFAULTERRORBOX | _SEM_NOOPENFILEERRORBOX)
    manques = set(MANQUES_PERMANENTS)
    if not _job_object():
        manques |= {
            ManqueIsolation.NOUVEAUX_PROGRAMMES,
            ManqueIsolation.MEMOIRE,
            ManqueIsolation.TEMPS,
        }
    if not _niveau_bas():
        manques.add(ManqueIsolation.ECRITURE)
    return manques
