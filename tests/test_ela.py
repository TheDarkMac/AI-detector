"""ELA : carte du niveau d'erreur de recompression, avertissement, visualisations au rapport (T42,
ADR-0197 à ADR-0201)."""

import base64
import dataclasses
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import zlib
from html import escape
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pytest
from metadonnees import contexte, raisons, resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import ela
from voight_kampff.modules._lecture import dct, jpeg
from voight_kampff.rapport import comparaison, export
from voight_kampff.rapport._html import politique
from voight_kampff.rapport._presentation import Presentation, accorder, texte, textes
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    EtatTechnique,
    Localisation,
    NatureVisualisation,
    Observation,
    Rapport,
    Visualisation,
    verifier_resultats,
)

pytestmark = pytest.mark.exigence("F-32", "F-84")

ECHANTILLONS = Path(__file__).parent / "donnees" / "ela"
CJPEG, DJPEG = shutil.which("cjpeg"), shutil.which("djpeg")
CARTE_COLLAGE = "3f7e9c17f1a6b17cbabc7e981b33f6aa5c963bd15d1a03e51687bdc8bb263755"
CARTE_SIMPLE = "47336b3bde87b00910540fbd382060682fc62005f4a1a76b04bc53393d8bbd67"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def echantillon(nom: str) -> bytes:
    return (ECHANTILLONS / f"{nom}.jpg").read_bytes()


def coefficients(contenu: bytes) -> jpeg.Coefficients:
    with tempfile.TemporaryFile() as fichier:
        lecture = jpeg.lire(
            contexte(fichier, contenu, "jpeg", "ela"), blocs=ela.BLOCS_MAX, visites=ela.VISITES_MAX
        )
    assert lecture.coefficients is not None
    return lecture.coefficients


def visualisations(lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ligne["visualisation"] for ligne in lignes if ligne["type"] == "visualisation"]


def pixels_du_png(png: bytes) -> npt.NDArray[np.uint8]:
    """Relit un PNG en niveaux de gris sur huit bits, sans filtre, par zlib."""
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    position, donnees, largeur, hauteur = 8, b"", 0, 0
    while position < len(png):
        (taille,) = struct.unpack(">I", png[position : position + 4])
        nature = png[position + 4 : position + 8]
        corps = png[position + 8 : position + 8 + taille]
        (crc,) = struct.unpack(">I", png[position + 8 + taille : position + 12 + taille])
        assert crc == zlib.crc32(nature + corps)
        if nature == b"IHDR":
            largeur, hauteur = struct.unpack(">II", corps[:8])
            assert corps[8:] == b"\x08\x00\x00\x00\x00"
        elif nature == b"IDAT":
            donnees += corps
        position += 12 + taille
    brut = zlib.decompress(donnees)
    lignes = [brut[i * (largeur + 1) : (i + 1) * (largeur + 1)] for i in range(hauteur)]
    assert all(ligne[0] == 0 for ligne in lignes)
    return np.array([list(ligne[1:]) for ligne in lignes], dtype=np.uint8)


# Calcul (ADR-0199)


@pytest.mark.parametrize(
    ("nom", "procede", "ecart_moyen", "empreinte"),
    [
        ("collage_60_92", "sequentiel", 0.2, CARTE_COLLAGE),
        ("collage_60_92_progressif", "progressif", 0.2, CARTE_COLLAGE),
        ("simple_92", "sequentiel", 1.11, CARTE_SIMPLE),
    ],
)
def test_carte_des_echantillons(nom: str, procede: str, ecart_moyen: float, empreinte: str) -> None:
    # Empreintes fixées : la carte est la même sur toutes les machines (NF-06, ADR-0199). Le
    # progressif porte les mêmes coefficients que le séquentiel, donc la même carte.
    lignes = resultats("ela", echantillon(nom), "jpeg")
    valeurs = valeurs_de(lignes)
    assert valeurs["ela.procede"] == procede
    assert valeurs["ela.qualite"] == ela.QUALITE == 95
    assert valeurs["ela.blocs"] == valeurs["ela.blocs_image"] == 32 * 24
    assert valeurs["ela.ecart_moyen"] == ecart_moyen
    (carte,) = visualisations(lignes)
    assert (carte["nature"], carte["largeur"], carte["hauteur"]) == ("carte_ela", 32, 24)
    assert carte["identifiante"] == "contenu"
    assert carte["empreinte"] == empreinte
    png = base64.b64decode(carte["donnees"])
    assert hashlib.sha256(png).hexdigest() == empreinte
    assert carte["localisation"] == {
        "chemin": "composante 1, image entière",
        "zone": {"x": 0, "y": 0, "largeur": 256, "hauteur": 192},
    }


def test_le_collage_ressort() -> None:
    # Le carré de 64 x 64 pixels collé sans perte (blocs 12 à 19, lignes 8 à 15) n'a pas subi la
    # compression à 60 du reste : il change bien plus à la recompression.
    carte = pixels_du_png(
        base64.b64decode(
            visualisations(resultats("ela", echantillon("collage_60_92"), "jpeg"))[0]["donnees"]
        )
    ).astype(np.int64)
    carre = np.zeros(carte.shape, dtype=bool)
    carre[8:16, 12:20] = True
    assert carte[carre].mean() > 5 * carte[~carre].mean()
    # Compressée une seule fois, la même image ne montre rien de tel.
    simple = pixels_du_png(
        base64.b64decode(
            visualisations(resultats("ela", echantillon("simple_92"), "jpeg"))[0]["donnees"]
        )
    ).astype(np.int64)
    assert simple[carre].mean() < 1.2 * simple[~carre].mean()


def test_carte_a_gain_fixe_bornee() -> None:
    sommes = np.array([[0, 1, 127, 128, 10_000]], dtype=np.int64)
    assert ela.carte(sommes).tolist() == [[0, 2, 254, 255, 255]]


def test_un_bloc_deja_a_la_qualite_95_ne_change_pas() -> None:
    # Coefficients quantifiés aux pas de la qualité 95 : la recompression les retrouve, à
    # l'arrondi de la DCT en virgule fixe près.
    table = dct.table_ijg(ela.QUALITE)
    blocs = [[0] * 64 for _ in range(4)]
    blocs[1][0], blocs[2][1], blocs[3][2] = 20, -3, 5
    sommes = ela.ecarts(_coefficients(blocs, table))
    assert int(sommes.max()) <= 8


def _coefficients(blocs: list[list[int]], table: tuple[int, ...]) -> jpeg.Coefficients:
    from array import array

    return jpeg.Coefficients(
        largeur=16,
        hauteur=16,
        procede="sequentiel",
        precision_table=False,
        table=table,
        colonnes=2,
        lignes=2,
        largeur_composante=16,
        hauteur_region=16,
        blocs_image=4,
        valeurs=array("q", [valeur for bloc in blocs for valeur in bloc]),
    )


def test_plan_et_luminance_concordent() -> None:
    c = coefficients(echantillon("collage_60_92"))
    plan = dct.plan(dct.blocs_de_pixels(c), c.lignes, c.colonnes)
    assert np.array_equal(plan[: c.hauteur_region, : c.largeur_composante], dct.luminance(c))


def test_dct_aller_retour() -> None:
    rng = np.random.default_rng(42)
    pixels = rng.integers(0, 256, size=(10, 8, 8), dtype=np.int64)
    retour = dct.inverser(dct.arrondir(dct.transformer(pixels - 128), 1 << (2 * dct.ECHELLE)))
    assert int(np.abs(retour - pixels).max()) <= 1


@pytest.mark.skipif(CJPEG is None or DJPEG is None, reason="cjpeg ou djpeg absent")
@pytest.mark.parametrize("nom", ["collage_60_92", "simple_92"])
def test_oracle_libjpeg_turbo(nom: str) -> None:
    # La recompression simulée suit celle de cjpeg à la qualité 95 : pixel par pixel à quelques
    # niveaux près, en écart moyen au centième près (fiche ela, « Limites connues »).
    assert CJPEG is not None
    assert DJPEG is not None

    def gris(donnees: bytes) -> npt.NDArray[np.int64]:
        entete, dimensions, _, pixels = donnees.split(b"\n", 3)
        assert entete == b"P5"
        largeur, hauteur = map(int, dimensions.split())
        return np.frombuffer(pixels, dtype=np.uint8).reshape(hauteur, largeur).astype(np.int64)

    def lancer(commande: list[str], entree: bytes) -> bytes:
        return subprocess.run(commande, input=entree, capture_output=True, check=True).stdout

    decode = lancer([DJPEG, "-grayscale", "-dct", "int", "-pnm"], echantillon(nom))
    recompresse = lancer(
        [DJPEG, "-dct", "int", "-pnm"],
        lancer([CJPEG, "-grayscale", "-quality", "95", "-dct", "int"], decode),
    )
    reference = float(np.abs(gris(decode) - gris(recompresse)).mean())
    c = coefficients(echantillon(nom))
    calcule = int(ela.ecarts(c).sum()) / (64 * c.lignes * c.colonnes)
    assert abs(calcule - reference) < 0.01


# Étendue (ADR-0199)


def test_haut_de_l_image_au_dela_du_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ela, "BLOCS_MAX", 32 * 5)
    lignes = resultats("ela", echantillon("collage_60_92"), "jpeg")
    valeurs = valeurs_de(lignes)
    assert (valeurs["ela.blocs"], valeurs["ela.blocs_image"]) == (32 * 5, 32 * 24)
    (carte,) = visualisations(lignes)
    assert (carte["largeur"], carte["hauteur"]) == (32, 5)
    assert carte["localisation"] == {
        "chemin": "composante 1, haut de l'image",
        "zone": {"x": 0, "y": 0, "largeur": 256, "hauteur": 40},
    }


def test_jpeg_non_lu() -> None:
    lignes = resultats("ela", b"\xff\xd8\xff\xc3\x00\x02\xff\xd9", "jpeg")
    assert raisons(lignes) == ["format_partiel"]
    assert visualisations(lignes) == []


# PNG (ADR-0199)


@pytest.mark.parametrize(("hauteur", "largeur"), [(1, 1), (3, 5), (300, 300)])
def test_png_gris_se_relit(hauteur: int, largeur: int) -> None:
    # 300 x 301 octets : deux blocs stockés de deflate.
    valeurs = np.arange(hauteur * largeur, dtype=np.int64).reshape(hauteur, largeur) % 256
    png = ela.png_gris(valeurs.astype(np.uint8))
    assert np.array_equal(pixels_du_png(png), valeurs)


def test_png_gris_sans_compression() -> None:
    # Blocs stockés seulement : les octets ne dépendent pas de la version de zlib (NF-06).
    png = ela.png_gris(np.zeros((2, 2), dtype=np.uint8))
    idat = png[png.index(b"IDAT") + 4 : png.index(b"IEND") - 8]
    assert idat[:2] == b"\x78\x01"
    assert idat[2] == 1  # bloc final, stocké (BTYPE 00)


# Modèle : objet Visualisation (ADR-0200)

PNG = ela.png_gris(np.zeros((2, 3), dtype=np.uint8))


def test_visualisation_aller_retour() -> None:
    visualisation = Visualisation(
        "ela", NatureVisualisation.CARTE_ELA, 3, 2, PNG, Localisation(chemin="c"), 2
    )
    document = visualisation.vers_dict()
    assert document["type_media"] == "image/png"
    assert document["empreinte"] == hashlib.sha256(PNG).hexdigest()
    assert visualisation.identifiante is CategorieIdentifiante.CONTENU
    assert Visualisation.depuis_dict(document) == visualisation


@pytest.mark.parametrize(
    ("autres", "message"),
    [
        pytest.param({"largeur": 0}, "largeur", id="largeur-nulle"),
        pytest.param({"hauteur": 65536}, "hauteur : trop grande", id="trop-haute"),
        pytest.param({"png": "pas des octets"}, "absente ou trop grande", id="pas-des-octets"),
        pytest.param({"png": PNG + bytes(768 << 10)}, "absente ou trop grande", id="trop-grand"),
        pytest.param({"png": b"GIF89a" + PNG[6:]}, "pas une image PNG", id="signature"),
        pytest.param({"png": PNG[:20]}, "pas une image PNG", id="tronque"),
        pytest.param({"largeur": 4}, "dimensions", id="dimensions"),
        pytest.param({"module": ""}, "module", id="module"),
    ],
)
def test_visualisation_refusee(autres: dict[str, Any], message: str) -> None:
    champs: dict[str, Any] = {
        "module": "ela",
        "nature": NatureVisualisation.CARTE_ELA,
        "largeur": 3,
        "hauteur": 2,
        "png": PNG,
    } | autres
    with pytest.raises(ValueError, match=message):
        Visualisation(**champs)


@pytest.mark.parametrize(
    ("autres", "message"),
    [
        pytest.param({"identifiante": "empreinte"}, "« contenu » attendu", id="categorie"),
        pytest.param({"donnees": "@@@@"}, "base64", id="base64"),
        pytest.param({"empreinte": "0" * 64}, "empreinte", id="empreinte"),
    ],
)
def test_visualisation_relue_refusee(autres: dict[str, Any], message: str) -> None:
    document = Visualisation("ela", NatureVisualisation.CARTE_ELA, 3, 2, PNG).vers_dict()
    with pytest.raises(ValueError, match=message):
        Visualisation.depuis_dict(document | autres)


# Rapport : exports, masquage, comparaison (ADR-0200)


@pytest.fixture(scope="module")
def analyse(tmp_path_factory: pytest.TempPathFactory) -> Analyse:
    chemin = tmp_path_factory.mktemp("ela") / "collage.jpg"
    chemin.write_bytes(echantillon("collage_60_92"))
    return analyser(chemin)


def test_analyse_porte_la_carte(analyse: Analyse) -> None:
    (carte,) = analyse.visualisations
    assert (carte.module, carte.nature, carte.largeur, carte.hauteur) == (
        "ela",
        NatureVisualisation.CARTE_ELA,
        32,
        24,
    )
    assert carte.empreinte == CARTE_COLLAGE
    etats = {t.module: t.etat for t in analyse.couverture.techniques}
    assert etats["ela"] is EtatTechnique.APPLIQUEE
    assert analyse.rapport().visualisations == analyse.visualisations


def test_json_masque_la_carte_par_defaut(analyse: Analyse) -> None:
    document = json.loads(export.exporter_json(analyse))
    assert "contenu" in document["masquage"]["masquees"]
    (carte,) = document["visualisations"]
    assert "donnees" not in carte
    assert "empreinte" not in carte
    assert carte["largeur"] == 32


def test_json_revele_la_carte(analyse: Analyse) -> None:
    document = json.loads(export.exporter_json(analyse, reveler=["contenu"]))
    assert document["masquage"]["levees"] == ["contenu"]
    (carte,) = document["visualisations"]
    assert carte["empreinte"] == CARTE_COLLAGE
    assert hashlib.sha256(base64.b64decode(carte["donnees"])).hexdigest() == CARTE_COLLAGE
    # Tout révélé, l'export se relit en rapport, carte comprise.
    tout = json.loads(export.exporter_json(analyse, reveler=list(CategorieIdentifiante)))
    assert Rapport.depuis_dict(tout).visualisations == analyse.visualisations


@pytest.mark.parametrize("reveler", [(), ("contenu",)])
def test_json_carte_incoherente_avec_le_masquage(analyse: Analyse, reveler: tuple[str]) -> None:
    document = json.loads(export.exporter_json(analyse, reveler=reveler))
    carte = document["visualisations"][0]
    if reveler:
        del carte["donnees"], carte["empreinte"]
    else:
        carte["empreinte"] = CARTE_COLLAGE
    with pytest.raises(ValueError, match="visualisations"):
        export.valider(document)


def test_html_masque_la_carte_par_defaut(analyse: Analyse) -> None:
    page = export.exporter_html(analyse)
    assert "<img" not in page
    assert escape(texte("visualisations.masquee")) in page
    assert CARTE_COLLAGE not in page


def test_html_carte_sous_son_avertissement(analyse: Analyse) -> None:
    page = export.exporter_html(analyse, reveler=["contenu"])
    debut = page.index('<section id="visualisations"')
    image = page.index('<img class="carte" src="data:image/png;base64,')
    assert debut < image
    avertissement = textes()["visualisations"]["carte_ela"]["avertissement"]
    assert len(avertissement) == 6
    for paragraphe in avertissement:
        position = page.index(escape(paragraphe))
        assert debut < position < image
    assert 'width="32" height="24"' in page
    assert CARTE_COLLAGE in page
    assert "img-src data:" in politique()
    couverture = texte("visualisations.couverture_entiere", blocs="768")
    assert escape(couverture) in page


def test_html_couverture_partielle_et_inconnue(analyse: Analyse) -> None:
    def remplacer(nom: str, valeur: int | None) -> tuple[Observation, ...]:
        return tuple(
            dataclasses.replace(o, valeur=valeur) if o.nom == nom and valeur is not None else o
            for o in analyse.observations
            if not (o.nom == nom and valeur is None)
        )

    partielle = dataclasses.replace(analyse, observations=remplacer("ela.blocs", 160))
    page = export.exporter_html(partielle, reveler=["contenu"])
    attendu = texte("visualisations.couverture_partielle", blocs="160", blocs_image="768")
    assert escape(attendu) in page
    inconnue = dataclasses.replace(analyse, observations=remplacer("ela.blocs", None))
    page = export.exporter_html(inconnue, reveler=["contenu"])
    assert "La carte couvre" not in page
    assert "La carte ne couvre" not in page


def test_html_sans_visualisation(analyse: Analyse) -> None:
    sans = dataclasses.replace(analyse, visualisations=())
    assert escape(texte("visualisations.aucune")) in export.exporter_html(sans)
    assert not any("visualisation" in ligne for ligne in Presentation(sans, ()).resume())


def test_resume_annonce_la_carte(analyse: Analyse) -> None:
    lignes = Presentation(analyse, ()).resume()
    assert (
        accorder(
            "resume.visualisations",
            1,
            natures="Carte du niveau d'erreur de recompression (ELA)",
        )
        in lignes
    )


def test_comparaison_sans_les_cartes_masquees(analyse: Analyse) -> None:
    masque = json.loads(export.exporter_json(analyse))
    revele = json.loads(export.exporter_json(analyse, reveler=["contenu"]))
    assert comparaison.comparer(masque, revele).identiques
    autre = json.loads(export.exporter_json(analyse, reveler=["contenu"]))
    autre["visualisations"][0]["largeur"] = 31
    assert not comparaison.comparer(revele, autre).identiques


def test_visualisation_d_une_technique_non_appliquee(analyse: Analyse) -> None:
    intrus = dataclasses.replace(analyse.visualisations[0], module="exif")
    sans_exif = dataclasses.replace(
        analyse.couverture,
        techniques=tuple(
            dataclasses.replace(t, etat=EtatTechnique.NON_APPLICABLE) if t.module == "exif" else t
            for t in analyse.couverture.techniques
        ),
    )
    with pytest.raises(ValueError, match="ni appliquée ni partielle"):
        verifier_resultats(
            analyse.identification,
            sans_exif,
            tuple(o for o in analyse.observations if o.module != "exif"),
            tuple(c for c in analyse.constats if c.module != "exif"),
            analyse.non_menees,
            (intrus,),
        )
    with pytest.raises(ValueError, match="trop nombreuses"):
        verifier_resultats(
            analyse.identification,
            analyse.couverture,
            analyse.observations,
            analyse.constats,
            analyse.non_menees,
            analyse.visualisations * 17,
        )
