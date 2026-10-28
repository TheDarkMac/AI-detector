"""Manifeste d'un corpus : lecture, validation, partition (ADR-0016, ADR-0103, ES-22).

Le manifeste ``corpus.toml`` décrit chaque fichier : chemin relatif, empreinte, catégorie du
§8 du cahier, partie (calibrage ou évaluation), groupe, origine réelle et provenance. Les
fichiers d'un même groupe dérivent d'un même original : ils sont tous dans la même partie, sinon
l'évaluation mesurerait ce qui a servi à régler (A-12).
"""

import hashlib
import json
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

__all__ = ["Categorie", "Corpus", "CorpusInvalide", "Entree", "Nature", "Origine", "Partie"]

TAILLE_MAX_MANIFESTE = 64 << 20
"""Un manifeste d'un million de fichiers tient dans quelques centaines de Mio : 64 Mio suffisent
largement au corpus de T100, et bornent la lecture."""

_BLOC = 1 << 20


class CorpusInvalide(ValueError):
    """Manifeste illisible ou non conforme, ou fichier du corpus absent ou modifié."""


class Categorie(StrEnum):
    """Catégories du corpus (§8 du cahier)."""

    AUTHENTIQUE = "authentique"
    GENERE = "genere"
    TRANSFORME = "transforme"
    RETOUCHE = "retouche"
    MALFORME = "malforme"


class Partie(StrEnum):
    """Partie du corpus (ADR-0016) : l'évaluation ne sert jamais à régler un seuil."""

    CALIBRAGE = "calibrage"
    EVALUATION = "evaluation"


class Origine(StrEnum):
    """Ce qu'est réellement un fichier : la vérité à laquelle les constats sont comparés."""

    AUTHENTIQUE = "authentique"
    IA = "ia"
    RETOUCHE = "retouche"


class Nature(StrEnum):
    """Corpus de démonstration du banc, ou corpus de référence de T100 (ADR-0105)."""

    ESSAI = "essai"
    REFERENCE = "reference"


@dataclass(frozen=True, slots=True)
class Entree:
    """Un fichier du corpus, tel que le manifeste le décrit."""

    chemin: str
    """Relatif au dossier du manifeste, segments séparés par « / »."""
    empreinte: str
    categorie: Categorie
    partie: Partie
    groupe: str
    origine: Origine | None
    """Absente seulement pour un fichier malformé sans original."""
    transformation: str | None = None


@dataclass(frozen=True, slots=True)
class Corpus:
    """Un corpus versionné, et le dossier où sont ses fichiers."""

    nom: str
    version: str
    date: date
    nature: Nature
    description: str
    empreinte: str
    """SHA-256 des octets du manifeste : identifie exactement le corpus évalué."""
    racine: Path
    entrees: tuple[Entree, ...]

    def partie(self, partie: Partie) -> tuple[Entree, ...]:
        """Entrées d'une partie, dans l'ordre du manifeste."""
        return tuple(entree for entree in self.entrees if entree.partie is partie)

    def chemin(self, entree: Entree) -> Path:
        return self.racine.joinpath(*entree.chemin.split("/"))

    def verifier(self, entree: Entree) -> Path:
        """Chemin du fichier, après avoir vérifié qu'il est dans le corpus et inchangé.

        Lève :class:`CorpusInvalide` si le fichier est absent, sort du dossier du corpus par un
        lien, ou si son empreinte diffère du manifeste : un taux mesuré sur d'autres octets que
        ceux de la version annoncée ne vaudrait rien (ES-22).
        """
        chemin = self.chemin(entree)
        try:
            reel = chemin.resolve(strict=True)
            if not reel.is_relative_to(self.racine.resolve(strict=True)):
                raise CorpusInvalide(f"{entree.chemin} : hors du dossier du corpus")
            empreinte = hashlib.sha256()
            with reel.open("rb") as fichier:
                while bloc := fichier.read(_BLOC):
                    empreinte.update(bloc)
        except OSError as erreur:
            raise CorpusInvalide(f"{entree.chemin} : illisible ({erreur.strerror})") from None
        if empreinte.hexdigest() != entree.empreinte:
            raise CorpusInvalide(f"{entree.chemin} : empreinte différente du manifeste")
        return chemin


@cache
def _valideur() -> Draft202012Validator:
    texte = (files(__package__) / "corpus.schema.json").read_text(encoding="utf-8")
    schema = json.loads(texte)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def charger(manifeste: str | Path) -> Corpus:
    """Lit et valide un manifeste ; lève :class:`CorpusInvalide` avec la raison."""
    chemin = Path(manifeste)
    try:
        with chemin.open("rb") as fichier:
            octets = fichier.read(TAILLE_MAX_MANIFESTE + 1)
    except OSError as erreur:
        raise CorpusInvalide(f"manifeste illisible ({erreur.strerror})") from None
    if len(octets) > TAILLE_MAX_MANIFESTE:
        raise CorpusInvalide("manifeste trop volumineux")
    try:
        document = tomllib.loads(octets.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as erreur:
        raise CorpusInvalide(f"manifeste illisible ({erreur})") from None
    erreur_schema = best_match(_valideur().iter_errors(document))
    if erreur_schema is not None:
        emplacement = "/".join(str(element) for element in erreur_schema.absolute_path)
        raise CorpusInvalide(f"manifeste non conforme : {emplacement or 'racine'}")
    try:
        jour = date.fromisoformat(document["date"])
    except ValueError:
        raise CorpusInvalide("manifeste non conforme : date") from None
    entrees = tuple(map(_entree, document["fichiers"]))
    _verifier_entrees(entrees)
    return Corpus(
        nom=document["nom"],
        version=document["version"],
        date=jour,
        nature=Nature(document["nature"]),
        description=document["description"],
        empreinte=hashlib.sha256(octets).hexdigest(),
        racine=chemin.parent,
        entrees=entrees,
    )


def _entree(document: dict[str, Any]) -> Entree:
    try:
        date.fromisoformat(document["provenance"]["date"])
    except ValueError:
        raise CorpusInvalide(f"{document['chemin']} : date de provenance invalide") from None
    origine = document.get("origine")
    return Entree(
        chemin=document["chemin"],
        empreinte=document["empreinte"],
        categorie=Categorie(document["categorie"]),
        partie=Partie(document["partie"]),
        groupe=document["groupe"],
        origine=None if origine is None else Origine(origine),
        transformation=document.get("transformation"),
    )


def _verifier_entrees(entrees: tuple[Entree, ...]) -> None:
    """Chemins et empreintes uniques ; chaque groupe dans une seule partie (A-12)."""
    chemins: set[str] = set()
    empreintes: set[str] = set()
    parties: defaultdict[str, set[Partie]] = defaultdict(set)
    for entree in entrees:
        # Comparaison sans la casse : deux chemins qui ne diffèrent que par elle désignent le
        # même fichier sous macOS et Windows.
        if entree.chemin.casefold() in chemins:
            raise CorpusInvalide(f"{entree.chemin} : chemin en double")
        if entree.empreinte in empreintes:
            raise CorpusInvalide(f"{entree.chemin} : même contenu qu'un autre fichier du corpus")
        chemins.add(entree.chemin.casefold())
        empreintes.add(entree.empreinte)
        parties[entree.groupe].add(entree.partie)
    for groupe, vues in parties.items():
        if len(vues) > 1:
            raise CorpusInvalide(f"groupe {groupe} : dans les deux parties du corpus")
