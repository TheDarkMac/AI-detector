"""Règles de T23 : incohérences internes et absence de métadonnées (F-13, F-14, ADR-0147 à 0151).

Comme ``test_signatures.py`` : le module s'exécute sur un contexte réel, puis le contexte applique
les règles « moteur » du module ; une analyse complète, par le processus de travail, vérifie le
même chemin jusqu'au rapport.
"""

from pathlib import Path
from typing import Any

import pytest
from bureautique import core, docx_, meta, odt_
from echantillons import boite
from medias import bloc_flac, flac, mp3, mvhd, quicktime, texte_qt, wav, webm
from metadonnees import (
    Sous,
    app1_exif,
    app1_xmp,
    ascii_,
    jpeg_meta,
    nombres,
    pdf_info,
    png_meta,
    tiff,
    xmp,
)
from test_signatures import CATALOGUE, constats

from voight_kampff._regles import Application
from voight_kampff._travail import garde
from voight_kampff.analyse import analyser
from voight_kampff.rapport.modele import Categorie, Direction, Fondement

pytestmark = pytest.mark.exigence("F-13")

REGLES_T23 = tuple(
    regle for regle in CATALOGUE.regles if regle.categorie is Categorie.INFORMATION_NEUTRE
)
ABSENCES = tuple(regle for regle in REGLES_T23 if regle.gabarit.endswith(".absence"))

XMP_NS = 'xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmlns:tiff="http://ns.adobe.com/tiff/1.0/"'
DCTERMS = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def t23(module: str, contenu: bytes, format_: str) -> dict[str, dict[str, Any]]:
    return constats(module, contenu, format_, REGLES_T23)


def exif(*ifd0: Any, sous: tuple[Any, ...] = ()) -> bytes:
    """JPEG à EXIF : entrées d'IFD0, et du sous-répertoire EXIF s'il y en a."""
    entrees = (*ifd0, Sous(0x8769, sous)) if sous else ifd0
    return jpeg_meta(app1_exif(tiff(tuple(entrees))))


def dates_exif(modification: str, prise: str, numerisation: str = "2026:11:13 10:00:00") -> bytes:
    return exif(
        ascii_(0x0132, modification), sous=(ascii_(0x9003, prise), ascii_(0x9004, numerisation))
    )


def dimensions(largeur: int, hauteur: int, appareil: str | None = "Canon") -> bytes:
    marque = (ascii_(0x010F, appareil),) if appareil else ()
    return exif(*marque, sous=(nombres(0xA002, 4, largeur), nombres(0xA003, 3, hauteur)))


def xmp_jpeg(proprietes: str) -> bytes:
    return jpeg_meta(app1_xmp(xmp(proprietes, espaces=XMP_NS)))


def dates_xmp(creation: str, modification: str, metadonnees: str = "2026-12-31") -> bytes:
    return xmp_jpeg(
        f"<xmp:CreateDate>{creation}</xmp:CreateDate>"
        f"<xmp:ModifyDate>{modification}</xmp:ModifyDate>"
        f"<xmp:MetadataDate>{metadonnees}</xmp:MetadataDate>"
    )


def dates_pdf(creation: str, modification: str) -> bytes:
    return pdf_info(f"<</CreationDate({creation})/ModDate({modification})>>".encode())


def dates_docx(creation: str, modification: str) -> bytes:
    return docx_(
        core(
            f'<dcterms:created {DCTERMS} xsi:type="dcterms:W3CDTF">{creation}</dcterms:created>'
            f'<dcterms:modified {DCTERMS} xsi:type="dcterms:W3CDTF">{modification}'
            "</dcterms:modified>"
        )
    )


def dates_odt(creation: str, modification: str) -> bytes:
    return odt_(
        meta(
            f"<meta:creation-date>{creation}</meta:creation-date><dc:date>{modification}</dc:date>"
        )
    )


def presentation(creation: int, modification: int) -> bytes:
    """MP4 daté par ``mvhd``, avec un titre : ses balises ne sont pas absentes."""
    titre = boite(b"udta", texte_qt(b"\xa9nam", b"Titre"))
    return quicktime(mvhd(creation, modification), titre, majeure=b"isom")


GENERATEUR = "Stable Diffusion XL"
PRISE = "2026:11:20 10:00:00"
MODIFICATION = "2026:11:13 10:00:00"

# Un échantillon par règle : module, format, contenu, règle, paramètres attendus.
CAS = [
    # EXIF : dates impossibles, puis dans un ordre renversé (plus de 26 heures d'écart).
    (
        "exif",
        "jpeg",
        dates_exif("2026:02:30 10:00:00", "2026:01:01 10:00:00", "2026:01:01 10:00:00"),
        "R-EXIF-003",
        {"date": "2026:02:30 10:00:00"},
    ),
    (
        "exif",
        "jpeg",
        dates_exif(MODIFICATION, "2026:13:01 10:00:00", "2026:01:01 10:00:00"),
        "R-EXIF-004",
        {"date": "2026:13:01 10:00:00"},
    ),
    (
        "exif",
        "jpeg",
        dates_exif(MODIFICATION, "2026:01:01 10:00:00", "2026:11:13 25:00:00"),
        "R-EXIF-005",
        {"date": "2026:11:13 25:00:00"},
    ),
    (
        "exif",
        "jpeg",
        dates_exif(MODIFICATION, PRISE, "    :  :     :  :  "),
        "R-EXIF-006",
        {"prise": PRISE, "modification": MODIFICATION},
    ),
    (
        "exif",
        "jpeg",
        dates_exif(MODIFICATION, "2026:01:01 10:00:00", PRISE),
        "R-EXIF-007",
        {"numerisation": PRISE, "modification": MODIFICATION},
    ),
    (
        "exif",
        "jpeg",
        dates_exif("2026:12:31 10:00:00", PRISE, MODIFICATION),
        "R-EXIF-008",
        {"prise": PRISE, "numerisation": MODIFICATION},
    ),
    # Appareil et logiciel, appareil et dimensions.
    (
        "exif",
        "jpeg",
        exif(ascii_(0x010F, "Canon"), ascii_(0x0131, GENERATEUR)),
        "R-EXIF-009",
        {"appareil": "Canon", "logiciel": GENERATEUR},
    ),
    (
        "exif",
        "jpeg",
        dimensions(1024, 1024),
        "R-EXIF-010",
        {"appareil": "Canon", "largeur": 1024, "hauteur": 1024},
    ),
    (
        "exif",
        "jpeg",
        dimensions(1792, 1024),
        "R-EXIF-011",
        {"appareil": "Canon", "largeur": 1792, "hauteur": 1024},
    ),
    (
        "exif",
        "jpeg",
        dimensions(1024, 1536),
        "R-EXIF-012",
        {"appareil": "Canon", "largeur": 1024, "hauteur": 1536},
    ),
    # XMP.
    ("xmp", "jpeg", dates_xmp("2026-02-30", "2026-11-13"), "R-XMP-006", {"date": "2026-02-30"}),
    (
        "xmp",
        "jpeg",
        dates_xmp("2026-11-01", "2026-11-13T25:00:00Z"),
        "R-XMP-007",
        {"date": "2026-11-13T25:00:00Z"},
    ),
    (
        "xmp",
        "jpeg",
        dates_xmp("2026-11-01", "2026-11-13", "2026-11-31"),
        "R-XMP-008",
        {"date": "2026-11-31"},
    ),
    (
        "xmp",
        "jpeg",
        dates_xmp("2026-11-13T10:00:01+01:00", "2026-11-13T09:00:00Z"),
        "R-XMP-009",
        {"creation": "2026-11-13T10:00:01+01:00", "modification": "2026-11-13T09:00:00Z"},
    ),
    (
        "xmp",
        "jpeg",
        dates_xmp("2026-11-20", "2026-12-01", "2026-11-13"),
        "R-XMP-010",
        {"creation": "2026-11-20", "metadonnees": "2026-11-13"},
    ),
    (
        "xmp",
        "jpeg",
        xmp_jpeg(f"<tiff:Make>Canon</tiff:Make><xmp:CreatorTool>{GENERATEUR}</xmp:CreatorTool>"),
        "R-XMP-011",
        {"appareil": "Canon", "logiciel": GENERATEUR},
    ),
    # PDF.
    (
        "infopdf",
        "pdf",
        dates_pdf("D:20260230", "D:20261113"),
        "R-INFOPDF-003",
        {"date": "D:20260230"},
    ),
    (
        "infopdf",
        "pdf",
        dates_pdf("D:20261101", "D:20261113250000Z"),
        "R-INFOPDF-004",
        {"date": "D:20261113250000Z"},
    ),
    (
        "infopdf",
        "pdf",
        dates_pdf("D:20261113100000+01'00'", "D:20261113085959Z"),
        "R-INFOPDF-005",
        {"creation": "D:20261113100000+01'00'", "modification": "D:20261113085959Z"},
    ),
    # Documents.
    (
        "ooxml",
        "docx",
        dates_docx("2026-02-30T10:00:00Z", "2026-11-13T10:00:00Z"),
        "R-OOXML-002",
        {"date": "2026-02-30T10:00:00Z"},
    ),
    (
        "ooxml",
        "docx",
        dates_docx("2026-11-01T10:00:00Z", "2026-11-13T10:61:00Z"),
        "R-OOXML-003",
        {"date": "2026-11-13T10:61:00Z"},
    ),
    (
        "ooxml",
        "docx",
        dates_docx("2026-11-13T10:00:00Z", "2026-11-13T09:59:59Z"),
        "R-OOXML-004",
        {"creation": "2026-11-13T10:00:00Z", "modification": "2026-11-13T09:59:59Z"},
    ),
    (
        "odf",
        "odt",
        dates_odt("2026-02-29T10:00:00", "2026-11-13T10:00:00"),
        "R-ODF-002",
        {"date": "2026-02-29T10:00:00"},
    ),
    (
        "odf",
        "odt",
        dates_odt("2026-11-01T10:00:00", "2026-13-13T10:00:00"),
        "R-ODF-003",
        {"date": "2026-13-13T10:00:00"},
    ),
    (
        "odf",
        "odt",
        dates_odt("2026-11-20T10:00:00.123456789", "2026-11-13T10:00:00"),
        "R-ODF-004",
        {"creation": "2026-11-20T10:00:00.123456789", "modification": "2026-11-13T10:00:00"},
    ),
    # Vidéo.
    (
        "quicktime",
        "mp4",
        presentation(3_800_000_001, 3_800_000_000),
        "R-QUICKTIME-003",
        {"creation": 3_800_000_001, "modification": 3_800_000_000},
    ),
    # Absences (F-14).
    ("exif", "jpeg", jpeg_meta(), "R-EXIF-013", {}),
    ("xmp", "png", png_meta(), "R-XMP-012", {}),
    ("iptc", "jpeg", jpeg_meta(), "R-IPTC-002", {}),
    ("textepng", "png", png_meta(), "R-TEXTEPNG-006", {}),
    ("infopdf", "pdf", pdf_info(b"<<>>", trailer="/Root 1 0 R"), "R-INFOPDF-006", {}),
    ("id3", "mp3", mp3(), "R-ID3-002", {}),
    ("infowav", "wav", wav(), "R-INFOWAV-002", {}),
    ("vorbis", "flac", flac(bloc_flac(0, bytes(34), dernier=True)), "R-VORBIS-002", {}),
    ("quicktime", "m4a", quicktime(), "R-QUICKTIME-004", {}),
    ("matroska", "webm", webm(), "R-MATROSKA-003", {}),
    ("ooxml", "docx", docx_(), "R-OOXML-005", {}),
    ("odf", "odt", odt_(None), "R-ODF-005", {}),
]


@pytest.mark.parametrize(("module", "format_", "contenu", "regle", "parametres"), CAS)
def test_regle_appliquee(
    module: str, format_: str, contenu: bytes, regle: str, parametres: dict[str, Any]
) -> None:
    assert t23(module, contenu, format_) == {regle: parametres}


def test_chaque_regle_de_t23_est_eprouvee() -> None:
    assert {cas[3] for cas in CAS} == {regle.identifiant for regle in REGLES_T23}
    assert (len(REGLES_T23), len(ABSENCES)) == (38, 12)
    assert len(REGLES_T23) + 24 == len(CATALOGUE.regles)  # les 24 de T22 (test_signatures.py)


@pytest.mark.exigence("F-14", "ES-20")
def test_regles_de_t23_informations_neutres() -> None:
    # ADR-0149 et ADR-0151 : une incohérence ou une absence ne pointe vers aucune hypothèse.
    for regle in REGLES_T23:
        assert regle.application is Application.MOTEUR
        assert regle.direction is Direction.RIEN_DE_PARTICULIER
        assert (regle.niveau, regle.evaluation) == (None, None)
        attendu = (
            Fondement.VERIFICATION_DETERMINISTE if regle in ABSENCES else Fondement.DECLARATION
        )
        assert regle.fondement is attendu


@pytest.mark.exigence("F-14")
def test_une_absence_par_module_de_metadonnees() -> None:
    assert {regle.module for regle in ABSENCES} == {
        "exif", "xmp", "iptc", "textepng", "infopdf", "id3",
        "infowav", "vorbis", "quicktime", "matroska", "ooxml", "odf",
    }  # fmt: skip
    for regle in ABSENCES:
        (condition,) = regle.conditions
        assert (condition.observation, condition.egal) == (f"{regle.module}.present", False)


def test_appareil_et_generateur_selon_la_liste_de_t22() -> None:
    # ADR-0144 : la liste des générateurs est la même que celle des règles de T22.
    t22 = next(regle for regle in CATALOGUE.regles if regle.identifiant == "R-EXIF-001")
    for identifiant in ("R-EXIF-009", "R-XMP-011"):
        regle = next(regle for regle in REGLES_T23 if regle.identifiant == identifiant)
        assert regle.conditions[1].motif == t22.conditions[0].motif


@pytest.mark.parametrize(
    ("module", "format_", "contenu"),
    [
        # Dates dans l'ordre, ou trop proches pour un ordre certain sans fuseau.
        pytest.param("exif", "jpeg", dates_exif(PRISE, MODIFICATION), id="exif-dans-l-ordre"),
        pytest.param(
            "exif",
            "jpeg",
            dates_exif("2026:11:13 10:00:00", "2026:11:14 12:00:00", "2026:11:13 10:00:00"),
            id="exif-26-heures",
        ),
        pytest.param(
            "exif",
            "jpeg",
            dates_exif("    :  :     :  :  ", PRISE, "0000:00:00 00:00:00"),
            id="exif-inconnues",
        ),
        pytest.param(
            "exif",
            "jpeg",
            dates_exif("13/11/2026", PRISE, "2026-11-20"),
            id="exif-autres-ecritures",
        ),
        pytest.param(
            "xmp",
            "jpeg",
            dates_xmp("2026-11-13T10:00:00+01:00", "2026-11-13T09:00:00Z"),
            id="xmp-meme-instant",
        ),
        pytest.param(
            "xmp", "jpeg", dates_xmp("2026-11-13", "2026-11-13T00:00:00Z"), id="xmp-meme-jour"
        ),
        pytest.param("xmp", "jpeg", dates_xmp("2026", "2026-06-01", "2026-06-01"), id="xmp-annee"),
        pytest.param(
            "infopdf",
            "pdf",
            dates_pdf("D:20261113100000", "D:20261113000000Z"),
            id="pdf-sans-fuseau",
        ),
        pytest.param(
            "infopdf", "pdf", dates_pdf("D:2026-11-13", "D:20261101"), id="pdf-non-reconnue"
        ),
        pytest.param(
            "ooxml",
            "docx",
            dates_docx("2026-11-13T10:00:00Z", "2026-11-13T10:00:00Z"),
            id="ooxml-egales",
        ),
        pytest.param(
            "odf",
            "odt",
            dates_odt("2026-11-13T10:00:00", "2026-11-14T08:00:00"),
            id="odf-dans-l-ordre",
        ),
        pytest.param(
            "quicktime",
            "mp4",
            presentation(3_800_000_000, 0),
            id="mvhd-non-renseignee",
        ),
        # Appareil, logiciel et dimensions qui vont ensemble, ou sans appareil déclaré.
        pytest.param(
            "exif",
            "jpeg",
            exif(ascii_(0x010F, "Canon"), ascii_(0x0131, "Adobe Photoshop 25.0")),
            id="logiciel-ordinaire",
        ),
        pytest.param(
            "exif", "jpeg", exif(ascii_(0x0131, GENERATEUR)), id="generateur-sans-appareil"
        ),
        pytest.param("exif", "jpeg", dimensions(6000, 4000), id="dimensions-d-un-appareil"),
        pytest.param("exif", "jpeg", dimensions(1024, 768), id="dimensions-sans-liste"),
        pytest.param("exif", "jpeg", dimensions(1536, 1792), id="dimensions-croisees"),
        pytest.param(
            "exif", "jpeg", dimensions(1024, 1024, appareil=None), id="dimensions-sans-appareil"
        ),
    ],
)
def test_sans_incoherence_sans_constat(module: str, format_: str, contenu: bytes) -> None:
    assert t23(module, contenu, format_) == {}


def test_une_regle_un_constat_par_partie() -> None:
    # ADR-0089 : plusieurs dates impossibles ne donnent qu'un constat par règle, la première.
    contenu = exif(ascii_(0x0132, "2026:02:30 10:00:00"), ascii_(0x0132, "2026:02:31 10:00:00"))
    assert t23("exif", contenu, "jpeg") == {"R-EXIF-003": {"date": "2026:02:30 10:00:00"}}


def _informations(chemin: Path) -> dict[str, tuple[Categorie, str]]:
    resultat = analyser(chemin)
    return {
        constat.regle.identifiant: (constat.categorie, constat.module)
        for constat in resultat.constats
    }


@pytest.mark.exigence("F-14", "P-04")
def test_analyse_complete_d_un_jpeg_sans_metadonnees(tmp_path: Path) -> None:
    # F-14 : une image sans métadonnées porte des informations neutres, aucun indice.
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(jpeg_meta())
    neutre = Categorie.INFORMATION_NEUTRE
    assert _informations(chemin) == {
        "R-EXIF-013": (neutre, "exif"),
        "R-IPTC-002": (neutre, "iptc"),
        "R-XMP-012": (neutre, "xmp"),
    }


def test_analyse_complete_d_un_jpeg_incoherent(tmp_path: Path) -> None:
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(
        jpeg_meta(
            app1_exif(
                tiff(
                    (
                        ascii_(0x010F, "Canon"),
                        ascii_(0x0131, "Midjourney"),
                        ascii_(0x0132, MODIFICATION),
                        Sous(0x8769, (ascii_(0x9003, PRISE),)),
                    )
                )
            )
        )
    )
    neutre = Categorie.INFORMATION_NEUTRE
    assert _informations(chemin) == {
        "R-EXIF-001": (Categorie.INDICE, "exif"),  # T22 : le générateur nommé
        "R-EXIF-006": (neutre, "exif"),
        "R-EXIF-009": (neutre, "exif"),
        "R-IPTC-002": (neutre, "iptc"),
        "R-XMP-012": (neutre, "xmp"),
    }
