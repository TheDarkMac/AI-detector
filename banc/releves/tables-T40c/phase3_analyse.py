"""Phase 3 du relevé du complément de T40 : regroupement des tables lues en phase 2.

- Écarte les fichiers illisibles, ceux dont les tables n'ont pas été atteintes et ceux dont les
  tables sont celles d'un encodeur que le module ``image`` reconnaît déjà (réencodés ailleurs).
- Photoshop : niveau = valeur brute signée de la ressource 0x0406 + 4 (ExifTool, Photoshop.pm) ;
  empreintes par niveau, avec le nombre de fichiers et de comptes.
- Appareils : empreintes par marque et modèle EXIF ; un modèle est dit adaptatif quand ses
  fichiers portent presque tous des tables différentes.
- Une empreinte est retenue si au moins ``FICHIERS_MIN`` fichiers la portent, versés par au moins
  ``COMPTES_MIN`` comptes ; ses collisions (autres niveaux, autres modèles, fichiers de contrôle)
  sont listées.

Écrit ``phase3.json`` et un résumé sur la sortie standard.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

type Fiche = dict[str, Any]
"""Un enregistrement JSON du relevé."""

ICI = Path(__file__).resolve().parent
FICHIERS_MIN = 3
COMPTES_MIN = 2


def charger() -> tuple[list[Fiche], dict[str, int]]:
    retenus: list[Fiche] = []
    ecartes: defaultdict[str, int] = defaultdict(int)
    vus: set[str] = set()
    with (ICI / "phase2.jsonl").open(encoding="utf-8") as entree:
        for ligne in entree:
            fiche = json.loads(ligne)
            if fiche["nom"] in vus:
                continue
            vus.add(fiche["nom"])
            if fiche.get("erreur"):
                ecartes[f"{fiche['nature']} : {fiche['erreur']}"] += 1
            elif fiche.get("incomplet") or "empreinte" not in fiche:
                ecartes[f"{fiche['nature']} : tables non atteintes"] += 1
            elif fiche["encodeur"]:
                ecartes[f"{fiche['nature']} : tables d'un encodeur reconnu"] += 1
                fiche["reconnu"] = True
                retenus.append(fiche)
            else:
                retenus.append(fiche)
    return retenus, dict(ecartes)


def niveau(fiche: Fiche) -> int | None:
    brut = fiche.get("r0406")
    if not brut or len(brut) < 4:
        return None
    return int.from_bytes(bytes.fromhex(brut[:4]), "big", signed=True) + 4


def cle(fiche: Fiche) -> str | None:
    if fiche.get("reconnu"):
        return None
    if fiche["nature"] == "photoshop":
        n = niveau(fiche)
        return None if n is None else f"photoshop {n}"
    if fiche["nature"] == "appareil":
        return f"appareil {fiche['make'].strip()} | {fiche['model'].strip()}"
    return f"controle {(fiche.get('software') or '').strip()[:40]}"


def main() -> None:
    fiches, ecartes = charger()
    groupes: dict[str, dict[str, list[Fiche]]] = defaultdict(lambda: defaultdict(list))
    par_empreinte: dict[str, set[str]] = defaultdict(set)
    for fiche in fiches:
        if fiche.get("reconnu"):
            continue
        if (groupe := cle(fiche)) is None:
            ecartes[f"{fiche['nature']} : sans ressource 0x0406"] = (
                ecartes.get(f"{fiche['nature']} : sans ressource 0x0406", 0) + 1
            )
            continue
        groupes[groupe][fiche["empreinte"]].append(fiche)
        par_empreinte[fiche["empreinte"]].add(groupe)
    resultat: Fiche = {"ecartes": ecartes, "groupes": {}}
    for groupe in sorted(groupes, key=lambda g: (g.split()[0], g)):
        empreintes = groupes[groupe]
        total = sum(map(len, empreintes.values()))
        lignes = []
        for empreinte, liste in sorted(empreintes.items(), key=lambda e: -len(e[1])):
            comptes = {f.get("compte") for f in liste}
            lignes.append(
                {
                    "empreinte": empreinte,
                    "fichiers": len(liste),
                    "comptes": len(comptes),
                    "retenue": len(liste) >= FICHIERS_MIN and len(comptes) >= COMPTES_MIN,
                    "ailleurs": sorted(par_empreinte[empreinte] - {groupe}),
                    "logiciels": sorted({(f.get("software") or "").strip() for f in liste}),
                    "formats": sorted({(f.get("r0406") or "")[4:] for f in liste}),
                    "exemples": [f["page"] for f in liste[:5]],
                }
            )
        adaptatif = groupe.startswith("appareil") and total >= 4 and len(empreintes) >= 0.75 * total
        resultat["groupes"][groupe] = {
            "fichiers": total,
            "empreintes": lignes,
            "adaptatif": adaptatif,
        }
    (ICI / "phase3.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=1))
    print("Écartés :", json.dumps(ecartes, ensure_ascii=False, indent=1))
    for groupe, donnees in resultat["groupes"].items():
        if groupe.startswith("controle"):
            continue
        retenues = [e for e in donnees["empreintes"] if e["retenue"]]
        marque = " ADAPTATIF" if donnees["adaptatif"] else ""
        print(
            f"{groupe} : {donnees['fichiers']} fichiers, {len(donnees['empreintes'])} empreintes,"
            f" {len(retenues)} retenues{marque}"
        )
        for e in retenues:
            print(
                f"    {e['empreinte'][:16]} {e['fichiers']} f / {e['comptes']} c"
                f" formats {e['formats']} ailleurs {e['ailleurs'][:4]}"
            )


if __name__ == "__main__":
    main()
