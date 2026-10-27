"""Ligne de commande, installée sous les noms ``voight-kampff`` et ``vk`` (ADR-0045).

``vk FICHIER...`` analyse chaque fichier indépendamment, dans un processus de travail neuf
(ADR-0015). Avant le rapport (T16), elle affiche un résumé par fichier, repéré par son rang
dans la commande : ni nom ni empreinte, qui sont identifiants (ADR-0031, ADR-0073).

Codes de sortie : 0 si chaque fichier a été analysé, même partiellement ; 1 si au moins un
a été refusé ; 2 pour une commande invalide (ADR-0075).
"""

import argparse
import sys
from collections.abc import Sequence

from voight_kampff import __version__
from voight_kampff._orchestration import manifestes
from voight_kampff.analyse import Analyse, AnalyseRefusee, analyser
from voight_kampff.rapport.modele import EtatTechnique, NiveauIsolation, Plage, RaisonNonMenee

_DESCRIPTION = (
    "Analyse la provenance et l'intégrité d'un fichier : preuves et indices de "
    "génération ou de retouche, sans verdict certain."
)

_ETATS = {
    EtatTechnique.APPLIQUEE: "appliquée",
    EtatTechnique.PARTIELLE: "partielle",
    EtatTechnique.NON_MENEE: "non menée",
    EtatTechnique.NON_APPLICABLE: "non applicable",
}


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
    analyseur.add_argument(
        "--desactiver",
        action="append",
        default=[],
        metavar="MODULE",
        help="n'exécute pas ce module ; le rapport le signale (option répétable)",
    )
    analyseur.add_argument(
        "fichiers",
        nargs="*",
        metavar="FICHIER",
        help="fichiers à analyser, chacun indépendamment des autres",
    )
    return analyseur


def _lister_modules() -> None:
    livres = manifestes.decouvrir()
    if not livres:
        print("Aucun module d'analyse livré dans cette version.")
    for manifeste in livres:
        print(f"{manifeste.identifiant} {manifeste.version}")


def _octets(plage: Plage) -> str:
    return f"octets {plage.debut} à {plage.debut + plage.longueur - 1}"


def resume(analyse: Analyse) -> list[str]:
    """Lignes du résumé d'une analyse, sans donnée identifiante (ADR-0073)."""
    identification = analyse.identification
    lignes = [f"format réel : {identification.format_reel}"]
    if identification.extension is None:
        lignes.append("extension : aucune")
    else:
        accord = "concordante" if identification.extension_concordante else "discordante"
        lignes.append(f"extension : {identification.extension}, {accord}")
    for partie in identification.parties:
        ligne = f"partie {partie.rang} : {partie.format}, {_octets(partie.octets)}"
        if partie.tronquee:
            ligne += ", tronquée ou corrompue"
        elif not partie.fin_connue:
            ligne += ", fin logique non établie"
        if not partie.dans_perimetre:
            ligne += ", hors périmètre, non analysée"
        lignes.append(ligne)
    lignes.extend(
        f"non reconnus : {_octets(plage)}" for plage in identification.octets_non_reconnus
    )
    if analyse.isolation.niveau is NiveauIsolation.COMPLETE:
        lignes.append("isolation : complète")
    else:
        lignes.append(f"isolation : réduite ; manque : {', '.join(analyse.isolation.manques)}")
    if not analyse.couverture.techniques:
        lignes.append("techniques : aucune dans cette version")
    lignes.extend(
        f"technique {technique.module}, partie {technique.partie} : {_ETATS[technique.etat]}"
        for technique in analyse.couverture.techniques
    )
    lignes.append(
        f"observations : {len(analyse.observations)} ; constats : {len(analyse.constats)}"
    )
    for non_menee in analyse.non_menees:
        if non_menee.raison is RaisonNonMenee.HORS_PERIMETRE:
            continue  # déjà dit avec sa partie
        octets = non_menee.localisation.octets if non_menee.localisation else None
        portee = [
            non_menee.module or "",
            f"partie {non_menee.partie}" if non_menee.partie else "",
            _octets(octets) if octets else "",
        ]
        precision = ", ".join(element for element in portee if element)
        lignes.append(f"non menée : {non_menee.raison}" + (f" ({precision})" if precision else ""))
    if analyse.interrompue:
        lignes.append("analyse interrompue : résultats partiels, hors garantie de reproductibilité")
    lignes.append("nom et empreinte : masqués")
    return lignes


def _analyser(fichiers: Sequence[str], desactiver: Sequence[str]) -> int:
    code = 0
    for rang, chemin in enumerate(fichiers, start=1):
        repere = f"[{rang}/{len(fichiers)}]"
        try:
            analyse = analyser(chemin, desactiver=desactiver)
        except AnalyseRefusee as refus:
            sys.stdout.flush()  # les deux flux restent dans l'ordre des fichiers
            print(f"{repere} refusé : {refus}", file=sys.stderr)
            code = 1
            continue
        lignes = resume(analyse)
        print(f"{repere} {lignes[0]}")
        for ligne in lignes[1:]:
            print(f"  {ligne}")
    return code


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée ; renvoie le code de sortie du processus."""
    analyseur = construire_analyseur()
    arguments = analyseur.parse_args(argv)
    if arguments.modules:
        _lister_modules()
        return 0
    if not arguments.fichiers:
        analyseur.print_help()
        return 0
    livres = manifestes.decouvrir()
    try:
        manifestes.selectionner(livres, arguments.desactiver)
    except manifestes.ModuleInconnu as erreur:
        connus = ", ".join(manifeste.identifiant for manifeste in livres) or "aucun"
        analyseur.error(f"{erreur} ; modules livrés : {connus}")
    return _analyser(arguments.fichiers, arguments.desactiver)
