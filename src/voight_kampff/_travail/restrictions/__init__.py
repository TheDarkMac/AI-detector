"""Restrictions que le processus de travail s'applique avant de lire le fichier (ADR-0035).

Chaque système a son module (ADR-0079 à ADR-0081) ; tous appellent le système par ``ctypes``
ou la bibliothèque standard, sans privilège ni dépendance. Une restriction qui échoue
n'arrête pas l'analyse : elle figure parmi les manques, et le rapport dit l'isolation réduite
(ADR-0028).

Après :func:`appliquer`, le processus de travail ne peut plus lire de fichier sur le disque :
tout ce dont il a besoin doit être importé avant.
"""

import sys
from collections.abc import Collection

from voight_kampff.rapport.modele import EtatIsolation, ManqueIsolation, NiveauIsolation

__all__ = ["appliquer", "etat"]


def etat(manques: Collection[ManqueIsolation]) -> EtatIsolation:
    """État de l'isolation, manques dans l'ordre du modèle."""
    if not manques:
        return EtatIsolation(NiveauIsolation.COMPLETE)
    return EtatIsolation(
        NiveauIsolation.REDUITE, tuple(manque for manque in ManqueIsolation if manque in manques)
    )


def appliquer() -> EtatIsolation:
    """Applique les restrictions du système courant ; renvoie l'isolation obtenue."""
    manques: Collection[ManqueIsolation]
    if sys.platform == "linux":
        from voight_kampff._travail.restrictions import linux

        manques = linux.appliquer()
    elif sys.platform == "darwin":  # pragma: no cover - exécuté par la CI macOS
        from voight_kampff._travail.restrictions import macos

        manques = macos.appliquer()
    elif sys.platform == "win32":  # pragma: no cover - exécuté par la CI Windows
        from voight_kampff._travail.restrictions import windows

        manques = windows.appliquer()
    else:  # pragma: no cover - système hors V1 (ADR-0035) : rien n'est restreint
        manques = tuple(ManqueIsolation)
    return etat(manques)
