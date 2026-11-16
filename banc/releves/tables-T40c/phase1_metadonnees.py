"""Phase 1 du relevé du complément de T40 : métadonnées des JPEG de Wikimedia Commons.

Parcourt ``list=allimages`` par fenêtres mensuelles (2008 à 2025), quatre appels de 50 fichiers
par mois, et garde pour chaque JPEG le nom, les adresses, le compte qui l'a versé et
les champs EXIF utiles (Make, Model, Software, dates, dimensions). Reprend là où il s'est arrêté
(fichier ``phase1.jsonl`` et ``phase1.etat.json``). Une requête à la fois, ``maxlag=5``.
"""

from __future__ import annotations

import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

type Fiche = dict[str, Any]
"""Un enregistrement JSON du relevé."""

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "phase1.jsonl"
ETAT = ICI / "phase1.etat.json"
API = "https://commons.wikimedia.org/w/api.php"
AGENT = "voight-kampff-releve/0.1 (https://github.com/TheDarkMac/AI-detector)"
CHAMPS = (
    "Make",
    "Model",
    "Software",
    "DateTimeOriginal",
    "DateTime",
    "PixelXDimension",
    "PixelYDimension",
)
APPELS_PAR_MOIS = 4


def appeler(parametres: dict[str, str]) -> Fiche:
    adresse = API + "?" + urllib.parse.urlencode(parametres)
    essai = 0
    while True:
        essai += 1
        # Adresse fixe en https de l'API de Commons : aucun autre schéma possible.
        requete = urllib.request.Request(adresse, headers={"User-Agent": AGENT})  # noqa: S310
        try:
            with urllib.request.urlopen(requete, timeout=60) as reponse:  # noqa: S310
                donnees: Fiche = json.load(reponse)
        except (OSError, http.client.HTTPException, json.JSONDecodeError) as erreur:
            attente = min(300, 10 * essai)
            if isinstance(erreur, urllib.error.HTTPError) and erreur.headers.get("Retry-After"):
                attente = max(attente, int(erreur.headers["Retry-After"]))
            print(f"erreur {erreur!r}, attente {attente} s", file=sys.stderr, flush=True)
            time.sleep(attente)
            continue
        if "error" in donnees:
            if donnees["error"].get("code") == "maxlag":
                time.sleep(10)
                continue
            raise RuntimeError(donnees["error"])
        return donnees


def mois() -> list[str]:
    return [f"{annee}-{m:02d}-01T00:00:00Z" for annee in range(2008, 2026) for m in range(1, 13)]


def main() -> None:
    faits = set(json.loads(ETAT.read_text())) if ETAT.exists() else set()
    with SORTIE.open("a", encoding="utf-8") as sortie:
        for debut in mois():
            if debut in faits:
                continue
            suite: dict[str, str] = {}
            for _ in range(APPELS_PAR_MOIS):
                parametres = {
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "list": "allimages",
                    "aisort": "timestamp",
                    "aidir": "newer",
                    "aistart": debut,
                    "ailimit": "50",
                    "aiprop": "url|user|mime|size|timestamp|metadata",
                    "maxlag": "5",
                    **suite,
                }
                donnees = appeler(parametres)
                for image in donnees["query"]["allimages"]:
                    if image.get("mime") != "image/jpeg":
                        continue
                    meta = {
                        m["name"]: m["value"]
                        for m in image.get("metadata") or []
                        if m.get("name") in CHAMPS and isinstance(m.get("value"), (str, int))
                    }
                    enregistrement = {
                        "nom": image["name"],
                        "adresse": image["url"],
                        "page": image["descriptionurl"],
                        "compte": image.get("user"),
                        "versement": image.get("timestamp"),
                        "largeur": image.get("width"),
                        "hauteur": image.get("height"),
                        "taille": image.get("size"),
                        **{k.lower(): v for k, v in meta.items()},
                    }
                    sortie.write(json.dumps(enregistrement, ensure_ascii=False) + "\n")
                sortie.flush()
                suite = donnees.get("continue", {})
                suite.pop("continue", None)
                time.sleep(1)
                if not suite:
                    break
            faits.add(debut)
            ETAT.write_text(json.dumps(sorted(faits)))
            print(f"{debut} fait", flush=True)


if __name__ == "__main__":
    main()
