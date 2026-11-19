"""Polices d'un PDF : largeurs et texte de leurs codes (ISO 32000-2, §9.6 à §9.10).

Lecteur partagé par ``pagespdf``, qui mesure les textes d'une page (T51, ADR-0215, ADR-0216),
et ``caracteres``, qui en lit le texte (complément de T53, ADR-0246). Ce que ``pagespdf`` lit
d'une police est inchangé depuis T51 : :class:`Police`, par :meth:`Polices.police`. Le texte
d'un code se lit à part, par :meth:`Polices.correspondance`, pour que ``pagespdf`` ne lise ni ne
compte rien de plus :

1. le CMap ``/ToUnicode`` de la police (§9.10.3), s'il donne le texte du code ;
2. sinon, pour une police simple, le nom du glyphe que lui donne son encodage (encodage de base
   et ``/Differences``, §9.6.5), traduit par l'Adobe Glyph List (``_glyphes``, spécification de
   l'AGL, §2) ; un nom que l'AGL fait correspondre à l'usage privé (petites capitales, chiffres
   de style d'Adobe) n'est pas traduit ;
3. sinon, le code n'est pas décodé.

Les codes d'une police simple ont un octet ; ceux d'une police composite, deux pour les CMap
Identity-H et Identity-V, sinon la longueur que disent les plages de codes de son CMap
incorporé ou de son ``/ToUnicode`` (§9.7.6.2), deux à défaut. Les CMap prédéfinis des écritures
chinoise, japonaise et coréenne ne sont pas livrés (ADR-0246).
"""

import bisect
import math
from collections.abc import Iterator
from dataclasses import dataclass

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import _glyphes, _polices14
from voight_kampff.modules._lecture.pdf import (
    Document,
    Flux,
    Illisible,
    Nom,
    Objet,
    Ref,
    entier,
    operations,
)

__all__ = [
    "AUCUNE",
    "ELEMENTS_MAX",
    "IDENTITE",
    "INCONNUE",
    "Correspondance",
    "Matrice",
    "Police",
    "Polices",
    "dico",
    "matrice",
    "nom",
    "produit",
    "reel",
    "reels",
    "sous_ensemble",
    "texte_du_glyphe",
]

ELEMENTS_MAX = 1 << 16
"""Éléments au plus d'un tableau de largeurs (``/Widths``, ``/W``) ou de ``/Differences`` ; au-
delà, largeurs inconnues ou différences ignorées. Plages au plus d'un CMap."""
_NOMS_MAX = 64
"""Caractères au plus d'un nom de police observé."""
_INCORPORATIONS = ("FontFile", "FontFile2", "FontFile3")
IDENTITE = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

type Matrice = tuple[float, float, float, float, float, float]


def produit(m: Matrice, n: Matrice) -> Matrice:
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


def reel(objet: Objet) -> float | None:
    """Nombre fini, entier ou réel ; ``None`` pour tout autre objet (un booléen n'en est pas un)."""
    if type(objet) is int or type(objet) is float:
        valeur = float(objet)
        return valeur if math.isfinite(valeur) and abs(valeur) <= 1e12 else None
    return None


def reels(objets: list[Objet], nombre: int) -> list[float] | None:
    """Les ``nombre`` derniers opérandes, s'ils sont tous des nombres."""
    if len(objets) < nombre:
        return None
    lus = [reel(o) for o in objets[len(objets) - nombre :]]
    return None if any(v is None for v in lus) else [v for v in lus if v is not None]


def matrice(objet: Objet) -> Matrice | None:
    if not isinstance(objet, list) or len(objet) != 6:
        return None
    lus = reels(objet, 6)
    return None if lus is None else (lus[0], lus[1], lus[2], lus[3], lus[4], lus[5])


def nom(objet: Objet) -> str | None:
    return str(objet) if isinstance(objet, Nom) else None


def dico(valeur: Objet) -> dict[str, Objet] | None:
    if isinstance(valeur, Flux):
        return valeur.dico
    return valeur if isinstance(valeur, dict) else None


# Données de référence, lues à l'import : après les restrictions, plus rien n'est lu sur le
# disque (ADR-0079).


def _charger_polices14() -> tuple[
    dict[str, list[str]], dict[str, tuple[float, float, str, dict[str, float]]]
]:
    encodages = {n: noms.split(" ") for n, noms in _polices14.ENCODAGES.items()}
    polices = {}
    for n, (montee, descente, propre, largeurs) in _polices14.POLICES.items():
        mots = largeurs.split(" ")
        polices[n] = (
            montee / 1000,
            descente / 1000,
            propre,
            {g: int(w) / 1000 for g, w in zip(mots[::2], mots[1::2], strict=True)},
        )
    return encodages, polices


_ENCODAGES, _STANDARD = _charger_polices14()
"""Encodages de l'annexe D et 14 polices standard."""
_BASES = ("StandardEncoding", "WinAnsiEncoding", "MacRomanEncoding")
"""Encodages de base qu'un ``/Encoding`` peut nommer et que le projet connaît ; MacExpertEncoding
ne l'est pas."""


def _points(texte: str) -> dict[str, str]:
    lus = {}
    for jeton in texte.split(" "):
        n, points = jeton.split("=")
        lus[n] = "".join(chr(int(p, 16)) for p in points.split("+"))
    return lus


_AGL = _points(_glyphes.AGL)
_ZAPF = _points(_glyphes.ZAPF_DINGBATS)
_HEXADECIMAL = frozenset("0123456789ABCDEF")


def _prive(texte: str) -> bool:
    return any(0xE000 <= ord(c) <= 0xF8FF for c in texte)


def _composant(composant: str, zapf: bool) -> str:
    """Texte d'un composant d'un nom de glyphe (spécification de l'AGL, §2, étape 3)."""
    if zapf and composant in _ZAPF:
        return _ZAPF[composant]
    if composant in _AGL:
        texte = _AGL[composant]
        return "" if _prive(texte) else texte
    chiffres = composant[3:]
    if composant.startswith("uni") and chiffres and len(chiffres) % 4 == 0:
        if set(chiffres) <= _HEXADECIMAL:
            points = [int(chiffres[i : i + 4], 16) for i in range(0, len(chiffres), 4)]
            if not any(0xD800 <= p <= 0xDFFF for p in points):
                return "".join(map(chr, points))
        return ""
    chiffres = composant[1:]
    if composant.startswith("u") and 4 <= len(chiffres) <= 6 and set(chiffres) <= _HEXADECIMAL:
        point = int(chiffres, 16)
        if point <= 0x10FFFF and not 0xD800 <= point <= 0xDFFF:
            return chr(point)
    return ""


def texte_du_glyphe(glyphe: str, *, zapf: bool = False) -> str | None:
    """Texte que désigne un nom de glyphe (spécification de l'AGL, §2) ; ``None`` s'il n'en désigne
    aucun. ``zapf`` : la police est ZapfDingbats, dont les noms ``a1`` à ``a206`` ont leur liste.
    """
    texte = "".join(_composant(c, zapf) for c in glyphe.split(".", 1)[0].split("_"))
    return texte or None


# Polices (§9.6 à §9.7 ; T51, ADR-0215, ADR-0216)


@dataclass(frozen=True, slots=True)
class Police:
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


INCONNUE = Police("", "", "", 0, {}, (), None, None, None, 0.8, -0.2)


def sous_ensemble(base: str) -> tuple[str, str]:
    """Préfixe d'un sous-ensemble (six capitales suivies de « + », §9.9.2) et nom de la police."""
    if len(base) > 7 and base[6] == "+" and all("A" <= c <= "Z" for c in base[:6]):
        return base[:6], base[7:]
    return "", base


# Texte des codes (§9.10)


@dataclass(frozen=True, slots=True)
class Correspondance:
    """Ce qui fait d'une chaîne de codes un texte : découpage en codes, texte de chaque code."""

    pas: int
    """Octets d'un code ; 0 : selon les plages de codes :attr:`espaces`."""
    espaces: tuple[tuple[bytes, bytes], ...]
    """Plages de codes du CMap (``begincodespacerange``) : bornes basse et haute, de même
    longueur, comparées octet par octet (§9.7.6.2)."""
    table: dict[tuple[int, int], str]
    """Texte de chaque code de ``/ToUnicode`` (``bfchar``), par longueur et valeur du code."""
    plages: tuple[tuple[int, int, int, bytes | list[str]], ...]
    """Plages de ``/ToUnicode`` (``bfrange``), triées : longueur, premier et dernier code, puis
    texte UTF-16BE du premier code, ou liste des textes des codes."""
    noms: tuple[str, ...]
    """Nom du glyphe de chaque code d'une police simple, vide si l'encodage n'en dit rien."""
    zapf: bool

    def codes(self, chaine: bytes) -> Iterator[tuple[int, int]]:
        """Codes d'une chaîne, dans l'ordre : leur valeur et leur longueur en octets. Des octets
        hors de toute plage de codes forment un code d'un octet (§9.7.6.3)."""
        rang = 0
        while rang < len(chaine):
            longueur = self.pas or self._longueur(chaine, rang)
            if rang + longueur > len(chaine):
                return  # code coupé à la fin de la chaîne : rien n'est affiché
            yield int.from_bytes(chaine[rang : rang + longueur]), longueur
            rang += longueur

    def _longueur(self, chaine: bytes, rang: int) -> int:
        for bas, haut in self.espaces:
            morceau = chaine[rang : rang + len(bas)]
            if len(morceau) == len(bas) and all(
                b <= c <= h for b, c, h in zip(bas, morceau, haut, strict=True)
            ):
                return len(bas)
        return 1

    def texte(self, code: int, longueur: int) -> str | None:
        """Texte du code ; ``None`` s'il n'est pas décodé."""
        trouve = self.table.get((longueur, code))
        if trouve is not None:
            return trouve
        rang = bisect.bisect_right(self.plages, (longueur, code, 1 << 32)) - 1
        if rang >= 0:
            taille, debut, fin, cible = self.plages[rang]
            if taille == longueur and debut <= code <= fin:
                if isinstance(cible, list):
                    return cible[code - debut] if code - debut < len(cible) else None
                return _incremente(cible, code - debut)
        if longueur == 1 and self.noms and self.noms[code]:
            return texte_du_glyphe(self.noms[code], zapf=self.zapf)
        return None


def _utf16(octets: bytes) -> str:
    return octets.decode("utf-16-be", "replace")


def _incremente(debut: bytes, decalage: int) -> str | None:
    """Texte UTF-16BE ``debut`` dont le dernier octet est augmenté de ``decalage``, la retenue
    passant aux octets précédents (§9.10.3)."""
    valeur = int.from_bytes(debut) + decalage
    if valeur >= 1 << (8 * len(debut)):
        return None
    return _utf16(valeur.to_bytes(len(debut)))


AUCUNE = Correspondance(1, (), {}, (), (), False)
"""Police inconnue : codes d'un octet, aucun décodé."""


def _triees(
    plages: list[tuple[int, int, int, bytes | list[str]]],
) -> tuple[tuple[int, int, int, bytes | list[str]], ...]:
    """Plages triées par longueur et codes ; deux plages aux mêmes codes gardent leur ordre."""
    return tuple(sorted(plages, key=lambda plage: plage[:3]))


class Polices:
    """Polices lues une fois chacune, par leur objet."""

    def __init__(self, contexte: Contexte, document: Document) -> None:
        self._contexte = contexte
        self._document = document
        self._lues: dict[object, Police] = {}
        self._correspondances: dict[object, Correspondance] = {}
        self.illisible: Illisible | None = None
        """Premier CMap ``/ToUnicode`` illisible, laissé de côté."""

    def _resoudre(self, objet: Objet) -> Objet:
        return self._document.resoudre(objet)

    def police(self, designee: Objet) -> Police:
        cle: object = designee if isinstance(designee, Ref) else id(designee)
        if cle not in self._lues:
            lu = dico(self._resoudre(designee))
            self._lues[cle] = INCONNUE if lu is None else self._lire(lu)
        return self._lues[cle]

    def _lire(self, lu: dict[str, Objet]) -> Police:
        sous_type = nom(self._resoudre(lu.get("Subtype")))
        base = nom(self._resoudre(lu.get("BaseFont"))) or ""
        prefixe, nom_ = sous_ensemble(base[:_NOMS_MAX])
        if sous_type == "Type0":
            return self._composite(lu, prefixe, nom_)
        if sous_type == "Type3":
            return self._type3(lu)
        descripteur = dico(self._resoudre(lu.get("FontDescriptor"))) or {}
        incorporation = next((c for c in _INCORPORATIONS if c in descripteur), "")
        montee, descente = self._hauteurs(descripteur)
        premier = entier(self._resoudre(lu.get("FirstChar")))
        dernier = entier(self._resoudre(lu.get("LastChar")))
        largeurs = self._resoudre(lu.get("Widths"))
        if isinstance(largeurs, list) and premier is not None and len(largeurs) <= ELEMENTS_MAX:
            self._contexte.compter_objets(len(largeurs))
            lues: dict[int, float] = {}
            for rang, largeur in enumerate(largeurs):
                valeur = reel(self._resoudre(largeur))
                if valeur is not None:
                    lues[premier + rang] = valeur / 1000
            manquante = reel(self._resoudre(descripteur.get("MissingWidth", 0)))
            return Police(
                nom_,
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
        standard = _STANDARD.get(nom_) if not incorporation and not prefixe else None
        if standard is None:
            return Police(
                nom_, prefixe, incorporation, 1, {}, (), None, None, None, montee, descente
            )
        haut, bas, propre, par_nom = standard
        noms = self._encodage(lu.get("Encoding"), propre)
        lues = {code: par_nom[n] for code, n in enumerate(noms) if n in par_nom}
        return Police(nom_, "", "", 1, lues, (), None, None, None, haut, bas)

    def _encodage(self, designe: Objet, propre: str) -> list[str]:
        """Noms des glyphes des codes 0 à 255 d'une police standard (§9.6.5)."""
        encodage = self._resoudre(designe)
        base = propre
        differences: Objet = None
        if isinstance(encodage, Nom):
            base = str(encodage)
        elif isinstance(encodage, dict):
            base = nom(self._resoudre(encodage.get("BaseEncoding"))) or propre
            differences = self._resoudre(encodage.get("Differences"))
        if propre in ("Symbol", "ZapfDingbats") or base not in _ENCODAGES:
            base = propre
        noms = list(_ENCODAGES[base])
        self._differences(differences, noms)
        return noms

    def _differences(self, differences: Objet, noms: list[str]) -> None:
        """Applique ``/Differences`` (§9.6.5.1) aux noms des codes 0 à 255."""
        code = None
        if isinstance(differences, list) and len(differences) <= ELEMENTS_MAX:
            self._contexte.compter_objets(len(differences))
            for element in differences:
                if (nombre := entier(element)) is not None:
                    code = nombre
                elif isinstance(element, Nom) and code is not None:
                    if 0 <= code < 256:
                        noms[code] = str(element)
                    code += 1

    def _hauteurs(self, descripteur: dict[str, Objet]) -> tuple[float, float]:
        """Montée et descente déclarées (``/Ascent``, ``/Descent``) ; 0,8 et -0,2 à défaut."""
        montee = reel(self._resoudre(descripteur.get("Ascent")))
        descente = reel(self._resoudre(descripteur.get("Descent")))
        if montee is None or descente is None or not -4000 <= descente < montee <= 4000:
            return 0.8, -0.2
        return montee / 1000, min(descente, 0.0) / 1000

    def _descendante(self, lu: dict[str, Objet]) -> dict[str, Objet]:
        descendantes = self._resoudre(lu.get("DescendantFonts"))
        return (
            dico(self._resoudre(descendantes[0]))
            if isinstance(descendantes, list) and descendantes
            else None
        ) or {}

    def _composite(self, lu: dict[str, Objet], prefixe: str, nom_: str) -> Police:
        """Police Type0 (§9.7) : sa descendante, ses largeurs ``/W`` et ``/DW``."""
        encodage = nom(self._resoudre(lu.get("Encoding")))
        descendante = self._descendante(lu)
        descripteur = dico(self._resoudre(descendante.get("FontDescriptor"))) or {}
        incorporation = next((c for c in _INCORPORATIONS if c in descripteur), "")
        montee, descente = self._hauteurs(descripteur)
        defaut = reel(self._resoudre(descendante.get("DW", 1000)))
        largeurs: dict[int, float] = {}
        plages: list[tuple[int, int, float]] = []
        lues = self._largeurs_w(self._resoudre(descendante.get("W")), largeurs, plages)
        octets = 2 if encodage == "Identity-H" and lues else 0
        return Police(
            nom_,
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
        if not isinstance(w, list) or len(w) > ELEMENTS_MAX:
            return False
        self._contexte.compter_objets(len(w))
        rang = 0
        while rang < len(w):
            premier = entier(w[rang])
            suivant = self._resoudre(w[rang + 1]) if rang + 1 < len(w) else None
            if premier is None:
                return False
            if isinstance(suivant, list):
                if len(largeurs) + len(suivant) > ELEMENTS_MAX:
                    return False
                self._contexte.compter_objets(len(suivant))
                for decalage, largeur in enumerate(suivant):
                    if (valeur := reel(largeur)) is not None:
                        largeurs[premier + decalage] = valeur / 1000
                rang += 2
                continue
            dernier = entier(suivant)
            largeur = reel(w[rang + 2]) if rang + 2 < len(w) else None
            if dernier is None or largeur is None:
                return False
            plages.append((premier, dernier, largeur / 1000))
            rang += 3
        return True

    def _type3(self, lu: dict[str, Objet]) -> Police:
        """Police Type3 (§9.6.4) : largeurs dans l'espace des glyphes, par ``/FontMatrix``."""
        m = matrice(self._resoudre(lu.get("FontMatrix")))
        largeurs = self._resoudre(lu.get("Widths"))
        premier = entier(self._resoudre(lu.get("FirstChar")))
        boite = self._resoudre(lu.get("FontBBox"))
        if (
            m is None
            or not isinstance(largeurs, list)
            or premier is None
            or len(largeurs) > ELEMENTS_MAX
        ):
            return Police("", "", "Type3", 1, {}, (), None, None, None, 0.8, -0.2)
        self._contexte.compter_objets(len(largeurs))
        lues = {}
        for rang, largeur in enumerate(largeurs):
            valeur = reel(self._resoudre(largeur))
            if valeur is not None:
                lues[premier + rang] = valeur * m[0]
        montee, descente = 0.8, -0.2
        cotes = reels(boite, 4) if isinstance(boite, list) and len(boite) == 4 else None
        if cotes is not None and cotes[3] * m[3] > cotes[1] * m[3]:
            montee, descente = cotes[3] * m[3], min(cotes[1] * m[3], 0.0)
        return Police("", "", "Type3", 1, lues, (), 0.0, None, None, montee, descente)

    # Texte des codes (§9.10 ; complément de T53, ADR-0246)

    def correspondance(self, designee: Objet) -> Correspondance:
        """Texte des codes de la police ``designee``, lu une fois."""
        cle: object = designee if isinstance(designee, Ref) else id(designee)
        if cle not in self._correspondances:
            lu = dico(self._resoudre(designee))
            self._correspondances[cle] = AUCUNE if lu is None else self._correspondre(lu)
        return self._correspondances[cle]

    def _correspondre(self, lu: dict[str, Objet]) -> Correspondance:
        espaces: list[tuple[bytes, bytes]] = []
        table: dict[tuple[int, int], str] = {}
        plages: list[tuple[int, int, int, bytes | list[str]]] = []
        cmap = self._resoudre(lu.get("ToUnicode"))
        if isinstance(cmap, Flux):
            try:
                self._cmap(cmap, espaces, table, plages)
            except Illisible as illisible:
                self.illisible = self.illisible or illisible
                espaces, table, plages = [], {}, []
        sous_type = nom(self._resoudre(lu.get("Subtype")))
        if sous_type == "Type0":
            encodage = self._resoudre(lu.get("Encoding"))
            pas = 2 if nom(encodage) in ("Identity-H", "Identity-V") else 0
            if isinstance(encodage, Flux):
                propres: list[tuple[bytes, bytes]] = []
                try:
                    self._cmap(encodage, propres, {}, [])
                except Illisible as illisible:
                    self.illisible = self.illisible or illisible
                espaces = propres or espaces
            if not pas and not espaces:
                pas = 2
            return Correspondance(pas, tuple(espaces), table, _triees(plages), (), False)
        base = nom(self._resoudre(lu.get("BaseFont"))) or ""
        prefixe, nom_ = sous_ensemble(base)
        noms = self._noms(lu, sous_type, nom_, bool(prefixe))
        return Correspondance(1, (), table, _triees(plages), tuple(noms), nom_ == "ZapfDingbats")

    def _noms(
        self, lu: dict[str, Objet], sous_type: str | None, nom_: str, prefixe: bool
    ) -> list[str]:
        """Noms des glyphes des codes 0 à 255 d'une police simple, pour son texte (§9.6.5) :
        encodage de base nommé, sinon celui qu'impose la police, puis ``/Differences``."""
        encodage = self._resoudre(lu.get("Encoding"))
        base = differences = None
        if isinstance(encodage, Nom):
            base = str(encodage)
        elif isinstance(encodage, dict):
            base = nom(self._resoudre(encodage.get("BaseEncoding")))
            differences = self._resoudre(encodage.get("Differences"))
        if base not in _BASES:
            base = self._base_implicite(lu, sous_type, nom_, prefixe)
        noms = ["" if n == "." else n for n in _ENCODAGES[base]] if base else [""] * 256
        self._differences(differences, noms)
        return noms

    def _base_implicite(
        self, lu: dict[str, Objet], sous_type: str | None, nom_: str, prefixe: bool
    ) -> str | None:
        """Encodage d'une police sans encodage de base connu (§9.6.5) : celui de Symbol ou de
        ZapfDingbats, StandardEncoding pour une police non incorporée ou que son descripteur dit
        non symbolique ; aucun pour une police Type3 ou un programme incorporé symbolique, dont
        l'encodage propre n'est pas lu."""
        if nom_ in ("Symbol", "ZapfDingbats") and not prefixe:
            return nom_
        if sous_type == "Type3":
            return None
        descripteur = dico(self._resoudre(lu.get("FontDescriptor"))) or {}
        incorporee = any(c in descripteur for c in _INCORPORATIONS)
        drapeaux = entier(self._resoudre(descripteur.get("Flags"))) or 0
        symbolique = bool(drapeaux & 1 << 2) or not drapeaux & 1 << 5
        return None if incorporee and symbolique else "StandardEncoding"

    def _cmap(
        self,
        flux: Flux,
        espaces: list[tuple[bytes, bytes]],
        table: dict[tuple[int, int], str],
        plages: list[tuple[int, int, int, bytes | list[str]]],
    ) -> None:
        """Lit un CMap (§9.7.5, §9.10.3) : plages de codes, ``bfchar``, ``bfrange``."""
        donnees = self._document.decoder(flux)
        for operateur, operandes in operations(self._contexte, donnees, flux.debut):
            if operateur == "endcodespacerange":
                for bas, haut in zip(operandes[::2], operandes[1::2], strict=False):
                    if (
                        isinstance(bas, bytes)
                        and isinstance(haut, bytes)
                        and 1 <= len(bas) == len(haut) <= 4
                        and len(espaces) < ELEMENTS_MAX
                    ):
                        espaces.append((bas, haut))
            elif operateur == "endbfchar":
                for source, cible in zip(operandes[::2], operandes[1::2], strict=False):
                    if isinstance(source, bytes) and 1 <= len(source) <= 4:
                        texte = self._cible(cible)
                        if texte is not None:
                            table[len(source), int.from_bytes(source)] = texte
            elif operateur == "endbfrange":
                for rang in range(0, len(operandes) - 2, 3):
                    self._plage(operandes[rang : rang + 3], plages)

    def _cible(self, cible: Objet) -> str | None:
        """Texte d'une destination de ``bfchar`` : UTF-16BE, ou nom de glyphe (§9.10.3)."""
        if isinstance(cible, bytes):
            return _utf16(cible)
        if isinstance(cible, Nom):
            return texte_du_glyphe(str(cible)) or ""
        return None

    def _plage(
        self, operandes: list[Objet], plages: list[tuple[int, int, int, bytes | list[str]]]
    ) -> None:
        bas, haut, cible = operandes
        if (
            not isinstance(bas, bytes)
            or not isinstance(haut, bytes)
            or not 1 <= len(bas) == len(haut) <= 4
            or len(plages) >= ELEMENTS_MAX
        ):
            return
        debut, fin = int.from_bytes(bas), int.from_bytes(haut)
        if debut > fin:
            return
        if isinstance(cible, bytes) and cible:
            plages.append((len(bas), debut, fin, cible))
        elif isinstance(cible, list) and len(cible) <= ELEMENTS_MAX:
            textes = [self._cible(element) for element in cible]
            plages.append((len(bas), debut, fin, [t or "" for t in textes]))
