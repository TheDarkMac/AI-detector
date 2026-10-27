"""Tests de l'identification du format par le contenu (F-02, F-03, ES-07, T13).

Chaque échantillon est écrit dans un fichier temporaire et identifié comme le fait le
processus de travail : on vérifie les parties reconnues, leur plage et leur fin logique.
"""

import struct
from pathlib import Path

import pytest
from echantillons import (
    PDF,
    TRAME_MP3,
    archive,
    bloc_png,
    boite,
    docx,
    ebml,
    ftyp,
    id3,
    iso,
    jpeg,
    odt,
    page_ogg,
    png,
    riff,
    segment,
    trame_adts,
)

from voight_kampff import formats
from voight_kampff._travail import garde, identification
from voight_kampff._travail.fichier import Fichier
from voight_kampff._travail.identification import identifier
from voight_kampff.rapport.modele import NOMBRE_MAX_PARTIES

type Attendu = list[tuple[str, int, int, bool, bool]]
"""Format, début, longueur, fin connue, tronquée."""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def identifier_octets(tmp_path: Path, contenu: bytes) -> Attendu:
    chemin = tmp_path / "echantillon"
    chemin.write_bytes(contenu)
    with chemin.open("rb") as fichier:
        parties = identifier(Fichier(fichier.fileno()), len(contenu))
    return [
        (p.format, p.octets.debut, p.octets.longueur, p.fin_connue, p.tronquee) for p in parties
    ]


def entier(contenu: bytes, nature: str) -> Attendu:
    return [(nature, 0, len(contenu), True, False)]


def ouvert(contenu: bytes, nature: str) -> Attendu:
    """Fin logique non établie : structure non parcourue ou de taille inconnue."""
    return [(nature, 0, len(contenu), False, False)]


def tronque(contenu: bytes, nature: str) -> Attendu:
    """Structure interrompue avant sa fin : tronquée ou corrompue."""
    return [(nature, 0, len(contenu), False, True)]


J, P, D = jpeg(), png(), docx()
MP3 = TRAME_MP3 * 3
ADTS = trame_adts() * 3

CAS: list[tuple[str, bytes, Attendu]] = [
    # Images
    ("jpeg", J, entier(J, "jpeg")),
    ("jpeg-remplissage", J[:-2] + b"\xff\xff\xd9", entier(J[:-2] + b"\xff\xff\xd9", "jpeg")),
    (
        "jpeg-rst-et-marqueur-sans-longueur",
        b"\xff\xd8\xff\x01" + J[2:],
        entier(b"\xff\xd8\xff\x01" + J[2:], "jpeg"),
    ),
    ("jpeg-sans-eoi", J[:-2], tronque(J[:-2], "jpeg")),
    ("jpeg-ff-final", J[:-1], tronque(J[:-1], "jpeg")),
    ("jpeg-tronque-apres-sos", J[:26], tronque(J[:26], "jpeg")),
    (
        "jpeg-octet-hors-marqueur",
        b"\xff\xd8" + segment(0xE0, b"JFIF\x00") + b"\x00\x00",
        tronque(b"\xff\xd8" + segment(0xE0, b"JFIF\x00") + b"\x00\x00", "jpeg"),
    ),
    ("jpeg-soi-inattendu", b"\xff\xd8\xff\xd8", tronque(b"\xff\xd8\xff\xd8", "jpeg")),
    (
        "jpeg-longueur-invalide",
        b"\xff\xd8\xff\xe0\x00\x01",
        tronque(b"\xff\xd8\xff\xe0\x00\x01", "jpeg"),
    ),
    (
        "jpeg-entropie-longue",
        jpeg(b"\x01" * (1 << 20) + b"\xff\x00"),
        entier(jpeg(b"\x01" * (1 << 20) + b"\xff\x00"), "jpeg"),
    ),
    (
        "jpeg-ff-en-fin-de-bloc",
        jpeg(b"\x01" * ((1 << 20) - 27) + b"\xff\x00"),
        entier(jpeg(b"\x01" * ((1 << 20) - 27) + b"\xff\x00"), "jpeg"),
    ),
    ("png", P, entier(P, "png")),
    ("png-sans-iend", P[:-12], tronque(P[:-12], "png")),
    (
        "png-bloc-demesure",
        P[:8] + b"\xff\xff\xff\xffIHDR",
        tronque(P[:8] + b"\xff\xff\xff\xffIHDR", "png"),
    ),
    (
        "png-bloc-au-dela",
        P[:8] + b"\x00\x00\x10\x00IHDR",
        tronque(P[:8] + b"\x00\x00\x10\x00IHDR", "png"),
    ),
    ("gif", b"GIF89a" + b"\x00" * 10, ouvert(b"GIF89a" + b"\x00" * 10, "gif")),
    ("tiff", b"II*\x00" + b"\x00" * 8, ouvert(b"II*\x00" + b"\x00" * 8, "tiff")),
    (
        "bmp",
        b"BM" + struct.pack("<I", 30) + b"\x00" * 8 + struct.pack("<I", 40) + b"\x00" * 12,
        [("bmp", 0, 30, True, False)],
    ),
    (
        "bmp-taille-incoherente",
        b"BM" + struct.pack("<I", 999) + b"\x00" * 8 + struct.pack("<I", 40) + b"\x00" * 12,
        [("bmp", 0, 30, False, False)],
    ),
    ("bmp-entete-inconnue", b"BM" + b"\x00" * 12 + struct.pack("<I", 41) + b"\x00" * 12, []),
    ("bmp-reserve-non-nul", b"BM" + b"\x00" * 4 + b"\x01" + b"\x00" * 30, []),
    # Conteneurs
    ("wav", riff(b"WAVE"), entier(riff(b"WAVE"), "wav")),
    (
        "webp",
        riff(b"WEBP", b"VP8 \x00\x00\x00\x00"),
        entier(riff(b"WEBP", b"VP8 \x00\x00\x00\x00"), "webp"),
    ),
    ("avi", riff(b"AVI "), entier(riff(b"AVI "), "avi")),
    (
        "riff-bourrage",
        riff(b"WAVE", b"abc") + b"\x00",
        entier(riff(b"WAVE", b"abc") + b"\x00", "wav"),
    ),
    ("riff-sans-bourrage", riff(b"WAVE", b"abc"), entier(riff(b"WAVE", b"abc"), "wav")),
    ("riff-tronque", riff(b"WAVE")[:-2], tronque(riff(b"WAVE")[:-2], "wav")),
    ("riff-inconnu", riff(b"XXXX"), []),
    ("mp4", iso(b"isom", b"isom"), entier(iso(b"isom", b"isom"), "mp4")),
    ("mp4-par-compatible", iso(b"zzzz", b"mp42"), entier(iso(b"zzzz", b"mp42"), "mp4")),
    ("mov", iso(b"qt  "), entier(iso(b"qt  "), "mov")),
    ("mov-sans-ftyp", boite(b"moov", b"\x00" * 4), entier(boite(b"moov", b"\x00" * 4), "mov")),
    ("m4a", iso(b"M4A ", b"isom"), entier(iso(b"M4A ", b"isom"), "m4a")),
    ("heic", iso(b"heic", b"mif1"), entier(iso(b"heic", b"mif1"), "heic")),
    ("heic-par-mif1", iso(b"mif1", b"heic"), entier(iso(b"mif1", b"heic"), "heic")),
    ("avif", iso(b"avif"), entier(iso(b"avif"), "avif")),
    ("avif-par-mif1", iso(b"mif1", b"avif"), entier(iso(b"mif1", b"avif"), "avif")),
    ("heif", iso(b"mif1"), entier(iso(b"mif1"), "heif")),
    ("3gp", iso(b"3gp5"), entier(iso(b"3gp5"), "3gp")),
    ("ftyp-inconnu", iso(b"zzzz"), []),
    ("ftyp-trop-court", boite(b"ftyp", b"isom"), []),
    ("ftyp-tronque", ftyp(b"isom")[:-2], []),
    (
        "boites-puis-donnees",
        iso(b"isom") + b"\x00\x01\x02\x03\x04\x05\x06\x07",
        [("mp4", 0, len(iso(b"isom")), True, False)],
    ),
    (
        "boite-jusqu-a-la-fin",
        ftyp(b"isom") + b"\x00\x00\x00\x00mdat" + b"\x00" * 9,
        entier(ftyp(b"isom") + b"\x00\x00\x00\x00mdat" + b"\x00" * 9, "mp4"),
    ),
    (
        "boite-64-bits",
        ftyp(b"isom") + struct.pack(">I", 1) + b"mdat" + struct.pack(">Q", 20) + b"\x00" * 4,
        entier(
            ftyp(b"isom") + struct.pack(">I", 1) + b"mdat" + struct.pack(">Q", 20) + b"\x00" * 4,
            "mp4",
        ),
    ),
    (
        "boite-64-bits-tronquee",
        ftyp(b"isom") + struct.pack(">I", 1) + b"mdat",
        tronque(ftyp(b"isom") + struct.pack(">I", 1) + b"mdat", "mp4"),
    ),
    (
        "boite-trop-petite",
        ftyp(b"isom") + struct.pack(">I", 4) + b"mdat",
        tronque(ftyp(b"isom") + struct.pack(">I", 4) + b"mdat", "mp4"),
    ),
    ("boite-coupee", ftyp(b"isom") + b"\x00\x00", tronque(ftyp(b"isom") + b"\x00\x00", "mp4")),
    ("webm", ebml(b"webm"), entier(ebml(b"webm"), "webm")),
    ("matroska", ebml(b"matroska"), entier(ebml(b"matroska"), "matroska")),
    (
        "webm-segment-de-taille-inconnue",
        ebml(b"webm", b"\xff"),
        ouvert(ebml(b"webm", b"\xff"), "webm"),
    ),
    ("webm-segment-au-dela", ebml(b"webm", b"\x88"), tronque(ebml(b"webm", b"\x88"), "webm")),
    ("webm-sans-segment", ebml(b"webm")[:-9], tronque(ebml(b"webm")[:-9], "webm")),
    ("ebml-type-inconnu", ebml(b"autre"), []),
    ("ebml-taille-inconnue", b"\x1a\x45\xdf\xa3\xff" + b"\x00" * 8, []),
    ("ebml-vint-invalide", b"\x1a\x45\xdf\xa3\x00" + b"\x00" * 8, []),
    ("ebml-vint-coupe", b"\x1a\x45\xdf\xa3\x40", []),
    ("ebml-element-invalide", b"\x1a\x45\xdf\xa3\x82\x01\x00", []),
    ("ebml-identifiant-coupe", b"\x1a\x45\xdf\xa3\x84\x42", []),
    ("ebml-taille-d-element-inconnue", b"\x1a\x45\xdf\xa3\x84\x42\x82\xff\x00", []),
    ("ogg", page_ogg() * 2, entier(page_ogg() * 2, "ogg")),
    ("ogg-puis-donnees", page_ogg() + b"junk", [("ogg", 0, len(page_ogg()), True, False)]),
    ("ogg-page-coupee", page_ogg() + b"OggS\x00\x02", tronque(page_ogg() + b"OggS\x00\x02", "ogg")),
    ("ogg-segments-coupes", page_ogg()[:27], tronque(page_ogg()[:27], "ogg")),
    ("ogg-page-au-dela", page_ogg()[:-1], tronque(page_ogg()[:-1], "ogg")),
    # Audio en trames
    ("mp3", MP3, entier(MP3, "mp3")),
    ("mp3-une-trame-seule", TRAME_MP3, entier(TRAME_MP3, "mp3")),
    ("mp3-id3v1", MP3 + b"TAG" + b"\x00" * 125, entier(MP3 + b"TAG" + b"\x00" * 125, "mp3")),
    ("mp3-id3v1-coupe", MP3 + b"TAG", tronque(MP3 + b"TAG", "mp3")),
    ("mp3-derniere-trame-coupee", MP3[:-1], tronque(MP3[:-1], "mp3")),
    ("mp3-puis-donnees", MP3 + b"\x00" * 9, [("mp3", 0, len(MP3), True, False)]),
    (
        "mp3-mpeg2",
        (b"\xff\xf3\x90\x00" + b"\x00" * 257) * 2,
        entier((b"\xff\xf3\x90\x00" + b"\x00" * 257) * 2, "mp3"),
    ),
    ("mpeg-couche-ii", b"\xff\xfd\x90\x00" + b"\x00" * 500, []),
    ("aac", ADTS, entier(ADTS, "aac")),
    ("adts-longueur-nulle", b"\xff\xf1\x50\x80\x00\x00\xfc" * 3, []),
    ("adts-frequence-invalide", b"\xff\xf1\x7c\x80\x02\x00\xfc" + b"\x00" * 9, []),
    ("id3-mp3", id3(MP3), entier(id3(MP3), "mp3")),
    ("id3-pied-aac", id3(ADTS, pied=True), entier(id3(ADTS, pied=True), "aac")),
    ("id3-flac", id3(b"fLaC\x00\x00\x00\x22"), ouvert(id3(b"fLaC\x00\x00\x00\x22"), "flac")),
    ("id3-seul", id3(b"\x00" * 20), []),
    ("id3-version-inconnue", b"ID3\x09" + b"\x00" * 20, []),
    (
        "flac",
        b"fLaC\x00\x00\x00\x22" + b"\x00" * 34,
        ouvert(b"fLaC\x00\x00\x00\x22" + b"\x00" * 34, "flac"),
    ),
    ("flac-sans-streaminfo", b"fLaC\x01\x00\x00\x22" + b"\x00" * 34, []),
    # Documents et texte
    ("pdf", PDF, entier(PDF, "pdf")),
    ("pdf-sans-eof", PDF[:-7], tronque(PDF[:-7], "pdf")),
    ("pdf-blancs-finaux", PDF + b"\r\n \x00", entier(PDF + b"\r\n \x00", "pdf")),
    # Ni PDF ni rien d'autre : de l'ASCII, donc du texte brut.
    ("pdf-version-invalide", b"%PDF-x" + PDF[6:], entier(b"%PDF-x" + PDF[6:], "texte")),
    ("pdf-decale-invalide", b"bruit%PDF-x", entier(b"bruit%PDF-x", "texte")),
    (
        "pdf-long",
        PDF[:-7] + b"\x00" * (1 << 20) + b"%%EOF" + b"\x00" * (1 << 20),
        entier(PDF[:-7] + b"\x00" * (1 << 20) + b"%%EOF" + b"\x00" * (1 << 20), "pdf"),
    ),
    ("pdf-apres-du-bruit", b"bruit\x00" + PDF, [("pdf", 6, len(PDF), True, False)]),
    ("docx", D, entier(D, "docx")),
    ("odt", odt(), entier(odt(), "odt")),
    ("zip", archive(("a.txt", b"a")), entier(archive(("a.txt", b"a")), "zip")),
    ("zip-vide", archive(), entier(archive(), "zip")),
    (
        "zip-commentaire",
        archive(("a", b"a"), commentaire=b"PK\x05\x06!"),
        entier(archive(("a", b"a"), commentaire=b"PK\x05\x06!"), "zip"),
    ),
    (
        "mimetype-autre",
        archive(("mimetype", b"application/zip")),
        entier(archive(("mimetype", b"application/zip")), "zip"),
    ),
    ("texte-utf8", "Bonjour, été\t\r\n".encode(), entier("Bonjour, été\t\r\n".encode(), "texte")),
    ("texte-bom", "﻿Bonjour".encode(), entier("﻿Bonjour".encode(), "texte")),
    ("texte-utf16", "﻿Salut".encode("utf-16-le"), entier("﻿Salut".encode("utf-16-le"), "texte")),
    ("utf16-controle", "﻿a\x01".encode("utf-16-le"), []),
    ("utf16-impair", "﻿a".encode("utf-16-le") + b"\x00\xd8", []),
    ("utf8-invalide", b"caf\xe9", []),
    ("binaire", b"\x00\x01\x02", []),
    # Formats reconnus pour être nommés
    ("gzip", b"\x1f\x8b\x08\x00" + b"\x00" * 6, ouvert(b"\x1f\x8b\x08\x00" + b"\x00" * 6, "gzip")),
    ("7z", b"7z\xbc\xaf\x27\x1c" + b"\x00" * 4, ouvert(b"7z\xbc\xaf\x27\x1c" + b"\x00" * 4, "7z")),
    ("rar", b"Rar!\x1a\x07\x00", ouvert(b"Rar!\x1a\x07\x00", "rar")),
    ("elf", b"\x7fELF" + b"\x00" * 12, ouvert(b"\x7fELF" + b"\x00" * 12, "elf")),
    (
        "exe",
        b"MZ" + b"\x00" * 58 + struct.pack("<I", 64) + b"PE\x00\x00",
        ouvert(b"MZ" + b"\x00" * 58 + struct.pack("<I", 64) + b"PE\x00\x00", "exe"),
    ),
    ("mz-sans-pe", b"MZ" + b"\x00" * 70, []),
    ("mz-court", b"MZ\x00", []),
]


@pytest.mark.parametrize(("contenu", "attendu"), [pytest.param(c, a, id=i) for i, c, a in CAS])
def test_format_reconnu(tmp_path: Path, contenu: bytes, attendu: Attendu) -> None:
    assert identifier_octets(tmp_path, contenu) == attendu


# Fichiers polyglottes et données après la fin logique (ES-07)


def test_jpeg_suivi_d_une_archive(tmp_path: Path) -> None:
    assert identifier_octets(tmp_path, J + D) == [
        ("jpeg", 0, len(J), True, False),
        ("docx", len(J), len(D), True, False),
    ]


def test_archive_aux_positions_absolues(tmp_path: Path) -> None:
    # Comme ``zip -A`` : les positions du répertoire comptent depuis le début du fichier.
    ajustee = bytearray(J + D)
    position = ajustee.find(b"PK\x01\x02")
    while position != -1:
        decalage = struct.unpack_from("<I", ajustee, position + 42)[0]
        struct.pack_into("<I", ajustee, position + 42, decalage + len(J))
        position = ajustee.find(b"PK\x01\x02", position + 4)
    fin = ajustee.rfind(b"PK\x05\x06")
    struct.pack_into(
        "<I", ajustee, fin + 16, struct.unpack_from("<I", ajustee, fin + 16)[0] + len(J)
    )
    assert identifier_octets(tmp_path, bytes(ajustee))[1] == ("docx", len(J), len(D), True, False)


def test_jpeg_a_plusieurs_images(tmp_path: Path) -> None:
    # Images secondaires d'un JPEG MPF : deux parties de même format.
    assert identifier_octets(tmp_path, J + J) == [
        ("jpeg", 0, len(J), True, False),
        ("jpeg", len(J), len(J), True, False),
    ]


def test_pdf_dans_l_en_tete_d_un_jpeg(tmp_path: Path) -> None:
    hote = b"\xff\xd8" + segment(0xFE, PDF[:-6]) + b"\xff\xd9" + b"%%EOF\n"
    assert identifier_octets(tmp_path, hote) == [
        ("jpeg", 0, len(hote) - 6, True, False),
        ("pdf", 6, len(hote) - 6, True, False),
    ]


def test_donnees_apres_la_fin_non_reconnues(tmp_path: Path) -> None:
    assert identifier_octets(tmp_path, J + b"\x00\x01\x02") == [("jpeg", 0, len(J), True, False)]


def test_pdf_puis_archive(tmp_path: Path) -> None:
    assert identifier_octets(tmp_path, PDF + D) == [
        ("pdf", 0, len(PDF), True, False),
        ("docx", len(PDF), len(D), True, False),
    ]


def test_archive_dans_un_format_sans_fin_connue(tmp_path: Path) -> None:
    gif = b"GIF89a" + b"\x00" * 10
    assert identifier_octets(tmp_path, gif + D) == [
        ("gif", 0, len(gif) + len(D), False, False),
        ("docx", len(gif), len(D), True, False),
    ]


def test_nombre_de_parties_borne(tmp_path: Path) -> None:
    parties = identifier_octets(tmp_path, J * (NOMBRE_MAX_PARTIES + 3))
    assert len(parties) == NOMBRE_MAX_PARTIES


def test_texte_seulement_si_rien_d_autre(tmp_path: Path) -> None:
    # Un PDF entièrement ASCII est un PDF, pas du texte.
    assert identifier_octets(tmp_path, PDF) == entier(PDF, "pdf")


def fin_zip(entrees: int, taille: int, decalage: int, commentaire: int = 0) -> bytes:
    return b"PK\x05\x06" + struct.pack(
        "<HHHHIIH", 0, 0, entrees, entrees, taille, decalage, commentaire
    )


@pytest.mark.parametrize(
    "contenu",
    [
        pytest.param(b"x" * 30 + fin_zip(0, 0, 0, 0xFFFF), id="commentaire-au-dela"),
        pytest.param(b"x" * 30 + fin_zip(1, 0x100, 0x100), id="positions-impossibles"),
        pytest.param(b"x" * 30 + fin_zip(1, 0, 0), id="repertoire-absent"),
        pytest.param(b"x" * 30 + fin_zip(1, 0xFFFFFFFF, 0), id="zip64-en-tete-du-fichier"),
        pytest.param(b"x" * 100 + fin_zip(1, 0xFFFFFFFF, 0), id="zip64-sans-enregistrement"),
    ],
)
def test_faux_enregistrement_de_fin_zip(tmp_path: Path, contenu: bytes) -> None:
    assert identifier_octets(tmp_path, contenu) == []


def test_archive_dont_l_entree_locale_manque(tmp_path: Path) -> None:
    abimee = bytearray(D)
    abimee[0:4] = b"XXXX"
    assert identifier_octets(tmp_path, bytes(abimee)) == []


def test_zip64(tmp_path: Path) -> None:
    contenu = archive(("a.txt", b"a"))
    fin = contenu.rfind(b"PK\x05\x06")
    entrees, taille, decalage = struct.unpack_from("<HII", contenu, fin + 10)
    zip64 = (
        b"PK\x06\x06"
        + struct.pack("<QHHII", 44, 45, 45, 0, 0)
        + struct.pack("<QQQQ", entrees, entrees, taille, decalage)
    )
    localisateur = b"PK\x06\x07" + struct.pack("<IQI", 0, fin, 1)
    eocd = bytearray(contenu[fin:])
    struct.pack_into("<HHII", eocd, 8, 0xFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
    modifie = contenu[:fin] + zip64 + localisateur + bytes(eocd)
    assert identifier_octets(tmp_path, modifie) == entier(modifie, "zip")


def test_texte_raccourci_pendant_la_lecture(tmp_path: Path) -> None:
    chemin = tmp_path / "f"
    chemin.write_bytes(b"abc")
    with chemin.open("rb") as fichier:
        assert identification._texte(Fichier(fichier.fileno()), 10)


def test_identification_reservee_au_processus_de_travail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", False)
    with pytest.raises(garde.HorsProcessusDeTravail):
        identifier(Fichier(-1), 0)


def test_structure_trop_longue_fin_inconnue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(identification, "_PAS_MAX", 2)
    trois_blocs = P[:33] + bloc_png(b"tEXt", b"a") + P[33:]
    for contenu, nature in [
        (J, "jpeg"),
        (trois_blocs, "png"),
        (iso(b"isom") + boite(b"free"), "mp4"),
        (page_ogg() * 3, "ogg"),
        (MP3, "mp3"),
    ]:
        assert identifier_octets(tmp_path, contenu) == ouvert(contenu, nature)


# Vocabulaire


def test_chaque_format_a_ses_extensions() -> None:
    assert set(formats.EXTENSIONS) == formats.FORMATS
    assert formats.PERIMETRE.isdisjoint(formats.HORS_PERIMETRE)
    assert all(formats.EXTENSIONS[nature] for nature in formats.FORMATS)


def test_vue_lit_au_dela_du_cache(tmp_path: Path) -> None:
    chemin = tmp_path / "f"
    chemin.write_bytes(bytes(range(256)) * 16384)
    with chemin.open("rb") as fichier:
        vue = identification._Vue(Fichier(fichier.fileno()), 0, 1 << 22)
        assert vue.octets(0, (1 << 20) + 1)[-1] == 0
        assert vue.octets(-1, 4) == b""
        assert vue.octets(5, 0) == b""
