"""Dates écrites dans les métadonnées, lues pour les règles qui les éprouvent (T23, ADR-0148).

Les modules observent les dates telles qu'écrites (ADR-0118, ADR-0128, ADR-0133) ; une règle du
catalogue dit comment lire la valeur (``lecture``), et ce module la lit. Une date lue est un
**intervalle** d'instants UTC : celui de tous les instants que l'écriture peut désigner. Une date
sans heure couvre son jour, une heure sans fuseau couvre les fuseaux de UTC-12 à UTC+14. Deux
dates ne sont dites dans un ordre que si tous les instants de l'une précèdent tous ceux de
l'autre : une écriture imprécise ne fait jamais naître un constat.

Une valeur se lit de quatre façons :

- une date : son intervalle ;
- ``IMPOSSIBLE`` : l'écriture est suivie, mais la date n'existe pas (mois 13, 30 février) ;
- ``NON_RENSEIGNEE`` : la valeur que l'écriture réserve à une date inconnue ;
- ``NON_RECONNUE`` : toute autre valeur, qui ne suit pas l'écriture.

Le code ne devine pas ce qu'une valeur non reconnue voulait dire. Les expressions sont fixes,
sans répétition imbriquée : leur temps est linéaire (ADR-0039).
"""

import calendar
import re
from dataclasses import dataclass
from datetime import date
from enum import Enum, StrEnum
from functools import lru_cache

from voight_kampff.rapport.modele import Scalaire

__all__ = ["Etat", "Intervalle", "Lecture", "lire"]


class Lecture(StrEnum):
    """Écriture d'une date, que la règle déclare pour les observations qu'elle lit."""

    EXIF = "date-exif"
    """``AAAA:MM:JJ HH:MM:SS``, heure locale sans fuseau (EXIF 3.0, CIPA DC-008-2023)."""
    PDF = "date-pdf"
    """``D:AAAAMMJJHHmmSSOHH'mm'``, champs finaux facultatifs (ISO 32000, chaîne de date)."""
    ISO8601 = "date-iso8601"
    """``AAAA-MM-JJThh:mm:ss.s±hh:mm``, parties finales et fuseau facultatifs : dates XMP,
    W3CDTF des propriétés OOXML, ``xsd:dateTime`` d'ODF."""
    SECONDES_1904 = "date-1904"
    """Entier, secondes depuis le 1904-01-01 à minuit UTC (ISO/IEC 14496-12, ``mvhd``)."""


class Etat(Enum):
    """Lecture qui ne donne aucun intervalle."""

    IMPOSSIBLE = "impossible"
    NON_RENSEIGNEE = "non_renseignee"
    NON_RECONNUE = "non_reconnue"


@dataclass(frozen=True, slots=True)
class Intervalle:
    """Instants qu'une date peut désigner, en microsecondes depuis 0001-01-01T00:00Z ; ``fin``
    est exclue."""

    debut: int
    fin: int

    def avant(self, autre: "Intervalle") -> bool:
        """Vrai si chaque instant de cette date précède chaque instant de l'autre."""
        return self.fin <= autre.debut


type Lue = Intervalle | Etat
type Champs = tuple[int, int | None, int | None, int | None, int | None, int | None]
"""Année, mois, jour, heure, minute, seconde ; seuls les premiers sont écrits."""

_US = 1_000_000
_MINUTE = 60 * _US
_HEURE = 60 * _MINUTE
_JOUR = 24 * _HEURE
_AVANCE_MAX = 14 * _HEURE
"""UTC+14 : une heure sans fuseau peut désigner un instant UTC jusqu'à 14 h plus tôt."""
_RETARD_MAX = 12 * _HEURE
"""UTC-12 : jusqu'à 12 h plus tard."""
_EPOQUE_1904 = (date(1904, 1, 1).toordinal() - 1) * _JOUR
_FIN = date(9999, 12, 31).toordinal() * _JOUR
"""Fin de l'an 9999, le dernier qui s'écrit en quatre chiffres ; ``toordinal`` compte le
0001-01-01 comme jour 1."""

_EXIF = re.compile(r"([0-9]{4}):([0-9]{2}):([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})")
_EXIF_INCONNUE = re.compile(r"[0 ]{4}:[0 ]{2}:[0 ]{2} [0 ]{2}:[0 ]{2}:[0 ]{2}")
"""Date inconnue d'EXIF : chiffres remplacés par des espaces (la norme), ou tous nuls (l'usage)."""
_PDF = re.compile(
    r"(?:D:)?([0-9]{4})(?:([0-9]{2})(?:([0-9]{2})(?:([0-9]{2})(?:([0-9]{2})(?:([0-9]{2}))?)?)?)?)?"
    r"(?:(Z)(?:00'?(?:00'?)?)?|([+-])([0-9]{2})(?:'?([0-9]{2}))?'?)?"
)
_ISO8601 = re.compile(
    r"([0-9]{4})(?:-([0-9]{2})(?:-([0-9]{2})(?:T([0-9]{2}):([0-9]{2})"
    r"(?::([0-9]{2})(?:[.,]([0-9]+))?)?(?:(Z)|([+-])([0-9]{2}):?([0-9]{2}))?)?)?)?"
)


def _entier(texte: str | None) -> int | None:
    return None if texte is None else int(texte)


def _premier_jour(annee: int, mois: int) -> int:
    if annee > 9999:
        return _FIN
    return (date(annee, mois, 1).toordinal() - 1) * _JOUR


def _intervalle(champs: Champs, fraction: str | None, decalage: int | None) -> Lue:
    """Intervalle d'une date écrite jusqu'à son dernier champ, à la précision de ce champ.

    ``decalage`` : avance de l'heure locale sur UTC, en minutes ; ``None`` si le fuseau n'est
    pas écrit. Un champ hors de son domaine rend la date impossible ; ``24:00:00`` est la fin
    du jour, et la seconde 60, une seconde intercalaire (ISO 8601).
    """
    annee, mois, jour, heure, minute, seconde = champs
    if annee == 0:
        return Etat.NON_RECONNUE  # l'an 0 n'existe pas dans le calendrier des métadonnées
    if mois is not None and not 1 <= mois <= 12:
        return Etat.IMPOSSIBLE
    if (
        mois is not None
        and jour is not None
        and not 1 <= jour <= calendar.monthrange(annee, mois)[1]
    ):
        return Etat.IMPOSSIBLE
    fin_du_jour = heure == 24 and not minute and not seconde and not int(fraction or "0")
    if heure is not None and not (heure <= 23 or fin_du_jour):
        return Etat.IMPOSSIBLE
    if (minute or 0) > 59 or (seconde or 0) > 60:
        return Etat.IMPOSSIBLE
    if mois is None:
        debut, fin = _premier_jour(annee, 1), _premier_jour(annee + 1, 1)
    elif jour is None:
        debut = _premier_jour(annee, mois)
        fin = _premier_jour(annee, mois + 1) if mois < 12 else _premier_jour(annee + 1, 1)
    else:
        debut = (date(annee, mois, jour).toordinal() - 1) * _JOUR
        debut += (heure or 0) * _HEURE + (minute or 0) * _MINUTE + (seconde or 0) * _US
        if heure is None:
            pas = _JOUR
        elif minute is None:
            pas = _HEURE
        elif seconde is None:
            pas = _MINUTE
        elif fraction:
            chiffres = fraction[:6]  # au-delà de la microseconde, la fin de l'intervalle couvre
            debut += int(chiffres.ljust(6, "0"))
            pas = 10 ** (6 - len(chiffres))
        else:
            pas = _US
        fin = debut + pas
    if decalage is None:
        return Intervalle(debut - _AVANCE_MAX, fin + _RETARD_MAX)
    return Intervalle(debut - decalage * _MINUTE, fin - decalage * _MINUTE)


def _decalage(
    zulu: str | None, signe: str | None, heures: str | None, minutes: str | None
) -> Etat | int | None:
    """Avance du fuseau sur UTC en minutes, ``None`` s'il n'est pas écrit."""
    if zulu is not None:
        return 0
    if signe is None or heures is None:
        return None
    valeur_h, valeur_m = int(heures), int(minutes or "0")
    if valeur_h > 23 or valeur_m > 59:
        return Etat.IMPOSSIBLE
    return (valeur_h * 60 + valeur_m) * (1 if signe == "+" else -1)


def _exif(texte: str) -> Lue:
    if _EXIF_INCONNUE.fullmatch(texte):
        return Etat.NON_RENSEIGNEE
    trouve = _EXIF.fullmatch(texte)
    if trouve is None:
        return Etat.NON_RECONNUE
    annee, mois, jour, heure, minute, seconde = map(int, trouve.groups())
    return _intervalle((annee, mois, jour, heure, minute, seconde), None, None)


def _ecrite(trouve: re.Match[str] | None, fraction: bool) -> Lue:
    """Date d'une écriture PDF ou ISO 8601 : six champs, fraction, puis fuseau."""
    if trouve is None:
        return Etat.NON_RECONNUE
    groupes = trouve.groups()
    annee = int(groupes[0])  # le seul groupe obligatoire
    mois, jour, heure, minute, seconde = (_entier(g) for g in groupes[1:6])
    reste = groupes[6:] if not fraction else groupes[7:]
    decalage = _decalage(*reste)
    if isinstance(decalage, Etat):
        return decalage
    if heure is None:
        decalage = None  # une date sans heure couvre son jour dans n'importe quel fuseau
    champs: Champs = (annee, mois, jour, heure, minute, seconde)
    return _intervalle(champs, groupes[6] if fraction else None, decalage)


def _secondes_1904(valeur: Scalaire) -> Lue:
    if isinstance(valeur, bool) or not isinstance(valeur, int):
        return Etat.NON_RECONNUE
    if valeur == 0:
        return Etat.NON_RENSEIGNEE  # valeur des fichiers qui ne datent pas leur présentation
    debut = _EPOQUE_1904 + valeur * _US
    if valeur < 0 or debut >= _FIN:
        return Etat.NON_RECONNUE
    return Intervalle(debut, debut + _US)


@lru_cache(maxsize=4096, typed=True)  # typé : `True == 1` pour Python, pas ici
def lire(lecture: Lecture, valeur: Scalaire) -> Lue:
    """Date que désigne ``valeur`` dans l'écriture ``lecture``, ou ce qui empêche de la lire."""
    if lecture is Lecture.SECONDES_1904:
        return _secondes_1904(valeur)
    if not isinstance(valeur, str):
        return Etat.NON_RECONNUE
    match lecture:
        case Lecture.EXIF:
            return _exif(valeur)
        case Lecture.PDF:
            return _ecrite(_PDF.fullmatch(valeur), fraction=False)
        case _:  # Lecture.ISO8601, la seule autre valeur
            return _ecrite(_ISO8601.fullmatch(valeur), fraction=True)
