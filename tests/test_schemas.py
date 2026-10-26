"""Tests des JSON Schema : conformité, accord avec le modèle, aucun accès réseau (T11)."""

import copy
import json
from collections.abc import Callable
from enum import StrEnum
from typing import Any

import pytest
from referencing.exceptions import NoSuchResource

from voight_kampff import schemas
from voight_kampff.rapport import modele
from voight_kampff.rapport.modele import Rapport

type Document = dict[str, Any]


def document_de(rapport: Rapport) -> Document:
    """Document tel que le processus principal le reçoit : passé par du texte JSON."""
    resultat: Document = json.loads(json.dumps(rapport.vers_dict()))
    return resultat


def definitions() -> dict[str, Any]:
    resultat: dict[str, Any] = schemas.charger("rapport")["$defs"]
    return resultat


# Conformité


@pytest.mark.parametrize("nom", schemas.NOMS)
def test_schema_conforme_au_metaschema(nom: schemas.NomSchema) -> None:
    schemas.valideur(nom)  # vérifie le schéma contre le métaschéma Draft 2020-12


def test_rapport_complet_conforme(rapport: Rapport) -> None:
    schemas.valider("rapport", document_de(rapport))


def test_chaque_message_conforme(rapport: Rapport) -> None:
    document = document_de(rapport)
    messages = [
        {
            "type": "isolation",
            "version_schema": modele.VERSION_SCHEMA,
            "isolation": document["isolation"],
        },
        *({"type": "observation", "observation": o} for o in document["observations"]),
        *({"type": "constat", "constat": c} for c in document["constats"]),
        *({"type": "non_menee", "non_menee": n} for n in document["non_menees"]),
        {"type": "versions", "dependances": document["versions"]["dependances"]},
        {"type": "fin", "empreinte": document["identification"]["empreinte"]},
    ]
    for message in messages:
        schemas.valider("messages", message)


@pytest.mark.parametrize(
    "message",
    [
        pytest.param({"type": "inconnu"}, id="type-inconnu"),
        pytest.param({"type": "fin"}, id="champ-manquant"),
        pytest.param({"type": "fin", "empreinte": "0" * 64, "en_plus": 1}, id="champ-en-plus"),
        pytest.param(
            {"type": "isolation", "version_schema": "9.9.9", "isolation": {}},
            id="version-differente",
        ),
        pytest.param(["fin"], id="pas-un-objet"),
    ],
)
def test_message_invalide_refuse(message: object) -> None:
    with pytest.raises(schemas.DocumentInvalide):
        schemas.valider("messages", message)


# Accord entre les schémas et le modèle


@pytest.mark.parametrize(
    ("definition", "enumeration"),
    [
        ("categorie", modele.Categorie),
        ("direction", modele.Direction),
        ("niveau", modele.Niveau),
        ("fondement", modele.Fondement),
        ("categorie_identifiante", modele.CategorieIdentifiante),
        ("raison_non_menee", modele.RaisonNonMenee),
        ("etat_technique", modele.EtatTechnique),
        ("niveau_isolation", modele.NiveauIsolation),
        ("manque_isolation", modele.ManqueIsolation),
    ],
)
def test_enumerations_identiques(definition: str, enumeration: type[StrEnum]) -> None:
    assert definitions()[definition]["enum"] == [membre.value for membre in enumeration]


def test_raisons_propres_a_une_technique_identiques() -> None:
    condition = definitions()["non_menee"]["if"]["properties"]["raison"]["enum"]
    assert set(condition) == set(modele.RAISONS_PROPRES_A_UNE_TECHNIQUE)


def test_fondements_de_preuve_identiques() -> None:
    condition = definitions()["constat"]["allOf"][0]["then"]["properties"]["fondement"]["enum"]
    assert set(condition) == {
        modele.Fondement.VERIFICATION_CRYPTOGRAPHIQUE,
        modele.Fondement.VERIFICATION_DETERMINISTE,
    }


def test_version_identique() -> None:
    rapport = schemas.charger("rapport")
    messages = schemas.charger("messages")
    assert rapport["properties"]["version_schema"]["const"] == modele.VERSION_SCHEMA
    version_message = messages["$defs"]["isolation"]["properties"]["version_schema"]["const"]
    assert version_message == modele.VERSION_SCHEMA


def test_bornes_identiques() -> None:
    defs = definitions()
    assert defs["identifiant"]["maxLength"] == modele.LONGUEUR_MAX_IDENTIFIANT
    assert defs["version"]["maxLength"] == modele.LONGUEUR_MAX_VERSION
    assert defs["texte"]["maxLength"] == modele.LONGUEUR_MAX_TEXTE
    assert defs["observation"]["properties"]["unite"]["maxLength"] == modele.LONGUEUR_MAX_UNITE
    assert defs["valeur"]["anyOf"][1]["maxItems"] == modele.NOMBRE_MAX_ELEMENTS
    assert defs["constat"]["properties"]["donnees"]["maxItems"] == modele.NOMBRE_MAX_DONNEES
    assert defs["phrase"]["properties"]["parametres"]["maxProperties"] == (
        modele.NOMBRE_MAX_PARAMETRES
    )
    assert defs["nombre"]["minimum"] == -(2**63)
    assert defs["nombre"]["maximum"] == 2**63 - 1


def premier_constat(categorie: str) -> Callable[[Document], Document]:
    def trouver(document: Document) -> Document:
        constat: Document = next(c for c in document["constats"] if c["categorie"] == categorie)
        return constat

    return trouver


def modifier(chemin: Callable[[Document], Document], **valeurs: Any) -> Callable[[Document], None]:
    def appliquer(document: Document) -> None:
        cible = chemin(document)
        for cle, valeur in valeurs.items():
            if valeur is ...:
                del cible[cle]
            else:
                cible[cle] = valeur

    return appliquer


def racine(document: Document) -> Document:
    return document


def observation(rang: int) -> Callable[[Document], Document]:
    return lambda document: document["observations"][rang]


PREUVE = premier_constat("preuve")
INDICE = premier_constat("indice")
NEUTRE = premier_constat("information_neutre")
IDENTIFICATION: Callable[[Document], Document] = lambda d: d["identification"]  # noqa: E731
ISOLATION: Callable[[Document], Document] = lambda d: d["isolation"]  # noqa: E731

# Chaque altération doit être refusée à la fois par le schéma et par le modèle.
ALTERATIONS_REFUSEES_PARTOUT: list[Any] = [
    pytest.param(modifier(racine, constats=...), id="champ-manquant"),
    pytest.param(modifier(racine, version_schema="9.9.9"), id="version-de-schema"),
    pytest.param(modifier(PREUVE, fondement="declaration"), id="preuve-sur-declaration"),
    pytest.param(modifier(PREUVE, fondement="mesure"), id="preuve-sur-mesure"),
    pytest.param(
        modifier(PREUVE, graduation={"niveau": "fort", "evaluee": True}), id="preuve-avec-niveau"
    ),
    pytest.param(modifier(INDICE, graduation=...), id="indice-sans-niveau"),
    pytest.param(modifier(INDICE, direction="rien_de_particulier"), id="indice-sans-direction"),
    pytest.param(modifier(NEUTRE, direction="origine_ia"), id="neutre-avec-direction"),
    pytest.param(
        modifier(NEUTRE, graduation={"niveau": "faible", "evaluee": False}),
        id="neutre-avec-niveau",
    ),
    pytest.param(
        modifier(INDICE, graduation={"niveau": "fort", "evaluee": False}),
        id="non-evaluee-au-niveau-fort",
    ),
    pytest.param(modifier(INDICE, direction="inconnue"), id="direction-inconnue"),
    pytest.param(modifier(INDICE, donnees=[]), id="sans-donnee"),
    pytest.param(
        modifier(INDICE, donnees=["metadonnees/1", "metadonnees/1"]), id="donnee-en-double"
    ),
    pytest.param(modifier(observation(0), identifiant="o1\n"), id="identifiant-fin-de-ligne"),
    pytest.param(modifier(observation(0), identifiant="x" * 129), id="identifiant-trop-long"),
    pytest.param(modifier(observation(0), identifiant="a b"), id="identifiant-espace"),
    pytest.param(modifier(observation(0), valeur=2**63), id="entier-trop-grand"),
    pytest.param(modifier(observation(0), valeur=1e19), id="reel-trop-grand"),
    pytest.param(modifier(observation(0), valeur="x" * 4097), id="texte-trop-long"),
    pytest.param(modifier(observation(0), valeur=[[1]]), id="liste-imbriquee"),
    pytest.param(modifier(observation(0), valeur=list(range(4097))), id="liste-trop-longue"),
    pytest.param(modifier(observation(0), valeur=None), id="valeur-nulle"),
    pytest.param(modifier(observation(0), unite=""), id="unite-vide"),
    pytest.param(modifier(observation(0), identifiante="adresse"), id="categorie-inconnue"),
    pytest.param(modifier(observation(0), localisation={}), id="localisation-vide"),
    pytest.param(modifier(observation(0), localisation={"page": 0}), id="page-zero"),
    pytest.param(
        modifier(observation(0), localisation={"octets": {"debut": 0, "longueur": 0}}),
        id="plage-vide",
    ),
    pytest.param(modifier(IDENTIFICATION, nom="/home/source/a.jpg"), id="nom-avec-chemin"),
    pytest.param(modifier(IDENTIFICATION, nom="C:\\source\\a.jpg"), id="nom-avec-chemin-windows"),
    pytest.param(modifier(IDENTIFICATION, empreinte="3F" * 32), id="empreinte-majuscules"),
    pytest.param(modifier(IDENTIFICATION, empreinte="3f" * 32 + "\n"), id="empreinte-fin-ligne"),
    pytest.param(modifier(IDENTIFICATION, taille=-1), id="taille-negative"),
    pytest.param(
        modifier(IDENTIFICATION, date_analyse="2026-10-26T14:03:00+02:00"), id="date-hors-utc"
    ),
    pytest.param(
        modifier(IDENTIFICATION, date_analyse="2026-10-26T14:03:00.5Z"), id="date-fraction"
    ),
    pytest.param(modifier(ISOLATION, niveau="complete"), id="complete-avec-manques"),
    pytest.param(modifier(ISOLATION, manques=[]), id="reduite-sans-manque"),
    pytest.param(
        modifier(lambda d: d["non_menees"][1], module=...), id="raison-propre-sans-module"
    ),
    pytest.param(
        modifier(lambda d: d["couverture"]["techniques"][0], version=...),
        id="technique-appliquee-sans-version",
    ),
    pytest.param(
        modifier(lambda d: d["couverture"], marquages_recherches=["c2pa", "c2pa"]),
        id="marquage-en-double",
    ),
    pytest.param(
        modifier(lambda d: d["versions"]["catalogue"], date="26/10/2026"), id="date-catalogue"
    ),
]


@pytest.mark.parametrize("alterer", ALTERATIONS_REFUSEES_PARTOUT)
def test_alteration_refusee_par_le_schema_et_le_modele(
    rapport: Rapport, alterer: Callable[[Document], None]
) -> None:
    document = copy.deepcopy(document_de(rapport))
    alterer(document)
    with pytest.raises(schemas.DocumentInvalide):
        schemas.valider("rapport", document)
    with pytest.raises((ValueError, TypeError, KeyError)):
        Rapport.depuis_dict(document)


def test_champ_inconnu_refuse_par_le_schema_seul(rapport: Rapport) -> None:
    # Le modèle lit un document déjà validé : il ignore ce que le schéma a déjà refusé.
    document = document_de(rapport) | {"en_plus": 1}
    with pytest.raises(schemas.DocumentInvalide):
        schemas.valider("rapport", document)
    assert Rapport.depuis_dict(document) == rapport


# Renvois entre objets et contraintes de valeur que JSON Schema n'exprime pas : seul le modèle
# les vérifie. Le processus principal applique donc toujours les deux (modele-de-donnees.md §7).
ALTERATIONS_REFUSEES_PAR_LE_MODELE_SEUL: list[Any] = [
    pytest.param(
        modifier(INDICE, phrase={"gabarit": "g", "parametres": {"p": "c2pa/1"}}),
        id="parametre-hors-donnees",
    ),
    pytest.param(modifier(INDICE, donnees=["absente/1"]), id="observation-absente"),
    pytest.param(
        lambda d: d["observations"].append(copy.deepcopy(d["observations"][0])),
        id="observation-en-double",
    ),
    pytest.param(
        lambda d: d["couverture"]["techniques"].append(
            copy.deepcopy(d["couverture"]["techniques"][0])
        ),
        id="technique-en-double",
    ),
    pytest.param(modifier(observation(0), module="inconnu"), id="technique-hors-couverture"),
    pytest.param(
        modifier(observation(0), localisation={"intervalle": {"debut": 2, "fin": 1}}),
        id="intervalle-inverse",
    ),
    pytest.param(modifier(observation(0), valeur="\ud800"), id="substitut-isole"),
    pytest.param(modifier(racine, interrompue=True), id="interrompue-incoherente"),
    pytest.param(modifier(IDENTIFICATION, date_analyse="2026-02-30T14:03:00Z"), id="date-du-30"),
]


@pytest.mark.parametrize("alterer", ALTERATIONS_REFUSEES_PAR_LE_MODELE_SEUL)
def test_alteration_refusee_par_le_modele_seul(
    rapport: Rapport, alterer: Callable[[Document], None]
) -> None:
    document = copy.deepcopy(document_de(rapport))
    alterer(document)
    schemas.valider("rapport", document)
    with pytest.raises(ValueError, match=r"."):
        Rapport.depuis_dict(document)


# Sécurité (ES-04, ES-15, NF-16)


def test_erreur_sans_la_valeur_recue(rapport: Rapport) -> None:
    document = document_de(rapport)
    document["identification"]["nom"] = "/home/source-CONFIDENTIELLE/photo.jpg"
    document["CLE_HOSTILE"] = "VALEUR_HOSTILE"
    with pytest.raises(schemas.DocumentInvalide) as erreur:
        schemas.valider("rapport", document)
    message = str(erreur.value)
    for fragment in ("CONFIDENTIELLE", "CLE_HOSTILE", "VALEUR_HOSTILE"):
        assert fragment not in message


def test_registre_sans_recuperation_reseau() -> None:
    # Un renvoi vers une ressource inconnue échoue au lieu de la télécharger.
    with pytest.raises(NoSuchResource):
        schemas._registre().get_or_retrieve("https://example.com/schema.json")


@pytest.mark.parametrize("nom", schemas.NOMS)
def test_renvois_internes_seulement(nom: schemas.NomSchema) -> None:
    texte = json.dumps(schemas.charger(nom))
    renvois = {
        valeur
        for cle, valeur in _paires(schemas.charger(nom))
        if cle == "$ref" and isinstance(valeur, str)
    }
    assert renvois
    assert all(r.startswith(("#", "urn:voight-kampff:schema:")) for r in renvois)
    assert "http://" not in texte.replace("http://json-schema.org", "")


def _paires(objet: object) -> list[tuple[str, object]]:
    if isinstance(objet, dict):
        return [p for cle, valeur in objet.items() for p in [(cle, valeur), *_paires(valeur)]]
    if isinstance(objet, list):
        return [p for element in objet for p in _paires(element)]
    return []
