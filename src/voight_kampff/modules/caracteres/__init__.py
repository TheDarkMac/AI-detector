"""Module ``caracteres`` : caractères invisibles ou substitués d'un texte (F-73 ; T80, ADR-0232 à
ADR-0236 ; fiche ``caracteres-invisibles``).

Le module lit un texte brut, enregistré dans un fichier ou collé (ADR-0233), et relève, d'après
les tables Unicode 18.0 du projet (``_unicode.py``, ADR-0234) :

- les **caractères invisibles**, par famille : contrôles, marques et forçages bidirectionnels,
  étiquettes, sélecteurs de variante, caractères sans chasse (largeur nulle, remplisseurs,
  ignorables par défaut), espaces et séparateurs inhabituels, usage privé. Chaque caractère est
  **ordinaire** quand son usage se reconnaît à ses voisins (émoji, drapeau, persan ou indien,
  espace insécable du français, marque d'ordre en tête, marque de direction dans une ligne
  écrite de droite à gauche), **inhabituel** sinon ; seuls les inhabituels font un constat. Le
  texte qu'écrivent des étiquettes hors d'un drapeau est décodé, et observé masqué par défaut
  (catégorie ``contenu``) ;
- les **homoglyphes** (UTS #39, ADR-0235) : un mot dont l'écriture dominante est mêlée de
  lettres d'une autre écriture qui se confondent avec des lettres de celle-ci (un a
  cyrillique, U+0430, dans un mot latin) ; et les **lettres de compatibilité** (variantes de police
  mathématiques, pleine chasse hors d'une ligne de chinois, de japonais ou de coréen) ;
- le **manifeste C2PA écrit dans le texte** (C2PA 2.3, annexe A.7, ADR-0236) : enveloppe
  ``C2PATXT`` en sélecteurs de variante après U+FEFF, décrite (version, longueur, boîte JUMBF),
  jamais vérifiée : c2pa-python ne lit pas le texte brut.

Le texte est lu par blocs et analysé par segments qui finissent à un saut de ligne : un fichier
de 1 Gio tient dans la mémoire du processus de travail. Les positions sont données en octets dans
le fichier et en ligne et colonne (points de code, à partir de 1). Le module n'émet aucun constat
: les règles du catalogue lisent ses observations, toutes en information neutre (A-43).
"""

import bisect
import codecs
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules.caracteres import _unicode
from voight_kampff.rapport.modele import CategorieIdentifiante, Localisation, Plage, RaisonNonMenee

__all__ = [
    "BLOC",
    "CODES_MAX",
    "FAMILLES",
    "MAGIQUE",
    "POSITIONS_MAX",
    "REPORT_MAX",
    "TEXTE_CACHE_MAX",
    "analyser",
]

BLOC = 1 << 20
"""Octets lus à la fois."""
REPORT_MAX = 8 << 20
"""Points de code gardés sans saut de ligne ni espace avant de couper le segment de force."""
POSITIONS_MAX = 8
"""Positions observées au plus par famille, pour les homoglyphes et pour les manifestes."""
CODES_MAX = 64
"""Caractères distincts au plus cités par famille ; ``…`` dit qu'il y en a d'autres."""
TEXTE_CACHE_MAX = 1024
"""Caractères au plus du texte écrit par des étiquettes."""
_POINTS_PAR_POSITION = 16

FAMILLES = (
    "controles",
    "bidirectionnels",
    "etiquettes",
    "selecteurs",
    "sans_chasse",
    "espaces",
    "prive",
)
"""Familles des caractères invisibles, dans l'ordre des observations (ADR-0234)."""

MAGIQUE = b"C2PATXT\x00"
"""En-tête de l'enveloppe d'un manifeste C2PA dans un texte (C2PA 2.3, A.7.2)."""
_ENTETE = len(MAGIQUE) + 1 + 4
_VERSION_ENVELOPPE = 1

# Décodeurs et encodeurs cherchés dès l'import : après les restrictions, la recherche d'un codec
# ne peut plus charger son module depuis le disque (ADR-0079, ERR-0009).
_CODECS = {
    nom: (codecs.getincrementaldecoder(nom), codecs.getencoder(nom))
    for nom in ("utf-8", "utf-16-le", "utf-16-be")
}
_ENCODAGES = {"utf-8": "UTF-8", "utf-16-le": "UTF-16LE", "utf-16-be": "UTF-16BE"}


# Tables (ADR-0234, ADR-0235)


def _classe(plages: Iterable[tuple[int, int]]) -> str:
    """Classe d'expression régulière qui couvre ces plages."""
    morceaux = []
    for debut, fin in plages:
        morceaux.append(re.escape(chr(debut)))
        if fin > debut:
            morceaux.append("-" + re.escape(chr(fin)))
    return "[" + "".join(morceaux) + "]"


_DEBUTS_FAMILLES = [debut for debut, _fin, _famille in _unicode.FAMILLES]
_DEBUTS_ECRITURES = [debut for debut, _fin, _indice in _unicode.PLAGES_ECRITURES]
_INCONNUE = _unicode.ECRITURES.index("Unknown")
_INDICES = {nom: rang for rang, nom in enumerate(_unicode.ECRITURES)}
_NEUTRES = frozenset(_INDICES[nom] for nom in ("Common", "Inherited", "Unknown"))
_HERITEE = _INDICES["Inherited"]
_HAN = _INDICES["Han"]
_AUGMENTEES = tuple(
    frozenset(_INDICES[nom] for nom in noms)
    for noms in (("Han", "Hiragana", "Katakana"), ("Han", "Hangul"), ("Han", "Bopomofo"))
)
"""Écritures qui s'emploient ensemble dans un mot : japonais, coréen, chinois avec bopomofo
(UTS #39, §5.1, ensembles augmentés)."""
_SANS_JOINTURE = frozenset(
    _INDICES[nom] for nom in ("Latin", "Greek", "Cyrillic", "Common", "Inherited", "Unknown")
)
"""Écritures où ZWJ et ZWNJ n'ont pas d'emploi ordinaire entre deux lettres."""
_DROITE_A_GAUCHE = (
    "Arabic",
    "Hebrew",
    "Syriac",
    "Thaana",
    "Nko",
    "Samaritan",
    "Mandaic",
    "Adlam",
    "Hanifi_Rohingya",
    "Yezidi",
    "Mende_Kikakui",
    "Old_South_Arabian",
    "Old_North_Arabian",
    "Imperial_Aramaic",
    "Nabataean",
    "Palmyrene",
    "Phoenician",
    "Avestan",
    "Kharoshthi",
    "Manichaean",
    "Psalter_Pahlavi",
    "Inscriptional_Pahlavi",
    "Inscriptional_Parthian",
    "Hatran",
    "Old_Sogdian",
    "Sogdian",
    "Chorasmian",
    "Elymaic",
    "Garay",
)
"""Écritures de droite à gauche : une marque de direction y est ordinaire (ADR-0234)."""
_ASIE_EST = ("Han", "Hiragana", "Katakana", "Hangul", "Bopomofo")
"""Écritures où les lettres pleine chasse sont ordinaires."""


def _plages_de(noms: Iterable[str]) -> list[tuple[int, int]]:
    indices = {_INDICES[nom] for nom in noms if nom in _INDICES}
    return [(d, f) for d, f, i in _unicode.PLAGES_ECRITURES if i in indices]


def _sans(debut: int, fin: int, exclus: str) -> list[tuple[int, int]]:
    """La plage, sans les caractères exclus."""
    morceaux, courant = [], debut
    for point in sorted(ord(c) for c in exclus if debut <= ord(c) <= fin):
        if courant < point:
            morceaux.append((courant, point - 1))
        courant = point + 1
    if courant <= fin:
        morceaux.append((courant, fin))
    return morceaux


_ESPACES_ORDINAIRES = "\u00a0\u2007\u2009\u202f\u3000"
"""Insécable, espace de chiffre, fine, insécable étroite, idéographique : toujours ordinaires
(ADR-0234). Comptées par ``str.count``, hors de l'expression des invisibles : un texte français
en a une dans presque chaque phrase."""
_PLAGES_INVISIBLES = [
    (d, f) for d, f, _famille in _unicode.FAMILLES for d, f in _sans(d, f, _ESPACES_ORDINAIRES)
]


def _motifs(plages: list[tuple[int, int]]) -> tuple[re.Pattern[str], re.Pattern[str]]:
    """Expression de ces plages, et la même limitée au plan de base : sans caractère astral, la
    classe se lit par une table de bits, bien plus vite qu'une liste de plages (mesure de T80)."""
    plan_de_base = [(d, min(f, 0xFFFF)) for d, f in plages if d <= 0xFFFF]
    return re.compile(_classe(plages) + "+"), re.compile(_classe(plan_de_base) + "+")


_INVISIBLES, _INVISIBLES_BMP = _motifs(_PLAGES_INVISIBLES)
_TRANSPARENTS = frozenset(
    point
    for d, f, famille in _unicode.FAMILLES
    if famille in {"sans_chasse", "selecteurs"}
    for point in range(d, f + 1)
)
"""Invisibles qui ne coupent pas un mot : un ZWSP glissé dans un mot le laisse entier."""
_BASE = 0xE000
"""Code de l'écriture d'indice ``i`` dans la traduction d'un segment : ``_BASE + i``."""
_DANS_LE_MOT = _BASE + 0x100
"""Code des caractères qui ne coupent pas un mot sans avoir d'écriture : marques Inherited,
invisibles transparents."""
_COUPURE = _BASE + 0x101
"""Code des caractères qui coupent un mot : Common, Unknown, autres invisibles."""
_MOTS = re.compile(f"[{chr(_BASE)}-{chr(_DANS_LE_MOT)}]+")
"""Mots, cherchés dans la traduction d'un segment (:class:`_Traduction`)."""


class _Traduction(dict[int, int]):
    """Table de ``str.translate`` : chaque caractère vers le code de son écriture, calculé à sa
    première rencontre (un texte n'emploie que quelques centaines de caractères distincts)."""

    def __missing__(self, point: int) -> int:
        indice = _ecriture(chr(point))
        if point in _TRANSPARENTS or indice == _HERITEE:
            code = _DANS_LE_MOT
        elif indice in _NEUTRES:
            code = _COUPURE
        else:
            code = _BASE + indice
        self[point] = code
        return code


_DROITE = re.compile(_classe(_plages_de(_DROITE_A_GAUCHE)))
_EST = re.compile(_classe(_plages_de(_ASIE_EST)))
_COMPATIBLES, _COMPATIBLES_BMP = _motifs([(d, f) for d, f, _nature in _unicode.COMPATIBILITE])
_DEBUTS_COMPATIBLES = [debut for debut, _fin, _nature in _unicode.COMPATIBILITE]
_ENSEMBLES = tuple(frozenset(map(int, ensemble.split())) for ensemble in _unicode.ENSEMBLES)
_CONFUSABLES: dict[int, frozenset[int]] = {
    point: _ENSEMBLES[rang]
    for debut, fin, rang in _unicode.CONFUSABLES
    for point in range(debut, fin + 1)
}


def _dans(plages: tuple[tuple[int, int, int], ...]) -> Callable[[str], bool]:
    debuts = [debut for debut, _fin, _valeur in plages]

    def contient(caractere: str) -> bool:
        point = ord(caractere)
        rang = bisect.bisect_right(debuts, point) - 1
        return rang >= 0 and plages[rang][0] <= point <= plages[rang][1]

    return contient


_pictogramme = _dans(_unicode.PICTOGRAMMES)
_modificateur = _dans(_unicode.MODIFICATEURS)
_ECRITURE_DE: dict[str, int] = {}
"""Écriture de chaque caractère déjà vu : un texte n'emploie que quelques centaines de
caractères distincts."""


def _ecriture(caractere: str) -> int:
    indice = _ECRITURE_DE.get(caractere)
    if indice is None:
        point = ord(caractere)
        # La première plage commence à U+0000 : le rang n'est jamais négatif.
        debut, fin, trouve = _unicode.PLAGES_ECRITURES[
            bisect.bisect_right(_DEBUTS_ECRITURES, point) - 1
        ]
        indice = trouve if debut <= point <= fin else _INCONNUE
        _ECRITURE_DE[caractere] = indice
    return indice


def _famille(caractere: str) -> str:
    point = ord(caractere)
    rang = bisect.bisect_right(_DEBUTS_FAMILLES, point) - 1
    debut, fin, famille = _unicode.FAMILLES[rang]
    if not debut <= point <= fin:  # pragma: no cover - l'expression ne trouve que des invisibles
        raise ValueError("caractère hors des familles")
    return famille


def _nature(caractere: str) -> str:
    point = ord(caractere)
    return _unicode.COMPATIBILITE[bisect.bisect_right(_DEBUTS_COMPATIBLES, point) - 1][2]


def _code(caractere: str) -> str:
    return f"U+{ord(caractere):04X}"


def _selecteur(caractere: str) -> bool:
    point = ord(caractere)
    return 0xFE00 <= point <= 0xFE0F or 0xE0100 <= point <= 0xE01EF


def _octet_de_selecteur(caractere: str) -> int:
    """Octet qu'écrit un sélecteur de variante (C2PA 2.3, A.7.3.2)."""
    point = ord(caractere)
    return point - 0xFE00 if point <= 0xFE0F else point - 0xE0100 + 16


def _lettre(caractere: str) -> bool:
    return _ecriture(caractere) not in _NEUTRES or _ecriture(caractere) == _HERITEE


# Relevés


@dataclass(slots=True)
class _Position:
    """Position demandée dans un segment, résolue à sa fin (:meth:`_Curseur.resoudre`)."""

    debut: int
    fin: int
    """Indices des caractères dans le segment, ``fin`` exclu."""
    valeur: str
    localisation: Localisation | None = None


@dataclass(slots=True)
class _Releve:
    """Relevé d'une famille : total, inhabituels, caractères cités, premières positions."""

    total: int = 0
    inhabituels: int = 0
    codes: Counter[str] = field(default_factory=Counter)
    positions: list[_Position] = field(default_factory=list)

    def citer(self) -> list[str]:
        cites = [f"{code} ({nombre})" for code, nombre in sorted(self.codes.items())]
        return cites[:CODES_MAX] + (["…"] if len(cites) > CODES_MAX else [])


@dataclass(slots=True)
class _Enveloppe:
    """Enveloppe C2PATXT trouvée dans le texte."""

    complete: bool
    version: int
    octets: int
    """Longueur déclarée du manifeste, en octets (``manifestLength``)."""
    position: _Position


@dataclass(slots=True)
class _Curseur:
    """Position du début du segment courant : octet dans la partie, ligne, début de ligne."""

    encoder: Callable[[str], tuple[bytes, int]]
    octet: int = 0
    ligne: int = 1
    debut_ligne: int = 0
    """Indice, dans le segment, du premier caractère de la ligne courante ; négatif si elle a
    commencé dans un segment précédent."""

    def resoudre(self, segment: str, positions: list[_Position]) -> None:
        """Localise les positions demandées, en une passe sur le segment, puis passe à la fin."""
        indices = sorted({p.debut for p in positions} | {p.fin for p in positions})
        reperes: dict[int, tuple[int, int, int]] = {}
        precedent = 0
        for indice in (*indices, len(segment)):
            morceau = segment[precedent:indice]
            self.octet += len(self.encoder(morceau)[0])
            sauts = morceau.count("\n")
            if sauts:
                self.ligne += sauts
                self.debut_ligne = precedent + morceau.rindex("\n") + 1
            reperes[indice] = (self.octet, self.ligne, indice - self.debut_ligne + 1)
            precedent = indice
        for position in positions:
            octet, ligne, colonne = reperes[position.debut]
            longueur = reperes[position.fin][0] - octet
            position.localisation = Localisation(
                chemin=f"ligne {ligne}, colonne {colonne}", octets=Plage(octet, max(longueur, 1))
            )
        self.debut_ligne -= len(segment)


_TRADUCTION = _Traduction()


_LIGNES = re.compile("[^\n]+")
_SANS_ECRITURE = str.maketrans("", "", chr(_DANS_LE_MOT) + chr(_COUPURE))


def _plusieurs_ecritures(codes: str) -> bool:
    """Vrai si ces codes nomment au moins deux écritures."""
    ecritures = codes.translate(_SANS_ECRITURE)
    return bool(ecritures) and min(ecritures) != max(ecritures)


def _mots_meles(texte: str) -> list[tuple[int, int]]:
    """Débuts et fins des mots qui ont au moins deux écritures, d'après la traduction du segment
    en codes d'écriture. Un mot ne peut en mêler deux que si sa ligne en a deux, et sa ligne
    que si le segment en a deux : un texte d'une seule écriture n'est pas parcouru mot à mot."""
    codes = texte.translate(_TRADUCTION)
    if not _plusieurs_ecritures(codes):
        return []
    meles = []
    for ligne in _LIGNES.finditer(texte):
        debut_ligne, fin_ligne = ligne.span()
        if not _plusieurs_ecritures(codes[debut_ligne:fin_ligne]):
            continue
        for trouve in _MOTS.finditer(codes, debut_ligne, fin_ligne):
            debut, fin = trouve.span()
            if _plusieurs_ecritures(codes[debut:fin]):
                meles.append((debut, fin))
    return meles


class _Analyse:
    """Analyse d'un texte, segment par segment."""

    def __init__(self, encoder: Callable[[str], tuple[bytes, int]]) -> None:
        self.curseur = _Curseur(encoder)
        self.familles = {famille: _Releve() for famille in FAMILLES}
        self.cache: list[str] = []
        self.homoglyphes = _Releve()
        self.lettres = 0
        self.compatibles = _Releve()
        self.enveloppes: list[_Enveloppe] = []
        self.longueur = 0
        self.premier = True
        self.demandes: list[_Position] = []
        """Positions demandées dans le segment courant."""

    def _demander(self, debut: int, fin: int, valeur: str) -> _Position:
        position = _Position(debut, fin, valeur)
        self.demandes.append(position)
        return position

    # Segment

    def segment(self, texte: str) -> None:
        """Analyse un segment : invisibles, mots mêlés, lettres de compatibilité, par ordre de
        position ; les positions demandées sont localisées à la fin, en une passe."""
        astral = bool(texte) and max(texte) > "\uffff"
        invisibles = _INVISIBLES if astral else _INVISIBLES_BMP
        evenements: list[tuple[int, int, Callable[[str, int, int], None]]] = [
            (m.start(), m.end(), self._invisibles) for m in invisibles.finditer(texte)
        ]
        self.familles["espaces"].total += sum(texte.count(c) for c in _ESPACES_ORDINAIRES)
        if not texte.isascii():
            compatibles = _COMPATIBLES if astral else _COMPATIBLES_BMP
            evenements += [(debut, fin, self._mot) for debut, fin in _mots_meles(texte)]
            evenements += [
                (m.start(), m.end(), self._compatible) for m in compatibles.finditer(texte)
            ]
        evenements.sort(key=lambda evenement: (evenement[0], evenement[1]))
        for debut, fin, traiter in evenements:
            traiter(texte, debut, fin)
        self.curseur.resoudre(texte, self.demandes)
        self.demandes = []
        self.longueur += len(texte)
        self.premier = False

    # Invisibles (ADR-0234)

    def _invisibles(self, texte: str, debut: int, fin: int) -> None:
        exclus = self._c2pa(texte, debut, fin)
        par_famille: dict[str, list[int]] = {}
        for indice in range(debut, fin):
            if indice in exclus:
                continue
            caractere = texte[indice]
            famille = _famille(caractere)
            releve = self.familles[famille]
            releve.total += 1
            if self._ordinaire(famille, texte, indice, debut, fin):
                continue
            releve.inhabituels += 1
            releve.codes[_code(caractere)] += 1
            par_famille.setdefault(famille, []).append(indice)
        for famille, indices in par_famille.items():
            releve = self.familles[famille]
            if famille == "etiquettes":
                self._etiquettes(texte, indices)
            if len(releve.positions) < POSITIONS_MAX:
                points = self._points(texte, indices)
                releve.positions.append(self._demander(indices[0], indices[-1] + 1, points))

    @staticmethod
    def _points(texte: str, indices: list[int]) -> str:
        codes = [_code(texte[i]) for i in indices[:_POINTS_PAR_POSITION]]
        return " ".join(codes) + (" …" if len(indices) > _POINTS_PAR_POSITION else "")

    def _ordinaire(self, famille: str, texte: str, indice: int, debut: int, fin: int) -> bool:
        """Usage qui se reconnaît aux voisins du caractère (ADR-0234)."""
        caractere = texte[indice]
        point = ord(caractere)
        avant = texte[indice - 1] if indice > 0 else ""
        apres = texte[indice + 1] if indice + 1 < len(texte) else ""
        seul = fin - debut == 1
        match famille:
            case "espaces":  # les espaces ordinaires sont comptées à part
                return False
            case "bidirectionnels":
                return point in {0x061C, 0x200E, 0x200F} and bool(
                    _DROITE.search(self._ligne(texte, indice))
                )
            case "etiquettes":
                return self._drapeau(texte, debut, fin)
            case "selecteurs":
                # Un seul sélecteur, juste après un caractère visible : émoji, variante
                # normalisée, variante idéographique, sélecteur mongol.
                return (
                    indice == debut
                    and bool(avant)
                    and not avant.isspace()
                    and (indice + 1 == fin or not _selecteur(texte[indice + 1]))
                )
            case "sans_chasse":
                return self._sans_chasse_ordinaire(texte, indice, avant, apres, seul)
            case _:  # contrôles, usage privé
                return False

    def _sans_chasse_ordinaire(
        self, texte: str, indice: int, avant: str, apres: str, seul: bool
    ) -> bool:
        point = ord(texte[indice])
        if point == 0xFEFF:
            return indice == 0 and self.premier  # marque d'ordre en tête du texte
        if point == 0x200D and self._emoji_avant(texte, indice) and apres and _pictogramme(apres):
            return True
        if not seul:
            return False
        ecriture_avant = _ecriture(avant) if avant else _INCONNUE
        ecriture_apres = _ecriture(apres) if apres else _INCONNUE
        voisines = {
            0x115F: "Hangul",
            0x1160: "Hangul",
            0x17B4: "Khmer",
            0x17B5: "Khmer",
            0x180E: "Mongolian",
        }
        attendue = voisines.get(point)
        if attendue is not None:  # remplisseurs, voyelles inhérentes : à côté de leur écriture
            return _INDICES[attendue] in {ecriture_avant, ecriture_apres}
        if not (avant and apres):
            return False
        if point in {0x200C, 0x200D}:
            return ecriture_avant == ecriture_apres and ecriture_avant not in _SANS_JOINTURE
        if point in {0x00AD, 0x034F}:  # césure conditionnelle, liant de graphèmes : dans un mot
            return _lettre(avant) and _lettre(apres)
        return False

    @staticmethod
    def _emoji_avant(texte: str, indice: int) -> bool:
        """Un pictogramme d'émoji avant ce ZWJ, au-delà de son sélecteur et de sa teinte."""
        rang = indice - 1
        while rang >= 0 and (texte[rang] in "\ufe0e\ufe0f" or _modificateur(texte[rang])):
            if _modificateur(texte[rang]):
                return True
            rang -= 1
        return rang >= 0 and _pictogramme(texte[rang])

    @staticmethod
    def _drapeau(texte: str, debut: int, fin: int) -> bool:
        """Drapeau de subdivision : U+1F3F4, étiquettes, étiquette de fin (UTS #51, §2.8)."""
        return (
            debut > 0
            and texte[debut - 1] == "\U0001f3f4"
            and fin - debut >= 2
            and texte[fin - 1] == "\U000e007f"
            and all(0xE0020 <= ord(c) <= 0xE007E for c in texte[debut : fin - 1])
        )

    @staticmethod
    def _ligne(texte: str, indice: int) -> str:
        debut = texte.rfind("\n", 0, indice) + 1
        fin = texte.find("\n", indice)
        return texte[debut : None if fin < 0 else fin]

    def _etiquettes(self, texte: str, indices: list[int]) -> None:
        """Texte écrit par des étiquettes : U+E0020 à U+E007E portent les caractères ASCII."""
        place = TEXTE_CACHE_MAX - sum(len(morceau) for morceau in self.cache)
        morceau = "".join(
            chr(ord(texte[i]) - 0xE0000) for i in indices if 0xE0020 <= ord(texte[i]) <= 0xE007E
        )
        if morceau and place > 0:
            self.cache.append(morceau[:place])

    # Manifeste C2PA (ADR-0236)

    def _c2pa(self, texte: str, debut: int, fin: int) -> set[int]:
        """Indices des enveloppes C2PATXT de ce groupe d'invisibles (C2PA 2.3, A.7.4.2)."""
        exclus: set[int] = set()
        indice = debut
        while indice < fin:
            if texte[indice] != "\ufeff":
                indice += 1
                continue
            suite = indice + 1
            while suite < fin and _selecteur(texte[suite]):
                suite += 1
            octets = bytes(_octet_de_selecteur(c) for c in texte[indice + 1 : suite])
            if octets[: len(MAGIQUE)] == MAGIQUE:
                exclus.update(range(indice, suite))
                self._enveloppe(texte, indice, suite, octets)
                indice = suite
            else:
                indice += 1
        return exclus

    def _enveloppe(self, texte: str, debut: int, fin: int, octets: bytes) -> None:
        version = octets[len(MAGIQUE)] if len(octets) > len(MAGIQUE) else 0
        longueur = (
            int.from_bytes(octets[len(MAGIQUE) + 1 : _ENTETE]) if len(octets) >= _ENTETE else 0
        )
        jumbf = octets[_ENTETE:]
        complete = (
            version == _VERSION_ENVELOPPE
            and len(octets) >= _ENTETE
            and len(jumbf) == longueur
            and _jumbf_c2pa(jumbf)
        )
        position = self._demander(debut, fin, "complète" if complete else "corrompue")
        self.enveloppes.append(_Enveloppe(complete, version, longueur, position))

    # Homoglyphes (ADR-0235)

    def _mot(self, texte: str, debut: int, fin: int) -> None:
        mot = texte[debut:fin]
        ecritures: Counter[int] = Counter()
        for caractere in mot:
            indice = _ecriture(caractere)
            if indice not in _NEUTRES:
                ecritures[indice] += 1
        if len(ecritures) < 2 or any(set(ecritures) <= ensemble for ensemble in _AUGMENTEES):
            return
        # Écriture dominante : la plus fréquente ; à égalité, la première dont les autres lettres
        # se confondent avec les siennes, dans l'ordre où elles apparaissent.
        plus = max(ecritures.values())
        dominante, substitues = -1, []
        for candidate in (indice for indice, nombre in ecritures.items() if nombre == plus):
            dominante, substitues = candidate, self._substitues(mot, candidate)
            if substitues:
                break
        if not substitues:
            return
        releve = self.homoglyphes
        releve.total += 1
        self.lettres += len(substitues)
        nom_dominante = _unicode.ECRITURES[dominante]
        for rang in substitues:
            caractere = mot[rang]
            nom = _unicode.ECRITURES[_ecriture(caractere)]
            releve.codes[f"{_code(caractere)} {nom} dans {nom_dominante}"] += 1
        if len(releve.positions) < POSITIONS_MAX:
            releve.positions.append(self._demander(debut, fin, self._points(mot, substitues)))

    @staticmethod
    def _substitues(mot: str, dominante: int) -> list[int]:
        """Rangs des lettres d'une autre écriture qui se confondent avec une de la dominante."""
        return [
            rang
            for rang, caractere in enumerate(mot)
            if _ecriture(caractere) not in _NEUTRES
            and _ecriture(caractere) != dominante
            and dominante in _CONFUSABLES.get(ord(caractere), frozenset())
        ]

    def _compatible(self, texte: str, debut: int, fin: int) -> None:
        releve = self.compatibles
        releve.total += fin - debut
        if _EST.search(self._ligne(texte, debut)):
            # Pleine chasse dans une ligne de chinois, de japonais ou de coréen : ordinaire.
            inhabituels = [i for i in range(debut, fin) if _nature(texte[i]) != "pleine_chasse"]
        else:
            inhabituels = list(range(debut, fin))
        if not inhabituels:
            return
        releve.inhabituels += len(inhabituels)
        for indice in inhabituels:
            releve.codes[_nature(texte[indice])] += 1
        if len(releve.positions) < POSITIONS_MAX:
            points = self._points(texte, inhabituels)
            releve.positions.append(self._demander(inhabituels[0], inhabituels[-1] + 1, points))


def _jumbf_c2pa(jumbf: bytes) -> bool:
    """Boîte JUMBF du magasin de manifestes C2PA : superboîte ``jumb`` de la longueur annoncée,
    description ``jumd`` d'étiquette ``c2pa`` (ISO/IEC 19566-5 ; C2PA 2.3, §11.1.4.2)."""
    if len(jumbf) < 8 + 8 + 16 + 1 or jumbf[4:8] != b"jumb":
        return False
    if int.from_bytes(jumbf[:4]) != len(jumbf) or jumbf[12:16] != b"jumd":
        return False
    description = int.from_bytes(jumbf[8:12])
    if not 8 + 17 <= description <= len(jumbf) - 8:
        return False
    bascules = jumbf[32]
    if not bascules & 0x02:  # pas d'étiquette
        return False
    etiquette = jumbf[33 : 8 + description].split(b"\x00", 1)[0]
    return etiquette == b"c2pa"


# Lecture


def _encodage(debut: bytes) -> str:
    """UTF-16 avec sa marque, sinon UTF-8 : ce que l'identification accepte (ADR-0070)."""
    if debut == codecs.BOM_UTF16_LE:
        return "utf-16-le"
    if debut == codecs.BOM_UTF16_BE:
        return "utf-16-be"
    return "utf-8"


def _coupure(texte: str) -> int:
    """Fin du segment à analyser : après le dernier saut de ligne, ou la dernière espace ; 0 si
    le texte n'en a pas."""
    return max(texte.rfind("\n"), texte.rfind(" ")) + 1


def analyser(contexte: Contexte) -> None:
    nom = _encodage(contexte.lire(0, 2))
    fabrique, encoder = _CODECS[nom]
    decodeur = fabrique("strict")
    analyse = _Analyse(encoder)
    report = ""
    position = 0
    while position < contexte.taille:
        bloc = contexte.lire(position, BLOC)
        try:
            report += decodeur.decode(bloc, final=position + len(bloc) >= contexte.taille)
        except UnicodeDecodeError:
            reste = Plage(position, contexte.taille - position)
            contexte.non_mener(
                RaisonNonMenee.FORMAT_PARTIEL, localisation=Localisation(octets=reste)
            )
            break
        position += len(bloc)
        coupure = _coupure(report)
        if not coupure and len(report) > REPORT_MAX:
            coupure = len(report)  # ligne sans espace trop longue : coupée de force
        if coupure:
            analyse.segment(report[:coupure])
            report = report[coupure:]
    if report:
        analyse.segment(report)
    encodage = _ENCODAGES[nom]
    if nom == "utf-8" and contexte.lire(0, 3) == codecs.BOM_UTF8:
        encodage += " avec marque d'ordre"
    contexte.observer("caracteres.encodage", encodage)
    contexte.observer("caracteres.longueur", analyse.longueur, unite="caractères")
    _observer(contexte, analyse)


def _observer_releve(contexte: Contexte, nom: str, releve: _Releve, inhabituels: bool) -> None:
    contexte.observer(nom, releve.total)
    if inhabituels:
        contexte.observer(f"{nom}.inhabituels", releve.inhabituels)
    if releve.codes:
        contexte.observer(f"{nom}.codes", releve.citer())
    for position in releve.positions:
        contexte.observer(f"{nom}.position", position.valeur, localisation=position.localisation)


def _observer(contexte: Contexte, analyse: _Analyse) -> None:
    for famille in FAMILLES:
        releve = analyse.familles[famille]
        if releve.total:
            _observer_releve(contexte, f"caracteres.{famille}", releve, inhabituels=True)
    if analyse.cache:
        contexte.observer(
            "caracteres.etiquettes.texte",
            " | ".join(analyse.cache),
            identifiante=CategorieIdentifiante.CONTENU,
        )
    if analyse.homoglyphes.total:
        _observer_releve(contexte, "caracteres.homoglyphes", analyse.homoglyphes, False)
        contexte.observer("caracteres.homoglyphes.lettres", analyse.lettres)
    if analyse.compatibles.total:
        _observer_releve(contexte, "caracteres.compatibilite", analyse.compatibles, True)
    if analyse.enveloppes:
        enveloppes = analyse.enveloppes
        completes = [enveloppe for enveloppe in enveloppes if enveloppe.complete]
        premiere = (completes or enveloppes)[0]
        contexte.observer("caracteres.c2pa", len(enveloppes))
        contexte.observer("caracteres.c2pa.completes", len(completes))
        contexte.observer("caracteres.c2pa.corrompues", len(enveloppes) - len(completes))
        contexte.observer("caracteres.c2pa.version", premiere.version)
        contexte.observer("caracteres.c2pa.octets", premiere.octets, unite="octets")
        for enveloppe in enveloppes[:POSITIONS_MAX]:
            position = enveloppe.position
            contexte.observer(
                "caracteres.c2pa.position", position.valeur, localisation=position.localisation
            )
