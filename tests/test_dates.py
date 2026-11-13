"""Lecture des dates des métadonnées : écritures, intervalles, ordre certain (T23, ADR-0148)."""

from datetime import UTC, datetime, timedelta

import pytest

from voight_kampff._dates import Etat, Intervalle, Lecture, lire
from voight_kampff.rapport.modele import Scalaire

pytestmark = pytest.mark.exigence("F-13")

ORIGINE = datetime(1, 1, 1, tzinfo=UTC)
S = 1_000_000
H = 3600 * S


def instant(
    annee: int, mois: int, jour: int, heure: int = 0, minute: int = 0, seconde: int = 0
) -> int:
    """Microsecondes depuis 0001-01-01T00:00Z d'un instant UTC."""
    utc = datetime(annee, mois, jour, heure, minute, seconde, tzinfo=UTC)
    return (utc - ORIGINE) // timedelta(microseconds=1)


@pytest.mark.parametrize(
    ("lecture", "valeur", "attendu"),
    [
        # EXIF : heure locale sans fuseau, de UTC-12 à UTC+14.
        (
            Lecture.EXIF,
            "2026:11:13 10:00:00",
            Intervalle(instant(2026, 11, 13, 10) - 14 * H, instant(2026, 11, 13, 10) + S + 12 * H),
        ),
        (
            Lecture.EXIF,
            "2024:02:29 00:00:00",
            Intervalle(instant(2024, 2, 29) - 14 * H, instant(2024, 2, 29) + S + 12 * H),
        ),
        (Lecture.EXIF, "2026:02:29 10:00:00", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "2026:13:01 10:00:00", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "2026:00:10 10:00:00", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "2026:04:31 10:00:00", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "2026:11:13 25:00:00", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "2026:11:13 10:60:00", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "2026:11:13 10:00:61", Etat.IMPOSSIBLE),
        # Seconde intercalaire, fin du jour : permises.
        (
            Lecture.EXIF,
            "2016:12:31 23:59:60",
            Intervalle(instant(2017, 1, 1) - 14 * H, instant(2017, 1, 1) + S + 12 * H),
        ),
        (
            Lecture.EXIF,
            "2026:11:13 24:00:00",
            Intervalle(instant(2026, 11, 14) - 14 * H, instant(2026, 11, 14) + S + 12 * H),
        ),
        (Lecture.EXIF, "2026:11:13 24:00:01", Etat.IMPOSSIBLE),
        (Lecture.EXIF, "    :  :     :  :  ", Etat.NON_RENSEIGNEE),
        (Lecture.EXIF, "0000:00:00 00:00:00", Etat.NON_RENSEIGNEE),
        (Lecture.EXIF, "0000:01:01 10:00:00", Etat.NON_RECONNUE),
        (Lecture.EXIF, "2026-11-13 10:00:00", Etat.NON_RECONNUE),
        (Lecture.EXIF, "2026:11:13", Etat.NON_RECONNUE),
        (Lecture.EXIF, "2026:11:13 10:00:00Z", Etat.NON_RECONNUE),
        (Lecture.EXIF, 20261113, Etat.NON_RECONNUE),
        # PDF : préfixe facultatif, champs finaux facultatifs, fuseau facultatif.
        (
            Lecture.PDF,
            "D:20261113100000+01'00'",
            Intervalle(instant(2026, 11, 13, 9), instant(2026, 11, 13, 9) + S),
        ),
        (
            Lecture.PDF,
            "D:20261113100000+01'00",
            Intervalle(instant(2026, 11, 13, 9), instant(2026, 11, 13, 9) + S),
        ),
        (
            Lecture.PDF,
            "D:20261113100000+0100",
            Intervalle(instant(2026, 11, 13, 9), instant(2026, 11, 13, 9) + S),
        ),
        (
            Lecture.PDF,
            "D:20261113100000-05",
            Intervalle(instant(2026, 11, 13, 15), instant(2026, 11, 13, 15) + S),
        ),
        (
            Lecture.PDF,
            "20261113100000Z",
            Intervalle(instant(2026, 11, 13, 10), instant(2026, 11, 13, 10) + S),
        ),
        (
            Lecture.PDF,
            "D:20261113100000Z00'00'",
            Intervalle(instant(2026, 11, 13, 10), instant(2026, 11, 13, 10) + S),
        ),
        (
            Lecture.PDF,
            "D:2026111310Z",
            Intervalle(instant(2026, 11, 13, 10), instant(2026, 11, 13, 11)),
        ),
        (
            Lecture.PDF,
            "D:202611131005Z",
            Intervalle(instant(2026, 11, 13, 10, 5), instant(2026, 11, 13, 10, 6)),
        ),
        (
            Lecture.PDF,
            "D:20261113",
            Intervalle(instant(2026, 11, 13) - 14 * H, instant(2026, 11, 14) + 12 * H),
        ),
        (
            Lecture.PDF,
            "D:202611",
            Intervalle(instant(2026, 11, 1) - 14 * H, instant(2026, 12, 1) + 12 * H),
        ),
        (
            Lecture.PDF,
            "D:202612",
            Intervalle(instant(2026, 12, 1) - 14 * H, instant(2027, 1, 1) + 12 * H),
        ),
        (
            Lecture.PDF,
            "D:2026",
            Intervalle(instant(2026, 1, 1) - 14 * H, instant(2027, 1, 1) + 12 * H),
        ),
        (
            Lecture.PDF,
            "D:9999",
            Intervalle(instant(9999, 1, 1) - 14 * H, instant(9999, 12, 31) + 24 * H + 12 * H),
        ),
        (
            Lecture.PDF,
            "D:999912",
            Intervalle(instant(9999, 12, 1) - 14 * H, instant(9999, 12, 31) + 24 * H + 12 * H),
        ),
        (
            Lecture.PDF,
            "D:20261113100000",
            Intervalle(instant(2026, 11, 13, 10) - 14 * H, instant(2026, 11, 13, 10) + S + 12 * H),
        ),
        (Lecture.PDF, "D:20261131", Etat.IMPOSSIBLE),
        (Lecture.PDF, "D:20261113100000+24'00'", Etat.IMPOSSIBLE),
        (Lecture.PDF, "D:20261113100000+01'60'", Etat.IMPOSSIBLE),
        (Lecture.PDF, "D:191261113100000", Etat.NON_RECONNUE),  # « an 19126 » d'anciens logiciels
        (Lecture.PDF, "D:2026-11-13", Etat.NON_RECONNUE),
        (Lecture.PDF, "", Etat.NON_RECONNUE),
        # ISO 8601 : XMP, W3CDTF, xsd:dateTime.
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00Z",
            Intervalle(instant(2026, 11, 13, 10), instant(2026, 11, 13, 10) + S),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00+02:00",
            Intervalle(instant(2026, 11, 13, 8), instant(2026, 11, 13, 8) + S),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00-0230",
            Intervalle(instant(2026, 11, 13, 12, 30), instant(2026, 11, 13, 12, 30) + S),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T10:00Z",
            Intervalle(instant(2026, 11, 13, 10), instant(2026, 11, 13, 10, 1)),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00.5Z",
            Intervalle(instant(2026, 11, 13, 10) + S // 2, instant(2026, 11, 13, 10) + 6 * S // 10),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00,25Z",
            Intervalle(
                instant(2026, 11, 13, 10) + S // 4, instant(2026, 11, 13, 10) + 26 * S // 100
            ),
        ),
        # Au-delà de la microseconde, la fraction est coupée et l'intervalle la couvre.
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00.123456789Z",
            Intervalle(instant(2026, 11, 13, 10) + 123456, instant(2026, 11, 13, 10) + 123457),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T10:00:00",
            Intervalle(instant(2026, 11, 13, 10) - 14 * H, instant(2026, 11, 13, 10) + S + 12 * H),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13",
            Intervalle(instant(2026, 11, 13) - 14 * H, instant(2026, 11, 14) + 12 * H),
        ),
        (
            Lecture.ISO8601,
            "2026-11",
            Intervalle(instant(2026, 11, 1) - 14 * H, instant(2026, 12, 1) + 12 * H),
        ),
        (
            Lecture.ISO8601,
            "2026",
            Intervalle(instant(2026, 1, 1) - 14 * H, instant(2027, 1, 1) + 12 * H),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T24:00:00Z",
            Intervalle(instant(2026, 11, 14), instant(2026, 11, 14) + S),
        ),
        (
            Lecture.ISO8601,
            "2026-11-13T24:00:00.0Z",
            Intervalle(instant(2026, 11, 14), instant(2026, 11, 14) + S // 10),
        ),
        (Lecture.ISO8601, "2026-11-13T24:00:00.1Z", Etat.IMPOSSIBLE),
        (Lecture.ISO8601, "2026-02-30T10:00:00Z", Etat.IMPOSSIBLE),
        (Lecture.ISO8601, "2026-11-13T10:00:00+25:00", Etat.IMPOSSIBLE),
        (Lecture.ISO8601, "2026-11-13T10:00:00+01:75", Etat.IMPOSSIBLE),
        (Lecture.ISO8601, "2026-11-13 10:00:00", Etat.NON_RECONNUE),
        (Lecture.ISO8601, "2026-11-13Z", Etat.NON_RECONNUE),
        (Lecture.ISO8601, "2026-11-13T10", Etat.NON_RECONNUE),
        (Lecture.ISO8601, "13/11/2026", Etat.NON_RECONNUE),
        (Lecture.ISO8601, "0000-01-01", Etat.NON_RECONNUE),
        (Lecture.ISO8601, True, Etat.NON_RECONNUE),
        # mvhd : secondes depuis 1904 en UTC ; 0, date non renseignée.
        (
            Lecture.SECONDES_1904,
            1,
            Intervalle(instant(1904, 1, 1, 0, 0, 1), instant(1904, 1, 1, 0, 0, 2)),
        ),
        (
            Lecture.SECONDES_1904,
            3_846_000_000,
            Intervalle(
                instant(1904, 1, 1) + 3_846_000_000 * S, instant(1904, 1, 1) + 3_846_000_001 * S
            ),
        ),
        (Lecture.SECONDES_1904, 0, Etat.NON_RENSEIGNEE),
        (Lecture.SECONDES_1904, -1, Etat.NON_RECONNUE),
        (Lecture.SECONDES_1904, 2**63 - 1, Etat.NON_RECONNUE),
        (Lecture.SECONDES_1904, str(2**64 - 1), Etat.NON_RECONNUE),
        (Lecture.SECONDES_1904, 1.5, Etat.NON_RECONNUE),
        (Lecture.SECONDES_1904, True, Etat.NON_RECONNUE),
    ],
)
def test_lecture(lecture: Lecture, valeur: Scalaire, attendu: Intervalle | Etat) -> None:
    assert lire(lecture, valeur) == attendu


def test_booleen_lu_a_part_d_un_entier() -> None:
    # Python tient True == 1 : le cache de la lecture les distingue (ADR-0089).
    assert isinstance(lire(Lecture.SECONDES_1904, 1), Intervalle)
    assert lire(Lecture.SECONDES_1904, True) is Etat.NON_RECONNUE
    assert isinstance(lire(Lecture.SECONDES_1904, 1), Intervalle)


@pytest.mark.parametrize(
    ("premiere", "seconde", "avant"),
    [
        # Deux heures sans fuseau : un ordre certain demande plus de 26 heures d'écart.
        ("2026:11:13 10:00:00", "2026:11:14 12:00:00", False),
        ("2026:11:13 10:00:00", "2026:11:14 12:00:01", True),
        ("2026:11:14 12:00:01", "2026:11:13 10:00:00", False),
        ("2026:11:13 10:00:00", "2026:11:13 10:00:00", False),
    ],
)
def test_ordre_certain_entre_deux_heures_sans_fuseau(
    premiere: str, seconde: str, avant: bool
) -> None:
    a, b = lire(Lecture.EXIF, premiere), lire(Lecture.EXIF, seconde)
    assert isinstance(a, Intervalle)
    assert isinstance(b, Intervalle)
    assert a.avant(b) is avant


def test_ordre_certain_entre_deux_heures_a_fuseau() -> None:
    a = lire(Lecture.ISO8601, "2026-11-13T10:00:00+01:00")
    b = lire(Lecture.ISO8601, "2026-11-13T09:00:01Z")
    c = lire(Lecture.ISO8601, "2026-11-13T09:00:00Z")
    assert isinstance(a, Intervalle)
    assert isinstance(b, Intervalle)
    assert isinstance(c, Intervalle)
    assert a.avant(b)
    assert not b.avant(a)
    assert not a.avant(c)
    assert not c.avant(a)
