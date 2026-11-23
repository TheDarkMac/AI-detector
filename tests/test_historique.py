"""Historique d'édition d'un DOCX ou d'un ODT : module ``historique``, règles du catalogue
(T81, ADR-0248 à ADR-0251).

Les documents synthétiques sont construits ici, sur les écrivains de ``bureautique.py`` : les DOCX
« à la manière de Word », avec identifiants de session, parce que LibreOffice n'en écrit pas dans
un DOCX. Les échantillons de ``tests/donnees/historique`` viennent de LibreOffice, écrits en
trois sessions, et ``oracle.json`` consigne ce qu'il en relit (``generer_historique.py``).
"""

import json
from html import escape
from pathlib import Path
from typing import Any

import pytest
from bureautique import (
    TYPE_APP,
    TYPE_CORE,
    TYPE_DOCUMENT,
    Brute,
    app,
    archive_brute,
    core,
    meta,
    odt_,
    relations,
    zip_,
)
from metadonnees import identifiantes, raisons, resultats, valeurs_de

from voight_kampff._travail import garde
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import historique
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import Presentation, texte
from voight_kampff.rapport.modele import EtatTechnique

pytestmark = pytest.mark.exigence("F-71")

ECHANTILLONS = Path(__file__).parent / "donnees" / "historique"
METADONNEES = Path(__file__).parent / "donnees" / "metadonnees"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
PARTIEL = "format_partiel"
MANQUANTE = "reference_manquante"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_STRICT = "http://purl.oclc.org/ooxml/wordprocessingml/main"
T = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
STRICT = "http://purl.oclc.org/ooxml/officeDocument/relationships/"
DCTERMS = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'

ESPACES_ODF = " ".join(
    f'xmlns:{prefixe}="{espace}"'
    for prefixe, espace in (
        ("office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
        ("text", "urn:oasis:names:tc:opendocument:xmlns:text:1.0"),
        ("style", "urn:oasis:names:tc:opendocument:xmlns:style:1.0"),
        ("draw", "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"),
        ("svg", "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"),
        ("dc", "http://purl.org/dc/elements/1.1/"),
        ("officeooo", "http://openoffice.org/2009/office"),
    )
)


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def lignes(contenu: bytes, format_: str = "docx") -> list[dict[str, Any]]:
    return resultats("historique", contenu, format_)


def obs(contenu: bytes, format_: str = "docx") -> dict[str, Any]:
    return valeurs_de(lignes(contenu, format_))


# DOCX construits


def corps(contenu: str, espace: str = W) -> bytes:
    return f'<w:document xmlns:w="{espace}"><w:body>{contenu}</w:body></w:document>'.encode()


def p(*courses: str, defaut: str | None = None) -> str:
    """Paragraphe, et sa session par défaut (``w:rsidRDefault``)."""
    attribut = "" if defaut is None else f' w:rsidRDefault="{defaut}"'
    return f"<w:p{attribut}>{''.join(courses)}</w:p>"


def r(texte_: str, rsid: str | None = None) -> str:
    """Course, et sa session (``w:rsidR``)."""
    attribut = "" if rsid is None else f' w:rsidR="{rsid}"'
    return f"<w:r{attribut}><w:t>{texte_}</w:t></w:r>"


def marque(nom: str, contenu: str = "", *, auteur: str = "A", date: str = "") -> str:
    attributs = f' w:id="1" w:author="{auteur}"' + (f' w:date="{date}"' if date else "")
    return f"<w:{nom}{attributs}>{contenu}</w:{nom}>"


def reglages(*rsids: str, racine: str | None = None, espace: str = W) -> bytes:
    elements = "" if racine is None else f'<w:rsidRoot w:val="{racine}"/>'
    elements += "".join(f'<w:rsid w:val="{rsid}"/>' for rsid in rsids)
    return (
        f'<w:settings xmlns:w="{espace}"><w:zoom w:percent="100"/>'
        f"<w:rsids>{elements}</w:rsids></w:settings>"
    ).encode()


def commentaires(*auteurs_dates: tuple[str, str], espace: str = W) -> bytes:
    elements = "".join(
        f'<w:comment w:id="{rang}" w:author="{auteur}"'
        + (f' w:date="{date}"' if date else "")
        + "><w:p><w:r><w:t>Avis</w:t></w:r></w:p></w:comment>"
        for rang, (auteur, date) in enumerate(auteurs_dates)
    )
    return f'<w:comments xmlns:w="{espace}">{elements}</w:comments>'.encode()


def proprietes(creation: str = "", modification: str = "", revision: str = "") -> bytes:
    contenu = ""
    if creation:
        contenu += f'<dcterms:created xsi:type="dcterms:W3CDTF">{creation}</dcterms:created>'
    if modification:
        contenu += f'<dcterms:modified xsi:type="dcterms:W3CDTF">{modification}</dcterms:modified>'
    if revision:
        contenu += f"<cp:revision>{revision}</cp:revision>"
    return core(contenu).replace(b"<cp:coreProperties ", f"<cp:coreProperties {DCTERMS} ".encode())


def docx(
    corps_: bytes | None = None,
    *,
    core_: bytes | None = None,
    app_: bytes | None = None,
    reglages_: bytes | None = None,
    commentaires_: bytes | None = None,
    prefixe: str = T,
) -> bytes:
    """Paquet, propriétés données, partie principale et, par ses relations, réglages et
    commentaires donnés."""
    paquet = [(TYPE_DOCUMENT, "word/document.xml")]
    entrees: list[tuple[str, bytes]] = []
    if core_ is not None:
        paquet.append((TYPE_CORE, "docProps/core.xml"))
        entrees.append(("docProps/core.xml", core_))
    if app_ is not None:
        paquet.append((TYPE_APP, "docProps/app.xml"))
        entrees.append(("docProps/app.xml", app_))
    annexes = []
    if reglages_ is not None:
        annexes.append((f"{prefixe}settings", "settings.xml"))
        entrees.append(("word/settings.xml", reglages_))
    if commentaires_ is not None:
        annexes.append((f"{prefixe}comments", "comments.xml"))
        entrees.append(("word/comments.xml", commentaires_))
    if annexes:
        entrees.append(("word/_rels/document.xml.rels", relations(*annexes)))
    return zip_(
        ("[Content_Types].xml", b"<Types/>"),
        ("_rels/.rels", relations(*paquet)),
        ("word/document.xml", corps("") if corps_ is None else corps_),
        *entrees,
    )


# ODT construits


def style(nom: str, famille: str, rsid: str | None = None, paragraphe: str | None = None) -> str:
    attributs = "" if rsid is None else f' officeooo:rsid="{rsid}"'
    attributs += "" if paragraphe is None else f' officeooo:paragraph-rsid="{paragraphe}"'
    return (
        f'<style:style style:name="{nom}" style:family="{famille}">'
        f"<style:text-properties{attributs}/></style:style>"
    )


def contenu_odt(styles: str, texte_: str, *, communs: str = "") -> bytes:
    return (
        f"<office:document-content {ESPACES_ODF}>{communs}"
        f"<office:automatic-styles>{styles}</office:automatic-styles>"
        f"<office:body><office:text>{texte_}</office:text></office:body>"
        "</office:document-content>"
    ).encode()


def odt(contenu: bytes | None, meta_: bytes | None = None) -> bytes:
    autres = () if contenu is None else (("content.xml", contenu),)
    return odt_(meta_, *autres)


def changement(sorte: str, auteur: str, date: str, contenu: str = "") -> str:
    return (
        f'<text:changed-region text:id="c{auteur}"><text:{sorte}><office:change-info>'
        f"<dc:creator>{auteur}</dc:creator><dc:date>{date}</dc:date></office:change-info>"
        f"{contenu}</text:{sorte}></text:changed-region>"
    )


def annotation(auteur: str, date: str) -> str:
    return (
        f"<office:annotation><dc:creator>{auteur}</dc:creator><dc:date>{date}</dc:date>"
        "<text:p>Avis du relecteur</text:p></office:annotation>"
    )


# Fonctions de lecture


@pytest.mark.parametrize(
    ("ecrite", "minutes"),
    [
        ("P0D", 0),
        ("PT59S", 0),
        ("PT1H2M3S", 62),
        (" PT2M ", 2),
        ("PT1.5S", 0),
        ("PT90,25S", 1),
        ("P1DT1M", 1441),
        ("P0Y0M1D", 1440),
        ("PT00H05M12S", 5),
        ("P1Y", None),
        ("P2M", None),
        ("P", None),
        ("PT", None),
        ("P1DT", None),
        ("-PT5M", None),
        ("5 minutes", None),
        ("", None),
    ],
)
def test_duree_iso8601(ecrite: str, minutes: int | None) -> None:
    assert historique.duree_iso8601(ecrite) == minutes


@pytest.mark.parametrize(
    ("ecrite", "lue"),
    [
        ("2026-11-23T10:00:00Z", "2026-11-23T10:00:00"),
        ("2026-11-23T10:00:00.5+02:00", "2026-11-23T10:00:00.5"),
        ("2026-11-23T10:00:00-0500", "2026-11-23T10:00:00"),
        ("2026-11-23T10:00:00+01", "2026-11-23T10:00:00"),
        ("2026-11-23T10:00:00", "2026-11-23T10:00:00"),
        (" 2026-11-23 ", "2026-11-23"),
    ],
)
def test_sans_fuseau(ecrite: str, lue: str) -> None:
    assert historique.sans_fuseau(ecrite) == lue


# DOCX : propriétés


def test_docx_temps_et_enregistrements() -> None:
    contenu = docx(app_=app("<TotalTime> 125 </TotalTime>"), core_=proprietes(revision="7"))
    valeurs_ = obs(contenu)
    assert valeurs_["historique.duree"] == 125
    assert valeurs_["historique.revisions"] == 7
    assert valeurs_["historique.present"] is True
    resultat = lignes(contenu)
    duree = next(
        o["observation"]
        for o in resultat
        if o.get("observation", {}).get("nom") == "historique.duree"
    )
    assert duree["unite"] == "minutes"
    assert duree["localisation"]["chemin"] == "docProps/app.xml"


@pytest.mark.parametrize("valeur", ["-3", "1.5", "deux", "", "1" * 19])
def test_docx_valeurs_non_entieres_non_observees(valeur: str) -> None:
    contenu = docx(app_=app(f"<TotalTime>{valeur}</TotalTime>"), core_=proprietes(revision=valeur))
    valeurs_ = obs(contenu)
    assert "historique.duree" not in valeurs_
    assert "historique.revisions" not in valeurs_


def test_docx_premiere_valeur_retenue_et_espaces_inconnus() -> None:
    # Une propriété répétée : la première ; un élément d'un autre espace : ignoré.
    contenu = docx(
        app_=app(
            '<TotalTime>3</TotalTime><TotalTime>9</TotalTime><x:TotalTime xmlns:x="urn:x">8'
            "</x:TotalTime>"
        ),
        core_=proprietes(revision="2") + b"",
    )
    assert obs(contenu)["historique.duree"] == 3


def test_docx_proprietes_strictes() -> None:
    espace = "http://purl.oclc.org/ooxml/officeDocument/extendedProperties"
    paquet = relations(
        (f"{STRICT}officeDocument", "word/document.xml"),
        (f"{STRICT}extendedProperties", "docProps/app.xml"),
        (
            "http://schemas.openxmlformats.org/officedocument/2006/relationships/metadata/"
            "core-properties",
            "docProps/core.xml",
        ),
    )
    contenu = zip_(
        ("_rels/.rels", paquet),
        ("docProps/app.xml", app("<TotalTime>4</TotalTime>", espace)),
        ("docProps/core.xml", proprietes(revision="5")),
        ("word/document.xml", corps(p(r("Texte")), W_STRICT)),
    )
    valeurs_ = obs(contenu)
    assert (valeurs_["historique.duree"], valeurs_["historique.revisions"]) == (4, 5)
    assert valeurs_["historique.texte.caracteres"] == 5


def test_docx_relations_ignorees() -> None:
    # Cible externe, type inconnu, cible vide : rien n'est suivi ; la première relation d'une
    # sorte l'emporte.
    paquet = relations(
        (TYPE_APP, "https://exemple.invalid/app.xml", "External"),
        ("urn:inconnu", "docProps/app.xml"),
        (TYPE_APP, ""),
        (TYPE_APP, "docProps/app.xml"),
        (TYPE_APP, "docProps/autre.xml"),
        (TYPE_DOCUMENT, "/word/./document.xml"),
    )
    contenu = zip_(
        ("_rels/.rels", paquet + b"<!-- -->"),
        ("docProps/app.xml", app("<TotalTime>4</TotalTime>")),
        ("docProps/autre.xml", app("<TotalTime>40</TotalTime>")),
        ("word/document.xml", corps("")),
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.duree"] == 4


def test_docx_cibles_relatives() -> None:
    # Cibles relatives à la partie principale, rangée ailleurs que dans word/ ; « .. » remonte.
    paquet = relations((TYPE_DOCUMENT, "texte/principal.xml"))
    annexes = relations((f"{T}settings", "../reglages/../reglages/r.xml"))
    contenu = zip_(
        ("_rels/.rels", paquet),
        ("texte/principal.xml", corps("")),
        ("texte/_rels/principal.xml.rels", annexes),
        ("reglages/r.xml", reglages("00AA0001")),
    )
    assert obs(contenu)["historique.sessions"] == 1


def test_docx_cible_qui_remonte_au_dessus_du_paquet() -> None:
    paquet = relations((TYPE_DOCUMENT, "../../word/document.xml"))
    contenu = zip_(("_rels/.rels", paquet), ("word/document.xml", corps(p(r("ab")))))
    assert obs(contenu)["historique.texte.caracteres"] == 2


# DOCX : sessions du texte


def test_docx_sessions_du_texte() -> None:
    # Course : sa session ; sinon celle du paragraphe ; sinon aucune.
    contenu = docx(
        corps(
            p(r("aaaa", "00a00001"), r("bb"), defaut="00A00002")
            + p(r("ccc", "00A00003"), r("dddddd"))
        ),
        reglages_=reglages("00A00002", "00A00003", "00A00004", racine="00A00001"),
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.sessions"] == 4
    assert valeurs_["historique.texte.caracteres"] == 15
    assert valeurs_["historique.texte.sans_session"] == 6
    assert valeurs_["historique.texte.sessions"] == 3
    assert valeurs_["historique.texte.part"] == 44  # 4 sur 9, arrondi au-dessous


def test_docx_une_seule_session() -> None:
    contenu = docx(corps(p(r("Un texte d'une traite."), defaut="00C0FFEE")))
    valeurs_ = obs(contenu)
    assert (valeurs_["historique.texte.sessions"], valeurs_["historique.texte.part"]) == (1, 100)
    assert "historique.sessions" not in valeurs_  # aucun réglage


def test_docx_texte_supprime_ou_deplace_non_compte() -> None:
    # Le texte supprimé (w:delText, ou w:t sous w:del) et celui qui a quitté sa place
    # (moveFrom) ne s'affichent pas ; celui qui y arrive (moveTo) et l'insertion, si.
    contenu = docx(
        corps(
            p(
                r("vu", "00000001"),
                marque("del", '<w:r w:rsidR="00000002"><w:delText>caché</w:delText></w:r>'),
                marque("del", r("aussi", "00000002")),
                marque("moveFrom", r("parti", "00000002")),
                marque("moveTo", r("venu", "00000003")),
                marque("ins", r("ajout", "00000003")),
            )
        )
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.texte.caracteres"] == 11
    assert valeurs_["historique.texte.sessions"] == 2
    assert valeurs_["historique.modifications"] == 5


def test_docx_sans_texte() -> None:
    valeurs_ = obs(docx(corps(p() + "<w:tbl/>")))
    assert valeurs_["historique.texte.caracteres"] == 0
    assert "historique.texte.sans_session" not in valeurs_
    assert valeurs_["historique.present"] is False


def test_docx_texte_hors_course_et_autres_espaces() -> None:
    # w:t hors d'une course, texte d'un autre espace, texte des codes de champ : seul le premier
    # est du texte (sans session).
    contenu = docx(
        corps(
            '<w:p w:rsidRDefault="00000001"><w:t>libre</w:t>'
            '<x:t xmlns:x="urn:x">autre</x:t>'
            "<w:r><w:instrText>PAGE</w:instrText></w:r></w:p>"
        )
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.texte.caracteres"] == 5
    assert valeurs_["historique.texte.sans_session"] == 5


def test_docx_reglages() -> None:
    # Racine comptée, identifiants en double ou de casse différente comptés une fois, valeur vide
    # ignorée, autres éléments ignorés.
    contenu = docx(
        reglages_=(
            f'<w:settings xmlns:w="{W}"><w:rsids><w:rsidRoot w:val="00ab0001"/>'
            '<w:rsid w:val="00AB0001"/><w:rsid w:val="00AB0002"/><w:rsid w:val=" "/>'
            '<w:rsid/><w:autre w:val="00AB0009"/><x:rsid xmlns:x="urn:x" x:val="1"/>'
            '</w:rsids><w:trackRevisions/><x:rsids xmlns:x="urn:x"/></w:settings>'
        ).encode()
    )
    assert obs(contenu)["historique.sessions"] == 2


def test_docx_reglages_stricts() -> None:
    contenu = docx(reglages_=reglages("00000001", espace=W_STRICT), prefixe=STRICT)
    assert obs(contenu)["historique.sessions"] == 1


# DOCX : modifications suivies et commentaires


def test_docx_marques_de_revision() -> None:
    marques = "".join(
        marque(nom, auteur=f"Relecteur {rang % 3}")
        for rang, nom in enumerate(sorted(historique.CHANGEMENTS_DOCX))
    )
    contenu = docx(
        corps(
            p(r("texte", "00000001"), marques)
            + '<w:p><w:pPr><w:rPr><w:ins w:id="9" w:author=" "/></w:rPr></w:pPr></w:p>'
            + '<w:p><w:moveFromRangeStart w:id="5" w:author="X"/></w:p>'
        )
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.modifications"] == len(historique.CHANGEMENTS_DOCX) + 1
    assert valeurs_["historique.modifications.auteurs"] == 3  # le nom blanc ne compte pas
    assert valeurs_["historique.commentaires"] == 0
    assert "historique.commentaires.auteurs" not in valeurs_


def test_docx_commentaires() -> None:
    contenu = docx(
        commentaires_=commentaires(
            ("Relecture", "2026-11-20T10:00:00Z"), ("Relecture", ""), ("Autre", ""), ("", "")
        )
    )
    resultat = lignes(contenu)
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["historique.commentaires"] == 4
    assert valeurs_["historique.commentaires.auteurs"] == 2
    assert "historique.modifications.auteurs" not in valeurs_
    assert identifiantes(resultat) == {}  # aucun nom n'est observé (ADR-0250)
    assert "Relecture" not in json.dumps(resultat, ensure_ascii=False)


def test_docx_commentaires_stricts() -> None:
    contenu = docx(commentaires_=commentaires(("A", ""), espace=W_STRICT), prefixe=STRICT)
    assert obs(contenu)["historique.commentaires"] == 1


def test_aucun_nom_observe() -> None:
    contenu = docx(
        corps(p(marque("ins", r("x"), auteur="Camille Martin"))),
        core_=core("<dc:creator>Camille Martin</dc:creator>"),
        commentaires_=commentaires(("Camille Martin", "")),
    )
    resultat = lignes(contenu)
    assert "Camille" not in json.dumps(resultat, ensure_ascii=False)


# DOCX : dates


def test_docx_ecart_entre_creation_et_enregistrement() -> None:
    contenu = docx(
        core_=proprietes("2026-11-20T10:00:00Z", "2026-11-20T12:30:20Z"),
        app_=app("<TotalTime>200</TotalTime>"),
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.ecart"] == 151  # 150 min 20 s, arrondi au-dessus
    assert valeurs_["historique.duree"] == 200


@pytest.mark.parametrize(
    ("creation", "modification", "ecart"),
    [
        ("2026-11-20T10:00:00", "2026-11-20T10:00:00", 26 * 60 + 1),  # sans fuseau : 26 h
        ("2026-11-20", "2026-11-21", 2 * 24 * 60 + 26 * 60),  # une date couvre son jour
        ("2026-11-20T10:00:00Z", "2026-11-20T10:00:00Z", 1),
        ("2026-11-21T10:00:00Z", "2026-11-20T10:00:00Z", None),  # création après : T23
        ("2026-13-20T10:00:00Z", "2026-11-20T10:00:00Z", None),  # impossible
        ("2026-11-20T10:00:00Z", "inconnue", None),
        ("", "2026-11-20T10:00:00Z", None),
    ],
)
def test_docx_ecart(creation: str, modification: str, ecart: int | None) -> None:
    valeurs_ = obs(docx(core_=proprietes(creation, modification)))
    assert valeurs_.get("historique.ecart") == ecart


def test_docx_dates_posterieures() -> None:
    # Dernier enregistrement à 10 h UTC ; une date de modification est lue sans fuseau : elle
    # n'est certainement postérieure que plus de 14 h après.
    contenu = docx(
        corps(
            p(
                marque("ins", r("a"), date="2026-11-21T00:01:00Z"),
                marque("ins", r("b"), date="2026-11-20T23:59:00Z"),
                marque("del", auteur="", date="2026-11-01T00:00:00Z"),
                marque("del", date="0-00-00T00:00:00Z"),
            )
        ),
        core_=proprietes("2026-11-01T09:00:00Z", "2026-11-20T10:00:00Z"),
        commentaires_=commentaires(("A", "2026-11-25T00:00:00+05:00"), ("B", "jamais")),
    )
    valeurs_ = obs(contenu)
    assert valeurs_["historique.posterieures"] == 2


@pytest.mark.parametrize(
    "dates",
    [
        ("0-00-00T00:00:00Z",),  # date nulle de LibreOffice
        (),
    ],
)
def test_docx_dates_illisibles_ou_absentes(dates: tuple[str, ...]) -> None:
    contenu = docx(
        corps(p(*(marque("ins", r("a"), date=d) for d in dates))),
        core_=proprietes(modification="2026-11-20T10:00:00Z"),
    )
    assert "historique.posterieures" not in obs(contenu)


def test_docx_enregistrement_illisible() -> None:
    contenu = docx(
        corps(p(marque("ins", r("a"), date="2026-11-21T00:00:00Z"))),
        core_=proprietes(modification="hier"),
    )
    assert "historique.posterieures" not in obs(contenu)


# DOCX : parties manquantes ou illisibles


def test_docx_sans_historique() -> None:
    resultat = lignes(docx(corps(p(r("Texte")))))
    assert valeurs_de(resultat) == {
        "historique.present": False,
        "historique.texte.caracteres": 5,
        "historique.texte.sans_session": 5,
        "historique.modifications": 0,
        "historique.commentaires": 0,
    }
    assert raisons(resultat) == []


def test_docx_sans_partie_principale() -> None:
    sans_relation = zip_(
        ("_rels/.rels", relations((TYPE_APP, "docProps/app.xml"))),
        ("docProps/app.xml", app("<TotalTime>2</TotalTime>")),
    )
    resultat = lignes(sans_relation)
    assert valeurs_de(resultat) == {"historique.present": True, "historique.duree": 2}
    assert raisons(resultat) == [MANQUANTE]
    sans_paquet = zip_(("word/document.xml", corps("")))
    assert raisons(lignes(sans_paquet)) == [MANQUANTE]
    assert valeurs_de(lignes(sans_paquet)) == {"historique.present": False}


def test_docx_partie_principale_absente() -> None:
    contenu = zip_(("_rels/.rels", relations((TYPE_DOCUMENT, "word/document.xml"))))
    resultat = lignes(contenu)
    assert raisons(resultat) == [MANQUANTE]
    assert valeurs_de(resultat) == {"historique.present": False}


def test_docx_parties_mal_formees() -> None:
    contenu = docx(
        corps(p(r("ab", "00000001")))[:-20],
        core_=b"<cp:coreProperties",
        app_=app("<TotalTime>3</TotalTime>")[:-5],
        reglages_=reglages("00000001")[:-3],
        commentaires_=commentaires(("A", ""))[:-4],
    )
    resultat = lignes(contenu)
    assert raisons(resultat) == [PARTIEL] * 5
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["historique.duree"] == 3  # lu avant l'arrêt
    assert valeurs_["historique.texte.caracteres"] == 2
    assert valeurs_["historique.commentaires"] == 1


def test_docx_entrees_en_double_et_illisibles() -> None:
    relations_ = relations((TYPE_DOCUMENT, "word/document.xml"), (TYPE_APP, "docProps/app.xml"))
    contenu = archive_brute(
        Brute(b"_rels/.rels", relations_),
        Brute(b"docProps/app.xml", app("<TotalTime>2</TotalTime>")),
        Brute(b"docProps/APP.xml", app("<TotalTime>3</TotalTime>")),
        Brute(b"word/document.xml", corps(""), donnees=b"\xff\xff\xff"),
    )
    resultat = lignes(contenu)
    # Deux entrées du même nom, à la casse près : refusées (OPC) ; données qui ne se
    # décompressent pas : la partie principale n'est pas lue.
    chemins = [
        n["non_menee"]["localisation"]["chemin"] for n in resultat if n["type"] == "non_menee"
    ]
    assert raisons(resultat) == [PARTIEL, PARTIEL]
    assert chemins == ["docProps/app.xml", "word/document.xml"]
    assert "historique.duree" not in valeurs_de(resultat)
    assert "historique.texte.caracteres" not in valeurs_de(resultat)


def test_archive_illisible() -> None:
    for format_ in ("docx", "odt"):
        resultat = lignes(b"PK\x03\x04 pas une archive", format_)
        assert valeurs_de(resultat) == {"historique.present": False}
        assert len(raisons(resultat)) == 1


# ODT


def test_odt_proprietes() -> None:
    contenu = odt(
        contenu_odt("", "<text:p>Texte</text:p>"),
        meta(
            "<meta:creation-date>2026-11-20T10:00:00</meta:creation-date>"
            "<dc:date>2026-11-20T11:00:00</dc:date>"
            "<meta:editing-duration>PT1H2M3S</meta:editing-duration>"
            "<meta:editing-duration>PT9H</meta:editing-duration>"
            "<meta:editing-cycles>4</meta:editing-cycles>"
            "<meta:generator>LibreOffice</meta:generator>"
        ),
    )
    valeurs_ = obs(contenu, "odt")
    assert valeurs_["historique.duree"] == 62
    assert valeurs_["historique.revisions"] == 4
    assert valeurs_["historique.ecart"] == 61 + 26 * 60  # sans fuseau ; seconde finale comprise


def test_odt_proprietes_illisibles() -> None:
    contenu = odt(
        contenu_odt("", ""),
        meta(
            "<meta:editing-duration>P1Y</meta:editing-duration>"
            "<meta:editing-cycles>un</meta:editing-cycles>"
            "<meta:creation-date></meta:creation-date><dc:date></dc:date>"
        ),
    )
    valeurs_ = obs(contenu, "odt")
    assert valeurs_["historique.present"] is False
    assert {"historique.duree", "historique.revisions", "historique.ecart"}.isdisjoint(valeurs_)


def test_odt_meta_hors_de_sa_place() -> None:
    # Racine ou bloc inconnus : rien n'est lu.
    ailleurs = b'<x:document-meta xmlns:x="urn:x"><x:meta/></x:document-meta>'
    autre_bloc = (
        meta("")
        .replace(b"<office:meta>", b"<office:autre>")
        .replace(b"</office:meta>", b"</office:autre>")
    )
    for meta_ in (ailleurs, autre_bloc):
        valeurs_ = obs(odt(contenu_odt("", ""), meta_), "odt")
        assert valeurs_["historique.present"] is False


def test_odt_sessions_du_texte() -> None:
    styles = (
        style("P1", "paragraph", "00825e0", "00825e0")
        + style("P2", "paragraph", None, "00900AA")
        + style("T1", "text", "009d0cf")
        + style("T2", "text")
    )
    texte_ = (
        '<text:p text:style-name="P1">aaaa<text:span text:style-name="T1">bb</text:span>'
        '<text:span text:style-name="T2">cc</text:span></text:p>'
        '<text:h text:style-name="P2">ddd<text:span text:style-name="T1">e</text:span></text:h>'
        '<text:p text:style-name="Inconnu">ff</text:p>'
    )
    valeurs_ = obs(odt(contenu_odt(styles, texte_)), "odt")
    assert valeurs_["historique.sessions"] == 3
    assert valeurs_["historique.texte.caracteres"] == 14
    assert valeurs_["historique.texte.sans_session"] == 5
    assert valeurs_["historique.texte.sessions"] == 2
    assert valeurs_["historique.texte.part"] == 66  # 6 sur 9


def test_odt_texte_hors_du_corps_non_compte() -> None:
    # Espaces entre paragraphes, notes, commentaires, région des modifications, description
    # d'une image : rien de cela n'est compté ; un style commun ne donne pas de session.
    styles = style("P1", "paragraph", "00000001")
    communs = "<office:styles>" + style("Standard", "paragraph", "00000009") + "</office:styles>"
    texte_ = (
        "\n  <text:tracked-changes>"
        + changement("deletion", "A", "2026-11-20T10:00:00", "<text:p>supprimé</text:p>")
        + "</text:tracked-changes>\n  "
        + '<text:p text:style-name="P1">vu<text:note><text:note-body><text:p>note</text:p>'
        + "</text:note-body></text:note>"
        + annotation("B", "2026-11-20T10:00:00")
        + "<draw:frame><svg:desc>image</svg:desc></draw:frame></text:p>\n"
        + '<text:p text:style-name="Standard">x</text:p>'
    )
    valeurs_ = obs(odt(contenu_odt(styles, texte_, communs=communs)), "odt")
    assert valeurs_["historique.texte.caracteres"] == 3
    assert valeurs_["historique.texte.sans_session"] == 1
    assert valeurs_["historique.sessions"] == 1
    assert valeurs_["historique.modifications"] == 1
    assert valeurs_["historique.commentaires"] == 1


def test_odt_modifications_et_commentaires() -> None:
    texte_ = (
        '<text:tracked-changes text:track-changes="true">'
        + changement("insertion", "Relecture", "2026-11-20T10:00:00")
        + changement("deletion", "Relecture", "2026-11-20T10:05:00")
        + changement("format-change", "Autre", "")
        + changement("insertion", "", "0000-00-00T00:00:00")
        + "</text:tracked-changes>"
        + "<text:p>a"
        + annotation("Relecture", "2026-11-20T10:00:00")
        + annotation("", "")
        + "</text:p>"
    )
    resultat = lignes(odt(contenu_odt("", texte_)), "odt")
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["historique.modifications"] == 4
    assert valeurs_["historique.modifications.auteurs"] == 2
    assert valeurs_["historique.commentaires"] == 2
    assert valeurs_["historique.commentaires.auteurs"] == 1
    assert "Relecture" not in json.dumps(resultat, ensure_ascii=False)


def test_odt_annotation_hors_du_corps_non_comptee() -> None:
    # Une annotation hors d'office:text (en-tête d'une page type, styles) n'est pas comptée.
    contenu = (
        f"<office:document-content {ESPACES_ODF}><office:automatic-styles/>"
        "<office:master-styles>" + annotation("A", "") + "</office:master-styles>"
        "<office:body><office:text/></office:body></office:document-content>"
    ).encode()
    assert obs(odt(contenu), "odt")["historique.commentaires"] == 0


def test_odt_auteur_hors_d_un_changement() -> None:
    # dc:creator ailleurs que sous office:change-info ou office:annotation : ignoré.
    texte_ = "<text:p><dc:creator>Personne</dc:creator>x</text:p>"
    valeurs_ = obs(odt(contenu_odt("", texte_)), "odt")
    assert valeurs_["historique.texte.caracteres"] == 1
    assert valeurs_["historique.modifications"] == 0


def test_odt_dates_posterieures() -> None:
    texte_ = (
        "<text:tracked-changes>"
        + changement("insertion", "A", "2026-11-22T12:00:01")  # 26 h et plus après
        + changement("insertion", "A", "2026-11-21T09:00:00")
        + "</text:tracked-changes>"
    )
    contenu = odt(contenu_odt("", texte_), meta("<dc:date>2026-11-20T10:00:00</dc:date>"))
    assert obs(contenu, "odt")["historique.posterieures"] == 1


def test_odt_sans_content() -> None:
    resultat = lignes(odt(None, meta("<meta:editing-cycles>1</meta:editing-cycles>")), "odt")
    assert valeurs_de(resultat) == {"historique.present": True, "historique.revisions": 1}
    assert raisons(resultat) == [MANQUANTE]


def test_odt_content_en_double_et_mal_forme() -> None:
    double = archive_brute(
        Brute(b"mimetype", b"application/vnd.oasis.opendocument.text", methode=0),
        Brute(b"content.xml", contenu_odt("", "")),
        Brute(b"content.xml", contenu_odt("", "")),
    )
    resultat = lignes(double, "odt")
    assert len(raisons(resultat)) == 1
    assert "historique.texte.caracteres" not in valeurs_de(resultat)
    tronque = odt(contenu_odt("", "<text:p>abc</text:p>")[:-30])
    resultat = lignes(tronque, "odt")
    assert raisons(resultat) == [PARTIEL]
    assert valeurs_de(resultat)["historique.texte.caracteres"] == 3


def test_odt_meta_mal_forme() -> None:
    meta_ = meta("<meta:editing-cycles>2</meta:editing-cycles>")[:-10]
    resultat = lignes(odt(contenu_odt("", ""), meta_), "odt")
    assert raisons(resultat) == [PARTIEL]


def test_odt_content_illisible() -> None:
    contenu = archive_brute(
        Brute(b"mimetype", b"application/vnd.oasis.opendocument.text", methode=0),
        Brute(b"content.xml", contenu_odt("", ""), donnees=b"\xff\xff"),
    )
    resultat = lignes(contenu, "odt")
    assert len(raisons(resultat)) == 1
    assert "historique.texte.caracteres" not in valeurs_de(resultat)


# Échantillons, oracle et règles


ATTENDUS = {
    "sessions.odt": {
        "R-HISTORIQUE-002",
        "R-HISTORIQUE-003",
        "R-HISTORIQUE-004",
        "R-HISTORIQUE-005",
        "R-HISTORIQUE-006",
    },
    "sessions.docx": {
        "R-HISTORIQUE-002",
        "R-HISTORIQUE-003",
        "R-HISTORIQUE-005",
        "R-HISTORIQUE-006",
    },
}
ORDINAIRES = {
    "document.docx": {"R-HISTORIQUE-002", "R-HISTORIQUE-003"},
    "document.odt": {"R-HISTORIQUE-002", "R-HISTORIQUE-003"},
}
"""Échantillons de ``tests/donnees/metadonnees`` (LibreOffice) : temps et cycles d'édition."""


def test_echantillons_et_oracle_concordent() -> None:
    assert set(ORACLE) - {"outils"} == set(ATTENDUS)


@pytest.mark.parametrize("nom", sorted(ATTENDUS))
def test_echantillons_compares_a_libreoffice(nom: str) -> None:
    # LibreOffice relit chaque échantillon : longueur et session de chaque portion du texte,
    # modifications suivies, commentaires et leurs auteurs, cycles et durée d'édition.
    attendu = ORACLE[nom]
    resultat = lignes((ECHANTILLONS / nom).read_bytes(), nom.rsplit(".", 1)[1])
    valeurs_ = valeurs_de(resultat)
    assert raisons(resultat) == []
    portions = attendu["portions"]
    total = sum(portion["longueur"] for portion in portions)
    assert valeurs_["historique.texte.caracteres"] == total
    par_session: dict[int, int] = {}
    for portion in portions:
        if portion["rsid"]:
            par_session[portion["rsid"]] = par_session.get(portion["rsid"], 0) + portion["longueur"]
    sans_session = total - sum(par_session.values())
    assert valeurs_["historique.texte.sans_session"] == sans_session
    if par_session:
        assert valeurs_["historique.texte.sessions"] == len(par_session)
        part = max(par_session.values()) * 100 // sum(par_session.values())
        assert valeurs_["historique.texte.part"] == part
    else:
        assert "historique.texte.sessions" not in valeurs_
    assert valeurs_["historique.revisions"] == attendu["cycles"]
    assert valeurs_["historique.duree"] == attendu["duree_secondes"] // 60
    assert valeurs_["historique.commentaires"] == attendu["commentaires"]
    assert valeurs_["historique.commentaires.auteurs"] == attendu["auteurs_commentaires"]
    assert valeurs_["historique.modifications.auteurs"] == attendu["auteurs_modifications"]
    if nom.endswith(".odt"):
        assert valeurs_["historique.modifications"] == attendu["modifications"]
    else:
        # LibreOffice relit une modification ; le DOCX en porte deux marques : le texte inséré
        # (w:ins) et la fin de son paragraphe (w:ins sous w:rPr de w:pPr).
        assert valeurs_["historique.modifications"] == attendu["modifications"] + 1


def test_trois_sessions_de_libreoffice() -> None:
    # Le document a été ouvert trois fois : trois sessions, comme le relit LibreOffice.
    valeurs_ = obs((ECHANTILLONS / "sessions.odt").read_bytes(), "odt")
    assert valeurs_["historique.sessions"] == valeurs_["historique.texte.sessions"] == 3


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("historique")
    sources = {n: (ECHANTILLONS / n).read_bytes() for n in ATTENDUS}
    sources |= {n: (METADONNEES / n).read_bytes() for n in ORDINAIRES}
    sources["incoherent.docx"] = docx(
        corps(p(r("Texte", "00000001"), marque("ins", r("x"), date="2026-11-22T00:00:00Z"))),
        core_=proprietes("2026-11-20T10:00:00Z", "2026-11-20T10:30:00Z", "2"),
        app_=app("<TotalTime>45</TotalTime>"),
        reglages_=reglages("00000001"),
    )
    sources["vide.docx"] = docx(corps(p(r("Texte"))))
    sources["vide.odt"] = odt(contenu_odt("", "<text:p>Texte</text:p>"))
    trouvees = {}
    for nom, contenu in sources.items():
        chemin = dossier / nom
        chemin.write_bytes(contenu)
        trouvees[nom] = analyser(chemin)
    return trouvees


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "historique"}


AUTRES = {
    "incoherent.docx": {
        "R-HISTORIQUE-002",
        "R-HISTORIQUE-003",
        "R-HISTORIQUE-004",
        "R-HISTORIQUE-005",
        "R-HISTORIQUE-007",
        "R-HISTORIQUE-008",
    },
    "vide.docx": {"R-HISTORIQUE-001"},
    "vide.odt": {"R-HISTORIQUE-001"},
}


@pytest.mark.parametrize(
    ("nom", "attendues"), [*ATTENDUS.items(), *ORDINAIRES.items(), *AUTRES.items()]
)
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques}
    assert etats["historique"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues


def test_toutes_les_regles_essayees() -> None:
    vues = set().union(*ATTENDUS.values(), *ORDINAIRES.values(), *AUTRES.values())
    assert vues == {f"R-HISTORIQUE-{n:03d}" for n in range(1, 9)}


def test_phrases_des_constats(analyses: dict[str, Analyse]) -> None:
    attendus = {
        "sessions.odt": (
            "Le document déclare un temps d'édition total de 0 minutes.",
            "Le document déclare 3 enregistrement(s) ou cycle(s) d'édition.",
            "Les 207 caractères du texte du corps portent la marque de 3 session(s) d'édition ; "
            "la plus représentée en porte 52 %.",
            "Le document porte 1 marque(s) de modification suivie, laissée(s) par 1 auteur(s) "
            "nommé(s) distinct(s) ; l'outil ne lit pas leurs noms.",
            "Le document porte 1 commentaire(s), laissé(s) par 1 auteur(s) nommé(s) "
            "distinct(s) ; l'outil ne lit pas leurs noms.",
        ),
        "incoherent.docx": (
            "Le document déclare 45 minutes d'édition, plus que les 31 minutes au plus qui "
            "séparent sa création de son dernier enregistrement, quel que soit le fuseau "
            "horaire : l'une de ces valeurs au moins est inexacte.",
            "1 modification(s) suivie(s) ou commentaire(s) sont datés après le dernier "
            "enregistrement du document, quel que soit le fuseau horaire : l'une de ces dates "
            "au moins est inexacte.",
        ),
        "vide.odt": ("Le document ne porte aucun historique d'édition",),
    }
    for nom, phrases in attendus.items():
        page = export.exporter_html(analyses[nom])
        for phrase in phrases:
            assert escape(phrase) in page, phrase


@pytest.mark.exigence("ES-13")
def test_aucun_auteur_au_rapport(analyses: dict[str, Analyse]) -> None:
    # Les auteurs des modifications et des commentaires ne sont ni observés ni écrits ; le nom
    # du commentaire de l'échantillon (« Relecture ») n'est au rapport que masqué, par le module
    # caracteres qui lit le texte des commentaires et non leur auteur.
    analyse = analyses["sessions.odt"]
    historiques = [o for o in analyse.observations if o.module == "historique"]
    assert all(o.identifiante is None for o in historiques)
    assert all("Relecture" not in str(o.valeur) for o in historiques)


def test_controle_avant_publication_complet(analyses: dict[str, Analyse]) -> None:
    # Le module ne lit aucune métadonnée identifiante : il est parmi les modules sans
    # métadonnées du résumé (ADR-0158, ADR-0250).
    analyse = analyses["sessions.docx"]
    assert "historique" not in {n.module for n in analyse.non_menees}
    analyse = analyses["vide.docx"]
    assert texte("resume.publication_incomplete") not in Presentation(analyse, ()).publication()


def test_docx_parties_designees_absentes() -> None:
    # Propriétés, réglages et commentaires désignés par une relation, absents de l'archive :
    # références manquantes ; un élément inconnu des relations est ignoré.
    paquet = relations(
        (TYPE_DOCUMENT, "word/document.xml"),
        (TYPE_CORE, "docProps/core.xml"),
        (TYPE_APP, "docProps/app.xml"),
    ).replace(b"</Relationships>", b"<Autre/></Relationships>")
    annexes = relations((f"{T}settings", "settings.xml"), (f"{T}comments", "comments.xml"))
    contenu = zip_(
        ("_rels/.rels", paquet),
        ("word/document.xml", corps(p(r("ab")))),
        ("word/_rels/document.xml.rels", annexes),
    )
    resultat = lignes(contenu)
    chemins = [
        n["non_menee"]["localisation"]["chemin"] for n in resultat if n["type"] == "non_menee"
    ]
    assert raisons(resultat) == [MANQUANTE] * 4
    assert chemins == [
        "docProps/app.xml",
        "docProps/core.xml",
        "word/settings.xml",
        "word/comments.xml",
    ]
    assert valeurs_de(resultat)["historique.commentaires"] == 0
