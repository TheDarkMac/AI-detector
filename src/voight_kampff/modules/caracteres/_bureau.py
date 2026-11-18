"""Texte d'un DOCX ou d'un ODT, paragraphe par paragraphe (complément de T80, ADR-0239 à
ADR-0242).

Le texte est tiré des parties XML que le logiciel affiche (ADR-0239) :

- DOCX (ECMA-376, partie 1, §17) : la partie principale, que désignent les relations du paquet,
  puis, par ses relations, ses en-têtes et pieds de page, notes de bas de page et de fin et
  commentaires. Texte : ``w:t`` ; ``w:delText`` d'une suppression suivie ; tabulation, saut de
  ligne, trait d'union insécable et conditionnel rendus par leur caractère. Les codes de champ
  (``w:instrText``) ne s'affichent pas : ils ne sont pas lus. Une course (``w:r``) dont les
  propriétés portent ``w:vanish`` est masquée ; le texte d'une suppression (``w:del``,
  ``w:moveFrom``) est supprimé.
- ODT (OpenDocument 1.3, partie 3) : ``content.xml`` (corps, notes, annotations, zones de
  texte), puis les en-têtes et pieds de page des pages types de ``styles.xml``. Texte : tout le
  texte d'un paragraphe (``text:p``, ``text:h``) hors des métadonnées (``dc:``, ``meta:``) et
  des descriptions (``svg:``) ; ``text:s``, ``text:tab``, ``text:line-break`` rendus par leur
  caractère. Est masqué le texte d'un paragraphe ou d'une portion dont le style, automatique ou
  commun, a ``text:display="none"`` ; supprimé, celui d'une suppression suivie
  (``text:deletion``).

Un paragraphe contenu dans un autre (zone de texte, note) est un paragraphe à part, numéroté
dans l'ordre où il s'ouvre. Les numéros de paragraphe comptent à partir de 1 dans chaque partie.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from urllib.parse import unquote

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture.arbre import lire_arbre, parcourir
from voight_kampff.modules._lecture.zip import Archive, Entree, Illisible
from voight_kampff.rapport.modele import Localisation, Plage, RaisonNonMenee

__all__ = ["Paragraphe", "Partie", "lire"]

_RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
_PREFIXES = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/",
    "http://purl.oclc.org/ooxml/officeDocument/relationships/",
)
"""Espaces des types de relations, transitionnel et strict (ECMA-376, partie 1)."""
_PRINCIPALE = "officeDocument"
_ANNEXES = ("header", "footer", "footnotes", "endnotes", "comments")
"""Relations de la partie principale lues, dans l'ordre de lecture."""
_W = frozenset(
    {
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://purl.oclc.org/ooxml/wordprocessingml/main",
    }
)
_CARACTERES_W = {"tab": "\t", "br": "\n", "cr": "\n", "noBreakHyphen": "\u2011"}
_CARACTERES_W |= {"softHyphen": "\u00ad"}
_FAUX = frozenset({"0", "false", "off"})

_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_STYLE = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
_EXCLUS_ODF = frozenset(
    {
        "http://purl.org/dc/elements/1.1/",
        "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
        "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
        "http://www.w3.org/2000/svg",
    }
)
"""Espaces dont le texte n'est pas celui du document : auteur et date d'une annotation ou d'une
modification, titre et description d'une image."""
_PAGES_TYPES = frozenset({"header", "header-left", "header-first", "footer", "footer-left"})
_PAGES_TYPES |= {"footer-first"}


@dataclass(slots=True)
class Paragraphe:
    """Texte d'un paragraphe et ses passages supprimés ou masqués (indices dans le texte)."""

    numero: int
    morceaux: list[str] = field(default_factory=list)
    longueur: int = 0
    supprimes: list[tuple[int, int]] = field(default_factory=list)
    masques: list[tuple[int, int]] = field(default_factory=list)

    @property
    def texte(self) -> str:
        return "".join(self.morceaux)

    def ajouter(self, texte: str, *, supprime: bool, masque: bool) -> None:
        """Ajoute un morceau, jamais vide : expat ne rend pas de texte vide."""
        debut, self.longueur = self.longueur, self.longueur + len(texte)
        self.morceaux.append(texte)
        if supprime:
            _etendre(self.supprimes, debut, self.longueur)
        if masque:
            _etendre(self.masques, debut, self.longueur)


def _etendre(passages: list[tuple[int, int]], debut: int, fin: int) -> None:
    if passages and passages[-1][1] == debut:
        passages[-1] = (passages[-1][0], fin)
    else:
        passages.append((debut, fin))


@dataclass(slots=True)
class Partie:
    """Partie XML lue : son nom, ses octets dans l'archive, ses paragraphes."""

    nom: str
    octets: Plage
    paragraphes: list[Paragraphe] = field(default_factory=list)


class _Lecture:
    """Paragraphes d'une partie, à mesure de la lecture : les paragraphes s'emboîtent."""

    def __init__(self, partie: Partie) -> None:
        self.partie = partie
        self.ouverts: list[Paragraphe] = []
        self.compte = 0

    def ouvrir(self) -> None:
        self.compte += 1
        self.ouverts.append(Paragraphe(self.compte))

    def fermer(self) -> None:
        paragraphe = self.ouverts.pop()
        if paragraphe.longueur:
            self.partie.paragraphes.append(paragraphe)

    def ajouter(self, texte: str, *, supprime: bool, masque: bool) -> None:
        if self.ouverts:
            self.ouverts[-1].ajouter(texte, supprime=supprime, masque=masque)

    def finir(self) -> None:
        """Lecture arrêtée en cours de route : les paragraphes ouverts sont gardés."""
        while self.ouverts:
            self.fermer()
        self.partie.paragraphes.sort(key=lambda paragraphe: paragraphe.numero)


def lire(contexte: Contexte) -> Iterator[Partie]:
    """Parties lues du DOCX ou de l'ODT, dans l'ordre de lecture ; une partie manquante ou
    illisible est déclarée non menée, et la lecture passe à la suivante."""
    try:
        archive = Archive(contexte)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    if contexte.format_reel == "odt":
        yield from _odt(contexte, archive)
    else:
        yield from _docx(contexte, archive)


def _trouver(contexte: Contexte, archive: Archive, nom: str, *, casse: bool) -> Entree | None:
    """Entrée de ce nom ; ``None`` si elle manque, ou si deux entrées portent ce nom (ce que
    le lecteur ZIP refuse) : ce cas-là est déclaré non mené ici."""
    try:
        return archive.trouver(nom, casse=casse)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=Localisation(chemin=nom))
        raise _DejaDeclaree from None


class _DejaDeclaree(Exception):
    """Partie illisible, déjà déclarée non menée : l'appelant passe à la suivante."""


def _donnees(contexte: Contexte, archive: Archive, entree: Entree) -> bytes | None:
    try:
        return archive.lire(entree)
    except Illisible as illisible:
        # La localisation de l'entrée relirait l'en-tête qui vient d'échouer : celle de l'arrêt.
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return None


def _partie(archive: Archive, entree: Entree) -> Partie:
    octets = archive.localisation(entree).octets
    return Partie(entree.nom, octets or Plage(0, 1))


def _partiel(contexte: Contexte, archive: Archive, entree: Entree) -> None:
    contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=archive.localisation(entree))


# DOCX


def _cible(source: str, cible: str) -> str | None:
    """Nom de la partie que désigne une cible relative à la partie source (OPC, partie 2)."""
    dossier = source.rpartition("/")[0]
    chemin = unquote(cible)
    if all(segment in ("", ".", "..") for segment in chemin.split("/")):
        return None
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


def _type(relation: str) -> str | None:
    for prefixe in _PREFIXES:
        if relation.startswith(prefixe):
            return relation.removeprefix(prefixe)
    return None


def _relations(contexte: Contexte, archive: Archive, source: str) -> list[tuple[str, str]] | None:
    """(type, partie) des relations internes d'une partie ; ``None`` si elles manquent."""
    dossier, _, nom = source.rpartition("/")
    chemin = f"{dossier}/_rels/{nom}.rels" if dossier else f"_rels/{nom}.rels"
    try:
        entree = _trouver(contexte, archive, chemin, casse=False)
    except _DejaDeclaree:
        return []
    if entree is None:
        return None
    donnees = _donnees(contexte, archive, entree)
    if donnees is None:
        return []
    racines, partiel = lire_arbre(contexte, donnees)
    if partiel:
        _partiel(contexte, archive, entree)
    trouvees = []
    for racine in racines:
        for relation in racine.enfants:
            if not relation.est(_RELATIONS, "Relationship"):
                continue
            if relation.attributs.get(("", "TargetMode")) == "External":
                continue
            nature = _type(relation.attributs.get(("", "Type"), ""))
            cible = _cible(source, relation.attributs.get(("", "Target"), ""))
            if nature is not None and cible is not None:
                trouvees.append((nature, cible))
    return trouvees


def _docx(contexte: Contexte, archive: Archive) -> Iterator[Partie]:
    paquet = _relations(contexte, archive, "") or []
    principale = next((cible for nature, cible in paquet if nature == _PRINCIPALE), None)
    if principale is None:
        contexte.non_mener(
            RaisonNonMenee.REFERENCE_MANQUANTE, localisation=Localisation("_rels/.rels")
        )
        return
    annexes = _relations(contexte, archive, principale) or []
    noms = [principale]
    for nature in _ANNEXES:
        noms += sorted({cible for type_, cible in annexes if type_ == nature})
    for nom in dict.fromkeys(noms):
        try:
            entree = _trouver(contexte, archive, nom, casse=False)
        except _DejaDeclaree:
            continue
        if entree is None:
            contexte.non_mener(RaisonNonMenee.REFERENCE_MANQUANTE, localisation=Localisation(nom))
            continue
        donnees = _donnees(contexte, archive, entree)
        if donnees is not None:
            yield _lire_docx(contexte, archive, entree, donnees)


def _lire_docx(contexte: Contexte, archive: Archive, entree: Entree, donnees: bytes) -> Partie:
    partie = _partie(archive, entree)
    lecture = _Lecture(partie)
    pile: list[str] = []
    """Noms locaux des éléments WordprocessingML ouverts (autres espaces : chaîne vide)."""
    courses: list[bool] = []
    """Pour chaque course ouverte (``w:r``) : masquée par ``w:vanish``."""
    suppressions = 0

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        nonlocal suppressions
        local = nom if espace in _W else ""
        pile.append(local)
        if local == "p":
            lecture.ouvrir()
        elif local == "r":
            courses.append(False)
        elif local in ("del", "moveFrom"):
            suppressions += 1
        elif local == "vanish" and courses and len(pile) >= 2 and pile[-2] == "rPr":
            valeur = next((v for (_, a), v in attributs.items() if a == "val"), "true")
            courses[-1] = valeur.lower() not in _FAUX
        elif local in _CARACTERES_W:
            ajouter(_CARACTERES_W[local])

    def ajouter(texte: str) -> None:
        lecture.ajouter(texte, supprime=suppressions > 0, masque=bool(courses and courses[-1]))

    def fermer() -> None:
        nonlocal suppressions
        local = pile.pop()
        if local == "p":
            lecture.fermer()
        elif local == "r":
            courses.pop()
        elif local in ("del", "moveFrom"):
            suppressions -= 1

    def texte(contenu: str) -> None:
        if pile and pile[-1] in ("t", "delText"):
            ajouter(contenu)

    if parcourir(contexte, donnees, ouvrir, fermer, texte):
        _partiel(contexte, archive, entree)
    lecture.finir()
    return partie


# ODT


def _odt(contexte: Contexte, archive: Archive) -> Iterator[Partie]:
    try:
        styles = _trouver(contexte, archive, "styles.xml", casse=True)
    except _DejaDeclaree:
        styles = None
    contenu_illisible = False
    try:
        contenu = _trouver(contexte, archive, "content.xml", casse=True)
    except _DejaDeclaree:
        contenu, contenu_illisible = None, True
    communs: set[str] = set()
    pages: Partie | None = None
    if styles is not None:
        donnees = _donnees(contexte, archive, styles)
        if donnees is not None:
            pages = _lire_odt(contexte, archive, styles, donnees, communs, pages_types=True)
    if contenu is None and not contenu_illisible:
        contexte.non_mener(
            RaisonNonMenee.REFERENCE_MANQUANTE, localisation=Localisation("content.xml")
        )
    elif contenu is not None:
        donnees = _donnees(contexte, archive, contenu)
        if donnees is not None:
            yield _lire_odt(contexte, archive, contenu, donnees, communs, pages_types=False)
    if pages is not None:
        yield pages


def _lire_odt(
    contexte: Contexte,
    archive: Archive,
    entree: Entree,
    donnees: bytes,
    communs: set[str],
    *,
    pages_types: bool,
) -> Partie:
    """Paragraphes de ``content.xml``, ou des pages types de ``styles.xml``. ``communs`` reçoit
    les styles communs de ``styles.xml`` qui ne s'affichent pas (``office:styles``), qui valent
    aussi pour ``content.xml`` ; les styles automatiques valent pour leur seule partie."""
    partie = _partie(archive, entree)
    masques = set(communs)
    communs_ouverts = 0
    lecture = _Lecture(partie)
    pile: list[tuple[str, str, bool]] = []
    """Éléments ouverts : espace, nom local, masqué (par lui ou un parent)."""
    style: list[str] = []
    """Nom du style en cours de définition."""
    suppressions = 0
    lisible = not pages_types
    """En dehors des pages types de styles.xml, aucun paragraphe n'est lu."""
    profondeur_pages = 0

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        nonlocal suppressions, lisible, profondeur_pages, communs_ouverts
        parent_masque = bool(pile) and pile[-1][2]
        nom_style = attributs.get((_TEXT, "style-name"), "")
        masque = parent_masque or (espace == _TEXT and nom_style in masques)
        pile.append((espace, nom, masque))
        if espace == _OFFICE and nom == "styles":
            communs_ouverts += 1
        elif espace == _STYLE and nom == "style":
            style.append(attributs.get((_STYLE, "name"), ""))
        elif espace == _STYLE and nom == "text-properties" and style:
            if attributs.get((_TEXT, "display")) == "none":
                masques.add(style[-1])
                if communs_ouverts:
                    communs.add(style[-1])
        elif pages_types and espace == _STYLE and nom in _PAGES_TYPES:
            profondeur_pages += 1
            lisible = True
        if not lisible:
            return
        if espace == _TEXT and nom in ("p", "h"):
            lecture.ouvrir()
        elif espace == _TEXT and nom == "deletion":
            suppressions += 1
        elif espace == _TEXT and nom == "s":
            ajouter(" " * _nombre(attributs.get((_TEXT, "c"), "1")))
        elif espace == _TEXT and nom == "tab":
            ajouter("\t")
        elif espace == _TEXT and nom == "line-break":
            ajouter("\n")

    def ajouter(texte: str) -> None:
        masque = bool(pile) and pile[-1][2]
        lecture.ajouter(texte, supprime=suppressions > 0, masque=masque)

    def fermer() -> None:
        nonlocal suppressions, lisible, profondeur_pages, communs_ouverts
        espace, nom, _masque = pile.pop()
        if espace == _OFFICE and nom == "styles":
            communs_ouverts -= 1
        elif espace == _STYLE and nom == "style" and style:
            style.pop()
        if lisible and espace == _TEXT and nom in ("p", "h"):
            lecture.fermer()
        elif lisible and espace == _TEXT and nom == "deletion":
            suppressions -= 1
        if pages_types and espace == _STYLE and nom in _PAGES_TYPES:
            profondeur_pages -= 1
            lisible = profondeur_pages > 0

    def texte(contenu: str) -> None:
        if lisible and pile and pile[-1][0] not in _EXCLUS_ODF:
            ajouter(contenu)

    if parcourir(contexte, donnees, ouvrir, fermer, texte):
        _partiel(contexte, archive, entree)
    lecture.finir()
    return partie


def _nombre(valeur: str) -> int:
    """Nombre d'espaces de ``text:s`` : 1 par défaut, borné à 1 024."""
    return min(int(valeur), 1024) if valeur.isdigit() and int(valeur) > 0 else 1
