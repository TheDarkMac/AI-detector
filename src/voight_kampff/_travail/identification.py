"""Identification du format par le contenu, dans le processus de travail (F-02, ES-07).

Le fichier est hostile : rien ici ne décode d'image ni n'interprète de données compressées. On
lit des signatures et des structures de conteneur (segments, blocs, boîtes, pages, trames)
pour situer le début et la fin logique de chaque format (ADR-0070).

Les parties sont cherchées en chaîne depuis le début du fichier : à la fin logique d'un format,
on cherche le suivant. S'y ajoutent les deux positions que les lecteurs usuels acceptent
ailleurs qu'en tête : un PDF dont l'en-tête est dans les 1024 premiers octets, une archive ZIP
lue depuis sa fin. Le texte brut n'est retenu que si rien d'autre n'est reconnu (ADR-0071).
"""

import codecs
import re
from collections.abc import Callable
from dataclasses import dataclass

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail import garde
from voight_kampff._travail.fichier import Fichier
from voight_kampff.rapport.modele import NOMBRE_MAX_PARTIES, Partie, Plage

__all__ = ["identifier"]

_BLOC = 1 << 20
_PAS_MAX = 1 << 20
"""Nombre maximal d'éléments parcourus dans une structure ; au-delà, la fin n'est pas connue."""

_ZONE_PDF = 1024
"""Les lecteurs PDF acceptent l'en-tête dans les 1024 premiers octets."""


@dataclass(frozen=True, slots=True)
class _Reconnu:
    format: str
    longueur: int | None
    """Du début du format à sa fin logique ; ``None`` si elle n'est pas connue."""
    tronque: bool = False
    """Structure interrompue avant sa fin : fichier tronqué ou corrompu."""


class _Tronque(Exception):
    """Levée par un parcours de structure qui s'interrompt avant la fin logique du format.

    Un parcours qui renvoie ``None`` n'a pas pu établir la fin sans que la structure soit
    fautive : taille déclarée inconnue, trop d'éléments à parcourir.
    """


def _mesurer(nature: str, fin: Callable[[], int | None]) -> _Reconnu:
    try:
        return _Reconnu(nature, fin())
    except _Tronque:
        return _Reconnu(nature, None, tronque=True)


class _Vue:
    """Portion du fichier à partir de ``debut``, lue par blocs mis en cache."""

    __slots__ = ("_cache", "_depart", "_fichier", "debut", "taille")

    def __init__(self, fichier: Fichier, debut: int, taille: int) -> None:
        self._fichier = fichier
        self.debut = debut
        self.taille = taille
        self._cache = b""
        self._depart = 0

    def octets(self, position: int, nombre: int) -> bytes:
        """Au plus ``nombre`` octets à partir de ``position`` ; moins en fin de vue."""
        if position < 0 or position >= self.taille or nombre <= 0:
            return b""
        nombre = min(nombre, self.taille - position, TAILLE_MAX_LECTURE)
        if nombre > _BLOC:
            return self._fichier.lire(self.debut + position, nombre)
        fin_cache = self._depart + len(self._cache)
        if not (self._depart <= position and position + nombre <= fin_cache):
            self._cache = self._fichier.lire(
                self.debut + position, min(_BLOC, self.taille - position)
            )
            self._depart = position
        relatif = position - self._depart
        return self._cache[relatif : relatif + nombre]


def _gros(octets: bytes) -> int:
    return int.from_bytes(octets, "big")


def _petit(octets: bytes) -> int:
    return int.from_bytes(octets, "little")


# Images


def _fin_jpeg(vue: _Vue) -> int | None:
    """Parcourt les segments jusqu'à EOI ; les données entropiques sont sautées (T.81, B.1)."""
    position = 2
    for _ in range(_PAS_MAX):
        tete = vue.octets(position, 4)
        if len(tete) < 2 or tete[0] != 0xFF:
            raise _Tronque
        marqueur = tete[1]
        if marqueur == 0xFF:  # octet de remplissage
            position += 1
        elif marqueur == 0xD9:  # EOI
            return position + 2
        elif marqueur == 0x01 or 0xD0 <= marqueur <= 0xD7:  # sans longueur
            position += 2
        elif marqueur in (0x00, 0xD8) or len(tete) < 4 or _gros(tete[2:4]) < 2:
            raise _Tronque
        else:
            position += 2 + _gros(tete[2:4])
            if marqueur == 0xDA:  # SOS : données entropiques jusqu'au marqueur suivant
                position = _apres_entropie(vue, position)
    return None


def _apres_entropie(vue: _Vue, position: int) -> int:
    """Position du premier marqueur après des données entropiques (``FF 00`` et RST sautés)."""
    while True:
        bloc = vue.octets(position, _BLOC)
        indice = bloc.find(b"\xff")
        while indice != -1 and indice + 1 < len(bloc):
            suivant = bloc[indice + 1]
            if suivant != 0x00 and not 0xD0 <= suivant <= 0xD7:
                return position + indice
            indice = bloc.find(b"\xff", indice + 2)
        if len(bloc) < 2:
            raise _Tronque
        # Bloc épuisé, ou FF en dernier octet : on reprend à partir de lui.
        position += len(bloc) if indice == -1 else indice


def _fin_png(vue: _Vue) -> int | None:
    """Parcourt les blocs jusqu'à IEND (PNG, §5.3)."""
    position = 8
    for _ in range(_PAS_MAX):
        tete = vue.octets(position, 8)
        if len(tete) < 8 or _gros(tete[:4]) > 0x7FFFFFFF:
            raise _Tronque
        position += 12 + _gros(tete[:4])
        if position > vue.taille:
            raise _Tronque
        if tete[4:8] == b"IEND":
            return position
    return None


def _bmp(vue: _Vue, tete: bytes) -> _Reconnu | None:
    if len(tete) < 18 or tete[6:10] != b"\x00" * 4:
        return None
    if _petit(tete[14:18]) not in {12, 40, 52, 56, 64, 108, 124}:
        return None
    taille = _petit(tete[2:6])
    return _Reconnu("bmp", taille if 18 <= taille <= vue.taille else None)


# Conteneurs RIFF, ISO BMFF, EBML, Ogg


def _riff(vue: _Vue, tete: bytes) -> _Reconnu | None:
    nature = {b"WAVE": "wav", b"WEBP": "webp", b"AVI ": "avi"}.get(tete[8:12])
    if nature is None:
        return None
    contenu = _petit(tete[4:8])
    # Un contenu de longueur impaire est suivi d'un octet de bourrage, parfois absent.
    for fin in (8 + contenu + contenu % 2, 8 + contenu):
        if 12 <= fin <= vue.taille:
            return _Reconnu(nature, fin)
    return _Reconnu(nature, None, tronque=True)


_MARQUES_HEIC = frozenset({b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx"})
_MARQUES_AVIF = frozenset({b"avif", b"avis"})
_MARQUES_MP4 = frozenset(
    {b"isom", b"iso2", b"iso3", b"iso4", b"iso5", b"iso6", b"iso8", b"iso9", b"mp41", b"mp42"}
    | {b"avc1", b"dash", b"M4V ", b"mmp4", b"msnv", b"f4v "}
)


def _classer_marques(majeure: bytes, marques: frozenset[bytes]) -> str | None:
    """Format désigné par les marques de la boîte ``ftyp`` (ISO/IEC 14496-12, §4.3)."""
    if majeure in _MARQUES_HEIC:
        return "heic"
    if majeure in _MARQUES_AVIF:
        return "avif"
    if majeure in {b"mif1", b"msf1"}:
        if marques & _MARQUES_HEIC:
            return "heic"
        return "avif" if marques & _MARQUES_AVIF else "heif"
    if majeure in {b"M4A ", b"M4B ", b"M4P "}:
        return "m4a"
    if majeure == b"qt  ":
        return "mov"
    if majeure.startswith(b"3g"):
        return "3gp"
    if majeure in _MARQUES_MP4 or marques & _MARQUES_MP4:
        return "mp4"
    return None


def _isobmff(vue: _Vue, tete: bytes) -> _Reconnu | None:
    taille_ftyp = _gros(tete[:4])
    if not 16 <= taille_ftyp <= 4096:
        return None
    ftyp = vue.octets(8, taille_ftyp - 8)
    if len(ftyp) < taille_ftyp - 8:
        return None
    marques = frozenset(ftyp[i : i + 4] for i in range(8, len(ftyp) - 3, 4)) | {ftyp[:4]}
    nature = _classer_marques(ftyp[:4], marques)
    return None if nature is None else _mesurer(nature, lambda: _fin_boites(vue))


def _fin_boites(vue: _Vue) -> int | None:
    """Parcourt les boîtes de premier niveau ; un type non imprimable clôt la structure."""
    position = 0
    for _ in range(_PAS_MAX):
        if position == vue.taille:
            return position
        tete = vue.octets(position, 16)
        if len(tete) < 8:
            raise _Tronque
        if not all(0x20 <= octet <= 0x7E for octet in tete[4:8]):
            return position or None
        taille = _gros(tete[:4])
        if taille == 0:  # jusqu'à la fin du fichier
            return vue.taille
        if taille == 1:
            if len(tete) < 16:
                raise _Tronque
            taille = _gros(tete[8:16])
        if taille < 8 or position + taille > vue.taille:
            raise _Tronque
        position += taille
    return None


def _vint(octets: bytes, position: int) -> tuple[int, int] | None:
    """Entier de taille variable EBML (RFC 8794, §4) : valeur et longueur ; ``-1`` si inconnue."""
    if position >= len(octets) or octets[position] == 0:
        return None
    longueur = 9 - octets[position].bit_length()
    brut = octets[position : position + longueur]
    if len(brut) < longueur:
        return None
    valeur = _gros(brut) & ((1 << (7 * longueur)) - 1)
    return (-1 if valeur == (1 << (7 * longueur)) - 1 else valeur), longueur


def _identifiant_ebml(octets: bytes, position: int) -> tuple[bytes, int] | None:
    if position >= len(octets) or octets[position] < 0x10:
        return None
    longueur = 9 - octets[position].bit_length()
    brut = octets[position : position + longueur]
    return (brut, longueur) if len(brut) == longueur else None


def _ebml(vue: _Vue) -> _Reconnu | None:
    """En-tête EBML, type de document, puis segment (RFC 8794, RFC 9559)."""
    entete = vue.octets(0, 4096)
    taille = _vint(entete, 4)
    if taille is None or taille[0] < 0:
        return None
    position, fin_entete = 4 + taille[1], 4 + taille[1] + taille[0]
    nature = None
    while position < min(fin_entete, len(entete)):
        element = _identifiant_ebml(entete, position)
        if element is None:
            return None
        valeur = _vint(entete, position + element[1])
        if valeur is None or valeur[0] < 0:
            return None
        debut_donnees = position + element[1] + valeur[1]
        if element[0] == b"\x42\x82":  # DocType
            type_document = entete[debut_donnees : debut_donnees + valeur[0]].rstrip(b"\x00")
            nature = {b"webm": "webm", b"matroska": "matroska"}.get(type_document)
        position = debut_donnees + valeur[0]
    if nature is None:
        return None
    segment = vue.octets(fin_entete, 12)
    taille_segment = _vint(segment, 4) if segment[:4] == b"\x18\x53\x80\x67" else None
    if taille_segment is not None and taille_segment[0] < 0:
        return _Reconnu(nature, None)  # segment de taille inconnue, permis pour un direct
    fin = None if taille_segment is None else fin_entete + 4 + taille_segment[1] + taille_segment[0]
    if fin is None or fin > vue.taille:
        return _Reconnu(nature, None, tronque=True)
    return _Reconnu(nature, fin)


def _fin_ogg(vue: _Vue) -> int | None:
    """Parcourt les pages (RFC 3533, §6) ; la structure finit à la première qui manque."""
    position = 0
    for _ in range(_PAS_MAX):
        tete = vue.octets(position, 27)
        if tete[:5] != b"OggS\x00":
            return position or None
        if len(tete) < 27:
            raise _Tronque
        segments = vue.octets(position + 27, tete[26])
        if len(segments) < tete[26]:
            raise _Tronque
        position += 27 + tete[26] + sum(segments)
        if position > vue.taille:
            raise _Tronque
        if position == vue.taille:
            return position
    return None


# Audio en trames


_DEBITS_V1 = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
_DEBITS_V2 = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
_FREQUENCES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}


def _trame_mp3(tete: bytes) -> int | None:
    """Longueur d'une trame MPEG audio couche III (ISO/IEC 11172-3, 13818-3), ou ``None``."""
    if len(tete) < 4 or tete[0] != 0xFF or tete[1] & 0xE0 != 0xE0:
        return None
    version, couche = (tete[1] >> 3) & 3, (tete[1] >> 1) & 3
    indice_debit, indice_frequence = tete[2] >> 4, (tete[2] >> 2) & 3
    if version == 1 or couche != 1 or indice_debit in (0, 15) or indice_frequence == 3:
        return None
    debit = (_DEBITS_V1 if version == 3 else _DEBITS_V2)[indice_debit] * 1000
    frequence = _FREQUENCES[version][indice_frequence]
    return (144 if version == 3 else 72) * debit // frequence + ((tete[2] >> 1) & 1)


def _trame_adts(tete: bytes) -> int | None:
    """Longueur d'une trame AAC ADTS (ISO/IEC 13818-7, §6.2), ou ``None``."""
    if len(tete) < 7 or tete[0] != 0xFF or tete[1] & 0xF6 != 0xF0 or (tete[2] >> 2) & 0xF >= 13:
        return None
    longueur = ((tete[3] & 3) << 11) | (tete[4] << 3) | (tete[5] >> 5)
    return longueur if longueur >= 7 else None


def _trames(
    vue: _Vue, position: int, trame: Callable[[bytes], int | None]
) -> tuple[int, int | None, bool]:
    """Trames consécutives depuis ``position`` : nombre, fin de la dernière, coupure finale."""
    nombre = 0
    for _ in range(_PAS_MAX):
        if position >= vue.taille:
            break
        longueur = trame(vue.octets(position, 7))
        if longueur is None:
            break
        if position + longueur > vue.taille:
            return nombre, None, True  # dernière trame coupée
        position += longueur
        nombre += 1
    else:
        return nombre, None, False
    return nombre, position, False


def _audio(vue: _Vue, position: int) -> _Reconnu | None:
    """MP3 ou AAC en trames, éventuellement après une balise ID3v2 ; au moins deux trames."""
    for nature, trame in (("mp3", _trame_mp3), ("aac", _trame_adts)):
        nombre, fin, coupee = _trames(vue, position, trame)
        if nombre >= 2 or (nombre == 1 and fin == vue.taille):
            if fin is not None and nature == "mp3" and vue.octets(fin, 3) == b"TAG":
                fin += 128  # balise ID3v1, en fin de fichier
                coupee = fin > vue.taille
            return _Reconnu(nature, None if coupee else fin, coupee)
    return None


def _id3(vue: _Vue, tete: bytes) -> _Reconnu | None:
    """Balise ID3v2 (id3.org, v2.4, §3.1), suivie d'une trame MP3, AAC ou d'un FLAC."""
    if len(tete) < 10 or tete[3] not in (2, 3, 4) or any(octet & 0x80 for octet in tete[6:10]):
        return None
    taille = 10 + sum(octet << (7 * (3 - i)) for i, octet in enumerate(tete[6:10]))
    taille += 10 if tete[5] & 0x10 else 0  # pied de balise
    if vue.octets(taille, 4) == b"fLaC":
        return _Reconnu("flac", None)
    return _audio(vue, taille)


# Documents


def _fin_pdf(vue: _Vue) -> int:
    """Après le dernier ``%%EOF`` et les blancs qui le suivent (ISO 32000-2, §7.5.5)."""
    fin = vue.taille
    while fin > 0:
        debut = max(0, fin - _BLOC)
        bloc = vue.octets(debut, fin - debut + 4)
        indice = bloc.rfind(b"%%EOF")
        if indice != -1:
            position = debut + indice + 5
            while vue.octets(position, 1) in {b"\x00", b"\t", b"\n", b"\x0c", b"\r", b" "}:
                position += 1
            return position
        fin = debut
    raise _Tronque


def _pdf(vue: _Vue, tete: bytes) -> _Reconnu | None:
    if not (tete.startswith(b"%PDF-") and tete[5:6].isdigit()):
        return None
    return _mesurer("pdf", lambda: _fin_pdf(vue))


# Formats reconnus seulement pour être nommés


def _exe(vue: _Vue, tete: bytes) -> _Reconnu | None:
    if len(tete) < 0x40:
        return None
    entete_pe = _petit(tete[0x3C:0x40])
    return _Reconnu("exe", None) if vue.octets(entete_pe, 4) == b"PE\x00\x00" else None


_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"II*\x00", "tiff"),
    (b"MM\x00*", "tiff"),
    (b"II+\x00", "tiff"),
    (b"\x1f\x8b\x08", "gzip"),
    (b"7z\xbc\xaf\x27\x1c", "7z"),
    (b"Rar!\x1a\x07", "rar"),
    (b"\x7fELF", "elf"),
)


def _reconnaitre(vue: _Vue) -> _Reconnu | None:
    """Format qui commence au début de la vue, du plus au moins spécifique."""
    tete = vue.octets(0, 64)
    if tete.startswith(b"\xff\xd8\xff"):
        return _mesurer("jpeg", lambda: _fin_jpeg(vue))
    if tete.startswith(b"\x89PNG\r\n\x1a\n"):
        return _mesurer("png", lambda: _fin_png(vue))
    if tete.startswith(b"%PDF-"):
        return _pdf(vue, tete)
    if tete.startswith(b"RIFF") and len(tete) >= 12:
        return _riff(vue, tete)
    if tete[4:8] == b"ftyp":
        return _isobmff(vue, tete)
    if tete[4:8] in {b"moov", b"mdat", b"wide"}:  # QuickTime sans boîte ftyp
        return _mesurer("mov", lambda: _fin_boites(vue))
    if tete.startswith(b"\x1a\x45\xdf\xa3"):
        return _ebml(vue)
    if tete.startswith(b"OggS\x00"):
        return _mesurer("ogg", lambda: _fin_ogg(vue))
    if tete.startswith(b"fLaC") and len(tete) >= 8 and tete[4] & 0x7F == 0:  # STREAMINFO
        return _Reconnu("flac", None)
    if tete.startswith(b"ID3"):
        return _id3(vue, tete)
    if tete.startswith(b"BM"):
        return _bmp(vue, tete)
    if tete.startswith(b"MZ"):
        return _exe(vue, tete)
    for signature, nature in _SIGNATURES:
        if tete.startswith(signature):
            return _Reconnu(nature, None)
    return _audio(vue, 0) if tete.startswith(b"\xff") else None


# ZIP, lu depuis sa fin


@dataclass(frozen=True, slots=True)
class _Archive:
    format: str
    debut: int
    fin: int


_MIME_ODT = b"application/vnd.oasis.opendocument.text"


def _zip(fichier: Fichier, taille: int) -> _Archive | None:
    """Archive ZIP lue comme le font les lecteurs : depuis l'enregistrement de fin (APPNOTE, §4.3).

    Le début est celui de la première entrée locale, ce qui situe aussi une archive placée
    après un autre format, que ses positions soient relatives à elle ou au fichier.
    """
    depart = max(0, taille - (22 + 0xFFFF + 76))
    queue = fichier.lire(depart, taille - depart)
    indice = queue.rfind(b"PK\x05\x06")
    while indice != -1 and indice + 22 + _petit(queue[indice + 20 : indice + 22]) > len(queue):
        indice = queue.rfind(b"PK\x05\x06", 0, indice)
    if indice == -1:
        return None
    fin_archive = depart + indice + 22 + _petit(queue[indice + 20 : indice + 22])
    entrees, taille_repertoire, decalage_repertoire = (
        _petit(queue[indice + 10 : indice + 12]),
        _petit(queue[indice + 12 : indice + 16]),
        _petit(queue[indice + 16 : indice + 20]),
    )
    fin_repertoire = depart + indice
    if 0xFFFFFFFF in (taille_repertoire, decalage_repertoire) or entrees == 0xFFFF:
        zip64 = depart + indice - 20 - 56  # enregistrement ZIP64, juste avant son localisateur
        enregistrement = fichier.lire(zip64, 56) if zip64 >= 0 else b""
        if enregistrement[:4] != b"PK\x06\x06":
            return None
        entrees = _petit(enregistrement[32:40])
        taille_repertoire = _petit(enregistrement[40:48])
        decalage_repertoire = _petit(enregistrement[48:56])
        fin_repertoire = zip64
    position_repertoire = fin_repertoire - taille_repertoire
    decalage = position_repertoire - decalage_repertoire
    if position_repertoire < 0 or decalage < 0:
        return None
    if entrees == 0:
        return _Archive("zip", position_repertoire, fin_archive)
    repertoire = fichier.lire(position_repertoire, min(taille_repertoire, TAILLE_MAX_LECTURE))
    if repertoire[:4] != b"PK\x01\x02" or len(repertoire) < 46:
        return None
    debut = decalage + _petit(repertoire[42:46])
    if debut >= fin_archive or fichier.lire(debut, 4) != b"PK\x03\x04":
        return None
    return _Archive(_classer_zip(fichier, debut, repertoire), debut, fin_archive)


def _noms(repertoire: bytes) -> set[bytes]:
    noms: set[bytes] = set()
    position = 0
    # Chaque entrée fait au moins 46 octets : la boucle avance toujours.
    while position + 46 <= len(repertoire) and repertoire[position : position + 4] == b"PK\x01\x02":
        longueurs = [_petit(repertoire[position + i : position + i + 2]) for i in (28, 30, 32)]
        noms.add(repertoire[position + 46 : position + 46 + longueurs[0]])
        position += 46 + sum(longueurs)
    return noms


def _classer_zip(fichier: Fichier, debut: int, repertoire: bytes) -> str:
    """DOCX par ses parties obligatoires (ECMA-376), ODT par son entrée ``mimetype`` (ODF, §3.3)."""
    locale = fichier.lire(debut, 30 + 8)
    if (
        locale[26:28] == b"\x08\x00"
        and locale[30:38] == b"mimetype"
        and locale[8:10] == b"\x00\x00"
    ):
        taille = _petit(locale[18:22])
        contenu = fichier.lire(debut + 38 + _petit(locale[28:30]), len(_MIME_ODT))
        if taille == len(_MIME_ODT) and contenu == _MIME_ODT:
            return "odt"
    if {b"[Content_Types].xml", b"word/document.xml"} <= _noms(repertoire):
        return "docx"
    return "zip"


# Texte brut


_CONTROLES = re.compile(rb"[\x00-\x08\x0b\x0e-\x1f\x7f]")
_CONTROLES_TEXTE = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")


def _texte(fichier: Fichier, taille: int) -> bool:
    """UTF-8, avec ou sans marque d'ordre, ou UTF-16 avec marque ; aucun caractère de contrôle
    autre que tabulation, sauts de ligne et de page."""
    debut = fichier.lire(0, 2)
    utf16 = debut in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)
    decodeur = codecs.getincrementaldecoder("utf-16" if utf16 else "utf-8-sig")("strict")
    position = 0
    try:
        while position < taille:
            bloc = fichier.lire(position, _BLOC)
            if not bloc:
                break
            position += len(bloc)
            if not utf16 and _CONTROLES.search(bloc):
                return False
            if _CONTROLES_TEXTE.search(decodeur.decode(bloc, final=position >= taille)):
                return False
        decodeur.decode(b"", final=True)
    except UnicodeDecodeError:
        return False
    return position > 0


# Assemblage


def identifier(fichier: Fichier, taille: int) -> tuple[Partie, ...]:
    """Parties reconnues dans le fichier, dans l'ordre de leurs débuts ; vide si aucune."""
    garde.exiger()
    trouvees: dict[int, _Reconnu] = {}
    archive = _zip(fichier, taille)

    position = 0
    while position < taille and len(trouvees) < NOMBRE_MAX_PARTIES:
        if archive is not None and archive.debut == position:
            reconnu: _Reconnu | None = _Reconnu(archive.format, archive.fin - archive.debut)
        else:
            reconnu = _reconnaitre(_Vue(fichier, position, taille - position))
        if reconnu is None:
            break
        trouvees[position] = reconnu
        if reconnu.longueur is None:
            break
        position += reconnu.longueur

    tete = fichier.lire(0, _ZONE_PDF + 8)
    # Seul le premier en-tête compte pour un lecteur ; en tête du fichier, la chaîne l'a vu.
    en_tete_pdf = tete.find(b"%PDF-", 0, _ZONE_PDF + 5)
    if en_tete_pdf > 0 and en_tete_pdf not in trouvees:
        reconnu = _pdf(_Vue(fichier, en_tete_pdf, taille - en_tete_pdf), tete[en_tete_pdf:])
        if reconnu is not None:
            trouvees[en_tete_pdf] = reconnu
    if archive is not None and archive.debut not in trouvees:
        trouvees[archive.debut] = _Reconnu(archive.format, archive.fin - archive.debut)
    if not trouvees and _texte(fichier, taille):
        trouvees[0] = _Reconnu("texte", taille)

    parties = []
    for rang, debut in enumerate(sorted(trouvees)[:NOMBRE_MAX_PARTIES], start=1):
        reconnu = trouvees[debut]
        longueur = taille - debut if reconnu.longueur is None else reconnu.longueur
        parties.append(
            Partie(
                rang,
                reconnu.format,
                Plage(debut, longueur),
                fin_connue=reconnu.longueur is not None,
                tronquee=reconnu.tronque,
            )
        )
    return tuple(parties)
