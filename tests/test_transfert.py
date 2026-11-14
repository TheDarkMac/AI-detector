"""Règles et module de T24 : indices de transfert par messagerie ou capture d'écran (F-06,
ADR-0153 à ADR-0157).

Comme ``test_signatures.py`` : le module s'exécute sur un contexte réel, puis le contexte applique
les règles « moteur » du module ; une analyse complète, par le processus de travail, vérifie le
même chemin jusqu'au rapport. Les JPEG d'ImageMagick et de ffmpeg servent d'oracle pour la
qualité libjpeg.
"""

import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any

import pytest
from echantillons import bloc_png
from metadonnees import (
    CHROMINANCE,
    LUMINANCE,
    Sous,
    app1_exif,
    app1_xmp,
    app13,
    ascii_,
    bloc_riff,
    dqt,
    indefini,
    jeu,
    jpeg_ijg,
    jpeg_image,
    jpeg_meta,
    png_meta,
    raisons,
    ressource,
    resultats,
    sof,
    table_ijg,
    texte,
    tiff,
    valeurs_de,
    vp8,
    vp8l,
    webp_image,
    webp_meta,
    xmp,
)
from test_signatures import CATALOGUE, constats

from voight_kampff._regles import Application
from voight_kampff._travail import garde
from voight_kampff.analyse import analyser
from voight_kampff.cli import resume
from voight_kampff.modules import image
from voight_kampff.rapport._presentation import texte as texte_du_rapport
from voight_kampff.rapport.modele import Categorie, Direction, Fondement, Niveau

pytestmark = pytest.mark.exigence("F-06")

RECOMMANDATION = texte_du_rapport("resume.transformation")

REGLES_T24 = tuple(
    regle for regle in CATALOGUE.regles if regle.direction is Direction.TRANSFORMATION
)
SIGNATURES = {"R-EXIF-014", "R-XMP-013", "R-IPTC-003", "R-TEXTEPNG-007"}

EXIF_NS = 'xmlns:exif="http://ns.adobe.com/exif/1.0/"'
FBMD = b"FBMD01000a8b0300009e1000003e2f0000"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def t24(module: str, contenu: bytes, format_: str) -> dict[str, dict[str, Any]]:
    return constats(module, contenu, format_, REGLES_T24)


def commentaire(texte_: bytes) -> bytes:
    """JPEG dont l'EXIF porte un UserComment en ASCII (code de jeu de huit octets, EXIF 3.0)."""
    return jpeg_meta(
        app1_exif(tiff((Sous(0x8769, (indefini(0x9286, b"ASCII\x00\x00\x00" + texte_),)),)))
    )


def commentaire_xmp(texte_: str) -> bytes:
    propriete = (
        f'<exif:UserComment><rdf:Alt><rdf:li xml:lang="x-default">{texte_}</rdf:li>'
        "</rdf:Alt></exif:UserComment>"
    )
    return jpeg_meta(app1_xmp(xmp(propriete, espaces=EXIF_NS)))


def png_image(largeur: int, hauteur: int) -> bytes:
    entete = bloc_png(b"IHDR", struct.pack(">IIBBBBB", largeur, hauteur, 8, 2, 0, 0, 0))
    return b"\x89PNG\r\n\x1a\n" + entete + bloc_png(b"IEND", b"")


AUTRES = dqt((0, (2,) * 64))
"""Une table de luminance qui n'est pas de libjpeg."""


def instructions(valeur: bytes) -> bytes:
    return jpeg_meta(app13(ressource(0x0404, jeu(2, 40, valeur))))


# Un échantillon par règle : module, format, contenu, règle, paramètres attendus.
CAS = [
    ("exif", "jpeg", commentaire(b"Screenshot"), "R-EXIF-014", {}),
    ("xmp", "jpeg", commentaire_xmp("Screenshot"), "R-XMP-013", {}),
    ("iptc", "jpeg", instructions(FBMD), "R-IPTC-003", {}),
    ("textepng", "png", png_meta(texte(b"Software", b"gnome-screenshot")), "R-TEXTEPNG-007", {}),
    ("image", "jpeg", jpeg_image(1600, 1200), "R-IMAGE-001", {"largeur": 1600, "hauteur": 1200}),
    ("image", "jpeg", jpeg_image(720, 1280), "R-IMAGE-002", {"largeur": 720, "hauteur": 1280}),
    ("image", "jpeg", jpeg_image(2048, 2048), "R-IMAGE-003", {"largeur": 2048, "hauteur": 2048}),
    ("image", "jpeg", jpeg_image(640, 480, tables=jpeg_ijg(75)), "R-IMAGE-004", {"qualite": 75}),
]


@pytest.mark.parametrize(("module", "format_", "contenu", "regle", "parametres"), CAS)
def test_regle_de_t24_declenchee(
    module: str, format_: str, contenu: bytes, regle: str, parametres: dict[str, Any]
) -> None:
    assert t24(module, contenu, format_) == {regle: parametres}


def test_chaque_regle_de_t24_est_eprouvee() -> None:
    assert {cas[3] for cas in CAS} == {regle.identifiant for regle in REGLES_T24}
    assert len(REGLES_T24) == 8


@pytest.mark.exigence("ES-20")
def test_regles_de_t24_indices_faibles_de_transformation() -> None:
    # ADR-0155 : indice faible non évalué ; déclaration pour une signature, lecture de la
    # structure pour le module image.
    for regle in REGLES_T24:
        assert regle.application is Application.MOTEUR
        assert regle.categorie is Categorie.INDICE
        assert (regle.niveau, regle.evaluation) == (Niveau.FAIBLE, None)
        attendu = (
            Fondement.DECLARATION
            if regle.identifiant in SIGNATURES
            else Fondement.VERIFICATION_DETERMINISTE
        )
        assert regle.fondement is attendu
    # Les trois règles de dimensions lisent la même liste de côtés.
    listes = {
        condition.parmi
        for regle in REGLES_T24
        for condition in regle.conditions
        if condition.parmi is not None
    }
    assert listes == {(960, 1080, 1280, 1600, 2048, 2560)}


@pytest.mark.parametrize(
    ("module", "format_", "contenu"),
    [
        pytest.param("exif", "jpeg", commentaire(b"Screenshot 2"), id="commentaire-autre"),
        pytest.param("xmp", "jpeg", commentaire_xmp("screenshot"), id="xmp-casse"),
        pytest.param("iptc", "jpeg", instructions(b"Voir " + FBMD), id="fbmd-pas-au-debut"),
        pytest.param(
            "textepng", "png", png_meta(texte(b"Software", b"GIMP 2.10")), id="logiciel-ordinaire"
        ),
        # Dimensions : métadonnées présentes, autre format, autre taille, côté non le plus long.
        pytest.param(
            "image",
            "jpeg",
            jpeg_image(1600, 1200, app1_exif(tiff((ascii_(0x010F, "Canon"),)))),
            id="avec-exif",
        ),
        pytest.param(
            "image",
            "png",
            png_image(1600, 1200),
            id="png-sans-tables",
        ),
        pytest.param("image", "jpeg", jpeg_image(1601, 1200), id="autre-taille"),
        pytest.param("image", "jpeg", jpeg_image(2000, 1600), id="cote-court"),
        pytest.param("image", "jpeg", jpeg_image(1600, 2000), id="cote-court-portrait"),
        # Tables : avec métadonnées, autres tables, chrominance d'une autre qualité, trois tables.
        pytest.param(
            "image",
            "jpeg",
            jpeg_image(640, 480, app1_xmp(xmp("")), tables=jpeg_ijg(75)),
            id="libjpeg-avec-xmp",
        ),
        pytest.param(
            "image",
            "jpeg",
            jpeg_image(
                640,
                480,
                tables=dqt((0, table_ijg(LUMINANCE, 75)), (1, table_ijg(CHROMINANCE, 76))),
            ),
            id="chrominance-autre-qualite",
        ),
        pytest.param(
            "image",
            "jpeg",
            jpeg_image(640, 480, tables=jpeg_ijg(75) + dqt((2, (1,) * 64))),
            id="trois-tables",
        ),
    ],
)
def test_sans_transfert_sans_constat(module: str, format_: str, contenu: bytes) -> None:
    assert t24(module, contenu, format_) == {}


def test_parcours_interrompu_sans_compte_de_metadonnees() -> None:
    # ADR-0154 : un parcours arrêté ne dit pas que le fichier est sans métadonnées.
    contenu = b"\xff\xd8" + AUTRES + sof(1600, 1200) + b"\xff\xe1\x00\x40Exif"
    lignes = resultats("image", contenu, "jpeg")
    assert "image.metadonnees" not in valeurs_de(lignes)
    assert raisons(lignes) == ["fichier_tronque"]
    assert t24("image", contenu, "jpeg") == {}


# Observations du module


@pytest.mark.parametrize(
    ("format_", "contenu", "attendu"),
    [
        pytest.param(
            "jpeg",
            jpeg_image(1600, 1200, app1_exif(tiff((ascii_(0x010F, "Canon"),)))),
            {"image.metadonnees": 1, "image.trame": "SOF0", "image.largeur": 1600,
             "image.hauteur": 1200, "image.jpeg.tables": 2},
            id="jpeg",
        ),
        pytest.param(
            "jpeg",
            jpeg_meta(jpeg_ijg(92), sof(64, 0, marqueur=0xC2)),
            {"image.metadonnees": 0, "image.trame": "SOF2", "image.largeur": 64,
             "image.jpeg.tables": 2, "image.jpeg.qualite_ijg": 92},
            id="jpeg-progressif-hauteur-dnl",
        ),
        pytest.param(
            "png",
            png_meta(texte(b"Software", b"x")),
            {"image.metadonnees": 1, "image.trame": "IHDR", "image.largeur": 1,
             "image.hauteur": 1},
            id="png",
        ),
        pytest.param(
            "webp",
            webp_meta(),
            {"image.metadonnees": 0, "image.trame": "VP8X", "image.largeur": 1,
             "image.hauteur": 1},
            id="webp-vp8x",
        ),
        pytest.param(
            "webp",
            webp_image(vp8(1280, 720)),
            {"image.metadonnees": 0, "image.trame": "VP8", "image.largeur": 1280,
             "image.hauteur": 720},
            id="webp-vp8",
        ),
        pytest.param(
            "webp",
            webp_image(vp8l(1600, 900)),
            {"image.metadonnees": 0, "image.trame": "VP8L", "image.largeur": 1600,
             "image.hauteur": 900},
            id="webp-vp8l",
        ),
        pytest.param(
            "webp",
            webp_image(bloc_riff(b"ICCP", b"profil"), vp8l(16, 9)),
            {"image.metadonnees": 0, "image.trame": "VP8L", "image.largeur": 16,
             "image.hauteur": 9},
            id="webp-profil-de-couleur-non-compte",
        ),
    ],
)  # fmt: skip
def test_observations_du_module_image(
    format_: str, contenu: bytes, attendu: dict[str, Any]
) -> None:
    lignes = resultats("image", contenu, format_)
    assert valeurs_de(lignes) == attendu
    assert raisons(lignes) == []


@pytest.mark.parametrize(
    ("format_", "contenu"),
    [
        pytest.param("jpeg", jpeg_meta(AUTRES, b"\xff\xc0\x00\x05\x08\x00\x10"), id="sof-court"),
        pytest.param(
            "png",
            b"\x89PNG\r\n\x1a\n" + bloc_png(b"IHDR", b"\x00" * 4) + bloc_png(b"IEND", b""),
            id="ihdr-court",
        ),
        pytest.param(
            "webp", webp_image(vp8l(16, 16).replace(b"\x2f", b"\x2e", 1)), id="vp8l-sans-signature"
        ),
        pytest.param(
            "webp",
            webp_image(vp8(16, 16).replace(b"\x9d\x01\x2a", b"\x00\x00\x00")),
            id="vp8-sans-code-de-depart",
        ),
        pytest.param("webp", webp_image(bloc_riff(b"VP8X", bytes(6))), id="vp8x-court"),
    ],
)
def test_en_tete_illisible_non_mene(format_: str, contenu: bytes) -> None:
    lignes = resultats("image", contenu, format_)
    assert "image.largeur" not in valeurs_de(lignes)
    assert raisons(lignes) == ["format_partiel"]


@pytest.mark.exigence("F-30")
def test_tables_de_seize_bits_et_redefinition() -> None:
    # Table de seize bits à une qualité basse : valeurs au-delà de 255 (force_baseline faux).
    seize = dqt(
        (0, table_ijg(LUMINANCE, 10, plafond=32767)),
        (1, table_ijg(CHROMINANCE, 10, plafond=32767)),
        seize_bits=True,
    )
    assert max(table_ijg(LUMINANCE, 10, plafond=32767)) > 255
    contenu = jpeg_meta(AUTRES, seize, sof(8, 8))
    valeurs = valeurs_de(resultats("image", contenu, "jpeg"))
    # T.81, B.2.4.1 : la dernière définition de la table 0 l'emporte.
    assert (valeurs["image.jpeg.tables"], valeurs["image.jpeg.qualite_ijg"]) == (2, 10)


@pytest.mark.exigence("F-30")
def test_table_invalide_non_menee_les_autres_gardees() -> None:
    invalide = dqt((0, table_ijg(LUMINANCE, 50))) + b"\xff\xdb\x00\x04\x25\x00"
    lignes = resultats("image", jpeg_meta(invalide, sof(8, 8)), "jpeg")
    assert raisons(lignes) == ["format_partiel"]
    assert valeurs_de(lignes)["image.jpeg.qualite_ijg"] == 50


@pytest.mark.exigence("F-30")
def test_une_qualite_par_table_de_libjpeg() -> None:
    # ADR-0154 : la qualité lue est unique, en huit et en seize bits.
    assert len(image._QUALITES) == 200
    for qualite in range(1, 101):
        tables = {
            0: (False, table_ijg(LUMINANCE, qualite)),
            1: (False, table_ijg(CHROMINANCE, qualite)),
        }
        assert image.qualite_ijg(tables) == qualite
        assert image.qualite_ijg({0: tables[0]}) == qualite  # image en niveaux de gris
    assert image.qualite_ijg({1: (False, table_ijg(CHROMINANCE, 50))}) is None


def _oracle(commande: list[str], sortie: Path) -> int | None:
    subprocess.run(commande, check=True, capture_output=True)
    valeurs = valeurs_de(resultats("image", sortie.read_bytes(), "jpeg"))
    return valeurs.get("image.jpeg.qualite_ijg")


@pytest.mark.exigence("F-30")
@pytest.mark.skipif(shutil.which("magick") is None, reason="ImageMagick absent")
@pytest.mark.parametrize("qualite", [5, 50, 75, 92, 100])
def test_oracle_qualite_d_imagemagick(qualite: int, tmp_path: Path) -> None:
    # ImageMagick encode par libjpeg : la qualité demandée est celle que le module lit.
    sortie = tmp_path / "image.jpg"
    commande = ["magick", "-size", "96x64", "xc:#3366cc", "-quality", str(qualite), str(sortie)]
    assert _oracle(commande, sortie) == qualite


@pytest.mark.exigence("F-30")
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg absent")
def test_oracle_tables_de_ffmpeg_non_reconnues(tmp_path: Path) -> None:
    # L'encodeur MJPEG de ffmpeg a ses propres tables : aucune qualité libjpeg.
    sortie = tmp_path / "image.jpg"
    commande = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=blue:s=96x64",
                "-frames:v", "1", str(sortie)]  # fmt: skip
    assert _oracle(commande, sortie) is None


# Analyses complètes


def _indices(chemin: Path) -> set[str]:
    return {
        constat.regle.identifiant
        for constat in analyser(chemin).constats
        if constat.categorie is Categorie.INDICE
    }


def test_analyse_complete_d_un_jpeg_de_messagerie(tmp_path: Path) -> None:
    # Profil d'une image reçue par une messagerie : 1 600 sur 1 200, tables de libjpeg, sans
    # métadonnées. Le résumé recommande une fois d'obtenir l'original (ADR-0156).
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(jpeg_image(1600, 1200, tables=jpeg_ijg(80)))
    analyse = analyser(chemin)
    assert {c.regle.identifiant for c in analyse.constats if c.categorie is Categorie.INDICE} == {
        "R-IMAGE-001",
        "R-IMAGE-004",
    }
    lignes = resume(analyse)
    assert lignes.count(RECOMMANDATION) == 1


def test_analyse_complete_sans_transformation_sans_recommandation(tmp_path: Path) -> None:
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(jpeg_image(640, 480))
    analyse = analyser(chemin)
    assert _indices(chemin) == set()
    assert RECOMMANDATION not in resume(analyse)


def test_analyse_complete_d_une_capture_d_ecran(tmp_path: Path) -> None:
    chemin = tmp_path / "capture.png"
    chemin.write_bytes(png_meta(texte(b"Software", b"gnome-screenshot")))
    assert _indices(chemin) == {"R-TEXTEPNG-007"}
