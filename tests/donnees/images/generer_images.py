"""Échantillons et oracle du module imagespdf (T53, ADR-0223 à ADR-0227).

Trois documents écrits par des outils courants, à partir des JPEG de ``../doublejpeg`` (image
de synthèse de 384 sur 256 pixels, ``generer.sh``) :

- ``imagemagick.pdf`` : ``ia.jpg`` converti par ImageMagick ; ``ia.jpg`` est
  ``double_60_90.jpg`` où exiftool a écrit une origine IA déclarée (XMP ``DigitalSourceType``
  ``trainedAlgorithmicMedia``) et un outil créateur ; ImageMagick réencode l'image et garde son
  XMP ;
- ``libreoffice.pdf`` : une page HTML qui montre ``ia.jpg`` et un dégradé PNG, convertie par
  LibreOffice : le JPEG est réencodé sans ses métadonnées, le PNG devient des pixels compressés
  (``FlateDecode``) ;
- ``ghostscript.pdf`` : ``../metadonnees/photo.jpg`` (8 sur 8 pixels) et ``simple_75.jpg`` sur deux
  pages, par ``viewjpeg.ps`` de Ghostscript : la petite image devient une image en ligne, qui
  n'est pas cherchée ; la grande reste un JPEG.

Puis des documents écrits ici, objet par objet, pour ce que les outils n'écrivent pas :

- ``formes.pdf`` : deux pages ; à la première, ``simple_75.jpg``, une image ``FlateDecode`` et une
  image sans filtre ; à la seconde, une forme qui dessine ``double_60_90.jpg``, de nouveau
  ``simple_75.jpg`` (une seule image, lue une fois), un JPEG compressé une seconde fois
  (``FlateDecode`` puis ``DCTDecode``), une image ``JPXDecode`` et une sous-forme qui dessine une
  image au filtre inconnu de la norme ;
- ``faux.pdf`` : trois flux ``DCTDecode`` qui ne sont pas des JPEG complets : un PNG, des octets
  quelconques, ``simple_75.jpg`` coupé de moitié ;
- ``nombreuses.pdf`` : dix-huit JPEG (``photo.jpg``) sur une page, deux de plus que la borne
  (ADR-0226).

Et ``chiffre.pdf`` : ``libreoffice.pdf`` réécrit et chiffré par Ghostscript (RC4 de 128 bits, mot
de passe d'ouverture vide, ``-sOwnerPassword``).

``oracle.json`` consigne ce qu'en dit Poppler : pour chaque image que liste ``pdfimages
-list`` (images dessinées), sa page, son objet et son codage, et pour un JPEG, l'empreinte
SHA-256 du fichier qu'écrit ``pdfimages -j``, qui recopie les données du flux.

Outils de la version du dépôt : ImageMagick 7.1.1-43, exiftool 13.25, LibreOffice 25.2.3.2,
Ghostscript 10.05.1, pdfimages de Poppler 25.03.0, sous Debian 13. À lancer depuis ce dossier :
``python3 -I generer_images.py``. Les PDF des outils changent à chaque génération (dates,
identifiants) : ne régénérer que pour changer les échantillons.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path

ICI = Path(__file__).resolve().parent
DONNEES = ICI.parent
SIMPLE = (DONNEES / "doublejpeg" / "simple_75.jpg").read_bytes()
DOUBLE = (DONNEES / "doublejpeg" / "double_60_90.jpg").read_bytes()
PHOTO = DONNEES / "metadonnees" / "photo.jpg"
VIEWJPEG = "/usr/share/ghostscript/10.05.1/lib/viewjpeg.ps"
IA = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00"
    b":~\x9bU\x00\x00\x00\rIDATx\x01\x01\x02\x00\xfd\xff\x00\x00\x00\x02\x00\x01"
    b"~\x05\r\xd2\x00\x00\x00\x00IEND\xaeB`\x82"
)

PAGE_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Images</title></head>
<body style="font-family: 'Liberation Serif'; font-size: 12pt">
<p>Une photographie, puis un dégradé.</p>
<p><img src="ia.jpg" width="384" height="256" alt="photographie"></p>
<p><img src="degrade.png" width="120" height="80" alt="dégradé"></p>
</body></html>
"""


def outil(nom: str) -> str:
    """Chemin complet d'un outil du poste."""
    chemin = shutil.which(nom)
    if chemin is None:
        raise SystemExit(f"{nom} introuvable")
    return chemin


def lancer(nom: str, *arguments: str, dossier: Path) -> None:
    subprocess.run([outil(nom), *arguments], cwd=dossier, check=True, capture_output=True)


# PDF écrits objet par objet


def flux(dico: bytes, donnees: bytes) -> bytes:
    return b"<<" + dico + b"/Length %d>>stream\n" % len(donnees) + donnees + b"\nendstream"


def image(filtre: bytes, donnees: bytes, largeur: int = 384, hauteur: int = 256) -> bytes:
    dico = b"/Type/XObject/Subtype/Image/Width %d/Height %d" % (largeur, hauteur)
    dico += b"/ColorSpace/DeviceRGB/BitsPerComponent 8"
    return flux(dico + (b"/Filter" + filtre if filtre else b""), donnees)


def forme(ressources: bytes, contenu: bytes) -> bytes:
    dico = b"/Type/XObject/Subtype/Form/BBox[0 0 400 300]/Resources<</XObject<<" + ressources
    return flux(dico + b">>>>", contenu)


def dessiner(*noms: str) -> bytes:
    """Chaque ressource dessinée à son tour, à la taille de la page."""
    return b"".join(b"q 384 0 0 256 0 0 cm /%s Do Q\n" % n.encode() for n in noms)


def document(objets: dict[int, bytes], pages: list[tuple[bytes, bytes]]) -> bytes:
    """Catalogue (1), arbre des pages (2), puis pour chaque page ses ressources ``/XObject`` et
    son contenu ; les objets numérotés à partir de 10 sont ceux de ``objets``."""
    tous = dict(objets)
    enfants = []
    for rang, (ressources, contenu) in enumerate(pages):
        page, flux_contenu = 3 + 2 * rang, 4 + 2 * rang
        enfants.append(b"%d 0 R" % page)
        tous[page] = (
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 400 300]/Resources<</XObject<<"
            + ressources
            + b">>>>/Contents %d 0 R>>" % flux_contenu
        )
        tous[flux_contenu] = flux(b"", contenu)
    tous[1] = b"<</Type/Catalog/Pages 2 0 R>>"
    tous[2] = b"<</Type/Pages/Kids[" + b" ".join(enfants) + b"]/Count %d>>" % len(pages)
    tampon = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    positions = {}
    for numero in sorted(tous):
        positions[numero] = len(tampon)
        tampon += b"%d 0 obj\n" % numero + tous[numero] + b"\nendobj\n"
    taille = max(tous) + 1
    xref = len(tampon)
    tampon += b"xref\n0 %d\n0000000000 65535 f \n" % taille
    for numero in range(1, taille):
        if numero in positions:
            tampon += b"%010d 00000 n \n" % positions[numero]
        else:
            tampon += b"0000000000 65535 f \n"
    tampon += b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (taille, xref)
    return bytes(tampon)


def formes() -> bytes:
    pixels = bytes(range(256)) * 3
    objets = {
        10: image(b"/DCTDecode", SIMPLE),
        11: image(b"/FlateDecode", zlib.compress(pixels), 16, 16),
        12: image(b"", pixels, 16, 16),
        13: forme(
            b"/B 14 0 R/A 10 0 R/C 15 0 R/J 16 0 R/S 17 0 R", dessiner("B", "A", "C", "J", "S")
        ),
        14: image(b"/DCTDecode", DOUBLE),
        15: image(b"[/FlateDecode/DCTDecode]", zlib.compress(SIMPLE)),
        16: image(b"/JPXDecode", b"\x00\x00\x00\x0cjP  \r\n\x87\n"),
        17: forme(b"/X 18 0 R", dessiner("X")),
        18: image(b"/Inconnu", bytes(48), 4, 4),
    }
    pages = [
        (b"/A 10 0 R/F 11 0 R/N 12 0 R", dessiner("A", "F", "N")),
        (b"/G 13 0 R", dessiner("G")),
    ]
    return document(objets, pages)


def faux() -> bytes:
    objets = {
        10: image(b"/DCTDecode", PNG_1X1, 1, 1),
        11: image(b"/DCTDecode", bytes(range(64)), 8, 8),
        12: image(b"/DCTDecode", SIMPLE[: len(SIMPLE) // 2]),
    }
    return document(objets, [(b"/P 10 0 R/Q 11 0 R/T 12 0 R", dessiner("P", "Q", "T"))])


def nombreuses() -> bytes:
    photo = PHOTO.read_bytes()
    objets = {10 + i: image(b"/DCTDecode", photo, 8, 8) for i in range(18)}
    noms = [f"I{i}" for i in range(18)]
    ressources = b"".join(b"/%s %d 0 R" % (n.encode(), 10 + i) for i, n in enumerate(noms))
    return document(objets, [(ressources, dessiner(*noms))])


# Oracle


def oracle(chemin: Path, dossier: Path) -> list[dict[str, object]]:
    """Images dessinées que liste ``pdfimages -list`` ; empreinte des JPEG de ``-j``."""
    sortie = subprocess.run(
        [outil("pdfimages"), "-list", str(chemin)], check=True, capture_output=True, text=True
    ).stdout
    extraits = dossier / chemin.stem
    extraits.mkdir()
    subprocess.run([outil("pdfimages"), "-j", str(chemin), str(extraits / "x")], check=True)
    images = []
    for rang, ligne in enumerate(sortie.splitlines()[2:]):
        champs = ligne.split()
        page, codage, objet = int(champs[0]), champs[8], champs[10]
        entree: dict[str, object] = {"page": page, "codage": codage, "objet": objet}
        if codage == "jpeg":
            donnees = (extraits / f"x-{rang:03d}.jpg").read_bytes()
            entree["sha256"] = hashlib.sha256(donnees).hexdigest()
        images.append(entree)
    return images


def principal() -> None:
    with tempfile.TemporaryDirectory() as temporaire:
        dossier = Path(temporaire)
        shutil.copy(DONNEES / "doublejpeg" / "double_60_90.jpg", dossier / "ia.jpg")
        shutil.copy(DONNEES / "doublejpeg" / "simple_75.jpg", dossier / "simple.jpg")
        shutil.copy(PHOTO, dossier / "photo.jpg")
        lancer(
            "exiftool",
            "-q",
            "-overwrite_original",
            f"-XMP-iptcExt:DigitalSourceType={IA}",
            "-XMP-xmp:CreatorTool=Générateur d'essai",
            "ia.jpg",
            dossier=dossier,
        )
        lancer("magick", "ia.jpg", "imagemagick.pdf", dossier=dossier)
        lancer(
            "magick", "-size", "120x80", "gradient:red-blue", "png24:degrade.png", dossier=dossier
        )
        (dossier / "page.html").write_text(PAGE_HTML, encoding="utf-8")
        lancer(
            "soffice",
            "--headless",
            "--infilter=HTML (StarWriter)",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "page.html",
            dossier=dossier,
        )
        shutil.move(dossier / "page.pdf", dossier / "libreoffice.pdf")
        afficher = " ".join(
            f"({dossier / nom}) << /PageSize 2 index viewJPEGgetsize 2 array astore >> "
            "setpagedevice viewJPEG showpage"
            for nom in ("photo.jpg", "simple.jpg")
        )
        lancer(
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-dNOSAFER",
            "-sDEVICE=pdfwrite",
            "-o",
            "ghostscript.pdf",
            VIEWJPEG,
            "-c",
            afficher,
            dossier=dossier,
        )
        lancer(
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=pdfwrite",
            "-sOwnerPassword=proprietaire",
            "-dEncryptionR=3",
            "-dKeyLength=128",
            "-o",
            "chiffre.pdf",
            "libreoffice.pdf",
            dossier=dossier,
        )
        for nom in ("imagemagick", "libreoffice", "ghostscript", "chiffre"):
            shutil.copy(dossier / f"{nom}.pdf", ICI / f"{nom}.pdf")
        (ICI / "formes.pdf").write_bytes(formes())
        (ICI / "faux.pdf").write_bytes(faux())
        (ICI / "nombreuses.pdf").write_bytes(nombreuses())
        echantillons = {
            nom: oracle(ICI / f"{nom}.pdf", dossier)
            for nom in ("imagemagick", "libreoffice", "ghostscript", "formes", "nombreuses")
        }
        version = subprocess.run(
            [outil("pdfimages"), "-v"], check=True, capture_output=True, text=True
        ).stderr
        poppler = re.search(r"version ([0-9.]+)", version)
    resultat = {
        "outil": f"pdfimages {poppler.group(1) if poppler else '?'}",
        "echantillons": echantillons,
    }
    (ICI / "oracle.json").write_text(
        json.dumps(resultat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    principal()
