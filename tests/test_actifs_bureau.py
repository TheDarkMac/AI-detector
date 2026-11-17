"""Éléments actifs d'un DOCX ou d'un ODT : module ``actifsbureau``, règles du catalogue
(complément bureautique de T52, ADR-0228 à ADR-0231).

Les documents synthétiques sont construits ici, sur les écrivains de ``bureautique.py`` ; les
échantillons de ``tests/donnees/actifsbureau`` viennent de LibreOffice, et ``oracle.json``
consigne ce qu'il en relit (``generer_actifsbureau.py``).
"""

import json
import socket
from html import escape
from pathlib import Path
from typing import Any

import pytest
from bureautique import (
    RELATIONS,
    TYPE_CORE,
    TYPE_DOCUMENT,
    Brute,
    archive_brute,
    core,
    meta,
    odt_,
    relations,
    zip_,
)
from metadonnees import identifiantes, raisons, resultats, valeurs_de

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import actifsbureau
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import Presentation, texte
from voight_kampff.rapport.modele import EtatTechnique

pytestmark = pytest.mark.exigence("F-62")

ECHANTILLONS = Path(__file__).parent / "donnees" / "actifsbureau"
METADONNEES = Path(__file__).parent / "donnees" / "metadonnees"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
PARTIEL = "format_partiel"
MANQUANTE = "reference_manquante"

T = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
STRICT = "http://purl.oclc.org/ooxml/officeDocument/relationships/"
MS = "http://schemas.microsoft.com/office/2006/relationships/"
MS7 = "http://schemas.microsoft.com/office/2007/relationships/"
EXTERNE = "External"
PISTAGE = "https://pistage.invalid/"

OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
ESPACES_ODF = " ".join(
    f'xmlns:{prefixe}="{espace}"'
    for prefixe, espace in (
        ("office", OFFICE),
        ("script", "urn:oasis:names:tc:opendocument:xmlns:script:1.0"),
        ("draw", "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"),
        ("text", "urn:oasis:names:tc:opendocument:xmlns:text:1.0"),
        ("style", "urn:oasis:names:tc:opendocument:xmlns:style:1.0"),
        ("form", "urn:oasis:names:tc:opendocument:xmlns:form:1.0"),
        ("xlink", "http://www.w3.org/1999/xlink"),
    )
)
MANIFESTE = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"

RIEN = {
    "actifsbureau.macros": 0,
    "actifsbureau.evenements": 0,
    "actifsbureau.objets": 0,
    "actifsbureau.externes": 0,
    "actifsbureau.automatiques": 0,
}


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def lignes(contenu: bytes, format_: str = "docx") -> list[dict[str, Any]]:
    return resultats("actifsbureau", contenu, format_)


def obs(contenu: bytes, format_: str = "docx") -> dict[str, Any]:
    return valeurs_de(lignes(contenu, format_))


def familles(valeurs_: dict[str, Any]) -> dict[str, Any]:
    """Les observations, sans le compte des parties lues."""
    return {n: v for n, v in valeurs_.items() if n != "actifsbureau.parties"}


def chemins(lignes_: list[dict[str, Any]]) -> list[str]:
    return [n["non_menee"]["localisation"]["chemin"] for n in lignes_ if n["type"] == "non_menee"]


# DOCX


def docx(*parties: tuple[str, bytes], paquet: bytes | None = None) -> bytes:
    """Paquet, partie principale ``word/document.xml`` et les parties données."""
    if paquet is None:
        paquet = relations((TYPE_CORE, "docProps/core.xml"), (TYPE_DOCUMENT, "word/document.xml"))
    return zip_(
        ("[Content_Types].xml", b"<Types/>"),
        ("_rels/.rels", paquet),
        ("docProps/core.xml", core("")),
        ("word/document.xml", b"<w/>"),
        *parties,
    )


def du_document(*liens: tuple[str, str] | tuple[str, str, str]) -> tuple[str, bytes]:
    return ("word/_rels/document.xml.rels", relations(*liens))


def test_docx_sans_element_actif() -> None:
    resultat = lignes(docx(du_document((f"{T}styles", "styles.xml")), ("word/styles.xml", b"<s/>")))
    assert valeurs_de(resultat) == {"actifsbureau.parties": 2} | RIEN
    assert raisons(resultat) == []
    assert identifiantes(resultat) == {}


def test_docx_macros_vba_et_ruban() -> None:
    # Projet VBA désigné par le document, ses données (vbaData) par le projet ; ruban désigné par
    # le paquet ([MS-CUSTOMUI], 2006 et 2007) ; le projet n'est pas ouvert.
    contenu = docx(
        du_document((f"{MS}vbaProject", "vbaProject.bin")),
        ("word/vbaProject.bin", b"\xd0\xcf\x11\xe0 pas lu"),
        ("word/_rels/vbaProject.bin.rels", relations((f"{MS}wordVbaData", "vbaData.xml"))),
        ("word/vbaData.xml", b"<d/>"),
        ("customUI/customUI.xml", b"<c/>"),
        ("customUI/customUI14.xml", b"<c/>"),
        paquet=relations(
            (TYPE_DOCUMENT, "word/document.xml"),
            (f"{MS}ui/extensibility", "customUI/customUI.xml"),
            (f"{MS7}ui/extensibility", "customUI/customUI14.xml"),
        ),
    )
    valeurs_ = obs(contenu)
    assert familles(valeurs_) == RIEN | {
        "actifsbureau.macros": 3,
        "actifsbureau.macros.natures": ["VBA", "ruban"],
    }
    assert valeurs_["actifsbureau.parties"] == 3  # paquet, document, projet VBA


def test_docx_objets_incorpores() -> None:
    # ActiveX, OLE, document incorporé ; celui d'un graphique en porte les données : pas compté.
    contenu = docx(
        du_document(
            (f"{T}control", "activeX/activeX1.xml"),
            (f"{T}oleObject", "embeddings/oleObject1.bin"),
            (f"{T}package", "embeddings/Classeur.xlsx"),
            (f"{T}chart", "charts/chart1.xml"),
        ),
        ("word/activeX/activeX1.xml", b"<a/>"),
        (
            "word/activeX/_rels/activeX1.xml.rels",
            relations((f"{MS}activeXControlBinary", "activeX1.bin")),
        ),
        ("word/activeX/activeX1.bin", b"\x00"),
        ("word/embeddings/oleObject1.bin", b"\x00"),
        ("word/embeddings/Classeur.xlsx", b"\x00"),
        ("word/charts/chart1.xml", b"<c/>"),
        ("word/charts/_rels/chart1.xml.rels", relations((f"{T}package", "../embeddings/D.xlsx"))),
        ("word/embeddings/D.xlsx", b"\x00"),
    )
    assert familles(obs(contenu)) == RIEN | {
        "actifsbureau.objets": 3,
        "actifsbureau.objets.natures": ["OLE", "ActiveX", "paquet"],
    }


@pytest.mark.exigence("ES-06", "NF-01")
def test_docx_relations_externes(monkeypatch: pytest.MonkeyPatch) -> None:
    # Modèle distant (M-14), image liée, cadre, objet lié, source de données d'un publipostage,
    # sous-document, lien, type inconnu : comptés par leur type, jamais suivis ni observés.
    def interdit(*_arguments: object, **_options: object) -> None:
        raise AssertionError("connexion réseau")

    monkeypatch.setattr(socket, "socket", interdit)
    monkeypatch.setattr(socket, "create_connection", interdit)
    contenu = docx(
        du_document(
            (f"{T}settings", "settings.xml"),
            (f"{T}webSettings", "webSettings.xml"),
            (f"{T}image", f"{PISTAGE}pixel.png", EXTERNE),
            (f"{T}oleObject", "mhtml:http://pistage.invalid/!x", EXTERNE),
            (f"{T}subDocument", "file:///C:/partage/tome2.docx", EXTERNE),
            (f"{T}hyperlink", f"{PISTAGE}page", EXTERNE),
            (f"{T}hyperlink", f"{PISTAGE}autre", EXTERNE),
            ("http://exemple.invalid/inconnu", f"{PISTAGE}x", EXTERNE),
        ),
        ("word/settings.xml", b"<s/>"),
        (
            "word/_rels/settings.xml.rels",
            relations(
                (f"{T}attachedTemplate", f"{PISTAGE}modele.dotm", EXTERNE),
                (f"{T}mailMergeSource", "file:///C:/donnees.xlsx", EXTERNE),
                (f"{T}recipientData", "recipientData.xml"),
            ),
        ),
        ("word/recipientData.xml", b"<r/>"),
        ("word/webSettings.xml", b"<w/>"),
        ("word/_rels/webSettings.xml.rels", relations((f"{T}frame", f"{PISTAGE}f", EXTERNE))),
    )
    resultat = lignes(contenu)
    assert familles(valeurs_de(resultat)) == RIEN | {
        "actifsbureau.externes": 9,
        "actifsbureau.externes.natures": [
            "modèle",
            "image",
            "cadre",
            "objet",
            "source de données",
            "sous-document",
            "lien",
            "autre",
        ],
        "actifsbureau.externes.declencheurs": ["ouverture", "utilisateur"],
        "actifsbureau.automatiques": 5,
        "actifsbureau.automatiques.natures": [
            "modèle",
            "image",
            "cadre",
            "objet",
            "source de données",
        ],
        "actifsbureau.automatiques.declencheurs": ["ouverture"],
    }
    assert raisons(resultat) == []
    assert "pistage" not in str(resultat)
    assert "partage" not in str(resultat)


def test_docx_espace_strict_et_cibles() -> None:
    # Espace strict ; cible absolue, relative au-dessus du dossier et même de la racine,
    # encodée, de casse différente (OPC) ; une partie désignée deux fois n'est lue qu'une fois.
    contenu = docx(
        (
            "word/_rels/document.xml.rels",
            relations(
                (f"{STRICT}vbaProject", "/word/Projet%20VBA.bin"),
                (f"{STRICT}settings", "../../word/./SETTINGS.xml"),
                (f"{STRICT}settings", "settings.xml"),
            ),
        ),
        ("word/projet vba.bin", b"\x00"),
        ("word/settings.xml", b"<s/>"),
        (
            "word/_rels/settings.xml.rels",
            relations(
                (f"{STRICT}attachedTemplate", f"{PISTAGE}m.dotm", EXTERNE),
                (f"{STRICT}officeDocument", "document.xml"),
            ),
        ),
        paquet=relations((f"{STRICT}officeDocument", "word/document.xml")),
    )
    valeurs_ = obs(contenu)
    assert valeurs_["actifsbureau.macros.natures"] == ["VBA"]
    assert valeurs_["actifsbureau.automatiques.natures"] == ["modèle"]
    assert valeurs_["actifsbureau.parties"] == 3


def test_docx_relations_du_paquet_non_suivies() -> None:
    # Propriétés, vignette : rien d'actif ; une partie de propriétés qui aurait des relations
    # vers un projet VBA n'est pas suivie.
    contenu = docx(
        ("docProps/_rels/core.xml.rels", relations((f"{MS}vbaProject", "../word/vba.bin"))),
        ("word/vba.bin", b"\x00"),
    )
    assert familles(obs(contenu)) == RIEN


def test_docx_partie_absente() -> None:
    # Projet VBA désigné mais absent de l'archive : référence manquante, rien de compté.
    resultat = lignes(docx(du_document((f"{MS}vbaProject", "vbaProject.bin"))))
    assert familles(valeurs_de(resultat)) == RIEN
    assert raisons(resultat) == [MANQUANTE]
    assert chemins(resultat) == ["VBA (partie absente)"]


@pytest.mark.parametrize(
    "relations_",
    [
        b"<Relationships",  # XML mal formé
        b"<Autres/>",  # racine inconnue
        relations((f"{T}settings", "")),  # sans cible
    ],
)
def test_docx_relations_illisibles(relations_: bytes) -> None:
    resultat = lignes(docx(("word/_rels/document.xml.rels", relations_)))
    assert raisons(resultat) == [PARTIEL]
    assert familles(valeurs_de(resultat)) == RIEN


def test_docx_element_inconnu_dans_les_relations() -> None:
    liens = (
        f'<Relationships xmlns="{RELATIONS}"><Autre/>'
        f'<Relationship Id="r" Type="{MS}vbaProject" Target="v.bin"/></Relationships>'
    ).encode()
    resultat = lignes(docx(("word/_rels/document.xml.rels", liens), ("word/v.bin", b"\x00")))
    assert raisons(resultat) == []
    assert valeurs_de(resultat)["actifsbureau.macros"] == 1


def test_docx_entrees_illisibles() -> None:
    # Relations en double, relations dont la compression ne se lit pas, partie active en
    # double : chacune non menée, les autres parties lues.
    paquet = relations((TYPE_DOCUMENT, "word/document.xml"), (TYPE_DOCUMENT, "word/autre.xml"))
    contenu = archive_brute(
        Brute(b"[Content_Types].xml", b"<Types/>"),
        Brute(b"_rels/.rels", paquet),
        Brute(b"word/document.xml", b"<w/>"),
        Brute(b"word/autre.xml", b"<w/>"),
        Brute(b"word/_rels/document.xml.rels", relations((f"{MS}vbaProject", "v.bin"))),
        Brute(b"word/_rels/document.xml.rels", relations()),
        Brute(b"word/_rels/autre.xml.rels", b"x", donnees=b"\xff\xff\xff"),
    )
    resultat = lignes(contenu)
    assert raisons(resultat) == [PARTIEL, PARTIEL]
    assert [c.split(" (")[0] for c in chemins(resultat)] == [
        "word/_rels/document.xml.rels",
        "word/_rels/autre.xml.rels",
    ]
    vba = relations((f"{MS}vbaProject", "v.bin"))
    contenu = archive_brute(
        Brute(b"[Content_Types].xml", b"<Types/>"),
        Brute(b"_rels/.rels", relations((TYPE_DOCUMENT, "word/document.xml"))),
        Brute(b"word/document.xml", b"<w/>"),
        Brute(b"word/_rels/document.xml.rels", vba),
        Brute(b"word/v.bin", b"\x00"),
        Brute(b"word/V.bin", b"\x00"),
    )
    resultat = lignes(contenu)
    assert raisons(resultat) == [PARTIEL]
    assert valeurs_de(resultat)["actifsbureau.macros"] == 0


def test_archive_illisible() -> None:
    resultat = lignes(b"PK pas une archive")
    assert raisons(resultat) == [PARTIEL]
    assert valeurs_de(resultat) == {}


def test_docx_limites(monkeypatch: pytest.MonkeyPatch) -> None:
    liens = du_document(*((f"{T}hyperlink", f"{PISTAGE}{i}", EXTERNE) for i in range(3)))
    monkeypatch.setattr(actifsbureau, "ELEMENTS_MAX", 2)
    valeurs_ = obs(docx(liens))
    assert (valeurs_["actifsbureau.externes"], valeurs_["actifsbureau.recherche_coupee"]) == (
        2,
        True,
    )
    monkeypatch.setattr(actifsbureau, "PARTIES_MAX", 1)
    valeurs_ = obs(docx(liens))
    assert (valeurs_["actifsbureau.parties"], valeurs_["actifsbureau.externes"]) == (1, 0)
    assert valeurs_["actifsbureau.recherche_coupee"] is True


def budget_bientot_epuise(monkeypatch: pytest.MonkeyPatch, apres: int) -> None:
    """Le budget paraît presque épuisé après ``apres`` consultations du compte des objets."""
    appels = {"n": 0}

    def objets_(_contexte: Contexte) -> int:
        appels["n"] += 1
        return OBJETS_MAX if appels["n"] > apres else 0

    monkeypatch.setattr(Contexte, "objets", property(objets_))


@pytest.mark.parametrize("apres", [0, 1])
def test_docx_arret_avant_budget(monkeypatch: pytest.MonkeyPatch, apres: int) -> None:
    # Arrêt avant le paquet, ou après lui : les observations déjà faites sont envoyées.
    budget_bientot_epuise(monkeypatch, apres)
    resultat = lignes(docx(du_document((f"{T}hyperlink", PISTAGE, EXTERNE))))
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["actifsbureau.arret_avant_budget"] is True
    assert valeurs_["actifsbureau.parties"] == apres
    assert raisons(resultat) == []


# ODT


def contenu_odt(corps: str, *, racine: str = "document-content", scripts: str = "") -> bytes:
    return (
        f"<office:{racine} {ESPACES_ODF}><office:scripts>{scripts}</office:scripts>"
        f"<office:body><office:text>{corps}</office:text></office:body></office:{racine}>"
    ).encode()


def evenement(nom: str) -> str:
    return (
        f'<script:event-listener script:language="ooo:script" script:event-name="{nom}" '
        'xlink:href="vnd.sun.star.script:Standard.Module1.Main?language=Basic&amp;location=document"/>'
    )


def manifeste(*entrees: tuple[str, str], chiffre: bool = False) -> tuple[str, bytes]:
    lignes_ = "".join(
        f'<manifest:file-entry manifest:full-path="{chemin}" manifest:media-type="{type_}">'
        + ("<manifest:encryption-data/>" if chiffre else "")
        + "</manifest:file-entry>"
        for chemin, type_ in entrees
    )
    texte_ = f'<manifest:manifest xmlns:manifest="{MANIFESTE}">{lignes_}</manifest:manifest>'
    return ("META-INF/manifest.xml", texte_.encode())


def odt(*autres: tuple[str, bytes], meta_: bytes | None = None) -> bytes:
    return odt_(meta_, *autres)


def test_odt_sans_element_actif() -> None:
    resultat = lignes(
        odt(("content.xml", contenu_odt("<text:p>Texte</text:p>")), meta_=meta("")), "odt"
    )
    assert valeurs_de(resultat) == {"actifsbureau.parties": 2} | RIEN
    assert raisons(resultat) == []


def test_odt_macros_par_les_entrees() -> None:
    # Deux bibliothèques Basic qui ont un module ; une qui n'a que ses index ; des boîtes de
    # dialogue ; des scripts Python, JavaScript et d'un langage inconnu. Ni noms ni code lus.
    contenu = odt(
        ("Basic/script-lc.xml", b"<l/>"),
        ("Basic/Standard/script-lb.xml", b"<l/>"),
        ("Basic/Standard/Module1.xml", b"<m/>"),
        ("Basic/Standard/Module2.xml", b"<m/>"),
        ("Basic/Outils/Module1.xml", b"<m/>"),
        ("Basic/Vide/script-lb.xml", b"<l/>"),
        ("Basic/Vide/dialog-lb.xml", b"<l/>"),
        ("Basic/Vide/Sous/Module.xml", b"<m/>"),
        ("Basic/Module.xml", b"<m/>"),
        ("Dialogs/Standard/Dialog1.xml", b"<d/>"),
        ("Scripts/", b""),
        ("Scripts/python/", b""),
        ("Scripts/python/macro.py", b"print(1)"),
        ("Scripts/python/lib/aide.py", b"x"),
        ("Scripts/JavaScript/m.js", b"x"),
        ("Scripts/cobol/m.cbl", b"x"),
    )
    assert familles(obs(contenu, "odt")) == RIEN | {
        "actifsbureau.macros": 5,
        "actifsbureau.macros.natures": ["Basic", "Python", "JavaScript", "autre"],
    }


def test_odt_evenements() -> None:
    # Événements du document sous office:scripts de la racine, dans content.xml et styles.xml ;
    # événement d'un contrôle de formulaire ; lien et bouton qui appellent une macro.
    corps = (
        "<form:button><office:event-listeners>"
        f"{evenement('dom:load')}</office:event-listeners></form:button>"
        '<text:p><text:a xlink:href="macro:///Standard.Module1.Main">x</text:a>'
        '<text:a xlink:href="vnd.sun.star.script:S.M.m?language=Basic">y</text:a></text:p>'
    )
    scripts = f"<office:event-listeners>{evenement('dom:load')}{evenement('office:save')}"
    scripts += f"{evenement('office:view-created')}</office:event-listeners>"
    styles = f"<office:event-listeners>{evenement('office:print')}</office:event-listeners>"
    contenu = odt(
        ("content.xml", contenu_odt(corps, scripts=scripts)),
        ("styles.xml", contenu_odt("", racine="document-styles", scripts=styles)),
    )
    resultat = lignes(contenu, "odt")
    assert familles(valeurs_de(resultat)) == RIEN | {
        "actifsbureau.evenements": 7,
        "actifsbureau.evenements.natures": ["macro"],
        "actifsbureau.evenements.declencheurs": ["ouverture", "document", "utilisateur"],
        "actifsbureau.automatiques": 4,
        "actifsbureau.automatiques.natures": ["macro"],
        "actifsbureau.automatiques.declencheurs": ["ouverture", "document"],
    }
    assert "Module1" not in str(resultat)


def test_odt_objets() -> None:
    # OLE, applet, module externe ; document incorporé compté sauf graphique ou formule, compté
    # aussi s'il manque au manifeste ; un objet lié hors de l'archive est une référence externe.
    corps = (
        '<draw:frame><draw:object-ole xlink:href="./Object 1"/></draw:frame>'
        '<draw:frame><draw:applet draw:code="A.class"/></draw:frame>'
        '<draw:frame><draw:plugin xlink:href="Medias/v.mp4"/></draw:frame>'
        '<draw:frame><draw:object xlink:href="./Object 2"/></draw:frame>'
        '<draw:frame><draw:object xlink:href="./Object 3"/></draw:frame>'
        '<draw:frame><draw:object xlink:href="Object 4/"/></draw:frame>'
        '<draw:frame><draw:object xlink:href="./Object 5"/></draw:frame>'
        '<draw:frame><draw:object xlink:href="../voisin.ods"/></draw:frame>'
        "<draw:frame><draw:object/></draw:frame>"
    )
    contenu = odt(
        manifeste(
            ("/", "application/vnd.oasis.opendocument.text"),
            ("Object 2/", "application/vnd.oasis.opendocument.spreadsheet"),
            ("Object 3/", "application/vnd.oasis.opendocument.chart"),
            ("Object 4/", "application/vnd.oasis.opendocument.formula"),
        ),
        ("content.xml", contenu_odt(corps)),
    )
    valeurs_ = obs(contenu, "odt")
    assert familles(valeurs_) == RIEN | {
        "actifsbureau.objets": 5,
        "actifsbureau.objets.natures": ["OLE", "document", "applet", "plugin"],
        "actifsbureau.externes": 1,
        "actifsbureau.externes.natures": ["objet"],
        "actifsbureau.externes.declencheurs": ["ouverture"],
        "actifsbureau.automatiques": 1,
        "actifsbureau.automatiques.natures": ["objet"],
        "actifsbureau.automatiques.declencheurs": ["ouverture"],
    }
    assert valeurs_["actifsbureau.parties"] == 2


@pytest.mark.exigence("ES-06", "NF-01")
def test_odt_references_hors_de_l_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    def interdit(*_arguments: object, **_options: object) -> None:
        raise AssertionError("connexion réseau")

    monkeypatch.setattr(socket, "socket", interdit)
    monkeypatch.setattr(socket, "create_connection", interdit)
    externes = (
        f'<draw:image xlink:href="{PISTAGE}i.png"/>',
        '<draw:image xlink:href="../../tmp/partage/logo.png"/>',
        '<draw:floating-frame xlink:href="//serveur/partage/page.html"/>',
        '<text:section><text:section-source xlink:href="\\\\serveur\\partage\\s.odt"/>'
        "</text:section>",
        '<text:a xlink:href="C:\\partage\\notes.odt">x</text:a>',
        f'<draw:a xlink:href="{PISTAGE}a">x</draw:a>',
        f'<form:button xlink:href="{PISTAGE}b"/>',
        f'<text:script xlink:href="{PISTAGE}s.js"/>',
        '<text:dde-connection-decl office:automatic-update="true" office:dde-application="X"/>',
        '<text:section><office:dde-source office:dde-application="X"/></text:section>',
    )
    internes = (
        '<draw:image xlink:href="Pictures/1.png"/>',
        '<draw:image xlink:href="./ObjectReplacements/Object 1"/>',
        '<draw:image xlink:href="a/../b.png"/>',
        '<draw:image xlink:href="vnd.sun.star.Package:Pictures/2.png"/>',
        '<draw:image xlink:href="vnd.sun.star.GraphicObject:10000"/>',
        '<text:a xlink:href="#Titre">x</text:a>',
        '<text:a xlink:href="1:2">x</text:a>',
        '<text:a xlink:href="é:x">x</text:a>',
        '<text:a xlink:href="">x</text:a>',
    )
    styles = f'<style:background-image xlink:href="{PISTAGE}fond.png"/>'
    styles += f'<draw:fill-image xlink:href="{PISTAGE}motif.png"/>'
    metadonnees = meta(
        f'<meta:template xlink:href="{PISTAGE}modele.ott"/>'
        f'<meta:auto-reload xlink:href="{PISTAGE}r.odt" meta:delay="PT1M"/>'
        '<meta:auto-reload meta:delay="PT1M"/>'
    )
    contenu = odt(
        ("content.xml", contenu_odt("".join(externes + internes))),
        ("styles.xml", contenu_odt(styles, racine="document-styles")),
        meta_=metadonnees,
    )
    resultat = lignes(contenu, "odt")
    assert familles(valeurs_de(resultat)) == RIEN | {
        "actifsbureau.externes": 14,
        "actifsbureau.externes.natures": [
            "modèle",
            "image",
            "cadre",
            "section",
            "rechargement",
            "DDE",
            "lien",
            "autre",
        ],
        "actifsbureau.externes.declencheurs": ["ouverture", "utilisateur"],
        "actifsbureau.automatiques": 9,
        "actifsbureau.automatiques.natures": [
            "modèle",
            "image",
            "cadre",
            "section",
            "rechargement",
            "DDE",
        ],
        "actifsbureau.automatiques.declencheurs": ["ouverture"],
    }
    assert raisons(resultat) == []
    assert "pistage" not in str(resultat)
    assert "partage" not in str(resultat)


def test_odt_chiffre() -> None:
    # Document protégé par mot de passe : manifeste en clair, parties chiffrées illisibles ;
    # les bibliothèques Basic se comptent par les noms des entrées.
    contenu = odt(
        manifeste(("content.xml", "text/xml"), chiffre=True),
        ("content.xml", b"\x8f\x00 chiffr\xe9"),
        ("Basic/Standard/Module1.xml", b"\x8f"),
    )
    resultat = lignes(contenu, "odt")
    valeurs_ = valeurs_de(resultat)
    assert (valeurs_["actifsbureau.chiffre"], valeurs_["actifsbureau.macros"]) == (True, 1)
    assert raisons(resultat) == [PARTIEL]
    assert chemins(resultat) == ["content.xml"]


def test_odt_parties_illisibles() -> None:
    # Manifeste mal formé, entrée sans chemin ; content.xml en double, styles.xml dont la
    # compression ne se lit pas, manifeste en double.
    contenu = odt(
        (
            "META-INF/manifest.xml",
            f'<manifest:manifest xmlns:manifest="{MANIFESTE}"><manifest:file-entry/>'.encode(),
        ),
    )
    resultat = lignes(contenu, "odt")
    assert raisons(resultat) == [PARTIEL]
    assert chemins(resultat) == ["META-INF/manifest.xml"]
    contenu = archive_brute(
        Brute(b"mimetype", b"application/vnd.oasis.opendocument.text", methode=0),
        Brute(b"META-INF/manifest.xml", b"<m/>"),
        Brute(b"META-INF/manifest.xml", b"<m/>"),
        Brute(b"content.xml", contenu_odt("")),
        Brute(b"content.xml", contenu_odt("")),
        Brute(b"styles.xml", b"x", donnees=b"\xff\xff\xff"),
        Brute(b"meta.xml", meta("")),
    )
    resultat = lignes(contenu, "odt")
    assert raisons(resultat) == [PARTIEL, PARTIEL, PARTIEL]
    assert [c.split(" (")[0] for c in chemins(resultat)] == [
        "META-INF/manifest.xml",
        "content.xml",
        "styles.xml",
    ]
    assert valeurs_de(resultat)["actifsbureau.parties"] == 1  # meta.xml


def test_odt_manifeste_illisible() -> None:
    contenu = archive_brute(
        Brute(b"mimetype", b"application/vnd.oasis.opendocument.text", methode=0),
        Brute(b"META-INF/manifest.xml", b"x", donnees=b"\xff\xff\xff"),
    )
    resultat = lignes(contenu, "odt")
    assert raisons(resultat) == [PARTIEL]
    assert valeurs_de(resultat)["actifsbureau.parties"] == 0


def test_odt_xml_mal_forme() -> None:
    resultat = lignes(odt(("content.xml", contenu_odt("<text:p>")[:-20])), "odt")
    assert raisons(resultat) == [PARTIEL]


def test_odt_encodage_qu_expat_ne_lit_pas() -> None:
    # Encodage inconnu : lecture partielle, pas d'erreur du module (ERR-0012).
    declaration = b'<?xml version="1.0" encoding="UTF-C"?>'
    resultat = lignes(odt(("content.xml", declaration + contenu_odt("<draw:applet/>"))), "odt")
    assert raisons(resultat) == [PARTIEL]


@pytest.mark.parametrize("apres", [0, 1, 4])
def test_odt_arret_avant_budget(monkeypatch: pytest.MonkeyPatch, apres: int) -> None:
    # Arrêt avant le manifeste, dans le manifeste, ou dans content.xml : pas de partie non menée
    # pour l'arrêt, les observations déjà faites sont envoyées.
    contenu = odt(
        manifeste(("/", "application/vnd.oasis.opendocument.text")),
        ("content.xml", contenu_odt("<draw:applet/><draw:applet/><draw:applet/>")),
    )
    budget_bientot_epuise(monkeypatch, apres)
    resultat = lignes(contenu, "odt")
    assert valeurs_de(resultat)["actifsbureau.arret_avant_budget"] is True
    assert raisons(resultat) == []


# Échantillons, oracle et règles


ATTENDUS = {
    "macros.odt": {"R-ACTIFSBUREAU-001", "R-ACTIFSBUREAU-002"},
    "liens.odt": {"R-ACTIFSBUREAU-002", "R-ACTIFSBUREAU-004"},
    "liens.docx": {"R-ACTIFSBUREAU-002", "R-ACTIFSBUREAU-004"},
    "objet.odt": {"R-ACTIFSBUREAU-003"},
    "objet.docx": {"R-ACTIFSBUREAU-003"},
}
ORDINAIRES = ("document.docx", "document.odt")
"""Échantillons de ``tests/donnees/metadonnees`` (LibreOffice), sans élément actif."""


def test_echantillons_et_oracle_concordent() -> None:
    assert set(ORACLE) - {"outils"} == set(ATTENDUS)


@pytest.mark.parametrize("nom", sorted(ATTENDUS))
def test_echantillons_compares_a_libreoffice(nom: str) -> None:
    # LibreOffice relit chaque échantillon : bibliothèques Basic, événements du document et des
    # contrôles, modèle, rechargement, sections et images liées, objets incorporés, liens.
    attendu = ORACLE[nom]
    resultat = lignes((ECHANTILLONS / nom).read_bytes(), nom.rsplit(".", 1)[1])
    valeurs_ = valeurs_de(resultat)
    assert raisons(resultat) == []
    natures = valeurs_.get("actifsbureau.macros.natures", [])
    assert natures.count("Basic") == valeurs_["actifsbureau.macros"]
    assert valeurs_["actifsbureau.macros"] == attendu["bibliotheques_basic"]
    evenements = len(attendu["evenements_du_document"]) + attendu["evenements_des_controles"]
    assert valeurs_["actifsbureau.evenements"] == evenements
    externes = valeurs_.get("actifsbureau.externes.natures", [])
    for nature, cle in (("modèle", "modele"), ("rechargement", "rechargement")):
        assert (nature in externes) == attendu[cle]
    assert ("section" in externes) == (attendu["sections_liees"] > 0)
    assert ("image" in externes) == (attendu["images_liees"] > 0)
    assert ("lien" in externes) == (attendu["liens"] > 0)
    comptes = attendu["sections_liees"] + attendu["images_liees"] + attendu["liens"]
    comptes += attendu["modele"] + attendu["rechargement"]
    assert valeurs_["actifsbureau.externes"] == comptes
    assert valeurs_["actifsbureau.objets"] == attendu["objets_incorpores"]


@pytest.mark.parametrize("nom", ORDINAIRES)
def test_documents_ordinaires(nom: str) -> None:
    resultat = lignes((METADONNEES / nom).read_bytes(), nom.rsplit(".", 1)[1])
    assert familles(valeurs_de(resultat)) == RIEN
    assert raisons(resultat) == []


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("actifsbureau")
    sources = {n: ECHANTILLONS / n for n in ATTENDUS} | {n: METADONNEES / n for n in ORDINAIRES}
    trouvees = {}
    for nom, source in sources.items():
        chemin = dossier / nom
        chemin.write_bytes(source.read_bytes())
        trouvees[nom] = analyser(chemin)
    return trouvees


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "actifsbureau"}


@pytest.mark.parametrize(
    ("nom", "attendues"), [*ATTENDUS.items(), *((n, set()) for n in ORDINAIRES)]
)
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques}
    assert etats["actifsbureau"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues


def test_phrases_des_constats(analyses: dict[str, Analyse]) -> None:
    attendus = {
        "macros.odt": (
            "Le document porte 1 ensemble(s) de macros (Basic) : l'outil ne les a ni lus ni "
            "exécutés.",
            "Le document porte 2 élément(s) qu'un traitement de texte déclenche ou charge sans "
            "geste de l'utilisateur (déclencheurs : ouverture, document ; natures : macro) : "
            "l'outil n'en a exécuté ni chargé aucun.",
        ),
        "liens.odt": (
            "Le document désigne 5 ressource(s) hors de son archive (modèle, image, section, "
            "rechargement, lien) : l'outil n'en a suivi aucune.",
        ),
        "objet.docx": (
            "Le document porte 1 objet(s) incorporé(s) qu'un autre programme active ou ouvre "
            "(paquet) : l'outil n'en a ouvert aucun.",
        ),
    }
    for nom, phrases in attendus.items():
        page = export.exporter_html(analyses[nom])
        for phrase in phrases:
            assert escape(phrase) in page, phrase


@pytest.mark.exigence("ES-06", "NF-01")
def test_aucune_adresse_au_rapport(analyses: dict[str, Analyse]) -> None:
    # Ni l'adresse du lien et du rechargement, ni le chemin des fichiers liés (ADR-0230).
    for nom in ("liens.odt", "liens.docx"):
        page = export.exporter_html(analyses[nom])
        document = json.dumps(export.exporter_json(analyses[nom]), ensure_ascii=False)
        for trace in ("example.org", "logo.png", "section.odt", "modele.ott"):
            assert trace not in page, (nom, trace)
            assert trace not in document, (nom, trace)


def test_controle_avant_publication_complet(analyses: dict[str, Analyse]) -> None:
    # Le module ne lit aucune métadonnée identifiante : il est parmi les modules sans
    # métadonnées du résumé (ADR-0158, ADR-0231).
    analyse = analyses["liens.odt"]
    assert "actifsbureau" not in {n.module for n in analyse.non_menees}
    assert texte("resume.publication_incomplete") not in Presentation(analyse, ()).publication()
