"""Module ``vorbis`` : commentaires Vorbis d'un FLAC ou d'un Ogg (F-10, ADR-0114, ADR-0131,
ADR-0132, ADR-0133 ; fiche ``metadonnees-vorbis``).

Lit le bloc ``VORBIS_COMMENT`` d'un FLAC (RFC 9639, §8.6), et le paquet de commentaires de
chaque flux Vorbis, Opus, Theora, Speex ou FLAC d'un Ogg. La chaîne du fournisseur, qui nomme
d'ordinaire la bibliothèque d'encodage, est observée sous ``vorbis.vendor`` ; chaque champ sous
``vorbis.<NOM>``, en majuscules, le nom d'un champ ne distinguant pas la casse ; un champ
répété donne une liste. Une image (``METADATA_BLOCK_PICTURE``, ``COVERART``) est observée par
sa seule taille. Observe aussi ``vorbis.present`` dans tous les cas (F-14).

Aucune règle « module » : les règles du catalogue lisent ces observations (T22, T23).
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.rapport.modele import CategorieIdentifiante, Localisation, RaisonNonMenee

__all__ = ["analyser"]

_NOMINATIVES = frozenset(
    valeurs.composant(nom)
    for nom in (
        "ARTIST",
        "ALBUMARTIST",
        "ALBUM ARTIST",
        "PERFORMER",
        "COMPOSER",
        "LYRICIST",
        "CONDUCTOR",
        "ARRANGER",
        "REMIXER",
        "PRODUCER",
        "AUTHOR",
        "WRITER",
        "PUBLISHER",
        "COPYRIGHT",
        "CONTACT",
        "ENCODED-BY",
        "ENCODEDBY",
    )
)
"""Champs qui nomment une personne ou un organisme (ADR-0119, ADR-0133) : ceux de la liste de
Xiph.org, et ceux qu'emploient les logiciels courants."""
_LIEUX = frozenset({"LOCATION"})
"""Lieu de l'enregistrement (liste de Xiph.org) : ADR-0160."""
_TEXTES_LIBRES = frozenset(
    {"TITLE", "SUBTITLE", "ALBUM", "DESCRIPTION", "COMMENT", "LYRICS", "UNSYNCEDLYRICS"}
)
"""Titres, album, description, commentaire, paroles : ADR-0160."""
_IMAGES = frozenset({"METADATA-BLOCK-PICTURE", "COVERART"})
"""Images codées en base 64 : observées par leur taille, comme une donnée binaire (ADR-0118)."""


class _Illisible(Exception):
    pass


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [bloc for bloc in releve.blocs if bloc.nature is Nature.VORBIS]
    contexte.observer("vorbis.present", bool(blocs))
    if blocs:
        contexte.observer("vorbis.blocs", len(blocs))
    for bloc in blocs:
        _commentaires(contexte, bloc)
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _commentaires(contexte: Contexte, bloc: Bloc) -> None:
    """Fournisseur, puis champs ``NOM=valeur`` en UTF-8, longueurs sur quatre octets
    petit-boutistes (Vorbis I, §5).

    Les champs lus avant une longueur qui déborde sont observés ; le bloc est alors non mené,
    une fois, comme s'il contient un champ sans ``=``.
    """
    donnees = lire_bloc(contexte, bloc)
    localisation = bloc.localisation()
    champs: dict[str, list[str]] = {}
    tailles: dict[str, int] = {}
    partiel = False
    try:
        fournisseur, position = _chaine(donnees, 0)
        valeurs.observer(contexte, "vorbis.vendor", _texte(fournisseur), localisation=localisation)
        nombre, position = _entier(donnees, position)
        for _ in range(nombre):
            contexte.compter_objets()
            champ, position = _chaine(donnees, position)
            nom, egal, valeur = champ.partition(b"=")
            if not egal or not nom:
                partiel = True
                continue
            cle = valeurs.composant(nom.decode("ascii", "replace").upper())
            if cle in _IMAGES:
                tailles[cle] = tailles.get(cle, 0) + len(valeur)
            else:
                champs.setdefault(cle, []).append(_texte(valeur))
    except _Illisible:
        partiel = True
    for cle, textes in champs.items():
        _observer(contexte, cle, textes, localisation)
    for cle, taille in tailles.items():
        contexte.observer(f"vorbis.{cle}.taille", taille, unite="octets", localisation=localisation)
    if partiel:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)


def _observer(contexte: Contexte, cle: str, textes: list[str], localisation: Localisation) -> None:
    valeurs.observer(
        contexte,
        valeurs.borner(f"vorbis.{cle}"),
        textes[0] if len(textes) == 1 else textes,
        localisation=localisation,
        identifiante=_identifiante(cle),
    )


def _identifiante(cle: str) -> CategorieIdentifiante | None:
    if cle in _NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if cle in _LIEUX:
        return CategorieIdentifiante.LIEU
    if cle in _TEXTES_LIBRES:
        return CategorieIdentifiante.TEXTE_LIBRE
    return None


def _entier(donnees: bytes, position: int) -> tuple[int, int]:
    if position + 4 > len(donnees):
        raise _Illisible
    return int.from_bytes(donnees[position : position + 4], "little"), position + 4


def _chaine(donnees: bytes, position: int) -> tuple[bytes, int]:
    longueur, debut = _entier(donnees, position)
    if debut + longueur > len(donnees):
        raise _Illisible
    return donnees[debut : debut + longueur], debut + longueur


def _texte(octets: bytes) -> str:
    """UTF-8, que fixe la norme ; un octet invalide devient le caractère de remplacement."""
    return octets.decode("utf-8", "replace")
