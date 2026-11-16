"""Module ``revisionspdf`` : versions successives d'un PDF et leur chronologie (F-60, F-84 ;
ADR-0207 à ADR-0212 ; fiche ``revisions-pdf``).

Une mise à jour incrémentale ajoute à la fin du fichier les objets qu'elle change, puis une
section de références croisées dont ``/Prev`` désigne la précédente (ISO 32000-2, §7.5.6) : les
versions antérieures restent dans le fichier, et la version *k* en est le début, jusqu'à la fin
de sa marque ``%%EOF``. Le module :

1. regroupe les sections de la chaîne en versions : les deux sections d'un document linéarisé
   (annexe F) n'en font qu'une, comme une table classique et la section en flux qui la
   complète (``/XRefStm``) ; il donne la fin de chaque version, qui suffit à la reconstituer
   (ADR-0207) ;
2. compare chaque version à la précédente, entrée par entrée : objets ajoutés, remplacés,
   supprimés ; il range ces objets d'après leur type et ce qui les désigne, et en tire la
   nature de la version : signature, formulaire, annotation, métadonnées, ou non reconnue
   (ADR-0208) ;
3. lit les signatures du formulaire par leur seule structure : la plage signée (``/ByteRange``)
   comparée aux fins de version, sans vérification cryptographique (ADR-0209) ;
4. rend la chronologie des versions en tableau (ADR-0212).

Rien n'est déchiffré : dans un document chiffré, les objets rangés dans des flux d'objets ne se
lisent pas, ni les dates (ADR-0210). Le module n'émet aucun constat : les règles du catalogue
lisent ses observations (ADR-0211).
"""

from collections.abc import Iterator
from dataclasses import dataclass, field

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.pdf import (
    Document,
    Entree,
    Flux,
    Illisible,
    Nom,
    Objet,
    Ref,
    entier,
    texte,
)
from voight_kampff.rapport.modele import (
    Localisation,
    NatureVisualisation,
    Plage,
)

__all__ = ["LIGNES_MAX", "NATURES", "SIGNATURES_MAX", "analyser"]

SIGNATURE = "signature"
FORMULAIRE = "formulaire"
ANNOTATION = "annotation"
METADONNEES = "metadonnees"
NON_RECONNUE = "non_reconnue"
NON_LUE = "non_lue"
NATURES = (SIGNATURE, FORMULAIRE, ANNOTATION, METADONNEES, NON_RECONNUE, NON_LUE)
"""Natures d'une version postérieure à la première, dans l'ordre où elles s'écrivent."""
ORIGINALE = "originale"
"""Nature de la première version."""
STRUCTURE = "structure"
"""Nature d'une version qui ne change que des objets de structure (sections, flux d'objets,
catalogue ou arbre des pages inchangés en substance)."""
PERMISES = frozenset({SIGNATURE, FORMULAIRE, ANNOTATION, METADONNEES})
"""Natures d'un ajout reconnu comme légitime (F-60, ADR-0208)."""

LIGNES_MAX = 256
"""Versions au plus dans le tableau de la chronologie ; les observations les comptent toutes."""
SIGNATURES_MAX = 32
"""Signatures au plus décrites une à une ; ``revisionspdf.signatures`` les compte toutes."""
_CONTENU_MAX = 1 << 20
"""Octets au plus de la valeur ``/Contents`` d'une signature, relus pour vérifier la plage."""
_DATE_MAX = 64
"""Caractères au plus d'une date déclarée au tableau ; au-delà, elle n'y figure pas."""
_ELEMENTS_MAX = 4096
"""Éléments au plus d'un tableau indirect examiné pour le ranger (``/Annots``, ``/Fields``)."""
PARCOURS_MAX = 1 << 16
"""Objets au plus parcourus depuis le catalogue d'une version pour savoir si un objet ajouté y
est désigné ; au-delà, l'objet est non lu."""

_CLES_DU_CATALOGUE = {
    "AcroForm": FORMULAIRE,
    "DSS": SIGNATURE,
    "Perms": SIGNATURE,
    "Metadata": METADONNEES,
    "Version": STRUCTURE,
    "Extensions": STRUCTURE,
}
"""Clés du catalogue dont le changement relève d'un ajout permis, ou de la structure pour la
version de la norme et ses extensions déclarées (§7.12) ; toute autre est non reconnue."""
_PROPRES_A_LA_STRUCTURE = frozenset({"XRef", "ObjStm"})
_SIGNATURES = frozenset({"Sig", "DocTimeStamp", "DSS"})
_CATALOGUE, _PAGE, _PAGES = "Catalog", "Page", "Pages"
_HEXADECIMAL = frozenset(b"0123456789abcdefABCDEF\x00\t\n\x0c\r ")
_LOCALISATION = Localisation(chemin="chaîne des références croisées")


@dataclass(slots=True)
class _Version:
    """Une version : ses sections dans la chaîne (la plus récente d'abord) et sa fin."""

    rangs: tuple[int, ...]
    fin: int
    marquee: bool
    nature: str = ORIGINALE
    ajoutes: int = 0
    remplaces: int = 0
    supprimes: int = 0
    date: str = ""
    signatures: int = 0
    natures: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class _Change:
    """Objet que change une version : son état (ajouté, remplacé, supprimé), sa référence et
    son entrée dans la version précédente."""

    etat: str
    ref: Ref
    ancienne: Entree | None


def analyser(contexte: Contexte) -> None:
    try:
        document = Document(contexte)
    except Illisible as illisible:
        _non_lue(contexte, illisible)
        return
    chiffre = "Encrypt" in document.trailer
    linearisation = document.premier_objet()
    linearise = isinstance(linearisation, dict) and "Linearized" in linearisation
    versions = _versions(document, linearise=linearise)
    try:
        origine = versions[0]
        origine.ajoutes = sum(1 for n, e in _entrees(document, origine) if n and e[0])
    except Illisible as illisible:
        _non_lue(contexte, illisible)
    for rang in range(1, len(versions)):
        _comparer(contexte, document, versions[rang - 1], versions[rang])
    _dater(document, versions, chiffre=chiffre)
    contexte.observer("revisionspdf.versions", len(versions), localisation=_LOCALISATION)
    contexte.observer("revisionspdf.sections", document.sections)
    contexte.observer("revisionspdf.chiffre", chiffre)
    contexte.observer("revisionspdf.linearise", linearise)
    if linearise and isinstance(linearisation, dict):
        longueur = entier(linearisation.get("L"))
        if longueur is not None:
            contexte.observer("revisionspdf.linearisation.longueur", longueur, unite="octets")
    # Une valeur par version, de la plus ancienne à la plus récente ; une liste trop longue est
    # coupée, et sa longueur entière observée à part (ADR-0207).
    valeurs.observer(contexte, "revisionspdf.fins", [v.fin for v in versions], unite="octets")
    valeurs.observer(contexte, "revisionspdf.natures", [v.nature for v in versions])
    valeurs.observer(contexte, "revisionspdf.ajoutes", [v.ajoutes for v in versions])
    valeurs.observer(contexte, "revisionspdf.remplaces", [v.remplaces for v in versions])
    valeurs.observer(contexte, "revisionspdf.supprimes", [v.supprimes for v in versions])
    sans_marque = sum(1 for v in versions if not v.marquee)
    if sans_marque:
        contexte.observer("revisionspdf.sans_marque_de_fin", sans_marque)
    apres = contexte.taille - versions[-1].fin
    contexte.observer("revisionspdf.octets_apres_fin", max(apres, 0), unite="octets")
    non_reconnues = sum(1 for v in versions[1:] if NON_RECONNUE in v.natures)
    contexte.observer("revisionspdf.versions_non_reconnues", non_reconnues)
    _signatures(contexte, document, versions, chiffre=chiffre)
    if len(versions) >= 2:
        lignes = [
            (v.fin, v.nature, v.ajoutes, v.remplaces, v.supprimes, v.date, v.signatures)
            for v in versions[:LIGNES_MAX]
        ]
        contexte.visualiser_tableau(
            NatureVisualisation.CHRONOLOGIE_REVISIONS,
            [(rang, *ligne) for rang, ligne in enumerate(lignes, start=1)],
            localisation=Localisation(
                chemin="versions du document", octets=Plage(0, max(versions[-1].fin, 1))
            ),
        )


# Versions


def _versions(document: Document, *, linearise: bool) -> list[_Version]:
    """Versions, de la plus ancienne à la plus récente ; les sections d'une linéarisation ne
    font qu'une version, la première (annexe F.3)."""
    chaine = document.chaine
    rangs = list(range(len(chaine) - 1, -1, -1))
    groupes: list[tuple[int, ...]] = []
    if linearise and len(chaine) >= 2:
        premiere, principale = chaine[-2], chaine[-1]
        precedente = entier(premiere.trailer.get("Prev"))
        if premiere.position < principale.position and precedente == principale.position:
            groupes.append((len(chaine) - 2, len(chaine) - 1))
            rangs = rangs[2:]
    groupes.extend((rang,) for rang in rangs)
    versions = []
    for groupe in groupes:
        sections = [chaine[rang] for rang in groupe]
        versions.append(
            _Version(
                rangs=groupe,
                fin=max(s.fin for s in sections),
                marquee=all(s.marquee for s in sections),
            )
        )
    return versions


def _entrees(document: Document, version: _Version) -> list[tuple[int, Entree]]:
    """Entrées que déclarent les sections de la version, la plus récente l'emportant."""
    vues: dict[int, Entree] = {}
    for rang in version.rangs:
        for numero, entree in document.entrees(rang).items():
            vues.setdefault(numero, entree)
    return sorted(vues.items())


def _non_lue(contexte: Contexte, illisible: Illisible) -> None:
    contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))


def _ref(numero: int, entree: Entree) -> Ref:
    """Référence de l'objet d'une entrée en usage : génération 0 dans un flux d'objets."""
    return Ref(numero, entree[2] if entree[0] == 1 else 0)


def _changes(document: Document, ancienne: Document, version: _Version) -> list[_Change]:
    changes = []
    for numero, entree in _entrees(document, version):
        if numero == 0:
            continue
        avant = ancienne.entree(numero)
        en_usage_avant = avant is not None and avant[0] != 0
        if entree[0] != 0:
            if not en_usage_avant:
                changes.append(_Change("ajoute", _ref(numero, entree), None))
            elif avant != entree:
                changes.append(_Change("remplace", _ref(numero, entree), avant))
        elif en_usage_avant and avant is not None:
            changes.append(_Change("supprime", _ref(numero, avant), avant))
    return changes


# Nature d'une version (ADR-0208)


def _dico(valeur: Objet) -> dict[str, Objet] | None:
    if isinstance(valeur, Flux):
        return valeur.dico
    return valeur if isinstance(valeur, dict) else None


def _nom(objet: Objet) -> str | None:
    """Un nom PDF en texte ; ``None`` pour tout autre objet."""
    return str(objet) if isinstance(objet, Nom) else None


def _propre(valeur: Objet, info: bool) -> str | None:
    """Ce qu'est l'objet d'après lui seul : nature permise, structure, catalogue, page, arbre des
    pages ; ``None`` s'il ne le dit pas."""
    if valeur is None:
        return STRUCTURE
    dico = _dico(valeur)
    if dico is None:
        return None
    if info:
        return METADONNEES
    genre = _nom(dico.get("Type"))
    if genre in _PROPRES_A_LA_STRUCTURE:
        return STRUCTURE
    if genre in _SIGNATURES:
        return SIGNATURE
    if genre == "Metadata":
        return METADONNEES
    if genre in (_CATALOGUE, _PAGE, _PAGES):
        return genre
    sous_type = _nom(dico.get("Subtype"))
    if genre == "Annot" or (sous_type is not None and "Rect" in dico):
        if sous_type != "Widget":
            return ANNOTATION
        return SIGNATURE if _nom(dico.get("FT")) == "Sig" else FORMULAIRE
    if "FT" in dico:
        return SIGNATURE if _nom(dico.get("FT")) == "Sig" else FORMULAIRE
    if "T" in dico and ("Kids" in dico or "Parent" in dico):
        return FORMULAIRE
    return None


def _differences(avant: Objet, apres: Objet) -> set[str] | None:
    """Clés dont la valeur diffère entre deux dictionnaires ; ``None`` si l'un n'en est pas un."""
    ancien, nouveau = _dico(avant), _dico(apres)
    if ancien is None or nouveau is None:
        return None
    absente = object()
    return {
        cle
        for cle in ancien.keys() | nouveau.keys()
        if ancien.get(cle, absente) != nouveau.get(cle, absente)
    }


def _references(valeur: Objet) -> Iterator[Ref]:
    """Références que contient un objet, à toute profondeur de ses objets directs."""
    pile = [valeur]
    while pile:
        objet = pile.pop()
        if isinstance(objet, Ref):
            yield objet
        elif isinstance(objet, list):
            pile.extend(objet)
        elif (dico := _dico(objet)) is not None:
            pile.extend(dico.values())


class _Classement:
    """Range les objets que change une version, puis en tire sa nature."""

    def __init__(
        self, contexte: Contexte, nouvelle: Document, ancienne: Document, changes: list[_Change]
    ) -> None:
        self._contexte = contexte
        self._nouvelle = nouvelle
        self._ancienne = ancienne
        self._changes = {c.ref.numero: c for c in changes}
        self._valeurs: dict[int, Objet] = {}
        self.categories: dict[int, str | None] = {}
        self._catalogue_change: set[str] = set()
        """Natures des clés changées du catalogue."""
        self.illisible: Illisible | None = None

    def _lire(self, document: Document, objet: Objet) -> Objet:
        try:
            return document.resoudre(objet)
        except Illisible as illisible:
            self.illisible = self.illisible or illisible
            raise

    def ranger(self) -> set[str]:
        info = {
            ref.numero
            for ref in (self._nouvelle.trailer.get("Info"), self._ancienne.trailer.get("Info"))
            if isinstance(ref, Ref)
        }
        for numero, change in self._changes.items():
            document = self._ancienne if change.etat == "supprime" else self._nouvelle
            try:
                valeur = self._lire(document, change.ref)
            except Illisible:
                self.categories[numero] = NON_LUE
                continue
            self._valeurs[numero] = valeur
            self.categories[numero] = _propre(valeur, numero in info)
        self._catalogue()
        for numero in list(self.categories):
            if self.categories[numero] in (_PAGE, _PAGES):
                self.categories[numero] = self._page(numero)
            elif self.categories[numero] == _CATALOGUE:
                self.categories[numero] = STRUCTURE
        self._tableaux()
        self._propager()
        self._orphelins()
        natures = {NON_RECONNUE if c is None else c for c in self.categories.values()}
        return (natures | self._catalogue_change) - {STRUCTURE}

    def _catalogue(self) -> None:
        """Clés du catalogue changées, et ce qu'elles désignent parmi les objets changés."""
        try:
            nouveau = self._lire(self._nouvelle, self._nouvelle.trailer.get("Root"))
            ancien = self._lire(self._ancienne, self._ancienne.trailer.get("Root"))
        except Illisible:
            self._catalogue_change.add(NON_LUE)
            return
        differences = _differences(ancien, nouveau)
        if differences is None:
            self._catalogue_change.add(NON_RECONNUE)
            return
        self._catalogue_change.update(_CLES_DU_CATALOGUE.get(c, NON_RECONNUE) for c in differences)
        dico = _dico(nouveau) or {}
        for cle, nature in _CLES_DU_CATALOGUE.items():
            designe = dico.get(cle)
            if isinstance(designe, Ref) and self.categories.get(designe.numero, "") is None:
                self.categories[designe.numero] = nature

    def _page(self, numero: int) -> str:
        """Une page ou un nœud de l'arbre des pages : ajouté, supprimé ou changé ailleurs que
        dans ses annotations, il change le contenu ; sinon, la nature des annotations."""
        change = self._changes[numero]
        if change.etat != "remplace" or change.ancienne is None:
            return NON_RECONNUE
        nouvelle = self._valeurs[numero]
        try:
            ancienne = self._lire(self._ancienne, _ref(numero, change.ancienne))
        except Illisible:
            return NON_LUE
        differences = _differences(ancienne, nouvelle)
        if differences is None or differences - {"Annots"}:
            return NON_RECONNUE
        if not differences:
            return STRUCTURE
        if _nom((_dico(nouvelle) or {}).get("Type")) == _PAGES:
            return NON_RECONNUE
        try:
            avant = self._lire(self._ancienne, (_dico(ancienne) or {}).get("Annots"))
            apres = self._lire(self._nouvelle, (_dico(nouvelle) or {}).get("Annots"))
        except Illisible:
            return NON_LUE
        anciennes = avant if isinstance(avant, list) else []
        ajoutees = [e for e in apres if e not in anciennes] if isinstance(apres, list) else []
        natures = {self._annotation(r) for r in ajoutees}
        if natures and natures <= {FORMULAIRE, SIGNATURE}:
            return SIGNATURE if SIGNATURE in natures else FORMULAIRE
        return ANNOTATION

    def _annotation(self, ref: Objet) -> str | None:
        if isinstance(ref, Ref) and ref.numero in self._changes:
            return self.categories.get(ref.numero)
        try:
            return _propre(self._lire(self._nouvelle, ref), info=False)
        except Illisible:
            return NON_LUE

    def _tableaux(self) -> None:
        """Un tableau indirect dont chaque élément est une annotation ou un champ (``/Annots``,
        ``/Fields``) prend leur nature."""
        for numero, categorie in self.categories.items():
            valeur = self._valeurs.get(numero)
            if categorie is not None or not isinstance(valeur, list):
                continue
            if not valeur:
                self.categories[numero] = STRUCTURE
                continue
            if len(valeur) > _ELEMENTS_MAX:
                continue
            self._contexte.compter_objets(len(valeur))
            natures = {self._annotation(element) for element in valeur}
            if natures <= PERMISES:  # non vide : le tableau a au moins un élément
                self.categories[numero] = next(n for n in NATURES if n in natures)

    def _propager(self) -> None:
        """Les objets changés que désigne un objet d'une nature permise en prennent la nature :
        apparences, polices et images d'une annotation, certificats d'un DSS…"""
        pile = [
            (numero, categorie)
            for numero, categorie in self.categories.items()
            if categorie in PERMISES and numero in self._valeurs
        ]
        while pile:
            numero, categorie = pile.pop()
            self._contexte.compter_objets()
            for ref in _references(self._valeurs[numero]):
                if ref.numero in self._valeurs and self.categories.get(ref.numero) is None:
                    self.categories[ref.numero] = categorie
                    pile.append((ref.numero, categorie))

    def _orphelins(self) -> None:
        """Objets ajoutés qu'aucun objet changé ne désigne : s'ils ne sont désignés nulle part
        depuis le catalogue et le dictionnaire Info de la version, ils ne changent rien de ce
        qu'elle affiche, et comptent comme structure (ADR-0208)."""
        designes = {ref.numero for valeur in self._valeurs.values() for ref in _references(valeur)}
        candidats = {
            numero
            for numero, categorie in self.categories.items()
            if categorie is None
            and self._changes[numero].etat == "ajoute"
            and numero not in designes
        }
        if not candidats:
            return
        trailer = self._nouvelle.trailer
        pile = [r for r in (trailer.get("Root"), trailer.get("Info")) if isinstance(r, Ref)]
        vus: set[int] = set()
        complet = True
        while pile and candidats - vus:
            ref = pile.pop()
            if ref.numero in vus:
                continue
            if len(vus) >= PARCOURS_MAX:
                complet = False
                break
            vus.add(ref.numero)
            self._contexte.compter_objets()
            try:
                valeur = self._nouvelle.objet(ref)
            except Illisible:
                complet = False
                continue
            pile.extend(_references(valeur))
        for numero in candidats - vus:
            self.categories[numero] = STRUCTURE if complet else NON_LUE


def _comparer(
    contexte: Contexte,
    document: Document,
    precedente: _Version,
    version: _Version,
) -> None:
    """Objets que change la version, et sa nature. Dans un document chiffré, les noms et les
    nombres se lisent en clair ; les objets d'un flux d'objets ne se lisent pas (ADR-0210)."""
    nouvelle = document.vue(version.rangs[0])
    ancienne = document.vue(precedente.rangs[0])
    try:
        changes = _changes(document, ancienne, version)
    except Illisible as illisible:
        version.natures, version.nature = {NON_LUE}, NON_LUE
        _non_lue(contexte, illisible)
        return
    version.ajoutes = sum(1 for c in changes if c.etat == "ajoute")
    version.remplaces = sum(1 for c in changes if c.etat == "remplace")
    version.supprimes = sum(1 for c in changes if c.etat == "supprime")
    classement = _Classement(contexte, nouvelle, ancienne, changes)
    version.natures = classement.ranger()
    version.nature = "+".join(n for n in NATURES if n in version.natures) or STRUCTURE
    if classement.illisible is not None:
        _non_lue(contexte, classement.illisible)


# Dates déclarées


def _date(document: Document, *, premiere: bool) -> str:
    """Date de modification du dictionnaire Info de la version (de création pour la première,
    à défaut) ; vide si elle manque, ne se lit pas ou dépasse :data:`_DATE_MAX` caractères."""
    try:
        info = _dico(document.resoudre(document.trailer.get("Info")))
        if info is None:
            return ""
        brute = document.resoudre(info.get("ModDate"))
        if not isinstance(brute, bytes) and premiere:
            brute = document.resoudre(info.get("CreationDate"))
    except Illisible:
        return ""
    if not isinstance(brute, bytes):
        return ""
    date = texte(brute)
    return date if len(date) <= _DATE_MAX else ""


def _dater(document: Document, versions: list[_Version], *, chiffre: bool) -> None:
    """Date déclarée de chaque version : celle de son dictionnaire Info quand elle diffère de
    la précédente (ADR-0212) ; rien pour un document chiffré, dont les chaînes le sont."""
    if chiffre:
        return
    precedente = ""
    for rang, version in enumerate(versions):
        date = _date(document.vue(version.rangs[0]), premiere=rang == 0)
        if date != precedente:
            version.date = date
        precedente = date


# Signatures (ADR-0209)


def _champs(contexte: Contexte, document: Document) -> Iterator[tuple[dict[str, Objet], Objet]]:
    """Champs de signature du formulaire de la dernière version, avec leur valeur ``/V``."""
    catalogue = _dico(document.resoudre(document.trailer.get("Root"))) or {}
    formulaire = _dico(document.resoudre(catalogue.get("AcroForm"))) or {}
    racines = document.resoudre(formulaire.get("Fields"))
    pile: list[tuple[Objet, Objet]] = (
        [(r, None) for r in racines] if isinstance(racines, list) else []
    )
    vus: set[int] = set()
    while pile:
        designe, herite = pile.pop()
        if isinstance(designe, Ref):
            if designe.numero in vus:
                continue
            vus.add(designe.numero)
        contexte.compter_objets()
        champ = _dico(document.resoudre(designe))
        if champ is None:
            continue
        genre = champ.get("FT", herite)
        enfants = document.resoudre(champ.get("Kids"))
        if isinstance(enfants, list):
            pile.extend((enfant, genre) for enfant in enfants)
        if genre == "Sig" and "V" in champ:
            yield champ, champ["V"]


def _plage(contexte: Contexte, plage: Objet, fins: dict[int, int]) -> tuple[int, bool]:
    """Version dont la fin est celle de la plage signée (0 si aucune), et si la plage ne laisse
    de côté qu'une chaîne hexadécimale, depuis le début du fichier."""
    nombres = [entier(n) for n in plage] if isinstance(plage, list) else []
    if len(nombres) != 4 or any(n is None or n < 0 for n in nombres):
        return 0, False
    debut, coupure, reprise, reste = (n or 0 for n in nombres)
    version = fins.get(reprise + reste, 0)
    if debut != 0 or not coupure < reprise or reprise - coupure > _CONTENU_MAX or not version:
        return version, False
    trou = contexte.lire(coupure, reprise - coupure)
    complete = (
        len(trou) >= 2
        and trou[:1] == b"<"
        and trou[-1:] == b">"
        and set(trou[1:-1]) <= _HEXADECIMAL
    )
    return version, complete


def _signatures(
    contexte: Contexte, document: Document, versions: list[_Version], *, chiffre: bool
) -> None:
    fins = {version.fin: rang for rang, version in enumerate(versions, start=1)}
    vues: set[int | Ref] = set()
    signees: list[int] = []
    rang = 0
    try:
        for _, designee in _champs(contexte, document):
            cle = designee if isinstance(designee, Ref) else id(designee)
            if cle in vues:
                continue
            vues.add(cle)
            signature = _dico(document.resoudre(designee))
            if signature is None:
                continue
            rang += 1
            version, complete = _plage(
                contexte, document.resoudre(signature.get("ByteRange")), fins
            )
            if complete:
                signees.append(version)
                versions[version - 1].signatures += 1
            if rang > SIGNATURES_MAX:
                continue
            prefixe = f"revisionspdf.signature.{rang}"
            contexte.observer(f"{prefixe}.version", version)
            contexte.observer(f"{prefixe}.plage_complete", complete)
            sous_filtre = document.resoudre(signature.get("SubFilter"))
            if isinstance(sous_filtre, Nom):
                contexte.observer(f"{prefixe}.sous_filtre", str(sous_filtre))
            date = document.resoudre(signature.get("M"))
            if isinstance(date, bytes) and not chiffre and len(texte(date)) <= _DATE_MAX:
                contexte.observer(f"{prefixe}.date", texte(date))
        mdp = _docmdp(document)
    except Illisible as illisible:
        _non_lue(contexte, illisible)
        mdp = None
    contexte.observer("revisionspdf.signatures", rang)
    if mdp is not None:
        contexte.observer("revisionspdf.docmdp", mdp)
    if signees:
        derniere = max(signees)
        contexte.observer("revisionspdf.derniere_version_signee", derniere)
        apres = sum(1 for v in versions[derniere:] if NON_RECONNUE in v.natures)
        contexte.observer("revisionspdf.non_reconnues_apres_signature", apres)


def _docmdp(document: Document) -> int | None:
    """Droits de modification d'une signature de certification (``/P`` de DocMDP, §12.8.2.2) :
    1, 2 ou 3 ; 2 si la signature ne le dit pas ; ``None`` sans signature de certification."""
    catalogue = _dico(document.resoudre(document.trailer.get("Root"))) or {}
    droits = _dico(document.resoudre(catalogue.get("Perms"))) or {}
    signature = _dico(document.resoudre(droits.get("DocMDP")))
    if signature is None:
        return None
    references = document.resoudre(signature.get("Reference"))
    for reference in references if isinstance(references, list) else []:
        dico = _dico(document.resoudre(reference)) or {}
        if dico.get("TransformMethod") == "DocMDP":
            parametres = _dico(document.resoudre(dico.get("TransformParams"))) or {}
            niveau = entier(document.resoudre(parametres.get("P", 2)))
            return niveau if niveau in (1, 2, 3) else None
    return 2
