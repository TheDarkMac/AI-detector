"""Phase 3 du relevé de T32 : lecture des fichiers téléchargés par l'outil lui-même.

Chaque fichier de ``phase2.jsonl`` est analysé par :func:`voight_kampff.analyse.analyser`, dans
un processus de travail isolé, tous les modules désactivés sauf ``dwtdct`` : les nombres sont
ceux que donnerait ``vk``, règles du catalogue comprises. Quatre analyses à la fois.

Écrit ``resultats.csv`` (au dépôt) : un fichier par ligne, avec sa page, sa licence, ses
dimensions, son empreinte, ce que le module en a lu et les règles qui ont donné un constat ; puis
``phase3.txt`` (hors du dépôt), le résumé que reprennent l'ADR-0204 et la fiche.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from voight_kampff.analyse import Analyse, analyser
from voight_kampff.modules import dwtdct
from voight_kampff.rapport.modele import Valeur

type Fiche = dict[str, Any]

ICI = Path(__file__).resolve().parent
ENTREE = ICI / "phase2.jsonl"
RESULTATS = ICI / "resultats.csv"
RESUME = ICI / "phase3.txt"
LIVRES = [
    "c2pa", "doublejpeg", "ela", "exif", "id3", "image", "infopdf", "infowav", "iptc",
    "matroska", "odf", "ooxml", "quicktime", "textepng", "vorbis", "xmp",
]  # fmt: skip
NOMS = [lecture.nom for lecture in dwtdct.LECTURES]
COLONNES = [
    "liste",
    "page",
    "licence",
    "compte",
    "versement",
    "type",
    "largeur",
    "hauteur",
    "sha256",
    "etat",
    "blocs",
    *NOMS,
    "constats",
]


def lire(fiche: Fiche) -> Fiche:
    analyse: Analyse = analyser(ICI / fiche["chemin"], desactiver=LIVRES)
    valeurs: dict[str, Valeur] = {
        o.nom: o.valeur for o in analyse.observations if o.module == "dwtdct"
    }
    propres = [n for n in analyse.non_menees if n.module == "dwtdct"]
    if propres:
        etat = "non_mene:" + ",".join(n.raison for n in propres)
    elif valeurs.get("dwtdct.chrominance") is False:
        etat = "gris"
    elif "dwtdct.blocs" not in valeurs:
        etat = "petite"
    else:
        etat = "lu"
    ligne = {colonne: fiche.get(colonne, "") for colonne in COLONNES[:9]}
    ligne["etat"] = etat
    ligne["blocs"] = valeurs.get("dwtdct.blocs", "")
    for nom in NOMS:
        ligne[nom] = valeurs.get(f"dwtdct.concordants_{nom}", "")
    ligne["constats"] = " ".join(sorted(c.regle.identifiant for c in analyse.constats))
    return ligne


def _repartition(valeurs: list[int]) -> str:
    effectifs = Counter(valeurs)
    haut = ", ".join(f"{v}:{effectifs[v]}" for v in sorted(effectifs)[-6:])
    return (
        f"min {valeurs[0]}, médiane {valeurs[len(valeurs) // 2]}, max {valeurs[-1]} ; "
        f"plus hautes valeurs {haut}"
    )


def resumer(lignes: list[Fiche]) -> str:
    sortie = []
    for liste in ("authentique", "declare"):
        choisies = [ligne for ligne in lignes if ligne["liste"] == liste]
        etats = Counter(ligne["etat"] for ligne in choisies).most_common()
        sortie.append(f"## {liste} : {len(choisies)} fichiers")
        sortie.append("états : " + ", ".join(f"{k} {v}" for k, v in etats))
        lus = [ligne for ligne in choisies if ligne["etat"] == "lu"]
        for type_ in ("image/jpeg", "image/png"):
            du_type = [ligne for ligne in lus if ligne["type"] == type_]
            sortie.append(f"### {type_} lus : {len(du_type)}")
            for lecture in dwtdct.LECTURES:
                valeurs = sorted(int(ligne[lecture.nom]) for ligne in du_type if ligne[lecture.nom])
                if valeurs:
                    n = len(lecture.message)
                    sortie.append(f"{lecture.nom} (sur {n}) : {_repartition(valeurs)}")
        constats: dict[str, int] = defaultdict(int)
        for ligne in choisies:
            for regle in ligne["constats"].split():
                constats[regle] += 1
        resume = ", ".join(f"{k} {v}" for k, v in sorted(constats.items())) or "aucun"
        sortie.append("constats : " + resume)
    return "\n".join(sortie) + "\n"


def main() -> None:
    fiches = [json.loads(ligne) for ligne in ENTREE.read_text(encoding="utf-8").splitlines()]
    fiches = [f for f in fiches if f.get("chemin")]
    with ThreadPoolExecutor(max_workers=4) as executeur:
        lignes = list(executeur.map(lire, fiches))
    with RESULTATS.open("w", encoding="utf-8", newline="") as sortie:
        ecrivain = csv.DictWriter(sortie, fieldnames=COLONNES, lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    RESUME.write_text(resumer(lignes), encoding="utf-8")
    sys.stdout.write(RESUME.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
