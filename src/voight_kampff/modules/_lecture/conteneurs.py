"""Blocs de métadonnées d'une image : où ils sont, sans les interpréter (ADR-0115).

Le conteneur est parcouru par sa structure seule : segments JPEG jusqu'au premier SOS, blocs PNG
jusqu'à IEND, blocs RIFF de WebP, boîtes ISOBMFF de HEIC (``meta``, ``iinf``, ``iloc``). Aucune
donnée d'image n'est décodée. Chaque module garde les blocs de la nature qu'il lit ; le parcours
est refait par chacun, ce qui garde leurs erreurs séparées (ADR-0114).

Un parcours interrompu rend les blocs trouvés jusque-là et la raison de l'arrêt : fichier
tronqué si la structure annonce plus d'octets que la partie n'en a, format partiel si elle est
incohérente ou emploie ce que le lecteur ne sait pas lire.
"""

import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Contexte
from voight_kampff.rapport.modele import Localisation, Plage, RaisonNonMenee

__all__ = ["Bloc", "Nature", "Releve", "TextePng", "lire_bloc", "relever", "texte_png"]


class Nature(StrEnum):
    """Nature d'un bloc de métadonnées."""

    EXIF = "exif"
    """Structure TIFF : en-tête, IFD0 et suivants."""
    XMP = "xmp"
    """Paquet XMP complet."""
    XMP_ETENDU = "xmp_etendu"
    """Morceau d'un paquet XMP étendu (JPEG) : GUID, longueur totale, position, données."""
    PHOTOSHOP = "photoshop"
    """Ressources Photoshop (APP13), dont l'IPTC-IIM."""
    TEXTE_PNG = "texte_png"
    """Bloc ``tEXt``, ``zTXt`` ou ``iTXt`` d'un PNG, hors XMP."""


@dataclass(frozen=True, slots=True)
class Bloc:
    """Bloc de métadonnées : sa nature, son emplacement, les octets qui le composent."""

    nature: Nature
    chemin: str
    """Élément de la structure qui le porte : segment, bloc, élément HEIC."""
    etendues: tuple[Plage, ...]
    """Plages de la partie, dans l'ordre ; plusieurs seulement pour un élément HEIC morcelé."""

    def localisation(self, suite: str | None = None) -> Localisation:
        """Chemin du bloc, suivi de ``suite`` ; plage d'octets si le bloc est d'un seul tenant."""
        chemin = self.chemin if suite is None else f"{self.chemin} / {suite}"
        octets = self.etendues[0] if len(self.etendues) == 1 else None
        return Localisation(chemin=chemin, octets=octets)


@dataclass(frozen=True, slots=True)
class Releve:
    """Blocs trouvés dans la partie, et la raison d'un parcours interrompu."""

    blocs: tuple[Bloc, ...]
    arret: RaisonNonMenee | None = None
    position: int = 0
    """Position où le parcours s'est arrêté."""

    def localisation_arret(self) -> Localisation:
        return Localisation(chemin="structure du conteneur", octets=Plage(self.position, 1))


class _Arret(Exception):
    def __init__(self, raison: RaisonNonMenee, position: int) -> None:
        super().__init__(raison)
        self.raison = raison
        self.position = position


def _gros(octets: bytes) -> int:
    return int.from_bytes(octets, "big")


def _petit(octets: bytes) -> int:
    return int.from_bytes(octets, "little")


def relever(contexte: Contexte) -> Releve:
    """Blocs de métadonnées de la partie, selon son format."""
    parcours = _PARCOURS[contexte.format_reel]
    blocs: list[Bloc] = []
    try:
        for bloc in parcours(contexte):
            blocs.append(bloc)
    except _Arret as arret:
        return Releve(tuple(blocs), arret.raison, arret.position)
    return Releve(tuple(blocs))


def lire_bloc(contexte: Contexte, bloc: Bloc, debut: int = 0) -> bytes:
    """Octets du bloc à partir de ``debut`` ; le bloc tient dans une lecture (16 Mio)."""
    morceaux = [contexte.lire(e.debut, e.longueur) for e in bloc.etendues]
    return b"".join(morceaux)[debut:]


def _verifier(contexte: Contexte, debut: int, longueur: int, position: int) -> None:
    """Arrêt si la zone déborde de la partie ou dépasse une lecture ; elle peut être vide."""
    if debut + longueur > contexte.taille:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
    if longueur > TAILLE_MAX_LECTURE:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)


def _plage(contexte: Contexte, debut: int, longueur: int, position: int) -> Plage:
    """Plage non vide de la partie, ou arrêt si elle déborde ou dépasse une lecture."""
    _verifier(contexte, debut, longueur, position)
    return Plage(debut, longueur)


# JPEG (T.81, annexe B ; EXIF 3.0 ; XMP, partie 3)

_EXIF = b"Exif\x00"
_XMP = b"http://ns.adobe.com/xap/1.0/\x00"
_XMP_ETENDU = b"http://ns.adobe.com/xmp/extension/\x00"
_PHOTOSHOP = b"Photoshop 3.0\x00"


def _jpeg(contexte: Contexte) -> Iterator[Bloc]:
    position = 2
    while True:
        tete = contexte.lire(position, 4)
        if len(tete) < 2:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        if tete[0] != 0xFF:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        marqueur = tete[1]
        contexte.compter_objets()
        if marqueur == 0xFF:  # octet de remplissage
            position += 1
            continue
        if marqueur == 0x01 or 0xD0 <= marqueur <= 0xD7:  # sans longueur
            position += 2
            continue
        if marqueur in (0xD9, 0xDA):  # EOI, SOS : les métadonnées les précèdent
            return
        if len(tete) < 4:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        longueur = _gros(tete[2:4]) - 2
        if longueur < 0 or marqueur in (0x00, 0xD8):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        debut = position + 4
        _verifier(contexte, debut, longueur, position)
        bloc = _segment(contexte, marqueur, debut, longueur)
        if bloc is not None:
            yield bloc
        position = debut + longueur


def _segment(contexte: Contexte, marqueur: int, debut: int, longueur: int) -> Bloc | None:
    entete = contexte.lire(debut, min(longueur, len(_XMP_ETENDU)))
    if marqueur == 0xE1:
        if entete.startswith(_EXIF):
            # « Exif » suivi de deux octets, nuls d'ordinaire.
            return _decoupe(Nature.EXIF, "APP1 Exif", debut, longueur, 6)
        if entete.startswith(_XMP):
            return _decoupe(Nature.XMP, "APP1 XMP", debut, longueur, len(_XMP))
        if entete.startswith(_XMP_ETENDU):
            return _decoupe(Nature.XMP_ETENDU, "APP1 XMP étendu", debut, longueur, len(_XMP_ETENDU))
    if marqueur == 0xED and entete.startswith(_PHOTOSHOP):
        return _decoupe(Nature.PHOTOSHOP, "APP13 Photoshop", debut, longueur, len(_PHOTOSHOP))
    return None


def _decoupe(nature: Nature, chemin: str, debut: int, longueur: int, entete: int) -> Bloc | None:
    if longueur <= entete:
        return None  # segment vide : rien à lire
    return Bloc(nature, chemin, (Plage(debut + entete, longueur - entete),))


# PNG (PNG, 3e édition)

_TEXTES = frozenset({b"tEXt", b"zTXt", b"iTXt"})
_MOT_CLE_XMP = b"XML:com.adobe.xmp"


def _png(contexte: Contexte) -> Iterator[Bloc]:
    position = 8
    while True:
        tete = contexte.lire(position, 8)
        if len(tete) < 8:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        longueur, nature = _gros(tete[:4]), tete[4:8]
        if longueur > 0x7FFFFFFF:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        contexte.compter_objets()
        debut = position + 8
        if debut + longueur + 4 > contexte.taille:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        if nature == b"IEND":
            return
        chemin = nature.decode("latin-1")
        if nature == b"eXIf" and longueur:
            yield Bloc(Nature.EXIF, chemin, (_plage(contexte, debut, longueur, position),))
        elif nature in _TEXTES and longueur:
            plage = _plage(contexte, debut, longueur, position)
            xmp = nature == b"iTXt" and contexte.lire(debut, len(_MOT_CLE_XMP) + 1) == (
                _MOT_CLE_XMP + b"\x00"
            )
            yield Bloc(Nature.XMP if xmp else Nature.TEXTE_PNG, chemin, (plage,))
        position = debut + longueur + 4


@dataclass(frozen=True, slots=True)
class TextePng:
    """Contenu d'un bloc texte PNG ; ``texte`` vaut ``None`` s'il n'a pas pu être lu."""

    mot_cle: str
    texte: str | None
    langue: str = ""
    """Langue d'un ``iTXt``, vide si non déclarée."""


def texte_png(contexte: Contexte, bloc: Bloc) -> TextePng:
    """Mot-clé et texte d'un bloc ``tEXt``, ``zTXt`` ou ``iTXt``, décompressé au besoin.

    ``tEXt`` et ``zTXt`` sont en Latin-1, ``iTXt`` en UTF-8 ; un octet UTF-8 invalide devient
    le caractère de remplacement. Une compression inconnue ou un flux invalide donnent un texte
    ``None`` : le module le dit par une analyse non menée.
    """
    donnees = lire_bloc(contexte, bloc)
    mot_cle, _, reste = donnees.partition(b"\x00")
    nom = mot_cle.decode("latin-1")
    try:
        if bloc.chemin == "tEXt":
            return TextePng(nom, reste.decode("latin-1"))
        if bloc.chemin == "zTXt":
            if reste[:1] != b"\x00":
                return TextePng(nom, None)
            return TextePng(nom, contexte.decompresser(reste[1:], "zlib").decode("latin-1"))
        compresse, methode = reste[:1], reste[1:2]
        langue, _, reste = reste[2:].partition(b"\x00")
        _traduit, _, texte = reste.partition(b"\x00")
        if compresse == b"\x01":
            if methode != b"\x00":
                return TextePng(nom, None, langue.decode("latin-1"))
            texte = contexte.decompresser(texte, "zlib")
        elif compresse != b"\x00":
            return TextePng(nom, None, langue.decode("latin-1"))
        return TextePng(nom, texte.decode("utf-8", "replace"), langue.decode("latin-1"))
    except zlib.error:
        return TextePng(nom, None)


# WebP (RFC 9649)


def _webp(contexte: Contexte) -> Iterator[Bloc]:
    tete = contexte.lire(0, 12)
    if len(tete) < 12:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, 0)
    fin = min(8 + _petit(tete[4:8]), contexte.taille)
    position = 12
    while position + 8 <= fin:
        tete = contexte.lire(position, 8)
        nature, longueur = tete[:4], _petit(tete[4:8])
        contexte.compter_objets()
        debut = position + 8
        if debut + longueur > fin:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        if nature in (b"EXIF", b"XMP ") and longueur:
            plage = _plage(contexte, debut, longueur, position)
            if nature == b"XMP ":
                yield Bloc(Nature.XMP, "XMP", (plage,))
            elif contexte.lire(debut, 6) != b"Exif\x00\x00":
                yield Bloc(Nature.EXIF, "EXIF", (plage,))
            elif (bloc := _decoupe(Nature.EXIF, "EXIF", debut, longueur, 6)) is not None:
                # Préfixe de JPEG que certains outils recopient (RFC 9649 le déconseille).
                yield bloc
        position = debut + longueur + (longueur & 1)
    if position < fin:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)


# HEIC (ISO/CEI 14496-12 ; ISO/CEI 23008-12)


@dataclass(frozen=True, slots=True)
class _Boite:
    nature: bytes
    debut: int
    """Position du contenu, après l'en-tête."""
    fin: int


def _boites(contexte: Contexte, debut: int, fin: int) -> Iterator[_Boite]:
    position = debut
    while position + 8 <= fin:
        tete = contexte.lire(position, 16)
        taille, nature, entete = _gros(tete[:4]), tete[4:8], 8
        contexte.compter_objets()
        if taille == 1:
            if len(tete) < 16:
                raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
            taille, entete = _gros(tete[8:16]), 16
        elif taille == 0:
            taille = fin - position
        if taille < entete:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        if position + taille > fin:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        yield _Boite(nature, position + entete, position + taille)
        position += taille
    if position < fin:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)


def _contenu(contexte: Contexte, boite: _Boite) -> bytes:
    _verifier(contexte, boite.debut, boite.fin - boite.debut, boite.debut)
    return contexte.lire(boite.debut, boite.fin - boite.debut)


@dataclass(frozen=True, slots=True)
class _Element:
    identifiant: int
    nature: bytes
    type_mime: str = ""


class _Curseur:
    """Lecture séquentielle d'un contenu de boîte ; un manque est un format partiel."""

    __slots__ = ("_donnees", "_origine", "position")

    def __init__(self, donnees: bytes, origine: int) -> None:
        self._donnees = donnees
        self._origine = origine
        self.position = 0

    def entier(self, taille: int) -> int:
        if taille == 0:
            return 0
        if self.position + taille > len(self._donnees):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, self._origine)
        valeur = _gros(self._donnees[self.position : self.position + taille])
        self.position += taille
        return valeur

    def chaine(self) -> str:
        fin = self._donnees.find(b"\x00", self.position)
        if fin == -1:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, self._origine)
        texte = self._donnees[self.position : fin].decode("utf-8", "replace")
        self.position = fin + 1
        return texte


def _iinf(contexte: Contexte, boite: _Boite) -> dict[int, _Element]:
    curseur = _Curseur(_contenu(contexte, boite), boite.debut)
    version = curseur.entier(4) >> 24
    curseur.entier(2 if version == 0 else 4)  # nombre d'entrées : les boîtes suffisent
    elements: dict[int, _Element] = {}
    for infe in _boites(contexte, boite.debut + curseur.position, boite.fin):
        if infe.nature != b"infe":
            continue
        entree = _Curseur(_contenu(contexte, infe), infe.debut)
        version_infe = entree.entier(4) >> 24
        if version_infe < 2:
            continue  # ancienne forme, sans type d'élément : ni Exif ni XMP
        identifiant = entree.entier(2 if version_infe == 2 else 4)
        entree.entier(2)  # protection
        nature = entree.entier(4).to_bytes(4, "big")
        entree.chaine()  # nom
        type_mime = entree.chaine() if nature == b"mime" else ""
        elements[identifiant] = _Element(identifiant, nature, type_mime)
    return elements


@dataclass(frozen=True, slots=True)
class _Emplacement:
    methode: int
    reference: int
    etendues: tuple[tuple[int, int], ...]


def _iloc(contexte: Contexte, boite: _Boite) -> dict[int, _Emplacement]:
    curseur = _Curseur(_contenu(contexte, boite), boite.debut)
    version = curseur.entier(4) >> 24
    tailles = curseur.entier(1)
    taille_position, taille_longueur = tailles >> 4, tailles & 0x0F
    tailles = curseur.entier(1)
    taille_base, taille_indice = tailles >> 4, (tailles & 0x0F) if version else 0
    if any(t not in (0, 4, 8) for t in (taille_position, taille_longueur, taille_base)):
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, boite.debut)
    nombre = curseur.entier(4 if version == 2 else 2)
    emplacements: dict[int, _Emplacement] = {}
    for _ in range(nombre):
        contexte.compter_objets()
        identifiant = curseur.entier(4 if version == 2 else 2)
        methode = curseur.entier(2) & 0x0F if version else 0
        reference = curseur.entier(2)
        base = curseur.entier(taille_base)
        etendues = []
        for _ in range(curseur.entier(2)):
            contexte.compter_objets()
            curseur.entier(taille_indice)
            position = base + curseur.entier(taille_position)
            etendues.append((position, curseur.entier(taille_longueur)))
        emplacements[identifiant] = _Emplacement(methode, reference, tuple(etendues))
    return emplacements


def _heic(contexte: Contexte) -> Iterator[Bloc]:
    meta = next((b for b in _boites(contexte, 0, contexte.taille) if b.nature == b"meta"), None)
    if meta is None:
        return
    if meta.fin - meta.debut < 4:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, meta.debut)
    enfants = {b.nature: b for b in _boites(contexte, meta.debut + 4, meta.fin)}
    if b"iinf" not in enfants or b"iloc" not in enfants:
        return
    elements = _iinf(contexte, enfants[b"iinf"])
    emplacements = _iloc(contexte, enfants[b"iloc"])
    idat = enfants.get(b"idat")
    for identifiant in sorted(elements):
        element = elements[identifiant]
        if element.nature == b"Exif":
            nature, chemin = Nature.EXIF, f"élément Exif {identifiant}"
        elif element.nature == b"mime" and element.type_mime == "application/rdf+xml":
            nature, chemin = Nature.XMP, f"élément XMP {identifiant}"
        else:
            continue
        emplacement = emplacements.get(identifiant)
        if emplacement is None or emplacement.reference != 0:
            # Sans emplacement, ou données dans un autre fichier : non lu.
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, enfants[b"iloc"].debut)
        yield Bloc(nature, chemin, _etendues(contexte, emplacement, idat))


def _etendues(
    contexte: Contexte, emplacement: _Emplacement, idat: _Boite | None
) -> tuple[Plage, ...]:
    if emplacement.methode == 1 and idat is not None:
        origine, fin = idat.debut, idat.fin
    elif emplacement.methode == 0:
        origine, fin = 0, contexte.taille
    else:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, 0)
    plages = []
    for position, longueur in emplacement.etendues:
        if longueur == 0:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, origine + position)
        if origine + position + longueur > fin:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, origine + position)
        plages.append(Plage(origine + position, longueur))
    if not plages or sum(p.longueur for p in plages) > TAILLE_MAX_LECTURE:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, origine)
    return tuple(plages)


_PARCOURS = {"jpeg": _jpeg, "png": _png, "webp": _webp, "heic": _heic}
