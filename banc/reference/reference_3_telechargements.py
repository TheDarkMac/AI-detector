"""Phase 3 du corpus de référence (T100) : téléchargement des originaux choisis en phase 2.

Pour chaque ligne de ``choix.jsonl`` :

- Commons et data.gouv.fr : l'original tel que la source le sert, vérifié par l'empreinte SHA-1
  que la source publie quand elle en publie une ; un fichier dont l'empreinte diffère est écarté ;
- Wikipédia : le texte de la révision choisie, rendu par l'API (``action=parse``), dont on garde
  les paragraphes, sans tableaux, notes ni références, jusqu'à :data:`TEXTE_MAX` caractères,
  écrit en UTF-8 avec des fins de ligne LF.

Les fichiers vont sous ``authentiques/`` et ``generes/`` (hors du dépôt) ;
``telechargements.jsonl`` garde, pour chacun, le statut, l'empreinte SHA-256 et la taille.
Une requête toutes les :data:`ATTENTE` secondes ; arrêt au-delà de :data:`PLAFOND` octets en tout
(volume annoncé à TheDarkMac) ; reprend là où il s'est arrêté (par l'identifiant).
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from html.parser import HTMLParser

from banc.reference.reference_commun import (
    ICI,
    Fiche,
    appeler,
    ecrire_jsonl,
    lire_jsonl,
    obtenir,
)

ENTREE = ICI / "choix.jsonl"
SORTIE = ICI / "telechargements.jsonl"
WIKIPEDIA = "https://fr.wikipedia.org/w/api.php"
ATTENTE = 2.0
PLAFOND = 8 << 30
"""Huit Gio en tout : le haut de l'estimation donnée à TheDarkMac (4 à 8 Go)."""
MARGE = 1 << 20
TEXTE_MAX = 6000
IGNORES = frozenset({"table", "style", "script", "sup", "math", "figure", "ol", "ul", "dl"})
"""Éléments dont le texte n'est pas gardé : tableaux, notes, formules, listes, légendes."""
MARQUES = ("mw-ref", "reference", "noprint", "mw-empty-elt", "metadata")
VIDES = frozenset({"br", "img", "hr", "wbr", "input", "meta", "link", "area", "source"})


class Paragraphes(HTMLParser):
    """Texte des paragraphes ``<p>`` d'une page rendue, hors des éléments de :data:`IGNORES` et
    de ceux que MediaWiki marque comme notes ou éléments non imprimés."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphes: list[str] = []
        self._courant: list[str] | None = None
        self._pile: list[str] = []
        """Élément ignoré en cours, répété pour chaque élément du même nom qu'il contient."""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class") or ""
        if self._pile:
            if tag == self._pile[-1]:
                self._pile.append(tag)
        elif tag in IGNORES or any(marque in classes for marque in MARQUES):
            if tag not in VIDES:
                self._pile.append(tag)
        elif tag == "p":
            self._courant = []
        elif tag == "br" and self._courant is not None:
            self._courant.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._pile:
            if tag == self._pile[-1]:
                self._pile.pop()
        elif tag == "p" and self._courant is not None:
            texte = re.sub(r"[ \t\r\n]+", " ", "".join(self._courant)).strip()
            if texte:
                self.paragraphes.append(texte)
            self._courant = None

    def handle_data(self, data: str) -> None:
        if self._courant is not None and not self._pile:
            self._courant.append(data)


def texte_wikipedia(revision: int) -> bytes | None:
    donnees = appeler(
        WIKIPEDIA,
        {
            "action": "parse",
            "format": "json",
            "formatversion": "2",
            "oldid": str(revision),
            "prop": "text",
            "disablelimitreport": "1",
            "disableeditsection": "1",
            "disabletoc": "1",
        },
    )
    lecteur = Paragraphes()
    lecteur.feed(donnees["parse"]["text"])
    lecteur.close()
    gardes: list[str] = []
    longueur = 0
    for paragraphe in lecteur.paragraphes:
        if longueur + len(paragraphe) > TEXTE_MAX and gardes:
            break
        gardes.append(html.unescape(paragraphe))
        longueur += len(paragraphe) + 2
    texte = "\n\n".join(gardes).strip()
    if len(texte) < 500:
        return None
    return (texte + "\n").encode("utf-8")


def telecharger(choix: Fiche) -> tuple[int, bytes, str]:
    """Statut, contenu et raison d'un écart (vide si aucun)."""
    if choix["source"] == "wikipedia":
        try:
            contenu = texte_wikipedia(int(choix["revision"]))
        except RuntimeError:
            # Révision masquée ou supprimée depuis la phase 1 (« permissiondenied »,
            # « nosuchrevision ») : le texte est écarté, la phase continue.
            return 0, b"", "révision illisible"
        if contenu is None:
            return 200, b"", "texte trop court"
        return 200, contenu, ""
    plafond = int(choix.get("taille") or 10 << 20) + MARGE
    statut, contenu = obtenir(choix["adresse"], plafond=plafond)
    time.sleep(ATTENTE)
    if statut != 200 or not contenu:
        return statut, b"", "non servi"
    controle = choix.get("controle")
    if controle and hashlib.sha1(contenu).hexdigest() != controle["valeur"].lower():  # noqa: S324
        return statut, b"", "empreinte SHA-1 différente de la source"
    return statut, contenu, ""


def main() -> None:
    faits = {fiche["id"]: fiche for fiche in lire_jsonl(SORTIE)}
    volume = sum(int(f.get("octets") or 0) for f in faits.values())
    choix = list(lire_jsonl(ENTREE))
    print(f"{len(choix)} choisis, {len(faits)} déjà faits, {volume} octets", flush=True)
    with SORTIE.open("a", encoding="utf-8") as sortie:
        for rang, fiche in enumerate(choix):
            if fiche["id"] in faits:
                continue
            if volume >= PLAFOND:
                print(f"plafond de {PLAFOND} octets atteint au rang {rang}", flush=True)
                break
            statut, contenu, ecart = telecharger(fiche)
            empreinte = None
            if contenu:
                chemin = ICI.joinpath(*fiche["chemin"].split("/"))
                chemin.parent.mkdir(parents=True, exist_ok=True)
                chemin.write_bytes(contenu)
                empreinte = hashlib.sha256(contenu).hexdigest()
                volume += len(contenu)
            ecrire_jsonl(
                sortie,
                {
                    "id": fiche["id"],
                    "statut": statut,
                    "ecart": ecart,
                    "sha256": empreinte,
                    "octets": len(contenu),
                },
            )
            if rang % 50 == 0:
                print(f"{rang} / {len(choix)}, {volume} octets", flush=True)
    print(json.dumps({"volume": volume}), flush=True)


if __name__ == "__main__":
    main()
