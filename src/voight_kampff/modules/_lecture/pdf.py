"""Structure d'un PDF : références croisées, objets et flux (ISO 32000-2, §7 ; ADR-0124).

Le document est lu par sa table des références croisées, depuis le dernier ``startxref`` :
tables classiques (§7.5.4), flux de références croisées (§7.5.8), sections antérieures par
``/Prev`` et ``/XRefStm``. Un objet est lu à la position que donne la table, ou dans son flux
d'objets (§7.5.7), seulement quand un module le demande. Rien n'est reconstruit : une table
fausse, un objet qui n'est pas où elle le dit, une longueur de flux inexacte arrêtent la
lecture, et le module le dit par une analyse non menée (ADR-0125).

Seul le filtre ``FlateDecode`` est décodé, prédicteurs PNG et TIFF compris, par
``Contexte.decompresser`` (ADR-0078). Un document chiffré est reconnu, jamais déchiffré
(ADR-0126). Rien n'est exécuté ni suivi hors du fichier : un flux dont les données sont dans
un autre fichier (``/F``) n'est pas lu.
"""

import codecs
import zlib
from collections.abc import Callable
from dataclasses import dataclass

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Contexte
from voight_kampff.rapport.modele import Localisation, Plage, RaisonNonMenee

__all__ = ["Document", "Flux", "Illisible", "Nom", "Objet", "Ref", "entier", "texte"]


class Nom(str):
    """Nom PDF (``/Producer``), sans la barre oblique ; distinct d'une chaîne, lue en octets."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Ref:
    """Référence indirecte ``n g R``."""

    numero: int
    generation: int


@dataclass(frozen=True, slots=True)
class Flux:
    """Flux : son dictionnaire et la plage de ses données dans la partie, non décodées."""

    dico: dict[str, "Objet"]
    debut: int
    longueur: int


type Objet = (
    bool | int | float | bytes | Nom | list["Objet"] | dict[str, "Objet"] | Ref | Flux | None
)
"""Objet PDF : chaîne en octets, nom en :class:`Nom`, clé de dictionnaire en texte."""


class Illisible(Exception):
    """Structure que le lecteur ne peut pas lire : la raison et la position de l'arrêt."""

    def __init__(self, raison: RaisonNonMenee, position: int, chemin: str) -> None:
        super().__init__(raison)
        self.raison = raison
        self.position = position
        self.chemin = chemin

    def localisation(self, taille: int) -> Localisation:
        """Chemin de ce qui n'a pas été lu, et l'octet où la lecture s'est arrêtée."""
        position = min(max(self.position, 0), max(taille - 1, 0))
        return Localisation(chemin=self.chemin, octets=Plage(position, 1))


def _partiel(position: int, chemin: str = "structure du PDF") -> Illisible:
    return Illisible(RaisonNonMenee.FORMAT_PARTIEL, position, chemin)


def entier(objet: Objet) -> int | None:
    """Entier, ou ``None`` pour tout autre objet (un booléen n'est pas un entier)."""
    return objet if type(objet) is int else None


# Texte (§7.9.2.2, annexe D)

# Codec chargé à l'import : après les restrictions, plus rien n'est lu sur le disque, et Python
# charge un codec à sa première utilisation (ADR-0079, ERR-0009).
codecs.lookup("utf-16-be")

_PDFDOC = {
    **dict.fromkeys((*range(0x09), 0x0B, 0x0C, *range(0x0E, 0x18), 0x7F, 0x9F, 0xAD), "\ufffd"),
    **dict(zip(range(0x18, 0x20), "\u02d8\u02c7\u02c6\u02d9\u02dd\u02db\u02da\u02dc", strict=True)),
    **dict(
        zip(
            range(0x80, 0x9F),
            "\u2022\u2020\u2021\u2026\u2014\u2013\u0192\u2044"
            "\u2039\u203a\u2212\u2030\u201e\u201c\u201d\u2018"
            "\u2019\u201a\u2122\ufb01\ufb02\u0141\u0152\u0160"
            "\u0178\u017d\u0131\u0142\u0153\u0161\u017e",
            strict=True,
        )
    ),
    0xA0: "\u20ac",
}
"""Écarts de PDFDocEncoding à Latin-1 ; un code non défini devient le caractère de remplacement."""


def texte(octets: bytes) -> str:
    """Chaîne de texte : UTF-16BE ou UTF-8 annoncés par leur marque, PDFDocEncoding sinon.

    Un octet invalide devient le caractère de remplacement : l'encodage est fixé par la norme
    (ADR-0118).
    """
    if octets.startswith(b"\xfe\xff"):
        return octets[2:].decode("utf-16-be", "replace")
    if octets.startswith(b"\xef\xbb\xbf"):
        return octets[3:].decode("utf-8", "replace")
    return "".join(_PDFDOC.get(octet, chr(octet)) for octet in octets)


# Analyse lexicale et syntaxique (§7.2, §7.3)

_BLANCS = frozenset(b"\x00\t\n\x0c\r ")
_DELIMITEURS = frozenset(b"()<>[]{}/%")
_FIN_DE_LIGNE = frozenset(b"\r\n")
_ECHAPPEMENTS = {
    ord("n"): 0x0A,
    ord("r"): 0x0D,
    ord("t"): 0x09,
    ord("b"): 0x08,
    ord("f"): 0x0C,
    ord("("): 0x28,
    ord(")"): 0x29,
    ord("\\"): 0x5C,
}
_HEXADECIMAL = frozenset(b"0123456789abcdefABCDEF")


class _Mot(bytes):
    """Mot-clé (``obj``, ``R``, ``true``…) ou délimiteur (``[``, ``<<``…)."""

    __slots__ = ()


class _Fin(Exception):
    """Fin des données atteinte au milieu d'un objet : une lecture plus large peut suffire."""


class _Analyseur:
    """Lecture des objets d'un tampon ; ``origine`` est la position du tampon dans la partie."""

    __slots__ = ("_contexte", "_d", "_origine", "complet", "position", "resoudre")

    def __init__(
        self,
        contexte: Contexte,
        donnees: bytes,
        origine: int,
        resoudre: Callable[[Objet], Objet] | None = None,
        *,
        complet: bool | None = None,
    ) -> None:
        self._contexte = contexte
        self._d = donnees
        self._origine = origine
        self.position = 0
        self.resoudre = resoudre
        """Résolution d'une longueur de flux indirecte ; ``None`` dans un flux d'objets."""
        self.complet = origine + len(donnees) >= contexte.taille if complet is None else complet
        """Vrai si rien ne suit le tampon : un mot qui finit avec lui est entier."""

    @property
    def absolue(self) -> int:
        return self._origine + self.position

    def _erreur(self) -> Illisible:
        return _partiel(self.absolue)

    def blancs(self) -> None:
        """Passe les blancs et les commentaires."""
        d, i = self._d, self.position
        while i < len(d):
            if d[i] in _BLANCS:
                i += 1
            elif d[i] == 0x25:  # commentaire, jusqu'à la fin de la ligne
                while i < len(d) and d[i] not in _FIN_DE_LIGNE:
                    i += 1
            else:
                break
        self.position = i

    def jeton(self) -> Objet | _Mot:
        self.blancs()
        d, i = self._d, self.position
        if i >= len(d):
            raise _Fin
        c = d[i]
        if c == 0x28:
            return self._chaine()
        if c == 0x2F:
            return self._nom()
        if c == 0x3C:
            if d[i + 1 : i + 2] == b"<":
                self.position = i + 2
                return _Mot(b"<<")
            return self._hexadecimale()
        if c == 0x3E:
            if d[i + 1 : i + 2] != b">":
                raise _Fin if i + 1 >= len(d) else self._erreur()
            self.position = i + 2
            return _Mot(b">>")
        if c in b"[]{}":
            self.position = i + 1
            return _Mot(bytes([c]))
        if c == 0x29:
            raise self._erreur()
        fin = i
        while fin < len(d) and d[fin] not in _BLANCS and d[fin] not in _DELIMITEURS:
            fin += 1
        if fin == len(d) and not self.complet:
            raise _Fin  # le mot peut continuer au-delà du tampon
        self.position = fin
        return _nombre(d[i:fin])

    def _chaine(self) -> bytes:
        d, i = self._d, self.position + 1
        profondeur, sortie = 1, bytearray()
        while True:
            if i >= len(d):
                raise _Fin
            c = d[i]
            if c == 0x5C:
                i += 1
                if i >= len(d):
                    raise _Fin
                c = d[i]
                if c in _ECHAPPEMENTS:
                    sortie.append(_ECHAPPEMENTS[c])
                    i += 1
                elif c == 0x0D:  # fin de ligne échappée : rien
                    i += 2 if d[i + 1 : i + 2] == b"\n" else 1
                elif c == 0x0A:
                    i += 1
                elif 0x30 <= c <= 0x37:
                    fin = i
                    while fin < min(i + 3, len(d)) and 0x30 <= d[fin] <= 0x37:
                        fin += 1
                    sortie.append(int(d[i:fin], 8) & 0xFF)
                    i = fin
                else:  # barre oblique inverse sans effet : ignorée
                    sortie.append(c)
                    i += 1
                continue
            if c == 0x29:
                profondeur -= 1
                if profondeur == 0:
                    self.position = i + 1
                    return bytes(sortie)
            elif c == 0x28:
                profondeur += 1
            elif c == 0x0D:  # CR et CR LF non échappés valent LF (§7.3.4.2)
                sortie.append(0x0A)
                i += 2 if d[i + 1 : i + 2] == b"\n" else 1
                continue
            sortie.append(c)
            i += 1

    def _hexadecimale(self) -> bytes:
        d, debut = self._d, self.position + 1
        fin = d.find(b">", debut)
        if fin == -1:
            raise _Fin
        chiffres = bytes(c for c in d[debut:fin] if c not in _BLANCS)
        if not set(chiffres) <= _HEXADECIMAL:
            raise self._erreur()
        self.position = fin + 1
        return bytes.fromhex((chiffres + b"0" * (len(chiffres) & 1)).decode("ascii"))

    def _nom(self) -> Nom:
        d, i = self._d, self.position + 1
        fin = i
        while fin < len(d) and d[fin] not in _BLANCS and d[fin] not in _DELIMITEURS:
            fin += 1
        if fin == len(d) and not self.complet:
            raise _Fin
        brut, octets, j = d[i:fin], bytearray(), 0
        while j < len(brut):
            echappe = brut[j + 1 : j + 3]
            if brut[j] == 0x23 and len(echappe) == 2 and set(echappe) <= _HEXADECIMAL:
                octets.append(int(echappe, 16))
                j += 3
            else:
                octets.append(brut[j])
                j += 1
        self.position = fin
        try:
            return Nom(octets.decode("utf-8"))
        except UnicodeDecodeError:
            return Nom(octets.decode("latin-1"))

    def objet(self) -> Objet:
        return self._objet(self.jeton())

    def _objet(self, jeton: Objet | _Mot) -> Objet:
        self._contexte.compter_objets()
        if isinstance(jeton, _Mot):
            if jeton == b"[":
                with self._contexte.imbrication():
                    liste: list[Objet] = []
                    while not _est(suivant := self.jeton(), b"]"):
                        liste.append(self._objet(suivant))
                    return liste
            if jeton == b"<<":
                with self._contexte.imbrication():
                    dico: dict[str, Objet] = {}
                    while not _est(cle := self.jeton(), b">>"):
                        if not isinstance(cle, Nom):
                            raise self._erreur()
                        dico[str(cle)] = self.objet()
                    return dico
            if jeton == b"true":
                return True
            if jeton == b"false":
                return False
            if jeton == b"null":
                return None
            raise self._erreur()
        if (numero := entier(jeton)) is not None and numero >= 0:
            return self._reference(numero)
        return jeton

    def _reference(self, numero: int) -> Objet:
        """``n g R``, ou l'entier ``n`` seul."""
        position = self.position
        try:
            generation = entier(self.jeton())
            if generation is not None and generation >= 0 and _est(self.jeton(), b"R"):
                return Ref(numero, generation)
        except _Fin:
            if not self.complet:
                raise  # « n g R » peut finir au-delà du tampon
        self.position = position
        return numero

    def mot(self, attendu: bytes) -> None:
        if not _est(self.jeton(), attendu):
            raise self._erreur()

    def indirect(self, ref: Ref | None) -> tuple[Ref, Objet, int]:
        """Objet indirect ``n g obj`` ; sa référence, sa valeur et la position de sa fin.

        Vérifie le numéro et la génération attendus, si ``ref`` est donnée. Lit les données
        d'un flux par leur longueur, sans les décoder.
        """
        numero, generation = entier(self.jeton()), entier(self.jeton())
        if numero is None or generation is None:
            raise self._erreur()
        lue = Ref(numero, generation)
        if ref is not None and ref != lue:
            raise self._erreur()
        self.mot(b"obj")
        valeur = self.objet()
        fin = self.absolue
        if isinstance(valeur, dict):
            position = self.position
            try:
                suivant: Objet | _Mot = self.jeton()
            except _Fin:
                if not self.complet:
                    raise
                suivant = None  # fin de la partie, sans endobj : l'objet est le dictionnaire
            if _est(suivant, b"stream"):
                valeur, fin = self._flux(valeur)
            else:
                self.position = position
        return lue, valeur, fin

    def _flux(self, dico: dict[str, Objet]) -> tuple[Flux, int]:
        d, i = self._d, self.position
        if i + 2 > len(d):
            raise _Fin
        # Fin de ligne après « stream » : CR LF ou LF (§7.3.8.1) ; CR seul toléré.
        i += 2 if d[i : i + 2] == b"\r\n" else 1 if d[i] in _FIN_DE_LIGNE else 0
        debut = self._origine + i
        declaree = dico.get("Length")
        if isinstance(declaree, Ref) and self.resoudre is not None:
            declaree = self.resoudre(declaree)
        longueur = entier(declaree)
        if longueur is None or longueur < 0:
            raise _partiel(debut, "longueur d'un flux")
        fin = debut + longueur
        if fin > self._contexte.taille:
            raise Illisible(RaisonNonMenee.FICHIER_TRONQUE, debut, "données d'un flux")
        suite = _Analyseur(self._contexte, self._contexte.lire(fin, 64), fin)
        try:
            suite.mot(b"endstream")
        except _Fin:
            raise _partiel(fin, "fin d'un flux") from None
        if "F" in dico:
            raise _partiel(debut, "flux dans un autre fichier")
        return Flux(dico, debut, longueur), suite.absolue


def _est(jeton: Objet | _Mot, mot: bytes) -> bool:
    """Vrai si le jeton est ce mot-clé ou ce délimiteur ; une chaîne de ces octets ne l'est pas."""
    return isinstance(jeton, _Mot) and jeton == mot


def _nombre(mot: bytes) -> Objet | _Mot:
    """Nombre entier ou réel (§7.3.3), sinon mot-clé."""
    chiffres = mot.lstrip(b"+-")
    if mot[:1] in b"+-" and len(mot) - len(chiffres) > 1:
        return _Mot(mot)
    entiere, point, decimale = chiffres.partition(b".")
    if (entiere or decimale) and (not entiere or entiere.isdigit()):
        if not point:
            return int(mot)
        if not decimale or decimale.isdigit():
            return float(mot)
    return _Mot(mot)


# Document

_FENETRE = 4096
_QUEUE = 2048
"""Octets lus à la fin de la partie pour trouver ``startxref``."""
_CLES_DU_TRAILER = ("Size", "Root", "Encrypt", "Info", "ID")
"""Clés que les sections antérieures complètent si la plus récente les omet."""


@dataclass(frozen=True, slots=True)
class _Table:
    """Section classique : ses sous-sections, lues à la demande."""

    sous_sections: tuple[tuple[int, int, int, int], ...]
    """Premier numéro, nombre d'entrées, position de la première, largeur d'une entrée."""


@dataclass(frozen=True, slots=True)
class _FluxXref:
    """Section en flux : ses sous-sections, ses largeurs de champs et ses données décodées."""

    sous_sections: tuple[tuple[int, int, int], ...]
    """Premier numéro, nombre d'entrées, rang de la première dans les données."""
    largeurs: tuple[int, int, int]
    donnees: bytes


type _Entree = tuple[int, int, int]
"""Type d'entrée (0 libre, 1 dans le fichier, 2 dans un flux d'objets) et ses deux champs."""


class Document:
    """Document PDF : table des références croisées lue à l'ouverture, objets à la demande."""

    __slots__ = (
        "_cache",
        "_contexte",
        "_en_cours",
        "_etendues",
        "_flux_objets",
        "_sections",
        "sections",
        "trailer",
    )

    def __init__(self, contexte: Contexte) -> None:
        """Lit la table des références croisées ; lève :class:`Illisible` si elle ne se lit pas."""
        self._contexte = contexte
        self._sections: list[_Table | _FluxXref] = []
        self._cache: dict[Ref, Objet] = {}
        self._en_cours: set[int] = set()
        self._etendues: dict[Ref, Plage] = {}
        self._flux_objets: dict[int, tuple[tuple[tuple[int, int], ...], int, bytes]] = {}
        self.trailer: dict[str, Objet] = {}
        """Dictionnaire de fin de la section la plus récente, complété par les antérieures."""
        self.sections = 0
        """Nombre de sections lues : une, plus une par mise à jour incrémentale."""
        self._ouvrir()

    # Lecture de la table

    def _ouvrir(self) -> None:
        position: int | None = self._startxref()
        vues: set[int] = set()
        while position is not None:
            if position in vues:
                raise _partiel(position, "sections de références croisées en boucle")
            vues.add(position)
            self._contexte.compter_objets()
            section, trailer = self._section(position)
            self._sections.append(section)
            self.sections += 1
            for cle in _CLES_DU_TRAILER:
                if cle in trailer and cle not in self.trailer:
                    self.trailer[cle] = trailer[cle]
            hybride = entier(trailer.get("XRefStm"))
            if isinstance(section, _Table) and hybride is not None and hybride not in vues:
                vues.add(hybride)
                complement, _ = self._section(hybride, flux_seulement=True)
                self._sections.append(complement)
            position = entier(trailer.get("Prev"))

    def _startxref(self) -> int:
        taille = self._contexte.taille
        debut = max(0, taille - _QUEUE)
        queue = self._contexte.lire(debut, taille - debut)
        indice = queue.rfind(b"startxref")
        if indice == -1:
            raise _partiel(taille - 1, "startxref")
        analyseur = _Analyseur(self._contexte, queue, debut)
        analyseur.position = indice + len(b"startxref")
        try:
            position = entier(analyseur.jeton())
        except _Fin:
            raise _partiel(debut + indice, "startxref") from None
        if position is None or not 0 <= position < taille:
            raise _partiel(debut + indice, "startxref")
        return position

    def _fenetre[T](self, position: int, lire: Callable[[_Analyseur], T]) -> T:
        """Lit depuis ``position`` par fenêtres croissantes, jusqu'à ce que l'objet tienne."""
        fenetre = _FENETRE
        while True:
            donnees = self._contexte.lire(position, fenetre)
            try:
                return lire(_Analyseur(self._contexte, donnees, position, self.resoudre))
            except _Fin:
                if position + len(donnees) >= self._contexte.taille:
                    raise Illisible(
                        RaisonNonMenee.FICHIER_TRONQUE, position, "objet du PDF"
                    ) from None
                if fenetre >= TAILLE_MAX_LECTURE:
                    raise _partiel(position, "objet du PDF") from None
                fenetre = min(fenetre * 16, TAILLE_MAX_LECTURE)

    def _section(
        self, position: int, *, flux_seulement: bool = False
    ) -> tuple[_Table | _FluxXref, dict[str, Objet]]:
        tete = self._contexte.lire(position, 64)
        decalage = len(tete) - len(tete.lstrip(bytes(_BLANCS)))
        if tete[decalage:].startswith(b"xref") and not flux_seulement:
            return self._table(position + decalage + 4)
        _, objet, _ = self._fenetre(position, lambda a: a.indirect(None))
        if not isinstance(objet, Flux) or objet.dico.get("Type") != "XRef":
            raise _partiel(position, "section de références croisées")
        return self._flux_xref(objet), objet.dico

    def _table(self, position: int) -> tuple[_Table, dict[str, Objet]]:
        sous_sections: list[tuple[int, int, int, int]] = []
        while True:
            self._contexte.compter_objets()
            premier, second, suite = self._fenetre(position, _tete_de_sous_section)
            if _est(premier, b"trailer"):
                if not isinstance(second, dict):
                    raise _partiel(position, "trailer")
                return _Table(tuple(sous_sections)), second
            debut, nombre = entier(premier), entier(second)
            if debut is None or nombre is None or debut < 0 or nombre < 0:
                raise _partiel(position, "table de références croisées")
            largeur = self._largeur(suite) if nombre else 20
            sous_sections.append((debut, nombre, suite, largeur))
            position = suite + nombre * largeur
            if position > self._contexte.taille:
                raise Illisible(
                    RaisonNonMenee.FICHIER_TRONQUE, suite, "table de références croisées"
                )

    def _largeur(self, position: int) -> int:
        """Largeur des entrées d'une sous-section : 20 octets d'après la norme, 19 ou 21 tolérés."""
        entree = self._contexte.lire(position, 21)
        if _entree_classique(entree) is None:
            raise _partiel(position, "table de références croisées")
        fin = 18
        while fin < len(entree) and entree[fin] in b" \r\n":
            fin += 1
        if fin == 18:
            raise _partiel(position, "table de références croisées")
        return fin

    def _flux_xref(self, flux: Flux) -> _FluxXref:
        dico = flux.dico
        largeurs = _positifs(dico.get("W"))
        nombres = _positifs(dico.get("Index", [0, dico.get("Size")]))
        if largeurs is None or len(largeurs) != 3 or max(largeurs) > 8:
            raise _partiel(flux.debut, "flux de références croisées")
        if nombres is None or len(nombres) % 2:
            raise _partiel(flux.debut, "flux de références croisées")
        donnees = self.decoder(flux)
        sous_sections, rang = [], 0
        for premier, nombre in zip(nombres[::2], nombres[1::2], strict=True):
            sous_sections.append((premier, nombre, rang))
            rang += nombre
        w1, w2, w3 = largeurs
        if len(donnees) < rang * (w1 + w2 + w3):
            raise _partiel(flux.debut, "flux de références croisées")
        return _FluxXref(tuple(sous_sections), (w1, w2, w3), donnees)

    def _entree(self, numero: int) -> _Entree | None:
        """Entrée de la section la plus récente qui connaît l'objet ; ``None`` si aucune."""
        for section in self._sections:
            if isinstance(section, _Table):
                for premier, nombre, position, largeur in section.sous_sections:
                    if premier <= numero < premier + nombre:
                        endroit = position + (numero - premier) * largeur
                        entree = _entree_classique(self._contexte.lire(endroit, 18))
                        if entree is None:
                            raise _partiel(endroit, "table de références croisées")
                        return entree
                continue
            for premier, nombre, rang in section.sous_sections:
                if premier <= numero < premier + nombre:
                    return _entree_flux(section, rang + numero - premier)
        return None

    # Objets

    def resoudre(self, objet: Objet) -> Objet:
        """L'objet au bout d'une chaîne de références ; tout autre objet tel quel."""
        vues: set[Ref] = set()
        while isinstance(objet, Ref):
            if objet in vues:
                raise _partiel(0, "références circulaires")
            vues.add(objet)
            objet = self.objet(objet)
        return objet

    def objet(self, ref: Ref) -> Objet:
        """Objet indirect ; ``None`` s'il est libre ou absent de la table (§7.3.10)."""
        if ref in self._cache:
            return self._cache[ref]
        if ref.numero in self._en_cours:
            raise _partiel(0, "références circulaires")
        entree = self._entree(ref.numero)
        valeur: Objet = None
        if entree is not None:
            self._en_cours.add(ref.numero)
            try:
                with self._contexte.imbrication():
                    valeur = self._lire(ref, entree)
            finally:
                self._en_cours.discard(ref.numero)
        self._cache[ref] = valeur
        return valeur

    def _lire(self, ref: Ref, entree: _Entree) -> Objet:
        nature, premier, second = entree
        if nature == 1 and second == ref.generation:
            if premier >= self._contexte.taille:
                raise _partiel(premier, f"objet {ref.numero} {ref.generation}")
            _, valeur, fin = self._fenetre(premier, lambda a: a.indirect(ref))
            self._etendues[ref] = Plage(premier, max(fin - premier, 1))
            return valeur
        if nature == 2 and ref.generation == 0:
            return self._dans_un_flux(ref, premier, second)
        return None  # libre, d'une autre génération ou d'un type inconnu : objet nul

    def _dans_un_flux(self, ref: Ref, numero_flux: int, rang: int) -> Objet:
        """Objet d'un flux d'objets (§7.5.7)."""
        if numero_flux not in self._flux_objets:
            flux = self.objet(Ref(numero_flux, 0))
            if not isinstance(flux, Flux) or flux.dico.get("Type") != "ObjStm":
                raise _partiel(0, f"flux d'objets {numero_flux}")
            nombre, premier = entier(flux.dico.get("N")), entier(flux.dico.get("First"))
            if nombre is None or premier is None or nombre < 0 or premier < 0:
                raise _partiel(flux.debut, f"flux d'objets {numero_flux}")
            donnees = self.decoder(flux)
            analyseur = _Analyseur(self._contexte, donnees[:premier], 0, complet=True)
            paires: list[tuple[int, int]] = []
            try:
                for _ in range(nombre):
                    numero, decalage = entier(analyseur.jeton()), entier(analyseur.jeton())
                    if numero is None or decalage is None:
                        raise _partiel(flux.debut, f"flux d'objets {numero_flux}")
                    paires.append((numero, decalage))
            except _Fin:
                raise _partiel(flux.debut, f"flux d'objets {numero_flux}") from None
            self._flux_objets[numero_flux] = (tuple(paires), premier, donnees)
        lues, premier, donnees = self._flux_objets[numero_flux]
        if not 0 <= rang < len(lues) or lues[rang][0] != ref.numero:
            raise _partiel(0, f"objet {ref.numero} 0 dans le flux d'objets {numero_flux}")
        analyseur = _Analyseur(self._contexte, donnees, 0, complet=True)
        analyseur.position = premier + lues[rang][1]
        try:
            return analyseur.objet()
        except (_Fin, Illisible):
            raise _partiel(0, f"objet {ref.numero} 0 dans le flux d'objets {numero_flux}") from None

    def localisation(self, ref: Ref, chemin: str) -> Localisation:
        """Chemin d'un objet, et sa plage d'octets s'il est lu directement dans le fichier."""
        return Localisation(
            chemin=f"{chemin} (objet {ref.numero} {ref.generation})",
            octets=self._etendues.get(ref),
        )

    # Flux

    def decoder(self, flux: Flux) -> bytes:
        """Données d'un flux, décodées ; seul ``FlateDecode`` est connu (§7.4.4)."""
        filtres = self.resoudre(flux.dico.get("Filter"))
        parametres = self.resoudre(flux.dico.get("DecodeParms"))
        if not isinstance(filtres, list):
            filtres = [] if filtres is None else [filtres]
        if not isinstance(parametres, list):
            parametres = [parametres] * len(filtres)
        if flux.longueur > TAILLE_MAX_LECTURE or len(parametres) != len(filtres):
            raise _partiel(flux.debut, "flux")
        donnees = self._contexte.lire(flux.debut, flux.longueur)
        for filtre, parametre in zip(filtres, parametres, strict=True):
            if self.resoudre(filtre) != "FlateDecode":
                raise _partiel(flux.debut, "filtre d'un flux")
            try:
                donnees = self._contexte.decompresser(donnees, "zlib")
            except zlib.error:
                raise _partiel(flux.debut, "flux compressé") from None
            donnees = _predire(donnees, self.resoudre(parametre), flux.debut)
        return donnees


def _positifs(objet: Objet) -> list[int] | None:
    """Liste d'entiers positifs ou nuls ; ``None`` pour tout autre objet."""
    if not isinstance(objet, list):
        return None
    nombres = [n for n in (entier(o) for o in objet) if n is not None and n >= 0]
    return nombres if len(nombres) == len(objet) else None


def _tete_de_sous_section(analyseur: _Analyseur) -> tuple[Objet | _Mot, Objet | _Mot, int]:
    """Premier numéro et nombre d'entrées d'une sous-section, ou ``trailer`` et son dictionnaire."""
    premier = analyseur.jeton()
    if _est(premier, b"trailer"):
        return premier, analyseur.objet(), analyseur.absolue
    nombre = analyseur.jeton()
    analyseur.blancs()
    return premier, nombre, analyseur.absolue


def _entree_classique(entree: bytes) -> _Entree | None:
    """Entrée ``nnnnnnnnnn ggggg n`` d'une table classique ; ``None`` si elle n'en est pas une."""
    position, generation, marque = entree[:10], entree[11:16], entree[17:18]
    if not (
        position.isdigit() and generation.isdigit() and entree[10:11] == entree[16:17] == b" "
    ) or marque not in (b"n", b"f"):
        return None
    return (1 if marque == b"n" else 0, int(position), int(generation))


def _entree_flux(section: _FluxXref, rang: int) -> _Entree:
    largeur = sum(section.largeurs)
    ligne = section.donnees[rang * largeur : (rang + 1) * largeur]
    champs, position = [], 0
    for taille in section.largeurs:
        champs.append(int.from_bytes(ligne[position : position + taille], "big"))
        position += taille
    nature = champs[0] if section.largeurs[0] else 1  # type absent : 1 (§7.5.8.3)
    return (nature, champs[1], champs[2])


# Prédicteurs (§7.4.4.4)


def _predire(donnees: bytes, parametres: Objet, position: int) -> bytes:
    if not isinstance(parametres, dict):
        return donnees
    predicteur = entier(parametres.get("Predictor", 1))
    colonnes = entier(parametres.get("Columns", 1))
    couleurs = entier(parametres.get("Colors", 1))
    bits = entier(parametres.get("BitsPerComponent", 8))
    if predicteur == 1:
        return donnees
    if (
        colonnes is None
        or couleurs is None
        or not 1 <= colonnes <= 1 << 24
        or not 1 <= couleurs <= 32
        or bits not in (1, 2, 4, 8, 16)
    ):
        raise _partiel(position, "prédicteur d'un flux")
    largeur = (colonnes * couleurs * bits + 7) // 8
    pas = max(1, couleurs * bits // 8)
    if predicteur == 2 and bits == 8:
        return _tiff(donnees, largeur, pas)
    if predicteur is not None and 10 <= predicteur <= 15:
        return _png(donnees, largeur, pas, position)
    raise _partiel(position, "prédicteur d'un flux")


def _tiff(donnees: bytes, largeur: int, pas: int) -> bytes:
    sortie = bytearray(donnees)
    for debut in range(0, len(sortie), largeur):
        for i in range(debut + pas, min(debut + largeur, len(sortie))):
            sortie[i] = (sortie[i] + sortie[i - pas]) & 0xFF
    return bytes(sortie)


_SEPT = 0x7F
_HUIT = 0x80


def _png(donnees: bytes, largeur: int, pas: int, position: int) -> bytes:
    """Lignes filtrées PNG ; une dernière ligne incomplète est écartée."""
    sortie = bytearray()
    precedente = bytes(largeur)
    masque_bas = int.from_bytes(bytes([_SEPT]) * largeur, "big")
    masque_haut = int.from_bytes(bytes([_HUIT]) * largeur, "big")
    for debut in range(0, len(donnees) - largeur, largeur + 1):
        filtre, ligne = donnees[debut], bytearray(donnees[debut + 1 : debut + 1 + largeur])
        if filtre == 2:  # Up : somme octet par octet, sans retenue, sur toute la ligne
            a, b = int.from_bytes(ligne, "big"), int.from_bytes(precedente, "big")
            somme = ((a & masque_bas) + (b & masque_bas)) ^ ((a ^ b) & masque_haut)
            ligne = bytearray(somme.to_bytes(largeur, "big"))
        elif filtre in (1, 3, 4):
            for i in range(largeur):
                gauche = ligne[i - pas] if i >= pas else 0
                haut = precedente[i]
                if filtre == 1:
                    ajout = gauche
                elif filtre == 3:
                    ajout = (gauche + haut) // 2
                else:
                    diagonale = precedente[i - pas] if i >= pas else 0
                    ajout = _paeth(gauche, haut, diagonale)
                ligne[i] = (ligne[i] + ajout) & 0xFF
        elif filtre != 0:
            raise _partiel(position, "prédicteur d'un flux")
        sortie += ligne
        precedente = bytes(ligne)
    return bytes(sortie)


def _paeth(gauche: int, haut: int, diagonale: int) -> int:
    estimation = gauche + haut - diagonale
    ecarts = (abs(estimation - gauche), abs(estimation - haut), abs(estimation - diagonale))
    if ecarts[0] <= ecarts[1] and ecarts[0] <= ecarts[2]:
        return gauche
    return haut if ecarts[1] <= ecarts[2] else diagonale
