"""Contrôles du catalogue de règles par la CI (ADR-0085, ADR-0088), depuis la racine du dépôt.

``python3 -I .github/scripts/catalogue.py base REVISION`` :

1. chaque entrée du registre ``docs/catalogue/versions.toml`` présente à REVISION l'est encore,
   à l'identique : une version inscrite ne change plus ;
2. une règle présente à REVISION sous une version l'est encore à l'identique si elle garde
   cette version ; sa version ne diminue jamais.

``python3 -I .github/scripts/catalogue.py paquet WHEEL`` : calcule la version, la date et
l'empreinte du catalogue contenu dans le wheel, selon la procédure publiée, vérifie qu'elles
sont la dernière entrée du registre, et les affiche (release, ADR-0041).

Que la dernière entrée du registre décrive le catalogue des sources est vérifié par les tests
(``tests/test_catalogue.py``). Ce script n'emploie que la bibliothèque standard.
"""

import hashlib
import subprocess
import sys
import tomllib
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

REGISTRE = "docs/catalogue/versions.toml"
REGLES = "src/voight_kampff/donnees/catalogue/regles"
DANS_LE_PAQUET = "voight_kampff/donnees/catalogue/"

type Regles = dict[tuple[str, str], dict[str, Any]]


def a_la_revision(revision: str, chemin: str) -> str | None:
    """Contenu du fichier à cette révision, ou ``None`` s'il n'y existait pas."""
    resultat = subprocess.run(  # noqa: S603 - commande fixe, révision passée en argument
        ["git", "show", f"{revision}:{chemin}"],  # noqa: S607 - git du runner
        capture_output=True,
        text=True,
        check=False,
    )
    return resultat.stdout if resultat.returncode == 0 else None


def fichiers_de_regles(revision: str) -> list[str]:
    sortie = subprocess.run(  # noqa: S603
        ["git", "ls-tree", "-r", "--name-only", revision, "--", REGLES],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [chemin for chemin in sortie.splitlines() if chemin.endswith(".toml")]


def regles(textes: Iterable[str]) -> Regles:
    return {
        (regle["identifiant"], regle["version"]): regle
        for texte in textes
        for regle in tomllib.loads(texte).get("regle", [])
    }


def ecarts(
    ancien_registre: list[Mapping[str, str]],
    registre: list[Mapping[str, str]],
    anciennes: Regles,
    actuelles: Regles,
) -> list[str]:
    """Écarts interdits entre la base et l'état actuel ; liste vide si tout va bien."""
    trouves = [
        f"registre : la version {entree['version']} a été modifiée ou retirée"
        for entree in ancien_registre
        if entree not in registre
    ]
    for (identifiant, version), regle in anciennes.items():
        actuelle = actuelles.get((identifiant, version))
        if actuelle is not None and actuelle != regle:
            trouves.append(f"règle {identifiant} : modifiée sans nouvelle version ({version})")
    for identifiant, version in actuelles:
        plus_haute = max((int(v) for i, v in anciennes if i == identifiant), default=int(version))
        if int(version) < plus_haute:
            trouves.append(f"règle {identifiant} : version {version} inférieure à {plus_haute}")
    return trouves


def du_paquet(wheel: str) -> dict[str, str]:
    """Version, date et empreinte du catalogue d'un wheel, sans installer le paquet."""
    with zipfile.ZipFile(wheel) as archive:
        contenus = {
            nom.removeprefix(DANS_LE_PAQUET): archive.read(nom)
            for nom in archive.namelist()
            if nom.startswith(DANS_LE_PAQUET) and not nom.endswith("/")
        }
    liste = "".join(
        f"{hashlib.sha256(contenu).hexdigest()}  {chemin}\n"
        for chemin, contenu in sorted(contenus.items())
    )
    entete = tomllib.loads(contenus["catalogue.toml"].decode("utf-8"))
    return {
        "version": entete["version"],
        "date": entete["date"],
        "empreinte": hashlib.sha256(liste.encode("utf-8")).hexdigest(),
    }


def paquet(wheel: str) -> int:
    catalogue = du_paquet(wheel)
    derniere = tomllib.loads(Path(REGISTRE).read_text(encoding="utf-8"))["version"][-1]
    if catalogue != derniere:
        print("::error::catalogue du paquet absent du registre ou différent (ADR-0085)")
        return 1
    print(f"Catalogue de règles {catalogue['version']} du {catalogue['date']}")
    print(f"Empreinte SHA-256 : {catalogue['empreinte']}")
    return 0


def base(revision: str) -> int:
    ancien = a_la_revision(revision, REGISTRE)
    ancien_registre = [] if ancien is None else tomllib.loads(ancien)["version"]
    registre = tomllib.loads(Path(REGISTRE).read_text(encoding="utf-8"))["version"]
    anciennes = regles(
        a_la_revision(revision, chemin) or "" for chemin in fichiers_de_regles(revision)
    )
    actuelles = regles(
        chemin.read_text(encoding="utf-8") for chemin in sorted(Path(REGLES).glob("*.toml"))
    )
    trouves = ecarts(ancien_registre, registre, anciennes, actuelles)
    for ecart in trouves:
        print(f"::error::{ecart} (ADR-0085)")
    if not trouves:
        print(f"Registre et règles conformes à {revision} : {len(registre)} version(s).")
    return 1 if trouves else 0


if __name__ == "__main__":
    commande, argument = sys.argv[1:]
    sys.exit({"base": base, "paquet": paquet}[commande](argument))
