"""Rapport d'évaluation : document JSON et sa version Markdown (ADR-0105).

Le Markdown est rendu depuis le document JSON : les deux disent exactement la même chose. Le
document cite le corpus (nom, version, empreinte du manifeste), la partie, les versions de
l'outil, du catalogue et des techniques, l'état du réseau et les bornes employées : de quoi
refaire l'évaluation et vérifier qu'on mesure la même chose (NF-06).
"""

import json
import os
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from banc.corpus import Corpus, Nature, Partie
from banc.evaluation import Evaluation
from banc.mesures import CONFIANCE
from voight_kampff._regles import BORNE_FORT, BORNE_MODERE
from voight_kampff.rapport.modele import VersionCatalogue

__all__ = ["FICHIERS", "FORMAT", "document", "ecrire", "markdown", "preparer"]

FORMAT = 1
FICHIERS = ("evaluation.json", "evaluation.md")
_CREATION = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)

_CATEGORIES = {
    "authentique": "Authentiques",
    "genere": "Générés",
    "transforme": "Transformés",
    "retouche": "Retouchés",
    "malforme": "Malformés",
}


def document(
    corpus: Corpus,
    evaluation: Evaluation,
    *,
    outil: str,
    catalogue: VersionCatalogue,
    techniques: Mapping[str, str],
    interfaces: Sequence[str],
    date: datetime,
) -> dict[str, Any]:
    """Document JSON de l'évaluation ; ``techniques`` donne la version de chaque module."""
    return {
        "format": FORMAT,
        "date": date.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "corpus": {
            "nom": corpus.nom,
            "version": corpus.version,
            "date": corpus.date.isoformat(),
            "nature": corpus.nature.value,
            "empreinte": corpus.empreinte,
        },
        "publiable": corpus.nature is Nature.REFERENCE and evaluation.partie is Partie.EVALUATION,
        "versions": {
            "outil": outil,
            "catalogue": {
                "version": catalogue.version,
                "date": catalogue.date.isoformat(),
                "empreinte": catalogue.empreinte,
                "fourni_par_utilisateur": catalogue.fourni_par_utilisateur,
            },
            "techniques": dict(techniques),
        },
        "reseau": {"interfaces": list(interfaces), "tentatives": 0},
        "bornes": {
            "methode": "wilson",
            "confiance": CONFIANCE,
            "fort": BORNE_FORT,
            "modere": BORNE_MODERE,
        },
    } | evaluation.vers_dict()


# Markdown


def _pourcent(valeur: float) -> str:
    return f"{valeur * 100:.1f}".replace(".", ",") + " %"


def _taux(taux: Mapping[str, Any]) -> str:
    """« 2/40 : 5,0 % [1,4 % ; 16,5 %] », ou un tiret sans effectif."""
    if not taux["effectif"]:
        return "—"
    basse, haute = taux["intervalle"]
    return (
        f"{taux['nombre']}/{taux['effectif']} : {_pourcent(taux['valeur'])} "
        f"[{_pourcent(basse)} ; {_pourcent(haute)}]"
    )


def _niveau(regle: Mapping[str, Any]) -> str:
    niveau: str | None = regle["niveau"]
    if niveau is None:
        return "—"
    return niveau + ("" if regle["evaluee"] else ", non évaluée")


def _tableau(entetes: Sequence[str], lignes: Sequence[Sequence[str]]) -> list[str]:
    def ligne(cellules: Sequence[str]) -> str:
        return "| " + " | ".join(c.replace("|", "\\|") for c in cellules) + " |"

    return [ligne(entetes), ligne(["---"] * len(entetes)), *map(ligne, lignes)]


def markdown(doc: Mapping[str, Any]) -> str:
    """Rapport d'évaluation lisible, rendu depuis le document JSON."""
    corpus, versions, fichiers = doc["corpus"], doc["versions"], doc["fichiers"]
    catalogue = versions["catalogue"]
    lignes = [
        f"# Évaluation du corpus {corpus['nom']} {corpus['version']}",
        "",
    ]
    if not doc["publiable"]:
        raison = (
            "corpus d'essai, qui ne sert qu'à éprouver le banc"
            if corpus["nature"] == "essai"
            else "partie calibrage, qui sert à régler les seuils (ADR-0016)"
        )
        lignes += [f"> **Aucun taux de ce rapport n'est publiable** : {raison}.", ""]
    lignes += [
        f"- Date : {doc['date']}",
        f"- Corpus : {corpus['nom']} {corpus['version']} du {corpus['date']} "
        f"({corpus['nature']}), manifeste {corpus['empreinte']}",
        f"- Partie : {doc['partie']}",
        f"- Outil : {versions['outil']} ; catalogue {catalogue['version']} du "
        f"{catalogue['date']}, empreinte {catalogue['empreinte']}"
        + (", fourni par l'utilisateur" if catalogue["fourni_par_utilisateur"] else ""),
        "- Techniques : "
        + (
            ", ".join(f"{m} {v}" for m, v in versions["techniques"].items())
            or "aucune technique livrée"
        ),
        f"- Réseau : interfaces {', '.join(doc['reseau']['interfaces']) or 'aucune'}, "
        f"{doc['reseau']['tentatives']} tentative de connexion",
        f"- Intervalles : Wilson, confiance {_pourcent(doc['bornes']['confiance'])} ; niveau "
        f"« fort » jusqu'à {_pourcent(doc['bornes']['fort'])}, « modéré » jusqu'à "
        f"{_pourcent(doc['bornes']['modere'])} (borne supérieure)",
        "",
        "## Fichiers",
        "",
        *_tableau(
            ["Catégorie", "Fichiers"],
            [[_CATEGORIES[c], str(n)] for c, n in fichiers["par_categorie"].items()]
            + [["Total", str(fichiers["total"])]],
        ),
        "",
        "Refus : "
        + (", ".join(f"{m} ({n})" for m, n in fichiers["refus"].items()) or "aucun")
        + ". Arrêts brutaux : "
        + (", ".join(f"{e} ({n})" for e, n in fichiers["arrets_brutaux"].items()) or "aucun")
        + f". Analyses interrompues : {fichiers['interrompues']}.",
        "",
        "## Taux par fichier (ADR-0018)",
        "",
        "Part des fichiers authentiques analysés dont le rapport porte une preuve, ou un indice "
        "modéré ou fort, dirigé vers l'origine IA ou la retouche.",
        "",
    ]
    par_fichier = doc["par_fichier"]
    lignes += _tableau(
        ["Catégorie", "Taux"],
        [[_CATEGORIES[c], _taux(t)] for c, t in par_fichier["categories"].items()],
    )
    atteinte = {True: "atteinte", False: "non atteinte", None: "non mesurable"}
    lignes += [
        "",
        f"Cible : borne supérieure au plus {_pourcent(par_fichier['cible'])} sur les "
        f"authentiques ; {atteinte[par_fichier['cible_atteinte']]}.",
        "",
        "## Techniques (§8 du cahier)",
        "",
    ]
    if doc["techniques"]:
        lignes += _tableau(
            [
                "Technique",
                "Catégorie",
                "Fichiers",
                "Non applicables",
                "Non analysables",
                "Faux positifs",
                "Faux négatifs",
                "Confusions",
            ],
            [
                [
                    m["module"],
                    _CATEGORIES[m["categorie"]],
                    str(m["effectif"]),
                    str(m["non_applicables"]),
                    _taux(m["non_analysables"]),
                    _taux(m["faux_positifs"]),
                    _taux(m["faux_negatifs"]),
                    str(m["confusions"]),
                ]
                for m in doc["techniques"]
            ],
        )
    else:
        lignes.append("Aucune technique livrée dans cette version de l'outil.")
    lignes += ["", "## Règles (ADR-0101)", ""]
    if doc["regles"]:
        lignes += _tableau(
            ["Règle", "Catégorie", "Direction", "Niveau", "Faux positifs", "Niveau permis"],
            [
                [
                    f"{r['identifiant']} v{r['version']} ({r['module']})",
                    r["categorie"],
                    r["direction"],
                    _niveau(r),
                    _taux(r["faux_positifs"]),
                    r["niveau_permis"] or "—",
                ]
                for r in doc["regles"]
            ],
        )
    else:
        lignes.append("Aucune règle de preuve ou d'indice dans ce catalogue.")
    lignes += ["", "## Écarts", ""]
    lignes += [f"- {ecart}" for ecart in doc["ecarts"]] or ["Aucun."]
    return "\n".join(lignes) + "\n"


# Écriture


def preparer(dossier: str | Path) -> Path:
    """Dossier du rapport, créé au besoin (pas ses parents), sans rapport déjà présent.

    Lève ``ValueError`` avec le message à afficher : rien n'est analysé.
    """
    chemin = Path(dossier)
    try:
        if not chemin.is_dir():
            chemin.mkdir()
    except OSError as erreur:
        raise ValueError(f"dossier inutilisable ({erreur.strerror})") from None
    for nom in FICHIERS:
        if (chemin / nom).exists():
            raise ValueError(f"{nom} existe déjà ; aucun rapport n'est écrasé")
    return chemin


def ecrire(dossier: Path, doc: Mapping[str, Any]) -> None:
    """Écrit le document JSON et sa version Markdown, sans rien écraser."""
    contenus = (
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        markdown(doc),
    )
    for nom, contenu in zip(FICHIERS, contenus, strict=True):
        descripteur = os.open(dossier / nom, _CREATION, 0o644)
        with os.fdopen(descripteur, "wb") as fichier:
            fichier.write(contenu.encode("utf-8"))
