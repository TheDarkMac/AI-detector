"""Restrictions sous Linux, système de référence (ADR-0035, ADR-0078).

Dans l'ordre :

1. limites de ressources : mémoire (``RLIMIT_AS``), temps processeur (``RLIMIT_CPU``),
   vidages (``RLIMIT_CORE`` à zéro, ``PR_SET_DUMPABLE`` à zéro) ;
2. ``PR_SET_NO_NEW_PRIVS``, sans lequel ni Landlock ni seccomp ne s'appliquent sans privilège ;
3. Landlock, sans aucune règle : aucun accès au système de fichiers, aucune connexion TCP
   (ABI 4), ni signal ni socket abstraite hors du domaine (ABI 6). Le fichier et les tubes,
   déjà ouverts, restent utilisables ;
4. seccomp : création de socket, exécution d'un programme, ``ptrace`` et ``io_uring`` refusés
   (``EPERM``) ; un appel d'une autre architecture que celle du processus le tue.

Les fonctions qui construisent les attributs de Landlock et le programme seccomp sont pures et
testées dans le processus des tests ; celles qui appellent le système ne s'exécutent que dans
un processus de travail, dont l'effet est vérifié par ``tests/test_isolation.py``.
"""

import ctypes
import os
import platform
import struct
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from voight_kampff._limites import MEMOIRE_MAX, TEMPS_PROCESSEUR
from voight_kampff._travail.restrictions.posix import limiter
from voight_kampff.rapport.modele import ManqueIsolation

__all__ = [
    "ARCHITECTURES",
    "Architecture",
    "appliquer",
    "attributs_landlock",
    "droits_landlock",
    "encoder_programme",
    "manques_landlock",
    "programme_seccomp",
]

type Instruction = tuple[int, int, int, int]
"""Instruction BPF : code, saut si vrai, saut si faux, constante."""

# prctl(2)
_PR_SET_DUMPABLE = 4
_PR_SET_SECCOMP = 22
_PR_SET_NO_NEW_PRIVS = 38
_SECCOMP_MODE_FILTER = 2

# Landlock : mêmes numéros d'appel sur toutes les architectures
_LANDLOCK_CREATE_RULESET = 444
_LANDLOCK_RESTRICT_SELF = 446
_LANDLOCK_CREATE_RULESET_VERSION = 1

# BPF (linux/filter.h) et seccomp (linux/seccomp.h)
_BPF_LD_W_ABS = 0x20
_BPF_JEQ_K = 0x15
_BPF_JGE_K = 0x35
_BPF_RET_K = 0x06
_SECCOMP_RET_KILL_PROCESS = 0x80000000
_SECCOMP_RET_ERRNO = 0x00050000
_SECCOMP_RET_ALLOW = 0x7FFF0000
_EPERM = 1
_DECALAGE_NUMERO = 0
_DECALAGE_ARCHITECTURE = 4
_APPELS_X32 = 0x40000000
"""Bit des appels de l'ABI x32 sous x86-64 : refusés, ils contourneraient la liste."""

_APPELS_REFUSES = (
    "socket",
    "socketpair",
    "execve",
    "execveat",
    "ptrace",
    "process_vm_readv",
    "process_vm_writev",
    "io_uring_setup",
    "io_uring_enter",
    "io_uring_register",
)
"""Réseau, nouveaux programmes, accès à un autre processus ; ``io_uring`` crée des sockets
sans passer par seccomp."""


@dataclass(frozen=True, slots=True)
class Architecture:
    """Ce que seccomp doit savoir d'une architecture : son identifiant d'audit, ses appels."""

    audit: int
    appels: Mapping[str, int]
    x32: bool = False


ARCHITECTURES = {
    "x86_64": Architecture(
        audit=0xC000003E,
        appels={
            "socket": 41,
            "socketpair": 53,
            "execve": 59,
            "execveat": 322,
            "ptrace": 101,
            "process_vm_readv": 310,
            "process_vm_writev": 311,
            "io_uring_setup": 425,
            "io_uring_enter": 426,
            "io_uring_register": 427,
        },
        x32=True,
    ),
    "aarch64": Architecture(
        audit=0xC00000B7,
        appels={
            "socket": 198,
            "socketpair": 199,
            "execve": 221,
            "execveat": 281,
            "ptrace": 117,
            "process_vm_readv": 270,
            "process_vm_writev": 271,
            "io_uring_setup": 425,
            "io_uring_enter": 426,
            "io_uring_register": 427,
        },
    ),
}
"""Architectures 64 bits de la V1 ; ailleurs, seccomp n'est pas appliqué et le rapport le dit."""


# Landlock


def droits_landlock(abi: int) -> tuple[int, int, int]:
    """Droits gérés selon l'ABI : système de fichiers, réseau, portée.

    Gérés sans règle qui les accorde, ils sont tous refusés. ABI 1 : treize droits sur les
    fichiers ; 2 : renommage entre dossiers ; 3 : troncature ; 4 : TCP ; 5 : ``ioctl`` des
    périphériques ; 6 : signaux et sockets abstraites hors du domaine.
    """
    if abi < 1:
        return 0, 0, 0
    fichiers = (1 << {1: 13, 2: 14, 3: 15, 4: 15}.get(abi, 16)) - 1
    reseau = 0b11 if abi >= 4 else 0
    portee = 0b11 if abi >= 6 else 0
    return fichiers, reseau, portee


def attributs_landlock(abi: int) -> bytes:
    """``struct landlock_ruleset_attr`` à la taille que le noyau de cette ABI connaît."""
    fichiers, reseau, portee = droits_landlock(abi)
    if abi >= 6:
        return struct.pack("=QQQ", fichiers, reseau, portee)
    if abi >= 4:
        return struct.pack("=QQ", fichiers, reseau)
    return struct.pack("=Q", fichiers)


def manques_landlock(abi: int) -> frozenset[ManqueIsolation]:
    """Ce qui manque au système de fichiers : avant l'ABI 3, la troncature reste permise."""
    if abi < 1:
        return frozenset({ManqueIsolation.LECTURE, ManqueIsolation.ECRITURE})
    if abi < 3:
        return frozenset({ManqueIsolation.ECRITURE})
    return frozenset()


# seccomp


def programme_seccomp(architecture: Architecture) -> list[Instruction]:
    """Filtre seccomp : refuse les appels de :data:`_APPELS_REFUSES`, permet les autres.

    ::

        charger l'architecture ; autre que celle attendue : tuer
        charger le numéro ; [x86-64 : appel x32 : tuer]
        pour chaque appel refusé : égal : EPERM
        permettre
    """
    refuses = [architecture.appels[nom] for nom in _APPELS_REFUSES]
    entete = 4 if architecture.x32 else 3
    permettre = entete + len(refuses)
    refuser, tuer = permettre + 1, permettre + 2

    def saut(depuis: int, vers: int) -> int:
        return vers - depuis - 1

    programme: list[Instruction] = [
        (_BPF_LD_W_ABS, 0, 0, _DECALAGE_ARCHITECTURE),
        (_BPF_JEQ_K, 0, saut(1, tuer), architecture.audit),
        (_BPF_LD_W_ABS, 0, 0, _DECALAGE_NUMERO),
    ]
    if architecture.x32:
        programme.append((_BPF_JGE_K, saut(3, tuer), 0, _APPELS_X32))
    for rang, numero in enumerate(refuses, start=entete):
        programme.append((_BPF_JEQ_K, saut(rang, refuser), 0, numero))
    programme += [
        (_BPF_RET_K, 0, 0, _SECCOMP_RET_ALLOW),
        (_BPF_RET_K, 0, 0, _SECCOMP_RET_ERRNO | _EPERM),
        (_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
    ]
    return programme


def encoder_programme(programme: Sequence[Instruction]) -> bytes:
    """Tableau de ``struct sock_filter`` : code sur 16 bits, deux sauts sur 8, constante sur 32."""
    return b"".join(struct.pack("=HBBI", *instruction) for instruction in programme)


def architecture_courante() -> Architecture | None:
    """Architecture du processus, si seccomp sait la filtrer ; un Python 32 bits n'en a pas."""
    if sys.maxsize <= 1 << 32:
        return None
    return ARCHITECTURES.get(platform.machine())


# Application : seulement dans un processus de travail


class _Programme(ctypes.Structure):
    _fields_ = (("longueur", ctypes.c_ushort), ("filtre", ctypes.c_void_p))


def _landlock(libc: ctypes.CDLL) -> frozenset[ManqueIsolation]:  # pragma: no cover - travail
    appel = libc.syscall
    abi = appel(
        ctypes.c_long(_LANDLOCK_CREATE_RULESET),
        None,
        ctypes.c_long(0),
        ctypes.c_long(_LANDLOCK_CREATE_RULESET_VERSION),
    )
    if abi < 1:  # noyau sans Landlock, ou Landlock désactivé
        return manques_landlock(0)
    attributs = attributs_landlock(abi)
    tampon = ctypes.create_string_buffer(attributs, len(attributs))
    regles = appel(
        ctypes.c_long(_LANDLOCK_CREATE_RULESET),
        tampon,
        ctypes.c_long(len(attributs)),
        ctypes.c_long(0),
    )
    if regles < 0:
        return manques_landlock(0)
    try:
        if appel(ctypes.c_long(_LANDLOCK_RESTRICT_SELF), ctypes.c_long(regles), ctypes.c_long(0)):
            return manques_landlock(0)
    finally:
        os.close(regles)
    return manques_landlock(abi)


def _seccomp(libc: ctypes.CDLL) -> frozenset[ManqueIsolation]:  # pragma: no cover - travail
    manques = frozenset({ManqueIsolation.RESEAU, ManqueIsolation.NOUVEAUX_PROGRAMMES})
    architecture = architecture_courante()
    if architecture is None:
        return manques
    octets = encoder_programme(programme_seccomp(architecture))
    filtre = ctypes.create_string_buffer(octets, len(octets))
    programme = _Programme(len(octets) // 8, ctypes.addressof(filtre))
    if libc.prctl(_PR_SET_SECCOMP, _SECCOMP_MODE_FILTER, ctypes.addressof(programme), 0, 0):
        return manques
    return frozenset()


def appliquer() -> set[ManqueIsolation]:  # pragma: no cover - exécuté dans le travail
    """Applique les restrictions ; renvoie celles qui manquent."""
    import resource

    manques: set[ManqueIsolation] = set()
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int] + [ctypes.c_ulong] * 4
    libc.prctl.restype = ctypes.c_int
    libc.syscall.restype = ctypes.c_long
    if not limiter(resource.RLIMIT_AS, MEMOIRE_MAX):
        manques.add(ManqueIsolation.MEMOIRE)
    if not limiter(resource.RLIMIT_CPU, TEMPS_PROCESSEUR, marge=1):
        manques.add(ManqueIsolation.TEMPS)
    if not limiter(resource.RLIMIT_CORE, 0) or libc.prctl(_PR_SET_DUMPABLE, 0, 0, 0, 0):
        manques.add(ManqueIsolation.VIDAGE_MEMOIRE)
    if libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0):
        return manques | {
            ManqueIsolation.RESEAU,
            ManqueIsolation.LECTURE,
            ManqueIsolation.ECRITURE,
            ManqueIsolation.NOUVEAUX_PROGRAMMES,
        }
    return manques | _landlock(libc) | _seccomp(libc)
