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


def _resoudre(noeud: Any, base: str, documents: dict[str, Any], suivies: tuple[str, ...]) -> Any:
    """Copie d'un schéma où chaque ``$ref`` est remplacé par le schéma qu'il désigne.

    Une référence accompagnée d'autres mots-clés devient un ``allOf`` avec eux, ce qui ne
    change rien en 2020-12, où ``$ref`` s'applique à côté des mots-clés voisins.
    """
    if isinstance(noeud, list):
        return [_resoudre(element, base, documents, suivies) for element in noeud]
    if not isinstance(noeud, dict):
        return noeud
    voisins = {
        cle: _resoudre(valeur, base, documents, suivies)
        for cle, valeur in noeud.items()
        if cle not in ("$ref", "$defs", "$id", "$schema")
    }
    reference = noeud.get("$ref")
    if reference is None:
        return voisins
    if reference in suivies:
        raise ValueError(f"schéma récursif : {reference}")
    adresse, _, fragment = reference.partition("#")
    adresse = adresse or base
    cible = documents[adresse]
    for element in fragment.split("/")[1:]:
        cible = cible[element]
    resolue = _resoudre(cible, adresse, documents, (*suivies, reference))
    return {"allOf": [resolue], **voisins} if voisins else resolue


@cache
def _valideurs_rapides(nom: NomSchema) -> dict[str | None, Draft202012Validator]:
    """Valideurs du schéma ``nom`` aux références résolues une fois pour toutes (ADR-0121).

    La résolution d'une référence par ``referencing`` coûte plus que le contrôle qu'elle
    désigne, et un message en passe des dizaines. Pour les messages, un valideur par nature :
    chaque branche du ``oneOf`` fixe la sienne par ``type``, donc au plus une peut convenir,
    et valider celle que désigne ``type`` revient au ``oneOf`` sans parcourir les autres. La
    clé ``None`` donne le valideur du schéma entier.
    """
    documents = {schema["$id"]: schema for schema in map(charger, NOMS)}
    schema = charger(nom)
    valideurs: dict[str | None, Draft202012Validator] = {
        None: Draft202012Validator(_resoudre(schema, schema["$id"], documents, ()))
    }
    if nom == "messages":
        for nature, branche in schema["$defs"].items():
            resolue = _resoudre(branche, schema["$id"], documents, ())
            valideurs[nature] = Draft202012Validator(resolue)
    return valideurs


def _conforme(nom: NomSchema, document: object) -> bool:
    valideurs = _valideurs_rapides(nom)
    nature = document.get("type") if isinstance(document, dict) else None
    valideur_ = valideurs.get(nature if isinstance(nature, str) else None, valideurs[None])
    return valideur_.is_valid(document)


def valider(nom: NomSchema, document: object) -> None:
    """Lève :class:`DocumentInvalide` si ``document`` n'est pas conforme au schéma ``nom``.

    Le valideur aux références résolues reconnaît un document conforme ; pour un document
    qu'il refuse, le valideur du schéma tel qu'il est livré donne l'emplacement de la règle en
    cause (ADR-0121). Si les deux valideurs étaient en désaccord, le document serait refusé.
    """
    if _conforme(nom, document):
        return
    erreur = best_match(valideur(nom).iter_errors(document))
    emplacement = "références résolues"
    if erreur is not None:
        emplacement = "/".join(str(element) for element in erreur.absolute_schema_path)
    raise DocumentInvalide(f"document non conforme au schéma {nom} : {emplacement}")
