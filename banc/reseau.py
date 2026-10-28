"""Évaluation sans réseau (ES-11, A-52, ADR-0100).

Deux barrières :

1. avant toute analyse, le banc vérifie qu'il ne voit aucune interface réseau autre que la
   boucle locale : lancé sous ``unshare -rn``, il est dans un espace de noms réseau vide, et
   les processus de travail qu'il lance y sont aussi ;
2. pendant l'évaluation, un crochet d'audit de Python refuse, et note, toute création de socket
   ou résolution de nom dans le processus du banc : une seule tentative fait échouer le banc.

La liste des interfaces est lue dans ``/proc/self/net/dev``, propre à l'espace de noms réseau
du processus, sans ouvrir de socket. ``/sys/class/net`` ne convient pas : il montre les
interfaces de l'espace de noms qui a monté ``/sys``.
"""

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

__all__ = ["ReseauInterdit", "ReseauPresent", "interfaces", "surveiller", "verifier_absence"]

BOUCLE_LOCALE = "lo"
_INTERFACES = Path("/proc/self/net/dev")

EVENEMENTS = frozenset(
    {
        "socket.__new__",
        "socket.bind",
        "socket.connect",
        "socket.getaddrinfo",
        "socket.gethostbyaddr",
        "socket.gethostbyname",
        "socket.getnameinfo",
        "socket.sendmsg",
        "socket.sendto",
    }
)
"""Événements d'audit de Python qui ouvrent, nomment ou emploient une socket : toute requête
réseau passe par eux, quelle que soit la bibliothèque qui la fait."""


class ReseauPresent(RuntimeError):
    """Le banc voit une interface réseau : il refuse de démarrer."""


class ReseauInterdit(RuntimeError):
    """Tentative d'accès au réseau dans le processus du banc pendant une évaluation."""


def interfaces(source: Path = _INTERFACES) -> tuple[str, ...]:
    """Interfaces réseau de l'espace de noms du processus ; Linux seulement.

    Lève :class:`ReseauPresent` hors de Linux, ou si la liste ne peut pas être lue : le banc
    ne peut alors pas établir qu'il est sans réseau.
    """
    if not sys.platform.startswith("linux"):
        raise ReseauPresent(
            "le banc ne s'exécute que sous Linux, dans un espace de noms réseau vide (ADR-0100)"
        )
    try:
        lignes = source.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeDecodeError):
        raise ReseauPresent("liste des interfaces réseau illisible") from None
    # Deux lignes d'en-tête, puis « nom: compteurs » par interface.
    return tuple(ligne.split(":", 1)[0].strip() for ligne in lignes[2:] if ":" in ligne)


def verifier_absence(source: Path = _INTERFACES) -> tuple[str, ...]:
    """Interfaces vues, si la boucle locale est la seule ; sinon :class:`ReseauPresent`."""
    vues = interfaces(source)
    autres = [nom for nom in vues if nom != BOUCLE_LOCALE]
    if autres:
        raise ReseauPresent(
            f"interfaces réseau présentes ({', '.join(autres)}) : lancer le banc dans un "
            "espace de noms réseau vide, par exemple « unshare -rn python -m banc … »"
        )
    return vues


class _Garde:
    """État du crochet : il est installé une fois pour toutes, et n'agit que s'il est actif."""

    installe = False
    actif = False
    tentatives: list[str] = []  # noqa: RUF012 (état du processus, jamais partagé)


# Python exécute les crochets d'audit sans traçage : coverage ne peut pas mesurer ces lignes. Leur
# effet est vérifié par tests/test_banc.py (refus, événements notés, crochet inactif hors du bloc).
def _crochet(evenement: str, _arguments: tuple[object, ...]) -> None:  # pragma: no cover - audit
    if _Garde.actif and evenement in EVENEMENTS:
        _Garde.tentatives.append(evenement)
        raise ReseauInterdit(f"accès au réseau refusé pendant l'évaluation : {evenement}")


@contextmanager
def surveiller() -> Iterator[list[str]]:
    """Refuse et note toute tentative d'accès au réseau dans ce processus, le temps du bloc.

    Rend la liste des événements refusés, qui reste lisible après le bloc. Un crochet d'audit
    ne se retire pas : il est installé au premier appel, puis activé le temps de chaque bloc.
    """
    if not _Garde.installe:
        sys.addaudithook(_crochet)
        _Garde.installe = True
    tentatives: list[str] = []
    _Garde.tentatives, _Garde.actif = tentatives, True
    try:
        yield tentatives
    finally:
        _Garde.actif = False
