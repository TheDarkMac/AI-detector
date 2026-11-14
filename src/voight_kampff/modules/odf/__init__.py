"""Module ``odf`` : métadonnées d'un document ODT (F-10, ADR-0136 à ADR-0140 ; fiche
``metadonnees-odf``).

Lit l'entrée ``meta.xml`` du paquet (OpenDocument, partie 3) et observe chaque enfant de
``office:meta`` sous ``odf.<préfixe>:<nom>`` : ``odf.meta:generator``, ``odf.dc:title``,
``odf.meta:initial-creator``, ``odf.meta:creation-date``, ``odf.meta:editing-cycles``,
``odf.meta:editing-duration``… Les attributs d'un élément suivent son nom
(``odf.meta:document-statistic.meta:page-count``) ; une propriété utilisateur est nommée par
le document (``odf.meta:user-defined.<nom>``). Observe aussi ``odf.present`` dans tous les cas
(F-14), et la version d'OpenDocument (``odf.version``).

Les dates et durées sont observées telles qu'écrites (ISO 8601). Les références (attributs
``xlink`` : modèle, rechargement automatique) ne sont ni lues ni suivies (ES-06, ADR-0138).
Aucune règle « module » : les règles du catalogue lisent ces observations (T22, T23, T81).
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.arbre import Noeud, lire_arbre
from voight_kampff.modules._lecture.proprietes import Proprietes, booleen, entier, reel
from voight_kampff.modules._lecture.zip import Archive, Illisible
from voight_kampff.rapport.modele import CategorieIdentifiante, Localisation, RaisonNonMenee

__all__ = ["analyser"]

_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
_META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
_XLINK = "http://www.w3.org/1999/xlink"
_CONNUS = {
    _OFFICE: "office",
    _META: "meta",
    "http://purl.org/dc/elements/1.1/": "dc",
    _XLINK: "xlink",
}
"""Préfixes de la spécification OpenDocument pour les espaces des métadonnées."""
_IGNORES = frozenset({_XLINK, "http://www.w3.org/XML/1998/namespace"})
"""Attributs non lus : références (ADR-0138) et langue (``xml:lang``)."""

_ENTIERS = frozenset({"editing-cycles"})
_STATISTIQUES = "document-statistic"
"""Ses attributs sont des nombres d'éléments du document : des entiers."""
_UTILISATEUR = "user-defined"
_TYPES = {"float": reel, "percentage": reel, "boolean": booleen}
"""Type d'une propriété utilisateur (``meta:value-type``) ; les autres sont des textes."""

_NOMINATIVES = frozenset({"meta:initial-creator", "dc:creator", "meta:printed-by"})
_TEXTES_LIBRES = frozenset({"dc:title", "dc:subject", "dc:description", "meta:keyword"})
"""Titre, sujet, description, mots-clés ; les propriétés utilisateur le sont toutes (ADR-0160)."""


def analyser(contexte: Contexte) -> None:
    try:
        archive = Archive(contexte)
        entree = archive.trouver("meta.xml")
    except Illisible as illisible:
        contexte.observer("odf.present", False)
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    contexte.observer("odf.present", entree is not None)
    if entree is None:
        return
    contexte.observer("odf.blocs", 1)
    try:
        donnees = archive.lire(entree)
        localisation = archive.localisation(entree)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    racines, partiel = lire_arbre(contexte, donnees)
    racine = next((r for r in racines if r.est(_OFFICE, "document-meta")), None)
    meta = (
        None
        if racine is None
        else next((e for e in racine.enfants if e.est(_OFFICE, "meta")), None)
    )
    if racine is not None and (version := racine.attributs.get((_OFFICE, "version"))):
        valeurs.observer(contexte, "odf.version", version, localisation=localisation)
    proprietes = Proprietes("odf", _CONNUS)
    complete = meta is not None
    if meta is not None:
        for element in meta.enfants:
            complete &= _element(proprietes, element, localisation)
    proprietes.observer(contexte)
    if partiel or not complete:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)


def _identifiante(nom: str) -> CategorieIdentifiante | None:
    if nom in _NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if nom in _TEXTES_LIBRES:
        return CategorieIdentifiante.TEXTE_LIBRE
    return None


def _element(proprietes: Proprietes, element: Noeud, localisation: Localisation) -> bool:
    """Propriétés d'un enfant de ``office:meta`` ; faux s'il n'a pas pu être lu."""
    nom = proprietes.composant(element.espace, element.nom, localisation)
    texte = "".join(element.texte)
    if element.espace == _META and element.nom == _UTILISATEUR:
        designation = element.attributs.get((_META, "name"))
        if not designation:
            return False
        lire = _TYPES.get(element.attributs.get((_META, "value-type"), ""))
        valeur = texte if lire is None else lire(texte)
        proprietes.ajouter(
            f"{nom}.{valeurs.composant(designation)}",
            valeur,
            localisation,
            CategorieIdentifiante.TEXTE_LIBRE,
        )
        return True
    identifiante = _identifiante(nom)
    statistiques = element.espace == _META and element.nom == _STATISTIQUES
    for (espace, attribut), valeur in element.attributs.items():
        if espace in _IGNORES:
            continue
        champ = f"{nom}.{proprietes.composant(espace, attribut, localisation)}"
        proprietes.ajouter(champ, entier(valeur) if statistiques else valeur, localisation)
    entiere = element.espace == _META and element.nom in _ENTIERS
    proprietes.ajouter(nom, entier(texte) if entiere else texte, localisation, identifiante)
    return True
