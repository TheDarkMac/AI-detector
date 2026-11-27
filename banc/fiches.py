"""Fiches techniques livrées dans le paquet (T95, ADR-0268).

La source est ``docs/techniques/<fiche>.md``, une par module livré, nommée par le champ
``fiche`` de son manifeste. Le paquet en porte une copie, octet pour octet, dans
``src/voight_kampff/donnees/fiches/``, que ``vk --fiche MODULE`` affiche hors ligne, à la
version exacte du code installé.

Usage, depuis la racine du dépôt :

- ``python -m banc.fiches`` : recopie les fiches dans le paquet et retire celles d'un module
  qui n'est plus livré ;
- ``python -m banc.fiches --verifier`` : échoue si la copie diffère de la source (les tests
  l'appellent) ;
- ``python -m banc.fiches --taux EVALUATION.json`` : écrit d'abord, dans la rubrique « Taux
  d'erreur » de chaque fiche, les taux que mesure ce rapport d'évaluation publiable pour son
  module, entre deux marqueurs, puis recopie les fiches (T101, ADR-0279). Le texte rédigé de la
  rubrique, hors des marqueurs, n'est pas touché.
"""

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from banc.sortie import _CATEGORIES, _tableau, _taux
from voight_kampff._orchestration import manifestes

__all__ = [
    "COPIE",
    "DEBUT",
    "FIN",
    "SOURCE",
    "attendues",
    "bloc_des_taux",
    "ecarts",
    "inscrire_taux",
    "main",
    "recopier",
]

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "docs" / "techniques"
COPIE = RACINE / "src" / "voight_kampff" / "donnees" / "fiches"


RUBRIQUE = "## Taux d'erreur"
DEBUT = "<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->"
FIN = "<!-- Fin des taux mesurés. -->"


def attendues() -> list[str]:
    """Noms des fichiers de fiche des modules livrés, triés."""
    return sorted(f"{manifeste.fiche}.md" for manifeste in manifestes.decouvrir())


def ecarts(source: Path | None = None, copie: Path | None = None) -> list[str]:
    """Écarts entre la source et la copie livrée : vide si elles sont identiques."""
    source, copie = source or SOURCE, copie or COPIE
    noms = attendues()
    problemes = []
    for nom in noms:
        origine, livree = source / nom, copie / nom
        if not origine.is_file():
            problemes.append(f"{nom} : fiche absente de {source}")
        elif not livree.is_file():
            problemes.append(f"{nom} : absente du paquet")
        elif origine.read_bytes() != livree.read_bytes():
            problemes.append(f"{nom} : copie du paquet différente de la source")
    presentes = sorted(p.name for p in copie.iterdir()) if copie.is_dir() else []
    problemes += [
        f"{nom} : dans le paquet sans module livré" for nom in presentes if nom not in noms
    ]
    return problemes


def recopier(source: Path | None = None, copie: Path | None = None) -> None:
    """Recopie dans le paquet la fiche de chaque module livré, et retire les autres fichiers."""
    source, copie = source or SOURCE, copie or COPIE
    noms = attendues()
    copie.mkdir(parents=True, exist_ok=True)
    for chemin in copie.iterdir():
        if chemin.name not in noms:
            chemin.unlink()
    for nom in noms:
        (copie / nom).write_bytes((source / nom).read_bytes())


def bloc_des_taux(module: str, doc: Mapping[str, Any], rapport: str) -> str:
    """Taux d'un module dans un rapport d'évaluation, marqueurs compris ; ``rapport`` est le
    lien vers sa version Markdown, relatif à la fiche."""
    corpus, versions = doc["corpus"], doc["versions"]
    mesures = [m for m in doc["techniques"] if m["module"] == module]
    regles = [r for r in doc["regles"] if r["module"] == module]
    lignes = [
        DEBUT,
        "",
        f"Mesurés le {doc['date'][:10]} par le banc, sur la partie évaluation du corpus "
        f"{corpus['nom']} {corpus['version']} ([rapport]({rapport})) : module `{module}` "
        f"{versions['techniques'][module]}, outil {versions['outil']}, catalogue "
        f"{versions['catalogue']['version']}. Chaque taux est donné avec son effectif et son "
        "intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions "
        "sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).",
        "",
        *_tableau(
            [
                "Catégorie",
                "Fichiers",
                "Non applicables",
                "Non analysables",
                "Faux positifs",
                "Faux négatifs",
                "Confusions",
            ],
            [
                [
                    _CATEGORIES[m["categorie"]],
                    str(m["effectif"]),
                    str(m["non_applicables"]),
                    _taux(m["non_analysables"]),
                    _taux(m["faux_positifs"]),
                    _taux(m["faux_negatifs"]),
                    str(m["confusions"]),
                ]
                for m in mesures
            ],
        ),
        "",
    ]
    if regles:
        lignes += _tableau(
            ["Règle", "Catégorie", "Direction", "Faux positifs", "Niveau permis", "Niveau"],
            [
                [
                    f"{r['identifiant']} v{r['version']}",
                    r["categorie"],
                    r["direction"],
                    _taux(r["faux_positifs"]),
                    r["niveau_permis"] or "—",
                    r["niveau"] or "—",
                ]
                for r in regles
            ],
        )
    else:
        lignes.append(
            "Aucune règle de preuve ou d'indice : les règles du module sont des informations "
            "neutres, sans taux."
        )
    lignes += ["", FIN]
    return "\n".join(lignes)


def _avec_bloc(texte: str, bloc: str) -> str:
    """Texte de la fiche où le bloc remplace l'ancien, ou s'ajoute en tête de la rubrique."""
    if DEBUT in texte:
        avant, reste = texte.split(DEBUT, 1)
        if FIN not in reste:
            raise ValueError("marqueur de fin des taux absent")
        return avant + bloc + reste.split(FIN, 1)[1]
    if f"\n{RUBRIQUE}\n\n" not in texte:
        raise ValueError(f"rubrique « {RUBRIQUE.removeprefix('## ')} » absente")
    avant, apres = texte.split(f"\n{RUBRIQUE}\n\n", 1)
    return f"{avant}\n{RUBRIQUE}\n\n{bloc}\n\n{apres}"


def inscrire_taux(doc: Mapping[str, Any], rapport: Path, source: Path | None = None) -> list[str]:
    """Écrit les taux de chaque module mesuré dans sa fiche ; rend les fiches écrites.

    ``rapport`` est le chemin du rapport Markdown, d'où le lien relatif de chaque fiche est
    tiré. Lève ``ValueError`` pour un rapport non publiable ou une fiche sans rubrique.
    """
    if not doc.get("publiable"):
        raise ValueError("rapport non publiable : aucun taux n'en est tiré (ADR-0105)")
    source = source or SOURCE
    lien = Path(_relatif(rapport.resolve(), source.resolve()))
    ecrites = []
    fiches = {m.identifiant: f"{m.fiche}.md" for m in manifestes.decouvrir()}
    for module in doc["versions"]["techniques"]:
        chemin = source / fiches[module]
        texte = chemin.read_text(encoding="utf-8")
        try:
            nouveau = _avec_bloc(texte, bloc_des_taux(module, doc, lien.as_posix()))
        except ValueError as erreur:
            raise ValueError(f"{chemin.name} : {erreur}") from None
        chemin.write_text(nouveau, encoding="utf-8")
        ecrites.append(chemin.name)
    return ecrites


def _relatif(cible: Path, depuis: Path) -> str:
    """Chemin de ``cible`` vu du dossier ``depuis``, avec des « .. » au besoin."""
    commun = Path(*[a for a, b in zip(cible.parts, depuis.parts, strict=False) if a == b])
    montees = len(depuis.parts) - len(commun.parts)
    return "/".join([".."] * montees + list(cible.parts[len(commun.parts) :]))


def main(argv: Sequence[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python -m banc.fiches",
        description="Fiches techniques livrées dans le paquet : copie et contrôle (ADR-0268).",
    )
    analyseur.add_argument(
        "--verifier", action="store_true", help="échoue si la copie diffère de la source"
    )
    analyseur.add_argument(
        "--taux",
        metavar="EVALUATION.json",
        help=(
            "écrit d'abord dans chaque fiche les taux de ce rapport d'évaluation publiable ; "
            "la version Markdown du rapport doit être à côté (ADR-0279)"
        ),
    )
    arguments = analyseur.parse_args(argv)
    if arguments.taux is not None:
        rapport = Path(arguments.taux)
        try:
            doc = json.loads(rapport.read_text(encoding="utf-8"))
            inscrire_taux(doc, rapport.with_suffix(".md"))
        except (OSError, ValueError, KeyError) as erreur:
            print(f"fiches : {erreur}", file=sys.stderr)
            return 2
    if not arguments.verifier:
        manquantes = [nom for nom in attendues() if not (SOURCE / nom).is_file()]
        if manquantes:
            print(f"fiches : absentes de {SOURCE} : {', '.join(manquantes)}", file=sys.stderr)
            return 2
        recopier()
    problemes = ecarts()
    for probleme in problemes:
        print(f"fiches : {probleme} ; lancer « python -m banc.fiches »", file=sys.stderr)
    return 1 if problemes else 0


if __name__ == "__main__":
    sys.exit(main())
