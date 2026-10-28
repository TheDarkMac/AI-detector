"""Structure TIFF d'un bloc EXIF : répertoires (IFD) et entrées (TIFF 6.0 ; EXIF 3.0).

Le lecteur suit IFD0 et les répertoires chaînés (IFD1, vignette), et les sous-répertoires
désignés par leur étiquette : EXIF, GPS, interopérabilité. Il rend chaque entrée avec ses octets
bruts, sans les interpréter : le module de métadonnées en tire les valeurs. Les octets sont une
vue sur le bloc, jamais une copie : un fichier qui fait désigner mille fois la même grande zone
ne coûte pas mille copies.

Un répertoire déjà parcouru n'est pas relu (boucle), une entrée qui déborde du bloc ou d'un type
inconnu est écartée ; l'un et l'autre font du bloc un format partiel.
"""

import struct
from collections.abc import Generator, Iterator
from dataclasses import dataclass

from voight_kampff._travail.contexte import Contexte

__all__ = ["POINTEURS", "Entree", "Tiff", "nombres"]

TAILLES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4, 129: 1}
"""Taille d'un élément par type : BYTE, ASCII, SHORT, LONG, RATIONAL, SBYTE, UNDEFINED, SSHORT,
SLONG, SRATIONAL, FLOAT, DOUBLE, IFD, UTF-8 (EXIF 3.0)."""

POINTEURS = {0x8769: "exif", 0x8825: "gps", 0xA005: "interop"}
"""Étiquettes qui désignent un sous-répertoire, et le nom de celui-ci."""


@dataclass(frozen=True, slots=True)
class Entree:
    """Entrée d'un répertoire : étiquette, type, nombre d'éléments, octets bruts."""

    repertoire: str
    """``ifd0``, ``ifd1``…, ``exif``, ``gps``, ``interop``."""
    etiquette: int
    type: int
    compte: int
    brut: memoryview
    ordre: str
    """``<`` (Intel) ou ``>`` (Motorola), pour ``struct``."""


class Tiff:
    """Lecture d'une structure TIFF ; ``partiel`` dit si quelque chose a été écarté."""

    __slots__ = ("_contexte", "_donnees", "_ordre", "_vus", "partiel")

    def __init__(self, contexte: Contexte, donnees: bytes) -> None:
        self._contexte = contexte
        self._donnees = memoryview(donnees)
        self._vus: set[int] = set()
        self.partiel = False
        self._ordre = {b"II*\x00": "<", b"MM\x00*": ">"}.get(bytes(self._donnees[:4]), "")

    @property
    def ordre(self) -> str:
        """``II`` ou ``MM`` ; vide si l'en-tête n'est pas celui d'une structure TIFF."""
        return {"<": "II", ">": "MM"}.get(self._ordre, "")

    def entrees(self) -> Iterator[Entree]:
        """Entrées de tous les répertoires, IFD0 d'abord, sous-répertoires à leur place."""
        if not self._ordre or len(self._donnees) < 8:
            self.partiel = True
            return
        position = self._entier(4, 4)
        rang = 0
        while position and rang < 1 << 16:
            suivant = yield from self._repertoire(f"ifd{rang}", position)
            position, rang = suivant, rang + 1

    def _entier(self, position: int, taille: int) -> int:
        format_ = {2: "H", 4: "I"}[taille]
        return int(struct.unpack_from(self._ordre + format_, self._donnees, position)[0])

    def _repertoire(self, nom: str, position: int) -> Generator[Entree, None, int]:
        """Entrées d'un répertoire ; renvoie la position du suivant, 0 s'il n'y en a pas."""
        if position in self._vus or position + 2 > len(self._donnees):
            self.partiel = True
            return 0
        self._vus.add(position)
        nombre = self._entier(position, 2)
        if position + 2 + 12 * nombre + 4 > len(self._donnees):
            self.partiel = True
            nombre = (len(self._donnees) - position - 2) // 12
            suivant = 0
        else:
            suivant = self._entier(position + 2 + 12 * nombre, 4)
        with self._contexte.imbrication():
            for rang in range(nombre):
                self._contexte.compter_objets()
                entree = self._entree(nom, position + 2 + 12 * rang)
                if entree is None:
                    continue
                sous = POINTEURS.get(entree.etiquette) if nom != "gps" else None
                if sous is not None and entree.type in (4, 13) and entree.compte == 1:
                    yield from self._repertoire(sous, self._entier(position + 10 + 12 * rang, 4))
                else:
                    yield entree
        return suivant

    def _entree(self, repertoire: str, position: int) -> Entree | None:
        etiquette, type_ = self._entier(position, 2), self._entier(position + 2, 2)
        compte = self._entier(position + 4, 4)
        taille = TAILLES.get(type_)
        if taille is None:
            self.partiel = True
            return None
        longueur = taille * compte
        debut = position + 8 if longueur <= 4 else self._entier(position + 8, 4)
        if debut + longueur > len(self._donnees):
            self.partiel = True
            return None
        brut = self._donnees[debut : debut + longueur]
        return Entree(repertoire, etiquette, type_, compte, brut, self._ordre)


_NOMBRES = {1: "B", 3: "H", 4: "I", 5: "II", 6: "b", 7: "B", 8: "h", 9: "i", 10: "ii"}
_NOMBRES |= {11: "f", 12: "d", 13: "I"}
"""Format ``struct`` d'un élément ; les octets indéfinis (7) sont lus comme des octets."""


def nombres(entree: Entree, maximum: int) -> list[int | float | tuple[int, int]]:
    """Au plus ``maximum`` éléments numériques ; une fraction, son numérateur et dénominateur."""
    format_ = _NOMBRES[entree.type]
    taille = TAILLES[entree.type]
    nombre = min(entree.compte, maximum)
    valeurs: list[int | float | tuple[int, int]] = []
    for rang in range(nombre):
        lu = struct.unpack_from(entree.ordre + format_, entree.brut, rang * taille)
        valeurs.append((int(lu[0]), int(lu[1])) if len(lu) == 2 else lu[0])
    return valeurs
