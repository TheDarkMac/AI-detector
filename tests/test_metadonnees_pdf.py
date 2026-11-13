"""Métadonnées d'un PDF : modules ``infopdf`` et ``xmp``, lecteur de structure (T21).

Décisions : ADR-0124 (lecteur), ADR-0125 (lecture stricte), ADR-0126 (chiffrement), ADR-0127.

Les échantillons sont construits par ``metadonnees.pdf`` : tables classiques et flux de
références croisées, flux d'objets, mises à jour incrémentales, chiffrement déclaré.
"""

import tempfile
import zlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from metadonnees import (
    CATALOGUE_PDF,
    PAGES_PDF,
    contexte,
    flux_pdf,
    identifiantes,
    lignes_png,
    observations,
    pdf,
    pdf_info,
    raisons,
    resultats,
    valeurs_de,
    xmp,
)

from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte, LimiteDepassee
from voight_kampff.modules._lecture import pdf as lecteur
from voight_kampff.rapport.modele import Plage, RaisonNonMenee

pytestmark = pytest.mark.exigence("F-10")

PARTIEL = RaisonNonMenee.FORMAT_PARTIEL.value
TRONQUE = RaisonNonMenee.FICHIER_TRONQUE.value
PAQUET = xmp("<dc:format>application/pdf</dc:format>")
DONNEES = Path(__file__).parent / "donnees" / "metadonnees"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def info(contenu: bytes) -> dict[str, Any]:
    return valeurs_de(resultats("infopdf", contenu, "pdf"))


@pytest.fixture(autouse=True)
def fichiers() -> Iterator[None]:
    """Ferme, à la fin du test, les fichiers temporaires que lisent ses documents."""
    yield
    while _OUVERTS:
        _OUVERTS.pop().close()


_OUVERTS: list[Any] = []


def ouvert(contenu: bytes) -> Contexte:
    """Contexte du module ``infopdf`` sur ``contenu``, ouvert jusqu'à la fin du test."""
    fichier = tempfile.TemporaryFile()  # noqa: SIM115 — fermé par la fixture « fichiers »
    _OUVERTS.append(fichier)
    return contexte(fichier, contenu, "pdf", "infopdf")


def document(contenu: bytes) -> lecteur.Document:
    return lecteur.Document(ouvert(contenu))


# Dictionnaire Info


def test_infopdf_entrees_et_formes_de_valeur() -> None:
    entrees = (
        b"/Title(Rapport \\(final\\)\\n\\101\\\r\nsuite (imbriqu\\351e))"
        b"/Author<FEFF00C900740069>"
        b"/Subject<EFBBBF C3A9 74 65>"
        b"/Keywords(\x80 \x9f \x18 \xa0)"
        b"/Creator 5 0 R"
        b"/Producer(ligne\rsuivante\r\nfin)"
        b"/Trapped/False"
        b"/Pages 12/Echelle -.5/Ouvert true/Vide null"
        b"/Liste[(a)/b 1 5 0 R]"
        b"/Cle#20propre#C3#A9(x)/Latin#E9(y)"
        b"/Sous<</Logiciel(Outil)>>"
        b"/Vignette 6 0 R"
        b"/Hexa<6 1 6>"
    )
    contenu = pdf(
        {
            1: CATALOGUE_PDF,
            2: PAGES_PDF,
            3: b"<<" + entrees + b">>",
            5: b"(Indirect)",
            6: flux_pdf("", b"abcdef"),
        },
        "/Root 1 0 R/Info 3 0 R",
    )
    lignes = resultats("infopdf", contenu, "pdf")
    assert valeurs_de(lignes) == {
        "infopdf.present": True,
        "infopdf.chiffre": False,
        "infopdf.Title": "Rapport (final)\nAsuite (imbriquée)",
        "infopdf.Author": "Éti",
        "infopdf.Subject": "éte",
        "infopdf.Keywords": "• � ˘ €",
        "infopdf.Creator": "Indirect",
        "infopdf.Producer": "ligne\nsuivante\nfin",
        "infopdf.Trapped": "False",
        "infopdf.Pages": 12,
        "infopdf.Echelle": -0.5,
        "infopdf.Ouvert": True,
        "infopdf.Liste": ["a", "b", 1, "Indirect"],
        "infopdf.Cle-propre-": "x",
        "infopdf.Latin-": "y",
        "infopdf.Sous.Logiciel": "Outil",
        "infopdf.Vignette.taille": 6,
        "infopdf.Hexa": "a`",
    }
    assert identifiantes(lignes) == {"infopdf.Author": "metadonnee_nominative"}
    assert raisons(lignes) == []
    [titre] = [o for o in observations(lignes) if o["nom"] == "infopdf.Title"]
    debut = contenu.index(b"3 0 obj")
    assert titre["localisation"]["chemin"] == "dictionnaire Info (objet 3 0)"
    assert titre["localisation"]["octets"]["debut"] == debut


def test_infopdf_absent_ou_libre() -> None:
    assert info(pdf({1: CATALOGUE_PDF, 2: PAGES_PDF})) == {
        "infopdf.present": False,
        "infopdf.chiffre": False,
    }
    # Info désigne un objet absent de la table : objet nul, donc pas de dictionnaire.
    assert info(pdf({1: CATALOGUE_PDF}, "/Root 1 0 R/Info 9 0 R"))["infopdf.present"] is False


def test_infopdf_dans_le_trailer() -> None:
    lignes = resultats("infopdf", pdf({1: CATALOGUE_PDF}, "/Root 1 0 R/Info<</Title(T)>>"), "pdf")
    assert valeurs_de(lignes)["infopdf.Title"] == "T"
    [titre] = [o for o in observations(lignes) if o["nom"] == "infopdf.Title"]
    assert titre["localisation"] == {"chemin": "dictionnaire Info (dans le trailer)"}


@pytest.mark.parametrize(
    "objets",
    [
        {3: b"(pas un dictionnaire)"},
        {3: b"<</Liste[[1]]>>"},
        {3: b"<</Liste[null]>>"},
        {3: b"<</Soi 3 0 R>>"},
        {3: b"<</Titre 5 0 R/Autre(gardee)>>", 5: b"5 0 R"},
    ],
)
def test_infopdf_entrees_non_lues(objets: dict[int, bytes]) -> None:
    lignes = resultats(
        "infopdf", pdf({1: CATALOGUE_PDF, **objets}, "/Root 1 0 R/Info 3 0 R"), "pdf"
    )
    assert PARTIEL in raisons(lignes)
    assert valeurs_de(lignes)["infopdf.present"] is True
    if 5 in objets:
        assert valeurs_de(lignes)["infopdf.Autre"] == "gardee"


def test_infopdf_info_illisible() -> None:
    lignes = resultats(
        "infopdf", pdf({1: CATALOGUE_PDF, 3: b"<</A"}, "/Root 1 0 R/Info 3 0 R"), "pdf"
    )
    assert valeurs_de(lignes)["infopdf.present"] is True
    assert raisons(lignes) == [PARTIEL]


def test_infopdf_chiffre() -> None:
    contenu = pdf_info(b"<</Title(\x8a\x01)>>", trailer="/Root 1 0 R/Info 3 0 R/Encrypt<</V 1>>")
    lignes = resultats("infopdf", contenu, "pdf")
    assert valeurs_de(lignes) == {"infopdf.present": True, "infopdf.chiffre": True}
    assert raisons(lignes) == [PARTIEL]
    sans = resultats("infopdf", pdf({1: CATALOGUE_PDF}, "/Root 1 0 R/Encrypt<<>>"), "pdf")
    assert valeurs_de(sans) == {"infopdf.present": False, "infopdf.chiffre": True}
    assert raisons(sans) == []


def test_pdf_chiffre_par_ghostscript() -> None:
    contenu = (DONNEES / "chiffre.pdf").read_bytes()
    lignes = resultats("infopdf", contenu, "pdf")
    assert valeurs_de(lignes) == {"infopdf.present": True, "infopdf.chiffre": True}
    assert raisons(lignes) == [PARTIEL]
    lignes = resultats("xmp", contenu, "pdf")
    assert valeurs_de(lignes) == {"xmp.present": True, "xmp.blocs": 1}
    [non_menee] = [ligne["non_menee"] for ligne in lignes if ligne["type"] == "non_menee"]
    assert non_menee["localisation"]["chemin"] == "flux Metadata du catalogue (document chiffré)"


def test_infopdf_structure_illisible() -> None:
    lignes = resultats("infopdf", b"%PDF-1.7\n1 0 obj<<>>endobj\n%%EOF\n", "pdf")
    assert valeurs_de(lignes) == {"infopdf.present": False}
    [non_menee] = [ligne["non_menee"] for ligne in lignes if ligne["type"] == "non_menee"]
    assert non_menee["localisation"]["chemin"] == "startxref"


def test_infopdf_valeur_longue() -> None:
    titre = b"x" * 10000  # plus grand que la première fenêtre de lecture
    assert info(pdf_info(b"<</Title(" + titre + b")>>"))["infopdf.Title.longueur"] == 10000


# XMP du catalogue


def test_xmp_pdf() -> None:
    lignes = resultats("xmp", pdf_info(b"<<>>", xmp_=PAQUET), "pdf")
    assert valeurs_de(lignes) == {
        "xmp.present": True,
        "xmp.blocs": 1,
        "xmp.x:xmptk": "Outil 1.0",
        "xmp.dc:format": "application/pdf",
    }
    assert observations(lignes)[-1]["localisation"]["chemin"] == (
        "flux Metadata du catalogue (objet 4 0)"
    )
    assert valeurs_de(resultats("xmp", pdf_info(b"<<>>"), "pdf")) == {"xmp.present": False}


def test_xmp_pdf_compresse_et_flux_d_objets() -> None:
    objets = {
        1: b"<</Type/Catalog/Metadata 4 0 R>>",
        4: flux_pdf("/Filter/FlateDecode", zlib.compress(PAQUET)),
    }
    contenu = pdf(objets, flux_xref=True, flux_objets={7: (1,)})
    assert valeurs_de(resultats("xmp", contenu, "pdf"))["xmp.dc:format"] == "application/pdf"


@pytest.mark.parametrize(
    ("catalogue", "chiffrement", "lu"),
    [
        (b"<</Metadata 4 0 R>>", "/Encrypt<</EncryptMetadata false>>", True),
        (b"<</Metadata 4 0 R>>", "/Encrypt 9 0 R", False),
        (b"<</Metadata 4 0 R>>", "/Encrypt<</EncryptMetadata true>>", False),
        (b"<</Metadata<</Type/Metadata>>>>", "", False),
    ],
)
def test_xmp_pdf_chiffre_ou_mal_forme(catalogue: bytes, chiffrement: str, lu: bool) -> None:
    objets = {1: catalogue, 4: flux_pdf("/Type/Metadata", PAQUET), 9: b"<</V 2>>"}
    lignes = resultats("xmp", pdf(objets, "/Root 1 0 R" + chiffrement), "pdf")
    assert valeurs_de(lignes)["xmp.present"] is True
    assert ("xmp.dc:format" in valeurs_de(lignes)) is lu
    assert raisons(lignes) == ([] if lu else [PARTIEL])


def test_xmp_pdf_structure_illisible() -> None:
    lignes = resultats("xmp", b"%PDF-1.7\nstartxref\n999\n%%EOF\n", "pdf")
    assert valeurs_de(lignes) == {"xmp.present": False}
    assert raisons(lignes) == [PARTIEL]


def test_xmp_pdf_catalogue_absent_ou_invalide() -> None:
    assert valeurs_de(resultats("xmp", pdf({1: b"(x)"}), "pdf")) == {"xmp.present": False}
    assert valeurs_de(resultats("xmp", pdf({}, ""), "pdf")) == {"xmp.present": False}


# Références croisées


@pytest.mark.parametrize("largeur", [19, 20, 21])
def test_table_classique_largeurs(largeur: int) -> None:
    assert info(pdf_info(b"<</Title(T)>>", largeur=largeur))["infopdf.Title"] == "T"


@pytest.mark.parametrize(
    ("predicteur", "png"),
    [
        ("", False),
        ("<</Predictor 12/Columns 7>>", True),
        ("<</Predictor 15/Columns 7/Colors 1/BitsPerComponent 8>>", True),
        ("[<</Predictor 1>>]", False),
        ("<<>>", False),
    ],
)
def test_flux_de_references_croisees(predicteur: str, png: bool) -> None:
    contenu = pdf_info(b"<</Title(T)>>", flux_xref=True, predicteur=predicteur, png=png)
    assert info(contenu)["infopdf.Title"] == "T"


@pytest.mark.parametrize("filtres", [(0,), (1,), (3,), (4,), (0, 1, 2, 3, 4)])
def test_predicteur_png_chaque_filtre(filtres: tuple[int, ...]) -> None:
    donnees = bytes((i * 37 + i // 7) & 0xFF for i in range(70))
    assert lecteur._png(lignes_png(donnees, 7, filtres), 7, 1, 0) == donnees
    # Plusieurs octets par pixel : la gauche est à ``pas`` octets ; ligne incomplète écartée.
    codees = lignes_png(donnees, 7, filtres, pas=3) + b"\x00"
    assert lecteur._png(codees, 7, 3, 0) == donnees


def test_predicteur_tiff() -> None:
    donnees = bytes(range(14))
    codees = bytearray(donnees)
    for debut in (0, 7):
        for i in range(debut + 6, debut, -1):
            codees[i] = (codees[i] - codees[i - 1]) & 0xFF
    assert lecteur._tiff(bytes(codees), 7, 1) == donnees
    flux = lecteur._predire(bytes(codees), {"Predictor": 2, "Columns": 7}, 0)
    assert flux == donnees


@pytest.mark.parametrize(
    "parametres",
    [
        {"Predictor": 2, "Columns": 7, "BitsPerComponent": 4},
        {"Predictor": 9},
        {"Predictor": 12, "Columns": 0},
        {"Predictor": 12, "Colors": 64},
        {"Predictor": 12, "BitsPerComponent": 3},
        {"Predictor": 12, "Columns": lecteur.Nom("x")},
    ],
)
def test_predicteur_refuse(parametres: dict[str, lecteur.Objet]) -> None:
    with pytest.raises(lecteur.Illisible):
        lecteur._predire(b"\x00\x01\x02", parametres, 0)
    with pytest.raises(lecteur.Illisible):
        lecteur._png(b"\x05abc", 3, 1, 0)  # type de filtre inconnu


def test_flux_d_objets() -> None:
    contenu = pdf_info(b"<</Title(T)>>", flux_xref=True, flux_objets={9: (3, 1)})
    assert info(contenu)["infopdf.Title"] == "T"


def test_mise_a_jour_incrementale() -> None:
    base = pdf_info(b"<</Title(Ancien)/Author(A)>>")
    mise_a_jour = pdf({3: b"<</Title(Nouveau)>>"}, "", base=base)  # trailer sans Root ni Info
    assert info(mise_a_jour) == {
        "infopdf.present": True,
        "infopdf.chiffre": False,
        "infopdf.Title": "Nouveau",
    }
    assert document(mise_a_jour).sections == 2
    en_flux = pdf({3: b"<</Title(Flux)>>"}, "/Root 1 0 R/Info 3 0 R", base=base, flux_xref=True)
    assert info(en_flux)["infopdf.Title"] == "Flux"


def test_table_hybride() -> None:
    # Section classique et flux complémentaire (/XRefStm), qui connaît l'objet 3.
    tete = b"%PDF-1.7\n"
    objet_1 = b"1 0 obj\n" + CATALOGUE_PDF + b"\nendobj\n"
    objet_3 = b"3 0 obj\n<</Title(Hybride)>>\nendobj\n"
    position_3 = len(tete) + len(objet_1)
    lignes = bytes([1]) + position_3.to_bytes(4, "big") + b"\x00\x00"
    position_flux = position_3 + len(objet_3)
    flux = b"4 0 obj\n" + flux_pdf("/Type/XRef/Size 5/W[1 4 2]/Index[3 1]", lignes) + b"\nendobj\n"
    table = len(tete)
    corps = tete + objet_1 + objet_3 + flux
    xref = (
        b"xref\n0 2\n0000000000 65535 f\r\n"
        + f"{table:010d} 00000 n\r\n".encode()
        + f"trailer\n<</Size 5/Root 1 0 R/Info 3 0 R/XRefStm {position_flux}>>\n".encode()
    )
    contenu = corps + xref + f"startxref\n{len(corps)}\n%%EOF\n".encode()
    assert info(contenu)["infopdf.Title"] == "Hybride"


def test_generation_et_entree_libre() -> None:
    contenu = pdf_info(b"<</Title(T)>>", trailer="/Root 1 0 R/Info 3 1 R")
    assert info(contenu)["infopdf.present"] is False  # autre génération : objet nul
    entrees = lecteur._entree_flux(lecteur._FluxXref(((0, 1, 0),), (0, 1, 1), b"\x05\x00"), 0)
    assert entrees == (1, 5, 0)  # type absent : 1
    d = document(pdf_info(b"<<>>", flux_xref=True, flux_objets={9: (3,)}))
    d._sections[0] = lecteur._FluxXref(((3, 1, 0),), (1, 4, 2), b"\x07" + bytes(6))
    assert d.objet(lecteur.Ref(3, 0)) is None  # type inconnu
    d._sections[0] = lecteur._FluxXref(((3, 1, 0),), (1, 4, 2), b"\x02" + bytes(6))
    assert d.objet(lecteur.Ref(3, 1)) is None  # dans un flux d'objets, génération non nulle


def section(texte: bytes) -> bytes:
    """PDF dont ``startxref`` désigne ``texte``, juste après l'en-tête."""
    return b"%PDF-1.7\n" + texte + b"\nstartxref\n9\n%%EOF"


def section_en_flux(dico: bytes) -> bytes:
    return section(b"1 0 obj<<" + dico + b"/Length 0>>stream\n\nendstream")


ENTREE_LIBRE = b"0000000000 65535 f\r\n"


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (b"%PDF-1.7\n", PARTIEL),  # pas de startxref
        (b"%PDF-1.7\nstartxref\n", PARTIEL),
        (b"%PDF-1.7\nstartxref\n(x)\n%%EOF", PARTIEL),
        (b"%PDF-1.7\nstartxref\n99999\n%%EOF", PARTIEL),
        (section(b"xref\n0 1\nxxxxxxxxxx 00000 n\r\ntrailer<<>>"), PARTIEL),
        (section(b"xref\n0 1\n0000000000 65535 f\ntrailer(x)"), PARTIEL),
        (section(b"xref\n(a) 1\ntrailer<<>>"), PARTIEL),
        (section(b"xref\n0 1\n0000000000 65535 fx"), PARTIEL),  # entrée sans fin de ligne
        (section(b"xref\n0 900\n" + ENTREE_LIBRE), TRONQUE),
        (section(b"xref\n0 1\n" + ENTREE_LIBRE + b"trailer<</Prev 9>>"), PARTIEL),  # boucle
        (section(b"1 0 obj<</Type/Pages>>endobj"), PARTIEL),
        (section_en_flux(b"/Type/XRef/W[1 2]"), PARTIEL),
        (section_en_flux(b"/Type/XRef/Size 5/W[1 2 2]"), PARTIEL),  # données trop courtes
        (section_en_flux(b"/Type/XRef/Index[0]/W[1 2 2]"), PARTIEL),
        (section_en_flux(b"/Type/XRef/Size 1"), PARTIEL),  # sans /W
    ],
)
def test_table_illisible(contenu: bytes, raison: str) -> None:
    lignes = resultats("infopdf", contenu, "pdf")
    assert raisons(lignes) == [raison]


def test_table_tronquee_par_un_objet() -> None:
    # startxref désigne un objet qui court jusqu'à la fin de la partie.
    contenu = b"%PDF-1.7\n1 0 obj<</A(" + b"x" * 5000 + b"startxref\n9\n%%EOF"
    assert raisons(resultats("infopdf", contenu, "pdf")) == [TRONQUE]


@pytest.mark.parametrize(
    "objet",
    [
        b"9 0 obj<<>>",  # numéro différent de celui de la table
        b"3 0 objet<<>>",
        b"3 (0) obj<<>>",
        b"3 0 obj<</Length 5>>stream\nabcdeXYZendstream",  # longueur fausse
        b"3 0 obj<</Length -1>>stream\nabc\nendstream",
        b"3 0 obj<</Length 9 0 R>>stream\nabc\nendstream",  # longueur indirecte absente
        b"3 0 obj<</F(autre.bin)/Length 3>>stream\nabc\nendstream",
        b"3 0 obj<</A>>",
        b"3 0 obj<<(cle)1>>",
        b"3 0 obj<</A)>>",
        b"3 0 obj<</A{1}>>",
        b"3 0 obj<</A<zz>>>",
        b"3 0 obj<</A>z>>",
        b"3 0 obj<</A 1.2.3>>",
    ],
)
def test_objet_illisible(objet: bytes) -> None:
    lignes = resultats("infopdf", objet_seul(objet), "pdf")
    assert raisons(lignes) == [PARTIEL]


def objet_seul(objet: bytes, position: int = 9) -> bytes:
    """PDF dont la table ne connaît que l'objet 3, à ``position`` ; le trailer le désigne."""
    corps = b"%PDF-1.7\n" + objet + b"\nendobj\n"
    return (
        corps
        + f"xref\n3 1\n{position:010d} 00000 n\r\n".encode()
        + b"trailer<</Info 3 0 R>>\nstartxref\n"
        + str(len(corps)).encode()
        + b"\n%%EOF\n"
    )


def test_objet_hors_de_la_partie() -> None:
    contenu = objet_seul(b"3 0 obj<<>>", position=99999999)
    assert raisons(resultats("infopdf", contenu, "pdf")) == [PARTIEL]


def test_flux_tronque_et_longueur_indirecte() -> None:
    objets = {1: CATALOGUE_PDF, 3: b"<</Length 5 0 R>>stream\nabc\nendstream", 5: b"3"}
    d = document(pdf(objets))
    flux = d.objet(lecteur.Ref(3, 0))
    assert isinstance(flux, lecteur.Flux)
    assert flux.longueur == 3
    assert d.decoder(flux) == b"abc"
    corps = b"%PDF-1.7\n3 0 obj<</Length 99999>>stream\nabc"
    contenu = corps + b"\nxref\n3 1\n0000000009 00000 n\r\ntrailer<</Info 3 0 R>>\nstartxref\n"
    contenu += str(len(corps) + 1).encode() + b"\n%%EOF\n"
    assert raisons(resultats("infopdf", contenu, "pdf")) == [TRONQUE]


@pytest.mark.parametrize(
    "dico",
    [
        "/Filter/LZWDecode",
        "/Filter/FlateDecode",  # données non compressées
        "/Filter[/FlateDecode]/DecodeParms[<<>><<>>]",
    ],
)
def test_flux_non_decode(dico: str) -> None:
    d = document(pdf({1: CATALOGUE_PDF, 3: flux_pdf(dico, b"abc")}))
    flux = d.objet(lecteur.Ref(3, 0))
    assert isinstance(flux, lecteur.Flux)
    with pytest.raises(lecteur.Illisible):
        d.decoder(flux)


def test_flux_trop_grand_pour_une_lecture(monkeypatch: pytest.MonkeyPatch) -> None:
    d = document(pdf({1: CATALOGUE_PDF, 3: flux_pdf("", b"abcdef")}))
    flux = d.objet(lecteur.Ref(3, 0))
    assert isinstance(flux, lecteur.Flux)
    monkeypatch.setattr(lecteur, "TAILLE_MAX_LECTURE", 4)
    with pytest.raises(lecteur.Illisible):
        d.decoder(flux)


def test_objet_trop_grand_pour_une_lecture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lecteur, "TAILLE_MAX_LECTURE", 8192)
    contenu = pdf_info(b"<</Title(" + b"x" * 20000 + b")>>")
    lignes = resultats("infopdf", contenu, "pdf")
    assert raisons(lignes) == [PARTIEL]


def dans_un_flux(dico: str, corps: bytes) -> lecteur.Document:
    """Document dont l'objet 3 est au rang 0 du flux d'objets 9, de dictionnaire ``dico``."""
    d = document(pdf({1: CATALOGUE_PDF, 9: flux_pdf(dico, corps)}, flux_xref=True))
    entree = b"\x02\x00\x00\x00\x09\x00\x00"
    d._sections.insert(0, lecteur._FluxXref(((3, 1, 0),), (1, 4, 2), entree))
    return d


def test_flux_d_objets_non_compresse() -> None:
    assert dans_un_flux("/Type/ObjStm/N 1/First 4", b"3 0 <<>>").objet(lecteur.Ref(3, 0)) == {}


@pytest.mark.parametrize(
    ("dico", "corps"),
    [
        ("/Type/XRef/N 1/First 4", b"3 0 <<>>"),
        ("/Type/ObjStm/N(1)/First 4", b"3 0 <<>>"),
        ("/Type/ObjStm/N 1/First 6", b"(a) 0 <<>>"),
        ("/Type/ObjStm/N 2/First 4", b"3 0 <<>>"),
        ("/Type/ObjStm/N 1/First 4", b"8 0 <<>>"),
        ("/Type/ObjStm/N 1/First 4", b"3 0 <</A"),
        ("/Type/ObjStm/N 1/First 4", b"3 0 <</A)>>"),
    ],
)
def test_flux_d_objets_illisible(dico: str, corps: bytes) -> None:
    with pytest.raises(lecteur.Illisible):
        dans_un_flux(dico, corps).objet(lecteur.Ref(3, 0))


def test_references_circulaires_et_imbrication() -> None:
    d = document(pdf({1: CATALOGUE_PDF, 3: b"5 0 R", 5: b"3 0 R"}))
    assert d.objet(lecteur.Ref(3, 0)) == lecteur.Ref(5, 0)
    with pytest.raises(lecteur.Illisible):
        d.resoudre(lecteur.Ref(3, 0))
    d = document(pdf({1: CATALOGUE_PDF, 3: b"<</Length 3 0 R>>stream\nabc\nendstream"}))
    with pytest.raises(lecteur.Illisible):
        d.objet(lecteur.Ref(3, 0))  # sa longueur est lui-même
    profond = b"<</A" + b"[" * 100 + b"]" * 100 + b">>"
    with pytest.raises(LimiteDepassee):
        resultats("infopdf", pdf_info(profond), "pdf")


# Analyse lexicale


@pytest.mark.parametrize(
    ("ecrit", "lu"),
    [
        (b"% commentaire\n 42 ", 42),
        (b"+17 ", 17),
        (b"-3.25 ", -3.25),
        (b"4. ", 4.0),
        (b"/A#42#4 ", "AB#4"),
        (b"/#zz ", "#zz"),
        (b"<41 4 > ", b"A@"),
        (b"(a\\qb) ", b"aqb"),
        (b"(\\7778) ", b"\xff8"),
        (b"(a\\\nb) ", b"ab"),
        (b"[1 2 R] ", [lecteur.Ref(1, 2)]),
        (b"[1 (R)] ", [1, b"R"]),
        (b"[1 2 (R)] ", [1, 2, b"R"]),
    ],
)
def test_jetons(ecrit: bytes, lu: object) -> None:
    assert analyseur_de(ecrit).objet() == lu


def test_reference_negative_refusee() -> None:
    with pytest.raises(lecteur.Illisible):
        analyseur_de(b"[-1 0 R] ").objet()  # « R » sans référence devant


def analyseur_de(donnees: bytes, *, complet: bool = True) -> Any:
    return lecteur._Analyseur(ouvert(donnees + b" " * 8), donnees, 0, complet=complet)


@pytest.mark.parametrize(
    "ecrit",
    [b"", b"(abc", b"(a\\", b"<41", b">", b"/Nom", b"12", b"[1 2", b"<<", b"5 0"],
)
def test_jetons_coupes(ecrit: bytes) -> None:
    with pytest.raises(lecteur._Fin):
        analyseur_de(ecrit, complet=False).objet()


def test_mot_et_nombre_en_fin_de_donnees_completes() -> None:
    assert analyseur_de(b"12", complet=True).objet() == 12
    assert analyseur_de(b"5 0", complet=True).objet() == 5
    assert analyseur_de(b"/Nom", complet=True).objet() == "Nom"
    assert lecteur._nombre(b"+-1") == lecteur._Mot(b"+-1")
    assert lecteur._nombre(b".") == lecteur._Mot(b".")
    assert lecteur._nombre(b"1e5") == lecteur._Mot(b"1e5")


def test_objet_sans_endobj_en_fin_de_partie() -> None:
    corps = b"%PDF-1.7\n3 0 obj<</Title(fin)>>"
    contenu = corps + b"\nxref\n3 1\n0000000009 00000 n\r\ntrailer<</Info 3 0 R>>\nstartxref\n"
    contenu += str(len(corps) + 1).encode() + b"\n%%EOF\n"
    assert info(contenu)["infopdf.Title"] == "fin"
    # Dictionnaire en fin de partie, sans endobj : l'objet est le dictionnaire.
    c = ouvert(b"%PDF-1.7\n3 0 obj<</A 1>>")
    analyseur = lecteur._Analyseur(c, b"3 0 obj<</A 1>>", 9)
    assert analyseur.indirect(None)[1] == {"A": 1}
    # Fenêtre coupée juste après le dictionnaire : une lecture plus large est demandée.
    coupe = lecteur._Analyseur(c, b"3 0 obj<</A 1>>", 0)
    with pytest.raises(lecteur._Fin):
        coupe.indirect(None)


def test_fin_de_ligne_apres_stream() -> None:
    for fin in (b"\r\n", b"\r", b"\n"):
        corps = b"<</Length 3>>stream" + fin + b"abc\nendstream"
        d = document(pdf({1: CATALOGUE_PDF, 3: corps}))
        flux = d.objet(lecteur.Ref(3, 0))
        assert isinstance(flux, lecteur.Flux)
        assert d.decoder(flux) == b"abc"


def test_texte() -> None:
    assert lecteur.texte(b"\xfe\xff\x00A\xd8") == "A�"
    assert lecteur.texte(b"\xef\xbb\xbf\xc3") == "�"
    assert lecteur.texte(b"\x01\x09\x7f\xad\xe9") == "�\t��é"
    assert lecteur.entier(True) is None


def test_localisation_d_un_arret() -> None:
    illisible = lecteur.Illisible(RaisonNonMenee.FORMAT_PARTIEL, 500, "x")
    assert illisible.localisation(100).octets == Plage(99, 1)
    assert illisible.localisation(0).octets == Plage(0, 1)


def test_entree_mal_formee_au_milieu_d_une_sous_section() -> None:
    contenu = pdf_info(b"<</Title(T)>>").replace(b" 00000 n\r\n", b" 0000x n\r\n", 3)
    assert raisons(resultats("infopdf", contenu, "pdf")) == [PARTIEL]


def test_deux_objets_du_meme_flux_d_objets() -> None:
    d = document(pdf_info(b"<</Title(T)>>", flux_xref=True, flux_objets={9: (1, 3)}))
    assert d.resoudre(lecteur.Ref(1, 0)) == {"Type": "Catalog", "Pages": lecteur.Ref(2, 0)}
    assert d.resoudre(lecteur.Ref(3, 0)) == {"Title": b"T"}


def test_mot_stream_en_fin_de_fenetre() -> None:
    with pytest.raises(lecteur._Fin):
        analyseur_de(b"3 0 obj<</Length 1>>stream\n", complet=False).indirect(None)
    # Données suivies de plus de 64 blancs avant endstream : la fin du flux n'est pas lue.
    corps = b"<</Length 1>>stream\nx" + b" " * 70 + b"endstream"
    d = document(pdf({1: CATALOGUE_PDF, 3: corps}))
    with pytest.raises(lecteur.Illisible):
        d.objet(lecteur.Ref(3, 0))
