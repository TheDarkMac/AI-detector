"""Ligne de commande, installée sous les noms ``voight-kampff`` et ``vk`` (ADR-0045).

``vk FICHIER...`` analyse chaque fichier indépendamment, dans un processus de travail neuf
(ADR-0015), et affiche un résumé par fichier, repéré par son rang dans la commande. Les données
identifiantes, nom et empreinte compris, y sont masquées (ADR-0031, ADR-0098).

``--rapport DOSSIER`` écrit le rapport de chaque fichier en HTML et en JSON, ``<rang>.html`` et
``<rang>.json``, sans jamais écraser un fichier (ADR-0092) ; ``--reveler CATEGORIE`` lève le
masquage d'une catégorie, au terminal comme dans les rapports, et le signale (ADR-0093).
``--catalogue DOSSIER`` remplace le catalogue livré par celui de l'utilisateur (ADR-0086) ;
``--regles`` affiche la version, la date, l'empreinte et les règles du catalogue (NF-07).

Codes de sortie : 0 si chaque fichier a été analysé, même partiellement, et son rapport écrit ;
1 si au moins un a été refusé ou n'a pas pu être écrit ; 2 pour une commande invalide, un
catalogue invalide ou un rapport qui existe déjà (ADR-0075, ADR-0086, ADR-0092).
"""

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from voight_kampff import __version__
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes
from voight_kampff.analyse import Analyse, AnalyseRefusee, analyser
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import (
    Presentation,
    etat_partie,
    libelle,
    localisation,
    neutraliser,
    octets,
    texte,
    textes,
)
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    RaisonNonMenee,
    VersionCatalogue,
)

_DESCRIPTION = (
    "Analyse la provenance et l'intégrité d'un fichier : preuves et indices de "
    "génération ou de retouche, sans verdict certain."
)

_EXTENSIONS = (".html", ".json")
_CREATION = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)


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
        "--regles",
        action="store_true",
        help="affiche la version, la date, l'empreinte et les règles du catalogue employé",
    )
    analyseur.add_argument(
        "--catalogue",
        metavar="DOSSIER",
        help="remplace le catalogue livré par celui de ce dossier ; le rapport le signale",
    )
    analyseur.add_argument(
        "--rapport",
        metavar="DOSSIER",
        help="écrit le rapport de chaque fichier dans ce dossier, en HTML et en JSON, nommés "
        "par le rang du fichier dans la commande (1.html, 1.json…) ; n'écrase rien",
    )
    analyseur.add_argument(
        "--reveler",
        action="append",
        default=[],
        choices=[categorie.value for categorie in CategorieIdentifiante],
        metavar="CATEGORIE",
        help="montre les données identifiantes de cette catégorie, masquées par défaut : "
        + ", ".join(categorie.value for categorie in CategorieIdentifiante)
        + " ; le rapport l'annonce en tête (option répétable)",
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


def _catalogue(version: VersionCatalogue) -> str:
    origine = ", fourni par l'utilisateur" if version.fourni_par_utilisateur else ""
    return (
        f"catalogue : {version.version} du {version.date.isoformat()}{origine}, "
        f"empreinte {version.empreinte}"
    )


def _lister_regles(catalogue: catalogues.Catalogue) -> None:
    print(_catalogue(catalogue.version))
    if not catalogue.regles:
        print("Aucune règle dans cette version du catalogue.")
    for regle in catalogue.regles:
        print(f"{regle.identifiant} version {regle.version} ({regle.module}) : {regle.titre}")


def resume(analyse: Analyse, reveler: Sequence[str] = ()) -> list[str]:
    """Lignes du résumé d'une analyse ; données identifiantes masquées sauf ``reveler``.

    Dans l'ordre d'ADR-0098 : ce qui change la portée du résultat, l'identification et ses
    signalements, l'isolation, la couverture, le résumé sans verdict d'ADR-0018, les analyses
    non menées, le catalogue. Les lignes ne sont pas neutralisées : l'appelant le fait en les
    écrivant (ES-12).
    """
    vue = Presentation(analyse, export.masquees(reveler))
    identification = analyse.identification
    lignes = [texte("terminal.format_reel", format=identification.format_reel)]
    lignes += [texte("terminal.alerte", alerte=alerte) for alerte in vue.alertes()]
    lignes.append(texte("terminal.nom", nom=vue.nom()))
    lignes.append(texte("terminal.empreinte", empreinte=vue.empreinte()))
    lignes += vue.signalements()
    lignes += [
        texte(
            "terminal.partie",
            rang=partie.rang,
            format=partie.format,
            octets=octets(partie.octets),
            etat=etat_partie(partie),
        )
        for partie in identification.parties
    ]
    lignes.append(
        texte("terminal.isolation", niveau=libelle("isolation", analyse.isolation.niveau))
    )
    lignes += [
        texte(
            "terminal.technique",
            module=technique.module,
            partie=technique.partie,
            etat=texte("formes.hors_version")
            if technique.version is None
            else libelle("etats", technique.etat),
        )
        for technique in analyse.couverture.techniques
    ]
    lignes += vue.resume()
    for non_menee in analyse.non_menees:
        if non_menee.raison in {RaisonNonMenee.HORS_PERIMETRE, RaisonNonMenee.HORS_V1}:
            continue  # déjà dit avec sa partie ou sa technique
        portee = [
            non_menee.module or "",
            f"{texte('champs.partie').lower()} {non_menee.partie}" if non_menee.partie else "",
            localisation(non_menee.localisation) if non_menee.localisation else "",
        ]
        precision = ", ".join(element for element in portee if element)
        cle = "terminal.non_menee_precisee" if precision else "terminal.non_menee"
        lignes.append(texte(cle, raison=vue.non_menee(non_menee), precision=precision))
    lignes.append(texte("terminal.catalogue", catalogue=vue.catalogue()))
    return lignes


def _ecrire(chemin: Path, contenu: str) -> None:
    """Crée le fichier, lisible par son seul propriétaire ; échoue s'il existe (ADR-0092)."""
    descripteur = os.open(chemin, _CREATION, 0o600)
    with os.fdopen(descripteur, "wb") as fichier:
        fichier.write(contenu.encode("utf-8"))


def _preparer(dossier: str, nombre: int) -> Path:
    """Dossier des rapports, créé au besoin (pas ses parents).

    Lève ``ValueError``, avec le message à afficher, si le dossier est inutilisable ou s'il
    contient déjà un des rapports à écrire : rien n'est analysé (ADR-0092).
    """
    chemin = Path(dossier)
    try:
        if not chemin.is_dir():
            chemin.mkdir()
    except OSError as erreur:
        raise ValueError(f"dossier inutilisable ({erreur.strerror})") from None
    for rang in range(1, nombre + 1):
        for extension in _EXTENSIONS:
            if (chemin / f"{rang}{extension}").exists():
                raise ValueError(f"{rang}{extension} existe déjà ; aucun rapport n'est écrasé")
    return chemin


def _analyser(
    fichiers: Sequence[str],
    desactiver: Sequence[str],
    catalogue: str | None,
    dossier: Path | None,
    reveler: Sequence[str],
) -> int:
    code = 0
    analysees = 0
    for rang, chemin in enumerate(fichiers, start=1):
        repere = f"[{rang}/{len(fichiers)}]"
        try:
            analyse = analyser(chemin, desactiver=desactiver, catalogue=catalogue)
        except AnalyseRefusee as refus:
            sys.stdout.flush()  # les deux flux restent dans l'ordre des fichiers
            print(f"{repere} refusé : {refus}", file=sys.stderr)
            code = 1
            continue
        analysees += 1
        lignes = resume(analyse, reveler)
        if dossier is not None:
            html, json = (dossier / f"{rang}{extension}" for extension in _EXTENSIONS)
            try:
                _ecrire(html, export.exporter_html(analyse, reveler=reveler))
                _ecrire(json, export.exporter_json(analyse, reveler=reveler))
            except OSError as erreur:
                sys.stdout.flush()
                print(f"{repere} rapport non écrit : {erreur.strerror}", file=sys.stderr)
                code = 1
            else:
                lignes.append(texte("terminal.rapport", html=html, json=json))
        print(neutraliser(f"{repere} {lignes[0]}"))
        for ligne in lignes[1:]:
            print(neutraliser(f"  {ligne}"))
    if analysees:
        print()
        for phrase in textes()["avertissement"]:
            print(phrase)
    return code


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée ; renvoie le code de sortie du processus."""
    analyseur = construire_analyseur()
    arguments = analyseur.parse_args(argv)
    if arguments.modules:
        _lister_modules()
        return 0
    if not (arguments.fichiers or arguments.regles):
        analyseur.print_help()
        return 0
    livres = manifestes.decouvrir()
    try:
        # Validé une fois avant le premier fichier : un catalogue invalide n'en refuse aucun.
        catalogue = catalogues.charger(livres, arguments.catalogue)
    except catalogues.CatalogueInvalide as erreur:
        analyseur.error(f"catalogue invalide : {erreur}")
    if arguments.regles:
        _lister_regles(catalogue)
        return 0
    try:
        manifestes.selectionner(livres, arguments.desactiver)
    except manifestes.ModuleInconnu as erreur:
        connus = ", ".join(manifeste.identifiant for manifeste in livres) or "aucun"
        analyseur.error(f"{erreur} ; modules livrés : {connus}")
    dossier = None
    if arguments.rapport is not None:
        try:
            dossier = _preparer(arguments.rapport, len(arguments.fichiers))
        except ValueError as erreur:
            analyseur.error(f"--rapport : {erreur}")
    return _analyser(
        arguments.fichiers, arguments.desactiver, arguments.catalogue, dossier, arguments.reveler
    )
