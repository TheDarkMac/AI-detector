"""Ligne de commande, installée sous les noms ``voight-kampff`` et ``vk`` (ADR-0045)."""

import argparse
from collections.abc import Sequence

from voight_kampff import __version__
from voight_kampff._orchestration import manifestes

_DESCRIPTION = (
    "Analyse la provenance et l'intégrité d'un fichier : preuves et indices de "
    "génération ou de retouche, sans verdict certain."
)


def construire_analyseur() -> argparse.ArgumentParser:
    """Construit l'analyseur d'arguments de la ligne de commande."""
    analyseur = argparse.ArgumentParser(prog="voight-kampff", description=_DESCRIPTION)
    analyseur.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    analyseur.add_argument(
        "--modules",
        action="store_true",
        help="liste les modules d'analyse livrés, avec leur version",
    )
    return analyseur


def _lister_modules() -> None:
    livres = manifestes.decouvrir()
    if not livres:
        print("Aucun module d'analyse livré dans cette version.")
    for manifeste in livres:
        print(f"{manifeste.identifiant} {manifeste.version}")


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée ; renvoie le code de sortie du processus."""
    analyseur = construire_analyseur()
    arguments = analyseur.parse_args(argv)
    if arguments.modules:
        _lister_modules()
        return 0
    # Aucune commande d'analyse avant T13 : sans option, l'aide est affichée.
    analyseur.print_help()
    return 0
