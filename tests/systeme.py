"""Isolation attendue du processus de travail sur chaque système de la V1 (ADR-0079 à ADR-0081).

Linux et macOS appliquent toutes les restrictions ; Windows ne bloque ni le réseau ni la
lecture, et l'effet de ses réglages sur les vidages mémoire n'est pas vérifiable (ADR-0081).
"""

import sys

from voight_kampff.rapport.modele import ManqueIsolation

MANQUES_ATTENDUS: frozenset[ManqueIsolation] = (
    frozenset({ManqueIsolation.RESEAU, ManqueIsolation.LECTURE, ManqueIsolation.VIDAGE_MEMOIRE})
    if sys.platform == "win32"
    else frozenset()
)
