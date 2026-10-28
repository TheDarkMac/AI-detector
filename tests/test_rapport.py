"""Tests du rapport exporté : JSON, HTML, masquage, neutralisation, textes (T16).

ADR-0091 à ADR-0098 ; ES-12, ES-13, ES-14 du modèle de menace.
"""

import base64
import dataclasses
import hashlib
import json
import re
from html.parser import HTMLParser
from typing import Any

import pytest
from catalogues import VERSION, regle
from conftest import EMPREINTE, construire_rapport
from hypothesis import given
from hypothesis import strategies as st

from voight_kampff import exporter_html, exporter_json
from voight_kampff._regles import Regle
from voight_kampff.analyse import Analyse
from voight_kampff.rapport import _html, export
from voight_kampff.rapport._presentation import (
    Presentation,
    echapper_json,
    neutraliser,
    textes,
)
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
    Constat,
    Couverture,
    Direction,
    EtatTechnique,
    Fondement,
    Niveau,
    NiveauIsolation,
    Plage,
    RaisonNonMenee,
    Rapport,
    TechniqueCouverte,
)

pytestmark = pytest.mark.exigence("F-83", "NF-18", "ES-12", "ES-13")

NOM = "photo virale.jpg"
ARTISTE = "Jeanne Martin"


def regle_de(constat: Constat, **champs: Any) -> Regle:
    """Règle du catalogue conforme à un constat du rapport de test."""
    parametres = list(constat.phrase.parametres)
    document: dict[str, Any] = {
        "version": constat.regle.version,
        "gabarit": constat.phrase.gabarit,
        "categorie": constat.categorie.value,
        "direction": constat.direction.value,
        "fondement": constat.fondement.value,
        "parametres": parametres or None,
        "phrase": {
            "fr": f"Constat {constat.regle.identifiant}"
            + "".join(f" « {{{nom}}} »" for nom in parametres)
        },
        "titre": f"Règle {constat.regle.identifiant}",
        "limites": [f"Limite de {constat.regle.identifiant}."],
    }
    if constat.graduation is not None:
        document["niveau"] = constat.graduation.niveau.value
        if constat.graduation.evaluee:
            document["evaluation"] = {
                "taux_faux_positifs": 0.002,
                "effectif": 1500,
                "borne_superieure": 0.00586,
                "corpus": "2026.1",
                "date": "2026-10-01",
            }
    return regle(constat.regle.identifiant, constat.module, **(document | champs))


def analyse_de(rapport: Rapport, **champs: Any) -> Analyse:
    analyse = Analyse(
        identification=rapport.identification,
        isolation=rapport.isolation,
        couverture=rapport.couverture,
        observations=rapport.observations,
        constats=rapport.constats,
        non_menees=rapport.non_menees,
        dependances=rapport.versions.dependances,
        catalogue=VERSION,
        regles=tuple(regle_de(constat) for constat in rapport.constats),
    )
    return dataclasses.replace(analyse, **champs) if champs else analyse


@pytest.fixture
def analyse() -> Analyse:
    return analyse_de(construire_rapport())


def avec_valeur(analyse: Analyse, valeur: str, nom: str = NOM) -> Analyse:
    """L'observation ``metadonnees/1``, citée par un indice, porte ``valeur`` ; le nom ``nom``."""
    observations = tuple(
        dataclasses.replace(o, valeur=valeur) if o.identifiant == "metadonnees/1" else o
        for o in analyse.observations
    )
    identification = dataclasses.replace(analyse.identification, nom=nom)
    return dataclasses.replace(analyse, observations=observations, identification=identification)


# Analyse et rapport (ADR-0097)


def test_rapport_de_l_analyse(analyse: Analyse) -> None:
    rapport = analyse.rapport()
    attendu = construire_rapport()
    assert rapport.identification == attendu.identification
    assert rapport.constats == attendu.constats
    assert rapport.versions.catalogue == VERSION
    assert rapport.versions.dependances == attendu.versions.dependances
    assert analyse.regle(analyse.constats[0]).identifiant == "R-C2PA-001"


def test_regle_d_un_constat_exigee(analyse: Analyse) -> None:
    with pytest.raises(ValueError, match="absente ou non conforme"):
        dataclasses.replace(analyse, regles=analyse.regles[1:])
    autre = dataclasses.replace(analyse.regles[0], fondement=Fondement.VERIFICATION_DETERMINISTE)
    with pytest.raises(ValueError, match="absente ou non conforme"):
        dataclasses.replace(analyse, regles=(*analyse.regles[1:], autre))
    with pytest.raises(ValueError, match="doublon"):
        dataclasses.replace(analyse, regles=(*analyse.regles, analyse.regles[0]))


# JSON (ADR-0095)


@pytest.mark.exigence("F-05")
def test_json_masque_par_defaut(analyse: Analyse) -> None:
    texte = exporter_json(analyse)
    document = json.loads(texte)
    # Le masquage est annoncé en tête, avant toute donnée (ES-13).
    assert list(document)[:2] == ["version_schema", "masquage"]
    assert document["masquage"] == {
        "masquees": [c.value for c in CategorieIdentifiante],
        "levees": [],
    }
    assert "nom" not in document["identification"]
    assert "empreinte" not in document["identification"]
    artiste = next(o for o in document["observations"] if o["identifiant"] == "metadonnees/2")
    assert "valeur" not in artiste
    assert artiste["identifiante"] == "metadonnee_nominative"
    # Masquée veut dire absente : ni le nom, ni l'empreinte, ni l'auteur ne sont dans le fichier.
    for donnee in (NOM, EMPREINTE, ARTISTE):
        assert donnee not in texte
    export.valider(document)


@pytest.mark.parametrize("categorie", list(CategorieIdentifiante))
def test_json_leve_une_categorie(analyse: Analyse, categorie: CategorieIdentifiante) -> None:
    document = json.loads(exporter_json(analyse, reveler=[categorie]))
    assert document["masquage"]["levees"] == [categorie.value]
    identification = document["identification"]
    assert ("nom" in identification) is (categorie is CategorieIdentifiante.NOM_DE_FICHIER)
    assert ("empreinte" in identification) is (categorie is CategorieIdentifiante.EMPREINTE)
    artiste = next(o for o in document["observations"] if o["identifiant"] == "metadonnees/2")
    assert ("valeur" in artiste) is (categorie is CategorieIdentifiante.METADONNEE_NOMINATIVE)


def test_json_tout_leve_se_relit(analyse: Analyse) -> None:
    document = json.loads(exporter_json(analyse, reveler=list(CategorieIdentifiante)))
    assert document["masquage"]["masquees"] == []
    assert Rapport.depuis_dict(document) == analyse.rapport()


def test_json_masque_ne_se_relit_pas(analyse: Analyse) -> None:
    document = json.loads(exporter_json(analyse, reveler=["nom_de_fichier", "empreinte"]))
    with pytest.raises(ValueError, match="export masqué"):
        Rapport.depuis_dict(document)


def test_categorie_inconnue(analyse: Analyse) -> None:
    with pytest.raises(ValueError, match="tout"):
        exporter_json(analyse, reveler=["tout"])


@pytest.mark.parametrize(
    "alterer",
    [
        pytest.param(
            lambda d: d["observations"][1].__setitem__("valeur", ARTISTE), id="valeur-masquee"
        ),
        pytest.param(lambda d: d["masquage"]["levees"].append("gps"), id="categorie-deux-fois"),
    ],
)
def test_export_altere_refuse(analyse: Analyse, alterer: Any) -> None:
    document = json.loads(exporter_json(analyse))
    alterer(document)
    with pytest.raises(ValueError, match=r"."):
        export.valider(document)


def test_export_sans_masquage_valide(analyse: Analyse) -> None:
    # Le rapport du modèle, sans « masquage », est un document complet : rien n'y manque.
    export.valider(analyse.rapport().vers_dict())


def test_json_echappe_les_caracteres_invisibles(analyse: Analyse) -> None:
    piege = "a‮b​c\x7fd\x1be\U000e0041f g"
    texte = exporter_json(avec_valeur(analyse, piege))
    assert piege not in texte
    for invisible in "‮​\x7f\x1b\U000e0041 ":
        assert invisible not in texte
    assert "a\\u202eb\\u200bc\\u007fd\\u001be\\udb40\\udc41f\\u2028g" in texte
    # Les données décodées sont inchangées.
    valeurs = {o["identifiant"]: o.get("valeur") for o in json.loads(texte)["observations"]}
    assert valeurs["metadonnees/1"] == piege
    assert texte.endswith("}\n")


def test_echapper_json_garde_la_mise_en_forme() -> None:
    texte = json.dumps({"a": ["é", " "]}, ensure_ascii=False, indent=2)
    assert echapper_json(texte) == texte


# Neutralisation (ADR-0096)


@pytest.mark.parametrize(
    ("brut", "vu"),
    [
        pytest.param("Texte ordinaire, accentué.", "Texte ordinaire, accentué.", id="ordinaire"),
        pytest.param("a‮b", "a⟨U+202E⟩b", id="bidirectionnel"),
        pytest.param("a⁦b⁩", "a⟨U+2066⟩b⟨U+2069⟩", id="isolat"),
        pytest.param("\x1b[2J", "⟨U+001B⟩[2J", id="echappement-terminal"),
        pytest.param("a\nb\tc\rd", "a⟨U+000A⟩b⟨U+0009⟩c⟨U+000D⟩d", id="sauts"),
        pytest.param("a\x85b c ", "a⟨U+0085⟩b⟨U+2028⟩c⟨U+2029⟩", id="lignes"),
        pytest.param("a​b﻿", "a⟨U+200B⟩b⟨U+FEFF⟩", id="sans-chasse"),
        pytest.param("\U000e0041", "⟨U+E0041⟩", id="etiquette"),
        pytest.param("a b", "a b", id="espace-insecable-garde"),
    ],
)
def test_neutraliser(brut: str, vu: str) -> None:
    assert neutraliser(brut) == vu


# HTML (ADR-0094, ADR-0098)


class Lecteur(HTMLParser):
    """Relève les balises, attributs et identifiants d'un document HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.balises: list[str] = []
        self.attributs: list[tuple[str, str | None]] = []
        self.identifiants: set[str] = set()
        self.ancres: set[str] = set()
        self.titres: list[str] = []
        self.style = ""
        self._dans: str | None = None

    def handle_starttag(self, balise: str, attributs: list[tuple[str, str | None]]) -> None:
        self.balises.append(balise)
        self.attributs += attributs
        valeurs = dict(attributs)
        if valeurs.get("id"):
            self.identifiants.add(str(valeurs["id"]))
        if balise == "a":
            self.ancres.add(str(valeurs["href"]))
        if balise in {"h1", "h2", "h3", "style"}:
            self._dans = balise
            if balise != "style":
                self.titres.append(balise)

    def handle_endtag(self, balise: str) -> None:
        self._dans = None

    def handle_data(self, donnees: str) -> None:
        if self._dans == "style":
            self.style += donnees


def lire(document: str) -> Lecteur:
    lecteur = Lecteur()
    lecteur.feed(document)
    lecteur.close()
    return lecteur


def test_html_autonome_sans_script(analyse: Analyse) -> None:
    document = exporter_html(analyse)
    lecteur = lire(document)
    assert document.startswith('<!DOCTYPE html>\n<html lang="fr">')
    assert "script" not in lecteur.balises
    assert not {"img", "link", "iframe", "object", "embed", "form", "base"} & set(lecteur.balises)
    # Aucune ressource externe ni gestionnaire d'événement (ES-12, ADR-0025).
    for nom, valeur in lecteur.attributs:
        assert not nom.startswith("on")
        assert nom not in {"src", "srcset", "action", "formaction"}
        if nom == "href":
            assert valeur is not None
            assert valeur.startswith("#")
    assert "http://" not in lecteur.style
    assert "url(" not in lecteur.style
    # Chaque lien interne mène à un élément du document.
    assert {ancre[1:] for ancre in lecteur.ancres} <= lecteur.identifiants


def test_html_politique_de_securite(analyse: Analyse) -> None:
    document = exporter_html(analyse)
    politique = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', document)
    assert politique is not None
    directives = dict(d.strip().split(" ", 1) for d in politique.group(1).split(";"))
    assert directives["default-src"] == "'none'"
    assert "script-src" not in directives
    # La seule feuille de style admise est celle du document, désignée par son empreinte.
    style = lire(document).style
    empreinte = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    assert directives["style-src"] == f"'sha256-{empreinte}'"
    assert style == _html.STYLE
    assert document.count("<style>") == 1
    # Avant tout contenu : la politique suit le jeu de caractères.
    assert document.index("Content-Security-Policy") < document.index("<title>")


@pytest.mark.exigence("NF-12")
def test_html_structure_accessible(analyse: Analyse) -> None:
    lecteur = lire(exporter_html(analyse))
    assert lecteur.titres.count("h1") == 1
    assert lecteur.titres[0] == "h1"
    assert "h3" not in lecteur.titres[: lecteur.titres.index("h2")]
    assert lecteur.balises.count("table") == lecteur.balises.count("caption")
    assert "main" in lecteur.balises


@pytest.mark.exigence("NF-11", "P-03", "P-04", "F-25")
def test_html_ordre_des_rubriques(analyse: Analyse) -> None:
    document = exporter_html(analyse)
    rubriques = re.findall(r'<section id="([a-z_]+)"', document)
    assert rubriques == [
        "avertissement",
        "resume",
        "identification",
        "versions",
        "isolation",
        "preuves",
        "indices",
        "informations",
        "non_menees",
        "couverture",
        "donnees_identifiantes",
        "observations",
        "glossaire",
    ]
    # Les alertes précèdent l'avertissement ; l'isolation du rapport de test est réduite.
    assert document.index("t-alertes") < document.index('id="avertissement"')


def test_html_masque_par_defaut(analyse: Analyse) -> None:
    document = exporter_html(analyse)
    for donnee in (NOM, EMPREINTE, ARTISTE):
        assert donnee not in document
    assert "[masqué : nom du fichier]" in document
    assert "[masqué : métadonnées nominatives]" in document
    assert "Masquage levé" not in document


def test_html_leve_et_annonce(analyse: Analyse) -> None:
    document = exporter_html(analyse, reveler=["nom_de_fichier", "empreinte"])
    assert NOM in document
    assert EMPREINTE in document
    assert ARTISTE not in document
    alerte = "Masquage levé à la demande de l&#x27;utilisateur pour : nom du fichier, empreinte"
    assert document.index(alerte) < document.index('id="avertissement"')
    # Le titre de l'onglet ne nomme jamais le fichier.
    titre = re.search(r"<title>([^<]*)</title>", document)
    assert titre is not None
    assert NOM not in titre.group(1)


def test_html_echappe_les_valeurs(analyse: Analyse) -> None:
    piege = '<script>alert(1)</script><img src=x onerror="y"> & ‮'
    document = exporter_html(
        avec_valeur(analyse, piege, nom="<i>nom.jpg"), reveler=["nom_de_fichier"]
    )
    lecteur = lire(document)
    assert "script" not in lecteur.balises
    assert "img" not in lecteur.balises
    assert "i" not in lecteur.balises
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in document
    assert "&lt;i&gt;nom.jpg" in document
    assert "‮" not in document
    assert "⟨U+202E⟩" in document


@given(st.text(max_size=200))
def test_html_aucune_valeur_ne_cree_de_balise(valeur: str) -> None:
    # Fuzzing (ES-19) : une valeur quelconque ne crée ni balise ni attribut, n'écrit aucun
    # caractère invisible, et le document reste lisible par un analyseur HTML.
    analyse = avec_valeur(analyse_de(construire_rapport()), valeur)
    document = exporter_html(analyse)
    temoin = lire(exporter_html(avec_valeur(analyse, "x")))
    lecteur = lire(document)
    assert lecteur.balises == temoin.balises
    assert lecteur.attributs == temoin.attributs
    assert neutraliser(document.replace("\n", "")) == document.replace("\n", "")


@pytest.mark.exigence("F-80", "F-81", "P-02")
def test_html_contenu_des_constats(analyse: Analyse) -> None:
    document = exporter_html(analyse)
    # Phrase de la règle, paramètres remplacés par la valeur de leur observation.
    assert "Constat R-C2PA-001 « valide »" in document
    assert "Preuve, vers origine IA : Constat R-C2PA-001 « valide »" in document
    # Règle, limites et évaluation, lues dans le catalogue (§6 du cahier).
    assert "R-META-001, version 2 : Règle R-META-001" in document
    assert "Limite de R-META-001." in document
    assert (
        "taux de faux positifs mesuré : 0.2 % sur 1\u202f500 fichiers, au plus 0.586 % avec une "
        "confiance de 95 % (corpus 2026.1, 2026-10-01)"
    ) in document
    assert "règle non évaluée" in document
    # Indices comptés par direction et niveau, sans conclusion (ADR-0018).
    assert "2 indice(s) :" in document
    assert "vers origine IA : 1 fort" in document
    assert "vers transformation : 1 faible" in document
    # Analyses non menées : la phrase de leur raison, jamais leur code.
    assert textes()["raisons"]["reference_manquante"].replace("'", "&#x27;") in document
    assert "reference_manquante" not in document
    assert "2 048 576 octets" in document


def test_html_sans_constat_ni_observation(analyse: Analyse) -> None:
    vide = dataclasses.replace(
        analyse,
        observations=(),
        constats=(),
        regles=(),
        couverture=dataclasses.replace(analyse.couverture, marquages_recherches=()),
        dependances=(),
    )
    document = exporter_html(vide)
    assert "Aucune preuve." in document
    assert "Aucun indice." in document
    assert "0 information(s) neutre(s)." in document


def test_alertes(analyse: Analyse) -> None:
    fourni = dataclasses.replace(VERSION, fourni_par_utilisateur=True)
    complete = dataclasses.replace(analyse.isolation, niveau=NiveauIsolation.COMPLETE, manques=())
    calme = dataclasses.replace(analyse, isolation=complete)
    assert Presentation(calme, set(CategorieIdentifiante)).alertes() == []
    vue = Presentation(dataclasses.replace(calme, catalogue=fourni), set(CategorieIdentifiante))
    assert vue.alertes()[0].startswith("Catalogue de règles fourni par l'utilisateur")
    assert ", fourni par l'utilisateur" in vue.catalogue()


# Textes (ADR-0098)


@pytest.mark.parametrize(
    ("table", "enumeration"),
    [
        ("categories", Categorie),
        ("directions", Direction),
        ("niveaux", Niveau),
        ("fondements", Fondement),
        ("raisons", RaisonNonMenee),
        ("identifiantes", CategorieIdentifiante),
        ("isolation", NiveauIsolation),
    ],
)
def test_un_libelle_par_valeur(table: str, enumeration: type[Any]) -> None:
    assert set(textes()[table]) == {valeur.value for valeur in enumeration}


@pytest.mark.exigence("NF-14", "P-04")
def test_textes_sans_verdict() -> None:
    # NF-14 : aucun texte de l'outil ne présente un indice comme une certitude.
    tout = json.dumps(textes(), ensure_ascii=False).lower()
    for interdit in (
        "est généré",
        "a été généré par",
        "est authentique",
        "est un faux",
        "certain que",
    ):
        assert interdit not in tout
    for terme in ("preuve", "indice", "information_neutre", "direction", "niveau", "fondement"):
        assert terme in textes()["glossaire"]


@pytest.mark.exigence("F-82")
def test_toutes_les_analyses_menees(analyse: Analyse) -> None:
    identification = dataclasses.replace(
        analyse.identification,
        taille=10,
        parties=(dataclasses.replace(analyse.identification.parties[0], octets=Plage(0, 10)),),
    )
    complete = dataclasses.replace(
        analyse,
        identification=identification,
        observations=(),
        constats=(),
        regles=(),
        non_menees=(),
        couverture=Couverture((TechniqueCouverte("jpeg", EtatTechnique.APPLIQUEE, "1"),), ()),
    )
    attendu = "Toutes les analyses prévues ont été menées."
    assert attendu in Presentation(complete, set(CategorieIdentifiante)).resume()
    assert f"<p>{attendu}</p>" in exporter_html(complete)
