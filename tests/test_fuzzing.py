"""Fuzzing des analyseurs (ES-19, ADR-0082), avec Hypothesis.

Quatre familles d'analyseurs lisent aujourd'hui des données hostiles :

- l'identification, dans le processus de travail, lit le fichier (ADR-0070) ;
- les modules de métadonnées (image, PDF, audio, vidéo, DOCX, ODT) et leurs lecteurs de
  structure (T20, T21, ADR-0114, ADR-0124, ADR-0131, ADR-0137), et le module ``image``, qui lit
  dimensions et tables de quantification (T24, ADR-0154) ;
- le décodage strict des lignes, dans le processus principal, lit ce qu'envoie un processus de
  travail peut-être compromis (ES-04) ;
- la réception, qui valide chaque message par le schéma puis par le modèle (ADR-0065).

Pour chacun, la propriété est la même : quelle que soit l'entrée, il rend un résultat valide
ou refuse par l'erreur prévue, jamais autre chose. Les entrées sont des octets quelconques et
des échantillons valides mutés (octets remplacés, insérés, supprimés, coupés, recollés).

Le profil ``defaut`` (``conftest.py``) tire 300 exemples d'une graine fixe ; ``VK_FUZZING=campagne``
lance une recherche longue (``CONTRIBUTING.md``).
"""

import importlib
import json
import tempfile
import zlib
from pathlib import Path
from typing import Any

import pytest
from bureautique import (
    TYPE_CORE as RELATION_CORE,
)
from bureautique import (
    Brute,
    app,
    archive_brute,
    core,
    custom,
    docx_,
    meta,
    odt_,
    relations,
)
from catalogues import CATALOGUE
from echantillons import (
    PDF,
    TRAME_MP3,
    archive,
    boite,
    docx,
    ebml,
    id3,
    iso,
    jpeg,
    odt,
    page_ogg,
    png,
    riff,
    trame_adts,
)
from hypothesis import given
from hypothesis import strategies as st
from medias import (
    bext,
    bloc_flac,
    bloc_wav,
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
from metadonnees import (
    Element,
    Sous,
    app1_etendu,
    app1_exif,
    app1_xmp,
    app13,
    ascii_,
    bloc_riff,
    contexte,
    dqt,
    fractions,
    heic_meta,
    jeu,
    jpeg_ijg,
    jpeg_image,
    jpeg_meta,
    pdf,
    pdf_info,
    png_meta,
    ressource,
    texte,
    texte_compresse,
    texte_international,
    tiff,
    vp8,
    vp8l,
    webp_image,
    webp_meta,
    xmp,
)

from voight_kampff import schemas
from voight_kampff._orchestration import travail
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff._protocole import MessageInvalide, decoder, encoder
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import LimiteDepassee
from voight_kampff._travail.fichier import Fichier
from voight_kampff._travail.identification import identifier
from voight_kampff.rapport.modele import Direction, Partie, RaisonNonMenee, verifier_parties

pytestmark = pytest.mark.exigence("ES-19", "NF-02", "NF-03")

ECHANTILLONS = (
    jpeg(),
    png(),
    PDF,
    riff(b"WAVE"),
    riff(b"WEBP", b"VP8 \x00\x00\x00\x00"),
    iso(b"isom", b"isom"),
    iso(b"heic", b"mif1"),
    ebml(b"webm"),
    page_ogg() + page_ogg(),
    id3(TRAME_MP3) + TRAME_MP3,
    trame_adts() * 3,
    docx(),
    odt(),
    archive(("a.txt", b"abc")),
    jpeg() + docx(),
    jpeg() + PDF,
    "Texte accentué\n".encode(),
    "﻿UTF-16".encode("utf-16"),
)
"""Un échantillon par famille de structure parcourue, et deux polyglottes."""


@pytest.fixture(autouse=True, scope="module")
def verrouille() -> None:
    garde.verrouiller()


@st.composite
def mutes(draw: st.DrawFn) -> bytes:
    """Échantillon valide transformé par quelques mutations."""
    octets = bytearray(draw(st.sampled_from(ECHANTILLONS)))
    for _ in range(draw(st.integers(0, 6))):
        position = draw(st.integers(0, len(octets)))
        match draw(st.sampled_from(("remplacer", "inserer", "supprimer", "couper", "coller"))):
            case "remplacer" if position < len(octets):
                octets[position] = draw(st.integers(0, 255))
            case "inserer":
                octets[position:position] = draw(st.binary(min_size=1, max_size=64))
            case "supprimer":
                del octets[position : position + draw(st.integers(1, 64))]
            case "couper":
                del octets[position:]
            case "coller":
                octets[position:position] = draw(st.sampled_from(ECHANTILLONS))
    return bytes(octets)


def identifier_octets(contenu: bytes) -> tuple[Partie, ...]:
    with tempfile.TemporaryFile() as fichier:
        fichier.write(contenu)
        fichier.flush()
        return identifier(Fichier(fichier.fileno()), len(contenu))


def verifier_identification(contenu: bytes) -> None:
    parties = identifier_octets(contenu)
    verifier_parties(parties, len(contenu))
    assert all(Partie.depuis_dict(partie.vers_dict()) == partie for partie in parties)
    assert identifier_octets(contenu) == parties  # même fichier, même identification


# Identification


@given(st.binary(max_size=4096))
def test_identification_octets_quelconques(contenu: bytes) -> None:
    verifier_identification(contenu)


@given(mutes())
def test_identification_echantillons_mutes(contenu: bytes) -> None:
    verifier_identification(contenu)


# Décodage strict des lignes


@given(st.binary(max_size=512))
def test_decodage_octets_quelconques(ligne: bytes) -> None:
    try:
        document = decoder(ligne)
    except MessageInvalide:
        return
    assert isinstance(document, dict)


JSON = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=8),
    lambda enfants: (
        st.lists(enfants, max_size=4) | st.dictionaries(st.text(max_size=8), enfants, max_size=4)
    ),
    max_leaves=8,
)


@given(st.dictionaries(st.text(max_size=12), JSON, max_size=6))
def test_decodage_aller_retour(document: dict[str, Any]) -> None:
    assert decoder(encoder(document)) == document


# Réception par le processus principal

MODULE = Manifeste(
    "alpha", "1.0", ("jpeg",), ("F-10",), (), "test", (Direction.RIEN_DE_PARTICULIER,)
)
MESSAGES: tuple[dict[str, Any], ...] = (
    {
        "type": "identification",
        "parties": [
            {
                "rang": 1,
                "format": "jpeg",
                "octets": {"debut": 0, "longueur": 100},
                "fin_connue": True,
                "tronquee": False,
            }
        ],
    },
    {
        "type": "observation",
        "observation": {
            "identifiant": "alpha/1",
            "module": "alpha",
            "nom": "taille",
            "valeur": 100,
            "partie": 1,
        },
    },
    {"type": "non_menee", "non_menee": {"raison": "format_partiel", "module": "alpha"}},
    {"type": "module", "module": "alpha", "partie": 1, "applicable": True},
    {"type": "versions", "dependances": [{"nom": "zlib", "version": "1.3"}]},
    {"type": "fin", "empreinte": "0" * 64},
)
"""Messages valides, dans l'ordre du protocole, que les mutations dérangent."""


@st.composite
def messages_mutes(draw: st.DrawFn) -> dict[str, Any]:
    message: dict[str, Any] = json.loads(json.dumps(draw(st.sampled_from(MESSAGES))))
    for _ in range(draw(st.integers(0, 3))):
        cible = message
        while True:  # descend dans un objet ou une liste du message
            cles = list(cible) if isinstance(cible, dict) else list(range(len(cible)))
            if not cles:
                break
            cle = draw(st.sampled_from(cles))
            if not isinstance(cible[cle], dict | list) or draw(st.booleans()):
                break
            cible = cible[cle]
        if cles:
            cible[cle] = draw(JSON)
    return message


@given(st.lists(messages_mutes(), min_size=1, max_size=5))
def test_reception_messages_mutes(suite: list[dict[str, Any]]) -> None:
    reception = travail._Reception((MODULE,), {r.identifiant: r for r in CATALOGUE.regles}, 100)
    for message in suite:
        try:
            schemas.valider("messages", decoder(encoder(message)))
        except (schemas.DocumentInvalide, MessageInvalide, ValueError):
            continue  # refusé avant le modèle : rien d'autre ne doit arriver
        try:
            reception._traiter(message)
        except travail._Interruption as interruption:
            raison = interruption.raison
            break
    else:
        raison = RaisonNonMenee.MESSAGE_INVALIDE
    assert raison is RaisonNonMenee.MESSAGE_INVALIDE  # seul refus possible d'un message
    reception.interrompre(raison)
    reception.resultat((MODULE,), set())  # le résultat se construit quoi qu'il soit arrivé


# Modules de métadonnées d'image (T20) et de PDF (T21)

_TIFF = tiff(
    (
        ascii_(0x010F, "Fabricant"),
        Sous(0x8769, (fractions(0x829A, (1, 250)), Sous(0xA005, (ascii_(0x0001, "R98"),)))),
        Sous(0x8825, (fractions(0x0002, (48, 1), (51, 1), (0, 1)),)),
    ),
    (ascii_(0x0131, "Logiciel"),),
)
_XMP = xmp(
    "<dc:creator><rdf:Seq><rdf:li>A</rdf:li></rdf:Seq></dc:creator>"
    '<dc:title><rdf:Alt><rdf:li xml:lang="x-default">T</rdf:li></rdf:Alt></dc:title>'
    '<dc:source rdf:parseType="Resource"><dc:x>1</dc:x></dc:source>'
)
_ORACLE = Path(__file__).parent / "donnees" / "metadonnees"
_INFO = (
    b"<</Title(Titre \\(entre parenth\\350ses\\))/Author<FEFF004A0065>/Trapped/False"
    b"/Pages 3/Liste[(a) 1]/Sous<</A(b)>>/Creator 2 0 R>>"
)
_PNG = "<</Predictor 12/Columns 7>>"
ECHANTILLONS_METADONNEES = (
    ("jpeg", jpeg_meta(app1_exif(_TIFF), app1_xmp(_XMP), app1_etendu(b"G" * 32, 4, 0, b"abcd"))),
    ("jpeg", jpeg_meta(app13(ressource(0x0404, jeu(1, 90, b"\x1b%G") + jeu(2, 25, b"mot"))))),
    (
        "png",
        png_meta(
            texte(b"parameters", b"Steps: 20"),
            texte_compresse(b"Comment", b"abc"),
            texte_international(b"XML:com.adobe.xmp", _XMP, compresse=True),
            texte_international(b"Title", b"t", langue=b"fr"),
        ),
    ),
    ("webp", webp_meta(bloc_riff(b"EXIF", _TIFF), bloc_riff(b"XMP ", _XMP))),
    # Structure d'une image (T24) : tables de quantification, en-têtes d'image.
    ("jpeg", jpeg_image(1600, 1200, tables=jpeg_ijg(80) + dqt((0, (2,) * 64), seize_bits=True))),
    ("webp", webp_image(vp8(1280, 720))),
    ("webp", webp_image(vp8l(1600, 900))),
    (
        "heic",
        heic_meta(
            Element(1, b"Exif", b"\x00" * 4 + _TIFF),
            Element(2, b"mime", _XMP, b"application/rdf+xml"),
        ),
    ),
    ("heic", heic_meta(Element(1, b"Exif", b"\x00" * 4 + _TIFF, morceaux=2), methode=1)),
    ("jpeg", (_ORACLE / "photo.jpg").read_bytes()),
    ("png", (_ORACLE / "image.png").read_bytes()),
    ("webp", (_ORACLE / "image.webp").read_bytes()),
    ("heic", (_ORACLE / "image.heic").read_bytes()),
    ("pdf", pdf_info(_INFO, xmp_=_XMP)),
    ("pdf", pdf_info(_INFO, flux_xref=True, flux_objets={9: (1, 3)}, predicteur=_PNG, png=True)),
    ("pdf", pdf({3: b"<</Title(Mise a jour)>>"}, "", base=pdf_info(_INFO), largeur=19)),
    ("pdf", (_ORACLE / "document.pdf").read_bytes()),
    ("pdf", (_ORACLE / "ghostscript.pdf").read_bytes()),
    ("pdf", (_ORACLE / "chiffre.pdf").read_bytes()),
    (
        "mp3",
        mp3(
            id3v2(
                texte_id3(b"TIT2", "Titre", encodage=1),
                texte_id3(b"TXXX", "desc", "valeur"),
                trame_id3(b"COMM", b"\x00fra\x00note"),
                trame_id3(b"APIC", b"\x00image/png\x00\x03\x00PNG"),
                trame_id3(b"TIT3", syncsafe(2) + zlib.compress(b"\x00x"), format_=0x09),
                bourrage=8,
            ),
            id3v2(texte_id3(b"TT2", "v2.2", version=2), version=2),
            v1=id3v1(b"Titre", b"Artiste", piste=1, genre=0),
        ),
    ),
    (
        "wav",
        wav(
            liste_info((b"ISFT", b"Lavf"), (b"IART", b"Moi")),
            bext(description=b"d", originator=b"o", umid=b"\x01", historique=b"A=PCM"),
            bloc_wav(b"id3 ", id3v2(texte_id3(b"TIT2", "t"))),
            bloc_wav(b"_PMX", _XMP),
        ),
    ),
    ("flac", flac(bloc_flac(4, commentaires(b"libFLAC", b"TITLE=t", b"ARTIST=a")))),
    (
        "ogg",
        ogg(
            (
                1,
                [
                    b"\x01vorbis" + bytes(23),
                    b"\x03vorbis" + commentaires(b"Xiph", b"A=" + b"1" * 400),
                ],
            ),
            (2, [b"OpusHead" + bytes(11), b"OpusTags" + commentaires(b"libopus", b"B=2")]),
            par_page=255,
        ),
    ),
    (
        "m4a",
        quicktime(
            mvhd(1, 2),
            boite(
                b"udta",
                texte_qt(b"\xa9swr", b"Lavf")
                + meta_itunes(
                    element_ilst(b"\xa9too", donnee(1, b"Lavf")),
                    element_ilst(b"tmpo", donnee(21, b"\x00\x78")),
                    libre(b"com.apple.iTunes", b"x", donnee(1, b"y")),
                )
                + boite(b"XMP_", _XMP),
            ),
            meta_mdta([b"com.apple.quicktime.software"], (1, donnee(1, b"17"))),
        ),
    ),
    (
        "webm",
        webm(
            info(texte_ebml(0x4D80, "Lavf"), element(0x4461, bytes(8))),
            cluster(inconnu=True),
            tags(tag(simple("ENCODER", "x", simple("A", "b")), cibles=element(0x63C5, b"\x01"))),
            segment_inconnu=True,
        ),
    ),
    *(
        (format_, (_ORACLE / nom).read_bytes())
        for nom, format_ in (
            ("son.wav", "wav"),
            ("son.mp3", "mp3"),
            ("son.aac", "aac"),
            ("son.m4a", "m4a"),
            ("son.flac", "flac"),
            ("son.ogg", "ogg"),
            ("son.opus", "ogg"),
            ("video.mp4", "mp4"),
            ("video.mov", "mov"),
            ("video.webm", "webm"),
            ("document.docx", "docx"),
            ("document.odt", "odt"),
        )
    ),
    (
        "docx",
        docx_(
            core("<dc:creator>A</dc:creator><cp:keywords>a<cp:value>b</cp:value></cp:keywords>"),
            app(
                "<TotalTime>3</TotalTime><ScaleCrop>false</ScaleCrop><TitlesOfParts>"
                "<vt:vector size='1' baseType='lpstr'><vt:lpstr>T</vt:lpstr></vt:vector>"
                "</TitlesOfParts><DigSig><vt:blob>AAEC</vt:blob></DigSig>"
            ),
            custom(("N", "<vt:r8>1.5</vt:r8>"), ("V", "<vt:variant><vt:i4>2</vt:i4></vt:variant>")),
        ),
    ),
    (
        "docx",
        archive_brute(
            Brute(b"_rels/.rels", relations((RELATION_CORE, "/docProps/c%6Fre.xml"))),
            Brute(b"docProps/core.xml", core("<dc:title>T</dc:title>"), methode=0),
            prefixe=b"MZ" + bytes(30),
            zip64=True,
        ),
    ),
    (
        "odt",
        odt_(
            meta(
                "<meta:generator>G</meta:generator><meta:keyword>a</meta:keyword>"
                '<meta:document-statistic meta:page-count="1"/>'
                '<meta:user-defined meta:name="N" meta:value-type="float">1</meta:user-defined>'
                '<meta:template xlink:href="http://exemple.invalid/" meta:date="2026"/>'
            )
        ),
    ),
)
"""Échantillons par format : toutes les familles, toutes les formes de conteneur lues."""
_MODULES: dict[str, tuple[str, ...]] = {
    "jpeg": ("exif", "xmp", "iptc", "image"),
    "png": ("exif", "xmp", "textepng", "image"),
    "webp": ("exif", "xmp", "image"),
    "heic": ("exif", "xmp"),
    "pdf": ("infopdf", "xmp"),
    "mp3": ("id3",),
    "aac": ("id3",),
    "wav": ("id3", "infowav", "xmp"),
    "flac": ("id3", "vorbis"),
    "ogg": ("vorbis",),
    "m4a": ("quicktime", "xmp"),
    "mp4": ("quicktime", "xmp"),
    "mov": ("quicktime", "xmp"),
    "webm": ("matroska",),
    "docx": ("ooxml",),
    "odt": ("odf",),
}


@st.composite
def metadonnees_mutees(draw: st.DrawFn) -> tuple[str, bytes]:
    format_, octets = draw(st.sampled_from(ECHANTILLONS_METADONNEES))
    tampon = bytearray(octets)
    for _ in range(draw(st.integers(0, 6))):
        position = draw(st.integers(0, len(tampon)))
        match draw(st.sampled_from(("remplacer", "inserer", "supprimer", "couper"))):
            case "remplacer" if position < len(tampon):
                tampon[position] = draw(st.integers(0, 255))
            case "inserer":
                tampon[position:position] = draw(st.binary(min_size=1, max_size=16))
            case "supprimer":
                del tampon[position : position + draw(st.integers(1, 16))]
            case "couper":
                del tampon[position:]
    return format_, bytes(tampon)


def executer_module(module: str, format_: str, contenu: bytes) -> tuple[bytes, ...] | None:
    """Lignes du module, chacune conforme au schéma des messages ; ``None`` si limite dépassée."""
    with tempfile.TemporaryFile() as fichier:
        c = contexte(fichier, contenu, format_, module)
        try:
            importlib.import_module(f"voight_kampff.modules.{module}").analyser(c)
        except LimiteDepassee:
            assert c.depasse
            return None
    for ligne in c.lignes:
        schemas.valider("messages", decoder(ligne))
    return c.lignes


@given(metadonnees_mutees())
def test_modules_de_metadonnees_echantillons_mutes(echantillon: tuple[str, bytes]) -> None:
    format_, contenu = echantillon
    if not contenu:
        return  # une partie a au moins un octet
    for module in _MODULES[format_]:
        lignes = executer_module(module, format_, contenu)
        assert executer_module(module, format_, contenu) == lignes  # même entrée, mêmes résultats


@given(st.sampled_from(sorted(_MODULES)), st.binary(min_size=1, max_size=2048))
def test_modules_de_metadonnees_octets_quelconques(format_: str, contenu: bytes) -> None:
    for module in _MODULES[format_]:
        executer_module(module, format_, contenu)
