"""Propriétés de DOCX et d'ODT : modules ``ooxml`` et ``odf``, lecteur ZIP (T21, complément
bureautique).

Décisions : ADR-0136 (modules), ADR-0137 (lecteur ZIP), ADR-0138 (relations et références non
suivies), ADR-0139 (parties lues), ADR-0140 (noms et valeurs). Les archives bien formées sont
écrites par ``zipfile`` ; les autres, octet par octet (``bureautique.archive_brute``).
"""

import io
import socket
import zipfile
from typing import Any

import pytest
from bureautique import (
    TYPE_APP,
    TYPE_CORE,
    TYPE_CUSTOM,
    Brute,
    app,
    archive_brute,
    core,
    custom,
    docx_,
    meta,
    odt_,
    relations,
    zip_,
)
from metadonnees import identifiantes, observations, raisons, resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff._travail.contexte import LimiteDepassee
from voight_kampff.modules._lecture import proprietes

pytestmark = pytest.mark.exigence("F-10")

PARTIEL = "format_partiel"
TRONQUE = "fichier_tronque"
MANQUANTE = "reference_manquante"
STRICT_APP = "http://purl.oclc.org/ooxml/officeDocument/extendedProperties"
STRICT_CUSTOM = "http://purl.oclc.org/ooxml/officeDocument/customProperties"
STRICT = "http://purl.oclc.org/ooxml/officeDocument/relationships/"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def ooxml(contenu: bytes) -> list[dict[str, Any]]:
    return resultats("ooxml", contenu, "docx")


def odf(contenu: bytes) -> list[dict[str, Any]]:
    return resultats("odf", contenu, "odt")


def proprietes_de(lignes: list[dict[str, Any]]) -> dict[str, Any]:
    """Observations hors présence et nombre de blocs."""
    generales = ("ooxml.present", "ooxml.blocs", "odf.present", "odf.blocs")
    return {n: v for n, v in valeurs_de(lignes).items() if n not in generales}


# DOCX : les trois parties


@pytest.mark.exigence("ES-13")
def test_ooxml_proprietes_principales() -> None:
    lignes = ooxml(
        docx_(
            core(
                "<dc:title>Titre accentué</dc:title><dc:creator>Jeanne Exemple</dc:creator>"
                "<cp:lastModifiedBy>Paul</cp:lastModifiedBy><cp:revision>7</cp:revision>"
                '<dcterms:created xsi:type="dcterms:W3CDTF" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                "2026-11-01T10:20:30Z</dcterms:created><dc:description></dc:description>"
                "<cp:keywords>a<cp:value>b</cp:value></cp:keywords>"
            )
        )
    )
    assert valeurs_de(lignes) == {
        "ooxml.present": True,
        "ooxml.blocs": 1,
        "ooxml.core.dc:title": "Titre accentué",
        "ooxml.core.dc:creator": "Jeanne Exemple",
        "ooxml.core.cp:lastModifiedBy": "Paul",
        "ooxml.core.cp:revision": "7",  # texte dans le schéma
        "ooxml.core.dcterms:created": "2026-11-01T10:20:30Z",  # telle qu'écrite
        "ooxml.core.cp:keywords": ["a", "b"],
    }
    assert identifiantes(lignes) == {
        "ooxml.core.dc:creator": "metadonnee_nominative",
        "ooxml.core.cp:lastModifiedBy": "metadonnee_nominative",
    }
    assert raisons(lignes) == []
    [titre] = [o for o in observations(lignes) if o["nom"] == "ooxml.core.dc:title"]
    assert titre["localisation"]["chemin"] == "docProps/core.xml"


@pytest.mark.exigence("ES-13", "ES-06")
def test_ooxml_proprietes_etendues_typees() -> None:
    lignes = ooxml(
        docx_(
            app_=app(
                "<Template>Normal.dotm</Template><TotalTime>62</TotalTime><Pages>2</Pages>"
                "<Words>x</Words><ScaleCrop>false</ScaleCrop><SharedDoc>oui</SharedDoc>"
                "<Company>Société</Company><Manager>Chef</Manager>"
                "<HyperlinkBase>\\\\serveur\\partage</HyperlinkBase>"
                "<Application>Microsoft Office Word</Application><AppVersion>16.0000</AppVersion>"
                "<HeadingPairs><vt:vector size='2' baseType='variant'>"
                "<vt:variant><vt:lpstr>Titre</vt:lpstr></vt:variant>"
                "<vt:variant><vt:i4>1</vt:i4></vt:variant></vt:vector></HeadingPairs>"
                "<TitlesOfParts><vt:vector size='1' baseType='lpstr'><vt:lpstr>Doc</vt:lpstr>"
                "</vt:vector></TitlesOfParts>"
                "<DigSig><vt:blob>AAECAw==</vt:blob></DigSig>"
                "<HLinks><vt:vector size='1' baseType='variant'><vt:variant>"
                "<vt:lpwstr>http://exemple.invalid/piste</vt:lpwstr></vt:variant></vt:vector></HLinks>"
            )
        )
    )
    assert proprietes_de(lignes) == {
        "ooxml.app.Template": "Normal.dotm",
        "ooxml.app.TotalTime": 62,
        "ooxml.app.Pages": 2,
        "ooxml.app.Words": "x",  # écriture que le type n'admet pas : le texte
        "ooxml.app.ScaleCrop": False,
        "ooxml.app.SharedDoc": "oui",
        "ooxml.app.Company": "Société",
        "ooxml.app.Manager": "Chef",
        "ooxml.app.HyperlinkBase": "\\\\serveur\\partage",
        "ooxml.app.Application": "Microsoft Office Word",
        "ooxml.app.AppVersion": "16.0000",
        "ooxml.app.HeadingPairs": ["Titre", 1],
        "ooxml.app.TitlesOfParts": ["Doc"],
        "ooxml.app.DigSig.taille": 4,
    }
    assert identifiantes(lignes) == {
        "ooxml.app.Template": "nom_de_fichier",
        "ooxml.app.HyperlinkBase": "nom_de_fichier",
        "ooxml.app.Company": "metadonnee_nominative",
        "ooxml.app.Manager": "metadonnee_nominative",
    }
    assert "exemple.invalid" not in str(lignes)  # HLinks : jamais lus (ADR-0138)


def test_ooxml_proprietes_personnalisees() -> None:
    lignes = ooxml(
        docx_(
            custom_=custom(
                ("Outil", "<vt:lpwstr>Générateur 3</vt:lpwstr>"),
                ("Note", "<vt:r8>4.5</vt:r8>"),
                ("Grand", "<vt:r8>1e999</vt:r8>"),
                ("Pas un nombre", "<vt:r8>NaN</vt:r8>"),
                ("Relu", "<vt:bool>1</vt:bool>"),
                ("Compte", "<vt:i4> 12 </vt:i4>"),
                ("Énorme", "<vt:ui8>18446744073709551615</vt:ui8>"),
                ("Date", "<vt:filetime>2026-11-01T10:00:00Z</vt:filetime>"),
                (
                    "Liste",
                    "<vt:vector size='2' baseType='i4'><vt:i4>1</vt:i4><vt:i4>2</vt:i4>"
                    "</vt:vector>",
                ),
                (
                    "Imbriquée",
                    "<vt:vector size='2' baseType='variant'><vt:variant><vt:vector "
                    "size='0' baseType='i4'/></vt:variant><vt:variant><vt:bool>false</vt:bool>"
                    "</vt:variant><autre>x</autre></vt:vector>",
                ),
                ("Binaire", "<vt:blob>!!!=</vt:blob>"),
                ("Vide", "<vt:empty/>"),
                ("Inconnue", "<autre>x</autre>"),
                ("Variante", "<vt:variant><vt:i2>-3</vt:i2></vt:variant>"),
                ("Réel", "<vt:r4>abc</vt:r4>"),
            )
        )
    )
    assert proprietes_de(lignes) == {
        "ooxml.custom.Outil": "Générateur 3",
        "ooxml.custom.Note": 4.5,
        "ooxml.custom.Grand": "inf",
        "ooxml.custom.Pas-un-nombre": "nan",
        "ooxml.custom.Relu": True,
        "ooxml.custom.Compte": 12,
        "ooxml.custom.-norme": "18446744073709551615",  # hors des 64 bits signés
        "ooxml.custom.Date": "2026-11-01T10:00:00Z",
        "ooxml.custom.Liste": [1, 2],
        "ooxml.custom.Imbriqu-e": [False],
        "ooxml.custom.Variante": -3,
        "ooxml.custom.R-el": "abc",
        "ooxml.custom.Binaire.taille": 4,
    }
    assert raisons(lignes) == []


def test_ooxml_propriete_personnalisee_sans_nom() -> None:
    contenu = custom(("", "<vt:lpwstr>a</vt:lpwstr>"), ("Bon", "<vt:lpwstr>b</vt:lpwstr>"))
    lignes = ooxml(docx_(custom_=contenu))
    assert proprietes_de(lignes) == {"ooxml.custom.Bon": "b"}
    assert raisons(lignes) == [PARTIEL]
    # Élément autre qu'une propriété.
    lignes = ooxml(docx_(custom_=custom().replace(b"</Properties>", b"<x/></Properties>")))
    assert raisons(lignes) == [PARTIEL]


def test_ooxml_espaces_stricts_et_inconnus() -> None:
    liens = relations(
        (TYPE_CORE, "docProps/core.xml"),
        (f"{STRICT}extendedProperties", "docProps/app.xml"),
        (f"{STRICT}customProperties", "docProps/custom.xml"),
    )
    lignes = ooxml(
        docx_(
            core('<e:x xmlns:e="urn:autre">1</e:x><dc:title>T</dc:title>'),
            app('<Pages>3</Pages><e:y xmlns:e="urn:autre2">2</e:y>', espace=STRICT_APP),
            custom(("A", "<vt:lpwstr>a</vt:lpwstr>"), espace=STRICT_CUSTOM),
            liens=liens,
        )
    )
    assert proprietes_de(lignes) == {
        "ooxml.core.ns1:x": "1",
        "ooxml.core.dc:title": "T",
        "ooxml.app.Pages": 3,
        "ooxml.app.ns2:y": "2",
        "ooxml.custom.A": "a",
        "ooxml.espace.ns1": "urn:autre",
        "ooxml.espace.ns2": "urn:autre2",
    }


def test_ooxml_type_de_relation_d_office_2007() -> None:
    ancien = "http://schemas.openxmlformats.org/officedocument/2006/relationships/metadata/"
    liens = relations((f"{ancien}core-properties", "docProps/core.xml"))
    lignes = ooxml(docx_(core("<dc:title>T</dc:title>"), liens=liens))
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}


@pytest.mark.parametrize(
    "cible",
    [
        "/docProps/core.xml",
        "./docProps/../docProps/core.xml",
        "doc%50rops/core.xml",
        "../DOCPROPS/CORE.XML",
    ],
)
def test_ooxml_cible_relative_a_la_racine(cible: str) -> None:
    # Cible résolue depuis la racine du paquet, noms de parties comparés sans casse (OPC).
    lignes = ooxml(docx_(core("<dc:title>T</dc:title>"), liens=relations((TYPE_CORE, cible))))
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}


def test_ooxml_sans_proprietes() -> None:
    lignes = ooxml(docx_())
    assert valeurs_de(lignes) == {"ooxml.present": False}
    assert raisons(lignes) == []


def test_ooxml_sans_relations_du_paquet() -> None:
    lignes = ooxml(zip_(("docProps/core.xml", core("<dc:title>T</dc:title>"))))
    assert valeurs_de(lignes) == {"ooxml.present": False}
    assert raisons(lignes) == [PARTIEL]


def test_ooxml_partie_absente() -> None:
    liens = relations((TYPE_CORE, "docProps/core.xml"), (TYPE_APP, "docProps/app.xml"))
    lignes = ooxml(docx_(core("<dc:title>T</dc:title>"), liens=liens))
    assert valeurs_de(lignes)["ooxml.present"] is True
    assert valeurs_de(lignes)["ooxml.blocs"] == 1
    assert raisons(lignes) == [MANQUANTE]


@pytest.mark.exigence("ES-05")
@pytest.mark.parametrize(
    "partie",
    [
        b"<Properties xmlns='urn:autre'/>",  # racine d'une autre partie
        b"<cp:coreProperties xmlns:cp='urn:x'><a/>",  # coupée, racine inconnue
        b"<!DOCTYPE x [<!ENTITY a 'b'>]><x/>",  # DTD refusée (ES-05)
    ],
)
def test_ooxml_partie_illisible(partie: bytes) -> None:
    lignes = ooxml(docx_(partie, app("<Pages>1</Pages>"), partie))
    assert proprietes_de(lignes) == {"ooxml.app.Pages": 1}
    assert raisons(lignes) == [PARTIEL, PARTIEL]


def test_ooxml_proprietes_etendues_illisibles() -> None:
    lignes = ooxml(docx_(app_=b"<Properties xmlns='urn:autre'/>"))
    assert valeurs_de(lignes) == {"ooxml.present": True, "ooxml.blocs": 1}
    assert raisons(lignes) == [PARTIEL]


def test_ooxml_relations_illisibles() -> None:
    racine_inconnue = b"<Autre/>"
    for liens in (racine_inconnue, b"<Relationships xmlns='" + b"x" * 3 + b"'/>"):
        lignes = ooxml(docx_(core("<dc:title>T</dc:title>"), liens=liens))
        assert valeurs_de(lignes) == {"ooxml.present": False}
        assert raisons(lignes) == [PARTIEL]
    # Relations coupées : celles lues avant la coupure restent suivies.
    coupees = relations((TYPE_CORE, "docProps/core.xml"), (TYPE_APP, "docProps/app.xml"))[:-30]
    lignes = ooxml(docx_(core("<dc:title>T</dc:title>"), liens=coupees))
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}
    assert raisons(lignes) == [PARTIEL]


@pytest.mark.exigence("ES-06")
def test_ooxml_relations_externes_jamais_suivies(monkeypatch: pytest.MonkeyPatch) -> None:
    # Modèle distant (M-14) : la relation du document vers lui n'est pas lue ; une relation de
    # propriétés externe ne l'est pas non plus, et sa cible ne figure pas au rapport (ADR-0138).
    def interdit(*_arguments: object, **_options: object) -> None:
        raise AssertionError("connexion réseau")

    monkeypatch.setattr(socket, "socket", interdit)
    monkeypatch.setattr(socket, "create_connection", interdit)
    liens = relations(
        (TYPE_CORE, "docProps/core.xml"),
        (TYPE_APP, "http://pistage.invalid/app.xml", "External"),
        (TYPE_CORE, "docProps/autre.xml"),
        (TYPE_CUSTOM, ""),
    )
    modele = relations(
        (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate",
            "http://pistage.invalid/modele.dotm",
            "External",
        )
    )
    lignes = ooxml(
        docx_(
            core("<dc:title>T</dc:title>"),
            None,
            None,
            ("word/_rels/settings.xml.rels", modele),
            ("docProps/autre.xml", core("<dc:title>Autre</dc:title>")),
            liens=liens,
        )
    )
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}
    assert raisons(lignes) == [PARTIEL, PARTIEL, PARTIEL]
    assert "pistage" not in str(lignes)
    chemins = [n["non_menee"]["localisation"]["chemin"] for n in lignes if n["type"] == "non_menee"]
    assert chemins == [
        "_rels/.rels / app (relation externe, non suivie)",
        "_rels/.rels / core (relation non lue)",
        "_rels/.rels / custom (relation non lue)",
    ]


def test_ooxml_texte_vide_non_observe() -> None:
    lignes = ooxml(docx_(core("<dc:title></dc:title><dc:subject/>"), app("<Template/>")))
    assert proprietes_de(lignes) == {}


def test_ooxml_propriete_repetee_en_liste() -> None:
    lignes = ooxml(docx_(core("<dc:subject>a</dc:subject><dc:subject>b</dc:subject>")))
    assert proprietes_de(lignes) == {"ooxml.core.dc:subject": ["a", "b"]}


def test_ooxml_texte_long_coupe() -> None:
    lignes = ooxml(docx_(core(f"<dc:title>{'a' * 5000}</dc:title>")))
    assert valeurs_de(lignes)["ooxml.core.dc:title.longueur"] == 5000


@pytest.mark.exigence("ES-03", "ES-05")
def test_ooxml_bombe_de_decompression() -> None:
    # 32 Mio de zéros, compressés plus de mille fois : arrêtés par le budget (ES-03).
    with pytest.raises(LimiteDepassee):
        ooxml(docx_(core(f"<dc:title>{' ' * (32 << 20)}</dc:title>")))


# Lecteur ZIP


def test_zip64() -> None:
    lignes = ooxml(
        archive_brute(
            Brute(b"_rels/.rels", relations((TYPE_CORE, "docProps/core.xml"))),
            Brute(b"docProps/core.xml", core("<dc:title>T</dc:title>"), methode=0),
            zip64=True,
        )
    )
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}


@pytest.mark.parametrize("relatif_au_fichier", [False, True])
def test_zip_apres_des_donnees(relatif_au_fichier: bool) -> None:
    # Positions relatives à l'archive ou au fichier : l'archive est retrouvée dans les deux cas.
    lignes = ooxml(
        archive_brute(
            Brute(b"_rels/.rels", relations((TYPE_CORE, "docProps/core.xml"))),
            Brute(b"docProps/core.xml", core("<dc:title>T</dc:title>")),
            prefixe=b"MZ" + bytes(98),
            relatif_au_fichier=relatif_au_fichier,
            commentaire=b"PK\x05\x06 faux enregistrement de fin",
        )
    )
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}
    [titre] = [o for o in observations(lignes) if o["nom"] == "ooxml.core.dc:title"]
    assert titre["localisation"]["octets"]["debut"] >= 100


def test_zip_nom_en_cp437() -> None:
    # Sans le drapeau UTF-8, le nom est en CP437 (APPNOTE, annexe D) : 0x82 est « é ».
    liens = relations((TYPE_CORE, "docProps/c%C3%A9.xml"))
    lignes = ooxml(
        archive_brute(
            Brute(b"_rels/.rels", liens),
            Brute(b"docProps/c\x82.xml", core("<dc:title>T</dc:title>")),
        )
    )
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "T"}
    lignes = ooxml(
        archive_brute(
            Brute(b"_rels/.rels", liens),
            Brute("docProps/cé.xml".encode(), core("<dc:title>U</dc:title>"), drapeaux=0x0800),
        )
    )
    assert proprietes_de(lignes) == {"ooxml.core.dc:title": "U"}


@pytest.mark.parametrize(
    ("entree", "raison", "chemin"),
    [
        (
            Brute(b"docProps/core.xml", b"<x/>", nom_local=b"docProps/autre.xml"),
            PARTIEL,
            "docProps/core.xml (nom de l'en-tête local différent)",
        ),
        (
            Brute(b"docProps/core.xml", b"<x/>", drapeaux=1),
            PARTIEL,
            "docProps/core.xml (entrée chiffrée)",
        ),
        (
            Brute(b"docProps/core.xml", b"<x/>", methode=12),
            PARTIEL,
            "docProps/core.xml (compression inconnue)",
        ),
        (Brute(b"docProps/core.xml", b"<x/>", donnees=b"\xff\xff"), PARTIEL, "docProps/core.xml"),
    ],
)
def test_zip_entree_illisible(entree: Brute, raison: str, chemin: str) -> None:
    lignes = ooxml(
        archive_brute(Brute(b"_rels/.rels", relations((TYPE_CORE, "docProps/core.xml"))), entree)
    )
    assert valeurs_de(lignes) == {"ooxml.present": True, "ooxml.blocs": 1}
    [non_menee] = [n["non_menee"] for n in lignes if n["type"] == "non_menee"]
    assert (non_menee["raison"], non_menee["localisation"]["chemin"]) == (raison, chemin)


@pytest.mark.exigence("ES-05")
def test_zip_entrees_en_double() -> None:
    # Deux lecteurs peuvent prendre l'une ou l'autre : aucune n'est lue.
    liens = relations((TYPE_CORE, "docProps/core.xml"))
    lignes = ooxml(
        archive_brute(
            Brute(b"_rels/.rels", liens),
            Brute(b"docProps/core.xml", core("<dc:title>A</dc:title>")),
            Brute(b"docProps/CORE.xml", core("<dc:title>B</dc:title>")),
        )
    )
    assert valeurs_de(lignes) == {"ooxml.present": True}
    assert raisons(lignes) == [PARTIEL]
    lignes = ooxml(archive_brute(Brute(b"_rels/.rels", liens), Brute(b"_rels/.rels", liens)))
    assert valeurs_de(lignes) == {"ooxml.present": False}


def test_zip_donnees_au_dela_de_la_partie() -> None:
    contenu = archive_brute(
        Brute(b"_rels/.rels", relations((TYPE_CORE, "docProps/core.xml"))),
        Brute(b"docProps/core.xml", core("<dc:title>T</dc:title>"), methode=0),
    )
    # Taille compressée du répertoire central portée au-delà de la fin.
    centrale = contenu.rindex(b"PK\x01\x02")
    gonfle = contenu[: centrale + 20] + (1 << 20).to_bytes(4, "little") + contenu[centrale + 24 :]
    assert raisons(ooxml(gonfle)) == [TRONQUE]
    # Entrée trop grande pour une lecture.
    gonfle = contenu[: centrale + 20] + (17 << 20).to_bytes(4, "little") + contenu[centrale + 24 :]
    assert raisons(ooxml(gonfle)) == [PARTIEL]
    # En-tête local hors de la partie, ou coupé.
    for position in (len(contenu) + 5, len(contenu) - 25):
        loin = contenu[: centrale + 42] + position.to_bytes(4, "little") + contenu[centrale + 46 :]
        assert raisons(ooxml(loin))[-1] in (PARTIEL, TRONQUE)


def test_zip_en_tete_local_coupe() -> None:
    contenu = archive_brute(
        Brute(b"_rels/.rels", relations((TYPE_CORE, "docProps/core.xml"))),
        Brute(b"docProps/core.xml", core("<dc:title>T</dc:title>")),
    )
    centrale = contenu.rindex(b"PK\x01\x02")
    position = len(contenu) - 10  # dans l'enregistrement de fin : moins de 30 octets jusqu'au bout
    loin = contenu[: centrale + 42] + position.to_bytes(4, "little") + contenu[centrale + 46 :]
    assert raisons(ooxml(loin)) == [TRONQUE]
    position = len(contenu) - 30
    loin = contenu[: centrale + 42] + position.to_bytes(4, "little") + contenu[centrale + 46 :]
    assert raisons(ooxml(loin)) == [PARTIEL]  # 30 octets, mais pas un en-tête local


@pytest.mark.parametrize(
    "contenu",
    [
        pytest.param(b"PK\x03\x04" + bytes(40), id="sans-fin"),
        pytest.param(
            b"PK\x05\x06" + bytes(6) + b"\x01\x00" + (99).to_bytes(4, "little") + bytes(6),
            id="repertoire-avant-le-debut",
        ),
        pytest.param(
            b"x" * 46
            + b"PK\x05\x06"
            + bytes(6)
            + b"\x01\x00"
            + (46).to_bytes(4, "little")
            + bytes(6),
            id="repertoire-invalide",
        ),
        pytest.param(
            b"PK\x05\x06" + bytes(4) + b"\xff\xff" * 2 + b"\xff" * 8 + bytes(2), id="zip64-absent"
        ),
        pytest.param(
            bytes(60) + b"PK\x05\x06" + bytes(4) + b"\xff\xff" * 2 + b"\xff" * 8 + bytes(2),
            id="zip64-illisible",
        ),
    ],
)
def test_zip_repertoire_illisible(contenu: bytes) -> None:
    lignes = ooxml(contenu)
    assert valeurs_de(lignes) == {"ooxml.present": False}
    assert raisons(lignes) == [PARTIEL]


def test_zip_repertoire_trop_grand() -> None:
    fin = b"PK\x05\x06" + bytes(6) + b"\x01\x00" + (17 << 20).to_bytes(4, "little") + bytes(6)
    assert raisons(ooxml(bytes(17 << 20) + fin)) == [PARTIEL]


def test_zip_enregistrement_central_coupe() -> None:
    contenu = archive_brute(Brute(b"_rels/.rels", b"<x/>"))
    centrale = contenu.rindex(b"PK\x01\x02")
    fin = contenu.rindex(b"PK\x05\x06")
    # Nom annoncé plus long que le répertoire.
    long = contenu[: centrale + 28] + b"\xff\x00" + contenu[centrale + 30 :]
    assert raisons(ooxml(long)) == [PARTIEL]
    # Deux entrées annoncées, une seule écrite.
    deux = contenu[: fin + 10] + b"\x02\x00" + contenu[fin + 12 :]
    assert raisons(ooxml(deux)) == [PARTIEL]


def test_zip64_sans_champ_supplementaire() -> None:
    contenu = archive_brute(Brute(b"_rels/.rels", b"<x/>"), zip64=True)
    champ = contenu.rindex(b"\x01\x00\x08\x00")
    assert champ > contenu.rindex(b"PK\x01\x02")  # dans le répertoire central
    # Champ ZIP64 renommé : la position 0xFFFFFFFF n'a plus de quoi être lue.
    autre = contenu[:champ] + b"\x02\x00" + contenu[champ + 2 :]
    assert raisons(ooxml(autre)) == [PARTIEL]
    # Champ ZIP64 vide : la position manque.
    vide = contenu[:champ] + b"\x01\x00\x00\x00" + contenu[champ + 4 :]
    assert raisons(ooxml(vide)) == [PARTIEL]


# ODT


def utilisateur(nom: str, type_: str | None, valeur: str) -> str:
    """Propriété utilisateur (``meta:user-defined``), typée si ``type_`` est donné."""
    typee = "" if type_ is None else f' meta:value-type="{type_}"'
    return f'<meta:user-defined meta:name="{nom}"{typee}>{valeur}</meta:user-defined>'


@pytest.mark.exigence("ES-13")
def test_odf_meta() -> None:
    lignes = odf(
        odt_(
            meta(
                "<meta:generator>LibreOffice/25.2</meta:generator><dc:title>Titre</dc:title>"
                "<meta:keyword>mot1</meta:keyword><meta:keyword>mot2</meta:keyword>"
                "<meta:initial-creator>Jeanne</meta:initial-creator><dc:creator>Paul</dc:creator>"
                "<meta:printed-by>Imprimeur</meta:printed-by>"
                "<meta:creation-date>2026-11-01T10:20:30</meta:creation-date>"
                "<meta:editing-cycles>7</meta:editing-cycles>"
                "<meta:editing-duration>PT1H2M3S</meta:editing-duration>"
                '<meta:document-statistic meta:page-count="1" meta:word-count="x"/>'
                + utilisateur("Outil", None, "Générateur")
                + utilisateur("Note", "float", "4.5")
                + utilisateur("Part", "percentage", "50")
                + utilisateur("Relu", "boolean", "true")
                + utilisateur("Jour", "date", "2026-11-01")
                + '<dc:language xml:lang="fr">fr-FR</dc:language>',
                version="1.4",
            )
        )
    )
    assert valeurs_de(lignes) == {
        "odf.present": True,
        "odf.blocs": 1,
        "odf.version": "1.4",
        "odf.meta:generator": "LibreOffice/25.2",
        "odf.dc:title": "Titre",
        "odf.meta:keyword": ["mot1", "mot2"],
        "odf.meta:initial-creator": "Jeanne",
        "odf.dc:creator": "Paul",
        "odf.meta:printed-by": "Imprimeur",
        "odf.meta:creation-date": "2026-11-01T10:20:30",
        "odf.meta:editing-cycles": 7,
        "odf.meta:editing-duration": "PT1H2M3S",
        "odf.meta:document-statistic.meta:page-count": 1,
        "odf.meta:document-statistic.meta:word-count": "x",
        "odf.meta:user-defined.Outil": "Générateur",
        "odf.meta:user-defined.Note": 4.5,
        "odf.meta:user-defined.Part": 50.0,
        "odf.meta:user-defined.Relu": True,
        "odf.meta:user-defined.Jour": "2026-11-01",
        "odf.dc:language": "fr-FR",
    }
    assert identifiantes(lignes) == {
        "odf.meta:initial-creator": "metadonnee_nominative",
        "odf.dc:creator": "metadonnee_nominative",
        "odf.meta:printed-by": "metadonnee_nominative",
    }
    assert raisons(lignes) == []


def test_odf_sans_meta() -> None:
    lignes = odf(odt_(None, ("content.xml", b"<x/>")))
    assert valeurs_de(lignes) == {"odf.present": False}
    assert raisons(lignes) == []


@pytest.mark.exigence("ES-06")
def test_odf_references_ni_lues_ni_suivies() -> None:
    lignes = odf(
        odt_(
            meta(
                '<meta:template xlink:type="simple" xlink:href="http://pistage.invalid/m.ott" '
                'xlink:title="Modèle" meta:date="2026-11-01T00:00:00"/>'
                '<meta:auto-reload xlink:href="http://pistage.invalid/" meta:delay="PT5S"/>'
            )
        )
    )
    assert proprietes_de(lignes) == {
        "odf.version": "1.3",
        "odf.meta:template.meta:date": "2026-11-01T00:00:00",
        "odf.meta:auto-reload.meta:delay": "PT5S",
    }
    assert "pistage" not in str(lignes)


def test_odf_espace_inconnu() -> None:
    lignes = odf(odt_(meta('<e:x e:a="1">v</e:x>', espaces='xmlns:e="urn:autre"')))
    assert proprietes_de(lignes) == {
        "odf.version": "1.3",
        "odf.ns1:x.ns1:a": "1",
        "odf.ns1:x": "v",
        "odf.espace.ns1": "urn:autre",
    }


@pytest.mark.parametrize(
    "contenu",
    [
        pytest.param(
            meta('<meta:user-defined meta:value-type="float">1</meta:user-defined>'),
            id="propriete-sans-nom",
        ),
        pytest.param(b"<autre/>", id="racine-inconnue"),
        pytest.param(meta("").replace(b"<office:meta></office:meta>", b""), id="sans-office-meta"),
        pytest.param(meta("<dc:title>T</dc:title>")[:-30], id="coupe"),
    ],
)
def test_odf_meta_illisible(contenu: bytes) -> None:
    lignes = odf(odt_(contenu))
    assert valeurs_de(lignes)["odf.present"] is True
    assert raisons(lignes) == [PARTIEL]


def test_odf_meta_chiffre() -> None:
    # Entrée chiffrée par l'application (manifeste) : deflate ne la lit pas.
    lignes = odf(
        archive_brute(
            Brute(b"mimetype", b"x", methode=0), Brute(b"meta.xml", b"", donnees=b"\x07" * 40)
        )
    )
    assert valeurs_de(lignes) == {"odf.present": True, "odf.blocs": 1}
    assert raisons(lignes) == [PARTIEL]


def test_odf_archive_illisible() -> None:
    lignes = odf(b"PK\x03\x04" + bytes(40))
    assert valeurs_de(lignes) == {"odf.present": False}
    assert raisons(lignes) == [PARTIEL]


def test_odf_entree_illisible() -> None:
    lignes = odf(archive_brute(Brute(b"meta.xml", b"<x/>", drapeaux=1)))
    assert valeurs_de(lignes) == {"odf.present": True, "odf.blocs": 1}
    assert raisons(lignes) == [PARTIEL]


def test_odf_noms_sensibles_a_la_casse() -> None:
    # OpenDocument ne compare pas les noms sans casse : « META.XML » n'est pas l'entrée.
    lignes = odf(archive_brute(Brute(b"META.XML", meta("<dc:title>T</dc:title>"))))
    assert valeurs_de(lignes) == {"odf.present": False}


# Valeurs typées


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [(" 12 ", 12), ("+3", 3), ("1.0", "1.0"), ("", ""), ("1_000", "1_000")],
)
def test_entier_de_xml_schema(texte: str, attendu: object) -> None:
    assert proprietes.entier(texte) == attendu


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("1.5", 1.5),
        (".5", 0.5),
        ("-2E3", -2000.0),
        ("INF", "inf"),
        ("-INF", "-inf"),
        ("1_0", "1_0"),
    ],
)
def test_reel_de_xml_schema(texte: str, attendu: object) -> None:
    assert proprietes.reel(texte) == attendu


def test_archive_brute_relue_par_zipfile() -> None:
    # L'écrivain octet par octet des tests suit APPNOTE : zipfile relit ses archives, ZIP64 compris.
    for contenu in (
        archive_brute(Brute(b"a", b"x"), Brute(b"b", b"y", methode=0)),
        archive_brute(Brute(b"a", b"x"), zip64=True),
    ):
        with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
            assert archive.read("a") == b"x"
            assert archive.testzip() is None  # CRC justes
