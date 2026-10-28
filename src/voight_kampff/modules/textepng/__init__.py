"""Module ``textepng`` : blocs texte d'un PNG (F-10, ADR-0114 ; fiche ``metadonnees-texte-png``).

Lit chaque bloc ``tEXt``, ``zTXt`` et ``iTXt``, décompressé au besoin par le contexte (budget
de décompression, ADR-0078), et observe son texte sous ``textepng.<mot-clé>`` (ADR-0117) ; la
langue d'un ``iTXt``, si elle est déclarée, sous ``textepng.<mot-clé>.langue``. Le bloc
``iTXt`` ``XML:com.adobe.xmp`` est lu par le module ``xmp``. Observe aussi ``textepng.present``
dans tous les cas (F-14).

Aucune règle : les paramètres de génération qu'un bloc texte peut porter sont l'affaire de T22.
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Nature, relever, texte_png
from voight_kampff.rapport.modele import CategorieIdentifiante, RaisonNonMenee

__all__ = ["analyser"]

_NOMINATIFS = frozenset({"author", "copyright"})
"""Mots-clés prédéfinis par la norme PNG qui nomment une personne (ADR-0119)."""


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [bloc for bloc in releve.blocs if bloc.nature is Nature.TEXTE_PNG]
    contexte.observer("textepng.present", bool(blocs))
    if blocs:
        contexte.observer("textepng.blocs", len(blocs))
    for bloc in blocs:
        texte = texte_png(contexte, bloc)
        localisation = bloc.localisation()
        if texte.texte is None:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
            continue
        nom = valeurs.borner(f"textepng.{valeurs.composant(texte.mot_cle)}")
        identifiante = (
            CategorieIdentifiante.METADONNEE_NOMINATIVE
            if texte.mot_cle.lower() in _NOMINATIFS
            else None
        )
        valeurs.observer(
            contexte, nom, texte.texte, localisation=localisation, identifiante=identifiante
        )
        if texte.langue:
            valeurs.observer(
                contexte, f"{nom}.langue", texte.langue[:64], localisation=localisation
            )
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())
