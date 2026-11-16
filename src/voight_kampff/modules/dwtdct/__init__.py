"""Module ``dwtdct`` : filigrane dwtDct de la bibliothèque invisible-watermark (F-24 ; ADR-0202
à ADR-0206 ; fiche ``filigrane-dwtdct``).

Les codes de référence de Stable Diffusion 1, de SDXL et de FLUX.1 posent un message fixe par la
méthode ``dwtDct`` d'invisible-watermark 0.2.0 (``imwatermark/maxDct.py``) :

1. l'image est convertie en YUV comme le fait OpenCV (``COLOR_BGR2YUV``) ; seule la composante U
   porte le message ;
2. la bande basse fréquence de sa transformée de Haar à un niveau est découpée en blocs de
   4 x 4 valeurs ; les bits du message se répètent dans l'ordre des blocs ;
3. dans chaque bloc, la plus grande valeur absolue hors de la première est quantifiée à l'échelle
   36 : décalée d'un quart d'échelle pour un 0, de trois quarts pour un 1. La méthode n'emploie
   aucune DCT, malgré son nom (ERR-0011).

La lecture suit celle de la bibliothèque, avec deux écarts mesurés (ADR-0203) :

- chaque message est lu dans le domaine où son code le pose : U sur huit bits pour Stable
  Diffusion 1 (image en entiers), U en flottant, centré sur 0,5, pour SDXL et FLUX.1 (image en
  flottants) ; SDXL l'est aussi le rouge et le bleu échangés, comme diffusers l'a posé du
  2023-07-06 au 2024-04-26, et la meilleure des deux lectures est gardée : un filigrane posé
  dans un ordre se lit en partie dans l'autre ;
- les bits sont décidés par rang : le score d'un bit est la part de ses blocs dont la valeur
  quantifiée tombe dans la seconde moitié de l'échelle ; les k bits aux scores les plus élevés
  valent 1, k étant le nombre de 1 du message. Des scores égaux de part et d'autre de ce rang
  laissent leurs bits indéterminés, comptés comme non concordants.

Sous l'hypothèse d'une image non marquée dont l'ordre des scores ne dépend pas du message, le
nombre de bits concordants suit une loi hypergéométrique : :func:`queue` en donne la probabilité
(ADR-0204).

Seule une région du haut de l'image est lue au-delà de :data:`PIXELS_MAX` pixels (ADR-0205) ; une
image de moins de :data:`PIXELS_MIN` pixels n'est pas lue, comme dans la bibliothèque. Les pixels
des WebP et des HEIC ne sont pas décodés : le module y est non mené, format partiel (ADR-0202).
Tout le calcul se fait en entiers : le résultat est le même sur toutes les machines (ADR-0189).

Observations : le nombre de pixels de l'image, l'absence de chrominance, les blocs lus et ceux de
l'image, et pour chaque lecture le nombre de bits concordants avec son message (et de bits
indéterminés, s'il y en a ; pour SDXL, si le rouge et le bleu échangés lisent mieux). Les règles
``R-DWTDCT-001`` à ``R-DWTDCT-003`` du catalogue lisent les bits concordants.
"""

from dataclasses import dataclass
from fractions import Fraction
from math import comb

import numpy as np
import numpy.typing as npt

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import pixels
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee, Zone

__all__ = [
    "ECHELLE",
    "LECTURES",
    "PIXELS_MAX",
    "PIXELS_MIN",
    "Lecture",
    "Releve",
    "analyser",
    "bits_du_message",
    "decider",
    "lire",
    "queue",
]

PIXELS_MAX = 1 << 22
"""Pixels lus au plus : 4 194 304, soit 2 048 x 2 048 (ADR-0205) ; au-delà, le haut de
l'image."""
PIXELS_MIN = 1 << 16
"""Pixels de l'image au moins : 256 x 256, le minimum de la bibliothèque à l'écriture comme à la
lecture."""
ECHELLE = 36
"""Pas de quantification de la composante U (``scales = [0, 36, 36]``)."""
_COTE = 4
"""Côté d'un bloc de la bande basse fréquence."""
_MILLION = 1_000_000


def _bits(valeur: int) -> tuple[int, ...]:
    """Bits de ``bin(valeur)[2:]``, comme les codes de SDXL et de FLUX.1 : sans zéros de tête."""
    return tuple(int(bit) for bit in format(valeur, "b"))


def bits_du_message(octets: bytes) -> tuple[int, ...]:
    """Bits des octets, poids fort d'abord (``np.unpackbits``, ``set_watermark("bytes")``)."""
    return tuple((octet >> (7 - rang)) & 1 for octet in octets for rang in range(8))


@dataclass(frozen=True, slots=True)
class Lecture:
    """Une lecture : un message, le domaine où il est posé, les ordres des couleurs essayés."""

    nom: str
    message: tuple[int, ...]
    huit_bits: bool
    """U sur huit bits, centré sur 128 (image en entiers) ; sinon en flottant, centré sur 0,5."""
    inversee: bool = False
    """Essayer aussi le rouge et le bleu échangés : l'image a pu être passée en RVB là où
    OpenCV attend du BVR. La meilleure des deux lectures est gardée."""


LECTURES = (
    # CompVis, scripts/txt2img.py : set_watermark("bytes", "StableDiffusionV1".encode()).
    Lecture("sd1", bits_du_message(b"StableDiffusionV1"), huit_bits=True),
    # Stability-AI, sgm/inference/helpers.py ; diffusers, stable_diffusion_xl/watermark.py, qui
    # passait l'image en RVB du 2023-07-06 au 2024-04-26 (huggingface/diffusers, PR 7013).
    Lecture(
        "sdxl",
        _bits(0b101100111110110010010000011110111011000110011110),
        huit_bits=False,
        inversee=True,
    ),
    # Black Forest Labs, src/flux/util.py.
    Lecture("flux", _bits(0b001010101111111010000111100111001111010100101110), huit_bits=False),
)


@dataclass(frozen=True, slots=True)
class Releve:
    """Résultat d'une lecture."""

    concordants: int
    indetermines: int
    inversee: bool = False
    """Le rouge et le bleu échangés donnent strictement plus de bits concordants."""


def _u(rvb: npt.NDArray[np.int64], huit_bits: bool, inversee: bool) -> npt.NDArray[np.int64]:
    """Composante U comme OpenCV la calcule (``COLOR_BGR2YUV``).

    Sur huit bits, en virgule fixe sur 14 bits, bornée à 0 et 255 : formule et coefficients
    vérifiés sur les 2^24 couleurs contre OpenCV 5.0.0 (ADR-0203). En flottant, ``0,492 (B - Y)
    + 0,5`` avec Y = 0,299 R + 0,587 G + 0,114 B, fois 10^6 : un entier exact.
    """
    rouge, vert, bleu = rvb[:, :, 0], rvb[:, :, 1], rvb[:, :, 2]
    if inversee:
        rouge, bleu = bleu, rouge
    if huit_bits:
        y = (1868 * bleu + 9617 * vert + 4899 * rouge + (1 << 13)) >> 14
        u8: npt.NDArray[np.int64] = np.clip(
            ((bleu - y) * 8061 + (128 << 14) + (1 << 13)) >> 14, 0, 255
        )
        return u8
    y_mille = 299 * rouge + 587 * vert + 114 * bleu
    u: npt.NDArray[np.int64] = 492 * (1000 * bleu - y_mille) + _MILLION // 2
    return u


def _scores(
    u: npt.NDArray[np.int64], lignes: int, colonnes: int, modulo: int
) -> npt.NDArray[np.bool_]:
    """Pour chaque bloc, dans l'ordre de la trame : sa valeur tombe-t-elle dans la seconde moitié
    de l'échelle ?

    La bande basse fréquence de Haar vaut (a + b + c + d) / 2 sur chaque carré de 2 x 2 pixels ;
    elle est gardée doublée, en entiers : ``modulo`` est deux fois l'échelle, dans l'unité de U.
    """
    plan = u[: 8 * lignes, : 8 * colonnes]
    doubles = plan[0::2, 0::2] + plan[0::2, 1::2] + plan[1::2, 0::2] + plan[1::2, 1::2]
    blocs = doubles.reshape(lignes, _COTE, colonnes, _COTE).transpose(0, 2, 1, 3)
    blocs = np.abs(blocs.reshape(-1, _COTE * _COTE))
    # Plus grande valeur absolue hors de la première ; la première en cas d'égalité (np.argmax).
    rangs = np.argmax(blocs[:, 1:], axis=1) + 1
    valeurs = blocs[np.arange(len(blocs)), rangs]
    resultat: npt.NDArray[np.bool_] = valeurs % modulo > modulo // 2
    return resultat


def decider(sommes: list[int], effectifs: list[int], uns: int) -> list[int | None]:
    """Bits lus par rang : 1 pour les ``uns`` scores les plus élevés, 0 pour les autres, ``None``
    pour des scores égaux de part et d'autre de ce rang."""
    scores = [Fraction(s, e) for s, e in zip(sommes, effectifs, strict=True)]
    seuil = sorted(scores, reverse=True)[uns - 1]
    nets = sum(score >= seuil for score in scores) == uns
    return [
        1 if score > seuil or (score == seuil and nets) else 0 if score < seuil else None
        for score in scores
    ]


def lire(rvb: npt.NDArray[np.int64], largeur: int, hauteur: int) -> tuple[int, dict[str, Releve]]:
    """Blocs lus et résultat de chaque lecture, sur les premières lignes de l'image ``rvb``.

    ``largeur`` et ``hauteur`` sont celles de l'image entière : la grille des blocs part de son
    coin en haut à gauche et compte ``largeur // 8`` blocs par ligne.
    """
    lignes = min(rvb.shape[0], hauteur) // 8
    colonnes = largeur // 8
    blocs = lignes * colonnes
    releves: dict[str, Releve] = {}
    plans: dict[tuple[bool, bool], npt.NDArray[np.bool_]] = {}
    for lecture in LECTURES:
        n = len(lecture.message)
        if blocs < n:
            continue
        rang_du_bit = np.arange(blocs) % n
        effectifs = [int(e) for e in np.bincount(rang_du_bit, minlength=n)]
        for inversee in (False, True) if lecture.inversee else (False,):
            cle = (lecture.huit_bits, inversee)
            if cle not in plans:
                modulo = 2 * ECHELLE * (1 if lecture.huit_bits else _MILLION)
                plans[cle] = _scores(_u(rvb, *cle), lignes, colonnes, modulo)
            sommes = np.bincount(rang_du_bit, weights=plans[cle], minlength=n)
            bits = decider([int(s) for s in sommes], effectifs, sum(lecture.message))
            releve = Releve(
                concordants=sum(
                    bit == attendu for bit, attendu in zip(bits, lecture.message, strict=True)
                ),
                indetermines=bits.count(None),
                inversee=inversee,
            )
            meilleur = releves.get(lecture.nom)
            if meilleur is None or releve.concordants > meilleur.concordants:
                releves[lecture.nom] = releve
    return blocs, releves


def queue(n: int, uns: int, concordants: int) -> Fraction:
    """Probabilité d'au moins ``concordants`` bits concordants pour une image non marquée.

    Si l'ordre des scores ne dépend pas du message, les ``uns`` bits lus à 1 sont tirés au hasard
    parmi les ``n`` : le nombre ``a`` de 1 du message parmi eux suit une loi hypergéométrique, et
    les bits concordants valent ``n - 2 uns + 2 a``.
    """
    minimum = max(0, -(-(concordants - n + 2 * uns) // 2))
    total = comb(n, uns)
    return Fraction(
        sum(comb(uns, a) * comb(n - uns, uns - a) for a in range(minimum, uns + 1)), total
    )


def analyser(contexte: Contexte) -> None:
    if contexte.format_reel not in pixels.FORMATS:
        # WebP et HEIC : le filigrane peut s'y trouver, mais leurs pixels ne sont pas décodés.
        contexte.non_mener(
            RaisonNonMenee.FORMAT_PARTIEL,
            localisation=Localisation(chemin=f"pixels {contexte.format_reel}, non décodés"),
        )
        return
    lecture = pixels.lire(contexte, pixels=PIXELS_MAX)
    image = lecture.pixels
    if image is None:
        # Sans pixels, la lecture a toujours une raison d'arrêt.
        contexte.non_mener(
            lecture.arret or RaisonNonMenee.FORMAT_PARTIEL, localisation=lecture.localisation
        )
        return
    contexte.observer("dwtdct.pixels_image", image.largeur * image.hauteur, unite="pixels")
    if image.largeur * image.hauteur < PIXELS_MIN:
        return
    if image.rvb is None:
        contexte.observer("dwtdct.chrominance", False)
        return
    blocs, releves = lire(image.rvb, image.largeur, image.hauteur)
    entiere = image.lignes == image.hauteur
    localisation = Localisation(
        chemin="composante U, image entière" if entiere else "composante U, haut de l'image",
        zone=Zone(0, 0, image.largeur, image.lignes),
    )
    contexte.observer("dwtdct.blocs", blocs, localisation=localisation)
    contexte.observer("dwtdct.blocs_image", (image.hauteur // 8) * (image.largeur // 8))
    for lu in LECTURES:
        releve = releves.get(lu.nom)
        if releve is None:
            continue  # moins de blocs que de bits du message
        contexte.observer(
            f"dwtdct.concordants_{lu.nom}",
            releve.concordants,
            unite=f"bits sur {len(lu.message)}",
            localisation=localisation,
        )
        if releve.indetermines:
            contexte.observer(f"dwtdct.indetermines_{lu.nom}", releve.indetermines)
        if releve.inversee:
            contexte.observer(f"dwtdct.rouge_et_bleu_echanges_{lu.nom}", True)
