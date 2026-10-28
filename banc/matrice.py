"""Matrice de vérification : exigence → méthode → résultat (ADR-0024, ADR-0102).

Les exigences connues sont lues à leur source : F et NF dans le cahier des charges, ES dans le
modèle de menace, principes P dans la matrice elle-même (A-11), cas d'usage CU dans le cahier
(A-27). ``docs/verification/matrice.toml`` porte, pour chacune, l'état, les tâches, les méthodes
et le résultat des méthodes autres que « test » ; les tests la citent par le marqueur
``exigence``. Ce module vérifie que les deux concordent et en tire ``matrice.md``.

Usage, depuis la racine du dépôt :

- ``python -m banc.matrice`` : écrit ``docs/verification/matrice.md`` ;
- ``python -m banc.matrice --verifier`` : échoue si la matrice est incohérente ou si
  ``matrice.md`` n'est pas à jour (CI) ;
- ``python -m banc.matrice --resultats JUNIT --sortie FICHIER`` : matrice avec le résultat de
  chaque test d'un passage de pytest (``--junitxml``), jointe à la CI.
"""

import argparse
import contextlib
import io
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["Matrice", "MatriceInvalide", "connues", "lire", "main", "rendre", "verifier"]

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "docs" / "verification"
MATRICE = DOSSIER / "matrice.toml"
SORTIE = DOSSIER / "matrice.md"
CAHIER = RACINE / "docs" / "00-cahier-des-charges" / "cahier-des-charges-v0.1.md"
MENACE = RACINE / "docs" / "modele-de-menace" / "modele-de-menace.md"

ETATS = {
    "realisee": "réalisée",
    "partielle": "partielle",
    "a_venir": "à venir",
    "hors_v1": "hors V1",
}
METHODES = ("test", "inspection", "analyse", "demonstration")
EN_COURS = frozenset({"realisee", "partielle"})
"""États où une méthode de vérification doit déjà pouvoir s'appliquer."""

FAMILLES = (
    ("F", "Exigences fonctionnelles (cahier, §5)"),
    ("NF", "Exigences non fonctionnelles (cahier, §7)"),
    ("ES", "Exigences de sécurité (modèle de menace, §8)"),
    ("P", "Principes directeurs (cahier, §2 ; A-11)"),
)

_LIGNE_CAHIER = re.compile(r"\| ((?:F|NF)-[0-9]{2}) \| (.*) \|")
_LIGNE_MENACE = re.compile(r"\| (ES-[0-9]{2}) \| (.*) \|")
_CAS = re.compile(r"- (CU-[0-9]) : (.*)")
_PRINCIPE = re.compile(r"P-0[1-9]")
_TACHE = re.compile(r"T[0-9]{2,3}")


class MatriceInvalide(ValueError):
    """Matrice illisible ou de forme incorrecte."""


@dataclass(frozen=True, slots=True)
class Entree:
    """Une exigence dans la matrice."""

    id: str
    etat: str
    taches: tuple[str, ...]
    methodes: tuple[str, ...]
    justification: str | None = None
    preuve: tuple[str, ...] = ()
    resultat: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class Matrice:
    principes: Mapping[str, str]
    """Identifiant → « nom : texte »."""
    entrees: tuple[Entree, ...]
    cas: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


def _famille(identifiant: str) -> str:
    return identifiant.split("-", 1)[0]


def exigences_du_cahier(texte: str) -> tuple[dict[str, str], dict[str, str]]:
    """Exigences F et NF (dernière cellule de leur ligne), et cas d'usage du cahier."""
    exigences, cas = {}, {}
    for ligne in texte.splitlines():
        if trouve := _LIGNE_CAHIER.fullmatch(ligne.strip()):
            exigences[trouve[1]] = trouve[2].split(" | ")[-1]
        elif trouve := _CAS.fullmatch(ligne.strip()):
            cas[trouve[1]] = trouve[2]
    return exigences, cas


def exigences_de_securite(texte: str) -> dict[str, str]:
    """Exigences ES du modèle de menace (première cellule après l'identifiant)."""
    return {
        trouve[1]: trouve[2].split(" | ")[0]
        for ligne in texte.splitlines()
        if (trouve := _LIGNE_MENACE.fullmatch(ligne.strip()))
    }


def lire(chemin: Path = MATRICE) -> Matrice:
    try:
        document = tomllib.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as erreur:
        raise MatriceInvalide(f"matrice illisible : {erreur}") from None
    try:
        if document["format"] != 1:
            raise MatriceInvalide("format de matrice inconnu")
        principes = {p["id"]: f"{p['nom']} : {p['texte']}" for p in document["principe"]}
        entrees = tuple(
            Entree(
                id=e["id"],
                etat=e["etat"],
                taches=tuple(e["taches"]),
                methodes=tuple(e["methodes"]),
                justification=e.get("justification"),
                preuve=tuple(e.get("preuve", ())),
                resultat=e.get("resultat"),
                note=e.get("note"),
            )
            for e in document["exigence"]
        )
        cas = {c["id"]: tuple(c["exigences"]) for c in document["cas_d_usage"]}
    except (KeyError, TypeError) as erreur:
        raise MatriceInvalide(f"matrice incomplète : {erreur}") from None
    return Matrice(principes, entrees, cas)


def connues(matrice: Matrice) -> tuple[dict[str, str], dict[str, str]]:
    """Exigences connues (identifiant → texte), et cas d'usage du cahier."""
    exigences, cas = exigences_du_cahier(CAHIER.read_text(encoding="utf-8"))
    exigences |= exigences_de_securite(MENACE.read_text(encoding="utf-8"))
    exigences |= matrice.principes
    return exigences, cas


def identifiants() -> frozenset[str]:
    """Identifiants que les marqueurs des tests peuvent citer : ceux de la matrice."""
    return frozenset(entree.id for entree in lire().entrees)


def _verifier_entree(entree: Entree, racine: Path) -> list[str]:
    erreurs = []
    if entree.etat not in ETATS:
        erreurs.append(f"{entree.id} : état inconnu « {entree.etat} »")
    if not entree.taches or not all(_TACHE.fullmatch(t) for t in entree.taches):
        erreurs.append(f"{entree.id} : tâches absentes ou mal écrites")
    if (
        not entree.methodes
        or len(set(entree.methodes)) != len(entree.methodes)
        or not set(entree.methodes) <= set(METHODES)
    ):
        erreurs.append(f"{entree.id} : méthodes absentes, en double ou inconnues")
    autres = set(entree.methodes) - {"test"}
    if autres and not entree.justification:
        erreurs.append(f"{entree.id} : méthode autre que « test » sans justification (ADR-0024)")
    if autres and entree.etat == "realisee" and not (entree.preuve and entree.resultat):
        erreurs.append(f"{entree.id} : réalisée sans preuve ni résultat pour {sorted(autres)}")
    if entree.etat == "hors_v1" and not entree.note:
        erreurs.append(f"{entree.id} : hors V1 sans la décision qui l'y place")
    erreurs += [
        f"{entree.id} : preuve introuvable : {document}"
        for document in entree.preuve
        if not (racine / document).exists()
    ]
    return erreurs


def verifier(
    matrice: Matrice,
    exigences: Mapping[str, str],
    cas: Mapping[str, str],
    tests: Mapping[str, Sequence[str]],
    racine: Path = RACINE,
) -> list[str]:
    """Incohérences de la matrice ; ``tests`` donne les tests de chaque exigence citée."""
    erreurs = [
        f"principe mal numéroté : {identifiant}"
        for identifiant in matrice.principes
        if not _PRINCIPE.fullmatch(identifiant)
    ]
    vus = Counter(entree.id for entree in matrice.entrees)
    erreurs += [f"{identifiant} : en double" for identifiant, n in vus.items() if n > 1]
    erreurs += [f"{identifiant} : inconnue" for identifiant in vus if identifiant not in exigences]
    erreurs += [
        f"{identifiant} : absente de la matrice"
        for identifiant in exigences
        if not vus[identifiant]
    ]
    for entree in matrice.entrees:
        erreurs += _verifier_entree(entree, racine)
        testee = "test" in entree.methodes and entree.etat in EN_COURS
        if testee and not tests.get(entree.id):
            erreurs.append(f"{entree.id} : vérifiée par test, mais aucun test ne la cite")
        if tests.get(entree.id) and not testee:
            erreurs.append(f"{entree.id} : citée par des tests, mais ni réalisée ni testée")
    erreurs += [
        f"{identifiant} : citée par un test, inconnue"
        for identifiant in tests
        if not vus[identifiant]
    ]
    erreurs += [
        f"{identifiant} : cas d'usage inconnu"
        for identifiant in matrice.cas
        if identifiant not in cas
    ]
    erreurs += [
        f"{identifiant} : cas d'usage absent de la matrice"
        for identifiant in cas
        if identifiant not in matrice.cas
    ]
    erreurs += [
        f"{identifiant} : exigence inconnue {exigence}"
        for identifiant, liees in matrice.cas.items()
        for exigence in liees
        if exigence not in exigences
    ]
    return erreurs


# Tests et résultats


class _Collecteur:
    """Greffon pytest : exigences citées par chaque test collecté."""

    def __init__(self) -> None:
        self.tests: dict[str, tuple[str, ...]] = {}

    def pytest_collection_finish(self, session: Any) -> None:
        for item in session.items:
            self.tests[item.nodeid] = tuple(
                identifiant
                for marqueur in item.iter_markers("exigence")
                for identifiant in marqueur.args
            )


def collecter() -> dict[str, tuple[str, ...]]:
    """Collecte les tests du dépôt (sans les exécuter) et leurs exigences."""
    import pytest  # importé ici : outil de développement, absent à l'exécution du banc

    collecteur = _Collecteur()
    sortie = io.StringIO()
    with contextlib.redirect_stdout(sortie):
        code = pytest.main(
            ["--collect-only", "-q", "-p", "no:cacheprovider", str(RACINE / "tests")],
            plugins=[collecteur],
        )
    if code != 0:
        raise MatriceInvalide(f"collecte des tests en échec (code {code}) :\n{sortie.getvalue()}")
    return collecteur.tests


def par_exigence(tests: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
    exigences: defaultdict[str, list[str]] = defaultdict(list)
    for nodeid, identifiants_du_test in tests.items():
        for identifiant in dict.fromkeys(identifiants_du_test):
            exigences[identifiant].append(nodeid)
    return dict(exigences)


def _cle_junit(nodeid: str) -> tuple[str, str]:
    """Classe et nom d'un test dans le rapport JUnit de pytest (``mangle_test_address``)."""
    chemin, crochet, parametres = nodeid.partition("[")
    noms = chemin.split("::")
    noms[0] = re.sub(r"\.py$", "", noms[0].replace("/", "."))
    noms[-1] += crochet + parametres
    return ".".join(noms[:-1]), noms[-1]


def lire_junit(chemin: Path) -> dict[tuple[str, str], str]:
    """Statut de chaque test : « réussi », « échec » ou « sauté »."""
    racine = ET.parse(chemin).getroot()  # noqa: S314 (fichier écrit par notre propre pytest)
    statuts = {}
    for cas in racine.iter("testcase"):
        if cas.find("failure") is not None or cas.find("error") is not None:
            statut = "échec"
        elif cas.find("skipped") is not None:
            statut = "sauté"
        else:
            statut = "réussi"
        statuts[cas.get("classname", ""), cas.get("name", "")] = statut
    return statuts


# Rendu


def _cellule(texte: str) -> str:
    return texte.replace("|", "\\|")


def _fichiers(nodeids: Sequence[str]) -> str:
    noms = dict.fromkeys(nodeid.split("::", 1)[0].rsplit("/", 1)[-1] for nodeid in nodeids)
    return ", ".join(f"`{nom}`" for nom in noms)


def _resultat_des_tests(
    nodeids: Sequence[str], statuts: Mapping[tuple[str, str], str] | None
) -> str:
    if statuts is None:
        return "tests : CI"
    compte = Counter(statuts.get(_cle_junit(nodeid), "non exécuté") for nodeid in nodeids)
    pluriels = {
        "réussi": "réussis",
        "échec": "échecs",
        "sauté": "sautés",
        "non exécuté": "non exécutés",
    }
    return "tests : " + ", ".join(
        f"{n} {pluriels[s] if n > 1 else s}" for s, n in sorted(compte.items())
    )


def _ligne(
    entree: Entree,
    texte: str,
    tests: Sequence[str],
    statuts: Mapping[tuple[str, str], str] | None,
) -> str:
    verification, resultat = [], []
    if tests:
        verification.append("tests : " + _fichiers(tests))
    if entree.preuve:
        liens = (f"[{Path(p).name}](../../{p})" for p in entree.preuve)
        verification.append("preuve : " + ", ".join(liens))
    if entree.justification:
        verification.append("justification : " + entree.justification)
    if entree.etat in EN_COURS:
        if tests:
            resultat.append(_resultat_des_tests(tests, statuts))
        if entree.resultat:
            resultat.append(entree.resultat)
    cellules = [
        entree.id,
        texte,
        ETATS.get(entree.etat, entree.etat),
        ", ".join(entree.taches),
        ", ".join(entree.methodes),
        " ; ".join(verification) or "—",
        " ; ".join(resultat) or "—",
        entree.note or "—",
    ]
    return "| " + " | ".join(map(_cellule, cellules)) + " |"


def rendre(
    matrice: Matrice,
    exigences: Mapping[str, str],
    cas: Mapping[str, str],
    tests: Mapping[str, Sequence[str]],
    statuts: Mapping[tuple[str, str], str] | None = None,
) -> str:
    """Matrice en Markdown ; avec ``statuts``, le résultat des tests d'un passage."""
    lignes = [
        "# Matrice de vérification",
        "",
        "<!-- Généré par « python -m banc.matrice » depuis matrice.toml et les marqueurs des "
        "tests : ne pas modifier à la main. -->",
        "",
        "Chaque exigence du cahier, de sécurité et chaque principe directeur, avec son état, "
        "ses méthodes de vérification et leur résultat ([ADR-0024]"
        "(../decisions/ADR-0024-methode-de-verification.md), [ADR-0102]"
        "(../decisions/ADR-0102-matrice-de-verification.md)). Procédure : [README](README.md).",
        "",
    ]
    if statuts is None:
        lignes += [
            "Le résultat des tests est celui de chaque passage de la CI, qui joint cette matrice "
            "remplie à ses artefacts.",
            "",
        ]
    else:
        lignes += ["Résultat des tests : passage de pytest joint à cette matrice.", ""]
    lignes += ["## Synthèse", ""]
    entetes = ["Famille", *ETATS.values(), "Total"]
    lignes += ["| " + " | ".join(entetes) + " |", "|" + " --- |" * len(entetes)]
    for prefixe, titre in FAMILLES:
        compte = Counter(e.etat for e in matrice.entrees if _famille(e.id) == prefixe)
        valeurs = [str(compte[etat]) for etat in ETATS]
        lignes.append(f"| {titre} | " + " | ".join(valeurs) + f" | {compte.total()} |")
    entetes = [
        "Id",
        "Exigence",
        "État",
        "Tâches",
        "Méthodes",
        "Vérification",
        "Résultat",
        "Remarque",
    ]
    for prefixe, titre in FAMILLES:
        lignes += ["", f"## {titre}", ""]
        lignes += ["| " + " | ".join(entetes) + " |", "|" + " --- |" * len(entetes)]
        lignes += [
            _ligne(entree, exigences.get(entree.id, ""), tests.get(entree.id, ()), statuts)
            for entree in matrice.entrees
            if _famille(entree.id) == prefixe
        ]
    lignes += [
        "",
        "## Cas d'usage (cahier, §4 ; A-27)",
        "",
        "| Cas | Description | Exigences |",
        "| --- | --- | --- |",
    ]
    lignes += [
        f"| {identifiant} | {_cellule(cas.get(identifiant, ''))} | {', '.join(liees)} |"
        for identifiant, liees in matrice.cas.items()
    ]
    return "\n".join(lignes) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python -m banc.matrice",
        description="Matrice de vérification : contrôle et rendu (ADR-0102).",
    )
    analyseur.add_argument(
        "--verifier", action="store_true", help="échoue si matrice.md n'est pas à jour"
    )
    analyseur.add_argument("--resultats", metavar="JUNIT", help="rapport JUnit d'un passage")
    analyseur.add_argument("--sortie", metavar="FICHIER", help="fichier à écrire (matrice.md)")
    arguments = analyseur.parse_args(argv)
    try:
        matrice = lire()
        exigences, cas = connues(matrice)
        tests = par_exigence(collecter())
        statuts = None if arguments.resultats is None else lire_junit(Path(arguments.resultats))
    except (MatriceInvalide, OSError, ET.ParseError) as erreur:
        print(f"matrice : {erreur}", file=sys.stderr)
        return 2
    erreurs = verifier(matrice, exigences, cas, tests)
    for probleme in erreurs:
        print(f"matrice : {probleme}", file=sys.stderr)
    if erreurs:
        return 1
    contenu = rendre(matrice, exigences, cas, tests, statuts)
    cible = Path(arguments.sortie) if arguments.sortie else SORTIE
    if arguments.verifier:
        if not cible.exists() or cible.read_text(encoding="utf-8") != contenu:
            print(
                f"matrice : {cible.name} n'est pas à jour ; lancer « python -m banc.matrice »",
                file=sys.stderr,
            )
            return 1
        return 0
    cible.write_text(contenu, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
