"""Phase 2 du corpus de référence (T100) : choix des originaux et de leur partie, avant tout
téléchargement et toute mesure (ADR-0016, ADR-0103, ADR-0274).

Lit ``listes.<source>.jsonl`` et écrit ``choix.jsonl``, un original par ligne, dans l'ordre où
la phase 3 les télécharge. Pour chaque format :

1. candidats retenus par les critères d'ADR-0273 : versés ou écrits avant
   :data:`~reference_commun.DATE_LIMITE` pour un authentique ; catégories de Commons qui ne
   disent ni génération ni retouche ; pour un JPEG authentique, marque et modèle d'appareil
   déclarés et aucun logiciel d'édition ; pour un fichier déclaré généré, générateur lu dans ses
   catégories ;
2. tirage au hasard (graine :data:`~reference_commun.GRAINE`), au plus :data:`PAR_COMPTE` fichiers
   par compte (:data:`PAR_COMPTE_FORMAT` pour certains formats), :data:`PAR_APPAREIL` par modèle
   d'appareil, :data:`PAR_GENERATEUR` par générateur, jusqu'à la cible de :data:`CIBLES` ;
3. un original sur trois, dans l'ordre du tirage, en partie calibrage, les autres en évaluation.
   Chaque original est son propre groupe : ses dérivés (phase 4) le suivent dans sa partie.
"""

from __future__ import annotations

import random
import re
from collections import Counter
from itertools import zip_longest

from banc.reference.reference_commun import (
    DATE_LIMITE,
    GRAINE,
    ICI,
    Fiche,
    ecrire_jsonl,
    lire_jsonl,
)

SORTIE = ICI / "choix.jsonl"
PAR_COMPTE = 3
"""Plafond par compte des images authentiques, qui viennent de nombreux comptes."""
PAR_COMPTE_FORMAT = {
    "ia": 10,
    "pdf": 10,
    "mp3": 10,
    "wav": 10,
    "ogg": 10,
    "flac": 10,
    "webm": 10,
    "docx": 50,
    "odt": 50,
}
"""Plafonds plus hauts là où les fichiers viennent de peu de comptes (mesurés sur les listes de
T100, ADR-0273) : trois par compte ne donneraient que 48 FLAC ou 24 DOCX."""
PAR_APPAREIL = 5
PAR_GENERATEUR = 150
TAILLE_ARTICLE_MIN = 3000
"""Octets de wikicode au moins : en deçà, une ébauche donne quelques lignes de texte."""
TAILLE_BUREAU_MAX = 10 << 20

SOURCES = ("commons", "datagouv", "wikipedia")
CIBLES = {
    "jpeg": 600,
    "png": 200,
    "webp": 100,
    "pdf": 600,
    "mp3": 220,
    "wav": 200,
    "ogg": 120,
    "flac": 120,
    "webm": 600,
    "docx": 450,
    "odt": 150,
    # Tous les articles éligibles : un sur six environ donne moins de 500 caractères de
    # paragraphes une fois les tableaux et les listes ôtés (phase 3) ; 600 ne suffisaient pas.
    "texte": 900,
    "ia": 600,
}
FAMILLES = {
    "jpeg": "image",
    "png": "image",
    "webp": "image",
    "ia": "image",
    "pdf": "pdf",
    "mp3": "audio",
    "wav": "audio",
    "ogg": "audio",
    "flac": "audio",
    "webm": "video",
    "docx": "bureau",
    "odt": "bureau",
    "texte": "texte",
}
TYPES = {
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "webp": {"image/webp"},
    "pdf": {"application/pdf"},
    "mp3": {"audio/mpeg"},
    "wav": {"audio/wav", "audio/x-wav"},
    "ogg": {"application/ogg", "audio/ogg"},
    "flac": {"audio/flac", "audio/x-flac"},
    "webm": {"video/webm"},
    "ia": {"image/jpeg", "image/png", "image/webp"},
}
MEDIAS = {"mp3": "AUDIO", "wav": "AUDIO", "ogg": "AUDIO", "flac": "AUDIO", "webm": "VIDEO"}
EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "application/ogg": "ogg",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
    "audio/x-flac": "flac",
    "video/webm": "webm",
}
FORMATS_IA = {"image/jpeg": "jpeg", "image/png": "png", "image/webp": "webp"}
LICENCES_DATAGOUV = {
    "lov2": "Licence Ouverte 2.0",
    "fr-lo": "Licence Ouverte 1.0",
    "cc-by": "CC BY 4.0",
    "cc-by-sa": "CC BY-SA 4.0",
    "cc-zero": "CC0 1.0",
    "odc-odbl": "ODbL 1.0",
    "odc-by": "ODC-By 1.0",
    "odc-pddl": "ODC PDDL 1.0",
}

MOTIF_IA = re.compile(
    r"AI[- ]generated|generated (?:by|with|using)|Stable Diffusion|SDXL|DALL|Midjourney|"
    r"Artificial intelligence|neural network|\bGAN\b|deepfake|text-to-image|Craiyon|FLUX\.1",
    re.IGNORECASE,
)
"""Catégories qui disent une génération : exclues des authentiques."""
MOTIF_RETOUCHE = re.compile(
    r"retouch|photomontage|manipulat|composite|collage|\bedited\b|\bHDR\b|stitch|panoram|"
    r"focus stack|restor|coloriz|colouriz|upscal|enhanc|photoshopped|montage",
    re.IGNORECASE,
)
"""Catégories qui disent une retouche ou un assemblage : exclues des authentiques et des
générés (une photo agrandie ou retouchée par une IA n'est pas générée)."""
MOTIF_EDITEUR = re.compile(
    r"photoshop|lightroom|camera raw|gimp|paint\.net|capture one|darktable|rawtherapee|"
    r"affinity|snapseed|picasa|acdsee|photoscape|luminar|\bdxo\b|\bon1\b|corel|paintshop|"
    r"pixelmator|aperture|iphoto|\bphotos\b|irfanview|xnview|faststone|digikam|shotwell|fotor|"
    r"picmonkey|canva|silkypix|hugin|ptgui|imagemagick|graphicsmagick|lightzone|zoner|polarr|"
    r"vsco|windows photo|photo gallery|krita|inkscape|bridge|preview",
    re.IGNORECASE,
)
"""Logiciels d'édition ou de développement déclarés dans l'EXIF : la photo n'est plus une
capture non retouchée."""
GENERATEURS = (
    (re.compile(r"Craiyon|DALL[-·. ]?E mini", re.IGNORECASE), "Craiyon (DALL-E mini)"),
    (re.compile(r"SDXL|Stable Diffusion XL", re.IGNORECASE), "Stable Diffusion XL"),
    (re.compile(r"Stable Diffusion", re.IGNORECASE), "Stable Diffusion, version non précisée"),
    (re.compile(r"FLUX", re.IGNORECASE), "FLUX.1"),
    (
        re.compile(r"DALL[-·. ]?E ?3|Bing Image Creator|Microsoft Designer", re.IGNORECASE),
        "DALL-E 3",
    ),
    (re.compile(r"DALL[-·. ]?E ?2", re.IGNORECASE), "DALL-E 2"),
    (re.compile(r"DALL[-·. ]?E", re.IGNORECASE), "DALL-E, version non précisée"),
    (re.compile(r"Midjourney", re.IGNORECASE), "Midjourney"),
    (re.compile(r"GPT-4o|ChatGPT|GPT Image", re.IGNORECASE), "GPT-4o ou GPT Image (OpenAI)"),
    (re.compile(r"Imagen|Gemini", re.IGNORECASE), "Imagen ou Gemini (Google)"),
    (re.compile(r"Firefly", re.IGNORECASE), "Adobe Firefly"),
    (re.compile(r"Ideogram", re.IGNORECASE), "Ideogram"),
    (re.compile(r"Leonardo", re.IGNORECASE), "Leonardo.Ai"),
    (re.compile(r"NovelAI", re.IGNORECASE), "NovelAI"),
    (re.compile(r"Grok|Aurora", re.IGNORECASE), "Grok (xAI)"),
    (re.compile(r"WOMBO", re.IGNORECASE), "Dream (WOMBO)"),
    (re.compile(r"Artbreeder", re.IGNORECASE), "Artbreeder"),
    (re.compile(r"StyleGAN|does not exist", re.IGNORECASE), "StyleGAN"),
)
GENERATEUR_INCONNU = "non précisé par la page (rangé parmi les images générées par une IA)"


def generateur(categories: str) -> str:
    for motif, nom in GENERATEURS:
        if motif.search(categories):
            return nom
    return GENERATEUR_INCONNU


def authentique_commons(fiche: Fiche, format_: str) -> bool:
    categories = fiche.get("categories") or ""
    if (
        fiche.get("type") not in TYPES[format_]
        or not fiche.get("licence")
        or not fiche.get("sha1")
        or (fiche.get("versement") or "9999") >= DATE_LIMITE
        or MOTIF_IA.search(categories)
        or MOTIF_RETOUCHE.search(categories)
    ):
        return False
    if format_ in MEDIAS and fiche.get("media") != MEDIAS[format_]:
        return False
    if format_ != "jpeg":
        return True
    exif = fiche.get("exif") or {}
    prise = exif.get("DateTimeOriginal", "")
    return bool(
        exif.get("Make", "").strip()
        and exif.get("Model", "").strip()
        and not MOTIF_EDITEUR.search(exif.get("Software", ""))
        and (not prise or prise.replace(":", "-", 2) < DATE_LIMITE)
    )


def genere_commons(fiche: Fiche) -> bool:
    categories = fiche.get("categories") or ""
    return bool(
        fiche.get("type") in TYPES["ia"]
        and fiche.get("licence")
        and fiche.get("sha1")
        and MOTIF_IA.search(categories)
        and not MOTIF_RETOUCHE.search(categories)
    )


def bureau(fiche: Fiche) -> bool:
    adresse = fiche.get("adresse") or ""
    return bool(
        adresse.startswith("https://static.data.gouv.fr/")
        and fiche.get("licence") in LICENCES_DATAGOUV
        and (fiche.get("versement") or "9999") < DATE_LIMITE
        and (fiche.get("taille") or 0) <= TAILLE_BUREAU_MAX
    )


def article(fiche: Fiche) -> bool:
    return (fiche.get("taille") or 0) >= TAILLE_ARTICLE_MIN


def candidats(fiches: list[Fiche], format_: str) -> list[Fiche]:
    """Candidats retenus d'un format, sans double (nom, adresse, contenu), dans l'ordre du nom."""
    if format_ == "ia":
        retenus = [f for f in fiches if f["source"] == "commons" and f["famille"] == "ia"]
        retenus = [f for f in retenus if genere_commons(f)]
    elif format_ in {"docx", "odt"}:
        retenus = [f for f in fiches if f["source"] == "datagouv" and f["famille"] == format_]
        retenus = [f for f in retenus if bureau(f)]
    elif format_ == "texte":
        retenus = [f for f in fiches if f["source"] == "wikipedia" and article(f)]
    else:
        retenus = [f for f in fiches if f["source"] == "commons" and f["famille"] == format_]
        retenus = [f for f in retenus if authentique_commons(f, format_)]
    vus: set[str] = set()
    uniques = []
    for fiche in sorted(retenus, key=lambda f: (str(f["nom"]), str(f.get("adresse") or ""))):
        controle = fiche.get("sha1") or (fiche.get("controle") or {}).get("value")
        cles = {f"nom:{fiche['nom']}"}
        if fiche.get("adresse"):
            cles.add(f"adresse:{fiche['adresse']}")
        if controle:
            cles.add(f"controle:{controle}")
        if not cles & vus:
            vus |= cles
            uniques.append(fiche)
    return uniques


def tirer(liste: list[Fiche], format_: str, comptes: Counter[str]) -> list[Fiche]:
    """Tirage reproductible jusqu'à la cible, sous les plafonds par compte, appareil, générateur.

    ``comptes`` est partagé entre les formats : le plafond d'un format s'applique à ce que le
    compte a déjà fourni, tous formats confondus.
    """
    hasard = random.Random(f"{GRAINE}:{format_}")  # noqa: S311 (tirage reproductible)
    melange = list(liste)
    hasard.shuffle(melange)
    retenus: list[Fiche] = []
    appareils: Counter[str] = Counter()
    generateurs: Counter[str] = Counter()
    plafond = PAR_COMPTE_FORMAT.get(format_, PAR_COMPTE)
    for fiche in melange:
        if len(retenus) == CIBLES[format_]:
            break
        compte = f"{fiche['source']}:{fiche.get('compte') or fiche['nom']}"
        if format_ == "ia":
            compte = "ia:" + compte
        exif = fiche.get("exif") or {}
        appareil = f"{exif.get('Make', '').strip()}|{exif.get('Model', '').strip()}"
        nom_generateur = generateur(fiche.get("categories") or "") if format_ == "ia" else ""
        if comptes[compte] >= plafond:
            continue
        if format_ == "jpeg" and appareils[appareil] >= PAR_APPAREIL:
            continue
        if format_ == "ia" and generateurs[nom_generateur] >= PAR_GENERATEUR:
            continue
        comptes[compte] += 1
        appareils[appareil] += 1
        generateurs[nom_generateur] += 1
        retenus.append(fiche)
    return retenus


def original(fiche: Fiche, format_: str, rang: int) -> Fiche:
    identifiant = f"{format_}-{rang + 1:04d}"
    partie = "calibrage" if rang % 3 == 0 else "evaluation"
    if format_ == "ia":
        type_ = fiche["type"]
        chemin = f"generes/image/{identifiant}.{EXTENSIONS[type_]}"
        return {
            "id": identifiant,
            "chemin": chemin,
            "categorie": "genere",
            "origine": "ia",
            "famille": "image",
            "format": FORMATS_IA[type_],
            "generateur": generateur(fiche.get("categories") or ""),
            **commun(fiche, partie, identifiant),
        }
    if format_ == "texte":
        extension = "txt"
    elif format_ in {"docx", "odt"}:
        extension = format_
    else:
        extension = EXTENSIONS[fiche["type"]]
    return {
        "id": identifiant,
        "chemin": f"authentiques/{FAMILLES[format_]}/{identifiant}.{extension}",
        "categorie": "authentique",
        "origine": "authentique",
        "famille": FAMILLES[format_],
        "format": format_,
        **commun(fiche, partie, identifiant),
    }


def commun(fiche: Fiche, partie: str, identifiant: str) -> Fiche:
    controle = None
    if fiche.get("sha1"):
        controle = {"type": "sha1", "valeur": fiche["sha1"]}
    elif (fiche.get("controle") or {}).get("type") == "sha1":
        controle = {"type": "sha1", "valeur": fiche["controle"]["value"]}
    licence = fiche.get("licence")
    if fiche["source"] == "datagouv":
        licence = LICENCES_DATAGOUV[str(licence)]
    return {
        "partie": partie,
        "groupe": identifiant,
        "source": fiche["source"],
        "nom": fiche["nom"],
        "page": fiche.get("page"),
        "adresse": fiche.get("adresse"),
        "revision": fiche.get("revision"),
        "licence": licence,
        "versement": fiche.get("versement"),
        "taille": fiche.get("taille"),
        "controle": controle,
        "compte": fiche.get("compte"),
    }


def main() -> None:
    fiches = [f for source in SOURCES for f in lire_jsonl(ICI / f"listes.{source}.jsonl")]
    comptes: Counter[str] = Counter()
    par_format: dict[str, list[Fiche]] = {}
    for format_ in CIBLES:
        liste = candidats(fiches, format_)
        retenus = tirer(liste, format_, comptes)
        par_format[format_] = [original(f, format_, rang) for rang, f in enumerate(retenus)]
        print(f"{format_} : {len(liste)} candidats, {len(retenus)} retenus", flush=True)
    # Téléchargement entrelacé : si le plafond de volume arrête la phase 3, chaque format a sa
    # part, et non les premiers seulement.
    with SORTIE.open("w", encoding="utf-8") as sortie:
        for rangee in zip_longest(*par_format.values()):
            for choix in rangee:
                if choix is not None:
                    ecrire_jsonl(sortie, choix)


if __name__ == "__main__":
    main()
