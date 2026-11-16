"""Phase 2 du relevé du complément de T40 : en-têtes JPEG des candidats retenus en phase 1.

Choisit les candidats dans ``phase1.jsonl`` (``choisir``), lit les 128 premiers Kio de chaque
original sur upload.wikimedia.org (davantage si les tables sont plus loin), une requête toutes
les 3 s, ``Retry-After`` respecté, et écrit dans ``phase2.jsonl`` : tables en vigueur au premier
balayage, empreinte (ADR-0181) et encodeur reconnu par le module ``image``, segment SOF, contenu
brut de la ressource Photoshop 0x0406 et du segment APP14 (Adobe). Reprend là où il s'est
arrêté ; relit ``phase1.jsonl`` tant que la phase 1 n'a pas fini.
"""

from __future__ import annotations

import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from voight_kampff.modules.image import empreinte_tables, encodeur

type Fiche = dict[str, Any]
"""Un enregistrement JSON du relevé."""

ICI = Path(__file__).resolve().parent
PHASE1 = ICI / "phase1.jsonl"
PHASE1_ETAT = ICI / "phase1.etat.json"
SORTIE = ICI / "phase2.jsonl"
AGENT = "voight-kampff-releve/0.1 (https://github.com/TheDarkMac/AI-detector)"
PAS = 3.0
PREMIER = 32768
MORCEAU = 131072
MAXIMUM = 1048576

EDITEURS = re.compile(
    r"photoshop|lightroom|gimp|paint|viewnx|capture nx|photo viewer|picasa|acdsee|affinity|"
    r"capture one|dxo|darktable|rawtherapee|iphoto|photos|aperture|irfanview|xnview|"
    r"photoscape|snapseed|faststone|digikam|luminar|shotwell|corel|paintshop|pixelmator|"
    r"windows|mac os|imagemagick|exiftool|photomatix|hugin|ptgui|microsoft|google|"
    r"silkypix|dpp|digital photo professional|zoner|camera raw|on1|perfectly clear|"
    r"skylum|polarr|vsco|instagram|picmonkey|canva|fotor|photoworks",
    re.IGNORECASE,
)
PHOTOSHOP = re.compile(r"^Adobe Photoshop (CS\d?|CC|\d|Elements)", re.IGNORECASE)
EXCLU_PHOTOSHOP = re.compile(r"lightroom|elements|camera raw|express", re.IGNORECASE)

PLAFOND = {"photoshop": 1800, "appareil": 1000, "controle": 500}
PAR_COMPTE = {"photoshop": 2, "controle": 2}
PAR_MODELE = 8
PAR_MODELE_ET_COMPTE = 3


def famille(fiche: Fiche) -> str | None:
    logiciel = (fiche.get("software") or "").strip()
    if PHOTOSHOP.match(logiciel) and not EXCLU_PHOTOSHOP.search(logiciel):
        return "photoshop"
    marque, modele = (fiche.get("make") or "").strip(), (fiche.get("model") or "").strip()
    if marque and modele and not EDITEURS.search(logiciel):
        date, originale = fiche.get("datetime"), fiche.get("datetimeoriginal")
        if date and originale and date != originale:
            return None
        px, py = fiche.get("pixelxdimension"), fiche.get("pixelydimension")
        if px and py:
            try:
                if {int(px), int(py)} != {fiche["largeur"], fiche["hauteur"]}:
                    return None
            except (TypeError, ValueError):
                return None
        return "appareil"
    if logiciel and EDITEURS.search(logiciel):
        return "controle"
    return None


def choisir(deja: set[str]) -> list[tuple[str, Fiche]]:
    """Candidats dans l'ordre de phase1.jsonl, sous les plafonds (comptés sur tout ce qui est lu).

    Appareils : seuls les modèles qui ont, en phase 1, au moins 3 fichiers éligibles versés par
    au moins 2 comptes ; les fichiers déjà lus comptent toujours dans les plafonds.
    """
    comptes: Counter[tuple[str, str]] = Counter()
    familles: Counter[str] = Counter()
    modeles: Counter[str] = Counter()
    modeles_comptes: Counter[tuple[str, str]] = Counter()
    choisis = []
    vus = set()
    fiches = []
    with PHASE1.open(encoding="utf-8") as entree:
        for ligne in entree:
            try:
                fiche = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            if fiche["nom"] in vus:
                continue
            vus.add(fiche["nom"])
            fiches.append((famille(fiche), fiche))
    # Modèles retenus : au moins 3 fichiers éligibles versés par au moins 2 comptes en phase 1.
    fichiers_modele: Counter[str] = Counter()
    comptes_modele: defaultdict[str, set[str]] = defaultdict(set)
    for nature, fiche in fiches:
        if nature == "appareil":
            modele = f"{fiche['make'].strip()} | {fiche['model'].strip()}"
            fichiers_modele[modele] += 1
            comptes_modele[modele].add(fiche.get("compte") or "")
    populaires = {m for m, n in fichiers_modele.items() if n >= 3 and len(comptes_modele[m]) >= 2}
    for nature, fiche in fiches:
        if nature is None or familles[nature] >= PLAFOND[nature]:
            continue
        compte = fiche.get("compte") or ""
        if nature in PAR_COMPTE and comptes[(nature, compte)] >= PAR_COMPTE[nature]:
            continue
        if nature == "appareil":
            modele = f"{fiche['make'].strip()} | {fiche['model'].strip()}"
            if fiche["nom"] not in deja and (
                modele not in populaires
                or modeles[modele] >= PAR_MODELE
                or modeles_comptes[(modele, compte)] >= PAR_MODELE_ET_COMPTE
            ):
                continue
            modeles[modele] += 1
            modeles_comptes[(modele, compte)] += 1
        comptes[(nature, compte)] += 1
        familles[nature] += 1
        if fiche["nom"] not in deja:
            choisis.append((nature, fiche))
    # Contrôles en dernier : ils ne servent qu'à chercher des collisions.
    return sorted(choisis, key=lambda choix: choix[0] == "controle")


def lire(adresse: str, debut: int, fin: int) -> bytes:
    essai = 0
    while True:
        essai += 1
        # Adresses https d'upload.wikimedia.org, données par l'API : aucun autre schéma.
        requete = urllib.request.Request(  # noqa: S310
            adresse, headers={"User-Agent": AGENT, "Range": f"bytes={debut}-{fin}"}
        )
        try:
            with urllib.request.urlopen(requete, timeout=60) as reponse:  # noqa: S310
                lu: bytes = reponse.read()
                return lu
        except urllib.error.HTTPError as erreur:
            if erreur.code == 416:
                return b""
            attente = max(min(300.0, PAS * 4 * essai), int(erreur.headers.get("Retry-After") or 0))
            if erreur.code == 404:
                raise
        except (OSError, http.client.HTTPException) as erreur:
            attente = min(300.0, PAS * 4 * essai)
            print(f"erreur {erreur!r}", file=sys.stderr, flush=True)
        time.sleep(attente)


def analyser(donnees: bytes) -> Fiche:
    """Segments jusqu'au premier SOS ; ``incomplet`` si les données s'arrêtent avant."""
    if donnees[:2] != b"\xff\xd8":
        return {"erreur": "pas un JPEG"}
    tables: dict[int, tuple[bool, tuple[int, ...]]] = {}
    resultat: Fiche = {"sof": None, "app14": None, "r0406": None, "incomplet": True}
    position = 2
    while position + 4 <= len(donnees):
        if donnees[position] != 0xFF:
            return {**resultat, "erreur": f"marqueur attendu à {position}"}
        marqueur = donnees[position + 1]
        if marqueur == 0xFF:
            position += 1
            continue
        if marqueur in (0x01, *range(0xD0, 0xD8)):
            position += 2
            continue
        longueur = int.from_bytes(donnees[position + 2 : position + 4], "big")
        corps = donnees[position + 4 : position + 2 + longueur]
        if len(corps) < longueur - 2:
            break
        if marqueur == 0xDA:
            resultat["incomplet"] = False
            break
        if marqueur == 0xDB:
            p = 0
            while p < len(corps):
                precision, identifiant = corps[p] >> 4, corps[p] & 0x0F
                taille = 128 if precision else 64
                octets = corps[p + 1 : p + 1 + taille]
                valeurs = (
                    tuple(int.from_bytes(octets[i : i + 2], "big") for i in range(0, 128, 2))
                    if precision
                    else tuple(octets)
                )
                tables[identifiant] = (bool(precision), valeurs)
                p += 1 + taille
        elif marqueur in (0xC0, 0xC1, 0xC2, 0xC3, 0xC9, 0xCA, 0xCB):
            composantes = corps[5] if len(corps) > 5 else 0
            echantillonnage = [
                (corps[6 + 3 * i], corps[7 + 3 * i], corps[8 + 3 * i])
                for i in range(composantes)
                if len(corps) >= 9 + 3 * i
            ]
            resultat["sof"] = {"marqueur": marqueur, "composantes": echantillonnage}
        elif marqueur == 0xEE and corps.startswith(b"Adobe"):
            resultat["app14"] = corps.hex()
        elif marqueur == 0xED and corps.startswith(b"Photoshop 3.0\x00"):
            p = 14
            while p + 12 <= len(corps) and corps[p : p + 4] == b"8BIM":
                ressource = int.from_bytes(corps[p + 4 : p + 6], "big")
                nom = corps[p + 6]
                p += 6 + ((nom + 2) & ~1)
                taille = int.from_bytes(corps[p : p + 4], "big")
                contenu = corps[p + 4 : p + 4 + taille]
                if ressource == 0x0406:
                    resultat["r0406"] = contenu.hex()
                p += 4 + taille + (taille & 1)
        position += 2 + longueur
    if tables:
        resultat["tables"] = {str(k): [v[0], list(v[1])] for k, v in sorted(tables.items())}
        resultat["empreinte"] = empreinte_tables(tables)
        resultat["encodeur"] = encodeur(tables)
    return resultat


def phase1_finie() -> bool:
    return ETAT_FINI.exists() or (
        PHASE1_ETAT.exists() and len(json.loads(PHASE1_ETAT.read_text())) >= 216
    )


ETAT_FINI = ICI / "phase1.fini"


def main() -> None:
    deja = set()
    if SORTIE.exists():
        with SORTIE.open(encoding="utf-8") as entree:
            deja = {json.loads(ligne)["nom"] for ligne in entree if ligne.strip()}
    with SORTIE.open("a", encoding="utf-8") as sortie:
        while True:
            fini = phase1_finie()
            candidats = choisir(deja)
            if not candidats:
                if fini:
                    break
                time.sleep(120)
                continue
            for nature, fiche in candidats:
                donnees = b""
                resultat: Fiche = {"erreur": "non lu"}
                try:
                    while len(donnees) < MAXIMUM:
                        fin = (len(donnees) + MORCEAU if donnees else PREMIER) - 1
                        morceau = lire(fiche["adresse"], len(donnees), fin)
                        time.sleep(PAS)
                        attendu = fin + 1 - len(donnees)
                        donnees += morceau
                        resultat = analyser(donnees)
                        if not resultat.get("incomplet") or len(morceau) < attendu:
                            break
                except urllib.error.HTTPError as erreur:
                    resultat = {"erreur": f"HTTP {erreur.code}"}
                    time.sleep(PAS)
                sortie.write(
                    json.dumps({"nature": nature, **fiche, **resultat}, ensure_ascii=False) + "\n"
                )
                sortie.flush()
                deja.add(fiche["nom"])
            print(f"{len(deja)} en-têtes lus", flush=True)


if __name__ == "__main__":
    main()
