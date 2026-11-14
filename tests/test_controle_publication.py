"""Contrôle avant publication : marques identifiantes des métadonnées (T25, F-90).

Décisions : ADR-0158 (rubrique et ligne du résumé), ADR-0159 (catégories « lieu » et « texte
libre »), ADR-0160 (champs marqués), ADR-0161 (valeur FBMD). Chaque module a un test par
catégorie qu'il produit (ADR-0057) : ceux qui ne sont pas ici sont dans ``test_metadonnees.py``,
``test_metadonnees_medias.py``, ``test_metadonnees_pdf.py`` et ``test_metadonnees_bureautique``.
"""

import dataclasses
import json
import re
from pathlib import Path

import pytest
from bureautique import core, custom, docx_
from conftest import construire_rapport
from medias import (
    bloc_flac,
    commentaires,
    donnee,
    flac,
    liste_info,
    meta_mdta,
    quicktime,
    simple,
    tag,
    tags,
    wav,
    webm,
)
from metadonnees import (
    Sous,
    app1_exif,
    app1_xmp,
    app13,
    ascii_,
    fractions,
    identifiantes,
    jeu,
    jpeg_image,
    jpeg_meta,
    nombres,
    ressource,
    resultats,
    tiff,
    xmp,
)
from test_rapport import analyse_de
from test_transfert import FBMD, instructions, t24

from voight_kampff import exporter_html, exporter_json
from voight_kampff._travail import garde
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.cli import construire_analyseur, resume
from voight_kampff.rapport._presentation import Presentation, texte
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    Observation,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("F-90", "ES-13")

LIEU = "lieu"
LIBRE = "texte_libre"
TOUTES = [categorie.value for categorie in CategorieIdentifiante]


# Champs marqués par les modules (ADR-0160)


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Les modules s'exécutent ici hors d'un processus de travail (ES-17), comme dans
    # test_metadonnees.py.
    monkeypatch.setattr(garde, "_verrouille", True)


def test_exif_textes_libres() -> None:
    donnees = tiff(
        (
            ascii_(0x010E, "Légende"),
            ascii_(0x010F, "Canon"),
            ascii_(0x011D, "Page 1"),
            nombres(0x9C9B, 1, *"Titre".encode("utf-16-le")),
            nombres(0x9C9C, 1, *"Note".encode("utf-16-le")),
            nombres(0x9C9E, 1, *"a;b".encode("utf-16-le")),
            nombres(0x9C9F, 1, *"Sujet".encode("utf-16-le")),
        )
    )
    lignes = resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg")
    assert identifiantes(lignes) == {
        "exif.ifd0.ImageDescription": LIBRE,
        "exif.ifd0.PageName": LIBRE,
        "exif.ifd0.XPTitle": LIBRE,
        "exif.ifd0.XPComment": LIBRE,
        "exif.ifd0.XPKeywords": LIBRE,
        "exif.ifd0.XPSubject": LIBRE,
    }


def test_exif_gps_reste_gps() -> None:
    # La zone nommée du répertoire GPS est un texte, mais tout le répertoire reste GPS.
    donnees = tiff((Sous(0x8825, (fractions(0x0002, (48, 1), (51, 1), (0, 1)),)),))
    lignes = resultats("exif", jpeg_meta(app1_exif(donnees)), "jpeg")
    assert identifiantes(lignes) == {"exif.gps.GPSLatitude": "gps"}


def test_xmp_lieux_et_textes_libres() -> None:
    espaces = (
        'xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"'
        ' xmlns:Iptc4xmpCore="http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/"'
        ' xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"'
    )
    description = (
        '<dc:title><rdf:Alt><rdf:li xml:lang="x-default">Titre</rdf:li></rdf:Alt></dc:title>'
        "<dc:subject><rdf:Bag><rdf:li>a</rdf:li><rdf:li>b</rdf:li></rdf:Bag></dc:subject>"
        "<photoshop:Headline>Titre court</photoshop:Headline>"
        "<photoshop:Instructions>Embargo</photoshop:Instructions>"
        "<photoshop:City>Lyon</photoshop:City>"
        "<photoshop:Country>France</photoshop:Country>"
        "<Iptc4xmpCore:Location>Place Bellecour</Iptc4xmpCore:Location>"
        '<Iptc4xmpExt:LocationShown rdf:parseType="Resource">'
        "<Iptc4xmpExt:City>Paris</Iptc4xmpExt:City>"
        "<Iptc4xmpExt:GPSLatitude>48,51N</Iptc4xmpExt:GPSLatitude>"
        "</Iptc4xmpExt:LocationShown>"
        "<dc:format>image/jpeg</dc:format>"
    )
    lignes = resultats("xmp", jpeg_meta(app1_xmp(xmp(description, espaces=espaces))), "jpeg")
    assert identifiantes(lignes) == {
        "xmp.dc:title": LIBRE,
        "xmp.dc:subject": LIBRE,
        "xmp.photoshop:Headline": LIBRE,
        "xmp.photoshop:Instructions": LIBRE,
        "xmp.photoshop:City": LIEU,
        "xmp.photoshop:Country": LIEU,
        "xmp.Iptc4xmpCore:Location": LIEU,
        # Dans une structure de lieu, chaque champ garde sa catégorie.
        "xmp.Iptc4xmpExt:LocationShown.Iptc4xmpExt:City": LIEU,
        "xmp.Iptc4xmpExt:LocationShown.Iptc4xmpExt:GPSLatitude": "gps",
    }


def test_iptc_lieux_et_textes_libres() -> None:
    iim = b"".join(
        (
            jeu(2, 5, b"Titre"),
            jeu(2, 27, b"Gare"),
            jeu(2, 40, b"Embargo"),
            jeu(2, 90, b"Lyon"),
            jeu(2, 92, b"Croix-Rousse"),
            jeu(2, 95, b"Rhone"),
            jeu(2, 100, b"FRA"),
            jeu(2, 101, b"France"),
            jeu(2, 105, b"Titre court"),
            jeu(2, 115, b"Agence"),
            jeu(2, 121, b"Legende locale"),
        )
    )
    lignes = resultats("iptc", jpeg_meta(app13(ressource(0x0404, iim))), "jpeg")
    assert identifiantes(lignes) == {
        "iptc.ObjectName": LIBRE,
        "iptc.ContentLocationName": LIEU,
        "iptc.SpecialInstructions": LIBRE,
        "iptc.City": LIEU,
        "iptc.Sub-location": LIEU,
        "iptc.Province-State": LIEU,
        "iptc.Country-PrimaryLocationCode": LIEU,
        "iptc.Country-PrimaryLocationName": LIEU,
        "iptc.Headline": LIBRE,
        "iptc.LocalCaption": LIBRE,
    }


def test_infowav_lieu_et_textes_libres() -> None:
    contenu = wav(
        liste_info((b"IARL", b"Archives"), (b"ISBJ", b"Sujet"), (b"IKEY", b"a; b")),
        liste_info((b"IPRD", b"Album"), (b"ISFT", b"Lavf")),
    )
    lignes = resultats("infowav", contenu, "wav")
    assert identifiantes(lignes) == {
        "infowav.IARL": LIEU,
        "infowav.ISBJ": LIBRE,
        "infowav.IKEY": LIBRE,
        "infowav.IPRD": LIBRE,
    }


def test_vorbis_lieu_et_textes_libres() -> None:
    bloc = commentaires(
        b"v", b"location=Lyon", b"ALBUM=A", b"COMMENT=c", b"LYRICS=l", b"ENCODER=Lavf"
    )
    lignes = resultats("vorbis", flac(bloc_flac(1, b"\x00" * 8), bloc_flac(4, bloc)), "flac")
    assert identifiantes(lignes) == {
        "vorbis.LOCATION": LIEU,
        "vorbis.ALBUM": LIBRE,
        "vorbis.COMMENT": LIBRE,
        "vorbis.LYRICS": LIBRE,
    }


def test_quicktime_cles_de_lieu_et_de_texte() -> None:
    cles = [
        b"com.apple.quicktime.location.name",
        b"com.apple.quicktime.title",
        b"com.apple.quicktime.location.note",
        b"com.apple.quicktime.make",
    ]
    meta = meta_mdta(
        cles,
        *((rang, donnee(1, valeur)) for rang, valeur in enumerate((b"Rue", b"T", b"N", b"A"), 1)),
    )
    lignes = resultats("quicktime", quicktime(meta, majeure=b"qt  "), "mov")
    assert identifiantes(lignes) == {
        "quicktime.mdta.com-apple-quicktime-location-name": LIEU,
        "quicktime.mdta.com-apple-quicktime-title": LIBRE,
        "quicktime.mdta.com-apple-quicktime-location-note": LIBRE,
    }


def test_matroska_balises_de_lieu_et_de_texte() -> None:
    contenu = webm(
        tags(
            tag(
                simple("RECORDING_LOCATION", "FR"),
                simple("COMMENT", "c"),
                simple("ENCODER", "Lavf"),
            )
        )
    )
    lignes = resultats("matroska", contenu, "webm")
    assert identifiantes(lignes) == {
        "matroska.tag.RECORDING-LOCATION": LIEU,
        "matroska.tag.COMMENT": LIBRE,
    }


def test_ooxml_proprietes_personnalisees_toutes_textes_libres() -> None:
    contenu = docx_(
        core(
            "<dc:subject>S</dc:subject><dc:description>D</dc:description><cp:category>C</cp:category>"
        ),
        None,
        custom(("Client", "<vt:lpwstr>X</vt:lpwstr>"), ("Nombre", "<vt:i4>3</vt:i4>")),
    )
    lignes = resultats("ooxml", contenu, "docx")
    assert identifiantes(lignes) == {
        "ooxml.core.dc:subject": LIBRE,
        "ooxml.core.dc:description": LIBRE,
        "ooxml.core.cp:category": LIBRE,
        "ooxml.custom.Client": LIBRE,
        "ooxml.custom.Nombre": LIBRE,
    }


# Valeur FBMD (ADR-0161)


def test_fbmd_marquee_numero_de_serie() -> None:
    lignes = resultats("iptc", instructions(FBMD), "jpeg")
    assert identifiantes(lignes) == {"iptc.SpecialInstructions": "numero_de_serie"}
    # La règle de T24 lit la valeur dans le processus de travail ; sa phrase ne la cite pas.
    assert t24("iptc", instructions(FBMD), "jpeg") == {"R-IPTC-003": {}}


def test_fbmd_pas_au_debut_reste_texte_libre() -> None:
    lignes = resultats("iptc", instructions(b"Voir " + FBMD), "jpeg")
    assert identifiantes(lignes) == {"iptc.SpecialInstructions": LIBRE}


# Rubrique et résumé (ADR-0158)


def avec_marques(analyse: Analyse) -> Analyse:
    """Ajoute un lieu et un texte libre aux observations du rapport de test."""
    ajoutees = (
        Observation(
            "metadonnees/4",
            "metadonnees",
            "xmp.photoshop:City",
            "Lyon",
            identifiante=CategorieIdentifiante.LIEU,
        ),
        Observation(
            "metadonnees/5",
            "metadonnees",
            "xmp.dc:title",
            "Note de Jeanne",
            identifiante=CategorieIdentifiante.TEXTE_LIBRE,
        ),
        Observation(
            "metadonnees/6",
            "metadonnees",
            "xmp.dc:description",
            "Sources",
            identifiante=CategorieIdentifiante.TEXTE_LIBRE,
        ),
    )
    return dataclasses.replace(analyse, observations=analyse.observations + ajoutees)


@pytest.fixture
def analyse() -> Analyse:
    return avec_marques(analyse_de(construire_rapport()))


def test_marques_par_categorie_dans_l_ordre_d_es13(analyse: Analyse) -> None:
    vue = Presentation(analyse, set(CategorieIdentifiante))
    assert [(c, [o.identifiant for o in obs]) for c, obs in vue.marques()] == [
        (CategorieIdentifiante.METADONNEE_NOMINATIVE, ["metadonnees/2"]),
        (CategorieIdentifiante.LIEU, ["metadonnees/4"]),
        (CategorieIdentifiante.TEXTE_LIBRE, ["metadonnees/5", "metadonnees/6"]),
    ]


def test_publication_au_resume(analyse: Analyse) -> None:
    vue = Presentation(analyse, set(CategorieIdentifiante))
    assert vue.publication() == [
        "Contrôle avant publication : 4 donnée(s) des métadonnées peuvent identifier la source "
        "(métadonnées nominatives, lieux nommés, textes libres). L'outil ne les retire pas : "
        "retirez-les avant de publier le fichier.",
        texte("resume.publication_incomplete"),
    ]
    assert vue.resume()[-2:] == vue.publication()


def test_publication_sans_marque_ni_partie_non_lue(tmp_path: Path) -> None:
    # JPEG sans métadonnées : seules les techniques hors V1 sont non menées. Elles ne lisent
    # pas de métadonnées et ne rendent pas le contrôle incomplet.
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(jpeg_image(640, 480))
    analyse = analyser(chemin)
    assert {n.raison for n in analyse.non_menees} == {RaisonNonMenee.HORS_V1}
    vue = Presentation(analyse, ())
    assert vue.marques() == []
    assert vue.publication() == [texte("resume.publication_aucune")]
    # Toute autre analyse non menée le rend incomplet : un module désactivé, par exemple.
    desactive = analyser(chemin, desactiver=("xmp",))
    assert Presentation(desactive, ()).publication() == [
        texte("resume.publication_aucune"),
        texte("resume.publication_incomplete"),
    ]


def rubrique(document: str) -> str:
    sections: list[str] = re.findall(
        r'<section id="controle_publication".*?</section>', document, re.S
    )
    assert len(sections) == 1
    return sections[0]


@pytest.mark.parametrize("reveler", [(), TOUTES], ids=["masque", "leve"])
def test_html_rubrique_sans_valeur(analyse: Analyse, reveler: list[str]) -> None:
    document = exporter_html(analyse, reveler=reveler)
    section = rubrique(document)
    assert "metadonnees/4 (xmp.photoshop:City)" in section
    assert "metadonnees/5 (xmp.dc:title), metadonnees/6 (xmp.dc:description)" in section
    assert "lieux nommés" in section
    # La rubrique ne porte jamais de valeur ; les observations la portent si la catégorie est levée.
    for valeur in ("Lyon", "Note de Jeanne", "Jeanne Martin"):
        assert valeur not in section
        assert (valeur in document) is bool(reveler)


def test_terminal_nomme_les_marques(analyse: Analyse) -> None:
    lignes = resume(analyse)
    assert "marques identifiantes, lieux nommés : xmp.photoshop:City" in lignes
    assert "marques identifiantes, textes libres : xmp.dc:title, xmp.dc:description" in lignes
    assert not any("Lyon" in ligne for ligne in lignes)


# Masquage des deux nouvelles catégories (ADR-0159)


def test_lieu_et_texte_libre_masques_par_defaut(analyse: Analyse) -> None:
    document = json.loads(exporter_json(analyse))
    assert document["masquage"] == {"masquees": TOUTES, "levees": []}
    par_identifiant = {o["identifiant"]: o for o in document["observations"]}
    assert "valeur" not in par_identifiant["metadonnees/4"]
    assert "valeur" not in par_identifiant["metadonnees/5"]
    leve = json.loads(exporter_json(analyse, reveler=["lieu"]))
    assert leve["masquage"]["levees"] == ["lieu"]
    assert {o["identifiant"]: o.get("valeur") for o in leve["observations"]}[
        "metadonnees/4"
    ] == "Lyon"
    assert "valeur" not in {o["identifiant"]: o for o in leve["observations"]}["metadonnees/5"]


def test_reveler_admet_les_deux_categories() -> None:
    arguments = construire_analyseur().parse_args(
        ["--reveler", "lieu", "--reveler", "texte_libre", "f"]
    )
    assert arguments.reveler == ["lieu", "texte_libre"]


# Analyse complète


def test_analyse_complete_d_une_photo_publiee(tmp_path: Path) -> None:
    # Photo qui porte un GPS, une ville, un titre et la marque de Facebook : le résumé du
    # terminal nomme les quatre catégories, sans valeur, et l'indice de T24 reste.
    exif = tiff((Sous(0x8825, (fractions(0x0002, (45, 1), (46, 1), (0, 1)),)),))
    iim = jeu(2, 5, b"Reunion") + jeu(2, 40, FBMD) + jeu(2, 90, b"Lyon")
    chemin = tmp_path / "photo.jpg"
    chemin.write_bytes(jpeg_meta(app1_exif(exif), app13(ressource(0x0404, iim))))
    analyse = analyser(chemin)
    assert "R-IPTC-003" in {c.regle.identifiant for c in analyse.constats}
    lignes = resume(analyse)
    [ligne] = [ligne for ligne in lignes if ligne.startswith("Contrôle avant publication :")]
    assert "(numéros de série, coordonnées GPS, lieux nommés, textes libres)" in ligne
    assert "marques identifiantes, numéros de série : iptc.SpecialInstructions" in lignes
    sortie = "\n".join(lignes)
    for valeur in ("Reunion", "Lyon", "FBMD"):
        assert valeur not in sortie
