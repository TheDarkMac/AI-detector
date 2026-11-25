"""Images d'un DOCX ou d'un ODT : module ``imagesbureau``, parties extraites lues en place ou
décompressées, règles du catalogue (complément de T81, ADR-0252 à ADR-0255).

Les documents synthétiques sont construits ici, par ``zipfile`` et les écrivains de
``bureautique.py`` : les DOCX « à la manière de Word », qui compresse ses images, déclare ses types
par extension et sa vignette par une relation du paquet. Les échantillons de
``tests/donnees/imagesbureau`` viennent de LibreOffice, et ``oracle.json`` consigne ce qu'en lisent
``zipfile`` et ``xml.etree`` (``generer_imagesbureau.py``).
"""

import hashlib
import io
import json
import tempfile
import zipfile
import zlib
from html import escape
from pathlib import Path
from typing import Any

import pytest
from bureautique import MIME_ODT, Brute, archive_brute
from metadonnees import raisons, valeurs_de

from voight_kampff._limites import OCTETS_EXTRAITS_MAX
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Contexte, Extraction
from voight_kampff._travail.fichier import Fichier
from voight_kampff.analyse import Analyse, analyser
from voight_kampff.cli import resume
from voight_kampff.modules import imagesbureau
from voight_kampff.modules._lecture.zip import Archive, Entree
from voight_kampff.rapport import export
from voight_kampff.rapport._presentation import (
    _SANS_METADONNEES,
    Presentation,
    origine_partie,
    texte,
)
from voight_kampff.rapport.modele import (
    NOMBRE_MAX_EXTRAITES,
    Direction,
    EtatTechnique,
    Localisation,
    Partie,
    Plage,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("F-63")

DONNEES = Path(__file__).parent / "donnees"
ECHANTILLONS = DONNEES / "imagesbureau"
ORACLE: dict[str, Any] = json.loads((ECHANTILLONS / "oracle.json").read_text(encoding="utf-8"))
SIMPLE = (DONNEES / "doublejpeg" / "simple_75.jpg").read_bytes()
PNG = (DONNEES / "metadonnees" / "image.png").read_bytes()
STOCKEE, DEFLATE = zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED

TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
VIGNETTE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
DOCUMENT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
MANIFESTE = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"


@pytest.fixture(autouse=True)
def verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


# Documents construits


def archive(*entrees: tuple[str, bytes, int]) -> bytes:
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w") as fichier:
        for nom, contenu, methode in entrees:
            fichier.writestr(nom, contenu, compress_type=methode)
    return flux.getvalue()


def types_de_contenu(defauts: dict[str, str], surcharges: dict[str, str] | None = None) -> bytes:
    elements = "".join(f'<Default Extension="{e}" ContentType="{t}"/>' for e, t in defauts.items())
    elements += "".join(
        f'<Override PartName="{p}" ContentType="{t}"/>' for p, t in (surcharges or {}).items()
    )
    return f'<Types xmlns="{TYPES}">{elements}</Types>'.encode()


def liens(*cibles: tuple[str, str, str | None]) -> bytes:
    elements = "".join(
        f'<Relationship Id="rId{rang}" Type="{type_}" Target="{cible}"'
        + (f' TargetMode="{mode}"' if mode else "")
        + "/>"
        for rang, (type_, cible, mode) in enumerate(cibles, start=1)
    )
    return f'<Relationships xmlns="{RELATIONS}">{elements}</Relationships>'.encode()


DEFAUTS_WORD = {
    "rels": "application/vnd.openxmlformats-package.relationships+xml",
    "xml": "application/xml",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "emf": "image/x-emf",
    "gif": "image/gif",
}


def docx_word(*medias: tuple[str, bytes, int], vignette: bytes | None = None) -> bytes:
    """DOCX comme l'écrit Word : types par extension, images compressées sous ``word/media``,
    vignette éventuelle sous ``docProps``, désignée par une relation du paquet."""
    relations_ = [(DOCUMENT, "word/document.xml", None)]
    entrees = [("word/document.xml", b"<w/>", DEFLATE)]
    if vignette is not None:
        relations_.append((VIGNETTE, "docProps/thumbnail.jpeg", None))
        entrees.append(("docProps/thumbnail.jpeg", vignette, DEFLATE))
    return archive(
        ("[Content_Types].xml", types_de_contenu(DEFAUTS_WORD), DEFLATE),
        ("_rels/.rels", liens(*relations_), DEFLATE),
        *entrees,
        *((f"word/media/{nom}", contenu, methode) for nom, contenu, methode in medias),
    )


def manifeste(*entrees: tuple[str, str] | tuple[str, str, bool]) -> bytes:
    elements = "".join(
        f'<manifest:file-entry manifest:full-path="{e[0]}" manifest:media-type="{e[1]}">'
        + ("<manifest:encryption-data/>" if len(e) == 3 and e[2] else "")
        + "</manifest:file-entry>"
        for e in entrees
    )
    return (
        f'<manifest:manifest xmlns:manifest="{MANIFESTE}">{elements}</manifest:manifest>'.encode()
    )


def odt(declarees: bytes | None, *entrees: tuple[str, bytes, int]) -> bytes:
    """ODT : ``mimetype`` stocké en tête, manifeste s'il est donné, puis les entrées."""
    manifeste_ = () if declarees is None else (("META-INF/manifest.xml", declarees, DEFLATE),)
    return archive(("mimetype", MIME_ODT, STOCKEE), *manifeste_, *entrees)


def executer(
    contenu: bytes,
    format_: str = "docx",
    *,
    places: int = NOMBRE_MAX_EXTRAITES,
    octets: int = OCTETS_EXTRAITS_MAX,
) -> tuple[list[dict[str, Any]], tuple[Extraction, ...], Localisation | None]:
    """Lignes, extractions et première extraction refusée du module."""
    with tempfile.TemporaryFile() as fichier:
        fichier.write(contenu)
        fichier.flush()
        c = Contexte(
            "imagesbureau",
            {Direction.RIEN_DE_PARTICULIER},
            Fichier(fichier.fileno()),
            Partie(1, format_, Plage(0, len(contenu)), fin_connue=True),
            64 << 20,
            extrait={"jpeg", "png", "webp", "heic"},
            places=places,
            octets_restants=octets,
        )
        imagesbureau.analyser(c)
        return [json.loads(ligne) for ligne in c.lignes], c.extractions, c.refusee


def obs(contenu: bytes, format_: str = "docx", **options: Any) -> dict[str, Any]:
    return valeurs_de(executer(contenu, format_, **options)[0])


def analysees(extractions: tuple[Extraction, ...], contenu: bytes) -> list[bytes]:
    """Ce que les modules d'image recevront de chaque extraction : le contenu décompressé, ou les
    octets du fichier."""
    return [
        e.contenu
        if e.contenu is not None
        else contenu[e.octets.debut : e.octets.debut + e.octets.longueur]
        for e in extractions
    ]


# Recherche des images (ADR-0253)


def test_document_sans_image() -> None:
    assert obs(docx_word()) == {
        "imagesbureau.images": 0,
        "imagesbureau.acheminables": 0,
        "imagesbureau.acheminees": 0,
        "imagesbureau.non_acheminees": 0,
    }
    lignes, extractions, refusee = executer(docx_word())
    assert (extractions, refusee, raisons(lignes)) == ((), None, [])
    premiere = next(ligne["observation"] for ligne in lignes if ligne["type"] == "observation")
    assert premiere["localisation"] == {"chemin": "entrées de l'archive"}


def test_docx_a_la_maniere_de_word() -> None:
    contenu = docx_word(
        ("image1.jpeg", SIMPLE, DEFLATE),
        ("image2.png", PNG, STOCKEE),
        ("image3.emf", b"emf", DEFLATE),
        ("image4.gif", b"GIF89a", DEFLATE),
        vignette=SIMPLE,
    )
    lignes, extractions, refusee = executer(contenu)
    assert valeurs_de(lignes) == {
        "imagesbureau.images": 4,
        "imagesbureau.vignette": True,
        "imagesbureau.acheminables": 2,
        "imagesbureau.acheminees": 2,
        "imagesbureau.acheminees.formats": ["jpeg", "png"],
        "imagesbureau.decompressees": 1,
        "imagesbureau.non_acheminees": 2,
        "imagesbureau.non_acheminees.types": ["image/gif", "image/x-emf"],
    }
    assert refusee is None
    assert [(e.format, e.localisation.chemin) for e in extractions] == [
        ("jpeg", "word/media/image1.jpeg"),
        ("png", "word/media/image2.png"),
    ]
    assert analysees(extractions, contenu) == [SIMPLE, PNG]
    # La plage d'une image compressée est celle de ses données compressées dans l'archive.
    jpeg, png = extractions
    donnees = contenu[jpeg.octets.debut : jpeg.octets.debut + jpeg.octets.longueur]
    assert zlib.decompress(donnees, -15) == SIMPLE
    assert png.contenu is None


def test_types_declares() -> None:
    # Une surcharge l'emporte sur l'extension ; noms de parties et extensions sans casse (OPC) ;
    # paramètres et casse du type ignorés ; une entrée sans type déclaré n'est pas une image.
    surcharges = {
        "/word/media/photo.bin": "image/JPEG; q=1",
        "/WORD/media/Image%201.PNG": "image/webp",
        "/word/media/b.jpeg": "application/octet-stream",
    }
    defauts = {"jpeg": "image/jpeg", "PNG": "image/png", "heif": "image/heif"}
    contenu = archive(
        ("[Content_Types].xml", types_de_contenu(defauts, surcharges), DEFLATE),
        ("word/media/photo.bin", SIMPLE, DEFLATE),
        ("word/media/image 1.png", PNG, DEFLATE),
        ("word/media/b.jpeg", SIMPLE, DEFLATE),
        ("word/media/c.JPEG", SIMPLE, DEFLATE),
        ("word/media/d.heif", b"heif", STOCKEE),
        ("word/media/sans_extension", SIMPLE, DEFLATE),
        ("word/media.d/inconnue.tiff", SIMPLE, DEFLATE),
        ("word/media/", b"", STOCKEE),
    )
    _, extractions, _ = executer(contenu)
    assert [(e.format, e.localisation.chemin) for e in extractions] == [
        ("jpeg", "word/media/photo.bin"),
        ("webp", "word/media/image 1.png"),
        ("jpeg", "word/media/c.JPEG"),
        ("heic", "word/media/d.heif"),
    ]


@pytest.mark.parametrize(
    ("type_", "format_"),
    [
        ("image/jpeg", "jpeg"),
        (" Image/PNG ; x=y", "png"),
        ("image/webp", "webp"),
        ("image/heic", "heic"),
        ("image/heif", "heic"),
        ("image/gif", None),
        ("image/jpg", None),
        ("application/pdf", None),
    ],
)
def test_format_du_type(type_: str, format_: str | None) -> None:
    assert imagesbureau.format_du_type(type_) == format_


def test_vignette_du_paquet_seule() -> None:
    # La relation thumbnail du paquet, cible relative à la racine ; une cible externe n'en est pas
    # une ; une autre relation vers une image, si.
    autre = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    contenu = archive(
        ("[Content_Types].xml", types_de_contenu({"jpeg": "image/jpeg"}), DEFLATE),
        (
            "_rels/.rels",
            liens(
                (VIGNETTE, "/docProps/./thumb%20nail.jpeg", None),
                (VIGNETTE, "https://exemple.invalid/v.jpeg", "External"),
                (VIGNETTE, "../docProps/x/../vignette.jpeg", None),
                (autre, "media/a.jpeg", None),
            ),
            DEFLATE,
        ),
        ("docProps/thumb nail.jpeg", SIMPLE, DEFLATE),
        ("docProps/vignette.jpeg", SIMPLE, DEFLATE),
        ("media/a.jpeg", SIMPLE, DEFLATE),
        ("v.jpeg", SIMPLE, DEFLATE),
    )
    valeurs = obs(contenu)
    assert (valeurs["imagesbureau.images"], valeurs["imagesbureau.vignette"]) == (2, True)
    _, extractions, _ = executer(contenu)
    assert [e.localisation.chemin for e in extractions] == ["media/a.jpeg", "v.jpeg"]


def test_relations_sans_cible_ni_type() -> None:
    elements = (
        f'<Relationships xmlns="{RELATIONS}"><Relationship Type="{VIGNETTE}"/>'
        '<Relationship Target="a.jpeg"/><autre/></Relationships>'
    ).encode()
    defauts = types_de_contenu({"jpeg": "image/jpeg"})
    types_ = defauts.replace(
        b"</Types>",
        b'<Default ContentType="image/png"/><Override/>'
        b'<x:a xmlns:x="urn:x" ContentType="y"/></Types>',
    )
    contenu = archive(
        ("[Content_Types].xml", types_, DEFLATE),
        ("_rels/.rels", elements, DEFLATE),
        ("a.jpeg", SIMPLE, DEFLATE),
    )
    assert obs(contenu)["imagesbureau.acheminees"] == 1


def test_odt_lu_en_place() -> None:
    contenu = odt(
        manifeste(
            ("/", MIME_ODT.decode()),
            ("Pictures/a.jpg", "image/jpeg"),
            ("./Pictures/b.png", "image/png"),
            ("Pictures/c.svg", "image/svg+xml"),
            ("Thumbnails/thumbnail.png", "image/png"),
            ("content.xml", "text/xml"),
        ).replace(b"</manifest:manifest>", b'<x:a xmlns:x="urn:x"/></manifest:manifest>'),
        ("content.xml", b"<office/>", DEFLATE),
        ("Pictures/a.jpg", SIMPLE, STOCKEE),
        ("Pictures/b.png", PNG, DEFLATE),
        ("Pictures/c.svg", b"<svg/>", DEFLATE),
        ("Pictures/d.jpg", SIMPLE, STOCKEE),  # non déclarée : pas cherchée
        ("Thumbnails/thumbnail.png", PNG, STOCKEE),
    )
    lignes, extractions, _ = executer(contenu, "odt")
    assert valeurs_de(lignes) == {
        "imagesbureau.images": 3,
        "imagesbureau.vignette": True,
        "imagesbureau.acheminables": 2,
        "imagesbureau.acheminees": 2,
        "imagesbureau.acheminees.formats": ["jpeg", "png"],
        "imagesbureau.decompressees": 1,
        "imagesbureau.non_acheminees": 1,
        "imagesbureau.non_acheminees.types": ["image/svg+xml"],
    }
    assert analysees(extractions, contenu) == [SIMPLE, PNG]
    assert [e.contenu is None for e in extractions] == [True, False]


def test_odt_aux_entrees_chiffrees() -> None:
    # Chiffrement entrée par entrée (ODF 1.2) : l'image chiffrée est comptée, ni lue ni acheminée.
    contenu = odt(
        manifeste(("Pictures/a.jpg", "image/jpeg", True), ("Pictures/b.jpg", "image/jpeg")),
        ("Pictures/a.jpg", b"\x00chiffre", DEFLATE),
        ("Pictures/b.jpg", SIMPLE, STOCKEE),
    )
    lignes, extractions, _ = executer(contenu, "odt")
    valeurs = valeurs_de(lignes)
    assert (valeurs["imagesbureau.images"], valeurs["imagesbureau.chiffre"]) == (2, True)
    assert [e.localisation.chemin for e in extractions] == ["Pictures/b.jpg"]
    assert raisons(lignes) == []


def test_declarations_absentes() -> None:
    # Sans types de contenu ni manifeste, aucune entrée n'est déclarée image.
    sans = archive(("word/media/a.jpeg", SIMPLE, DEFLATE))
    assert obs(sans)["imagesbureau.images"] == 0
    assert obs(odt(None, ("Pictures/a.jpg", SIMPLE, STOCKEE)), "odt")["imagesbureau.images"] == 0


@pytest.mark.parametrize("format_", ["docx", "odt"])
def test_declarations_illisibles(format_: str) -> None:
    # XML mal formé : non mené pour format partiel, une fois, le reste lu.
    if format_ == "docx":
        contenu = archive(
            ("[Content_Types].xml", b"<Types", DEFLATE),
            ("_rels/.rels", b"<Relationships", DEFLATE),
        )
    else:
        contenu = odt(b"<manifest:manifest", ("Pictures/a.jpg", SIMPLE, STOCKEE))
    lignes, extractions, _ = executer(contenu, format_)
    assert raisons(lignes) == ["format_partiel"]
    assert extractions == ()
    assert valeurs_de(lignes)["imagesbureau.images"] == 0


def test_declarations_en_double() -> None:
    types_ = types_de_contenu({"jpeg": "image/jpeg"})
    contenu = archive_brute(
        Brute(b"[Content_Types].xml", types_),
        Brute(b"[content_types].xml", types_),
        Brute(b"a.jpeg", SIMPLE),
    )
    lignes, extractions, _ = executer(contenu)
    assert raisons(lignes) == ["format_partiel"]
    assert extractions == ()


def test_archive_illisible() -> None:
    lignes, extractions, _ = executer(b"PK\x03\x04" + bytes(40))
    assert raisons(lignes) == ["format_partiel"]
    assert extractions == ()
    assert valeurs_de(lignes) == {}


def test_entrees_illisibles_n_arretent_pas_les_autres() -> None:
    # Une entrée chiffrée par l'archive, une compressée autrement, une deflate invalide : la
    # première est non menée, les suivantes sont passées, les autres images acheminées.
    types_ = types_de_contenu({"jpeg": "image/jpeg"})
    contenu = archive_brute(
        Brute(b"[Content_Types].xml", types_),
        Brute(b"a.jpeg", SIMPLE, drapeaux=1),
        Brute(b"b.jpeg", SIMPLE, methode=12),
        Brute(b"c.jpeg", SIMPLE, donnees=b"\xff" * 8),
        Brute(b"d.jpeg", SIMPLE),
    )
    lignes, extractions, _ = executer(contenu)
    assert raisons(lignes) == ["format_partiel"]
    assert [e.localisation.chemin for e in extractions] == ["d.jpeg"]
    assert valeurs_de(lignes)["imagesbureau.acheminables"] == 4


def test_image_au_dela_de_la_partie() -> None:
    # Taille compressée de la dernière entrée portée au-delà de la fin : non menée pour fichier
    # tronqué, localisée à l'entrée ; rien n'est acheminé.
    contenu = docx_word(("a.jpeg", SIMPLE, STOCKEE))
    centrale = contenu.rindex(b"PK\x01\x02")
    gonfle = contenu[: centrale + 20] + (1 << 20).to_bytes(4, "little") + contenu[centrale + 24 :]
    lignes, extractions, _ = executer(gonfle)
    (non_menee,) = [ligne["non_menee"] for ligne in lignes if ligne["type"] == "non_menee"]
    assert non_menee["raison"] == "fichier_tronque"
    assert non_menee["localisation"]["chemin"] == "word/media/a.jpeg"
    assert extractions == ()


def test_entree_vide_comptee_non_acheminee() -> None:
    contenu = docx_word(("a.jpeg", b"", STOCKEE), ("b.jpeg", b"", DEFLATE))
    valeurs = obs(contenu)
    assert (valeurs["imagesbureau.images"], valeurs["imagesbureau.acheminees"]) == (2, 0)


def test_image_trop_grande(monkeypatch: pytest.MonkeyPatch) -> None:
    # Au-delà de la borne, l'image compressée est comptée, non acheminée ; stockée telle quelle,
    # elle est lue en place, sans borne (ADR-0254).
    monkeypatch.setattr(imagesbureau, "TAILLE_MAX_IMAGE", len(SIMPLE) - 1)
    contenu = docx_word(("a.jpeg", SIMPLE, DEFLATE), ("b.jpeg", SIMPLE, STOCKEE))
    lignes, extractions, _ = executer(contenu)
    assert valeurs_de(lignes)["imagesbureau.trop_grandes"] == 1
    assert [e.localisation.chemin for e in extractions] == ["word/media/b.jpeg"]


def test_places_epuisees(monkeypatch: pytest.MonkeyPatch) -> None:
    # Plus de place : rien n'est décompressé, et la première refusée est retenue (ADR-0226).
    lues: list[str] = []
    lire = Archive.lire

    def compter(self: Archive, entree: Entree, maximum: int | None = None) -> bytes:
        lues.append(entree.nom)
        return lire(self, entree, maximum)

    monkeypatch.setattr(Archive, "lire", compter)
    contenu = docx_word(*((f"{n}.jpeg", SIMPLE, DEFLATE) for n in "abc"))
    lignes, extractions, refusee = executer(contenu, places=1)
    assert [e.localisation.chemin for e in extractions] == ["word/media/a.jpeg"]
    assert refusee == Localisation(chemin="word/media/b.jpeg")
    assert valeurs_de(lignes)["imagesbureau.au_dela"] == 2
    assert "word/media/a.jpeg" in lues
    assert "word/media/b.jpeg" not in lues


def test_octets_epuises() -> None:
    # Celle qui franchit le seuil est encore acheminée ; une compressée y compte décompressée.
    contenu = docx_word(*((f"{n}.jpeg", SIMPLE, DEFLATE) for n in "abc"))
    valeurs = obs(contenu, octets=len(SIMPLE) + 1)
    assert (valeurs["imagesbureau.acheminees"], valeurs["imagesbureau.au_dela"]) == (2, 1)


def test_dix_huit_images() -> None:
    contenu = docx_word(*((f"image{n}.jpeg", SIMPLE, STOCKEE) for n in range(18)))
    valeurs = obs(contenu)
    assert (valeurs["imagesbureau.acheminees"], valeurs["imagesbureau.au_dela"]) == (16, 2)


def test_origine_d_une_partie_reconnue() -> None:
    assert origine_partie(Partie(1, "docx", Plage(0, 1), fin_connue=True)) == ""


# Échantillons de LibreOffice, comparés à l'oracle


def test_echantillons_et_oracle_concordent() -> None:
    assert sorted(ORACLE["echantillons"]) == sorted(
        p.name for p in ECHANTILLONS.iterdir() if p.suffix in {".docx", ".odt"}
    )


@pytest.mark.parametrize("nom", sorted(ORACLE["echantillons"]))
def test_echantillons_compares_a_l_oracle(nom: str) -> None:
    attendu = ORACLE["echantillons"][nom]
    contenu = (ECHANTILLONS / nom).read_bytes()
    lignes, extractions, _ = executer(contenu, nom.rpartition(".")[2])
    images = [i for i in attendu["images"] if not i["vignette"]]
    acheminables = [i for i in images if imagesbureau.format_du_type(i["type"])]
    assert [e.localisation.chemin for e in extractions] == [i["nom"] for i in acheminables]
    empreintes = [hashlib.sha256(o).hexdigest() for o in analysees(extractions, contenu)]
    assert empreintes == [i["sha256"] for i in acheminables]
    compressees = [e.contenu is not None for e in extractions]
    assert compressees == [i["compression"] == "deflate" for i in acheminables]
    valeurs = valeurs_de(lignes)
    assert valeurs["imagesbureau.images"] == len(images)
    assert valeurs.get("imagesbureau.vignette", False) is any(
        i["vignette"] for i in attendu["images"]
    )
    assert valeurs.get("imagesbureau.chiffre", False) is attendu["chiffre"]
    # LibreOffice recopie les images sans les réencoder : ce sont celles d'origine.
    assert set(empreintes) <= set(ORACLE["images"].values())


# Analyses complètes

ATTENDUS = {
    "libreoffice.odt": {"R-IMAGESBUREAU-001", "R-IMAGESBUREAU-002"},
    "libreoffice.docx": {"R-IMAGESBUREAU-001", "R-IMAGESBUREAU-002"},
    "chiffre.odt": {"R-IMAGESBUREAU-005"},
}


@pytest.fixture(scope="module")
def analyses(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Analyse]:
    dossier = tmp_path_factory.mktemp("imagesbureau")
    trouvees = {}
    for nom in ATTENDUS:
        chemin = dossier / nom
        chemin.write_bytes((ECHANTILLONS / nom).read_bytes())
        trouvees[nom] = analyser(chemin)
    return trouvees


def regles(analyse: Analyse) -> set[str]:
    return {c.regle.identifiant for c in analyse.constats if c.module == "imagesbureau"}


@pytest.mark.parametrize(("nom", "attendues"), ATTENDUS.items())
def test_regles_du_catalogue(analyses: dict[str, Analyse], nom: str, attendues: set[str]) -> None:
    analyse = analyses[nom]
    etats = {t.module: t.etat for t in analyse.couverture.techniques if t.partie == 1}
    assert etats["imagesbureau"] is EtatTechnique.APPLIQUEE
    assert regles(analyse) == attendues
    assert not analyse.interrompue


@pytest.mark.parametrize("nom", ["libreoffice.odt", "libreoffice.docx"])
def test_image_d_origine_ia_declaree_dans_un_document(
    analyses: dict[str, Analyse], nom: str
) -> None:
    # L'image marquée garde son XMP : son origine IA déclarée est vue dans sa partie extraite,
    # lue en place dans l'ODT, décompressée dans le DOCX (ADR-0254).
    analyse = analyses[nom]
    extraites = {p.format: p for p in analyse.identification.extraites}
    assert sorted(extraites) == ["jpeg", "png"]
    jpeg = extraites["jpeg"]
    assert jpeg.origine is not None
    assert (jpeg.origine.contenant, jpeg.origine.module) == (1, "imagesbureau")
    assert (jpeg.origine.decompression is not None) is nom.endswith(".docx")
    constats = {(c.regle.identifiant, c.partie) for c in analyse.constats}
    assert ("R-XMP-001", jpeg.rang) in constats
    etats = {t.module: t.etat for t in analyse.couverture.techniques if t.partie == jpeg.rang}
    for module in ("c2pa", "doublejpeg", "dwtdct", "ela", "exif", "image", "iptc", "xmp"):
        assert etats[module] is EtatTechnique.APPLIQUEE, module
    assert etats["imagesbureau"] is EtatTechnique.NON_APPLICABLE
    png = {
        t.module: t.etat for t in analyse.couverture.techniques if t.partie == extraites["png"].rang
    }
    assert png["textepng"] is EtatTechnique.APPLIQUEE


def test_document_chiffre_sans_images_declarees(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["chiffre.odt"]
    assert analyse.identification.extraites == ()
    valeurs = {o.nom: o.valeur for o in analyse.observations if o.module == "imagesbureau"}
    assert (valeurs["imagesbureau.images"], valeurs["imagesbureau.chiffre"]) == (0, True)


def test_contenu_d_un_autre_format_que_celui_declare(tmp_path: Path) -> None:
    # Un PNG déclaré JPEG : le moteur le reconnaît, et le déclare non mené pour format partiel.
    chemin = tmp_path / "faux.docx"
    chemin.write_bytes(docx_word(("image1.jpeg", PNG, DEFLATE)))
    analyse = analyser(chemin)
    assert analyse.identification.extraites == ()
    du_fichier = {
        (n.raison, n.partie, n.localisation.chemin if n.localisation else None)
        for n in analyse.non_menees
        if n.module is None
    }
    assert (RaisonNonMenee.FORMAT_PARTIEL, 1, "word/media/image1.jpeg") in du_fichier


def jpeg_rembourre(taille: int) -> bytes:
    """``simple_75.jpg`` grossi de segments APP15 jusqu'à ``taille`` octets environ, compressibles :
    un JPEG valide, dont l'analyse reste rapide."""
    segments = b""
    while len(SIMPLE) + len(segments) < taille:
        segments += b"\xff\xef" + (65535).to_bytes(2, "big") + bytes(65533)
    return SIMPLE[:2] + segments + SIMPLE[2:]


@pytest.mark.exigence("NF-06")
def test_budget_d_octets_de_bout_en_bout(tmp_path: Path) -> None:
    # Trois JPEG de 1,2 Mio, compressés à quelques Kio : le seuil compte leur taille
    # décompressée ; le deuxième franchit les 2 Mio et l'est encore, le troisième non.
    gros = jpeg_rembourre(1_200_000)
    chemin = tmp_path / "gros.docx"
    chemin.write_bytes(docx_word(*((f"{n}.jpeg", gros, DEFLATE) for n in "abc")))
    assert chemin.stat().st_size < 100_000
    analyse = analyser(chemin)
    assert [p.rang for p in analyse.identification.extraites] == [2, 3]
    assert regles(analyse) == {"R-IMAGESBUREAU-001", "R-IMAGESBUREAU-003"}
    assert not analyse.interrompue


def test_phrases_des_constats(analyses: dict[str, Analyse], tmp_path: Path) -> None:
    attendus = {
        "libreoffice.docx": (
            "Le document porte 2 image(s) JPEG, PNG, WebP ou HEIC : 2 sont analysée(s) chacune "
            "comme une partie extraite, par les modules d'image (formats : jpeg, png).",
            "1 image(s) du document sont dans un format que les modules d'image ne lisent pas "
            "(types : image/gif) : aucune n'a été analysée.",
        ),
        "chiffre.odt": (
            "Le document est chiffré par un mot de passe : ses images ne sont pas analysées, "
            "l'outil ne déchiffrant rien.",
        ),
    }
    for nom, phrases in attendus.items():
        page = export.exporter_html(analyses[nom])
        for phrase in phrases:
            assert escape(phrase) in page, phrase
    chemin = tmp_path / "nombreuses.docx"
    chemin.write_bytes(docx_word(*((f"i{n}.jpeg", SIMPLE, STOCKEE) for n in range(17))))
    page = export.exporter_html(analyser(chemin))
    phrase = (
        "1 image(s) du document ne sont pas analysées : l'outil analyse, dans l'ordre de "
        "l'archive, seize images au plus, jusqu'à 2 Mio de données."
    )
    assert escape(phrase) in page


def test_phrase_des_images_trop_grandes(tmp_path: Path) -> None:
    # Une image de plus de 16 Mio une fois décompressée : JPEG grossi de segments, compressible.
    chemin = tmp_path / "grande.docx"
    chemin.write_bytes(docx_word(("a.jpeg", jpeg_rembourre((16 << 20) + 1), DEFLATE)))
    analyse = analyser(chemin)
    assert analyse.identification.extraites == ()
    assert regles(analyse) == {"R-IMAGESBUREAU-004"}
    phrase = (
        "1 image(s) compressée(s) du document dépassent 16 Mio une fois décompressées : elles ne "
        "sont pas analysées."
    )
    assert escape(phrase) in export.exporter_html(analyse)


def test_rapport_montre_les_parties_decompressees(analyses: dict[str, Analyse]) -> None:
    analyse = analyses["libreoffice.docx"]
    page = export.exporter_html(analyse)
    (jpeg, png) = analyse.identification.extraites
    assert jpeg.origine is not None
    assert jpeg.origine.decompression is not None
    taille = jpeg.origine.decompression.taille
    origine = (
        "extraite de la partie 1 par images d'un DOCX ou d'un ODT (imagesbureau) : chemin "
        "word/media/image1.jpeg ; décompressée "
        f"(deflate, {taille} octets) : les positions de ses résultats se lisent dans ce contenu"
    )
    assert origine_partie(jpeg) == origine
    assert escape(origine) in page
    signalement = texte("signalements.extraites", nombre=2, premiere=2, derniere=3)
    assert escape(signalement) in page
    lignes = resume(analyse, ())
    assert any(ligne.startswith("partie 2 : jpeg") and origine in ligne for ligne in lignes)
    document_json = json.loads(export.exporter_json(analyse))
    extraites = document_json["identification"]["extraites"]
    assert [p["origine"]["decompression"]["methode"] for p in extraites] == ["deflate"] * 2
    # Lue en place, une image d'ODT n'a pas de décompression.
    (odt_jpeg,) = [
        p for p in analyses["libreoffice.odt"].identification.extraites if p.format == "jpeg"
    ]
    assert odt_jpeg.origine is not None
    assert odt_jpeg.origine.decompression is None
    assert "décompressée" not in origine_partie(odt_jpeg)
    assert png.format == "png"


def test_controle_avant_publication_complet(tmp_path: Path) -> None:
    # Le module ne lit aucune métadonnée identifiante : non mené, il ne rend pas le contrôle
    # avant publication incomplet (ADR-0255). Désactivé, aucune image n'est extraite.
    chemin = tmp_path / "libreoffice.docx"
    chemin.write_bytes((ECHANTILLONS / "libreoffice.docx").read_bytes())
    analyse = analyser(chemin, desactiver={"imagesbureau"})
    assert analyse.identification.extraites == ()
    assert "imagesbureau" in {n.module for n in analyse.non_menees}
    assert "imagesbureau" in _SANS_METADONNEES
    assert texte("resume.publication_incomplete") not in Presentation(analyse, ()).publication()
