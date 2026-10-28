"""Règles et catalogues de test, partagés entre fichiers de tests (T15).

``CATALOGUE`` porte les règles des modules factices de ``travail_factice.py`` : ``alpha``
constate par la règle « module » R-TEST-001, et le moteur lui applique la règle R-TEST-003.
"""

from datetime import date
from pathlib import Path
from typing import Any

from voight_kampff._orchestration.catalogue import Catalogue
from voight_kampff._regles import Regle
from voight_kampff.rapport.modele import VersionCatalogue

VERSION = VersionCatalogue("0.0.1", date(2026, 10, 27), "c" * 64, fourni_par_utilisateur=False)


def regle_dict(
    identifiant: str = "R-TEST-001", module: str = "alpha", **champs: Any
) -> dict[str, Any]:
    """Règle « module » d'information neutre, sous la forme du catalogue ; ``champs`` la modifie.

    Un champ qui vaut ``None`` est retiré. Sans ``phrase``, la phrase cite chaque paramètre
    déclaré, par la règle ou par ses conditions (ADR-0091).
    """
    document: dict[str, Any] = {
        "identifiant": identifiant,
        "version": "1",
        "module": module,
        "titre": "Règle de test",
        "description": "Règle employée par les tests.",
        "gabarit": "test.regle",
        "categorie": "information_neutre",
        "direction": "rien_de_particulier",
        "fondement": "mesure",
        "limites": ["Aucune : règle de test."],
        "application": "module",
    } | champs
    if "phrase" not in champs:
        noms = champs.get("parametres", []) + [
            c["parametre"] for c in champs.get("condition", []) if "parametre" in c
        ]
        document["phrase"] = {"fr": " ".join(["Phrase de test", *(f"{{{n}}}" for n in noms)])}
    return {cle: valeur for cle, valeur in document.items() if valeur is not None}


def regle(identifiant: str = "R-TEST-001", module: str = "alpha", **champs: Any) -> Regle:
    return Regle.depuis_dict(regle_dict(identifiant, module, **champs))


def moteur(*conditions: dict[str, Any], **champs: Any) -> dict[str, Any]:
    """Champs d'une règle du moteur, à passer à :func:`regle` ou :func:`regle_dict`."""
    return {"application": "moteur", "condition": list(conditions)} | champs


REGLES = (
    regle("R-TEST-001", gabarit="test.taille", parametres=["taille"]),
    regle("R-TEST-002", gabarit="g"),
    regle(
        "R-TEST-003",
        **moteur({"observation": "debut", "egal": "VKFT", "parametre": "debut"}),
        gabarit="test.debut",
    ),
)

CATALOGUE = Catalogue(VERSION, "Catalogue de test.", REGLES)


def chaine(valeur: Any) -> str:
    """Valeur TOML d'un texte, d'un nombre, d'un booléen ou d'une liste."""
    if isinstance(valeur, bool):
        return "true" if valeur else "false"
    if isinstance(valeur, str):
        return '"' + valeur.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(valeur, list):
        return "[" + ", ".join(map(chaine, valeur)) + "]"
    if isinstance(valeur, dict):
        return "{ " + ", ".join(f"{cle} = {chaine(v)}" for cle, v in valeur.items()) + " }"
    return repr(valeur)


def toml_regles(*regles: dict[str, Any]) -> str:
    """Fichier ``regles/<module>.toml`` : une table ``[[regle]]`` par règle."""
    blocs = []
    for document in regles:
        lignes = ["[[regle]]"]
        lignes += [f"{cle} = {chaine(v)}" for cle, v in document.items() if cle != "condition"]
        for condition in document.get("condition", ()):
            lignes.append("[[regle.condition]]")
            lignes += [f"{cle} = {chaine(v)}" for cle, v in condition.items()]
        blocs.append("\n".join(lignes))
    return "\n\n".join(blocs) + "\n"


ENTETE = 'format = 1\nversion = "1.2.3"\ndate = "2026-10-20"\ndescription = "Catalogue de test."\n'


def ecrire_catalogue(
    dossier: Path, regles: dict[str, str] | None = None, entete: str = ENTETE
) -> Path:
    """Écrit un catalogue : en-tête, puis ``regles/<module>.toml`` pour chaque module donné."""
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "catalogue.toml").write_bytes(entete.encode())
    if regles:
        (dossier / "regles").mkdir(exist_ok=True)
        for module, contenu in regles.items():
            (dossier / "regles" / f"{module}.toml").write_bytes(contenu.encode())
    return dossier
