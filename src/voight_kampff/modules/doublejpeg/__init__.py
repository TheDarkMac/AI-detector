"""Module ``doublejpeg`` : double compression JPEG (F-31, ADR-0185 à ADR-0190 ; fiche
``double-compression-jpeg``).

Estime, pour les premières fréquences de la luminance, le pas d'une quantification antérieure à
celle des tables du fichier (Lukáš et Fridrich 2003, calibrage) :

1. les coefficients quantifiés de la région du haut de l'image sont lus par le décodage
   entropique du projet (``_lecture.jpeg``) ;
2. la luminance en est recalculée, puis recadrée de 4 pixels vers le bas et la droite et
   transformée de nouveau : ses coefficients, désaccordés de la grille des blocs, estiment ceux de
   l'image avant toute compression ;
3. pour chaque fréquence examinée, l'histogramme des coefficients du fichier est comparé à celui
   que donnent ces estimations quantifiées une fois au pas du fichier, ou deux fois, d'abord à un
   pas antérieur puis au pas du fichier ; une trace est relevée quand une double quantification
   l'explique au moins :data:`RAPPORT` fois mieux qu'une simple.

Tout le calcul se fait en entiers (ADR-0189) : le résultat est le même sur toutes les machines.

Observations : le procédé, le nombre de blocs examinés, les fréquences examinées, celles qui
portent une trace et le pas antérieur estimé pour chacune, et les qualités de libjpeg dont la
table de luminance a ces pas. La règle ``R-DOUBLEJPEG-001`` du catalogue lit le nombre de traces.
"""

from fractions import Fraction

import numpy as np
import numpy.typing as npt

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import dct, jpeg
from voight_kampff.modules._lecture.jpeg import Coefficients
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee

__all__ = [
    "FREQUENCES",
    "NON_NULS_MIN",
    "RAPPORT",
    "Estimation",
    "analyser",
    "estimer",
    "luminance",
    "qualites_ijg",
]

FREQUENCES = range(1, 10)
"""Fréquences examinées : les neuf premières après le coefficient continu, dans l'ordre en
zigzag."""
NON_NULS_MIN = 256
"""Coefficients non nuls au moins pour qu'une fréquence soit examinée."""
RAPPORT = Fraction(4)
"""Une trace : la double quantification explique l'histogramme au moins quatre fois mieux."""
QUALITE_TRACES_MIN = 3
"""Traces au moins pour chercher les qualités de libjpeg qui les expliquent."""
_DECALAGE = 4
"""Recadrage du calibrage, en pixels : la moitié d'un bloc."""
_BORNE_MIN = 8
_BORNE_MAX = 128
luminance = dct.luminance
"""Pixels de la première composante sur la région (fonction du module ``_lecture.dct``)."""


def _calibrage(image: npt.NDArray[np.int64]) -> npt.NDArray[np.int64] | None:
    """Coefficients des blocs de l'image recadrée de 4 pixels, fois 2^24 ; ``None`` si elle est
    trop petite."""
    recadree = image[_DECALAGE:, _DECALAGE:]
    lignes, colonnes = recadree.shape[0] // 8, recadree.shape[1] // 8
    if not lignes or not colonnes:
        return None
    blocs = recadree[: lignes * 8, : colonnes * 8] - 128
    blocs = blocs.reshape(lignes, 8, colonnes, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
    # F = C f C^T, fois 2^24.
    calibres: npt.NDArray[np.int64] = dct.transformer(blocs).reshape(-1, 64)
    return calibres


def _histogramme(valeurs: npt.NDArray[np.int64], borne: int) -> list[int]:
    """Effectifs de -borne à borne, les extrêmes cumulés aux bords, le zéro retiré."""
    effectifs = np.bincount(np.clip(valeurs, -borne, borne) + borne, minlength=2 * borne + 1)
    effectifs[borne] = 0
    return [int(n) for n in effectifs]


def _ecart(observe: list[int], simule: list[int]) -> Fraction | None:
    """Écart quadratique entre les deux histogrammes normalisés, à un facteur commun près.

    L'effectif de l'histogramme observé est le même pour tous les pas : il est mis en facteur.
    ``None`` si l'histogramme simulé est vide.
    """
    total = sum(simule)
    if not total:
        return None
    reference = sum(observe)
    somme = sum((a * total - b * reference) ** 2 for a, b in zip(observe, simule, strict=True))
    return Fraction(somme, total * total)


class Estimation:
    """Résultat de l'estimation, fréquence par fréquence."""

    __slots__ = ("anterieurs", "blocs", "examinees", "tracees")

    def __init__(self, blocs: int) -> None:
        self.blocs = blocs
        self.examinees: list[int] = []
        """Fréquences examinées, rangs dans l'ordre en zigzag."""
        self.tracees: list[int] = []
        """Fréquences qui portent une trace."""
        self.anterieurs: list[int] = []
        """Pas antérieur estimé, pour chaque fréquence de :attr:`tracees`."""


def estimer(coefficients: Coefficients) -> Estimation:
    """Fréquences examinées, et le pas antérieur de celles qui portent une trace."""
    naturels = dct.naturels(coefficients)
    estimation = Estimation(len(naturels))
    calibres = _calibrage(luminance(coefficients))
    if calibres is None:
        return estimation
    echelle = 1 << (2 * dct.ECHELLE)
    for rang in FREQUENCES:
        position = dct.ZIGZAG[rang]
        pas = coefficients.table[rang]
        observes = naturels[:, position]
        absolus = np.abs(observes)
        if int(np.count_nonzero(observes)) < NON_NULS_MIN:
            continue
        estimation.examinees.append(rang)
        borne = _borne(absolus)
        observe = _histogramme(observes, borne)
        simple: Fraction | None = None
        double: tuple[Fraction, int] | None = None
        for anterieur in range(1, min(255, 4 * pas + 16) + 1):
            quantifies = dct.arrondir(calibres[:, position], anterieur * echelle)
            ecart = _ecart(observe, _histogramme(dct.arrondir(quantifies * anterieur, pas), borne))
            if ecart is None:
                continue
            if pas % anterieur == 0:
                # Un pas antérieur qui divise celui du fichier ne laisse aucune trace.
                simple = ecart if simple is None else min(simple, ecart)
            elif double is None or ecart < double[0]:
                double = (ecart, anterieur)
        # Un écart simple nul : l'histogramme est expliqué sans double quantification.
        if simple and double is not None and simple >= RAPPORT * double[0]:
            estimation.tracees.append(rang)
            estimation.anterieurs.append(double[1])
    return estimation


def _borne(absolus: npt.NDArray[np.int64]) -> int:
    """Plus petite borne, de 8 à 128, qui contient 99,5 % des coefficients."""
    effectifs = np.cumsum(np.bincount(np.minimum(absolus, _BORNE_MAX), minlength=_BORNE_MAX + 1))
    total = int(effectifs[-1])
    for borne in range(_BORNE_MIN, _BORNE_MAX):
        if 1000 * int(effectifs[borne]) >= 995 * total:
            return borne
    return _BORNE_MAX


_TABLES_IJG = {qualite: dct.table_ijg(qualite) for qualite in range(1, 101)}


def qualites_ijg(tracees: list[int], anterieurs: list[int]) -> list[int]:
    """Qualités de libjpeg dont la table de luminance a ces pas à ces fréquences."""
    return [
        qualite
        for qualite, table in _TABLES_IJG.items()
        if all(table[rang] == pas for rang, pas in zip(tracees, anterieurs, strict=True))
    ]


def analyser(contexte: Contexte) -> None:
    lecture = jpeg.lire(contexte)
    coefficients = lecture.coefficients
    if coefficients is None:
        # Sans coefficients, la lecture a toujours une raison d'arrêt.
        raison = lecture.arret or RaisonNonMenee.FORMAT_PARTIEL
        contexte.non_mener(raison, localisation=lecture.localisation_arret())
        return
    estimation = estimer(coefficients)
    localisation = Localisation(chemin="composante 1, région du haut de l'image")
    contexte.observer("doublejpeg.procede", coefficients.procede)
    contexte.observer("doublejpeg.blocs", estimation.blocs, localisation=localisation)
    contexte.observer("doublejpeg.blocs_image", coefficients.blocs_image)
    contexte.observer(
        "doublejpeg.frequences_examinees", len(estimation.examinees), localisation=localisation
    )
    if not estimation.examinees:
        return
    contexte.observer("doublejpeg.frequences", estimation.examinees, localisation=localisation)
    contexte.observer("doublejpeg.pas", [coefficients.table[rang] for rang in estimation.examinees])
    contexte.observer("doublejpeg.traces", len(estimation.tracees), localisation=localisation)
    if not estimation.tracees:
        return
    contexte.observer("doublejpeg.frequences_tracees", estimation.tracees)
    contexte.observer("doublejpeg.pas_anterieurs", estimation.anterieurs)
    if len(estimation.tracees) >= QUALITE_TRACES_MIN:
        qualites = qualites_ijg(estimation.tracees, estimation.anterieurs)
        if qualites:
            contexte.observer("doublejpeg.qualites_ijg_anterieures", qualites)
