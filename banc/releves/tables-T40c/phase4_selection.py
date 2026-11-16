"""Phase 4 du relevé du complément de T40 : empreintes retenues, licences, fichiers livrés.

Critères (ADR-0193, ADR-0194, ADR-0195) :

- un fichier compte s'il a été lu jusqu'au premier balayage, si ses tables ne sont pas celles
  d'un encodeur que le module ``image`` reconnaît déjà, et, pour Photoshop, s'il porte la
  ressource 0x0406 (niveau = valeur brute signée + 4) ;
- Photoshop : par niveau, toute empreinte portée par au moins 3 fichiers de 2 comptes ;
- appareils : toute empreinte portée par au moins 3 fichiers de 2 comptes, d'une seule marque,
  jamais sur un fichier de Photoshop ; les fichiers d'autres logiciels sont comptés et nommés ;
  les modèles adaptatifs (au moins 4 fichiers, presque tous à des tables différentes) sont
  listés, leurs fichiers ne comptent pas.

Lit la licence de chaque fichier retenu par l'API de Wikimedia Commons (``LicenseShortName``),
15 titres par appel, et écrit ``tables.toml`` (empreintes, tables en clair, comptes) et
``fichiers.csv`` (un fichier source par ligne).
"""

from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from phase1_metadonnees import API, appeler  # noqa: F401  (même client, mêmes reprises)

type Fiche = dict[str, Any]
"""Un enregistrement JSON du relevé."""

ICI = Path(__file__).resolve().parent
LICENCES = ICI / "licences.json"
LOT = 15
"""Titres par appel : au-delà, l'adresse de la requête dépasse ce qu'accepte le serveur (414)."""
MARQUES = (
    ("CANON", "Canon"),
    ("NIKON", "Nikon"),
    ("PANASONIC", "Panasonic"),
    ("KODAK", "Kodak"),
    ("APPLE", "Apple"),
    ("SONY", "Sony"),
    ("OLYMPUS", "Olympus"),
    ("FUJI", "Fujifilm"),
    ("SAMSUNG", "Samsung"),
    ("PENTAX", "Pentax"),
    ("CASIO", "Casio"),
    ("MINOLTA", "Minolta"),
)


def marque(fiche: Fiche) -> str:
    brute = fiche["make"].strip()
    return next((nom for cle, nom in MARQUES if cle in brute.upper()), brute)


def niveau(fiche: Fiche) -> int:
    return int.from_bytes(bytes.fromhex(fiche["r0406"][:4]), "big", signed=True) + 4


def charger() -> list[Fiche]:
    fiches: dict[str, Fiche] = {}
    with (ICI / "phase2.jsonl").open(encoding="utf-8") as entree:
        for ligne in entree:
            fiche = json.loads(ligne)
            fiches.setdefault(fiche["nom"], fiche)
    return [
        f
        for f in fiches.values()
        if f.get("empreinte")
        and not f.get("encodeur")
        and not f.get("incomplet")
        and f.get("sof")
        and (f["nature"] != "photoshop" or f.get("r0406"))
    ]


def retenir(fiches: list[Fiche]) -> tuple[list[Fiche], list[str]]:
    par_empreinte: dict[str, list[Fiche]] = defaultdict(list)
    for f in fiches:
        par_empreinte[f["empreinte"]].append(f)
    photoshop = {f["empreinte"] for f in fiches if f["nature"] == "photoshop"}
    retenues = []
    # Photoshop, par niveau.
    par_niveau: dict[tuple[int, str], list[Fiche]] = defaultdict(list)
    for f in fiches:
        if f["nature"] == "photoshop":
            par_niveau[(niveau(f), f["empreinte"])].append(f)
    for (n, empreinte), liste in sorted(par_niveau.items()):
        if len(liste) >= 3 and len({f["compte"] for f in liste}) >= 2:
            retenues.append(
                {
                    "famille": "photoshop",
                    "niveau": n,
                    "empreinte": empreinte,
                    "sources": liste,
                    "toutes": par_empreinte[empreinte],
                }
            )
    # Appareils.
    modeles: dict[str, dict[str, int]] = defaultdict(Counter)
    for f in fiches:
        if f["nature"] == "appareil":
            modeles[f"{f['make'].strip()} | {f['model'].strip()}"][f["empreinte"]] += 1
    adaptatifs = sorted(
        m for m, e in modeles.items() if sum(e.values()) >= 4 and len(e) >= 0.75 * sum(e.values())
    )
    for empreinte, toutes in sorted(par_empreinte.items()):
        liste = [
            f
            for f in toutes
            if f["nature"] == "appareil"
            and f"{f['make'].strip()} | {f['model'].strip()}" not in adaptatifs
        ]
        marques = {marque(f) for f in liste}
        if (
            len(liste) >= 3
            and len({f["compte"] for f in liste}) >= 2
            and len(marques) == 1
            and empreinte not in photoshop
        ):
            retenues.append(
                {
                    "famille": "appareil",
                    "marque": marques.pop(),
                    "empreinte": empreinte,
                    "sources": liste,
                    "toutes": toutes,
                }
            )
    return retenues, adaptatifs


def licences(noms: list[str]) -> dict[str, str]:
    connues: dict[str, str] = json.loads(LICENCES.read_text()) if LICENCES.exists() else {}
    manquants = [n for n in noms if n not in connues]
    for debut in range(0, len(manquants), LOT):
        lot = manquants[debut : debut + LOT]
        donnees = appeler(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "imageinfo",
                "iiprop": "extmetadata",
                "iiextmetadatafilter": "LicenseShortName",
                "titles": "|".join(f"File:{n}" for n in lot),
                "maxlag": "5",
            }
        )
        normalises = {n["to"]: n["from"] for n in donnees["query"].get("normalized", [])}
        for page in donnees["query"]["pages"]:
            titre = normalises.get(page["title"], page["title"])
            info = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
            connues[titre.removeprefix("File:")] = (info.get("LicenseShortName") or {}).get(
                "value", "inconnue"
            )
        LICENCES.write_text(json.dumps(connues, ensure_ascii=False, indent=0))
        time.sleep(1)
    return connues


def ecrire(retenues: list[Fiche], adaptatifs: list[str], licence: dict[str, str]) -> None:
    lignes = [
        "# Tables relevées par le complément de T40 (ADR-0193 à ADR-0195), écrites par",
        "# phase4_selection.py. Tables dans l'ordre du segment DQT ; empreinte : ADR-0181.",
        "",
    ]
    for r in retenues:
        s = r["sources"]
        autres = Counter(
            (f.get("software") or "").strip()
            or f"{f.get('make', '').strip()} {f.get('model', '').strip()}"
            for f in r["toutes"]
            if f not in s
        )
        cotes = [max(f["largeur"], f["hauteur"]) for f in s]
        lignes += ["[[tables]]", f'empreinte = "{r["empreinte"]}"', f'famille = "{r["famille"]}"']
        if r["famille"] == "photoshop":
            lignes.append(f"niveau = {r['niveau']}")
        else:
            lignes.append(f'marque = "{r["marque"]}"')
            modeles = sorted({f["model"].strip() for f in s})
            lignes.append("modeles = " + json.dumps(modeles, ensure_ascii=False))
        lignes += [
            f"fichiers = {len(s)}",
            f"comptes = {len({f['compte'] for f in s})}",
            f"composantes = {sorted({len(f['sof']['composantes']) for f in s})}",
            f"cote_long = [{min(cotes)}, {max(cotes)}]",
            "ailleurs = "
            + json.dumps(dict(autres.most_common()), ensure_ascii=False)
            .replace(": ", " = ")
            .replace("{", "{ ")
            .replace("}", " }")
            if autres
            else "ailleurs = {}",
        ]
        tables = s[0]["tables"]
        for identifiant, (_seize, valeurs) in sorted(tables.items()):
            lignes.append(f"table_{identifiant} = {valeurs}")
        lignes.append("")
    lignes.append("[modeles_adaptatifs]")
    lignes.append("liste = " + json.dumps(adaptatifs, ensure_ascii=False))
    (ICI / "tables.toml").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    with (ICI / "fichiers.csv").open("w", encoding="utf-8", newline="") as sortie:
        ecrivain = csv.writer(sortie)
        ecrivain.writerow(
            [
                "empreinte",
                "famille",
                "niveau_ou_marque",
                "page",
                "licence",
                "compte",
                "logiciel",
                "marque_exif",
                "modele_exif",
                "largeur",
                "hauteur",
            ]
        )
        for r in retenues:
            for f in sorted(r["sources"], key=lambda f: f["nom"]):
                ecrivain.writerow(
                    [
                        r["empreinte"],
                        r["famille"],
                        r.get("niveau", r.get("marque")),
                        f["page"],
                        licence.get(f["nom"], "inconnue"),
                        f["compte"],
                        (f.get("software") or "").strip(),
                        (f.get("make") or "").strip(),
                        (f.get("model") or "").strip(),
                        f["largeur"],
                        f["hauteur"],
                    ]
                )


def ecrire_entetes() -> None:
    """Les en-têtes lus en phase 2, un par fichier, sans les tables (``entetes.csv``)."""
    vus: set[str] = set()
    with (
        (ICI / "phase2.jsonl").open(encoding="utf-8") as entree,
        (ICI / "entetes.csv").open("w", encoding="utf-8", newline="") as sortie,
    ):
        ecrivain = csv.writer(sortie)
        ecrivain.writerow(
            [
                "page",
                "compte",
                "nature",
                "logiciel",
                "marque_exif",
                "modele_exif",
                "largeur",
                "hauteur",
                "r0406",
                "composantes",
                "empreinte",
                "encodeur_reconnu",
                "erreur",
            ]
        )
        for ligne in entree:
            f = json.loads(ligne)
            if f["nom"] in vus:
                continue
            vus.add(f["nom"])
            ecrivain.writerow(
                [
                    f["page"],
                    f.get("compte"),
                    f["nature"],
                    (f.get("software") or "").strip(),
                    (f.get("make") or "").strip(),
                    (f.get("model") or "").strip(),
                    f["largeur"],
                    f["hauteur"],
                    f.get("r0406") or "",
                    len(f["sof"]["composantes"]) if f.get("sof") else "",
                    f.get("empreinte", ""),
                    json.dumps(f.get("encodeur") or {}, sort_keys=True),
                    f.get("erreur") or ("tables non atteintes" if f.get("incomplet") else ""),
                ]
            )


def main() -> None:
    retenues, adaptatifs = retenir(charger())
    noms = sorted({f["nom"] for r in retenues for f in r["sources"]})
    print(
        len(retenues), "empreintes,", len(noms), "fichiers,", len(adaptatifs), "modèles adaptatifs"
    )
    ecrire(retenues, adaptatifs, licences(noms))
    ecrire_entetes()
    print(Counter(json.loads(LICENCES.read_text()).get(n, "?") for n in noms).most_common(12))


if __name__ == "__main__":
    main()
