"""Soumission d'un fichier : ouverture, empreinte, analyse, contrôles (F-01 à F-05, ES-08).

Le processus principal ouvre le fichier une fois, vérifie sur le descripteur que c'est un
fichier régulier, le hache, puis transmet ce même descripteur au processus de travail : un
lien remplacé entre-temps ne change pas le fichier analysé (M-06, M-30). En fin d'analyse,
l'empreinte recalculée par le travail doit être celle du début ; si le travail s'est arrêté
avant de l'envoyer, le principal hache de nouveau le fichier (ADR-0075).

Le principal ne lit le fichier que pour le hacher : l'identification se fait dans le travail.
Un fichier de plus de 1 Gio est refusé « hors limites » avant d'être lu (F-04, ADR-0077).
"""

import hashlib
import os
import stat
from collections.abc import Callable, Collection, Sequence
from datetime import UTC, datetime
from pathlib import Path

from voight_kampff._limites import TAILLE_MAX_FICHIER
from voight_kampff._orchestration import manifestes as livres
from voight_kampff._orchestration.manifestes import Manifeste, selectionner
from voight_kampff._orchestration.travail import DELAI, ResultatTravail, commande_travail, executer
from voight_kampff.analyse import Analyse, AnalyseRefusee, MotifRefus
from voight_kampff.rapport.modele import RAISONS_D_INTERRUPTION, Identification

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
    manifestes: Sequence[Manifeste] | None = None,
    delai: float = DELAI,
    commande: Callable[[int], Sequence[str]] = commande_travail,
) -> Analyse:
    """Analyse un fichier ; lève :class:`AnalyseRefusee` s'il n'y a rien à livrer.

    ``manifestes`` et ``commande`` remplacent, pour les tests, les modules et le processus
    de travail livrés.
    """
    modules = livres.decouvrir() if manifestes is None else tuple(manifestes)
    selectionner(modules, desactives)  # un module inconnu est refusé avant toute lecture
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
            descripteur, modules, desactives, taille=taille, delai=delai, commande=commande
        )
        finale = resultat.empreinte or empreinte(descripteur, TAILLE_MAX_FICHIER)[0]
    finally:
        os.close(descripteur)
    if finale != initiale:
        raise AnalyseRefusee(MotifRefus.FICHIER_MODIFIE)
    return _analyse(resultat, nom_affichable(chemin), taille, initiale, date_analyse)


def _analyse(
    resultat: ResultatTravail, nom: str, taille: int, empreinte_: str, date_analyse: datetime
) -> Analyse:
    if resultat.parties is None:
        arret = next(n.raison for n in resultat.non_menees if n.raison in RAISONS_D_INTERRUPTION)
        raise AnalyseRefusee(MotifRefus.ANALYSE_IMPOSSIBLE, raison=arret)
    if not resultat.parties:
        raise AnalyseRefusee(MotifRefus.FORMAT_INCONNU)
    if not any(partie.dans_perimetre for partie in resultat.parties):
        formats = tuple(dict.fromkeys(partie.format for partie in resultat.parties))
        raise AnalyseRefusee(MotifRefus.HORS_PERIMETRE, formats=formats)
    identification = Identification(
        nom=nom,
        format_reel=resultat.parties[0].format,
        taille=taille,
        empreinte=empreinte_,
        date_analyse=date_analyse,
        parties=resultat.parties,
    )
    return Analyse(
        identification=identification,
        isolation=resultat.isolation,
        couverture=resultat.couverture,
        observations=resultat.observations,
        constats=resultat.constats,
        non_menees=resultat.non_menees,
        dependances=resultat.dependances,
    )
