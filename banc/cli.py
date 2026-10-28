"""Commande du banc : ``python -m banc CORPUS --sortie DOSSIER`` (ADR-0099, ADR-0105).

Codes de sortie :

- 0 : évaluation menée, aucun écart ;
- 1 : évaluation menée, au moins un écart (critère non atteint ou non mesurable, niveau du
  catalogue que la mesure ne permet pas, preuve fautive, arrêt brutal) ;
- 2 : rien n'est évalué (réseau présent, corpus invalide ou modifié, dossier inutilisable,
  catalogue invalide, module inconnu) ;
- 3 : tentative d'accès au réseau pendant l'évaluation (ES-11) ; aucun rapport n'est écrit.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from banc import corpus as corpora
from banc import evaluation, reseau, sortie
from voight_kampff import Analyse, __version__, analyser
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes

__all__ = ["main"]


def construire_analyseur() -> argparse.ArgumentParser:
    analyseur = argparse.ArgumentParser(
        prog="python -m banc",
        description=(
            "Banc d'évaluation de Voight-Kampff : analyse chaque fichier d'une partie du "
            "corpus, sans réseau, et mesure les taux d'erreur (T17)."
        ),
    )
    analyseur.add_argument("corpus", metavar="CORPUS", help="manifeste corpus.toml du corpus")
    analyseur.add_argument(
        "--sortie",
        required=True,
        metavar="DOSSIER",
        help="dossier où écrire evaluation.json et evaluation.md, sans rien écraser",
    )
    analyseur.add_argument(
        "--partie",
        choices=[p.value for p in corpora.Partie],
        default=corpora.Partie.EVALUATION.value,
        help="partie du corpus à analyser (par défaut : evaluation, seule à fonder un taux)",
    )
    analyseur.add_argument(
        "--catalogue",
        metavar="DOSSIER",
        help="catalogue de règles à évaluer à la place du catalogue livré (ADR-0086)",
    )
    analyseur.add_argument(
        "--desactiver",
        action="append",
        default=[],
        metavar="MODULE",
        help="module à ne pas exécuter (répétable)",
    )
    return analyseur


def _erreur(message: str) -> int:
    print(f"banc : {message}", file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = construire_analyseur().parse_args(argv)
    partie = corpora.Partie(arguments.partie)
    try:
        interfaces = reseau.verifier_absence()
    except reseau.ReseauPresent as erreur:
        return _erreur(str(erreur))
    try:
        corpus = corpora.charger(arguments.corpus)
        livres = manifestes.decouvrir()
        actifs, _ = manifestes.selectionner(livres, arguments.desactiver)
        catalogue = catalogues.charger(livres, arguments.catalogue)
        dossier = sortie.preparer(arguments.sortie)
    except (ValueError, OSError) as erreur:
        # CorpusInvalide, ModuleInconnu, CatalogueInvalide et le dossier : messages explicites.
        return _erreur(str(erreur))
    modules = [manifeste.identifiant for manifeste in actifs]

    def analyser_fichier(chemin: Path) -> Analyse:
        return analyser(chemin, desactiver=arguments.desactiver, catalogue=arguments.catalogue)

    interdit: reseau.ReseauInterdit | None = None
    with reseau.surveiller() as tentatives:
        try:
            resultats = evaluation.analyser_corpus(corpus, partie, analyser_fichier, modules)
        except reseau.ReseauInterdit as erreur:
            interdit = erreur
        except corpora.CorpusInvalide as erreur:
            return _erreur(str(erreur))
    if tentatives or interdit:
        # Une tentative avalée par la bibliothèque qui l'a faite reste notée par le crochet.
        evenements = ", ".join(tentatives) or str(interdit)
        print(
            f"banc : accès au réseau pendant l'évaluation ({evenements}) : évaluation "
            "invalide, aucun rapport écrit (ES-11)",
            file=sys.stderr,
        )
        return 3
    mesures = evaluation.mesurer(partie, resultats, modules, catalogue.regles)
    doc = sortie.document(
        corpus,
        mesures,
        outil=__version__,
        catalogue=catalogue.version,
        techniques={manifeste.identifiant: manifeste.version for manifeste in actifs},
        interfaces=interfaces,
        date=datetime.now(UTC),
    )
    sortie.ecrire(dossier, doc)
    print(
        f"{len(resultats)} fichiers de la partie {partie.value} évalués ; rapport dans "
        f"{dossier / sortie.FICHIERS[1]}"
    )
    for ecart in mesures.ecarts:
        print(f"écart : {ecart}")
    return 1 if mesures.ecarts else 0
