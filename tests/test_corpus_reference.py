"""Tests du manifeste du corpus de référence (T100, ADR-0272 à ADR-0276).

Les fichiers du corpus ne sont pas au dépôt : ces tests relisent le manifeste par le banc et
vérifient ce qu'il dit sans les fichiers (catégories, parties, groupes, provenance), son accord
avec ``effectifs.json``, et l'identité des textes écrits par l'assistant, qui eux sont au dépôt.
"""

import hashlib
import json
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from banc.corpus import Categorie, Corpus, Nature, Origine, Partie, charger
from banc.reference.reference_commun import AdresseRefusee, sans_suivi, verifier_adresse

pytestmark = pytest.mark.exigence("ES-22")

DOSSIER = Path(__file__).resolve().parents[1] / "banc" / "reference"
MANIFESTE = DOSSIER / "corpus.toml"
SOURCES = (
    "https://commons.wikimedia.org/wiki/File:",
    "https://www.data.gouv.fr/",
    "https://fr.wikipedia.org/w/index.php?oldid=",
)
DERIVES = ("Dérivé de ", "Fabriqué de toutes pièces ", "Écrit par l'assistant pendant T100 ")


@pytest.fixture(scope="module")
def corpus() -> Corpus:
    return charger(MANIFESTE)


@pytest.fixture(scope="module")
def fichiers() -> list[dict[str, Any]]:
    document = tomllib.loads(MANIFESTE.read_text(encoding="utf-8"))
    liste: list[dict[str, Any]] = document["fichiers"]
    return liste


def test_manifeste_lu_par_le_banc(corpus: Corpus) -> None:
    assert corpus.nom == "reference"
    assert corpus.version == "1.0.0"
    assert corpus.nature is Nature.REFERENCE
    assert len(corpus.entrees) > 5000


def test_cinq_categories_dans_les_deux_parties(corpus: Corpus) -> None:
    vues = {(entree.categorie, entree.partie) for entree in corpus.entrees}
    assert vues == {(categorie, partie) for categorie in Categorie for partie in Partie}


def test_un_original_sur_trois_en_calibrage(corpus: Corpus) -> None:
    """ADR-0274 : un original sur trois en calibrage, dans chaque format.

    Les dérivés suivent leur original ; les originaux qu'ils dérivent sont tirés toutes parties
    confondues, si bien que la part de calibrage d'une catégorie dérivée n'est pas fixée.
    """
    parties: dict[str, list[Partie]] = defaultdict(list)
    for entree in corpus.entrees:
        if entree.categorie in {Categorie.AUTHENTIQUE, Categorie.GENERE}:
            dossier, nom = entree.chemin.rsplit("/", 1)
            parties[f"{dossier}/{nom.split('-')[0]}"].append(entree.partie)
    assert len(parties) >= 15
    for format_, liste in parties.items():
        calibrage = sum(partie is Partie.CALIBRAGE for partie in liste)
        # Un original écarté (texte trop court, empreinte différente) déplace un peu la part.
        assert 0.29 <= calibrage / len(liste) <= 0.38, (format_, calibrage, len(liste))


def test_derives_dans_le_groupe_de_leur_original(corpus: Corpus) -> None:
    originaux = {
        entree.groupe: entree
        for entree in corpus.entrees
        if entree.categorie in {Categorie.AUTHENTIQUE, Categorie.GENERE}
    }
    for entree in corpus.entrees:
        if entree.categorie in {Categorie.AUTHENTIQUE, Categorie.GENERE}:
            assert entree.chemin.rsplit("/", 1)[1].startswith(entree.groupe + "."), entree.chemin
            continue
        if entree.chemin.startswith("malformes/pieges/"):
            assert entree.origine is None
            continue
        original = originaux[entree.groupe]
        assert entree.partie is original.partie
        assert entree.chemin.rsplit("/", 1)[1].startswith(entree.groupe + ".")
        if entree.categorie is Categorie.RETOUCHE:
            assert original.origine is Origine.AUTHENTIQUE
        else:
            assert entree.origine is original.origine


def test_provenance_de_chaque_fichier(fichiers: list[dict[str, Any]]) -> None:
    for fichier in fichiers:
        provenance = fichier["provenance"]
        assert provenance["licence"].strip()
        # Originaux téléchargés : authentiques et images générées ; le reste est fabriqué.
        if fichier["chemin"].startswith(("authentiques/", "generes/image/")):
            assert provenance["source"].startswith(SOURCES), fichier["chemin"]
        else:
            assert provenance["source"].startswith(DERIVES), fichier["chemin"]
        if fichier["chemin"].startswith("generes/image/"):
            assert "non vérifiée" in provenance["remarque"]
        elif fichier["chemin"].startswith("generes/"):
            assert provenance["generateur"].startswith("Claude Opus 5.5")


def test_aucun_nom_de_compte(fichiers: list[dict[str, Any]]) -> None:
    """ADR-0276 : le manifeste ne répète pas les noms des comptes qui ont versé les fichiers."""
    for fichier in fichiers:
        assert set(fichier["provenance"]) <= {"source", "licence", "date", "generateur", "remarque"}
        assert "User:" not in json.dumps(fichier, ensure_ascii=False)


def test_effectifs_accordes_au_manifeste(corpus: Corpus, fichiers: list[dict[str, Any]]) -> None:
    effectifs = json.loads((DOSSIER / "effectifs.json").read_text(encoding="utf-8"))
    assert effectifs["version"] == corpus.version
    assert effectifs["empreinte_manifeste"] == corpus.empreinte
    assert effectifs["fichiers"] == len(corpus.entrees) == sum(effectifs["effectifs"].values())
    par_categorie: Counter[str] = Counter()
    for cle, nombre in effectifs["effectifs"].items():
        par_categorie[cle.split("|")[0]] += nombre
    assert par_categorie == Counter(fichier["categorie"] for fichier in fichiers)


def test_textes_de_l_assistant_tels_quels(corpus: Corpus) -> None:
    """Les textes générés en texte brut sont les octets de ``textes-ia/``, au dépôt."""
    textes = sorted((DOSSIER / "textes-ia").glob("ia-*.txt"))
    assert len(textes) == 40
    empreintes = {entree.chemin: entree.empreinte for entree in corpus.entrees}
    for texte in textes:
        chemin = f"generes/texte/texte-{texte.stem}.txt"
        assert empreintes[chemin] == hashlib.sha256(texte.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "adresse",
    [
        "https://commons.wikimedia.org/w/api.php?action=query",
        "https://upload.wikimedia.org/wikipedia/commons/a/ab/X.jpg",
        "https://static.data.gouv.fr/resources/x.docx",
        "https://fr.wikipedia.org/w/api.php",
    ],
)
def test_sources_retenues_acceptees(adresse: str) -> None:
    assert verifier_adresse(adresse) == adresse


@pytest.mark.parametrize(
    "adresse",
    [
        "http://commons.wikimedia.org/w/api.php",
        "https://example.org/",
        "https://commons.wikimedia.org.example.org/",
        "file:///etc/passwd",
        "https://en.wikipedia.org/w/api.php",
    ],
)
def test_autres_adresses_refusees(adresse: str) -> None:
    with pytest.raises(AdresseRefusee):
        verifier_adresse(adresse)


def test_parametres_de_suivi_retires() -> None:
    adresse = "https://upload.wikimedia.org/a/X.pdf?utm_source=commons&utm_campaign=x&page=2"
    assert sans_suivi(adresse) == "https://upload.wikimedia.org/a/X.pdf?page=2"
