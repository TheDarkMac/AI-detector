"""Échantillons de métadonnées d'image, construits octet par octet pour les tests (T20).

Chaque constructeur suit la structure que lisent les modules : en-tête et répertoires TIFF,
segments JPEG, blocs PNG et WebP, boîtes HEIC, paquets XMP, ressources Photoshop et IIM. Aucun
échantillon n'est décodable comme image : les données d'image sont absentes ou factices.
"""

import importlib
import json
import struct
import tempfile
import zlib
from dataclasses import dataclass
from typing import Any

from echantillons import bloc_png, boite, ftyp, segment

from voight_kampff._travail.contexte import Contexte
from voight_kampff._travail.fichier import Fichier
from voight_kampff.rapport.modele import Direction, Partie, Plage

type Entree = tuple[int, int, int, bytes]
"""Étiquette, type, nombre d'éléments, octets de la valeur."""

DC = "http://purl.org/dc/elements/1.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XMP_NS = b"http://ns.adobe.com/xap/1.0/\x00"
XMP_ETENDU_NS = b"http://ns.adobe.com/xmp/extension/\x00"


# TIFF


@dataclass(frozen=True)
class Sous:
    """Sous-répertoire désigné par son étiquette dans le répertoire parent."""

    etiquette: int
    entrees: tuple["Entree | Sous", ...]


def ascii_(etiquette: int, texte: str | bytes) -> Entree:
    octets = texte.encode() if isinstance(texte, str) else texte
    return (etiquette, 2, len(octets) + 1, octets + b"\x00")


def nombres(etiquette: int, type_: int, *valeurs: int | float, ordre: str = ">") -> Entree:
    format_ = {1: "B", 3: "H", 4: "I", 6: "b", 8: "h", 9: "i", 11: "f", 12: "d"}[type_]
    return (etiquette, type_, len(valeurs), struct.pack(ordre + format_ * len(valeurs), *valeurs))


def fractions(
    etiquette: int, *valeurs: tuple[int, int], signe: bool = False, ordre: str = ">"
) -> Entree:
    format_ = "ii" if signe else "II"
    octets = b"".join(struct.pack(ordre + format_, n, d) for n, d in valeurs)
    return (etiquette, 10 if signe else 5, len(valeurs), octets)


def indefini(etiquette: int, octets: bytes) -> Entree:
    return (etiquette, 7, len(octets), octets)


def tiff(
    ifd0: tuple[Entree | Sous, ...],
    *suivants: tuple[Entree | Sous, ...],
    ordre: str = ">",
) -> bytes:
    """Structure TIFF : IFD0, sous-répertoires à la suite de leur parent, IFD chaînés."""
    tampon = bytearray((b"MM\x00*" if ordre == ">" else b"II*\x00") + struct.pack(ordre + "I", 8))

    def ecrire(entrees: tuple[Entree | Sous, ...]) -> int:
        debut = len(tampon)
        tampon.extend(struct.pack(ordre + "H", len(entrees)) + bytes(12 * len(entrees) + 4))
        for rang, entree in enumerate(entrees):
            position = debut + 2 + 12 * rang
            if isinstance(entree, Sous):
                struct.pack_into(ordre + "HHI", tampon, position, entree.etiquette, 4, 1)
                struct.pack_into(ordre + "I", tampon, position + 8, ecrire(entree.entrees))
                continue
            etiquette, type_, compte, octets = entree
            struct.pack_into(ordre + "HHI", tampon, position, etiquette, type_, compte)
            if len(octets) <= 4:
                tampon[position + 8 : position + 8 + len(octets)] = octets
            else:
                struct.pack_into(ordre + "I", tampon, position + 8, len(tampon))
                tampon.extend(octets + b"\x00" * (len(octets) & 1))
        return debut

    precedent, nombre = ecrire(ifd0), len(ifd0)
    for repertoire in suivants:
        position = ecrire(repertoire)
        struct.pack_into(ordre + "I", tampon, precedent + 2 + 12 * nombre, position)
        precedent, nombre = position, len(repertoire)
    return bytes(tampon)


# Conteneurs

ENTROPIE = segment(0xDA, b"\x01\x01\x00\x00\x3f\x00") + b"\x12\x34\xff\xd9"


def jpeg_meta(*segments: bytes) -> bytes:
    return b"\xff\xd8" + b"".join(segments) + ENTROPIE


def app1_exif(donnees: bytes) -> bytes:
    return segment(0xE1, b"Exif\x00\x00" + donnees)


def app1_xmp(paquet: bytes) -> bytes:
    return segment(0xE1, XMP_NS + paquet)


def app1_etendu(guid: bytes, total: int, position: int, donnees: bytes) -> bytes:
    entete = guid + struct.pack(">II", total, position)
    return segment(0xE1, XMP_ETENDU_NS + entete + donnees)


def app13(ressources: bytes) -> bytes:
    return segment(0xED, b"Photoshop 3.0\x00" + ressources)


def png_meta(*blocs: bytes) -> bytes:
    entete = bloc_png(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    donnees = bloc_png(b"IDAT", zlib.compress(b"\x00\x00"))
    return b"\x89PNG\r\n\x1a\n" + entete + b"".join(blocs) + donnees + bloc_png(b"IEND", b"")


def texte(mot_cle: bytes, contenu: bytes) -> bytes:
    return bloc_png(b"tEXt", mot_cle + b"\x00" + contenu)


def texte_compresse(mot_cle: bytes, contenu: bytes, methode: bytes = b"\x00") -> bytes:
    return bloc_png(b"zTXt", mot_cle + b"\x00" + methode + zlib.compress(contenu))


def texte_international(
    mot_cle: bytes,
    contenu: bytes,
    *,
    compresse: bool = False,
    methode: bytes = b"\x00",
    langue: bytes = b"",
    drapeau: bytes | None = None,
) -> bytes:
    corps = zlib.compress(contenu) if compresse else contenu
    drapeau = (b"\x01" if compresse else b"\x00") if drapeau is None else drapeau
    entete = mot_cle + b"\x00" + drapeau + methode + langue + b"\x00" + b"\x00"
    return bloc_png(b"iTXt", entete + corps)


def bloc_riff(nature: bytes, donnees: bytes) -> bytes:
    return nature + struct.pack("<I", len(donnees)) + donnees + b"\x00" * (len(donnees) & 1)


def webp_meta(*blocs: bytes) -> bytes:
    contenu = b"WEBP" + bloc_riff(b"VP8X", bytes(10)) + b"".join(blocs)
    return b"RIFF" + struct.pack("<I", len(contenu)) + contenu


@dataclass(frozen=True)
class Element:
    """Élément d'un HEIC : identifiant, type, contenu, type MIME pour ``mime``."""

    identifiant: int
    nature: bytes
    contenu: bytes
    type_mime: bytes = b""
    morceaux: int = 1
    """Nombre d'étendues sur lesquelles le contenu est réparti."""
    version: int = 2
    """Version de sa boîte ``infe`` : 0 et 1 sont l'ancienne forme, sans type d'élément."""


def _boite_pleine(nature: bytes, version: int, contenu: bytes) -> bytes:
    return boite(nature, bytes([version, 0, 0, 0]) + contenu)


def infe(element: Element) -> bytes:
    version = element.version
    if version < 2:
        corps = struct.pack(">HH", element.identifiant, 0) + b"nom\x00type\x00\x00"
        return _boite_pleine(b"infe", version, corps)
    taille = ">H" if version == 2 else ">I"
    corps = struct.pack(taille, element.identifiant) + b"\x00\x00" + element.nature + b"\x00"
    if element.nature == b"mime":
        corps += element.type_mime + b"\x00"
    return _boite_pleine(b"infe", version, corps)


def heic_meta(
    *elements: Element,
    methode: int = 0,
    reference: int = 0,
    autres: bytes = b"",
    version_iloc: int = 1,
    iloc_brut: bytes | None = None,
) -> bytes:
    """HEIC : ``ftyp``, ``meta`` (``hdlr``, ``iinf``, ``iloc``, ``idat`` si méthode 1), ``mdat``."""
    entete = ftyp(b"heic", b"mif1", b"heic")
    iinf = _boite_pleine(
        b"iinf", 0, struct.pack(">H", len(elements)) + b"".join(infe(e) for e in elements)
    )
    hdlr = _boite_pleine(b"hdlr", 0, b"\x00" * 4 + b"pict" + b"\x00" * 13)

    taille_id = ">I" if version_iloc == 2 else ">H"

    def iloc(origine: int) -> bytes:
        corps = b"\x44\x00" + struct.pack(taille_id, len(elements))
        position = origine
        for element in elements:
            corps += struct.pack(taille_id, element.identifiant)
            if version_iloc:
                corps += struct.pack(">H", methode)
            corps += struct.pack(">HH", reference, element.morceaux)
            taille = -(-len(element.contenu) // max(element.morceaux, 1))
            for debut in range(0, len(element.contenu) if element.morceaux else 0, taille):
                morceau = element.contenu[debut : debut + taille]
                corps += struct.pack(">II", position, len(morceau))
                position += len(morceau)
        return _boite_pleine(b"iloc", version_iloc, corps) if iloc_brut is None else iloc_brut

    donnees = b"".join(element.contenu for element in elements)
    if methode == 1:
        meta = _boite_pleine(b"meta", 0, hdlr + iinf + iloc(0) + boite(b"idat", donnees) + autres)
        return entete + meta
    longueur_meta = len(_boite_pleine(b"meta", 0, hdlr + iinf + iloc(0) + autres))
    origine = len(entete) + longueur_meta + 8
    meta = _boite_pleine(b"meta", 0, hdlr + iinf + iloc(origine) + autres)
    return entete + meta + boite(b"mdat", donnees)


# XMP


def xmp(description: str, *, espaces: str = f'xmlns:dc="{DC}"', attributs: str = "") -> bytes:
    """Paquet XMP complet, avec enveloppe ``xpacket`` et ``x:xmpmeta``."""
    return (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Outil 1.0">'
        f'<rdf:RDF xmlns:rdf="{RDF}">'
        f'<rdf:Description rdf:about="" {espaces} {attributs}>{description}</rdf:Description>'
        "</rdf:RDF></x:xmpmeta>"
        '<?xpacket end="w"?>'
    ).encode()


# Photoshop et IIM


def ressource(
    identifiant: int, donnees: bytes, nom: bytes = b"", signature: bytes = b"8BIM"
) -> bytes:
    pascal = bytes([len(nom)]) + nom
    pascal += b"\x00" * (len(pascal) & 1)
    corps = donnees + b"\x00" * (len(donnees) & 1)
    return (
        signature
        + struct.pack(">H", identifiant)
        + pascal
        + struct.pack(">I", len(donnees))
        + corps
    )


def jeu(enregistrement: int, numero: int, donnees: bytes) -> bytes:
    return bytes([0x1C, enregistrement, numero]) + struct.pack(">H", len(donnees)) + donnees


# Exécution d'un module dans le processus des tests (garde levée par le test appelant)


def contexte(fichier: Any, contenu: bytes, format_: str, module: str) -> Contexte:
    fichier.write(contenu)
    fichier.flush()
    partie = Partie(1, format_, Plage(0, len(contenu)), fin_connue=True)
    directions = {Direction.RIEN_DE_PARTICULIER}
    return Contexte(module, directions, Fichier(fichier.fileno()), partie, 64 << 20)


def resultats(module: str, contenu: bytes, format_: str) -> list[dict[str, Any]]:
    """Messages produits par le module sur ``contenu``, décodés."""
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, contenu, format_, module)
        importlib.import_module(f"voight_kampff.modules.{module}").analyser(c)
        return [json.loads(ligne) for ligne in c.lignes]


def observations(lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ligne["observation"] for ligne in lignes if ligne["type"] == "observation"]


def valeurs_de(lignes: list[dict[str, Any]]) -> dict[str, Any]:
    """Valeur de chaque observation par nom ; la dernière l'emporte."""
    return {o["nom"]: o["valeur"] for o in observations(lignes)}


def raisons(lignes: list[dict[str, Any]]) -> list[str]:
    return [ligne["non_menee"]["raison"] for ligne in lignes if ligne["type"] == "non_menee"]


def identifiantes(lignes: list[dict[str, Any]]) -> dict[str, str]:
    return {o["nom"]: o["identifiante"] for o in observations(lignes) if "identifiante" in o}
