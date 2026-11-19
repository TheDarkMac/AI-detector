"""Images d'un PDF : module ``imagespdf``, parties extraites, règles du catalogue (T53,
ADR-0223 à ADR-0227).

Les documents synthétiques sont construits ici ; les échantillons de ``tests/donnees/images``
viennent d'ImageMagick, de LibreOffice et de Ghostscript, ou sont écrits objet par objet, et
``oracle.json`` consigne ce qu'en dit ``pdfimages`` de Poppler (``generer_images.py``).
"""

import hashlib
import json
import tempfile
import zlib
from html import escape
from pathlib import Path
from typing import Any

import pytest
from metadonnees import flux_pdf, identifiantes, pdf, raisons, valeurs_de

from voight_kampff._limites import OBJETS_MAX, OCTETS_EXTRAITS_MAX
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte, Extraction
from voight_kampff._travail.fichier import Fichier
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.cli import resume
from voight_kampff.modules import imagespdf
from voight_kampff.modules._lecture import pdf as lecteur
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import (
    _SANS_METADONNEES,
    Presentation,
    origine_partie,
    texte,
)
from voight_kampff.rapport.modele import (
    NOMBRE_MAX_EXTRAITES,
    Direction,
    EtatTechnique,
    Localisation,
    Partie,
    Plage,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("F-63")

DONNEES = Path(__file__).parent / "donnees"
ECHANTILLONS = DONNEES / "images"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
SIMPLE = (DONNEES / "doublejpeg" / "simple_75.jpg").read_bytes()
DOUBLE = (DONNEES / "doublejpeg" / "double_60_90.jpg").read_bytes()
SANS_IMAGE = {
    "imagespdf.pages": 1,
    "imagespdf.pages_lues": 1,
    "imagespdf.images": 0,
    "imagespdf.jpeg": 0,
    "imagespdf.acheminees": 0,
    "imagespdf.non_acheminees": 0,
}
FORMES = {
    "imagespdf.pages": 2,
    "imagespdf.pages_lues": 2,
    "imagespdf.images": 7,
    "imagespdf.jpeg": 2,
    "imagespdf.acheminees": 2,
    "imagespdf.acheminees.pages": [1, 2],
    "imagespdf.non_acheminees": 5,
    "imagespdf.non_acheminees.filtres": [
        "FlateDecode",
        "FlateDecode+DCTDecode",
        "JPXDecode",
        "aucun",
        "autre",
    ],
    "imagespdf.non_acheminees.pages": [1, 2],
}


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def image(filtre: bytes = b"/Filter/DCTDecode", donnees: bytes = SIMPLE) -> bytes:
    return flux_pdf(f"/Type/XObject/Subtype/Image/Width 1/Height 1{filtre.decode()}", donnees)


def document(ressources: bytes, objets: dict[int, bytes], *, pages: int = 1) -> bytes:
    """Catalogue (1), arbre des pages (2), ``pages`` pages (3, 4…) aux mêmes ressources
    ``/XObject`` ; ``objets`` à partir de 10."""
    enfants = " ".join(f"{3 + n} 0 R" for n in range(pages)).encode()
    tous = {
        1: b"<</Type/Catalog/Pages 2 0 R>>",
        2: b"<</Type/Pages/Kids[" + enfants + b"]/Count %d>>" % pages,
    }
    for n in range(pages):
        tous[3 + n] = b"<</Type/Page/Parent 2 0 R/Resources<</XObject<<" + ressources + b">>>>>>"
    return pdf(tous | objets)


def executer(
    contenu: bytes, *, places: int = NOMBRE_MAX_EXTRAITES, octets: int = OCTETS_EXTRAITS_MAX
) -> tuple[list[dict[str, Any]], tuple[Extraction, ...], Localisation | None, bytes]:
    """Lignes, extractions et première extraction refusée du module ; et le contenu, pour
    relire les plages extraites."""
    with tempfile.TemporaryFile() as fichier:
        fichier.write(contenu)
        fichier.flush()
        partie = Partie(1, "pdf", Plage(0, len(contenu)), fin_connue=True)
        c = Contexte(
            "imagespdf",
            {Direction.RIEN_DE_PARTICULIER},
            Fichier(fichier.fileno()),
            partie,
            64 << 20,
            extrait={"jpeg"},
            places=places,
            octets_restants=octets,
        )
        imagespdf.analyser(c)
        return [json.loads(ligne) for ligne in c.lignes], c.extractions, c.refusee, contenu


def obs(contenu: bytes, **options: Any) -> dict[str, Any]:
    return valeurs_de(executer(contenu, **options)[0])


def echantillon(nom: str) -> bytes:
    return (ECHANTILLONS / f"{nom}.pdf").read_bytes()


def octets(contenu: bytes, extraction: Extraction) -> bytes:
    debut = extraction.octets.debut
    return contenu[debut : debut + extraction.octets.longueur]


# Recherche des images (ADR-0225)


def test_document_sans_image() -> None:
    resultat, extractions, refusee, _ = executer(document(b"", {}))
    assert valeurs_de(resultat) == SANS_IMAGE
    assert (raisons(resultat), extractions, refusee) == ([], (), None)
    assert identifiantes(resultat) == {}


def test_images_des_pages_et_des_formes() -> None:
    # formes.pdf : page 1, un JPEG, des pixels compressés et en clair ; page 2, une forme qui
    # reprend le JPEG de la page 1 (lu une fois), un autre JPEG, un JPEG compressé une seconde
    # fois, un JPEG 2000, et une sous-forme à l'image au filtre inconnu.
    resultat, extractions, refusee, contenu = executer(echantillon("formes"))
    assert valeurs_de(resultat) == FORMES
    assert [(e.format, e.localisation) for e in extractions] == [
        ("jpeg", Localisation(chemin="image (objet 10 0)", page=1)),
        ("jpeg", Localisation(chemin="image (objet 14 0)", page=2)),
    ]
    assert [octets(contenu, e) for e in extractions] == [SIMPLE, DOUBLE]
    assert refusee is None


def test_image_listee_non_dessinee_et_reprise_par_une_autre_page() -> None:
    # Les flux de contenu ne sont pas lus : une image listée compte ; reprise par la page 2,
    # elle est comptée une fois, à la première.
    valeurs_ = obs(document(b"/A 10 0 R", {10: image()}, pages=2))
    assert valeurs_["imagespdf.images"] == 1
    assert valeurs_["imagespdf.acheminees.pages"] == [1]
    assert valeurs_["imagespdf.pages_lues"] == 2


def test_ressources_mal_formees() -> None:
    # Entrée directe, référence vers autre chose qu'un flux, flux sans sous-type ou d'un autre
    # sous-type, filtre qui n'est pas un nom : rien n'arrête la recherche.
    objets = {
        10: b"<</Subtype/Image>>",
        11: flux_pdf("/Type/XObject", b"x"),
        12: flux_pdf("/Subtype/PS", b"x"),
        13: image(b"/Filter(DCTDecode)"),
        14: image(b"/Filter[/DCTDecode/DCTDecode]"),
    }
    ressources = b"/D<</Subtype/Image>>/A 10 0 R/B 11 0 R/C 12 0 R/E 13 0 R/F 14 0 R/X 99 0 R"
    valeurs_ = obs(document(ressources, objets))
    assert valeurs_["imagespdf.images"] == 2
    assert valeurs_["imagespdf.non_acheminees.filtres"] == ["DCTDecode+DCTDecode", "autre"]


def test_ressources_et_xobjets_en_flux() -> None:
    # Un dictionnaire de ressources, ou de XObject, écrit en flux : son dictionnaire est lu.
    contenu = pdf(
        {
            1: b"<</Type/Catalog/Pages 2 0 R>>",
            2: b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
            3: b"<</Type/Page/Parent 2 0 R/Resources 20 0 R>>",
            10: image(),
            20: flux_pdf("/XObject 21 0 R", b""),
            21: flux_pdf("/A 10 0 R", b""),
        }
    )
    assert obs(contenu)["imagespdf.acheminees"] == 1


def test_origine_d_une_partie_reconnue() -> None:
    assert origine_partie(Partie(1, "pdf", Plage(0, 1), fin_connue=True)) == ""


def test_flux_vide_compte_non_achemine() -> None:
    resultat, extractions, _, _ = executer(document(b"/A 10 0 R", {10: image(donnees=b"")}))
    assert valeurs_de(resultat)["imagespdf.jpeg"] == 1
    assert valeurs_de(resultat)["imagespdf.acheminees"] == 0
    assert extractions == ()


def test_formes_trop_imbriquees(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(imagespdf, "FORMES_MAX", 1)
    valeurs_ = obs(echantillon("formes"))
    # La sous-forme de la page 2 n'est pas lue : son image n'est pas comptée.
    assert valeurs_["imagespdf.recherche_coupee"] is True
    assert (valeurs_["imagespdf.images"], valeurs_["imagespdf.pages_lues"]) == (6, 1)


def test_trop_d_images(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(imagespdf, "IMAGES_MAX", 2)
    valeurs_ = obs(echantillon("formes"))
    assert valeurs_["imagespdf.recherche_coupee"] is True
    assert (valeurs_["imagespdf.images"], valeurs_["imagespdf.pages_lues"]) == (2, 0)


def test_pages_au_dela_de_la_limite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(imagespdf, "PAGES_MAX", 1)
    valeurs_ = obs(echantillon("formes"))
    assert (valeurs_["imagespdf.pages"], valeurs_["imagespdf.pages_lues"]) == (2, 1)
    assert valeurs_["imagespdf.images"] == 3


def test_arret_avant_le_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(imagespdf, "OBJETS_RESERVES", OBJETS_MAX)
    valeurs_ = obs(echantillon("formes"))
    assert valeurs_["imagespdf.arret_avant_budget"] is True
    assert (valeurs_["imagespdf.pages_lues"], valeurs_["imagespdf.images"]) == (0, 0)


@pytest.mark.parametrize("apres", range(1, 40, 2))
def test_arret_en_cours_de_recherche(monkeypatch: pytest.MonkeyPatch, apres: int) -> None:
    # Le budget s'épuise après « apres » objets comptés : la recherche s'arrête, ce qui est vu
    # est observé, sans dépasser la limite.
    compter = Contexte.compter_objets

    def compte(contexte: Contexte, nombre: int = 1) -> None:
        compter(contexte, nombre)
        if contexte.objets >= apres:
            monkeypatch.setattr(imagespdf, "OBJETS_RESERVES", OBJETS_MAX)

    monkeypatch.setattr(Contexte, "compter_objets", compte)
    valeurs_ = obs(echantillon("formes"))
    assert valeurs_["imagespdf.arret_avant_budget"] is True
    assert valeurs_["imagespdf.images"] <= FORMES["imagespdf.images"]


@pytest.mark.parametrize("appels", range(1, 10))
def test_arret_entre_deux_ressources(monkeypatch: pytest.MonkeyPatch, appels: int) -> None:
    # La recherche vérifie le budget avant chaque page et chaque ressource : arrêtée au n-ième
    # contrôle, elle observe ce qu'elle a vu, la page en cours n'étant pas lue en entier.
    vus = 0

    def continuer(recherche: Any) -> bool:
        nonlocal vus
        vus += 1
        recherche.arrete = recherche.arrete or vus >= appels
        return not recherche.arrete

    monkeypatch.setattr(imagespdf._Recherche, "continuer", continuer)
    valeurs_ = obs(echantillon("formes"))
    assert valeurs_["imagespdf.arret_avant_budget"] is True
    assert valeurs_["imagespdf.pages_lues"] < FORMES["imagespdf.pages_lues"]


def test_document_chiffre() -> None:
    # Les données des flux sont chiffrées : rien n'est acheminé, rien n'est déchiffré.
    resultat, extractions, _, _ = executer(echantillon("chiffre"))
    assert valeurs_de(resultat) == {
        "imagespdf.pages": 1,
        "imagespdf.pages_lues": 1,
        "imagespdf.images": 2,
        "imagespdf.chiffre": True,
    }
    assert extractions == ()


def test_document_illisible() -> None:
    resultat, extractions, _, _ = executer(b"%PDF-1.7\nrien\n")
    assert raisons(resultat) == ["format_partiel"]
    assert valeurs_de(resultat) == {}
    assert extractions == ()


def test_page_illisible_n_arrete_pas_les_autres() -> None:
    # La page 1 désigne une image dont l'objet n'est pas où la table le dit ; la page 2 est lue.
    page2 = b"<</Type/Page/Parent 2 0 R/Resources<</XObject<</B 11 0 R>>>>>>"
    base = pdf(
        {
            1: b"<</Type/Catalog/Pages 2 0 R>>",
            2: b"<</Type/Pages/Kids[3 0 R 4 0 R]/Count 2>>",
            3: b"<</Type/Page/Parent 2 0 R/Resources<</XObject<</A 10 0 R>>>>>>",
            4: page2,
            10: image(),
            11: image(donnees=DOUBLE),
        }
    )
    casse = base.replace(b"10 0 obj", b"10 0 xxx")
    resultat, extractions, _, contenu = executer(casse)
    assert raisons(resultat) == ["format_partiel"]
    valeurs_ = valeurs_de(resultat)
    assert (valeurs_["imagespdf.pages_lues"], valeurs_["imagespdf.images"]) == (1, 1)
    assert [octets(contenu, e) for e in extractions] == [DOUBLE]


def test_rien_n_est_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le module lit la structure ; il ne décode aucun flux, ni image ni contenu (ADR-0225).
    def interdit(*_arguments: Any, **_options: Any) -> bytes:
        raise AssertionError

    monkeypatch.setattr(lecteur.Document, "decoder", interdit)
    monkeypatch.setattr(Contexte, "decompresser", interdit)
    assert obs(echantillon("formes")) == FORMES


# Borne des extractions (ADR-0226)


def test_places_epuisees() -> None:
    resultat, extractions, refusee, _ = executer(echantillon("formes"), places=1)
    valeurs_ = valeurs_de(resultat)
    assert (valeurs_["imagespdf.acheminees"], valeurs_["imagespdf.au_dela"]) == (1, 1)
    assert len(extractions) == 1
    assert refusee == Localisation(chemin="image (objet 14 0)", page=2)


def test_octets_epuises() -> None:
    # Le premier JPEG franchit le seuil : il est encore acheminé, le suivant ne l'est pas.
    resultat, extractions, refusee, _ = executer(echantillon("formes"), octets=1)
    assert valeurs_de(resultat)["imagespdf.au_dela"] == 1
    assert [e.localisation.page for e in extractions] == [1]
    assert refusee is not None


def test_dix_huit_images() -> None:
    resultat, extractions, refusee, _ = executer(echantillon("nombreuses"))
    valeurs_ = valeurs_de(resultat)
    assert (valeurs_["imagespdf.jpeg"], valeurs_["imagespdf.acheminees"]) == (18, 16)
    assert valeurs_["imagespdf.au_dela"] == 2
    assert len(extractions) == NOMBRE_MAX_EXTRAITES
    assert refusee == Localisation(chemin="image (objet 26 0)", page=1)


# Échantillons comparés à Poppler


def test_echantillons_et_oracle_concordent() -> None:
    assert ORACLE["outil"] == "pdfimages 25.03.0"
    assert set(ORACLE["echantillons"]) == {
        "imagemagick",
        "libreoffice",
        "ghostscript",
        "formes",
        "nombreuses",
    }


@pytest.mark.parametrize("nom", sorted(ORACLE["echantillons"]))
def test_echantillons_compares_a_poppler(nom: str) -> None:
    # pdfimages liste les images dessinées, et recopie les données d'un JPEG (-j) : chaque
    # partie extraite est ce JPEG, octet pour octet, à la page de sa première apparition.
    resultat, extractions, _, contenu = executer(echantillon(nom), places=64, octets=1 << 30)
    premieres: dict[str, dict[str, Any]] = {}
    for entree in ORACLE["echantillons"][nom]:
        premieres.setdefault(entree["objet"], entree)
    # Un JPEG compressé une seconde fois (FlateDecode puis DCTDecode) est un JPEG pour Poppler,
    # qui le décompresse ; il ne l'est pas ici (ADR-0225).
    doubles = {"15"} if nom == "formes" else set()
    jpeg = {
        objet: (entree["page"], entree["sha256"])
        for objet, entree in premieres.items()
        if entree["codage"] == "jpeg" and objet not in doubles
    }
    trouves = {
        str(e.localisation.chemin).split()[2]: (
            e.localisation.page,
            hashlib.sha256(octets(contenu, e)).hexdigest(),
        )
        for e in extractions
    }
    assert trouves == jpeg
    valeurs_ = valeurs_de(resultat)
    autres = [o for o, e in premieres.items() if e["codage"] != "jpeg" and o != "[inline]"]
    assert valeurs_["imagespdf.non_acheminees"] == len(autres) + len(doubles)
    assert raisons(resultat) == []


# Parties extraites et règles du catalogue (analyse complète)


ATTENDUS = {
    "imagemagick": {"R-IMAGESPDF-001"},
    "libreoffice": {"R-IMAGESPDF-001", "R-IMAGESPDF-002"},
    "ghostscript": {"R-IMAGESPDF-001"},
    "formes": {"R-IMAGESPDF-001", "R-IMAGESPDF-002"},
    "faux": {"R-IMAGESPDF-001"},
    "nombreuses": {"R-IMAGESPDF-001", "R-IMAGESPDF-003"},
    "chiffre": {"R-IMAGESPDF-004"},
}
ORDINAIRES = ("document", "ghostscript")
"""Échantillons de ``tests/donnees/pages`` (LibreOffice, Ghostscript), sans image."""


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("images")
    sources = {n: ECHANTILLONS / f"{n}.pdf" for n in ATTENDUS}
    sources |= {f"pages_{n}": DONNEES / "pages" / f"{n}.pdf" for n in ORDINAIRES}
    trouvees = {}
    for nom, source in sources.items():
        chemin = dossier / f"{nom}.pdf"
        chemin.write_bytes(source.read_bytes())
        trouvees[nom] = analyser(chemin)
    return trouvees


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "imagespdf"}


@pytest.mark.parametrize(
    ("nom", "attendues"),
    [*ATTENDUS.items(), *((f"pages_{n}", set()) for n in ORDINAIRES)],
)
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques if t.partie == 1}
    assert etats["imagespdf"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues
    assert not analyse.interrompue


def test_image_d_origine_ia_declaree_dans_un_pdf(analyses: dict[str, Analyse]) -> None:
    # L'image d'ImageMagick garde son XMP : son origine IA déclarée est vue dans la partie 2,
    # qui dit d'où elle vient (ADR-0224).
    analyse = analyses["imagemagick"]
    (extraite,) = analyse.identification.extraites
    assert (extraite.rang, extraite.format, extraite.fin_connue) == (2, "jpeg", True)
    assert extraite.origine is not None
    assert (extraite.origine.contenant, extraite.origine.module) == (1, "imagespdf")
    assert extraite.origine.localisation == Localisation(chemin="image (objet 8 0)", page=1)
    constats = {(c.regle.identifiant, c.partie) for c in analyse.constats}
    assert ("R-XMP-001", 2) in constats
    etats = {t.module: t.etat for t in analyse.couverture.techniques if t.partie == 2}
    for module in ("c2pa", "doublejpeg", "dwtdct", "ela", "exif", "image", "iptc", "xmp"):
        assert etats[module] is EtatTechnique.APPLIQUEE, module
    assert etats["imagespdf"] is etats["infopdf"] is EtatTechnique.NON_APPLICABLE
    # Les techniques hors V1 d'un JPEG figurent aussi pour la partie extraite (ADR-0087).
    hors_v1 = {
        (n.module, n.partie) for n in analyse.non_menees if n.raison is RaisonNonMenee.HORS_V1
    }
    assert {("bruit", 2), ("cfa", 2), ("prnu", 2)} <= hors_v1
    # Le filigrane dwtDct est recherché dans la partie extraite (ADR-0178).
    assert "M-DWTDCT" in analyse.couverture.marquages_recherches


def test_contenus_qui_ne_sont_pas_des_jpeg(analyses: dict[str, Analyse]) -> None:
    # faux.pdf : un PNG et des octets quelconques dans des flux DCTDecode, non menés pour format
    # partiel ; un JPEG coupé, partie extraite tronquée.
    analyse = analyses["faux"]
    (extraite,) = analyse.identification.extraites
    assert (extraite.rang, extraite.tronquee) == (2, True)
    assert extraite.origine is not None
    assert extraite.origine.localisation == Localisation(chemin="image (objet 12 0)", page=1)
    du_fichier = {
        (n.raison, n.partie, n.localisation.chemin if n.localisation else None)
        for n in analyse.non_menees
        if n.module is None
    }
    assert (RaisonNonMenee.FORMAT_PARTIEL, 1, "image (objet 10 0)") in du_fichier
    assert (RaisonNonMenee.FORMAT_PARTIEL, 1, "image (objet 11 0)") in du_fichier
    assert (RaisonNonMenee.FICHIER_TRONQUE, 2, None) in du_fichier


def test_seize_parties_extraites_au_plus(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["nombreuses"]
    extraites = analyse.identification.extraites
    assert [p.rang for p in extraites] == list(range(2, 18))
    limites = [n for n in analyse.non_menees if n.raison is RaisonNonMenee.LIMITE_DEPASSEE]
    assert [(n.module, n.partie, n.localisation) for n in limites] == [
        (None, 1, Localisation(chemin="image (objet 26 0)", page=1))
    ]


def jpeg_rembourre(taille: int) -> bytes:
    """``simple_75.jpg`` grossi de segments APP15 jusqu'à ``taille`` octets environ : un JPEG
    valide, dont l'analyse reste rapide (peu de données entropiques)."""
    segments = b""
    while len(SIMPLE) + len(segments) < taille:
        segments += b"\xff\xef" + (65535).to_bytes(2, "big") + bytes(65533)
    return SIMPLE[:2] + segments + SIMPLE[2:]


@pytest.mark.exigence("NF-06")
def test_budget_d_octets_de_bout_en_bout(tmp_path: Path) -> None:
    # Trois JPEG de 1,2 Mio : le deuxième franchit les 2 Mio et l'est encore, le troisième non.
    gros = jpeg_rembourre(1_200_000)
    objets = {10 + i: image(donnees=gros) for i in range(3)}
    contenu = document(b"/A 10 0 R/B 11 0 R/C 12 0 R", objets)
    chemin = tmp_path / "gros.pdf"
    chemin.write_bytes(contenu)
    analyse = analyser(chemin)
    assert [p.rang for p in analyse.identification.extraites] == [2, 3]
    assert regles(analyse) == {"R-IMAGESPDF-001", "R-IMAGESPDF-003"}
    assert not analyse.interrompue


def test_phrases_des_constats(analyses: dict[str, Analyse]) -> None:
    attendus = {
        "libreoffice": (
            "Le document porte 1 image(s) JPEG écrite(s) telle(s) quelle(s) (pages 1) : 1 sont "
            "analysée(s) chacune comme une partie extraite, par les modules d'image.",
            "1 image(s) du document (pages 1) ne sont pas des JPEG écrits tels quels (filtres : "
            "FlateDecode) : l'outil ne décode pas leurs pixels, aucun module d'image ne les a "
            "analysées.",
        ),
        "nombreuses": (
            "2 image(s) JPEG du document ne sont pas analysées : l'outil analyse, dans l'ordre "
            "des pages, seize images au plus, jusqu'à 2 Mio de données.",
        ),
        "chiffre": (
            "Le document est chiffré : ses 2 image(s) ne sont pas analysées, l'outil ne "
            "déchiffrant rien.",
        ),
    }
    for nom, phrases in attendus.items():
        page = export.exporter_html(analyses[nom])
        for phrase in phrases:
            assert escape(phrase) in page, phrase


def test_rapport_montre_les_parties_extraites(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["formes"]
    page = export.exporter_html(analyse)
    assert escape(texte("champs.extraites")) in page
    origine = "extraite de la partie 1 par imagespdf : chemin image (objet 14 0), page 2"
    assert escape(origine) in page
    signalement = texte("signalements.extraites", nombre=2, premiere=2, derniere=3)
    assert escape(signalement) in page
    lignes = resume(analyse, ())
    assert any(ligne.startswith("partie 3 : jpeg") and origine in ligne for ligne in lignes)
    unique = texte("signalements.extraite", premiere=2)
    assert unique in Presentation(analyses["imagemagick"], ()).signalements()
    document_json = json.loads(export.exporter_json(analyse))
    assert [p["rang"] for p in document_json["identification"]["extraites"]] == [2, 3]


def test_controle_avant_publication_complet(tmp_path: Path) -> None:
    # Le module ne lit aucune métadonnée identifiante : non mené, il ne rend pas le contrôle
    # avant publication incomplet (ADR-0227). Désactivé, aucune image n'est extraite. La page
    # d'image seule n'a pas de couche texte : la non menée de caracteres (ADR-0247), qui le rend
    # incomplet, est la seule qui compte.
    chemin = tmp_path / "imagemagick.pdf"
    chemin.write_bytes(echantillon("imagemagick"))
    analyse = analyser(chemin, desactiver={"imagespdf"})
    assert analyse.identification.extraites == ()
    assert "imagespdf" in {n.module for n in analyse.non_menees}
    (numerise,) = [n for n in analyse.non_menees if n.module == "caracteres"]
    assert numerise.raison is RaisonNonMenee.DOCUMENT_NUMERISE
    assert texte("resume.publication_incomplete") in Presentation(analyse, ()).publication()
    comptees = {
        n.module
        for n in analyse.non_menees
        if n.raison is not RaisonNonMenee.HORS_V1 and n.module not in _SANS_METADONNEES
    }
    assert comptees == {"caracteres"}


def test_document_sans_jpeg_ne_reprend_pas_d_autre_image() -> None:
    # Pixels compressés seuls : aucune partie extraite.
    pixels = zlib.compress(bytes(3))
    valeurs_ = obs(document(b"/A 10 0 R", {10: image(b"/Filter/FlateDecode", pixels)}))
    assert valeurs_["imagespdf.acheminees"] == 0
    assert valeurs_["imagespdf.non_acheminees.filtres"] == ["FlateDecode"]
