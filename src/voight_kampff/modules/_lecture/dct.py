"""DCT de taille 8 en entiers, sur les coefficients d'un JPEG (T.81, A.3.3 ; ADR-0189, ADR-0201).

Commun aux modules de signal qui recalculent des pixels à partir des coefficients lus par
:mod:`voight_kampff.modules._lecture.jpeg` : la double compression (``doublejpeg``, T41) et
l'ELA (``ela``, T42). Tout le calcul se fait en entiers, en virgule fixe : le résultat est le même
sur toutes les machines (ADR-0189).

Les produits de matrices sont écrits comme un seul produit de deux tableaux à deux dimensions
(``(n x 8) · (8 x 8)``) plutôt qu'un produit par bloc : le résultat est identique, entier pour
entier, et le calcul plus rapide (mesuré pendant T42 : 0,9 s au lieu de 2,2 s pour 65 536 blocs).
"""

import numpy as np
import numpy.typing as npt

from voight_kampff.modules._lecture.jpeg import Coefficients

__all__ = [
    "COSINUS",
    "ECHELLE",
    "LUMINANCE",
    "ZIGZAG",
    "arrondir",
    "blocs_de_pixels",
    "dans_le_bloc",
    "inverser",
    "luminance",
    "naturels",
    "plan",
    "table_ijg",
    "transformer",
]

ECHELLE = 12
"""Bits de la virgule fixe des cosinus."""

ZIGZAG = (
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
)  # fmt: skip
"""Position dans le bloc de chaque coefficient, dans l'ordre du segment DQT (T.81, figure A.6)."""

LUMINANCE = (
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
)  # fmt: skip
"""Table de luminance de l'annexe K de T.81 (tableau K.1), dans l'ordre du bloc."""

COSINUS = (
    1448, 1448, 1448, 1448, 1448, 1448, 1448, 1448,
    2009, 1703, 1138, 400, -400, -1138, -1703, -2009,
    1892, 784, -784, -1892, -1892, -784, 784, 1892,
    1703, -400, -2009, -1138, 1138, 2009, 400, -1703,
    1448, -1448, -1448, 1448, 1448, -1448, -1448, 1448,
    1138, -2009, 400, 1703, -1703, -400, 2009, -1138,
    784, -1892, 1892, -784, -784, 1892, -1892, 784,
    400, -1138, 1703, -2009, 2009, -1703, 1138, -400,
)  # fmt: skip
"""DCT orthonormée de taille 8 (T.81, A.3.3) en virgule fixe : ``C[u][x] = c(u) cos((2x + 1)uπ/16)``
fois 2^12, arrondi à l'entier, avec c(0) = 1/√8 et c(u) = 1/2 ; écrite en entiers pour que le
calcul n'emploie aucun flottant (vérifiée par les tests)."""

_C = np.array(COSINUS, dtype=np.int64).reshape(8, 8)
_DEMI = 1 << (2 * ECHELLE - 1)


def table_ijg(qualite: int) -> tuple[int, ...]:
    """Table de luminance de libjpeg en huit bits à cette qualité, dans l'ordre en zigzag."""
    facteur = 5000 // qualite if qualite < 50 else 200 - 2 * qualite
    return tuple(min(max((LUMINANCE[i] * facteur + 50) // 100, 1), 255) for i in ZIGZAG)


def arrondir(valeurs: npt.NDArray[np.int64], pas: int) -> npt.NDArray[np.int64]:
    """Quotient arrondi au plus proche, la moitié loin de zéro, comme la quantification de
    libjpeg (jcdctmgr.c)."""
    quotients: npt.NDArray[np.int64] = np.sign(valeurs) * ((np.abs(valeurs) + pas // 2) // pas)
    return quotients


def naturels(coefficients: Coefficients) -> npt.NDArray[np.int64]:
    """Coefficients de chaque bloc dans l'ordre du bloc, un bloc par ligne."""
    zigzag = np.frombuffer(coefficients.valeurs, dtype=np.int64).reshape(-1, 64)
    resultat = np.zeros_like(zigzag)
    resultat[:, list(ZIGZAG)] = zigzag
    return resultat


def dans_le_bloc(table: tuple[int, ...]) -> list[int]:
    """Table de quantification dans l'ordre du bloc, à partir de l'ordre en zigzag."""
    valeurs = [0] * 64
    for rang, position in enumerate(ZIGZAG):
        valeurs[position] = table[rang]
    return valeurs


def _gauche(matrice: npt.NDArray[np.int64], blocs: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """``matrice · B`` pour chaque bloc B de ``blocs`` (n x 8 x 8)."""
    colonnes = blocs.transpose(0, 2, 1).reshape(-1, 8) @ matrice.T
    resultat: npt.NDArray[np.int64] = colonnes.reshape(-1, 8, 8).transpose(0, 2, 1)
    return resultat


def _droite(blocs: npt.NDArray[np.int64], matrice: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """``B · matrice`` pour chaque bloc B de ``blocs`` (n x 8 x 8)."""
    resultat: npt.NDArray[np.int64] = (blocs.reshape(-1, 8) @ matrice).reshape(-1, 8, 8)
    return resultat


def transformer(blocs: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """DCT de chaque bloc (n x 8 x 8, valeurs centrées) : ``F = C f C^T``, fois 2^24."""
    return _droite(_gauche(_C, blocs), _C.T)


def inverser(blocs: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """Pixels de chaque bloc de coefficients déquantifiés (n x 8 x 8), de 0 à 255.

    ``f = C^T F C`` : deux produits par 2^12, soit 2^24, retirés avec l'arrondi au plus proche ;
    le résultat est recentré et borné comme le ferait un décodeur. Les coefficients sont bornés à
    ±2^15, la plage d'un coefficient de libjpeg.
    """
    bornes = np.clip(blocs, -(1 << 15), 1 << 15)
    pixels = (_droite(_gauche(_C.T, bornes), _C) + _DEMI) >> (2 * ECHELLE)
    resultat: npt.NDArray[np.int64] = np.clip(pixels + 128, 0, 255)
    return resultat


def blocs_de_pixels(coefficients: Coefficients) -> npt.NDArray[np.int64]:
    """Pixels de la première composante, bloc par bloc (n x 8 x 8), dans l'ordre de la trame."""
    dequantifies = naturels(coefficients) * np.array(dans_le_bloc(coefficients.table))
    return inverser(dequantifies.reshape(-1, 8, 8))


def plan(blocs: npt.NDArray[np.int64], lignes: int, colonnes: int) -> npt.NDArray[np.int64]:
    """Plan de pixels (8 lignes x 8 colonnes de blocs) à partir des blocs dans l'ordre de la
    trame."""
    rangees = blocs.reshape(lignes, colonnes, 8, 8).transpose(0, 2, 1, 3)
    resultat: npt.NDArray[np.int64] = rangees.reshape(lignes * 8, colonnes * 8)
    return resultat


def luminance(coefficients: Coefficients) -> npt.NDArray[np.int64]:
    """Pixels de la première composante sur la région, de 0 à 255, par une IDCT en entiers.

    Le plan est recadré à la largeur de la composante et à la hauteur de la région.
    """
    pixels = plan(blocs_de_pixels(coefficients), coefficients.lignes, coefficients.colonnes)
    return pixels[: coefficients.hauteur_region, : coefficients.largeur_composante]
