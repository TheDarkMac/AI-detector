"""Interface de la V1 : ligne de commande et rapport HTML lisibles et accessibles (T90).

Sommaire du rapport (ADR-0259), noms des techniques (ADR-0257), accords et lignes des
techniques au terminal (ADR-0258). La conformité à WCAG 2.2 AA, qui se vérifie par inspection
et démonstration, est consignée dans ``docs/verification/accessibilite.md`` (ADR-0256).
"""

import dataclasses
import re
from pathlib import Path
from typing import Any

import pytest
from conftest import construire_rapport
from test_rapport import analyse_de

from voight_kampff import exporter_html
from voight_kampff._orchestration import manifestes
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.cli import resume
from voight_kampff.rapport import _html
from voight_kampff.rapport._presentation import Presentation, accorder, technique, textes
from voight_kampff.rapport.modele import CategorieIdentifiante, EtatIsolation, NiveauIsolation

DONNEES = Path(__file__).parent / "donnees"


@pytest.fixture
def analyse() -> Analyse:
    return analyse_de(construire_rapport())


def _sommaire(document: str) -> list[str]:
    nav = document[document.index("<nav") : document.index("</nav>")]
    return re.findall(r'<li><a href="#([a-z_]+)">', nav)


@pytest.mark.exigence("NF-11", "NF-12")
def test_sommaire_des_rubriques(analyse: Analyse) -> None:
    document = exporter_html(analyse)
    rubriques = re.findall(r'<section id="([a-z_]+)"', document)
    assert Presentation(
        analyse, set(CategorieIdentifiante)
    ).alertes()  # isolation réduite du rapport de test
    assert _sommaire(document) == rubriques
    assert rubriques[0] == "alertes"
    # Entre l'en-tête et le contenu principal, nommé par son titre ; non imprimé.
    assert document.index("</header>") < document.index("<nav") < document.index("<main>")
    assert '<nav aria-labelledby="t-sommaire"><h2 id="t-sommaire">Sommaire</h2>' in document
    assert "@media print{body{max-width:none}.evitement,nav{display:none}" in _html.STYLE
    # Le lien d'évitement passe le sommaire.
    assert '<a class="evitement" href="#resume">' in document


@pytest.mark.exigence("NF-11")
def test_sommaire_sans_alerte(analyse: Analyse) -> None:
    complete = dataclasses.replace(analyse, isolation=EtatIsolation(NiveauIsolation.COMPLETE, ()))
    assert not Presentation(complete, set(CategorieIdentifiante)).alertes()
    document = exporter_html(complete)
    assert _sommaire(document) == re.findall(r'<section id="([a-z_]+)"', document)
    assert "alertes" not in _sommaire(document)


@pytest.mark.exigence("NF-12")
def test_feuille_de_style_des_petits_ecrans() -> None:
    """Refusion à 320 px (1.4.10) et cibles du sommaire de 24 px au moins (2.5.8)."""
    style = _html.STYLE
    assert "@media (max-width:30rem){dl{grid-template-columns:1fr;gap:0}" in style
    assert "h3,p,li,dd,td{overflow-wrap:anywhere}" in style
    assert "nav a{display:inline-block;padding:.2rem 0}" in style
    assert ".defilement:focus-visible{outline:3px solid var(--lien)" in style


@pytest.mark.parametrize(
    ("quantite", "attendu"),
    [
        (0, "0 information neutre."),
        (1, "1 information neutre."),
        (2, "2 informations neutres."),
        (12345, "12\u202f345 informations neutres."),
    ],
)
def test_accorder(quantite: int, attendu: str) -> None:
    assert accorder("resume.informations", quantite) == attendu


def test_accorder_avec_valeurs() -> None:
    assert accorder("terminal.non_applicables", 1, partie=3) == (
        "partie 3 : 1 technique non applicable à son format"
    )
    assert accorder("terminal.non_applicables", 19, partie=1) == (
        "partie 1 : 19 techniques non applicables à son format"
    )


def _chaines(entree: Any) -> list[str]:
    if isinstance(entree, str):
        return [entree]
    if isinstance(entree, dict):
        return [c for valeur in entree.values() for c in _chaines(valeur)]
    return [c for valeur in entree for c in _chaines(valeur)]


@pytest.mark.exigence("NF-11")
def test_aucun_pluriel_entre_parentheses() -> None:
    """Les textes de l'outil s'accordent au nombre au lieu d'écrire « (s) » (ADR-0258)."""
    fautifs = [c for c in _chaines(textes()) if re.search(r"\((?:s|e|es|x)\)", c)]
    assert fautifs == []


@pytest.mark.exigence("NF-11")
def test_chaque_technique_a_un_nom() -> None:
    livres = manifestes.decouvrir()
    identifiants = {m.identifiant for m in livres} | {
        t.identifiant for t in manifestes.hors_v1(livres)
    }
    assert set(textes()["techniques"]) == identifiants


def test_nom_d_une_technique() -> None:
    assert technique("ela") == "niveau d'erreur de recompression (ELA) (ela)"
    assert technique("bruit") == "motifs périodiques du résidu de bruit (bruit)"
    # Identifiant sans nom (module factice des tests) : écrit seul.
    assert technique("alpha") == "alpha"


@pytest.mark.exigence("NF-11", "F-25")
def test_techniques_par_partie_au_terminal() -> None:
    """Un DOCX à deux images : une ligne par état et par partie, non applicables comptées."""
    analyse = analyser(DONNEES / "imagesbureau" / "libreoffice.docx")
    lignes = resume(analyse)
    par_partie = [
        ligne for ligne in lignes if re.match(r"partie \d+(,| :) \d* ?techniques?", ligne)
    ]
    attendues = []
    for rang in (1, 2, 3):
        siennes = [t for t in analyse.couverture.techniques if t.partie == rang]
        appliquees = [technique(t.module) for t in siennes if t.etat.value == "appliquee"]
        # Hors de cette version et non applicables au format : comptées avec les non applicables.
        hors = [
            technique(t.module)
            for t in siennes
            if t.version is None and t.etat.value != "non_applicable"
        ]
        non_applicables = sum(t.etat.value == "non_applicable" for t in siennes)
        assert appliquees
        assert hors
        assert non_applicables > 1
        attendues += [
            f"partie {rang}, techniques appliquées : {', '.join(appliquees)}",
            f"partie {rang}, techniques hors de cette version : {', '.join(hors)}",
            f"partie {rang} : {non_applicables} techniques non applicables à son format",
        ]
    assert par_partie == attendues
    assert (
        "partie 1, techniques appliquées : éléments actifs d'un DOCX ou d'un ODT"
        in lignes[lignes.index(attendues[0])]
    )
    # L'origine d'une partie extraite nomme la technique qui l'a extraite.
    assert any("par images d'un DOCX ou d'un ODT (imagesbureau)" in ligne for ligne in lignes)
