"""Module ``matroska`` : éléments ``Info`` et ``Tags`` d'un WebM (F-10, ADR-0114, ADR-0131,
ADR-0132, ADR-0133 ; fiche ``metadonnees-matroska``).

Lit, dans le segment (RFC 9559) :

- ``Info`` : ``Title``, ``MuxingApp``, ``WritingApp`` (bibliothèque et logiciel d'écriture),
  ``DateUTC``, telle qu'écrite, en nanosecondes depuis 2001, et les noms de fichier
  ``SegmentFilename``, ``PrevFilename``, ``NextFilename``, sous ``matroska.<élément>`` ;
- ``Tags`` : chaque balise simple, sous ``matroska.tag.<NOM>`` si elle porte sur tout le
  segment, ``matroska.piste.<NOM>`` si elle vise une piste, ``matroska.cible.<NOM>`` si elle
  vise une édition, un chapitre ou un fichier joint ; une balise imbriquée à la suite de son
  parent ; une balise binaire par sa seule taille.

Observe aussi ``matroska.present`` dans tous les cas (F-14). Aucune règle « module » : les
règles du catalogue lisent ces observations (T22, T23).
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import ebml, valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.rapport.modele import CategorieIdentifiante, Localisation, RaisonNonMenee

__all__ = ["analyser"]

_DATE = "ns depuis 2001-01-01 UTC"
_INFO = {
    0x7BA9: "Title",
    0x4D80: "MuxingApp",
    0x5741: "WritingApp",
    0x7384: "SegmentFilename",
    0x3C83AB: "PrevFilename",
    0x3E83BB: "NextFilename",
}
"""Éléments de texte d'``Info`` lus (RFC 9559)."""
_DATE_UTC = 0x4461
_FICHIERS = frozenset({"SegmentFilename", "PrevFilename", "NextFilename"})
_LIEUX = frozenset(valeurs.composant(nom) for nom in ("RECORDING_LOCATION", "COMPOSITION_LOCATION"))
"""Balises officielles d'un lieu (Matroska, « Tagging »), passées par la règle des composants
comme ``_NOMINATIVES`` : ADR-0160."""
_TEXTES_LIBRES = frozenset(
    {"TITLE", "SUBTITLE", "DESCRIPTION", "SYNOPSIS", "SUMMARY", "COMMENT", "KEYWORDS", "LYRICS"}
)
"""Balises officielles de titre, description, résumé, commentaire, mots-clés, paroles ; avec
l'élément ``Title`` d'``Info`` : ADR-0160."""
_TAG = 0x7373
_TARGETS = 0x63C0
_SIMPLE_TAG = 0x67C8
_TAG_NAME = 0x45A3
_TAG_STRING = 0x4487
_TAG_BINARY = 0x4485
_PISTE = 0x63C5
_AUTRES_CIBLES = frozenset({0x63C9, 0x63C4, 0x63C6})
"""``TagEditionUID``, ``TagChapterUID``, ``TagAttachmentUID``."""
_NOMINATIVES = frozenset(
    valeurs.composant(nom)
    for nom in (
        "ARTIST",
        "LEAD_PERFORMER",
        "ACCOMPANIMENT",
        "COMPOSER",
        "ARRANGER",
        "LYRICIST",
        "CONDUCTOR",
        "DIRECTOR",
        "ASSISTANT_DIRECTOR",
        "DIRECTOR_OF_PHOTOGRAPHY",
        "SOUND_ENGINEER",
        "ART_DIRECTOR",
        "PRODUCTION_DESIGNER",
        "CHOREGRAPHER",
        "COSTUME_DESIGNER",
        "ACTOR",
        "WRITTEN_BY",
        "SCREENPLAY_BY",
        "EDITED_BY",
        "PRODUCER",
        "COPRODUCER",
        "EXECUTIVE_PRODUCER",
        "DISTRIBUTED_BY",
        "MASTERED_BY",
        "ENCODED_BY",
        "MIXED_BY",
        "REMIXED_BY",
        "PRODUCTION_STUDIO",
        "THANKS_TO",
        "PUBLISHER",
        "LABEL",
        "COPYRIGHT",
        "PRODUCTION_COPYRIGHT",
    )
)
"""Balises officielles qui nomment une personne ou un organisme (Matroska, « Tagging »),
comparées à leur nom passé par la règle des composants (ADR-0119, ADR-0133)."""


_IDENTIFIANTES_INFO = {
    **dict.fromkeys(_FICHIERS, CategorieIdentifiante.NOM_DE_FICHIER),
    "Title": CategorieIdentifiante.TEXTE_LIBRE,
}


def _identifiante(nom: str) -> CategorieIdentifiante | None:
    if nom in _NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if nom in _LIEUX:
        return CategorieIdentifiante.LIEU
    if nom in _TEXTES_LIBRES:
        return CategorieIdentifiante.TEXTE_LIBRE
    return None


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [bloc for bloc in releve.blocs if bloc.nature is Nature.MATROSKA]
    contexte.observer("matroska.present", bool(blocs))
    if blocs:
        contexte.observer("matroska.blocs", len(blocs))
    for bloc in blocs:
        donnees = lire_bloc(contexte, bloc)
        try:
            if bloc.chemin == "Segment/Info":
                _info(contexte, bloc, donnees)
            else:
                _tags(contexte, bloc, donnees)
        except ebml.Invalide:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _info(contexte: Contexte, bloc: Bloc, donnees: bytes) -> None:
    localisation = bloc.localisation()
    for identifiant, debut, fin in ebml.enfants(donnees, 0, len(donnees)):
        contexte.compter_objets()
        if identifiant == _DATE_UTC:
            date = valeurs.entier(ebml.signe(donnees[debut:fin]))
            contexte.observer("matroska.DateUTC", date, unite=_DATE, localisation=localisation)
        elif identifiant in _INFO and fin > debut:
            nom = _INFO[identifiant]
            valeurs.observer(
                contexte,
                f"matroska.{nom}",
                _texte(donnees[debut:fin]),
                localisation=localisation,
                identifiante=_IDENTIFIANTES_INFO.get(nom),
            )


def _tags(contexte: Contexte, bloc: Bloc, donnees: bytes) -> None:
    for identifiant, debut, fin in ebml.enfants(donnees, 0, len(donnees)):
        contexte.compter_objets()
        if identifiant != _TAG:
            continue
        enfants = list(ebml.enfants(donnees, debut, fin))
        prefixe = "matroska.tag"
        for sous, d, f in enfants:
            if sous == _TARGETS:
                prefixe = _prefixe(donnees, d, f)
        localisation = bloc.localisation()
        for sous, d, f in enfants:
            if sous == _SIMPLE_TAG:
                _simple(contexte, donnees, d, f, prefixe, localisation)


def _prefixe(donnees: bytes, debut: int, fin: int) -> str:
    """Partie du nom selon la cible (RFC 9559, « Targets ») : un identifiant nul vaut absence."""
    cibles = {i for i, d, f in ebml.enfants(donnees, debut, fin) if ebml.entier(donnees[d:f])}
    if _PISTE in cibles:
        return "matroska.piste"
    if cibles & _AUTRES_CIBLES:
        return "matroska.cible"
    return "matroska.tag"


def _simple(
    contexte: Contexte,
    donnees: bytes,
    debut: int,
    fin: int,
    prefixe: str,
    localisation: Localisation,
) -> None:
    """Balise simple : nom, texte ou binaire, balises imbriquées sous son nom."""
    contexte.compter_objets()
    nom: str | None = None
    texte: str | None = None
    binaire: int | None = None
    imbriquees: list[tuple[int, int]] = []
    for identifiant, d, f in ebml.enfants(donnees, debut, fin):
        if identifiant == _TAG_NAME:
            nom = _texte(donnees[d:f])
        elif identifiant == _TAG_STRING:
            texte = _texte(donnees[d:f])
        elif identifiant == _TAG_BINARY:
            binaire = f - d
        elif identifiant == _SIMPLE_TAG:
            imbriquees.append((d, f))
    if not nom:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
        return
    complet = valeurs.borner(f"{prefixe}.{valeurs.composant(nom)}")
    identifiante = _identifiante(valeurs.composant(nom).upper())
    if texte:
        valeurs.observer(
            contexte, complet, texte, localisation=localisation, identifiante=identifiante
        )
    if binaire:
        contexte.observer(
            f"{complet}.taille",
            binaire,
            unite="octets",
            localisation=localisation,
            identifiante=identifiante,
        )
    with contexte.imbrication():
        for d, f in imbriquees:
            _simple(contexte, donnees, d, f, complet, localisation)


def _texte(octets: bytes) -> str:
    """Chaîne UTF-8 (RFC 8794, §7.6), complétée parfois par des nuls."""
    return octets.decode("utf-8", "replace").rstrip("\x00")
