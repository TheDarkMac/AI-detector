"""Soumission d'un fichier : ouverture, empreinte, analyse, contrôles (F-01 à F-05, ES-08).

Le processus principal ouvre le fichier une fois, vérifie sur le descripteur que c'est un
fichier régulier, le hache, puis transmet ce même descripteur au processus de travail : un
lien remplacé entre-temps ne change pas le fichier analysé (M-06, M-30). En fin d'analyse,
l'empreinte recalculée par le travail doit être celle du début ; si le travail s'est arrêté
avant de l'envoyer, le principal hache de nouveau le fichier (ADR-0075).

Le principal ne lit le fichier que pour le hacher : l'identification se fait dans le travail.
Un fichier de plus de 1 Gio est refusé « hors limites » avant d'être lu (F-04, ADR-0077).

Le catalogue, livré ou fourni par l'utilisateur, est validé avant l'ouverture du fichier
(ADR-0029, ADR-0086) ; sa version et les règles que citent les constats sont jointes à
l'analyse (ADR-0097). Les techniques hors de cette version sont inscrites non menées pour
chaque partie d'un de leurs formats (ADR-0087).
"""

import hashlib
import os
import stat
from collections.abc import Callable, Collection, Sequence
from datetime import UTC, datetime
from pathlib import Path

from voight_kampff._limites import TAILLE_MAX_FICHIER
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes as livres
from voight_kampff._orchestration.catalogue import Catalogue
from voight_kampff._orchestration.manifestes import Manifeste, TechniqueHorsV1, selectionner
from voight_kampff._orchestration.travail import DELAI, ResultatTravail, commande_travail, executer
from voight_kampff.analyse import Analyse, AnalyseRefusee, MotifRefus
from voight_kampff.rapport.modele import (
    RAISONS_D_INTERRUPTION,
    Couverture,
    EtatTechnique,
    Identification,
    NonMenee,
    Partie,
    RaisonNonMenee,
    TechniqueCouverte,
)

__all__ = ["empreinte", "nom_affichable", "ouvrir", "soumettre"]

_DRAPEAUX = (
    os.O_RDONLY
    | getattr(os, "O_NONBLOCK", 0)  # un tube nommé ne bloque pas l'ouverture
    | getattr(os, "O_NOCTTY", 0)
    | getattr(os, "O_BINARY", 0)
)
_BLOC = 1 << 20
_REMPLACEMENT = "�"


def ouvrir(chemin: str | os.PathLike[str]) -> int:
    """Ouvre en lecture seule ; refuse ce qui n'est pas un fichier régulier (ES-08)."""
    try:
        descripteur = os.open(chemin, _DRAPEAUX)
    except OSError as erreur:
        raise AnalyseRefusee(MotifRefus.ILLISIBLE, detail=erreur.strerror) from None
    if not stat.S_ISREG(os.fstat(descripteur).st_mode):
        os.close(descripteur)
        raise AnalyseRefusee(MotifRefus.NON_REGULIER)
    return descripteur


def empreinte(descripteur: int, maximum: int | None = None) -> tuple[str, int]:
    """SHA-256 du fichier entier et sa taille, depuis le début (ADR-0040).

    Avec ``maximum``, la lecture s'arrête au premier bloc qui le dépasse : la taille rendue
    dit alors que le fichier est trop grand, et l'empreinte n'a pas de sens.
    """
    os.lseek(descripteur, 0, os.SEEK_SET)
    condensat = hashlib.sha256()
    taille = 0
    while bloc := os.read(descripteur, _BLOC):
        condensat.update(bloc)
        taille += len(bloc)
        if maximum is not None and taille > maximum:
            break
    return condensat.hexdigest(), taille


def nom_affichable(chemin: str | os.PathLike[str]) -> str:
    """Nom du fichier sans chemin (ES-14) ; ce que le modèle refuse est remplacé par U+FFFD.

    Un nom POSIX peut contenir une barre oblique inverse ou des octets non UTF-8 : il reste
    lisible, sans devenir un chemin.
    """
    nom = Path(chemin).name
    nom = "".join(
        _REMPLACEMENT if caractere in "\\\x00" or "\ud800" <= caractere <= "\udfff" else caractere
        for caractere in nom
    )
    return nom or _REMPLACEMENT


def soumettre(
    chemin: str | os.PathLike[str],
    desactives: Collection[str] = (),
    *,
    catalogue: Catalogue | str | os.PathLike[str] | None = None,
    manifestes: Sequence[Manifeste] | None = None,
    hors_v1: Sequence[TechniqueHorsV1] | None = None,
    delai: float = DELAI,
    commande: Callable[[int], Sequence[str]] = commande_travail,
) -> Analyse:
    """Analyse un fichier ; lève :class:`AnalyseRefusee` s'il n'y a rien à livrer.

    ``catalogue`` est un catalogue déjà validé, ou le dossier d'un catalogue fourni par
    l'utilisateur ; par défaut, le catalogue livré. ``manifestes``, ``hors_v1`` et
    ``commande`` remplacent, pour les tests, les modules, les techniques hors de cette version
    et le processus de travail livrés.
    """
    modules = livres.decouvrir() if manifestes is None else tuple(manifestes)
    selectionner(modules, desactives)  # un module inconnu est refusé avant toute lecture
    if not isinstance(catalogue, Catalogue):
        catalogue = catalogues.charger(modules, catalogue)
    techniques_hors_v1 = livres.hors_v1(modules) if hors_v1 is None else tuple(hors_v1)
    date_analyse = datetime.now(UTC).replace(microsecond=0)
    descripteur = ouvrir(chemin)
    try:
        # Taille annoncée d'abord, pour ne pas lire un fichier énorme ; puis taille lue, s'il a
        # grandi entre-temps.
        if os.fstat(descripteur).st_size > TAILLE_MAX_FICHIER:
            raise AnalyseRefusee(MotifRefus.HORS_LIMITES)
        initiale, taille = empreinte(descripteur, TAILLE_MAX_FICHIER)
        if taille > TAILLE_MAX_FICHIER:
            raise AnalyseRefusee(MotifRefus.HORS_LIMITES)
        if taille == 0:
            raise AnalyseRefusee(MotifRefus.VIDE)
        resultat = executer(
            descripteur,
            modules,
            desactives,
            catalogue=catalogue,
            taille=taille,
            delai=delai,
            commande=commande,
        )
        finale = resultat.empreinte or empreinte(descripteur, TAILLE_MAX_FICHIER)[0]
    finally:
        os.close(descripteur)
    if finale != initiale:
        raise AnalyseRefusee(MotifRefus.FICHIER_MODIFIE)
    identification = _identification(
        resultat, nom_affichable(chemin), taille, initiale, date_analyse
    )
    techniques, non_menees = _hors_v1(identification.parties, techniques_hors_v1)
    return Analyse(
        identification=identification,
        isolation=resultat.isolation,
        couverture=Couverture(
            resultat.couverture.techniques + techniques,
            resultat.couverture.marquages_recherches,
        ),
        observations=resultat.observations,
        constats=resultat.constats,
        non_menees=resultat.non_menees + non_menees,
        dependances=resultat.dependances,
        catalogue=catalogue.version,
        regles=tuple(
            regle
            for regle in catalogue.regles
            if any(constat.regle == regle.reference for constat in resultat.constats)
        ),
    )


def _hors_v1(
    parties: Sequence[Partie], techniques: Sequence[TechniqueHorsV1]
) -> tuple[tuple[TechniqueCouverte, ...], tuple[NonMenee, ...]]:
    """Couverture et non menées des techniques hors de cette version (ADR-0012, ADR-0087).

    Seules figurent celles qui s'appliqueraient à au moins une partie analysée : non menées
    sur les parties de leurs formats, non applicables sur les autres d'un polyglotte, puisque
    chaque technique figure une fois par partie analysée (ADR-0071).
    """
    analysees = [partie for partie in parties if partie.dans_perimetre]
    couverture: list[TechniqueCouverte] = []
    non_menees: list[NonMenee] = []
    for technique in techniques:
        if not any(partie.format in technique.formats for partie in analysees):
            continue
        for partie in analysees:
            if partie.format in technique.formats:
                etat = EtatTechnique.NON_MENEE
                non_menees.append(
                    NonMenee(RaisonNonMenee.HORS_V1, technique.identifiant, partie=partie.rang)
                )
            else:
                etat = EtatTechnique.NON_APPLICABLE
            couverture.append(TechniqueCouverte(technique.identifiant, etat, None, partie.rang))
    return tuple(couverture), tuple(non_menees)


def _identification(
    resultat: ResultatTravail, nom: str, taille: int, empreinte_: str, date_analyse: datetime
) -> Identification:
    if resultat.parties is None:
        arret = next(n.raison for n in resultat.non_menees if n.raison in RAISONS_D_INTERRUPTION)
        raise AnalyseRefusee(MotifRefus.ANALYSE_IMPOSSIBLE, raison=arret)
    if not resultat.parties:
        raise AnalyseRefusee(MotifRefus.FORMAT_INCONNU)
    if not any(partie.dans_perimetre for partie in resultat.parties):
        formats = tuple(dict.fromkeys(partie.format for partie in resultat.parties))
        raise AnalyseRefusee(MotifRefus.HORS_PERIMETRE, formats=formats)
    return Identification(
        nom=nom,
        format_reel=resultat.parties[0].format,
        taille=taille,
        empreinte=empreinte_,
        date_analyse=date_analyse,
        parties=resultat.parties,
    )
