"""Module ``imagesbureau`` : images d'un DOCX ou d'un ODT, acheminées vers les modules d'image
(F-63 étendue par A-24 ; complément de T81, ADR-0252 à ADR-0255 ; fiche ``images-bureau``).

Le module cherche les images parmi toutes les entrées de l'archive, dans l'ordre du répertoire
central, qu'un texte les cite ou non (ADR-0253). Une entrée est une image si le document la
déclare ainsi : par les types de contenu (``[Content_Types].xml``) d'un DOCX, extension ou nom
de partie, sans casse (ECMA-376, partie 2, §10.1.2) ; par le manifeste (``META-INF/manifest.xml``)
d'un ODT (ODF 1.3, partie 2, §4). Le format donné au moteur est celui de ce type déclaré : le
moteur le vérifie par l'identification, et déclare non mené pour format partiel un contenu d'un
autre format (ADR-0224).

Une image JPEG, PNG, WebP ou HEIC est acheminée vers les modules d'image comme une partie
extraite : stockée telle quelle, elle est lue en place, par sa plage ; compressée par deflate,
elle est décompressée ici, au plus :data:`TAILLE_MAX_IMAGE` octets, et le moteur l'analyse en
mémoire (ADR-0254). Elles le sont seize au plus, tant que leur taille cumulée n'a pas atteint
2 Mio (ADR-0226) ; les suivantes sont comptées, et le moteur déclare non menée la première
d'entre elles. La vignette du document (relation ``thumbnail`` du paquet d'un DOCX,
``Thumbnails/thumbnail.png`` d'un ODT), rendue par le logiciel à partir de la première page,
est comptée à part, non acheminée. Les images d'un autre type (GIF, EMF, WMF, SVG, TIFF, BMP…)
sont comptées par type, non analysées. Un ODT protégé par un mot de passe est dit chiffré : rien
n'est déchiffré (ADR-0126) ; une image chiffrée est comptée, non acheminée, et un paquet chiffré
en entier (``encrypted-package`` d'ODF 1.4) ne déclare plus d'images.

Le module n'émet aucun constat : les règles du catalogue lisent ses observations (ADR-0255).
"""

from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import unquote

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Contexte, TailleDepassee
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.arbre import Ouvrir, parcourir
from voight_kampff.modules._lecture.zip import Archive, Entree, Illisible
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee

__all__ = ["FORMATS", "TAILLE_MAX_IMAGE", "TYPE_MAX", "analyser", "format_du_type"]

FORMATS = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heic",
}
"""Types déclarés des images que lisent les modules d'image, et leur format (ADR-0253)."""
TAILLE_MAX_IMAGE = TAILLE_MAX_LECTURE
"""Contenu décompressé au plus d'une image compressée ; au-delà, elle est comptée, non
acheminée (ADR-0254). Une image stockée telle quelle n'est pas lue ici : elle n'a pas de borne."""
TYPE_MAX = 127
"""Longueur au plus d'un type déclaré gardé dans les observations (RFC 6838, §4.2)."""

_TYPES_DE_CONTENU = "http://schemas.openxmlformats.org/package/2006/content-types"
_RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
_VIGNETTE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
"""Type de la relation du paquet vers sa vignette (ECMA-376, partie 2, annexe E), le même en
transitionnel et en strict."""
_MANIFESTE = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
_VIGNETTE_ODT = "Thumbnails/thumbnail.png"
"""Vignette d'un ODT (ODF 1.3, partie 2, §3.3)."""
_LOCALISATION = Localisation(chemin="entrées de l'archive")


def format_du_type(type_: str) -> str | None:
    """Format d'un type déclaré, sans ses paramètres ni sa casse (RFC 2045, §5.1) ; ``None`` pour
    un type que les modules d'image ne lisent pas."""
    return FORMATS.get(type_.partition(";")[0].strip().lower())


def _est_image(type_: str) -> bool:
    return type_.partition(";")[0].strip().lower().startswith("image/")


def _ascii_minuscules(texte: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in texte)


@dataclass(slots=True)
class _Declarations:
    """Ce que le document déclare de ses entrées : type de chacune, vignette, chiffrement."""

    types: dict[str, str] = field(default_factory=dict)
    """Type déclaré par nom d'entrée ; pour un DOCX, par nom sans casse."""
    defauts: dict[str, str] = field(default_factory=dict)
    """Type par extension, sans casse (DOCX seulement)."""
    vignettes: set[str] = field(default_factory=set)
    chiffrees: set[str] = field(default_factory=set)
    """Entrées chiffrées par le manifeste d'un ODT (mot de passe) : le paquet entier, ou chaque
    entrée."""
    casse: bool = True
    """Faux pour un DOCX, dont les noms de parties se comparent sans casse (OPC)."""

    def cle(self, nom: str) -> str:
        return nom if self.casse else _ascii_minuscules(nom)

    def type_de(self, nom: str) -> str | None:
        declare = self.types.get(self.cle(nom))
        if declare is not None or self.casse:
            return declare
        extension = nom.rpartition("/")[2].rpartition(".")
        return self.defauts.get(_ascii_minuscules(extension[2])) if extension[1] else None


class _Lecture:
    """Parties XML lues pour les déclarations ; la première illisible est non menée."""

    def __init__(self, contexte: Contexte, archive: Archive) -> None:
        self.contexte = contexte
        self.archive = archive
        self.non_menee = False

    def non_mener(self, illisible: Illisible) -> None:
        if not self.non_menee:
            self.non_menee = True
            self.contexte.non_mener(
                illisible.raison, localisation=illisible.localisation(self.contexte.taille)
            )

    def parcourir(self, nom: str, ouvrir: Ouvrir, *, casse: bool) -> bool:
        """Lit la partie ``nom`` élément par élément ; faux si elle est absente ou illisible."""
        try:
            entree = self.archive.trouver(nom, casse=casse)
            if entree is None:
                return False
            donnees = self.archive.lire(entree)
            localisation = self.archive.localisation(entree)
        except Illisible as illisible:
            self.non_mener(illisible)
            return False
        if parcourir(self.contexte, donnees, ouvrir, lambda: None):
            if not self.non_menee:
                self.non_menee = True
                self.contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
            return False
        return True


def _docx(lecture: _Lecture) -> _Declarations:
    declarations = _Declarations(casse=False)

    def types(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        if espace != _TYPES_DE_CONTENU:
            return
        type_ = attributs.get(("", "ContentType"))
        if type_ is None:
            return
        if nom == "Default" and (extension := attributs.get(("", "Extension"))) is not None:
            declarations.defauts.setdefault(_ascii_minuscules(extension), type_)
        elif nom == "Override" and (partie := attributs.get(("", "PartName"))) is not None:
            nom_ = declarations.cle(unquote(partie).removeprefix("/"))
            declarations.types.setdefault(nom_, type_)

    def relations(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        if (espace, nom) != (_RELATIONS, "Relationship"):
            return
        if attributs.get(("", "Type")) != _VIGNETTE or attributs.get(("", "TargetMode")):
            return  # une cible externe n'est pas dans l'archive
        cible = attributs.get(("", "Target"))
        if cible is not None:
            declarations.vignettes.add(declarations.cle(_racine(cible)))

    lecture.parcourir("[Content_Types].xml", types, casse=False)
    lecture.parcourir("_rels/.rels", relations, casse=False)
    return declarations


def _racine(cible: str) -> str:
    """Nom d'entrée d'une cible relative à la racine du paquet."""
    segments: list[str] = []
    for segment in unquote(cible).split("/"):
        if segment == "..":
            if segments:
                segments.pop()
        elif segment not in ("", "."):
            segments.append(segment)
    return "/".join(segments)


def _odt(lecture: _Lecture) -> _Declarations:
    declarations = _Declarations(vignettes={_VIGNETTE_ODT})
    entree: list[str] = []

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        if espace != _MANIFESTE:
            return
        if nom == "file-entry":
            chemin = attributs.get((_MANIFESTE, "full-path"), "").removeprefix("./")
            entree[:] = [chemin]
            declarations.types.setdefault(chemin, attributs.get((_MANIFESTE, "media-type"), ""))
        elif nom == "encryption-data" and entree:
            declarations.chiffrees.add(entree[0])

    lecture.parcourir("META-INF/manifest.xml", ouvrir, casse=True)
    return declarations


@dataclass(slots=True)
class _Releve:
    images: int = 0
    vignettes: int = 0
    acheminables: list[tuple[Entree, str]] = field(default_factory=list)
    autres: Counter[str] = field(default_factory=Counter)


def _relever(archive: Archive, declarations: _Declarations) -> _Releve:
    releve = _Releve()
    for entree in archive.entrees:
        if entree.nom.endswith("/"):
            continue
        type_ = declarations.type_de(entree.nom)
        if type_ is None or not _est_image(type_):
            continue
        if declarations.cle(entree.nom) in declarations.vignettes:
            releve.vignettes += 1
            continue
        releve.images += 1
        format_ = format_du_type(type_)
        if entree.nom in declarations.chiffrees:
            continue  # comptée parmi les images, ni lue ni acheminée (ADR-0126)
        if format_ is None:
            releve.autres[type_.partition(";")[0].strip().lower()[:TYPE_MAX]] += 1
        else:
            releve.acheminables.append((entree, format_))
    return releve


def analyser(contexte: Contexte) -> None:
    try:
        archive = Archive(contexte)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    lecture = _Lecture(contexte, archive)
    declarations = _odt(lecture) if contexte.format_reel == "odt" else _docx(lecture)
    releve = _relever(archive, declarations)
    contexte.observer("imagesbureau.images", releve.images, localisation=_LOCALISATION)
    if releve.vignettes:
        contexte.observer("imagesbureau.vignette", True)
    _acheminer(contexte, lecture, releve.acheminables)
    autres = releve.autres
    contexte.observer("imagesbureau.non_acheminees", sum(autres.values()))
    if autres:
        valeurs.observer(contexte, "imagesbureau.non_acheminees.types", sorted(autres))
    if declarations.chiffrees:
        contexte.observer("imagesbureau.chiffre", True)


def _acheminer(contexte: Contexte, lecture: _Lecture, images: list[tuple[Entree, str]]) -> None:
    """Donne au moteur chaque image, dans l'ordre du répertoire central (ADR-0226, ADR-0254)."""
    archive = lecture.archive
    formats: set[str] = set()
    acheminees = decompressees = au_dela = trop_grandes = 0
    for entree, format_ in images:
        localisation = Localisation(chemin=entree.nom)
        try:
            plage = archive.donnees(entree)
            if plage is None:
                continue  # entrée vide : rien à analyser, comptée parmi les images
            contenu = None
            if archive.compressee(entree) and contexte.extraction_possible:
                contenu = archive.lire(entree, TAILLE_MAX_IMAGE)
        except TailleDepassee:
            trop_grandes += 1
            continue
        except Illisible as illisible:
            lecture.non_mener(illisible)
            continue
        if contenu == b"":
            continue
        # Plus de place : l'extraction est refusée sans que rien soit décompressé, et le moteur
        # déclare non menée la première refusée (ADR-0226).
        if contexte.extraire(format_, plage, localisation, contenu):
            acheminees += 1
            decompressees += contenu is not None
            formats.add(format_)
        else:
            au_dela += 1
    contexte.observer("imagesbureau.acheminables", len(images))
    contexte.observer("imagesbureau.acheminees", acheminees)
    if formats:
        valeurs.observer(contexte, "imagesbureau.acheminees.formats", sorted(formats))
    if decompressees:
        contexte.observer("imagesbureau.decompressees", decompressees)
    if au_dela:
        contexte.observer("imagesbureau.au_dela", au_dela)
    if trop_grandes:
        contexte.observer("imagesbureau.trop_grandes", trop_grandes)
