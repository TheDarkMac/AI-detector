"""Modules de métadonnées d'image : exif, xmp, iptc, textepng (T20, F-10, ADR-0114 à ADR-0121).

Chaque module est exécuté dans le processus des tests, sur un contexte réel qui lit un fichier
temporaire : mêmes lectures, mêmes budgets, mêmes objets du modèle que dans le processus de
travail. Les échantillons viennent de ``metadonnees.py`` ; la comparaison à exiftool est dans
``test_oracle_exiftool.py``.
"""

import importlib
import json
import struct
import tempfile
import zlib
from typing import Any
from xml.parsers import expat

import pytest
from echantillons import bloc_png, boite, jpeg, png, segment
from metadonnees import (
    DC,
    Element,
    Sous,
    app1_etendu,
    app1_exif,
    app1_xmp,
    app13,
    ascii_,
    bloc_riff,
    contexte,
    fractions,
    heic_meta,
    identifiantes,
    indefini,
    jeu,
    jpeg_meta,
    nombres,
    observations,
    png_meta,
    raisons,
    ressource,
    resultats,
    texte,
    texte_compresse,
    texte_international,
    tiff,
    valeurs_de,
    webp_meta,
    xmp,
)

from voight_kampff._limites import RESULTATS_MAX
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import LimiteDepassee
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture import xmp as lecture_xmp
from voight_kampff.modules._lecture.conteneurs import Nature, relever
from voight_kampff.rapport.modele import (
    LONGUEUR_MAX_TEXTE,
    NOMBRE_MAX_ELEMENTS,
)

pytestmark = pytest.mark.exigence("F-10")


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


# Absence : une observation, jamais un constat (F-14, ADR-0058)


@pytest.mark.exigence("F-14")
@pytest.mark.parametrize(
    ("module", "format_", "contenu"),
    [
        ("exif", "jpeg", jpeg()),
        ("exif", "png", png()),
        ("exif", "webp", webp_meta()),
        ("exif", "heic", heic_meta()),
        ("xmp", "jpeg", jpeg()),
        ("xmp", "png", png()),
        ("iptc", "jpeg", jpeg()),
        ("textepng", "png", png()),
    ],
)
def test_absence_observee(module: str, format_: str, contenu: bytes) -> None:
    lignes = resultats(module, contenu, format_)
    assert lignes == [
        {
            "type": "observation",
            "observation": {
                "identifiant": f"{module}/1",
                "module": module,
                "nom": f"{module}.present",
                "valeur": False,
                "partie": 1,
            },
        }
    ]


# EXIF

EXIF_COMPLET = tiff(
    (
        ascii_(0x010F, "Canon"),
        ascii_(0x0110, "EOS 5D"),
        nombres(0x0112, 3, 1),
        fractions(0x011A, (72, 1)),
        ascii_(0x0131, "Logiciel 2.0"),
        ascii_(0x013B, "Jean Dupont"),
        nombres(0x9C9D, 1, *"Auteur".encode("utf-16-le")),
        Sous(
            0x8769,
            (
                fractions(0x829A, (1, 250)),
                fractions(0x9204, (-1, 3), signe=True),
                fractions(0x9206, (5, 0)),
                indefini(0x9000, b"0232"),
                indefini(0x9101, b"\x01\x02\x03\x00"),
                indefini(0x9286, b"ASCII\x00\x00\x00Bonjour  \x00"),
                indefini(0x927C, b"\x00" * 40),
                indefini(0xA302, b"\x00\x02\x00\x02\x01\x02\x00\x01"),
                ascii_(0xA431, "SN-1234"),
                nombres(0x8827, 3, 100, 200),
                nombres(0xA460, 3),
                (0xA436, 129, 7, "Été 1\x00".encode()),
                nombres(0x9400, 12, 21.5),
                nombres(0x9401, 11, float("nan")),
                nombres(0x1234, 4, 7),
                Sous(0xA005, (ascii_(0x0001, "R98"), indefini(0x0002, b"0100"))),
            ),
        ),
        Sous(
            0x8825,
            (
                nombres(0x0000, 1, 2, 3, 0, 0),
                ascii_(0x0001, "N"),
                fractions(0x0002, (48, 1), (51, 1), (0, 1)),
            ),
        ),
    ),
    (nombres(0x0201, 4, 1234), nombres(0x0202, 4, 56)),
)


def test_exif_jpeg() -> None:
    lignes = resultats("exif", jpeg_meta(app1_exif(EXIF_COMPLET)), "jpeg")
    lues = valeurs_de(lignes)
    assert lues == {
        "exif.present": True,
        "exif.blocs": 1,
        "exif.ordre": "MM",
        "exif.ifd0.Make": "Canon",
        "exif.ifd0.Model": "EOS 5D",
        "exif.ifd0.Orientation": 1,
        "exif.ifd0.XResolution": 72.0,
        "exif.ifd0.Software": "Logiciel 2.0",
        "exif.ifd0.Artist": "Jean Dupont",
        "exif.ifd0.XPAuthor": "Auteur",
        "exif.exif.ExposureTime": 0.004,
        "exif.exif.ExposureBiasValue": pytest.approx(-1 / 3),
        "exif.exif.SubjectDistance": "5/0",
        "exif.exif.ExifVersion": "0232",
        "exif.exif.ComponentsConfiguration": [1, 2, 3, 0],
        "exif.exif.UserComment": "Bonjour",
        "exif.exif.MakerNote.taille": 40,
        "exif.exif.CFAPattern.taille": 8,
        "exif.exif.BodySerialNumber": "SN-1234",
        "exif.exif.PhotographicSensitivity": [100, 200],
        "exif.exif.CompositeImage": [],
        "exif.exif.ImageTitle": "Été 1",
        "exif.exif.Temperature": 21.5,
        "exif.exif.Humidity": "nan",
        "exif.exif.0x1234": 7,
        "exif.interop.InteroperabilityIndex": "R98",
        "exif.interop.InteroperabilityVersion": "0100",
        "exif.gps.GPSVersionID": [2, 3, 0, 0],
        "exif.gps.GPSLatitudeRef": "N",
        "exif.gps.GPSLatitude": [48.0, 51.0, 0.0],
        "exif.ifd1.JPEGInterchangeFormat": 1234,
        "exif.ifd1.JPEGInterchangeFormatLength": 56,
    }
    assert raisons(lignes) == []
    unites = {o["nom"]: o.get("unite") for o in observations(lignes)}
    assert unites["exif.exif.MakerNote.taille"] == "octets"
    localisations = {o["nom"]: o.get("localisation") for o in observations(lignes)}
    assert localisations["exif.gps.GPSLatitude"] == {
        "chemin": "APP1 Exif / gps",
        "octets": {"debut": 12, "longueur": len(EXIF_COMPLET)},
    }


@pytest.mark.exigence("ES-13", "F-90")
def test_exif_donnees_identifiantes() -> None:
    lignes = resultats("exif", jpeg_meta(app1_exif(EXIF_COMPLET)), "jpeg")
    marquees = identifiantes(lignes)
    assert marquees == {
        "exif.ifd0.Artist": "metadonnee_nominative",
        "exif.ifd0.XPAuthor": "metadonnee_nominative",
        "exif.exif.BodySerialNumber": "numero_de_serie",
        "exif.gps.GPSVersionID": "gps",
        "exif.gps.GPSLatitudeRef": "gps",
        "exif.gps.GPSLatitude": "gps",
    }


def test_exif_ordre_intel_et_commentaires() -> None:
    donnees = tiff(
        (
            ascii_(0x010D, "photo.jpg"),
            Sous(
                0x8769,
                (
                    indefini(0x9286, b"UNICODE\x00" + "Hé".encode("utf-16-le")),
                    indefini(0xA300, b"\x03"),
                    ascii_(0xA004, b"son\xe9.wav"),
                ),
            ),
            Sous(
                0x8825,
                (
                    indefini(0x001B, b"JIS\x00\x00\x00\x00\x00" + "東京".encode("shift_jis")),
                    indefini(0x001C, b"\x00" * 8 + b"zone"),
                ),
            ),
        ),
        ordre="<",
    )
    lignes = resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg")
    lues = valeurs_de(lignes)
    assert lues["exif.ordre"] == "II"
    assert lues["exif.exif.UserComment"] == "Hé"
    assert lues["exif.exif.FileSource"] == 3
    assert lues["exif.exif.RelatedSoundFile"] == "soné.wav"  # Latin-1, faute d'UTF-8 valide
    assert lues["exif.gps.GPSProcessingMethod"] == "東京"
    assert lues["exif.gps.GPSAreaInformation"] == "zone"
    assert identifiantes(lignes)["exif.ifd0.DocumentName"] == "nom_de_fichier"


def test_exif_commentaire_unicode_motorola() -> None:
    donnees = tiff((Sous(0x8769, (indefini(0x9286, b"UNICODE\x00" + "Hé".encode("utf-16-be")),)),))
    lues = valeurs_de(resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg"))
    assert lues["exif.exif.UserComment"] == "Hé"


@pytest.mark.parametrize(
    ("format_", "contenu"),
    [
        ("png", png_meta(bloc_png(b"eXIf", tiff((ascii_(0x010F, "Nikon"),))))),
        ("webp", webp_meta(bloc_riff(b"EXIF", tiff((ascii_(0x010F, "Nikon"),))))),
        ("webp", webp_meta(bloc_riff(b"EXIF", b"Exif\x00\x00" + tiff((ascii_(0x010F, "Nikon"),))))),
        (
            "heic",
            heic_meta(Element(1, b"Exif", b"\x00\x00\x00\x00" + tiff((ascii_(0x010F, "Nikon"),)))),
        ),
        (
            "heic",
            heic_meta(
                Element(
                    1, b"Exif", b"\x00\x00\x00\x06Exif\x00\x00" + tiff((ascii_(0x010F, "Nikon"),))
                ),
                methode=1,
            ),
        ),
        (
            "heic",
            heic_meta(
                Element(
                    2, b"Exif", b"\x00\x00\x00\x00" + tiff((ascii_(0x010F, "Nikon"),)), morceaux=3
                )
            ),
        ),
    ],
)
def test_exif_autres_formats(format_: str, contenu: bytes) -> None:
    lues = valeurs_de(resultats("exif", contenu, format_))
    assert lues["exif.ifd0.Make"] == "Nikon"


def test_exif_heic_morcele_sans_plage() -> None:
    contenu = heic_meta(Element(2, b"Exif", b"\x00" * 4 + tiff((ascii_(0x010F, "N"),)), morceaux=2))
    [ordre] = [
        o for o in observations(resultats("exif", contenu, "heic")) if o["nom"] == "exif.ordre"
    ]
    assert ordre["localisation"] == {"chemin": "élément Exif 2"}


def test_exif_plusieurs_blocs() -> None:
    contenu = jpeg_meta(
        app1_exif(tiff((ascii_(0x010F, "A"),))), app1_exif(tiff((ascii_(0x010F, "B"),)))
    )
    lignes = resultats("exif", contenu, "jpeg")
    assert valeurs_de(lignes)["exif.blocs"] == 2
    assert [o["valeur"] for o in observations(lignes) if o["nom"] == "exif.ifd0.Make"] == ["A", "B"]


@pytest.mark.exigence("NF-03")
@pytest.mark.parametrize(
    "donnees",
    [
        pytest.param(b"XX*\x00\x00\x00\x00\x08", id="en-tete"),
        pytest.param(b"MM\x00*", id="court"),
        pytest.param(b"MM\x00*\x00\x00\x00\x40", id="ifd-hors-bloc"),
        pytest.param(tiff((ascii_(0x010F, "x" * 40),))[:-20], id="valeur-hors-bloc"),
        pytest.param(tiff(((0x010F, 99, 1, b"\x00"),)), id="type-inconnu"),
        pytest.param(tiff((ascii_(0x010F, "N"),))[:20], id="repertoire-coupe"),
        pytest.param(
            b"MM\x00*\x00\x00\x00\x08\x00\x01"
            + struct.pack(">HHII", 0x8769, 4, 1, 8)
            + b"\x00" * 4,
            id="boucle",
        ),
    ],
)
def test_exif_partiel(donnees: bytes) -> None:
    lignes = resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg")
    assert raisons(lignes) == ["format_partiel"]
    assert valeurs_de(lignes)["exif.present"] is True


def test_exif_heic_decalage_absent() -> None:
    lignes = resultats("exif", heic_meta(Element(1, b"Exif", b"\x00\x00")), "heic")
    assert raisons(lignes) == ["format_partiel"]


def test_exif_valeurs_longues() -> None:
    donnees = tiff(
        (
            ascii_(0x010E, "a" * (LONGUEUR_MAX_TEXTE + 10)),
            nombres(0x0111, 4, *range(NOMBRE_MAX_ELEMENTS + 5)),
        )
    )
    lignes = resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg")
    lues = valeurs_de(lignes)
    assert lues["exif.ifd0.ImageDescription"] == "a" * LONGUEUR_MAX_TEXTE
    assert lues["exif.ifd0.ImageDescription.longueur"] == LONGUEUR_MAX_TEXTE + 10
    assert lues["exif.ifd0.StripOffsets"] == list(range(NOMBRE_MAX_ELEMENTS))
    assert lues["exif.ifd0.StripOffsets.longueur"] == NOMBRE_MAX_ELEMENTS + 5


def test_exif_repertoires_chaines_numerotes() -> None:
    donnees = tiff((ascii_(0x010F, "A"),), (nombres(0x0100, 3, 1),), (nombres(0x0100, 3, 2),))
    lues = valeurs_de(resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg"))
    assert lues["exif.ifd1.ImageWidth"] == 1
    assert lues["exif.ifd2.ImageWidth"] == 2


def test_exif_pointeur_gps_dans_gps_ignore() -> None:
    # Dans le répertoire GPS, 0x8769 n'est pas un pointeur : c'est une étiquette inconnue.
    donnees = tiff((Sous(0x8825, (nombres(0x8769, 4, 8),)),))
    lues = valeurs_de(resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg"))
    assert lues["exif.gps.0x8769"] == 8


# Conteneurs


@pytest.mark.exigence("NF-03")
@pytest.mark.parametrize(
    ("format_", "contenu", "raison"),
    [
        ("jpeg", b"\xff\xd8" + app1_exif(tiff(()))[:5], "fichier_tronque"),
        ("jpeg", b"\xff\xd8\xff", "fichier_tronque"),
        ("jpeg", b"\xff\xd8\x00\x00", "format_partiel"),
        ("jpeg", b"\xff\xd8\xff\xe1", "fichier_tronque"),
        ("jpeg", b"\xff\xd8\xff\xe1\x00\x01", "format_partiel"),
        ("jpeg", b"\xff\xd8\xff\xd8\x00\x04", "format_partiel"),
        ("png", png()[:-6], "fichier_tronque"),
        ("png", png()[:8] + b"\x80\x00\x00\x00tEXt", "format_partiel"),
        ("png", png()[:8] + b"\x00\x00\x00\x40tEXt", "fichier_tronque"),
        ("webp", b"RIFF\x00\x00", "fichier_tronque"),
        ("webp", webp_meta(bloc_riff(b"EXIF", b"\x00" * 10))[:-4], "fichier_tronque"),
        ("webp", webp_meta() + b"\x00\x00", "fichier_tronque"),
        ("heic", heic_meta(Element(1, b"Exif", b"\x00" * 8))[:60], "fichier_tronque"),
        ("heic", boite(b"meta", b"\x00\x00"), "format_partiel"),
        ("heic", struct.pack(">I", 4) + b"meta", "format_partiel"),
    ],
)
def test_conteneur_interrompu(format_: str, contenu: bytes, raison: str) -> None:
    webp_court = format_ == "webp" and len(contenu) > 12
    contenu = (
        contenu
        if not webp_court
        else contenu[:4] + struct.pack("<I", len(contenu) - 8) + contenu[8:]
    )
    lignes = resultats("exif", contenu, format_)
    assert raisons(lignes)[-1:] == [raison]
    [arret] = [ligne["non_menee"] for ligne in lignes if ligne["type"] == "non_menee"][-1:]
    assert arret["localisation"]["chemin"] == "structure du conteneur"


def test_jpeg_remplissage_marqueurs_sans_longueur_et_segments_vides() -> None:
    contenu = jpeg_meta(
        b"\xff\xff\xff\x01\xff\xd0",
        segment(0xE1, b"Exif\x00\x00"),
        segment(0xE1, b"http://ns.adobe.com/xap/1.0/\x00"),
        segment(0xE1, b"autre chose"),
        segment(0xE2, b"ICC_PROFILE\x00"),
        app1_exif(tiff((ascii_(0x010F, "N"),))),
    )
    assert valeurs_de(resultats("exif", contenu, "jpeg"))["exif.ifd0.Make"] == "N"
    assert valeurs_de(resultats("xmp", contenu, "jpeg")) == {"xmp.present": False}


def test_jpeg_s_arrete_a_eoi() -> None:
    contenu = b"\xff\xd8\xff\xd9" + app1_exif(tiff((ascii_(0x010F, "N"),)))
    assert valeurs_de(resultats("exif", contenu, "jpeg")) == {"exif.present": False}


def test_bloc_trop_grand_pour_une_lecture(monkeypatch: pytest.MonkeyPatch) -> None:
    from voight_kampff.modules._lecture import conteneurs

    monkeypatch.setattr(conteneurs, "TAILLE_MAX_LECTURE", 4)
    lignes = resultats("exif", png_meta(bloc_png(b"eXIf", tiff(()))), "png")
    assert raisons(lignes) == ["format_partiel"]


@pytest.mark.parametrize(
    "contenu",
    [
        pytest.param(heic_meta(Element(1, b"Exif", b"\x00" * 8), reference=1), id="autre-fichier"),
        pytest.param(heic_meta(Element(1, b"Exif", b"\x00" * 8), methode=2), id="methode-2"),
        pytest.param(heic_meta(Element(1, b"Exif", b"\x00" * 8), methode=1)[:-30], id="idat-court"),
    ],
)
def test_heic_emplacement_non_lu(contenu: bytes) -> None:
    lignes = resultats("exif", contenu, "heic")
    assert raisons(lignes)[-1:] in (["format_partiel"], ["fichier_tronque"])


def test_heic_sans_meta_ni_iloc() -> None:
    assert raisons(resultats("exif", boite(b"ftyp", b"heic"), "heic")) == []
    sans_iloc = heic_meta(Element(1, b"Exif", b"\x00" * 8)).replace(b"iloc", b"ilox")
    assert raisons(resultats("exif", sans_iloc, "heic")) == []


def test_heic_elements_ignores_et_xmp() -> None:
    paquet = xmp("<dc:format>image/heic</dc:format>")
    contenu = heic_meta(
        Element(1, b"hvc1", b"\x00" * 4),
        Element(2, b"mime", paquet, b"application/rdf+xml"),
        Element(3, b"mime", b"<a/>", b"text/plain"),
        Element(4, b"Exif", b"\x00" * 8, version=1),
    )
    lues = valeurs_de(resultats("xmp", contenu, "heic"))
    assert lues["xmp.dc:format"] == "image/heic"
    assert valeurs_de(resultats("exif", contenu, "heic")) == {"exif.present": False}


def test_heic_boites_particulieres() -> None:
    # Boîte de taille 64 bits et boîte « jusqu'à la fin » parmi les enfants de meta ;
    # boîte iloc de version 0 ou 2 ; infe de version 3.
    exif = b"\x00" * 4 + tiff((ascii_(0x010F, "N"),))
    grande = struct.pack(">I", 1) + b"free" + struct.pack(">Q", 16)
    jusqua_la_fin = b"\x00\x00\x00\x00skip"
    for contenu in (
        heic_meta(Element(1, b"Exif", exif), autres=grande + jusqua_la_fin),
        heic_meta(Element(1, b"Exif", exif), version_iloc=0),
        heic_meta(Element(1, b"Exif", exif, version=3), version_iloc=2),
    ):
        lignes = resultats("exif", contenu, "heic")
        assert valeurs_de(lignes)["exif.ifd0.Make"] == "N"
        assert raisons(lignes) == []
    coupe = heic_meta(Element(1, b"Exif", exif), autres=struct.pack(">I", 1) + b"free")
    assert raisons(resultats("exif", coupe, "heic")) == ["fichier_tronque"]


def test_heic_iloc_tailles_invalides() -> None:
    contenu = heic_meta(Element(1, b"Exif", b"\x00" * 8))
    position = contenu.index(b"iloc") + 8
    abime = contenu[:position] + b"\x33" + contenu[position + 1 :]
    assert raisons(resultats("exif", abime, "heic")) == ["format_partiel"]


def test_heic_element_sans_emplacement() -> None:
    contenu = heic_meta(Element(1, b"Exif", b"\x00" * 8))
    position = contenu.index(b"iloc") + 10
    abime = contenu[:position] + b"\x00\x00" + contenu[position + 2 :]  # aucun emplacement
    assert raisons(resultats("exif", abime, "heic")) == ["format_partiel"]


def test_heic_etendue_vide_ou_hors_fichier() -> None:
    contenu = heic_meta(Element(1, b"Exif", b"\x00" * 8))
    position = contenu.index(b"iloc") + 4 + 4 + 2 + 2 + 2 + 2 + 2 + 2 + 4
    vide = contenu[:position] + b"\x00\x00\x00\x00" + contenu[position + 4 :]
    assert raisons(resultats("exif", vide, "heic")) == ["format_partiel"]
    loin = contenu[:position] + b"\x00\x01\x00\x00" + contenu[position + 4 :]
    assert raisons(resultats("exif", loin, "heic")) == ["fichier_tronque"]


def test_heic_curseur_coupe() -> None:
    contenu = heic_meta(Element(1, b"mime", b"x", b"application/rdf+xml"))
    position = contenu.index(b"application/rdf+xml") + len(b"application/rdf+xml")
    abime = contenu[:position] + b"!" + contenu[position + 1 :]  # chaîne sans fin
    assert raisons(resultats("xmp", abime, "heic")) == ["format_partiel"]
    iloc = contenu.index(b"iloc")
    coupe = (
        contenu[: iloc - 4]
        + struct.pack(">I", 14)
        + b"iloc\x01\x00\x00\x00\x44\x00"
        + contenu[iloc + 10 :]
    )
    assert raisons(resultats("xmp", coupe, "heic"))[-1:] in (
        ["format_partiel"],
        ["fichier_tronque"],
    )


def test_releve_par_nature() -> None:
    contenu = jpeg_meta(app1_exif(tiff(())), app1_xmp(xmp("")), app13(ressource(0x0404, b"")))
    with tempfile.TemporaryFile() as fichier:
        releve = relever(contexte(fichier, contenu, "jpeg", "exif"))
    assert [bloc.nature for bloc in releve.blocs] == [Nature.EXIF, Nature.XMP, Nature.PHOTOSHOP]
    assert releve.arret is None


# XMP


def test_xmp_proprietes() -> None:
    espaces = (
        f'xmlns:dc="{DC}" xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"'
        ' xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#"'
        ' xmlns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#"'
        ' xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"'
        ' xmlns:exif="http://ns.adobe.com/exif/1.0/" xmlns:faux="http://exemple.org/faux/"'
        ' xmlns:autre="http://exemple.org/autre/" xmlns:xmp="http://ns.adobe.com/xap/1.0/"'
    )
    description = (
        "<dc:creator><rdf:Seq><rdf:li>Jean</rdf:li><rdf:li>Marie</rdf:li></rdf:Seq></dc:creator>"
        '<dc:title><rdf:Alt><rdf:li xml:lang="x-default">Titre</rdf:li></rdf:Alt></dc:title>'
        "<xmpMM:History><rdf:Seq>"
        '<rdf:li rdf:parseType="Resource"><stEvt:action>created</stEvt:action></rdf:li>'
        '<rdf:li><rdf:Description stEvt:action="saved"/></rdf:li>'
        "</rdf:Seq></xmpMM:History>"
        '<xmpMM:DerivedFrom stRef:filePath="C:\\photo.psd"/>'
        "<Iptc4xmpExt:DigitalSourceType rdf:resource="
        '"http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"/>'
        "<exif:GPSLatitude>48,51.0N</exif:GPSLatitude>"
        "<faux:Valeur><rdf:Description><rdf:value>42</rdf:value></rdf:Description></faux:Valeur>"
        "<autre:Qualifiee><rdf:value>7</rdf:value></autre:Qualifiee>"
        "<faux:Nom_Avec.Point>x</faux:Nom_Avec.Point>"
        "<xmp:Vide/>"
    )
    paquet = xmp(description, espaces=espaces, attributs='xmp:CreatorTool="Générateur 3"')
    lignes = resultats("xmp", jpeg_meta(app1_xmp(paquet)), "jpeg")
    assert valeurs_de(lignes) == {
        "xmp.present": True,
        "xmp.blocs": 1,
        "xmp.espace.ns1": "http://exemple.org/faux/",
        "xmp.espace.ns2": "http://exemple.org/autre/",
        "xmp.x:xmptk": "Outil 1.0",
        "xmp.xmp:CreatorTool": "Générateur 3",
        "xmp.dc:creator": ["Jean", "Marie"],
        "xmp.dc:title": ["Titre"],
        "xmp.xmpMM:History.stEvt:action": ["created", "saved"],
        "xmp.xmpMM:DerivedFrom.stRef:filePath": "C:\\photo.psd",
        "xmp.Iptc4xmpExt:DigitalSourceType": (
            "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
        ),
        "xmp.exif:GPSLatitude": "48,51.0N",
        "xmp.ns1:Valeur": "42",
        "xmp.ns2:Qualifiee": "7",
        "xmp.ns1:Nom-Avec-Point": "x",
        "xmp.xmp:Vide": "",
    }
    assert raisons(lignes) == []


@pytest.mark.exigence("ES-13", "F-90")
def test_xmp_donnees_identifiantes() -> None:
    espaces = (
        f'xmlns:dc="{DC}" xmlns:aux="http://ns.adobe.com/exif/1.0/aux/"'
        ' xmlns:exif="http://ns.adobe.com/exif/1.0/"'
        ' xmlns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#"'
        ' xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"'
    )
    description = (
        "<dc:creator><rdf:Seq><rdf:li>Jean</rdf:li></rdf:Seq></dc:creator>"
        "<aux:SerialNumber>123</aux:SerialNumber>"
        "<exif:GPSLongitude>2,20E</exif:GPSLongitude>"
        '<xmpMM:DerivedFrom stRef:filePath="a.psd"/>'
        "<dc:format>image/jpeg</dc:format>"
    )
    lignes = resultats("xmp", jpeg_meta(app1_xmp(xmp(description, espaces=espaces))), "jpeg")
    assert identifiantes(lignes) == {
        "xmp.dc:creator": "metadonnee_nominative",
        "xmp.aux:SerialNumber": "numero_de_serie",
        "xmp.exif:GPSLongitude": "gps",
        "xmp.xmpMM:DerivedFrom.stRef:filePath": "nom_de_fichier",
    }


def test_xmp_prefixe_usurpe() -> None:
    # Le préfixe « dc » déclaré pour une autre adresse ne donne pas « dc:creator ».
    paquet = xmp("<dc:creator>Faux</dc:creator>", espaces='xmlns:dc="http://exemple.org/faux/"')
    lues = valeurs_de(resultats("xmp", jpeg_meta(app1_xmp(paquet)), "jpeg"))
    assert "xmp.dc:creator" not in lues
    assert lues["xmp.ns1:creator"] == "Faux"
    assert lues["xmp.espace.ns1"] == "http://exemple.org/faux/"


@pytest.mark.exigence("ES-05", "NF-01")
@pytest.mark.parametrize(
    "paquet",
    [
        pytest.param(
            b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><x>&a;</x>', id="entite"
        ),
        pytest.param(
            b'<?xml version="1.0"?><!DOCTYPE x SYSTEM "http://exemple.org/x.dtd"><x/>',
            id="dtd-externe",
        ),
        pytest.param(
            b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>', id="entite-externe"
        ),
        pytest.param(
            b'<!DOCTYPE x [<!ENTITY a "a"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">]><x>&b;</x>',
            id="milliard-de-rires",
        ),
        pytest.param(b"<x>&inconnue;</x>", id="entite-non-declaree"),
        pytest.param(xmp("<dc:format>a</dc:format>")[:-40], id="coupe"),
    ],
)
def test_xmp_refuse_dtd_et_entites(paquet: bytes) -> None:
    lignes = resultats("xmp", jpeg_meta(app1_xmp(paquet)), "jpeg")
    assert raisons(lignes) == ["format_partiel"]
    assert all(
        not o["nom"].startswith("xmp.x") or o["nom"] == "xmp.x:xmptk" for o in observations(lignes)
    )
    assert "passwd" not in json.dumps(lignes)


def test_xmp_entite_externe_refusee(monkeypatch: pytest.MonkeyPatch) -> None:
    # Sans DTD, aucune entité externe ne peut être déclarée ; le gestionnaire refuse quand même.
    lecteurs: list[expat.XMLParserType] = []
    creer = expat.ParserCreate

    def espion(*arguments: Any, **options: Any) -> expat.XMLParserType:
        lecteurs.append(creer(*arguments, **options))
        return lecteurs[-1]

    monkeypatch.setattr(expat, "ParserCreate", espion)
    paquet = b'<x xmlns="u"><y/></x>'
    assert valeurs_de(resultats("xmp", jpeg_meta(app1_xmp(paquet)), "jpeg"))["xmp.present"]
    [lecteur] = lecteurs
    gestionnaire = lecteur.ExternalEntityRefHandler
    assert gestionnaire is not None
    with pytest.raises(lecture_xmp._Refus):
        gestionnaire("contexte", None, "http://x", None)


def test_xmp_partiel_garde_le_debut() -> None:
    paquet = xmp("<dc:format>image/png</dc:format><dc:source>s</dc:source>")
    coupe = paquet[: paquet.index(b"<dc:source>") + 3]
    lignes = resultats("xmp", jpeg_meta(app1_xmp(coupe)), "jpeg")
    assert valeurs_de(lignes)["xmp.dc:format"] == "image/png"
    assert raisons(lignes) == ["format_partiel"]


def test_xmp_sans_enveloppe_et_texte_hors_element() -> None:
    paquet = (
        f'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        f'<rdf:Description xmlns:dc="{DC}" dc:format="a"/><autre/></rdf:RDF>'
    ).encode()
    lues = valeurs_de(resultats("xmp", jpeg_meta(app1_xmp(b"<r>" + paquet + b"</r>")), "jpeg"))
    assert lues["xmp.dc:format"] == "a"


@pytest.mark.parametrize(
    ("format_", "contenu"),
    [
        (
            "png",
            png_meta(texte_international(b"XML:com.adobe.xmp", xmp("<dc:format>p</dc:format>"))),
        ),
        (
            "png",
            png_meta(
                texte_international(
                    b"XML:com.adobe.xmp", xmp("<dc:format>p</dc:format>"), compresse=True
                )
            ),
        ),
        ("webp", webp_meta(bloc_riff(b"XMP ", xmp("<dc:format>p</dc:format>")))),
        (
            "heic",
            heic_meta(Element(5, b"mime", xmp("<dc:format>p</dc:format>"), b"application/rdf+xml")),
        ),
    ],
)
def test_xmp_autres_formats(format_: str, contenu: bytes) -> None:
    assert valeurs_de(resultats("xmp", contenu, format_))["xmp.dc:format"] == "p"


def test_xmp_png_illisible() -> None:
    contenu = png_meta(
        texte_international(b"XML:com.adobe.xmp", b"x", compresse=True, methode=b"\x05")
    )
    assert raisons(resultats("xmp", contenu, "png")) == ["format_partiel"]


def test_xmp_etendu() -> None:
    etendu = xmp("<dc:format>etendu</dc:format>")
    guid = b"0123456789ABCDEF0123456789ABCDEF"
    principal_ = xmp(
        f"<xmpNote:HasExtendedXMP>{guid.decode()}</xmpNote:HasExtendedXMP>",
        espaces=f'xmlns:dc="{DC}" xmlns:xmpNote="http://ns.adobe.com/xmp/note/"',
    )
    moitie = len(etendu) // 2
    contenu = jpeg_meta(
        app1_xmp(principal_),
        app1_etendu(guid, len(etendu), moitie, etendu[moitie:]),
        app1_etendu(guid, len(etendu), 0, etendu[:moitie]),
    )
    lignes = resultats("xmp", contenu, "jpeg")
    lues = valeurs_de(lignes)
    assert lues["xmp.etendu.blocs"] == 2
    assert lues["xmp.dc:format"] == "etendu"
    assert raisons(lignes) == []


@pytest.mark.parametrize(
    "morceaux",
    [
        pytest.param(lambda g, e: [app1_etendu(g, len(e), 0, e[:10])], id="incomplet"),
        pytest.param(lambda g, e: [app1_etendu(b"F" * 32, len(e), 0, e)], id="non-designe"),
        pytest.param(lambda g, e: [app1_etendu(g, 4, 0, e)], id="deborde"),
        pytest.param(
            lambda g, e: [app1_etendu(g, len(e), 0, e), app1_etendu(g, len(e) + 1, 0, e)],
            id="totaux-differents",
        ),
        pytest.param(
            lambda g, e: [segment(0xE1, b"http://ns.adobe.com/xmp/extension/\x00abc")], id="court"
        ),
        pytest.param(lambda g, e: [app1_etendu(g, len(e), 5, e[5:])], id="trou"),
    ],
)
def test_xmp_etendu_ecarte(morceaux: Any) -> None:
    etendu = xmp("<dc:format>etendu</dc:format>")
    guid = b"0123456789ABCDEF0123456789ABCDEF"
    principal_ = xmp(
        f"<xmpNote:HasExtendedXMP>{guid.decode()}</xmpNote:HasExtendedXMP>",
        espaces=f'xmlns:dc="{DC}" xmlns:xmpNote="http://ns.adobe.com/xmp/note/"',
    )
    lignes = resultats("xmp", jpeg_meta(app1_xmp(principal_), *morceaux(guid, etendu)), "jpeg")
    assert "format_partiel" in raisons(lignes)
    # Un morceau d'un autre total est écarté ; le premier, complet à lui seul, est lu.
    lu = len(morceaux(guid, etendu)) == 2
    assert ("xmp.dc:format" in valeurs_de(lignes)) == lu


def test_xmp_tableaux_longs() -> None:
    elements = "".join(f"<rdf:li>{'m' * 100}</rdf:li>" for _ in range(400))
    paquet = xmp(f"<dc:subject><rdf:Bag>{elements}</rdf:Bag></dc:subject>")
    lues = valeurs_de(resultats("xmp", jpeg_meta(app1_xmp(paquet)), "jpeg"))
    assert len(lues["xmp.dc:subject"]) == valeurs.CARACTERES_MAX_LISTE // 100
    assert lues["xmp.dc:subject.longueur"] == 400


def test_xmp_profondeur_leve() -> None:
    profond = "<a>" * 80 + "</a>" * 80
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, jpeg_meta(app1_xmp(xmp(f"<dc:x>{profond}</dc:x>"))), "jpeg", "xmp")
        with pytest.raises(LimiteDepassee):
            importlib.import_module("voight_kampff.modules.xmp").analyser(c)
        assert c.depasse


# IPTC


def test_iptc() -> None:
    iim = (
        jeu(1, 90, b"\x1b%G")
        + jeu(2, 0, b"\x00\x04")
        + jeu(2, 25, "été".encode())
        + jeu(2, 25, b"mer")
        + jeu(2, 80, b"Jean")
        + jeu(2, 5, b"Titre")
        + jeu(2, 202, b"\x00" * 30)
        + jeu(2, 199, b"inconnu")
        + bytes([0x1C, 2, 120, 0x80, 0x02, 0x00, 0x03])
        + b"abc"
        + b"\x00\x00"
    )
    irb = ressource(0x0425, b"\x00" * 16) + ressource(0x0404, iim, nom=b"IPTC")
    lignes = resultats("iptc", jpeg_meta(app13(irb)), "jpeg")
    assert valeurs_de(lignes) == {
        "iptc.photoshop.ressources": [0x0425, 0x0404],
        "iptc.CodedCharacterSet": "\x1b%G",
        "iptc.ApplicationRecordVersion": 4,
        "iptc.Keywords": ["été", "mer"],
        "iptc.By-line": ["Jean"],
        "iptc.ObjectName": "Titre",
        "iptc.ObjectPreviewData.taille": 30,
        "iptc.2:199": "inconnu",
        "iptc.Caption-Abstract": "abc",
        "iptc.present": True,
    }
    assert identifiantes(lignes) == {"iptc.By-line": "metadonnee_nominative"}
    assert raisons(lignes) == []


def test_iptc_jeu_de_caracteres_par_defaut() -> None:
    iim = jeu(2, 5, "é".encode("latin-1")) + jeu(2, 105, "é".encode()) + jeu(2, 5, b"b")
    lues = valeurs_de(resultats("iptc", jpeg_meta(app13(ressource(0x0404, iim))), "jpeg"))
    assert lues["iptc.ObjectName"] == ["é", "b"]  # Latin-1 faute d'UTF-8 valide ; répété
    assert lues["iptc.Headline"] == "é"


def test_iptc_utf8_declare_et_octets_invalides() -> None:
    iim = jeu(1, 90, b"\x1b%G") + jeu(2, 5, b"\xff")
    lues = valeurs_de(resultats("iptc", jpeg_meta(app13(ressource(0x0404, iim))), "jpeg"))
    assert lues["iptc.ObjectName"] == "\ufffd"


def test_iptc_sans_ressource_iptc() -> None:
    lignes = resultats(
        "iptc", jpeg_meta(app13(ressource(0x0425, b"\x00" * 16, signature=b"PHUT"))), "jpeg"
    )
    assert valeurs_de(lignes) == {"iptc.photoshop.ressources": [0x0425], "iptc.present": False}


@pytest.mark.exigence("NF-03")
@pytest.mark.parametrize(
    "irb",
    [
        pytest.param(b"XXXX\x04\x04", id="signature"),
        pytest.param(b"8BIM\x04\x04\x00", id="nom-coupe"),
        pytest.param(b"8BIM\x04\x04\x00\x00\x00\x00", id="taille-coupee"),
        pytest.param(b"8BIM\x04\x04\x00\x00\x00\x00\x00\x10abc", id="donnees-coupees"),
        pytest.param(ressource(0x0404, b"\x01\x02"), id="iim-desynchronise"),
        pytest.param(ressource(0x0404, b"\x1c\x02\x05\x00"), id="iim-coupe"),
        pytest.param(ressource(0x0404, b"\x1c\x02\x05\x00\x10abc"), id="valeur-coupee"),
        pytest.param(ressource(0x0404, b"\x1c\x02\x05\x80\x09"), id="longueur-etendue-invalide"),
        pytest.param(ressource(0x0404, b"\x1c\x02\x05\x80\x02\x00"), id="longueur-etendue-coupee"),
    ],
)
def test_iptc_partiel(irb: bytes) -> None:
    lignes = resultats("iptc", jpeg_meta(app13(irb)), "jpeg")
    assert raisons(lignes) == ["format_partiel"]


def test_iptc_arret_du_conteneur() -> None:
    lignes = resultats("iptc", b"\xff\xd8" + app13(ressource(0x0404, b""))[:10], "jpeg")
    assert raisons(lignes) == ["fichier_tronque"]


# Blocs texte PNG


def test_textepng() -> None:
    contenu = png_meta(
        texte(b"parameters", b"Steps: 20, Sampler: Euler"),
        texte(b"Author", "Jérôme".encode("latin-1")),
        texte_compresse(b"Comment", b"compresse"),
        texte_international(b"Description", "légende".encode(), langue=b"fr"),
        texte_international(b"Title", b"titre", compresse=True),
        texte_international(b"XML:com.adobe.xmp", xmp("")),
        texte(b"Creation Time", b"2026"),
    )
    lignes = resultats("textepng", contenu, "png")
    assert valeurs_de(lignes) == {
        "textepng.present": True,
        "textepng.blocs": 6,
        "textepng.parameters": "Steps: 20, Sampler: Euler",
        "textepng.Author": "Jérôme",
        "textepng.Comment": "compresse",
        "textepng.Description": "légende",
        "textepng.Description.langue": "fr",
        "textepng.Title": "titre",
        "textepng.Creation-Time": "2026",
    }
    assert identifiantes(lignes) == {"textepng.Author": "metadonnee_nominative"}


@pytest.mark.exigence("NF-02", "ES-03")
def test_textepng_bombe_de_decompression() -> None:
    bombe = bloc_png(b"zTXt", b"k\x00\x00" + zlib.compress(b"\x00" * (600 << 20), 9))
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, png_meta(bombe), "png", "textepng")
        with pytest.raises(LimiteDepassee):
            importlib.import_module("voight_kampff.modules.textepng").analyser(c)


@pytest.mark.parametrize(
    "bloc",
    [
        pytest.param(texte_compresse(b"k", b"x", methode=b"\x01"), id="ztxt-methode"),
        pytest.param(bloc_png(b"zTXt", b"k\x00\x00pas du zlib"), id="ztxt-invalide"),
        pytest.param(
            texte_international(b"k", b"x", compresse=True, methode=b"\x02"), id="itxt-methode"
        ),
        pytest.param(texte_international(b"k", b"x", drapeau=b"\x07"), id="itxt-drapeau"),
        pytest.param(
            texte_international(b"k", b"x", drapeau=b"\x01", langue=b"de"), id="itxt-invalide"
        ),
    ],
)
def test_textepng_illisible(bloc: bytes) -> None:
    lignes = resultats("textepng", png_meta(bloc), "png")
    assert raisons(lignes) == ["format_partiel"]
    assert valeurs_de(lignes) == {"textepng.present": True, "textepng.blocs": 1}


def test_textepng_texte_long_et_arret() -> None:
    contenu = png_meta(texte(b"k", b"a" * 5000))
    lues = valeurs_de(resultats("textepng", contenu, "png"))
    assert lues["textepng.k.longueur"] == 5000
    lignes = resultats("textepng", contenu[:-6], "png")
    assert raisons(lignes) == ["fichier_tronque"]


# Valeurs, noms et budget


def test_valeurs_bornees() -> None:
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, b"x", "png", "textepng")
        valeurs.observer(c, "a", ["x" * 5000, "y"])
        valeurs.observer(c, "b", list(range(NOMBRE_MAX_ELEMENTS + 1)))
        valeurs.observer(c, "c", True, unite="octets")
        lues = {o["nom"]: o for o in (json.loads(ligne)["observation"] for ligne in c.lignes)}
    assert lues["a"]["valeur"] == ["x" * LONGUEUR_MAX_TEXTE, "y"]
    assert lues["a.longueur"]["valeur"] == 2
    assert lues["b.longueur"]["valeur"] == NOMBRE_MAX_ELEMENTS + 1
    assert lues["c"]["unite"] == "octets"
    assert valeurs.nombre(1e300) == "1e+300"
    assert valeurs.nombre(float("-inf")) == "-inf"
    assert valeurs.composant("a b_c.d") == "a-b-c-d"
    assert len(valeurs.borner("x" * 200) + ".longueur") == 128


def test_nombre_de_resultats_borne() -> None:
    # Un bloc par résultat : au-delà de RESULTATS_MAX, la limite comptée arrête le module.
    contenu = png_meta(*(texte(b"k", b"v") for _ in range(RESULTATS_MAX)))
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, contenu, "png", "textepng")
        with pytest.raises(LimiteDepassee):
            importlib.import_module("voight_kampff.modules.textepng").analyser(c)
        assert c.depasse


# Cas rares des structures


def test_webp_exif_reduit_au_prefixe() -> None:
    contenu = webp_meta(bloc_riff(b"EXIF", b"Exif\x00\x00"))
    assert valeurs_de(resultats("exif", contenu, "webp")) == {"exif.present": False}


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        pytest.param(
            boite(b"ftyp", b"heic") + b"\x00\x00\x00\x01free", "fichier_tronque", id="64-bits-coupe"
        ),
        pytest.param(boite(b"ftyp", b"heic") + b"\x00\x00", "fichier_tronque", id="reste"),
        pytest.param(
            heic_meta(
                Element(1, b"Exif", b"\x00" * 8), iloc_brut=boite(b"iloc", b"\x01\x00\x00\x00\x44")
            ),
            "format_partiel",
            id="iloc-court",
        ),
        pytest.param(
            heic_meta(Element(1, b"Exif", b"\x00" * 8, morceaux=0)),
            "format_partiel",
            id="sans-etendue",
        ),
    ],
)
def test_heic_structures_rares(contenu: bytes, raison: str) -> None:
    assert raisons(resultats("exif", contenu, "heic")) == [raison]


def test_heic_enfant_de_iinf_inconnu_et_element_trop_grand(monkeypatch: pytest.MonkeyPatch) -> None:
    contenu = heic_meta(Element(1, b"Exif", b"\x00" * 4 + tiff(())))
    assert valeurs_de(resultats("exif", contenu.replace(b"infe", b"xxxx"), "heic")) == {
        "exif.present": False
    }
    from voight_kampff.modules._lecture import conteneurs

    monkeypatch.setattr(conteneurs, "TAILLE_MAX_LECTURE", 8)
    assert raisons(resultats("exif", contenu, "heic")) == ["format_partiel"]


def test_xmp_formes_tolerees() -> None:
    # Structure sans parseType, élément étranger dans un tableau, élément RDF inattendu.
    description = (
        "<dc:struct><dc:champ>v</dc:champ><rdf:autre>w</rdf:autre></dc:struct>"
        "<dc:liste><rdf:Bag><dc:intrus>x</dc:intrus><rdf:li>y</rdf:li></rdf:Bag></dc:liste>"
    )
    lues = valeurs_de(resultats("xmp", jpeg_meta(app1_xmp(xmp(description))), "jpeg"))
    assert lues["xmp.dc:struct.dc:champ"] == "v"
    assert lues["xmp.dc:liste"] == ["y"]


@pytest.mark.exigence("NF-03")
def test_segment_et_boite_vides() -> None:
    # Trouvés par le fuzzing : un segment JPEG de longueur 2, une boîte iinf sans contenu.
    contenu = jpeg_meta(b"\xff\xe1\x00\x02", app1_exif(tiff((ascii_(0x010F, "N"),))))
    assert valeurs_de(resultats("exif", contenu, "jpeg"))["exif.ifd0.Make"] == "N"
    heic = heic_meta(Element(1, b"Exif", b"\x00" * 8))
    iinf = heic.index(b"iinf") - 4
    longueur = int.from_bytes(heic[iinf : iinf + 4], "big")
    vide = heic[:iinf] + boite(b"iinf") + b"\x00" * (longueur - 8) + heic[iinf + longueur :]
    vide = vide.replace(b"\x00" * (longueur - 8), boite(b"free", b"\x00" * (longueur - 16)), 1)
    assert raisons(resultats("exif", vide, "heic")) == ["format_partiel"]
