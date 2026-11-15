"""Module ``ela`` : niveau d'erreur de recompression d'un JPEG, en carte (F-32, F-84 ; ADR-0197 à
ADR-0201 ; fiche ``ela``).

L'image est réenregistrée, par le calcul, à une qualité connue, et l'on regarde de combien chaque
bloc change (Krawetz 2007, §3.4.2) :

1. les coefficients quantifiés de la luminance sont lus par le décodage entropique du projet
   (``_lecture.jpeg``), sur toute l'image jusqu'à :data:`BLOCS_MAX` blocs, sur le haut de
   l'image au-delà ;
2. les pixels en sont recalculés (IDCT en entiers, ``_lecture.dct``), puis transformés de
   nouveau, quantifiés aux tables de luminance de libjpeg à la qualité :data:`QUALITE`,
   déquantifiés et recalculés ;
3. la valeur d'un bloc est la somme des écarts absolus de ses 64 pixels entre les deux images,
   multipliée par :data:`GAIN` et bornée à 255 : un écart moyen de 2 niveaux par pixel donne le
   blanc, quelle que soit l'image (gain fixe, ADR-0199).

La carte, une valeur par bloc, est un PNG en niveaux de gris ; le module n'émet aucun constat
(ADR-0198). Tout le calcul se fait en entiers, et le PNG est écrit sans compression : la carte
et son empreinte sont les mêmes sur toutes les machines (NF-06).

Observations : le procédé, la qualité de recompression, les blocs de la carte et ceux de l'image,
l'écart moyen par pixel sur la carte et le plus grand écart moyen d'un bloc.
"""

import struct
import zlib

import numpy as np
import numpy.typing as npt

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import dct, jpeg
from voight_kampff.modules._lecture.jpeg import Coefficients
from voight_kampff.rapport.modele import (
    Localisation,
    NatureVisualisation,
    RaisonNonMenee,
    Zone,
)

__all__ = ["BLOCS_MAX", "GAIN", "QUALITE", "VISITES_MAX", "analyser", "carte", "ecarts", "png_gris"]

QUALITE = 95
"""Qualité de libjpeg de la recompression (Krawetz 2007 : « such as 95% »)."""
BLOCS_MAX = 1 << 16
"""Blocs de luminance au plus sur la carte : 65 536, soit 2 048 x 2 048 pixels (ADR-0199)."""
GAIN = 2
"""Multiplicateur de la somme des écarts d'un bloc : 128 fois l'écart moyen par pixel."""
VISITES_MAX = 1 << 19
"""Blocs décodés au plus, tous balayages et composantes compris : un JPEG progressif décode
plusieurs fois chaque bloc."""
_TABLE = np.array(dct.dans_le_bloc(dct.table_ijg(QUALITE)), dtype=np.int64).reshape(8, 8)
_STOCKE_MAX = 65535
"""Octets au plus d'un bloc stocké de deflate (RFC 1951, 3.2.4)."""


def ecarts(coefficients: Coefficients) -> npt.NDArray[np.int64]:
    """Somme des écarts absolus des 64 pixels de chaque bloc, après recompression ; un tableau
    de ``lignes`` x ``colonnes`` blocs."""
    pixels = dct.blocs_de_pixels(coefficients)
    transformes = dct.transformer(pixels - 128)
    pas = _TABLE << (2 * dct.ECHELLE)
    # Quantification de libjpeg : arrondi au plus proche, la moitié loin de zéro (jcdctmgr.c).
    quantifies = np.sign(transformes) * ((np.abs(transformes) + (pas >> 1)) // pas)
    recompresses = dct.inverser(quantifies * _TABLE)
    sommes: npt.NDArray[np.int64] = np.abs(pixels - recompresses).sum(axis=(1, 2))
    return sommes.reshape(coefficients.lignes, coefficients.colonnes)


def carte(sommes: npt.NDArray[np.int64]) -> npt.NDArray[np.uint8]:
    """Valeur de chaque bloc sur la carte : la somme de ses écarts fois :data:`GAIN`, bornée à
    255."""
    valeurs: npt.NDArray[np.uint8] = np.minimum(GAIN * sommes, 255).astype(np.uint8)
    return valeurs


def _morceau(nature: bytes, donnees: bytes) -> bytes:
    crc = zlib.crc32(nature + donnees)
    return struct.pack(">I", len(donnees)) + nature + donnees + struct.pack(">I", crc)


def png_gris(valeurs: npt.NDArray[np.uint8]) -> bytes:
    """PNG en niveaux de gris sur huit bits, sans filtre ni compression.

    Le flux zlib n'a que des blocs stockés (RFC 1950, RFC 1951) écrits ici : ses octets ne
    dépendent pas de la version de zlib, contrairement à un flux compressé.
    """
    hauteur, largeur = valeurs.shape
    brut = b"".join(b"\x00" + valeurs[ligne].tobytes() for ligne in range(hauteur))
    blocs = [brut[i : i + _STOCKE_MAX] for i in range(0, len(brut), _STOCKE_MAX)] or [b""]
    flux = bytearray(b"\x78\x01")
    for rang, bloc in enumerate(blocs):
        final = rang == len(blocs) - 1
        flux += struct.pack("<BHH", final, len(bloc), len(bloc) ^ 0xFFFF) + bloc
    flux += struct.pack(">I", zlib.adler32(brut))
    entete = struct.pack(">IIBBBBB", largeur, hauteur, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _morceau(b"IHDR", entete)
        + _morceau(b"IDAT", bytes(flux))
        + _morceau(b"IEND", b"")
    )


def analyser(contexte: Contexte) -> None:
    lecture = jpeg.lire(contexte, blocs=BLOCS_MAX, visites=VISITES_MAX)
    coefficients = lecture.coefficients
    if coefficients is None:
        # Sans coefficients, la lecture a toujours une raison d'arrêt.
        raison = lecture.arret or RaisonNonMenee.FORMAT_PARTIEL
        contexte.non_mener(raison, localisation=lecture.localisation_arret())
        return
    sommes = ecarts(coefficients)
    blocs = coefficients.lignes * coefficients.colonnes
    entiere = blocs == coefficients.blocs_image
    localisation = Localisation(
        chemin="composante 1, image entière" if entiere else "composante 1, haut de l'image",
        zone=Zone(0, 0, coefficients.largeur_composante, coefficients.hauteur_region),
    )
    contexte.observer("ela.procede", coefficients.procede)
    contexte.observer("ela.qualite", QUALITE)
    contexte.observer("ela.blocs", blocs, localisation=localisation)
    contexte.observer("ela.blocs_image", coefficients.blocs_image)
    contexte.observer(
        "ela.ecart_moyen",
        round(int(sommes.sum()) / (64 * blocs), 2),
        unite="niveaux par pixel",
        localisation=localisation,
    )
    contexte.observer(
        "ela.ecart_moyen_max",
        round(int(sommes.max()) / 64, 2),
        unite="niveaux par pixel",
        localisation=localisation,
    )
    contexte.visualiser(
        NatureVisualisation.CARTE_ELA,
        png_gris(carte(sommes)),
        coefficients.colonnes,
        coefficients.lignes,
        localisation=localisation,
    )
