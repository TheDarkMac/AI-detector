"""Phase 1 du corpus de référence (T100) : listes de candidats, sans rien télécharger d'autre.

Trois sources (ADR-0272), chacune dans ``listes.<source>.jsonl`` (champ ``source``), et lançables
à part (``--source commons``, ``datagouv`` ou ``wikipedia``), en parallèle : elles ne visent pas
les mêmes serveurs.

- ``commons`` : pour chaque famille de :data:`RECHERCHES`, des appels à la recherche de
  Wikimedia Commons triée au hasard (``gsrsort=random``), 50 fichiers par appel, à la suite
  dans ce tri (décalage ``gsroffset``), avec leur
  licence, leurs catégories, leur empreinte SHA-1 et, pour les images, les champs EXIF qui
  servent au choix (marque, modèle, logiciel, date de prise de vue) ;
- ``datagouv`` : toutes les ressources DOCX et ODT des jeux de données de data.gouv.fr servies
  par ``static.data.gouv.fr``, avec la licence de leur jeu ;
- ``wikipedia`` : des articles de Wikipédia en français tirés au hasard, et leur dernière
  révision antérieure à :data:`~reference_commun.DATE_LIMITE`.

Reprend là où il s'est arrêté (``listes.<source>.etat.json``). Une requête à la fois par source,
une seconde au moins entre deux.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from banc.reference.reference_commun import (
    DATE_LIMITE,
    ICI,
    Fiche,
    appeler,
    ecrire_jsonl,
    sans_suivi,
)

COMMONS = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA = "https://fr.wikipedia.org/w/api.php"
DATAGOUV = "https://www.data.gouv.fr/api/1/datasets/"
PAR_APPEL = 50
EXIF = ("Make", "Model", "Software", "DateTimeOriginal")

RECHERCHES: dict[str, tuple[str, int, bool]] = {
    # famille : (recherche, appels, champs EXIF demandés) ; tailles en Kio. 199 appels au plus :
    # la recherche ne va pas au-delà du 10 000e résultat. PDF, sons et vidéos viennent de peu de
    # comptes : il en faut plus de candidats pour en tirer assez sous le plafond par compte.
    "jpeg": ("filemime:image/jpeg filesize:<8000", 120, True),
    "png": ("filemime:image/png filesize:<8000", 30, True),
    "webp": ("filemime:image/webp filesize:<8000", 40, True),
    "pdf": ("filemime:application/pdf filesize:<6000", 199, False),
    "mp3": ("filemime:audio/mpeg filesize:<5000", 199, False),
    "wav": ("filemime:audio/wav filesize:<5000", 30, False),
    "ogg": ("filemime:application/ogg filesize:<5000", 199, False),
    "flac": ("filemime:audio/flac filesize:<5000", 199, False),
    "webm": ("filemime:video/webm filesize:<5000", 199, False),
    "ia": ('deepcat:"AI-generated images" filesize:<8000', 40, True),
}
FORMATS_BUREAU = ("docx", "odt")
ARTICLES = 1700
"""Articles tirés de Wikipédia : 600 textes retenus au plus, après les articles trop courts ou
créés après la date limite (sur les 1 100 premiers, 950 existaient avant la date limite et 562
avaient au moins 3 000 octets de wikicode)."""
TIRAGES = 4
"""Appels de 500 titres au hasard."""


def fiche_commons(page: Fiche, famille: str) -> Fiche | None:
    infos = (page.get("imageinfo") or [None])[0]
    if not infos or "url" not in infos:
        return None
    meta = infos.get("extmetadata") or {}
    exif = {
        element["name"]: str(element["value"])[:200]
        for element in infos.get("metadata") or []
        if isinstance(element, dict) and element.get("name") in EXIF
    }
    return {
        "source": "commons",
        "famille": famille,
        "nom": page["title"].removeprefix("File:"),
        "page": infos.get("descriptionurl"),
        "adresse": sans_suivi(infos["url"]),
        "compte": infos.get("user"),
        "type": infos.get("mime"),
        "media": infos.get("mediatype"),
        "taille": infos.get("size"),
        "largeur": infos.get("width"),
        "hauteur": infos.get("height"),
        "versement": infos.get("timestamp"),
        "sha1": infos.get("sha1"),
        "licence": (meta.get("LicenseShortName") or {}).get("value"),
        "categories": (meta.get("Categories") or {}).get("value", ""),
        "exif": exif,
    }


def commons(sortie: Any, faits: set[str]) -> None:
    for famille, (recherche, appels, avec_exif) in RECHERCHES.items():
        proprietes = "url|user|mime|mediatype|size|timestamp|sha1|extmetadata"
        if avec_exif:
            proprietes += "|metadata"
        for rang in range(appels):
            etape = f"commons:{famille}:{rang}"
            if etape in faits:
                continue
            donnees = appeler(
                COMMONS,
                {
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "generator": "search",
                    "gsrsearch": recherche,
                    "gsrnamespace": "6",
                    "gsrlimit": str(PAR_APPEL),
                    "gsrsort": "random",
                    # Le tri au hasard de Commons est mis en cache pour une même requête : les
                    # appels se suivent par décalage dans ce tri (au plus 10 000).
                    "gsroffset": str(rang * PAR_APPEL),
                    "prop": "imageinfo",
                    "iiprop": proprietes,
                    "iiextmetadatafilter": "LicenseShortName|Categories",
                    "maxlag": "5",
                },
            )
            for page in donnees.get("query", {}).get("pages", []):
                fiche = fiche_commons(page, famille)
                if fiche is not None:
                    ecrire_jsonl(sortie, fiche)
            marquer(faits, etape)


def datagouv(sortie: Any, faits: set[str]) -> None:
    for format_ in FORMATS_BUREAU:
        page = 1
        while True:
            etape = f"datagouv:{format_}:{page}"
            if etape not in faits:
                donnees = appeler(
                    DATAGOUV, {"format": format_, "page_size": "100", "page": str(page)}
                )
                for jeu in donnees.get("data", []):
                    for ressource in jeu.get("resources", []):
                        if (ressource.get("format") or "").lower() != format_:
                            continue
                        ecrire_jsonl(
                            sortie,
                            {
                                "source": "datagouv",
                                "famille": format_,
                                "nom": ressource.get("title"),
                                "jeu": jeu.get("id"),
                                "page": jeu.get("page"),
                                "ressource": ressource.get("id"),
                                "adresse": ressource.get("url"),
                                "taille": ressource.get("filesize"),
                                "versement": ressource.get("created_at"),
                                "modification": ressource.get("last_modified"),
                                "licence": jeu.get("license"),
                                "compte": (jeu.get("organization") or jeu.get("owner") or {}).get(
                                    "id"
                                ),
                                "controle": ressource.get("checksum"),
                            },
                        )
                marquer(faits, etape)
                if not donnees.get("next_page"):
                    marquer(faits, f"datagouv:{format_}:fin")
            if f"datagouv:{format_}:fin" in faits:
                break
            page += 1


def wikipedia(sortie: Any, faits: set[str]) -> None:
    titres: list[str] = []
    for rang in range(TIRAGES):
        etape = f"wikipedia:hasard:{rang}"
        fichier = ICI / f"listes.hasard{rang}.json"
        if etape not in faits:
            donnees = appeler(
                WIKIPEDIA,
                {
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "list": "random",
                    "rnnamespace": "0",
                    "rnlimit": "500",
                },
            )
            fichier.write_text(json.dumps([p["title"] for p in donnees["query"]["random"]]))
            marquer(faits, etape)
        titres.extend(json.loads(fichier.read_text()))
    uniques = list(dict.fromkeys(titres))[:ARTICLES]
    for titre in uniques:
        etape = f"wikipedia:article:{titre}"
        if etape in faits:
            continue
        donnees = appeler(
            WIKIPEDIA,
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "revisions",
                "titles": titre,
                "rvprop": "ids|timestamp|size",
                "rvlimit": "1",
                "rvstart": f"{DATE_LIMITE}T00:00:00Z",
                "rvdir": "older",
            },
        )
        pages = donnees.get("query", {}).get("pages", [])
        revisions = pages[0].get("revisions") if pages else None
        if revisions:
            revision = revisions[0]
            ecrire_jsonl(
                sortie,
                {
                    "source": "wikipedia",
                    "famille": "texte",
                    "nom": titre,
                    "page": "https://fr.wikipedia.org/w/index.php?oldid=" + str(revision["revid"]),
                    "revision": revision["revid"],
                    "versement": revision["timestamp"],
                    "taille": revision.get("size"),
                    "licence": "CC BY-SA 3.0",
                },
            )
        marquer(faits, etape)


def etat(source: str) -> Path:
    return ICI / f"listes.{source}.etat.json"


ETAT_COURANT: list[Path] = []
"""Fichier d'état de la source en cours."""


def marquer(faits: set[str], etape: str) -> None:
    faits.add(etape)
    ETAT_COURANT[-1].write_text(json.dumps(sorted(faits), ensure_ascii=False))
    print(f"{etape} fait", flush=True)


SOURCES: dict[str, Callable[[Any, set[str]], None]] = {
    "commons": commons,
    "datagouv": datagouv,
    "wikipedia": wikipedia,
}


def main() -> None:
    lecteur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    lecteur.add_argument("--source", choices=sorted(SOURCES), action="append")
    for source in lecteur.parse_args().source or list(SOURCES):
        ETAT_COURANT.append(etat(source))
        faits = set(json.loads(etat(source).read_text())) if etat(source).exists() else set()
        with (ICI / f"listes.{source}.jsonl").open("a", encoding="utf-8") as sortie:
            SOURCES[source](sortie, faits)


if __name__ == "__main__":
    main()
