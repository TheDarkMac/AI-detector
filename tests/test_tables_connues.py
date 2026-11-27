"""Tables de quantification JPEG comparées à des tables connues (T40, F-30, ADR-0180 à ADR-0184).

Comme ``test_transfert.py`` : le module ``image`` s'exécute sur un contexte réel, puis le contexte
applique les règles « moteur » ; une analyse complète vérifie le même chemin jusqu'au rapport.
cjpeg (libjpeg-turbo, et mozjpeg s'il est installé) et ffmpeg servent d'oracle, ignorés s'ils
manquent.
"""

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from catalogues import niveau_mesure
from metadonnees import (
    CHROMINANCE,
    LUMINANCE,
    ZIGZAG,
    app1_exif,
    ascii_,
    dqt,
    jpeg_ijg,
    jpeg_image,
    jpeg_meta,
    resultats,
    sof,
    table_ijg,
    tiff,
    valeurs_de,
)
from test_signatures import CATALOGUE, constats

from voight_kampff._regles import Application
from voight_kampff._travail import garde
from voight_kampff.analyse import analyser
from voight_kampff.cli import resume
from voight_kampff.modules import image
from voight_kampff.rapport._presentation import texte as texte_du_rapport
from voight_kampff.rapport.modele import Categorie, Direction, Fondement

pytestmark = pytest.mark.exigence("F-30")

REGLES_T40 = tuple(
    regle
    for regle in CATALOGUE.regles
    if regle.identifiant in {"R-IMAGE-005", "R-IMAGE-006", "R-IMAGE-007"}
)
REGLES_IMAGE = tuple(regle for regle in CATALOGUE.regles if regle.module == "image")

ENCODEURS = {
    "image.jpeg.qualite_ijg",
    "image.jpeg.qualite_ijg_luminance",
    "image.jpeg.qualite_ijg_chrominance",
    "image.jpeg.jeu_mozjpeg",
    "image.jpeg.qualite_mozjpeg",
    "image.jpeg.qscale_ffmpeg",
}


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def mozjpeg(jeu: int, qualite: int, plafond: int = 255) -> bytes:
    """Tables de luminance et de chrominance du jeu de mozjpeg à cette qualité, en un segment."""
    return dqt(
        (0, table_ijg(image._MOZJPEG_LUMINANCE[jeu], qualite, plafond)),
        (1, table_ijg(image._MOZJPEG_CHROMINANCE[jeu], qualite, plafond)),
        seize_bits=plafond > 255,
    )


def table_ffmpeg(qscale: int) -> tuple[int, ...]:
    """Table de l'encodeur MJPEG de ffmpeg (mpegvideo_enc.c), écrite sans le code du module."""
    matrice = image._MPEG1_INTRA
    return tuple(8 if i == 0 else min(matrice[i] * qscale // 8, 255) for i in ZIGZAG)


def encodeurs(contenu: bytes) -> dict[str, Any]:
    valeurs = valeurs_de(resultats("image", contenu, "jpeg"))
    return {nom: valeur for nom, valeur in valeurs.items() if nom in ENCODEURS}


def t40(contenu: bytes) -> dict[str, dict[str, Any]]:
    return constats("image", contenu, "jpeg", REGLES_IMAGE)


DEUX_QUALITES = dqt((0, table_ijg(LUMINANCE, 90)), (1, table_ijg(CHROMINANCE, 70)))

# Un échantillon par règle : contenu, règle, paramètres attendus.
CAS = [
    (jpeg_image(640, 480, tables=DEUX_QUALITES), "R-IMAGE-005",
     {"luminance": 90, "chrominance": 70}),
    (jpeg_image(640, 480, tables=mozjpeg(3, 75)), "R-IMAGE-006", {"jeu": 3, "qualite": 75}),
    (jpeg_image(640, 480, tables=dqt((0, table_ffmpeg(5)))), "R-IMAGE-007", {"qscale": 5}),
]  # fmt: skip


@pytest.mark.parametrize(("contenu", "regle", "parametres"), CAS)
def test_regle_de_t40_declenchee(contenu: bytes, regle: str, parametres: dict[str, Any]) -> None:
    assert t40(contenu) == {regle: parametres}


def test_chaque_regle_de_t40_est_eprouvee() -> None:
    assert {cas[1] for cas in CAS} == {regle.identifiant for regle in REGLES_T40}
    assert len(REGLES_T40) == 3


@pytest.mark.exigence("ES-20")
def test_regles_de_t40_comme_r_image_004() -> None:
    # ADR-0182 : même nature que R-IMAGE-004 (ADR-0155), lecture de la structure, sans
    # métadonnées.
    for regle in REGLES_T40:
        assert regle.application is Application.MOTEUR
        assert regle.categorie is Categorie.INDICE
        assert regle.direction is Direction.TRANSFORMATION
        assert niveau_mesure(regle)  # niveau permis par sa mesure (T101, ADR-0278)
        assert regle.fondement is Fondement.VERIFICATION_DETERMINISTE
        premiere = regle.conditions[0]
        assert (premiere.observation, premiere.egal) == ("image.metadonnees", 0)


@pytest.mark.parametrize(
    "tables",
    [
        pytest.param(DEUX_QUALITES, id="libjpeg-deux-qualites"),
        pytest.param(mozjpeg(3, 75), id="mozjpeg"),
        pytest.param(dqt((0, table_ffmpeg(5))), id="ffmpeg"),
    ],
)
def test_pas_de_constat_avec_des_metadonnees(tables: bytes) -> None:
    contenu = jpeg_image(640, 480, app1_exif(tiff((ascii_(0x010F, "Canon"),))), tables=tables)
    assert t40(contenu) == {}
    assert encodeurs(contenu) != {}


# Reconnaissance


@pytest.mark.parametrize(
    ("tables", "attendu"),
    [
        pytest.param(jpeg_ijg(75), {"image.jpeg.qualite_ijg": 75}, id="libjpeg"),
        pytest.param(
            DEUX_QUALITES,
            {"image.jpeg.qualite_ijg_luminance": 90, "image.jpeg.qualite_ijg_chrominance": 70},
            id="libjpeg-deux-qualites",
        ),
        pytest.param(
            dqt(
                (0, table_ijg(LUMINANCE, 20, plafond=32767)),
                (1, table_ijg(CHROMINANCE, 40, plafond=32767)),
                seize_bits=True,
            ),
            {"image.jpeg.qualite_ijg_luminance": 20, "image.jpeg.qualite_ijg_chrominance": 40},
            id="libjpeg-deux-qualites-seize-bits",
        ),
        pytest.param(
            mozjpeg(3, 75), {"image.jpeg.jeu_mozjpeg": 3, "image.jpeg.qualite_mozjpeg": 75},
            id="mozjpeg-defaut",
        ),
        pytest.param(
            mozjpeg(2, 50), {"image.jpeg.jeu_mozjpeg": 2, "image.jpeg.qualite_mozjpeg": 50},
            id="mozjpeg-jeu-2",
        ),
        pytest.param(
            mozjpeg(5, 10, plafond=32767),
            {"image.jpeg.jeu_mozjpeg": 5, "image.jpeg.qualite_mozjpeg": 10},
            id="mozjpeg-seize-bits",
        ),
        pytest.param(
            dqt((0, table_ijg(image._MOZJPEG_LUMINANCE[7], 90))),
            {"image.jpeg.jeu_mozjpeg": 7, "image.jpeg.qualite_mozjpeg": 90},
            id="mozjpeg-niveaux-de-gris",
        ),
        pytest.param(dqt((0, table_ffmpeg(2))), {"image.jpeg.qscale_ffmpeg": 2}, id="ffmpeg"),
        pytest.param(
            dqt((0, table_ffmpeg(31)), (1, table_ffmpeg(31))),
            {"image.jpeg.qscale_ffmpeg": 31},
            id="ffmpeg-matrice-dupliquee",
        ),
        # Tables dégénérées, que plusieurs encodeurs écrivent : libjpeg d'abord (ADR-0183).
        pytest.param(dqt((0, (1,) * 64), (1, (1,) * 64)), {"image.jpeg.qualite_ijg": 100},
                     id="toutes-a-1"),
        pytest.param(dqt((0, (255,) * 64), (1, (255,) * 64)), {"image.jpeg.qualite_ijg": 1},
                     id="toutes-a-255"),
    ],
)  # fmt: skip
def test_encodeur_reconnu(tables: bytes, attendu: dict[str, int]) -> None:
    assert encodeurs(jpeg_meta(tables, sof(8, 8))) == attendu


@pytest.mark.parametrize(
    "tables",
    [
        # Chrominance de libjpeg à une qualité de 1 à 3, en huit bits : qualité ambiguë.
        pytest.param(
            dqt((0, table_ijg(LUMINANCE, 50)), (1, table_ijg(CHROMINANCE, 2))),
            id="chrominance-ambigue",
        ),
        pytest.param(
            dqt((0, table_ijg(LUMINANCE, 50)), (1, (2,) * 64)), id="libjpeg-chrominance-inconnue"
        ),
        pytest.param(
            dqt(
                (0, table_ijg(image._MOZJPEG_LUMINANCE[3], 75)),
                (1, table_ijg(image._MOZJPEG_CHROMINANCE[3], 70)),
            ),
            id="mozjpeg-deux-qualites",
        ),
        pytest.param(
            dqt((0, table_ijg(image._MOZJPEG_LUMINANCE[2], 75)), (1, (2,) * 64)),
            id="mozjpeg-chrominance-inconnue",
        ),
        pytest.param(dqt((0, (16,) * 64)), id="mozjpeg-jeu-plat"),
        pytest.param(dqt((0, table_ffmpeg(5)), (1, table_ffmpeg(6))), id="ffmpeg-deux-matrices"),
        pytest.param(dqt((0, table_ffmpeg(5)), seize_bits=True), id="ffmpeg-seize-bits"),
        pytest.param(dqt((0, (4, *table_ffmpeg(5)[1:]))), id="ffmpeg-autre-continu"),
        pytest.param(dqt((0, table_ffmpeg(5)), (2, table_ffmpeg(5))), id="trois-tables"),
        pytest.param(dqt((1, table_ffmpeg(5))), id="sans-table-0"),
    ],
)
def test_encodeur_non_reconnu(tables: bytes) -> None:
    assert encodeurs(jpeg_meta(tables, sof(8, 8))) == {}


def test_un_couple_par_table_de_mozjpeg() -> None:
    # Par jeu : 100 qualités en huit et en seize bits, moins la qualité 100 (toutes à 1, de
    # libjpeg) et, en huit bits, les qualités basses où toutes les valeurs atteignent 255.
    par_jeu: dict[int, int] = {}
    for jeu, _qualite in image._JEUX_MOZJPEG.values():
        par_jeu[jeu] = par_jeu.get(jeu, 0) + 1
    assert par_jeu == {2: 196, 3: 195, 4: 197, 5: 197, 6: 197, 7: 197, 8: 197}
    assert not image._JEUX_MOZJPEG.keys() & image._QUALITES.keys()
    for jeu in range(2, 9):
        # Qualité 50 : facteur 100, la table de jcparam.c telle quelle ; en seize bits si une
        # valeur dépasse 255 (jeux 3 et 5), comme l'écrit libjpeg sans -baseline.
        seize_bits = max(image._MOZJPEG_LUMINANCE[jeu]) > 255
        tables = {
            0: (seize_bits, tuple(image._MOZJPEG_LUMINANCE[jeu][i] for i in ZIGZAG)),
            1: (seize_bits, tuple(image._MOZJPEG_CHROMINANCE[jeu][i] for i in ZIGZAG)),
        }
        assert image.jeu_mozjpeg(tables) == (jeu, 50)
        for qualite in range(4, 100):
            tables = {
                0: (False, table_ijg(image._MOZJPEG_LUMINANCE[jeu], qualite)),
                1: (False, table_ijg(image._MOZJPEG_CHROMINANCE[jeu], qualite)),
            }
            assert image.encodeur(tables) == {
                "image.jpeg.jeu_mozjpeg": jeu,
                "image.jpeg.qualite_mozjpeg": qualite,
            }


def test_un_qscale_par_table_de_ffmpeg() -> None:
    assert len(image._QSCALES_FFMPEG) == 31
    for qscale in range(1, 32):
        assert image.qscale_ffmpeg({0: (False, table_ffmpeg(qscale))}) == qscale


def test_qualites_de_la_chrominance_de_libjpeg() -> None:
    # En huit bits, seules les qualités 1 à 3 donnent la même table de chrominance (ADR-0183).
    ambigues = {
        cle: qualites for cle, qualites in image._QUALITES_CHROMINANCE.items() if len(qualites) > 1
    }
    assert ambigues == {(False, (255,) * 64): (1, 2, 3)}
    for luminance in (10, 50, 95):
        for chrominance in range(4, 101):
            tables = {
                0: (False, table_ijg(LUMINANCE, luminance)),
                1: (False, table_ijg(CHROMINANCE, chrominance)),
            }
            attendu = None if chrominance == luminance else (luminance, chrominance)
            assert image.qualites_ijg(tables) == attendu


# Empreinte des tables (ADR-0181)


def test_empreinte_des_tables_ecriture_canonique() -> None:
    tables = {1: (False, (3,) * 64), 0: (False, tuple(range(1, 65)))}
    ecriture = "0:" + ",".join(map(str, range(1, 65))) + "\n1:" + ",".join(["3"] * 64)
    assert image.empreinte_tables(tables) == hashlib.sha256(ecriture.encode()).hexdigest()
    # La précision n'en fait pas partie.
    seize = {identifiant: (True, valeurs) for identifiant, (_, valeurs) in tables.items()}
    assert image.empreinte_tables(seize) == image.empreinte_tables(tables)


def test_empreinte_observee_pour_toutes_tables() -> None:
    valeurs = valeurs_de(resultats("image", jpeg_meta(dqt((0, (2,) * 64)), sof(8, 8)), "jpeg"))
    attendu = hashlib.sha256(("0:" + ",".join(["2"] * 64)).encode()).hexdigest()
    assert valeurs["image.jpeg.empreinte_tables"] == attendu
    assert not ENCODEURS & valeurs.keys()


# Oracles


def _ppm(largeur: int, hauteur: int) -> bytes:
    pixels = bytes((x * 7 + y * 13 + c * 50) % 256 for y in range(hauteur) for x in range(largeur)
                   for c in range(3))  # fmt: skip
    return f"P6\n{largeur} {hauteur}\n255\n".encode() + pixels


CJPEG = shutil.which("cjpeg")


def _version_de_cjpeg() -> str:
    if CJPEG is None:
        return ""
    sortie = subprocess.run([CJPEG, "-version"], capture_output=True, text=True, check=False)
    return sortie.stderr + sortie.stdout


VERSION_DE_CJPEG = _version_de_cjpeg()


def _cjpeg_encode(tmp_path: Path, *options: str) -> dict[str, Any]:
    source = tmp_path / "source.ppm"
    source.write_bytes(_ppm(48, 32))
    assert CJPEG is not None
    sortie = subprocess.run([CJPEG, *options, str(source)], capture_output=True, check=True)
    return encodeurs(sortie.stdout)


@pytest.mark.skipif("libjpeg-turbo" not in VERSION_DE_CJPEG, reason="cjpeg de libjpeg-turbo absent")
@pytest.mark.parametrize(
    ("options", "attendu"),
    [
        (("-quality", "80"), {"image.jpeg.qualite_ijg": 80}),
        (("-quality", "90,70"),
         {"image.jpeg.qualite_ijg_luminance": 90, "image.jpeg.qualite_ijg_chrominance": 70}),
        (("-quality", "15,40"),
         {"image.jpeg.qualite_ijg_luminance": 15, "image.jpeg.qualite_ijg_chrominance": 40}),
    ],
)  # fmt: skip
def test_oracle_cjpeg_de_libjpeg_turbo(
    options: tuple[str, ...], attendu: dict[str, int], tmp_path: Path
) -> None:
    # Sans -baseline, cjpeg écrit en seize bits une table dont une valeur dépasse 255 (qualité 15).
    assert _cjpeg_encode(tmp_path, *options) == attendu


@pytest.mark.skipif("mozjpeg" not in VERSION_DE_CJPEG, reason="cjpeg de mozjpeg absent")
@pytest.mark.parametrize(("jeu", "qualite"), [(3, 75), (2, 85), (6, 30)])
def test_oracle_cjpeg_de_mozjpeg(jeu: int, qualite: int, tmp_path: Path) -> None:
    options = ("-quant-table", str(jeu), "-quality", str(qualite))
    assert _cjpeg_encode(tmp_path, *options) == {
        "image.jpeg.jeu_mozjpeg": jeu,
        "image.jpeg.qualite_mozjpeg": qualite,
    }


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg absent")
@pytest.mark.parametrize("qscale", [2, 5, 31])
def test_oracle_ffmpeg(qscale: int, tmp_path: Path) -> None:
    sortie = tmp_path / "image.jpg"
    commande = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=96x64",
                "-frames:v", "1", "-q:v", str(qscale), str(sortie)]  # fmt: skip
    subprocess.run(commande, check=True, capture_output=True)
    assert encodeurs(sortie.read_bytes()) == {"image.jpeg.qscale_ffmpeg": qscale}


# Analyse complète


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg absent")
def test_analyse_complete_d_une_image_extraite_par_ffmpeg(tmp_path: Path) -> None:
    # ffmpeg extrait une image d'une vidéo par son encodeur MJPEG, sans métadonnées.
    chemin = tmp_path / "image.jpg"
    commande = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=96x64",
                "-frames:v", "1", "-q:v", "4", str(chemin)]  # fmt: skip
    subprocess.run(commande, check=True, capture_output=True)
    analyse = analyser(chemin)
    indices = {c.regle.identifiant for c in analyse.constats if c.categorie is Categorie.INDICE}
    assert indices == {"R-IMAGE-007"}
    assert resume(analyse).count(texte_du_rapport("resume.transformation")) == 1
