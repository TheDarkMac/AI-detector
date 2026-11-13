"""Archive ZIP d'un DOCX ou d'un ODT : répertoire central et entrées, lus en mémoire (ADR-0137).

L'archive est lue comme le font les lecteurs, et comme l'identification (ADR-0070) : depuis
l'enregistrement de fin, ZIP64 compris, puis le répertoire central (APPNOTE, §4.3). Une entrée
n'est lue que sur demande, par son nom : en-tête local, puis données stockées ou compressées
par deflate. Rien n'est écrit sur disque (ES-05) ; la décompression passe par le contexte, qui
la compte contre le budget du module (ES-03).

Lecture stricte : un en-tête local dont le nom diffère de celui du répertoire central, deux
entrées de même nom, une entrée chiffrée ou compressée autrement que par deflate arrêtent la
lecture de l'entrée. Le CRC n'est pas vérifié : il ne change pas ce que l'entrée déclare.
"""

import codecs
import zlib
from dataclasses import dataclass

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Contexte
from voight_kampff.rapport.modele import Localisation, Plage, RaisonNonMenee

__all__ = ["Archive", "Entree", "Illisible"]

# Cherché dès l'import : après les restrictions, un codec ne peut plus être chargé (ERR-0009).
_CP437 = codecs.lookup("cp437")

_FIN = b"PK\x05\x06"
_FIN_ZIP64 = b"PK\x06\x06"
_CENTRALE = b"PK\x01\x02"
_LOCALE = b"PK\x03\x04"
_STOCKEE, _DEFLATE = 0, 8
_CHIFFREE, _UTF8 = 0x0001, 0x0800
_ZIP64 = 0x0001
"""Identifiant du champ supplémentaire ZIP64 (APPNOTE, §4.5.3)."""


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


def _partiel(position: int, chemin: str = "structure de l'archive") -> Illisible:
    return Illisible(RaisonNonMenee.FORMAT_PARTIEL, position, chemin)


def _petit(octets: bytes) -> int:
    return int.from_bytes(octets, "little")


@dataclass(frozen=True, slots=True)
class Entree:
    """Entrée du répertoire central."""

    nom: str
    brut: bytes
    """Nom tel qu'écrit, comparé à celui de l'en-tête local."""
    drapeaux: int
    methode: int
    compresse: int
    """Taille des données dans l'archive, en octets."""
    locale: int
    """Position de l'en-tête local dans la partie."""


class Archive:
    """Répertoire central d'une archive ZIP ; lève :class:`Illisible` s'il ne se lit pas."""

    def __init__(self, contexte: Contexte) -> None:
        self._contexte = contexte
        self.entrees = self._repertoire()

    def _repertoire(self) -> tuple[Entree, ...]:
        contexte = self._contexte
        depart = max(0, contexte.taille - (22 + 0xFFFF))
        queue = contexte.lire(depart, contexte.taille - depart)
        indice = queue.rfind(_FIN)
        # Comme l'identification : le dernier enregistrement dont le commentaire tient.
        while indice != -1 and indice + 22 + _petit(queue[indice + 20 : indice + 22]) > len(queue):
            indice = queue.rfind(_FIN, 0, indice)
        if indice == -1:
            raise _partiel(contexte.taille - 1)
        fin = depart + indice
        nombre = _petit(queue[indice + 10 : indice + 12])
        taille = _petit(queue[indice + 12 : indice + 16])
        decalage = _petit(queue[indice + 16 : indice + 20])
        if 0xFFFFFFFF in (taille, decalage) or nombre == 0xFFFF:
            fin -= 20 + 56  # enregistrement ZIP64, juste avant son localisateur
            enregistrement = contexte.lire(fin, 56) if fin >= 0 else b""
            if enregistrement[:4] != _FIN_ZIP64:
                raise _partiel(max(fin, 0))
            nombre = _petit(enregistrement[32:40])
            taille = _petit(enregistrement[40:48])
            decalage = _petit(enregistrement[48:56])
        position = fin - taille
        if position < 0:
            raise _partiel(fin)
        if taille > TAILLE_MAX_LECTURE:
            raise _partiel(position, "répertoire central")
        # Positions relatives à l'archive ou au fichier : le répertoire central les situe.
        self._decalage = position - decalage
        repertoire = contexte.lire(position, taille)
        entrees: list[Entree] = []
        curseur = 0
        for _ in range(nombre):
            contexte.compter_objets()
            entrees.append(self._entree(repertoire, curseur, position))
            longueurs = (_petit(repertoire[curseur + i : curseur + i + 2]) for i in (28, 30, 32))
            curseur += 46 + sum(longueurs)
        return tuple(entrees)

    def _entree(self, repertoire: bytes, curseur: int, position: int) -> Entree:
        enregistrement = repertoire[curseur : curseur + 46]
        if len(enregistrement) < 46 or enregistrement[:4] != _CENTRALE:
            raise _partiel(position + curseur, "répertoire central")
        longueur, supplement = _petit(enregistrement[28:30]), _petit(enregistrement[30:32])
        brut = repertoire[curseur + 46 : curseur + 46 + longueur]
        champs = repertoire[curseur + 46 + longueur : curseur + 46 + longueur + supplement]
        if len(brut) < longueur or len(champs) < supplement:
            raise _partiel(position + curseur, "répertoire central")
        drapeaux = _petit(enregistrement[8:10])
        compresse, locale = _petit(enregistrement[20:24]), _petit(enregistrement[42:46])
        if 0xFFFFFFFF in (compresse, locale):
            compresse, locale = self._zip64(champs, enregistrement, position + curseur)
        nom = brut.decode("utf-8", "replace") if drapeaux & _UTF8 else _CP437.decode(brut)[0]
        return Entree(nom, brut, drapeaux, _petit(enregistrement[10:12]), compresse, locale)

    @staticmethod
    def _zip64(champs: bytes, enregistrement: bytes, position: int) -> tuple[int, int]:
        """Tailles et position du champ ZIP64, dans l'ordre de la norme, présentes seulement
        pour les valeurs qui valent 0xFFFFFFFF dans l'enregistrement (APPNOTE, §4.5.3)."""
        curseur = 0
        while curseur + 4 <= len(champs):
            identifiant = _petit(champs[curseur : curseur + 2])
            longueur = _petit(champs[curseur + 2 : curseur + 4])
            donnees = champs[curseur + 4 : curseur + 4 + longueur]
            curseur += 4 + longueur
            if identifiant != _ZIP64:
                continue
            lues = (_petit(donnees[i : i + 8]) for i in range(0, len(donnees) - 7, 8))
            valeurs: dict[int, int] = {}
            for debut in (24, 20, 42):  # non compressée, compressée, position locale
                valeur: int | None = _petit(enregistrement[debut : debut + 4])
                if valeur == 0xFFFFFFFF:
                    valeur = next(lues, None)
                if valeur is None:
                    raise _partiel(position, "répertoire central")
                valeurs[debut] = valeur
            return valeurs[20], valeurs[42]
        raise _partiel(position, "répertoire central")

    def trouver(self, nom: str, *, casse: bool = True) -> Entree | None:
        """Entrée de ce nom, ``None`` si aucune ; deux entrées de ce nom sont illisibles.

        ``casse=False`` compare les lettres ASCII sans leur casse, comme les noms de parties
        d'OPC (ECMA-376, partie 2).
        """
        cle = nom if casse else _ascii_minuscules(nom)
        trouvees = [
            entree
            for entree in self.entrees
            if (entree.nom if casse else _ascii_minuscules(entree.nom)) == cle
        ]
        if len(trouvees) > 1:
            raise _partiel(self._decalage + trouvees[1].locale, f"{nom} (entrées en double)")
        return trouvees[0] if trouvees else None

    def _donnees(self, entree: Entree) -> int:
        """Position des données de l'entrée, après son en-tête local vérifié."""
        locale = self._decalage + entree.locale
        if locale < 0 or locale >= self._contexte.taille:
            raise _partiel(max(locale, 0), entree.nom)
        entete = self._contexte.lire(locale, 30)
        if len(entete) < 30:
            raise Illisible(RaisonNonMenee.FICHIER_TRONQUE, locale, entree.nom)
        if entete[:4] != _LOCALE:
            raise _partiel(locale, entree.nom)
        longueur, supplement = _petit(entete[26:28]), _petit(entete[28:30])
        if self._contexte.lire(locale + 30, longueur) != entree.brut:
            raise _partiel(locale, f"{entree.nom} (nom de l'en-tête local différent)")
        return locale + 30 + longueur + supplement

    def lire(self, entree: Entree) -> bytes:
        """Contenu de l'entrée, décompressé ; lève :class:`Illisible` s'il ne se lit pas."""
        debut = self._donnees(entree)
        if entree.drapeaux & _CHIFFREE:
            raise _partiel(debut, f"{entree.nom} (entrée chiffrée)")
        if entree.methode not in (_STOCKEE, _DEFLATE):
            raise _partiel(debut, f"{entree.nom} (compression inconnue)")
        if entree.compresse > TAILLE_MAX_LECTURE:
            raise _partiel(debut, entree.nom)
        if debut + entree.compresse > self._contexte.taille:
            raise Illisible(RaisonNonMenee.FICHIER_TRONQUE, debut, entree.nom)
        donnees = self._contexte.lire(debut, entree.compresse)
        if entree.methode == _STOCKEE:
            return donnees
        try:
            return self._contexte.decompresser(donnees, "deflate")
        except zlib.error:
            raise _partiel(debut, entree.nom) from None

    def localisation(self, entree: Entree) -> Localisation:
        """Nom de l'entrée et ses octets dans la partie, en-tête local compris."""
        locale = self._decalage + entree.locale
        fin = self._donnees(entree) + entree.compresse
        return Localisation(chemin=entree.nom, octets=Plage(locale, fin - locale))


def _ascii_minuscules(texte: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in texte)
