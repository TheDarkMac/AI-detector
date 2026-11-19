"""Couche texte native d'un PDF : lecteur des polices, lecture du texte et module ``caracteres``
(complément de T53, ADR-0243 à ADR-0247).

Les échantillons de ``tests/donnees/caracteres`` (``generer_pdf.py``) sont comparés au texte que
``pdftotext -raw`` de Poppler 25.03.0 en extrait (``oracle_pdf.json``) ; les autres documents
sont construits ici, objet par objet, pour chaque chemin du décodage et de la lecture.
"""

import contextlib
import json
import tempfile
import zlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from metadonnees import CATALOGUE_PDF, contexte, flux_pdf, pdf, raisons, resultats, valeurs_de

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules._lecture import pdf as lecteur
from voight_kampff.modules._lecture import polices
from voight_kampff.modules.caracteres import _pdf
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import Presentation
from voight_kampff.rapport.modele import EtatTechnique, RaisonNonMenee

pytestmark = [pytest.mark.exigence("F-63"), pytest.mark.exigence("F-73")]

DONNEES = Path(__file__).parent / "donnees" / "caracteres"
ORACLE: dict[str, Any] = json.loads((DONNEES / "oracle_pdf.json").read_text(encoding="utf-8"))
ECHANTILLONS = ("libreoffice.pdf", "ghostscript.pdf", "construit.pdf")
PARTIEL = RaisonNonMenee.FORMAT_PARTIEL.value
NUMERISE = RaisonNonMenee.DOCUMENT_NUMERISE.value
HELV = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"
ZWSP = "\u200b"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def cmap(
    corps: bytes, espace: bytes = b"1 begincodespacerange <00> <FF> endcodespacerange"
) -> bytes:
    """CMap ``/ToUnicode`` : ses plages de codes, puis ``corps``."""
    return (
        b"/CIDInit/ProcSet findresource begin 12 dict begin begincmap\n"
        + espace
        + b"\n"
        + corps
        + b"\nendcmap CMapName currentdict/CMap defineresource pop end end"
    )


def document(
    contenu: bytes,
    *,
    polices_: bytes = b"/H 5 0 R",
    ressources: bytes = b"",
    page: bytes = b"",
    objets: dict[int, bytes] | None = None,
    trailer: str = "/Root 1 0 R",
) -> bytes:
    """Une page (3), son contenu (4), Helvetica (5) dans ses ressources ; ``objets`` en plus."""
    tous = {
        1: CATALOGUE_PDF,
        2: b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        3: b"<</Type/Page/Parent 2 0 R/Contents 4 0 R/Resources<</Font<<"
        + polices_
        + b">>"
        + ressources
        + b">>"
        + page
        + b">>",
        4: flux_pdf("", contenu),
        5: HELV,
    } | (objets or {})
    return pdf(tous, trailer)


def pages(nombre: int, page: bytes) -> dict[int, bytes]:
    """Arbre de ``nombre`` pages distinctes (objets 30 et suivants), toutes ``page``."""
    kids = b" ".join(b"%d 0 R" % (30 + rang) for rang in range(nombre))
    arbre = {2: b"<</Type/Pages/Kids[" + kids + b"]/Count %d>>" % nombre}
    return arbre | {30 + rang: page for rang in range(nombre)}


def police(corps: bytes, objets: dict[int, bytes] | None = None) -> dict[int, bytes]:
    """Objets d'une police ``/P`` (objet 7), et ceux qu'elle désigne."""
    return {7: corps} | (objets or {})


@contextlib.contextmanager
def ouvert(contenu: bytes) -> Iterator[tuple[Contexte, lecteur.Document]]:
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, contenu, "pdf", "caracteres")
        yield c, lecteur.Document(c)


def lire(contenu: bytes) -> _pdf.Texte:
    with ouvert(contenu) as (c, doc):
        return _pdf.lire(c, doc)


def lignes(contenu: bytes) -> list[tuple[str, int, str]]:
    """(lieu, numéro, texte) de chaque ligne lue."""
    return [
        (ligne.lieu, ligne.numero, ligne.texte) for p in lire(contenu).pages for ligne in p.lignes
    ]


def textes(contenu: bytes) -> list[str]:
    return [texte for _, _, texte in lignes(contenu)]


def ecrit(contenu: bytes, **options: Any) -> list[str]:
    """Textes des lignes d'une page dont le contenu est ``contenu``."""
    return textes(document(contenu, **options))


def messages(contenu: bytes) -> list[dict[str, Any]]:
    return resultats("caracteres", contenu, "pdf")


def obs(contenu: bytes) -> dict[str, Any]:
    return valeurs_de(messages(contenu))


def positions(contenu: bytes, nom: str) -> list[str]:
    return [
        o["localisation"]["chemin"]
        for o in (m["observation"] for m in messages(contenu) if m["type"] == "observation")
        if o["nom"] == nom
    ]


def correspondance(corps: bytes, objets: dict[int, bytes] | None = None) -> polices.Correspondance:
    with ouvert(document(b"", objets=police(corps, objets))) as (c, doc):
        return polices.Polices(c, doc).correspondance(lecteur.Ref(7, 0))


def decoder(corps: bytes, chaine: bytes, objets: dict[int, bytes] | None = None) -> list[Any]:
    lue = correspondance(corps, objets)
    return [lue.texte(code, longueur) for code, longueur in lue.codes(chaine)]


def oracle(nom: str) -> list[str]:
    """Texte de chaque page selon ``pdftotext -raw``."""
    return ["".join(chr(int(c[2:], 16)) for c in page) for page in ORACLE[nom]]


# Échantillons et oracle de Poppler


def test_oracle_des_outils() -> None:
    assert ORACLE["outils"] == {
        "Ghostscript": "10.05.1",
        "LibreOffice": "LibreOffice 25.2.3.2 520(Build:2)",
        "Poppler": "pdftotext version 25.03.0",
    }


@pytest.mark.parametrize("nom", ECHANTILLONS)
def test_echantillons_contre_poppler(nom: str) -> None:
    # Le texte des pages et des apparences, mot pour mot ; Poppler ne lit pas les commentaires.
    lu = lire((DONNEES / nom).read_bytes())
    attendus = oracle(nom)
    assert len(lu.pages) == len(attendus)
    for page, attendu in zip(lu.pages, attendus, strict=True):
        mots = [
            mot
            for ligne in page.lignes
            if not ligne.lieu.endswith("commentaire")
            for mot in ligne.texte.split()
        ]
        assert mots == attendu.split()


def test_lignes_de_libreoffice() -> None:
    # Chaque ligne de Poppler est une ligne du module, aux blancs près (Poppler écrit une espace
    # cadratin comme une espace).
    lu = lire((DONNEES / "libreoffice.pdf").read_bytes())
    attendues = oracle("libreoffice.pdf")[0].strip("\n").split("\n")
    contenu = [
        " ".join(ligne.texte.split()) for ligne in lu.pages[0].lignes if ligne.lieu == "page 1"
    ]
    assert contenu == [" ".join(ligne.split()) for ligne in attendues]


def test_releves_de_libreoffice() -> None:
    contenu = (DONNEES / "libreoffice.pdf").read_bytes()
    valeurs_ = obs(contenu)
    assert valeurs_["caracteres.homoglyphes.codes"] == ["U+0430 Cyrillic dans Latin (1)"]
    assert valeurs_["caracteres.espaces.codes"] == ["U+2003 (1)"]
    assert valeurs_["caracteres.etiquettes.texte"] == "cache"
    assert valeurs_["caracteres.non_decodes"] == 0
    assert positions(contenu, "caracteres.homoglyphes.position") == [
        "page 1, ligne 2, caractère 11"
    ]
    assert positions(contenu, "caracteres.espaces.position") == ["page 1, ligne 1, caractère 8"]


def test_releves_de_ghostscript() -> None:
    contenu = (DONNEES / "ghostscript.pdf").read_bytes()
    valeurs_ = obs(contenu)
    assert valeurs_["caracteres.homoglyphes.codes"] == ["U+03BF Greek dans Latin (1)"]
    assert positions(contenu, "caracteres.homoglyphes.position") == ["page 1, ligne 2, caractère 1"]


def test_releves_du_document_construit() -> None:
    contenu = (DONNEES / "construit.pdf").read_bytes()
    resultat = messages(contenu)
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["caracteres.pages"] == valeurs_["caracteres.pages_lues"] == 2
    assert valeurs_["caracteres.texte_invisible"] == len("Consigne invisible au lecteur.")
    assert valeurs_["caracteres.pages_sans_texte"] == 1
    assert valeurs_["caracteres.pages_sans_texte.pages"] == [2]
    assert valeurs_["caracteres.homoglyphes.codes"] == ["U+0435 Cyrillic dans Latin (1)"]
    assert valeurs_["caracteres.sans_chasse.codes"] == ["U+200B (1)"]
    assert valeurs_["caracteres.bidirectionnels.codes"] == ["U+202E (1)"]
    assert positions(contenu, "caracteres.bidirectionnels.position") == [
        "page 1, annotation 1, commentaire, ligne 1, caractère 6"
    ]
    assert positions(contenu, "caracteres.sans_chasse.position") == ["page 1, ligne 3, caractère 4"]
    (non_menee,) = [m["non_menee"] for m in resultat if m["type"] == "non_menee"]
    assert non_menee["raison"] == NUMERISE
    assert non_menee["module"] == "caracteres"
    assert non_menee["localisation"]["chemin"] == "page sans couche texte native : 2"
    lieux = {lieu for lieu, _, _ in lignes(contenu)}
    assert lieux == {"page 1", "page 1, annotation 1", "page 1, annotation 1, commentaire"}


@pytest.fixture(scope="module")
def analyse_construit(tmp_path_factory: pytest.TempPathFactory) -> Analyse:
    chemin = tmp_path_factory.mktemp("texte-pdf") / "construit.pdf"
    chemin.write_bytes((DONNEES / "construit.pdf").read_bytes())
    return analyser(chemin)


def test_regles_sur_le_document_construit(analyse_construit: Analyse) -> None:
    analyse = analyse_construit
    regles = {c.regle.identifiant for c in analyse.constats if c.module == "caracteres"}
    assert regles == {
        "R-CARACTERES-002",
        "R-CARACTERES-005",
        "R-CARACTERES-008",
        "R-CARACTERES-014",
    }
    vue = Presentation(analyse, export.masquees())
    assert (
        "Le document porte 30 caractères de texte invisible, écrit sans être peint sur ses pages."
        in [vue.phrase(c) for c in analyse.constats]
    )
    etats = {t.module: t.etat for t in analyse.couverture.techniques if t.partie == 1}
    assert etats["caracteres"] is EtatTechnique.PARTIELLE
    (numerise,) = [n for n in analyse.non_menees if n.raison is RaisonNonMenee.DOCUMENT_NUMERISE]
    assert numerise.module == "caracteres"


# Noms de glyphes (spécification de l'AGL, §2)


@pytest.mark.parametrize(
    ("glyphe", "zapf", "attendu"),
    [
        ("A", False, "A"),
        ("eacute", False, "é"),
        ("dalethatafpatah", False, "\u05d3\u05b2"),
        ("f_i", False, "fi"),
        ("a.sc", False, "a"),
        ("uni0041", False, "A"),
        ("uni00410042", False, "AB"),
        ("uni0041.alt", False, "A"),
        ("u1F600", False, "\U0001f600"),
        ("u0041", False, "A"),
        ("a1", True, "\u2701"),
        ("a1", False, None),
        ("A", True, "A"),
        ("Asmall", False, None),
        ("uniD800", False, None),
        ("uni004", False, None),
        ("uni00g1", False, None),
        ("uniabcd", False, None),
        ("uni", False, None),
        ("u110000", False, None),
        ("uD800", False, None),
        ("u004", False, None),
        ("u0000041", False, None),
        ("g12", False, None),
        (".notdef", False, None),
        ("", False, None),
        ("A_g12", False, "A"),
    ],
)
def test_texte_du_glyphe(glyphe: str, zapf: bool, attendu: str | None) -> None:
    assert polices.texte_du_glyphe(glyphe, zapf=zapf) == attendu


def test_tables_des_glyphes() -> None:
    from voight_kampff.modules._lecture import _glyphes

    noms = _glyphes.AGL.split(" ")
    assert len(noms) == 4281
    assert len(_glyphes.ZAPF_DINGBATS.split(" ")) == 201
    assert "space=0020" in noms
    assert "Copyright 2002-2019 Adobe" in (_glyphes.__doc__ or "")


# Texte des codes : /ToUnicode, encodages


def test_bfchar_et_bfrange() -> None:
    corps = cmap(
        b"2 beginbfchar <01> <0041> <02> <D83DDE00> endbfchar\n"
        b"3 beginbfrange <10> <12> <0061> <20> <21> [<0058> /eacute] <FE> <FF> <FFFF> endbfrange"
    )
    objets = {8: flux_pdf("", corps)}
    lus = decoder(
        b"<</Subtype/TrueType/ToUnicode 8 0 R>>", b"\x01\x02\x10\x12\x20\x21\xfe\xff", objets
    )
    assert lus == ["A", "\U0001f600", "a", "c", "X", "é", "\uffff", None]


def test_bfrange_hors_de_son_tableau() -> None:
    corps = cmap(b"1 beginbfrange <20> <22> [<0058>] endbfrange")
    objets = {8: flux_pdf("", corps)}
    # Un code hors de toute plage prend le nom de son glyphe.
    assert decoder(b"<</Subtype/Type1/ToUnicode 8 0 R>>", b" !A", objets) == ["X", None, "A"]


def test_entrees_de_cmap_ignorees() -> None:
    corps = cmap(
        b"4 beginbfchar 1 <0041> <0102030405> <0042> <03> 7 <04> <> endbfchar\n"
        b"4 beginbfrange <05> <04> <0041> <06> <0006> <0041> <07> <07> <> <08> <08> 9 endbfrange\n"
        b"2 begincodespacerange <00> <00FF> <0000000000> <FFFFFFFFFF> endcodespacerange",
        b"",
    )
    objets = {8: flux_pdf("", corps)}
    lue = correspondance(b"<</Subtype/Type0/Encoding/UniGB-UCS2-H/ToUnicode 8 0 R>>", objets)
    assert (lue.pas, lue.espaces, lue.table, lue.plages) == (2, (), {(1, 4): ""}, ())


def test_plages_identiques_gardent_leur_ordre() -> None:
    corps = cmap(b"2 beginbfrange <20> <20> [<0041>] <20> <20> <0042> endbfrange")
    lue = correspondance(b"<</Subtype/Type1/ToUnicode 8 0 R>>", {8: flux_pdf("", corps)})
    assert [p[3] for p in lue.plages] == [["A"], b"\x00B"]


def test_trop_de_plages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(polices, "ELEMENTS_MAX", 1)
    corps = cmap(
        b"2 beginbfrange <20> <20> <0041> <21> <21> <0042> <22> <23> [<0043> <0044>] endbfrange",
        b"2 begincodespacerange <00> <7F> <80> <FF> endcodespacerange",
    )
    lue = correspondance(b"<</Subtype/Type0/ToUnicode 8 0 R>>", {8: flux_pdf("", corps)})
    assert (len(lue.plages), len(lue.espaces)) == (1, 1)


def test_cmap_illisible() -> None:
    # Filtre inconnu : le CMap est laissé de côté, déclaré non mené, le texte reste lu.
    objets = police(
        b"<</Subtype/Type1/BaseFont/Helvetica/ToUnicode 8 0 R>>",
        {8: flux_pdf("/Filter/LZWDecode", b"x")},
    )
    contenu = document(b"BT /P 12 Tf (Bonjour) Tj ET", polices_=b"/P 7 0 R", objets=objets)
    resultat = messages(contenu)
    assert raisons(resultat) == [PARTIEL]
    assert valeurs_de(resultat)["caracteres.longueur"] == len("Bonjour")


def test_cmap_illisible_d_une_police_composite() -> None:
    mauvais = flux_pdf("/Filter/LZWDecode", b"x")
    with ouvert(
        document(b"", objets=police(b"<</Subtype/Type0/Encoding 8 0 R>>", {8: mauvais}))
    ) as (c, doc):
        lues = polices.Polices(c, doc)
        lue = lues.correspondance(lecteur.Ref(7, 0))
        assert (lue.pas, lue.espaces) == (2, ())
        assert lues.illisible is not None


@pytest.mark.parametrize(
    ("chaine", "attendus"),
    [
        (b"\x41\x81\x40\x42", [(0x41, 1), (0x8140, 2), (0x42, 1)]),
        (b"\x41\xa0", [(0x41, 1), (0xA0, 1)]),
        (b"\x81", [(0x81, 1)]),
    ],
)
def test_plages_de_codes_d_un_cmap_incorpore(
    chaine: bytes, attendus: list[tuple[int, int]]
) -> None:
    # Codes d'un ou deux octets, selon les plages du CMap d'encodage incorporé (§9.7.6.2).
    espaces = b"2 begincodespacerange <00> <80> <8140> <9FFC> endcodespacerange"
    encodage = flux_pdf("/Type/CMap", cmap(b"", espaces))
    lue = correspondance(b"<</Subtype/Type0/Encoding 8 0 R>>", {8: encodage})
    assert list(lue.codes(chaine)) == attendus


def test_plages_de_codes_du_to_unicode() -> None:
    espaces = b"1 begincodespacerange <0000> <FFFF> endcodespacerange"
    unicode = flux_pdf("", cmap(b"1 beginbfchar <0102> <0041> endbfchar", espaces))
    lue = correspondance(b"<</Subtype/Type0/Encoding/UniJIS-UCS2-H/ToUnicode 8 0 R>>", {8: unicode})
    assert (lue.pas, [lue.texte(c, n) for c, n in lue.codes(b"\x01\x02")]) == (0, ["A"])


@pytest.mark.parametrize("encodage", [b"/Identity-H", b"/Identity-V", b"/UniGB-UCS2-H"])
def test_codes_de_deux_octets(encodage: bytes) -> None:
    lue = correspondance(b"<</Subtype/Type0/Encoding" + encodage + b">>")
    assert (lue.pas, list(lue.codes(b"\x00\x41\x00"))) == (2, [(0x41, 2)])
    assert lue.texte(0x41, 2) is None


@pytest.mark.parametrize(
    ("corps", "chaine", "attendus"),
    [
        (HELV, b"A'", ["A", "\u2019"]),  # StandardEncoding de Helvetica
        (
            b"<</Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>",
            b"'\x80",
            ["'", "\u20ac"],
        ),
        (b"<</Subtype/Type1/BaseFont/Times-Roman/Encoding/MacRomanEncoding>>", b"\x8e", ["é"]),
        (b"<</Subtype/Type1/BaseFont/Symbol>>", b"a", ["\u03b1"]),
        (b"<</Subtype/Type1/BaseFont/ZapfDingbats>>", b"!", ["\u2701"]),
        (b"<</Subtype/Type1/BaseFont/ABCDEF+Symbol/Encoding/MacExpertEncoding>>", b"A", ["A"]),
        (
            b"<</Subtype/Type1/BaseFont/X/Encoding<</BaseEncoding/WinAnsiEncoding"
            b"/Differences[65/uni0410/B 1 /g1]>>>>",
            b"ABC\x01\x00",
            ["\u0410", "B", "C", None, None],
        ),
        (b"<</Subtype/Type3/Encoding<</Differences[65/A]>>>>", b"AB", ["A", None]),
        (b"<</Subtype/TrueType/BaseFont/X/FontDescriptor 8 0 R>>", b"A", [None]),
        (b"<</Subtype/TrueType/BaseFont/X/FontDescriptor 9 0 R>>", b"A", ["A"]),
        (b"<</Subtype/Type1/BaseFont/X>>", b"A", ["A"]),
        (b"<</Subtype/Type1/BaseFont/X/Encoding/Inconnu>>", b"A", ["A"]),
    ],
)
def test_encodages_d_une_police_simple(corps: bytes, chaine: bytes, attendus: list[Any]) -> None:
    objets = {
        8: b"<</Type/FontDescriptor/Flags 4/FontFile2 10 0 R>>",  # symbolique, incorporée
        9: b"<</Type/FontDescriptor/Flags 32/FontFile2 10 0 R>>",  # non symbolique
        10: flux_pdf("", b"programme"),
    }
    assert decoder(corps, chaine, objets) == attendus


def test_police_absente_ou_illisible() -> None:
    with ouvert(document(b"", objets={7: b"12"})) as (c, doc):
        lues = polices.Polices(c, doc)
        lue = lues.correspondance(lecteur.Ref(7, 0))
        assert lue is polices.AUCUNE
        assert lues.correspondance(lecteur.Ref(7, 0)) is lue  # lue une fois
        assert lues.correspondance({"Subtype": lecteur.Nom("Type1")}).noms[65] == "A"


def test_destination_d_un_nom_de_glyphe() -> None:
    corps = cmap(b"2 beginbfchar <41> /eacute <42> /g12 endbfchar")
    lus = decoder(b"<</Subtype/Type1/ToUnicode 8 0 R>>", b"AB", {8: flux_pdf("", corps)})
    assert lus == ["é", ""]


# Lignes et espaces


def test_espaces_tirees_des_ajustements() -> None:
    contenu = b"BT /H 12 Tf 72 700 Td [(Bon)-20(jour)-300(le)-1000(monde)] TJ ET"
    assert ecrit(contenu) == ["Bonjour le monde"]


def test_espace_ecrite_non_doublee() -> None:
    contenu = b"BT /H 12 Tf 72 700 Td [(Bonjour )-300( le)] TJ ET"
    assert ecrit(contenu) == ["Bonjour  le"]


def test_lignes_tirees_des_positions() -> None:
    contenu = (
        b"BT /H 12 Tf 72 700 Td (Un) Tj 0 -14 Td (Deux) Tj ET"
        b" BT /H 12 Tf 72 680 Td (Trois) Tj ET BT /H 12 Tf 60 680 Td (Recul) Tj ET"
        b" BT /H 12 Tf 0 1 -1 0 300 300 Tm (Tourne) Tj ET"
        b" BT /H 12 Tf 95 680 Td (Suite) Tj ET"
    )
    assert ecrit(contenu) == ["Un", "Deux", "Trois", "Recul", "Tourne", "Suite"]


def test_mots_poses_un_a_un() -> None:
    # Chaque mot posé à sa place, sans espace écrite : une espace par écart.
    contenu = b"BT /H 10 Tf 72 700 Td (Un) Tj 15 0 Td (mot) Tj 18 0 Td (pose) Tj ET"
    assert ecrit(contenu) == ["Un mot pose"]


def test_operateurs_de_texte() -> None:
    contenu = (
        b"BT /H 10 Tf 14 TL 72 700 Td (Un) Tj T* (Deux) Tj (Trois) ' 2 1 (Quatre) \" ET"
        b" BT /H 10 Tf 0 -12 TD (x) Tj T* (y) Tj ET"
        b" BT 1 0 0 1 72 500 Tm /H 10 Tf 5 Tc 3 Tw 50 Tz (a b) Tj ET"
        b" BT /H 10 Tf 72 400 Td 3.5 Tr (vu) Tj ET"
    )
    assert ecrit(contenu) == ["Un", "Deux", "Trois", "Quatre", "x", "y", "a b", "vu"]


def test_operandes_invalides() -> None:
    contenu = (
        b"BT /H Tf (a) Tj ET BT /H 10 Tf (b) Tj /H x Tf (c) Tj x Tc x Tz Tc 1 2 Td x Td"
        b" 1 2 3 Tm Tj TJ ' (d) Tj ET 1 2 cm"
    )
    resultat = lire(document(contenu))
    assert [ligne.texte for ligne in resultat.pages[0].lignes] == ["bc", "d"]
    assert resultat.pages[0].non_decodes == 1  # « a », sans police


def test_police_inconnue() -> None:
    valeurs_ = obs(document(b"BT /X 10 Tf (ab) Tj ET"))
    assert (valeurs_["caracteres.non_decodes"], valeurs_["caracteres.longueur"]) == (2, 0)


def test_coordonnees_demesurees() -> None:
    contenu = (
        b"BT /H 10 Tf 72 700 Td (Avant) Tj ET"
        b" BT /H 10 Tf 100000000000 0 0 100000000000 0 0 Tm (WW) Tj ET"
        b" BT /H 10 Tf 0 0 0 0 0 0 Tm (Nul) Tj ET BT /H 10 Tf 80 700 Td (Apres) Tj ET"
    )
    # Le cadratin démesuré du premier W le garde sur la ligne ; le second finit hors des bornes ;
    # la matrice nulle n'a pas de direction : chaque glyphe fait sa ligne.
    assert ecrit(contenu) == ["AvantW", "W", "N", "u", "l", "Apres"]


def test_largeurs_inconnues() -> None:
    # Avancée nulle : les codes d'une chaîne se suivent, un déplacement sépare.
    objets = police(b"<</Subtype/TrueType/BaseFont/ABCDEF+X/ToUnicode 8 0 R>>")
    objets[8] = flux_pdf("", cmap(b"2 beginbfchar <01> <0061> <02> <0062> endbfchar"))
    contenu = b"BT /P 10 Tf 72 700 Td <0102> Tj 20 0 Td <02> Tj ET"
    assert ecrit(contenu, polices_=b"/P 7 0 R", objets=objets) == ["ab b"]


def test_police_composite_et_ses_largeurs() -> None:
    objets = police(
        b"<</Subtype/Type0/BaseFont/X/Encoding/Identity-H/DescendantFonts[8 0 R]/ToUnicode 9 0 R>>",
        {
            8: b"<</Subtype/CIDFontType2/DW 500/W[1[600 600]]>>",
            9: flux_pdf(
                "",
                cmap(
                    b"1 beginbfrange <0001> <0002> <0041> endbfrange",
                    b"1 begincodespacerange <0000> <FFFF> endcodespacerange",
                ),
            ),
        },
    )
    contenu = b"BT /P 10 Tf 72 700 Td <00010002> Tj 20 0 Td <0001> Tj ET"
    assert ecrit(contenu, polices_=b"/P 7 0 R", objets=objets) == ["AB A"]


def test_police_d_un_etat_graphique() -> None:
    ressources = b"/ExtGState<</G 8 0 R/V 9 0 R>>"
    objets = {8: b"<</Font[5 0 R 12]>>", 9: b"<</CA 1>>"}
    contenu = b"BT /G gs /V gs /W gs gs 72 700 Td (Etat) Tj ET"
    assert ecrit(contenu, ressources=ressources, objets=objets) == ["Etat"]


def test_etat_graphique_garde_et_rendu() -> None:
    contenu = b"q 3 Tr BT /H 10 Tf 72 700 Td (cache) Tj ET Q Q BT /H 10 Tf 72 680 Td (vu) Tj ET"
    (page,) = lire(document(contenu)).pages
    assert [(ligne.texte, ligne.invisibles) for ligne in page.lignes] == [
        ("cache", [(0, 5)]),
        ("vu", []),
    ]
    assert page.invisibles == 5


# Texte invisible (ADR-0245)


def test_texte_invisible_et_ses_positions() -> None:
    contenu = (
        b"BT /H 10 Tf 72 700 Td (Visible) Tj 7 Tr [(a)-300(b)] TJ 0 Tr (c) Tj ET"
        b" BT /Z 10 Tf 3 Tr 72 680 Td (\x01) Tj ET"
    )
    zwsp = b"<</Subtype/Type1/BaseFont/Helvetica/Encoding<</Differences[1/uni200B]>>>>"
    options: dict[str, Any] = {"polices_": b"/H 5 0 R/Z 7 0 R", "objets": {7: zwsp}}
    (page,) = lire(document(contenu, **options)).pages
    assert [(ligne.texte, ligne.invisibles) for ligne in page.lignes] == [
        ("Visiblea bc", [(7, 8), (9, 10)]),
        (ZWSP, [(0, 1)]),
    ]
    valeurs_ = obs(document(contenu, **options))
    assert valeurs_["caracteres.texte_invisible"] == 3
    assert positions(document(contenu, **options), "caracteres.sans_chasse.position") == [
        "page 1, ligne 2, caractère 1, texte invisible"
    ]


# Texte de remplacement (/ActualText)


@pytest.mark.parametrize(
    ("contenu", "attendus"),
    [
        (b"/Span<</ActualText(oui)>>BDC (XX) Tj EMC", ["oui"]),
        (b"/Span/R BDC (XX) Tj EMC", ["non"]),
        (b"/Span/Absente BDC (XX) Tj EMC", ["XX"]),
        (b"/Span<</ActualText(a)>>BDC /Span<</ActualText(b)>>BDC (XX) Tj EMC EMC", ["a"]),
        (b"(Av) Tj /Span<</ActualText(rien)>>BDC EMC (Ap) Tj", ["AvrienAp"]),
        (b"/Span<</ActualText(seul)>>BDC EMC (suite) Tj", ["seul", "suite"]),
        (b"/Span<</ActualText 12>>BDC (XX) Tj EMC", ["XX"]),
        (b"/Tag BMC (Y) Tj EMC EMC (Z) Tj", ["YZ"]),
        (b"/Tag BDC (Y) Tj EMC", ["Y"]),
        (b"/Span<</ActualText(ouvert)>>BDC (XX) Tj", ["ouvert"]),
        (b"/Span<</ActualText(fin)>>BDC", ["fin"]),
    ],
)
def test_texte_de_remplacement(contenu: bytes, attendus: list[str]) -> None:
    ressources = b"/Properties<</R<</ActualText(non)>>>>"
    corps = b"BT /H 10 Tf 72 700 Td " + contenu + b" ET"
    assert ecrit(corps, ressources=ressources) == attendus


def test_texte_de_remplacement_et_formes() -> None:
    # Une forme qui laisse un contenu marqué ouvert le ferme ; elle ne ferme pas ceux de la page.
    forme = flux_pdf(
        "/Subtype/Form/Resources<</Font<</H 5 0 R>>>>",
        b"EMC BT /H 10 Tf (XX) Tj ET /Span<</ActualText(dans)>>BDC",
    )
    contenu = b"/Span<</ActualText(page)>>BDC /F Do EMC BT /H 10 Tf 72 600 Td (Z) Tj ET"
    resultat = ecrit(contenu, ressources=b"/XObject<</F 8 0 R>>", objets={8: forme})
    assert resultat == ["page", "Z"]


# Formes, images, contenus


def test_formes_et_images() -> None:
    forme = flux_pdf(
        "/Subtype/Form/Matrix[1 0 0 1 10 0]/Resources<</Font<</H 5 0 R>>/XObject<</I 9 0 R>>>>",
        b"BT /H 10 Tf 72 700 Td (Forme) Tj ET /I Do",
    )
    heritee = flux_pdf("/Subtype/Form", b"BT /H 10 Tf 72 680 Td (Heritee) Tj ET")
    image = flux_pdf("/Subtype/Image/Width 1/Height 1", b"\x00")
    autre = flux_pdf("/Subtype/PS", b"")
    ressources = b"/XObject<</F 8 0 R/G 10 0 R/I 9 0 R/P 11 0 R/N 5 0 R>>"
    contenu = b"/F Do /G Do /I Do /P Do /N Do /X Do Do BI /W 1 /H 1 ID \x00 EI"
    objets = {8: forme, 9: image, 10: heritee, 11: autre}
    (page,) = lire(document(contenu, ressources=ressources, objets=objets)).pages
    assert [ligne.texte for ligne in page.lignes] == ["Forme", "Heritee"]
    assert (page.images, page.codes, page.sans_texte) == (3, 12, False)


def test_formes_trop_imbriquees() -> None:
    forme = flux_pdf(
        "/Subtype/Form/Resources<</XObject<</F 8 0 R>>/Font<</H 5 0 R>>>>", b"(a) Tj /F Do"
    )
    contenu = b"BT /H 10 Tf ET /F Do"
    (page,) = lire(document(contenu, ressources=b"/XObject<</F 8 0 R>>", objets={8: forme})).pages
    assert page.complete is False
    assert page.codes == 8  # huit niveaux lus, le neuvième non


def test_plusieurs_flux_de_contenu() -> None:
    page = b"<</Type/Page/Contents[4 0 R 12 6 0 R]/Resources<</Font<</H 5 0 R>>>>>>"
    objets = {3: page, 6: flux_pdf("", b"(suite) Tj ET")}
    contenu = document(b"BT /H 10 Tf 72 700 Td", objets=objets)
    assert textes(contenu) == ["suite"]
    with ouvert(contenu) as (c, doc):
        (lue,) = _pdf.lire(c, doc).pages
    debut = contenu.index(b"stream\nBT") + len(b"stream\n")
    fin = contenu.index(b"(suite) Tj ET") + len(b"(suite) Tj ET")
    assert lue.lignes[0].octets is not None
    assert (lue.lignes[0].octets.debut, lue.lignes[0].octets.longueur) == (debut, fin - debut)


def test_page_sans_contenu() -> None:
    lu = lire(document(b"", objets={3: b"<</Type/Page>>"}))
    assert (lu.trouvees, len(lu.pages), lu.pages[0].lignes) == (1, 1, [])


def test_contenu_illisible() -> None:
    page = b"<</Type/Page/Contents 7 0 R>>"
    pages = b"<</Type/Pages/Kids[3 0 R 8 0 R]/Count 2>>"
    objets = {2: pages, 3: page, 7: flux_pdf("/Filter/LZWDecode", b"x")}
    objets[8] = b"<</Type/Page/Contents 9 0 R/Resources<</Font<</H 5 0 R>>>>>>"
    objets[9] = flux_pdf("", b"BT /H 10 Tf (lue) Tj ET")
    resultat = messages(document(b"", objets=objets))
    assert raisons(resultat) == [PARTIEL]
    valeurs_ = valeurs_de(resultat)
    assert (valeurs_["caracteres.pages_lues"], valeurs_["caracteres.longueur"]) == (1, 3)


def test_contenu_compresse() -> None:
    page = b"<</Type/Page/Contents 7 0 R/Resources<</Font<</H 5 0 R>>>>>>"
    flux = flux_pdf("/Filter/FlateDecode", zlib.compress(b"BT /H 10 Tf (zip) Tj ET"))
    assert textes(document(b"", objets={3: page, 7: flux})) == ["zip"]


# Annotations (ADR-0244)


def annotation(corps: bytes, numero: int = 8) -> dict[int, bytes]:
    apparence = flux_pdf(
        "/BBox[0 0 100 20]/Resources<</Font<</H 5 0 R>>>>", b"BT /H 10 Tf 2 2 Td (Vue) Tj ET"
    )
    return {numero: corps, 9: apparence}


@pytest.mark.parametrize(
    ("corps", "attendues"),
    [
        (
            b"<</Subtype/FreeText/Rect[0 0 100 20]/AP<</N 9 0 R>>/Contents(Dit)>>",
            [("page 1, annotation 1", "Vue"), ("page 1, annotation 1, commentaire", "Dit")],
        ),
        (
            b"<</Subtype/Text/F 2/Rect[0 0 100 20]/AP<</N 9 0 R>>/Contents(Cachee)>>",
            [("page 1, annotation 1, commentaire", "Cachee")],
        ),
        (b"<</Subtype/Popup/Rect[0 0 100 20]/AP<</N 9 0 R>>/Contents(Fenetre)>>", []),
        (
            b"<</Subtype/Widget/Rect[0 0 100 20]/AP<</N 9 0 R>>/Contents(Champ)>>",
            [("page 1, annotation 1, commentaire", "Champ")],
        ),
        (
            b"<</Subtype/Stamp/Rect[0 0 100 20]/AP<</N<</Oui 9 0 R>>>>/AS/Oui>>",
            [("page 1, annotation 1", "Vue")],
        ),
        (b"<</Subtype/Stamp/Rect[0 0 100 20]/AP<</N<</Oui 9 0 R>>>>>>", []),
        (b"<</Subtype/Stamp/Rect[0 0 100]/AP<</N 9 0 R>>/Contents()>>", []),
        (b"<</Subtype/Stamp/Rect[0 0 100 20]/AP<</N 10 0 R>>>>", []),
        (b"<</Subtype/Stamp/Rect[0 0 100 20]/AP<</N 11 0 R>>>>", []),
        (b"12", []),
    ],
)
def test_annotations(corps: bytes, attendues: list[tuple[str, str]]) -> None:
    objets = annotation(corps)
    objets[10] = flux_pdf("/Resources<</Font<</H 5 0 R>>>>", b"(Sans cadre) Tj")
    objets[11] = flux_pdf("/BBox[0 0 0 20]", b"(Plat) Tj")
    contenu = document(b"", page=b"/Annots[8 0 R]", objets=objets)
    assert [(lieu, texte) for lieu, _, texte in lignes(contenu)] == attendues


def test_commentaire_en_plusieurs_lignes() -> None:
    corps = b"<</Subtype/Text/Contents<FEFF0055006E000D000A0044006500750078000D0000000A>>>"
    contenu = document(b"", page=b"/Annots[8 0 R]", objets={8: corps})
    assert lignes(contenu) == [
        ("page 1, annotation 1, commentaire", 1, "Un"),
        ("page 1, annotation 1, commentaire", 2, "Deux"),
        ("page 1, annotation 1, commentaire", 3, "\x00"),
    ]
    with ouvert(contenu) as (c, doc):
        (page,) = _pdf.lire(c, doc).pages
    assert page.lignes[0].octets == doc.localisation(lecteur.Ref(8, 0), "").octets


def test_annotation_directe_et_annotations_illisibles() -> None:
    page = b"/Annots[<</Subtype/Text/Contents(Direct)>>]"
    (ligne,) = lire(document(b"", page=page)).pages[0].lignes
    assert (ligne.lieu, ligne.texte, ligne.octets) == (
        "page 1, annotation 1, commentaire",
        "Direct",
        None,
    )
    assert lignes(document(b"", page=b"/Annots 12")) == []


def test_apparence_ne_compte_pas_pour_la_page() -> None:
    apparence = flux_pdf(
        "/BBox[0 0 10 10]/Resources<</XObject<</I 10 0 R>>>>", b"/I Do BI /W 1 ID \x00 EI"
    )
    objets = {8: b"<</Subtype/Stamp/Rect[0 0 10 10]/AP<</N 9 0 R>>>>", 9: apparence}
    objets[10] = flux_pdf("/Subtype/Image", b"\x00")
    (page,) = lire(document(b"(a) Tj", page=b"/Annots[8 0 R]", objets=objets)).pages
    assert (page.images, page.codes) == (0, 1)


# Pages sans couche texte native (ADR-0247)


def test_pages_sans_couche_texte() -> None:
    image = flux_pdf("/Subtype/Image/Width 1/Height 1", b"\x00")
    page = b"<</Type/Page/Contents 4 0 R/Resources<</XObject<</I 8 0 R>>>>>>"
    nombre = 20
    objets = pages(nombre, page) | {8: image}
    contenu = document(b"/I Do", objets=objets)
    resultat = messages(contenu)
    (non_menee,) = [m["non_menee"] for m in resultat if m["type"] == "non_menee"]
    cites = ", ".join(str(n) for n in range(1, 17))
    assert non_menee["localisation"]["chemin"] == f"pages sans couche texte native : {cites}, …"
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["caracteres.pages_sans_texte"] == nombre
    assert valeurs_["caracteres.pages_sans_texte.pages"] == list(range(1, nombre + 1))


@pytest.mark.parametrize(
    ("contenu", "sans_texte"),
    [(b"/I Do", True), (b"", False), (b"/I Do BT 3 Tr /H 10 Tf (ocr) Tj ET", False)],
)
def test_page_d_image_seule(contenu: bytes, sans_texte: bool) -> None:
    image = flux_pdf("/Subtype/Image/Width 1/Height 1", b"\x00")
    resultat = messages(document(contenu, ressources=b"/XObject<</I 8 0 R>>", objets={8: image}))
    assert (NUMERISE in raisons(resultat)) is sans_texte


# Documents et budget


def test_observations_d_une_page_ordinaire() -> None:
    assert obs(document(b"BT /H 12 Tf 72 700 Td (Bonjour) Tj ET")) == {
        "caracteres.pages": 1,
        "caracteres.pages_lues": 1,
        "caracteres.longueur": 7,
        "caracteres.non_decodes": 0,
        "caracteres.texte_invisible": 0,
        "caracteres.pages_sans_texte": 0,
    }


def test_marque_d_ordre_jamais_ordinaire() -> None:
    objets = police(b"<</Subtype/TrueType/ToUnicode 8 0 R>>")
    objets[8] = flux_pdf("", cmap(b"1 beginbfchar <01> <FEFF> endbfchar"))
    contenu = document(b"BT /P 10 Tf <01> Tj (x) Tj ET", polices_=b"/P 7 0 R", objets=objets)
    assert obs(contenu)["caracteres.sans_chasse.inhabituels"] == 1


def test_trop_de_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_pdf, "PAGES_MAX", 1)
    objets = pages(2, b"<</Type/Page/Contents 4 0 R/Resources<</Font<</H 5 0 R>>>>>>")
    valeurs_ = obs(document(b"BT /H 10 Tf (a) Tj ET", objets=objets))
    assert (valeurs_["caracteres.pages"], valeurs_["caracteres.pages_lues"]) == (2, 1)


def test_arret_avant_le_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_pdf, "OBJETS_RESERVES", OBJETS_MAX)
    objets = pages(2, b"<</Type/Page/Contents 4 0 R/Annots[9 0 R]>>")
    valeurs_ = obs(document(b"BT /H 10 Tf (a) Tj ET", objets=objets))
    assert valeurs_["caracteres.arret_avant_budget"] is True
    assert (valeurs_["caracteres.pages"], valeurs_["caracteres.pages_lues"]) == (2, 0)
    assert valeurs_["caracteres.longueur"] == 0


def test_arret_dans_une_forme(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le budget s'épuise dans la forme : la page et ses annotations s'arrêtent aussi.
    forme = flux_pdf("/Subtype/Form", b"q Q " * 1100)
    appels = {"n": 0}

    def objets_(contexte: Any) -> int:
        appels["n"] += 1
        return OBJETS_MAX if appels["n"] > 2 else 0

    monkeypatch.setattr(Contexte, "objets", property(objets_))
    objets = {7: forme, 8: b"<</Subtype/Text/Contents(non)>>"}
    contenu = document(
        b"/X Do", ressources=b"/XObject<</X 7 0 R>>", page=b"/Annots[8 0 R]", objets=objets
    )
    lu = lire(contenu)
    assert lu.arrete is True
    assert lu.pages[0].lignes == []


def test_document_chiffre() -> None:
    resultat = messages(document(b"", trailer="/Root 1 0 R/Encrypt<</Filter/Standard>>"))
    assert valeurs_de(resultat) == {}
    (non_menee,) = [m["non_menee"] for m in resultat if m["type"] == "non_menee"]
    assert non_menee["raison"] == PARTIEL
    assert non_menee["localisation"]["chemin"] == "texte des pages (document chiffré)"


def test_document_illisible() -> None:
    resultat = messages(b"%PDF-1.7\n")
    assert (valeurs_de(resultat), raisons(resultat)) == ({}, [PARTIEL])


def test_arbre_des_pages_illisible() -> None:
    abime = document(b"").replace(b"\n2 0 obj", b"\nx 0 obj", 1)
    resultat = messages(abime)
    assert (valeurs_de(resultat), raisons(resultat)) == ({}, [PARTIEL])


# Lecteur partagé avec pagespdf


def test_pagespdf_lit_les_memes_polices() -> None:
    # Ce que pagespdf lit d'une police ne change pas : il ne lit pas /ToUnicode, même illisible.
    objets = police(
        b"<</Subtype/Type1/BaseFont/Helvetica/ToUnicode 8 0 R>>",
        {8: flux_pdf("/Filter/LZWDecode", b"x")},
    )
    contenu = document(b"BT /P 12 Tf (Bonjour) Tj ET", polices_=b"/P 7 0 R", objets=objets)
    resultat = resultats("pagespdf", contenu, "pdf")
    assert raisons(resultat) == []
    assert valeurs_de(resultat)["pagespdf.textes"] == 1
