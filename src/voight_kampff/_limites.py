"""Valeurs des limites d'une analyse (ES-03, NF-02, NF-08, ADR-0076, ADR-0077).

Fixes en V1 : aucune option ne les change, et les deux processus lisent ce même module. Le
processus de travail les applique avant d'avoir reçu quoi que ce soit, d'où l'absence des
limites dans la configuration (ADR-0065). Ce module n'importe rien : le processus de travail
s'en sert sans rien charger de plus.

Deux familles (ADR-0076) :

- les limites **comptées** par le moteur (sorties, décompression, objets, dimensions,
  imbrication) : déterministes, elles donnent le même résultat sur toutes les machines ;
- les limites du **système** (mémoire, temps) : garde-fous, une analyse arrêtée par elles est
  interrompue et hors garantie de reproductibilité (ADR-0023).
"""

__all__ = [
    "DELAI",
    "DELAI_ARRET",
    "MEMOIRE_MAX",
    "OBJETS_MAX",
    "PIXELS_MAX",
    "PROFONDEUR_MAX",
    "RAPPORT_COMPRESSION_MAX",
    "SEUIL_RAPPORT_COMPRESSION",
    "TAILLE_MAX_CONFIGURATION",
    "TAILLE_MAX_DECOMPRESSEE",
    "TAILLE_MAX_FICHIER",
    "TAILLE_MAX_LECTURE",
    "TAILLE_MAX_MESSAGE",
    "TAILLE_MAX_SORTIE",
    "TEMPS_PROCESSEUR",
]

# Entrée (F-04)

TAILLE_MAX_FICHIER = 1 << 30
"""Taille maximale d'un fichier soumis : 1 Gio ; au-delà, refus « hors limites »."""

# Système : garde-fous, non déterministes

MEMOIRE_MAX = 2 << 30
"""Mémoire du processus de travail : 2 Gio."""
DELAI = 120.0
"""Durée maximale de l'analyse d'un fichier, en secondes, mesurée par le processus principal."""
TEMPS_PROCESSEUR = 120
"""Temps processeur du processus de travail, en secondes : utile si un décodeur emploie
plusieurs fils, quand le temps processeur dépasse la durée écoulée."""
DELAI_ARRET = 5.0
"""Attente de la fin du processus de travail après son dernier message ou son arrêt forcé."""

# Protocole : comptées, déterministes (ADR-0065)

TAILLE_MAX_MESSAGE = 1 << 20
"""Taille maximale d'une ligne envoyée par le processus de travail, saut de ligne compris."""
TAILLE_MAX_SORTIE = 64 << 20
"""Taille maximale de l'ensemble des messages d'une analyse."""
TAILLE_MAX_CONFIGURATION = 16 << 20
"""Taille maximale de la configuration envoyée par le processus principal."""
TAILLE_MAX_LECTURE = 16 << 20
"""Taille maximale d'une lecture du fichier par un module."""

# Budget d'un module sur une partie : compté, déterministe (ES-03)

TAILLE_MAX_DECOMPRESSEE = 512 << 20
"""Octets décompressés cumulés : 512 Mio."""
RAPPORT_COMPRESSION_MAX = 1000
"""Rapport maximal entre octets décompressés et octets compressés cumulés…"""
SEUIL_RAPPORT_COMPRESSION = 16 << 20
"""… contrôlé au-delà de 16 Mio décompressés : un petit flux très compressible est normal."""
PIXELS_MAX = 1 << 27
"""Pixels d'une image déclarée (largeur fois hauteur) : environ 134 millions."""
PROFONDEUR_MAX = 64
"""Profondeur d'imbrication des structures parcourues."""
OBJETS_MAX = 1 << 20
"""Objets parcourus : entrées d'une archive, objets d'un PDF, blocs, balises."""
