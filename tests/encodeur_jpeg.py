"""Encodeur JPEG séquentiel minimal, pour éprouver le décodage entropique (T41, ADR-0187).

Il écrit des coefficients quantifiés donnés, sans DCT : ce que le décodeur doit relire à
l'identique. Codes de Huffman canoniques choisis pour les tests (longueurs 2, 4 et 9), pas ceux
de l'annexe K : le décodeur lit les tables du fichier. Un balayage entrelacé s'il y a plusieurs
composantes, intervalle de redémarrage au choix.
"""

import struct
from collections.abc import Sequence
from dataclasses import dataclass

CONTINUS = list(range(12))
"""Symboles des différences du coefficient continu : leur taille, de 0 à 11."""
ALTERNATIFS = (
    [0x00, 0x01]
    + [r << 4 | s for r in range(16) for s in range(1, 11) if (r, s) != (0, 1)]
    + [0xF0]
)
"""Symboles des coefficients alternatifs : fin de bloc, (zéros, taille), seize zéros."""


def segment(marqueur: int, donnees: bytes) -> bytes:
    return b"\xff" + bytes([marqueur]) + struct.pack(">H", len(donnees) + 2) + donnees


def comptes_continus() -> bytes:
    return bytes([0, 0, 0, 12] + [0] * 12)


def comptes_alternatifs() -> bytes:
    return bytes([0, 2] + [0] * 6 + [len(ALTERNATIFS) - 2] + [0] * 7)


def codes(comptes: bytes, symboles: Sequence[int]) -> dict[int, tuple[int, int]]:
    """Code canonique (T.81, annexe C) de chaque symbole : valeur et longueur."""
    table: dict[int, tuple[int, int]] = {}
    code = rang = 0
    for longueur in range(1, 17):
        for _ in range(comptes[longueur - 1]):
            table[symboles[rang]] = (code, longueur)
            rang += 1
            code += 1
        code <<= 1
    return table


def dht(classe: int, identifiant: int, comptes: bytes, symboles: Sequence[int]) -> bytes:
    return segment(0xC4, bytes([classe << 4 | identifiant]) + comptes + bytes(symboles))


def dqt(identifiant: int, table: Sequence[int]) -> bytes:
    if max(table) > 255:
        return segment(0xDB, bytes([0x10 | identifiant]) + struct.pack(">64H", *table))
    return segment(0xDB, bytes([identifiant]) + bytes(table))


@dataclass(frozen=True)
class Composante:
    identifiant: int
    horizontal: int = 1
    vertical: int = 1
    table: int = 0


class _Bits:
    def __init__(self) -> None:
        self.octets = bytearray()
        self.accumule = 0
        self.nombre = 0

    def ecrire(self, valeur: int, longueur: int) -> None:
        self.accumule = (self.accumule << longueur) | (valeur & ((1 << longueur) - 1))
        self.nombre += longueur
        while self.nombre >= 8:
            self.nombre -= 8
            octet = (self.accumule >> self.nombre) & 0xFF
            self.octets.append(octet)
            if octet == 0xFF:
                self.octets.append(0)
        self.accumule &= (1 << self.nombre) - 1

    def vider(self) -> bytes:
        """Complète l'octet en cours par des 1 (T.81, F.1.2.3) et rend les octets."""
        if self.nombre:
            self.ecrire((1 << (8 - self.nombre)) - 1, 8 - self.nombre)
        octets = bytes(self.octets)
        self.octets.clear()
        return octets


def _plafond(a: int, b: int) -> int:
    return -(-a // b)


def _taille(valeur: int) -> int:
    return abs(valeur).bit_length()


def _bloc(bits: _Bits, bloc: Sequence[int], difference: int) -> None:
    continus = codes(comptes_continus(), CONTINUS)
    alternatifs = codes(comptes_alternatifs(), ALTERNATIFS)
    taille = _taille(difference)
    bits.ecrire(*continus[taille])
    if taille:
        bits.ecrire(difference if difference > 0 else difference - 1, taille)
    zeros = 0
    for valeur in bloc[1:]:
        if not valeur:
            zeros += 1
            continue
        while zeros > 15:
            bits.ecrire(*alternatifs[0xF0])
            zeros -= 16
        taille = _taille(valeur)
        bits.ecrire(*alternatifs[zeros << 4 | taille])
        bits.ecrire(valeur if valeur > 0 else valeur - 1, taille)
        zeros = 0
    if zeros:
        bits.ecrire(*alternatifs[0x00])


def encoder(
    largeur: int,
    hauteur: int,
    composantes: Sequence[Composante],
    blocs: Sequence[Sequence[Sequence[int]]],
    tables: dict[int, Sequence[int]],
    *,
    intervalle: int = 0,
    marqueur_sof: int = 0xC0,
    avant_balayage: bytes = b"",
    seule: int | None = None,
) -> bytes:
    """JPEG séquentiel : ``blocs[c]`` donne les blocs de la composante ``c`` (64 valeurs dans
    l'ordre en zigzag), ligne après ligne sur la grille des MCU (ou de la composante seule).

    ``seule`` : rang de la seule composante du balayage, les autres n'en ont aucun ; ses blocs
    sont alors sur sa propre grille."""
    hmax = max(c.horizontal for c in composantes)
    vmax = max(c.vertical for c in composantes)
    entete = struct.pack(">BHHB", 8, hauteur, largeur, len(composantes)) + b"".join(
        bytes([c.identifiant, c.horizontal << 4 | c.vertical, c.table]) for c in composantes
    )
    balayees = composantes if seule is None else [composantes[seule]]
    sos = (
        bytes([len(balayees)])
        + b"".join(bytes([c.identifiant, 0x00]) for c in balayees)
        + bytes([0, 63, 0])
    )
    fichier = bytearray(b"\xff\xd8")
    for identifiant, table in tables.items():
        fichier += dqt(identifiant, table)
    fichier += segment(marqueur_sof, entete)
    fichier += dht(0, 0, comptes_continus(), CONTINUS)
    fichier += dht(1, 0, comptes_alternatifs(), ALTERNATIFS)
    if intervalle:
        fichier += segment(0xDD, struct.pack(">H", intervalle))
    fichier += avant_balayage + segment(0xDA, sos)
    # Ordre des blocs dans le balayage.
    if seule is not None:
        c = composantes[seule]
        largeur_blocs = _plafond(_plafond(largeur * c.horizontal, hmax), 8)
        hauteur_blocs = _plafond(_plafond(hauteur * c.vertical, vmax), 8)
        unites = [
            [(seule, ligne * largeur_blocs + colonne)]
            for ligne in range(hauteur_blocs)
            for colonne in range(largeur_blocs)
        ]
    elif len(composantes) == 1:
        largeur_blocs = -(-largeur // 8)
        hauteur_blocs = -(-hauteur // 8)
        unites = [
            [(0, ligne * largeur_blocs + colonne)]
            for ligne in range(hauteur_blocs)
            for colonne in range(largeur_blocs)
        ]
    else:
        mcu_colonnes = -(-largeur // (8 * hmax))
        mcu_lignes = -(-hauteur // (8 * vmax))
        unites = []
        for ligne in range(mcu_lignes):
            for colonne in range(mcu_colonnes):
                unite = []
                for rang, c in enumerate(composantes):
                    grille = mcu_colonnes * c.horizontal
                    for v in range(c.vertical):
                        for h in range(c.horizontal):
                            position = (
                                (ligne * c.vertical + v) * grille + colonne * c.horizontal + h
                            )
                            unite.append((rang, position))
                unites.append(unite)
    bits = _Bits()
    predictions = [0] * len(composantes)
    for numero, unite in enumerate(unites):
        if intervalle and numero and numero % intervalle == 0:
            fichier += bits.vider() + bytes([0xFF, 0xD0 + (numero // intervalle - 1) % 8])
            predictions = [0] * len(composantes)
        for rang, position in unite:
            bloc = blocs[rang][position]
            _bloc(bits, bloc, bloc[0] - predictions[rang])
            predictions[rang] = bloc[0]
    fichier += bits.vider() + b"\xff\xd9"
    return bytes(fichier)


def blocs_nuls(
    composantes: Sequence[Composante], largeur: int, hauteur: int
) -> list[list[list[int]]]:
    """Blocs à zéro de chaque composante, sur la grille qu'``encoder`` parcourt."""
    hmax = max(c.horizontal for c in composantes)
    vmax = max(c.vertical for c in composantes)
    if len(composantes) == 1:
        return [[[0] * 64 for _ in range(-(-largeur // 8) * -(-hauteur // 8))]]
    mcu_colonnes = -(-largeur // (8 * hmax))
    mcu_lignes = -(-hauteur // (8 * vmax))
    return [
        [[0] * 64 for _ in range(mcu_colonnes * c.horizontal * mcu_lignes * c.vertical)]
        for c in composantes
    ]
