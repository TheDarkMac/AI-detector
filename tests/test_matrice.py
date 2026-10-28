"""Tests de la matrice de vérification (T17, ADR-0024, ADR-0102).

La vraie matrice est vérifiée par ``python -m banc.matrice --verifier``, lancé ici comme par la
CI : elle doit être cohérente avec le cahier, le modèle de menace et les marqueurs des tests, et
``matrice.md`` doit être à jour. Les contrôles eux-mêmes sont testés sur de petites matrices.
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import conftest
import pytest

from banc import matrice
from banc.matrice import Entree, Matrice

RACINE = Path(__file__).resolve().parent.parent


def test_matrice_du_depot_a_jour() -> None:
    fini = subprocess.run(
        [sys.executable, "-m", "banc.matrice", "--verifier"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=RACINE,
        check=False,
    )
    assert fini.returncode == 0, fini.stderr


def test_exigences_lues_a_leur_source() -> None:
    exigences, cas = matrice.connues(matrice.lire())
    familles = [identifiant.split("-")[0] for identifiant in exigences]
    assert (familles.count("F"), familles.count("NF")) == (48, 19)
    assert (familles.count("ES"), familles.count("P")) == (22, 6)
    assert list(cas) == ["CU-1", "CU-2", "CU-3", "CU-4", "CU-5"]
    assert exigences["NF-01"].startswith("Tout fichier est traité comme hostile")
    assert exigences["ES-11"].startswith("Le banc d'évaluation exécute l'analyse")
    assert exigences["P-03"].startswith("Preuve ≠ indice : ")


# Contrôles

EXIGENCES = {"F-01": "a", "NF-01": "b", "P-01": "c"}
CAS = {"CU-1": "analyser"}


def entree(identifiant: str, **champs: Any) -> Entree:
    document = {"id": identifiant, "etat": "realisee", "taches": ("T13",), "methodes": ("test",)}
    return Entree(**(document | champs))


def petite(*entrees: Entree, **champs: Any) -> Matrice:
    return Matrice(
        champs.get("principes", {"P-01": "Nom : texte"}),
        entrees or (entree("F-01"), entree("NF-01"), entree("P-01")),
        champs.get("cas", {"CU-1": ("F-01",)}),
    )


TESTS = {"F-01": ["t::a"], "NF-01": ["t::b"], "P-01": ["t::c"]}


def test_matrice_coherente() -> None:
    assert matrice.verifier(petite(), EXIGENCES, CAS, TESTS) == []


@pytest.mark.parametrize(
    ("entrees", "tests", "attendu"),
    [
        pytest.param(
            {"F-01": {"etat": "fini"}}, {"NF-01": ["t"], "P-01": ["t"]}, "état inconnu", id="etat"
        ),
        pytest.param({"F-01": {"taches": ("13",)}}, TESTS, "tâches", id="taches"),
        pytest.param({"F-01": {"methodes": ("test", "test")}}, TESTS, "méthodes", id="doublon"),
        pytest.param(
            {"F-01": {"methodes": ("test", "essai"), "justification": "j", "etat": "partielle"}},
            TESTS,
            "méthodes",
            id="inconnue",
        ),
        pytest.param(
            {"F-01": {"methodes": ()}}, {"NF-01": ["t"], "P-01": ["t"]}, "méthodes", id="aucune"
        ),
        pytest.param(
            {"NF-01": {"methodes": ("inspection",), "etat": "partielle"}},
            {"F-01": ["t"], "P-01": ["t"]},
            "sans justification",
            id="justification",
        ),
        pytest.param(
            {"NF-01": {"methodes": ("inspection",), "justification": "j"}},
            {"F-01": ["t"], "P-01": ["t"]},
            "sans preuve ni résultat",
            id="preuve",
        ),
        pytest.param(
            {"NF-01": {"preuve": ("docs/absent.md",)}}, TESTS, "preuve introuvable", id="absente"
        ),
        pytest.param(
            {"F-01": {"etat": "hors_v1"}}, {"NF-01": ["t"], "P-01": ["t"]}, "hors V1", id="hors-v1"
        ),
        pytest.param({}, {"NF-01": ["t"], "P-01": ["t"]}, "aucun test ne la cite", id="sans-test"),
        pytest.param(
            {"F-01": {"etat": "a_venir"}}, TESTS, "ni réalisée ni testée", id="test-a-venir"
        ),
        pytest.param({}, TESTS | {"F-99": ["t"]}, "F-99 : citée par un test", id="test-inconnu"),
    ],
)
def test_incoherence_relevee(
    entrees: dict[str, dict[str, Any]], tests: dict[str, list[str]], attendu: str
) -> None:
    lignes = tuple(
        Entree(
            **(
                {"id": i, "etat": "realisee", "taches": ("T13",), "methodes": ("test",)}
                | entrees.get(i, {})
            )
        )
        for i in ("F-01", "NF-01", "P-01")
    )
    erreurs = matrice.verifier(petite(*lignes), EXIGENCES, CAS, tests)
    assert len(erreurs) == 1
    assert attendu in erreurs[0]


def test_liste_des_exigences_relevee() -> None:
    erreurs = matrice.verifier(
        petite(
            entree("F-01"),
            entree("F-01"),
            entree("F-02"),
            principes={"P-1": "x"},
            cas={"CU-1": ("F-09",), "CU-9": ()},
        ),
        EXIGENCES,
        CAS | {"CU-2": "b"},
        {"F-01": ["t"], "F-02": ["t"]},
    )
    assert erreurs == [
        "principe mal numéroté : P-1",
        "F-01 : en double",
        "F-02 : inconnue",
        "NF-01 : absente de la matrice",
        "P-01 : absente de la matrice",
        "CU-9 : cas d'usage inconnu",
        "CU-2 : cas d'usage absent de la matrice",
        "CU-1 : exigence inconnue F-09",
    ]


def test_lecture(tmp_path: Path) -> None:
    lue = matrice.lire()
    assert len(lue.entrees) == 95
    assert lue.principes["P-06"].startswith("Modularité : ")
    with pytest.raises(matrice.MatriceInvalide, match="illisible"):
        matrice.lire(tmp_path / "absente.toml")
    (tmp_path / "m.toml").write_text("format = 2\n", encoding="utf-8")
    with pytest.raises(matrice.MatriceInvalide, match="format"):
        matrice.lire(tmp_path / "m.toml")
    (tmp_path / "m.toml").write_text("format = 1\n", encoding="utf-8")
    with pytest.raises(matrice.MatriceInvalide, match="incomplète"):
        matrice.lire(tmp_path / "m.toml")


# Tests collectés et résultats

JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest">
<testcase classname="tests.test_a" name="test_x" />
<testcase classname="tests.test_a" name="test_y[p::q]"><failure message="f" /></testcase>
<testcase classname="tests.test_b.TestC" name="test_z"><skipped message="s" /></testcase>
<testcase classname="tests.test_b" name="test_e"><error message="e" /></testcase>
</testsuite></testsuites>
"""


def test_resultats_d_un_passage(tmp_path: Path) -> None:
    (tmp_path / "junit.xml").write_text(JUNIT, encoding="utf-8")
    statuts = matrice.lire_junit(tmp_path / "junit.xml")
    assert matrice._cle_junit("tests/test_a.py::test_y[p::q]") == ("tests.test_a", "test_y[p::q]")
    assert matrice._cle_junit("tests/test_b.py::TestC::test_z") == ("tests.test_b.TestC", "test_z")
    tests = matrice.par_exigence(
        {
            "tests/test_a.py::test_x": ("F-01", "F-01"),
            "tests/test_a.py::test_y[p::q]": ("F-01",),
            "tests/test_b.py::TestC::test_z": ("F-01", "NF-01"),
            "tests/test_b.py::test_e": ("NF-01",),
            "tests/test_b.py::test_absent": ("NF-01", "P-01"),
            "tests/test_b.py::test_sans": (),
        }
    )
    assert tests["F-01"] == [
        "tests/test_a.py::test_x",
        "tests/test_a.py::test_y[p::q]",
        "tests/test_b.py::TestC::test_z",
    ]
    texte = matrice.rendre(petite(), EXIGENCES, CAS, tests, statuts)
    assert "Résultat des tests : passage de pytest joint à cette matrice." in texte
    assert "| tests : 1 réussi, 1 sauté, 1 échec |" in texte
    assert "tests : `test_a.py`, `test_b.py`" in texte
    assert "tests : 1 non exécuté, 1 sauté, 1 échec" in texte
    # Sans résultats : renvoi à la CI.
    assert "tests : CI" in matrice.rendre(petite(), EXIGENCES, CAS, tests)


def test_rendu() -> None:
    texte = matrice.rendre(
        petite(
            entree("F-01", note="N|ote"),
            entree(
                "NF-01",
                methodes=("test", "inspection"),
                justification="J",
                preuve=("docs/glossaire.md",),
                resultat="R",
            ),
            entree("P-01", etat="a_venir"),
        ),
        EXIGENCES,
        CAS,
        {"F-01": ["tests/test_a.py::t"], "NF-01": ["tests/test_a.py::t"]},
    )
    assert "| Exigences fonctionnelles (cahier, §5) | 1 | 0 | 0 | 0 | 1 |" in texte
    assert (
        "| F-01 | a | réalisée | T13 | test | tests : `test_a.py` | tests : CI | N\\|ote |" in texte
    )
    assert (
        "| NF-01 | b | réalisée | T13 | test, inspection | tests : `test_a.py` ; preuve : "
        "[glossaire.md](../../docs/glossaire.md) ; justification : J | tests : CI ; R | — |"
    ) in texte
    assert "| P-01 | c | à venir | T13 | test | — | — | — |" in texte
    assert "| CU-1 | analyser | F-01 |" in texte


def test_collecte(monkeypatch: pytest.MonkeyPatch) -> None:
    def item(nodeid: str, *marqueurs: tuple[str, ...]) -> SimpleNamespace:
        return SimpleNamespace(
            nodeid=nodeid,
            iter_markers=lambda nom: [SimpleNamespace(args=args) for args in marqueurs],
        )

    def principal(arguments: list[str], plugins: list[Any]) -> int:
        assert "--collect-only" in arguments
        session = SimpleNamespace(items=[item("t::a", ("F-01",), ("NF-01",)), item("t::b")])
        plugins[0].pytest_collection_finish(session)
        print("sortie de pytest, gardée pour l'erreur")
        return 0

    monkeypatch.setattr(pytest, "main", principal)
    assert matrice.collecter() == {"t::a": ("F-01", "NF-01"), "t::b": ()}
    monkeypatch.setattr(pytest, "main", lambda arguments, plugins: 4)
    with pytest.raises(matrice.MatriceInvalide, match="code 4"):
        matrice.collecter()


# Commande, dans le processus des tests (la collecte réelle est lancée à part, plus haut)


@pytest.fixture
def factice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matrice, "lire", petite)
    monkeypatch.setattr(matrice, "connues", lambda _m: (EXIGENCES, CAS))
    monkeypatch.setattr(matrice, "collecter", lambda: {f"t::{i}": (i,) for i in EXIGENCES})


@pytest.mark.usefixtures("factice")
def test_commande(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cible = tmp_path / "matrice.md"
    assert matrice.main(["--sortie", str(cible), "--verifier"]) == 1
    assert "matrice.md n'est pas à jour" in capsys.readouterr().err
    assert matrice.main(["--sortie", str(cible)]) == 0
    assert matrice.main(["--sortie", str(cible), "--verifier"]) == 0
    cible.write_text("ancienne\n", encoding="utf-8")
    assert matrice.main(["--sortie", str(cible), "--verifier"]) == 1
    (tmp_path / "junit.xml").write_text(JUNIT, encoding="utf-8")
    assert matrice.main(["--sortie", str(cible), "--resultats", str(tmp_path / "junit.xml")]) == 0
    assert "tests : 1 non exécuté" in cible.read_text(encoding="utf-8")


@pytest.mark.usefixtures("factice")
def test_commande_en_echec(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert matrice.main(["--resultats", str(tmp_path / "absent.xml")]) == 2
    monkeypatch.setattr(matrice, "collecter", dict)
    assert matrice.main(["--sortie", str(tmp_path / "m.md")]) == 1
    erreurs = capsys.readouterr().err.splitlines()
    assert erreurs[0].startswith("matrice : ")
    assert erreurs[1:] == [
        "matrice : F-01 : vérifiée par test, mais aucun test ne la cite",
        "matrice : NF-01 : vérifiée par test, mais aucun test ne la cite",
        "matrice : P-01 : vérifiée par test, mais aucun test ne la cite",
    ]
    assert not (tmp_path / "m.md").exists()


# Marqueurs des tests


def test_marqueur_inconnu_refuse() -> None:
    def item(*args: str) -> pytest.Item:
        marqueurs = [SimpleNamespace(args=args)]
        return cast(pytest.Item, SimpleNamespace(nodeid="t::x", iter_markers=lambda nom: marqueurs))

    conftest.pytest_collection_modifyitems([item("F-01", "NF-02")])
    with pytest.raises(pytest.UsageError, match="exigence inconnue F-99"):
        conftest.pytest_collection_modifyitems([item("F-01", "F-99")])
    with pytest.raises(pytest.UsageError, match=r"\(aucune\)"):
        conftest.pytest_collection_modifyitems([item()])
