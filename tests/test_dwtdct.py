"""Filigrane dwtDct d'invisible-watermark (T32, ADR-0202 à ADR-0206) : lecteur PNG, couleurs d'un
JPEG, composante U, décision par rang, loi des bits concordants, observations et règles."""

import shutil
import struct
import subprocess
import tempfile
import tomllib
import zlib
from array import array
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest
from echantillons import bloc_png
from encodeur_jpeg import Composante, blocs_nuls, segment
from encodeur_jpeg import encoder as encoder_jpeg
from metadonnees import contexte, raisons, resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff._travail.contexte import LimiteDepassee
from voight_kampff.analyse import analyser
from voight_kampff.modules import dwtdct
from voight_kampff.modules._lecture import jpeg, pixels, png
from voight_kampff.modules._lecture.jpeg import Coefficients
from voight_kampff.rapport.modele import RaisonNonMenee

pytestmark = pytest.mark.exigence("F-24")

ECHANTILLONS = Path(__file__).parent / "donnees" / "dwtdct"
SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def echantillon(nom: str) -> bytes:
    return (ECHANTILLONS / nom).read_bytes()


def format_de(nom: str) -> str:
    return "png" if nom.endswith(".png") else "jpeg"


def lire_pixels(contenu: bytes, format_: str, budget: int = dwtdct.PIXELS_MAX) -> pixels.Lecture:
    with tempfile.TemporaryFile() as fichier:
        return pixels.lire(contexte(fichier, contenu, format_, "dwtdct"), pixels=budget)


def rvb_de(contenu: bytes, format_: str) -> npt.NDArray[np.int64]:
    lecture = lire_pixels(contenu, format_)
    assert lecture.pixels is not None
    assert lecture.pixels.rvb is not None
    return lecture.pixels.rvb


# PNG écrits par les tests : filtres appliqués ligne par ligne (ISO/IEC 15948, §9)


def _filtrer(ligne: bytes, precedente: bytes, filtre: int, pas: int) -> bytes:
    sortie = bytearray()
    for i, x in enumerate(ligne):
        a = ligne[i - pas] if i >= pas else 0
        b = precedente[i]
        c = precedente[i - pas] if i >= pas else 0
        if filtre == 0:
            prediction = 0
        elif filtre == 1:
            prediction = a
        elif filtre == 2:
            prediction = b
        elif filtre == 3:
            prediction = (a + b) >> 1
        else:
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            prediction = a if pa <= pb and pa <= pc else b if pb <= pc else c
        sortie.append((x - prediction) & 0xFF)
    return bytes(sortie)


def ecrire_png(
    largeur: int,
    hauteur: int,
    lignes: list[bytes],
    *,
    couleurs: int = 2,
    profondeur: int = 8,
    filtres: list[int] | None = None,
    pas: int = 3,
    palette: bytes | None = None,
    entrelacement: int = 0,
    avant: bytes = b"",
    fin: bytes | None = None,
) -> bytes:
    """PNG dont les ``lignes`` (octets bruts) sont filtrées par ``filtres``, cycliquement."""
    filtres = filtres or [0]
    brut = bytearray()
    precedente = bytes(len(lignes[0]))
    for rang, ligne in enumerate(lignes):
        filtre = filtres[rang % len(filtres)]
        brut += bytes([filtre]) + _filtrer(ligne, precedente, filtre, pas)
        precedente = ligne
    entete = struct.pack(">IIBBBBB", largeur, hauteur, profondeur, couleurs, 0, 0, entrelacement)
    return (
        SIGNATURE
        + bloc_png(b"IHDR", entete)
        + avant
        + (bloc_png(b"PLTE", palette) if palette is not None else b"")
        + bloc_png(b"IDAT", zlib.compress(bytes(brut)))
        + (bloc_png(b"IEND", b"") if fin is None else fin)
    )


def lignes_aleatoires(
    largeur: int, hauteur: int, canaux: int, graine: int = 32, octets: int = 1
) -> list[bytes]:
    rng = np.random.default_rng(graine)
    valeurs = rng.integers(0, 256, size=(hauteur, largeur * canaux * octets), dtype=np.uint8)
    return [ligne.tobytes() for ligne in valeurs]


def png_lu(contenu: bytes, budget: int = 1 << 22) -> png.Lecture:
    with tempfile.TemporaryFile() as fichier:
        return png.lire(contexte(fichier, contenu, "png", "dwtdct"), pixels=budget)


# Lecteur PNG


@pytest.mark.parametrize("filtres", [[0], [1], [2], [3], [4], [0, 1, 2, 3, 4]])
@pytest.mark.parametrize(("couleurs", "canaux"), [(2, 3), (6, 4)])
def test_png_filtres_en_huit_bits(filtres: list[int], couleurs: int, canaux: int) -> None:
    lignes = lignes_aleatoires(7, 6, canaux)
    lecture = png_lu(ecrire_png(7, 6, lignes, couleurs=couleurs, filtres=filtres, pas=canaux))
    assert lecture.image is not None
    assert lecture.image.rvb is not None
    attendu = np.frombuffer(b"".join(lignes), np.uint8).reshape(6, 7, canaux)[:, :, :3]
    assert np.array_equal(lecture.image.rvb, attendu)
    assert (lecture.image.largeur, lecture.image.hauteur, lecture.image.lignes) == (7, 6, 6)


def test_png_seize_bits_garde_l_octet_de_poids_fort() -> None:
    lignes = lignes_aleatoires(5, 4, 3, octets=2)
    lecture = png_lu(ecrire_png(5, 4, lignes, profondeur=16, filtres=[4, 1], pas=6))
    assert lecture.image is not None
    assert lecture.image.rvb is not None
    attendu = np.frombuffer(b"".join(lignes), np.uint8).reshape(4, 5, 3, 2)[:, :, :, 0]
    assert np.array_equal(lecture.image.rvb, attendu)


@pytest.mark.parametrize("profondeur", [1, 2, 4, 8])
def test_png_palette(profondeur: int) -> None:
    largeur, hauteur = 9, 3
    rng = np.random.default_rng(profondeur)
    indices = rng.integers(0, 1 << profondeur, size=(hauteur, largeur))
    lignes = []
    for rangee in indices:
        bits = "".join(format(int(i), f"0{profondeur}b") for i in rangee)
        bits += "0" * (-len(bits) % 8)
        lignes.append(int(bits, 2).to_bytes(len(bits) // 8, "big"))
    couleurs = rng.integers(0, 256, size=(1 << profondeur, 3), dtype=np.uint8)
    contenu = ecrire_png(
        largeur,
        hauteur,
        lignes,
        couleurs=3,
        profondeur=profondeur,
        filtres=[0, 1, 2],
        pas=1,
        palette=couleurs.tobytes(),
    )
    lecture = png_lu(contenu)
    assert lecture.image is not None
    assert lecture.image.rvb is not None
    assert np.array_equal(lecture.image.rvb, couleurs[indices])


@pytest.mark.parametrize("couleurs", [0, 4])
def test_png_en_niveaux_de_gris_sans_decompression(couleurs: int) -> None:
    # Données illisibles : le lecteur ne les décompresse pas.
    entete = struct.pack(">IIBBBBB", 300, 300, 8, couleurs, 0, 0, 0)
    contenu = (
        SIGNATURE
        + bloc_png(b"IHDR", entete)
        + bloc_png(b"IDAT", b"pas du zlib")
        + bloc_png(b"IEND", b"")
    )
    lecture = png_lu(contenu)
    assert lecture.image is not None
    assert lecture.image.rvb is None
    assert lecture.image.lignes == 0


def test_png_premieres_lignes_seulement() -> None:
    lignes = lignes_aleatoires(10, 40, 3)
    # Les lignes au-delà du budget ne sont ni décompressées ni défiltrées : un filtre invalide
    # n'y gêne pas.
    contenu = ecrire_png(10, 40, lignes, filtres=[1] * 39 + [2])
    lecture = png_lu(contenu, budget=105)
    assert lecture.image is not None
    assert lecture.image.lignes == 10
    assert lecture.image.rvb is not None
    assert lecture.image.rvb.shape == (10, 10, 3)


def test_png_iend_manquant_tolere() -> None:
    lignes = lignes_aleatoires(4, 4, 3)
    lecture = png_lu(ecrire_png(4, 4, lignes, fin=b""))
    assert lecture.image is not None


def test_png_crc_non_verifie() -> None:
    contenu = bytearray(ecrire_png(4, 4, lignes_aleatoires(4, 4, 3)))
    contenu[8 + 8 + 13] ^= 0xFF  # CRC de IHDR
    assert png_lu(bytes(contenu)).image is not None


def test_png_bloc_idat_vide_ignore() -> None:
    lignes = lignes_aleatoires(4, 4, 3)
    contenu = ecrire_png(4, 4, lignes, avant=bloc_png(b"IDAT", b""))
    lecture = png_lu(contenu)
    assert lecture.image is not None
    assert lecture.image.rvb is not None
    attendu = np.frombuffer(b"".join(lignes), np.uint8).reshape(4, 4, 3)
    assert np.array_equal(lecture.image.rvb, attendu)


def _ihdr(**champs: int) -> bytes:
    valeurs = {"largeur": 4, "hauteur": 4, "profondeur": 8, "couleurs": 2} | champs
    return struct.pack(
        ">IIBBBBB",
        valeurs["largeur"],
        valeurs["hauteur"],
        valeurs["profondeur"],
        valeurs["couleurs"],
        valeurs.get("compression", 0),
        valeurs.get("filtre", 0),
        valeurs.get("entrelacement", 0),
    )


_IDAT = bloc_png(b"IDAT", zlib.compress(b"\x00" + b"\x00" * 12))
_LIGNES = lignes_aleatoires(4, 4, 3)


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (b"GIF89a" + b"\x00" * 40, "format_partiel"),
        (SIGNATURE + b"\x00\x00", "fichier_tronque"),
        (SIGNATURE + bloc_png(b"IDAT", b"x") + bloc_png(b"IEND", b""), "format_partiel"),
        (SIGNATURE + b"\x80\x00\x00\x00IHDR", "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr()[:12]), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(profondeur=4)), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(couleurs=5)), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(largeur=0)), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(compression=1)), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(filtre=1)), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(entrelacement=2)), "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr(entrelacement=1)) + _IDAT, "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr()) * 2, "format_partiel"),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr()) + bloc_png(b"IEND", b""), "format_partiel"),
        (
            SIGNATURE + bloc_png(b"IHDR", _ihdr()) + bloc_png(b"tEXt", b"a" * 20)[:12],
            "fichier_tronque",
        ),
        (SIGNATURE + bloc_png(b"IHDR", _ihdr()) + b"\x00", "fichier_tronque"),
        (ecrire_png(4, 4, _LIGNES, avant=bloc_png(b"PLTE", b"\x00" * 4)), "format_partiel"),
        (ecrire_png(4, 4, _LIGNES, avant=bloc_png(b"PLTE", b"\x00" * 771)), "format_partiel"),
        (ecrire_png(4, 4, [b"\x00\x00"] * 4, couleurs=3, pas=1), "format_partiel"),
        (
            ecrire_png(4, 4, [b"\x05" * 4] * 4, couleurs=3, pas=1, palette=b"\x00" * 6),
            "format_partiel",
        ),
        (
            SIGNATURE
            + bloc_png(b"IHDR", _ihdr())
            + bloc_png(b"IDAT", b"pas du zlib")
            + bloc_png(b"IEND", b""),
            "format_partiel",
        ),
        (
            SIGNATURE
            + bloc_png(b"IHDR", _ihdr())
            + bloc_png(b"IDAT", zlib.compress(b"\x00" * 13))
            + bloc_png(b"IEND", b""),
            "format_partiel",
        ),
        (
            SIGNATURE
            + bloc_png(b"IHDR", _ihdr())
            # Données aléatoires, peu compressibles, coupées au milieu du flux.
            + bloc_png(b"IDAT", zlib.compress(b"".join(b"\x00" + ligne for ligne in _LIGNES)))[:30],
            "fichier_tronque",
        ),
        (
            SIGNATURE
            + bloc_png(b"IHDR", _ihdr())
            + bloc_png(b"IDAT", zlib.compress(b"\x07" + b"\x00" * 51))
            + bloc_png(b"IEND", b""),
            "format_partiel",
        ),
    ],
)
def test_png_refuse(contenu: bytes, raison: str) -> None:
    lecture = png_lu(contenu)
    assert lecture.image is None
    assert lecture.arret == raison
    assert lecture.localisation_arret().chemin == "blocs du PNG"


def test_png_trop_grand_avant_decompression() -> None:
    contenu = SIGNATURE + bloc_png(b"IHDR", _ihdr(largeur=1 << 20, hauteur=1 << 20))
    with tempfile.TemporaryFile() as fichier, pytest.raises(LimiteDepassee):
        png.lire(contexte(fichier, contenu, "png", "dwtdct"), pixels=1 << 22)


# Couleurs d'un JPEG (ADR-0202)


DJPEG = shutil.which("djpeg")


def test_ycbcr_vers_rvb_comme_libjpeg() -> None:
    y = np.array([[0, 128, 255, 76, 29, 150]], dtype=np.int64)
    cb = np.array([[128, 128, 128, 85, 255, 44]], dtype=np.int64)
    cr = np.array([[128, 128, 128, 255, 107, 21]], dtype=np.int64)
    rvb = pixels.ycbcr_vers_rvb(y, cb, cr)
    # Valeurs du calcul flottant, arrondies et bornées : les tables de libjpeg leur sont égales,
    # au plus un niveau près.
    yf, cbf, crf = y.astype(float), cb - 128.0, cr - 128.0
    flottant = np.stack(
        [yf + 1.402 * crf, yf - 0.34414 * cbf - 0.71414 * crf, yf + 1.772 * cbf], axis=2
    )
    assert int(np.abs(rvb - np.clip(np.rint(flottant), 0, 255)).max()) <= 1
    assert rvb[0, 1].tolist() == [128, 128, 128]
    assert rvb[0, 3].tolist() == [254, 0, 0]


@pytest.mark.skipif(DJPEG is None, reason="djpeg absent")
@pytest.mark.parametrize("nom", ["flux.jpg", "sdxl_420.jpg", "sd1_progressif.jpg", "rvb.jpg"])
def test_oracle_libjpeg_turbo(nom: str) -> None:
    # Pixels de djpeg -nosmooth -dct int (suréchantillonnage par répétition, IDCT en entiers de
    # libjpeg) : l'IDCT exacte du projet en diffère de quelques niveaux sur quelques pixels.
    assert DJPEG is not None
    sortie = subprocess.run(
        [DJPEG, "-nosmooth", "-dct", "int", "-pnm"],
        input=echantillon(nom),
        capture_output=True,
        check=True,
    ).stdout
    entete, dimensions, _, donnees = sortie.split(b"\n", 3)
    assert entete == b"P6"
    largeur, hauteur = map(int, dimensions.split())
    reference = np.frombuffer(donnees, np.uint8).reshape(hauteur, largeur, 3).astype(np.int64)
    ecarts = np.abs(rvb_de(echantillon(nom), "jpeg") - reference)
    assert int(ecarts.max()) <= 4
    assert float(ecarts.mean()) < 0.1


def test_jpeg_premieres_lignes_de_mcu() -> None:
    lecture = lire_pixels(echantillon("sdxl_420.jpg"), "jpeg", budget=256 * 40)
    assert lecture.pixels is not None
    # 40 lignes demandées : 2 lignes de MCU de 16 pixels.
    assert lecture.pixels.lignes == 32
    assert lecture.pixels.rvb is not None
    assert np.array_equal(lecture.pixels.rvb, rvb_de(echantillon("sdxl_420.jpg"), "jpeg")[:32])


def _jpeg(
    composantes: list[Composante],
    avant: bytes = b"",
    tables: dict[int, Sequence[int]] | None = None,
    seule: int | None = None,
) -> bytes:
    blocs = blocs_nuls(composantes, 16, 16)
    if seule is not None:
        blocs[seule] = [[0] * 64 for _ in range(len(blocs[seule]))]
    return encoder_jpeg(
        16, 16, composantes, blocs, tables or {0: (1,) * 64}, avant_balayage=avant, seule=seule
    )


_YCBCR = [Composante(1), Composante(2), Composante(3)]
_RVB = [Composante(ord("R")), Composante(ord("G")), Composante(ord("B"))]


def _adobe(transformation: int) -> bytes:
    return segment(0xEE, b"Adobe" + b"\x00\x64\x00\x00\x00\x00" + bytes([transformation]))


@pytest.mark.parametrize(
    ("composantes", "avant", "attendu"),
    [
        # Blocs nuls : Y = Cb = Cr = 128 donne du gris ; R = G = B = 128 aussi. Les cas se
        # distinguent par le premier pixel d'une image dont seul le premier coefficient continu
        # de la première composante change (voir plus bas).
        (_YCBCR, b"", False),
        (_RVB, b"", True),
        (_RVB, segment(0xE0, b"JFIF\x00\x01\x02\x00\x00\x01\x00\x01\x00\x00"), False),
        (_YCBCR, _adobe(0), True),
        (_RVB, _adobe(1), False),
    ],
)
def test_jpeg_espace_des_couleurs(
    composantes: list[Composante], avant: bytes, attendu: bool
) -> None:
    blocs = blocs_nuls(composantes, 16, 16)
    for bloc in blocs[0]:
        bloc[0] = 64  # première composante à 128 + 64 / 8 x 8 = 192 partout
    contenu = encoder_jpeg(16, 16, composantes, blocs, {0: (8,) * 64}, avant_balayage=avant)
    rvb = rvb_de(contenu, "jpeg")
    if attendu:  # R = 192, G = B = 128
        assert rvb[0, 0].tolist() == [192, 128, 128]
    else:  # Y = 192, Cb = Cr = 128 : gris
        assert rvb[0, 0].tolist() == [192, 192, 192]


def test_jpeg_segment_adobe_trop_court_ignore() -> None:
    blocs = blocs_nuls(_RVB, 16, 16)
    contenu = encoder_jpeg(
        16, 16, _RVB, blocs, {0: (8,) * 64}, avant_balayage=segment(0xEE, b"Adobe\x00")
    )
    lecture = lire_pixels(contenu, "jpeg")
    assert lecture.pixels is not None


def test_jpeg_en_niveaux_de_gris() -> None:
    lecture = lire_pixels(_jpeg([Composante(1)]), "jpeg")
    assert lecture.pixels is not None
    assert lecture.pixels.rvb is None
    assert (lecture.pixels.largeur, lecture.pixels.hauteur) == (16, 16)


def test_jpeg_cmyk_non_lu() -> None:
    lecture = lire_pixels(_jpeg([Composante(i) for i in range(1, 5)]), "jpeg")
    assert lecture.pixels is None
    assert lecture.arret == RaisonNonMenee.FORMAT_PARTIEL
    assert lecture.localisation is not None
    assert lecture.localisation.chemin == "segment SOF du JPEG"


def test_jpeg_malforme() -> None:
    lecture = lire_pixels(b"\xff\xd8\xff\xd9", "jpeg")
    assert lecture.pixels is None
    assert lecture.arret == RaisonNonMenee.FORMAT_PARTIEL


def test_jpeg_composante_sans_balayage() -> None:
    # Seule la luminance a un balayage : la chrominance reste à 128, ses tables viennent du DQT.
    lecture = lire_pixels(_jpeg(_YCBCR, seule=0), "jpeg")
    assert lecture.pixels is not None
    assert lecture.pixels.rvb is not None
    assert int(lecture.pixels.rvb.min()) == int(lecture.pixels.rvb.max()) == 128


def test_jpeg_composante_sans_balayage_ni_table() -> None:
    composantes = [Composante(1), Composante(2, table=1), Composante(3, table=1)]
    lecture = lire_pixels(_jpeg(composantes, seule=0), "jpeg")
    assert lecture.pixels is None
    assert lecture.arret == RaisonNonMenee.FORMAT_PARTIEL


def test_jpeg_table_manquante_au_balayage() -> None:
    composantes = [Composante(1), Composante(2, table=1), Composante(3, table=1)]
    with tempfile.TemporaryFile() as fichier:
        lecture = jpeg.lire(contexte(fichier, _jpeg(composantes), "jpeg", "dwtdct"), toutes=True)
    assert lecture.coefficients is None
    assert lecture.arret == RaisonNonMenee.FORMAT_PARTIEL


def test_jpeg_sans_toutes_les_composantes() -> None:
    # Le décodage de la seule luminance (T41) ne voit pas la table manquante de la chrominance,
    # ni le balayage qui ne porte qu'elle.
    composantes = [Composante(1), Composante(2, table=1), Composante(3, table=1)]
    with tempfile.TemporaryFile() as fichier:
        lecture = jpeg.lire(contexte(fichier, _jpeg(composantes, seule=0), "jpeg", "dwtdct"))
    assert lecture.coefficients is not None
    assert lecture.composantes == ()


def test_jpeg_visites_au_dela_du_budget() -> None:
    with tempfile.TemporaryFile() as fichier:
        lecture = jpeg.lire(
            contexte(fichier, echantillon("sdxl_420.jpg"), "jpeg", "dwtdct"),
            visites=5,
            toutes=True,
        )
    assert lecture.arret == RaisonNonMenee.FORMAT_PARTIEL


def test_jpeg_region_reduite_par_les_visites() -> None:
    with tempfile.TemporaryFile() as fichier:
        lecture = jpeg.lire(
            contexte(fichier, echantillon("sd1_progressif.jpg"), "jpeg", "dwtdct"),
            visites=4000,
            toutes=True,
        )
    assert lecture.coefficients is not None
    # Lignes de MCU entières : la luminance n'a qu'un bloc par MCU en hauteur.
    assert 0 < lecture.coefficients.lignes < 32
    hauteurs = {8 * c.lignes * c.vertical_max // c.vertical for c in lecture.composantes}
    assert len(hauteurs) == 1


def _coefficients(horizontal: int, horizontal_max: int) -> Coefficients:
    return Coefficients(
        largeur=16,
        hauteur=8,
        procede="sequentiel",
        precision_table=False,
        table=(1,) * 64,
        colonnes=1,
        lignes=1,
        largeur_composante=8,
        hauteur_region=8,
        blocs_image=1,
        valeurs=array("q", bytes(8 * 64)),
        horizontal=horizontal,
        horizontal_max=horizontal_max,
    )


def test_echantillonnage_non_entier_non_lu() -> None:
    assert pixels._plan(_coefficients(2, 3)) is None
    plan = pixels._plan(_coefficients(1, 2))
    assert plan is not None
    assert plan.shape == (8, 16)
    # Luminance en 3 x 1, chrominance en 2 x 1 et 1 x 1 : 3 / 2 n'est pas entier.
    composantes = [Composante(1, 3, 1), Composante(2, 2, 1), Composante(3)]
    contenu = encoder_jpeg(24, 8, composantes, blocs_nuls(composantes, 24, 8), {0: (1,) * 64})
    lecture = lire_pixels(contenu, "jpeg")
    assert lecture.pixels is None
    assert lecture.arret == RaisonNonMenee.FORMAT_PARTIEL


# Composante U (ADR-0203)

# Valeurs relevées sur OpenCV 5.0.0 (cv2.cvtColor, COLOR_BGR2YUV) : la formule en entiers du
# module leur est égale sur les 2^24 couleurs (vérifié pendant T32, hors des tests).
_OPENCV = [
    # (R, G, B) : U sur huit bits, U en flottant
    ((0, 0, 255), 239, 111.65756),
    ((255, 0, 0), 91, -37.01254),
    ((0, 255, 0), 54, -73.14502),
    ((128, 128, 128), 128, 0.5),
    ((12, 200, 77), 102, -25.46088),
    ((255, 255, 255), 128, 0.5),
]


@pytest.mark.parametrize(("couleur", "huit_bits", "flottant"), _OPENCV)
def test_composante_u_comme_opencv(
    couleur: tuple[int, int, int], huit_bits: int, flottant: float
) -> None:
    rvb = np.array([[couleur]], dtype=np.int64)
    assert int(dwtdct._u(rvb, True, False)[0, 0]) == huit_bits
    assert abs(int(dwtdct._u(rvb, False, False)[0, 0]) / 1e6 - flottant) < 1e-4
    inverse = np.array([[couleur[::-1]]], dtype=np.int64)
    assert int(dwtdct._u(inverse, True, True)[0, 0]) == huit_bits


def test_bande_basse_de_haar_et_blocs() -> None:
    # Un bloc dont la plus grande valeur hors de la première vaut 2 x 30 (doublée) : 30 % 36 > 18.
    u = np.zeros((8, 16), dtype=np.int64)
    u[2:4, 2:4] = 15  # carré (1, 1) du bloc 0 : (15 x 4) / 2 = 30
    u[0:2, 8:10] = 50  # première valeur du bloc 1, ignorée : (50 x 4) / 2 = 100
    u[6:8, 14:16] = 2  # dernière valeur du bloc 1 : 4
    scores = dwtdct._scores(u, 1, 2, 72)
    assert scores.tolist() == [True, False]


# Décision par rang et loi des bits concordants (ADR-0203, ADR-0204)


def test_decider_par_rang() -> None:
    assert dwtdct.decider([5, 1, 4, 0], [10, 10, 10, 10], 2) == [1, 0, 1, 0]
    # Égalité de part et d'autre du rang : indéterminés.
    assert dwtdct.decider([5, 3, 3, 0], [10, 10, 10, 10], 2) == [1, None, None, 0]
    # Égalité entièrement au-dessus du rang : décidée.
    assert dwtdct.decider([3, 3, 1, 0], [10, 10, 10, 10], 2) == [1, 1, 0, 0]
    # Les scores sont des proportions : 2 / 3 > 3 / 5.
    assert dwtdct.decider([2, 3], [3, 5], 1) == [1, 0]


def test_queue_hypergeometrique() -> None:
    assert dwtdct.queue(4, 2, 0) == 1
    # a = 2 (les deux 1 du message parmi les deux bits lus à 1) : une chance sur six.
    assert dwtdct.queue(4, 2, 4) == Fraction(1, 6)
    assert dwtdct.queue(4, 2, 3) == Fraction(1, 6)
    sd1, sdxl, flux = (lecture.message for lecture in dwtdct.LECTURES)
    assert float(dwtdct.queue(len(sd1), sum(sd1), 98)) == pytest.approx(2.2e-7, rel=0.05)
    assert float(dwtdct.queue(len(sdxl), sum(sdxl), 42)) == pytest.approx(1.78e-7, rel=0.05)
    assert float(dwtdct.queue(len(flux), sum(flux), 39)) == pytest.approx(9.69e-7, rel=0.05)


def test_messages_des_codes_de_reference() -> None:
    sd1, sdxl, flux = dwtdct.LECTURES
    assert (len(sd1.message), sum(sd1.message)) == (136, 68)
    assert (
        bytes(int("".join(map(str, sd1.message[i : i + 8])), 2) for i in range(0, 136, 8))
        == b"StableDiffusionV1"
    )
    assert "".join(map(str, sdxl.message)) == format(0xB3EC907BB19E, "b")
    assert len(sdxl.message) == 48
    # bin() retire les deux zéros de tête du message de FLUX.1.
    assert "".join(map(str, flux.message)) == format(0x2AFE879CF52E, "048b")[2:]
    assert len(flux.message) == 46
    assert (sd1.huit_bits, sdxl.huit_bits, flux.huit_bits) == (True, False, False)
    assert (sd1.inversee, sdxl.inversee, flux.inversee) == (False, True, False)


# Lecture des échantillons (ADR-0203) : filigranes posés par invisible-watermark 0.2.0


# Bits concordants lus par le module ; la référence (attendus.toml) lit moins.
ATTENDUS = {
    "aucun.png": (56, 30, 25),
    "sd1.png": (136, 30, 21),
    "sd1_progressif.jpg": (132, 29, 21),
    "sdxl.png": (53, 48, 24),
    "sdxl_420.jpg": (55, 48, 23),
    "sdxl_rvb.png": (57, 48, 26),
    "flux.jpg": (56, 28, 46),
    "rvb.jpg": (53, 32, 46),
}


@pytest.mark.parametrize(("nom", "attendus"), ATTENDUS.items())
def test_lecture_des_echantillons(nom: str, attendus: tuple[int, int, int]) -> None:
    valeurs = valeurs_de(resultats("dwtdct", echantillon(nom), format_de(nom)))
    lus = tuple(valeurs[f"dwtdct.concordants_{n}"] for n in ("sd1", "sdxl", "flux"))
    assert lus == attendus
    assert valeurs["dwtdct.blocs"] == valeurs["dwtdct.blocs_image"] == 1024
    assert valeurs["dwtdct.pixels_image"] == 65536


def test_la_reference_lit_moins() -> None:
    # Décodeur de la bibliothèque (huit bits, seuil d'un demi), relevé par generer.py.
    reference = tomllib.loads((ECHANTILLONS / "attendus.toml").read_text(encoding="utf-8"))
    colonne = {"sd1": 0, "sdxl": 1, "flux": 2}
    for nom, lus in reference.items():
        if nom == "aucun.png":
            continue
        message = nom.split(".")[0].split("_")[0]
        assert ATTENDUS[nom][colonne[message]] > lus


def test_sdxl_couleurs_inversees() -> None:
    valeurs = valeurs_de(resultats("dwtdct", echantillon("sdxl_rvb.png"), "png"))
    assert valeurs["dwtdct.rouge_et_bleu_echanges_sdxl"] is True
    valeurs = valeurs_de(resultats("dwtdct", echantillon("sdxl.png"), "png"))
    assert "dwtdct.rouge_et_bleu_echanges_sdxl" not in valeurs


def test_indetermines_observes() -> None:
    valeurs = valeurs_de(resultats("dwtdct", echantillon("aucun.png"), "png"))
    assert valeurs["dwtdct.indetermines_sd1"] == 19
    assert "dwtdct.indetermines_sd1" not in valeurs_de(
        resultats("dwtdct", echantillon("sd1.png"), "png")
    )


def test_haut_de_l_image(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dwtdct, "PIXELS_MAX", 256 * 128)
    lignes = resultats("dwtdct", echantillon("sdxl.png"), "png")
    valeurs = valeurs_de(lignes)
    assert valeurs["dwtdct.blocs"] == 512
    assert valeurs["dwtdct.blocs_image"] == 1024
    assert valeurs["dwtdct.concordants_sdxl"] == 48
    blocs = next(
        ligne["observation"]
        for ligne in lignes
        if ligne["type"] == "observation" and ligne["observation"]["nom"] == "dwtdct.blocs"
    )
    assert blocs["localisation"]["chemin"] == "composante U, haut de l'image"
    assert blocs["localisation"]["zone"] == {"x": 0, "y": 0, "largeur": 256, "hauteur": 128}


# Ce que le module observe, et ce qu'il ne lit pas


def test_webp_et_heic_non_menes() -> None:
    for format_ in ("webp", "heic"):
        lignes = resultats("dwtdct", b"RIFF\x00\x00\x00\x00WEBP", format_)
        assert raisons(lignes) == ["format_partiel"]
        non_menee = next(ligne for ligne in lignes if ligne["type"] == "non_menee")
        chemin = non_menee["non_menee"]["localisation"]["chemin"]
        assert chemin == f"pixels {format_}, non décodés"


def test_image_illisible_non_menee() -> None:
    lignes = resultats("dwtdct", SIGNATURE + b"\x00\x00", "png")
    assert raisons(lignes) == ["fichier_tronque"]


def test_image_trop_petite() -> None:
    contenu = ecrire_png(255, 256, [bytes(255 * 3)] * 256)
    assert valeurs_de(resultats("dwtdct", contenu, "png")) == {"dwtdct.pixels_image": 65280}


def test_image_sans_chrominance() -> None:
    entete = struct.pack(">IIBBBBB", 256, 256, 8, 0, 0, 0, 0)
    contenu = SIGNATURE + bloc_png(b"IHDR", entete) + _IDAT + bloc_png(b"IEND", b"")
    valeurs = valeurs_de(resultats("dwtdct", contenu, "png"))
    assert valeurs == {"dwtdct.pixels_image": 65536, "dwtdct.chrominance": False}


def test_moins_de_blocs_que_de_bits() -> None:
    # 16 384 x 4 pixels : aucune ligne de blocs entière, aucun message lu.
    contenu = ecrire_png(16384, 4, [bytes(16384 * 3)] * 4)
    valeurs = valeurs_de(resultats("dwtdct", contenu, "png"))
    assert valeurs == {
        "dwtdct.pixels_image": 65536,
        "dwtdct.blocs": 0,
        "dwtdct.blocs_image": 0,
    }


# Analyse complète : règles du catalogue (ADR-0206)


@pytest.mark.parametrize(
    ("nom", "regle"),
    [
        ("sd1.png", "R-DWTDCT-001"),
        ("sdxl.png", "R-DWTDCT-002"),
        ("sdxl_rvb.png", "R-DWTDCT-002"),
        ("flux.jpg", "R-DWTDCT-003"),
    ],
)
def test_analyse_complete(tmp_path: Path, nom: str, regle: str) -> None:
    chemin = tmp_path / nom
    chemin.write_bytes(echantillon(nom))
    analyse = analyser(chemin)
    constats = [c for c in analyse.constats if c.module == "dwtdct"]
    assert [c.regle.identifiant for c in constats] == [regle]
    assert "M-DWTDCT" in analyse.couverture.marquages_recherches


def test_analyse_complete_sans_filigrane(tmp_path: Path) -> None:
    chemin = tmp_path / "aucun.png"
    chemin.write_bytes(echantillon("aucun.png"))
    analyse = analyser(chemin)
    assert not [c for c in analyse.constats if c.module == "dwtdct"]
