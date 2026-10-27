"""Échantillons minimaux de chaque format, construits octet par octet pour les tests (T13).

Aucun n'est décodable comme média : seules comptent les structures que l'identification
parcourt (signatures, segments, blocs, boîtes, pages, trames, répertoire ZIP).
"""

import io
import struct
import zipfile
import zlib


def segment(marqueur: int, donnees: bytes) -> bytes:
    return b"\xff" + bytes([marqueur]) + struct.pack(">H", len(donnees) + 2) + donnees


def jpeg(entropie: bytes = b"\x12\xff\x00\x34\xff\xd0\x56") -> bytes:
    """SOI, APP0, SOS, données entropiques, EOI."""
    return (
        b"\xff\xd8"
        + segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
        + segment(0xDA, b"\x01\x01\x00\x00\x3f\x00")
        + entropie
        + b"\xff\xd9"
    )


def bloc_png(nature: bytes, donnees: bytes) -> bytes:
    crc = struct.pack(">I", zlib.crc32(nature + donnees))
    return struct.pack(">I", len(donnees)) + nature + donnees + crc


def png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + bloc_png(b"IHDR", b"\x00" * 13) + bloc_png(b"IEND", b"")


PDF = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def riff(nature: bytes, contenu: bytes = b"data\x00\x00\x00\x00") -> bytes:
    return b"RIFF" + struct.pack("<I", 4 + len(contenu)) + nature + contenu


def boite(nature: bytes, contenu: bytes = b"") -> bytes:
    return struct.pack(">I", 8 + len(contenu)) + nature + contenu


def ftyp(majeure: bytes, *compatibles: bytes) -> bytes:
    return boite(b"ftyp", majeure + b"\x00\x00\x00\x00" + b"".join(compatibles))


def iso(majeure: bytes, *compatibles: bytes) -> bytes:
    return ftyp(majeure, *compatibles) + boite(b"mdat", b"\x00" * 4)


def ebml(
    type_document: bytes, segment_taille: bytes = b"\x84", contenu: bytes = b"\x00" * 4
) -> bytes:
    """En-tête EBML avec version et type de document, puis un segment."""
    elements = (
        b"\x42\x86\x81\x01" + b"\x42\x82" + bytes([0x80 | len(type_document)]) + type_document
    )
    entete = b"\x1a\x45\xdf\xa3" + bytes([0x80 | len(elements)]) + elements
    return entete + b"\x18\x53\x80\x67" + segment_taille + contenu


def page_ogg(contenu: bytes = b"abcde") -> bytes:
    return b"OggS\x00\x02" + b"\x00" * 20 + b"\x01" + bytes([len(contenu)]) + contenu


TRAME_MP3 = b"\xff\xfb\x90\x00" + b"\x00" * (417 - 4)
"""MPEG-1 couche III, 128 kbit/s, 44,1 kHz, sans bourrage : 417 octets."""


def trame_adts(longueur: int = 16) -> bytes:
    entete = bytes(
        [
            0xFF,
            0xF1,
            0x50,
            0x80 | (longueur >> 11),
            (longueur >> 3) & 0xFF,
            (longueur & 7) << 5,
            0xFC,
        ]
    )
    return entete + b"\x00" * (longueur - 7)


def id3(contenu: bytes, taille: int = 10, pied: bool = False) -> bytes:
    synchro = bytes(
        [(taille >> 21) & 0x7F, (taille >> 14) & 0x7F, (taille >> 7) & 0x7F, taille & 0x7F]
    )
    entete = b"ID3\x04\x00" + bytes([0x10 if pied else 0]) + synchro
    return entete + b"\x00" * taille + (b"3DI" + b"\x00" * 7 if pied else b"") + contenu


def archive(*entrees: tuple[str, bytes], commentaire: bytes = b"") -> bytes:
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w") as fichier:
        for nom, contenu in entrees:
            fichier.writestr(zipfile.ZipInfo(nom), contenu)
        fichier.comment = commentaire
    return flux.getvalue()


def docx() -> bytes:
    return archive(("[Content_Types].xml", b"<Types/>"), ("word/document.xml", b"<w/>"))


def odt() -> bytes:
    return archive(
        ("mimetype", b"application/vnd.oasis.opendocument.text"), ("content.xml", b"<o/>")
    )
