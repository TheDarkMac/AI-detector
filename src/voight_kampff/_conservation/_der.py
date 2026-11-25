"""Lecture et écriture DER minimales, juste ce que demande l'horodatage RFC 3161 (ADR-0263).

La réponse d'une autorité d'horodatage est lue par le processus principal, hors du processus de
travail : elle vient du réseau et se lit comme un fichier hostile. La lecture n'admet que des
longueurs définies, des étiquettes d'un octet, et vérifie chaque longueur contre les octets
disponibles ; elle n'est pas récursive, chaque élément construit n'étant découpé qu'à la
demande. Toute anomalie lève :class:`DerInvalide`, dont le message ne cite aucun octet reçu.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

__all__ = [
    "BOOLEEN",
    "CONTEXTE_0",
    "ENSEMBLE",
    "ENTIER",
    "HEURE_GENERALISEE",
    "NUL",
    "OCTETS",
    "OID",
    "SUITE",
    "DerInvalide",
    "Element",
    "booleen",
    "encoder",
    "entier",
    "heure",
    "lire",
    "oid",
    "suite",
    "valeur_entiere",
    "valeur_oid",
]

BOOLEEN = 0x01
ENTIER = 0x02
OCTETS = 0x04
NUL = 0x05
OID = 0x06
HEURE_GENERALISEE = 0x18
SUITE = 0x30
ENSEMBLE = 0x31
CONTEXTE_0 = 0xA0
"""Étiquette ``[0]`` construite, explicite ou implicite."""

_OCTETS_DE_LONGUEUR_MAX = 4


class DerInvalide(ValueError):
    """Structure DER illisible ou inattendue ; le message ne cite aucun octet reçu."""


@dataclass(frozen=True, slots=True)
class Element:
    """Élément DER : étiquette d'un octet et contenu, encore non interprété."""

    etiquette: int
    contenu: bytes

    def enfants(self) -> list["Element"]:
        """Éléments du contenu d'un élément construit, dans l'ordre."""
        if not self.etiquette & 0x20:
            raise DerInvalide("élément primitif là où un élément construit est attendu")
        return _suite(self.contenu)

    def attendre(self, etiquette: int, quoi: str) -> "Element":
        """Lui-même, s'il porte cette étiquette ; sinon ``DerInvalide`` qui nomme ``quoi``."""
        if self.etiquette != etiquette:
            raise DerInvalide(f"{quoi} : étiquette inattendue")
        return self


def _element(donnees: bytes, debut: int) -> tuple[Element, int]:
    """Élément qui commence à ``debut``, et la position qui le suit."""
    if debut + 2 > len(donnees):
        raise DerInvalide("élément tronqué")
    etiquette = donnees[debut]
    if etiquette & 0x1F == 0x1F:
        raise DerInvalide("étiquette de plus d'un octet")
    premier = donnees[debut + 1]
    position = debut + 2
    if premier < 0x80:
        longueur = premier
    else:
        nombre = premier & 0x7F
        if nombre == 0:
            raise DerInvalide("longueur indéfinie")
        if nombre > _OCTETS_DE_LONGUEUR_MAX or position + nombre > len(donnees):
            raise DerInvalide("longueur illisible")
        longueur = int.from_bytes(donnees[position : position + nombre], "big")
        position += nombre
    fin = position + longueur
    if fin > len(donnees):
        raise DerInvalide("élément plus long que les données")
    return Element(etiquette, donnees[position:fin]), fin


def _suite(donnees: bytes) -> list[Element]:
    elements = []
    position = 0
    while position < len(donnees):
        element, position = _element(donnees, position)
        elements.append(element)
    return elements


def lire(donnees: bytes) -> Element:
    """Le seul élément de ``donnees`` ; des octets après lui lèvent ``DerInvalide``."""
    element, fin = _element(donnees, 0)
    if fin != len(donnees):
        raise DerInvalide("octets après la fin de la structure")
    return element


def valeur_entiere(element: Element) -> int:
    """Valeur d'un ``INTEGER``, signée."""
    element.attendre(ENTIER, "entier")
    if not element.contenu:
        raise DerInvalide("entier vide")
    return int.from_bytes(element.contenu, "big", signed=True)


def valeur_oid(element: Element) -> str:
    """Identifiant d'objet, en notation pointée."""
    element.attendre(OID, "identifiant d'objet")
    contenu = element.contenu
    if not contenu or contenu[-1] & 0x80:
        raise DerInvalide("identifiant d'objet tronqué")
    arcs: list[int] = []
    courant = 0
    for octet in contenu:
        courant = (courant << 7) | (octet & 0x7F)
        if not octet & 0x80:
            arcs.append(courant)
            courant = 0
    premier = min(arcs[0] // 40, 2)
    return ".".join(str(arc) for arc in [premier, arcs[0] - 40 * premier, *arcs[1:]])


def heure(element: Element) -> datetime:
    """Heure d'un ``GeneralizedTime`` en UTC (``AAAAMMJJHHMMSS[.f]Z``), à la seconde."""
    element.attendre(HEURE_GENERALISEE, "heure")
    try:
        texte = element.contenu.decode("ascii")
    except UnicodeDecodeError:
        raise DerInvalide("heure illisible") from None
    secondes, point, fraction = texte.removesuffix("Z").partition(".")
    chiffres = secondes + (fraction if point else "0")
    if (
        not texte.endswith("Z")
        or len(secondes) != 14
        or not (chiffres.isascii() and chiffres.isdigit() and (fraction or not point))
    ):
        raise DerInvalide("heure illisible")
    try:
        return datetime.strptime(secondes, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:
        raise DerInvalide("heure illisible") from None


# Écriture


def encoder(etiquette: int, contenu: bytes) -> bytes:
    """Élément DER de cette étiquette et de ce contenu."""
    longueur = len(contenu)
    if longueur < 0x80:
        return bytes([etiquette, longueur]) + contenu
    octets = longueur.to_bytes((longueur.bit_length() + 7) // 8, "big")
    return bytes([etiquette, 0x80 | len(octets)]) + octets + contenu


def suite(*elements: bytes) -> bytes:
    """``SEQUENCE`` de ces éléments déjà encodés."""
    return encoder(SUITE, b"".join(elements))


def entier(valeur: int) -> bytes:
    """``INTEGER`` positif ou nul, sur le moins d'octets possible."""
    return encoder(ENTIER, valeur.to_bytes(valeur.bit_length() // 8 + 1, "big", signed=True))


def booleen(valeur: bool) -> bytes:
    """``BOOLEAN``."""
    return encoder(BOOLEEN, b"\xff" if valeur else b"\x00")


def oid(texte: str) -> bytes:
    """``OBJECT IDENTIFIER`` en notation pointée."""
    premier, second, *autres = (int(arc) for arc in texte.split("."))
    contenu = bytearray()
    for arc in [40 * premier + second, *autres]:
        groupes = [arc & 0x7F]
        arc >>= 7
        while arc:
            groupes.append(0x80 | (arc & 0x7F))
            arc >>= 7
        contenu += bytes(reversed(groupes))
    return encoder(OID, bytes(contenu))
