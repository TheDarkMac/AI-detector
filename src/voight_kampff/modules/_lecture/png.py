"""Pixels d'un PNG, en rouge, vert et bleu sur huit bits (ISO/IEC 15948:2004 ; ADR-0202).

Le lecteur parcourt les blocs du PNG, décompresse les données ``IDAT`` par zlib, au fil de la
lecture et dans le budget de décompression du contexte, et défait les filtres des lignes
(§9.2), sur les premières lignes de l'image seulement : au plus ``pixels`` pixels. Les images en
couleurs vraies (types 2 et 6, huit ou seize bits) et à palette (type 3) sont lues ; l'alpha est
ignoré, une valeur sur seize bits est réduite à son octet de poids fort, comme le fait OpenCV.
Une image en niveaux de gris (types 0 et 4) est reconnue sans être décompressée : elle n'a pas
de chrominance. L'entrelacement Adam7 n'est pas lu (format partiel). Les sommes de contrôle CRC
ne sont pas vérifiées : une image dont un CRC est faux est lue comme un décodeur tolérant la lirait.

Un PNG malformé n'y lève jamais d'exception : la lecture s'arrête et rend sa raison, fichier
tronqué si les données manquent, format partiel sinon.
"""

import zlib
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from voight_kampff._travail.contexte import Contexte
from voight_kampff.rapport.modele import Localisation, Plage, RaisonNonMenee

__all__ = ["Image", "Lecture", "lire"]

SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PROFONDEURS = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
"""Profondeurs admises pour chaque type de couleurs (tableau 11.1)."""
_CANAUX = {2: 3, 3: 1, 6: 4}
_GRIS = frozenset({0, 4})
_MORCEAU = 1 << 20
"""Octets compressés lus à la fois."""
_BLOC = 1 << 20
"""Octets décompressés au plus à chaque appel de zlib, comptés contre le budget."""


@dataclass(frozen=True, slots=True)
class Image:
    """Pixels des premières lignes de l'image."""

    largeur: int
    hauteur: int
    lignes: int
    """Lignes lues, à partir du haut de l'image."""
    rvb: npt.NDArray[np.int64] | None
    """``lignes`` x ``largeur`` x 3 valeurs de 0 à 255 ; ``None`` pour une image en niveaux de
    gris, qui n'est pas décompressée."""


@dataclass(frozen=True, slots=True)
class Lecture:
    """Image lue, ou la raison de l'arrêt et sa position."""

    image: Image | None
    arret: RaisonNonMenee | None = None
    position: int = 0

    def localisation_arret(self) -> Localisation:
        return Localisation(chemin="blocs du PNG", octets=Plage(self.position, 1))


class _Arret(Exception):
    def __init__(self, raison: RaisonNonMenee, position: int) -> None:
        super().__init__(raison)
        self.raison = raison
        self.position = position


@dataclass(frozen=True, slots=True)
class _Entete:
    largeur: int
    hauteur: int
    profondeur: int
    couleurs: int


def lire(contexte: Contexte, *, pixels: int) -> Lecture:
    """Pixels des premières lignes du PNG, au plus ``pixels`` pixels (au moins une ligne)."""
    try:
        return Lecture(_lire(contexte, pixels))
    except _Arret as arret:
        return Lecture(None, arret.raison, arret.position)


def _lire(contexte: Contexte, pixels: int) -> Image:
    if contexte.lire(0, 8) != SIGNATURE:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, 0)
    entete, palette, idat, complet = _blocs(contexte)
    if entete.couleurs in _GRIS:
        return Image(entete.largeur, entete.hauteur, 0, None)
    if entete.couleurs == 3 and not palette:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, 8)
    canaux = _CANAUX[entete.couleurs]
    bits = canaux * entete.profondeur
    longueur = (entete.largeur * bits + 7) // 8
    lignes = min(entete.hauteur, max(1, pixels // entete.largeur))
    brut = _decompresser(contexte, idat, lignes * (longueur + 1), complet)
    octets = _defiltrer(brut, lignes, longueur, max(1, bits // 8), idat[0][0])
    return Image(entete.largeur, entete.hauteur, lignes, _rvb(octets, entete, palette))


def _blocs(contexte: Contexte) -> tuple[_Entete, bytes, list[tuple[int, int]], bool]:
    """En-tête, palette et plages des données ``IDAT`` ; vrai si le bloc ``IEND`` est atteint."""
    position = 8
    entete: _Entete | None = None
    palette = b""
    idat: list[tuple[int, int]] = []
    while True:
        tete = contexte.lire(position, 8)
        if len(tete) < 8:
            if entete is not None and idat:
                return entete, palette, idat, False  # IEND manquant après les données : toléré
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        longueur, nature = int.from_bytes(tete[:4], "big"), tete[4:8]
        if longueur > 0x7FFFFFFF or (entete is None and nature != b"IHDR"):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        contexte.compter_objets()
        debut = position + 8
        if nature == b"IEND":
            if entete is None or not idat:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            return entete, palette, idat, True
        if debut + longueur > contexte.taille:
            if nature == b"IDAT" and entete is not None:
                idat.append((debut, contexte.taille - debut))
                return entete, palette, idat, False
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        if nature == b"IHDR":
            if entete is not None:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            entete = _ihdr(contexte, contexte.lire(debut, longueur), position)
        elif nature == b"PLTE":
            if longueur % 3 or longueur > 768:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            palette = contexte.lire(debut, longueur)
        elif nature == b"IDAT" and longueur:
            idat.append((debut, longueur))
        position = debut + longueur + 4


def _ihdr(contexte: Contexte, donnees: bytes, position: int) -> _Entete:
    if len(donnees) != 13:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
    largeur = int.from_bytes(donnees[0:4], "big")
    hauteur = int.from_bytes(donnees[4:8], "big")
    profondeur, couleurs, compression, filtre, entrelacement = donnees[8:13]
    if (
        not largeur
        or not hauteur
        or profondeur not in _PROFONDEURS.get(couleurs, ())
        or compression
        or filtre
        or entrelacement > 1
    ):
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
    contexte.verifier_dimensions(largeur, hauteur)
    if entrelacement:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)  # Adam7 : non lu
    return _Entete(largeur, hauteur, profondeur, couleurs)


def _decompresser(
    contexte: Contexte, idat: list[tuple[int, int]], besoin: int, complet: bool
) -> bytes:
    """Les ``besoin`` premiers octets du flux zlib des données ``IDAT``."""
    flux = zlib.decompressobj()
    morceaux: list[bytes] = []
    obtenus = 0
    try:
        for debut, longueur in idat:
            for position in range(debut, debut + longueur, _MORCEAU):
                entree = contexte.lire(position, min(_MORCEAU, debut + longueur - position))
                while entree and obtenus < besoin and not flux.eof:
                    sortie = flux.decompress(entree, min(_BLOC, besoin - obtenus))
                    contexte.compter_decompression(
                        len(entree) - len(flux.unconsumed_tail), len(sortie)
                    )
                    morceaux.append(sortie)
                    obtenus += len(sortie)
                    entree = flux.unconsumed_tail
                if obtenus >= besoin or flux.eof:
                    break
            if obtenus >= besoin or flux.eof:
                break
    except zlib.error:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, idat[0][0]) from None
    if obtenus < besoin:
        raison = RaisonNonMenee.FORMAT_PARTIEL if complet else RaisonNonMenee.FICHIER_TRONQUE
        raise _Arret(raison, idat[0][0])
    return b"".join(morceaux)[:besoin]


def _defiltrer(
    brut: bytes, lignes: int, longueur: int, pas: int, position: int
) -> npt.NDArray[np.uint8]:
    """Octets des lignes, filtres défaits (§9.2) ; ``pas`` octets par pixel, au moins un."""
    resultat = np.zeros((lignes, longueur), dtype=np.uint8)
    precedente = np.zeros(longueur, dtype=np.uint8)
    for ligne in range(lignes):
        debut = ligne * (longueur + 1)
        filtre = brut[debut]
        donnees = brut[debut + 1 : debut + 1 + longueur]
        if filtre == 0:
            courante = np.frombuffer(donnees, dtype=np.uint8)
        elif filtre == 1:
            # Sub : somme cumulée, octet par octet, des octets de même rang dans chaque pixel.
            valeurs = np.frombuffer(donnees, dtype=np.uint8).reshape(-1, pas)
            courante = np.cumsum(valeurs, axis=0, dtype=np.uint8).reshape(-1)
        elif filtre == 2:
            courante = np.frombuffer(donnees, dtype=np.uint8) + precedente
        elif filtre == 3:
            courante = np.frombuffer(_moyenne(donnees, precedente.tobytes(), pas), np.uint8)
        elif filtre == 4:
            courante = np.frombuffer(_paeth(donnees, precedente.tobytes(), pas), np.uint8)
        else:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        resultat[ligne] = courante
        precedente = resultat[ligne]
    return resultat


def _moyenne(donnees: bytes, precedente: bytes, pas: int) -> bytearray:
    """Filtre Average : chaque octet plus la moyenne, arrondie vers le bas, de l'octet de gauche
    et de celui du dessus."""
    ligne = bytearray(donnees)
    for i in range(pas):
        ligne[i] = (ligne[i] + (precedente[i] >> 1)) & 0xFF
    for i in range(pas, len(ligne)):
        ligne[i] = (ligne[i] + ((ligne[i - pas] + precedente[i]) >> 1)) & 0xFF
    return ligne


def _paeth(donnees: bytes, precedente: bytes, pas: int) -> bytearray:
    """Filtre Paeth : chaque octet plus celui de gauche, du dessus ou du coin, le plus proche de
    leur prédiction (§9.4)."""
    ligne = bytearray(donnees)
    for i in range(pas):
        # À gauche du premier pixel, a et c valent 0 : la prédiction est l'octet du dessus.
        ligne[i] = (ligne[i] + precedente[i]) & 0xFF
    for i in range(pas, len(ligne)):
        a, b, c = ligne[i - pas], precedente[i], precedente[i - pas]
        pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
        if pa <= pb and pa <= pc:
            ligne[i] = (ligne[i] + a) & 0xFF
        elif pb <= pc:
            ligne[i] = (ligne[i] + b) & 0xFF
        else:
            ligne[i] = (ligne[i] + c) & 0xFF
    return ligne


def _rvb(octets: npt.NDArray[np.uint8], entete: _Entete, palette: bytes) -> npt.NDArray[np.int64]:
    lignes, largeur = octets.shape[0], entete.largeur
    if entete.couleurs == 3:
        if entete.profondeur < 8:
            bits = np.unpackbits(octets, axis=1).reshape(lignes, -1, entete.profondeur)
            poids = 1 << np.arange(entete.profondeur - 1, -1, -1)
            indices = (bits * poids).sum(axis=2)[:, :largeur]
        else:
            indices = octets[:, :largeur].astype(np.int64)
        couleurs = np.frombuffer(palette, dtype=np.uint8).reshape(-1, 3).astype(np.int64)
        if int(indices.max()) >= len(couleurs):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, 8)
        resultat: npt.NDArray[np.int64] = couleurs[indices]
        return resultat
    canaux = _CANAUX[entete.couleurs]
    if entete.profondeur == 16:
        # Octet de poids fort de chaque valeur sur seize bits, rangée en gros-boutiste.
        valeurs = octets.reshape(lignes, largeur, canaux, 2)[:, :, :3, 0]
    else:
        valeurs = octets.reshape(lignes, largeur, canaux)[:, :, :3]
    resultat = valeurs.astype(np.int64)
    return resultat
