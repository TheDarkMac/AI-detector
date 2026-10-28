"""Exports du rapport : JSON et HTML autonome, masqués par défaut (F-83, ES-12, ES-13).

Le rapport d'une :class:`~voight_kampff.analyse.Analyse` s'exporte en JSON, conforme au schéma
publié ``rapport`` (ADR-0025, ADR-0095), ou en HTML autonome, sans script ni ressource externe
(ADR-0094). Les cinq catégories de données identifiantes sont masquées, sauf celles que
``reveler`` nomme ; la levée est annoncée en tête de l'export (ES-13, ADR-0093). Une donnée
masquée n'est pas cachée dans le fichier produit : elle en est absente.

Ce module n'importe ni ``jsonschema`` ni le processus principal : le processus de travail, qui
importe le paquet, n'en charge rien.
"""

import json
from collections.abc import Collection, Mapping
from typing import Any

from voight_kampff.analyse import Analyse
from voight_kampff.rapport import _html
from voight_kampff.rapport._presentation import echapper_json
from voight_kampff.rapport.modele import CategorieIdentifiante, verifier_masquage

__all__ = ["exporter_html", "exporter_json", "masquees", "valider"]

type Categories = Collection[CategorieIdentifiante | str]


def masquees(reveler: Categories = ()) -> frozenset[CategorieIdentifiante]:
    """Catégories masquées : toutes, sauf celles nommées ; un nom inconnu lève ``ValueError``."""
    levees = {CategorieIdentifiante(categorie) for categorie in reveler}
    return frozenset(CategorieIdentifiante) - levees


def document(analyse: Analyse, reveler: Categories = ()) -> dict[str, Any]:
    """Document JSON du rapport, données masquées retirées, ``masquage`` en tête (ADR-0095)."""
    caches = masquees(reveler)
    rapport = analyse.rapport().vers_dict()
    identification = rapport["identification"]
    if CategorieIdentifiante.NOM_DE_FICHIER in caches:
        del identification["nom"]
    if CategorieIdentifiante.EMPREINTE in caches:
        del identification["empreinte"]
    for observation in rapport["observations"]:
        if observation.get("identifiante") in caches:
            del observation["valeur"]
    masquage = {
        "masquees": [c.value for c in CategorieIdentifiante if c in caches],
        "levees": [c.value for c in CategorieIdentifiante if c not in caches],
    }
    return {"version_schema": rapport.pop("version_schema"), "masquage": masquage} | rapport


def valider(document: Mapping[str, Any]) -> None:
    """Vérifie un export JSON : son schéma, puis ce que seul le code vérifie (ADR-0095).

    Le masquage nomme chaque catégorie une fois ; une observation n'a pas de valeur si et
    seulement si sa catégorie est masquée. Lève ``DocumentInvalide`` ou ``ValueError``.
    """
    from voight_kampff import schemas  # jsonschema : seulement dans le processus principal

    schemas.valider("rapport", document)
    caches = verifier_masquage(document["masquage"]) if "masquage" in document else frozenset()
    for observation in document["observations"]:
        masquee = observation.get("identifiante") in caches
        if masquee == ("valeur" in observation):
            raise ValueError("observations : valeur présente si et seulement si non masquée")


def exporter_json(analyse: Analyse, *, reveler: Categories = ()) -> str:
    """Rapport en JSON, vérifié avant d'être rendu ; caractères invisibles échappés (ES-12)."""
    contenu = document(analyse, reveler)
    valider(contenu)
    return echapper_json(json.dumps(contenu, ensure_ascii=False, indent=2)) + "\n"


def exporter_html(analyse: Analyse, *, reveler: Categories = ()) -> str:
    """Rapport en HTML autonome, accessible, sans script ni ressource externe (ADR-0094)."""
    return _html.html(analyse, masquees(reveler))
