"""Pages d'un PDF : flux de contenu, module ``pagespdf``, règles du catalogue (T51, ADR-0213 à
ADR-0216, ADR-0218).

Les documents synthétiques sont construits ici, page par page ; les échantillons de
``tests/donnees/pages`` viennent de LibreOffice et de Ghostscript, retouchés par pypdf, et
``oracle.json`` consigne ce qu'en disent ``pdffonts`` et ``pdftotext -bbox`` de Poppler
(``generer_pages.py``). Les largeurs des 14 polices standard viennent des fichiers AFM d'Adobe
(``generer_polices14.py``).
"""

import contextlib
import json
import tempfile
import zlib
from collections.abc import Iterator
from html import escape
from pathlib import Path
from typing import Any

import pytest
from metadonnees import CATALOGUE_PDF, contexte, flux_pdf, pdf, raisons, resultats, valeurs_de

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail import garde
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import pagespdf
from voight_kampff.modules._lecture import pdf as lecteur
from voight_kampff.modules.pagespdf import _polices14
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import Presentation, texte
from voight_kampff.rapport.modele import EtatTechnique

pytestmark = pytest.mark.exigence("F-61")

ECHANTILLONS = Path(__file__).parent / "donnees" / "pages"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
PARTIEL = "format_partiel"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


# Construction des documents

HELV = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"
"""Helvetica standard, sans largeurs : celles de l'AFM d'Adobe, encodage StandardEncoding."""
LARGEURS = b"[" + b"500 " * 91 + b"]"
SIMPLE = b"<</Type/Font/Subtype/TrueType/BaseFont/ABCDEF+Arial/FirstChar 32/LastChar 122"
SIMPLE += b"/Widths " + LARGEURS + b"/FontDescriptor 9 0 R>>"
"""Sous-ensemble TrueType, codes 32 à 122 de 500 millièmes, montée 0,9 et descente -0,2."""
DESCRIPTEUR = b"<</Type/FontDescriptor/Ascent 900/Descent -200/FontFile2 10 0 R>>"


def document(
    contenu: bytes,
    *,
    polices: bytes = b"/H 5 0 R/S 6 0 R",
    ressources: bytes = b"",
    page: bytes = b"",
    objets: dict[int, bytes] | None = None,
    trailer: str = "/Root 1 0 R",
) -> bytes:
    """Une page (3) et son contenu (4) ; Helvetica (5) et le sous-ensemble ``SIMPLE`` (6, son
    descripteur 9 et son programme 10) dans ses ressources ; ``objets`` en plus ou à la place."""
    tous = {
        1: CATALOGUE_PDF,
        2: b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        3: b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Resources<</Font<<"
        + polices
        + b">>"
        + ressources
        + b">>"
        + page
        + b">>",
        4: flux_pdf("", contenu),
        5: HELV,
        6: SIMPLE,
        9: DESCRIPTEUR,
        10: flux_pdf("", b"programme"),
    } | (objets or {})
    return pdf(tous, trailer)


def lignes(contenu: bytes) -> list[dict[str, Any]]:
    return resultats("pagespdf", contenu, "pdf")


def obs(contenu: bytes) -> dict[str, Any]:
    return valeurs_de(lignes(contenu))


@pytest.fixture
def ouvrir() -> Iterator[Any]:
    """Interprète la première page d'un document et rend ce qui y a été relevé."""
    with contextlib.ExitStack() as pile:

        def relever(contenu: bytes) -> Any:
            fichier = pile.enter_context(tempfile.TemporaryFile())
            c = contexte(fichier, contenu, "pdf", "pagespdf")
            doc = lecteur.Document(c)
            (page, ressources), *_ = pagespdf._pages(c, doc)[0]
            return pagespdf._Interprete(c, doc).page(1, page, ressources)

        yield relever


def boites(relevee: Any) -> list[tuple[float, ...]]:
    return [tuple(round(v, 3) for v in t.boite) for t in relevee.textes]


# Flux de contenu (lecteur, §7.8.2)


def operations(donnees: bytes) -> list[tuple[str, list[Any]]]:
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, b"%PDF", "pdf", "pagespdf")
        return list(lecteur.operations(c, donnees))


def test_operations() -> None:
    assert operations(b"q 1 0 0 1 72 720 cm /F1 12 Tf [(a) -20 (b)] TJ (x) ' 1 2 (y) \" Q") == [
        ("q", []),
        ("cm", [1, 0, 0, 1, 72, 720]),
        ("Tf", [lecteur.Nom("F1"), 12]),
        ("TJ", [[b"a", -20, b"b"]]),
        ("'", [b"x"]),
        ('"', [1, 2, b"y"]),
        ("Q", []),
    ]
    assert operations(b"") == operations(b"  % commentaire\n") == []
    assert operations(b"<</A 1>> BDC true false null EMC") == [
        ("BDC", [{"A": 1}]),
        ("EMC", [True, False, None]),
    ]


def test_image_en_ligne() -> None:
    # « EI » au milieu des données n'est pas la fin : il faut un blanc avant et après.
    donnees = b"BI /W 2 /H 1 /CS /G ID \x00EI\x01 xEIx EI Q"
    assert operations(donnees) == [("BI", [{"W": 2, "H": 1, "CS": lecteur.Nom("G")}]), ("Q", [])]
    assert operations(b"BI /W 1 ID EI") == [("BI", [{"W": 1}])]
    assert operations(b"BI /W 1 ID \x00\nEI") == [("BI", [{"W": 1}])]


@pytest.mark.parametrize(
    "donnees",
    [
        pytest.param(b"1 0 0 ] cm", id="fermant-seul"),
        pytest.param(b">> Tf", id="fermant-de-dictionnaire"),
        pytest.param(b"{ Q", id="accolade"),
        pytest.param(b"(sans fin Tj", id="chaine-sans-fin"),
        pytest.param(b"<</A 1 Tj", id="dictionnaire-sans-fin"),
        pytest.param(b"BI /W 1 ID donnees", id="image-sans-fin"),
        pytest.param(b"BI 1 ID EI", id="image-cle-non-nom"),
        pytest.param(b"BI /W", id="image-coupee"),
        pytest.param(b"<</A>> Tj", id="valeur-manquante"),
    ],
)
def test_operations_mal_formees(donnees: bytes) -> None:
    with pytest.raises(lecteur.Illisible) as erreur:
        operations(donnees)
    assert erreur.value.chemin == "flux de contenu"


# Textes posés et superpositions (ADR-0214, ADR-0215)


def test_boite_d_un_texte_en_helvetica(ouvrir: Any) -> None:
    # « AB » en Helvetica 10 : 667 + 667 millièmes ; montée 718, descente -207 (AFM d'Adobe).
    (boite,) = boites(ouvrir(document(b"BT /H 10 Tf 50 60 Td (AB) Tj ET")))
    assert boite == (50.0, 57.93, 63.34, 67.18)


@pytest.mark.parametrize(
    ("operations_", "attendue"),
    [
        pytest.param(b"2 Tc", (50.0, 57.93, 67.34, 67.18), id="espacement"),
        pytest.param(b"50 Tz", (50.0, 57.93, 56.67, 67.18), id="echelle"),
        pytest.param(b"3 Ts", (50.0, 60.93, 63.34, 70.18), id="montee"),
        pytest.param(b"q 2 0 0 2 0 0 cm", (100.0, 115.86, 126.68, 134.36), id="matrice"),
        pytest.param(b"q 2 0 0 2 0 0 cm Q", (50.0, 57.93, 63.34, 67.18), id="matrice-rendue"),
        pytest.param(b"Q Q", (50.0, 57.93, 63.34, 67.18), id="pile-vide"),
        pytest.param(b"/H Tf 1 Tc x Tz", (50.0, 57.93, 65.34, 67.18), id="operandes-invalides"),
    ],
)
def test_etat_du_texte(ouvrir: Any, operations_: bytes, attendue: tuple[float, ...]) -> None:
    contenu = b"BT /H 10 Tf " + operations_ + b" 50 60 Td (AB) Tj ET"
    if operations_.startswith(b"q"):
        contenu = operations_ + b" BT /H 10 Tf 50 60 Td (AB) Tj ET"
    assert boites(ouvrir(document(contenu))) == [attendue]


def test_operandes_invalides(ouvrir: Any) -> None:
    # Opérandes manquants ou d'un autre type : l'opération est ignorée, la lecture continue.
    contenu = b"/x cm BT /H 10 Tf 50 60 Td 1 Td 1 2 3 Tm 1.5 Tr 0 0 m /x l (AB) Tj ET"
    assert boites(ouvrir(document(contenu))) == [(50.0, 57.93, 63.34, 67.18)]


def test_mots_et_ajustements(ouvrir: Any) -> None:
    # « A A » : l'espace (278) prend Tw ; un ajustement de -1000 avance d'un cadratin.
    relevee = ouvrir(document(b"BT /H 10 Tf 5 Tw 0 0 Td [(A A) -1000 (B)] TJ ET"))
    assert boites(relevee)[0][2] == round((667 + 278 + 667 + 1000 + 667) / 100 + 5, 3)
    # Un ajustement positif ramène en arrière : la boîte part de là où le texte est allé.
    relevee = ouvrir(document(b"BT /H 10 Tf 0 0 Td [2000 (A)] TJ ET"))
    assert boites(relevee)[0][0] == -20.0


def test_positions_successives(ouvrir: Any) -> None:
    contenu = (
        b"BT /H 10 Tf 0 100 Td (A) Tj 14 TL T* (A) Tj 0 -20 TD (A) Tj (A) ' 1 2 (A) \" "
        b"2 0 0 2 300 300 Tm (A) Tj ET"
    )
    departs = [(b[0], b[1]) for b in boites(ouvrir(document(contenu)))]
    assert departs == [
        (0.0, 97.93),
        (0.0, 83.93),
        (0.0, 63.93),
        (0.0, 43.93),
        (0.0, 23.93),
        (300.0, 295.86),
    ]


def test_texte_sur_texte() -> None:
    contenu = b"BT /H 12 Tf 100 700 Td (Total 100) Tj ET BT /H 12 Tf 130 700 Td (200) Tj ET"
    valeurs_ = obs(document(contenu))
    assert valeurs_["pagespdf.superpositions"] == 1
    assert valeurs_["pagespdf.superpositions.premiere_page"] == 1
    assert valeurs_["pagespdf.superpositions.pages"] == [1]


@pytest.mark.parametrize(
    ("second", "superpositions", "d_un_signe"),
    [
        pytest.param(b"100.3 700 Td (Total 100)", 0, 0, id="faux-gras"),
        pytest.param(b"130 700 Td (2)", 0, 1, id="un-signe"),
        pytest.param(b"130 700 Td (   )", 0, 0, id="espaces"),
        pytest.param(b"300 700 Td (200)", 0, 0, id="ailleurs"),
        pytest.param(b"100 708 Td (Total 100 !)", 0, 0, id="decale-de-moins-de-moitie"),
        pytest.param(b"3 Tr 130 700 Td (200)", 0, 0, id="invisible"),
    ],
)
def test_textes_qui_ne_se_superposent_pas(
    second: bytes, superpositions: int, d_un_signe: int
) -> None:
    contenu = b"BT /H 12 Tf 100 700 Td (Total 100) Tj ET BT /H 12 Tf " + second + b" Tj ET"
    valeurs_ = obs(document(contenu))
    assert valeurs_["pagespdf.superpositions"] == superpositions
    assert valeurs_["pagespdf.superpositions_d_un_signe"] == d_un_signe
    assert "pagespdf.superpositions.pages" not in valeurs_ or superpositions


def test_texte_invisible_et_texte_d_espaces_dessous() -> None:
    # Un texte invisible n'est pas posé ; un texte d'espaces dessous ne compte pas.
    contenu = b"BT /H 12 Tf 3 Tr 100 700 Td (Total 100) Tj 0 Tr (     ) Tj ET"
    contenu += b" BT /H 12 Tf 100 700 Td (200) Tj ET"
    valeurs_ = obs(document(contenu))
    assert valeurs_["pagespdf.superpositions"] == 0
    assert valeurs_["pagespdf.textes"] == 2


def test_textes_vides_et_sans_taille(ouvrir: Any) -> None:
    relevee = ouvrir(document(b"BT /H 0 Tf (AB) Tj (AB) Tj /H 10 Tf () Tj [] TJ 5 TJ Tj ET"))
    assert [t.boite[2] - t.boite[0] for t in relevee.textes] == [0.0, 0.0]
    assert relevee.superpositions == 0


# Textes non mesurés


@pytest.mark.parametrize(
    ("police", "contenu"),
    [
        pytest.param(b"/H 99 0 R", b"/H 10 Tf (AB) Tj", id="police-absente"),
        pytest.param(b"", b"/H 10 Tf (AB) Tj", id="sans-police"),
        pytest.param(b"/H 5 0 R", b"(AB) Tj", id="sans-Tf"),
        pytest.param(b"/H 7 0 R", b"/H 10 Tf (AB) Tj", id="non-standard-sans-largeurs"),
        pytest.param(b"/H 5 0 R", b"/H 10000000 Tf (AB) Tj", id="taille-demesuree"),
        pytest.param(b"/H 5 0 R", b"/H 10 Tf 1 0 0 1 100000000 0 Tm (AB) Tj", id="hors-page"),
    ],
)
def test_textes_non_mesures(police: bytes, contenu: bytes) -> None:
    autre = {7: b"<</Type/Font/Subtype/Type1/BaseFont/Inconnue>>"}
    valeurs_ = obs(document(b"BT " + contenu + b" ET", polices=police, objets=autre))
    assert valeurs_["pagespdf.textes_non_mesures"] == 1
    assert valeurs_["pagespdf.textes"] == 0


# Polices (ADR-0215, ADR-0216)


def police(corps: bytes, ouvrir: Any, texte: bytes = b"AB", objets: Any = None) -> Any:
    """Ce qu'on relève d'un texte écrit, en taille 10, avec la police ``corps`` (objet 7)."""
    contenu = b"BT /P 10 Tf 0 0 Td <" + texte.hex().encode() + b"> Tj ET"
    return ouvrir(document(contenu, polices=b"/P 7 0 R", objets={7: corps} | (objets or {})))


def test_polices_14_standard() -> None:
    # Largeurs de l'AFM d'Adobe, pour quelques glyphes vérifiés à la main dans les fichiers.
    largeurs = {
        nom: dict(zip(mots.split()[::2], map(int, mots.split()[1::2]), strict=True))
        for nom, (_, _, _, mots) in _polices14.POLICES.items()
    }
    assert len(largeurs) == 14
    assert largeurs["Helvetica"]["A"] == 667
    assert largeurs["Times-Roman"]["a"] == 444
    assert set(largeurs["Courier"].values()) == {600}
    assert _polices14.POLICES["Symbol"][2] == "Symbol"
    winansi = _polices14.ENCODAGES["WinAnsiEncoding"].split()
    assert (winansi[0x80], winansi[0xE9], winansi[0xA0], winansi[0x27]) == (
        "Euro",
        "eacute",
        "space",
        "quotesingle",
    )
    assert _polices14.ENCODAGES["StandardEncoding"].split()[0x27] == "quoteright"
    assert _polices14.ENCODAGES["MacRomanEncoding"].split()[0xDB] == "currency"


@pytest.mark.parametrize(
    ("encodage", "texte", "largeur"),
    [
        pytest.param(b"", b"'", 0.222, id="standard-par-defaut"),
        pytest.param(b"/Encoding/WinAnsiEncoding", b"'", 0.191, id="winansi"),
        pytest.param(b"/Encoding/MacRomanEncoding", b"\xdb", 0.556, id="macroman"),
        pytest.param(b"/Encoding/Inconnu", b"'", 0.222, id="encodage-inconnu"),
        pytest.param(
            b"/Encoding<</BaseEncoding/WinAnsiEncoding/Differences[39/A/B 300/C]>>",
            b"'(",
            1.334,
            id="differences",
        ),
        pytest.param(b"/Encoding<</Differences[/A 39/A]>>", b"'", 0.667, id="nom-avant-code"),
        pytest.param(b"/Encoding<</Differences 5>>", b"'", 0.222, id="differences-invalides"),
    ],
)
def test_encodages_d_une_police_standard(
    ouvrir: Any, encodage: bytes, texte: bytes, largeur: float
) -> None:
    corps = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica" + encodage + b">>"
    (boite,) = police(corps, ouvrir, texte).textes
    assert round((boite.boite[2] - boite.boite[0]) / 10, 3) == largeur


def test_symbol_garde_son_encodage(ouvrir: Any) -> None:
    corps = b"<</Type/Font/Subtype/Type1/BaseFont/Symbol/Encoding/WinAnsiEncoding>>"
    (texte,) = police(corps, ouvrir, b"a").textes  # alpha : 631 millièmes
    assert round(texte.boite[2] - texte.boite[0], 2) == 6.31


def test_glyphe_absent_de_l_afm(ouvrir: Any) -> None:
    corps = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding<</Differences[65/inconnu]>>>>"
    relevee = police(corps, ouvrir, b"A")
    assert (relevee.textes, relevee.non_mesures) == ([], 1)


@pytest.mark.parametrize(
    ("descripteur", "hauteurs"),
    [
        pytest.param(b"<</Ascent 900/Descent -200>>", (9.0, -2.0), id="declarees"),
        pytest.param(b"<</Ascent 900/Descent 100>>", (9.0, 0.0), id="descente-positive"),
        pytest.param(b"<</Ascent 100/Descent 200>>", (8.0, -2.0), id="inversees"),
        pytest.param(b"<</Ascent 900>>", (8.0, -2.0), id="descente-absente"),
        pytest.param(b"<<>>", (8.0, -2.0), id="vide"),
    ],
)
def test_montee_et_descente(ouvrir: Any, descripteur: bytes, hauteurs: tuple[float, float]) -> None:
    corps = b"<</Subtype/TrueType/BaseFont/X/FirstChar 65/LastChar 66/Widths[500 500]"
    corps += b"/FontDescriptor 8 0 R>>"
    (texte,) = police(corps, ouvrir, objets={8: descripteur}).textes
    assert (round(texte.boite[3], 3), round(texte.boite[1], 3)) == hauteurs


def test_police_simple_et_largeur_manquante(ouvrir: Any) -> None:
    # Codes hors de /FirstChar à /LastChar : /MissingWidth ; une largeur illisible aussi.
    corps = b"<</Subtype/TrueType/BaseFont/X/FirstChar 65/LastChar 66/Widths[500 /x]"
    corps += b"/FontDescriptor 8 0 R>>"
    relevee = police(corps, ouvrir, b"ABC", {8: b"<</MissingWidth 250>>"})
    (texte,) = relevee.textes
    assert texte.boite[2] - texte.boite[0] == 10.0
    assert relevee.hors_plage == 1


def test_plage_deduite_des_largeurs_et_sans_largeur_manquante(ouvrir: Any) -> None:
    corps = b"<</Subtype/Type1/BaseFont/X/FirstChar 65/Widths[500]/FontDescriptor 8 0 R>>"
    relevee = police(corps, ouvrir, b"AB", {8: b"<</MissingWidth /x>>"})
    assert (relevee.hors_plage, relevee.textes[0].boite[2]) == (1, 5.0)


@pytest.mark.parametrize(
    ("w", "texte", "largeur"),
    [
        pytest.param(b"[65[500 600]]", b"\x00A\x00B", 11.0, id="liste"),
        pytest.param(b"[65 70 300]", b"\x00A\x00B", 6.0, id="plage"),
        pytest.param(b"[65 65 300 66 66 400]", b"\x00A\x00B", 7.0, id="deux-plages"),
        pytest.param(b"[65[500 /x]]", b"\x00A\x00B", 15.0, id="largeur-illisible"),
        pytest.param(None, b"\x00A", 10.0, id="defaut"),
    ],
)
def test_police_composite(ouvrir: Any, w: bytes | None, texte: bytes, largeur: float) -> None:
    descendante = b"<</Subtype/CIDFontType2/FontDescriptor 9 0 R" + (b"/W " + w if w else b"")
    corps = b"<</Subtype/Type0/BaseFont/ABCDEF+Noto/Encoding/Identity-H/DescendantFonts[8 0 R]>>"
    relevee = police(corps, ouvrir, texte, {8: descendante + b">>"})
    (boite,) = relevee.textes
    assert round(boite.boite[2] - boite.boite[0], 3) == largeur
    assert relevee.polices == {"Noto": {("ABCDEF", "FontFile2")}}


@pytest.mark.parametrize(
    ("encodage", "w"),
    [
        pytest.param(b"/Identity-V", b"", id="verticale"),
        pytest.param(b"/UniJIS-UCS2-H", b"", id="autre-cmap"),
        pytest.param(b"/Identity-H", b"/W 5", id="w-pas-une-liste"),
        pytest.param(b"/Identity-H", b"/W[/x 1 2]", id="w-premier-invalide"),
        pytest.param(b"/Identity-H", b"/W[65 66]", id="w-tronque"),
        pytest.param(b"/Identity-H", b"/W[65]", id="w-seul"),
    ],
)
def test_police_composite_non_mesuree(ouvrir: Any, encodage: bytes, w: bytes) -> None:
    corps = b"<</Subtype/Type0/BaseFont/X/Encoding" + encodage + b"/DescendantFonts[8 0 R]>>"
    relevee = police(corps, ouvrir, b"\x00A", {8: b"<<" + w + b">>"})
    assert (relevee.textes, relevee.non_mesures) == ([], 1)


def test_police_composite_sans_descendante(ouvrir: Any) -> None:
    corps = b"<</Subtype/Type0/BaseFont/X/Encoding/Identity-H/DescendantFonts[]/W 5>>"
    relevee = police(corps, ouvrir, b"\x00A")
    assert round(relevee.textes[0].boite[2], 3) == 10.0  # /DW par défaut : 1000


def test_largeurs_trop_nombreuses(monkeypatch: pytest.MonkeyPatch, ouvrir: Any) -> None:
    monkeypatch.setattr(pagespdf, "_ELEMENTS_MAX", 2)
    simple = b"<</Subtype/TrueType/BaseFont/X/FirstChar 65/Widths[1 2 3]>>"
    assert police(simple, ouvrir).non_mesures == 1
    composite = b"<</Subtype/Type0/BaseFont/X/Encoding/Identity-H/DescendantFonts[8 0 R]>>"
    for w in (b"[1 2 3]", b"[65[1 2 3]]"):
        assert police(composite, ouvrir, b"\x00A", {8: b"<</W " + w + b">>"}).non_mesures == 1
    standard = b"<</Subtype/Type1/BaseFont/Helvetica/Encoding<</Differences[65/B/C/D]>>>>"
    (texte,) = police(standard, ouvrir, b"A").textes
    assert texte.boite[2] == 6.67  # Differences ignorées : « A » reste « A »


def test_police_type3(ouvrir: Any) -> None:
    corps = b"<</Subtype/Type3/FontMatrix[0.01 0 0 0.01 0 0]/FirstChar 65/Widths[50 /x]"
    corps += b"/FontBBox[0 -30 100 90]>>"
    relevee = police(corps, ouvrir, b"AB")
    (texte,) = relevee.textes
    assert tuple(round(v, 3) for v in texte.boite) == (0.0, -3.0, 5.0, 9.0)
    assert (relevee.polices, relevee.hors_plage) == ({}, 0)


@pytest.mark.parametrize(
    "corps",
    [
        pytest.param(b"<</Subtype/Type3/Widths[50]/FirstChar 65>>", id="sans-matrice"),
        pytest.param(b"<</Subtype/Type3/FontMatrix[1 0 0 1 0 0]/FirstChar 65>>", id="sans-widths"),
    ],
)
def test_police_type3_non_mesuree(ouvrir: Any, corps: bytes) -> None:
    assert police(corps, ouvrir).non_mesures == 1


def test_police_type3_boite_inversee(ouvrir: Any) -> None:
    corps = b"<</Subtype/Type3/FontMatrix[0.01 0 0 0.01 0 0]/FirstChar 65/Widths[50 50]"
    corps += b"/FontBBox[0 90 100 -30]>>"
    (texte,) = police(corps, ouvrir).textes
    assert (texte.boite[1], texte.boite[3]) == (-2.0, 8.0)


def test_police_qui_n_est_pas_un_dictionnaire(ouvrir: Any) -> None:
    assert police(b"[1]", ouvrir).non_mesures == 1


def test_police_lue_une_fois_et_police_directe() -> None:
    contenu = b"BT /H 10 Tf (AB) Tj /H 10 Tf (AB) Tj /D 10 Tf (AB) Tj ET"
    valeurs_ = obs(document(contenu, polices=b"/H 5 0 R/D<</Subtype/Type1/BaseFont/Helvetica>>"))
    assert valeurs_["pagespdf.polices"] == 2


@pytest.mark.parametrize(
    ("base", "attendu"),
    [
        (b"ABCDEF+Arial", ("ABCDEF", "Arial")),
        (b"abcdef+Arial", ("", "abcdef+Arial")),
        (b"ABCDE+Arial", ("", "ABCDE+Arial")),
        (b"ABCDEF+", ("", "ABCDEF+")),
    ],
)
def test_prefixe_d_un_sous_ensemble(base: bytes, attendu: tuple[str, str]) -> None:
    assert pagespdf._sous_ensemble(base.decode()) == attendu


def test_familles_melangees() -> None:
    # Deux sous-ensembles d'Arial sur la page ; deux objets d'un même sous-ensemble, non.
    autre = SIMPLE.replace(b"ABCDEF+", b"GHIJKL+")
    contenu = b"BT /S 10 Tf (AB) Tj /T 10 Tf 0 50 Td (CD) Tj /U 10 Tf 0 50 Td (EF) Tj ET"
    valeurs_ = obs(
        document(contenu, polices=b"/S 6 0 R/T 7 0 R/U 8 0 R", objets={7: autre, 8: SIMPLE})
    )
    assert valeurs_["pagespdf.familles_melangees"] == 1
    assert valeurs_["pagespdf.familles_melangees.premiere_page"] == 1
    assert valeurs_["pagespdf.familles_melangees.noms"] == ["Arial"]
    assert valeurs_["pagespdf.polices"] == 3


def test_familles_incorporee_et_non_incorporee_invisible() -> None:
    # Arial non incorporée, mais en texte invisible : ne compte pas.
    non_incorporee = b"<</Subtype/TrueType/BaseFont/Arial/FirstChar 65/LastChar 66/Widths[1 1]>>"
    contenu = b"BT /S 10 Tf (AB) Tj 3 Tr /T 10 Tf (AB) Tj ET"
    valeurs_ = obs(document(contenu, polices=b"/S 6 0 R/T 7 0 R", objets={7: non_incorporee}))
    assert valeurs_["pagespdf.familles_melangees"] == 0
    assert "pagespdf.familles_melangees.noms" not in valeurs_


def test_codes_hors_plage() -> None:
    # « { » (123) et « ~ » (126) passent /LastChar 122 ; en texte invisible, ils ne comptent pas.
    contenu = b"BT /S 10 Tf (a{~) Tj 3 Tr ({) Tj ET"
    valeurs_ = obs(document(contenu))
    assert valeurs_["pagespdf.codes_hors_plage"] == 2
    assert valeurs_["pagespdf.codes_hors_plage.pages"] == [1]


# Caches (ADR-0214)

TEXTE = b"BT /H 12 Tf 100 700 Td (Total 100) Tj ET "
"""Un texte de 100 à 150 en largeur, de 697,5 à 708,6 en hauteur."""


@pytest.mark.parametrize(
    ("chemin", "caches"),
    [
        pytest.param(b"1 g 95 690 80 25 re f", 1, id="rectangle"),
        pytest.param(b"95 690 80 25 re F 95 690 80 25 re f*", 1, id="deux-fois-le-meme-texte"),
        pytest.param(b"95 690 m 175 690 l 175 715 l 95 715 l h f", 1, id="quatre-segments"),
        pytest.param(b"95 690 m 175 690 l 175 715 l 95 715 l 95 690 l b", 1, id="referme"),
        pytest.param(b"0 0 m 1 1 l 95 690 80 25 re B", 1, id="re-apres-un-trace"),
        pytest.param(
            b"0 0 m 1 0 l 1 1 l 0 1 l 95 690 m 175 690 l 175 715 l 95 715 l f", 1, id="second-trace"
        ),
        pytest.param(b"0 1 -1 0 0 0 cm 690 -175 25 80 re f", 1, id="quart-de-tour"),
        pytest.param(b"95 690 80 4 re f", 0, id="soulignement"),
        pytest.param(b"95 690 80 25 re S", 0, id="trait-seul"),
        pytest.param(b"95 690 80 25 re n", 0, id="sans-peinture"),
        pytest.param(b"95 690 m 175 690 l 175 715 l 95 700 l f", 0, id="pas-un-rectangle"),
        pytest.param(b"95 690 m 175 690 l 175 715 c 95 715 l f", 0, id="courbe"),
        pytest.param(b"95 690 m 175 690 l 175 715 l f", 0, id="trois-points"),
        pytest.param(b"0.7 0.7 -0.7 0.7 0 0 cm 95 690 80 25 re f", 0, id="tourne"),
        pytest.param(b"0 0 1000000000 1000000000 re f", 0, id="demesure"),
        pytest.param(b"1 2 re f 95 690 m f", 0, id="operandes-invalides"),
    ],
)
def test_caches(chemin: bytes, caches: int) -> None:
    valeurs_ = obs(document(TEXTE + chemin))
    assert valeurs_["pagespdf.caches"] == caches
    assert valeurs_["pagespdf.textes_caches"] == caches


def test_rectangle_avant_le_texte() -> None:
    valeurs_ = obs(document(b"1 g 95 690 80 25 re f 0 g " + TEXTE))
    assert valeurs_["pagespdf.caches"] == 0


def test_rectangle_sur_un_texte_d_espaces_et_un_texte_vide() -> None:
    contenu = b"BT /H 12 Tf 100 700 Td (    ) Tj /H 0 Tf (AB) Tj ET 0 0 600 800 re f"
    assert obs(document(contenu))["pagespdf.caches"] == 0


@pytest.mark.parametrize(
    ("etat", "caches"),
    [
        pytest.param(b"<</ca 0.5>>", 0, id="transparent"),
        pytest.param(b"<</ca 1>>", 1, id="opaque"),
        pytest.param(b"<</BM/Multiply>>", 0, id="produit"),
        pytest.param(b"<</BM[/Multiply/Normal]>>", 0, id="produit-en-liste"),
        pytest.param(b"<</BM[]>>", 1, id="liste-vide"),
        pytest.param(b"<</BM/Compatible>>", 1, id="compatible"),
        pytest.param(b"<</SMask<</S/Luminosity>>>>", 0, id="masque-doux"),
        pytest.param(b"<</SMask/None>>", 1, id="sans-masque"),
        pytest.param(b"5", 1, id="pas-un-dictionnaire"),
        pytest.param(flux_pdf("/ca 0.5", b""), 0, id="en-flux"),
    ],
)
def test_etat_graphique(etat: bytes, caches: int) -> None:
    contenu = TEXTE + b"/E gs 95 690 80 25 re f"
    ressources = b"/ExtGState<</E 7 0 R>>"
    valeurs_ = obs(document(contenu, ressources=ressources, objets={7: etat}))
    assert valeurs_["pagespdf.caches"] == caches


def test_etat_graphique_absent_et_police() -> None:
    # /Font d'un état graphique (§8.4.5) ; un état inconnu ou sans nom ne change rien.
    contenu = b"/X gs gs BT /E gs 100 700 Td (Total 100) Tj ET 95 690 80 25 re f"
    ressources = b"/ExtGState<</E<</Font[5 0 R 12]>>>>"
    assert obs(document(contenu, ressources=ressources))["pagespdf.caches"] == 1
    sans_taille = b"/ExtGState<</E<</Font[5 0 R 0]>>>>"
    assert obs(document(contenu, ressources=sans_taille))["pagespdf.textes_non_mesures"] == 1


# Formes et annotations (ADR-0214)


def test_forme_appelee_par_do() -> None:
    # La forme hérite de la police de l'appelant ; sa matrice la place sur le texte.
    forme = flux_pdf(
        "/Type/XObject/Subtype/Form/BBox[0 0 100 20]/Matrix[1 0 0 1 100 690]", b"1 g 0 0 80 25 re f"
    )
    contenu = TEXTE + b"/X Do /I Do /Z Do Do"
    ressources = b"/XObject<</X 7 0 R/I 8 0 R>>"
    image = flux_pdf("/Subtype/Image/Width 1/Height 1", b"\x00")
    valeurs_ = obs(document(contenu, ressources=ressources, objets={7: forme, 8: image}))
    assert valeurs_["pagespdf.caches"] == 1


def test_forme_avec_ses_ressources() -> None:
    forme = flux_pdf(
        "/Subtype/Form/Resources<</Font<</F 5 0 R>>>>", b"BT /F 12 Tf 130 700 Td (200) Tj ET"
    )
    contenu = TEXTE + b"/X Do"
    valeurs_ = obs(document(contenu, ressources=b"/XObject<</X 7 0 R>>", objets={7: forme}))
    assert valeurs_["pagespdf.superpositions"] == 1


def test_formes_trop_imbriquees() -> None:
    forme = flux_pdf("/Subtype/Form/Resources<</XObject<</X 7 0 R>>>>", b"/X Do")
    valeurs_ = obs(document(b"/X Do", ressources=b"/XObject<</X 7 0 R>>", objets={7: forme}))
    assert valeurs_["pagespdf.pages_lues"] == 0


def annotation(corps: bytes, apparence: bytes = b"", **options: Any) -> dict[str, Any]:
    """Observations d'une page dont la seule annotation (7) a l'apparence normale 8."""
    flux = flux_pdf(
        "/Subtype/Form/BBox[0 0 80 25]" + options.get("forme", ""),
        apparence or b"1 g 0 0 80 25 re f",
    )
    objets = {7: corps, 8: flux}
    return obs(document(TEXTE, page=b"/Annots[7 0 R 99 0 R]", objets=objets))


def test_annotation_qui_cache_un_texte() -> None:
    valeurs_ = annotation(b"<</Subtype/FreeText/Rect[95 690 175 715]/AP<</N 8 0 R>>>>")
    assert valeurs_["pagespdf.caches"] == 1


def test_apparence_placee_dans_son_rectangle() -> None:
    # BBox de 0 à 80 sur 0 à 25, doublée par sa matrice, ramenée au rectangle inversé de
    # l'annotation.
    corps = b"<</Subtype/Square/Rect[175 715 95 690]/AP<</N 8 0 R>>>>"
    valeurs_ = annotation(corps, forme="/Matrix[2 0 0 2 0 0]")
    assert valeurs_["pagespdf.caches"] == 1


def test_apparence_par_etat() -> None:
    corps = b"<</Subtype/Stamp/Rect[95 690 175 715]/AS/Oui/AP<</N<</Oui 8 0 R>>>>>>"
    assert annotation(corps)["pagespdf.caches"] == 1
    corps = b"<</Subtype/Stamp/Rect[95 690 175 715]/AP<</N<</Oui 8 0 R>>>>>>"
    assert annotation(corps)["pagespdf.caches"] == 0


@pytest.mark.parametrize(
    "corps",
    [
        pytest.param(b"<</Subtype/Widget/Rect[95 690 175 715]/AP<</N 8 0 R>>>>", id="champ"),
        pytest.param(b"<</Subtype/Popup/Rect[95 690 175 715]/AP<</N 8 0 R>>>>", id="fenetre"),
        pytest.param(b"<</Subtype/Text/F 2/Rect[95 690 175 715]/AP<</N 8 0 R>>>>", id="cachee"),
        pytest.param(b"<</Subtype/Text/F 32/Rect[95 690 175 715]/AP<</N 8 0 R>>>>", id="non-vue"),
        pytest.param(b"<</Subtype/Text/Rect[95 690 175]/AP<</N 8 0 R>>>>", id="rectangle"),
        pytest.param(b"<</Subtype/Text/Rect[95 690 175 715]>>", id="sans-apparence"),
        pytest.param(b"[1]", id="pas-un-dictionnaire"),
    ],
)
def test_annotations_sans_apparence_lue(corps: bytes) -> None:
    assert annotation(corps)["pagespdf.caches"] == 0


@pytest.mark.parametrize("forme", ["/BBox 5", "/BBox[0 0 0 25]"])
def test_apparence_sans_cadre(forme: str) -> None:
    flux = flux_pdf("/Subtype/Form" + forme, b"1 g 0 0 80 25 re f")
    corps = b"<</Subtype/Square/Rect[95 690 175 715]/AP<</N 8 0 R>>>>"
    valeurs_ = obs(document(TEXTE, page=b"/Annots[7 0 R]", objets={7: corps, 8: flux}))
    assert valeurs_["pagespdf.caches"] == 0


# Pages et limites


def test_arbre_des_pages() -> None:
    # Nœud intermédiaire sans /Type, page vue deux fois, enfant qui n'est pas un dictionnaire ;
    # ressources héritées du nœud.
    pages = b"<</Type/Pages/Kids[7 0 R 3 0 R 8 0 R]/Count 3/Resources<</Font<</H 5 0 R>>>>>>"
    noeud = b"<</Kids[3 0 R 9 0 R]>>"
    seconde = b"<</Type/Page/Contents 11 0 R>>"
    contenu = b"BT /H 12 Tf 100 700 Td (AB) Tj ET"
    objets = {
        2: pages,
        3: b"<</Type/Page/Contents 4 0 R>>",
        7: noeud,
        8: b"5",
        9: seconde,
        11: flux_pdf("", contenu + b" 0 0 600 800 re f"),
    }
    valeurs_ = obs(document(contenu, objets=objets))
    assert (valeurs_["pagespdf.pages"], valeurs_["pagespdf.pages_lues"]) == (2, 2)
    assert valeurs_["pagespdf.caches.pages"] == [2]


def test_page_directe_et_noeud_sans_enfants() -> None:
    pages = b"<</Type/Pages/Kids[<</Type/Page/Contents 4 0 R>> 7 0 R]/Count 1>>"
    valeurs_ = obs(document(TEXTE, objets={2: pages, 7: b"<</Type/Pages>>"}))
    assert (valeurs_["pagespdf.pages"], valeurs_["pagespdf.textes_non_mesures"]) == (1, 1)


def test_pages_au_dela_de_la_limite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pagespdf, "PAGES_MAX", 1)
    pages = b"<</Type/Pages/Kids[3 0 R 3 0 R 7 0 R]/Count 2>>"
    valeurs_ = obs(document(b"", objets={2: pages, 7: b"<</Type/Page>>"}))
    assert (valeurs_["pagespdf.pages"], valeurs_["pagespdf.pages_lues"]) == (2, 1)


def test_contenus_en_tableau() -> None:
    # Deux flux de contenu, et un élément qui n'en est pas un.
    page = b"<</Type/Page/Contents[4 0 R 5 0 R 7 0 R]/Resources<</Font<</H 5 0 R>>>>>>"
    objets = {3: page, 7: flux_pdf("", b"BT /H 12 Tf 130 700 Td (200) Tj ET")}
    assert obs(document(TEXTE, objets=objets))["pagespdf.superpositions"] == 1


def test_page_sans_contenu() -> None:
    valeurs_ = obs(document(b"", objets={3: b"<</Type/Page>>"}))
    assert (valeurs_["pagespdf.pages_lues"], valeurs_["pagespdf.textes"]) == (1, 0)


def test_contenu_illisible() -> None:
    # Filtre inconnu : la page n'est pas lue, une analyse non menée pour tout le module.
    page = b"<</Type/Page/Contents[7 0 R 7 0 R]>>"
    objets = {3: page, 7: flux_pdf("/Filter/LZWDecode", b"x")}
    pages = b"<</Type/Pages/Kids[3 0 R 3 0 R 8 0 R]/Count 2>>"
    contenu = document(b"", objets=objets | {2: pages, 8: page})
    resultat = lignes(contenu)
    assert raisons(resultat) == [PARTIEL]
    assert valeurs_de(resultat)["pagespdf.pages_lues"] == 0


def test_contenu_compresse() -> None:
    page = b"<</Type/Page/Contents 7 0 R/Resources<</Font<</H 5 0 R>>>>>>"
    flux = flux_pdf("/Filter/FlateDecode", zlib.compress(TEXTE + b"95 690 80 25 re f"))
    assert obs(document(b"", objets={3: page, 7: flux}))["pagespdf.caches"] == 1


def test_trop_de_textes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pagespdf, "TEXTES_MAX", 1)
    valeurs_ = obs(document(TEXTE + b"BT /H 12 Tf 130 700 Td (200) Tj ET"))
    assert (valeurs_["pagespdf.pages_lues"], valeurs_["pagespdf.textes"]) == (0, 1)
    assert valeurs_["pagespdf.superpositions"] == 1


def test_grandes_boites(monkeypatch: pytest.MonkeyPatch) -> None:
    # Une boîte qui couvre plus de CASES_MAX cases est comparée à toutes les autres.
    monkeypatch.setattr(pagespdf, "CASES_MAX", 4)
    contenu = TEXTE + b"BT /H 120 Tf 50 650 Td (WW) Tj ET BT /H 12 Tf 130 700 Td (200) Tj ET"
    valeurs_ = obs(document(contenu))
    assert valeurs_["pagespdf.superpositions"] == 2
    assert obs(document(TEXTE + b"0 0 600 800 re f"))["pagespdf.caches"] == 1


def test_arret_avant_le_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pagespdf, "OBJETS_RESERVES", OBJETS_MAX)
    pages = b"<</Type/Pages/Kids[3 0 R 7 0 R]/Count 2>>"
    objets = {2: pages, 7: b"<</Type/Page/Contents 4 0 R>>"}
    valeurs_ = obs(document(TEXTE, page=b"/Annots[8 0 R]", objets=objets))
    assert valeurs_["pagespdf.arret_avant_budget"] is True
    assert (valeurs_["pagespdf.pages"], valeurs_["pagespdf.pages_lues"]) == (2, 0)
    assert valeurs_["pagespdf.textes"] == 0


def test_arret_dans_une_forme(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le budget s'épuise dans la forme : la page appelante s'arrête aussi.
    forme = flux_pdf("/Subtype/Form", b"q Q " * 1100)
    appels = {"n": 0}

    def objets_(contexte: Any) -> int:
        appels["n"] += 1
        return OBJETS_MAX if appels["n"] > 2 else 0

    monkeypatch.setattr(pagespdf.Contexte, "objets", property(objets_))
    contenu = b"/X Do " + TEXTE
    valeurs_ = obs(document(contenu, ressources=b"/XObject<</X 7 0 R>>", objets={7: forme}))
    assert valeurs_["pagespdf.arret_avant_budget"] is True
    assert valeurs_["pagespdf.textes"] == 0


def test_document_chiffre() -> None:
    resultat = lignes(document(TEXTE, trailer="/Root 1 0 R/Encrypt<</Filter/Standard>>"))
    assert valeurs_de(resultat) == {"pagespdf.chiffre": True}
    assert raisons(resultat) == [PARTIEL]


def test_document_illisible() -> None:
    resultat = lignes(b"%PDF-1.7\n")
    assert valeurs_de(resultat) == {}
    assert raisons(resultat) == [PARTIEL]


def test_arbre_des_pages_illisible() -> None:
    contenu = document(TEXTE)
    abime = contenu.replace(b"\n2 0 obj", b"\nx 0 obj", 1)
    resultat = lignes(abime)
    assert valeurs_de(resultat) == {}
    assert raisons(resultat) == [PARTIEL]


def test_observations_d_une_page_ordinaire() -> None:
    assert obs(document(TEXTE)) == {
        "pagespdf.pages": 1,
        "pagespdf.pages_lues": 1,
        "pagespdf.textes": 1,
        "pagespdf.textes_non_mesures": 0,
        "pagespdf.polices": 1,
        "pagespdf.superpositions": 0,
        "pagespdf.superpositions_d_un_signe": 0,
        "pagespdf.caches": 0,
        "pagespdf.textes_caches": 0,
        "pagespdf.familles_melangees": 0,
        "pagespdf.codes_hors_plage": 0,
    }


# Échantillons et oracle de Poppler

ATTENDUS = {
    "document": {},
    "ghostscript": {},
    "superpose": {"pagespdf.superpositions": 1},
    "cache": {"pagespdf.superpositions": 1, "pagespdf.caches": 1},
    "cache_seul": {"pagespdf.caches": 1},
    "annotation": {"pagespdf.superpositions": 1, "pagespdf.caches": 1},
    "fusion": {"pagespdf.familles_melangees": 1},
    "hors_plage": {"pagespdf.codes_hors_plage": 2},
}
"""Relevés non nuls de chaque échantillon."""
RELEVES = (
    "pagespdf.superpositions",
    "pagespdf.superpositions_d_un_signe",
    "pagespdf.caches",
    "pagespdf.familles_melangees",
    "pagespdf.codes_hors_plage",
    "pagespdf.textes_non_mesures",
)


@pytest.mark.parametrize("nom", sorted(ATTENDUS))
def test_echantillons(nom: str) -> None:
    valeurs_ = obs((ECHANTILLONS / f"{nom}.pdf").read_bytes())
    releves = {cle: valeurs_[cle] for cle in RELEVES if valeurs_[cle]}
    assert releves == ATTENDUS[nom]
    assert valeurs_["pagespdf.pages"] == valeurs_["pagespdf.pages_lues"]
    if "pagespdf.familles_melangees" in releves:
        assert valeurs_["pagespdf.familles_melangees.noms"] == ["Helvetica"]


@pytest.mark.parametrize("nom", sorted(ORACLE["echantillons"]))
def test_boites_comparees_a_pdftotext(nom: str) -> None:
    # Chaque mot de pdftotext, de largeur non nulle, est couvert au moins à 90 % par un texte du
    # module, à la même hauteur (montée et descente de la police, comme Poppler).
    contenu = (ECHANTILLONS / f"{nom}.pdf").read_bytes()
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, contenu, "pdf", "pagespdf")
        doc = lecteur.Document(c)
        interprete = pagespdf._Interprete(c, doc)
        pages = [
            interprete.page(numero, page, ressources)
            for numero, (page, ressources) in enumerate(pagespdf._pages(c, doc)[0], start=1)
        ]
    mots = [m for m in ORACLE["echantillons"][nom]["mots"] if m["boite"][2] > m["boite"][0]]
    assert mots
    for mot in mots:
        boite = tuple(mot["boite"])
        textes = pages[mot["page"] - 1].textes
        meilleur = max(textes, key=lambda t: pagespdf._commune(t.boite, boite))
        part = pagespdf._commune(meilleur.boite, boite) / pagespdf._aire(boite)
        assert part >= 0.9, (mot, meilleur.boite)
        assert abs(meilleur.boite[1] - boite[1]) < 0.5
        assert abs(meilleur.boite[3] - boite[3]) < 0.5


@pytest.mark.parametrize("nom", sorted(ORACLE["echantillons"]))
def test_polices_comparees_a_pdffonts(nom: str, ouvrir: Any) -> None:
    # Préfixe de sous-ensemble et incorporation, pour chaque police de la page employée.
    relevee = ouvrir((ECHANTILLONS / f"{nom}.pdf").read_bytes())
    attendues: dict[str, set[tuple[bool, bool]]] = {}
    for police_ in ORACLE["echantillons"][nom]["polices"]:
        _, base = pagespdf._sous_ensemble(police_["nom"])
        attendues.setdefault(base, set()).add((police_["sous_ensemble"], police_["incorporee"]))
    lues = {
        nom_: {(bool(prefixe), bool(programme)) for prefixe, programme in vues}
        for nom_, vues in relevee.polices.items()
    }
    for nom_, vues in lues.items():
        assert vues <= attendues[nom_], nom_


# Règles du catalogue et rapport (ADR-0218)


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("pages")
    trouvees = {}
    for nom in ATTENDUS:
        chemin = dossier / f"{nom}.pdf"
        chemin.write_bytes((ECHANTILLONS / f"{nom}.pdf").read_bytes())
        trouvees[nom] = analyser(chemin)
    return trouvees


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "pagespdf"}


@pytest.mark.parametrize(
    ("nom", "attendues"),
    [
        ("document", set()),
        ("ghostscript", set()),
        ("superpose", {"R-PAGESPDF-001"}),
        ("cache", {"R-PAGESPDF-001", "R-PAGESPDF-002"}),
        ("cache_seul", {"R-PAGESPDF-002"}),
        ("annotation", {"R-PAGESPDF-001", "R-PAGESPDF-002"}),
        ("fusion", {"R-PAGESPDF-003"}),
        ("hors_plage", {"R-PAGESPDF-004"}),
    ],
)
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques}
    assert etats["pagespdf"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues


def test_phrases_des_constats(analyses: dict[str, Analyse]) -> None:
    attendus = {
        "cache": (
            "1 texte(s) posé(s) sur un autre texte, différent, à la même place (première page "
            "concernée : 1)",
            "1 rectangle(s) opaque(s) peint(s) sur un texte déjà posé (première page "
            "concernée : 1)",
        ),
        "fusion": ("1 police(s) employée(s) sur une même page en plusieurs incorporations",),
        "hors_plage": ("2 code(s) de caractère dessiné(s) hors de la plage",),
    }
    for nom, phrases in attendus.items():
        page = export.exporter_html(analyses[nom])
        for phrase in phrases:
            assert escape(phrase) in page, phrase


def test_controle_avant_publication_complet(analyses: dict[str, Analyse]) -> None:
    # Le module ne lit aucune métadonnée identifiante : une analyse non menée ne rend pas le
    # contrôle avant publication incomplet (ADR-0218).
    analyse = analyses["document"]
    assert "pagespdf" not in {n.module for n in analyse.non_menees}
    assert texte("resume.publication_incomplete") not in Presentation(analyse, ()).publication()
