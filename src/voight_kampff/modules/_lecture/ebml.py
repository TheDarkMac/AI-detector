"""Éléments EBML (RFC 8794) : en-têtes, enfants et entiers, lus dans des octets (ADR-0131).

Un élément est un identifiant de une à quatre octets, une taille de une à huit octets, puis
ses données ; une taille dont tous les bits valent un est « inconnue » (§6.2). Le lecteur ne
décode que ce que lui demandent ``conteneurs`` (éléments de premier niveau d'un WebM) et le
module ``matroska`` (contenu de ``Info`` et de ``Tags``).
"""

from collections.abc import Iterator

__all__ = ["Incomplet", "Invalide", "enfants", "entete", "entier", "signe"]


class Invalide(Exception):
    """Élément mal formé, ou qui déborde de son parent."""


class Incomplet(Invalide):
    """En-tête coupé par la fin des octets lus."""


def entete(octets: bytes, position: int, fin: int | None = None) -> tuple[int, int, int | None]:
    """Identifiant, longueur de l'en-tête et taille des données de l'élément à ``position``.

    La taille vaut ``None`` si elle est inconnue. Les octets s'arrêtent à ``fin``, ou à la fin
    de ``octets``.
    """
    fin = len(octets) if fin is None else fin
    if position >= fin:
        raise Incomplet
    if octets[position] < 0x10:
        raise Invalide  # identifiant nul ou de plus de quatre octets
    longueur = 9 - octets[position].bit_length()
    if position + longueur >= fin:
        raise Incomplet
    identifiant = int.from_bytes(octets[position : position + longueur], "big")
    suite = position + longueur
    if octets[suite] == 0:
        raise Invalide  # taille de plus de huit octets
    octets_taille = 9 - octets[suite].bit_length()
    if suite + octets_taille > fin:
        raise Incomplet
    masque = (1 << (7 * octets_taille)) - 1
    brute = int.from_bytes(octets[suite : suite + octets_taille], "big") & masque
    return identifiant, longueur + octets_taille, None if brute == masque else brute


def enfants(octets: bytes, debut: int, fin: int) -> Iterator[tuple[int, int, int]]:
    """Identifiant, début et fin des données de chaque élément entre ``debut`` et ``fin``.

    Un élément de taille inconnue, ou qui déborde de ``fin``, lève ``Invalide`` : seuls les
    éléments de premier niveau d'un segment peuvent être de taille inconnue.
    """
    position = debut
    while position < fin:
        try:
            identifiant, longueur, taille = entete(octets, position, fin)
        except Incomplet:
            raise Invalide from None
        if taille is None or position + longueur + taille > fin:
            raise Invalide
        yield identifiant, position + longueur, position + longueur + taille
        position += longueur + taille


def entier(octets: bytes) -> int:
    """Entier non signé, gros-boutiste, de zéro à huit octets (§7.2)."""
    if len(octets) > 8:
        raise Invalide
    return int.from_bytes(octets, "big")


def signe(octets: bytes) -> int:
    """Entier signé, gros-boutiste, de zéro à huit octets (§7.1)."""
    if len(octets) > 8:
        raise Invalide
    return int.from_bytes(octets, "big", signed=True)
