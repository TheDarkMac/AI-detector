"""Pixels d'une image JPEG ou PNG, en rouge, vert et bleu sur huit bits (ADR-0202).

Commun aux modules qui lisent les couleurs d'une image : le filigrane dwtDct (``dwtdct``, T32).

- **PNG** : lecteur :mod:`voight_kampff.modules._lecture.png`.
- **JPEG** : coefficients de toutes les composantes, lus par le décodage entropique du projet
  (:mod:`voight_kampff.modules._lecture.jpeg`) ; pixels de chacune par l'IDCT en entiers
  (:mod:`voight_kampff.modules._lecture.dct`) ; chrominance suréchantillonnée par répétition
  des pixels, sans le lissage de libjpeg (ADR-0202) ; conversion de YCbCr en RVB par les tables
  en virgule fixe de libjpeg (``jdcolor.c``), bornées à 0 et 255. Les composantes sont en YCbCr,
  ou en RVB selon la règle de libjpeg (segments JFIF et Adobe, puis identifiants des
  composantes). Les images CMYK et YCCK, à deux ou quatre composantes, ne sont pas lues (format
  partiel) ; une image à une composante est en niveaux de gris.

Seules les premières lignes de l'image sont lues, au plus ``pixels`` pixels : une région faite
de lignes de MCU entières pour un JPEG. Tout le calcul se fait en entiers : les pixels sont les
mêmes sur toutes les machines (ADR-0189).
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import dct, jpeg, png
from voight_kampff.modules._lecture.jpeg import Coefficients
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee

__all__ = ["FORMATS", "Lecture", "Pixels", "lire", "ycbcr_vers_rvb"]

FORMATS = frozenset({"jpeg", "png"})
"""Formats dont les pixels sont décodés."""

_VISITES_PAR_PIXEL = 1 << 3
"""Blocs décodés au plus, tous balayages compris, pour 64 pixels de la région : un JPEG
progressif décode plusieurs fois chaque bloc."""
_UN_DEMI = 1 << 15
_RVB = (ord("R"), ord("G"), ord("B"))


def _fixe(valeur: float) -> int:
    """Coefficient en virgule fixe sur 16 bits, comme ``FIX`` de libjpeg."""
    return int(valeur * 65536 + 0.5)


_CR_R = _fixe(1.40200)
_CB_B = _fixe(1.77200)
_CR_G = _fixe(0.71414)
_CB_G = _fixe(0.34414)


@dataclass(frozen=True, slots=True)
class Pixels:
    """Pixels des premières lignes de l'image."""

    format: str
    """``jpeg`` ou ``png``."""
    largeur: int
    hauteur: int
    lignes: int
    """Lignes lues, à partir du haut de l'image ; 0 pour une image en niveaux de gris."""
    rvb: npt.NDArray[np.int64] | None
    """``lignes`` x ``largeur`` x 3 valeurs de 0 à 255 ; ``None`` pour une image en niveaux de
    gris, qui n'a pas de chrominance."""


@dataclass(frozen=True, slots=True)
class Lecture:
    """Pixels lus, ou la raison de l'arrêt et sa localisation."""

    pixels: Pixels | None
    arret: RaisonNonMenee | None = None
    localisation: Localisation | None = None


def lire(contexte: Contexte, *, pixels: int) -> Lecture:
    """Pixels des premières lignes de la partie, JPEG ou PNG, au plus ``pixels`` pixels."""
    if contexte.format_reel == "png":
        lecture = png.lire(contexte, pixels=pixels)
        if lecture.image is None:
            return Lecture(None, lecture.arret, lecture.localisation_arret())
        image = lecture.image
        return Lecture(Pixels("png", image.largeur, image.hauteur, image.lignes, image.rvb))
    return _jpeg(contexte, pixels)


def _jpeg(contexte: Contexte, pixels: int) -> Lecture:
    blocs = max(1, pixels // 64)
    lecture = jpeg.lire(contexte, blocs=blocs, visites=_VISITES_PAR_PIXEL * blocs, toutes=True)
    composantes = lecture.composantes
    if lecture.coefficients is None or not composantes:
        # Sans coefficients, la lecture a toujours une raison d'arrêt.
        raison = lecture.arret or RaisonNonMenee.FORMAT_PARTIEL
        return Lecture(None, raison, lecture.localisation_arret())
    premiere = composantes[0]
    if len(composantes) == 1:
        return Lecture(Pixels("jpeg", premiere.largeur, premiere.hauteur, 0, None))
    localisation = Localisation(chemin="segment SOF du JPEG")
    if len(composantes) != 3:
        return Lecture(None, RaisonNonMenee.FORMAT_PARTIEL, localisation)  # CMYK, YCCK
    plans = [_plan(composante) for composante in composantes]
    if any(plan is None for plan in plans):
        return Lecture(None, RaisonNonMenee.FORMAT_PARTIEL, localisation)
    # Lignes de l'image couvertes par la région : la même pour les trois composantes.
    lignes = min(premiere.hauteur, 8 * premiere.lignes * premiere.vertical_max // premiere.vertical)
    un, deux, trois = (plan[:lignes, : premiere.largeur] for plan in plans if plan is not None)
    if _en_rvb(lecture, composantes):
        rvb = np.stack([un, deux, trois], axis=2)
    else:
        rvb = ycbcr_vers_rvb(un, deux, trois)
    return Lecture(Pixels("jpeg", premiere.largeur, premiere.hauteur, lignes, rvb))


def _plan(composante: Coefficients) -> npt.NDArray[np.int64] | None:
    """Pixels de la composante sur la région, à la taille de l'image ; ``None`` si son
    échantillonnage n'est pas un diviseur de celui de l'image."""
    horizontal, reste_h = divmod(composante.horizontal_max, composante.horizontal)
    vertical, reste_v = divmod(composante.vertical_max, composante.vertical)
    if reste_h or reste_v:
        return None
    plan = dct.plan(dct.blocs_de_pixels(composante), composante.lignes, composante.colonnes)
    if horizontal > 1:
        plan = np.repeat(plan, horizontal, axis=1)
    if vertical > 1:
        plan = np.repeat(plan, vertical, axis=0)
    return plan


def _en_rvb(lecture: jpeg.Lecture, composantes: tuple[Coefficients, ...]) -> bool:
    """Composantes en RVB plutôt qu'en YCbCr, selon la règle de libjpeg (``jdapimin.c``)."""
    if lecture.jfif:
        return False
    if lecture.adobe is not None:
        return lecture.adobe == 0
    return tuple(c.identifiant for c in composantes) == _RVB


def ycbcr_vers_rvb(
    y: npt.NDArray[np.int64], cb: npt.NDArray[np.int64], cr: npt.NDArray[np.int64]
) -> npt.NDArray[np.int64]:
    """RVB de 0 à 255, par les tables en virgule fixe de libjpeg (``jdcolor.c``).

    R = Y + 1,402 Cr ; G = Y - 0,34414 Cb - 0,71414 Cr ; B = Y + 1,772 Cb, avec Cb et Cr centrés
    sur 128 ; chaque terme est arrondi comme dans les tables de libjpeg.
    """
    cb, cr = cb - 128, cr - 128
    rouge = y + ((_CR_R * cr + _UN_DEMI) >> 16)
    vert = y + ((-_CB_G * cb - _CR_G * cr + _UN_DEMI) >> 16)
    bleu = y + ((_CB_B * cb + _UN_DEMI) >> 16)
    rvb: npt.NDArray[np.int64] = np.clip(np.stack([rouge, vert, bleu], axis=2), 0, 255)
    return rvb
