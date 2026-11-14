"""Échantillons de métadonnées, construits octet par octet pour les tests (T20, T21).

Chaque constructeur suit la structure que lisent les modules : en-tête et répertoires TIFF,
segments JPEG, blocs PNG et WebP, boîtes HEIC, paquets XMP, ressources Photoshop et IIM,
objets et références croisées d'un PDF. Aucun échantillon n'est décodable comme image, ni
affichable comme document : les données d'image et les pages sont absentes ou factices.
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


# Structure d'une image (T24) : en-têtes et tables de quantification

LUMINANCE = (
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99,
)  # fmt: skip
"""Tableau K.1 de T.81, dans l'ordre du bloc."""
CHROMINANCE = (
    17, 18, 24, 47, 99, 99, 99, 99, 18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99, 47, 66, 99, 99, 99, 99, 99, 99,
    *(99,) * 32,
)  # fmt: skip
"""Tableau K.2 de T.81."""
ZIGZAG = (
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48,
    41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23,
    30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
)  # fmt: skip


def table_ijg(base: tuple[int, ...], qualite: int, plafond: int = 255) -> tuple[int, ...]:
    """Table de libjpeg à cette qualité (jcparam.c), dans l'ordre du segment DQT."""
    facteur = 5000 // qualite if qualite < 50 else 200 - 2 * qualite
    return tuple(min(max((base[i] * facteur + 50) // 100, 1), plafond) for i in ZIGZAG)


def dqt(*tables: tuple[int, tuple[int, ...]], seize_bits: bool = False) -> bytes:
    """Segment DQT : identifiant et 64 valeurs de chaque table."""
    corps = b""
    for identifiant, valeurs in tables:
        if seize_bits:
            corps += bytes([0x10 | identifiant]) + struct.pack(">64H", *valeurs)
        else:
            corps += bytes([identifiant]) + bytes(valeurs)
    return segment(0xDB, corps)


def sof(largeur: int, hauteur: int, marqueur: int = 0xC0, composantes: int = 3) -> bytes:
    composante = b"".join(bytes([n + 1, 0x11, min(n, 1)]) for n in range(composantes))
    return segment(marqueur, struct.pack(">BHHB", 8, hauteur, largeur, composantes) + composante)


def jpeg_ijg(qualite: int) -> bytes:
    """Tables de luminance et de chrominance de libjpeg à cette qualité, en un segment."""
    return dqt((0, table_ijg(LUMINANCE, qualite)), (1, table_ijg(CHROMINANCE, qualite)))


AUTRES_TABLES = dqt((0, (2,) * 64), (1, (3,) * 64))
"""Tables qui ne sont pas celles de libjpeg."""


def jpeg_image(
    largeur: int, hauteur: int, *segments: bytes, tables: bytes = AUTRES_TABLES
) -> bytes:
    """JPEG à tables de quantification et en-tête d'image, suivis de ``segments``."""
    return jpeg_meta(tables, sof(largeur, hauteur), *segments)


def vp8(largeur: int, hauteur: int) -> bytes:
    """Bloc ``VP8 `` d'une trame clé (RFC 6386, 9.1)."""
    return bloc_riff(b"VP8 ", b"\x10\x02\x00\x9d\x01\x2a" + struct.pack("<HH", largeur, hauteur))


def vp8l(largeur: int, hauteur: int) -> bytes:
    """Bloc ``VP8L`` (RFC 9649) : signature, largeur - 1 et hauteur - 1 sur 14 bits."""
    bits = (largeur - 1) | ((hauteur - 1) << 14)
    return bloc_riff(b"VP8L", b"\x2f" + struct.pack("<I", bits))


def webp_image(*blocs: bytes) -> bytes:
    """WebP sans ``VP8X`` : ses blocs tels quels."""
    contenu = b"WEBP" + b"".join(blocs)
    return b"RIFF" + struct.pack("<I", len(contenu)) + contenu


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


# PDF (ISO 32000-2, §7.5)


def flux_pdf(dico: str, donnees: bytes) -> bytes:
    """Corps d'un objet flux : dictionnaire, longueur exacte, données."""
    return f"<<{dico}/Length {len(donnees)}>>stream\n".encode() + donnees + b"\nendstream"


def lignes_png(
    donnees: bytes, colonnes: int, filtres: tuple[int, ...] = (2,), pas: int = 1
) -> bytes:
    """Lignes filtrées par le prédicteur PNG, un filtre par ligne pris en boucle dans ``filtres``.

    ``pas`` est le nombre d'octets d'un pixel : la gauche d'un octet est ``pas`` octets avant.
    """
    sortie, precedente = bytearray(), bytes(colonnes)
    for rang, debut in enumerate(range(0, len(donnees), colonnes)):
        ligne, filtre = donnees[debut : debut + colonnes], filtres[rang % len(filtres)]
        codee = bytearray()
        for i, octet in enumerate(ligne):
            gauche = ligne[i - pas] if i >= pas else 0
            haut = precedente[i]
            diagonale = precedente[i - pas] if i >= pas else 0
            estimation = gauche + haut - diagonale
            ecarts = [abs(estimation - v) for v in (gauche, haut, diagonale)]
            paeth = (gauche, haut, diagonale)[ecarts.index(min(ecarts))]
            ajout = (0, gauche, haut, (gauche + haut) // 2, paeth)[filtre]
            codee.append((octet - ajout) & 0xFF)
        sortie += bytes([filtre]) + codee
        precedente = ligne
    return bytes(sortie)


def pdf(
    objets: dict[int, bytes],
    trailer: str = "/Root 1 0 R",
    *,
    flux_xref: bool = False,
    flux_objets: dict[int, tuple[int, ...]] | None = None,
    predicteur: str = "",
    png: bool = False,
    base: bytes | None = None,
    largeur: int = 20,
) -> bytes:
    """PDF : objets (numéro → corps), table classique ou flux de références croisées.

    ``flux_objets`` range des objets dans des flux d'objets (numéro du flux → numéros des
    objets) ; ``predicteur`` est le ``/DecodeParms`` du flux de références croisées, et ``png``
    filtre ses lignes en Up. Avec ``base``, ajoute une mise à jour incrémentale à ce document.
    """
    tampon = bytearray(base if base is not None else b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    entrees: dict[int, tuple[int, int, int]] = {} if base is not None else {0: (0, 0, 65535)}
    contenus = dict(objets)
    for numero_flux, ranges in (flux_objets or {}).items():
        tete, corps = b"", b""
        for rang, numero in enumerate(ranges):
            tete += f"{numero} {len(corps)} ".encode()
            corps += contenus.pop(numero) + b"\n"
            entrees[numero] = (2, numero_flux, rang)
        dico = f"/Type/ObjStm/N {len(ranges)}/First {len(tete)}/Filter/FlateDecode"
        contenus[numero_flux] = flux_pdf(dico, zlib.compress(tete + corps))
    for numero, corps in sorted(contenus.items()):
        entrees[numero] = (1, len(tampon), 0)
        tampon += f"{numero} 0 obj\n".encode() + corps + b"\nendobj\n"
    precedent = f"/Prev {_startxref(base)}" if base is not None else ""
    taille = max(entrees) + 1
    debut = len(tampon)
    if not flux_xref:
        fin = {19: b"\n", 20: b"\r\n", 21: b" \r\n"}[largeur]
        tampon += b"xref\n"
        for premier, numeros in _plages(entrees):
            tampon += f"{premier} {len(numeros)}\n".encode()
            for numero in numeros:
                nature, champ, generation = entrees[numero]
                marque = "n" if nature == 1 else "f"
                tampon += f"{champ:010d} {generation:05d} {marque}".encode() + fin
        tampon += f"trailer\n<</Size {taille}{trailer}{precedent}>>\n".encode()
    else:
        entrees[taille] = (1, debut, 0)
        taille += 1
        index, lignes = "", b""
        for premier, numeros in _plages(entrees):
            index += f"{premier} {len(numeros)} "
            lignes += b"".join(struct.pack(">BIH", *entrees[n]) for n in numeros)
        if png:
            lignes = lignes_png(lignes, 7)
        dico = f"/Type/XRef/Size {taille}/W[1 4 2]/Index[{index}]{trailer}{precedent}"
        dico += "/Filter/FlateDecode" + (f"/DecodeParms{predicteur}" if predicteur else "")
        corps = flux_pdf(dico, zlib.compress(lignes))
        tampon += f"{taille - 1} 0 obj\n".encode() + corps + b"\nendobj\n"
    tampon += f"startxref\n{debut}\n%%EOF\n".encode()
    return bytes(tampon)


def _startxref(document: bytes) -> int:
    queue = document[document.rindex(b"startxref") + 9 :]
    return int(queue.split()[0])


def _plages(entrees: dict[int, tuple[int, int, int]]) -> list[tuple[int, list[int]]]:
    plages: list[tuple[int, list[int]]] = []
    for numero in sorted(entrees):
        if plages and plages[-1][0] + len(plages[-1][1]) == numero:
            plages[-1][1].append(numero)
        else:
            plages.append((numero, [numero]))
    return plages


CATALOGUE_PDF = b"<</Type/Catalog/Pages 2 0 R>>"
PAGES_PDF = b"<</Type/Pages/Kids[]/Count 0>>"


def pdf_info(info: bytes, *, xmp_: bytes | None = None, **options: Any) -> bytes:
    """PDF d'un catalogue, de ses pages, d'un dictionnaire Info (objet 3) et d'un XMP (objet 4)."""
    catalogue = CATALOGUE_PDF if xmp_ is None else b"<</Type/Catalog/Pages 2 0 R/Metadata 4 0 R>>"
    objets = {1: catalogue, 2: PAGES_PDF, 3: info}
    if xmp_ is not None:
        objets[4] = flux_pdf("/Type/Metadata/Subtype/XML", xmp_)
    return pdf(objets, options.pop("trailer", "/Root 1 0 R/Info 3 0 R"), **options)


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
