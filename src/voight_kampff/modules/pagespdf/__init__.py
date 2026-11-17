"""Module ``pagespdf`` : textes superposés, caches et polices incohérentes des pages d'un PDF
(F-61 ; ADR-0213 à ADR-0216, ADR-0218 ; fiche ``pages-pdf``).

Le module interprète le contenu de chaque page de la dernière version du document, comme un
lecteur l'afficherait, sans rien dessiner (ISO 32000-2, §8 et §9) : le flux de contenu de la
page, les formes qu'il appelle (``Do``), puis les apparences des annotations visibles, hors
champs de formulaire et fenêtres d'annotation (ADR-0214). Il suit la matrice de transformation
(``cm``, ``q``, ``Q``), l'état du texte (``Tf``, ``Tm``, ``Td``, ``Tc``, ``Tw``, ``Tz``,
``TL``, ``Ts``, ``Tr``) et les chemins remplis. Il relève :

1. les **textes superposés** : un texte posé sur un texte différent déjà posé, dont les boîtes
   se recouvrent au moins à moitié (le même texte redit, faux gras ou ombre, ne compte pas) ;
2. les **caches** : un rectangle plein et opaque peint sur un texte déjà posé, qu'il recouvre au
   moins à moitié ;
3. les **familles mélangées** : une même police employée sur une page par plusieurs polices
   d'incorporation différente (sous-ensembles distincts, incorporée ou non, programme TrueType
   ou CFF) ;
4. les **codes hors plage** : des codes dessinés hors de la plage que déclare une police simple
   (``/FirstChar``, ``/LastChar``), écrits après l'extraction de son sous-ensemble (ADR-0216).

La boîte d'un texte va de son point de départ à la somme des avancées de ses glyphes, en
largeur, et de la descente à la montée de la police, en hauteur (ADR-0215). Les largeurs sont
celles que déclare la police (``/Widths``, ``/W``) ; pour les 14 polices standard non
incorporées qui n'en déclarent pas, celles des fichiers AFM d'Adobe (``_polices14``). Un texte
dont les largeurs ne se connaissent pas n'est pas mesuré. Le texte invisible (modes 3 et 7,
couche de texte d'un document numérisé) n'est pas compté. Rien n'est déchiffré : un document
chiffré n'est pas interprété (ADR-0126). Le module n'émet aucun constat : les règles du
catalogue lisent ses observations (ADR-0218).
"""

import math
from collections.abc import Iterator
from dataclasses import dataclass, field

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.pdf import (
    Document,
    Flux,
    Illisible,
    Nom,
    Objet,
    Ref,
    entier,
    operations,
    pages,
)
from voight_kampff.modules.pagespdf import _polices14
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee

__all__ = [
    "CASES_MAX",
    "OBJETS_RESERVES",
    "PAGES_MAX",
    "PROFONDEUR_MAX",
    "RECOUVREMENT",
    "TEXTES_MAX",
    "analyser",
]

RECOUVREMENT = 0.5
"""Part de la plus petite boîte, ou du texte caché, qu'un recouvrement doit atteindre."""
PAGES_MAX = 4096
"""Pages au plus interprétées ; ``pagespdf.pages`` les compte toutes."""
TEXTES_MAX = 1 << 16
"""Textes au plus retenus par page ; au-delà, la page n'est lue qu'en partie."""
PROFONDEUR_MAX = 8
"""Formes au plus imbriquées (``Do`` dans une forme) ; au-delà, la forme n'est pas lue."""
OBJETS_RESERVES = 1 << 18
"""Objets du budget (ES-03) gardés pour finir : l'interprétation s'arrête quand il n'en reste
pas plus, pour que les observations déjà faites soient envoyées (ADR-0213)."""
CASES_MAX = 4096
"""Cases au plus de la grille pour une boîte ; une boîte plus grande est comparée à toutes."""
_CASE = 16.0
"""Côté d'une case de la grille qui range les boîtes, en unités de l'espace de la page."""
_ELEMENTS_MAX = 1 << 16
"""Éléments au plus d'un tableau de largeurs (``/Widths``, ``/W``) ; au-delà, largeurs
inconnues."""
_NOMS_MAX = 64
"""Caractères au plus d'un nom de police observé."""
_ECHELLE_MAX = 1e6
"""Coefficient au plus d'une matrice ou d'une taille : au-delà, le texte n'est pas mesuré."""
_COTE_MAX = 1e7
"""Coordonnée au plus d'une boîte, en valeur absolue : au-delà, elle est hors de toute page."""
_INVISIBLES = frozenset({3, 7})
"""Modes de rendu du texte qui ne peignent rien (§9.3.6)."""
_REMPLISSAGES = frozenset({"f", "F", "f*", "B", "B*", "b", "b*"})
_PEINTURES = _REMPLISSAGES | {"S", "s", "n"}
_CACHEES = 1 << 1 | 1 << 5 | 1 << 0
"""Indicateurs d'une annotation non affichée : invisible, cachée, non vue (§12.5.3)."""
_SANS_APPARENCE = frozenset({"Popup", "Widget"})
"""Annotations dont l'apparence n'est pas interprétée (ADR-0214)."""
_INCORPORATIONS = ("FontFile", "FontFile2", "FontFile3")
_IDENTITE = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
_LOCALISATION = Localisation(chemin="contenu des pages")

type Matrice = tuple[float, float, float, float, float, float]
type Boite = tuple[float, float, float, float]


def _produit(m: Matrice, n: Matrice) -> Matrice:
    """Produit de ``m`` par ``n`` : ``m`` appliquée d'abord (vecteur ligne, §8.3.4)."""
    a, b, c, d, e, f = m
    p, q, r, s, t, u = n
    return (
        a * p + b * r,
        a * q + b * s,
        c * p + d * r,
        c * q + d * s,
        e * p + f * r + t,
        e * q + f * s + u,
    )


def _boite(m: Matrice, x0: float, y0: float, x1: float, y1: float) -> Boite:
    """Boîte alignée sur les axes qui contient le rectangle ``(x0, y0, x1, y1)`` transformé."""
    a, b, c, d, e, f = m
    xs = [x * a + y * c + e for x in (x0, x1) for y in (y0, y1)]
    ys = [x * b + y * d + f for x in (x0, x1) for y in (y0, y1)]
    return (min(xs), min(ys), max(xs), max(ys))


def _finie(b: Boite) -> bool:
    """Vrai si la boîte est dans les bornes de :data:`_COTE_MAX`."""
    return all(-_COTE_MAX <= v <= _COTE_MAX for v in b)


def _aire(b: Boite) -> float:
    return max(b[2] - b[0], 0.0) * max(b[3] - b[1], 0.0)


def _commune(a: Boite, b: Boite) -> float:
    """Aire de l'intersection de deux boîtes."""
    largeur = min(a[2], b[2]) - max(a[0], b[0])
    hauteur = min(a[3], b[3]) - max(a[1], b[1])
    return largeur * hauteur if largeur > 0 and hauteur > 0 else 0.0


def _reel(objet: Objet) -> float | None:
    """Nombre fini, entier ou réel ; ``None`` pour tout autre objet (un booléen n'en est pas un)."""
    if type(objet) is int or type(objet) is float:
        valeur = float(objet)
        return valeur if math.isfinite(valeur) and abs(valeur) <= 1e12 else None
    return None


def _reels(objets: list[Objet], nombre: int) -> list[float] | None:
    """Les ``nombre`` derniers opérandes, s'ils sont tous des nombres."""
    if len(objets) < nombre:
        return None
    lus = [_reel(o) for o in objets[len(objets) - nombre :]]
    return None if any(v is None for v in lus) else [v for v in lus if v is not None]


def _matrice(objet: Objet) -> Matrice | None:
    if not isinstance(objet, list) or len(objet) != 6:
        return None
    lus = _reels(objet, 6)
    return None if lus is None else (lus[0], lus[1], lus[2], lus[3], lus[4], lus[5])


def _nom(objet: Objet) -> str | None:
    return str(objet) if isinstance(objet, Nom) else None


def _dico(valeur: Objet) -> dict[str, Objet] | None:
    if isinstance(valeur, Flux):
        return valeur.dico
    return valeur if isinstance(valeur, dict) else None


# Polices (§9.6 à §9.7 ; ADR-0215, ADR-0216)


def _charger_polices14() -> tuple[
    dict[str, list[str]], dict[str, tuple[float, float, str, dict[str, float]]]
]:
    encodages = {nom: noms.split(" ") for nom, noms in _polices14.ENCODAGES.items()}
    polices = {}
    for nom, (montee, descente, propre, largeurs) in _polices14.POLICES.items():
        mots = largeurs.split(" ")
        polices[nom] = (
            montee / 1000,
            descente / 1000,
            propre,
            {g: int(w) / 1000 for g, w in zip(mots[::2], mots[1::2], strict=True)},
        )
    return encodages, polices


_ENCODAGES, _STANDARD = _charger_polices14()
"""Encodages de l'annexe D et 14 polices standard, lus à l'import : après les restrictions,
plus rien n'est lu sur le disque (ADR-0079)."""


@dataclass(frozen=True, slots=True)
class _Police:
    """Ce qu'une police déclare de ses glyphes, pour une taille de 1."""

    nom: str
    """Nom de la police (``/BaseFont``) sans le préfixe d'un sous-ensemble ; vide pour une
    police Type3 ou sans nom."""
    prefixe: str
    """Préfixe de six capitales d'un sous-ensemble (``ABCDEF+``), vide sinon."""
    incorporation: str
    """Clé du programme incorporé (``FontFile``, ``FontFile2``, ``FontFile3``), ``Type3``, ou
    vide pour une police non incorporée."""
    octets: int
    """Octets d'un code : 1 pour une police simple, 2 pour un CMap Identity-H ; 0 si les codes
    ne se découpent pas (autre CMap, écriture verticale) et que le texte n'est pas mesuré."""
    largeurs: dict[int, float]
    plages: tuple[tuple[int, int, float], ...]
    """Largeurs par plage de codes (``c1 c2 w`` de ``/W``)."""
    defaut: float | None
    """Largeur d'un code sans largeur déclarée ; ``None`` si elle n'est pas connue."""
    premier: int | None
    dernier: int | None
    """Plage déclarée d'une police simple (``/FirstChar``, ``/LastChar``)."""
    montee: float
    descente: float

    def largeur(self, code: int) -> float | None:
        if code in self.largeurs:
            return self.largeurs[code]
        for debut, fin, largeur in self.plages:
            if debut <= code <= fin:
                return largeur
        return self.defaut

    def hors_plage(self, code: int) -> bool:
        if self.premier is None or self.dernier is None:
            return False
        return not self.premier <= code <= self.dernier


_INCONNUE = _Police("", "", "", 0, {}, (), None, None, None, 0.8, -0.2)


def _sous_ensemble(base: str) -> tuple[str, str]:
    """Préfixe d'un sous-ensemble (six capitales suivies de « + », §9.9.2) et nom de la police."""
    if len(base) > 7 and base[6] == "+" and all("A" <= c <= "Z" for c in base[:6]):
        return base[:6], base[7:]
    return "", base


class _Polices:
    """Polices lues une fois chacune, par leur objet."""

    def __init__(self, contexte: Contexte, document: Document) -> None:
        self._contexte = contexte
        self._document = document
        self._lues: dict[object, _Police] = {}

    def _resoudre(self, objet: Objet) -> Objet:
        return self._document.resoudre(objet)

    def police(self, designee: Objet) -> _Police:
        cle: object = designee if isinstance(designee, Ref) else id(designee)
        if cle not in self._lues:
            dico = _dico(self._resoudre(designee))
            self._lues[cle] = _INCONNUE if dico is None else self._lire(dico)
        return self._lues[cle]

    def _lire(self, dico: dict[str, Objet]) -> _Police:
        sous_type = _nom(self._resoudre(dico.get("Subtype")))
        base = _nom(self._resoudre(dico.get("BaseFont"))) or ""
        prefixe, nom = _sous_ensemble(base[:_NOMS_MAX])
        if sous_type == "Type0":
            return self._composite(dico, prefixe, nom)
        if sous_type == "Type3":
            return self._type3(dico)
        descripteur = _dico(self._resoudre(dico.get("FontDescriptor"))) or {}
        incorporation = next((c for c in _INCORPORATIONS if c in descripteur), "")
        montee, descente = self._hauteurs(descripteur)
        premier = entier(self._resoudre(dico.get("FirstChar")))
        dernier = entier(self._resoudre(dico.get("LastChar")))
        largeurs = self._resoudre(dico.get("Widths"))
        if isinstance(largeurs, list) and premier is not None and len(largeurs) <= _ELEMENTS_MAX:
            self._contexte.compter_objets(len(largeurs))
            lues: dict[int, float] = {}
            for rang, largeur in enumerate(largeurs):
                valeur = _reel(self._resoudre(largeur))
                if valeur is not None:
                    lues[premier + rang] = valeur / 1000
            manquante = _reel(self._resoudre(descripteur.get("MissingWidth", 0)))
            return _Police(
                nom,
                prefixe,
                incorporation,
                1,
                lues,
                (),
                0.0 if manquante is None else manquante / 1000,
                premier,
                premier + len(largeurs) - 1 if dernier is None else dernier,
                montee,
                descente,
            )
        standard = _STANDARD.get(nom) if not incorporation and not prefixe else None
        if standard is None:
            return _Police(
                nom, prefixe, incorporation, 1, {}, (), None, None, None, montee, descente
            )
        haut, bas, propre, par_nom = standard
        noms = self._encodage(dico.get("Encoding"), propre)
        lues = {code: par_nom[n] for code, n in enumerate(noms) if n in par_nom}
        return _Police(nom, "", "", 1, lues, (), None, None, None, haut, bas)

    def _encodage(self, designe: Objet, propre: str) -> list[str]:
        """Noms des glyphes des codes 0 à 255 d'une police standard (§9.6.5)."""
        encodage = self._resoudre(designe)
        base = propre
        differences: Objet = None
        if isinstance(encodage, Nom):
            base = str(encodage)
        elif isinstance(encodage, dict):
            base = _nom(self._resoudre(encodage.get("BaseEncoding"))) or propre
            differences = self._resoudre(encodage.get("Differences"))
        if propre in ("Symbol", "ZapfDingbats") or base not in _ENCODAGES:
            base = propre
        noms = list(_ENCODAGES[base])
        code = None
        if isinstance(differences, list) and len(differences) <= _ELEMENTS_MAX:
            self._contexte.compter_objets(len(differences))
            for element in differences:
                if (nombre := entier(element)) is not None:
                    code = nombre
                elif isinstance(element, Nom) and code is not None:
                    if 0 <= code < 256:
                        noms[code] = str(element)
                    code += 1
        return noms

    def _hauteurs(self, descripteur: dict[str, Objet]) -> tuple[float, float]:
        """Montée et descente déclarées (``/Ascent``, ``/Descent``) ; 0,8 et -0,2 à défaut."""
        montee = _reel(self._resoudre(descripteur.get("Ascent")))
        descente = _reel(self._resoudre(descripteur.get("Descent")))
        if montee is None or descente is None or not -4000 <= descente < montee <= 4000:
            return 0.8, -0.2
        return montee / 1000, min(descente, 0.0) / 1000

    def _composite(self, dico: dict[str, Objet], prefixe: str, nom: str) -> _Police:
        """Police Type0 (§9.7) : sa descendante, ses largeurs ``/W`` et ``/DW``."""
        encodage = _nom(self._resoudre(dico.get("Encoding")))
        descendantes = self._resoudre(dico.get("DescendantFonts"))
        descendante = (
            _dico(self._resoudre(descendantes[0]))
            if isinstance(descendantes, list) and descendantes
            else None
        ) or {}
        descripteur = _dico(self._resoudre(descendante.get("FontDescriptor"))) or {}
        incorporation = next((c for c in _INCORPORATIONS if c in descripteur), "")
        montee, descente = self._hauteurs(descripteur)
        defaut = _reel(self._resoudre(descendante.get("DW", 1000)))
        largeurs: dict[int, float] = {}
        plages: list[tuple[int, int, float]] = []
        lues = self._largeurs_w(self._resoudre(descendante.get("W")), largeurs, plages)
        octets = 2 if encodage == "Identity-H" and lues else 0
        return _Police(
            nom,
            prefixe,
            incorporation,
            octets,
            largeurs,
            tuple(plages),
            None if defaut is None else defaut / 1000,
            None,
            None,
            montee,
            descente,
        )

    def _largeurs_w(
        self, w: Objet, largeurs: dict[int, float], plages: list[tuple[int, int, float]]
    ) -> bool:
        """Lit ``/W`` : ``c [w1 w2 …]`` ou ``c1 c2 w`` (§9.7.4.3) ; faux s'il est mal formé."""
        if w is None:
            return True
        if not isinstance(w, list) or len(w) > _ELEMENTS_MAX:
            return False
        self._contexte.compter_objets(len(w))
        rang = 0
        while rang < len(w):
            premier = entier(w[rang])
            suivant = self._resoudre(w[rang + 1]) if rang + 1 < len(w) else None
            if premier is None:
                return False
            if isinstance(suivant, list):
                if len(largeurs) + len(suivant) > _ELEMENTS_MAX:
                    return False
                self._contexte.compter_objets(len(suivant))
                for decalage, largeur in enumerate(suivant):
                    if (valeur := _reel(largeur)) is not None:
                        largeurs[premier + decalage] = valeur / 1000
                rang += 2
                continue
            dernier = entier(suivant)
            largeur = _reel(w[rang + 2]) if rang + 2 < len(w) else None
            if dernier is None or largeur is None:
                return False
            plages.append((premier, dernier, largeur / 1000))
            rang += 3
        return True

    def _type3(self, dico: dict[str, Objet]) -> _Police:
        """Police Type3 (§9.6.4) : largeurs dans l'espace des glyphes, par ``/FontMatrix``."""
        matrice = _matrice(self._resoudre(dico.get("FontMatrix")))
        largeurs = self._resoudre(dico.get("Widths"))
        premier = entier(self._resoudre(dico.get("FirstChar")))
        boite = self._resoudre(dico.get("FontBBox"))
        if (
            matrice is None
            or not isinstance(largeurs, list)
            or premier is None
            or len(largeurs) > _ELEMENTS_MAX
        ):
            return _Police("", "", "Type3", 1, {}, (), None, None, None, 0.8, -0.2)
        self._contexte.compter_objets(len(largeurs))
        lues = {}
        for rang, largeur in enumerate(largeurs):
            valeur = _reel(self._resoudre(largeur))
            if valeur is not None:
                lues[premier + rang] = valeur * matrice[0]
        montee, descente = 0.8, -0.2
        cotes = _reels(boite, 4) if isinstance(boite, list) and len(boite) == 4 else None
        if cotes is not None and cotes[3] * matrice[3] > cotes[1] * matrice[3]:
            montee, descente = cotes[3] * matrice[3], min(cotes[1] * matrice[3], 0.0)
        return _Police("", "", "Type3", 1, lues, (), 0.0, None, None, montee, descente)


# Interprétation d'une page (§8.4, §9.3, §9.4)


@dataclass(slots=True)
class _Etat:
    """État graphique (§8.4.1) : ce que ``q`` garde et ``Q`` rend."""

    ctm: Matrice = _IDENTITE
    police: _Police = _INCONNUE
    taille: float = 0.0
    espacement: float = 0.0
    """``Tc``."""
    mots: float = 0.0
    """``Tw``."""
    echelle: float = 1.0
    """``Tz`` divisé par 100."""
    interligne: float = 0.0
    montee: float = 0.0
    """``Ts``."""
    rendu: int = 0
    opaque: bool = True
    """Remplissage opaque : ``/ca`` de 1, mode de fusion normal, sans masque doux (§11)."""

    def copie(self) -> "_Etat":
        return _Etat(
            self.ctm,
            self.police,
            self.taille,
            self.espacement,
            self.mots,
            self.echelle,
            self.interligne,
            self.montee,
            self.rendu,
            self.opaque,
        )


@dataclass(slots=True)
class _Texte:
    boite: Boite
    codes: bytes
    signes: int
    """Codes autres que l'espace (code 32 d'une police simple)."""
    cache: bool = False


@dataclass(slots=True)
class _Page:
    """Ce qu'on a relevé sur une page."""

    numero: int
    textes: list[_Texte] = field(default_factory=list)
    grille: dict[tuple[int, int], list[int]] = field(default_factory=dict)
    grands: list[int] = field(default_factory=list)
    superpositions: int = 0
    d_un_signe: int = 0
    caches: int = 0
    caches_textes: int = 0
    non_mesures: int = 0
    hors_plage: int = 0
    polices: dict[str, set[tuple[str, str]]] = field(default_factory=dict)
    """Par nom de police, les incorporations employées sur la page (préfixe, programme)."""
    complete: bool = True

    def cases(self, boite: Boite) -> list[tuple[int, int]] | None:
        x0, y0 = math.floor(boite[0] / _CASE), math.floor(boite[1] / _CASE)
        x1, y1 = math.floor(boite[2] / _CASE), math.floor(boite[3] / _CASE)
        if (x1 - x0 + 1) * (y1 - y0 + 1) > CASES_MAX:
            return None
        return [(i, j) for i in range(x0, x1 + 1) for j in range(y0, y1 + 1)]

    def voisins(self, contexte: Contexte, boite: Boite) -> Iterator[_Texte]:
        """Textes déjà posés dont la boîte peut rencontrer celle-ci."""
        cases = self.cases(boite)
        if cases is None:
            rangs = set(range(len(self.textes)))
        else:
            rangs = set(self.grands)
            for case in cases:
                rangs.update(self.grille.get(case, ()))
        contexte.compter_objets(len(rangs) // 64)
        for rang in sorted(rangs):
            yield self.textes[rang]

    def ranger(self, texte: _Texte) -> None:
        rang = len(self.textes)
        self.textes.append(texte)
        cases = self.cases(texte.boite)
        if cases is None:
            self.grands.append(rang)
            return
        for case in cases:
            self.grille.setdefault(case, []).append(rang)


class _Interprete:
    """Interprète les pages d'un document, l'une après l'autre."""

    def __init__(self, contexte: Contexte, document: Document) -> None:
        self._contexte = contexte
        self._document = document
        self._polices = _Polices(contexte, document)
        self.polices_employees: set[object] = set()
        self.illisible: Illisible | None = None
        self.arrete = False
        """Vrai si l'interprétation s'est arrêtée avant le budget (OBJETS_RESERVES)."""

    def _resoudre(self, objet: Objet) -> Objet:
        return self._document.resoudre(objet)

    def page(self, numero: int, page: dict[str, Objet], ressources: Objet) -> _Page:
        relevee = _Page(numero)
        try:
            contenus = self._resoudre(page.get("Contents"))
            flux = contenus if isinstance(contenus, list) else [contenus]
            morceaux: list[bytes] = []
            debut = 0
            for element in flux:
                lu = self._resoudre(element)
                if isinstance(lu, Flux):
                    debut = debut or lu.debut
                    morceaux.append(self._document.decoder(lu))
            self._contenu(
                relevee,
                b"\n".join(morceaux),
                debut,
                _dico(self._resoudre(ressources)) or {},
                _Etat(),
                0,
            )
            self._annotations(relevee, page)
        except Illisible as illisible:
            self.illisible = self.illisible or illisible
            relevee.complete = False
        return relevee

    def _annotations(self, relevee: _Page, page: dict[str, Objet]) -> None:
        """Apparences normales des annotations visibles, peintes après le contenu (§12.5.5)."""
        annotations = self._resoudre(page.get("Annots"))
        for designee in annotations if isinstance(annotations, list) else []:
            if self.arrete:
                return
            annotation = _dico(self._resoudre(designee))
            if (
                annotation is None
                or _nom(self._resoudre(annotation.get("Subtype"))) in _SANS_APPARENCE
            ):
                continue
            indicateurs = entier(self._resoudre(annotation.get("F"))) or 0
            rect = self._resoudre(annotation.get("Rect"))
            apparences = _dico(self._resoudre(annotation.get("AP"))) or {}
            normale = self._resoudre(apparences.get("N"))
            if isinstance(normale, dict):  # apparences par état : celle de /AS
                normale = self._resoudre(
                    normale.get(_nom(self._resoudre(annotation.get("AS"))) or "")
                )
            cotes = _reels(rect, 4) if isinstance(rect, list) and len(rect) == 4 else None
            if indicateurs & _CACHEES or not isinstance(normale, Flux) or cotes is None:
                continue
            matrice = _matrice(self._resoudre(normale.dico.get("Matrix"))) or _IDENTITE
            bbox = self._resoudre(normale.dico.get("BBox"))
            cadre = _reels(bbox, 4) if isinstance(bbox, list) and len(bbox) == 4 else None
            if cadre is None:
                continue
            x0, y0, x1, y1 = _boite(matrice, *cadre)
            r0, r1 = min(cotes[0], cotes[2]), max(cotes[0], cotes[2])
            s0, s1 = min(cotes[1], cotes[3]), max(cotes[1], cotes[3])
            if x1 - x0 <= 0 or y1 - y0 <= 0:
                continue
            sx, sy = (r1 - r0) / (x1 - x0), (s1 - s0) / (y1 - y0)
            ajustement: Matrice = (sx, 0.0, 0.0, sy, r0 - x0 * sx, s0 - y0 * sy)
            ressources = _dico(self._resoudre(normale.dico.get("Resources"))) or {}
            self._contenu(
                relevee,
                self._document.decoder(normale),
                normale.debut,
                ressources,
                _Etat(ctm=_produit(matrice, ajustement)),
                1,
            )

    def _contenu(
        self,
        relevee: _Page,
        donnees: bytes,
        debut: int,
        ressources: dict[str, Objet],
        etat: _Etat,
        profondeur: int,
    ) -> None:
        """Interprète un flux de contenu depuis l'état graphique ``etat`` (§8.4.1)."""
        pile: list[_Etat] = []
        tm = tlm = _IDENTITE
        chemin: list[Boite | None] = []
        """Rectangles du chemin en cours, dans l'espace de la page ; ``None`` pour un tracé
        qui n'en est pas un."""
        points: list[tuple[float, float]] = []
        for rang, (operateur, operandes) in enumerate(operations(self._contexte, donnees, debut)):
            if rang % 1024 == 0 and self._contexte.objets > OBJETS_MAX - OBJETS_RESERVES:
                self.arrete = True
                relevee.complete = False
                return
            if operateur == "q":
                pile.append(etat.copie())
            elif operateur == "Q":
                if pile:
                    etat = pile.pop()
            elif operateur == "cm":
                if (m := _reels(operandes, 6)) is not None:
                    etat.ctm = _produit((m[0], m[1], m[2], m[3], m[4], m[5]), etat.ctm)
            elif operateur == "gs":
                self._etat_graphique(etat, ressources, operandes)
            elif operateur == "BT":
                tm = tlm = _IDENTITE
            elif operateur == "Tf":
                self._police(etat, ressources, operandes)
            elif operateur in ("Tc", "Tw", "Tz", "TL", "Ts", "Tr"):
                self._etat_du_texte(etat, operateur, operandes)
            elif operateur in ("Td", "TD"):
                if (d := _reels(operandes, 2)) is not None:
                    if operateur == "TD":
                        etat.interligne = -d[1]
                    tm = tlm = _produit((1.0, 0.0, 0.0, 1.0, d[0], d[1]), tlm)
            elif operateur == "Tm":
                if (m := _reels(operandes, 6)) is not None:
                    tm = tlm = (m[0], m[1], m[2], m[3], m[4], m[5])
            elif operateur == "T*":
                tm = tlm = _produit((1.0, 0.0, 0.0, 1.0, 0.0, -etat.interligne), tlm)
            elif operateur in ("Tj", "'", '"', "TJ"):
                if operateur in ("'", '"'):
                    if operateur == '"' and (d := _reels(operandes[:-1], 2)) is not None:
                        etat.mots, etat.espacement = d
                    tm = tlm = _produit((1.0, 0.0, 0.0, 1.0, 0.0, -etat.interligne), tlm)
                elements = operandes[-1] if operandes else None
                if operateur != "TJ":
                    elements = [elements]
                if isinstance(elements, list):
                    tm = self._montrer(relevee, etat, tm, elements)
            elif operateur == "re":
                if points:
                    chemin.append(self._polygone(etat.ctm, points))
                    points = []
                if (r := _reels(operandes, 4)) is not None:
                    chemin.append(self._rectangle(etat.ctm, r))
            elif operateur in ("m", "l"):
                if (p := _reels(operandes, 2)) is not None:
                    if operateur == "m" and points:
                        chemin.append(self._polygone(etat.ctm, points))
                        points = []
                    points.append((p[0], p[1]))
            elif operateur in ("c", "v", "y"):
                points.append((math.nan, math.nan))  # courbe : pas un rectangle
            elif operateur in _PEINTURES:
                if points:
                    chemin.append(self._polygone(etat.ctm, points))
                    points = []
                if operateur in _REMPLISSAGES and etat.opaque:
                    for boite in chemin:
                        if boite is not None:
                            self._couvrir(relevee, boite)
                chemin = []
            elif operateur == "Do":
                self._forme(relevee, etat, ressources, operandes, profondeur)
            if self.arrete:
                return

    # Texte

    def _police(self, etat: _Etat, ressources: dict[str, Objet], operandes: list[Objet]) -> None:
        if len(operandes) < 2 or (taille := _reel(operandes[-1])) is None:
            return
        nom = _nom(operandes[-2])
        polices = _dico(self._resoudre(ressources.get("Font"))) or {}
        designee = polices.get(nom) if nom is not None else None
        etat.taille = taille
        etat.police = _INCONNUE if designee is None else self._polices.police(designee)
        if designee is not None:
            self.polices_employees.add(designee if isinstance(designee, Ref) else id(designee))

    def _etat_du_texte(self, etat: _Etat, operateur: str, operandes: list[Objet]) -> None:
        valeur = _reel(operandes[-1]) if operandes else None
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
        elif operateur == "Ts":
            etat.montee = valeur
        elif valeur == int(valeur):
            etat.rendu = int(valeur)

    def _etat_graphique(
        self, etat: _Etat, ressources: dict[str, Objet], operandes: list[Objet]
    ) -> None:
        """Dictionnaire d'état graphique (§8.4.5) : opacité du remplissage et police."""
        nom = _nom(operandes[-1]) if operandes else None
        etats = _dico(self._resoudre(ressources.get("ExtGState"))) or {}
        dico = _dico(self._resoudre(etats.get(nom))) if nom is not None else None
        if dico is None:
            return
        if "ca" in dico:
            etat.opaque = _reel(self._resoudre(dico["ca"])) == 1.0
        fusion = self._resoudre(dico.get("BM"))
        if isinstance(fusion, list):
            fusion = fusion[0] if fusion else None
        if fusion is not None:
            etat.opaque = etat.opaque and _nom(fusion) in ("Normal", "Compatible")
        masque = self._resoudre(dico.get("SMask"))
        if masque is not None and _nom(masque) != "None":
            etat.opaque = False
        police = self._resoudre(dico.get("Font"))
        if isinstance(police, list) and len(police) == 2 and (taille := _reel(police[1])):
            etat.police, etat.taille = self._polices.police(police[0]), taille

    def _montrer(self, relevee: _Page, etat: _Etat, tm: Matrice, elements: list[Objet]) -> Matrice:
        """Pose un texte (``Tj``, ``TJ``, ``'``, ``"``) ; renvoie la matrice de texte après lui."""
        police, taille, echelle = etat.police, etat.taille, etat.echelle
        avance, gauche, droite = 0.0, 0.0, 0.0
        codes = bytearray()
        signes = 0
        mesurable = police.octets > 0
        for element in elements:
            if isinstance(element, bytes):
                pas = police.octets or 1
                for rang in range(0, len(element) - pas + 1, pas):
                    code = int.from_bytes(element[rang : rang + pas], "big")
                    codes += element[rang : rang + pas]
                    espace = pas == 1 and code == 32
                    signes += not espace
                    if police.hors_plage(code) and etat.rendu not in _INVISIBLES:
                        relevee.hors_plage += 1
                    largeur = police.largeur(code)
                    if largeur is None:
                        mesurable = False
                        continue
                    avance += (largeur * taille + etat.espacement + etat.mots * espace) * echelle
                    gauche, droite = min(gauche, avance), max(droite, avance)
            elif (ajustement := _reel(element)) is not None:
                avance -= ajustement / 1000 * taille * echelle
                gauche, droite = min(gauche, avance), max(droite, avance)
        if not codes:
            return tm
        if police.nom and etat.rendu not in _INVISIBLES:
            relevee.polices.setdefault(police.nom, set()).add(
                (police.prefixe, police.incorporation)
            )
        apres = _produit((1.0, 0.0, 0.0, 1.0, avance, 0.0), tm)
        if etat.rendu in _INVISIBLES:
            return apres
        matrice = _produit(tm, etat.ctm)
        if not mesurable or max(abs(v) for v in (*matrice[:4], taille, echelle)) > _ECHELLE_MAX:
            relevee.non_mesures += 1
            return apres
        bas = police.descente * taille + etat.montee
        haut = police.montee * taille + etat.montee
        boite = _boite(matrice, gauche, min(bas, haut), droite, max(bas, haut))
        if not _finie(boite):
            relevee.non_mesures += 1
            return apres
        texte = _Texte(boite, bytes(codes), signes)
        if _aire(boite) > 0 and signes:
            self._comparer(relevee, texte)
        if len(relevee.textes) >= TEXTES_MAX:
            relevee.complete = False
        else:
            relevee.ranger(texte)
        return apres

    def _comparer(self, relevee: _Page, texte: _Texte) -> None:
        """Texte posé sur un texte différent déjà posé, qu'il recouvre au moins à moitié."""
        aire = _aire(texte.boite)
        for autre in relevee.voisins(self._contexte, texte.boite):
            if autre.codes == texte.codes or not autre.signes:
                continue
            plus_petite = min(aire, _aire(autre.boite))
            if plus_petite > 0 and _commune(texte.boite, autre.boite) >= RECOUVREMENT * plus_petite:
                if min(texte.signes, autre.signes) >= 2:
                    relevee.superpositions += 1
                else:
                    relevee.d_un_signe += 1
                return

    # Chemins

    @staticmethod
    def _rectangle(ctm: Matrice, r: list[float]) -> Boite | None:
        """Rectangle ``re`` dans l'espace de la page ; ``None`` s'il n'y reste pas aligné sur les
        axes (rotation autre qu'un quart de tour, inclinaison)."""
        a, b, c, d = ctm[:4]
        if not (b == 0 and c == 0) and not (a == 0 and d == 0):
            return None
        return _boite(ctm, r[0], r[1], r[0] + r[2], r[1] + r[3])

    @staticmethod
    def _polygone(ctm: Matrice, points: list[tuple[float, float]]) -> Boite | None:
        """Quatre segments aux côtés alignés sur les axes, refermés ou non ; ``None`` sinon."""
        if len(points) == 5 and points[4] == points[0]:
            points = points[:4]
        if len(points) != 4 or any(math.isnan(x) for x, _ in points):
            return None
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1], strict=True):
            if x0 != x1 and y0 != y1:
                return None
        xs, ys = [x for x, _ in points], [y for _, y in points]
        return _Interprete._rectangle(ctm, [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)])

    def _couvrir(self, relevee: _Page, boite: Boite) -> None:
        """Rectangle plein et opaque : les textes déjà posés qu'il cache au moins à moitié."""
        if not _finie(boite):
            return
        cache = False
        for texte in relevee.voisins(self._contexte, boite):
            aire = _aire(texte.boite)
            if texte.cache or aire <= 0 or not texte.signes:
                continue
            if _commune(boite, texte.boite) >= RECOUVREMENT * aire:
                texte.cache = cache = True
                relevee.caches_textes += 1
        relevee.caches += cache

    # Formes

    def _forme(
        self,
        relevee: _Page,
        etat: _Etat,
        ressources: dict[str, Objet],
        operandes: list[Objet],
        profondeur: int,
    ) -> None:
        """Forme appelée par ``Do`` (§8.10) ; une image n'est pas lue."""
        nom = _nom(operandes[-1]) if operandes else None
        objets = _dico(self._resoudre(ressources.get("XObject"))) or {}
        forme = self._resoudre(objets.get(nom)) if nom is not None else None
        if not isinstance(forme, Flux) or _nom(forme.dico.get("Subtype")) != "Form":
            return
        if profondeur >= PROFONDEUR_MAX:
            relevee.complete = False
            return
        matrice = _matrice(self._resoudre(forme.dico.get("Matrix"))) or _IDENTITE
        siennes = _dico(self._resoudre(forme.dico.get("Resources")))
        appele = etat.copie()
        appele.ctm = _produit(matrice, etat.ctm)
        with self._contexte.imbrication():
            self._contenu(
                relevee,
                self._document.decoder(forme),
                forme.debut,
                ressources if siennes is None else siennes,
                appele,
                profondeur + 1,
            )


# Pages du document (§7.7.3)


def _pages(
    contexte: Contexte, document: Document
) -> tuple[list[tuple[dict[str, Objet], Objet]], int]:
    """Pages, dans l'ordre, avec leurs ressources héritées (§7.7.3.4), au plus
    :data:`PAGES_MAX` ; et le nombre de pages trouvées (parcours du lecteur, partagé avec
    ``actifspdf``)."""
    return pages(contexte, document, PAGES_MAX)


# Analyse


def analyser(contexte: Contexte) -> None:
    try:
        document = Document(contexte)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    if "Encrypt" in document.trailer:
        contexte.observer("pagespdf.chiffre", True)
        contexte.non_mener(
            RaisonNonMenee.FORMAT_PARTIEL,
            localisation=Localisation(chemin="contenu des pages (document chiffré)"),
        )
        return
    try:
        pages, trouvees = _pages(contexte, document)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    interprete = _Interprete(contexte, document)
    relevees: list[_Page] = []
    for numero, (page, ressources) in enumerate(pages, start=1):
        if interprete.arrete:
            break
        relevees.append(interprete.page(numero, page, ressources))
    if (erreur := interprete.illisible) is not None:
        contexte.non_mener(erreur.raison, localisation=erreur.localisation(contexte.taille))
    _observer(contexte, relevees, trouvees, interprete)


def _observer(
    contexte: Contexte, relevees: list[_Page], trouvees: int, interprete: _Interprete
) -> None:
    contexte.observer("pagespdf.pages", trouvees, localisation=_LOCALISATION)
    contexte.observer("pagespdf.pages_lues", sum(1 for p in relevees if p.complete))
    if interprete.arrete:
        contexte.observer("pagespdf.arret_avant_budget", True)
    contexte.observer("pagespdf.textes", sum(len(p.textes) for p in relevees))
    contexte.observer("pagespdf.textes_non_mesures", sum(p.non_mesures for p in relevees))
    contexte.observer("pagespdf.polices", len(interprete.polices_employees))
    _releve(contexte, "superpositions", [(p.numero, p.superpositions) for p in relevees])
    contexte.observer("pagespdf.superpositions_d_un_signe", sum(p.d_un_signe for p in relevees))
    _releve(contexte, "caches", [(p.numero, p.caches) for p in relevees])
    contexte.observer("pagespdf.textes_caches", sum(p.caches_textes for p in relevees))
    melangees = {
        p.numero: [nom for nom, vues in sorted(p.polices.items()) if len(vues) >= 2]
        for p in relevees
    }
    _releve(contexte, "familles_melangees", [(n, len(noms)) for n, noms in melangees.items()])
    noms = sorted({nom for liste in melangees.values() for nom in liste})
    if noms:
        valeurs.observer(contexte, "pagespdf.familles_melangees.noms", noms)
    _releve(contexte, "codes_hors_plage", [(p.numero, p.hors_plage) for p in relevees])


def _releve(contexte: Contexte, nom: str, par_page: list[tuple[int, int]]) -> None:
    """Total d'un relevé, et s'il y en a, la première page et la liste des pages concernées."""
    concernees = [(numero, nombre) for numero, nombre in par_page if nombre]
    contexte.observer(f"pagespdf.{nom}", sum(nombre for _, nombre in concernees))
    if concernees:
        contexte.observer(f"pagespdf.{nom}.premiere_page", concernees[0][0])
        valeurs.observer(contexte, f"pagespdf.{nom}.pages", [n for n, _ in concernees])
