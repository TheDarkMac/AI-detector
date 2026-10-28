"""Ressources Photoshop et IPTC-IIM (Photoshop File Formats, « Image Resource Blocks » ;
IPTC-NAA IIM 4.2).

Le segment APP13 d'un JPEG porte une suite de ressources Photoshop ; celle d'identifiant
``0x0404`` contient les jeux de données IPTC-IIM. Chaque jeu de données porte son enregistrement,
son numéro et sa valeur ; une longueur étendue (bit de poids fort) est admise jusqu'à 4 octets.

Un bloc qui s'interrompt rend ce qui a été lu, et le dit (``partiel``).
"""

from dataclasses import dataclass

from voight_kampff._travail.contexte import Contexte

__all__ = ["IPTC_NAA", "JeuDeDonnees", "Ressource", "jeux_de_donnees", "ressources"]

IPTC_NAA = 0x0404
"""Ressource Photoshop qui contient l'IPTC-IIM."""

_SIGNATURES = frozenset({b"8BIM", b"PHUT", b"AgHg", b"DCSR"})


@dataclass(frozen=True, slots=True)
class Ressource:
    identifiant: int
    debut: int
    """Position des données dans le bloc."""
    donnees: bytes


@dataclass(frozen=True, slots=True)
class JeuDeDonnees:
    enregistrement: int
    numero: int
    debut: int
    """Position de la valeur dans les données de la ressource."""
    valeur: bytes


def _gros(octets: bytes) -> int:
    return int.from_bytes(octets, "big")


def ressources(contexte: Contexte, donnees: bytes) -> tuple[list[Ressource], bool]:
    """Ressources du bloc ; vrai en second si le bloc s'interrompt ou se désynchronise."""
    trouvees: list[Ressource] = []
    position = 0
    while position < len(donnees):
        contexte.compter_objets()
        if donnees[position : position + 4] not in _SIGNATURES or position + 7 > len(donnees):
            return trouvees, True
        identifiant = _gros(donnees[position + 4 : position + 6])
        nom = donnees[position + 6]
        position += 6 + ((nom + 2) & ~1)  # nom en chaîne Pascal, longueur paire
        if position + 4 > len(donnees):
            return trouvees, True
        taille = _gros(donnees[position : position + 4])
        position += 4
        if position + taille > len(donnees):
            return trouvees, True
        trouvees.append(Ressource(identifiant, position, donnees[position : position + taille]))
        position += taille + (taille & 1)
    return trouvees, False


def jeux_de_donnees(contexte: Contexte, donnees: bytes) -> tuple[list[JeuDeDonnees], bool]:
    """Jeux de données IIM ; vrai en second si la suite s'interrompt ou se désynchronise.

    Des octets nuls après le dernier jeu sont un remplissage courant, pas un défaut.
    """
    jeux: list[JeuDeDonnees] = []
    position = 0
    while position < len(donnees):
        if donnees[position] != 0x1C:
            return jeux, any(donnees[position:])
        contexte.compter_objets()
        if position + 5 > len(donnees):
            return jeux, True
        enregistrement, numero = donnees[position + 1], donnees[position + 2]
        longueur = _gros(donnees[position + 3 : position + 5])
        position += 5
        if longueur & 0x8000:
            octets = longueur & 0x7FFF
            if not 1 <= octets <= 4 or position + octets > len(donnees):
                return jeux, True
            longueur = _gros(donnees[position : position + octets])
            position += octets
        if position + longueur > len(donnees):
            return jeux, True
        jeux.append(
            JeuDeDonnees(enregistrement, numero, position, donnees[position : position + longueur])
        )
        position += longueur
    return jeux, False
