"""Module ``ooxml`` : propriétés d'un document DOCX (F-10, ADR-0136 à ADR-0140 ; fiche
``metadonnees-ooxml``).

Suit les relations du paquet (``_rels/.rels``) vers ses trois parties de propriétés (ECMA-376,
parties 1 et 2) et observe chacune sous ``ooxml.core``, ``ooxml.app`` ou ``ooxml.custom`` :

- propriétés principales (``docProps/core.xml`` d'ordinaire) : ``ooxml.core.dc:creator``,
  ``ooxml.core.cp:lastModifiedBy``, ``ooxml.core.dcterms:created``… ;
- propriétés étendues (``docProps/app.xml``) : ``ooxml.app.Application``,
  ``ooxml.app.TotalTime``… ;
- propriétés personnalisées (``docProps/custom.xml``) : ``ooxml.custom.<nom>``.

Observe aussi ``ooxml.present`` dans tous les cas (F-14). Les dates sont observées telles
qu'écrites (W3CDTF). Aucune autre relation n'est lue ni suivie : ni le document, ni un modèle
distant, ni un lien, ni la liste des liens des propriétés étendues (``HLinks``) (ES-06,
ADR-0138). Aucune règle : T22, T23 et T81 lisent ces observations.
"""

import binascii
from urllib.parse import unquote

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.arbre import Noeud, lire_arbre
from voight_kampff.modules._lecture.proprietes import Proprietes, booleen, entier, reel
from voight_kampff.modules._lecture.zip import Archive, Entree, Illisible
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    Localisation,
    RaisonNonMenee,
    Scalaire,
)

__all__ = ["analyser"]

_RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
_PROPRIETES = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/"
_DOCUMENT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
_STRICT = "http://purl.oclc.org/ooxml/officeDocument/relationships/"
_TYPES = {
    f"{_PROPRIETES}core-properties": "core",
    # Écriture des premières versions d'Office 2007, encore lue par les logiciels.
    f"{_DOCUMENT.lower()}metadata/core-properties": "core",
    f"{_DOCUMENT}extended-properties": "app",
    f"{_STRICT}extendedProperties": "app",
    f"{_DOCUMENT}custom-properties": "custom",
    f"{_STRICT}customProperties": "custom",
}
"""Types des relations vers les parties de propriétés, transitionnels et stricts."""
_SORTES = ("core", "app", "custom")

_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
_APP = frozenset(
    {
        "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
        "http://purl.oclc.org/ooxml/officeDocument/extendedProperties",
    }
)
_CUSTOM = frozenset(
    {
        "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties",
        "http://purl.oclc.org/ooxml/officeDocument/customProperties",
    }
)
_VT = frozenset(
    {
        "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
        "http://purl.oclc.org/ooxml/officeDocument/docPropsVTypes",
    }
)
_CONNUS = {
    _CP: "cp",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://purl.org/dc/terms/": "dcterms",
    "http://purl.org/dc/dcmitype/": "dcmitype",
}
"""Préfixes de la partie 2 d'ECMA-376 pour les propriétés principales."""

_ENTIERS = frozenset(
    {
        "Characters",
        "CharactersWithSpaces",
        "DocSecurity",
        "HiddenSlides",
        "Lines",
        "MMClips",
        "Notes",
        "Pages",
        "Paragraphs",
        "Slides",
        "TotalTime",
        "Words",
    }
)
_BOOLEENS = frozenset({"HyperlinksChanged", "LinksUpToDate", "ScaleCrop", "SharedDoc"})
"""Propriétés étendues typées par le schéma ; les autres sont des textes."""
_LIENS = "HLinks"
"""Liste des liens du document : jamais lue (ADR-0138)."""

_VT_TEXTES = frozenset({"lpstr", "lpwstr", "bstr", "date", "filetime", "cy", "error", "clsid"})
_VT_ENTIERS = frozenset({"i1", "i2", "i4", "i8", "int", "ui1", "ui2", "ui4", "ui8", "uint"})
_VT_REELS = frozenset({"r4", "r8", "decimal"})
_VT_BINAIRES = frozenset(
    {"blob", "oblob", "stream", "ostream", "storage", "ostorage", "vstream", "cf"}
)
_VT_LISTES = frozenset({"vector", "array"})

_NOMINATIVES = frozenset(
    {"core.dc:creator", "core.cp:lastModifiedBy", "app.Company", "app.Manager"}
)
_FICHIERS = frozenset({"app.Template", "app.HyperlinkBase"})
"""Propriétés identifiantes (ADR-0119, ADR-0140) ; ``Template`` est le nom du modèle, parfois son
chemin, ``HyperlinkBase`` un chemin ou une adresse."""


def _identifiante(nom: str) -> CategorieIdentifiante | None:
    if nom in _NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if nom in _FICHIERS:
        return CategorieIdentifiante.NOM_DE_FICHIER
    return None


def analyser(contexte: Contexte) -> None:
    try:
        archive = Archive(contexte)
        relations = archive.trouver("_rels/.rels", casse=False)
        if relations is None:
            raise Illisible(RaisonNonMenee.FORMAT_PARTIEL, 0, "_rels/.rels")
        cibles = _cibles(contexte, archive, relations)
    except Illisible as illisible:
        contexte.observer("ooxml.present", False)
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    trouvees: list[tuple[str, Entree]] = []
    for sorte, partie in cibles:
        try:
            entree = archive.trouver(partie, casse=False)
        except Illisible as illisible:
            contexte.non_mener(
                illisible.raison, localisation=illisible.localisation(contexte.taille)
            )
            continue
        if entree is None:
            localisation = Localisation(chemin=f"{partie} (partie absente)")
            contexte.non_mener(RaisonNonMenee.REFERENCE_MANQUANTE, localisation=localisation)
            continue
        trouvees.append((sorte, entree))
    contexte.observer("ooxml.present", bool(cibles))
    if trouvees:
        contexte.observer("ooxml.blocs", len(trouvees))
    proprietes = Proprietes("ooxml", _CONNUS)
    for sorte, entree in trouvees:
        try:
            donnees = archive.lire(entree)
            localisation = archive.localisation(entree)
        except Illisible as illisible:
            contexte.non_mener(
                illisible.raison, localisation=illisible.localisation(contexte.taille)
            )
            continue
        racines, partiel = lire_arbre(contexte, donnees)
        lue = _PARTIES[sorte](proprietes, racines, localisation)
        if partiel or not lue:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
    proprietes.observer(contexte)


def _cibles(contexte: Contexte, archive: Archive, relations: Entree) -> list[tuple[str, str]]:
    """Parties de propriétés désignées par les relations du paquet, une par sorte.

    Une relation externe n'est jamais suivie ; une seconde relation de même sorte n'est pas lue.
    Les deux sont non menées, sans que leur cible figure au rapport.
    """
    racines, partiel = lire_arbre(contexte, archive.lire(relations))
    localisation = archive.localisation(relations)
    if partiel:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
    cibles: dict[str, str] = {}
    for racine in racines:
        if not racine.est(_RELATIONS, "Relationships"):
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
            continue
        for relation in racine.enfants:
            sorte = _TYPES.get(relation.attributs.get(("", "Type"), ""))
            if not relation.est(_RELATIONS, "Relationship") or sorte is None:
                continue  # autre relation : ni lue ni suivie (ADR-0138)
            cible = _partie(relation.attributs.get(("", "Target"), ""))
            externe = relation.attributs.get(("", "TargetMode")) == "External"
            if externe or cible is None or sorte in cibles:
                suite = "relation externe, non suivie" if externe else "relation non lue"
                ecartee = Localisation(chemin=f"_rels/.rels / {sorte} ({suite})")
                contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=ecartee)
                continue
            cibles[sorte] = cible
    return [(sorte, cibles[sorte]) for sorte in _SORTES if sorte in cibles]


def _partie(cible: str) -> str | None:
    """Nom, dans l'archive, de la partie que désigne une cible relative à la racine du paquet."""
    segments: list[str] = []
    for segment in unquote(cible).split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)
    return "/".join(segments) or None


# Parties de propriétés


def _texte(noeud: Noeud) -> Scalaire | list[Scalaire]:
    """Texte d'un élément ; celui de ses enfants à la suite, en liste (``cp:keywords``)."""
    if not noeud.enfants:
        return "".join(noeud.texte)
    return ["".join(noeud.texte), *("".join(enfant.texte) for enfant in noeud.enfants)]


def _core(proprietes: Proprietes, racines: list[Noeud], localisation: Localisation) -> bool:
    racine = next((r for r in racines if r.est(_CP, "coreProperties")), None)
    if racine is None:
        return False
    for element in racine.enfants:
        nom = f"core.{proprietes.composant(element.espace, element.nom, localisation)}"
        proprietes.ajouter(nom, _texte(element), localisation, _identifiante(nom))
    return True


def _app(proprietes: Proprietes, racines: list[Noeud], localisation: Localisation) -> bool:
    racine = next((r for r in racines if r.espace in _APP and r.nom == "Properties"), None)
    if racine is None:
        return False
    for element in racine.enfants:
        if element.espace in _APP:
            if element.nom == _LIENS:
                continue
            nom = f"app.{valeurs.composant(element.nom)}"
        else:
            nom = f"app.{proprietes.composant(element.espace, element.nom, localisation)}"
        identifiante = _identifiante(nom)
        if element.enfants:
            for variante in element.enfants:
                _variante(proprietes, nom, variante, localisation, identifiante)
            continue
        texte = "".join(element.texte)
        if element.espace in _APP and element.nom in _ENTIERS:
            proprietes.ajouter(nom, entier(texte), localisation, identifiante)
        elif element.espace in _APP and element.nom in _BOOLEENS:
            proprietes.ajouter(nom, booleen(texte), localisation, identifiante)
        else:
            proprietes.ajouter(nom, texte, localisation, identifiante)
    return True


def _custom(proprietes: Proprietes, racines: list[Noeud], localisation: Localisation) -> bool:
    racine = next((r for r in racines if r.espace in _CUSTOM and r.nom == "Properties"), None)
    if racine is None:
        return False
    complete = True
    for propriete in racine.enfants:
        designation = propriete.attributs.get(("", "name"))
        if propriete.espace not in _CUSTOM or propriete.nom != "property" or not designation:
            complete = False
            continue
        nom = f"custom.{valeurs.composant(designation)}"
        for variante in propriete.enfants:
            _variante(proprietes, nom, variante, localisation, None)
    return complete


def _variante(
    proprietes: Proprietes,
    nom: str,
    noeud: Noeud,
    localisation: Localisation,
    identifiante: CategorieIdentifiante | None,
) -> None:
    """Valeur typée de ``docPropsVTypes`` : texte, nombre, booléen, liste, ou taille d'un binaire.

    Une liste (``vt:vector``) devient une liste d'observation, même d'un élément ; les éléments
    ``vt:variant`` y sont remplacés par leur valeur.
    """
    if noeud.espace not in _VT:
        return
    if noeud.nom in _VT_LISTES:
        elements = [
            valeur
            for enfant in noeud.enfants
            if (valeur := _scalaire(_sans_variante(enfant))) is not None
        ]
        proprietes.ajouter(nom, elements, localisation, identifiante)
        return
    noeud = _sans_variante(noeud)
    if noeud.espace in _VT and noeud.nom in _VT_BINAIRES:
        proprietes.taille(nom, _octets("".join(noeud.texte)), localisation, identifiante)
        return
    valeur = _scalaire(noeud)
    if valeur is not None:
        proprietes.ajouter(nom, valeur, localisation, identifiante)


def _sans_variante(noeud: Noeud) -> Noeud:
    while noeud.espace in _VT and noeud.nom == "variant" and noeud.enfants:
        noeud = noeud.enfants[0]
    return noeud


def _scalaire(noeud: Noeud) -> str | int | float | bool | None:
    """Valeur d'un type simple ; ``None`` pour une liste, un binaire ou un type inconnu."""
    if noeud.espace not in _VT:
        return None
    texte = "".join(noeud.texte)
    if noeud.nom in _VT_TEXTES:
        return texte
    if noeud.nom in _VT_ENTIERS:
        return entier(texte)
    if noeud.nom in _VT_REELS:
        return reel(texte)
    if noeud.nom == "bool":
        return booleen(texte)
    return None


def _octets(base64: str) -> int:
    """Taille d'une donnée binaire écrite en base 64, blancs ignorés ; celle du texte si elle est
    mal écrite."""
    try:
        return len(binascii.a2b_base64("".join(base64.split()), strict_mode=True))
    except binascii.Error:
        return len(base64.encode())


_PARTIES = {"core": _core, "app": _app, "custom": _custom}
