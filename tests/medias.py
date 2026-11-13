"""Balises de fichiers audio et vidéo, construites octet par octet pour les tests (T21).

Chaque constructeur suit la structure que lisent les modules : balises ID3, blocs RIFF d'un WAV,
blocs de métadonnées d'un FLAC, pages et paquets Ogg, boîtes ISOBMFF de ``moov``, éléments EBML
d'un WebM. Aucun échantillon n'est décodable comme son ou comme image : les données sont
absentes ou factices, seules les trames MP3 et AAC sont bien formées, pour l'identification.
"""

import struct

from echantillons import TRAME_MP3, boite, ftyp

# ID3 (id3.org)


def syncsafe(valeur: int) -> bytes:
    return bytes((valeur >> shift) & 0x7F for shift in (21, 14, 7, 0))


def trame_id3(identifiant: bytes, donnees: bytes, *, version: int = 4, format_: int = 0) -> bytes:
    """Trame : en-tête de six octets en v2.2, de dix sinon (taille synchrosûre en v2.4)."""
    if version == 2:
        return identifiant + len(donnees).to_bytes(3, "big") + donnees
    taille = syncsafe(len(donnees)) if version == 4 else len(donnees).to_bytes(4, "big")
    return identifiant + taille + bytes([0, format_]) + donnees


def texte_id3(identifiant: bytes, *textes: str, encodage: int = 3, version: int = 4) -> bytes:
    codec = {0: "latin-1", 1: "utf-16", 2: "utf-16-be", 3: "utf-8"}[encodage]
    nul = b"\x00\x00" if encodage in (1, 2) else b"\x00"
    corps = nul.join(t.encode(codec) for t in textes)
    return trame_id3(identifiant, bytes([encodage]) + corps, version=version)


def id3v2(*trames: bytes, version: int = 4, drapeaux: int = 0, bourrage: int = 0) -> bytes:
    corps = b"".join(trames) + b"\x00" * bourrage
    entete = b"ID3" + bytes([version, 0, drapeaux]) + syncsafe(len(corps))
    pied = b"3DI" + bytes([version, 0, drapeaux]) + syncsafe(len(corps)) if drapeaux & 0x10 else b""
    return entete + corps + pied


def id3v1(
    titre: bytes = b"",
    artiste: bytes = b"",
    album: bytes = b"",
    annee: bytes = b"",
    commentaire: bytes = b"",
    piste: int | None = None,
    genre: int = 255,
) -> bytes:
    def champ(octets: bytes, taille: int) -> bytes:
        return octets[:taille].ljust(taille, b"\x00")

    if piste is None:
        fin = champ(commentaire, 30)
    else:
        fin = champ(commentaire, 28) + b"\x00" + bytes([piste])
    return (
        b"TAG"
        + champ(titre, 30)
        + champ(artiste, 30)
        + champ(album, 30)
        + champ(annee, 4)
        + fin
        + bytes([genre])
    )


def mp3(*balises: bytes, v1: bytes = b"") -> bytes:
    """Balises ID3v2, deux trames MPEG-1 couche III, balise ID3v1 éventuelle."""
    return b"".join(balises) + TRAME_MP3 * 2 + v1


# WAV (RIFF ; EBU Tech 3285)

_FMT = b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 16000, 2, 16)


def bloc_wav(nature: bytes, donnees: bytes) -> bytes:
    return nature + struct.pack("<I", len(donnees)) + donnees + b"\x00" * (len(donnees) & 1)


def wav(*blocs: bytes, donnees: bytes = b"\x00\x00\x00\x00") -> bytes:
    contenu = b"WAVE" + _FMT + b"".join(blocs) + bloc_wav(b"data", donnees)
    return b"RIFF" + struct.pack("<I", len(contenu)) + contenu


def liste_info(*entrees: tuple[bytes, bytes]) -> bytes:
    corps = b"".join(bloc_wav(identifiant, texte + b"\x00") for identifiant, texte in entrees)
    return bloc_wav(b"LIST", b"INFO" + corps)


def bext(
    *,
    description: bytes = b"",
    originator: bytes = b"",
    reference: bytes = b"",
    date: bytes = b"",
    heure: bytes = b"",
    temps: int = 0,
    version: int = 1,
    umid: bytes = b"",
    historique: bytes = b"",
) -> bytes:
    corps = (
        description.ljust(256, b"\x00")
        + originator.ljust(32, b"\x00")
        + reference.ljust(32, b"\x00")
        + date.ljust(10, b"\x00")
        + heure.ljust(8, b"\x00")
        + struct.pack("<QH", temps, version)
        + umid.ljust(64, b"\x00")
        + b"\x00" * 190
        + historique
    )
    return bloc_wav(b"bext", corps)


# Commentaires Vorbis (Vorbis I, §5) ; FLAC (RFC 9639) ; Ogg (RFC 3533)


def commentaires(fournisseur: bytes, *champs: bytes) -> bytes:
    corps = struct.pack("<I", len(fournisseur)) + fournisseur + struct.pack("<I", len(champs))
    return corps + b"".join(struct.pack("<I", len(champ)) + champ for champ in champs)


def bloc_flac(nature: int, donnees: bytes, *, dernier: bool = False) -> bytes:
    return bytes([nature | (0x80 if dernier else 0)]) + len(donnees).to_bytes(3, "big") + donnees


STREAMINFO = (
    bytes.fromhex("10001000") + b"\x00" * 6 + bytes.fromhex("01f400f000000000") + b"\x00" * 16
)
"""Bloc STREAMINFO de 34 octets : 8 kHz, mono, 16 bits."""


def flac(*blocs: bytes, avant: bytes = b"", trames: bytes = b"\xff\xf8\x00\x00") -> bytes:
    """En-tête, STREAMINFO, blocs donnés (le dernier marqué comme tel), trames factices."""
    tous = [bloc_flac(0, STREAMINFO), *blocs]
    tous[-1] = bytes([tous[-1][0] | 0x80]) + tous[-1][1:]
    return avant + b"fLaC" + b"".join(tous) + trames


def _crc_ogg(octets: bytes) -> int:
    """CRC-32 d'Ogg : polynôme 0x04C11DB7, sans réflexion ni inversion (RFC 3533, §6)."""
    crc = 0
    for octet in octets:
        crc ^= octet << 24
        for _ in range(8):
            crc = ((crc << 1) ^ 0x04C11DB7) if crc & 0x80000000 else crc << 1
            crc &= 0xFFFFFFFF
    return crc


def page_ogg(
    numero: int, sequence: int, segments: list[int], donnees: bytes, *, type_: int = 0
) -> bytes:
    entete = struct.pack("<4sBBqIIIB", b"OggS", 0, type_, 0, numero, sequence, 0, len(segments))
    page = entete + bytes(segments) + donnees
    return page[:22] + struct.pack("<I", _crc_ogg(page)) + page[26:]


def ogg(*flux: tuple[int, list[bytes]], par_page: int = 255 * 255) -> bytes:
    """Pages des flux, entrelacées paquet par paquet : un paquet commence une page, et s'étend
    sur plusieurs si plus long que ``par_page`` octets (multiple de 255)."""
    pages: list[bytes] = []
    sequences = dict.fromkeys((numero for numero, _ in flux), 0)
    rang = 0
    while any(rang < len(paquets) for _, paquets in flux):
        for numero, paquets in flux:
            if rang >= len(paquets):
                continue
            paquet = paquets[rang]
            morceaux = [paquet[i : i + par_page] for i in range(0, len(paquet), par_page)] or [b""]
            for indice, morceau in enumerate(morceaux):
                segments = [255] * (len(morceau) // 255)
                if indice == len(morceaux) - 1:
                    segments.append(len(morceau) % 255)
                type_ = (2 if rang == 0 and indice == 0 else 0) | (1 if indice else 0)
                pages.append(page_ogg(numero, sequences[numero], segments, morceau, type_=type_))
                sequences[numero] += 1
        rang += 1
    return b"".join(pages)


# ISOBMFF : M4A, MP4, MOV (ISO/CEI 14496-12 ; QuickTime File Format)


def boite_pleine(nature: bytes, contenu: bytes, version: int = 0) -> bytes:
    return boite(nature, bytes([version, 0, 0, 0]) + contenu)


def mvhd(creation: int, modification: int, *, version: int = 0) -> bytes:
    format_ = ">QQ" if version else ">II"
    return boite_pleine(
        b"mvhd", struct.pack(format_, creation, modification) + b"\x00" * 80, version
    )


def texte_qt(code: bytes, *textes: bytes, langue: int = 0x55C4) -> bytes:
    """Boîte ``©xxx`` de ``udta`` : longueur, langue, texte, pour chaque texte."""
    return boite(code, b"".join(struct.pack(">HH", len(t), langue) + t for t in textes))


def donnee(type_: int, valeur: bytes) -> bytes:
    return boite(b"data", struct.pack(">II", type_, 0) + valeur)


def element_ilst(code: bytes, *donnees: bytes) -> bytes:
    return boite(code, b"".join(donnees))


def libre(domaine: bytes, nom: bytes, *donnees: bytes) -> bytes:
    corps = boite_pleine(b"mean", domaine) + boite_pleine(b"name", nom) + b"".join(donnees)
    return boite(b"----", corps)


def hdlr(gestionnaire: bytes) -> bytes:
    return boite_pleine(b"hdlr", b"\x00" * 4 + gestionnaire + b"\x00" * 13)


def meta_itunes(*elements: bytes) -> bytes:
    """``meta`` de ``udta`` : boîte pleine, gestionnaire ``mdir``, ``ilst``."""
    return boite_pleine(b"meta", hdlr(b"mdir") + boite(b"ilst", b"".join(elements)))


def meta_mdta(cles: list[bytes], *elements: tuple[int, bytes]) -> bytes:
    """``meta`` de ``moov`` (QuickTime) : sans version ; ``hdlr`` ``mdta``, ``keys``, ``ilst``."""
    corps = struct.pack(">I", len(cles)) + b"".join(boite(b"mdta", cle) for cle in cles)
    ilst = b"".join(struct.pack(">I", 8 + len(d)) + struct.pack(">I", i) + d for i, d in elements)
    return boite(b"meta", hdlr(b"mdta") + boite_pleine(b"keys", corps) + boite(b"ilst", ilst))


def quicktime(*enfants: bytes, majeure: bytes = b"M4A ", apres: bytes = b"") -> bytes:
    """``ftyp``, ``moov`` (``mvhd`` d'abord s'il n'est pas donné), ``mdat``, puis ``apres``."""
    moov = b"".join(enfants)
    if b"mvhd" not in moov[:8]:
        moov = mvhd(0, 0) + moov
    entete = ftyp(majeure, b"isom") if majeure != b"qt  " else ftyp(b"qt  ")
    return entete + boite(b"moov", moov) + boite(b"mdat", b"\x00" * 8) + apres


# EBML : WebM (RFC 8794 ; RFC 9559)


def taille_ebml(taille: int) -> bytes:
    for longueur in range(1, 9):
        if taille < (1 << (7 * longueur)) - 1:
            return (taille | (1 << (7 * longueur))).to_bytes(longueur, "big")
    raise ValueError(taille)


def element(identifiant: int, contenu: bytes) -> bytes:
    octets = identifiant.to_bytes((identifiant.bit_length() + 7) // 8, "big")
    return octets + taille_ebml(len(contenu)) + contenu


def texte_ebml(identifiant: int, texte: str) -> bytes:
    return element(identifiant, texte.encode())


INCONNUE = b"\x01\xff\xff\xff\xff\xff\xff\xff"
"""Taille inconnue sur huit octets."""


def webm(*enfants: bytes, segment_inconnu: bool = False) -> bytes:
    entete = element(
        0x1A45DFA3, element(0x4286, b"\x01") + element(0x4282, b"webm") + element(0x4287, b"\x04")
    )
    corps = b"".join(enfants)
    if segment_inconnu:
        return entete + b"\x18\x53\x80\x67" + INCONNUE + corps
    return entete + element(0x18538067, corps)


def info(*elements: bytes) -> bytes:
    return element(0x1549A966, b"".join(elements))


def simple(nom: str, texte: str | None = None, *imbriquees: bytes, binaire: bytes = b"") -> bytes:
    corps = texte_ebml(0x45A3, nom)
    if texte is not None:
        corps += texte_ebml(0x4487, texte)
    if binaire:
        corps += element(0x4485, binaire)
    return element(0x67C8, corps + b"".join(imbriquees))


def tag(*simples: bytes, cibles: bytes = b"") -> bytes:
    return element(0x7373, element(0x63C0, cibles) + b"".join(simples))


def tags(*elements: bytes) -> bytes:
    return element(0x1254C367, b"".join(elements))


def cluster(contenu: bytes = b"", *, inconnu: bool = False) -> bytes:
    bloc = element(0xE7, b"\x00") + element(0xA3, b"\x81\x00\x00\x80" + contenu)
    if inconnu:
        return b"\x1f\x43\xb6\x75" + INCONNUE + bloc
    return element(0x1F43B675, bloc)
