"""Document XML lu par expat, sans DTD, en arbre d'éléments (ADR-0116).

Le XML est lu par l'expat de la bibliothèque standard, avec trois refus : toute déclaration de
type de document (DOCTYPE), toute déclaration d'entité, toute référence à une entité externe
lèvent une erreur qui arrête la lecture. Sans DTD, aucune entité ne peut être définie, donc
aucune ne peut être développée ni aller chercher un fichier ou une adresse (ES-05, M-02, M-04).
Les entités prédéfinies (``&amp;``) et les références de caractères restent lues.

Chaque élément compte contre le budget du module, et chaque niveau contre son imbrication.
Commun au XMP (ADR-0116) et aux propriétés de DOCX et d'ODT (ADR-0136).
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from xml.parsers import expat

from voight_kampff._travail.contexte import Contexte

__all__ = ["Noeud", "Refus", "lire_arbre"]


class Refus(Exception):
    """DTD, entité déclarée ou externe : la lecture s'arrête (ES-05)."""


@dataclass(slots=True)
class Noeud:
    """Élément : adresse de son espace de noms, nom local, attributs, enfants et texte."""

    espace: str
    nom: str
    attributs: dict[tuple[str, str], str]
    """Attributs par (espace, nom local) ; l'espace d'un attribut sans préfixe est vide."""
    enfants: list["Noeud"] = field(default_factory=list)
    texte: list[str] = field(default_factory=list)
    """Morceaux de texte directement contenus, dans l'ordre."""

    def est(self, espace: str, nom: str) -> bool:
        return self.espace == espace and self.nom == nom


def _separer(nom: str) -> tuple[str, str]:
    espace, _, local = nom.rpartition(" ")
    return espace, local


def lire_arbre(contexte: Contexte, donnees: bytes | str) -> tuple[list[Noeud], bool]:
    """Racines du document, même si la lecture s'est arrêtée ; vrai si elle s'est arrêtée."""
    lecteur = expat.ParserCreate(namespace_separator=" ")
    lecteur.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    lecteur.buffer_text = True
    racines: list[Noeud] = []
    pile: list[Noeud] = []
    niveaux: list[AbstractContextManager[None]] = []

    def refuser(*_arguments: object) -> int:
        raise Refus

    def ouvrir(nom: str, attributs: dict[str, str]) -> None:
        contexte.compter_objets()
        niveau = contexte.imbrication()
        niveau.__enter__()
        niveaux.append(niveau)
        noeud = Noeud(*_separer(nom), {_separer(a): v for a, v in attributs.items()})
        (pile[-1].enfants if pile else racines).append(noeud)
        pile.append(noeud)

    def fermer(_nom: str) -> None:
        pile.pop()
        niveaux.pop().__exit__(None, None, None)

    def texte(contenu: str) -> None:
        pile[-1].texte.append(contenu)  # expat ne rend pas de texte hors de la racine

    lecteur.StartDoctypeDeclHandler = refuser
    lecteur.EntityDeclHandler = refuser
    lecteur.ExternalEntityRefHandler = refuser
    lecteur.StartElementHandler = ouvrir
    lecteur.EndElementHandler = fermer
    lecteur.CharacterDataHandler = texte
    try:
        lecteur.Parse(donnees, True)
    except (Refus, expat.ExpatError):
        return racines, True
    finally:
        while niveaux:
            niveaux.pop().__exit__(None, None, None)
    return racines, False
