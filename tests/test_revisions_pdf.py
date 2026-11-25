"""Versions successives d'un PDF : lecteur, module ``revisionspdf``, chronologie en tableau,
règles du catalogue (T50, ADR-0207 à ADR-0212).

Les documents synthétiques sont construits ici, mise à jour par mise à jour (``maj``) ; les
échantillons de ``tests/donnees/revisions`` viennent de Ghostscript, LibreOffice, exiftool et
pyHanko, et ``oracle.json`` consigne ce qu'en disent pyHanko et ``pdfsig``
(``generer_revisions.py``).
"""

import contextlib
import dataclasses
import json
import tempfile
from collections.abc import Callable, Iterator
from html import escape
from pathlib import Path
from typing import Any

import pytest
from metadonnees import CATALOGUE_PDF, contexte, flux_pdf, pdf, raisons, resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import revisionspdf
from voight_kampff.modules._lecture import pdf as lecteur
from voight_kampff.modules._lecture import valeurs
from voight_kampff.rapport import comparaison, export
from voight_kampff.rapport._presentation import Presentation, accorder, texte, textes
from voight_kampff.rapport.modele import (
    COLONNES,
    LIGNES_MAX_TABLEAU,
    CategorieIdentifiante,
    EtatTechnique,
    Localisation,
    NatureVisualisation,
    Plage,
    Rapport,
    Visualisation,
)

pytestmark = pytest.mark.exigence("F-60")

ECHANTILLONS = Path(__file__).parent / "donnees" / "revisions"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
CHRONOLOGIE = NatureVisualisation.CHRONOLOGIE_REVISIONS
OBJETS = NatureVisualisation.OBJETS_REVISIONS
PARTIEL = "format_partiel"
FINE = "\N{NARROW NO-BREAK SPACE}"
"""Séparateur des milliers des nombres du rapport."""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


# Construction des documents

PAGE = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R>>"
PAGES = b"<</Type/Pages/Kids[3 0 R]/Count 1>>"
CONTENU = flux_pdf("", b"BT (Bonjour) Tj ET")
INFO = b"<</Producer(Outil)/CreationDate(D:20260101000000Z)/ModDate(D:20260101000000Z)>>"
TRAILER = "/Root 1 0 R/Info 5 0 R"


def base(objets: dict[int, bytes] | None = None, trailer: str = TRAILER, **options: Any) -> bytes:
    """Catalogue (1), arbre des pages (2), une page (3), son contenu (4), Info (5), et
    ``objets`` en plus ou à la place."""
    tous = {1: CATALOGUE_PDF, 2: PAGES, 3: PAGE, 4: CONTENU, 5: INFO} | (objets or {})
    return pdf(tous, trailer, **options)


def _startxref(document: bytes) -> int:
    return int(document[document.rindex(b"startxref") + 9 :].split()[0])


def maj(
    document: bytes,
    objets: dict[int, bytes],
    *,
    libres: dict[int, int] | None = None,
    brutes: dict[int, bytes] | None = None,
    trailer: str = TRAILER,
    fin: bytes = b"%%EOF\n",
    prev: int | None = None,
) -> bytes:
    """Mise à jour incrémentale en table classique : objets écrits, objets libérés (numéro →
    génération), entrées écrites telles quelles (``brutes``), une sous-section par entrée ;
    ``fin`` suit ``startxref``."""
    tampon = bytearray(document)
    entrees: dict[int, bytes] = {}
    for numero, corps in sorted(objets.items()):
        entrees[numero] = f"{len(tampon):010d} 00000 n".encode()
        tampon += f"{numero} 0 obj\n".encode() + corps + b"\nendobj\n"
    for numero, generation in (libres or {}).items():
        entrees[numero] = f"0000000000 {generation:05d} f".encode()
    entrees |= brutes or {}
    debut = len(tampon)
    tampon += b"xref\n"
    for numero, entree in sorted(entrees.items()):
        tampon += f"{numero} 1\n".encode() + entree + b"\r\n"
    precedente = _startxref(document) if prev is None else prev
    tampon += f"trailer\n<</Size 100{trailer}/Prev {precedente}>>\n".encode()
    tampon += f"startxref\n{debut}\n".encode() + fin
    return bytes(tampon)


def sans_marque(document: bytes, queue: bytes = b"") -> tuple[bytes, int]:
    """Le document sans son ``startxref`` final, remplacé par ``queue`` ; et la position de
    sa table, pour le ``/Prev`` de la mise à jour suivante."""
    return document[: document.rindex(b"startxref")] + queue, _startxref(document)


def lignes(contenu: bytes) -> list[dict[str, Any]]:
    return resultats("revisionspdf", contenu, "pdf")


def obs(contenu: bytes) -> dict[str, Any]:
    return valeurs_de(lignes(contenu))


def natures(contenu: bytes) -> list[str]:
    valeur: list[str] = obs(contenu)["revisionspdf.natures"]
    return valeur


def derniere(contenu: bytes) -> str:
    return natures(contenu)[-1]


def tableau(contenu: bytes, nature: str = CHRONOLOGIE) -> list[list[Any]]:
    (visualisation,) = [
        ligne["visualisation"]
        for ligne in lignes(contenu)
        if ligne["type"] == "visualisation" and ligne["visualisation"]["nature"] == nature
    ]
    resultat: list[list[Any]] = visualisation["lignes"]
    return resultat


def objets(contenu: bytes) -> list[list[Any]]:
    """Lignes du tableau des objets changés (T51, ADR-0217)."""
    return tableau(contenu, OBJETS)


@pytest.fixture
def ouvrir() -> Iterator[Callable[[bytes], lecteur.Document]]:
    """Document du lecteur sur un contenu ; les fichiers sont fermés à la fin du test."""
    with contextlib.ExitStack() as pile:

        def document(contenu: bytes) -> lecteur.Document:
            fichier = pile.enter_context(tempfile.TemporaryFile())
            return lecteur.Document(contexte(fichier, contenu, "pdf", "revisionspdf"))

        yield document


Ouvrir = Callable[[bytes], lecteur.Document]


# Lecteur : chaîne, fins de version, entrées, vues (ADR-0207)


def test_chaine_et_vues(ouvrir: Ouvrir) -> None:
    premiere = base()
    seconde = maj(premiere, {5: b"<</Producer(Autre)>>"}, libres={4: 1})
    document = ouvrir(seconde)
    recente, ancienne = document.chaine
    assert (recente.fin, ancienne.fin) == (len(seconde), len(premiere))
    assert recente.marquee
    assert ancienne.marquee
    assert not recente.flux
    assert not recente.hybride
    assert document.entrees(0) == {4: (0, 0, 1), 5: (1, len(premiere), 0)}
    assert set(document.entrees(1)) == {0, 1, 2, 3, 4, 5}
    vue = document.vue(1)
    assert vue.sections == 1
    assert vue.chaine == (ancienne,)
    assert vue.trailer["Info"] == lecteur.Ref(5, 0)
    info = vue.objet(lecteur.Ref(5, 0))
    assert isinstance(info, dict)
    assert info["Producer"] == b"Outil"
    info = document.objet(lecteur.Ref(5, 0))
    assert isinstance(info, dict)
    assert info["Producer"] == b"Autre"
    assert document.entree(4) == (0, 0, 1)
    entree = vue.entree(4)
    assert entree is not None
    assert entree[0] == 1
    assert document.entree(99) is None


def test_chaine_en_flux(ouvrir: Ouvrir) -> None:
    premiere = pdf({1: CATALOGUE_PDF, 2: b"<<>>"}, flux_xref=True, flux_objets={9: (2,)})
    seconde = pdf({3: b"<<>>"}, "", base=premiere, flux_xref=True)
    document = ouvrir(seconde)
    recente, ancienne = document.chaine
    assert recente.flux
    assert ancienne.flux
    assert recente.marquee
    assert ancienne.marquee
    assert (recente.fin, ancienne.fin) == (len(seconde), len(premiere))
    assert document.entrees(1)[2] == (2, 9, 0)


@pytest.mark.parametrize(
    ("fin", "longueur"),
    [
        pytest.param(b"%%EOF\r\n", 7, id="crlf"),
        pytest.param(b"%%EOF\r", 6, id="cr"),
        pytest.param(b"%%EOF", 5, id="sans-fin-de-ligne"),
        pytest.param(b"  %%EOF\n\n", 8, id="blancs"),
    ],
)
def test_marque_de_fin(ouvrir: Ouvrir, fin: bytes, longueur: int) -> None:
    contenu = maj(base(), {6: b"<<>>"}, fin=fin)
    section = ouvrir(contenu).chaine[0]
    assert section.marquee
    assert section.fin == len(contenu) - len(fin) + longueur


@pytest.mark.parametrize(
    "queue",
    [
        pytest.param(b"", id="rien"),
        pytest.param(b"startxref\nnul\n%%EOF\n", id="sans-nombre"),
        pytest.param(b"startxref\n12\n%EOF\n", id="mauvais-mot"),
        pytest.param(b")\n", id="illisible"),
        pytest.param(b"startxref\n12", id="tronquee"),
    ],
)
def test_marque_de_fin_absente(ouvrir: Ouvrir, queue: bytes) -> None:
    coupee, position = sans_marque(base(), queue)
    contenu = maj(coupee, {6: b"<<>>"}, prev=position)
    recente, ancienne = ouvrir(contenu).chaine
    assert recente.marquee
    assert not ancienne.marquee
    assert ancienne.fin == base().rindex(b">>\nstartxref") + 2  # fin du trailer


def test_entree_illisible_a_l_enumeration(ouvrir: Ouvrir) -> None:
    contenu = base()
    position = contenu.rindex(b"xref\n0 6\n") + len(b"xref\n0 6\n") + 3 * 20
    abime = contenu[:position] + b"x" * 18 + contenu[position + 18 :]
    with pytest.raises(lecteur.Illisible):
        ouvrir(abime).entrees(0)


def test_premier_objet(ouvrir: Ouvrir) -> None:
    assert ouvrir(base()).premier_objet() == {"Type": "Catalog", "Pages": lecteur.Ref(2, 0)}
    illisible = b"%PDF-1.7\n)    \n" + base()[15:]
    assert ouvrir(illisible).premier_objet() is None


# Module : versions, fins, natures (ADR-0207, ADR-0208)


def test_document_illisible() -> None:
    resultat = lignes(b"%PDF-1.7\nrien\n")
    assert raisons(resultat) == [PARTIEL]
    assert [ligne["type"] for ligne in resultat] == ["non_menee"]


def test_une_seule_version() -> None:
    contenu = base()
    resultat = lignes(contenu)
    valeurs_ = valeurs_de(resultat)
    assert valeurs_ == {
        "revisionspdf.versions": 1,
        "revisionspdf.sections": 1,
        "revisionspdf.chiffre": False,
        "revisionspdf.linearise": False,
        "revisionspdf.fins": [len(contenu)],
        "revisionspdf.natures": ["originale"],
        "revisionspdf.ajoutes": [5],
        "revisionspdf.remplaces": [0],
        "revisionspdf.supprimes": [0],
        "revisionspdf.octets_apres_fin": 0,
        "revisionspdf.versions_non_reconnues": 0,
        "revisionspdf.signatures": 0,
        "revisionspdf.objets": 0,
    }
    assert not [ligne for ligne in resultat if ligne["type"] == "visualisation"]


def test_metadonnees_et_dates() -> None:
    seconde = maj(base(), {5: b"<</Producer(Autre)/ModDate(D:20260202000000Z)>>"})
    troisieme = maj(seconde, {5: b"<</Producer(Encore)/ModDate(D:20260202000000Z)>>"})
    valeurs_ = obs(troisieme)
    assert valeurs_["revisionspdf.natures"] == ["originale", "metadonnees", "metadonnees"]
    assert valeurs_["revisionspdf.remplaces"] == [0, 1, 1]
    assert valeurs_["revisionspdf.versions_non_reconnues"] == 0
    dates = [ligne[6] for ligne in tableau(troisieme)]
    assert dates == ["D:20260101000000Z", "D:20260202000000Z", ""]


def abimer(contenu: bytes, numero: int, *, premier: bool = False) -> bytes:
    """L'objet ``numero`` rendu illisible : « n 0 obj » devient « x 0 obj » (sa dernière
    écriture, ou la première avec ``premier``)."""
    motif = f"\n{numero} 0 obj".encode()
    position = (contenu.index(motif) if premier else contenu.rindex(motif)) + 1
    return contenu[:position] + b"x" * len(str(numero)) + contenu[position + len(str(numero)) :]


@pytest.mark.parametrize(
    ("info", "date", "illisible"),
    [
        pytest.param(b"<</CreationDate(D:2025)>>", "D:2025", False, id="creation-a-defaut"),
        pytest.param(b"<</ModDate 7>>", "", False, id="pas-une-chaine"),
        pytest.param(b"<</ModDate(" + b"9" * 65 + b")>>", "", False, id="trop-longue"),
        pytest.param(b"[1]", "", False, id="pas-un-dictionnaire"),
        pytest.param(b"<</ModDate 9 0 R>>", "", True, id="illisible"),
    ],
)
def test_date_de_la_premiere_version(info: bytes, date: str, illisible: bool) -> None:
    premiere = base({5: info, 9: b"<</A 1>>"})
    if illisible:
        premiere = abimer(premiere, 9)
    contenu = maj(premiere, {6: b"<<>>"})
    assert tableau(contenu)[0][6] == date


def test_document_chiffre_sans_dates() -> None:
    premiere = base(trailer=TRAILER + "/Encrypt<</Filter/Standard>>")
    contenu = maj(premiere, {5: b"<</ModDate(chiffree)>>"}, trailer=TRAILER)
    valeurs_ = obs(contenu)
    assert valeurs_["revisionspdf.chiffre"] is True
    assert [ligne[6] for ligne in tableau(contenu)] == ["", ""]


def test_contenu_change() -> None:
    contenu = maj(base(), {4: flux_pdf("", b"BT (Autre) Tj ET")})
    assert natures(contenu) == ["originale", "non_reconnue"]
    assert obs(contenu)["revisionspdf.versions_non_reconnues"] == 1


def test_page_ajoutee_et_supprimee() -> None:
    page = b"<</Type/Page/Parent 2 0 R>>"
    ajoutee = maj(base(), {6: page, 2: b"<</Type/Pages/Kids[3 0 R 6 0 R]/Count 2>>"})
    assert derniere(ajoutee) == "non_reconnue"
    supprimee = maj(ajoutee, {2: PAGES}, libres={6: 1})
    assert derniere(supprimee) == "non_reconnue"
    assert obs(supprimee)["revisionspdf.supprimes"] == [0, 0, 1]


def test_entrees_redites_sans_changement() -> None:
    # La page redite à sa position, un numéro jamais employé libéré : rien ne change.
    premiere = base()
    position = premiere.index(b"\n3 0 obj") + 1
    brutes = {3: f"{position:010d} 00000 n".encode()}
    contenu = maj(premiere, {}, libres={50: 0}, brutes=brutes)
    valeurs_ = obs(contenu)
    assert valeurs_["revisionspdf.natures"] == ["originale", "structure"]
    assert (valeurs_["revisionspdf.ajoutes"], valeurs_["revisionspdf.supprimes"]) == (
        [5, 0],
        [0, 0],
    )
    assert valeurs_["revisionspdf.remplaces"] == [0, 0]


def test_page_reecrite_a_l_identique() -> None:
    contenu = maj(base(), {3: PAGE + b" "})
    assert derniere(contenu) == "structure"


def test_arbre_des_pages_change_dans_ses_annotations() -> None:
    contenu = maj(base(), {2: b"<</Type/Pages/Kids[3 0 R]/Count 1/Annots[]>>"})
    assert derniere(contenu) == "non_reconnue"


@pytest.mark.parametrize(
    ("annotation", "nature"),
    [
        pytest.param(b"<</Type/Annot/Subtype/Text/Rect[0 0 1 1]>>", "annotation", id="note"),
        pytest.param(b"<</Subtype/Square/Rect[0 0 1 1]>>", "annotation", id="sans-type"),
        pytest.param(b"<</Subtype/Widget/Rect[0 0 1 1]/FT/Tx>>", "formulaire", id="widget"),
        pytest.param(b"<</Subtype/Widget/Rect[0 0 1 1]/FT/Sig>>", "signature", id="widget-sig"),
    ],
)
def test_annotation_ajoutee_a_une_page(annotation: bytes, nature: str) -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[6 0 R]>>"
    contenu = maj(base(), {3: page, 6: annotation})
    assert derniere(contenu) == nature


def test_annotations_d_une_page_mixtes() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[6 0 R 7 0 R]>>"
    widget = b"<</Subtype/Widget/Rect[0 0 1 1]/FT/Tx>>"
    note = b"<</Subtype/Text/Rect[0 0 1 1]>>"
    contenu = maj(base(), {3: page, 6: widget, 7: note})
    assert derniere(contenu) == "formulaire+annotation"
    seule = maj(base(), {3: page, 6: widget, 7: widget})
    assert derniere(seule) == "formulaire"


def test_annotation_existante_rattachee_a_la_page() -> None:
    premiere = base({6: b"<</Subtype/Widget/Rect[0 0 1 1]/FT/Tx>>"})
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[6 0 R]>>"
    assert derniere(maj(premiere, {3: page})) == "formulaire"


def test_annotation_retiree_d_une_page() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[6 0 R]>>"
    premiere = base({3: page, 6: b"<</Subtype/Text/Rect[0 0 1 1]>>"})
    contenu = maj(premiere, {3: PAGE}, libres={6: 1})
    assert derniere(contenu) == "annotation"


def test_annotations_en_tableau_indirect() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots 6 0 R>>"
    premiere = base({6: b"[7 0 R]", 7: b"<</Subtype/Widget/Rect[0 0 1 1]/FT/Tx>>"})
    assert derniere(maj(premiere, {3: page})) == "formulaire"


def test_annotations_illisibles() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots 6 0 R>>"
    resultat = lignes(maj(abimer(base({6: b"[]"}), 6), {3: page}))
    assert valeurs_de(resultat)["revisionspdf.natures"][-1] == "non_lue"
    assert PARTIEL in raisons(resultat)
    # Une annotation ajoutée qui ne se lit pas : la page reste rangée parmi les annotations.
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[6 0 R]>>"
    premiere = abimer(base({6: b"<</Subtype/Widget/Rect[0 0 1 1]/FT/Tx>>"}), 6)
    resultat = lignes(maj(premiere, {3: page}))
    assert valeurs_de(resultat)["revisionspdf.natures"][-1] == "annotation"
    assert PARTIEL in raisons(resultat)


def test_ancienne_page_illisible() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[]>>"
    assert derniere(maj(abimer(base(), 3), {3: page})) == "non_lue"


@pytest.mark.parametrize(
    ("catalogue", "nature"),
    [
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/AcroForm<<>>>>", "formulaire", id="acroform"),
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/DSS<<>>>>", "signature", id="dss"),
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/Perms<<>>>>", "signature", id="perms"),
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/Metadata<<>>>>", "metadonnees", id="xmp"),
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/Version/2.0>>", "structure", id="version"),
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/Extensions<<>>>>", "structure", id="ext"),
        pytest.param(b"<</Type/Catalog/Pages 2 0 R/OpenAction[]>>", "non_reconnue", id="action"),
        pytest.param(b"[1]", "non_reconnue", id="pas-un-dictionnaire"),
    ],
)
def test_catalogue_change(catalogue: bytes, nature: str) -> None:
    assert derniere(maj(base(), {1: catalogue})) == nature


def test_catalogue_absent_ou_illisible() -> None:
    # Le trailer de la mise à jour désigne un catalogue qui n'existe pas : objet nul.
    absent = maj(base(), {6: b"<<>>"}, trailer="/Root 9 0 R/Info 5 0 R")
    assert derniere(absent) == "non_reconnue"
    resultat = lignes(maj(abimer(base(), 1), {6: b"<<>>"}))
    assert valeurs_de(resultat)["revisionspdf.natures"][-1] == "non_lue"
    assert PARTIEL in raisons(resultat)


@pytest.mark.parametrize(
    ("objets", "nature"),
    [
        pytest.param({7: b"<</FT/Tx/T(Nom)>>"}, "formulaire", id="champ"),
        pytest.param({7: b"<</FT/Sig/T(S)>>"}, "signature", id="champ-signature"),
        pytest.param({7: b"<</T(Parent)/Kids[]>>"}, "formulaire", id="champ-parent"),
        pytest.param({7: b"[8 0 R]", 8: b"<</FT/Tx>>"}, "formulaire", id="tableau-de-champs"),
        pytest.param({7: b"[8 0 R]", 8: b"<</FT/Sig>>"}, "signature", id="tableau-signature"),
        pytest.param({7: b"[8 0 R]", 8: b"<</Subtype/Text/Rect[]>>"}, "annotation", id="notes"),
        pytest.param({7: b"[]"}, "structure", id="tableau-vide"),
        pytest.param({7: b"[8 0 R]", 8: b"<<>>"}, "non_reconnue", id="tableau-inconnu"),
    ],
)
def test_champs_designes_par_le_formulaire(objets: dict[int, bytes], nature: str) -> None:
    catalogue = b"<</Type/Catalog/Pages 2 0 R/AcroForm<</Fields 7 0 R>>>>"
    assert derniere(maj(base({1: catalogue}), objets)) == nature


def test_tableau_trop_long(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(revisionspdf, "_ELEMENTS_MAX", 1)
    catalogue = b"<</Type/Catalog/Pages 2 0 R/AcroForm<</Fields 7 0 R>>>>"
    contenu = maj(base({1: catalogue}), {7: b"[8 0 R 8 0 R]", 8: b"<</FT/Tx>>"})
    assert derniere(contenu) == "formulaire+non_reconnue"


@pytest.mark.parametrize(
    ("objet", "nature"),
    [
        pytest.param(flux_pdf("/Type/Metadata/Subtype/XML", b"<x/>"), "metadonnees", id="xmp"),
        pytest.param(b"<</Type/DSS>>", "signature", id="dss"),
        pytest.param(b"<</Type/Sig/ByteRange[0 1 2 3]>>", "signature", id="sig"),
        pytest.param(b"<</Type/DocTimeStamp>>", "signature", id="horodatage"),
        pytest.param(b"<</Type/XRef>>", "structure", id="xref"),
        pytest.param(b"null", "structure", id="nul"),
        pytest.param(b"<</Type[/Catalog]>>", "structure", id="type-qui-n-est-pas-un-nom"),
    ],
)
def test_objet_range_par_son_type(objet: bytes, nature: str) -> None:
    # Objet ajouté que rien ne désigne : son type dit sa nature ; sans type connu, il est
    # orphelin, compté comme structure.
    assert derniere(maj(base(), {6: objet})) == nature


def test_propagation_aux_objets_designes() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Annots[6 0 R]>>"
    note = b"<</Subtype/Text/Rect[0 0 1 1]/AP<</N 7 0 R>>>>"
    apparence = flux_pdf("/Subtype/Form/Resources<</Font<</F 8 0 R>>>>", b"q Q")
    police = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"
    contenu = maj(base(), {3: page, 6: note, 7: apparence, 8: police, 9: b"12"})
    # 9 n'est désigné par rien : orphelin, compté comme structure.
    assert derniere(contenu) == "annotation"


def test_objet_ajoute_designe_par_un_objet_ancien() -> None:
    # Un objet de la première version désigne un numéro encore libre, que la mise à jour
    # remplit : il change ce qu'affiche le document sans changer l'objet qui le désigne.
    premiere = base({3: b"<</Type/Page/Parent 2 0 R/Contents[4 0 R 6 0 R]>>"})
    contenu = maj(premiere, {6: flux_pdf("", b"BT (Ajout) Tj ET")})
    assert derniere(contenu) == "non_reconnue"


def test_orphelins_parcours_borne(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(revisionspdf, "PARCOURS_MAX", 0)
    assert derniere(maj(base(), {6: b"<<>>"})) == "non_lue"


def test_orphelins_parcours_illisible() -> None:
    seconde = maj(abimer(base({6: b"<</A 1>>"}), 6), {1: b"<</Type/Catalog/Pages 2 0 R/X 6 0 R>>"})
    assert derniere(maj(seconde, {7: b"<<>>"})) == "non_lue"


def test_objet_change_illisible() -> None:
    resultat = lignes(abimer(maj(base(), {6: b"<<>>"}), 6))
    assert valeurs_de(resultat)["revisionspdf.natures"][-1] == "non_lue"
    assert PARTIEL in raisons(resultat)


def test_entrees_illisibles() -> None:
    premiere = base()
    position = premiere.rindex(b"xref\n0 6\n") + len(b"xref\n0 6\n") + 3 * 20
    abimee = premiere[:position] + b"x" * 18 + premiere[position + 18 :]
    resultat = lignes(maj(abimee, {3: PAGE + b" "}))
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["revisionspdf.natures"] == ["originale", "non_lue"]
    assert valeurs_["revisionspdf.ajoutes"] == [0, 0]
    assert raisons(resultat).count(PARTIEL) == 2


def test_section_sans_marque_et_octets_apres_la_fin() -> None:
    coupee, position = sans_marque(base())
    contenu = maj(coupee, {6: b"<<>>"}, prev=position) + b"donnees ajoutees\n"
    valeurs_ = obs(contenu)
    assert valeurs_["revisionspdf.sans_marque_de_fin"] == 1
    assert valeurs_["revisionspdf.octets_apres_fin"] == len(b"donnees ajoutees\n")


def test_mise_a_jour_en_flux_et_flux_d_objets() -> None:
    premiere = pdf({1: CATALOGUE_PDF, 2: PAGES, 3: PAGE, 4: CONTENU}, flux_xref=True)
    seconde = pdf(
        {5: b"<</Producer(P)>>", 6: b"<<>>"},
        "/Root 1 0 R/Info 5 0 R",
        base=premiere,
        flux_xref=True,
        flux_objets={8: (5,)},
    )
    valeurs_ = obs(seconde)
    assert valeurs_["revisionspdf.natures"] == ["originale", "metadonnees"]
    # 5, flux de la table de la première version, devient le dictionnaire Info, rangé dans le
    # flux d'objets 8 ; 6 est orphelin, 9 est le nouveau flux de la table.
    assert (valeurs_["revisionspdf.ajoutes"][1], valeurs_["revisionspdf.remplaces"][1]) == (3, 1)


def test_listes_coupees(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valeurs, "NOMBRE_MAX_ELEMENTS", 2)
    contenu = maj(maj(base(), {6: b"<<>>"}), {7: b"<<>>"})
    valeurs_ = obs(contenu)
    for nom in ("fins", "natures", "ajoutes", "remplaces", "supprimes"):
        assert len(valeurs_[f"revisionspdf.{nom}"]) == 2
        assert valeurs_[f"revisionspdf.{nom}.longueur"] == 3


# Linéarisation (ADR-0207)

LINEARISATION = b"<</Linearized 1/L 1000>>"


def test_linearisation_mal_formee() -> None:
    # Le premier objet se dit linéarisé, mais les sections ne sont pas celles d'une
    # linéarisation : chacune reste une version.
    premiere = pdf(
        {1: LINEARISATION, 2: PAGES, 3: PAGE, 4: CONTENU, 6: CATALOGUE_PDF}, "/Root 6 0 R"
    )
    contenu = maj(premiere, {5: b"<<>>"}, trailer="/Root 6 0 R")
    valeurs_ = obs(contenu)
    assert valeurs_["revisionspdf.linearise"] is True
    assert valeurs_["revisionspdf.linearisation.longueur"] == 1000
    assert valeurs_["revisionspdf.versions"] == 2
    seule = obs(premiere)
    assert (seule["revisionspdf.linearise"], seule["revisionspdf.versions"]) == (True, 1)
    sans_longueur = pdf({1: b"<</Linearized 1>>", 6: CATALOGUE_PDF}, "/Root 6 0 R")
    assert "revisionspdf.linearisation.longueur" not in obs(sans_longueur)


@pytest.mark.parametrize("nom", ["lineaire.pdf", "lineaire_maj.pdf"])
def test_linearisation_de_ghostscript(nom: str) -> None:
    contenu = (ECHANTILLONS / nom).read_bytes()
    valeurs_ = obs(contenu)
    assert valeurs_["revisionspdf.linearise"] is True
    assert valeurs_["revisionspdf.sections"] == valeurs_["revisionspdf.versions"] + 1
    assert valeurs_["revisionspdf.fins"][0] == valeurs_["revisionspdf.linearisation.longueur"]


# Signatures (ADR-0209)

CONTENTS = b"<" + b"0" * 32 + b">"
SIGNATURE = b"<</Type/Sig/Filter/Adobe.PPKLite/SubFilter/adbe.pkcs7.detached/M(D:20260303000000Z)"
LARGEUR_PLAGE = 40
AVANT_CONTENTS = len(SIGNATURE) + len(b"/ByteRange[") + LARGEUR_PLAGE + len(b"]/Contents ")
"""Octets du dictionnaire de signature avant sa valeur ``/Contents``."""


def signe(
    document: bytes,
    *,
    plage: Callable[[int, int, int], str] | None = None,
    champ: bytes = b"<</FT/Sig/T(S)/V 8 0 R>>",
    signature: bytes = SIGNATURE,
    catalogue: bytes = b"<</Type/Catalog/Pages 2 0 R/AcroForm<</Fields[7 0 R]>>>>",
    autres: dict[int, bytes] | None = None,
) -> bytes:
    """Mise à jour qui signe ``document`` : la plage couvre la version qu'elle écrit, sauf la
    valeur ``/Contents`` ; ``plage(coupure, reprise, fin)`` peut l'écrire autrement."""
    gabarit = b"/ByteRange[%s]/Contents " + CONTENTS + b">>"
    largeur = LARGEUR_PLAGE
    signature_ = signature + gabarit % (b" " * largeur)
    provisoire = maj(document, {1: catalogue, 7: champ, 8: signature_} | (autres or {}))
    coupure = provisoire.index(CONTENTS, len(document))
    reprise = coupure + len(CONTENTS)
    fin = len(provisoire)
    texte_ = plage(coupure, reprise, fin) if plage else f"0 {coupure} {reprise} {fin - reprise}"
    signature_ = signature + gabarit % texte_.encode().ljust(largeur)
    resultat = maj(document, {1: catalogue, 7: champ, 8: signature_} | (autres or {}))
    assert len(resultat) == fin
    return resultat


def test_signature_complete() -> None:
    signee = signe(base())
    valeurs_ = obs(signee)
    assert valeurs_["revisionspdf.signatures"] == 1
    assert valeurs_["revisionspdf.signature.1.version"] == 2
    assert valeurs_["revisionspdf.signature.1.plage_complete"] is True
    assert valeurs_["revisionspdf.signature.1.sous_filtre"] == "adbe.pkcs7.detached"
    assert valeurs_["revisionspdf.signature.1.date"] == "D:20260303000000Z"
    assert valeurs_["revisionspdf.derniere_version_signee"] == 2
    assert valeurs_["revisionspdf.non_reconnues_apres_signature"] == 0
    assert valeurs_["revisionspdf.natures"] == ["originale", "signature+formulaire"]
    assert tableau(signee)[1][7] == 1
    modifiee = maj(signee, {4: flux_pdf("", b"BT (Autre) Tj ET")})
    assert obs(modifiee)["revisionspdf.non_reconnues_apres_signature"] == 1


@pytest.mark.parametrize(
    "plage",
    [
        pytest.param(lambda c, r, f: f"1 {c - 1} {r} {f - r}", id="pas-au-debut"),
        pytest.param(lambda c, r, f: f"0 {c} {r} {f - r - 1}", id="fin-d-aucune-version"),
        pytest.param(lambda c, r, f: f"0 {c + 1} {r} {f - r}", id="trou-mal-place"),
        pytest.param(lambda c, r, f: f"0 {r} {c} {f - c}", id="trou-inverse"),
        pytest.param(lambda c, r, f: f"0 {c} {r}", id="trois-nombres"),
        pytest.param(lambda c, r, f: f"0 -1 {r} {f - r}", id="negatif"),
    ],
)
def test_signature_incomplete(plage: Callable[[int, int, int], str]) -> None:
    valeurs_ = obs(signe(base(), plage=plage))
    assert valeurs_["revisionspdf.signature.1.plage_complete"] is False
    assert "revisionspdf.derniere_version_signee" not in valeurs_


def test_signature_trou_trop_grand(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(revisionspdf, "_CONTENU_MAX", 8)
    valeurs_ = obs(signe(base()))
    assert valeurs_["revisionspdf.signature.1.version"] == 2
    assert valeurs_["revisionspdf.signature.1.plage_complete"] is False


def test_signature_trou_non_hexadecimal() -> None:
    # La plage laisse de côté tout le dictionnaire de signature, pas seulement /Contents.
    signee = signe(base(), plage=lambda c, r, f: f"0 {c - AVANT_CONTENTS} {r} {f - r}")
    assert signee[signee.rindex(CONTENTS) - AVANT_CONTENTS :].startswith(b"<</Type/Sig")
    assert obs(signee)["revisionspdf.signature.1.plage_complete"] is False


def test_champs_de_signature_herites_et_partages() -> None:
    champ = b"<</FT/Sig/T(P)/Kids[9 0 R 10 0 R 7 0 R]/V 8 0 R>>"
    autres = {9: b"<</T(A)/V 8 0 R>>", 10: b"<</T(B)/V<</ByteRange[]>>>>", 11: b"<</T(C)>>"}
    valeurs_ = obs(signe(base(), champ=champ, autres=autres))
    # 7 et 9 désignent la même signature ; 10 une signature directe ; 7 revient sans boucle.
    assert valeurs_["revisionspdf.signatures"] == 2
    assert valeurs_["revisionspdf.signature.2.plage_complete"] is False


def test_champs_sans_valeur_ni_dictionnaire() -> None:
    catalogue = b"<</Type/Catalog/Pages 2 0 R/AcroForm<</Fields[7 0 R 9 0 R 12]>>>>"
    autres = {9: b"<</FT/Sig/V 10 0 R>>", 10: b"[1]"}
    valeurs_ = obs(signe(base(), catalogue=catalogue, autres=autres))
    assert valeurs_["revisionspdf.signatures"] == 1


def test_signatures_au_dela_de_la_limite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(revisionspdf, "SIGNATURES_MAX", 0)
    valeurs_ = obs(signe(base()))
    assert valeurs_["revisionspdf.signatures"] == 1
    assert "revisionspdf.signature.1.version" not in valeurs_
    assert valeurs_["revisionspdf.derniere_version_signee"] == 2


def test_signature_d_un_document_chiffre_sans_date() -> None:
    premiere = base(trailer=TRAILER + "/Encrypt<</Filter/Standard>>")
    valeurs_ = obs(signe(premiere))
    assert "revisionspdf.signature.1.date" not in valeurs_
    assert "revisionspdf.signature.1.sous_filtre" in valeurs_


def test_signature_sans_sous_filtre_ni_date() -> None:
    valeurs_ = obs(signe(base(), signature=b"<</Type/Sig/M 3"))
    assert "revisionspdf.signature.1.sous_filtre" not in valeurs_
    assert "revisionspdf.signature.1.date" not in valeurs_


def test_formulaire_illisible() -> None:
    catalogue = b"<</Type/Catalog/Pages 2 0 R/AcroForm 9 0 R>>"
    resultat = lignes(abimer(maj(base(), {1: catalogue, 9: b"<</Fields[]>>"}), 9))
    assert valeurs_de(resultat)["revisionspdf.signatures"] == 0
    assert PARTIEL in raisons(resultat)


DOCMDP = b"/Reference[<</TransformMethod/DocMDP/TransformParams<<%s>>>>]"


@pytest.mark.parametrize(
    ("perms", "reference", "niveau"),
    [
        pytest.param(b"<</DocMDP 8 0 R>>", DOCMDP % b"/P 1", 1, id="aucune-modification"),
        pytest.param(b"<</DocMDP 8 0 R>>", DOCMDP % b"", 2, id="p-par-defaut"),
        pytest.param(b"<</DocMDP 8 0 R>>", DOCMDP % b"/P 7", None, id="p-inconnu"),
        pytest.param(b"<</DocMDP 8 0 R>>", b"/Reference[<</TransformMethod/FieldMDP>>]", 2, id="f"),
        pytest.param(b"<</DocMDP 8 0 R>>", b"", 2, id="sans-reference"),
        pytest.param(b"<<>>", b"", None, id="sans-certification"),
    ],
)
def test_docmdp(perms: bytes, reference: bytes, niveau: int | None) -> None:
    catalogue = b"<</Type/Catalog/Pages 2 0 R/AcroForm<</Fields[7 0 R]>>/Perms" + perms + b">>"
    signature = b"<</Type/Sig/SubFilter/adbe.pkcs7.detached" + reference
    valeurs_ = obs(signe(base(), catalogue=catalogue, signature=signature))
    assert valeurs_.get("revisionspdf.docmdp") == niveau


# Échantillons et oracle (pyHanko, pdfsig)


@pytest.mark.parametrize("nom", sorted(ORACLE))
def test_echantillons_et_oracle(nom: str) -> None:
    contenu = (ECHANTILLONS / nom).read_bytes()
    oracle = ORACLE[nom]
    assert len(contenu) == oracle["taille"]
    valeurs_ = obs(contenu)
    # pyHanko compte les deux sections d'une linéarisation comme deux révisions.
    linearise = 1 if valeurs_["revisionspdf.linearise"] else 0
    assert valeurs_["revisionspdf.versions"] == oracle["revisions_pyhanko"] - linearise
    fins = valeurs_["revisionspdf.fins"]
    assert valeurs_["revisionspdf.signatures"] == len(oracle["signatures"])
    for rang, signature in enumerate(oracle["signatures"], start=1):
        version = valeurs_[f"revisionspdf.signature.{rang}.version"]
        assert fins[version - 1] == signature["fin"]
        assert valeurs_[f"revisionspdf.signature.{rang}.plage_complete"] is signature["intacte"]
        entiere = signature["couverture"] == "ENTIRE_FILE"
        assert (version == len(fins)) is entiere
        assert (oracle["pdfsig"][rang - 1] == "- Total document signed") is entiere
        if signature["docmdp"] is not None:
            assert valeurs_["revisionspdf.docmdp"] == signature["docmdp"]


NATURES_ATTENDUES = {
    "formulaire.pdf": [
        "originale",
        "formulaire+metadonnees",
        "signature+formulaire+metadonnees",
        "formulaire+metadonnees",
    ],
    "certifie.pdf": ["originale", "signature+formulaire+metadonnees"],
    "lineaire.pdf": ["originale"],
    "lineaire_maj.pdf": ["originale", "metadonnees"],
    "modifie.pdf": ["originale", "metadonnees+non_reconnue"],
}


@pytest.mark.parametrize("nom", sorted(NATURES_ATTENDUES))
def test_natures_des_echantillons(nom: str) -> None:
    assert natures((ECHANTILLONS / nom).read_bytes()) == NATURES_ATTENDUES[nom]


@pytest.mark.parametrize(
    ("nom", "derniere_nature"),
    [
        ("signe.pdf", "signature+formulaire+metadonnees"),
        ("signe_annote.pdf", "annotation+metadonnees"),
        ("signe_modifie.pdf", "metadonnees+non_reconnue"),
    ],
)
def test_natures_des_echantillons_signes(nom: str, derniere_nature: str) -> None:
    valeurs_ = natures((ECHANTILLONS / nom).read_bytes())
    assert valeurs_[:4] == NATURES_ATTENDUES["formulaire.pdf"]
    assert valeurs_[-1] == derniere_nature


# Modèle : visualisation en tableau (ADR-0212)

LIGNE = (1, 100, "originale", 3, 0, 0, "D:2026", 0)


def test_tableau_aller_retour() -> None:
    tableau_ = Visualisation.tableau(
        "revisionspdf",
        CHRONOLOGIE,
        [LIGNE, (2, 200, "signature+formulaire", 1, 2, 0, "", 1)],
        localisation=Localisation(chemin="c", octets=Plage(0, 200)),
        partie=2,
    )
    assert tableau_.est_un_tableau
    assert tableau_.identifiante is None
    assert (tableau_.largeur, tableau_.hauteur, tableau_.png) == (8, 2, b"")
    document = tableau_.vers_dict()
    assert document["colonnes"] == [nom for nom, _ in COLONNES[CHRONOLOGIE]]
    assert set(document) == {"module", "nature", "colonnes", "lignes", "localisation", "partie"}
    assert Visualisation.depuis_dict(document) == tableau_


@pytest.mark.parametrize(
    ("lignes_", "message"),
    [
        pytest.param([], "aucune ou trop nombreuses", id="vide"),
        pytest.param([LIGNE] * (LIGNES_MAX_TABLEAU + 1), "trop nombreuses", id="trop"),
        pytest.param([LIGNE[:7]], "autre largeur", id="largeur"),
        pytest.param([(True, *LIGNE[1:])], "type de cellule", id="booleen"),
        pytest.param([(1, 2, 3, *LIGNE[3:])], "type de cellule", id="entier-en-texte"),
        pytest.param([(-1, *LIGNE[1:])], "hors bornes", id="negatif"),
        pytest.param([(*LIGNE[:6], "x" * 65, 0)], "trop long", id="texte-trop-long"),
    ],
)
def test_tableau_refuse(lignes_: list[tuple[Any, ...]], message: str) -> None:
    with pytest.raises((ValueError, TypeError), match=message):
        Visualisation.tableau("revisionspdf", CHRONOLOGIE, lignes_)


def test_tableau_mal_construit() -> None:
    with pytest.raises(ValueError, match="pas un tableau"):
        Visualisation.tableau("ela", NatureVisualisation.CARTE_ELA, [LIGNE])
    with pytest.raises(ValueError, match="pas d'image"):
        Visualisation("revisionspdf", CHRONOLOGIE, 8, 1, b"x", lignes=(LIGNE,))
    with pytest.raises(ValueError, match="dimensions"):
        Visualisation("revisionspdf", CHRONOLOGIE, 7, 1, b"", lignes=(LIGNE,))
    with pytest.raises(ValueError, match="autre largeur"):
        Visualisation("revisionspdf", CHRONOLOGIE, 8, 1, b"", lignes=(list(LIGNE),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="seulement pour un tableau"):
        Visualisation("ela", NatureVisualisation.CARTE_ELA, 1, 1, b"", lignes=(LIGNE,))


def test_tableau_relu_avec_d_autres_colonnes() -> None:
    document = Visualisation.tableau("revisionspdf", CHRONOLOGIE, [LIGNE]).vers_dict()
    document["colonnes"] = document["colonnes"][::-1]
    with pytest.raises(ValueError, match="colonnes"):
        Visualisation.depuis_dict(document)


def test_message_du_tableau_conforme() -> None:
    from voight_kampff import schemas

    messages = [
        ligne for ligne in lignes(maj(base(), {6: b"<<>>"})) if ligne["type"] == "visualisation"
    ]
    assert [m["visualisation"]["nature"] for m in messages] == [CHRONOLOGIE, OBJETS]
    for message in messages:
        schemas.valider("messages", message)


# Rapport : règles du catalogue, exports, résumé (ADR-0211, ADR-0212)


def _analyser(dossier: Path, nom: str, contenu: bytes) -> Analyse:
    chemin = dossier / nom
    chemin.write_bytes(contenu)
    return analyser(chemin)


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("revisions")
    echantillons = {
        nom: (ECHANTILLONS / nom).read_bytes()
        for nom in ("formulaire.pdf", "modifie.pdf", "signe_modifie.pdf", "signe_annote.pdf")
    }
    echantillons["seule.pdf"] = base()
    date = b"<</Producer(P)/ModDate(<script>alert(1)</script>)>>"
    echantillons["date.pdf"] = maj(base(), {5: date})
    echantillons["objet_illisible.pdf"] = abimer(maj(base(), {6: b"<<>>"}), 6)
    return {nom: _analyser(dossier, nom, contenu) for nom, contenu in echantillons.items()}


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "revisionspdf"}


@pytest.mark.exigence("F-60")
@pytest.mark.parametrize(
    ("nom", "attendues"),
    [
        ("seule.pdf", set()),
        ("formulaire.pdf", {"R-REVISIONSPDF-001"}),
        ("signe_annote.pdf", {"R-REVISIONSPDF-001"}),
        ("modifie.pdf", {"R-REVISIONSPDF-001", "R-REVISIONSPDF-002"}),
        ("signe_modifie.pdf", {"R-REVISIONSPDF-001", "R-REVISIONSPDF-002", "R-REVISIONSPDF-003"}),
    ],
)
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques}
    assert etats["revisionspdf"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues


def test_phrases_des_constats(analyses: dict[str, Analyse]) -> None:
    page = export.exporter_html(analyses["signe_modifie.pdf"])
    for attendu in (
        "Le PDF garde 6 versions successives",
        "1 version(s) ajoutée(s) après la première changent des objets",
        "Après la version 5, couverte par une signature, 1 version(s) changent des objets",
    ):
        assert attendu in page


@pytest.mark.exigence("F-84")
def test_html_chronologie(analyses: dict[str, Analyse]) -> None:
    page = export.exporter_html(analyses["signe_modifie.pdf"])
    debut = page.index('<section id="visualisations"')
    tableau_ = page.index("<table>", debut)
    for paragraphe in textes()["visualisations"]["chronologie_revisions"]["avertissement"]:
        assert debut < page.index(escape(paragraphe)) < tableau_
    for colonne in textes()["visualisations"]["chronologie_revisions"]["colonnes"].values():
        assert escape(colonne) in page[tableau_:]
    assert "<td>signature, formulaire, métadonnées</td>" in page
    assert "<td>métadonnées, non reconnue</td>" in page
    assert "<td>première version</td>" in page
    fin = ORACLE["signe_modifie.pdf"]["signatures"][0]["fin"]
    assert f"<td>{fin:,}</td>".replace(",", FINE) in page
    assert "<td>—</td>" in page


@pytest.mark.exigence("F-84", "ES-12")
def test_html_chronologie_echappee(analyses: dict[str, Analyse]) -> None:
    page = export.exporter_html(analyses["date.pdf"])
    assert "<script>alert(1)</script>" not in page
    assert escape("<script>alert(1)</script>") in page


@pytest.mark.exigence("F-84")
def test_html_chronologie_partielle(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["formulaire.pdf"]
    observations = tuple(
        dataclasses.replace(o, valeur=300) if o.nom == "revisionspdf.versions" else o
        for o in analyse.observations
    )
    page = export.exporter_html(dataclasses.replace(analyse, observations=observations))
    attendu = texte(
        "visualisations.chronologie_revisions.couverture_partielle", lignes="4", total="300"
    )
    assert escape(attendu) in page
    assert "Le tableau ne montre" not in export.exporter_html(analyse)


def test_chronologie_coupee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(revisionspdf, "LIGNES_MAX", 2)
    contenu = maj(maj(base(), {6: b"<<>>"}), {7: b"<<>>"})
    assert [ligne[0] for ligne in tableau(contenu)] == [1, 2]
    assert obs(contenu)["revisionspdf.versions"] == 3


@pytest.mark.exigence("F-84")
def test_json_chronologie_jamais_masquee(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["signe_modifie.pdf"]
    masque = json.loads(export.exporter_json(analyse))
    assert "contenu" in masque["masquage"]["masquees"]
    chronologie, objets_ = masque["visualisations"]
    assert chronologie["nature"] == "chronologie_revisions"
    assert len(chronologie["lignes"]) == 6
    assert objets_["nature"] == "objets_revisions"
    revele = json.loads(export.exporter_json(analyse, reveler=["contenu"]))
    assert revele["visualisations"] == masque["visualisations"]
    assert comparaison.comparer(masque, revele).identiques
    tout = json.loads(export.exporter_json(analyse, reveler=list(CategorieIdentifiante)))
    assert Rapport.depuis_dict(tout).visualisations == analyse.visualisations


def test_resume_annonce_la_chronologie(analyses: dict[str, Analyse]) -> None:
    lignes_ = Presentation(analyses["signe_modifie.pdf"], ()).resume()
    natures = "Chronologie des versions du PDF, Objets changés par les versions du PDF"
    attendu = accorder("resume.visualisations", 2, natures=natures)
    assert attendu in lignes_


@pytest.mark.exigence("F-90")
def test_controle_avant_publication_complet(analyses: dict[str, Analyse]) -> None:
    # Le module ne lit aucune métadonnée identifiante : son analyse non menée ne rend pas le
    # contrôle avant publication incomplet (ADR-0211).
    analyse = analyses["objet_illisible.pdf"]
    non_menees = {n.module for n in analyse.non_menees if n.raison.value != "hors_v1"}
    assert non_menees == {"revisionspdf"}
    assert texte("resume.publication_incomplete") not in Presentation(analyse, ()).publication()


# Objets changés, un par un (T51, ADR-0217)


@pytest.mark.exigence("F-61")
def test_objets_un_par_un() -> None:
    page = b"<</Type/Page/Parent 2 0 R/Contents[4 0 R 6 0 R]/Resources<</Font<</F 7 0 R>>>>>>"
    police = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"
    contenu = maj(base(), {3: page, 6: flux_pdf("", b"BT ET"), 7: police})
    assert objets(contenu) == [
        [2, 3, 0, "remplace", "Page", "non_reconnue", 1],
        [2, 6, 0, "ajoute", "flux", "non_reconnue", 1],
        [2, 7, 0, "ajoute", "Font/Type1", "non_reconnue", 1],
    ]
    assert obs(contenu)["revisionspdf.objets"] == 3


@pytest.mark.exigence("F-61")
def test_objet_supprime_et_page_de_la_version_precedente() -> None:
    contenu = maj(base(), {3: b"<</Type/Page/Parent 2 0 R>>"}, libres={4: 1})
    assert objets(contenu) == [
        [2, 3, 0, "remplace", "Page", "non_reconnue", 1],
        [2, 4, 0, "supprime", "flux", "non_reconnue", 1],
    ]


@pytest.mark.parametrize(
    ("corps", "genre"),
    [
        pytest.param(b"[1 2]", "tableau", id="tableau"),
        pytest.param(b"42", "valeur", id="valeur"),
        pytest.param(b"<</A 1>>", "dictionnaire", id="dictionnaire"),
        pytest.param(b"<</Subtype/Text>>", "Text", id="sous-type-seul"),
        pytest.param(b"null", "", id="nul"),
        pytest.param(b"<</Type/" + b"N" * 80 + b">>", "N" * 64, id="type-coupe"),
    ],
)
def test_type_d_un_objet(corps: bytes, genre: str) -> None:
    ((*_, type_, _, page),) = objets(maj(base(), {6: corps}))
    assert (type_, page) == (genre, 0)


def test_objet_non_lu() -> None:
    ((*_, type_, nature, _),) = objets(abimer(maj(base(), {6: b"<<>>"}), 6))
    assert (type_, nature) == ("", "non_lue")


def test_pages_des_objets_designes() -> None:
    # Deuxième page sous un nœud intermédiaire : ses annotations, ses ressources, ses polices et
    # ses objets externes ; une page vue deux fois n'est comptée qu'une fois.
    pages = b"<</Type/Pages/Kids[3 0 R 8 0 R 3 0 R]/Count 2>>"
    noeud = b"<</Type/Pages/Kids[9 0 R]/Count 1>>"
    seconde = b"<</Type/Page/Parent 8 0 R/Contents 10 0 R/Annots 11 0 R/Resources 12 0 R>>"
    premiere = base(
        {
            2: pages,
            8: noeud,
            9: seconde,
            10: CONTENU,
            11: b"[13 0 R]",
            12: b"<</Font 14 0 R/XObject<</X 15 0 R>>>>",
            13: b"<</Subtype/Text/Rect[0 0 1 1]>>",
            14: b"<</F 16 0 R>>",
            15: flux_pdf("/Subtype/Form", b""),
            16: b"<</Type/Font>>",
        }
    )
    changes = {
        10: flux_pdf("", b"BT ET"),
        11: b"[13 0 R 13 0 R]",
        12: b"<</Font 14 0 R/XObject<</X 15 0 R>>/A 1>>",
        13: b"<</Subtype/Text/Rect[0 0 2 2]>>",
        14: b"<</F 16 0 R/G 1>>",
        15: flux_pdf("/Subtype/Form/A 1", b""),
        16: b"<</Type/Font/A 1>>",
    }
    lignes_ = objets(maj(premiere, changes))
    assert {ligne[1]: ligne[6] for ligne in lignes_} == dict.fromkeys(range(10, 17), 2)


def test_page_directe_dans_l_arbre() -> None:
    # Une page écrite directement dans /Kids : ses objets sont désignés, elle-même ne l'est pas.
    pages = b"<</Type/Pages/Kids[<</Type/Page/Contents 4 0 R>>]/Count 1>>"
    ((*_, page),) = objets(maj(base({2: pages}), {4: flux_pdf("", b"BT ET")}))
    assert page == 1


def test_pages_des_objets_illisibles() -> None:
    # L'arbre des pages ne se lit plus : le relevé s'arrête, aucune page n'est désignée.
    pages = b"<</Type/Pages/Kids[3 0 R 8 0 R]/Count 2>>"
    premiere = abimer(base({2: pages, 8: b"<</Type/Page>>"}), 8)
    ((*_, page),) = objets(maj(premiere, {4: CONTENU + b" "}))
    assert page == 1  # le contenu de la première page, lue avant l'objet illisible
    contenu = maj(abimer(base({2: b"<</Type/Pages/Kids 8 0 R>>", 8: b"[3 0 R]"}), 8), {6: b"1"})
    ((*_, page),) = objets(contenu)
    assert page == 0


def test_objets_coupes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(revisionspdf, "OBJETS_MAX", 2)
    contenu = maj(maj(base(), {6: b"1", 7: b"2"}), {8: b"3"})
    assert [ligne[1] for ligne in objets(contenu)] == [6, 7]
    assert obs(contenu)["revisionspdf.objets"] == 3


@pytest.mark.exigence("F-61", "F-84")
def test_html_objets(analyses: dict[str, Analyse]) -> None:
    page = export.exporter_html(analyses["modifie.pdf"])
    debut = page.index(f"<h3>{escape(texte('visualisations.objets_revisions.titre'))}</h3>")
    tableau_ = page.index("<table>", debut)
    for paragraphe in textes()["visualisations"]["objets_revisions"]["avertissement"]:
        assert debut < page.index(escape(paragraphe)) < tableau_
    for colonne in textes()["visualisations"]["objets_revisions"]["colonnes"].values():
        assert escape(colonne) in page[tableau_:]
    corps = page[tableau_ : page.index("</table>", tableau_)]
    assert "<td>remplacé</td>" in corps
    assert "<td>ajouté</td>" in corps
    assert "<td>non reconnue</td>" in corps
    assert "<td>métadonnées</td>" in corps
    assert "<td>Font/Type1</td>" in corps
    assert "<td>—</td>" in corps  # objet qu'aucune page ne désigne


@pytest.mark.exigence("F-61", "F-84")
def test_html_objets_partiel(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["modifie.pdf"]
    observations = tuple(
        dataclasses.replace(o, valeur=900) if o.nom == "revisionspdf.objets" else o
        for o in analyse.observations
    )
    page = export.exporter_html(dataclasses.replace(analyse, observations=observations))
    attendu = texte("visualisations.objets_revisions.couverture_partielle", lignes="6", total="900")
    assert escape(attendu) in page
