"""JSON Schema du rapport, des messages du processus de travail (T11, ADR-0054), des
manifestes des modules (T12, ADR-0064), du catalogue de règles et des techniques hors V1 (T15,
ADR-0087, ADR-0088).

Les schémas sont livrés dans le paquet et résolus entre eux sans accès réseau : le registre
ne connaît que ces fichiers et n'a aucune fonction de récupération.
"""

import json
from functools import cache
from importlib.resources import files
from typing import Any, Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

__all__ = ["NOMS", "DocumentInvalide", "charger", "valider", "valideur"]

type NomSchema = Literal["rapport", "messages", "manifeste", "catalogue", "regles", "hors_v1"]

NOMS: tuple[NomSchema, ...] = ("rapport", "messages", "manifeste", "catalogue", "regles", "hors_v1")


class DocumentInvalide(ValueError):
    """Document non conforme à son schéma.

    Le message ne cite que l'emplacement de la règle dans le schéma, jamais la valeur reçue,
    qui peut venir d'un fichier hostile (ES-04, ES-15).
    """


def charger(nom: NomSchema) -> dict[str, Any]:
    """Lit un schéma livré avec l'outil."""
    texte = (files(__package__) / f"{nom}.schema.json").read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(texte)
    return schema


@cache
def _registre() -> Registry[Any]:
    schemas = [charger(nom) for nom in NOMS]
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )


@cache
def valideur(nom: NomSchema) -> Draft202012Validator:
    """Valideur du schéma ``nom``, vérifié contre le métaschéma au premier appel."""
    schema = charger(nom)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=_registre())


def valider(nom: NomSchema, document: object) -> None:
    """Lève :class:`DocumentInvalide` si ``document`` n'est pas conforme au schéma ``nom``."""
    erreur = best_match(valideur(nom).iter_errors(document))
    if erreur is not None:
        emplacement = "/".join(str(element) for element in erreur.absolute_schema_path)
        raise DocumentInvalide(f"document non conforme au schéma {nom} : {emplacement}")
