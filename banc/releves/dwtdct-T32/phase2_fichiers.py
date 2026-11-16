"""Phase 2 du relevé de T32 : choix des fichiers et téléchargement.

- ``authentique`` : parmi les JPEG et PNG de la phase 1 dont l'original a au moins
  :data:`LARGEUR_MIN` pixels de large (le rendu de 960 pixels est donc une réduction), au plus
  :data:`PAR_COMPTE` fichiers par compte qui les a versés, :data:`JPEG` JPEG et :data:`PNG` PNG
  tirés au hasard (graine :data:`GRAINE`) ; on télécharge le rendu de 960 pixels de large que
  Commons sert, pas l'original.
- ``declare`` : tous les fichiers de la phase 1 de moins de :data:`TAILLE_MAX` octets, en
  original : un rendu réduit aurait effacé le filigrane.

Les fichiers vont dans ``fichiers/`` (hors du dépôt) ; ``phase2.jsonl`` garde, pour chacun, sa
page, sa licence, son empreinte SHA-256 et le statut HTTP. Une requête toutes les
:data:`ATTENTE` secondes ; reprend là où il s'est arrêté (par le nom du fichier).
"""

from __future__ import annotations

import hashlib
import http.client
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

type Fiche = dict[str, Any]

ICI = Path(__file__).resolve().parent
ENTREE = ICI / "phase1.jsonl"
SORTIE = ICI / "phase2.jsonl"
DOSSIER = ICI / "fichiers"
AGENT = "voight-kampff-releve/0.1 (https://github.com/TheDarkMac/AI-detector)"
GRAINE = 32
JPEG = 1000
PNG = 300
PAR_COMPTE = 3
LARGEUR_MIN = 1000
HAUTEUR_RENDU_MIN = 128
TAILLE_MAX = 20 << 20
ATTENTE = 2.0
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png"}


def choisir(fiches: list[Fiche]) -> list[Fiche]:
    """Fichiers à télécharger, dans un ordre fixe : déclarés, puis authentiques tirés."""
    vus: set[str] = set()
    uniques = []
    for fiche in fiches:
        if fiche["nom"] not in vus:
            vus.add(fiche["nom"])
            uniques.append(fiche)
    declares = sorted(
        (f for f in uniques if f["liste"] == "declare" and (f["taille"] or 0) <= TAILLE_MAX),
        key=lambda f: f["nom"],
    )
    candidats = sorted(
        (
            f
            for f in uniques
            if f["liste"] == "authentique"
            and f["rendu"]
            and (f["largeur"] or 0) >= LARGEUR_MIN
            and 960 * (f["hauteur"] or 0) >= HAUTEUR_RENDU_MIN * f["largeur"]
        ),
        key=lambda f: f["nom"],
    )
    hasard = random.Random(GRAINE)  # noqa: S311 (tirage reproductible, pas de la cryptographie)
    hasard.shuffle(candidats)
    retenus: list[Fiche] = []
    par_compte: dict[str, int] = {}
    restants = {"image/jpeg": JPEG, "image/png": PNG}
    for fiche in candidats:
        compte = fiche["compte"] or ""
        if restants[fiche["type"]] and par_compte.get(compte, 0) < PAR_COMPTE:
            retenus.append(fiche)
            restants[fiche["type"]] -= 1
            par_compte[compte] = par_compte.get(compte, 0) + 1
    return declares + retenus


def telecharger(adresse: str) -> tuple[int, bytes]:
    essai = 0
    while True:
        essai += 1
        # Adresses https de Commons, rendues par son API : aucun autre schéma possible.
        requete = urllib.request.Request(adresse, headers={"User-Agent": AGENT})  # noqa: S310
        try:
            with urllib.request.urlopen(requete, timeout=120) as reponse:  # noqa: S310
                return reponse.status, reponse.read()
        except urllib.error.HTTPError as erreur:
            if erreur.code in {404, 410, 400}:
                return erreur.code, b""
            attente = min(300, 10 * essai)
            if erreur.headers.get("Retry-After"):
                attente = max(attente, int(erreur.headers["Retry-After"]))
            print(f"erreur {erreur!r}, attente {attente} s", file=sys.stderr, flush=True)
            time.sleep(attente)
        except (OSError, http.client.HTTPException) as erreur:
            attente = min(300, 10 * essai)
            print(f"erreur {erreur!r}, attente {attente} s", file=sys.stderr, flush=True)
            time.sleep(attente)


def main() -> None:
    fiches = [json.loads(ligne) for ligne in ENTREE.read_text(encoding="utf-8").splitlines()]
    faits = set()
    if SORTIE.exists():
        lignes = SORTIE.read_text(encoding="utf-8").splitlines()
        faits = {json.loads(ligne)["nom"] for ligne in lignes}
    choisis = choisir(fiches)
    print(f"{len(choisis)} fichiers choisis, {len(faits)} déjà faits", flush=True)
    with SORTIE.open("a", encoding="utf-8") as sortie:
        for rang, fiche in enumerate(choisis):
            if fiche["nom"] in faits:
                continue
            adresse = fiche["adresse"] if fiche["liste"] == "declare" else fiche["rendu"]
            statut, contenu = telecharger(adresse)
            chemin = None
            empreinte = None
            if statut == 200 and contenu:
                empreinte = hashlib.sha256(contenu).hexdigest()
                dossier = DOSSIER / fiche["liste"]
                dossier.mkdir(parents=True, exist_ok=True)
                fichier = dossier / f"{rang:05d}.{EXTENSIONS[fiche['type']]}"
                fichier.write_bytes(contenu)
                chemin = str(fichier.relative_to(ICI))
            enregistrement = {
                **fiche,
                "telecharge": adresse,
                "statut": statut,
                "chemin": chemin,
                "sha256": empreinte,
                "octets": len(contenu),
            }
            sortie.write(json.dumps(enregistrement, ensure_ascii=False) + "\n")
            sortie.flush()
            if rang % 50 == 0:
                print(f"{rang} / {len(choisis)}", flush=True)
            time.sleep(ATTENTE)


if __name__ == "__main__":
    main()
