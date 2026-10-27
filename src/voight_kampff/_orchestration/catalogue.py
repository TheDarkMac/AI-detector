"""Catalogue de règles : lecture, validation, empreinte (ADR-0029, ADR-0038, ADR-0085 à ADR-0088).

Le catalogue est un dossier de fichiers TOML, séparé du moteur (F-26) :

    catalogue.toml          en-tête : format, version, date, description
    regles/<module>.toml    règles d'un module, une table ``[[regle]]`` chacune

Le catalogue livré est dans le paquet (``donnees/catalogue``). L'utilisateur peut en fournir un
autre, qui le remplace en entier et que le rapport signale (ADR-0086). Dans les deux cas, le
processus principal lit chaque fichier une fois, calcule l'empreinte, valide chaque fichier par
son schéma, construit les règles, ce qui compile leurs motifs par RE2 (ADR-0039), et vérifie leur
cohérence avec les manifestes des modules (ADR-0064). Un catalogue invalide arrête tout avant la
lecture d'un fichier à analyser, avec un message explicite (ADR-0029).

Empreinte (ADR-0088) : SHA-256 de la liste ``<sha256 du fichier>  <chemin relatif>``, une ligne
par fichier, triée par chemin : la sortie de ``sha256sum`` sur les fichiers triés.
"""

import hashlib
import os
import re
import tomllib
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

from voight_kampff import schemas
from voight_kampff._limites import FICHIERS_MAX_CATALOGUE, REGLES_MAX, TAILLE_MAX_CATALOGUE
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff._regles import Application, Regle
from voight_kampff.rapport.modele import VersionCatalogue

__all__ = [
    "ENTETE",
    "REGLES",
    "Catalogue",
    "CatalogueInvalide",
    "charger",
    "empreinte",
    "livre",
]

ENTETE = "catalogue.toml"
REGLES = "regles"
_SUFFIXE = ".toml"
_MODULE = re.compile(r"[a-z][a-z0-9]{0,31}")


class CatalogueInvalide(ValueError):
    """Catalogue illisible, non conforme à son schéma ou incohérent avec les modules livrés."""


@dataclass(frozen=True, slots=True)
class Catalogue:
    """Catalogue validé : ce que le rapport en dit, et les règles qu'il porte."""

    version: VersionCatalogue
    description: str
    regles: tuple[Regle, ...]
    """Triées par identifiant : l'ordre d'évaluation ne dépend pas du découpage en fichiers."""

    def du_module(self, module: str) -> tuple[Regle, ...]:
        return tuple(regle for regle in self.regles if regle.module == module)

    def configuration(self, modules: Collection[str]) -> list[dict[str, Any]]:
        """Règles des modules actifs, sous la forme envoyée au processus de travail."""
        return [regle.vers_dict() for regle in self.regles if regle.module in modules]


def livre() -> Traversable:
    """Dossier du catalogue livré dans le paquet."""
    return files("voight_kampff") / "donnees" / "catalogue"


def empreinte(contenus: Iterable[tuple[str, bytes]]) -> str:
    """Empreinte d'un catalogue à partir du chemin relatif et du contenu de chaque fichier."""
    liste = "".join(
        f"{hashlib.sha256(contenu).hexdigest()}  {chemin}\n" for chemin, contenu in sorted(contenus)
    )
    return hashlib.sha256(liste.encode("utf-8")).hexdigest()


def charger(
    manifestes: Sequence[Manifeste], dossier: str | os.PathLike[str] | Traversable | None = None
) -> Catalogue:
    """Lit et valide le catalogue livré, ou celui du dossier ``dossier`` fourni par l'utilisateur.

    ``manifestes`` sont ceux des modules livrés, désactivés compris : les règles d'un module
    désactivé restent vérifiées.
    """
    if dossier is None:
        racine: Traversable = livre()
    elif isinstance(dossier, str | os.PathLike):
        racine = Path(dossier)
    else:
        racine = dossier
    contenus = _lire(racine)
    entete = _entete(contenus[ENTETE])
    regles = sorted(
        (
            regle
            for chemin, contenu in contenus.items()
            if chemin != ENTETE
            for regle in _regles(chemin, contenu)
        ),
        key=lambda regle: regle.identifiant,
    )
    identifiants = [regle.identifiant for regle in regles]
    if len(identifiants) > REGLES_MAX:
        raise CatalogueInvalide(f"catalogue : plus de {REGLES_MAX} règles")
    doubles = sorted({i for i in identifiants if identifiants.count(i) > 1})
    if doubles:
        raise CatalogueInvalide(f"catalogue : règle définie deux fois : {doubles[0]}")
    _verifier_modules(regles, manifestes)
    version = VersionCatalogue(
        version=entete["version"],
        date=entete["date"],
        empreinte=empreinte(contenus.items()),
        fourni_par_utilisateur=dossier is not None,
    )
    return Catalogue(version, entete["description"], tuple(regles))


# Lecture


def _lire(racine: Traversable) -> dict[str, bytes]:
    """Contenu de chaque fichier, par chemin relatif ; refuse tout fichier inattendu."""
    if not racine.is_dir():
        raise CatalogueInvalide("catalogue : dossier introuvable")
    trouves: list[tuple[str, Traversable]] = []
    for element in racine.iterdir():
        if element.name == ENTETE and element.is_file():
            trouves.append((ENTETE, element))
        elif element.name == REGLES and element.is_dir():
            for fichier in element.iterdir():
                module = fichier.name.removesuffix(_SUFFIXE)
                if not (
                    fichier.is_file()
                    and fichier.name.endswith(_SUFFIXE)
                    and _MODULE.fullmatch(module)
                ):
                    raise CatalogueInvalide(
                        f"catalogue : fichier inattendu : {REGLES}/{fichier.name!r}"
                    )
                trouves.append((f"{REGLES}/{fichier.name}", fichier))
        else:
            raise CatalogueInvalide(f"catalogue : fichier inattendu : {element.name!r}")
        if len(trouves) > FICHIERS_MAX_CATALOGUE:
            raise CatalogueInvalide(f"catalogue : plus de {FICHIERS_MAX_CATALOGUE} fichiers")
    if not any(chemin == ENTETE for chemin, _ in trouves):
        raise CatalogueInvalide(f"catalogue : en-tête {ENTETE} absent")
    contenus: dict[str, bytes] = {}
    total = 0
    for chemin, fichier in sorted(trouves, key=lambda trouve: trouve[0]):
        # Taille annoncée d'abord, quand le système la donne, pour ne pas lire un fichier énorme.
        if isinstance(fichier, Path) and total + fichier.stat().st_size > TAILLE_MAX_CATALOGUE:
            raise CatalogueInvalide(f"catalogue : plus de {TAILLE_MAX_CATALOGUE >> 20} Mio")
        contenu = fichier.read_bytes()
        total += len(contenu)
        if total > TAILLE_MAX_CATALOGUE:
            raise CatalogueInvalide(f"catalogue : plus de {TAILLE_MAX_CATALOGUE >> 20} Mio")
        contenus[chemin] = contenu
    return contenus


def _document(chemin: str, contenu: bytes, schema: schemas.NomSchema) -> dict[str, Any]:
    try:
        document = tomllib.loads(contenu.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise CatalogueInvalide(f"{chemin} : TOML illisible") from None
    try:
        schemas.valider(schema, document)
    except schemas.DocumentInvalide as erreur:
        raise CatalogueInvalide(f"{chemin} : {erreur}") from None
    return document


def _entete(contenu: bytes) -> dict[str, Any]:
    entete = _document(ENTETE, contenu, "catalogue")
    try:
        entete["date"] = date.fromisoformat(entete["date"])
    except ValueError:
        raise CatalogueInvalide(f"{ENTETE} : date inexistante") from None
    return entete


def _regles(chemin: str, contenu: bytes) -> list[Regle]:
    module = chemin.removeprefix(f"{REGLES}/").removesuffix(_SUFFIXE)
    regles: list[Regle] = []
    for document in _document(chemin, contenu, "regles")["regle"]:
        identifiant = document["identifiant"]
        if document["module"] != module:
            raise CatalogueInvalide(f"{chemin} : règle {identifiant} d'un autre module")
        try:
            regles.append(Regle.depuis_dict(document))
        except ValueError as erreur:
            raise CatalogueInvalide(f"{chemin} : règle {identifiant} : {erreur}") from None
    return regles


# Cohérence avec les modules livrés (ADR-0064, ADR-0084)


def _verifier_modules(regles: Sequence[Regle], manifestes: Sequence[Manifeste]) -> None:
    """Chaque règle a son module ; chaque manifeste cite exactement ses règles « module ».

    Les règles du moteur ne sont pas citées par les manifestes : en ajouter une ne demande
    aucun changement de l'outil (F-26).
    """
    par_module = {manifeste.identifiant: manifeste for manifeste in manifestes}
    par_identifiant = {regle.identifiant: regle for regle in regles}
    for regle in regles:
        manifeste = par_module.get(regle.module)
        if manifeste is None:
            raise CatalogueInvalide(
                f"règle {regle.identifiant} : module {regle.module} absent de cette version"
            )
        if regle.direction not in manifeste.directions:
            raise CatalogueInvalide(
                f"règle {regle.identifiant} : direction non permise par le manifeste du module"
            )
    for manifeste in manifestes:
        for identifiant in manifeste.regles:
            citee = par_identifiant.get(identifiant)
            if citee is None or citee.module != manifeste.identifiant:
                raise CatalogueInvalide(
                    f"module {manifeste.identifiant} : règle {identifiant} absente du catalogue"
                )
            if citee.application is not Application.MODULE:
                raise CatalogueInvalide(
                    f"module {manifeste.identifiant} : règle {identifiant} appliquée par le moteur"
                )
    for regle in regles:
        if (
            regle.application is Application.MODULE
            and regle.identifiant not in par_module[regle.module].regles
        ):
            raise CatalogueInvalide(
                f"règle {regle.identifiant} : appliquée par le module, absente de son manifeste"
            )
