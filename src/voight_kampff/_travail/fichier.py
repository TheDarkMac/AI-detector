"""Accès du processus de travail au fichier analysé, par le descripteur hérité (ADR-0036)."""

import hashlib
import os
import sys

from voight_kampff._protocole import TAILLE_MAX_LECTURE

__all__ = ["Fichier", "ouvrir_herite"]

_BLOC = 1 << 20


def ouvrir_herite(valeur: int) -> int:
    """Descripteur du fichier transmis par le processus principal.

    Sous Windows, le processus principal transmet un handle, converti ici en descripteur.
    """
    if sys.platform == "win32":  # pragma: no cover - exécuté par la CI Windows
        import msvcrt

        return msvcrt.open_osfhandle(valeur, os.O_RDONLY | os.O_BINARY)
    return valeur


class Fichier:
    """Lectures à position explicite : le processus de travail ne dépend d'aucune position."""

    __slots__ = ("_descripteur",)

    def __init__(self, descripteur: int) -> None:
        self._descripteur = descripteur

    def lire(self, position: int, taille: int) -> bytes:
        """Au plus ``taille`` octets à partir de ``position`` ; moins en fin de fichier."""
        if position < 0 or not 0 <= taille <= TAILLE_MAX_LECTURE:
            raise ValueError("lecture : position ou taille hors bornes")
        morceaux: list[bytes] = []
        reste = taille
        while reste:
            morceau = self._lire_a(position, reste)
            if not morceau:
                break
            morceaux.append(morceau)
            position += len(morceau)
            reste -= len(morceau)
        return b"".join(morceaux)

    def _lire_a(self, position: int, taille: int) -> bytes:
        if sys.platform == "win32":  # pragma: no cover - exécuté par la CI Windows
            # Pas de pread sous Windows. Le processus principal ne lit plus le descripteur
            # pendant l'analyse : déplacer la position commune ne gêne personne.
            os.lseek(self._descripteur, position, os.SEEK_SET)
            return os.read(self._descripteur, taille)
        return os.pread(self._descripteur, taille, position)

    def taille(self) -> int:
        """Taille actuelle du fichier ; l'empreinte finale dira s'il a changé (ES-08)."""
        return os.fstat(self._descripteur).st_size

    def empreinte(self) -> tuple[str, int]:
        """SHA-256 du fichier entier, en hexadécimal minuscule, et sa taille (ES-08, ADR-0040)."""
        condensat = hashlib.sha256()
        position = 0
        while morceau := self._lire_a(position, _BLOC):
            condensat.update(morceau)
            position += len(morceau)
        return condensat.hexdigest(), position
