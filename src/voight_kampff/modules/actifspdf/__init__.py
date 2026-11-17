"""Module ``actifspdf`` : éléments actifs d'un PDF, signalés, jamais exécutés (F-62, NF-01,
ES-06 ; ADR-0219 à ADR-0222 ; fiche ``actifs-pdf``).

Le module cherche, depuis le catalogue de la dernière version, ce qu'un lecteur exécuterait ou
ouvrirait : les actions (ISO 32000-2, §12.6) et leurs chaînes (``/Next``), les scripts au niveau
du document (arbre de noms ``/JavaScript``), les formulaires XFA, les fichiers incorporés
(arbre ``/EmbeddedFiles``, annotations ``FileAttachment``, fichiers associés ``/AF``)
(ADR-0221). Il parcourt :

1. le catalogue : action d'ouverture (``/OpenAction``), actions du document (``/AA`` :
   fermeture, enregistrement, impression), arbres de noms, formulaire (``/AcroForm`` : ``/XFA``
   et l'arbre des champs, leurs actions ``/AA``), signets (``/Outlines``) ;
2. chaque page : ses actions (``/AA`` : ouverture, fermeture), ses annotations, leur action
   (``/A``) et leurs actions ``/AA``, ses fichiers associés.

Chaque action est décrite par sa **nature** (``/S`` : ``JavaScript``, ``Launch``, ``URI``…), par
ses **déclencheurs** (ouverture du document, événement du document, affichage d'une page,
calcul ou mise en forme d'un champ, geste de l'utilisateur) et par les pages où elle se trouve
(ADR-0220). Ni adresse, ni nom de fichier, ni code de script n'est lu : aucune chaîne du
document ne l'est. Rien n'est exécuté, rien n'est ouvert, aucune adresse n'est résolue (ES-06,
ADR-0033). Un document chiffré se parcourt par sa structure, qui ne l'est pas ; rien n'est
déchiffré (ADR-0126, ADR-0210). Le module n'émet aucun constat : les règles du catalogue lisent
ses observations (ADR-0222).
"""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.pdf import Document, Flux, Illisible, Nom, Objet, Ref, pages
from voight_kampff.rapport.modele import Localisation

__all__ = [
    "ACTIONS_MAX",
    "AUTRE",
    "DECLENCHEURS",
    "NATURES",
    "NOEUDS_MAX",
    "OBJETS_RESERVES",
    "PAGES_MAX",
    "analyser",
]

PAGES_MAX = 4096
"""Pages au plus parcourues ; ``actifspdf.pages`` les compte toutes."""
ACTIONS_MAX = 1 << 16
"""Actions au plus retenues ; au-delà, ``actifspdf.actions_coupees`` le dit."""
NOEUDS_MAX = 1 << 16
"""Nœuds et entrées au plus lus d'un arbre (noms, champs, signets) ; au-delà, l'arbre n'est lu
qu'en partie."""
OBJETS_RESERVES = 1 << 18
"""Objets du budget (ES-03) gardés pour finir : la recherche s'arrête quand il n'en reste pas
plus, pour que les observations déjà faites soient envoyées (comme ``pagespdf``, ADR-0213)."""

OUVERTURE = "ouverture"
"""Ouverture du document : ``/OpenAction``, scripts de l'arbre de noms ``/JavaScript``."""
DOCUMENT = "document"
"""Événement du document : fermeture, enregistrement, impression (``/AA`` du catalogue)."""
PAGE = "page"
"""Ouverture ou fermeture d'une page, annotation qui devient visible ou invisible."""
CHAMP = "champ"
"""Calcul ou mise en forme d'un champ de formulaire (``/AA`` : ``C``, ``F``)."""
UTILISATEUR = "utilisateur"
"""Geste de l'utilisateur : clic, survol, saisie, signet choisi."""
DECLENCHEURS = (OUVERTURE, DOCUMENT, PAGE, CHAMP, UTILISATEUR)
"""Déclencheurs, dans l'ordre où ils s'écrivent ; les quatre premiers sont automatiques."""
_AUTOMATIQUES = frozenset({OUVERTURE, DOCUMENT, PAGE, CHAMP})

NATURES = frozenset(
    {
        "GoTo",
        "GoToR",
        "GoToE",
        "GoToDp",
        "Launch",
        "Thread",
        "URI",
        "Sound",
        "Movie",
        "Hide",
        "Named",
        "SubmitForm",
        "ResetForm",
        "ImportData",
        "SetOCGState",
        "Rendition",
        "Trans",
        "GoTo3DView",
        "JavaScript",
        "RichMediaExecute",
    }
)
"""Types d'actions de la norme (tableau 201) ; tout autre type est observé comme :data:`AUTRE`."""
AUTRE = "autre"
_AFFICHAGE = frozenset(
    {"GoTo", "GoToDp", "Thread", "Trans", "GoTo3DView", "SetOCGState", "Hide", "ResetForm"}
)
"""Actions qui ne changent que l'affichage du document : jamais comptées automatiques."""
_OUVERTURES = frozenset({"Launch", "GoToR", "GoToE", "ImportData"})
"""Actions qui ouvrent un programme ou un autre fichier."""
_ENVOIS = frozenset({"SubmitForm", "URI"})
"""Actions qui envoient le formulaire ou ouvrent une adresse."""
XFA = "XFA"
"""Nature d'un formulaire XFA, compté parmi les scripts (ses scripts ne sont pas lus)."""

_AA_DOCUMENT = dict.fromkeys(("WC", "WS", "DS", "WP", "DP"), DOCUMENT)
"""Actions du catalogue (§12.6.3, tableau 199)."""
_AA_PAGE = dict.fromkeys(("O", "C"), PAGE)
"""Actions d'une page (tableau 198)."""
_AA_ANNOTATION = (
    dict.fromkeys(("PO", "PC", "PV", "PI"), PAGE)
    | dict.fromkeys(("C", "F"), CHAMP)
    | dict.fromkeys(("E", "X", "D", "U", "Fo", "Bl", "K", "V"), UTILISATEUR)
)
"""Actions d'une annotation (tableau 197) et d'un champ (tableau 200) ; une clé inconnue n'est
exécutée par aucun lecteur conforme et n'est pas lue."""
_LOCALISATION = Localisation(chemin="actions et fichiers incorporés")


def _nom(objet: Objet) -> str | None:
    return str(objet) if isinstance(objet, Nom) else None


def _dico(valeur: Objet) -> dict[str, Objet] | None:
    if isinstance(valeur, Flux):
        return valeur.dico
    return valeur if isinstance(valeur, dict) else None


@dataclass(slots=True)
class _Action:
    """Une action, lue une fois, et tout ce qui la déclenche."""

    nature: str
    script: bool
    """Vrai pour une action ``JavaScript``, ou ``Rendition`` qui porte un script (``/JS``)."""
    declencheurs: set[str] = field(default_factory=set)
    pages: set[int] = field(default_factory=set)


class _Recherche:
    """Parcourt le document et range ses actions et ses fichiers incorporés."""

    def __init__(self, contexte: Contexte, document: Document) -> None:
        self._contexte = contexte
        self._document = document
        self.actions: dict[object, _Action] = {}
        self.fichiers: dict[object, set[int]] = {}
        """Spécifications de fichiers incorporés (``/EF``), et les pages où elles se trouvent."""
        self.xfa = False
        self.illisible: Illisible | None = None
        self.arrete = False
        """Vrai si la recherche s'est arrêtée avant le budget (:data:`OBJETS_RESERVES`)."""
        self.coupee = False
        """Vrai si une limite (:data:`ACTIONS_MAX`, :data:`NOEUDS_MAX`) a été atteinte."""

    def _resoudre(self, objet: Objet) -> Objet:
        return self._document.resoudre(objet)

    def continuer(self) -> bool:
        """Faux dès qu'il ne reste plus que :data:`OBJETS_RESERVES` objets du budget."""
        if self._contexte.objets > OBJETS_MAX - OBJETS_RESERVES:
            self.arrete = True
        return not self.arrete

    def partie(self, lire: Callable[[], None]) -> bool:
        """Lit une partie du document ; une partie illisible n'arrête pas les autres. Vrai si
        elle a été lue en entier."""
        if not self.continuer():
            return False
        try:
            lire()
        except Illisible as illisible:
            self.illisible = self.illisible or illisible
            return False
        return not self.arrete

    @staticmethod
    def _cle(designe: Objet, valeur: object) -> object:
        """Clé d'un objet lu : sa référence, ou l'objet direct lui-même, que le lecteur garde."""
        return designe if isinstance(designe, Ref) else id(valeur)

    # Actions (§12.6)

    def action(self, designee: Objet, declencheur: str, page: int | None) -> None:
        """Une action et les actions de sa chaîne (``/Next``, §12.6.2)."""
        pile = [designee]
        vues: set[object] = set()
        while pile:
            designe = pile.pop()
            valeur = _dico(self._resoudre(designe))
            if valeur is None:
                continue
            cle = self._cle(designe, valeur)
            if cle in vues:
                continue
            vues.add(cle)
            self._contexte.compter_objets()
            nature = _nom(self._resoudre(valeur.get("S")))
            if nature is None:
                continue  # sans type, ce n'est pas une action (§12.6.2)
            trouvee = self.actions.get(cle)
            if trouvee is None:
                if len(self.actions) >= ACTIONS_MAX:
                    self.coupee = True
                    return
                script = nature == "JavaScript" or (nature == "Rendition" and "JS" in valeur)
                trouvee = _Action(nature if nature in NATURES else AUTRE, script)
                self.actions[cle] = trouvee
            trouvee.declencheurs.add(declencheur)
            if page is not None:
                trouvee.pages.add(page)
            suivante = valeur.get("Next")
            resolue = self._resoudre(suivante)
            if isinstance(resolue, list):
                pile.extend(reversed(resolue))
            elif resolue is not None:
                pile.append(suivante)

    def actions_supplementaires(
        self, designees: Objet, declencheurs: dict[str, str], page: int | None
    ) -> None:
        """Actions d'un dictionnaire ``/AA``, par la clé de leur événement."""
        dico = _dico(self._resoudre(designees))
        for cle, designee in (dico or {}).items():
            if cle in declencheurs:
                self.action(designee, declencheurs[cle], page)

    # Fichiers incorporés (§7.11)

    def fichier(self, designe: Objet, page: int | None) -> None:
        """Spécification de fichier ; comptée si elle incorpore le fichier (``/EF``)."""
        valeur = _dico(self._resoudre(designe))
        if valeur is None or _dico(self._resoudre(valeur.get("EF"))) is None:
            return
        self._contexte.compter_objets()
        pages_ = self.fichiers.setdefault(self._cle(designe, valeur), set())
        if page is not None:
            pages_.add(page)

    def fichiers_associes(self, designes: Objet, page: int | None) -> None:
        """Fichiers associés (``/AF``, §14.13)."""
        liste = self._resoudre(designes)
        for designe in liste if isinstance(liste, list) else []:
            self.fichier(designe, page)

    # Arbres

    def arbre_de_noms(self, racine: Objet) -> Iterator[Objet]:
        """Valeurs d'un arbre de noms (§7.9.6), dans l'ordre ; ses clés ne sont pas lues."""
        pile = [racine]
        vues: set[Ref] = set()
        lus = 0
        while pile:
            designe = pile.pop()
            if isinstance(designe, Ref):
                if designe in vues:
                    continue
                vues.add(designe)
            noeud = _dico(self._resoudre(designe))
            if noeud is None:
                continue
            noms = self._resoudre(noeud.get("Names"))
            enfants = self._resoudre(noeud.get("Kids"))
            lus += 1 + (len(noms) // 2 if isinstance(noms, list) else 0)
            if lus > NOEUDS_MAX or not self.continuer():
                self.coupee = self.coupee or lus > NOEUDS_MAX
                return
            self._contexte.compter_objets()
            if isinstance(noms, list):
                yield from noms[1::2]
            if isinstance(enfants, list):
                pile.extend(reversed(enfants))

    def champs(self, racines: Objet) -> None:
        """Arbre des champs du formulaire (§12.7.4) : actions ``/AA`` des champs, actions et
        actions ``/AA`` de leurs annotations."""
        liste = self._resoudre(racines)
        pile = list(reversed(liste)) if isinstance(liste, list) else []
        vues: set[Ref] = set()
        lus = 0
        while pile:
            designe = pile.pop()
            if isinstance(designe, Ref):
                if designe in vues:
                    continue
                vues.add(designe)
            noeud = _dico(self._resoudre(designe))
            if noeud is None:
                continue
            lus += 1
            if lus > NOEUDS_MAX or not self.continuer():
                self.coupee = self.coupee or lus > NOEUDS_MAX
                return
            self._contexte.compter_objets()
            if "A" in noeud:
                self.action(noeud["A"], UTILISATEUR, None)
            self.actions_supplementaires(noeud.get("AA"), _AA_ANNOTATION, None)
            enfants = self._resoudre(noeud.get("Kids"))
            if isinstance(enfants, list):
                pile.extend(reversed(enfants))

    def signets(self, racine: Objet) -> None:
        """Signets (§12.3.3) : l'action de chacun, choisie par l'utilisateur."""
        dico = _dico(self._resoudre(racine))
        pile = [dico.get("First")] if dico is not None else []
        vues: set[Ref] = set()
        lus = 0
        while pile:
            designe = pile.pop()
            if isinstance(designe, Ref):
                if designe in vues:
                    continue
                vues.add(designe)
            signet = _dico(self._resoudre(designe))
            if signet is None:
                continue
            lus += 1
            if lus > NOEUDS_MAX or not self.continuer():
                self.coupee = self.coupee or lus > NOEUDS_MAX
                return
            self._contexte.compter_objets()
            if "A" in signet:
                self.action(signet["A"], UTILISATEUR, None)
            pile.extend(e for e in (signet.get("Next"), signet.get("First")) if e is not None)

    # Catalogue et pages

    def catalogue(self, catalogue: dict[str, Objet]) -> None:
        self.partie(lambda: self._ouverture(catalogue.get("OpenAction")))
        self.partie(lambda: self.actions_supplementaires(catalogue.get("AA"), _AA_DOCUMENT, None))
        self.partie(lambda: self._noms(catalogue.get("Names")))
        self.partie(lambda: self.fichiers_associes(catalogue.get("AF"), None))
        self.partie(lambda: self._formulaire(catalogue.get("AcroForm")))
        self.partie(lambda: self.signets(catalogue.get("Outlines")))

    def _ouverture(self, designee: Objet) -> None:
        """Action d'ouverture ; une destination (tableau) n'est pas une action (§12.3.2)."""
        if isinstance(self._resoudre(designee), dict):
            self.action(designee, OUVERTURE, None)

    def _noms(self, designe: Objet) -> None:
        noms = _dico(self._resoudre(designe)) or {}
        self.partie(lambda: self._scripts_du_document(noms.get("JavaScript")))
        self.partie(lambda: self._fichiers_du_document(noms.get("EmbeddedFiles")))

    def _formulaire(self, designe: Objet) -> None:
        formulaire = _dico(self._resoudre(designe)) or {}
        self.xfa = self._resoudre(formulaire.get("XFA")) is not None
        self.champs(formulaire.get("Fields"))

    def _scripts_du_document(self, racine: Objet) -> None:
        for valeur in self.arbre_de_noms(racine):
            self.action(valeur, OUVERTURE, None)

    def _fichiers_du_document(self, racine: Objet) -> None:
        for valeur in self.arbre_de_noms(racine):
            self.fichier(valeur, None)

    def page(self, numero: int, page: dict[str, Objet]) -> bool:
        """Actions, annotations et fichiers associés d'une page ; faux si elle n'est pas lue en
        entier."""

        def lire() -> None:
            self.actions_supplementaires(page.get("AA"), _AA_PAGE, numero)
            self.fichiers_associes(page.get("AF"), numero)
            annotations = self._resoudre(page.get("Annots"))
            for designee in annotations if isinstance(annotations, list) else []:
                if not self.continuer():
                    return
                annotation = _dico(self._resoudre(designee))
                if annotation is None:
                    continue
                self._contexte.compter_objets()
                if "A" in annotation:
                    self.action(annotation["A"], UTILISATEUR, numero)
                self.actions_supplementaires(annotation.get("AA"), _AA_ANNOTATION, numero)
                if _nom(self._resoudre(annotation.get("Subtype"))) == "FileAttachment":
                    self.fichier(annotation.get("FS"), numero)
                self.fichiers_associes(annotation.get("AF"), numero)

        return self.partie(lire)


# Analyse


def analyser(contexte: Contexte) -> None:
    try:
        document = Document(contexte)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    if "Encrypt" in document.trailer:
        contexte.observer("actifspdf.chiffre", True)
    recherche = _Recherche(contexte, document)
    try:
        catalogue = _dico(document.resoudre(document.trailer.get("Root"))) or {}
        liste, trouvees = pages(contexte, document, PAGES_MAX)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    recherche.catalogue(catalogue)
    lues = 0
    for numero, (page, _) in enumerate(liste, start=1):
        if not recherche.continuer():
            break
        lues += recherche.page(numero, page)
    if (erreur := recherche.illisible) is not None:
        contexte.non_mener(erreur.raison, localisation=erreur.localisation(contexte.taille))
    _observer(contexte, recherche, trouvees, lues)


def _observer(contexte: Contexte, recherche: _Recherche, trouvees: int, lues: int) -> None:
    contexte.observer("actifspdf.pages", trouvees, localisation=_LOCALISATION)
    contexte.observer("actifspdf.pages_lues", lues)
    if recherche.arrete:
        contexte.observer("actifspdf.arret_avant_budget", True)
    if recherche.coupee:
        contexte.observer("actifspdf.recherche_coupee", True)
    actions = list(recherche.actions.values())
    _famille(contexte, "actions", actions)
    _famille(
        contexte,
        "scripts",
        [a for a in actions if a.script],
        [XFA] if recherche.xfa else [],
    )
    automatiques = [
        a for a in actions if a.nature not in _AFFICHAGE and a.declencheurs & _AUTOMATIQUES
    ]
    _famille(contexte, "automatiques", automatiques, automatiques=True)
    _famille(contexte, "ouvertures", [a for a in actions if a.nature in _OUVERTURES])
    _famille(contexte, "envois", [a for a in actions if a.nature in _ENVOIS])
    contexte.observer("actifspdf.fichiers", len(recherche.fichiers))
    _pages_concernees(
        contexte, "fichiers", [p for vues in recherche.fichiers.values() for p in vues]
    )


def _famille(
    contexte: Contexte,
    nom: str,
    actions: list[_Action],
    autres: list[str] | None = None,
    *,
    automatiques: bool = False,
) -> None:
    """Nombre d'éléments d'une famille ; s'il y en a, leurs natures, leurs déclencheurs et les
    pages où ils se trouvent."""
    autres = autres or []
    contexte.observer(f"actifspdf.{nom}", len(actions) + len(autres))
    if not actions and not autres:
        return
    natures = sorted({a.nature for a in actions}) + autres
    valeurs.observer(contexte, f"actifspdf.{nom}.natures", natures)
    vus = {d for a in actions for d in a.declencheurs}
    if automatiques:
        vus &= _AUTOMATIQUES
    if vus:
        declencheurs = [d for d in DECLENCHEURS if d in vus]
        valeurs.observer(contexte, f"actifspdf.{nom}.declencheurs", declencheurs)
    _pages_concernees(contexte, nom, [p for a in actions for p in a.pages])


def _pages_concernees(contexte: Contexte, nom: str, numeros: list[int]) -> None:
    if numeros:
        valeurs.observer(contexte, f"actifspdf.{nom}.pages", sorted(set(numeros)))
