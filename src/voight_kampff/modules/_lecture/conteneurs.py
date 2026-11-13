"""Blocs de métadonnées d'une image, d'un fichier audio ou vidéo : où ils sont, sans les
interpréter (ADR-0115, ADR-0131).

Le conteneur est parcouru par sa structure seule : segments JPEG jusqu'au premier SOS, blocs PNG
jusqu'à IEND, blocs RIFF de WebP et de WAV, boîtes ISOBMFF de HEIC (``meta``, ``iinf``,
``iloc``) et de M4A, MP4 et MOV (``moov``), balises ID3 d'un MP3 ou d'un AAC, blocs de
métadonnées d'un FLAC, pages Ogg, éléments EBML d'un WebM. Aucune donnée d'image ni de son n'est
décodée. Chaque module garde les blocs de la nature qu'il lit ; le parcours est refait par
chacun, ce qui garde leurs erreurs séparées (ADR-0114).

Un parcours interrompu rend les blocs trouvés jusque-là et la raison de l'arrêt : fichier
tronqué si la structure annonce plus d'octets que la partie n'en a, format partiel si elle est
incohérente ou emploie ce que le lecteur ne sait pas lire.
"""

import zlib
from collections.abc import Generator, Iterator
from dataclasses import dataclass
from enum import StrEnum

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import ebml
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
    ID3V2 = "id3v2"
    """Balise ID3v2 entière, en-tête de dix octets compris."""
    ID3V1 = "id3v1"
    """Balise ID3v1 : les 128 derniers octets, ``TAG`` compris."""
    INFO_RIFF = "info_riff"
    """Sous-blocs d'une liste ``LIST`` de type ``INFO`` (WAV), après le type."""
    BEXT = "bext"
    """Bloc ``bext`` d'un WAV de diffusion (EBU Tech 3285)."""
    VORBIS = "vorbis"
    """Commentaires Vorbis : chaîne du fournisseur puis champs, sans l'en-tête du paquet."""
    QUICKTIME = "quicktime"
    """Contenu d'une boîte ``mvhd``, ``udta`` ou ``meta`` de ``moov`` (M4A, MP4, MOV)."""
    MATROSKA = "matroska"
    """Contenu d'un élément ``Info`` ou ``Tags`` du segment (WebM)."""


@dataclass(frozen=True, slots=True)
class Bloc:
    """Bloc de métadonnées : sa nature, son emplacement, les octets qui le composent."""

    nature: Nature
    chemin: str
    """Élément de la structure qui le porte : segment, bloc, élément HEIC."""
    etendues: tuple[Plage, ...]
    """Plages de la partie, dans l'ordre ; plusieurs pour un élément HEIC morcelé ou un paquet
    Ogg réparti sur plusieurs pages."""

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


# RIFF : WebP (RFC 9649), WAV (Microsoft RIFF ; EBU Tech 3285)


def _blocs_riff(contexte: Contexte) -> Iterator[tuple[bytes, int, int, int]]:
    """Nature, début, longueur et position de chaque bloc après l'en-tête ``RIFF``."""
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
        yield nature, debut, longueur, position
        position = debut + longueur + (longueur & 1)
    if position < fin:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)


def _webp(contexte: Contexte) -> Iterator[Bloc]:
    for nature, debut, longueur, position in _blocs_riff(contexte):
        if nature in (b"EXIF", b"XMP ") and longueur:
            plage = _plage(contexte, debut, longueur, position)
            if nature == b"XMP ":
                yield Bloc(Nature.XMP, "XMP", (plage,))
            elif contexte.lire(debut, 6) != b"Exif\x00\x00":
                yield Bloc(Nature.EXIF, "EXIF", (plage,))
            elif (bloc := _decoupe(Nature.EXIF, "EXIF", debut, longueur, 6)) is not None:
                # Préfixe de JPEG que certains outils recopient (RFC 9649 le déconseille).
                yield bloc


_BLOCS_WAV = {
    b"bext": Nature.BEXT,
    b"id3 ": Nature.ID3V2,
    b"ID3 ": Nature.ID3V2,
    b"_PMX": Nature.XMP,
}
"""Blocs lus d'un WAV, hors ``LIST`` : ``id3 `` en minuscules chez la plupart des outils."""


def _wav(contexte: Contexte) -> Iterator[Bloc]:
    for nature, debut, longueur, position in _blocs_riff(contexte):
        if nature == b"LIST" and longueur > 4 and contexte.lire(debut, 4) == b"INFO":
            plage = _plage(contexte, debut + 4, longueur - 4, position)
            yield Bloc(Nature.INFO_RIFF, "LIST INFO", (plage,))
        elif nature in _BLOCS_WAV and longueur:
            plage = _plage(contexte, debut, longueur, position)
            yield Bloc(_BLOCS_WAV[nature], nature.decode("latin-1"), (plage,))


# ID3 (id3.org : ID3v2.2, v2.3, v2.4 ; ID3v1) devant un MP3, un AAC ou un FLAC


def _id3v2(contexte: Contexte, position: int) -> Generator[Bloc, None, int]:
    """Balises ID3v2 consécutives depuis ``position`` ; rend la position qui suit la dernière."""
    while True:
        tete = contexte.lire(position, 10)
        if not tete.startswith(b"ID3"):
            return position
        if len(tete) < 10:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        if tete[3] not in (2, 3, 4) or any(octet & 0x80 for octet in tete[6:10]):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        contexte.compter_objets()
        longueur = 10 + sum(octet << (7 * (3 - i)) for i, octet in enumerate(tete[6:10]))
        longueur += 10 if tete[3] == 4 and tete[5] & 0x10 else 0  # pied de balise
        yield Bloc(Nature.ID3V2, "ID3v2", (_plage(contexte, position, longueur, position),))
        position += longueur


def _mpeg(contexte: Contexte) -> Iterator[Bloc]:
    """MP3 ou AAC : balises ID3v2 en tête ; ID3v1 en fin d'un MP3 seulement, comme
    l'identification (ADR-0070)."""
    fin = yield from _id3v2(contexte, 0)
    debut = contexte.taille - 128
    if contexte.format_reel == "mp3" and debut >= fin and contexte.lire(debut, 3) == b"TAG":
        yield Bloc(Nature.ID3V1, "ID3v1", (Plage(debut, 128),))


def _flac(contexte: Contexte) -> Iterator[Bloc]:
    """Blocs de métadonnées d'un FLAC (RFC 9639, §8), après d'éventuelles balises ID3v2."""
    position = yield from _id3v2(contexte, 0)
    if contexte.lire(position, 4) != b"fLaC":
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
    position += 4
    while True:
        tete = contexte.lire(position, 4)
        if len(tete) < 4:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        contexte.compter_objets()
        nature, longueur, debut = tete[0] & 0x7F, _gros(tete[1:4]), position + 4
        if nature == 127:  # interdit : ne peut se distinguer d'une trame
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        _verifier(contexte, debut, longueur, position)
        if nature == 4 and longueur:
            yield Bloc(Nature.VORBIS, "VORBIS_COMMENT", (Plage(debut, longueur),))
        if tete[0] & 0x80:  # dernier bloc de métadonnées
            return
        position = debut + longueur


# Ogg (RFC 3533) : Vorbis, Opus (RFC 7845), Theora, Speex, FLAC (RFC 9639)

_OGG = (
    (b"\x01vorbis", b"\x03vorbis"),
    (b"OpusHead", b"OpusTags"),
    (b"\x80theora", b"\x81theora"),
    (b"Speex   ", b""),
)
"""Premier paquet d'un flux, et début de son paquet de commentaires, le second."""
_OGG_FLAC = b"\x7fFLAC"


@dataclass(slots=True)
class _Flux:
    """Flux logique d'un Ogg : paquet en cours et paquets complets."""

    morceaux: list[Plage]
    paquets: int = 0
    premier: bytes = b""
    """Début du premier paquet, qui nomme le codec."""
    fini: bool = False


def _ogg(contexte: Contexte) -> Iterator[Bloc]:
    """Paquet de commentaires de chaque flux du premier maillon de la chaîne.

    Les paquets d'en-tête précèdent les données dans la correspondance de chaque codec avec
    Ogg : le parcours s'arrête dès que chaque flux connu a donné son second paquet.
    """
    flux: dict[int, _Flux] = {}
    position = 0
    while position < contexte.taille:
        tete = contexte.lire(position, 27)
        if not tete.startswith(b"OggS\x00"):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        if len(tete) < 27:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        contexte.compter_objets()
        table = contexte.lire(position + 27, tete[26])
        if len(table) < tete[26]:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        debut = position + 27 + len(table)
        if debut + sum(table) > contexte.taille:
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        courant = flux.setdefault(_petit(tete[14:18]), _Flux([]))
        if bool(tete[5] & 1) != bool(courant.morceaux) and not courant.fini:
            # Suite annoncée sans paquet commencé, ou paquet commencé sans suite annoncée.
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        for longueur in table:
            if not courant.fini:
                bloc = _segment_ogg(contexte, courant, _petit(tete[14:18]), debut, longueur)
                if bloc is not None:
                    yield bloc
            debut += longueur
        if all(f.fini for f in flux.values()):
            return
        position = debut


def _segment_ogg(
    contexte: Contexte, courant: _Flux, numero: int, debut: int, longueur: int
) -> Bloc | None:
    """Ajoute un segment au paquet en cours ; rend le bloc de commentaires qu'il achève."""
    if longueur:
        dernier = courant.morceaux[-1] if courant.morceaux else None
        if dernier is not None and dernier.debut + dernier.longueur == debut:
            courant.morceaux[-1] = Plage(dernier.debut, dernier.longueur + longueur)
        else:
            courant.morceaux.append(Plage(debut, longueur))
        if sum(m.longueur for m in courant.morceaux) > TAILLE_MAX_LECTURE:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, debut)
    if longueur == 255:
        return None  # le paquet continue
    morceaux, courant.morceaux = courant.morceaux, []
    courant.paquets += 1
    tete = b""
    for morceau in morceaux:
        if len(tete) >= 16:
            break
        tete += contexte.lire(morceau.debut, min(morceau.longueur, 16))
    if courant.paquets == 1:
        courant.premier = tete
        courant.fini = not tete.startswith(_OGG_FLAC) and not any(
            tete.startswith(premier) for premier, _ in _OGG
        )
        return None
    courant.fini = True
    if courant.premier.startswith(_OGG_FLAC):
        # Chaque paquet d'en-tête est un bloc de métadonnées, en-tête de quatre octets compris.
        entete = 4 if tete[:1] and tete[0] & 0x7F == 4 else None
    else:
        commentaires = next(c for p, c in _OGG if courant.premier.startswith(p))
        entete = len(commentaires) if tete.startswith(commentaires) else None
    # Un paquet qui continue sur la page suivante y a au moins 255 octets : l'en-tête, de huit
    # octets au plus, tient dans son premier morceau.
    if entete is None or not morceaux or morceaux[0].longueur <= entete:
        return None
    premier = Plage(morceaux[0].debut + entete, morceaux[0].longueur - entete)
    return Bloc(Nature.VORBIS, f"flux {numero:08x} / commentaires", (premier, *morceaux[1:]))


# HEIC (ISO/CEI 14496-12 ; ISO/CEI 23008-12)


@dataclass(frozen=True, slots=True)
class _Boite:
    nature: bytes
    debut: int
    """Position du contenu, après l'en-tête."""
    fin: int


def _boites(
    contexte: Contexte, debut: int, fin: int, *, terminal: bool = False
) -> Iterator[_Boite]:
    """Boîtes de ``debut`` à ``fin`` ; avec ``terminal``, quatre octets nuls peuvent clore la
    liste, comme dans ``udta`` (QuickTime File Format)."""
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
    if terminal and fin - position == 4 and contexte.lire(position, 4) == b"\x00" * 4:
        return
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


# M4A, MP4, MOV (ISO/CEI 14496-12 ; Apple, QuickTime File Format ; XMP, partie 3)

_UUID_XMP = bytes.fromhex("be7acfcb97a942e89c71999491e3afac")


def _quicktime(contexte: Contexte) -> Iterator[Bloc]:
    """Boîtes ``mvhd``, ``udta`` et ``meta`` du premier ``moov`` ; paquets XMP d'une boîte
    ``uuid`` de premier niveau ou d'une boîte ``XMP_`` de ``moov/udta``.

    Les métadonnées des pistes (``trak``) ne sont pas relevées (ADR-0132).
    """
    moov_lu = False
    for boite in _boites(contexte, 0, contexte.taille):
        if boite.nature == b"uuid" and boite.fin - boite.debut > 16:
            if contexte.lire(boite.debut, 16) == _UUID_XMP:
                longueur = boite.fin - boite.debut - 16
                plage = _plage(contexte, boite.debut + 16, longueur, boite.debut)
                yield Bloc(Nature.XMP, "uuid XMP", (plage,))
        elif boite.nature == b"moov" and not moov_lu:
            moov_lu = True
            for enfant in _boites(contexte, boite.debut, boite.fin):
                if enfant.nature not in (b"mvhd", b"udta", b"meta"):
                    continue
                chemin = f"moov/{enfant.nature.decode('latin-1')}"
                if enfant.fin > enfant.debut:
                    longueur = enfant.fin - enfant.debut
                    plage = _plage(contexte, enfant.debut, longueur, enfant.debut)
                    yield Bloc(Nature.QUICKTIME, chemin, (plage,))
                if enfant.nature == b"udta":
                    yield from _xmp_udta(contexte, enfant)


def _xmp_udta(contexte: Contexte, udta: _Boite) -> Iterator[Bloc]:
    for boite in _boites(contexte, udta.debut, udta.fin, terminal=True):
        if boite.nature == b"XMP_" and boite.fin > boite.debut:
            plage = _plage(contexte, boite.debut, boite.fin - boite.debut, boite.debut)
            yield Bloc(Nature.XMP, "moov/udta/XMP_", (plage,))


# WebM (RFC 8794 ; RFC 9559)

_EBML = 0x1A45DFA3
_SEGMENT = 0x18538067
_INFO = 0x1549A966
_TAGS = 0x1254C367
_CLUSTER = 0x1F43B675
_NIVEAU_1 = frozenset(
    {0x114D9B74, _INFO, 0x1654AE6B, 0x1043A770, _CLUSTER, 0x1C53BB6B, 0x1941A469, _TAGS}
)
"""Éléments de premier niveau du segment : l'un d'eux clôt un élément de taille inconnue."""


def _element(contexte: Contexte, position: int) -> tuple[int, int, int | None]:
    """Identifiant, longueur de l'en-tête et taille (``None`` si inconnue) d'un élément."""
    tete = contexte.lire(position, 12)
    try:
        return ebml.entete(tete, 0)
    except ebml.Incomplet:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position) from None
    except ebml.Invalide:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position) from None


def _webm(contexte: Contexte) -> Iterator[Bloc]:
    """Éléments ``Info`` et ``Tags`` du segment, parcouru élément par élément."""
    identifiant, entete, taille = _element(contexte, 0)
    if identifiant != _EBML or taille is None:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, 0)
    position = entete + taille
    identifiant, entete, taille = _element(contexte, position)
    if identifiant != _SEGMENT:
        raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
    position += entete
    fin = contexte.taille if taille is None else position + taille
    while position < min(fin, contexte.taille):
        identifiant, entete, taille = _element(contexte, position)
        contexte.compter_objets()
        debut = position + entete
        if taille is None:
            if identifiant != _CLUSTER:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            position = _fin_inconnue(contexte, debut, fin)
            continue
        if debut + taille > min(fin, contexte.taille):
            raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
        if identifiant in (_INFO, _TAGS) and taille:
            chemin = "Segment/Info" if identifiant == _INFO else "Segment/Tags"
            yield Bloc(Nature.MATROSKA, chemin, (_plage(contexte, debut, taille, position),))
        position = debut + taille
    if fin > contexte.taille:
        raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, contexte.taille)


def _fin_inconnue(contexte: Contexte, position: int, fin: int) -> int:
    """Fin d'un ``Cluster`` de taille inconnue : le premier élément de premier niveau qui le
    suit (RFC 8794, §6.2), ou la fin du segment."""
    while position < min(fin, contexte.taille):
        identifiant, entete, taille = _element(contexte, position)
        if identifiant in _NIVEAU_1:
            return position
        contexte.compter_objets()
        if taille is None:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        position += entete + taille
    return position


_PARCOURS = {
    "jpeg": _jpeg,
    "png": _png,
    "webp": _webp,
    "heic": _heic,
    "wav": _wav,
    "mp3": _mpeg,
    "aac": _mpeg,
    "flac": _flac,
    "ogg": _ogg,
    "m4a": _quicktime,
    "mp4": _quicktime,
    "mov": _quicktime,
    "webm": _webm,
}
