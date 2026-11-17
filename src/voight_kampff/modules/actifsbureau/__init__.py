"""Module ``actifsbureau`` : éléments actifs d'un DOCX ou d'un ODT, signalés, jamais exécutés
(F-62, NF-01, ES-06 ; complément bureautique de T52, ADR-0228 à ADR-0231 ; fiche
``actifs-bureau``).

Le module cherche ce qu'un traitement de texte exécuterait, activerait ou irait chercher hors du
document, en suivant le document comme le logiciel le lit (ADR-0229) :

- DOCX : les relations des parties (ECMA-376, partie 2, §9), depuis celles du paquet
  (``_rels/.rels``) et de proche en proche vers chaque partie qu'elles désignent dans
  l'archive : projet de macros VBA (``vbaProject``), extension du ruban (``customUI``),
  contrôles ActiveX (``control``), objets OLE (``oleObject``) et documents incorporés
  (``package``), et toute relation dont la cible est hors de l'archive (``TargetMode="External"``)
  : modèle distant (``attachedTemplate``), image liée, cadre, objet lié, source de données d'un
  publipostage, sous-document, lien. Le corps (``word/document.xml``) n'est lu que par ses
  relations : ses codes de champ ne le sont pas.
- ODT : les bibliothèques Basic (``Basic/``) et les scripts (``Scripts/``) par les noms des
  entrées de l'archive ; dans ``content.xml`` et ``styles.xml``, les événements liés à une macro
  (``script:event-listener``), les objets OLE, documents incorporés, applets et modules
  externes, les connexions DDE et toute référence ``xlink:href`` hors de l'archive ; dans
  ``meta.xml``, le modèle et le rechargement automatique ; dans ``META-INF/manifest.xml``, le
  type des documents incorporés (un graphique ou une formule est ordinaire).

Chaque élément est décrit par sa **nature**, en liste fermée (``VBA``, ``Basic``, ``OLE``,
``modèle``, ``image``…, ``autre`` pour un type que le module ne connaît pas), et par son
**déclencheur** (ouverture du document, autre événement du document, geste de l'utilisateur)
(ADR-0230). Ni adresse, ni chemin, ni nom de macro, de module ou de bibliothèque, ni code n'est
lu ni observé : le projet VBA n'est pas ouvert, aucune adresse n'est résolue, aucun fichier lié
n'est lu (ES-06, ADR-0033, ADR-0138). Le module n'émet aucun constat : les règles du catalogue
lisent ses observations (ADR-0231).
"""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import unquote

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.arbre import Ouvrir, lire_arbre, parcourir
from voight_kampff.modules._lecture.zip import Archive, Entree, Illisible
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee

__all__ = [
    "AUTRE",
    "DECLENCHEURS",
    "ELEMENTS_MAX",
    "NATURES",
    "OBJETS_RESERVES",
    "PARTIES_MAX",
    "analyser",
]

PARTIES_MAX = 4096
"""Parties d'un DOCX au plus suivies ; au-delà, ``actifsbureau.recherche_coupee`` le dit."""
ELEMENTS_MAX = 1 << 16
"""Éléments au plus retenus ; au-delà, ``actifsbureau.recherche_coupee`` le dit."""
OBJETS_RESERVES = 1 << 18
"""Objets du budget (ES-03) gardés pour finir : la recherche s'arrête quand il n'en reste pas
plus, pour que les observations déjà faites soient envoyées (comme ``actifspdf``, ADR-0221)."""

OUVERTURE = "ouverture"
"""Ouverture du document : événement d'ouverture, ressource chargée pour l'afficher."""
DOCUMENT = "document"
"""Autre événement du document : enregistrement, impression, fermeture, changement de vue…"""
UTILISATEUR = "utilisateur"
"""Geste de l'utilisateur : clic sur un lien ou un bouton, saisie dans un champ."""
DECLENCHEURS = (OUVERTURE, DOCUMENT, UTILISATEUR)
"""Déclencheurs, dans l'ordre où ils s'écrivent ; les deux premiers sont automatiques."""
_AUTOMATIQUES = frozenset({OUVERTURE, DOCUMENT})

AUTRE = "autre"
MACRO = "macro"
"""Nature d'un événement : il appelle une macro, du document ou de l'application."""

_MACROS = "macros"
_EVENEMENTS = "evenements"
_OBJETS = "objets"
_EXTERNES = "externes"
NATURES = {
    _MACROS: ("VBA", "ruban", "Basic", "Python", "JavaScript", "BeanShell", "Java", AUTRE),
    _EVENEMENTS: (MACRO,),
    _OBJETS: ("OLE", "ActiveX", "paquet", "document", "applet", "plugin"),
    _EXTERNES: (
        "modèle",
        "image",
        "cadre",
        "objet",
        "section",
        "source de données",
        "rechargement",
        "DDE",
        "sous-document",
        "lien",
        AUTRE,
    ),
}
"""Natures de chaque famille, en liste fermée et dans l'ordre où elles s'écrivent."""
_LOCALISATION = Localisation(chemin="macros, objets et références externes")


@dataclass(slots=True)
class _Element:
    famille: str
    nature: str
    declencheurs: set[str] = field(default_factory=set)


class _Arret(Exception):
    """Plus que :data:`OBJETS_RESERVES` objets du budget : la lecture d'une partie s'arrête."""


class _Recherche:
    """Éléments trouvés, parties lues, et la garde du budget."""

    def __init__(self, contexte: Contexte, archive: Archive) -> None:
        self.contexte = contexte
        self.archive = archive
        self.elements: list[_Element] = []
        self.parties = 0
        """Parties lues : relations d'une partie (DOCX), parties XML (ODT)."""
        self.arrete = False
        self.coupee = False
        self.chiffre = False
        """Vrai si le manifeste d'un ODT déclare des entrées chiffrées (mot de passe)."""
        self._index: dict[str, list[Entree]] = {}
        for entree in archive.entrees:
            self._index.setdefault(_ascii_minuscules(entree.nom), []).append(entree)

    def continuer(self) -> bool:
        """Faux dès qu'il ne reste plus que :data:`OBJETS_RESERVES` objets du budget."""
        if self.contexte.objets > OBJETS_MAX - OBJETS_RESERVES:
            self.arrete = True
        return not self.arrete

    def ajouter(self, famille: str, nature: str, declencheur: str | None = None) -> None:
        if len(self.elements) >= ELEMENTS_MAX:
            self.coupee = True
            return
        self.contexte.compter_objets()
        element = _Element(famille, nature)
        if declencheur is not None:
            element.declencheurs.add(declencheur)
        self.elements.append(element)

    def trouver(self, nom: str, *, casse: bool) -> Entree | None:
        """Entrée de ce nom, par l'index ; deux entrées de ce nom sont illisibles, comme le dit
        :meth:`Archive.trouver`, qui les signale."""
        trouvees = [
            e for e in self._index.get(_ascii_minuscules(nom), []) if not casse or e.nom == nom
        ]
        if len(trouvees) > 1:
            self.archive.trouver(nom, casse=casse)  # lève Illisible
        return trouvees[0] if trouvees else None

    def lire(self, entree: Entree) -> tuple[bytes, Localisation] | None:
        """Contenu d'une partie et sa localisation ; ``None``, et la partie non menée, si elle ne
        se lit pas."""
        try:
            return self.archive.lire(entree), self.archive.localisation(entree)
        except Illisible as illisible:
            self.non_mener(illisible)
            return None

    def parcourir(self, donnees: bytes, ouvrir: Ouvrir, fermer: Callable[[], object]) -> bool:
        """Lit une partie XML élément par élément ; vrai si elle a été lue en entier."""

        def garder(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
            if not self.continuer():
                raise _Arret
            ouvrir(espace, nom, attributs)

        try:
            return not parcourir(self.contexte, donnees, garder, fermer)
        except _Arret:
            return False

    def non_mener(self, illisible: Illisible) -> None:
        self.contexte.non_mener(
            illisible.raison, localisation=illisible.localisation(self.contexte.taille)
        )


def analyser(contexte: Contexte) -> None:
    try:
        archive = Archive(contexte)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    recherche = _Recherche(contexte, archive)
    if contexte.format_reel == "odt":
        _odt(recherche)
    else:
        _docx(recherche)
    _observer(recherche)


# DOCX


_PREFIXES = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/",
    "http://purl.oclc.org/ooxml/officeDocument/relationships/",
    "http://schemas.microsoft.com/office/2006/relationships/",
    "http://schemas.microsoft.com/office/2007/relationships/",
)
"""Espaces des types de relations : transitionnel et strict d'ECMA-376, extensions de Microsoft
([MS-OFFMACRO], [MS-CUSTOMUI])."""
_RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
_PRINCIPALE = "officeDocument"
_INTERNES = {
    "vbaProject": (_MACROS, "VBA"),
    "ui/extensibility": (_MACROS, "ruban"),
    "control": (_OBJETS, "ActiveX"),
    "oleObject": (_OBJETS, "OLE"),
    "package": (_OBJETS, "paquet"),
}
"""Relations vers une partie de l'archive qui porte un élément actif."""
_GRAPHIQUE = "chart"
"""Un document incorporé dans un graphique en porte les données : il n'est pas compté."""
_EXTERNES_DOCX = {
    "attachedTemplate": ("modèle", OUVERTURE),
    "image": ("image", OUVERTURE),
    "frame": ("cadre", OUVERTURE),
    "oleObject": ("objet", OUVERTURE),
    "mailMergeSource": ("source de données", OUVERTURE),
    "mailMergeHeaderSource": ("source de données", OUVERTURE),
    "recipientData": ("source de données", OUVERTURE),
    "subDocument": ("sous-document", UTILISATEUR),
    "hyperlink": ("lien", UTILISATEUR),
}
"""Relations vers une cible hors de l'archive : nature et déclencheur. Les autres sont
observées ``autre``, sans déclencheur."""


def _sorte(type_: str) -> str | None:
    """Nom court d'un type de relation, sans son espace ; ``None`` pour un espace inconnu."""
    for prefixe in _PREFIXES:
        if type_.startswith(prefixe):
            return type_[len(prefixe) :]
    return None


def _relations_de(partie: str) -> str:
    """Partie des relations d'une partie (``word/document.xml`` → ``word/_rels/document.xml.rels``)
    ; celles du paquet pour la racine."""
    dossier, _, nom = partie.rpartition("/")
    return f"{dossier}/_rels/{nom}.rels" if dossier else f"_rels/{nom}.rels"


def _cible(source: str, cible: str) -> str | None:
    """Nom, dans l'archive, de la partie que désigne une cible relative à la partie source."""
    dossier = source.rpartition("/")[0]
    chemin = unquote(cible)
    if all(segment in ("", ".", "..") for segment in chemin.split("/")):
        return None  # une cible doit nommer une partie, pas un dossier (OPC)
    segments: list[str] = [] if chemin.startswith("/") or not dossier else dossier.split("/")
    for segment in chemin.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)
    return "/".join(segments)


def _docx(recherche: _Recherche) -> None:
    """Relations du paquet, puis de chaque partie qu'elles désignent, de proche en proche."""
    file: deque[tuple[str, str | None]] = deque([("", None)])
    vues = {""}
    while file:
        if not recherche.continuer():
            return
        if recherche.parties >= PARTIES_MAX:
            recherche.coupee = True
            return
        source, venue = file.popleft()
        nom = _relations_de(source)
        try:
            entree = recherche.trouver(nom, casse=False)
        except Illisible as illisible:
            recherche.non_mener(illisible)
            continue
        if entree is None:
            continue
        lue = recherche.lire(entree)
        if lue is None:
            continue
        recherche.parties += 1
        donnees, localisation = lue
        for cible in _relations(recherche, source, venue, donnees, localisation):
            if _ascii_minuscules(cible[0]) not in vues:
                vues.add(_ascii_minuscules(cible[0]))
                file.append(cible)


def _relations(
    recherche: _Recherche,
    source: str,
    venue: str | None,
    donnees: bytes,
    localisation: Localisation,
) -> list[tuple[str, str | None]]:
    """Éléments des relations d'une partie ; renvoie les parties à suivre et la sorte de la
    relation qui y mène."""
    racines, partiel = lire_arbre(recherche.contexte, donnees)
    complete = not partiel
    suivre: list[tuple[str, str | None]] = []
    for racine in racines:
        if not racine.est(_RELATIONS, "Relationships"):
            complete = False
            continue
        for relation in racine.enfants:
            if not relation.est(_RELATIONS, "Relationship"):
                continue
            sorte = _sorte(relation.attributs.get(("", "Type"), ""))
            if relation.attributs.get(("", "TargetMode")) == "External":
                nature, declencheur = _EXTERNES_DOCX.get(sorte or "", (AUTRE, None))
                recherche.ajouter(_EXTERNES, nature, declencheur)
                continue
            if source == "" and sorte != _PRINCIPALE and sorte not in _INTERNES:
                continue  # propriétés, vignette, signatures : rien d'actif ni à suivre
            partie = _cible(source, relation.attributs.get(("", "Target"), ""))
            if partie is None:
                complete = False
                continue
            actif = _INTERNES.get(sorte or "")
            if actif is not None and not (sorte == "package" and venue == _GRAPHIQUE):
                if not _presente(recherche, partie, actif[1]):
                    continue
                recherche.ajouter(*actif)
            suivre.append((partie, sorte))
    if not complete:
        recherche.contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
    return suivre


def _presente(recherche: _Recherche, partie: str, nature: str) -> bool:
    """Vrai si la partie d'un élément actif est dans l'archive ; sinon, référence manquante."""
    try:
        trouvee = recherche.trouver(partie, casse=False)
    except Illisible as illisible:
        recherche.non_mener(illisible)
        return False
    if trouvee is None:
        localisation = Localisation(chemin=f"{nature} (partie absente)")
        recherche.contexte.non_mener(RaisonNonMenee.REFERENCE_MANQUANTE, localisation=localisation)
    return trouvee is not None


# ODT


_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
_META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
_SCRIPT = "urn:oasis:names:tc:opendocument:xmlns:script:1.0"
_DRAW = "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_STYLE = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
_FORM = "urn:oasis:names:tc:opendocument:xmlns:form:1.0"
_TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
_MANIFESTE = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
_XLINK = "http://www.w3.org/1999/xlink"

_INDEX_BASIC = frozenset({"script-lc.xml", "script-lb.xml", "dialog-lc.xml", "dialog-lb.xml"})
"""Index des bibliothèques Basic et des boîtes de dialogue : ils ne portent pas de code."""
_LANGAGES = {
    "basic": "Basic",
    "python": "Python",
    "javascript": "JavaScript",
    "beanshell": "BeanShell",
    "java": "Java",
}
"""Dossiers de ``Scripts/`` : un par langage."""
_OUVERTURE_ODF = frozenset(
    {
        "dom:load",
        "office:new",
        "office:create",
        "office:load-finished",
        "office:view-created",
        "office:layout-finished",
    }
)
"""Événements du document levés à son ouverture ; les autres le sont par un autre événement du
document (enregistrement, impression, fermeture…)."""
_EXTERNES_ODF = {
    (_DRAW, "image"): ("image", OUVERTURE),
    (_DRAW, "fill-image"): ("image", OUVERTURE),
    (_STYLE, "background-image"): ("image", OUVERTURE),
    (_DRAW, "object"): ("objet", OUVERTURE),
    (_DRAW, "object-ole"): ("objet", OUVERTURE),
    (_DRAW, "floating-frame"): ("cadre", OUVERTURE),
    (_TEXT, "section-source"): ("section", OUVERTURE),
    (_TEXT, "a"): ("lien", UTILISATEUR),
    (_DRAW, "a"): ("lien", UTILISATEUR),
    (_FORM, "button"): ("lien", UTILISATEUR),
    (_META, "template"): ("modèle", OUVERTURE),
    (_META, "auto-reload"): ("rechargement", OUVERTURE),
}
"""Éléments dont la référence ``xlink:href`` hors de l'archive est chargée ou suivie ; tout
autre est observé ``autre``, sans déclencheur."""
_OBJETS_ODF = {
    (_DRAW, "object-ole"): "OLE",
    (_DRAW, "applet"): "applet",
    (_DRAW, "plugin"): "plugin",
}
_DDE = frozenset({(_TEXT, "dde-connection-decl"), (_OFFICE, "dde-source")})
_ORDINAIRES = frozenset(
    {"application/vnd.oasis.opendocument.chart", "application/vnd.oasis.opendocument.formula"}
)
"""Documents incorporés ordinaires : graphique, formule (comme le graphique d'un DOCX)."""
_SCHEMAS_INTERNES = ("vnd.sun.star.package:", "vnd.sun.star.graphicobject:")
_SCHEMAS_MACROS = ("macro:", "vnd.sun.star.script:")
"""Une référence de ces schémas appelle une macro, au clic : c'est un événement."""


def _schema(reference: str) -> str | None:
    """Schéma d'une adresse (RFC 3986, §3.1), en minuscules, deux-points compris."""
    schema, deux_points, _ = reference.partition(":")
    if (
        deux_points
        and schema[:1].isascii()
        and schema[:1].isalpha()
        and all(c.isascii() and (c.isalnum() or c in "+-.") for c in schema)
    ):
        return f"{schema.lower()}:"
    return None


def _hors_archive(reference: str) -> bool:
    """Vrai pour une référence qui sort de l'archive : adresse à schéma, chemin absolu, chemin
    qui remonte au-dessus du paquet (OpenDocument, partie 3, §3.5)."""
    schema = _schema(reference)
    if schema is not None:
        return not schema.startswith(_SCHEMAS_INTERNES)
    chemin = reference.replace("\\", "/")
    if chemin.startswith("/"):
        return True
    profondeur = 0
    for segment in chemin.split("/"):
        if segment == "..":
            profondeur -= 1
            if profondeur < 0:
                return True
        elif segment not in ("", "."):
            profondeur += 1
    return False


def _odt(recherche: _Recherche) -> None:
    _macros_odt(recherche)
    types = _manifeste(recherche)
    for nom in ("content.xml", "styles.xml", "meta.xml"):
        if not recherche.continuer():
            return
        try:
            entree = recherche.trouver(nom, casse=True)
        except Illisible as illisible:
            recherche.non_mener(illisible)
            continue
        if entree is None:
            continue
        lue = recherche.lire(entree)
        if lue is None:
            continue
        donnees, localisation = lue
        recherche.parties += 1
        if not _partie_odt(recherche, donnees, types) and not recherche.arrete:
            recherche.contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)


def _macros_odt(recherche: _Recherche) -> None:
    """Bibliothèques Basic qui ont un module, et langages de ``Scripts/``, par les noms des
    entrées ; ni les noms ni le code ne sont lus."""
    bibliotheques: set[str] = set()
    langages: set[str] = set()
    for entree in recherche.archive.entrees:
        segments = entree.nom.split("/")
        if entree.nom.endswith("/") or len(segments) < 3:
            continue
        if segments[0] == "Basic" and len(segments) == 3 and segments[2] not in _INDEX_BASIC:
            bibliotheques.add(segments[1])
        elif segments[0] == "Scripts":
            langages.add(segments[1].lower())
    for _ in sorted(bibliotheques):
        recherche.ajouter(_MACROS, "Basic")
    for langage in sorted(langages):
        recherche.ajouter(_MACROS, _LANGAGES.get(langage, AUTRE))


def _manifeste(recherche: _Recherche) -> dict[str, str]:
    """Types des entrées que déclare ``META-INF/manifest.xml``, par chemin."""
    try:
        entree = recherche.trouver("META-INF/manifest.xml", casse=True)
    except Illisible as illisible:
        recherche.non_mener(illisible)
        return {}
    lue = None if entree is None else recherche.lire(entree)
    if lue is None:
        return {}
    donnees, localisation = lue
    types: dict[str, str] = {}

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        if espace == _MANIFESTE and nom == "encryption-data":
            recherche.chiffre = True
        elif espace == _MANIFESTE and nom == "file-entry":
            chemin = attributs.get((_MANIFESTE, "full-path"))
            if chemin is not None:
                types[chemin.removeprefix("./").rstrip("/")] = attributs.get(
                    (_MANIFESTE, "media-type"), ""
                )

    recherche.parties += 1
    if not recherche.parcourir(donnees, ouvrir, lambda: None) and not recherche.arrete:
        recherche.contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
    return types


def _partie_odt(recherche: _Recherche, donnees: bytes, types: dict[str, str]) -> bool:
    """Éléments d'une partie XML d'un ODT ; vrai si elle a été lue en entier."""
    pile: list[tuple[str, str]] = []

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        element = (espace, nom)
        if element == (_SCRIPT, "event-listener"):
            recherche.ajouter(_EVENEMENTS, MACRO, _declencheur(pile, attributs))
        else:
            _references(recherche, element, attributs, types)
        pile.append(element)

    return recherche.parcourir(donnees, ouvrir, pile.pop)


def _declencheur(pile: list[tuple[str, str]], attributs: dict[tuple[str, str], str]) -> str:
    """Événement du document s'il est déclaré sous ``office:scripts`` de la racine ; sinon,
    événement d'un contrôle, d'un lien ou d'une image : un geste de l'utilisateur."""
    if pile[1:] != [(_OFFICE, "scripts"), (_OFFICE, "event-listeners")]:
        return UTILISATEUR
    nom = attributs.get((_SCRIPT, "event-name"), "")
    return OUVERTURE if nom in _OUVERTURE_ODF else DOCUMENT


def _references(
    recherche: _Recherche,
    element: tuple[str, str],
    attributs: dict[tuple[str, str], str],
    types: dict[str, str],
) -> None:
    reference = attributs.get((_XLINK, "href"))
    if element in _OBJETS_ODF:
        recherche.ajouter(_OBJETS, _OBJETS_ODF[element])
    elif element == (_DRAW, "object") and reference is not None and not _hors_archive(reference):
        chemin = reference.removeprefix("./").rstrip("/")
        if types.get(chemin) not in _ORDINAIRES:
            recherche.ajouter(_OBJETS, "document")
    if element in _DDE:
        automatique = attributs.get((_OFFICE, "automatic-update")) == "true"
        recherche.ajouter(_EXTERNES, "DDE", OUVERTURE if automatique else UTILISATEUR)
    if reference is None:
        return
    if (_schema(reference) or "").startswith(_SCHEMAS_MACROS):
        recherche.ajouter(_EVENEMENTS, MACRO, UTILISATEUR)
    elif _hors_archive(reference):
        nature, declencheur = _EXTERNES_ODF.get(element, (AUTRE, None))
        recherche.ajouter(_EXTERNES, nature, declencheur)


# Observations


def _observer(recherche: _Recherche) -> None:
    contexte = recherche.contexte
    contexte.observer("actifsbureau.parties", recherche.parties, localisation=_LOCALISATION)
    if recherche.chiffre:
        contexte.observer("actifsbureau.chiffre", True)
    if recherche.arrete:
        contexte.observer("actifsbureau.arret_avant_budget", True)
    if recherche.coupee:
        contexte.observer("actifsbureau.recherche_coupee", True)
    elements = recherche.elements
    for famille in (_MACROS, _EVENEMENTS, _OBJETS, _EXTERNES):
        _famille(contexte, famille, [e for e in elements if e.famille == famille])
    automatiques = [e for e in elements if e.declencheurs & _AUTOMATIQUES]
    _famille(contexte, "automatiques", automatiques, automatiques=True)


def _famille(
    contexte: Contexte, nom: str, elements: list[_Element], *, automatiques: bool = False
) -> None:
    """Nombre d'éléments d'une famille ; s'il y en a, leurs natures et leurs déclencheurs."""
    contexte.observer(f"actifsbureau.{nom}", len(elements))
    if not elements:
        return
    # Ordre de la famille ; pour les éléments automatiques, événements puis références.
    rangees = (nom,) if nom in NATURES else (_EVENEMENTS, _EXTERNES)
    vues = {e.nature for e in elements}
    natures = [n for f in rangees for n in NATURES[f] if n in vues]
    valeurs.observer(contexte, f"actifsbureau.{nom}.natures", natures)
    declencheurs = {d for e in elements for d in e.declencheurs}
    if automatiques:
        declencheurs &= _AUTOMATIQUES
    if declencheurs:
        ordonnes = [d for d in DECLENCHEURS if d in declencheurs]
        valeurs.observer(contexte, f"actifsbureau.{nom}.declencheurs", ordonnes)


def _ascii_minuscules(texte: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in texte)
