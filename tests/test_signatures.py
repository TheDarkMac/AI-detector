"""Règles de T22 : origine IA déclarée, signatures de générateurs (F-11, F-12, ADR-0142 à 0146).

Les règles du catalogue livré sont appliquées par le moteur aux observations d'un module, comme
dans le processus de travail : le module s'exécute sur un contexte réel, puis le contexte applique
les règles « moteur » du module (``Contexte.appliquer_catalogue``). Deux analyses complètes, par
le processus de travail, vérifient le même chemin jusqu'au rapport. Les échantillons viennent de
``metadonnees.py``, ``medias.py`` et ``bureautique.py``.
"""

import importlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
from bureautique import app, docx_, meta, odt_
from echantillons import boite
from medias import (
    bloc_flac,
    commentaires,
    donnee,
    element_ilst,
    flac,
    id3v2,
    info,
    liste_info,
    meta_itunes,
    mp3,
    quicktime,
    simple,
    tag,
    tags,
    texte_ebml,
    texte_id3,
    texte_qt,
    wav,
    webm,
)
from metadonnees import (
    Sous,
    app1_exif,
    app1_xmp,
    app13,
    ascii_,
    indefini,
    jeu,
    jpeg_meta,
    pdf_info,
    png_meta,
    ressource,
    texte,
    texte_compresse,
    texte_international,
    tiff,
    xmp,
)

from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes, travail
from voight_kampff._regles import Application
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte
from voight_kampff._travail.fichier import Fichier
from voight_kampff.analyse import analyser
from voight_kampff.rapport.modele import Categorie, Direction, Fondement, Niveau, Partie, Plage

pytestmark = pytest.mark.exigence("F-12")

MANIFESTES = {manifeste.identifiant: manifeste for manifeste in manifestes.decouvrir()}
CATALOGUE = catalogues.charger(tuple(MANIFESTES.values()))
REGLES_T22 = tuple(
    regle
    for regle in CATALOGUE.regles
    if regle.categorie is Categorie.INDICE and regle.direction is not Direction.TRANSFORMATION
)
"""Règles de T22 : les indices du catalogue, hors indices de transfert de T24 (vers la
transformation, ``test_transfert.py``) ; celles de T23 sont des informations neutres
(``test_incoherences.py``)."""

IPTC = "http://cv.iptc.org/newscodes/digitalsourcetype/"
EXT = 'xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"'
XMP_NS = 'xmlns:xmp="http://ns.adobe.com/xap/1.0/"'
MM = (
    'xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/" '
    'xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#"'
)
A1111 = (
    "un phare sous la pluie\nNegative prompt: flou\n"
    "Steps: 20, Sampler: Euler a, Schedule type: Automatic, CFG scale: 7, Seed: 1, Size: 512x512"
)
"""Paramètres au format de ``create_infotext`` (modules/processing.py d'AUTOMATIC1111)."""
COMFYUI = '{"3": {"inputs": {"seed": 1, "steps": 20}, "class_type": "KSampler"}}'
"""Graphe au format de l'API de ComfyUI, que ``SaveImage`` écrit sous le mot-clé ``prompt``."""


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    # Le processus de travail d'une analyse complète pose son propre verrou (ADR-0036).
    monkeypatch.setattr(garde, "_verrouille", True)


def constats(
    module: str, contenu: bytes, format_: str, regles: tuple[Any, ...] = REGLES_T22
) -> dict[str, dict[str, Any]]:
    """Constats des ``regles`` sur ``contenu`` : valeur de chaque paramètre, par règle.

    Par défaut, les règles de T22 ; ``test_incoherences.py`` passe celles de T23.
    """
    with tempfile.TemporaryFile() as fichier:
        fichier.write(contenu)
        fichier.flush()
        partie = Partie(1, format_, Plage(0, len(contenu)), fin_connue=True)
        contexte = Contexte(
            module,
            MANIFESTES[module].directions,
            Fichier(fichier.fileno()),
            partie,
            64 << 20,
            regles=tuple(regle for regle in regles if regle.module == module),
        )
        importlib.import_module(f"voight_kampff.modules.{module}").analyser(contexte)
        contexte.appliquer_catalogue()
        lignes = [json.loads(ligne) for ligne in contexte.lignes]
    valeurs = {
        ligne["observation"]["identifiant"]: ligne["observation"]["valeur"]
        for ligne in lignes
        if ligne["type"] == "observation"
    }
    return {
        ligne["constat"]["regle"]["identifiant"]: {
            nom: valeurs[observation]
            for nom, observation in ligne["constat"]["phrase"]["parametres"].items()
        }
        for ligne in lignes
        if ligne["type"] == "constat"
    }


def png_xmp(description: str, espaces: str = EXT) -> bytes:
    return png_meta(texte_international(b"XML:com.adobe.xmp", xmp(description, espaces=espaces)))


def source(valeur: str) -> bytes:
    return png_xmp(f"<Iptc4xmpExt:DigitalSourceType>{valeur}</Iptc4xmpExt:DigitalSourceType>")


def exif_jpeg(*ifd0: Any) -> bytes:
    return jpeg_meta(app1_exif(tiff(tuple(ifd0))))


def mov(*boites: bytes) -> bytes:
    return quicktime(boite(b"udta", b"".join(boites)), majeure=b"qt  ")


# Un échantillon par règle : module, format, contenu, règle, paramètres attendus.
CAS = [
    (
        "xmp",
        "png",
        source(IPTC + "trainedAlgorithmicMedia"),
        "R-XMP-001",
        {"source": IPTC + "trainedAlgorithmicMedia"},
    ),
    (
        "xmp",
        "png",
        source(IPTC + "compositeWithTrainedAlgorithmicMedia"),
        "R-XMP-002",
        {"source": IPTC + "compositeWithTrainedAlgorithmicMedia"},
    ),
    (
        "xmp",
        "png",
        source(IPTC + "compositeSynthetic"),
        "R-XMP-003",
        {"source": IPTC + "compositeSynthetic"},
    ),
    (
        "xmp",
        "jpeg",
        jpeg_meta(app1_xmp(xmp("<xmp:CreatorTool>Midjourney</xmp:CreatorTool>", espaces=XMP_NS))),
        "R-XMP-004",
        {"logiciel": "Midjourney"},
    ),
    (
        "xmp",
        "png",
        png_xmp(
            "<xmpMM:History><rdf:Seq>"
            '<rdf:li stEvt:action="created" stEvt:softwareAgent="Adobe Photoshop 25.0"/>'
            '<rdf:li stEvt:action="saved" stEvt:softwareAgent="Adobe Firefly"/>'
            "</rdf:Seq></xmpMM:History>",
            espaces=MM,
        ),
        "R-XMP-005",
        {"logiciel": ["Adobe Photoshop 25.0", "Adobe Firefly"]},
    ),
    (
        "exif",
        "jpeg",
        exif_jpeg(ascii_(0x0131, "Stable Diffusion XL")),
        "R-EXIF-001",
        {"logiciel": "Stable Diffusion XL"},
    ),
    (
        "exif",
        "jpeg",
        exif_jpeg(Sous(0x8769, (indefini(0x9286, b"UNICODE\x00" + A1111.encode("utf-16-be")),))),
        "R-EXIF-002",
        {},
    ),
    ("textepng", "png", png_meta(texte(b"parameters", A1111.encode())), "R-TEXTEPNG-001", {}),
    ("textepng", "png", png_meta(texte(b"prompt", COMFYUI.encode())), "R-TEXTEPNG-002", {}),
    ("textepng", "png", png_meta(texte(b"invokeai_metadata", b"{}")), "R-TEXTEPNG-003", {}),
    ("textepng", "png", png_meta(texte(b"sd-metadata", b"{}")), "R-TEXTEPNG-004", {}),
    (
        "textepng",
        "png",
        png_meta(texte(b"Software", b"NovelAI")),
        "R-TEXTEPNG-005",
        {"logiciel": "NovelAI"},
    ),
    (
        "iptc",
        "jpeg",
        jpeg_meta(app13(ressource(0x0404, jeu(2, 65, b"DALL-E 3")))),
        "R-IPTC-001",
        {"logiciel": "DALL-E 3"},
    ),
    (
        "infopdf",
        "pdf",
        pdf_info(b"<</Creator(ChatGPT)>>"),
        "R-INFOPDF-001",
        {"logiciel": "ChatGPT"},
    ),
    (
        "infopdf",
        "pdf",
        pdf_info(b"<</Producer(Ideogram)>>"),
        "R-INFOPDF-002",
        {"logiciel": "Ideogram"},
    ),
    ("id3", "mp3", mp3(id3v2(texte_id3(b"TSSE", "Suno"))), "R-ID3-001", {"logiciel": "Suno"}),
    (
        "infowav",
        "wav",
        wav(liste_info((b"ISFT", b"ElevenLabs"))),
        "R-INFOWAV-001",
        {"logiciel": "ElevenLabs"},
    ),
    (
        "vorbis",
        "flac",
        flac(bloc_flac(4, commentaires(b"reference libFLAC", b"ENCODER=Udio"), dernier=True)),
        "R-VORBIS-001",
        {"logiciel": "Udio"},
    ),
    (
        "quicktime",
        "m4a",
        quicktime(boite(b"udta", meta_itunes(element_ilst(b"\xa9too", donnee(1, b"Suno v4"))))),
        "R-QUICKTIME-001",
        {"logiciel": "Suno v4"},
    ),
    (
        "quicktime",
        "mov",
        mov(texte_qt(b"\xa9swr", b"Leonardo.Ai")),
        "R-QUICKTIME-002",
        {"logiciel": "Leonardo.Ai"},
    ),
    (
        "matroska",
        "webm",
        webm(info(texte_ebml(0x4D80, "Lavf61.7.100"), texte_ebml(0x5741, "ComfyUI"))),
        "R-MATROSKA-001",
        {"logiciel": "ComfyUI"},
    ),
    (
        "matroska",
        "webm",
        webm(tags(tag(simple("ENCODER", "InvokeAI 5.0")))),
        "R-MATROSKA-002",
        {"logiciel": "InvokeAI 5.0"},
    ),
    (
        "ooxml",
        "docx",
        docx_(app_=app("<Application>ChatGPT</Application>")),
        "R-OOXML-001",
        {"logiciel": "ChatGPT"},
    ),
    (
        "odf",
        "odt",
        odt_(meta("<meta:generator>Craiyon</meta:generator>")),
        "R-ODF-001",
        {"logiciel": "Craiyon"},
    ),
]


@pytest.mark.parametrize(("module", "format_", "contenu", "regle", "parametres"), CAS)
def test_regle_appliquee(
    module: str, format_: str, contenu: bytes, regle: str, parametres: dict[str, Any]
) -> None:
    assert constats(module, contenu, format_) == {regle: parametres}


def test_chaque_regle_de_t22_est_eprouvee() -> None:
    assert {cas[3] for cas in CAS} == {regle.identifiant for regle in REGLES_T22}
    assert len(REGLES_T22) == 24


@pytest.mark.exigence("ES-20", "F-14")
def test_regles_de_t22_indices_faibles_de_declaration() -> None:
    # ADR-0142 : une déclaration du fichier n'est qu'un indice, faible tant qu'il n'est pas évalué.
    for regle in REGLES_T22:
        assert regle.application is Application.MOTEUR
        assert regle.categorie is Categorie.INDICE
        assert regle.fondement is Fondement.DECLARATION
        assert (regle.niveau, regle.evaluation) == (Niveau.FAIBLE, None)


def test_une_seule_liste_de_generateurs() -> None:
    # ADR-0144 : chaque champ logiciel est éprouvé par la même liste de noms, au même paramètre.
    regles = [regle for regle in REGLES_T22 if regle.gabarit.endswith("-generateur")]
    assert len(regles) == 16
    assert {(c.motif, c.parametre) for regle in regles for c in regle.conditions} == {
        (regles[0].conditions[0].motif, "logiciel")
    }


@pytest.mark.exigence("F-11")
@pytest.mark.parametrize(
    ("valeur", "regle"),
    [
        (IPTC + "trainedAlgorithmicMedia", "R-XMP-001"),
        ("https://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia", "R-XMP-001"),
        ("cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia/", "R-XMP-001"),
        ("  trainedAlgorithmicMedia\n", "R-XMP-001"),
        ("TRAINEDALGORITHMICMEDIA", "R-XMP-001"),
        (IPTC + "compositeWithTrainedAlgorithmicMedia", "R-XMP-002"),
        ("compositeWithTrainedAlgorithmicMedia", "R-XMP-002"),
        (IPTC + "compositeSynthetic", "R-XMP-003"),
        ("compositesynthetic", "R-XMP-003"),
    ],
)
def test_source_numerique_reconnue(valeur: str, regle: str) -> None:
    assert list(constats("xmp", source(valeur), "png")) == [regle]


@pytest.mark.exigence("F-11", "F-14")
@pytest.mark.parametrize(
    "valeur",
    [
        # Valeurs du vocabulaire sans règle (ADR-0143) : elles restent des observations.
        IPTC + "digitalCapture",
        IPTC + "computationalCapture",
        IPTC + "algorithmicMedia",
        IPTC + "algorithmicallyEnhanced",
        IPTC + "composite",
        IPTC + "compositeCapture",
        IPTC + "virtualRecording",
        IPTC + "digitalCreation",
        IPTC + "softwareImage",
        # Graphies non reconnues.
        "http://exemple.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
        IPTC + "trainedAlgorithmicMediaX",
        "trainedAlgorithmicMedia composite",
        "non trainedAlgorithmicMedia",
    ],
)
def test_source_numerique_sans_constat(valeur: str) -> None:
    assert constats("xmp", source(valeur), "png") == {}


@pytest.mark.exigence("F-11")
def test_source_numerique_en_ressource_et_en_liste() -> None:
    ressource_ = png_xmp(
        f'<Iptc4xmpExt:DigitalSourceType rdf:resource="{IPTC}trainedAlgorithmicMedia"/>'
    )
    assert list(constats("xmp", ressource_, "png")) == ["R-XMP-001"]
    # Une liste, contraire à la norme (cardinalité 0..1), satisfait la condition par un élément.
    liste = png_xmp(
        "<Iptc4xmpExt:DigitalSourceType><rdf:Bag><rdf:li>digitalCapture</rdf:li>"
        "<rdf:li>compositeSynthetic</rdf:li></rdf:Bag></Iptc4xmpExt:DigitalSourceType>"
    )
    assert constats("xmp", liste, "png") == {
        "R-XMP-003": {"source": ["digitalCapture", "compositeSynthetic"]}
    }


@pytest.mark.exigence("F-11")
def test_source_numerique_d_un_espace_au_prefixe_choisi() -> None:
    # Le nom vient de l'adresse de l'espace, jamais du préfixe écrit (ADR-0117).
    contenu = png_xmp(
        f"<iptc:DigitalSourceType>{IPTC}trainedAlgorithmicMedia</iptc:DigitalSourceType>",
        espaces='xmlns:iptc="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"',
    )
    assert list(constats("xmp", contenu, "png")) == ["R-XMP-001"]
    faux = png_xmp(
        f"<Iptc4xmpExt:DigitalSourceType>{IPTC}trainedAlgorithmicMedia</Iptc4xmpExt:DigitalSourceType>",
        espaces='xmlns:Iptc4xmpExt="http://exemple.org/iptc/"',
    )
    assert constats("xmp", faux, "png") == {}


@pytest.mark.parametrize(
    "logiciel",
    [
        "Midjourney",
        "midjourney v6",
        "DALL·E 3",
        "DALL-E",
        "dall e 2",
        "Stable Diffusion",
        "stable-diffusion-webui",
        "StableDiffusion XL",
        "Adobe Firefly Image 3",
        "ComfyUI",
        "InvokeAI",
        "Invoke AI",
        "NovelAI Diffusion V3",
        "AUTOMATIC1111",
        "Fooocus 2.5",
        "Leonardo.Ai",
        "Ideogram 2.0",
        "Craiyon",
        "DreamStudio",
        "ChatGPT",
        "Suno",
        "Udio",
        "ElevenLabs",
    ],
)
def test_generateur_reconnu(logiciel: str) -> None:
    contenu = exif_jpeg(ascii_(0x0131, logiciel))
    assert constats("exif", contenu, "jpeg") == {"R-EXIF-001": {"logiciel": logiciel}}


@pytest.mark.parametrize(
    "logiciel",
    [
        # Logiciels ordinaires, et noms communs écartés de la liste (ADR-0144).
        "Adobe Photoshop 25.0 (Windows)",
        "GIMP 2.10.36",
        "Firefly",
        "Google Imagen",
        "Flux",
        "Sora",
        "Runway",
        "Dalle de béton",
        "DALLE",
        "Midjourneys",
        "SunoX",
        "studio",
        "LibreOffice/25.2",
        "Lavf61.7.100",
    ],
)
def test_logiciel_ordinaire_sans_constat(logiciel: str) -> None:
    assert constats("exif", exif_jpeg(ascii_(0x0131, logiciel)), "jpeg") == {}


@pytest.mark.parametrize(
    ("mot_cle", "contenu"),
    [
        (b"parameters", "un phare sous la pluie"),
        (b"parameters", "Steps: vingt, Sampler: Euler"),
        (b"Comment", A1111),
        (b"prompt", "un phare sous la pluie"),
        (b"prompt", '{"3": {"inputs": {}, "classe": "KSampler"}}'),
        (b"workflow", COMFYUI),
        (b"invokeai", "{}"),
        (b"Dream", '"un phare" -s 50'),
    ],
)
def test_bloc_texte_sans_signature(mot_cle: bytes, contenu: str) -> None:
    assert constats("textepng", png_meta(texte(mot_cle, contenu.encode())), "png") == {}


def test_parametres_compresses_et_internationaux() -> None:
    contenu = png_meta(
        texte_compresse(b"parameters", A1111.encode()),
        texte_international(b"prompt", COMFYUI.encode(), compresse=True),
    )
    assert list(constats("textepng", contenu, "png")) == ["R-TEXTEPNG-001", "R-TEXTEPNG-002"]


def test_parametres_au_dela_des_4096_premiers_caracteres_non_vus() -> None:
    # Limite connue de R-TEXTEPNG-001 : le texte est coupé à 4 096 caractères (ADR-0118).
    long_ = "x" * 4096 + "\n" + A1111
    assert constats("textepng", png_meta(texte(b"parameters", long_.encode())), "png") == {}


@pytest.mark.exigence("F-14")
@pytest.mark.parametrize(
    ("module", "format_", "contenu"),
    [
        ("xmp", "png", png_meta()),
        ("textepng", "png", png_meta()),
        ("exif", "jpeg", jpeg_meta()),
        ("infopdf", "pdf", pdf_info(b"<<>>")),
        ("odf", "odt", odt_(None)),
    ],
)
def test_absence_sans_constat(module: str, format_: str, contenu: bytes) -> None:
    assert constats(module, contenu, format_) == {}


def test_une_regle_un_constat_par_partie() -> None:
    # ADR-0089 : deux observations qui satisfont la règle ne donnent qu'un constat, la première.
    contenu = png_meta(texte(b"Software", b"Midjourney"), texte(b"Software", b"NovelAI"))
    assert constats("textepng", contenu, "png") == {"R-TEXTEPNG-005": {"logiciel": "Midjourney"}}


def test_quicktime_hors_moov_udta_non_lu() -> None:
    # La boîte d'une piste n'est pas lue (ADR-0132) : son logiciel ne fait aucun constat.
    contenu = quicktime(boite(b"trak", boite(b"udta", texte_qt(b"\xa9swr", b"Midjourney"))))
    assert constats("quicktime", contenu, "m4a") == {}


def _analyse(chemin: Path) -> dict[str, Any]:
    """Indices d'une analyse complète ; les informations neutres de T23 sont éprouvées ailleurs."""
    resultat = analyser(chemin)
    return {
        constat.regle.identifiant: (constat.direction, constat.module)
        for constat in resultat.constats
        if constat.categorie is Categorie.INDICE
    }


@pytest.mark.exigence("F-11")
def test_analyse_complete_d_un_png(tmp_path: Path) -> None:
    chemin = tmp_path / "image.png"
    paquet = xmp(
        f"<Iptc4xmpExt:DigitalSourceType>{IPTC}compositeWithTrainedAlgorithmicMedia"
        "</Iptc4xmpExt:DigitalSourceType>",
        espaces=EXT,
    )
    chemin.write_bytes(
        png_meta(
            texte_international(b"XML:com.adobe.xmp", paquet),
            texte(b"parameters", A1111.encode()),
        )
    )
    assert _analyse(chemin) == {
        "R-TEXTEPNG-001": (Direction.ORIGINE_IA, "textepng"),
        "R-XMP-002": (Direction.RETOUCHE, "xmp"),
    }


def test_analyse_complete_d_un_docx(tmp_path: Path) -> None:
    chemin = tmp_path / "document.docx"
    chemin.write_bytes(docx_(app_=app("<Application>ChatGPT</Application>")))
    assert _analyse(chemin) == {"R-OOXML-001": (Direction.ORIGINE_IA, "ooxml")}


def test_processus_de_travail_applique_le_catalogue_livre_par_defaut(tmp_path: Path) -> None:
    # Sans catalogue désigné, le travail reçoit les règles du catalogue livré (ADR-0029).
    chemin = tmp_path / "image.png"
    chemin.write_bytes(png_meta(texte(b"prompt", COMFYUI.encode())))
    descripteur = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    try:
        resultat = travail.executer(descripteur, manifestes.decouvrir())
    finally:
        os.close(descripteur)
    assert [
        constat.regle.identifiant
        for constat in resultat.constats
        if constat.categorie is Categorie.INDICE
    ] == ["R-TEXTEPNG-002"]
