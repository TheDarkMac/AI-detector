"""Fiches techniques livrées dans le paquet (T95, ADR-0268).

La source est ``docs/techniques/<fiche>.md``, une par module livré, nommée par le champ
``fiche`` de son manifeste. Le paquet en porte une copie, octet pour octet, dans
``src/voight_kampff/donnees/fiches/``, que ``vk --fiche MODULE`` affiche hors ligne, à la
version exacte du code installé.

Usage, depuis la racine du dépôt :

- ``python -m banc.fiches`` : recopie les fiches dans le paquet et retire celles d'un module
  qui n'est plus livré ;
- ``python -m banc.fiches --verifier`` : échoue si la copie diffère de la source (les tests
  l'appellent).
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from voight_kampff._orchestration import manifestes

__all__ = ["COPIE", "SOURCE", "attendues", "ecarts", "main", "recopier"]

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "docs" / "techniques"
COPIE = RACINE / "src" / "voight_kampff" / "donnees" / "fiches"


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


def main(argv: Sequence[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python -m banc.fiches",
        description="Fiches techniques livrées dans le paquet : copie et contrôle (ADR-0268).",
    )
    analyseur.add_argument(
        "--verifier", action="store_true", help="échoue si la copie diffère de la source"
    )
    arguments = analyseur.parse_args(argv)
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
