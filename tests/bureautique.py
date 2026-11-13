"""Documents DOCX et ODT construits pour les tests (T21, complément bureautique).

Deux écrivains d'archive : ``zipfile``, de la bibliothèque standard, indépendant du lecteur
testé, pour les archives bien formées ; :func:`archive_brute`, octet par octet, pour ce que
``zipfile`` n'écrit pas (ZIP64 forcé, en-tête local différent du répertoire central, entrées
en double, positions relatives au fichier). Les parties XML suivent ECMA-376 et OpenDocument ;
aucun document ne s'ouvre dans un traitement de texte : le corps est absent ou factice.
"""

import io
import struct
import zipfile
import zlib
from dataclasses import dataclass

CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
APP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
CUSTOM = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
TYPE_CORE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
TYPE_APP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"
TYPE_CUSTOM = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
)
TYPE_DOCUMENT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
XLINK = "http://www.w3.org/1999/xlink"
MIME_ODT = b"application/vnd.oasis.opendocument.text"


def zip_(*entrees: tuple[str, bytes], methode: int = zipfile.ZIP_DEFLATED) -> bytes:
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w", compression=methode) as fichier:
        for nom, contenu in entrees:
            fichier.writestr(nom, contenu)
    return flux.getvalue()


# DOCX


def relations(*liens: tuple[str, str] | tuple[str, str, str]) -> bytes:
    """``_rels/.rels`` : type, cible et, au besoin, mode de la cible."""
    elements = "".join(
        f'<Relationship Id="rId{rang}" Type="{lien[0]}" Target="{lien[1]}"'
        + (f' TargetMode="{lien[2]}"' if len(lien) == 3 else "")
        + "/>"
        for rang, lien in enumerate(liens, start=1)
    )
    return f'<Relationships xmlns="{RELATIONS}">{elements}</Relationships>'.encode()


def core(contenu: str) -> bytes:
    espaces = f'xmlns:cp="{CP}" xmlns:dc="{DC}" xmlns:dcterms="{DCTERMS}"'
    return f"<cp:coreProperties {espaces}>{contenu}</cp:coreProperties>".encode()


def app(contenu: str, espace: str = APP) -> bytes:
    return f'<Properties xmlns="{espace}" xmlns:vt="{VT}">{contenu}</Properties>'.encode()


def custom(*proprietes: tuple[str, str], espace: str = CUSTOM) -> bytes:
    """Propriétés personnalisées : nom et valeur typée (``<vt:lpwstr>…</vt:lpwstr>``)."""
    elements = "".join(
        f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{rang}" name="{nom}">'
        f"{valeur}</property>"
        for rang, (nom, valeur) in enumerate(proprietes, start=2)
    )
    return f'<Properties xmlns="{espace}" xmlns:vt="{VT}">{elements}</Properties>'.encode()


def docx_(
    core_: bytes | None = None,
    app_: bytes | None = None,
    custom_: bytes | None = None,
    *autres: tuple[str, bytes],
    liens: bytes | None = None,
) -> bytes:
    """DOCX : relations du paquet vers les parties données, rangées sous ``docProps/``."""
    parties = [
        (type_, f"docProps/{nom}.xml", contenu)
        for type_, nom, contenu in (
            (TYPE_CORE, "core", core_),
            (TYPE_APP, "app", app_),
            (TYPE_CUSTOM, "custom", custom_),
        )
        if contenu is not None
    ]
    if liens is None:
        liens = relations(
            *((type_, chemin) for type_, chemin, _ in parties), (TYPE_DOCUMENT, "word/document.xml")
        )
    return zip_(
        ("[Content_Types].xml", b"<Types/>"),
        ("_rels/.rels", liens),
        *((chemin, contenu) for _, chemin, contenu in parties),
        ("word/document.xml", b"<w/>"),
        *autres,
    )


# ODT


def meta(contenu: str, *, version: str = "1.3", espaces: str = "") -> bytes:
    declarations = f'xmlns:office="{OFFICE}" xmlns:meta="{META}" xmlns:dc="{DC}" '
    declarations += f'xmlns:xlink="{XLINK}" {espaces}'
    return (
        f'<office:document-meta {declarations} office:version="{version}">'
        f"<office:meta>{contenu}</office:meta></office:document-meta>"
    ).encode()


def odt_(meta_: bytes | None, *autres: tuple[str, bytes]) -> bytes:
    """ODT : ``mimetype`` stocké en tête, puis ``meta.xml`` s'il est donné."""
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w", compression=zipfile.ZIP_DEFLATED) as fichier:
        fichier.writestr("mimetype", MIME_ODT, compress_type=zipfile.ZIP_STORED)
        if meta_ is not None:
            fichier.writestr("meta.xml", meta_)
        for nom, contenu in autres:
            fichier.writestr(nom, contenu)
    return flux.getvalue()


# Archive octet par octet (APPNOTE)


@dataclass(frozen=True)
class Brute:
    """Entrée d'une archive brute : nom, contenu, compression, drapeaux, nom de l'en-tête local."""

    nom: bytes
    contenu: bytes
    methode: int = 8
    drapeaux: int = 0
    nom_local: bytes | None = None
    donnees: bytes | None = None
    """Octets écrits à la place du contenu compressé, s'ils sont donnés."""


def archive_brute(
    *entrees: Brute,
    prefixe: bytes = b"",
    relatif_au_fichier: bool = False,
    zip64: bool = False,
    commentaire: bytes = b"",
) -> bytes:
    """Archive ZIP ; avec ``zip64``, enregistrement de fin ZIP64 et positions des entrées dans
    leur champ ZIP64."""
    tampon = bytearray(prefixe)
    origine = 0 if relatif_au_fichier else len(prefixe)
    centrale = bytearray()
    for entree in entrees:
        if entree.donnees is not None:
            donnees = entree.donnees
        elif entree.methode == 8:
            compresseur = zlib.compressobj(wbits=-15)
            donnees = compresseur.compress(entree.contenu) + compresseur.flush()
        else:
            donnees = entree.contenu
        crc = zlib.crc32(entree.contenu)
        locale = entree.nom if entree.nom_local is None else entree.nom_local
        position = len(tampon) - origine
        tampon += struct.pack(
            "<4sHHHHHIIIHH",
            b"PK\x03\x04",
            20,
            entree.drapeaux,
            entree.methode,
            0,
            0,
            crc,
            len(donnees),
            len(entree.contenu),
            len(locale),
            0,
        )
        tampon += locale + donnees
        tailles = (len(donnees), len(entree.contenu), position)
        supplement = b""
        if zip64:  # position seule dans le champ ZIP64, les tailles restant dans l'enregistrement
            supplement = struct.pack("<HHQ", 1, 8, tailles[2])
            tailles = (tailles[0], tailles[1], 0xFFFFFFFF)
        centrale += struct.pack(
            "<4sHHHHHHIIIHHHHHII",
            b"PK\x01\x02",
            20,
            20,
            entree.drapeaux,
            entree.methode,
            0,
            0,
            crc,
            tailles[0],
            tailles[1],
            len(entree.nom),
            len(supplement),
            0,
            0,
            0,
            0,
            tailles[2],
        )
        centrale += entree.nom + supplement
    debut_centrale = len(tampon) - origine
    tampon += centrale
    if zip64:
        position_zip64 = len(tampon) - origine
        tampon += struct.pack(
            "<4sQHHIIQQQQ",
            b"PK\x06\x06",
            44,
            45,
            45,
            0,
            0,
            len(entrees),
            len(entrees),
            len(centrale),
            debut_centrale,
        )
        tampon += struct.pack("<4sIQI", b"PK\x06\x07", 0, position_zip64, 1)
        fin = (0xFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
    else:
        fin = (len(entrees), len(entrees), len(centrale), debut_centrale)
    tampon += struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, *fin, len(commentaire))
    return bytes(tampon + commentaire)
