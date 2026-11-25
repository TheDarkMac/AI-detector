"""Ligne de commande, installée sous les noms ``voight-kampff`` et ``vk`` (ADR-0045).

``vk FICHIER...`` analyse chaque fichier indépendamment, dans un processus de travail neuf
(ADR-0015), et affiche un résumé par fichier, repéré par son rang dans la commande. Les données
identifiantes, nom et empreinte compris, y sont masquées (ADR-0031, ADR-0098).

``--rapport DOSSIER`` écrit le rapport de chaque fichier en HTML et en JSON, ``<rang>.html`` et
``<rang>.json``, sans jamais écraser un fichier (ADR-0092) ; ``--reveler CATEGORIE`` lève le
masquage d'une catégorie, au terminal comme dans les rapports, et le signale (ADR-0093).
``--catalogue DOSSIER`` remplace le catalogue livré par celui de l'utilisateur (ADR-0086) ;
``--regles`` affiche la version, la date, l'empreinte, les règles et les marquages du catalogue
(NF-07, ADR-0175).
``--confiance DOSSIER`` remplace de même la liste de confiance C2PA livrée (ADR-0171).
``--texte`` analyse le texte lu sur l'entrée standard, collé ou reçu d'un tube, au lieu d'un
fichier (ADR-0233) ; il s'emploie sans fichier, et son rapport s'écrit ``1.html`` et ``1.json``.

Codes de sortie : 0 si chaque fichier a été analysé, même partiellement, et son rapport écrit ;
1 si au moins un a été refusé ou n'a pas pu être écrit ; 2 pour une commande invalide, un
catalogue ou une liste de confiance invalides, ou un rapport qui existe déjà (ADR-0075, ADR-0086,
ADR-0092).

``--comparer A B`` compare deux rapports JSON du même fichier (NF-06, ADR-0112) : 0 si leurs
résultats sont identiques, 1 s'ils diffèrent, 2 si l'un n'est pas un rapport valide.

Chaîne de conservation, optionnelle (NF-17, ADR-0030) : ``--journal FICHIER`` tient un journal
chaîné des soumissions, refus, exports et rapports comparés, sans nom de fichier, et l'annonce
à chaque emploi ; ``--qui NOM`` y inscrit un nom déclaré (ADR-0260, ADR-0261).
``--verifier-journal FICHIER`` vérifie sa chaîne : 0 si elle est cohérente, 1 si elle est
rompue, 2 si le fichier n'est pas un journal. ``--horodater URL`` fait horodater chaque fichier
de rapport écrit par une autorité RFC 3161, ``1.json.tsr`` à côté de ``1.json`` (ADR-0262,
ADR-0263). Un horodatage non obtenu, ou une entrée du journal non écrite, donnent le code 1 ;
la seconde arrête la commande.

Conservation des données (NF-05) : à la fin d'une analyse ou d'une comparaison, un bloc dit où
est gardé chaque fichier lu ou écrit, et jusqu'à quand ; ``--conservation``, seule, affiche
l'énoncé complet, ce qui échappe à l'outil compris (ADR-0264, ADR-0266).

Hors d'un terminal, la sortie et l'erreur s'écrivent en UTF-8, quel que soit l'encodage local
(ADR-0238).
"""

import argparse
import hashlib
import io
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voight_kampff import __version__
from voight_kampff._conservation import horodatage, journal
from voight_kampff._limites import TAILLE_MAX_TEXTE
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import confiance as listes
from voight_kampff._orchestration import manifestes
from voight_kampff.analyse import Analyse, AnalyseRefusee, analyser, analyser_texte
from voight_kampff.rapport import comparaison, export
from voight_kampff.rapport._presentation import (
    Presentation,
    accorder,
    etat_partie,
    libelle,
    localisation,
    neutraliser,
    octets,
    origine_partie,
    technique,
    texte,
    textes,
)
from voight_kampff.rapport.comparaison import Nature
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    EtatTechnique,
    RaisonNonMenee,
    Saisie,
    VersionCatalogue,
)

_DESCRIPTION = (
    "Analyse la provenance et l'intégrité d'un fichier : preuves et indices de "
    "génération ou de retouche, sans verdict certain."
)

_EXTENSIONS = (".html", ".json")
_JETON = ".tsr"
_ECARTS_AFFICHES = 50
# Conditions de la garantie (ADR-0023), par le début du chemin de leurs écarts.
_RAISONS = (
    ("empreinte", "identification.empreinte"),
    ("extension", "identification.extension"),
    ("versions", "versions"),
)
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
        "--confiance",
        metavar="DOSSIER",
        help="remplace la liste de confiance C2PA livrée par celle de ce dossier ; le rapport "
        "le signale",
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
        "--texte",
        action="store_true",
        help="analyse le texte lu sur l'entrée standard (collé, puis Ctrl-D, ou Ctrl-Z et "
        "Entrée sous Windows ; ou reçu d'un tube) au lieu d'un fichier ; s'emploie sans fichier",
    )
    analyseur.add_argument(
        "--comparer",
        nargs=2,
        metavar=("RAPPORT_A", "RAPPORT_B"),
        help="compare deux rapports JSON du même fichier, à la date et au nom près, et dit si "
        "la garantie de reproductibilité s'applique ; s'emploie seule, ou avec --journal",
    )
    analyseur.add_argument(
        "--journal",
        metavar="FICHIER",
        help="tient un journal de conservation dans ce fichier, créé au besoin : l'empreinte de "
        "chaque fichier analysé et de chaque rapport écrit ou comparé, sans nom de fichier ; à "
        "qui détient l'original, elle suffit à confirmer que vous l'avez eu",
    )
    analyseur.add_argument(
        "--qui",
        metavar="NOM",
        help="nom inscrit à chaque entrée du journal, déclaré, non vérifié ; avec --journal",
    )
    analyseur.add_argument(
        "--verifier-journal",
        metavar="FICHIER",
        help="vérifie la chaîne d'un journal de conservation ; s'emploie seule",
    )
    analyseur.add_argument(
        "--horodater",
        metavar="URL",
        help="fait horodater chaque fichier de rapport écrit par cette autorité RFC 3161, que "
        "vous choisissez ; elle ne reçoit que l'empreinte du fichier ; avec --rapport",
    )
    analyseur.add_argument(
        "--conservation",
        action="store_true",
        help="dit où et combien de temps l'outil garde les fichiers analysés, les rapports, les "
        "jetons d'horodatage et le journal, et ce qui lui échappe ; s'emploie seule",
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
    for marquage in catalogue.marquages:
        recherche = marquage.module or f"non recherché : {marquage.raison}"
        print(f"{marquage.identifiant} ({recherche}) : {marquage.nom}")


_ETATS_AFFICHES = ("appliquee", "partielle", "non_menee", "hors_version")
"""États des techniques nommées au terminal, dans cet ordre ; les non applicables y sont
seulement comptées (ADR-0258)."""


def _techniques(analyse: Analyse) -> list[str]:
    """Techniques de chaque partie : une ligne par état qui les nomme, puis le nombre de non
    applicables, hors de cette version comprises (NF-11, ADR-0258)."""
    par_partie: dict[int, dict[str, list[str]]] = {}
    for t in analyse.couverture.techniques:
        hors_version = t.version is None and t.etat is not EtatTechnique.NON_APPLICABLE
        etat = "hors_version" if hors_version else t.etat.value
        par_partie.setdefault(t.partie, {}).setdefault(etat, []).append(technique(t.module))
    lignes = []
    for partie, etats in par_partie.items():
        lignes += [
            texte(
                "terminal.techniques",
                partie=partie,
                etat=texte(f"terminal.etats.{etat}"),
                techniques=", ".join(etats[etat]),
            )
            for etat in _ETATS_AFFICHES
            if etat in etats
        ]
        if non_applicables := etats.get(EtatTechnique.NON_APPLICABLE.value):
            lignes.append(accorder("terminal.non_applicables", len(non_applicables), partie=partie))
    return lignes


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
    lignes += [
        texte(
            "terminal.extraite",
            rang=partie.rang,
            format=partie.format,
            octets=octets(partie.octets),
            etat=etat_partie(partie),
            origine=origine_partie(partie),
        )
        for partie in identification.extraites
    ]
    lignes.append(
        texte("terminal.isolation", niveau=libelle("isolation", analyse.isolation.niveau))
    )
    lignes += _techniques(analyse)
    couverture = analyse.couverture
    if couverture.marquages_recherches:
        noms = (analyse.marquage(i).nom for i in couverture.marquages_recherches)
        lignes.append(texte("terminal.marquages", marquages=", ".join(noms)))
    lignes += [
        texte(
            "terminal.non_recherche",
            nom=analyse.marquage(marquage.identifiant).nom,
            raison=libelle("raisons_marquage", marquage.raison),
        )
        for marquage in couverture.marquages_non_recherches
    ]
    lignes += vue.resume()
    lignes += [
        texte(
            "terminal.marque",
            categorie=libelle("identifiantes", categorie),
            donnees=", ".join(dict.fromkeys(o.nom for o in observations)),
        )
        for categorie, observations in vue.marques()
    ]
    for non_menee in analyse.non_menees:
        if non_menee.raison in {RaisonNonMenee.HORS_PERIMETRE, RaisonNonMenee.HORS_V1}:
            continue  # déjà dit avec sa partie ou sa technique
        portee = [
            technique(non_menee.module) if non_menee.module else "",
            f"{texte('champs.partie').lower()} {non_menee.partie}" if non_menee.partie else "",
            localisation(non_menee.localisation) if non_menee.localisation else "",
        ]
        precision = ", ".join(element for element in portee if element)
        cle = "terminal.non_menee_precisee" if precision else "terminal.non_menee"
        lignes.append(texte(cle, raison=vue.non_menee(non_menee), precision=precision))
    lignes.append(texte("terminal.catalogue", catalogue=vue.catalogue()))
    lignes.append(texte("terminal.confiance", confiance=vue.confiance()))
    return lignes


def _ecrire(chemin: Path, contenu: bytes) -> None:
    """Crée le fichier, lisible par son seul propriétaire ; échoue s'il existe (ADR-0092)."""
    descripteur = os.open(chemin, _CREATION, 0o600)
    with os.fdopen(descripteur, "wb") as fichier:
        fichier.write(contenu)


def _preparer(dossier: str, nombre: int, jetons: bool = False) -> Path:
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
    noms = [e + j for e in _EXTENSIONS for j in ("", _JETON) if jetons or not j]
    for rang in range(1, nombre + 1):
        for extension in noms:
            if (chemin / f"{rang}{extension}").exists():
                raise ValueError(f"{rang}{extension} existe déjà ; aucun rapport n'est écrasé")
    return chemin


@dataclass
class _Ecrits:
    """Ce qu'une commande a écrit ou envoyé, pour le bloc de conservation (ADR-0264)."""

    rapports: bool = False
    jetons: bool = False
    autorite: bool = False


def lignes_conservation(
    soumis: int,
    texte_colle: bool,
    dossier: Path | None,
    ecrits: _Ecrits,
    tenu: journal.Journal | None,
) -> list[str]:
    """Bloc affiché à la fin d'une analyse : où et jusqu'à quand chaque donnée est gardée (NF-05).

    ``soumis`` vaut 0 pour une comparaison, dont les rapports lus remplacent les fichiers.
    Les lignes ne sont pas neutralisées : l'appelant le fait en les écrivant (ES-12).
    """
    cle = "conservation.donnees"
    lignes = [texte(f"{cle}.titre")]
    if not soumis:
        lignes.append(texte(f"{cle}.compares"))
    elif texte_colle:
        lignes.append(texte(f"{cle}.texte"))
    else:
        lignes.append(accorder(f"{cle}.fichiers", soumis))
    if soumis:
        if dossier is not None and ecrits.rapports:
            rapports = "rapports_jetons" if ecrits.jetons else "rapports"
            lignes.append(texte(f"{cle}.{rapports}", dossier=dossier))
        else:
            lignes.append(texte(f"{cle}.rapports_aucun"))
    if tenu is not None:
        lignes.append(texte(f"{cle}.journal", journal=tenu.chemin))
    if ecrits.autorite:
        lignes.append(texte(f"{cle}.autorite"))
    return [lignes[0], *(f"  {ligne}" for ligne in lignes[1:])]


def _afficher_conservation(lignes: Sequence[str]) -> None:
    print()
    for ligne in lignes:
        print(neutraliser(ligne))


def _consigner(repere: str, ajout: Callable[..., int], **champs: Any) -> int:
    """Ajoute une entrée au journal et rend son numéro ; à l'échec, le dit et rend 0."""
    try:
        return ajout(**champs)
    except journal.JournalInvalide as erreur:
        sys.stdout.flush()
        print(f"{repere} journal non écrit : {erreur} ; arrêt", file=sys.stderr)
        return 0


def _horodater(
    repere: str,
    fichier: Path,
    contenu: bytes,
    autorite: str | None,
    lignes: list[str],
    ecrits: _Ecrits,
) -> tuple[bool, dict[str, str] | None]:
    """Fait horodater un fichier de rapport écrit et écrit son jeton à côté (ADR-0262).

    Rend la réussite, vraie sans horodatage demandé, et ce que le journal garde du jeton ; la
    ligne du terminal s'ajoute à ``lignes``.
    """
    if autorite is None:
        return True, None
    ecrits.autorite = True  # la demande part, qu'elle aboutisse ou non
    chemin = fichier.with_name(fichier.name + _JETON)
    try:
        jeton = horodatage.horodater(autorite, hashlib.sha256(contenu).digest())
        _ecrire(chemin, jeton.reponse)
        ecrits.jetons = True
    except horodatage.HorodatageImpossible as erreur:
        sys.stdout.flush()
        print(f"{repere} {fichier.name} non horodaté : {erreur}", file=sys.stderr)
        return False, None
    except OSError as erreur:
        sys.stdout.flush()
        print(f"{repere} jeton de {fichier.name} non écrit : {erreur.strerror}", file=sys.stderr)
        return False, None
    heure = jeton.heure.strftime("%Y-%m-%d %H:%M:%S")
    lignes.append(texte("conservation.horodatage", fichier=fichier.name, heure=heure, jeton=chemin))
    return True, {
        "autorite": autorite,
        "heure": jeton.heure.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jeton": hashlib.sha256(jeton.reponse).hexdigest(),
    }


def _analyser(
    fichiers: Sequence[str | None],
    desactiver: Sequence[str],
    catalogue: str | None,
    confiance: str | None,
    dossier: Path | None,
    reveler: Sequence[str],
    tenu: journal.Journal | None = None,
    autorite: str | None = None,
) -> int:
    """Analyse chaque fichier ; ``None`` désigne le texte de l'entrée standard (ADR-0233).

    ``tenu`` est le journal de conservation, ``autorite`` l'autorité d'horodatage, s'ils sont
    demandés (ADR-0260, ADR-0262). Une entrée du journal non écrite arrête la commande. Le bloc
    de conservation s'affiche à la fin, arrêt compris (ADR-0264).
    """
    ecrits = _Ecrits()
    code = _analyser_chacun(
        fichiers, desactiver, catalogue, confiance, dossier, reveler, tenu, autorite, ecrits
    )
    _afficher_conservation(
        lignes_conservation(len(fichiers), None in fichiers, dossier, ecrits, tenu)
    )
    return code


def _analyser_chacun(
    fichiers: Sequence[str | None],
    desactiver: Sequence[str],
    catalogue: str | None,
    confiance: str | None,
    dossier: Path | None,
    reveler: Sequence[str],
    tenu: journal.Journal | None,
    autorite: str | None,
    ecrits: _Ecrits,
) -> int:
    """Boucle d'``_analyser`` ; ``ecrits`` reçoit ce qui a été écrit ou envoyé."""
    code = 0
    analysees = 0
    exemple: Path | None = None
    levees = [c.value for c in CategorieIdentifiante if c.value in reveler]
    for rang, chemin in enumerate(fichiers, start=1):
        repere = f"[{rang}/{len(fichiers)}]"
        saisie = (Saisie.FICHIER if chemin is not None else Saisie.TEXTE_COLLE).value
        try:
            if chemin is None:
                analyse = analyser_texte(
                    _lire_entree(), desactiver=desactiver, catalogue=catalogue, confiance=confiance
                )
            else:
                analyse = analyser(
                    chemin, desactiver=desactiver, catalogue=catalogue, confiance=confiance
                )
        except AnalyseRefusee as refus:
            sys.stdout.flush()  # les deux flux restent dans l'ordre des fichiers
            print(f"{repere} refusé : {refus}", file=sys.stderr)
            code = 1
            if tenu is not None and not _consigner(
                repere, tenu.refus, saisie=saisie, motif=refus.motif.value
            ):
                return 1
            continue
        analysees += 1
        numero = 0
        if tenu is not None:
            numero = _consigner(
                repere,
                tenu.soumission,
                saisie=saisie,
                empreinte=analyse.identification.empreinte,
                format_reel=analyse.identification.format_reel,
                levees=levees,
            )
            if not numero:
                return 1
        lignes = resume(analyse, reveler)
        if dossier is not None:
            html, json = (dossier / f"{rang}{extension}" for extension in _EXTENSIONS)
            rapports = (
                (html, export.exporter_html(analyse, reveler=reveler)),
                (json, export.exporter_json(analyse, reveler=reveler)),
            )
            horodatages: list[str] = []
            for fichier, contenu in rapports:
                octets_ = contenu.encode("utf-8")
                try:
                    _ecrire(fichier, octets_)
                except OSError as erreur:
                    sys.stdout.flush()
                    print(f"{repere} rapport non écrit : {erreur.strerror}", file=sys.stderr)
                    code = 1
                    break
                ecrits.rapports = True
                reussi, jeton = _horodater(repere, fichier, octets_, autorite, horodatages, ecrits)
                code = code if reussi else 1
                exemple = fichier if jeton is not None else exemple
                if tenu is not None and not _consigner(
                    repere,
                    tenu.export,
                    soumission=numero,
                    rapport=fichier.suffix.removeprefix("."),
                    empreinte=hashlib.sha256(octets_).hexdigest(),
                    horodatage=jeton,
                ):
                    return 1
            else:
                lignes.append(texte("terminal.rapport", html=html, json=json))
            lignes += horodatages
        print(neutraliser(f"{repere} {lignes[0]}"))
        for ligne in lignes[1:]:
            print(neutraliser(f"  {ligne}"))
    if analysees:
        print()
        for phrase in textes()["avertissement"]:
            print(phrase)
    if exemple is not None:
        tsr = exemple.with_name(exemple.name + _JETON)
        print(neutraliser(texte("conservation.verification_jeton", fichier=exemple, jeton=tsr)))
    return code


def _lire_entree() -> bytes:
    """Octets de l'entrée standard, un de plus que la limite pour qu'un texte trop long soit
    refusé sans être lu en entier (ADR-0233)."""
    if sys.stdin.isatty():
        print(texte("terminal.coller"), file=sys.stderr)
    return sys.stdin.buffer.read(TAILLE_MAX_TEXTE + 1)


def lignes_comparaison(resultat: comparaison.Comparaison) -> list[str]:
    """Lignes du résultat d'une comparaison : résultats, garantie, écarts (ADR-0112).

    Un écart n'est cité que par son chemin : aucune valeur, identifiante ou non, n'est affichée.
    Les lignes ne sont pas neutralisées : l'appelant le fait en les écrivant (ES-12).
    """
    ecarts = resultat.ecarts
    if resultat.identiques:
        lignes = [texte("comparaison.identiques")]
    else:
        lignes = [accorder("comparaison.differents", len(resultat.nature(Nature.RESULTAT)))]
    if resultat.garantie:
        lignes.append(texte("comparaison.garantie"))
    else:
        conditions = [ecart.chemin for ecart in resultat.nature(Nature.CONDITION)]
        raisons = [
            texte(f"comparaison.raisons.{raison}")
            for raison, prefixe in _RAISONS
            if any(chemin.startswith(prefixe) for chemin in conditions)
        ]
        if not resultat.meme_fichier:
            raisons.append(texte("comparaison.raisons.empreinte_masquee"))
        if resultat.interrompue:
            raisons.append(texte("comparaison.raisons.interrompue"))
        lignes.append(texte("comparaison.hors_garantie", raisons=", ".join(raisons)))
    if resultat.defaut:
        lignes.append(texte("comparaison.defaut"))
    if resultat.nature(Nature.ENVIRONNEMENT):
        lignes.append(texte("comparaison.environnement"))
    if resultat.non_comparees:
        categories = ", ".join(libelle("identifiantes", c) for c in resultat.non_comparees)
        lignes.append(texte("comparaison.non_comparees", categories=categories))
        if not resultat.meme_fichier:
            lignes.append(texte("comparaison.empreinte_masquee"))
    lignes += [
        texte(
            "comparaison.ecart",
            nature=texte(f"comparaison.natures.{ecart.nature}"),
            chemin=ecart.chemin,
        )
        for ecart in ecarts[:_ECARTS_AFFICHES]
    ]
    if len(ecarts) > _ECARTS_AFFICHES:
        lignes.append(accorder("comparaison.autres", len(ecarts) - _ECARTS_AFFICHES))
    return lignes


def _comparer(chemins: Sequence[str], tenu: journal.Journal | None = None) -> int:
    """Compare deux rapports ; chacun est consigné au journal, s'il est tenu, avant que le
    résultat ne s'affiche (ADR-0261)."""
    lus = []
    for rang, chemin in enumerate(chemins, start=1):
        try:
            lus.append(comparaison.lire_avec_empreinte(chemin))
        except comparaison.RapportIllisible as erreur:
            print(
                neutraliser(texte("comparaison.illisible", rang=rang, erreur=erreur)),
                file=sys.stderr,
            )
            return 2
    if tenu is not None:
        for rang, (_, empreinte) in enumerate(lus, start=1):
            if not _consigner(f"[{rang}/2]", tenu.consultation, empreinte=empreinte):
                _afficher_conservation(lignes_conservation(0, False, None, _Ecrits(), tenu))
                return 2
    resultat = comparaison.comparer(*(document for document, _ in lus))
    for ligne in lignes_comparaison(resultat):
        print(neutraliser(ligne))
    _afficher_conservation(lignes_conservation(0, False, None, _Ecrits(), tenu))
    return 0 if resultat.identiques else 1


def _verifier_journal(chemin: str) -> int:
    """Vérifie un journal : 0 s'il est cohérent, 1 s'il est rompu, 2 s'il est illisible."""
    try:
        bilan = journal.lire(chemin)
    except journal.JournalInvalide as erreur:
        if erreur.numero is None:
            print(texte("conservation.illisible", erreur=erreur), file=sys.stderr)
            return 2
        print(texte("conservation.rompu", numero=erreur.numero, erreur=erreur))
        return 1
    if bilan.premiere is None or bilan.derniere is None:
        print(texte("conservation.vide"))
    else:
        print(
            accorder(
                "conservation.coherent",
                bilan.entrees,
                premiere=bilan.premiere.strftime("%Y-%m-%d %H:%M:%S"),
                derniere=bilan.derniere.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
    print(texte("conservation.portee"))
    return 0


def _afficher_enonce() -> None:
    """Énoncé complet de la conservation des données (NF-05, ADR-0264, ADR-0266)."""
    for paragraphe in textes()["conservation"]["donnees"]["enonce"]:
        print(paragraphe)


def _ouvrir_journal(
    analyseur: argparse.ArgumentParser, arguments: argparse.Namespace
) -> journal.Journal | None:
    """Journal demandé, vérifié et annoncé ; un journal inutilisable arrête tout (code 2)."""
    if arguments.journal is None:
        return None
    try:
        tenu = journal.Journal(arguments.journal, arguments.qui)
    except journal.JournalInvalide as erreur:
        cause = f"entrée {erreur.numero} : {erreur}" if erreur.numero else str(erreur)
        analyseur.error(f"--journal : {cause} ; --verifier-journal le détaille")
    print(texte("conservation.avertissement_journal"), file=sys.stderr)
    return tenu


def _sortie_en_utf8() -> None:
    """Écrit en UTF-8 la sortie et l'erreur qui ne sont pas un terminal (ADR-0238, ERR-0013).

    Redirigé vers un fichier ou un tube, un flux s'écrit sinon dans l'encodage local, cp1252
    sous Windows, qui n'a ni « ⟨ » de la neutralisation (ADR-0096) ni la plupart des écritures.
    Un terminal garde le sien : la console de Windows reçoit déjà de l'UTF-8. Seul un substitut
    isolé ne s'écrit pas en UTF-8 : il s'écrit en échappement, sans erreur.
    """
    for flux in (sys.stdout, sys.stderr):
        if isinstance(flux, io.TextIOWrapper) and not flux.isatty():
            flux.reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée ; renvoie le code de sortie du processus."""
    _sortie_en_utf8()
    analyseur = construire_analyseur()
    arguments = analyseur.parse_args(argv)
    if arguments.conservation:
        options = {k: v for k, v in vars(arguments).items() if k != "conservation"}
        if any(options.values()):
            analyseur.error("--conservation s'emploie seule")
        _afficher_enonce()
        return 0
    if arguments.verifier_journal is not None:
        autres = (
            arguments.fichiers,
            arguments.modules,
            arguments.regles,
            arguments.texte,
            arguments.comparer,
            arguments.journal,
            arguments.horodater,
        )
        if any(autres):
            analyseur.error("--verifier-journal s'emploie seule")
        return _verifier_journal(arguments.verifier_journal)
    if arguments.qui is not None:
        if arguments.journal is None:
            analyseur.error("--qui s'emploie avec --journal")
        try:
            journal.verifier_qui(arguments.qui)
        except ValueError as erreur:
            analyseur.error(f"--qui : {erreur}")
    if arguments.horodater is not None:
        if arguments.rapport is None:
            analyseur.error(
                "--horodater s'emploie avec --rapport : il horodate les rapports écrits"
            )
        try:
            horodatage.verifier_url(arguments.horodater)
        except ValueError as erreur:
            analyseur.error(f"--horodater : {erreur}")
    if arguments.comparer is not None:
        if arguments.fichiers or arguments.modules or arguments.regles or arguments.texte:
            analyseur.error("--comparer s'emploie seule, sans fichier à analyser")
        if arguments.horodater is not None:
            analyseur.error("--horodater s'emploie avec une analyse, pas avec --comparer")
        return _comparer(arguments.comparer, _ouvrir_journal(analyseur, arguments))
    if arguments.journal is not None and not (arguments.fichiers or arguments.texte):
        analyseur.error("--journal s'emploie avec une analyse ou avec --comparer")
    if arguments.modules:
        _lister_modules()
        return 0
    if arguments.texte and arguments.fichiers:
        analyseur.error("--texte s'emploie sans fichier : le texte est lu sur l'entrée standard")
    if not (arguments.fichiers or arguments.regles or arguments.texte):
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
        listes.charger(arguments.confiance)
    except listes.ConfianceInvalide as erreur:
        analyseur.error(f"liste de confiance invalide : {erreur}")
    try:
        manifestes.selectionner(livres, arguments.desactiver)
    except manifestes.ModuleInconnu as erreur:
        connus = ", ".join(manifeste.identifiant for manifeste in livres) or "aucun"
        analyseur.error(f"{erreur} ; modules livrés : {connus}")
    dossier = None
    if arguments.rapport is not None:
        try:
            dossier = _preparer(
                arguments.rapport,
                max(len(arguments.fichiers), 1),
                jetons=arguments.horodater is not None,
            )
        except ValueError as erreur:
            analyseur.error(f"--rapport : {erreur}")
    tenu = _ouvrir_journal(analyseur, arguments)
    if arguments.horodater is not None:
        print(texte("conservation.avertissement_horodatage"), file=sys.stderr)
    return _analyser(
        [None] if arguments.texte else arguments.fichiers,
        arguments.desactiver,
        arguments.catalogue,
        arguments.confiance,
        dossier,
        arguments.reveler,
        tenu,
        arguments.horodater,
    )
