"""Outils partagés des scripts de constitution du corpus de référence (T100).

Requêtes HTTPS vers les seules sources retenues (ADR-0272), avec un ``User-Agent`` qui nomme le
dépôt, sans donnée personnelle ; reprise après une coupure du réseau ; lecture bornée.
Les scripts se lancent depuis la racine du dépôt (``python -m banc.reference.reference_1_listes``…),
dans l'ordre de leur numéro, avec l'interpréteur de l'environnement du projet.
"""

from __future__ import annotations

import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

type Fiche = dict[str, Any]
"""Un enregistrement JSON des listes, choix et fichiers produits."""

ICI = Path(__file__).resolve().parent
AGENT = "voight-kampff-corpus/0.1 (https://github.com/TheDarkMac/AI-detector)"
DATE_LIMITE = "2022-08-22"
"""Publication de Stable Diffusion 1 : un fichier versé ou écrit avant n'est pas généré par les
générateurs diffusés depuis (même borne que le relevé de T32, ADR-0204)."""
HOTES = frozenset(
    {
        "commons.wikimedia.org",
        "upload.wikimedia.org",
        "fr.wikipedia.org",
        "www.data.gouv.fr",
        "static.data.gouv.fr",
    }
)
"""Seules sources du corpus (ADR-0272) : toute autre adresse est refusée avant la requête."""
GRAINE = 100
"""Graine de tous les tirages du corpus (choix des fichiers, parties, dérivés)."""


PASSAGERES = frozenset({"maxlag", "ratelimited", "readonly", "internal_api_error_DBQueryError"})
"""Erreurs d'une API MediaWiki qui passent d'elles-mêmes : l'appel est refait après une attente
croissante (jusqu'à 10 minutes), comme les erreurs « *-too-busy-error » de la recherche."""


class AdresseRefusee(ValueError):
    """Adresse hors des sources retenues."""


def verifier_adresse(adresse: str) -> str:
    morceaux = urllib.parse.urlsplit(adresse)
    if morceaux.scheme != "https" or morceaux.hostname not in HOTES:
        raise AdresseRefusee(adresse)
    return adresse


class _Redirections(urllib.request.HTTPRedirectHandler):
    """Ne suit une redirection que vers une des sources retenues (ADR-0272)."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        verifier_adresse(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OUVREUR = urllib.request.build_opener(_Redirections)


def sans_suivi(adresse: str) -> str:
    """Adresse sans ses paramètres de suivi (``utm_*``), que l'API de Commons ajoute."""
    morceaux = urllib.parse.urlsplit(adresse)
    parametres = [
        (cle, valeur)
        for cle, valeur in urllib.parse.parse_qsl(morceaux.query, keep_blank_values=True)
        if not cle.startswith("utm_")
    ]
    return urllib.parse.urlunsplit(morceaux._replace(query=urllib.parse.urlencode(parametres)))


def obtenir(adresse: str, *, plafond: int, delai: float = 120) -> tuple[int, bytes]:
    """Statut et contenu ; réessaie sans fin après une erreur passagère.

    Un contenu de plus de ``plafond`` octets est abandonné (statut 413) : rien n'est lu au-delà.
    Une redirection hors des sources retenues n'est pas suivie (statut 0).
    """
    verifier_adresse(adresse)
    essai = 0
    while True:
        essai += 1
        # Adresse https d'une des sources retenues, vérifiée ci-dessus.
        requete = urllib.request.Request(adresse, headers={"User-Agent": AGENT})  # noqa: S310
        try:
            with _OUVREUR.open(requete, timeout=delai) as reponse:
                contenu = reponse.read(plafond + 1)
                if len(contenu) > plafond:
                    return 413, b""
                return reponse.status, contenu
        except AdresseRefusee:
            # Redirection hors des sources retenues : rien n'est demandé à l'autre adresse.
            return 0, b""
        except urllib.error.HTTPError as erreur:
            if erreur.code in {400, 403, 404, 410}:
                return erreur.code, b""
            attente = min(300, 10 * essai)
            if erreur.headers.get("Retry-After", "").isdigit():
                attente = max(attente, int(erreur.headers["Retry-After"]))
            print(f"erreur {erreur!r}, attente {attente} s", file=sys.stderr, flush=True)
            time.sleep(attente)
        except (OSError, http.client.HTTPException) as erreur:
            attente = min(300, 10 * essai)
            print(f"erreur {erreur!r}, attente {attente} s", file=sys.stderr, flush=True)
            time.sleep(attente)


def appeler(api: str, parametres: dict[str, str]) -> Fiche:
    """Appel d'une API JSON (MediaWiki ou data.gouv.fr), une seconde au moins entre deux appels."""
    adresse = api + "?" + urllib.parse.urlencode(parametres)
    occupe = 0
    while True:
        statut, contenu = obtenir(adresse, plafond=64 << 20)
        if statut != 200:
            raise RuntimeError(f"{adresse} : statut {statut}")
        try:
            donnees: Fiche = json.loads(contenu)
        except json.JSONDecodeError:
            print("réponse illisible, nouvel essai dans 30 s", file=sys.stderr, flush=True)
            time.sleep(30)
            continue
        erreur = donnees.get("error") if isinstance(donnees, dict) else None
        if erreur:
            code = str(erreur.get("code", "")) if isinstance(erreur, dict) else ""
            if code in PASSAGERES or code.endswith("-too-busy-error"):
                occupe += 1
                attente = min(600, 30 * occupe)
                print(f"{code}, attente {attente} s", file=sys.stderr, flush=True)
                time.sleep(attente)
                continue
            raise RuntimeError(erreur)
        time.sleep(1)
        return donnees


def lire_jsonl(chemin: Path) -> Iterator[Fiche]:
    if chemin.exists():
        with chemin.open(encoding="utf-8") as entree:
            for ligne in entree:
                if ligne.strip():
                    yield json.loads(ligne)


def ecrire_jsonl(sortie: Any, fiche: Fiche) -> None:
    sortie.write(json.dumps(fiche, ensure_ascii=False, sort_keys=True) + "\n")
    sortie.flush()
