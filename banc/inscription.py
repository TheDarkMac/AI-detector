"""Inscription des taux mesurés au catalogue (T101, ADR-0278).

Le guide du catalogue (§5) demande de recopier, pour chaque indice mesuré, le taux, l'effectif et
la borne supérieure que donne le banc, et de régler son niveau sur ce que la borne permet
(ADR-0018, ADR-0101, ADR-0107). Cette commande le fait à partir d'un rapport d'évaluation
publiable, sans rien recopier à la main :

- pour chaque indice dont le module a analysé au moins un fichier de sa population, la table
  ``[regle.evaluation]`` est écrite (ou remplacée), le niveau devient le niveau permis, et la
  version de la règle augmente ;
- les autres règles ne changent pas : une preuve n'a pas de niveau, une information neutre n'a
  pas de taux, un indice sans effectif reste « faible » ;
- le rapport doit avoir été écrit avec ce catalogue (même empreinte) : une seconde inscription
  du même rapport est refusée, puisque la première a changé le catalogue.

Usage, depuis la racine du dépôt : ``python -m banc.inscription EVALUATION.json``, ou
``--catalogue DOSSIER`` pour un autre dossier que le catalogue des sources. L'en-tête du
catalogue (version, date), le registre des versions et l'empreinte restent à mettre à jour
(guide du catalogue, §5).

Les fichiers sont modifiés ligne à ligne, pour garder leur mise en forme et leurs
commentaires, dans une copie du catalogue ; la copie est rechargée par l'outil, qui refuse un
niveau que l'évaluation ne permet pas, et seuls les fichiers modifiés sont recopiés ensuite. Une
inscription refusée ne change donc rien.
"""

import argparse
import json
import re
import shutil
import sys
import tempfile
import tomllib
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes
from voight_kampff._regles import niveau_permis

__all__ = ["Inscription", "InscriptionRefusee", "inscriptions", "inscrire", "main"]

RACINE = Path(__file__).resolve().parent.parent
CATALOGUE = RACINE / "src" / "voight_kampff" / "donnees" / "catalogue"

_ENTETE = re.compile(r"^\[\[?[A-Za-z]")
_REGLE = "[[regle]]"
_EVALUATION = "[regle.evaluation]"


class InscriptionRefusee(ValueError):
    """Rapport non publiable, écrit avec un autre catalogue, ou règle introuvable."""


class Inscription:
    """Évaluation d'un indice, telle qu'elle s'écrit au catalogue."""

    __slots__ = ("borne", "corpus", "date", "effectif", "identifiant", "niveau", "taux")

    def __init__(
        self,
        identifiant: str,
        *,
        taux: float,
        effectif: int,
        borne: float,
        corpus: str,
        date: date,
    ) -> None:
        self.identifiant = identifiant
        self.taux, self.effectif, self.borne = taux, effectif, borne
        self.corpus, self.date = corpus, date
        self.niveau = niveau_permis(borne).value

    def table(self) -> list[str]:
        return [
            _EVALUATION,
            f"taux_faux_positifs = {self.taux!r}",
            f"effectif = {self.effectif}",
            f"borne_superieure = {self.borne!r}",
            f'corpus = "{self.corpus}"',
            f'date = "{self.date.isoformat()}"',
        ]


def inscriptions(document: Mapping[str, Any], empreinte: str) -> list[Inscription]:
    """Inscriptions d'un rapport d'évaluation écrit avec le catalogue d'empreinte ``empreinte``."""
    if not document.get("publiable"):
        raise InscriptionRefusee(
            "rapport non publiable : seule la partie évaluation du corpus de référence fonde un "
            "taux (ADR-0105)"
        )
    catalogue = document["versions"]["catalogue"]
    if catalogue["empreinte"] != empreinte or catalogue["fourni_par_utilisateur"]:
        raise InscriptionRefusee(
            "rapport écrit avec un autre catalogue : relancer le banc avec celui-ci (guide du "
            "catalogue, §5)"
        )
    corpus = f"{document['corpus']['nom']}-{document['corpus']['version']}"
    jour = date.fromisoformat(document["date"][:10])
    resultat = []
    for regle in document["regles"]:
        faux_positifs = regle["faux_positifs"]
        if regle["categorie"] != "indice" or not faux_positifs["effectif"]:
            continue
        resultat.append(
            Inscription(
                regle["identifiant"],
                taux=faux_positifs["valeur"],
                effectif=faux_positifs["effectif"],
                borne=faux_positifs["intervalle"][1],
                corpus=corpus,
                date=jour,
            )
        )
    return resultat


def _blocs(lignes: Sequence[str]) -> list[tuple[int, int]]:
    """Début et fin (exclue) de chaque table ``[[regle]]`` du fichier."""
    debuts = [rang for rang, ligne in enumerate(lignes) if ligne.strip() == _REGLE]
    return list(zip(debuts, [*debuts[1:], len(lignes)], strict=True))


def _remplacer(lignes: list[str], debut: int, fin: int, cle: str, valeur: str) -> None:
    for rang in range(debut, fin):
        if _ENTETE.match(lignes[rang]):
            break
        if lignes[rang].split("=", 1)[0].strip() == cle:
            lignes[rang] = f"{cle} = {valeur}"
            return
    raise InscriptionRefusee(f"clé « {cle} » absente de la règle")


def _inscrire_bloc(lignes: list[str], debut: int, fin: int, inscription: Inscription) -> None:
    """Écrit l'évaluation dans la table de règle ``lignes[debut:fin]``, en place."""
    version = None
    for rang in range(debut + 1, fin):
        if _ENTETE.match(lignes[rang]):
            break
        if lignes[rang].split("=", 1)[0].strip() == "version":
            version = int(tomllib.loads(lignes[rang])["version"])
    if version is None:
        raise InscriptionRefusee(f"{inscription.identifiant} : version absente")
    _remplacer(lignes, debut + 1, fin, "version", f'"{version + 1}"')
    _remplacer(lignes, debut + 1, fin, "niveau", f'"{inscription.niveau}"')
    # Ancienne évaluation retirée, avec la ligne vide qui la suit.
    for rang in range(debut + 1, fin):
        if lignes[rang].strip() == _EVALUATION:
            suite = next(
                (r for r in range(rang + 1, fin) if _ENTETE.match(lignes[r])),
                fin,
            )
            del lignes[rang:suite]
            fin -= suite - rang
            break
    # Nouvelle évaluation : avant la première sous-table, ou à la fin de la règle.
    position = next((r for r in range(debut + 1, fin) if _ENTETE.match(lignes[r])), fin)
    while position > debut + 1 and not lignes[position - 1].strip():
        position -= 1
    lignes[position:position] = ["", *inscription.table()]


def _inscrire_fichier(fichier: Path, restantes: dict[str, Inscription]) -> bool:
    """Inscrit dans ``fichier`` les évaluations de ses règles ; vrai s'il a changé."""
    lignes = fichier.read_text(encoding="utf-8").split("\n")
    modifie = False
    # De la dernière règle à la première : une insertion ne décale pas les précédentes.
    for debut, fin in reversed(_blocs(lignes)):
        identifiants = [
            tomllib.loads(lignes[rang])["identifiant"]
            for rang in range(debut + 1, fin)
            if lignes[rang].split("=", 1)[0].strip() == "identifiant"
        ]
        if identifiants and identifiants[0] in restantes:
            _inscrire_bloc(lignes, debut, fin, restantes.pop(identifiants[0]))
            modifie = True
    if modifie:
        fichier.write_text("\n".join(lignes), encoding="utf-8")
    return modifie


def inscrire(inscriptions_: Sequence[Inscription], dossier: Path | None = None) -> list[str]:
    """Inscrit chaque évaluation dans le fichier de règles de son module ; rend les fichiers
    modifiés, relatifs au dossier du catalogue.

    Lève :class:`InscriptionRefusee` si une règle est introuvable, ``CatalogueInvalide`` si le
    catalogue modifié n'est plus valide ; le catalogue reste alors inchangé.
    """
    dossier = dossier or CATALOGUE
    restantes = {inscription.identifiant: inscription for inscription in inscriptions_}
    with tempfile.TemporaryDirectory() as temporaire:
        copie = Path(temporaire) / "catalogue"
        shutil.copytree(dossier, copie)
        modifies = [
            fichier.relative_to(copie).as_posix()
            for fichier in sorted((copie / "regles").glob("*.toml"))
            if _inscrire_fichier(fichier, restantes)
        ]
        if restantes:
            raise InscriptionRefusee(
                f"règles absentes du catalogue : {', '.join(sorted(restantes))}"
            )
        catalogues.charger(manifestes.decouvrir(), copie)
        for relatif in modifies:
            shutil.copyfile(copie / relatif, dossier / relatif)
    return modifies


def main(argv: Sequence[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python -m banc.inscription",
        description=(
            "Inscrit au catalogue l'évaluation de chaque indice mesuré par un rapport "
            "d'évaluation publiable, et règle son niveau sur ce qu'elle permet (ADR-0278)."
        ),
    )
    analyseur.add_argument("rapport", metavar="EVALUATION.json", help="rapport du banc")
    analyseur.add_argument(
        "--catalogue",
        metavar="DOSSIER",
        help="dossier du catalogue à modifier (par défaut : celui des sources)",
    )
    arguments = analyseur.parse_args(argv)
    dossier = Path(arguments.catalogue) if arguments.catalogue else CATALOGUE
    try:
        document = json.loads(Path(arguments.rapport).read_text(encoding="utf-8"))
        empreinte = catalogues.charger(manifestes.decouvrir(), dossier).version.empreinte
        liste = inscriptions(document, empreinte)
        inscrire(liste, dossier)
    except (OSError, ValueError, KeyError, TypeError) as erreur:
        print(f"inscription : {erreur}", file=sys.stderr)
        return 2
    niveaux = {niveau: sum(i.niveau == niveau for i in liste) for niveau in ("fort", "modere")}
    print(
        f"{len(liste)} indices évalués ; {niveaux['fort']} au niveau « fort », "
        f"{niveaux['modere']} au niveau « modéré », les autres « faible »"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
