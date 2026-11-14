"""Module ``image`` : structure d'une image (F-06, ADR-0154 ; fiche ``structure-image``).

Lit les blocs de structure que relève le lecteur de conteneurs, sans décoder l'image :

- les dimensions de l'en-tête de l'image (premier segment SOF d'un JPEG, bloc ``IHDR`` d'un PNG,
  bloc ``VP8X``, ``VP8 `` ou ``VP8L`` d'un WebP), sous ``image.largeur`` et ``image.hauteur``,
  et le bloc qui les porte sous ``image.trame`` ;
- le nombre de blocs de métadonnées que lisent les modules du projet, sous ``image.metadonnees``,
  observé seulement si le parcours du conteneur est complet ;
- pour un JPEG, le nombre de tables de quantification en vigueur au premier balayage, sous
  ``image.jpeg.tables``, et, si elles sont celles de la bibliothèque libjpeg de l'IJG à une
  qualité de 1 à 100, cette qualité sous ``image.jpeg.qualite_ijg``.

Aucune règle « module » : les règles du catalogue lisent ces observations (T24, indices de
transfert). Le HEIC n'est pas lu (ADR-0154).
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture.conteneurs import (
    STRUCTURE,
    Bloc,
    Nature,
    lire_bloc,
    relever,
)
from voight_kampff.rapport.modele import RaisonNonMenee

__all__ = ["analyser", "qualite_ijg"]

_ZIGZAG = (
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
)  # fmt: skip
"""Position dans le bloc de 8 sur 8 de chaque coefficient, dans l'ordre où le segment DQT les écrit
(T.81, figure A.6)."""

_LUMINANCE = (
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
)  # fmt: skip
"""Table de luminance de l'annexe K de T.81 (tableau K.1), reprise par libjpeg, dans l'ordre du
bloc."""

_CHROMINANCE = (
    17, 18, 24, 47, 99, 99, 99, 99,
    18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99,
    47, 66, 99, 99, 99, 99, 99, 99,
    *(99,) * 32,
)  # fmt: skip
"""Table de chrominance de l'annexe K de T.81 (tableau K.2)."""


def _table_ijg(base: tuple[int, ...], qualite: int, seize_bits: bool) -> tuple[int, ...]:
    """Table que libjpeg écrit à cette qualité, dans l'ordre du segment DQT.

    ``jpeg_quality_scaling`` puis ``jpeg_add_quant_table`` (jcparam.c) : facteur 5000 / q sous
    50, 200 - 2q au-delà ; arrondi, borné à 1 et 32 767, et à 255 pour une table de huit bits.
    """
    facteur = 5000 // qualite if qualite < 50 else 200 - 2 * qualite
    plafond = 32767 if seize_bits else 255
    return tuple(min(max((base[i] * facteur + 50) // 100, 1), plafond) for i in _ZIGZAG)


_QUALITES = {
    (seize_bits, _table_ijg(_LUMINANCE, qualite, seize_bits)): qualite
    for seize_bits in (False, True)
    for qualite in range(100, 0, -1)
}
"""Qualité de chaque table de luminance de libjpeg ; une qualité par table (vérifié par les
tests)."""


def qualite_ijg(tables: dict[int, tuple[bool, tuple[int, ...]]]) -> int | None:
    """Qualité libjpeg dont viennent ces tables, ou ``None``.

    ``tables`` donne, par identifiant, la précision (seize bits ou non) et les 64 valeurs dans
    l'ordre du segment. Les tables doivent être la luminance (0) et, s'il y en a une, la
    chrominance (1) de la même qualité ; aucune autre.
    """
    if 0 not in tables or not tables.keys() <= {0, 1}:
        return None
    qualite = _QUALITES.get(tables[0])
    if qualite is None:
        return None
    if 1 in tables:
        seize_bits, valeurs = tables[1]
        if valeurs != _table_ijg(_CHROMINANCE, qualite, seize_bits):
            return None
    return qualite


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    if releve.arret is None:
        metadonnees = [bloc for bloc in releve.blocs if bloc.nature not in STRUCTURE]
        contexte.observer("image.metadonnees", len(metadonnees))
    trame = next((bloc for bloc in releve.blocs if bloc.nature is Nature.TRAME), None)
    if trame is not None:
        _trame(contexte, trame)
    if contexte.format_reel == "jpeg":
        _quantification(
            contexte, [bloc for bloc in releve.blocs if bloc.nature is Nature.QUANTIFICATION]
        )
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _trame(contexte: Contexte, bloc: Bloc) -> None:
    donnees = lire_bloc(contexte, bloc)
    dimensions = _dimensions(bloc.chemin, donnees)
    localisation = bloc.localisation()
    if dimensions is None:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
        return
    largeur, hauteur = dimensions
    contexte.observer("image.trame", bloc.chemin, localisation=localisation)
    contexte.observer("image.largeur", largeur, unite="px", localisation=localisation)
    if hauteur is not None:
        contexte.observer("image.hauteur", hauteur, unite="px", localisation=localisation)


def _dimensions(chemin: str, donnees: bytes) -> tuple[int, int | None] | None:
    """Largeur et hauteur d'un en-tête d'image ; hauteur ``None`` si un JPEG la donne plus loin."""
    if chemin.startswith("SOF"):
        # Précision, hauteur, largeur, composantes (T.81, B.2.2) ; une hauteur nulle est
        # donnée par un segment DNL après le premier balayage, que le lecteur ne lit pas.
        if len(donnees) < 6:
            return None
        hauteur = int.from_bytes(donnees[1:3], "big")
        return int.from_bytes(donnees[3:5], "big"), hauteur or None
    if chemin == "IHDR":
        if len(donnees) < 8:
            return None
        return int.from_bytes(donnees[:4], "big"), int.from_bytes(donnees[4:8], "big")
    if chemin == "VP8X":
        # Drapeaux, trois octets réservés, largeur - 1 et hauteur - 1 en 24 bits (RFC 9649).
        if len(donnees) < 10:
            return None
        return (
            int.from_bytes(donnees[4:7], "little") + 1,
            int.from_bytes(donnees[7:10], "little") + 1,
        )
    if chemin == "VP8L":
        # Signature 0x2F, puis largeur - 1 et hauteur - 1 sur 14 bits chacune (RFC 9649).
        if len(donnees) < 5 or donnees[0] != 0x2F:
            return None
        bits = int.from_bytes(donnees[1:5], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    # VP8 : trame clé, code de départ 9D 01 2A, dimensions sur 14 bits (RFC 6386, 9.1).
    if len(donnees) < 10 or donnees[0] & 1 or donnees[3:6] != b"\x9d\x01\x2a":
        return None
    return (
        int.from_bytes(donnees[6:8], "little") & 0x3FFF,
        int.from_bytes(donnees[8:10], "little") & 0x3FFF,
    )


def _quantification(contexte: Contexte, blocs: list[Bloc]) -> None:
    """Tables en vigueur au premier balayage : la dernière définie pour chaque identifiant."""
    tables: dict[int, tuple[bool, tuple[int, ...]]] = {}
    for bloc in blocs:
        donnees = lire_bloc(contexte, bloc)
        position = 0
        while position < len(donnees):
            precision, identifiant = donnees[position] >> 4, donnees[position] & 0x0F
            taille = 128 if precision else 64
            octets = donnees[position + 1 : position + 1 + taille]
            if precision > 1 or identifiant > 3 or len(octets) < taille:
                contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())
                break
            valeurs = (
                tuple(int.from_bytes(octets[i : i + 2], "big") for i in range(0, 128, 2))
                if precision
                else tuple(octets)
            )
            tables[identifiant] = (bool(precision), valeurs)
            position += 1 + taille
    if not tables:
        return
    localisation = blocs[0].localisation() if len(blocs) == 1 else None
    contexte.observer("image.jpeg.tables", len(tables), localisation=localisation)
    qualite = qualite_ijg(tables)
    if qualite is not None:
        contexte.observer("image.jpeg.qualite_ijg", qualite, localisation=localisation)
