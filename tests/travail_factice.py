"""Processus de travail factice pour les tests du processus principal (T12, T13).

Lancé par ``python -I -B tests/travail_factice.py <scenario> --descripteur N``. Les scénarios
``modules`` et ``polyglotte`` exécutent le vrai déroulé du processus de travail avec les
analyseurs ci-dessous et une identification choisie ; les autres écrivent des lignes choisies,
pour vérifier que le processus principal refuse un processus de travail défaillant ou
compromis (ES-04, M-10).
"""

import json
import os
import sys
import time
from collections.abc import Callable
from typing import Any, BinaryIO

from voight_kampff._travail.contexte import Contexte
from voight_kampff._travail.fichier import Fichier, ouvrir_herite
from voight_kampff._travail.principal import Identifieur, canal_du_protocole, principal
from voight_kampff.rapport.modele import (
    Categorie,
    Direction,
    Fondement,
    Localisation,
    Partie,
    Phrase,
    Plage,
    RaisonNonMenee,
    ReferenceRegle,
)

FORMAT = "jpeg"
"""Format que l'identification factice attribue à tout le fichier (scénario ``modules``)."""


def un_seul_format(_fichier: Fichier, taille: int) -> tuple[Partie, ...]:
    return (Partie(1, FORMAT, Plage(0, taille), fin_connue=True),)


def polyglotte(_fichier: Fichier, taille: int) -> tuple[Partie, ...]:
    """Un JPEG de 4 octets, une archive hors périmètre, puis un PDF jusqu'à la fin."""
    return (
        Partie(1, "jpeg", Plage(0, 4), fin_connue=True),
        Partie(2, "zip", Plage(4, 100), fin_connue=True),
        Partie(3, "pdf", Plage(104, taille - 104), fin_connue=False),
    )


IDENTIFIEURS: dict[str, Identifieur] = {"modules": un_seul_format, "polyglotte": polyglotte}

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
    contexte.observer("lu", contexte.lire(0, 2).hex())
    # Plage relative à la partie : le contexte la ramène à une position dans le fichier.
    contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=Localisation(octets=Plage(1, 1)))


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


def partie(rang: int = 1, debut: int = 0, format_: str = "jpeg") -> dict[str, Any]:
    """Partie qui s'étend jusqu'à la fin du fichier ; sa longueur est complétée à l'envoi."""
    return {
        "rang": rang,
        "format": format_,
        "octets": {"debut": debut, "longueur": None},
        "fin_connue": True,
        "tronquee": False,
    }


def identification(*parties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "identification", "parties": list(parties)}


IDENTIFICATION = identification(partie())
VERSIONS = {"type": "versions", "dependances": []}
FIN = {"type": "fin", "empreinte": "0" * 64}


def observation(identifiant: str, module: str = "alpha", **autres: Any) -> dict[str, Any]:
    contenu = {"identifiant": identifiant, "module": module, "nom": "n", "valeur": 1, "partie": 1}
    return {"type": "observation", "observation": contenu | autres}


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
            "partie": 1,
        }
        | (
            {}
            if direction == "rien_de_particulier"
            else {"graduation": {"niveau": "faible", "evaluee": False}}
        ),
    }


def non_menee(raison: str, module: str | None = "alpha", partie: int | None = 1) -> dict[str, Any]:
    contenu: dict[str, Any] = {"raison": raison}
    if module is not None:
        contenu["module"] = module
    if partie is not None:
        contenu["partie"] = partie
    return {"type": "non_menee", "non_menee": contenu}


def module(identifiant: str = "alpha", applicable: bool = True, partie: int = 1) -> dict[str, Any]:
    return {"type": "module", "module": identifiant, "partie": partie, "applicable": applicable}


type Ligne = dict[str, Any] | bytes

# Les tests configurent deux modules actifs, alpha puis beta : une suite complète les termine.
FINS = [module("alpha"), module("beta", applicable=False), VERSIONS, FIN]

# Ces scénarios envoient eux-mêmes leur identification, ou l'omettent.
AVEC_IDENTIFICATION = {
    "sans_identification",
    "identification_double",
    "identification_rangs",
    "identification_hors_fichier",
    "identification_vide",
    "hors_perimetre",
    "polyglotte_valide",
    "partie_tronquee",
}

HOSTILES: dict[str, list[Ligne]] = {
    "valide": [
        observation("alpha/1"),
        constat("alpha/1"),
        non_menee("fichier_tronque", module=None, partie=None),
        *FINS,
    ],
    "polyglotte_valide": [
        identification(partie(), partie(2, 1, "zip"), partie(3, 2, "pdf")),
        module("alpha"),
        observation("alpha/1", partie=3),
        module("alpha", partie=3),
        non_menee("format_partiel", module=None, partie=2),
        VERSIONS,
        FIN,
    ],
    "identification_vide": [identification(), VERSIONS, FIN],
    "partie_tronquee": [identification(partie() | {"fin_connue": False, "tronquee": True}), *FINS],
    "hors_perimetre": [identification(partie(format_="gif")), VERSIONS, FIN],
    "sans_identification": [observation("alpha/1")],
    "identification_double": [IDENTIFICATION, IDENTIFICATION],
    "identification_rangs": [identification(partie(2))],
    "identification_hors_fichier": [identification(partie(debut=1 << 40))],
    "partie_d_un_autre_module": [observation("alpha/1", partie=2)],
    "module_d_une_autre_partie": [module("alpha", partie=2)],
    "non_menee_partie_inconnue": [non_menee("fichier_tronque", module=None, partie=5)],
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
    "raison_reservee_fichier": [non_menee("arret_processus", module=None, partie=None)],
    "hors_perimetre_par_le_travail": [non_menee("hors_perimetre", module=None)],
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


def ligne(element: Ligne, taille: int = 0) -> bytes:
    if isinstance(element, bytes):
        return element
    if element["type"] == "identification":
        copie: dict[str, Any] = json.loads(json.dumps(element))
        for contenu in copie["parties"]:
            octets = contenu["octets"]
            octets["longueur"] = octets["longueur"] or max(1, taille - octets["debut"])
        element = copie
    return (json.dumps(element) + "\n").encode()


def hostile(nom: str, entree: BinaryIO, sortie: BinaryIO, taille: int) -> int:
    if nom == "sans_isolation":
        sortie.write(ligne(observation("alpha/1")))
        return 0
    sortie.write(ligne(ISOLATION))
    sortie.flush()
    entree.readline()
    if nom not in AVEC_IDENTIFICATION:
        sortie.write(ligne(IDENTIFICATION, taille))
    for element in HOSTILES[nom]:
        sortie.write(ligne(element, taille))
    sortie.flush()
    return 0


def special(nom: str, entree: BinaryIO, sortie: BinaryIO, taille: int) -> int:
    """Scénarios qui ne se réduisent pas à une liste de lignes."""
    if nom == "rien":
        return 0
    sortie.write(ligne(ISOLATION))
    sortie.flush()
    entree.readline()
    match nom:
        case "silence":
            time.sleep(60)
        case "silence_apres_identification":
            sortie.write(ligne(IDENTIFICATION, taille))
            sortie.flush()
            time.sleep(60)
        case "code_non_nul":
            for element in [IDENTIFICATION, observation("alpha/1"), *FINS]:
                sortie.write(ligne(element, taille))
            sortie.flush()
            return 1
        case "ferme_et_attend":
            # Tout est envoyé, la sortie est fermée, mais le processus ne se termine pas.
            for element in [IDENTIFICATION, *FINS]:
                sortie.write(ligne(element, taille))
            sortie.close()
            time.sleep(60)
        case "ligne_coupee":
            sortie.write(b'{"type":"versions"')
        case "sortie_trop_longue":
            # Lignes valides, chacune sous la limite, mais trop nombreuses au total.
            remplissage = b" " * ((1 << 20) - 200)
            sortie.write(ligne(IDENTIFICATION, taille))
            for numero in range(1, 70):
                sortie.write(ligne(observation(f"alpha/{numero}"))[:-1] + remplissage + b"\n")
    sortie.flush()
    return 0


SPECIAUX = (
    "rien",
    "silence",
    "silence_apres_identification",
    "code_non_nul",
    "ferme_et_attend",
    "ligne_coupee",
    "sortie_trop_longue",
)


def main() -> int:
    scenario, argv = sys.argv[1], sys.argv[2:]
    entree = sys.stdin.buffer
    sortie = canal_du_protocole()
    executer: Callable[[str, BinaryIO, BinaryIO, int], int]
    if scenario in IDENTIFIEURS:
        return principal(
            argv, entree, sortie, analyseurs=ANALYSEURS, identifier=IDENTIFIEURS[scenario]
        )
    # Taille du fichier transmis : les parties annoncées s'étendent jusqu'à sa fin.
    taille = os.fstat(ouvrir_herite(int(argv[argv.index("--descripteur") + 1]))).st_size
    executer = special if scenario in SPECIAUX else hostile
    return executer(scenario, entree, sortie, taille)


if __name__ == "__main__":
    sys.exit(main())
