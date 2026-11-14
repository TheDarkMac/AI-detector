"""Module ``image`` : structure d'une image (F-06, ADR-0154 ; fiche ``structure-image``).

Lit les blocs de structure que relève le lecteur de conteneurs, sans décoder l'image :

- les dimensions de l'en-tête de l'image (premier segment SOF d'un JPEG, bloc ``IHDR`` d'un PNG,
  bloc ``VP8X``, ``VP8 `` ou ``VP8L`` d'un WebP), sous ``image.largeur`` et ``image.hauteur``,
  et le bloc qui les porte sous ``image.trame`` ;
- le nombre de blocs de métadonnées que lisent les modules du projet, sous ``image.metadonnees``,
  observé seulement si le parcours du conteneur est complet ;
- pour un JPEG, le nombre de tables de quantification en vigueur au premier balayage, sous
  ``image.jpeg.tables``, leur empreinte sous ``image.jpeg.empreinte_tables`` (ADR-0181), et
  l'encodeur connu dont elles viennent (ADR-0180, ADR-0183) : la bibliothèque libjpeg de l'IJG
  à une qualité de 1 à 100 (``image.jpeg.qualite_ijg``), ou à deux qualités pour la luminance et
  la chrominance (``image.jpeg.qualite_ijg_luminance`` et ``image.jpeg.qualite_ijg_chrominance``),
  un jeu de tables de mozjpeg (``image.jpeg.jeu_mozjpeg`` et ``image.jpeg.qualite_mozjpeg``), ou
  l'encodeur MJPEG de ffmpeg (``image.jpeg.qscale_ffmpeg``).

Aucune règle « module » : les règles du catalogue lisent ces observations (T24, indices de
transfert ; T40). Le HEIC n'est pas lu (ADR-0154).
"""

import hashlib

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture.conteneurs import (
    STRUCTURE,
    Bloc,
    Nature,
    lire_bloc,
    relever,
)
from voight_kampff.rapport.modele import RaisonNonMenee

__all__ = [
    "Tables",
    "analyser",
    "empreinte_tables",
    "encodeur",
    "jeu_mozjpeg",
    "qscale_ffmpeg",
    "qualite_ijg",
    "qualites_ijg",
]

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

_MOZJPEG_LUMINANCE = {
    2: (
        12, 17, 20, 21, 30, 34, 56, 63,
        18, 20, 20, 26, 28, 51, 61, 55,
        19, 20, 21, 26, 33, 58, 69, 55,
        26, 26, 26, 30, 46, 87, 86, 66,
        31, 33, 36, 40, 46, 96, 100, 73,
        40, 35, 46, 62, 81, 100, 111, 91,
        46, 66, 76, 86, 102, 121, 120, 101,
        68, 90, 90, 96, 113, 102, 105, 103,
    ),
    3: (
        16, 16, 16, 18, 25, 37, 56, 85,
        16, 17, 20, 27, 34, 40, 53, 75,
        16, 20, 24, 31, 43, 62, 91, 135,
        18, 27, 31, 40, 53, 74, 106, 156,
        25, 34, 43, 53, 69, 94, 131, 189,
        37, 40, 62, 74, 94, 124, 169, 238,
        56, 53, 91, 106, 131, 169, 226, 311,
        85, 75, 135, 156, 189, 238, 311, 418,
    ),
    4: (
        9, 10, 12, 14, 27, 32, 51, 62,
        11, 12, 14, 19, 27, 44, 59, 73,
        12, 14, 18, 25, 42, 59, 79, 78,
        17, 18, 25, 42, 61, 92, 87, 92,
        23, 28, 42, 75, 79, 112, 112, 99,
        40, 42, 59, 84, 88, 124, 132, 111,
        42, 64, 78, 95, 105, 126, 125, 99,
        70, 75, 100, 102, 116, 100, 107, 98,
    ),
    5: (
        10, 12, 14, 19, 26, 38, 57, 86,
        12, 18, 21, 28, 35, 41, 54, 76,
        14, 21, 25, 32, 44, 63, 92, 136,
        19, 28, 32, 41, 54, 75, 107, 157,
        26, 35, 44, 54, 70, 95, 132, 190,
        38, 41, 63, 75, 95, 125, 170, 239,
        57, 54, 92, 107, 132, 170, 227, 312,
        86, 76, 136, 157, 190, 239, 312, 419,
    ),
    6: (
        7, 8, 10, 14, 23, 44, 95, 241,
        8, 8, 11, 15, 25, 47, 102, 255,
        10, 11, 13, 19, 31, 58, 127, 255,
        14, 15, 19, 27, 44, 83, 181, 255,
        23, 25, 31, 44, 72, 136, 255, 255,
        44, 47, 58, 83, 136, 255, 255, 255,
        95, 102, 127, 181, 255, 255, 255, 255,
        241, 255, 255, 255, 255, 255, 255, 255,
    ),
    7: (
        15, 11, 11, 12, 15, 19, 25, 32,
        11, 13, 10, 10, 12, 15, 19, 24,
        11, 10, 14, 14, 16, 18, 22, 27,
        12, 10, 14, 18, 21, 24, 28, 33,
        15, 12, 16, 21, 26, 31, 36, 42,
        19, 15, 18, 24, 31, 38, 45, 53,
        25, 19, 22, 28, 36, 45, 55, 65,
        32, 24, 27, 33, 42, 53, 65, 77,
    ),
    8: (
        14, 10, 11, 14, 19, 25, 34, 45,
        10, 11, 11, 12, 15, 20, 26, 33,
        11, 11, 15, 18, 21, 25, 31, 38,
        14, 12, 18, 24, 28, 33, 39, 47,
        19, 15, 21, 28, 36, 43, 51, 59,
        25, 20, 25, 33, 43, 54, 64, 74,
        34, 26, 31, 39, 51, 64, 77, 91,
        45, 33, 38, 47, 59, 74, 91, 108,
    ),
}  # fmt: skip
"""Tables de luminance des jeux 2 à 8 de mozjpeg 4.1.1 (``std_luminance_quant_tbl`` de
jcparam.c), dans l'ordre du bloc ; le jeu 0 est l'annexe K (libjpeg), le jeu 1, plat, n'est pas
reconnu (ADR-0183)."""

_MOZJPEG_CHROMINANCE = {
    2: (
        8, 12, 15, 15, 86, 96, 96, 98,
        13, 13, 15, 26, 90, 96, 99, 98,
        12, 15, 18, 96, 99, 99, 99, 99,
        17, 16, 90, 96, 99, 99, 99, 99,
        96, 96, 99, 99, 99, 99, 99, 99,
        *(99,) * 24,
    ),
    3: _MOZJPEG_LUMINANCE[3],
    4: (
        9, 10, 17, 19, 62, 89, 91, 97,
        12, 13, 18, 29, 84, 91, 88, 98,
        14, 19, 29, 93, 95, 95, 98, 97,
        20, 26, 84, 88, 95, 95, 98, 94,
        26, 86, 91, 93, 97, 99, 98, 99,
        99, 100, 98, 99, 99, 99, 99, 99,
        99, 99, 99, 99, 99, 99, 99, 99,
        97, 97, 99, 99, 99, 99, 97, 99,
    ),
    5: _MOZJPEG_LUMINANCE[5],
    6: _MOZJPEG_LUMINANCE[6],
    7: _MOZJPEG_LUMINANCE[7],
    8: _MOZJPEG_LUMINANCE[8],
}  # fmt: skip
"""Tables de chrominance des mêmes jeux (``std_chrominance_quant_tbl``) ; celles des jeux 3 et 5
à 8 sont, dans jcparam.c, des copies de la luminance."""

_MPEG1_INTRA = (
    8, 16, 19, 22, 26, 27, 29, 34,
    16, 16, 22, 24, 27, 29, 34, 37,
    19, 22, 26, 27, 29, 34, 34, 38,
    22, 22, 26, 27, 29, 34, 37, 40,
    22, 26, 27, 29, 32, 35, 40, 48,
    26, 27, 29, 32, 35, 40, 48, 58,
    26, 27, 29, 34, 38, 46, 56, 69,
    27, 29, 35, 38, 46, 56, 69, 83,
)  # fmt: skip
"""Matrice intra par défaut de MPEG-1 (``ff_mpeg1_default_intra_matrix``, mpeg12data.c de FFmpeg
7.1), que l'encodeur MJPEG de ffmpeg met à l'échelle, dans l'ordre du bloc."""

Tables = dict[int, tuple[bool, tuple[int, ...]]]
"""Tables de quantification par identifiant : précision (seize bits ou non) et 64 valeurs dans
l'ordre du segment DQT."""


def _table_ijg(base: tuple[int, ...], qualite: int, seize_bits: bool) -> tuple[int, ...]:
    """Table que libjpeg ou mozjpeg écrit à cette qualité, dans l'ordre du segment DQT.

    ``jpeg_quality_scaling`` puis ``jpeg_add_quant_table`` (jcparam.c) : facteur 5000 / q sous
    50, 200 - 2q au-delà ; arrondi, borné à 1 et 32 767, et à 255 pour une table de huit bits.
    """
    facteur = 5000 // qualite if qualite < 50 else 200 - 2 * qualite
    plafond = 32767 if seize_bits else 255
    return tuple(min(max((base[i] * facteur + 50) // 100, 1), plafond) for i in _ZIGZAG)


def _table_ffmpeg(qscale: int) -> tuple[int, ...]:
    """Table que l'encodeur MJPEG de ffmpeg écrit à ce qscale, dans l'ordre du segment DQT.

    ``encode_picture`` (mpegvideo_enc.c) : coefficient continu à 8, les autres à
    ``(matrice * qscale) >> 3`` bornés à 255 ; ffmpeg écrit toujours des tables de huit bits.
    """
    return (8, *(min((_MPEG1_INTRA[i] * qscale) >> 3, 255) for i in _ZIGZAG[1:]))


_QUALITES = {
    (seize_bits, _table_ijg(_LUMINANCE, qualite, seize_bits)): qualite
    for seize_bits in (False, True)
    for qualite in range(100, 0, -1)
}
"""Qualité de chaque table de luminance de libjpeg ; une qualité par table (vérifié par les
tests)."""


def _qualites_chrominance() -> dict[tuple[bool, tuple[int, ...]], tuple[int, ...]]:
    qualites: dict[tuple[bool, tuple[int, ...]], tuple[int, ...]] = {}
    for seize_bits in (False, True):
        for qualite in range(1, 101):
            cle = (seize_bits, _table_ijg(_CHROMINANCE, qualite, seize_bits))
            qualites[cle] = (*qualites.get(cle, ()), qualite)
    return qualites


_QUALITES_CHROMINANCE = _qualites_chrominance()
"""Qualités de chaque table de chrominance de libjpeg ; en huit bits, les qualités 1 à 3 donnent la
même table (vérifié par les tests)."""


def _jeux_mozjpeg() -> dict[tuple[bool, tuple[int, ...]], tuple[int, int]]:
    """Jeu et qualité de chaque table de luminance de mozjpeg qui n'est pas aussi de libjpeg.

    Une table qu'écrivent deux couples (jeu, qualité) n'est pas retenue ; seules les tables
    dégénérées (toutes à 1 ou toutes à 255) le sont, et libjpeg les écrit aussi (vérifié par les
    tests).
    """
    couples: dict[tuple[bool, tuple[int, ...]], set[tuple[int, int]]] = {}
    for jeu, base in _MOZJPEG_LUMINANCE.items():
        for seize_bits in (False, True):
            for qualite in range(1, 101):
                cle = (seize_bits, _table_ijg(base, qualite, seize_bits))
                couples.setdefault(cle, set()).add((jeu, qualite))
    return {
        cle: next(iter(trouves))
        for cle, trouves in couples.items()
        if len(trouves) == 1 and cle not in _QUALITES
    }


_JEUX_MOZJPEG = _jeux_mozjpeg()

_QSCALES_FFMPEG = {_table_ffmpeg(qscale): qscale for qscale in range(1, 32)}
"""qscale de chaque table de ffmpeg, de 1 à 31 (``qmax`` par défaut) ; un qscale par table."""


def qualite_ijg(tables: Tables) -> int | None:
    """Qualité libjpeg dont viennent ces tables, ou ``None``.

    Les tables doivent être la luminance (0) et, s'il y en a une, la chrominance (1) de la même
    qualité ; aucune autre.
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


def qualites_ijg(tables: Tables) -> tuple[int, int] | None:
    """Qualités libjpeg de la luminance et de la chrominance, si elles diffèrent, ou ``None``.

    ``cjpeg -quality 90,70`` et ``q_scale_factor`` de l'interface de libjpeg 7 et suivantes. La
    qualité de la chrominance doit être unique : en huit bits, les qualités 1 à 3 ne le sont pas.
    """
    if tables.keys() != {0, 1}:
        return None
    luminance = _QUALITES.get(tables[0])
    chrominance = _QUALITES_CHROMINANCE.get(tables[1], ())
    if luminance is None or luminance in chrominance or len(chrominance) != 1:
        return None
    return luminance, chrominance[0]


def jeu_mozjpeg(tables: Tables) -> tuple[int, int] | None:
    """Jeu de mozjpeg (2 à 8) et qualité dont viennent ces tables, ou ``None``.

    Comme pour libjpeg : la luminance (0) et, s'il y en a une, la chrominance (1) du même jeu à
    la même qualité.
    """
    if 0 not in tables or not tables.keys() <= {0, 1}:
        return None
    trouve = _JEUX_MOZJPEG.get(tables[0])
    if trouve is None:
        return None
    if 1 in tables:
        jeu, qualite = trouve
        seize_bits, valeurs = tables[1]
        if valeurs != _table_ijg(_MOZJPEG_CHROMINANCE[jeu], qualite, seize_bits):
            return None
    return trouve


def qscale_ffmpeg(tables: Tables) -> int | None:
    """qscale de l'encodeur MJPEG de ffmpeg dont viennent ces tables, ou ``None``.

    ffmpeg écrit une table, ou deux tables égales (``force_duplicated_matrix``), toujours en huit
    bits.
    """
    if 0 not in tables or not tables.keys() <= {0, 1}:
        return None
    seize_bits, valeurs = tables[0]
    if seize_bits or (1 in tables and tables[1] != tables[0]):
        return None
    return _QSCALES_FFMPEG.get(valeurs)


def encodeur(tables: Tables) -> dict[str, int]:
    """Observations de l'encodeur connu dont viennent ces tables, vide si aucun (ADR-0183).

    Les encodeurs sont essayés dans l'ordre libjpeg, libjpeg à deux qualités, mozjpeg, ffmpeg ; le
    premier reconnu est seul observé.
    """
    if (qualite := qualite_ijg(tables)) is not None:
        return {"image.jpeg.qualite_ijg": qualite}
    if (qualites := qualites_ijg(tables)) is not None:
        return {
            "image.jpeg.qualite_ijg_luminance": qualites[0],
            "image.jpeg.qualite_ijg_chrominance": qualites[1],
        }
    if (mozjpeg := jeu_mozjpeg(tables)) is not None:
        return {"image.jpeg.jeu_mozjpeg": mozjpeg[0], "image.jpeg.qualite_mozjpeg": mozjpeg[1]}
    if (qscale := qscale_ffmpeg(tables)) is not None:
        return {"image.jpeg.qscale_ffmpeg": qscale}
    return {}


def empreinte_tables(tables: Tables) -> str:
    """SHA-256, en hexadécimal minuscule, de l'écriture canonique des tables (ADR-0181).

    Une ligne par table, dans l'ordre des identifiants : l'identifiant, deux-points, puis les 64
    valeurs dans l'ordre du segment DQT, en décimal, séparées par des virgules ; lignes séparées
    par un saut de ligne, sans saut final, en ASCII. La précision n'en fait pas partie.
    """
    lignes = (
        f"{identifiant}:{','.join(map(str, tables[identifiant][1]))}"
        for identifiant in sorted(tables)
    )
    return hashlib.sha256("\n".join(lignes).encode("ascii")).hexdigest()


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
    tables: Tables = {}
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
    contexte.observer(
        "image.jpeg.empreinte_tables", empreinte_tables(tables), localisation=localisation
    )
    for nom, valeur in encodeur(tables).items():
        contexte.observer(nom, valeur, localisation=localisation)
