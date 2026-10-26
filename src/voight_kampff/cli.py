"""Ligne de commande, installée sous les noms ``voight-kampff`` et ``vk`` (ADR-0045)."""

import argparse
from collections.abc import Sequence

from voight_kampff import __version__

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
    return analyseur


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée ; renvoie le code de sortie du processus."""
    analyseur = construire_analyseur()
    analyseur.parse_args(argv)
    # Aucune commande d'analyse avant T12 : sans argument, l'aide est affichée.
    analyseur.print_help()
    return 0
