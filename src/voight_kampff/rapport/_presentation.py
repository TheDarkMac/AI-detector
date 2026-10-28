"""Présentation du rapport : textes, valeurs, signalements, résumé (ADR-0096, ADR-0098).

Commun au résumé du terminal et à l'export HTML. Les textes de l'outil viennent de
``textes.toml`` (ADR-0020) ; les phrases des constats, des règles du catalogue (ADR-0091).
Une valeur d'une catégorie masquée est remplacée par une mention, jamais écrite (ES-13).

Chaque sortie neutralise ce qu'elle écrit, au moment de l'écrire : :func:`neutraliser` montre
sous forme visible les caractères de contrôle et bidirectionnels (ES-12, M-21) ; pour le JSON,
:func:`echapper_json` les écrit en échappements, sans changer les données décodées.
"""

import tomllib
import unicodedata
from collections import Counter
from collections.abc import Collection
from functools import cache
from importlib.resources import files
from typing import Any

from voight_kampff._regles import Regle, remplir
from voight_kampff.analyse import Analyse
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
    Constat,
    Direction,
    EtatTechnique,
    Localisation,
    Niveau,
    NiveauIsolation,
    NonMenee,
    Observation,
    Partie,
    Plage,
    Scalaire,
)

__all__ = [
    "Presentation",
    "echapper_json",
    "etat_partie",
    "libelle",
    "localisation",
    "neutraliser",
    "nombre",
    "octets",
    "texte",
    "textes",
]

_INVISIBLES = frozenset({"Cc", "Cf", "Zl", "Zp"})
"""Contrôle, mise en forme (bidirectionnels, sans chasse, étiquettes), séparateurs de ligne et
de paragraphe : ce qu'un terminal ou un navigateur n'affiche pas tel quel (ES-12)."""


def _invisible(caractere: str) -> bool:
    return unicodedata.category(caractere) in _INVISIBLES


def neutraliser(chaine: str) -> str:
    """Montre chaque caractère invisible ou de contrôle sous la forme ``⟨U+XXXX⟩`` (ES-12)."""
    if chaine.isprintable():  # chemin rapide : aucun caractère de ces catégories
        return chaine
    return "".join(f"⟨U+{ord(c):04X}⟩" if _invisible(c) else c for c in chaine)


def _echappement(caractere: str) -> str:
    point = ord(caractere)
    if point <= 0xFFFF:
        return f"\\u{point:04x}"
    point -= 0x10000  # hors du plan de base : paire de substituts, comme l'écrit JSON
    return f"\\u{0xD800 + (point >> 10):04x}\\u{0xDC00 + (point & 0x3FF):04x}"


def echapper_json(document: str) -> str:
    """Texte JSON dont les caractères invisibles sont écrits ``\\uXXXX`` (ES-12).

    ``json.dumps`` échappe toujours les caractères de contrôle inférieurs à U+0020 dans une
    chaîne : ceux qui restent sont la mise en forme du document, laissée telle quelle. Les
    autres caractères invisibles ne peuvent figurer que dans une chaîne, où l'échappement ne
    change pas la valeur décodée.
    """
    lignes = []
    for ligne in document.split("\n"):
        if not ligne.isprintable():
            ligne = "".join(
                _echappement(c) if ord(c) >= 0x20 and _invisible(c) else c for c in ligne
            )
        lignes.append(ligne)
    return "\n".join(lignes)


@cache
def textes() -> dict[str, Any]:
    """Textes du rapport, lus une fois dans le paquet (ADR-0020)."""
    contenu = (files("voight_kampff.rapport") / "textes.toml").read_text(encoding="utf-8")
    return tomllib.loads(contenu)


def texte(cle: str, **valeurs: object) -> str:
    """Texte de ``textes.toml`` désigné par ``table.cle``, ses ``{nom}`` remplacés.

    Les gabarits sont ceux de l'outil, jamais une donnée du fichier : ``str.format`` y est sûr.
    """
    entree: Any = textes()
    for partie in cle.split("."):
        entree = entree[partie]
    resultat: str = entree.format(**valeurs) if valeurs else entree
    return resultat


def libelle(table: str, valeur: str) -> str:
    """Libellé d'une valeur d'énumération : catégorie, direction, niveau, raison…"""
    resultat: str = textes()[table][valeur]
    return resultat


def _scalaire(valeur: Scalaire) -> str:
    if isinstance(valeur, bool):
        return texte("vrai" if valeur else "faux")
    if isinstance(valeur, str):
        return valeur or texte("texte_vide")
    return repr(valeur)  # entier, ou réel au plus court qui se relit à l'identique


def nombre(entier: int) -> str:
    """Entier groupé par milliers, à la française (espace fine insécable)."""
    return f"{entier:,}".replace(",", "\u202f")


def octets(plage: Plage) -> str:
    return texte("formes.octets", debut=plage.debut, fin=plage.debut + plage.longueur - 1)


def localisation(lieu: Localisation) -> str:
    elements = []
    if lieu.chemin is not None:
        elements.append(texte("formes.chemin", chemin=lieu.chemin))
    if lieu.octets is not None:
        elements.append(octets(lieu.octets))
    if lieu.page is not None:
        elements.append(texte("formes.page", page=lieu.page))
    if lieu.zone is not None:
        zone = lieu.zone
        elements.append(
            texte("formes.zone", x=zone.x, y=zone.y, largeur=zone.largeur, hauteur=zone.hauteur)
        )
    if lieu.intervalle is not None:
        elements.append(
            texte("formes.intervalle", debut=lieu.intervalle.debut, fin=lieu.intervalle.fin)
        )
    return ", ".join(elements)


def etat_partie(partie: Partie) -> str:
    """Analysée ou non, et fin logique : tronquée ou non établie (ADR-0070, ADR-0071)."""
    etats = [texte("formes.analysee" if partie.dans_perimetre else "formes.non_analysee")]
    if partie.tronquee:
        etats.append(texte("formes.tronquee"))
    elif not partie.fin_connue:
        etats.append(texte("formes.fin_inconnue"))
    return ", ".join(etats)


_NIVEAUX_DECROISSANTS = (Niveau.FORT, Niveau.MODERE, Niveau.FAIBLE)


class Presentation:
    """Ce qu'on écrit d'une analyse, selon les catégories masquées (ES-13)."""

    def __init__(self, analyse: Analyse, masquees: Collection[CategorieIdentifiante]) -> None:
        self.analyse = analyse
        self.masquees = frozenset(masquees)
        self._observations = {o.identifiant: o for o in analyse.observations}

    def masquee(self, categorie: CategorieIdentifiante) -> bool:
        return categorie in self.masquees

    def mention_masquee(self, categorie: CategorieIdentifiante) -> str:
        return texte("masque", categorie=libelle("identifiantes", categorie))

    def valeur(self, observation: Observation) -> str:
        """Valeur affichée, avec son unité ; une mention si sa catégorie est masquée."""
        if observation.identifiante is not None and self.masquee(observation.identifiante):
            return self.mention_masquee(observation.identifiante)
        brute = observation.valeur
        if isinstance(brute, tuple):
            rendu = ", ".join(map(_scalaire, brute)) if brute else texte("liste_vide")
        else:
            rendu = _scalaire(brute)
        return f"{rendu} {observation.unite}" if observation.unite else rendu

    def observation(self, identifiant: str) -> Observation:
        return self._observations[identifiant]

    def regle(self, constat: Constat) -> Regle:
        return self.analyse.regle(constat)

    def phrase(self, constat: Constat) -> str:
        """Phrase du constat : texte de sa règle, paramètres remplacés par leurs valeurs."""
        valeurs = {
            nom: self.valeur(self.observation(identifiant))
            for nom, identifiant in constat.phrase.parametres.items()
        }
        return remplir(self.regle(constat).textes["fr"], valeurs)

    def nom(self) -> str:
        if self.masquee(CategorieIdentifiante.NOM_DE_FICHIER):
            return self.mention_masquee(CategorieIdentifiante.NOM_DE_FICHIER)
        return self.analyse.identification.nom

    def empreinte(self) -> str:
        if self.masquee(CategorieIdentifiante.EMPREINTE):
            return self.mention_masquee(CategorieIdentifiante.EMPREINTE)
        return self.analyse.identification.empreinte

    def catalogue(self) -> str:
        version = self.analyse.catalogue
        cle = "formes.catalogue_fourni" if version.fourni_par_utilisateur else "formes.catalogue"
        return texte(
            cle, version=version.version, date=version.date.isoformat(), empreinte=version.empreinte
        )

    def evaluation(self, regle: Regle) -> str:
        if regle.evaluation is None:
            return texte("formes.non_evaluee")
        return texte(
            "formes.evaluee",
            taux=f"{regle.evaluation.taux_faux_positifs * 100:g} %",
            corpus=regle.evaluation.corpus,
            date=regle.evaluation.date.isoformat(),
        )

    def non_menee(self, non_menee: NonMenee) -> str:
        return libelle("raisons", non_menee.raison)

    def constats(self, categorie: Categorie) -> list[Constat]:
        """Constats d'une catégorie ; indices par direction, puis du plus fort au plus faible."""
        choisis = [c for c in self.analyse.constats if c.categorie is categorie]
        if categorie is Categorie.INDICE:
            directions = list(Direction)
            choisis.sort(
                key=lambda c: (
                    directions.index(c.direction),
                    _NIVEAUX_DECROISSANTS.index(c.graduation.niveau) if c.graduation else 0,
                )
            )
        return choisis

    def alertes(self) -> list[str]:
        """Ce qui change la portée du rapport, annoncé en tête (ES-13, ADR-0086, ADR-0028)."""
        alertes = []
        levees = [c for c in CategorieIdentifiante if not self.masquee(c)]
        if levees:
            categories = ", ".join(libelle("identifiantes", c) for c in levees)
            alertes.append(texte("alertes.masquage_leve", categories=categories))
        if self.analyse.catalogue.fourni_par_utilisateur:
            alertes.append(texte("alertes.catalogue_fourni"))
        isolation = self.analyse.isolation
        if isolation.niveau is NiveauIsolation.REDUITE:
            manques = ", ".join(libelle("manques", manque) for manque in isolation.manques)
            alertes.append(texte("alertes.isolation_reduite", manques=manques))
        if self.analyse.interrompue:
            alertes.append(texte("alertes.interrompue"))
        return alertes

    def signalements(self) -> list[str]:
        """Signalements de l'identification (F-03, ES-07, ADR-0072)."""
        identification = self.analyse.identification
        lignes = []
        if identification.extension is None:
            lignes.append(texte("signalements.extension_absente"))
        elif identification.extension_concordante:
            lignes.append(
                texte("signalements.extension_concordante", extension=identification.extension)
            )
        else:
            lignes.append(
                texte(
                    "signalements.extension_discordante",
                    extension=identification.extension,
                    format=identification.format_reel,
                )
            )
        if len(identification.parties) > 1:
            lignes.append(texte("signalements.polyglotte", nombre=len(identification.parties)))
        for partie in identification.parties:
            if partie.tronquee:
                cle = "signalements.tronquee"
            elif not partie.fin_connue:
                cle = "signalements.fin_non_etablie"
            else:
                cle = ""
            if cle:
                lignes.append(texte(cle, rang=partie.rang, format=partie.format))
            if not partie.dans_perimetre:
                lignes.append(
                    texte("signalements.hors_perimetre", rang=partie.rang, format=partie.format)
                )
        fin_logique = max(partie.fin for partie in identification.parties)
        for plage in identification.octets_non_reconnus:
            cle = (
                "signalements.apres_fin"
                if plage.debut >= fin_logique
                else "signalements.non_reconnus"
            )
            lignes.append(texte(cle, octets=octets(plage)))
        return lignes

    def resume(self) -> list[str]:
        """Résumé sans verdict, dans l'ordre d'ADR-0018 : preuves, indices, le reste."""
        lignes: list[str] = []
        preuves = self.constats(Categorie.PREUVE)
        lignes.extend(
            texte(
                "resume.preuve",
                direction=libelle("directions", preuve.direction),
                phrase=self.phrase(preuve),
            )
            for preuve in preuves
        )
        if not preuves:
            lignes.append(texte("resume.preuves_aucune"))
        lignes.extend(self.indices())
        informations = self.constats(Categorie.INFORMATION_NEUTRE)
        lignes.append(texte("resume.informations", nombre=len(informations)))
        etats = Counter(technique.etat for technique in self.analyse.couverture.techniques)
        lignes.append(
            texte(
                "resume.techniques",
                appliquees=etats[EtatTechnique.APPLIQUEE],
                partielles=etats[EtatTechnique.PARTIELLE],
                non_menees=etats[EtatTechnique.NON_MENEE],
                non_applicables=etats[EtatTechnique.NON_APPLICABLE],
            )
        )
        if self.analyse.non_menees:
            lignes.append(texte("resume.non_menees", nombre=len(self.analyse.non_menees)))
        else:
            lignes.append(texte("resume.non_menees_aucune"))
        return lignes

    def indices(self) -> list[str]:
        """Nombre d'indices par direction et par niveau, sans les combiner (ADR-0018)."""
        indices = self.constats(Categorie.INDICE)
        if not indices:
            return [texte("resume.indices_aucun")]
        lignes = [texte("resume.indices", nombre=len(indices))]
        for direction in Direction:
            niveaux = Counter(
                c.graduation.niveau for c in indices if c.direction is direction and c.graduation
            )
            if niveaux:
                detail = ", ".join(
                    texte(
                        "resume.indice_par_niveau", nombre=niveaux[n], niveau=libelle("niveaux", n)
                    )
                    for n in _NIVEAUX_DECROISSANTS
                    if niveaux[n]
                )
                lignes.append(
                    texte(
                        "resume.indice_par_direction",
                        direction=libelle("directions", direction),
                        detail=detail,
                    )
                )
        return lignes
