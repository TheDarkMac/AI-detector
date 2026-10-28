"""Paquet XMP : XML lu par expat, sans DTD, puis propriétés RDF (ADR-0116 ; XMP, partie 1).

Le XML est lu par l'expat de la bibliothèque standard, avec trois refus : toute déclaration de
type de document (DOCTYPE), toute déclaration d'entité, toute référence à une entité externe
lèvent une erreur qui arrête la lecture. Un paquet XMP n'a jamais de DTD ; sans elle, aucune
entité ne peut être définie, donc aucune ne peut être développée ni aller chercher un fichier ou
une adresse (ES-05, M-02, M-04). Les entités prédéfinies (``&amp;``) et les références de
caractères restent lues.

Chaque élément compte contre le budget du module, et chaque niveau contre son imbrication.

Les propriétés sont nommées par l'espace de noms qu'elles déclarent, pas par le préfixe écrit
dans le fichier : un espace connu prend son préfixe usuel (``dc``, ``xmpMM``…), un autre prend
``ns1``, ``ns2``… dans l'ordre de première apparition (ADR-0117). Un fichier ne peut donc pas
faire passer une propriété inventée pour ``dc:creator`` en déclarant le préfixe ``dc``.
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from xml.parsers import expat

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture.valeurs import composant

__all__ = ["ESPACES", "Propriete", "Xmp", "lire_xmp"]

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
_XML = "http://www.w3.org/XML/1998/namespace"
_X = "adobe:ns:meta/"

ESPACES = {
    _X: "x",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://purl.org/dc/terms/": "dcterms",
    "http://ns.adobe.com/xap/1.0/": "xmp",
    "http://ns.adobe.com/xap/1.0/rights/": "xmpRights",
    "http://ns.adobe.com/xap/1.0/mm/": "xmpMM",
    "http://ns.adobe.com/xap/1.0/bj/": "xmpBJ",
    "http://ns.adobe.com/xap/1.0/t/pg/": "xmpTPg",
    "http://ns.adobe.com/xap/1.0/g/": "xmpG",
    "http://ns.adobe.com/xap/1.0/g/img/": "xmpGImg",
    "http://ns.adobe.com/xmp/1.0/DynamicMedia/": "xmpDM",
    "http://ns.adobe.com/xmp/Identifier/qual/1.0/": "xmpidq",
    "http://ns.adobe.com/xmp/note/": "xmpNote",
    "http://ns.adobe.com/xap/1.0/sType/ResourceEvent#": "stEvt",
    "http://ns.adobe.com/xap/1.0/sType/ResourceRef#": "stRef",
    "http://ns.adobe.com/xap/1.0/sType/Version#": "stVer",
    "http://ns.adobe.com/xap/1.0/sType/Job#": "stJob",
    "http://ns.adobe.com/xap/1.0/sType/Dimensions#": "stDim",
    "http://ns.adobe.com/xap/1.0/sType/Font#": "stFnt",
    "http://ns.adobe.com/xmp/sType/Area#": "stArea",
    "http://ns.adobe.com/pdf/1.3/": "pdf",
    "http://ns.adobe.com/pdfx/1.3/": "pdfx",
    "http://www.aiim.org/pdfa/ns/id/": "pdfaid",
    "http://ns.adobe.com/photoshop/1.0/": "photoshop",
    "http://ns.adobe.com/camera-raw-settings/1.0/": "crs",
    "http://ns.adobe.com/lightroom/1.0/": "lr",
    "http://ns.adobe.com/illustrator/1.0/": "illustrator",
    "http://ns.adobe.com/hdr-gain-map/1.0/": "hdrgm",
    "http://ns.adobe.com/tiff/1.0/": "tiff",
    "http://ns.adobe.com/exif/1.0/": "exif",
    "http://ns.adobe.com/exif/1.0/aux/": "aux",
    "http://cipa.jp/exif/1.0/": "exifEX",
    "http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/": "Iptc4xmpCore",
    "http://iptc.org/std/Iptc4xmpExt/2008-02-29/": "Iptc4xmpExt",
    "http://ns.useplus.org/ldf/xmp/1.0/": "plus",
    "http://www.metadataworkinggroup.com/schemas/regions/": "mwg-rs",
    "http://www.metadataworkinggroup.com/schemas/keywords/": "mwg-kw",
    "http://www.metadataworkinggroup.com/schemas/collections/": "mwg-coll",
    "http://ns.microsoft.com/photo/1.0/": "MicrosoftPhoto",
    "http://ns.google.com/photos/1.0/panorama/": "GPano",
    "http://ns.google.com/photos/1.0/camera/": "GCamera",
    "http://ns.google.com/photos/1.0/container/": "GContainer",
    "http://ns.google.com/photos/1.0/container/item/": "Item",
    "http://ns.google.com/photos/1.0/image/": "GImage",
    "http://ns.google.com/photos/1.0/depthmap/": "GDepth",
    "http://ns.apple.com/faceinfo/1.0/": "apple-fi",
}
"""Espaces de noms connus et leur préfixe usuel, celui de la spécification qui les définit."""


class _Refus(Exception):
    """DTD, entité déclarée ou externe : la lecture s'arrête (ES-05)."""


@dataclass(slots=True)
class _Noeud:
    espace: str
    nom: str
    attributs: dict[tuple[str, str], str]
    enfants: list["_Noeud"] = field(default_factory=list)
    texte: list[str] = field(default_factory=list)

    def est(self, espace: str, nom: str) -> bool:
        return self.espace == espace and self.nom == nom


@dataclass(frozen=True, slots=True)
class Propriete:
    """Propriété XMP : chemin des composants ``préfixe:nom``, valeurs, forme de tableau."""

    composants: tuple[str, ...]
    valeurs: tuple[str, ...]
    tableau: bool
    """Vrai pour un tableau (``rdf:Bag``, ``rdf:Seq``, ``rdf:Alt``), même d'un élément."""

    @property
    def nom(self) -> str:
        return ".".join(self.composants)


@dataclass(frozen=True, slots=True)
class Xmp:
    """Propriétés d'un paquet, espaces inconnus numérotés, et lecture incomplète ou non."""

    proprietes: tuple[Propriete, ...]
    inconnus: tuple[str, ...]
    """Adresse de l'espace ``ns1``, ``ns2``…, dans l'ordre."""
    partiel: bool


def _separer(nom: str) -> tuple[str, str]:
    espace, _, local = nom.rpartition(" ")
    return espace, local


def _arbre(contexte: Contexte, donnees: bytes | str) -> tuple[list[_Noeud], bool]:
    """Racines du document, même si la lecture s'est arrêtée ; vrai si elle s'est arrêtée."""
    lecteur = expat.ParserCreate(namespace_separator=" ")
    lecteur.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    lecteur.buffer_text = True
    racines: list[_Noeud] = []
    pile: list[_Noeud] = []
    niveaux: list[AbstractContextManager[None]] = []

    def refuser(*_arguments: object) -> int:
        raise _Refus

    def ouvrir(nom: str, attributs: dict[str, str]) -> None:
        contexte.compter_objets()
        niveau = contexte.imbrication()
        niveau.__enter__()
        niveaux.append(niveau)
        noeud = _Noeud(*_separer(nom), {_separer(a): v for a, v in attributs.items()})
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
    except (_Refus, expat.ExpatError):
        return racines, True
    finally:
        while niveaux:
            niveaux.pop().__exit__(None, None, None)
    return racines, False


class _Interprete:
    """Parcours RDF d'un arbre : une propriété par chemin, dans l'ordre du document."""

    def __init__(self, contexte: Contexte) -> None:
        self._contexte = contexte
        self._inconnus: dict[str, str] = {}
        self._valeurs: dict[tuple[str, ...], tuple[list[str], list[bool]]] = {}

    def prefixe(self, espace: str) -> str:
        connu = ESPACES.get(espace)
        if connu is not None:
            return connu
        return self._inconnus.setdefault(espace, f"ns{len(self._inconnus) + 1}")

    def composant(self, espace: str, nom: str) -> str:
        return f"{self.prefixe(espace)}:{composant(nom)}"

    def ajouter(self, chemin: tuple[str, ...], valeur: str, tableau: bool) -> None:
        valeurs, tableaux = self._valeurs.setdefault(chemin, ([], []))
        valeurs.append(valeur)
        tableaux.append(tableau)

    def resultat(self, partiel: bool) -> Xmp:
        proprietes = tuple(
            Propriete(chemin, tuple(valeurs), len(valeurs) > 1 or any(tableaux))
            for chemin, (valeurs, tableaux) in self._valeurs.items()
        )
        return Xmp(proprietes, tuple(self._inconnus), partiel)

    # Structure RDF

    def document(self, racines: list[_Noeud]) -> None:
        for racine in racines:
            self.chercher(racine)

    def chercher(self, noeud: _Noeud) -> None:
        if noeud.est(_X, "xmpmeta"):
            self.attributs(noeud, ())
        if noeud.est(RDF, "RDF"):
            for description in noeud.enfants:
                if description.est(RDF, "Description"):
                    self.ressource(description, (), False)
            return
        for enfant in noeud.enfants:
            self.chercher(enfant)

    def attributs(self, noeud: _Noeud, chemin: tuple[str, ...]) -> None:
        for (espace, nom), valeur in noeud.attributs.items():
            if espace not in (RDF, _XML, ""):
                self.ajouter((*chemin, self.composant(espace, nom)), valeur, False)

    def ressource(self, noeud: _Noeud, chemin: tuple[str, ...], tableau: bool) -> None:
        """Champs d'une description ou d'une structure : attributs, puis éléments."""
        self.attributs(noeud, chemin)
        for enfant in noeud.enfants:
            self.propriete(enfant, chemin, tableau)

    def propriete(self, noeud: _Noeud, chemin: tuple[str, ...], tableau: bool) -> None:
        with self._contexte.imbrication():
            chemin = (*chemin, self.composant(noeud.espace, noeud.nom))
            self.valeur(noeud, chemin, tableau)

    def valeur(self, noeud: _Noeud, chemin: tuple[str, ...], tableau: bool) -> None:
        """Valeur d'un élément de propriété ou d'un élément de tableau (``rdf:li``)."""
        ressource = noeud.attributs.get((RDF, "resource"))
        if ressource is not None:
            self.ajouter(chemin, ressource, tableau)
            return
        if noeud.attributs.get((RDF, "parseType")) == "Resource":
            self.ressource(noeud, chemin, tableau)
            return
        elements = noeud.enfants
        if not elements:
            if any(espace not in (RDF, _XML, "") for espace, _ in noeud.attributs):
                self.attributs(noeud, chemin)  # structure écrite en attributs
            else:
                self.ajouter(chemin, "".join(noeud.texte), tableau)
            return
        for enfant in elements:
            if enfant.espace == RDF and enfant.nom in ("Bag", "Seq", "Alt"):
                for element in enfant.enfants:
                    if element.est(RDF, "li"):
                        with self._contexte.imbrication():
                            self.valeur(element, chemin, True)
            elif enfant.est(RDF, "Description"):
                valeur = next((e for e in enfant.enfants if e.est(RDF, "value")), None)
                if valeur is not None:
                    self.valeur(valeur, chemin, tableau)  # valeur qualifiée
                else:
                    self.ressource(enfant, chemin, tableau)
            elif enfant.est(RDF, "value"):
                self.valeur(enfant, chemin, tableau)
            elif enfant.espace != RDF:
                self.propriete(enfant, chemin, tableau)


def lire_xmp(contexte: Contexte, donnees: bytes | str) -> Xmp:
    """Propriétés d'un paquet XMP ; ``partiel`` si le XML est invalide ou refusé.

    Un texte déjà décodé (bloc ``iTXt`` d'un PNG) est lu en UTF-8, quelle que soit la
    déclaration d'encodage du paquet.
    """
    racines, partiel = _arbre(contexte, donnees)
    interprete = _Interprete(contexte)
    interprete.document(racines)
    return interprete.resultat(partiel)
