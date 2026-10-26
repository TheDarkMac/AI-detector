"""Modules d'analyse : une technique par sous-paquet, avec son manifeste (ADR-0042).

Un module est un dossier ``modules/<identifiant>/`` qui contient ``manifeste.toml`` et un
``__init__.py`` exposant ``analyser(contexte)`` (ADR-0061). Le processus principal lit les
manifestes sans importer ce code ; seul le processus de travail l'importe.

La découverte se limite à ce dossier : aucune extension tierce n'est chargée (ADR-0042). Aucun
module n'est livré avant T13.
"""

from importlib.resources import files
from importlib.resources.abc import Traversable

__all__ = ["MANIFESTE", "dossiers"]

MANIFESTE = "manifeste.toml"
"""Nom du manifeste dans le dossier de chaque module."""


def dossiers(racine: Traversable | None = None) -> tuple[Traversable, ...]:
    """Dossiers des modules, triés par nom : ceux qui contiennent un manifeste.

    ``racine`` vaut par défaut le dossier de ce paquet ; les tests en donnent un autre.
    """
    racine = files(__name__) if racine is None else racine
    trouves = (
        dossier
        for dossier in racine.iterdir()
        if dossier.is_dir() and (dossier / MANIFESTE).is_file()
    )
    return tuple(sorted(trouves, key=lambda dossier: dossier.name))
