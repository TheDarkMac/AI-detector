"""Couche texte native d'un PDF, ligne par ligne (complément de T53, ADR-0243 à ADR-0247).

Le texte est celui qu'un lecteur affiche sur les pages de la dernière version (ADR-0244) : le
contenu de chaque page, les formes qu'il appelle (``Do``, huit niveaux au plus) et l'apparence
normale de chaque annotation visible, hors champs de formulaire et fenêtres d'annotation, comme
les interprète ``pagespdf`` (ADR-0214) ; puis le texte de chaque annotation (``/Contents``), hors
fenêtres d'annotation, comme les commentaires d'un DOCX. Le texte invisible (modes de rendu 3
et 7) est lu et marqué (ADR-0245).

Chaque code est traduit par le lecteur des polices (``_lecture/polices.py``, ADR-0246) : CMap
``/ToUnicode``, sinon nom du glyphe et Adobe Glyph List ; un code sans texte n'est pas décodé, il
est compté et ne laisse rien dans le texte. Les textes sont mis bout à bout dans l'ordre du flux
de contenu, comme ``pdftotext -raw`` : une espace est ajoutée quand un glyphe commence à plus de
:data:`ESPACE` cadratin de la fin du précédent, sur sa ligne ; une ligne commence quand il s'en
écarte de plus de :data:`INTERLIGNE` cadratin perpendiculairement, recule de plus de
:data:`RECUL` cadratin, ou change de direction. L'avancée d'un glyphe est celle que déclare sa
police ; nulle si elle n'est pas connue.

Une page dont le contenu peint une image sans montrer aucun code est **sans couche texte
native** : elle n'est pas lue, la lecture des documents numérisés étant exclue (ADR-0017,
ADR-0247).
"""

import math
from dataclasses import dataclass, field

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture.pdf import (
    Document,
    Flux,
    Illisible,
    Objet,
    Ref,
    entier,
    operations,
    pages,
    texte,
)
from voight_kampff.modules._lecture.polices import (
    AUCUNE,
    IDENTITE,
    INCONNUE,
    Correspondance,
    Matrice,
    Police,
    Polices,
    dico,
    matrice,
    nom,
    produit,
    reel,
    reels,
)
from voight_kampff.rapport.modele import Plage

__all__ = [
    "ESPACE",
    "INTERLIGNE",
    "OBJETS_RESERVES",
    "PAGES_MAX",
    "PROFONDEUR_MAX",
    "RECUL",
    "Ligne",
    "Page",
    "Texte",
    "lire",
]

PAGES_MAX = 4096
"""Pages au plus lues ; ``caracteres.pages`` les compte toutes."""
PROFONDEUR_MAX = 8
"""Formes au plus imbriquées (``Do`` dans une forme) ; au-delà, la forme n'est pas lue."""
OBJETS_RESERVES = 1 << 18
"""Objets du budget (ES-03) gardés pour finir : la lecture s'arrête quand il n'en reste pas
plus, pour que l'analyse du texte déjà lu soit menée et envoyée (comme ``pagespdf``)."""
ESPACE = 0.1
"""Écart, en cadratins, au-delà duquel une espace sépare deux glyphes d'une ligne (Poppler,
``minWordBreakSpace``)."""
INTERLIGNE = 0.5
"""Écart perpendiculaire à la ligne, en cadratins, au-delà duquel une ligne commence."""
RECUL = 0.5
"""Recul sur la ligne, en cadratins, au-delà duquel une ligne commence."""
_DIRECTION = 1e-3
"""Écart au plus entre les directions de deux glyphes d'une même ligne (cosinus)."""
_INVISIBLES = frozenset({3, 7})
"""Modes de rendu du texte qui ne peignent rien (§9.3.6)."""
_CACHEES = 1 << 1 | 1 << 5 | 1 << 0
"""Indicateurs d'une annotation non affichée : invisible, cachée, non vue (§12.5.3)."""
_SANS_APPARENCE = frozenset({"Popup", "Widget"})
"""Annotations dont l'apparence n'est pas lue (ADR-0214)."""
_SAUTS = str.maketrans({"\r": "\n"})


@dataclass(slots=True)
class Ligne:
    """Texte d'une ligne, ses passages invisibles (indices dans le texte) et ce qu'elle désigne."""

    lieu: str
    """« page N », « page N, annotation K » (apparence) ou « page N, annotation K,
    commentaire » (``/Contents``)."""
    numero: int
    """Rang de la ligne dans son lieu, à partir de 1."""
    octets: Plage | None
    """Octets du flux d'où vient la ligne, ou de l'annotation ; le texte en est décodé."""
    morceaux: list[str] = field(default_factory=list)
    longueur: int = 0
    invisibles: list[tuple[int, int]] = field(default_factory=list)

    @property
    def texte(self) -> str:
        return "".join(self.morceaux)

    def ajouter(self, morceau: str, *, invisible: bool) -> None:
        debut, self.longueur = self.longueur, self.longueur + len(morceau)
        self.morceaux.append(morceau)
        if invisible:
            if self.invisibles and self.invisibles[-1][1] == debut:
                self.invisibles[-1] = (self.invisibles[-1][0], self.longueur)
            else:
                self.invisibles.append((debut, self.longueur))


@dataclass(slots=True)
class Page:
    """Ce qu'on a lu d'une page."""

    numero: int
    lignes: list[Ligne] = field(default_factory=list)
    codes: int = 0
    """Codes montrés par le contenu de la page et ses formes, décodés ou non."""
    images: int = 0
    """Images peintes par le contenu de la page et ses formes (``Do``, ``BI``)."""
    non_decodes: int = 0
    invisibles: int = 0
    """Caractères du texte invisible (modes de rendu 3 et 7)."""
    complete: bool = True

    @property
    def sans_texte(self) -> bool:
        """Page sans couche texte native : une image peinte, aucun code montré (ADR-0247)."""
        return self.images > 0 and self.codes == 0


@dataclass(slots=True)
class Texte:
    """Texte d'un document : pages lues, pages trouvées, arrêt avant le budget, et la première
    erreur de lecture (flux de contenu ou CMap illisible), que le module déclare."""

    pages: list[Page]
    trouvees: int
    arrete: bool
    illisible: Illisible | None


@dataclass(slots=True)
class _Etat:
    """État graphique (§8.4.1) : ce que ``q`` garde et ``Q`` rend."""

    ctm: Matrice = IDENTITE
    police: Police = INCONNUE
    correspondance: Correspondance = AUCUNE
    taille: float = 0.0
    espacement: float = 0.0
    mots: float = 0.0
    echelle: float = 1.0
    interligne: float = 0.0
    rendu: int = 0

    def copie(self) -> "_Etat":
        return _Etat(
            self.ctm,
            self.police,
            self.correspondance,
            self.taille,
            self.espacement,
            self.mots,
            self.echelle,
            self.interligne,
            self.rendu,
        )


@dataclass(slots=True)
class _Marque:
    """Contenu marqué qui porte un texte de remplacement (``/ActualText``, §14.9.4)."""

    texte: str
    ecrit: bool = False


@dataclass(slots=True)
class _Plume:
    """Où le texte en est : la ligne en cours, la fin du dernier glyphe, la séparation due."""

    page: Page
    lieu: str
    octets: Plage | None
    compte: int = 0
    ligne: Ligne | None = None
    fin: tuple[float, float] | None = None
    direction: tuple[float, float] = (1.0, 0.0)
    cadratin: float = 0.0
    attente: str = ""
    """Séparation à écrire avant le prochain texte : rien, une espace ou un saut de ligne."""
    marques: list[_Marque | None] = field(default_factory=list)
    """Contenus marqués ouverts (``BDC``, ``BMC``), du plus extérieur au plus intérieur."""

    @property
    def remplacement(self) -> _Marque | None:
        """Texte de remplacement en cours : celui du contenu marqué le plus extérieur."""
        return next((marque for marque in self.marques if marque is not None), None)

    def deplacer(
        self, debut: tuple[float, float], direction: tuple[float, float], cadratin: float
    ) -> None:
        """Le prochain glyphe commence en ``debut`` : séparation due depuis le précédent."""
        if self.fin is not None:
            ecart_x, ecart_y = debut[0] - self.fin[0], debut[1] - self.fin[1]
            ux, uy = direction
            le_long = ecart_x * ux + ecart_y * uy
            en_travers = ecart_y * ux - ecart_x * uy
            unite = max(cadratin, self.cadratin)
            meme = ux * self.direction[0] + uy * self.direction[1] >= 1 - _DIRECTION
            if not meme or abs(en_travers) > INTERLIGNE * unite or le_long < -RECUL * unite:
                self.attente = "\n"
            elif le_long > ESPACE * unite and not self.attente:
                self.attente = " "
        self.direction, self.cadratin = direction, cadratin

    def ecrire(self, morceau: str, fin: tuple[float, float], *, invisible: bool) -> None:
        if morceau:
            if self.ligne is None or self.attente == "\n":
                self.compte += 1
                self.ligne = Ligne(self.lieu, self.compte, self.octets)
                self.page.lignes.append(self.ligne)
            elif self.attente == " " and not (
                self.ligne.morceaux[-1][-1:].isspace() or morceau[:1].isspace()
            ):
                self.ligne.ajouter(" ", invisible=False)
            self.ligne.ajouter(morceau, invisible=invisible)
            self.attente = ""
        self.fin = fin

    def rompre(self) -> None:
        """Position perdue (coordonnées démesurées) : le prochain texte commence une ligne."""
        self.fin = None
        self.attente = "\n"


def _fini(*valeurs: float) -> bool:
    return all(math.isfinite(v) and abs(v) <= 1e12 for v in valeurs)


class _Lecteur:
    """Lit le texte des pages d'un document, l'une après l'autre."""

    def __init__(self, contexte: Contexte, document: Document) -> None:
        self._contexte = contexte
        self._document = document
        self.polices = Polices(contexte, document)
        self.illisible: Illisible | None = None
        self.arrete = False

    def _resoudre(self, objet: Objet) -> Objet:
        return self._document.resoudre(objet)

    def page(self, numero: int, page: dict[str, Objet], ressources: Objet) -> Page:
        lue = Page(numero)
        try:
            contenus = self._resoudre(page.get("Contents"))
            morceaux: list[bytes] = []
            debut = fin = 0
            for element in contenus if isinstance(contenus, list) else [contenus]:
                flux = self._resoudre(element)
                if isinstance(flux, Flux):
                    if not morceaux:
                        debut = flux.debut
                    fin = max(fin, flux.debut + flux.longueur)
                    morceaux.append(self._document.decoder(flux))
            octets = Plage(debut, max(fin - debut, 1)) if morceaux else None
            plume = _Plume(lue, f"page {numero}", octets)
            self._contenu(
                plume,
                b"\n".join(morceaux),
                debut,
                dico(self._resoudre(ressources)) or {},
                _Etat(),
                0,
                compter=True,
            )
            self._annotations(lue, page)
        except Illisible as illisible:
            self.illisible = self.illisible or illisible
            lue.complete = False
        return lue

    # Annotations (§12.5)

    def _annotations(self, lue: Page, page: dict[str, Objet]) -> None:
        annotations = self._resoudre(page.get("Annots"))
        for rang, designee in enumerate(annotations if isinstance(annotations, list) else [], 1):
            if self.arrete:
                return
            annotation = dico(self._resoudre(designee))
            if annotation is None:
                continue
            sous_type = nom(self._resoudre(annotation.get("Subtype")))
            lieu = f"page {lue.numero}, annotation {rang}"
            if sous_type not in _SANS_APPARENCE:
                self._apparence(lue, annotation, lieu)
            commentaire = self._resoudre(annotation.get("Contents"))
            if sous_type != "Popup" and isinstance(commentaire, bytes) and commentaire:
                octets = (
                    self._document.localisation(designee, lieu).octets
                    if isinstance(designee, Ref)
                    else None
                )
                plume = _Plume(lue, f"{lieu}, commentaire", octets)
                for ligne in texte(commentaire).translate(_SAUTS).split("\n"):
                    plume.attente = "\n"
                    plume.ecrire(ligne, (0.0, 0.0), invisible=False)

    def _apparence(self, lue: Page, annotation: dict[str, Objet], lieu: str) -> None:
        """Apparence normale d'une annotation visible (§12.5.5), comme ``pagespdf``."""
        indicateurs = entier(self._resoudre(annotation.get("F"))) or 0
        rect = self._resoudre(annotation.get("Rect"))
        apparences = dico(self._resoudre(annotation.get("AP"))) or {}
        normale = self._resoudre(apparences.get("N"))
        if isinstance(normale, dict):  # apparences par état : celle de /AS
            normale = self._resoudre(normale.get(nom(self._resoudre(annotation.get("AS"))) or ""))
        cotes = reels(rect, 4) if isinstance(rect, list) and len(rect) == 4 else None
        if indicateurs & _CACHEES or not isinstance(normale, Flux) or cotes is None:
            return
        m = matrice(self._resoudre(normale.dico.get("Matrix"))) or IDENTITE
        bbox = self._resoudre(normale.dico.get("BBox"))
        cadre = reels(bbox, 4) if isinstance(bbox, list) and len(bbox) == 4 else None
        if cadre is None:
            return
        xs = [
            x * m[0] + y * m[2] + m[4] for x in (cadre[0], cadre[2]) for y in (cadre[1], cadre[3])
        ]
        ys = [
            x * m[1] + y * m[3] + m[5] for x in (cadre[0], cadre[2]) for y in (cadre[1], cadre[3])
        ]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            return
        r0, r1 = min(cotes[0], cotes[2]), max(cotes[0], cotes[2])
        s0, s1 = min(cotes[1], cotes[3]), max(cotes[1], cotes[3])
        sx, sy = (r1 - r0) / (x1 - x0), (s1 - s0) / (y1 - y0)
        ajustement: Matrice = (sx, 0.0, 0.0, sy, r0 - x0 * sx, s0 - y0 * sy)
        ressources = dico(self._resoudre(normale.dico.get("Resources"))) or {}
        plume = _Plume(lue, lieu, Plage(normale.debut, max(normale.longueur, 1)))
        self._contenu(
            plume,
            self._document.decoder(normale),
            normale.debut,
            ressources,
            _Etat(ctm=produit(m, ajustement)),
            1,
            compter=False,
        )

    # Contenu (§8.4, §9.3, §9.4)

    def _contenu(
        self,
        plume: _Plume,
        donnees: bytes,
        debut: int,
        ressources: dict[str, Objet],
        etat: _Etat,
        profondeur: int,
        *,
        compter: bool,
    ) -> None:
        """Lit un flux de contenu depuis l'état ``etat`` ; ``compter`` : ses codes et ses
        images sont ceux de la page (pas d'une apparence d'annotation). Les contenus marqués
        qu'il laisse ouverts sont fermés à sa fin."""
        ouvertes = len(plume.marques)
        self._operations(plume, donnees, debut, ressources, etat, profondeur, compter=compter)
        while len(plume.marques) > ouvertes:
            self._fermer(plume)

    def _operations(
        self,
        plume: _Plume,
        donnees: bytes,
        debut: int,
        ressources: dict[str, Objet],
        etat: _Etat,
        profondeur: int,
        *,
        compter: bool,
    ) -> None:
        pile: list[_Etat] = []
        tm = tlm = IDENTITE
        ouvertes = len(plume.marques)
        for rang, (operateur, operandes) in enumerate(operations(self._contexte, donnees, debut)):
            if rang % 1024 == 0 and self._contexte.objets > OBJETS_MAX - OBJETS_RESERVES:
                self.arrete = True
                plume.page.complete = False
                return
            if operateur == "q":
                pile.append(etat.copie())
            elif operateur == "Q":
                if pile:
                    etat = pile.pop()
            elif operateur == "cm":
                if (v := reels(operandes, 6)) is not None:
                    etat.ctm = produit((v[0], v[1], v[2], v[3], v[4], v[5]), etat.ctm)
            elif operateur == "gs":
                self._etat_graphique(etat, ressources, operandes)
            elif operateur == "BT":
                tm = tlm = IDENTITE
            elif operateur == "Tf":
                self._police(etat, ressources, operandes)
            elif operateur in ("Tc", "Tw", "Tz", "TL", "Tr"):
                self._etat_du_texte(etat, operateur, operandes)
            elif operateur in ("Td", "TD"):
                if (d := reels(operandes, 2)) is not None:
                    if operateur == "TD":
                        etat.interligne = -d[1]
                    tm = tlm = produit((1.0, 0.0, 0.0, 1.0, d[0], d[1]), tlm)
            elif operateur == "Tm":
                if (v := reels(operandes, 6)) is not None:
                    tm = tlm = (v[0], v[1], v[2], v[3], v[4], v[5])
            elif operateur == "T*":
                tm = tlm = produit((1.0, 0.0, 0.0, 1.0, 0.0, -etat.interligne), tlm)
            elif operateur in ("Tj", "'", '"', "TJ"):
                if operateur in ("'", '"'):
                    if operateur == '"' and (d := reels(operandes[:-1], 2)) is not None:
                        etat.mots, etat.espacement = d
                    tm = tlm = produit((1.0, 0.0, 0.0, 1.0, 0.0, -etat.interligne), tlm)
                elements = operandes[-1] if operandes else None
                if operateur != "TJ":
                    elements = [elements]
                if isinstance(elements, list):
                    tm = self._montrer(plume, etat, tm, elements, compter=compter)
            elif operateur == "BI":
                plume.page.images += compter
            elif operateur in ("BDC", "BMC"):
                plume.marques.append(self._marque(ressources, operandes, operateur))
            elif operateur == "EMC":
                if len(plume.marques) > ouvertes:
                    self._fermer(plume)
            elif operateur == "Do":
                self._objet(plume, etat, ressources, operandes, profondeur, compter=compter)
            if self.arrete:
                return

    def _marque(
        self, ressources: dict[str, Objet], operandes: list[Objet], operateur: str
    ) -> _Marque | None:
        """Contenu marqué ouvert ; son texte de remplacement, s'il en a un (§14.6, §14.9.4)."""
        if operateur == "BMC" or len(operandes) < 2:
            return None
        proprietes = self._resoudre(operandes[-1])
        if (nommees := nom(proprietes)) is not None:
            liste = dico(self._resoudre(ressources.get("Properties"))) or {}
            proprietes = self._resoudre(liste.get(nommees))
        lues = dico(proprietes)
        remplacement = self._resoudre(lues.get("ActualText")) if lues is not None else None
        return _Marque(texte(remplacement)) if isinstance(remplacement, bytes) else None

    @staticmethod
    def _fermer(plume: _Plume) -> None:
        """Ferme le contenu marqué le plus intérieur ; un texte de remplacement que nul glyphe
        n'a placé est écrit à la suite."""
        marque = plume.marques.pop()
        if marque is not None and not marque.ecrit and plume.remplacement is None:
            if plume.fin is None:  # aucune position : le texte suivant commence une ligne
                plume.ecrire(marque.texte, (0.0, 0.0), invisible=False)
                plume.rompre()
            else:
                plume.ecrire(marque.texte, plume.fin, invisible=False)

    def _police(self, etat: _Etat, ressources: dict[str, Objet], operandes: list[Objet]) -> None:
        if len(operandes) < 2 or (taille := reel(operandes[-1])) is None:
            return
        nommee = nom(operandes[-2])
        polices = dico(self._resoudre(ressources.get("Font"))) or {}
        designee = polices.get(nommee) if nommee is not None else None
        etat.taille = taille
        etat.police = INCONNUE if designee is None else self.polices.police(designee)
        etat.correspondance = AUCUNE if designee is None else self.polices.correspondance(designee)

    def _etat_du_texte(self, etat: _Etat, operateur: str, operandes: list[Objet]) -> None:
        valeur = reel(operandes[-1]) if operandes else None
        if valeur is None:
            return
        if operateur == "Tc":
            etat.espacement = valeur
        elif operateur == "Tw":
            etat.mots = valeur
        elif operateur == "Tz":
            etat.echelle = valeur / 100
        elif operateur == "TL":
            etat.interligne = valeur
        elif valeur == int(valeur):
            etat.rendu = int(valeur)

    def _etat_graphique(
        self, etat: _Etat, ressources: dict[str, Objet], operandes: list[Objet]
    ) -> None:
        """Police d'un dictionnaire d'état graphique (§8.4.5)."""
        nomme = nom(operandes[-1]) if operandes else None
        etats = dico(self._resoudre(ressources.get("ExtGState"))) or {}
        lu = dico(self._resoudre(etats.get(nomme))) if nomme is not None else None
        police = self._resoudre(lu.get("Font")) if lu is not None else None
        if isinstance(police, list) and len(police) == 2 and (taille := reel(police[1])):
            etat.police, etat.taille = self.polices.police(police[0]), taille
            etat.correspondance = self.polices.correspondance(police[0])

    def _montrer(
        self,
        plume: _Plume,
        etat: _Etat,
        tm: Matrice,
        elements: list[Objet],
        *,
        compter: bool,
    ) -> Matrice:
        """Montre un texte (``Tj``, ``TJ``, ``'``, ``"``) ; rend la matrice de texte après lui."""
        police, correspondance = etat.police, etat.correspondance
        taille, echelle = etat.taille, etat.echelle
        m = produit(tm, etat.ctm)
        direction = math.hypot(m[0], m[1])
        cadratin = abs(taille) * math.hypot(m[2], m[3])
        mesurable = _fini(*m, taille, echelle, direction, cadratin) and direction > 0
        unite = (m[0] / direction, m[1] / direction) if mesurable else (1.0, 0.0)
        invisible = etat.rendu in _INVISIBLES
        avance = 0.0
        for element in elements:
            if isinstance(element, bytes):
                for code, longueur in correspondance.codes(element):
                    plume.page.codes += compter
                    debut = (avance * m[0] + m[4], avance * m[1] + m[5])
                    largeur = police.largeur(code) or 0.0
                    espace = longueur == 1 and code == 32
                    avance += (largeur * taille + etat.espacement + etat.mots * espace) * echelle
                    fin = (avance * m[0] + m[4], avance * m[1] + m[5])
                    decode = self._decoder(plume, correspondance, code, longueur)
                    if invisible:
                        plume.page.invisibles += len(decode)
                    if mesurable and _fini(*debut, *fin):
                        plume.deplacer(debut, unite, cadratin)
                        plume.ecrire(decode, fin, invisible=invisible)
                    else:
                        plume.rompre()
                        plume.ecrire(decode, (0.0, 0.0), invisible=invisible)
                        plume.rompre()
            elif (ajustement := reel(element)) is not None:
                avance -= ajustement / 1000 * taille * echelle
        return produit((1.0, 0.0, 0.0, 1.0, avance, 0.0), tm)

    @staticmethod
    def _decoder(plume: _Plume, correspondance: Correspondance, code: int, longueur: int) -> str:
        """Texte d'un code : celui du contenu marqué qui le remplace, une fois pour tous ses
        glyphes ; sinon celui de sa police, rien s'il n'est pas décodé."""
        remplacement = plume.remplacement
        if remplacement is not None:
            ecrit, remplacement.ecrit = remplacement.ecrit, True
            return "" if ecrit else remplacement.texte
        decode = correspondance.texte(code, longueur)
        if decode is None:
            plume.page.non_decodes += 1
            return ""
        return decode

    def _objet(
        self,
        plume: _Plume,
        etat: _Etat,
        ressources: dict[str, Objet],
        operandes: list[Objet],
        profondeur: int,
        *,
        compter: bool,
    ) -> None:
        """Objet appelé par ``Do`` (§8.8) : une image est comptée, une forme lue (§8.10)."""
        nomme = nom(operandes[-1]) if operandes else None
        objets = dico(self._resoudre(ressources.get("XObject"))) or {}
        objet = self._resoudre(objets.get(nomme)) if nomme is not None else None
        if not isinstance(objet, Flux):
            return
        sous_type = nom(objet.dico.get("Subtype"))
        if sous_type == "Image":
            plume.page.images += compter
            return
        if sous_type != "Form":
            return
        if profondeur >= PROFONDEUR_MAX:
            plume.page.complete = False
            return
        m = matrice(self._resoudre(objet.dico.get("Matrix"))) or IDENTITE
        siennes = dico(self._resoudre(objet.dico.get("Resources")))
        appele = etat.copie()
        appele.ctm = produit(m, etat.ctm)
        with self._contexte.imbrication():
            self._contenu(
                plume,
                self._document.decoder(objet),
                objet.debut,
                ressources if siennes is None else siennes,
                appele,
                profondeur + 1,
                compter=compter,
            )


def lire(contexte: Contexte, document: Document) -> Texte:
    """Texte des pages de la dernière version d'un document non chiffré. Un flux de contenu
    illisible arrête la lecture de sa page ; un CMap illisible est laissé de côté."""
    retenues, trouvees = pages(contexte, document, PAGES_MAX)
    lecteur = _Lecteur(contexte, document)
    lues: list[Page] = []
    for numero, (page, ressources) in enumerate(retenues, start=1):
        if lecteur.arrete:
            break
        lues.append(lecteur.page(numero, page, ressources))
    illisible = lecteur.illisible or lecteur.polices.illisible
    return Texte(lues, trouvees, lecteur.arrete, illisible)
