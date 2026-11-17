"""Document XML lu par expat, sans DTD, en arbre d'éléments (ADR-0116).

Le XML est lu par l'expat de la bibliothèque standard, avec trois refus : toute déclaration de
type de document (DOCTYPE), toute déclaration d'entité, toute référence à une entité externe
lèvent une erreur qui arrête la lecture. Sans DTD, aucune entité ne peut être définie, donc
aucune ne peut être développée ni aller chercher un fichier ou une adresse (ES-05, M-02, M-04).
Les entités prédéfinies (``&amp;``) et les références de caractères restent lues.

Chaque élément compte contre le budget du module, et chaque niveau contre son imbrication.
Commun au XMP (ADR-0116), aux propriétés de DOCX et d'ODT (ADR-0136) et à leurs éléments
actifs, lus élément par élément par :func:`parcourir` (complément bureautique de T52).
"""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from xml.parsers import expat

from voight_kampff._travail.contexte import Contexte

__all__ = ["Noeud", "Ouvrir", "Refus", "lire_arbre", "parcourir"]


class Refus(Exception):
    """DTD, entité déclarée ou externe : la lecture s'arrête (ES-05)."""


class _Rappel(Exception):
    """Exception d'un rappel, mise à part de celles d'expat le temps de la lecture."""


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


Ouvrir = Callable[[str, str, dict[tuple[str, str], str]], None]
"""Appelée à l'ouverture d'un élément : espace, nom local, attributs."""


def parcourir(
    contexte: Contexte,
    donnees: bytes | str,
    ouvrir: Ouvrir,
    fermer: Callable[[], object],
    texte: Callable[[str], None] | None = None,
) -> bool:
    """Lit le document élément par élément, sans en garder l'arbre ; vrai si la lecture s'est
    arrêtée (XML mal formé, DTD ou entité refusée, encodage déclaré qu'expat ne lit pas).

    Chaque élément compte contre le budget du module et son imbrication, avant ``ouvrir`` ; une
    exception levée par ``ouvrir`` (ou par le budget) arrête la lecture et remonte telle quelle.
    ``fermer`` et ``texte`` ne lèvent pas.

    Expat lit seul UTF-8, UTF-16, ISO-8859-1 et ASCII ; pour un autre encodage déclaré, il
    demande le codec à Python, qui lève ``LookupError`` (encodage inconnu), ``ValueError``
    (encodage multioctet) ou ``OSError`` (codec que le processus restreint ne peut plus lire sur
    le disque, ADR-0079) : la lecture s'arrête comme pour un XML mal formé (ERR-0012). Les
    exceptions des rappels sont mises à part, et remontent telles quelles. XMP, DOCX et ODT
    s'écrivent en UTF-8 ou en UTF-16.
    """
    lecteur = expat.ParserCreate(namespace_separator=" ")
    lecteur.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    lecteur.buffer_text = True
    niveaux: list[AbstractContextManager[None]] = []
    erreurs: list[Exception] = []

    def refuser(*_arguments: object) -> int:
        raise Refus

    def debut(nom: str, attributs: dict[str, str]) -> None:
        try:
            contexte.compter_objets()
            niveau = contexte.imbrication()
            niveau.__enter__()
            niveaux.append(niveau)
            ouvrir(*_separer(nom), {_separer(a): v for a, v in attributs.items()})
        except Exception as erreur:
            erreurs.append(erreur)
            raise _Rappel from None

    def fin(_nom: str) -> None:
        fermer()  # ne lève pas : celui de lire_arbre, comme ceux d'actifsbureau, dépile
        niveaux.pop().__exit__(None, None, None)

    lecteur.StartDoctypeDeclHandler = refuser
    lecteur.EntityDeclHandler = refuser
    lecteur.ExternalEntityRefHandler = refuser
    lecteur.StartElementHandler = debut
    lecteur.EndElementHandler = fin
    if texte is not None:
        lecteur.CharacterDataHandler = texte
    try:
        lecteur.Parse(donnees, True)
    except _Rappel:
        raise erreurs[0] from None
    except (Refus, expat.ExpatError, LookupError, ValueError, OSError):
        return True
    finally:
        while niveaux:
            niveaux.pop().__exit__(None, None, None)
    return False


def lire_arbre(contexte: Contexte, donnees: bytes | str) -> tuple[list[Noeud], bool]:
    """Racines du document, même si la lecture s'est arrêtée ; vrai si elle s'est arrêtée."""
    racines: list[Noeud] = []
    pile: list[Noeud] = []

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        noeud = Noeud(espace, nom, attributs)
        (pile[-1].enfants if pile else racines).append(noeud)
        pile.append(noeud)

    def texte(contenu: str) -> None:
        pile[-1].texte.append(contenu)  # expat ne rend pas de texte hors de la racine

    partiel = parcourir(contexte, donnees, ouvrir, pile.pop, texte)
    return racines, partiel
