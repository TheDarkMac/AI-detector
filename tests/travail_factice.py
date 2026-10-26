"""Processus de travail factice pour les tests du processus principal (T12).

Lancé par ``python -I -B tests/travail_factice.py <scenario> --descripteur N``. Le scénario
``modules`` exécute le vrai déroulé du processus de travail avec les analyseurs ci-dessous ;
les autres écrivent des lignes choisies, pour vérifier que le processus principal refuse un
processus de travail défaillant ou compromis (ES-04, M-10).
"""

import json
import os
import sys
import time
from collections.abc import Callable
from typing import Any, BinaryIO

from voight_kampff._travail.contexte import Contexte
from voight_kampff._travail.principal import canal_du_protocole, principal
from voight_kampff.rapport.modele import (
    Categorie,
    Direction,
    Fondement,
    Phrase,
    RaisonNonMenee,
    ReferenceRegle,
)

FORMAT = "test"
"""Format que l'identification factice attribue à tout fichier."""

# Analyseurs du scénario « modules »


def alpha(contexte: Contexte) -> None:
    print("texte affiché par un module")  # doit partir sur la sortie d'erreur
    debut = contexte.observer("debut", contexte.lire(0, 4).decode("ascii"))
    taille = contexte.observer("taille", contexte.taille, unite="o")
    contexte.constater(
        Phrase("test.taille", {"taille": taille}),
        (debut, taille),
        ReferenceRegle("R-TEST-001", "1"),
        fondement=Fondement.MESURE,
        categorie=Categorie.INFORMATION_NEUTRE,
        direction=Direction.RIEN_DE_PARTICULIER,
    )


def beta(contexte: Contexte) -> None:
    contexte.observer("avant.erreur", True)
    raise RuntimeError("défaut du module")


def gamma(contexte: Contexte) -> None:
    contexte.observer("jamais", 1)  # format non traité : jamais appelé


def delta(contexte: Contexte) -> None:
    contexte.observer("lu", contexte.lire(0, 2).decode("ascii"))
    contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL)


def epsilon(_contexte: Contexte) -> None:
    sys.exit(3)


def zeta(_contexte: Contexte) -> None:
    time.sleep(60)


def eta(_contexte: Contexte) -> None:
    os._exit(0)


ANALYSEURS = {f.__name__: f for f in (alpha, beta, gamma, delta, epsilon, zeta, eta)}


# Lignes choisies

ISOLATION = {
    "type": "isolation",
    "version_schema": "0.1.0",
    "isolation": {"niveau": "reduite", "manques": ["reseau"]},
}
VERSIONS = {"type": "versions", "dependances": []}
FIN = {"type": "fin", "empreinte": "0" * 64}


def observation(identifiant: str, module: str = "alpha", **autres: Any) -> dict[str, Any]:
    return {
        "type": "observation",
        "observation": {"identifiant": identifiant, "module": module, "nom": "n", "valeur": 1}
        | autres,
    }


def constat(donnee: str, direction: str = "rien_de_particulier") -> dict[str, Any]:
    return {
        "type": "constat",
        "constat": {
            "phrase": {"gabarit": "g", "parametres": {}},
            "donnees": [donnee],
            "regle": {"identifiant": "R-1", "version": "1"},
            "module": "alpha",
            "fondement": "mesure",
            "categorie": "information_neutre" if direction == "rien_de_particulier" else "indice",
            "direction": direction,
        }
        | (
            {}
            if direction == "rien_de_particulier"
            else {"graduation": {"niveau": "faible", "evaluee": False}}
        ),
    }


def non_menee(raison: str, module: str | None = "alpha") -> dict[str, Any]:
    contenu: dict[str, Any] = {"raison": raison}
    if module is not None:
        contenu["module"] = module
    return {"type": "non_menee", "non_menee": contenu}


def module(identifiant: str = "alpha", applicable: bool = True) -> dict[str, Any]:
    return {"type": "module", "module": identifiant, "applicable": applicable}


type Ligne = dict[str, Any] | bytes

# Les tests configurent deux modules actifs, alpha puis beta : une suite complète les termine.
FINS = [module("alpha"), module("beta", applicable=False), VERSIONS, FIN]

HOSTILES: dict[str, list[Ligne]] = {
    "valide": [
        observation("alpha/1"),
        constat("alpha/1"),
        non_menee("fichier_tronque", module=None),
        *FINS,
    ],
    "sans_isolation": [],  # traité à part : rien n'est envoyé avant l'observation
    "json_invalide": [b"{pas du json\n"],
    "nan": [b'{"type":"fin","empreinte":NaN}\n'],
    "infini": [
        b'{"type":"observation","observation":{"identifiant":"alpha/1","module":"alpha",'
        b'"nom":"n","valeur":1e400}}\n'
    ],
    "cle_double": [b'{"type":"versions","dependances":[],"dependances":[]}\n'],
    "utf8_invalide": [b'{"type":"versions","dependances":["\xff"]}\n'],
    "pas_un_objet": [b"[1]\n"],
    "schema": [{"type": "fin"}],
    "isolation_double": [ISOLATION],
    "module_inconnu": [observation("intrus/1", module="intrus")],
    "identifiant_sans_prefixe": [observation("autre/1")],
    "identifiant_double": [observation("alpha/1"), observation("alpha/1")],
    "modele": [observation("alpha/1", localisation={"intervalle": {"debut": 2, "fin": 1}})],
    "constat_sans_donnee": [observation("alpha/1"), constat("alpha/9")],
    "direction_interdite": [observation("alpha/1"), constat("alpha/1", "origine_ia")],
    "raison_reservee": [non_menee("module_desactive")],
    "raison_reservee_fichier": [non_menee("arret_processus", module=None)],
    "erreur_apres_resultats": [observation("alpha/1"), non_menee("erreur_module")],
    "resultat_apres_erreur": [non_menee("erreur_module"), observation("alpha/1")],
    "ordre_des_modules": [module("beta")],
    "module_en_trop": [*FINS[:2], module("gamma")],
    "non_applicable_avec_resultat": [observation("alpha/1"), module("alpha", applicable=False)],
    "fin_trop_tot": [FIN],
    "fin_sans_versions": [*FINS[:2], FIN],
    "versions_double": [VERSIONS, *FINS],
    "dependance_double": [
        {"type": "versions", "dependances": [{"nom": "x", "version": "1"}] * 2},
    ],
    "ligne_apres_fin": [*FINS, VERSIONS],
    "ligne_trop_longue": [b" " * (1 << 20) + b"\n"],
}


def ligne(element: Ligne) -> bytes:
    return element if isinstance(element, bytes) else (json.dumps(element) + "\n").encode()


def hostile(nom: str, entree: BinaryIO, sortie: BinaryIO) -> int:
    if nom == "sans_isolation":
        sortie.write(ligne(observation("alpha/1")))
        return 0
    sortie.write(ligne(ISOLATION))
    sortie.flush()
    entree.readline()
    for element in HOSTILES[nom]:
        sortie.write(ligne(element))
    sortie.flush()
    return 0


def special(nom: str, entree: BinaryIO, sortie: BinaryIO) -> int:
    """Scénarios qui ne se réduisent pas à une liste de lignes."""
    if nom == "rien":
        return 0
    sortie.write(ligne(ISOLATION))
    sortie.flush()
    entree.readline()
    match nom:
        case "silence":
            time.sleep(60)
        case "code_non_nul":
            for element in [observation("alpha/1"), *FINS]:
                sortie.write(ligne(element))
            sortie.flush()
            return 1
        case "ferme_et_attend":
            # Tout est envoyé, la sortie est fermée, mais le processus ne se termine pas.
            for element in FINS:
                sortie.write(ligne(element))
            sortie.close()
            time.sleep(60)
        case "ligne_coupee":
            sortie.write(b'{"type":"versions"')
        case "sortie_trop_longue":
            # Lignes valides, chacune sous la limite, mais trop nombreuses au total.
            remplissage = b" " * ((1 << 20) - 200)
            for numero in range(1, 70):
                sortie.write(ligne(observation(f"alpha/{numero}"))[:-1] + remplissage + b"\n")
    sortie.flush()
    return 0


SPECIAUX = (
    "rien",
    "silence",
    "code_non_nul",
    "ferme_et_attend",
    "ligne_coupee",
    "sortie_trop_longue",
)


def main() -> int:
    scenario, argv = sys.argv[1], sys.argv[2:]
    entree = sys.stdin.buffer
    sortie = canal_du_protocole()
    executer: Callable[[str, BinaryIO, BinaryIO], int]
    if scenario == "modules":
        return principal(
            argv, entree, sortie, analyseurs=ANALYSEURS, identifier=lambda _fichier: FORMAT
        )
    executer = special if scenario in SPECIAUX else hostile
    return executer(scenario, entree, sortie)


if __name__ == "__main__":
    sys.exit(main())
