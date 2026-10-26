"""Garde des analyseurs : ils refusent de s'exécuter hors d'un processus de travail (ES-17).

Le processus de travail se déclare verrouillé après avoir appliqué ses restrictions et avant
d'envoyer l'état de l'isolation (ADR-0036). Un programme qui importerait un module d'analyse
pour l'appeler dans son propre processus est arrêté par :func:`exiger`.
"""

__all__ = ["HorsProcessusDeTravail", "exiger", "verrouiller"]

_verrouille = False


class HorsProcessusDeTravail(RuntimeError):
    """Analyse demandée hors d'un processus de travail verrouillé."""


def verrouiller() -> None:
    """Déclare le processus courant processus de travail verrouillé ; sans retour arrière."""
    global _verrouille  # état du processus entier, posé une seule fois
    _verrouille = True


def exiger() -> None:
    """Lève :class:`HorsProcessusDeTravail` hors d'un processus de travail verrouillé."""
    if not _verrouille:
        raise HorsProcessusDeTravail(
            "les analyseurs ne s'exécutent que dans un processus de travail (ES-17)"
        )
