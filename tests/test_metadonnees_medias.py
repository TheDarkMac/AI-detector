"""Balises des conteneurs audio et vidéo : modules ``id3``, ``infowav``, ``vorbis``,
``quicktime``, ``matroska`` et ``xmp`` (T21, complément audio et vidéo).

Décisions : ADR-0130 (découpage), ADR-0131 (modules et lecteurs), ADR-0132 (emplacements),
ADR-0133 (noms et valeurs), ADR-0134 (XMP). Les échantillons sont construits par ``medias`` ;
ceux de l'oracle exiftool, écrits par ffmpeg, sont comparés dans ``test_oracle_exiftool``
(ADR-0135).
"""

import struct
import tempfile
import zlib

import pytest
from echantillons import TRAME_MP3, boite, ftyp, trame_adts
from medias import (
    bext,
    bloc_flac,
    bloc_wav,
    boite_pleine,
    cluster,
    commentaires,
    donnee,
    element,
    element_ilst,
    flac,
    id3v1,
    id3v2,
    info,
    libre,
    liste_info,
    meta_itunes,
    meta_mdta,
    mp3,
    mvhd,
    ogg,
    page_ogg,
    quicktime,
    simple,
    syncsafe,
    tag,
    tags,
    texte_ebml,
    texte_id3,
    texte_qt,
    trame_id3,
    wav,
    webm,
)
from metadonnees import contexte, identifiantes, raisons, resultats, valeurs_de, xmp

from voight_kampff._travail import garde
from voight_kampff._travail.contexte import LimiteDepassee
from voight_kampff.modules._lecture import ebml
from voight_kampff.modules._lecture.conteneurs import Nature, relever

pytestmark = pytest.mark.exigence("F-10")

PARTIEL = "format_partiel"
TRONQUE = "fichier_tronque"
UUID_XMP = bytes.fromhex("be7acfcb97a942e89c71999491e3afac")
NOMINATIVE = "metadonnee_nominative"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


def lu(module: str, contenu: bytes, format_: str) -> dict[str, object]:
    return valeurs_de(resultats(module, contenu, format_))


# Absence (F-14)


@pytest.mark.exigence("F-14")
@pytest.mark.parametrize(
    ("module", "format_", "contenu"),
    [
        ("id3", "mp3", mp3()),
        ("id3", "aac", trame_adts() * 2),
        ("id3", "flac", flac()),
        ("id3", "wav", wav()),
        ("infowav", "wav", wav()),
        ("vorbis", "flac", flac()),
        ("vorbis", "ogg", ogg((1, [b"\x01vorbis" + bytes(23)]))),
        ("quicktime", "mp4", ftyp(b"isom") + boite(b"mdat")),
        ("matroska", "webm", webm()),
        ("xmp", "wav", wav()),
        ("xmp", "mov", quicktime(majeure=b"qt  ")),
    ],
)
def test_absence_observee(module: str, format_: str, contenu: bytes) -> None:
    lignes = resultats(module, contenu, format_)
    assert valeurs_de(lignes) == {f"{module}.present": False}
    assert raisons(lignes) == []


# ID3


def test_id3_v24_trames() -> None:
    contenu = mp3(
        id3v2(
            texte_id3(b"TIT2", "Titre"),
            texte_id3(b"TPE1", "Une", "Deux"),
            texte_id3(b"TSSE", "Lavf61.7.100", encodage=0),
            texte_id3(b"TCOM", "Compositrice", encodage=1),
            texte_id3(b"TALB", "Album", encodage=2),
            texte_id3(b"TXXX", "Logiciel", "Générateur"),
            texte_id3(b"TXXX", "", "sans description"),
            trame_id3(b"COMM", b"\x03fra\x00Bonjour"),
            trame_id3(b"COMM", b"\x03eng" + b"iTunNORM\x00 0001"),
            trame_id3(b"USLT", b"\x00fra\x00"),
            trame_id3(b"WOAR", b"https://exemple.org/\x00"),
            trame_id3(b"WCOM", b""),
            trame_id3(b"WXXX", b"\x01\xff\xfeS\x00i\x00\x00\x00https://site/"),
            trame_id3(b"WXXX", b"\x00\x00"),
            trame_id3(b"APIC", b"\x00image/png\x00\x03\x00PNG"),
            trame_id3(b"PRIV", b"XMP\x00<x/>"),
            trame_id3(b"TOFN", b"\x00prise.wav"),
            trame_id3(b"TDRC", b""),
            trame_id3(b"TPE2", b"\x00"),
            bourrage=20,
        )
    )
    lignes = resultats("id3", contenu, "mp3")
    assert valeurs_de(lignes) == {
        "id3.present": True,
        "id3.blocs": 1,
        "id3.version": "2.4.0",
        "id3.TIT2": "Titre",
        "id3.TPE1": ["Une", "Deux"],
        "id3.TSSE": "Lavf61.7.100",
        "id3.TCOM": "Compositrice",
        "id3.TALB": "Album",
        "id3.TXXX.Logiciel": "Générateur",
        "id3.TXXX": "sans description",
        "id3.COMM": "Bonjour",
        "id3.COMM.iTunNORM": " 0001",
        "id3.WOAR": "https://exemple.org/",
        "id3.WXXX.Si": "https://site/",
        "id3.APIC.taille": 16,
        "id3.PRIV.taille": 8,
        "id3.TOFN": "prise.wav",
    }
    assert raisons(lignes) == []
    assert identifiantes(lignes) == {
        "id3.TPE1": NOMINATIVE,
        "id3.TCOM": NOMINATIVE,
        "id3.TOFN": "nom_de_fichier",
    }
    [titre] = [o for o in lignes if o.get("observation", {}).get("nom") == "id3.TIT2"]
    assert titre["observation"]["localisation"]["chemin"] == "ID3v2 / trame TIT2"


def test_id3_utf16_sans_marque_et_gros_boutiste() -> None:
    trames = (
        trame_id3(b"TIT2", b"\x01" + "Petit".encode("utf-16-le")),
        trame_id3(b"TIT3", b"\x01\xfe\xff" + "Gros".encode("utf-16-be") + b"\x00\x00"),
        trame_id3(b"TIT1", b"\x01\xff\xfe" + "A".encode("utf-16-le") + b"\x00"),
    )
    valeurs = lu("id3", mp3(id3v2(*trames)), "mp3")
    assert valeurs["id3.TIT2"] == "Petit"
    assert valeurs["id3.TIT3"] == "Gros"
    assert valeurs["id3.TIT1"] == "A\ufffd"  # octet seul : caractère de remplacement


def test_id3_v23_desynchronisee_compressee_et_groupee() -> None:
    compresse = struct.pack(">I", 7) + zlib.compress(b"\x00\xffTexte")
    trames = (
        trame_id3(b"TIT2", compresse, version=3, format_=0x80),
        trame_id3(b"TPE1", b"\x05\x00Groupe", version=3, format_=0x20),
        trame_id3(b"TALB", b"\x00Chiffre", version=3, format_=0x40),
        trame_id3(b"TCON", struct.pack(">I", 3) + b"pas zlib", version=3, format_=0x80),
    )
    corps = b"".join(trames)
    desynchronise = corps.replace(b"\xff", b"\xff\x00")
    balise = b"ID3\x03\x00\x80" + syncsafe(len(desynchronise)) + desynchronise
    lignes = resultats("id3", mp3(balise), "mp3")
    valeurs = valeurs_de(lignes)
    assert valeurs["id3.version"] == "2.3.0"
    assert valeurs["id3.TIT2"] == "ÿTexte"
    assert valeurs["id3.TPE1"] == "Groupe"
    assert "id3.TALB" not in valeurs
    assert "id3.TCON" not in valeurs
    assert raisons(lignes) == [PARTIEL, PARTIEL]


def test_id3_v24_drapeaux_de_trame() -> None:
    texte = b"\x00Au\xff\x00dela"
    compresse = zlib.compress(b"\x00Compresse")
    trames = (
        trame_id3(b"TIT2", texte, format_=0x02),
        trame_id3(b"TIT3", b"G" + syncsafe(10) + compresse, format_=0x49),
        trame_id3(b"TALB", b"\x01" + b"\x00Chiffre", format_=0x04),
        trame_id3(b"TCON", b"\x00", format_=0x01),
    )
    lignes = resultats("id3", mp3(id3v2(*trames)), "mp3")
    valeurs = valeurs_de(lignes)
    assert valeurs["id3.TIT2"] == "Au\xffdela"
    assert valeurs["id3.TIT3"] == "Compresse"
    assert raisons(lignes) == [PARTIEL, PARTIEL]


def test_id3_v24_desynchronisee_en_entier_et_entete_etendu() -> None:
    trame = trame_id3(b"TIT2", b"\x00\xff\x00x")
    etendu = syncsafe(6) + b"\x01\x00"
    balise = b"ID3\x04\x00\xc0" + syncsafe(len(etendu + trame)) + etendu + trame
    assert lu("id3", mp3(balise), "mp3")["id3.TIT2"] == "\xffx"


def test_id3_v23_entete_etendu_et_pied_v24() -> None:
    trame = trame_id3(b"TIT2", b"\x00Texte", version=3)
    etendu = struct.pack(">I", 6) + b"\x00" * 6
    balise = b"ID3\x03\x00\x40" + syncsafe(len(etendu + trame)) + etendu + trame
    assert lu("id3", mp3(balise), "mp3")["id3.TIT2"] == "Texte"
    pied = id3v2(texte_id3(b"TIT2", "Pied"), drapeaux=0x10)
    assert lu("id3", mp3(pied), "mp3")["id3.TIT2"] == "Pied"


def test_id3_v22() -> None:
    trames = (
        texte_id3(b"TT2", "Ancien", version=2),
        texte_id3(b"TP1", "Artiste", version=2),
        trame_id3(b"COM", b"\x00eng\x00Note", version=2),
        trame_id3(b"PIC", b"\x00PNG\x00\x00data", version=2),
    )
    lignes = resultats("id3", mp3(id3v2(*trames, version=2)), "mp3")
    assert valeurs_de(lignes) == {
        "id3.present": True,
        "id3.blocs": 1,
        "id3.version": "2.2.0",
        "id3.TT2": "Ancien",
        "id3.TP1": "Artiste",
        "id3.COM": "Note",
        "id3.PIC.taille": 10,
    }
    assert identifiantes(lignes) == {"id3.TP1": NOMINATIVE}
    compresse = b"ID3\x02\x00\x40" + syncsafe(0)
    assert raisons(resultats("id3", mp3(compresse), "mp3")) == [PARTIEL]


@pytest.mark.parametrize(
    "balise",
    [
        pytest.param(id3v2(trame_id3(b"tit2", b"\x00x")), id="identifiant-invalide"),
        pytest.param(
            b"ID3\x04\x00\x00" + syncsafe(11) + b"TIT2\x80\x00\x00\x01\x00\x00x",
            id="taille-non-synchrosure",
        ),
        pytest.param(
            b"ID3\x04\x00\x00" + syncsafe(11) + b"TIT2" + syncsafe(5) + b"\x00\x00x",
            id="trame-debordante",
        ),
        pytest.param(b"ID3\x04\x00\x40" + syncsafe(2) + b"\x00\x00", id="etendu-court"),
        pytest.param(b"ID3\x03\x00\x40" + syncsafe(4) + b"\x00\x00\x00\x09", id="etendu-long"),
        pytest.param(id3v2(trame_id3(b"TIT2", b"\x07x")), id="encodage-inconnu"),
        pytest.param(id3v2(trame_id3(b"COMM", b"\x00en")), id="commentaire-court"),
        pytest.param(id3v2(trame_id3(b"TXXX", b"")), id="description-vide"),
        pytest.param(
            id3v2(trame_id3(b"TIT2", b"\x00x", format_=0x01)), id="longueur-de-donnees-coupee"
        ),
    ],
)
def test_id3_trames_illisibles(balise: bytes) -> None:
    assert raisons(resultats("id3", mp3(balise), "mp3")) == [PARTIEL]


def test_id3_texte_vide_ignore() -> None:
    assert lu("id3", mp3(id3v2(trame_id3(b"TIT2", b""))), "mp3") == {
        "id3.present": True,
        "id3.blocs": 1,
        "id3.version": "2.4.0",
    }


def test_id3v1() -> None:
    v1 = id3v1(b"Titre  ", b"Artiste", b"Album", b"2024", b"Note", piste=7, genre=12)
    lignes = resultats("id3", mp3(v1=v1), "mp3")
    assert valeurs_de(lignes) == {
        "id3.present": True,
        "id3.blocs": 1,
        "id3.v1.Title": "Titre",
        "id3.v1.Artist": "Artiste",
        "id3.v1.Album": "Album",
        "id3.v1.Year": "2024",
        "id3.v1.Comment": "Note",
        "id3.v1.Track": 7,
        "id3.v1.Genre": 12,
    }
    assert identifiantes(lignes) == {"id3.v1.Artist": NOMINATIVE}
    v10 = id3v1(b"\xe9t\xe9", commentaire=b"x" * 30)
    assert lu("id3", mp3(v1=v10), "mp3") == {
        "id3.present": True,
        "id3.blocs": 1,
        "id3.v1.Title": "été",
        "id3.v1.Comment": "x" * 30,
    }


def test_id3_v1_et_v2_du_mp3_aac_sans_v1() -> None:
    contenu = mp3(id3v2(texte_id3(b"TIT2", "A")), id3v2(texte_id3(b"TIT2", "B")), v1=id3v1(b"C"))
    lignes = resultats("id3", contenu, "mp3")
    assert valeurs_de(lignes)["id3.blocs"] == 3
    titres = [o["observation"]["valeur"] for o in lignes if "TIT2" in str(o) or "Title" in str(o)]
    assert titres == ["A", "B", "C"]
    aac = id3v2(texte_id3(b"TIT2", "D")) + trame_adts() * 2 + id3v1(b"E")
    assert lu("id3", aac, "aac")["id3.blocs"] == 1


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (b"ID3\x04\x00\x00\x00\x00", TRONQUE),
        (b"ID3\x05\x00\x00\x00\x00\x00\x00" + TRAME_MP3 * 2, PARTIEL),
        (b"ID3\x04\x00\x00\x00\x00\x80\x00" + TRAME_MP3 * 2, PARTIEL),
        (b"ID3\x04\x00\x00\x00\x7f\x7f\x7f", TRONQUE),
    ],
)
def test_id3_balise_interrompue(contenu: bytes, raison: str) -> None:
    lignes = resultats("id3", contenu, "mp3")
    assert raisons(lignes) == [raison]


def test_id3_wav_et_flac() -> None:
    balise = id3v2(texte_id3(b"TIT2", "Dans le WAV"))
    assert lu("id3", wav(bloc_wav(b"id3 ", balise)), "wav")["id3.TIT2"] == "Dans le WAV"
    assert lu("id3", wav(bloc_wav(b"ID3 ", balise)), "wav")["id3.TIT2"] == "Dans le WAV"
    assert lu("id3", flac(avant=balise), "flac")["id3.TIT2"] == "Dans le WAV"


# RIFF : liste INFO et bext


def test_infowav() -> None:
    contenu = wav(
        liste_info((b"ISFT", b"Lavf61.7.100"), (b"IART", b"Artiste"), (b"ICMT", b"\xe9t\xe9")),
        liste_info((b"INAM", b"Titre"), (b"IKEY", b"")),
        bloc_wav(b"LIST", b"adtlrien"),
        bext(
            description=b"Prise 3",
            originator=b"Enregistreur",
            reference=b"FRXYZ0123456789",
            date=b"2026-11-13",
            heure=b"10:20:30",
            temps=48000,
            umid=b"\x06\x0a+4" + b"\x00" * 12 + b"\x01",
            historique=b"A=PCM,F=48000,W=24,M=mono\r\n",
        ),
    )
    lignes = resultats("infowav", contenu, "wav")
    assert valeurs_de(lignes) == {
        "infowav.present": True,
        "infowav.blocs": 3,
        "infowav.ISFT": "Lavf61.7.100",
        "infowav.IART": "Artiste",
        "infowav.ICMT": "été",
        "infowav.INAM": "Titre",
        "infowav.bext.Description": "Prise 3",
        "infowav.bext.Originator": "Enregistreur",
        "infowav.bext.OriginatorReference": "FRXYZ0123456789",
        "infowav.bext.OriginationDate": "2026-11-13",
        "infowav.bext.OriginationTime": "10:20:30",
        "infowav.bext.TimeReference": 48000,
        "infowav.bext.Version": 1,
        "infowav.bext.UMID": "060A2B3400000000000000000000000001",
        "infowav.bext.CodingHistory": "A=PCM,F=48000,W=24,M=mono\r\n",
    }
    assert identifiantes(lignes) == {
        "infowav.IART": NOMINATIVE,
        "infowav.bext.Originator": NOMINATIVE,
        "infowav.bext.OriginatorReference": "numero_de_serie",
        "infowav.bext.UMID": "numero_de_serie",
    }
    assert raisons(lignes) == []


def test_infowav_bext_version_0_et_umid_nul() -> None:
    valeurs = lu("infowav", wav(bext(version=0, umid=b"\x01")), "wav")
    assert "infowav.bext.UMID" not in valeurs
    assert lu("infowav", wav(bext()), "wav")["infowav.bext.Version"] == 1


@pytest.mark.parametrize(
    "bloc",
    [
        pytest.param(bloc_wav(b"bext", b"\x00" * 100), id="bext-court"),
        pytest.param(bloc_wav(b"LIST", b"INFOISFT\x40\x00\x00\x00abc"), id="info-debordant"),
        pytest.param(bloc_wav(b"LIST", b"INFOISFT\x02\x00\x00\x00ab\x00\x00"), id="info-reste"),
    ],
)
def test_infowav_illisible(bloc: bytes) -> None:
    assert raisons(resultats("infowav", wav(bloc), "wav")) == [PARTIEL]


def test_wav_interrompu() -> None:
    coupe = wav(liste_info((b"ISFT", b"x")))
    coupe = coupe[:-6]
    coupe = coupe[:4] + struct.pack("<I", len(coupe) - 8 + 100) + coupe[8:]
    lignes = resultats("infowav", coupe, "wav")
    assert valeurs_de(lignes)["infowav.ISFT"] == "x"
    assert raisons(lignes) == [TRONQUE]
    assert raisons(resultats("infowav", b"RIFF\x04\x00", "wav")) == [TRONQUE]


# Vorbis : FLAC et Ogg


def test_vorbis_flac() -> None:
    bloc = commentaires(
        b"reference libFLAC 1.4.3",
        b"TITLE=Titre",
        b"artist=Une",
        b"Artist=Deux",
        b"ENCODER=Lavf61",
        b"METADATA_BLOCK_PICTURE=" + b"A" * 40,
        b"COVERART=AAAA",
        b"DESCRIPTION=\xc3\xa9t\xc3\xa9 \xff",
    )
    lignes = resultats("vorbis", flac(bloc_flac(1, b"\x00" * 8), bloc_flac(4, bloc)), "flac")
    assert valeurs_de(lignes) == {
        "vorbis.present": True,
        "vorbis.blocs": 1,
        "vorbis.vendor": "reference libFLAC 1.4.3",
        "vorbis.TITLE": "Titre",
        "vorbis.ARTIST": ["Une", "Deux"],
        "vorbis.ENCODER": "Lavf61",
        "vorbis.DESCRIPTION": "été �",
        "vorbis.METADATA-BLOCK-PICTURE.taille": 40,
        "vorbis.COVERART.taille": 4,
    }
    assert identifiantes(lignes) == {"vorbis.ARTIST": NOMINATIVE}
    [titre] = [o["observation"] for o in lignes if o["observation"]["nom"] == "vorbis.TITLE"]
    assert titre["localisation"]["chemin"] == "VORBIS_COMMENT"


@pytest.mark.parametrize(
    "bloc",
    [
        pytest.param(commentaires(b"v", b"SANS_EGAL", b"=vide", b"OK=1"), id="champ-mal-forme"),
        pytest.param(commentaires(b"v", b"OK=1")[:-2], id="champ-coupe"),
        pytest.param(struct.pack("<I", 1) + b"v", id="sans-nombre"),
        pytest.param(b"\xff\x00\x00\x00", id="fournisseur-debordant"),
    ],
)
def test_vorbis_illisible(bloc: bytes) -> None:
    lignes = resultats("vorbis", flac(bloc_flac(4, bloc)), "flac")
    assert raisons(lignes) == [PARTIEL]
    valeurs = valeurs_de(lignes)
    if "OK=1" in repr(bloc) and not bloc.endswith(b"O"):
        assert valeurs.get("vorbis.OK") == "1"


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (b"fLaC" + bloc_flac(0, b"\x00" * 34)[:3], TRONQUE),
        (b"fLaC" + bloc_flac(127, b""), PARTIEL),
        (b"fLaC" + bloc_flac(4, b"\x00" * 4)[:6], TRONQUE),
        (flac(avant=b"ID3\x04\x00\x00" + syncsafe(1) + b"\x00")[:10] + b"\x00RIEN", PARTIEL),
    ],
)
def test_flac_interrompu(contenu: bytes, raison: str) -> None:
    assert raisons(resultats("vorbis", contenu, "flac")) == [raison]


def test_vorbis_ogg_chaque_codec() -> None:
    contenu = ogg(
        (1, [b"\x01vorbis" + bytes(23), b"\x03vorbis" + commentaires(b"Xiph", b"A=1") + b"\x01"]),
        (2, [b"OpusHead" + bytes(11), b"OpusTags" + commentaires(b"libopus", b"B=2")]),
        (3, [b"\x80theora" + bytes(35), b"\x81theora" + commentaires(b"Xiph", b"C=3")]),
        (4, [b"Speex   " + bytes(72), commentaires(b"Speex", b"D=4")]),
        (
            5,
            [
                b"\x7fFLAC\x01\x00\x00\x01fLaC" + bloc_flac(0, bytes(34)),
                bloc_flac(4, commentaires(b"libFLAC", b"E=5")),
            ],
        ),
        (6, [b"fishead\x00" + bytes(56), b"autre"]),
        (7, [b"\x01vorbis" + bytes(23), b"\x05vorbis"]),
        (8, [b"\x7fFLAC\x01\x00\x00\x01fLaC", bloc_flac(1, b"\x00")]),
    )
    lignes = resultats("vorbis", contenu, "ogg")
    valeurs = valeurs_de(lignes)
    assert valeurs["vorbis.blocs"] == 5
    assert [valeurs[f"vorbis.{c}"] for c in "ABCDE"] == ["1", "2", "3", "4", "5"]
    chemins = sorted({o["observation"].get("localisation", {}).get("chemin", "") for o in lignes})
    assert "flux 00000002 / commentaires" in chemins
    assert raisons(lignes) == []


def test_vorbis_ogg_paquet_sur_plusieurs_pages() -> None:
    long = b"\x03vorbis" + commentaires(b"Xiph", b"TITLE=" + b"t" * 1000) + b"\x01"
    contenu = ogg((1, [b"\x01vorbis" + bytes(23), long, b"\x05vorbis", b"audio"]), par_page=255)
    lignes = resultats("vorbis", contenu, "ogg")
    assert valeurs_de(lignes)["vorbis.TITLE"] == "t" * 1000
    [titre] = [o["observation"] for o in lignes if o["observation"]["nom"] == "vorbis.TITLE"]
    assert "octets" not in titre["localisation"]  # plusieurs plages : pas d'étendue unique
    with tempfile.TemporaryFile() as fichier:
        [bloc] = relever(contexte(fichier, contenu, "ogg", "vorbis")).blocs
    assert len(bloc.etendues) == 5  # 1 + 1 000 + 15 octets, en tranches de 255
    une_page = ogg((1, [b"\x01vorbis" + bytes(23), long]))
    with tempfile.TemporaryFile() as fichier:
        [bloc] = relever(contexte(fichier, une_page, "ogg", "vorbis")).blocs
    assert len(bloc.etendues) == 1  # segments de la même page : une seule plage


def test_ogg_paquet_qui_finit_sur_une_page_pleine() -> None:
    premier = b"\x01vorbis" + bytes(248)  # 255 octets : un segment nul l'achève
    second = b"\x03vorbis" + commentaires(b"Xiph", b"A=1")
    pages = page_ogg(1, 0, [255], premier, type_=2) + page_ogg(
        1, 1, [0, len(second)], second, type_=1
    )
    assert lu("vorbis", pages, "ogg")["vorbis.A"] == "1"


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (b"OggS\x00\x02" + bytes(10), TRONQUE),
        (page_ogg(1, 0, [10], b"\x01vorbis" + bytes(3), type_=2)[:-1], TRONQUE),
        (page_ogg(1, 0, [10, 10], bytes(20), type_=2)[:28], TRONQUE),
        (page_ogg(1, 0, [10], b"\x01vorbis" + bytes(3), type_=2) + b"RIEN", PARTIEL),
        (page_ogg(1, 0, [10], b"\x01vorbis" + bytes(3), type_=3), PARTIEL),
        (page_ogg(1, 0, [255], b"\x01vorbis" + bytes(248), type_=2) * 2, PARTIEL),
    ],
)
def test_ogg_interrompu(contenu: bytes, raison: str) -> None:
    assert raisons(resultats("vorbis", contenu, "ogg")) == [raison]


def test_ogg_paquet_trop_grand(monkeypatch: pytest.MonkeyPatch) -> None:
    from voight_kampff.modules._lecture import conteneurs

    monkeypatch.setattr(conteneurs, "TAILLE_MAX_LECTURE", 300)
    contenu = ogg((1, [b"\x01vorbis" + bytes(400)]), par_page=255)
    assert raisons(resultats("vorbis", contenu, "ogg")) == [PARTIEL]


def test_ogg_paquet_vide_et_commentaires_vides() -> None:
    contenu = ogg((1, [b"", b"x"]), (2, [b"\x01vorbis" + bytes(23), b"\x03vorbis"]))
    assert lu("vorbis", contenu, "ogg") == {"vorbis.present": False}


# QuickTime : M4A, MP4, MOV


def test_quicktime_m4a_itunes() -> None:
    elements = (
        element_ilst(b"\xa9nam", donnee(1, b"Titre")),
        element_ilst(b"\xa9ART", donnee(1, b"Artiste")),
        element_ilst(b"\xa9too", donnee(1, b"Lavf61.7.100")),
        element_ilst(b"\xa9cmt", donnee(2, "été".encode("utf-16-be"))),
        element_ilst(b"\xa9lyr", donnee(3, "かな".encode("shift_jis"))),
        element_ilst(b"tmpo", donnee(21, b"\x00\x78")),
        element_ilst(b"plID", donnee(22, b"\xff" * 8)),
        element_ilst(b"rate", donnee(23, struct.pack(">f", 0.5))),
        element_ilst(b"rtng", donnee(24, struct.pack(">d", 2.25))),
        element_ilst(b"trkn", donnee(0, b"\x00\x00\x00\x03\x00\x0a\x00\x00")),
        element_ilst(b"covr", donnee(13, b"JPEG"), donnee(14, b"PNG")),
        element_ilst(b"keyw", donnee(1, b"a"), donnee(1, b"b"), donnee(1, b"")),
        element_ilst(b"desc", boite(b"autr", b"x")),
        libre(b"com.apple.iTunes", b"iTunSMPB", donnee(1, b" 00000000")),
    )
    contenu = quicktime(
        mvhd(3_800_000_000, 3_800_000_100),
        boite(b"trak", boite(b"udta", texte_qt(b"\xa9nam", b"Piste"))),
        boite(b"udta", meta_itunes(*elements)),
    )
    lignes = resultats("quicktime", contenu, "m4a")
    assert valeurs_de(lignes) == {
        "quicktime.present": True,
        "quicktime.blocs": 1,
        "quicktime.mvhd.CreationTime": 3_800_000_000,
        "quicktime.mvhd.ModificationTime": 3_800_000_100,
        "quicktime.ilst.-nam": "Titre",
        "quicktime.ilst.-ART": "Artiste",
        "quicktime.ilst.-too": "Lavf61.7.100",
        "quicktime.ilst.-cmt": "été",
        "quicktime.ilst.-lyr": "かな",
        "quicktime.ilst.tmpo": 120,
        "quicktime.ilst.plID": str(2**64 - 1),
        "quicktime.ilst.rate": 0.5,
        "quicktime.ilst.rtng": 2.25,
        "quicktime.ilst.trkn.taille": 8,
        "quicktime.ilst.covr.taille": 7,
        "quicktime.ilst.keyw": ["a", "b"],
        "quicktime.ilst.----.com-apple-iTunes.iTunSMPB": " 00000000",
    }
    assert identifiantes(lignes) == {"quicktime.ilst.-ART": NOMINATIVE}
    [date] = [o["observation"] for o in lignes if o["observation"]["nom"].endswith("CreationTime")]
    assert date["unite"] == "s depuis 1904-01-01 UTC"
    assert raisons(lignes) == []


def test_quicktime_udta_mov() -> None:
    udta = boite(
        b"udta",
        texte_qt(b"\xa9swr", b"Lavf61.7.100")
        + texte_qt(b"\xa9xyz", b"+48.8577+002.2950/")
        + texte_qt(b"\xa9nam", b"\x8e", langue=0)
        + texte_qt(b"\xa9des", b"\xfe\xff" + "Gros".encode("utf-16-be"))
        + texte_qt(b"\xa9inf", b"un", b"deux")
        + texte_qt(b"\xa9cmt", b"")
        + boite(b"\xa9too", donnee(1, b"Comme iTunes"))
        + boite_pleine(b"cprt", b"\x15\xc7Droits\x00")
        + boite_pleine(b"auth", b"\x15\xc7\xfe\xff" + "Moi".encode("utf-16-be") + b"\x00\x00")
        + boite(b"Xtra", b"\x00" * 12)
        + boite(b"XMP_", b"<x/>")
        + b"\x00\x00\x00\x00",
    )
    lignes = resultats("quicktime", quicktime(udta, majeure=b"qt  "), "mov")
    assert valeurs_de(lignes) == {
        "quicktime.present": True,
        "quicktime.blocs": 1,
        "quicktime.mvhd.CreationTime": 0,
        "quicktime.mvhd.ModificationTime": 0,
        "quicktime.udta.-swr": "Lavf61.7.100",
        "quicktime.udta.-xyz": "+48.8577+002.2950/",
        "quicktime.udta.-nam": "é",
        "quicktime.udta.-des": "Gros",
        "quicktime.udta.-inf": ["un", "deux"],
        "quicktime.udta.-too": "Comme iTunes",
        "quicktime.udta.cprt": "Droits",
        "quicktime.udta.auth": "Moi",
        "quicktime.udta.Xtra.taille": 12,
    }
    assert identifiantes(lignes) == {
        "quicktime.udta.-xyz": "gps",
        "quicktime.udta.cprt": NOMINATIVE,
        "quicktime.udta.auth": NOMINATIVE,
    }


def test_quicktime_mdta_et_mvhd_64_bits() -> None:
    cles = [
        b"com.apple.quicktime.software",
        b"com.apple.quicktime.location.ISO6709",
        b"com.apple.quicktime.author",
    ]
    meta = meta_mdta(
        cles,
        (1, donnee(1, b"17.1")),
        (2, donnee(1, b"+48.85+002.29/")),
        (3, donnee(1, b"Moi")),
        (9, donnee(1, b"?")),
    )
    contenu = quicktime(mvhd(2**64 - 1, 5, version=1), meta, majeure=b"qt  ")
    lignes = resultats("quicktime", contenu, "mov")
    assert valeurs_de(lignes) == {
        "quicktime.present": True,
        "quicktime.blocs": 1,
        "quicktime.mvhd.CreationTime": str(2**64 - 1),
        "quicktime.mvhd.ModificationTime": 5,
        "quicktime.mdta.com-apple-quicktime-software": "17.1",
        "quicktime.mdta.com-apple-quicktime-location-ISO6709": "+48.85+002.29/",
        "quicktime.mdta.com-apple-quicktime-author": "Moi",
    }
    assert identifiantes(lignes) == {
        "quicktime.mdta.com-apple-quicktime-location-ISO6709": "gps",
        "quicktime.mdta.com-apple-quicktime-author": NOMINATIVE,
    }
    assert raisons(lignes) == [PARTIEL]  # clé 9 absente de « keys »


def test_quicktime_meta_de_moov_en_boite_pleine_sans_gestionnaire() -> None:
    meta = boite_pleine(b"meta", boite(b"ilst", element_ilst(b"\xa9too", donnee(1, b"x"))))
    assert lu("quicktime", quicktime(meta), "mp4")["quicktime.ilst.-too"] == "x"


@pytest.mark.parametrize(
    "enfant",
    [
        pytest.param(boite(b"mvhd", b"\x00\x00"), id="mvhd-court"),
        pytest.param(
            boite(b"udta", boite(b"\xa9nam", b"\x00\x09\x15\xc7abc")), id="texte-debordant"
        ),
        pytest.param(boite(b"udta", boite(b"\xa9nam", b"\x00\x01\x15\xc7ab")), id="texte-reste"),
        pytest.param(boite(b"udta", boite_pleine(b"cprt", b"\x15")), id="iso-court"),
        pytest.param(
            boite(b"udta", meta_itunes(element_ilst(b"\xa9too", boite(b"data", b"\x00")))),
            id="data-court",
        ),
        pytest.param(boite(b"meta", boite(b"hdlr", b"\x00")[:-1] + b"\x00\x00"), id="meta-reste"),
    ],
)
def test_quicktime_illisible(enfant: bytes) -> None:
    assert raisons(resultats("quicktime", quicktime(enfant), "mp4")) == [PARTIEL]


@pytest.mark.parametrize(
    ("udta", "arret"),
    [
        pytest.param(b"\x00\x00\x00\x40abcd", TRONQUE, id="boite-debordante"),
        pytest.param(b"\x00\x00\x00\x01abcd\x00\x00", TRONQUE, id="taille-64-coupee"),
        pytest.param(b"\x00\x00\x00\x04abcd", PARTIEL, id="taille-trop-petite"),
        pytest.param(b"\x00\x00\x00\x08abcd\x01\x02", TRONQUE, id="reste"),
    ],
)
def test_quicktime_udta_mal_forme(udta: bytes, arret: str) -> None:
    """``udta`` est lu par ``quicktime`` et parcouru par le relevé, qui y cherche ``XMP_`` :
    chacun dit l'erreur, le second par l'arrêt du parcours."""
    lignes = resultats("quicktime", quicktime(boite(b"udta", udta)), "mp4")
    assert raisons(lignes) == [PARTIEL, arret]
    assert raisons(resultats("xmp", quicktime(boite(b"udta", udta)), "mp4")) == [arret]


def test_quicktime_tailles_particulieres() -> None:
    grande = (
        struct.pack(">I", 1)
        + b"\xa9nam"
        + struct.pack(">Q", 16 + 9)
        + struct.pack(">HH", 5, 0x55C4)
        + b"Titre"
    )
    jusqu_au_bout = struct.pack(">I", 0) + b"\xa9ART" + struct.pack(">HH", 3, 0x55C4) + b"Moi"
    valeurs = lu("quicktime", quicktime(boite(b"udta", grande + jusqu_au_bout)), "mp4")
    assert valeurs["quicktime.udta.-nam"] == "Titre"
    assert valeurs["quicktime.udta.-ART"] == "Moi"


def test_quicktime_premier_moov_seul_et_boites_vides() -> None:
    second = boite(b"moov", boite(b"udta", texte_qt(b"\xa9nam", b"Second")))
    contenu = quicktime(boite(b"udta"), boite(b"meta"), apres=second)
    lignes = resultats("quicktime", contenu, "mp4")
    assert valeurs_de(lignes) == {
        "quicktime.present": False,
        "quicktime.mvhd.CreationTime": 0,
        "quicktime.mvhd.ModificationTime": 0,
    }


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (ftyp(b"isom") + b"\x00\x00\x00\x40moov", TRONQUE),
        (ftyp(b"isom") + boite(b"moov", b"\x00\x00\x00\x40mvhd"), TRONQUE),
        (ftyp(b"isom") + boite(b"moov", boite(b"udta", b"\x00\x00\x00\x40XMP_")), TRONQUE),
    ],
)
def test_quicktime_interrompu(contenu: bytes, raison: str) -> None:
    assert raisons(resultats("quicktime", contenu, "mp4"))[-1:] == [raison]


# Matroska : WebM


def test_matroska_info_et_tags() -> None:
    contenu = webm(
        element(0x114D9B74, b"\x00" * 4),
        info(
            element(0x2AD7B1, b"\x0f\x42\x40"),
            texte_ebml(0x7BA9, "Titre"),
            texte_ebml(0x4D80, "Lavf61.7.100"),
            texte_ebml(0x5741, "Lavf61.7.100\x00\x00"),
            element(0x4461, (-(10**15)).to_bytes(8, "big", signed=True)),
            texte_ebml(0x7384, "prise.webm"),
            element(0x5741, b""),
        ),
        cluster(),
        tags(
            tag(
                simple("ENCODER", "Lavf61.7.100"),
                simple("ARTIST", "Moi", element(0x447A, b"fre")),
            ),
            tag(
                simple("ENCODER", "Lavc61 libvpx-vp9"),
                simple("DURATION", "00:00:01.000000000"),
                cibles=element(0x68CA, b"\x32") + element(0x63C5, b"\x01"),
            ),
            tag(simple("TITLE", "Chapitre"), cibles=element(0x63C4, b"\x07")),
            tag(simple("TITLE", "Global"), cibles=element(0x63C5, b"\x00")),
            tag(
                simple("ORIGINAL", None, simple("TITLE", "Imbriqué"), simple("COMPOSER", "Elle")),
                simple("VIGNETTE", None, binaire=b"\x89PNG"),
                simple("VIDE", ""),
            ),
            element(0xEC, b"\x00\x00"),
        ),
    )
    lignes = resultats("matroska", contenu, "webm")
    assert valeurs_de(lignes) == {
        "matroska.present": True,
        "matroska.blocs": 2,
        "matroska.Title": "Titre",
        "matroska.MuxingApp": "Lavf61.7.100",
        "matroska.WritingApp": "Lavf61.7.100",
        "matroska.DateUTC": -(10**15),
        "matroska.SegmentFilename": "prise.webm",
        "matroska.tag.ENCODER": "Lavf61.7.100",
        "matroska.tag.ARTIST": "Moi",
        "matroska.piste.ENCODER": "Lavc61 libvpx-vp9",
        "matroska.piste.DURATION": "00:00:01.000000000",
        "matroska.cible.TITLE": "Chapitre",
        "matroska.tag.TITLE": "Global",
        "matroska.tag.ORIGINAL.TITLE": "Imbriqué",
        "matroska.tag.ORIGINAL.COMPOSER": "Elle",
        "matroska.tag.VIGNETTE.taille": 4,
    }
    assert identifiantes(lignes) == {
        "matroska.SegmentFilename": "nom_de_fichier",
        "matroska.tag.ARTIST": NOMINATIVE,
        "matroska.tag.ORIGINAL.COMPOSER": NOMINATIVE,
    }
    [date] = [o["observation"] for o in lignes if o["observation"]["nom"] == "matroska.DateUTC"]
    assert date["unite"] == "ns depuis 2001-01-01 UTC"
    assert raisons(lignes) == []


def test_matroska_segment_et_cluster_de_taille_inconnue() -> None:
    contenu = webm(
        info(texte_ebml(0x4D80, "Chrome")),
        cluster(inconnu=True),
        cluster(inconnu=True),
        tags(tag(simple("ENCODER", "x"))),
        segment_inconnu=True,
    )
    valeurs = lu("matroska", contenu, "webm")
    assert valeurs["matroska.MuxingApp"] == "Chrome"
    assert valeurs["matroska.tag.ENCODER"] == "x"
    fin = webm(info(texte_ebml(0x4D80, "Chrome")), cluster(inconnu=True), segment_inconnu=True)
    assert lu("matroska", fin, "webm")["matroska.MuxingApp"] == "Chrome"


@pytest.mark.parametrize(
    "enfant",
    [
        pytest.param(info(element(0x4461, b"\x00" * 9)), id="date-trop-longue"),
        pytest.param(info(b"\x00\x81\x00"), id="identifiant-invalide"),
        pytest.param(info(texte_ebml(0x4D80, "x")[:-1] + b"\x7b\xa9\x01"), id="enfant-coupe"),
        pytest.param(info(b"\x7b\xa9\x01\xff\xff\xff\xff\xff\xff\xff"), id="enfant-inconnu"),
        pytest.param(info(b"\x7b\xa9\x89" + b"x" * 4), id="enfant-debordant"),
        pytest.param(tags(tag(element(0x67C8, texte_ebml(0x4487, "sans nom")))), id="sans-nom"),
        pytest.param(tags(tag(cibles=element(0x63C5, b"\x00" * 9))), id="cible-trop-longue"),
    ],
)
def test_matroska_illisible(enfant: bytes) -> None:
    assert raisons(resultats("matroska", webm(enfant), "webm")) == [PARTIEL]


@pytest.mark.parametrize(
    ("contenu", "raison"),
    [
        (b"\x1a\x45\xdf\xa3\x01\xff\xff\xff\xff\xff\xff\xff", PARTIEL),
        (webm()[:-5] + b"\x1f\x43\xb6\x75\x80", PARTIEL),
        (webm(info(texte_ebml(0x7BA9, "x")))[:-1], TRONQUE),
        (webm(element(0x1549A966, b"\x00"))[:-2], TRONQUE),
        (webm(b"\x1c\x53\xbb\x6b" + b"\x01\xff\xff\xff\xff\xff\xff\xff"), PARTIEL),
        (
            webm(
                cluster(inconnu=True) + b"\xa3\x01\xff\xff\xff\xff\xff\xff\xff",
                segment_inconnu=True,
            ),
            PARTIEL,
        ),
        (webm(b"\x00\x80"), PARTIEL),
        (webm(b"\x1f\x43\xb6"), TRONQUE),
    ],
)
def test_webm_interrompu(contenu: bytes, raison: str) -> None:
    assert raisons(resultats("matroska", contenu, "webm"))[-1:] == [raison]


def test_webm_segment_annonce_plus_long() -> None:
    contenu = webm(info(texte_ebml(0x7BA9, "Titre")))
    entete = contenu.index(b"\x18\x53\x80\x67")
    allonge = contenu[: entete + 4] + taille(len(contenu) - entete) + contenu[entete + 5 :]
    lignes = resultats("matroska", allonge, "webm")
    assert valeurs_de(lignes)["matroska.Title"] == "Titre"
    assert raisons(lignes) == [TRONQUE]


def taille(valeur: int) -> bytes:
    return bytes([0x80 | valeur])


def test_ebml_lecteur() -> None:
    assert ebml.entete(b"\x1a\x45\xdf\xa3\x84", 0) == (0x1A45DFA3, 5, 4)
    assert ebml.entete(b"\xa3\xff", 0) == (0xA3, 2, None)
    for octets, erreur in [
        (b"", ebml.Incomplet),
        (b"\x1a\x45", ebml.Incomplet),
        (b"\xa3", ebml.Incomplet),
        (b"\xa3\x40", ebml.Incomplet),
        (b"\x00\x80", ebml.Invalide),
        (b"\xa3\x00", ebml.Invalide),
    ]:
        with pytest.raises(erreur):
            ebml.entete(octets, 0)
    assert ebml.entier(b"") == 0
    assert ebml.signe(b"\xff") == -1


# XMP des fichiers audio et vidéo


def test_xmp_audio_et_video() -> None:
    paquet = xmp("<dc:format>video</dc:format>")
    mp4 = quicktime(
        majeure=b"isom", apres=boite(b"uuid", UUID_XMP + paquet) + boite(b"uuid", b"\x00" * 20)
    )
    assert lu("xmp", mp4, "mp4")["xmp.dc:format"] == "video"
    mov = quicktime(boite(b"udta", boite(b"XMP_", paquet) + boite(b"XMP_")), majeure=b"qt  ")
    assert lu("xmp", mov, "mov")["xmp.blocs"] == 1
    assert lu("xmp", wav(bloc_wav(b"_PMX", paquet)), "wav")["xmp.dc:format"] == "video"


def test_releve_par_nature() -> None:
    contenu = wav(
        liste_info((b"ISFT", b"x")), bext(), bloc_wav(b"id3 ", id3v2()), bloc_wav(b"_PMX", b"<x/>")
    )
    with tempfile.TemporaryFile() as fichier:
        releve = relever(contexte(fichier, contenu, "wav", "infowav"))
    assert [bloc.nature for bloc in releve.blocs] == [
        Nature.INFO_RIFF,
        Nature.BEXT,
        Nature.ID3V2,
        Nature.XMP,
    ]


# Budget (ES-03)


@pytest.mark.exigence("ES-03")
@pytest.mark.parametrize(
    ("module", "format_", "contenu"),
    [
        ("id3", "mp3", mp3(id3v2(*[texte_id3(b"TIT2", "x")] * 50))),
        ("vorbis", "flac", flac(bloc_flac(4, commentaires(b"v", *[b"A=1"] * 50)))),
        ("matroska", "webm", webm(tags(*[tag(simple("A", "1"))] * 50))),
        ("quicktime", "m4a", quicktime(boite(b"udta", texte_qt(b"\xa9nam", b"x") * 50))),
        ("infowav", "wav", wav(liste_info(*[(b"ISFT", b"x")] * 50))),
    ],
)
def test_objets_comptes(
    monkeypatch: pytest.MonkeyPatch, module: str, format_: str, contenu: bytes
) -> None:
    from voight_kampff._travail import contexte as module_contexte

    monkeypatch.setattr(module_contexte, "OBJETS_MAX", 20)
    with pytest.raises(LimiteDepassee):
        resultats(module, contenu, format_)


@pytest.mark.exigence("ES-03")
def test_matroska_imbrication_bornee() -> None:
    balise = simple("A", "1")
    for _ in range(80):
        balise = simple("A", None, balise)
    with pytest.raises(LimiteDepassee):
        resultats("matroska", webm(tags(tag(balise))), "webm")


@pytest.mark.exigence("ES-03")
def test_id3_bombe_de_decompression() -> None:
    bombe = zlib.compress(b"\x00" * (64 << 20), 9)
    trame = trame_id3(b"TIT2", struct.pack(">I", 64 << 20) + bombe, version=3, format_=0x80)
    balise = b"ID3\x03\x00\x00" + syncsafe(len(trame)) + trame
    with pytest.raises(LimiteDepassee):
        resultats("id3", mp3(balise), "mp3")
