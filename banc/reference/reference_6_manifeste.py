"""Phase 6 du corpus de référence (T100) : manifeste ``corpus.toml`` (ADR-0103, ADR-0276).

Rassemble les originaux téléchargés (phases 2 et 3) et les dérivés produits (phases 4 et 5),
calcule l'empreinte SHA-256 de chaque fichier présent, écarte un fichier dont le contenu est
déjà au corpus (le banc refuse deux fois le même contenu), puis écrit le manifeste, le relit par
le banc (:func:`banc.corpus.charger`) et vérifie chaque empreinte comme le banc le fera.

Écrit aussi ``effectifs.json`` : nombre de fichiers par catégorie, partie, famille et format, et
les fichiers écartés avec leur raison.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from banc.corpus import charger
from banc.reference.reference_commun import ICI, Fiche, lire_jsonl

CHOIX = ICI / "choix.jsonl"
TELECHARGEMENTS = ICI / "telechargements.jsonl"
DERIVES = ICI / "derives.jsonl"
RESULTATS_UNO = ICI / "uno.resultats.json"
MANIFESTE = ICI / "corpus.toml"
EFFECTIFS = ICI / "effectifs.json"
VERSION = "1.0.0"
TEXTE_MAX = 1024
DESCRIPTION = (
    "Corpus de référence de T100 : originaux libres de Wikimedia Commons (images, PDF, audio, "
    "vidéo), de data.gouv.fr (DOCX, ODT) et de Wikipédia (textes), versés ou écrits avant le "
    "2022-08-22 ; images déclarées générées par une IA sur Commons et textes écrits par "
    "l'assistant ; transformés, retouchés et malformés fabriqués sur le poste par les scripts "
    "de banc/reference/. Un original sur trois en calibrage, avec ses dérivés."
)


def empreinte(chemin: Path) -> str:
    resultat = hashlib.sha256()
    with chemin.open("rb") as fichier:
        while bloc := fichier.read(1 << 20):
            resultat.update(bloc)
    return resultat.hexdigest()


def tronquer(texte: str) -> str:
    return texte if len(texte) <= TEXTE_MAX else texte[: TEXTE_MAX - 1] + "…"


def jour(horodatage: str | None, defaut: str) -> str:
    return (horodatage or defaut)[:10]


def chaine(texte: str) -> str:
    """Chaîne TOML de base, échappée."""
    return json.dumps(texte, ensure_ascii=False)


def provenance_originale(choix: Fiche, aujourdhui: str) -> Fiche:
    provenance: Fiche = {
        "licence": tronquer(str(choix["licence"])),
        "date": jour(choix.get("versement"), aujourdhui),
    }
    if choix["source"] == "commons":
        provenance["source"] = tronquer(str(choix["page"]))
        remarque = f"Original de Wikimedia Commons, versé le {provenance['date']}"
    elif choix["source"] == "datagouv":
        provenance["source"] = tronquer(f"{choix['page']} (ressource {choix['nom']})")
        remarque = f"Ressource de data.gouv.fr, versée le {provenance['date']}"
    else:
        provenance["source"] = str(choix["page"])
        remarque = (
            f"Paragraphes de l'article « {choix['nom']} » de Wikipédia, révision du "
            f"{provenance['date']}, texte rendu par l'API"
        )
    if choix["categorie"] == "genere":
        provenance["generateur"] = tronquer(str(choix["generateur"]))
        remarque += " ; origine IA déclarée par ses catégories, non vérifiée"
    provenance["remarque"] = tronquer(remarque + f" ; obtenu le {aujourdhui}")
    return provenance


def provenance_derivee(derive: Fiche, chemins: dict[str, str], aujourdhui: str) -> Fiche:
    operation = derive["operation"]
    description = derive.get("description") or operation
    outil = derive.get("outil") or "script du corpus"
    if operation == "piege":
        source = (
            f"Fabriqué de toutes pièces par banc/reference/reference_4_derives.py : {description}"
        )
    elif str(derive.get("parent", "")).startswith("textes-ia/"):
        texte = f"banc/reference/{derive['parent']}"
        source = f"Écrit par l'assistant pendant T100 ({texte}) : {description}"
    else:
        parent = chemins.get(derive["parent"], derive["parent"])
        source = f"Dérivé de {parent} : {description} ({outil})"
    provenance: Fiche = {
        "source": tronquer(source),
        "licence": tronquer(str(derive["licence"])),
        "date": aujourdhui,
    }
    if derive.get("generateur"):
        provenance["generateur"] = tronquer(str(derive["generateur"]))
    return provenance


def entree_toml(fiche: Fiche) -> str:
    lignes = ["[[fichiers]]"]
    for cle in (
        "chemin",
        "empreinte",
        "categorie",
        "partie",
        "groupe",
        "origine",
        "transformation",
    ):
        if fiche.get(cle):
            lignes.append(f"{cle} = {chaine(str(fiche[cle]))}")
    provenance = ", ".join(
        f"{cle} = {chaine(str(valeur))}" for cle, valeur in fiche["provenance"].items()
    )
    lignes.append(f"provenance = {{ {provenance} }}")
    return "\n".join(lignes)


def main() -> None:
    aujourdhui = datetime.now(UTC).date().isoformat()
    choix = {f["id"]: f for f in lire_jsonl(CHOIX)}
    telecharges = {f["id"]: f for f in lire_jsonl(TELECHARGEMENTS) if f.get("sha256")}
    uno = json.loads(RESULTATS_UNO.read_text(encoding="utf-8")) if RESULTATS_UNO.exists() else {}
    fiches: list[Fiche] = []
    ecartes: list[Fiche] = []
    chemins = {identifiant: choix[identifiant]["chemin"] for identifiant in telecharges}
    for identifiant in telecharges:
        original = choix[identifiant]
        fiches.append(
            {
                **{
                    cle: original[cle]
                    for cle in ("chemin", "categorie", "partie", "groupe", "origine")
                },
                "famille": original["famille"],
                "format": original["format"],
                "provenance": provenance_originale(original, aujourdhui),
            }
        )
    for derive in lire_jsonl(DERIVES):
        etat = derive.get("etat")
        if etat == "confie":
            resultat = uno.get(derive["chemin"], {})
            etat = resultat.get("etat", "non fait")
            derive = {**derive, "description": resultat.get("description")}
        if etat != "fait":
            ecartes.append({"chemin": derive["chemin"], "raison": f"dérivé {etat}"})
            continue
        fiches.append(
            {
                **{
                    cle: derive.get(cle)
                    for cle in (
                        "chemin",
                        "categorie",
                        "partie",
                        "groupe",
                        "origine",
                        "transformation",
                    )
                },
                "famille": derive["famille"],
                "format": derive["chemin"].rsplit(".", 1)[1],
                "provenance": provenance_derivee(derive, chemins, aujourdhui),
            }
        )
    vues: set[str] = set()
    retenues: list[Fiche] = []
    for fiche in fiches:
        fichier = ICI.joinpath(*fiche["chemin"].split("/"))
        if not fichier.is_file():
            ecartes.append({"chemin": fiche["chemin"], "raison": "fichier absent"})
            continue
        fiche["empreinte"] = empreinte(fichier)
        if fiche["empreinte"] in vues:
            ecartes.append(
                {"chemin": fiche["chemin"], "raison": "même contenu qu'un autre fichier"}
            )
            continue
        vues.add(fiche["empreinte"])
        retenues.append(fiche)
    retenues.sort(key=lambda f: str(f["chemin"]))
    entete = [
        "# Corpus de référence du banc d'évaluation (T100, ADR-0272 à ADR-0276).",
        "#",
        "# Écrit par banc/reference/reference_6_manifeste.py : ne pas modifier à la main. Les",
        "# fichiers ne sont pas au dépôt (droits et volume) ; description : docs/verification/",
        "# corpus-de-reference.md. Aucune partie ne change sans nouvelle version du corpus.",
        "",
        "format = 1",
        'nom = "reference"',
        f"version = {chaine(VERSION)}",
        f"date = {chaine(aujourdhui)}",
        'nature = "reference"',
        f"description = {chaine(DESCRIPTION)}",
    ]
    texte = "\n".join(entete) + "\n\n" + "\n\n".join(map(entree_toml, retenues)) + "\n"
    MANIFESTE.write_text(texte, encoding="utf-8", newline="\n")
    corpus = charger(MANIFESTE)
    for entree in corpus.entrees:
        corpus.verifier(entree)
    effectifs: Counter[str] = Counter()
    for fiche in retenues:
        effectifs[
            f"{fiche['categorie']}|{fiche['partie']}|{fiche['famille']}|{fiche['format']}"
        ] += 1
    EFFECTIFS.write_text(
        json.dumps(
            {
                "version": VERSION,
                "date": aujourdhui,
                "empreinte_manifeste": corpus.empreinte,
                "fichiers": len(corpus.entrees),
                "effectifs": dict(sorted(effectifs.items())),
                "ecartes": ecartes,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{len(corpus.entrees)} fichiers, {len(ecartes)} écartés, empreinte {corpus.empreinte}")


if __name__ == "__main__":
    main()
