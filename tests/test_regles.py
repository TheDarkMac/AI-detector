"""Tests des règles du catalogue : forme, motifs RE2, évaluation (T15, ADR-0084, ADR-0089)."""

import dataclasses
import subprocess
import sys
from typing import Any

import pytest
from catalogues import moteur, regle, regle_dict

from voight_kampff._regles import (
    Application,
    Comparaison,
    Condition,
    Regle,
    Seuil,
    appliquer,
    conforme,
    emplacements,
    niveau_permis,
    remplir,
)
from voight_kampff.rapport.modele import (
    Categorie,
    Constat,
    Direction,
    Fondement,
    Graduation,
    Niveau,
    Observation,
    Phrase,
    ReferenceRegle,
    Valeur,
)


def condition(**test: Any) -> Condition:
    return Condition.depuis_dict({"observation": "n"} | test)


# Conditions


@pytest.mark.parametrize(
    ("test", "valeur", "attendu"),
    [
        ({"egal": "a"}, "a", True),
        ({"egal": "a"}, "A", False),
        ({"egal": 1}, 1.0, True),
        # Python tient True == 1 ; le catalogue non.
        ({"egal": 1}, True, False),
        ({"egal": True}, 1, False),
        ({"egal": True}, True, True),
        ({"egal": "1"}, 1, False),
        ({"parmi": ["a", 2]}, 2, True),
        ({"parmi": ["a", 2]}, "2", False),
        ({"parmi": [1]}, True, False),
        ({"parmi": [False]}, 0, False),
        ({"motif": "(?i)^mid"}, "Midjourney", True),
        ({"motif": "journey"}, "Midjourney", True),  # cherché n'importe où
        ({"motif": "^journey"}, "Midjourney", False),
        ({"motif": "x"}, 1, False),  # un motif ne vaut que pour un texte
        ({"seuil": {"operateur": ">=", "valeur": 3}}, 3, True),
        ({"seuil": {"operateur": ">", "valeur": 3}}, 3, False),
        ({"seuil": {"operateur": "<", "valeur": 3}}, 2.5, True),
        ({"seuil": {"operateur": "<=", "valeur": 3}}, 4, False),
        ({"seuil": {"operateur": ">", "valeur": 0}}, True, False),  # un booléen n'est pas compté
        ({"seuil": {"operateur": ">", "valeur": 0}}, "5", False),
        ({"presente": True}, False, True),
        # Liste : satisfaite si un élément l'est.
        ({"egal": "b"}, ("a", "b"), True),
        ({"egal": "c"}, ("a", "b"), False),
        ({"presente": True}, (), True),
    ],
)
def test_condition(test: dict[str, Any], valeur: Valeur, attendu: bool) -> None:
    assert condition(**test).satisfaite(valeur) is attendu


@pytest.mark.parametrize(
    ("test", "attendu"),
    [
        pytest.param({}, "un test et un seul", id="aucun-test"),
        pytest.param({"egal": 1, "parmi": [1]}, "un test et un seul", id="deux-tests"),
        pytest.param({"egal": float("nan")}, "nombre fini", id="nan"),
        pytest.param({"parmi": [float("inf")]}, "nombre fini", id="infini"),
        pytest.param({"parmi": []}, "de 1 à 4096", id="parmi-vide"),
        pytest.param({"egal": ""}, "texte vide", id="texte-vide"),
        pytest.param({"egal": None, "parmi": [[1]]}, "texte, nombre", id="liste-dans-parmi"),
        pytest.param({"motif": "(a)\\1"}, "refusé par RE2", id="reference-arriere"),
        pytest.param({"motif": "(?=a)"}, "refusé par RE2", id="assertion-de-contexte"),
        pytest.param({"motif": "x" * 1025}, "trop long", id="motif-trop-long"),
        pytest.param({"motif": "\\pL{5}"}, "trop grand", id="programme-trop-grand"),
        pytest.param({"motif": "\\pL{1000}"}, "refusé par RE2", id="memoire-depassee"),
        pytest.param({"seuil": {"operateur": ">", "valeur": True}}, "nombre", id="seuil-booleen"),
        pytest.param({"presente": True, "parametre": "a b"}, "parametre", id="parametre"),
    ],
)
def test_condition_refusee(test: dict[str, Any], attendu: str) -> None:
    with pytest.raises(ValueError, match=attendu):
        condition(**test)


def test_condition_aller_retour() -> None:
    for test in (
        {"egal": "a", "parametre": "p"},
        {"parmi": [1, "a", True]},
        {"motif": "^a"},
        {"seuil": {"operateur": "<=", "valeur": 2.5}},
        {"presente": True},
    ):
        document = {"observation": "n"} | test
        assert condition(**test).vers_dict() == document


def test_seuil_entier_ou_reel() -> None:
    assert condition(seuil={"operateur": ">=", "valeur": 2.5}).satisfaite(3)
    with pytest.raises(ValueError, match="nombre fini"):
        Seuil(Comparaison.SUPERIEUR, 2.0**64)


def test_motif_refuse_sans_ecrire_sur_la_sortie_d_erreur() -> None:
    # RE2 journalise ses erreurs sur la sortie d'erreur, sauf si on le lui interdit.
    code = (
        "from voight_kampff._regles import Condition\n"
        "try:\n"
        "    Condition('n', motif='(?=a)')\n"
        "except ValueError:\n"
        "    pass\n"
    )
    resultat = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True
    )
    assert resultat.stderr == ""


# Règles


def evaluee(niveau: str, **evaluation: Any) -> dict[str, Any]:
    """Champs d'un indice évalué, au niveau donné ; ``evaluation`` modifie son évaluation."""
    return {
        "categorie": "indice",
        "direction": "origine_ia",
        "niveau": niveau,
        "evaluation": {
            "taux_faux_positifs": 0.002,
            "effectif": 1500,
            "borne_superieure": 0.0059,
            "corpus": "1",
            "date": "2026-10-01",
        }
        | evaluation,
    }


@pytest.mark.parametrize(
    ("borne", "niveau"),
    [(0.0, "fort"), (0.01, "fort"), (0.0101, "modere"), (0.05, "modere"), (0.0501, "faible")],
)
def test_niveau_permis_par_la_borne(borne: float, niveau: str) -> None:
    assert niveau_permis(borne) is Niveau(niveau)
    regle(**evaluee(niveau, taux_faux_positifs=0.0, borne_superieure=borne))


def test_regle_lue_et_reecrite() -> None:
    document = regle_dict(
        "R-META-001",
        "metadonnees",
        categorie="indice",
        direction="origine_ia",
        fondement="declaration",
        niveau="modere",
        evaluation={
            "taux_faux_positifs": 0.004,
            "effectif": 500,
            "borne_superieure": 0.0145,
            "corpus": "2026.1",
            "date": "2026-10-01",
        },
        calibrage={"methode": "corpus", "procedure": "Seuil au 99e centile.", "corpus": "2026.1"},
        **moteur(
            {"observation": "exif.ifd0.Software", "motif": "^Midjourney", "parametre": "logiciel"},
            {"observation": "largeur", "seuil": {"operateur": ">", "valeur": 512}},
        ),
    )
    lue = Regle.depuis_dict(document)
    assert lue.vers_dict() == document
    manuelle = document | {"calibrage": {"methode": "manuelle", "procedure": "Seuil de la norme."}}
    assert Regle.depuis_dict(manuelle).vers_dict() == manuelle
    assert lue.reference == ReferenceRegle("R-META-001", "1")
    assert lue.graduation == Graduation(Niveau.MODERE, evaluee=True)
    assert lue.noms_des_parametres == ("logiciel",)
    assert lue.application is Application.MOTEUR


@pytest.mark.parametrize(
    ("champs", "attendu"),
    [
        pytest.param({"identifiant": "F-21"}, "identifiant", id="identifiant-d-exigence"),
        pytest.param({"identifiant": "R-" + "A" * 40 + "-001"}, "valeur invalide", id="trop-long"),
        pytest.param({"version": "1.0"}, "version", id="version-non-entiere"),
        pytest.param({"module": "Alpha"}, "module", id="module"),
        pytest.param({"gabarit": "Gabarit"}, "gabarit", id="gabarit"),
        pytest.param({"titre": ""}, "titre", id="titre-vide"),
        pytest.param({"limites": []}, "limites", id="sans-limite"),
        pytest.param({"parametres": ["a", "a"]}, "doublon", id="parametres-en-double"),
        pytest.param(moteur(), "condition", id="moteur-sans-condition"),
        pytest.param(
            moteur({"observation": "n", "presente": True}, parametres=["a"]),
            "condition",
            id="moteur-avec-parametres",
        ),
        pytest.param(
            {"condition": [{"observation": "n", "presente": True}]},
            "aucune condition",
            id="module-avec-condition",
        ),
        pytest.param({"niveau": "faible"}, "réservé aux indices", id="niveau-hors-indice"),
        pytest.param(
            moteur({"observation": "n", "seuil": {"operateur": ">", "valeur": 1}}),
            "calibrage",
            id="seuil-sans-calibrage",
        ),
        pytest.param(
            {"calibrage": {"methode": "corpus", "procedure": "p"}},
            "calibrage.corpus",
            id="calibrage-sans-corpus",
        ),
        pytest.param(
            {"categorie": "indice", "direction": "origine_ia"}, "un indice a un niveau", id="indice"
        ),
        pytest.param(
            {"categorie": "indice", "direction": "origine_ia", "niveau": "fort"},
            "non évaluée",
            id="indice-fort-non-evalue",
        ),
        pytest.param(
            {"categorie": "preuve", "fondement": "declaration"},
            "preuve repose sur une vérification",
            id="preuve-sur-declaration",
        ),
        pytest.param({"direction": "origine_ia"}, "information neutre", id="neutre-dirigee"),
        pytest.param(evaluee("faible", taux_faux_positifs=1.5), "taux", id="taux-hors-bornes"),
        pytest.param(evaluee("faible", borne_superieure=0.001), "borne", id="borne-sous-le-taux"),
        pytest.param(evaluee("faible", borne_superieure="0.1"), "borne", id="borne-en-texte"),
        pytest.param(evaluee("faible", effectif=0), "effectif", id="effectif-nul"),
        pytest.param(evaluee("faible", effectif=True), "effectif", id="effectif-booleen"),
        pytest.param(evaluee("fort", borne_superieure=0.0101), "plus élevé", id="fort-trop-haut"),
        pytest.param(
            evaluee("modere", borne_superieure=0.051), "plus élevé", id="modere-trop-haut"
        ),
        pytest.param({"phrase": {"en": "Test."}}, "français", id="phrase-sans-francais"),
        pytest.param(
            {"phrase": {"fr": "Test.", "en": "Test."}}, "français", id="phrase-autre-langue"
        ),
        pytest.param({"phrase": {"fr": ""}}, "vide", id="phrase-vide"),
        pytest.param({"phrase": {"fr": "x" * 1025}}, "trop long", id="phrase-trop-longue"),
        pytest.param(
            {"phrase": {"fr": "Valeur {absent}."}}, "emplacements", id="emplacement-inconnu"
        ),
        pytest.param(
            {"parametres": ["a"], "phrase": {"fr": "Sans emplacement."}},
            "emplacements",
            id="parametre-non-cite",
        ),
        pytest.param({"phrase": {"fr": "Accolade { seule."}}, "accolade", id="accolade-ouvrante"),
        pytest.param({"phrase": {"fr": "Accolade } seule."}}, "accolade", id="accolade-fermante"),
        pytest.param({"phrase": {"fr": "{{double}}"}}, "accolade", id="accolades-doublees"),
        pytest.param({"phrase": {"fr": "Nom {a b}."}}, "regle.phrase", id="emplacement-invalide"),
    ],
)
def test_regle_refusee(champs: dict[str, Any], attendu: str) -> None:
    with pytest.raises(ValueError, match=attendu):
        regle(**champs)


# Évaluation


def observation(numero: int, nom: str, valeur: Valeur) -> Observation:
    return Observation(f"alpha/{numero}", "alpha", nom, valeur)


OBSERVATIONS = (
    observation(1, "logiciel", "Éditeur"),
    observation(2, "logiciel", "Générateur 3"),
    observation(3, "logiciel", "Générateur 4"),
    observation(4, "largeur", 1024),
)


def test_premiere_observation_retenue_par_condition() -> None:
    regles = [
        regle(
            "R-TEST-001",
            **moteur(
                {"observation": "logiciel", "motif": "^Générateur", "parametre": "logiciel"},
                {"observation": "largeur", "presente": True},
                {"observation": "logiciel", "egal": "Générateur 3"},
            ),
        ),
        regle("R-TEST-002", **moteur({"observation": "hauteur", "presente": True})),
        regle("R-TEST-003", gabarit="test.module"),  # règle du module : jamais par le moteur
        regle("R-TEST-004", **moteur({"observation": "largeur", "egal": 1024})),
    ]
    resultats = [(r.identifiant, d, p) for r, d, p in appliquer(regles, OBSERVATIONS)]
    assert resultats == [
        # Une même observation retenue par deux conditions n'est citée qu'une fois.
        ("R-TEST-001", ("alpha/2", "alpha/4"), {"logiciel": "alpha/2"}),
        ("R-TEST-004", ("alpha/4",), {}),
    ]


def test_conforme() -> None:
    indice = regle(
        "R-TEST-001",
        categorie="indice",
        direction="origine_ia",
        niveau="faible",
        parametres=["valeur"],
    )
    constat = Constat(
        Phrase("test.regle", {"valeur": "alpha/1"}),
        ("alpha/1",),
        ReferenceRegle("R-TEST-001", "1"),
        "alpha",
        Fondement.MESURE,
        Categorie.INDICE,
        Direction.ORIGINE_IA,
        graduation=Graduation(Niveau.FAIBLE, evaluee=False),
    )
    assert conforme(indice, constat)
    ecarts: list[dict[str, Any]] = [
        {"regle": ReferenceRegle("R-TEST-001", "2")},
        {"module": "beta"},
        {"phrase": Phrase("autre", {"valeur": "alpha/1"})},
        {"phrase": Phrase("test.regle")},
        {"direction": Direction.RETOUCHE},
        {"fondement": Fondement.DECLARATION},
    ]
    for ecart in ecarts:
        assert not conforme(indice, dataclasses.replace(constat, **ecart))
    neutre = regle("R-TEST-001", parametres=["valeur"])
    assert not conforme(neutre, constat)


# Phrase de la règle (T16, ADR-0091)


def test_phrase_et_ses_emplacements() -> None:
    lue = regle(parametres=["a.b", "c"], phrase={"fr": "« {a.b} » puis {c}, encore {a.b}."})
    assert lue.textes == {"fr": "« {a.b} » puis {c}, encore {a.b}."}
    assert emplacements(lue.textes["fr"]) == ("a.b", "c", "a.b")
    assert lue.vers_dict()["phrase"] == {"fr": "« {a.b} » puis {c}, encore {a.b}."}
    # Remplacement littéral : ni attribut suivi (« a.b »), ni accolade d'une valeur interprétée.
    rendu = remplir(lue.textes["fr"], {"a.b": "{c}", "c": "{0.__class__}"})
    assert rendu == "« {c} » puis {0.__class__}, encore {c}."


def test_phrase_figee() -> None:
    textes = {"fr": "Phrase de test"}
    lue = Regle.depuis_dict(regle_dict(phrase=textes))
    textes["fr"] = "modifiée"
    assert lue.textes["fr"] == "Phrase de test"
    with pytest.raises(TypeError):
        lue.textes["fr"] = "modifiée"  # type: ignore[index]
