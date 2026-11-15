"""Double compression JPEG (T41, F-31, ADR-0185 à ADR-0190).

Deux parties : le décodage entropique (``modules/_lecture/jpeg.py``), éprouvé par un aller-retour
avec l'encodeur des tests et par les transcodages sans perte de jpegtran ; puis l'estimation du
module ``doublejpeg`` et sa règle, sur les échantillons de ``tests/donnees/doublejpeg`` (écrits par
cjpeg, ``generer.sh``). djpeg et jpegtran servent d'oracle, ignorés s'ils manquent.
"""

import math
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from encodeur_jpeg import (
    ALTERNATIFS,
    CONTINUS,
    Composante,
    blocs_nuls,
    comptes_alternatifs,
    comptes_continus,
    dht,
    dqt,
    encoder,
    segment,
)
from hypothesis import given, settings
from hypothesis import strategies as st
from metadonnees import contexte, raisons, resultats, valeurs_de
from test_signatures import CATALOGUE, constats

from voight_kampff._orchestration import travail
from voight_kampff._regles import Application
from voight_kampff._travail import garde
from voight_kampff.analyse import analyser
from voight_kampff.cli import resume
from voight_kampff.modules import doublejpeg
from voight_kampff.modules._lecture import jpeg
from voight_kampff.rapport._presentation import texte as texte_du_rapport
from voight_kampff.rapport.modele import (
    Categorie,
    Direction,
    Fondement,
    Niveau,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("F-31")

ECHANTILLONS = Path(__file__).parent / "donnees" / "doublejpeg"
REGLES = tuple(regle for regle in CATALOGUE.regles if regle.module == "doublejpeg")
TABLE = tuple(range(1, 65))
"""Table de quantification des JPEG construits : toutes ses valeurs diffèrent."""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def echantillon(nom: str) -> bytes:
    return (ECHANTILLONS / f"{nom}.jpg").read_bytes()


def lire(contenu: bytes) -> jpeg.Lecture:
    with tempfile.TemporaryFile() as fichier:
        return jpeg.lire(contexte(fichier, contenu, "jpeg", "doublejpeg"))


def coefficients(contenu: bytes) -> jpeg.Coefficients:
    lecture = lire(contenu)
    assert lecture.coefficients is not None, lecture
    return lecture.coefficients


def blocs_de(c: jpeg.Coefficients) -> list[list[int]]:
    return [list(c.valeurs[i : i + 64]) for i in range(0, len(c.valeurs), 64)]


# Décodage : aller-retour avec l'encodeur des tests


@st.composite
def images(draw: st.DrawFn) -> tuple[bytes, list[list[int]], int, int]:
    """JPEG séquentiel construit, et les blocs attendus de la première composante."""
    largeur = draw(st.integers(1, 40))
    hauteur = draw(st.integers(1, 40))
    facteurs = draw(st.sampled_from(((1, 1), (2, 1), (1, 2), (2, 2))))
    composantes = (
        [Composante(1)]
        if draw(st.booleans())
        else [Composante(1, *facteurs), Composante(2, table=1), Composante(3, table=1)]
    )
    blocs = blocs_nuls(composantes, largeur, hauteur)
    coefficient = st.integers(-1023, 1023) | st.just(0)
    for blocs_composante in blocs:
        for bloc in blocs_composante:
            bloc[0] = draw(st.integers(-1000, 1000))
            for _ in range(draw(st.integers(0, 4))):
                bloc[draw(st.integers(1, 63))] = draw(coefficient)
    intervalle = draw(st.integers(0, 3))
    contenu = encoder(
        largeur, hauteur, composantes, blocs, {0: TABLE, 1: TABLE}, intervalle=intervalle
    )
    premiere = composantes[0]
    hmax = max(c.horizontal for c in composantes)
    colonnes = math.ceil(math.ceil(largeur * premiere.horizontal / hmax) / 8)
    vmax = max(c.vertical for c in composantes)
    lignes = math.ceil(math.ceil(hauteur * premiere.vertical / vmax) / 8)
    par_ligne = (
        colonnes if len(composantes) == 1 else math.ceil(largeur / (8 * hmax)) * premiere.horizontal
    )
    attendus = [
        blocs[0][ligne * par_ligne + colonne]
        for ligne in range(lignes)
        for colonne in range(colonnes)
    ]
    return contenu, attendus, colonnes, lignes


@settings(max_examples=150)
@given(images())
def test_aller_retour_sequentiel(image: tuple[bytes, list[list[int]], int, int]) -> None:
    contenu, attendus, colonnes, lignes = image
    c = coefficients(contenu)
    assert (c.procede, c.colonnes, c.lignes, c.blocs_image) == (
        "sequentiel",
        colonnes,
        lignes,
        colonnes * lignes,
    )
    assert blocs_de(c) == attendus
    assert c.table == TABLE
    assert c.precision_table is False


def test_codes_des_tables_de_l_encodeur() -> None:
    # Les tables de l'encodeur des tests sont des codes complets au sens de Kraft, ou presque.
    assert sum(comptes_continus()) == len(CONTINUS)
    assert sum(comptes_alternatifs()) == len(ALTERNATIFS) == 162
    assert sum(n / 2 ** (i + 1) for i, n in enumerate(comptes_alternatifs())) <= 1


def test_sof1_et_table_de_seize_bits() -> None:
    blocs = blocs_nuls([Composante(1)], 16, 8)
    blocs[0][1][5] = -7
    table = (300, *range(2, 65))
    c = coefficients(encoder(16, 8, [Composante(1)], blocs, {0: table}, marqueur_sof=0xC1))
    assert c.precision_table is True
    assert c.table == table
    assert blocs_de(c)[1][5] == -7


def test_tables_redefinies_apres_le_balayage_ignorees() -> None:
    # Les tables en vigueur sont celles du premier balayage de la composante, comme pour T40.
    blocs = blocs_nuls([Composante(1)], 8, 8)
    contenu = encoder(8, 8, [Composante(1)], blocs, {0: TABLE})
    contenu = contenu[:-2] + dqt(0, (9,) * 64) + b"\xff\xd9"
    assert coefficients(contenu).table == TABLE


# Décodage : transcodages sans perte (jpegtran) et sous-échantillonnage


@pytest.mark.parametrize("variante", ["double_60_90_progressif", "double_60_90_redemarrage"])
def test_memes_coefficients_que_le_sequentiel(variante: str) -> None:
    # jpegtran réécrit le balayage sans toucher aux coefficients (generer.sh).
    reference = coefficients(echantillon("double_60_90"))
    autre = coefficients(echantillon(variante))
    assert autre.valeurs == reference.valeurs
    assert (autre.lignes, autre.colonnes, autre.table) == (
        reference.lignes,
        reference.colonnes,
        reference.table,
    )
    assert autre.procede == ("progressif" if "progressif" in variante else "sequentiel")


def test_echantillons_de_l_image_entiere() -> None:
    # 384 sur 256 pixels : 48 sur 32 blocs de luminance, tous dans la région ; 4:2:0 par défaut.
    for nom in ("simple_75", "double_60_90_gris_progressif", "simple_75_444_progressif"):
        c = coefficients(echantillon(nom))
        assert (c.colonnes, c.lignes, c.blocs_image) == (48, 32, 48 * 32), nom
        assert (c.largeur, c.hauteur, c.largeur_composante, c.hauteur_region) == (
            384,
            256,
            384,
            256,
        )


DJPEG = shutil.which("djpeg")
JPEGTRAN = shutil.which("jpegtran")


@pytest.mark.skipif(JPEGTRAN is None, reason="jpegtran absent")
@pytest.mark.parametrize(
    "options",
    [["-progressive"], ["-progressive", "-restart", "1B"], ["-optimize"], ["-restart", "2"]],
)
def test_oracle_jpegtran(options: list[str]) -> None:
    # Coefficients d'un JPEG de l'encodeur des tests, transcodé sans perte par jpegtran.
    composantes = [Composante(1, 2, 2), Composante(2, table=1), Composante(3, table=1)]
    blocs = blocs_nuls(composantes, 40, 24)
    for rang, bloc in enumerate(blocs[0]):
        bloc[0] = rang * 7 - 60
        bloc[rang % 63 + 1] = (-1) ** rang * (rang + 3)
        bloc[63] = 2
    contenu = encoder(40, 24, composantes, blocs, {0: TABLE, 1: TABLE})
    assert JPEGTRAN is not None
    transcode = subprocess.run(
        [JPEGTRAN, *options], input=contenu, capture_output=True, check=True
    ).stdout
    assert coefficients(transcode).valeurs == coefficients(contenu).valeurs


@pytest.mark.skipif(DJPEG is None, reason="djpeg absent")
@pytest.mark.parametrize(
    "nom", ["simple_75", "double_60_90_progressif", "double_60_90_gris_progressif"]
)
def test_oracle_djpeg_luminance(nom: str) -> None:
    # La luminance recalculée en entiers ne s'écarte de celle de djpeg (IDCT en flottants,
    # luminance seule) que d'un niveau au plus, par l'arrondi.
    assert DJPEG is not None
    sortie = subprocess.run(
        [DJPEG, "-grayscale", "-dct", "float", "-pnm"],
        input=echantillon(nom),
        capture_output=True,
        check=True,
    ).stdout
    entete, largeur_hauteur, _, pixels = sortie.split(b"\n", 3)
    assert entete == b"P5"
    largeur, hauteur = map(int, largeur_hauteur.split())
    reference = np.frombuffer(pixels, dtype=np.uint8).reshape(hauteur, largeur)
    image = doublejpeg.luminance(coefficients(echantillon(nom)))
    ecart = np.abs(image - reference.astype(np.int64))
    assert int(ecart.max()) <= 1
    assert float(np.mean(ecart > 0)) < 0.05


# Décodage : région et limites


def test_region_limitee_par_les_blocs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jpeg, "BLOCS_REGION", 12)
    blocs = blocs_nuls([Composante(1)], 40, 40)
    for rang, bloc in enumerate(blocs[0]):
        bloc[0] = rang
    c = coefficients(encoder(40, 40, [Composante(1)], blocs, {0: TABLE}))
    # 5 blocs par ligne : 2 lignes dans 12 blocs.
    assert (c.colonnes, c.lignes, c.blocs_image, c.hauteur_region) == (5, 2, 25, 16)
    assert [bloc[0] for bloc in blocs_de(c)] == list(range(10))


def test_region_entrelacee_en_lignes_de_mcu(monkeypatch: pytest.MonkeyPatch) -> None:
    # 4:2:0 : deux lignes de blocs de luminance par MCU ; 5 lignes dans la région, donc trois
    # lignes de MCU décodées et la sixième ligne de blocs oubliée.
    monkeypatch.setattr(jpeg, "BLOCS_REGION", 25)
    composantes = [Composante(1, 2, 2), Composante(2, table=1), Composante(3, table=1)]
    blocs = blocs_nuls(composantes, 40, 64)
    for rang, bloc in enumerate(blocs[0]):
        bloc[0] = rang
    c = coefficients(encoder(40, 64, composantes, blocs, {0: TABLE, 1: TABLE}))
    assert (c.colonnes, c.lignes, c.hauteur_region) == (5, 5, 40)
    # Grille des MCU : 3 colonnes de MCU, 6 blocs par ligne, dont 5 recouvrent la composante.
    assert [bloc[0] for bloc in blocs_de(c)] == [
        ligne * 6 + colonne for ligne in range(5) for colonne in range(5)
    ]


def test_region_reduite_par_les_visites(monkeypatch: pytest.MonkeyPatch) -> None:
    # 3 blocs décodés par bloc de luminance (4:4:4) : 8 lignes de 5 blocs en coûteraient 120.
    monkeypatch.setattr(jpeg, "VISITES_MAX", 50)
    composantes = [Composante(1), Composante(2, table=1), Composante(3, table=1)]
    blocs = blocs_nuls(composantes, 40, 64)
    c = coefficients(encoder(40, 64, composantes, blocs, {0: TABLE, 1: TABLE}))
    assert c.lignes * c.colonnes * 3 <= 50
    assert c.lignes >= 1


def test_trop_de_visites_meme_pour_une_ligne(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jpeg, "VISITES_MAX", 10)
    composantes = [Composante(1), Composante(2, table=1), Composante(3, table=1)]
    blocs = blocs_nuls(composantes, 40, 16)
    lecture = lire(encoder(40, 16, composantes, blocs, {0: TABLE, 1: TABLE}))
    assert lecture.arret is RaisonNonMenee.FORMAT_PARTIEL


def test_petite_image_entrelacee() -> None:
    # Une ligne de blocs de luminance pour un facteur vertical de 2 : la MCU est décodée entière.
    composantes = [Composante(1, 1, 2), Composante(2, table=1), Composante(3, table=1)]
    blocs = blocs_nuls(composantes, 8, 4)
    blocs[0][0][0] = 5
    c = coefficients(encoder(8, 4, composantes, blocs, {0: TABLE, 1: TABLE}))
    assert (c.colonnes, c.lignes, blocs_de(c)[0][0]) == (1, 1, 5)


# Décodage : JPEG non lus ou malformés


def _base(**options: Any) -> bytes:
    blocs = blocs_nuls([Composante(1)], 16, 8)
    blocs[0][0][0] = 3
    return encoder(16, 8, [Composante(1)], blocs, {0: TABLE}, **options)


def _sof(*composantes: tuple[int, int, int], precision: int = 8, hauteur: int = 8) -> bytes:
    return struct.pack(">BHHB", precision, hauteur, 16, len(composantes)) + b"".join(
        bytes(c) for c in composantes
    )


def _remplacer(contenu: bytes, ancien: bytes, nouveau: bytes) -> bytes:
    assert contenu.count(ancien) == 1
    return contenu.replace(ancien, nouveau)


SOS = segment(0xDA, bytes([1, 1, 0x00, 0, 63, 0]))
SOF0 = segment(0xC0, _sof((1, 0x11, 0)))


def _cas_malformes() -> list[Any]:
    base = _base()
    entete, entropie = base.split(SOS)
    cas = [
        ("fin avant tout segment", b"\xff\xd8", RaisonNonMenee.FICHIER_TRONQUE),
        ("octet hors marqueur", b"\xff\xd8\x00\x00", RaisonNonMenee.FORMAT_PARTIEL),
        ("marqueur coupé", b"\xff\xd8\xff\xe0\x00", RaisonNonMenee.FICHIER_TRONQUE),
        ("second SOI", b"\xff\xd8\xff\xd8" + base[2:], RaisonNonMenee.FORMAT_PARTIEL),
        ("marqueur nul", b"\xff\xd8\xff\x00\x00\x04", RaisonNonMenee.FORMAT_PARTIEL),
        ("longueur trop courte", b"\xff\xd8\xff\xe0\x00\x01", RaisonNonMenee.FORMAT_PARTIEL),
        ("segment hors du fichier", b"\xff\xd8\xff\xe0\x00\x10ab", RaisonNonMenee.FICHIER_TRONQUE),
        ("sans balayage", entete + b"\xff\xd9", RaisonNonMenee.FORMAT_PARTIEL),
        (
            "procédé sans perte",
            _remplacer(base, b"\xff\xc0", b"\xff\xc3"),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "codage arithmétique",
            _remplacer(base, b"\xff\xc0", b"\xff\xc9"),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "douze bits",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x11, 0), precision=12))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "hauteur par DNL",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x11, 0), hauteur=0))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "SOF court",
            _remplacer(base, SOF0, segment(0xC0, b"\x08\x00")),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "SOF sans ses composantes",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x11, 0))[:-1])),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "facteur nul",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x01, 0)))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "table de composante invalide",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x11, 4)))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "composante en double",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x11, 0), (1, 0x11, 0)))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        ("second SOF", _remplacer(base, SOF0, SOF0 + SOF0), RaisonNonMenee.FORMAT_PARTIEL),
        (
            "DQT de précision invalide",
            _remplacer(base, b"\xff\xdb\x00\x43\x00", b"\xff\xdb\x00\x43\x20"),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "DQT coupé",
            _remplacer(base, dqt(0, TABLE), segment(0xDB, b"\x00" + bytes(TABLE[:10]))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "pas nul",
            _remplacer(base, dqt(0, TABLE), dqt(0, (0, *TABLE[1:]))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "DHT de classe invalide",
            _remplacer(
                base,
                dht(0, 0, comptes_continus(), CONTINUS),
                dht(2, 0, comptes_continus(), CONTINUS),
            ),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "DHT coupé",
            _remplacer(
                base,
                dht(0, 0, comptes_continus(), CONTINUS),
                segment(0xC4, b"\x00" + comptes_continus() + b"\x00"),
            ),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "code de Huffman impossible",
            _remplacer(
                base,
                dht(0, 0, comptes_continus(), CONTINUS),
                dht(0, 0, bytes([3] + [0] * 15), (0, 1, 2)),
            ),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "DRI court",
            _remplacer(base, SOS, segment(0xDD, b"\x00") + SOS),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        ("SOS avant SOF", b"\xff\xd8" + SOS + entropie, RaisonNonMenee.FORMAT_PARTIEL),
        ("SOS vide", _remplacer(base, SOS, segment(0xDA, b"")), RaisonNonMenee.FORMAT_PARTIEL),
        (
            "SOS de zéro composante",
            _remplacer(base, SOS, segment(0xDA, bytes([0, 0, 63, 0]))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "SOS d'une composante inconnue",
            _remplacer(base, SOS, segment(0xDA, bytes([1, 9, 0, 0, 63, 0]))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "séquentiel à bande partielle",
            _remplacer(base, SOS, segment(0xDA, bytes([1, 1, 0, 0, 5, 0]))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "table de Huffman absente",
            _remplacer(base, SOS, segment(0xDA, bytes([1, 1, 0x11, 0, 63, 0]))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        (
            "table de quantification absente",
            _remplacer(base, SOF0, segment(0xC0, _sof((1, 0x11, 2)))),
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
        ("données coupées", base[: len(entete) + len(SOS) + 1], RaisonNonMenee.FICHIER_TRONQUE),
        (
            "données vides avant un marqueur",
            entete + SOS + b"\xff\xd9",
            RaisonNonMenee.FORMAT_PARTIEL,
        ),
    ]
    return [pytest.param(contenu, raison, id=nom) for nom, contenu, raison in cas]


@pytest.mark.exigence("ES-19")
@pytest.mark.parametrize(("contenu", "raison"), _cas_malformes())
def test_jpeg_non_lu(contenu: bytes, raison: RaisonNonMenee) -> None:
    lecture = lire(contenu)
    assert (lecture.coefficients, lecture.arret) == (None, raison)
    assert lecture.localisation_arret().octets is not None


def test_eoi_manquant_tolere() -> None:
    assert lire(_base()[:-2]).coefficients is not None


def test_remplissage_et_marqueurs_sans_longueur() -> None:
    # Octets 0xFF de remplissage avant un marqueur, marqueur TEM : sautés.
    contenu = _remplacer(_base(), SOS, b"\xff\xff\xff\x01" + SOS)
    assert lire(contenu).coefficients is not None


def test_balayage_d_une_autre_composante_saute() -> None:
    # Un balayage qui ne porte pas la première composante n'est pas décodé, même illisible.
    composantes = [Composante(1), Composante(2, table=1), Composante(3, table=1)]
    blocs = blocs_nuls(composantes, 8, 8)
    contenu = encoder(8, 8, composantes, blocs, {0: TABLE, 1: TABLE})
    autre = segment(0xDA, bytes([1, 2, 0x33, 0, 63, 0])) + b"\x12\x34"
    assert lire(contenu[:-2] + autre + b"\xff\xd9").coefficients is not None


def test_trop_de_balayages() -> None:
    entete, entropie = _base().split(SOS)
    contenu = entete + (SOS + entropie[:-2]) * (jpeg.BALAYAGES_MAX + 1) + b"\xff\xd9"
    assert lire(contenu).arret is RaisonNonMenee.FORMAT_PARTIEL


def test_trop_de_tables_de_huffman() -> None:
    table = dht(0, 1, comptes_continus(), CONTINUS)
    contenu = _remplacer(_base(), SOS, table * (256) + SOS)
    assert lire(contenu).arret is RaisonNonMenee.FORMAT_PARTIEL


def test_trop_de_blocs_par_mcu() -> None:
    sof = _sof((1, 0x22, 0), (2, 0x22, 0), (3, 0x22, 0))
    sos = segment(0xDA, bytes([3, 1, 0, 2, 0, 3, 0, 0, 63, 0]))
    contenu = _remplacer(_remplacer(_base(), SOF0, segment(0xC0, sof)), SOS, sos)
    assert lire(contenu).arret is RaisonNonMenee.FORMAT_PARTIEL


def test_composantes_du_balayage_hors_d_ordre() -> None:
    sof = _sof((1, 0x11, 0), (2, 0x11, 0))
    sos = segment(0xDA, bytes([2, 2, 0, 1, 0, 0, 63, 0]))
    contenu = _remplacer(_remplacer(_base(), SOF0, segment(0xC0, sof)), SOS, sos)
    assert lire(contenu).arret is RaisonNonMenee.FORMAT_PARTIEL


@pytest.mark.parametrize(
    ("ss", "se", "ahal", "nombre"),
    [
        pytest.param(0, 5, 0x00, 1, id="continu-et-alternatif"),
        pytest.param(5, 2, 0x00, 1, id="bande-inversee"),
        pytest.param(1, 5, 0x00, 2, id="alternatif-entrelace"),
        pytest.param(1, 5, 0x31, 1, id="raffinement-de-deux-bits"),
        pytest.param(1, 5, 0x0E, 1, id="al-de-14"),
    ],
)
def test_balayage_progressif_invalide(ss: int, se: int, ahal: int, nombre: int) -> None:
    sof = _sof((1, 0x11, 0), (2, 0x11, 0))
    composantes = bytes([1, 0]) + (bytes([2, 0]) if nombre == 2 else b"")
    sos = segment(0xDA, bytes([nombre]) + composantes + bytes([ss, se, ahal]))
    contenu = _remplacer(_remplacer(_base(), SOF0, segment(0xC2, sof)), SOS, sos)
    assert lire(contenu).arret is RaisonNonMenee.FORMAT_PARTIEL


def _entropie_remplacee(contenu: bytes, donnees: bytes) -> bytes:
    entete, _ = contenu.split(SOS)
    return entete + SOS + donnees + b"\xff\xd9"


@pytest.mark.parametrize(
    "donnees",
    [
        # Code continu absent de la table (les codes de 4 bits vont de 0000 à 1011).
        pytest.param(b"\xf0\x00", id="code-continu-absent"),
        # Taille 1 (0001), bit 1, puis fin de bloc absente : 111111111 n'est pas un code.
        pytest.param(b"\x1f\xff\x00\xff\x00", id="code-alternatif-absent"),
    ],
)
def test_code_invalide(donnees: bytes) -> None:
    assert lire(_entropie_remplacee(_base(), donnees)).arret is RaisonNonMenee.FORMAT_PARTIEL


def test_taille_continue_au_dela_de_11() -> None:
    table = dht(0, 0, bytes([0, 0, 0, 13] + [0] * 12), list(range(13)))
    contenu = _remplacer(_base(), dht(0, 0, comptes_continus(), CONTINUS), table)
    # Code 1100 : taille 12.
    assert lire(_entropie_remplacee(contenu, b"\xc0\x00")).arret is RaisonNonMenee.FORMAT_PARTIEL


def test_coefficient_au_dela_du_bloc() -> None:
    # Continu nul (0000), puis 15 zéros et une valeur (0xF1) quatre fois : rang 64.
    alternatif = {s: (code, longueur) for s, code, longueur in _codes_alternatifs()}
    bits = "0000" + "".join(
        format(alternatif[0xF1][0], f"0{alternatif[0xF1][1]}b") + "1" for _ in range(4)
    )
    donnees = _octets(bits)
    assert lire(_entropie_remplacee(_base(), donnees)).arret is RaisonNonMenee.FORMAT_PARTIEL


def _codes_alternatifs() -> list[tuple[int, int, int]]:
    from encodeur_jpeg import codes

    return [(s, *codes(comptes_alternatifs(), ALTERNATIFS)[s]) for s in ALTERNATIFS]


def _octets(bits: str) -> bytes:
    bits += "1" * (-len(bits) % 8)
    octets = bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))
    return octets.replace(b"\xff", b"\xff\x00")


def test_intervalles_manquants() -> None:
    # Intervalle de redémarrage d'une MCU, deux MCU, un seul intervalle dans les données.
    contenu = _base(intervalle=1)
    entete, entropie = contenu.split(SOS)
    premier = entropie.split(b"\xff\xd0")[0]
    assert lire(entete + SOS + premier + b"\xff\xd9").arret is RaisonNonMenee.FORMAT_PARTIEL


def test_borne_des_lectures() -> None:
    # Les données entropiques sont lues jusqu'à une borne : 420 octets par bloc au plus.
    assert math.ceil((27 + 63 * 26) / 8) * 2 <= jpeg._OCTETS_PAR_BLOC


# Décodage : JPEG progressifs construits par jpegtran à partir de scripts de balayages


@pytest.mark.skipif(JPEGTRAN is None, reason="jpegtran absent")
def test_oracle_jpegtran_script_de_balayages(tmp_path: Path) -> None:
    # Bandes étroites et raffinements de plusieurs bits : fins de bande en série, seize zéros.
    script = tmp_path / "balayages.txt"
    script.write_text(
        "0,1,2: 0-0, 0, 2;\n0: 1-2, 0, 2;\n0: 3-63, 0, 2;\n1: 1-63, 0, 0;\n2: 1-63, 0, 0;\n"
        "0: 1-63, 2, 1;\n0,1,2: 0-0, 2, 1;\n0: 1-63, 1, 0;\n0,1,2: 0-0, 1, 0;\n",
        encoding="ascii",
    )
    assert JPEGTRAN is not None
    contenu = echantillon("simple_90")
    transcode = subprocess.run(
        [JPEGTRAN, "-scans", str(script)], input=contenu, capture_output=True, check=True
    ).stdout
    assert coefficients(transcode).valeurs == coefficients(contenu).valeurs


# Estimation


def test_cosinus_ecrits_en_entiers() -> None:
    for u in range(8):
        echelle = math.sqrt(1 / 8) if u == 0 else 0.5
        for x in range(8):
            attendu = round(echelle * math.cos((2 * x + 1) * u * math.pi / 16) * 4096)
            assert doublejpeg._COSINUS[8 * u + x] == attendu


def test_arrondi_la_moitie_loin_de_zero() -> None:
    valeurs = np.array([-15, -14, -5, -4, 0, 4, 5, 14, 15], dtype=np.int64)
    assert doublejpeg._arrondir(valeurs, 10).tolist() == [-2, -1, -1, 0, 0, 0, 1, 1, 2]


def test_borne_des_histogrammes() -> None:
    assert doublejpeg._borne(np.zeros(100, dtype=np.int64)) == 8
    assert doublejpeg._borne(np.full(100, 500, dtype=np.int64)) == 128
    assert doublejpeg._borne(np.array([20] * 996 + [0] * 4, dtype=np.int64)) == 20


def test_ecart_d_un_histogramme_vide() -> None:
    assert doublejpeg._ecart([1, 2], [0, 0]) is None


def test_qualites_ijg() -> None:
    table = doublejpeg._table_ijg(60)
    rangs = list(range(1, 10))
    assert doublejpeg.qualites_ijg(rangs, [table[r] for r in rangs]) == [60]
    assert doublejpeg.qualites_ijg([1], [255]) == [1, 2]  # 11 fois 50 et 25, bornés à 255
    assert doublejpeg.qualites_ijg([1, 2], [3, 200]) == []


@pytest.mark.parametrize(
    ("nom", "qualite"),
    [
        ("double_60_90", 60),
        ("double_60_90_progressif", 60),
        ("double_60_90_redemarrage", 60),
        ("double_60_90_gris_progressif", 60),
        ("double_50_75", None),
    ],
)
def test_double_compression_relevee(nom: str, qualite: int | None) -> None:
    valeurs = valeurs_de(resultats("doublejpeg", echantillon(nom), "jpeg"))
    assert valeurs["doublejpeg.traces"] >= 4
    assert len(valeurs["doublejpeg.pas_anterieurs"]) == valeurs["doublejpeg.traces"]
    assert valeurs["doublejpeg.frequences_examinees"] == len(valeurs["doublejpeg.frequences"])
    if qualite is None:
        assert "doublejpeg.qualites_ijg_anterieures" not in valeurs
    else:
        assert valeurs["doublejpeg.qualites_ijg_anterieures"] == [qualite]
    # Les pas antérieurs de libjpeg à la qualité 60 : 10 (rang 2), 11 (rang 3), 10 (rang 4)…
    if qualite == 60:
        assert valeurs["doublejpeg.frequences_tracees"][:4] == [2, 3, 4, 5]
        assert valeurs["doublejpeg.pas_anterieurs"][:4] == [10, 11, 10, 8]


@pytest.mark.parametrize("nom", ["simple_75", "simple_90", "simple_75_444_progressif"])
def test_simple_compression_sous_le_seuil(nom: str) -> None:
    valeurs = valeurs_de(resultats("doublejpeg", echantillon(nom), "jpeg"))
    assert valeurs["doublejpeg.frequences_examinees"] >= 8
    assert valeurs["doublejpeg.traces"] <= 2
    assert constats("doublejpeg", echantillon(nom), "jpeg", REGLES) == {}


def test_memes_observations_quel_que_soit_le_balayage() -> None:
    # Mêmes coefficients, même estimation : seul le procédé diffère.
    reference = valeurs_de(resultats("doublejpeg", echantillon("double_60_90"), "jpeg"))
    for nom, procede in (
        ("double_60_90_progressif", "progressif"),
        ("double_60_90_redemarrage", "sequentiel"),
    ):
        valeurs = valeurs_de(resultats("doublejpeg", echantillon(nom), "jpeg"))
        assert valeurs == reference | {"doublejpeg.procede": procede}


def test_image_trop_petite_pour_le_calibrage() -> None:
    blocs = blocs_nuls([Composante(1)], 8, 8)
    valeurs = valeurs_de(
        resultats("doublejpeg", encoder(8, 8, [Composante(1)], blocs, {0: TABLE}), "jpeg")
    )
    assert valeurs == {
        "doublejpeg.procede": "sequentiel",
        "doublejpeg.blocs": 1,
        "doublejpeg.blocs_image": 1,
        "doublejpeg.frequences_examinees": 0,
    }


def test_frequences_sans_assez_de_coefficients() -> None:
    # Une image presque plate : aucune fréquence n'a 256 coefficients non nuls.
    blocs = blocs_nuls([Composante(1)], 64, 64)
    blocs[0][3][1] = 2
    valeurs = valeurs_de(
        resultats("doublejpeg", encoder(64, 64, [Composante(1)], blocs, {0: TABLE}), "jpeg")
    )
    assert valeurs["doublejpeg.frequences_examinees"] == 0
    assert "doublejpeg.traces" not in valeurs


def test_aucune_trace() -> None:
    valeurs = valeurs_de(resultats("doublejpeg", echantillon("simple_90"), "jpeg"))
    assert valeurs["doublejpeg.traces"] == 0
    assert "doublejpeg.frequences_tracees" not in valeurs


def test_jpeg_illisible_non_mene() -> None:
    lignes = resultats("doublejpeg", b"\xff\xd8\xff\xc3\x00\x02\xff\xd9", "jpeg")
    assert raisons(lignes) == ["format_partiel"]
    assert valeurs_de(lignes) == {}


def test_trop_peu_de_traces_pour_une_qualite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doublejpeg, "QUALITE_TRACES_MIN", 100)
    valeurs = valeurs_de(resultats("doublejpeg", echantillon("double_60_90"), "jpeg"))
    assert valeurs["doublejpeg.traces"] >= 4
    assert "doublejpeg.qualites_ijg_anterieures" not in valeurs


# Règle et analyse complète


def test_regle_de_t41() -> None:
    [regle] = REGLES
    assert regle.identifiant == "R-DOUBLEJPEG-001"
    assert regle.application is Application.MOTEUR
    assert (regle.categorie, regle.direction, regle.fondement) == (
        Categorie.INDICE,
        Direction.TRANSFORMATION,
        Fondement.MESURE,
    )
    assert (regle.niveau, regle.evaluation) == (Niveau.FAIBLE, None)
    assert regle.calibrage is not None
    [seuil] = [c.seuil for c in regle.conditions if c.seuil is not None]
    assert (seuil.operateur, seuil.valeur) == (">=", 4)


def test_constat_de_double_compression() -> None:
    trouves = constats("doublejpeg", echantillon("double_60_90"), "jpeg", REGLES)
    [parametres] = trouves.values()
    assert list(trouves) == ["R-DOUBLEJPEG-001"]
    assert parametres["traces"] >= 4
    assert parametres["examinees"] >= parametres["traces"]


def test_analyse_complete(tmp_path: Path) -> None:
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(echantillon("double_60_90_progressif"))
    analyse = analyser(chemin)
    regles = {c.regle.identifiant for c in analyse.constats if c.categorie is Categorie.INDICE}
    assert "R-DOUBLEJPEG-001" in regles
    assert resume(analyse).count(texte_du_rapport("resume.transformation")) == 1
    assert "numpy" in {d.nom for d in analyse.dependances}


def test_un_fil_pour_openblas() -> None:
    assert travail._environnement()["OPENBLAS_NUM_THREADS"] == "1"


# Décodage progressif : balayages écrits bit à bit. Table continue : 12 codes de 4 bits, le
# code d'une taille est la taille elle-même ; table alternative : 255 codes de 8 bits, le code
# d'un symbole est le symbole lui-même (0xFF, absent, est un code invalide).


def _progressif(largeur: int, *balayages: tuple[int, int, int, int, str]) -> bytes:
    """JPEG progressif d'une composante : balayages (Ss, Se, Ah, Al, bits)."""
    contenu = bytearray(b"\xff\xd8" + dqt(0, TABLE))
    contenu += segment(0xC2, struct.pack(">BHHB", 8, 8, largeur, 1) + bytes([1, 0x11, 0]))
    contenu += dht(0, 0, comptes_continus(), CONTINUS)
    contenu += dht(1, 0, bytes([0] * 7 + [255] + [0] * 8), list(range(255)))
    for ss, se, ah, al, bits in balayages:
        contenu += segment(0xDA, bytes([1, 1, 0x00, ss, se, ah << 4 | al]))
        contenu += _octets(bits) if bits else b""
    return bytes(contenu + b"\xff\xd9")


def _s(symbole: int) -> str:
    return format(symbole, "08b")


def test_progressif_fin_de_bande_en_serie() -> None:
    # Cinq blocs. Continu : taille 1, valeur +1, à Al = 1, soit 2. Alternatifs (1-63) : bloc 1,
    # seize zéros (0xF0) puis 1 au rang 17 ; blocs 2 à 5, une série de fins de bande
    # (0x20 : 3 plus 2 bits, ici 1, soit 4 blocs).
    # Différences du continu : +1, puis 0 pour les quatre autres blocs.
    continu = "0001" + "1" + "0000" * 4
    contenu = _progressif(
        40,
        (0, 0, 0, 1, continu),
        (1, 63, 0, 0, _s(0xF0) + _s(0x01) + "1" + _s(0x00) + _s(0x20) + "01"),
    )
    blocs = blocs_de(coefficients(contenu))
    assert [bloc[0] for bloc in blocs] == [2] * 5
    assert blocs[0][17] == 1
    assert all(not any(bloc[1:]) for bloc in blocs[1:])


def test_progressif_raffinement_construit() -> None:
    # Premier passage (Al = 1) : rang 1 à -1, soit -2. Raffinement (Ah = 1, Al = 0), bande
    # 1-63 : symbole 0x11 (un zéro passé, puis nouveau coefficient), signe 1 ; le rang 1, non nul,
    # reçoit d'abord son bit de correction 1 (-2 devient -3) ; puis trois séries de seize zéros
    # (0xF0) et une fin de bande.
    contenu = _progressif(
        8,
        (0, 0, 0, 0, "0000"),
        (1, 63, 0, 1, _s(0x01) + "0" + _s(0x00)),
        (1, 63, 1, 0, _s(0x11) + "1" + "1" + _s(0xF0) * 3 + _s(0x00)),
    )
    [bloc] = blocs_de(coefficients(contenu))
    assert (bloc[1], bloc[2], bloc[3]) == (-3, 0, 1)


@pytest.mark.parametrize(
    "balayage",
    [
        pytest.param((0, 0, 0, 0, "1111"), id="continu-code-absent"),
        pytest.param((0, 0, 0, 0, ""), id="continu-donnees-epuisees"),
        pytest.param((1, 5, 0, 0, _s(0xFF)), id="premier-code-absent"),
        pytest.param((1, 5, 0, 0, _s(0x51) + "1"), id="premier-au-dela-de-la-bande"),
        pytest.param((1, 5, 0, 0, ""), id="premier-donnees-epuisees"),
        pytest.param((1, 5, 1, 0, _s(0xFF)), id="raffinement-code-absent"),
        pytest.param((1, 5, 1, 0, _s(0x51) + "1"), id="raffinement-au-dela-de-la-bande"),
        pytest.param((1, 5, 1, 0, ""), id="raffinement-donnees-epuisees"),
    ],
)
def test_progressif_malforme(balayage: tuple[int, int, int, int, str]) -> None:
    lecture = lire(_progressif(8, balayage))
    assert lecture.arret is RaisonNonMenee.FORMAT_PARTIEL


def test_progressif_seize_zeros_au_bord_de_la_bande() -> None:
    # Raffinement de la bande 1-5 : seize zéros (0xF0) dépassent la bande sans nouveau
    # coefficient, puis fin de bande.
    contenu = _progressif(8, (1, 5, 1, 0, _s(0xF0) + _s(0x00)))
    [bloc] = blocs_de(coefficients(contenu))
    assert not any(bloc)
