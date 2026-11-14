"""Module ``infopdf`` : dictionnaire d'information d'un PDF (F-10, ADR-0114, ADR-0127 ; fiche
``metadonnees-info-pdf``).

Lit le dictionnaire que désigne la clé ``/Info`` du trailer le plus récent (ISO 32000-2,
§14.3.3) et observe chacune de ses entrées sous ``infopdf.<clé>`` : ``Title``, ``Author``,
``Creator``, ``Producer``, ``CreationDate``… et les clés propres à un logiciel. Les dates sont
observées telles qu'écrites (``D:AAAAMMJJHHmmSS+HH'mm'``). Observe aussi ``infopdf.present``
dans tous les cas (F-14), et ``infopdf.chiffre`` dès que la table des références croisées se
lit ; noms et formes des valeurs : ADR-0128.

Un document chiffré n'est pas déchiffré : ses chaînes ne sont pas lues (ADR-0126). Aucune
règle « module » : les règles du catalogue lisent ces observations (T22, T23).
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.pdf import Document, Flux, Illisible, Nom, Objet, Ref, texte
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    Localisation,
    RaisonNonMenee,
    Scalaire,
)

__all__ = ["analyser"]

_NOMINATIVES = frozenset({"Author"})
"""Clés nominatives (ADR-0119)."""
_TEXTES_LIBRES = frozenset({"Title", "Subject", "Keywords"})
"""Titre, sujet, mots-clés (ADR-0160) ; ``Title`` porte souvent le nom du fichier source."""


def analyser(contexte: Contexte) -> None:
    try:
        document = Document(contexte)
    except Illisible as illisible:
        contexte.observer("infopdf.present", False)
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    designe = document.trailer.get("Info")
    chiffre = "Encrypt" in document.trailer
    if chiffre:
        contexte.observer("infopdf.present", designe is not None)
        contexte.observer("infopdf.chiffre", True)
        if designe is not None:
            localisation = Localisation(chemin="dictionnaire Info (document chiffré)")
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
        return
    try:
        info = document.resoudre(designe)
    except Illisible as illisible:
        contexte.observer("infopdf.present", True)
        contexte.observer("infopdf.chiffre", False)
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    contexte.observer("infopdf.present", info is not None)
    contexte.observer("infopdf.chiffre", False)
    if info is None:
        return
    if isinstance(designe, Ref):
        localisation = document.localisation(designe, "dictionnaire Info")
    else:
        localisation = Localisation(chemin="dictionnaire Info (dans le trailer)")
    if not isinstance(info, dict):
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
        return
    _entrees(contexte, document, info, "infopdf", localisation, (id(info),))


def _identifiante(cle: str) -> CategorieIdentifiante | None:
    if cle in _NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if cle in _TEXTES_LIBRES:
        return CategorieIdentifiante.TEXTE_LIBRE
    return None


def _entrees(
    contexte: Contexte,
    document: Document,
    dico: dict[str, Objet],
    prefixe: str,
    localisation: Localisation,
    parents: tuple[int, ...],
) -> None:
    """Entrées d'un dictionnaire ; un dictionnaire imbriqué donne ``<clé>.<sous-clé>``.

    ``parents`` tient les dictionnaires en cours de lecture : un dictionnaire qui se contient,
    par une référence, est non mené plutôt que relu jusqu'à la limite d'imbrication.
    """
    for cle, brute in dico.items():
        nom = valeurs.borner(f"{prefixe}.{valeurs.composant(cle)}")
        identifiante = _identifiante(cle)
        try:
            valeur = document.resoudre(brute)
            if isinstance(valeur, dict):
                if id(valeur) in parents:
                    contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
                    continue
                with contexte.imbrication():
                    suite = (*parents, id(valeur))
                    _entrees(contexte, document, valeur, nom, localisation, suite)
                continue
            if isinstance(valeur, Flux):
                valeurs.observer(
                    contexte,
                    f"{nom}.taille",
                    valeur.longueur,
                    unite="octets",
                    localisation=localisation,
                    identifiante=identifiante,
                )
                continue
            if isinstance(valeur, list):
                elements = [_scalaire(document.resoudre(element)) for element in valeur]
                if any(element is None for element in elements):
                    contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
                    continue
                forme: Scalaire | list[Scalaire] = [e for e in elements if e is not None]
            else:
                scalaire = _scalaire(valeur)
                if scalaire is None:
                    continue  # objet nul : l'entrée est absente (ISO 32000-2, §7.3.9)
                forme = scalaire
        except Illisible as illisible:
            contexte.non_mener(
                illisible.raison, localisation=illisible.localisation(contexte.taille)
            )
            continue
        valeurs.observer(contexte, nom, forme, localisation=localisation, identifiante=identifiante)


def _scalaire(objet: Objet) -> Scalaire | None:
    """Valeur d'une entrée : texte, nom, nombre ou booléen ; ``None`` pour tout autre objet."""
    if isinstance(objet, bytes):
        return texte(objet)
    if isinstance(objet, Nom):
        return str(objet)
    if isinstance(objet, bool | int):
        return objet
    if isinstance(objet, float):
        return valeurs.nombre(objet)
    return None
