"""Échantillons et oracle du module imagesbureau (complément de T81, ADR-0252 à ADR-0255).

Un document de LibreOffice qui montre trois images, écrit de trois façons :

- ``libreoffice.odt`` : en ODT, où LibreOffice range chaque image telle quelle (entrée stockée,
  sans compression) et ajoute la vignette ``Thumbnails/thumbnail.png`` ;
- ``libreoffice.docx`` : en DOCX, où il compresse chaque image par deflate, sans vignette ;
- ``chiffre.odt`` : en ODT protégé par un mot de passe (``essai``) : LibreOffice 25.2 chiffre le
  paquet entier dans une seule entrée, ``encrypted-package``, que le manifeste déclare chiffrée ;
  aucune image n'est plus déclarée.

Les trois images : ``ia.jpg``, ``../doublejpeg/double_60_90.jpg`` où exiftool a écrit une
origine IA déclarée (XMP ``DigitalSourceType`` ``trainedAlgorithmicMedia``), comme pour
l'échantillon d'ImageMagick de ``../images`` ; ``degrade.png`` et ``dessin.gif``, écrits par
ImageMagick. LibreOffice les reçoit en données binaires d'un document à plat (``.fodt``), et les
recopie sans les réencoder : leurs empreintes sont celles des fichiers d'origine.

``oracle.json`` consigne, pour chaque échantillon, ce qu'en lisent des outils indépendants du
module : ``zipfile`` (compression et empreinte SHA-256 du contenu de chaque entrée) et
``xml.etree`` (type que déclarent les types de contenu ou le manifeste, vignette, chiffrement),
pour chaque entrée déclarée image, dans l'ordre du répertoire central, et si le manifeste déclare
une entrée chiffrée ; et les empreintes des trois images d'origine.

Outils de la version du dépôt : LibreOffice 25.2.3.2 et son module Python ``uno``, ImageMagick
7.1.1-43, exiftool 13.25, sous Debian 13. À lancer depuis ce dossier, avec l'interpréteur du
système (où ``uno`` est installé) : ``python3 -I generer_imagesbureau.py``. Les documents changent
à chaque génération (dates, identifiants) : ne régénérer que pour changer les échantillons.
"""
# mypy: ignore-errors
# (uno n'est pas dans l'environnement du projet.)

import base64
import contextlib
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile

import uno
from com.sun.star.beans import PropertyValue

ICI = pathlib.Path(__file__).resolve().parent
DONNEES = ICI.parent
IA = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
MOT_DE_PASSE = "essai"
TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"
RELATIONS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
VIGNETTE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
MANIFESTE = "{urn:oasis:names:tc:opendocument:xmlns:manifest:1.0}"
IMAGES = ("ia.jpg", "degrade.png", "dessin.gif")


def propriete(nom, valeur):
    resultat = PropertyValue()
    resultat.Name = nom
    resultat.Value = valeur
    return resultat


def proprietes(**valeurs):
    return tuple(propriete(nom, valeur) for nom, valeur in valeurs.items())


def lancer(*commande: str, dossier: pathlib.Path) -> None:
    subprocess.run(commande, check=True, cwd=dossier)


def a_plat(dossier: pathlib.Path) -> str:
    """Document à plat : un paragraphe, puis les trois images en données binaires."""
    cadres = "".join(
        f'<draw:frame draw:name="image{rang}" text:anchor-type="as-char" svg:width="3cm" '
        f'svg:height="2cm"><draw:image><office:binary-data>'
        f"{base64.b64encode((dossier / nom).read_bytes()).decode()}"
        f"</office:binary-data></draw:image></draw:frame>"
        for rang, nom in enumerate(IMAGES, start=1)
    )
    espaces = " ".join(
        f'xmlns:{prefixe}="{espace}"'
        for prefixe, espace in (
            ("office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
            ("text", "urn:oasis:names:tc:opendocument:xmlns:text:1.0"),
            ("draw", "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"),
            ("svg", "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"),
            ("xlink", "http://www.w3.org/1999/xlink"),
        )
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n<office:document {espaces} '
        'office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">'
        "<office:body><office:text><text:p>Un document illustré.</text:p>"
        f"<text:p>{cadres}</text:p></office:text></office:body></office:document>\n"
    )


class Office:
    """LibreOffice sans affichage, joint par un tube nommé, avec un profil jetable."""

    def __init__(self, dossier: pathlib.Path) -> None:
        tube = f"vk-imagesbureau-{os.getpid()}"
        soffice = shutil.which("soffice")
        if soffice is None:
            raise SystemExit("soffice introuvable")
        self._processus = subprocess.Popen(
            [
                soffice,
                "--headless",
                "--invisible",
                "--norestore",
                f"-env:UserInstallation={(dossier / 'profil').as_uri()}",
                f"--accept=pipe,name={tube};urp;",
            ]
        )
        local = uno.getComponentContext()
        resolveur = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local
        )
        for _ in range(120):
            try:
                distant = resolveur.resolve(f"uno:pipe,name={tube};urp;StarOffice.ComponentContext")
                break
            except Exception:  # LibreOffice pas encore prêt
                time.sleep(0.5)
        else:
            raise RuntimeError("LibreOffice ne répond pas")
        self.bureau = distant.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", distant
        )

    def ecrire(self, source: pathlib.Path) -> None:
        document = self.bureau.loadComponentFromURL(
            source.as_uri(), "_blank", 0, proprietes(Hidden=True)
        )
        document.storeToURL((ICI / "libreoffice.odt").as_uri(), proprietes(FilterName="writer8"))
        document.storeToURL(
            (ICI / "libreoffice.docx").as_uri(), proprietes(FilterName="MS Word 2007 XML")
        )
        document.storeToURL(
            (ICI / "chiffre.odt").as_uri(),
            proprietes(FilterName="writer8", Password=MOT_DE_PASSE),
        )
        document.close(True)

    def fermer(self) -> None:
        with contextlib.suppress(Exception):
            self.bureau.terminate()
        self._processus.wait(timeout=60)


def declarations_docx(archive: zipfile.ZipFile) -> tuple[dict[str, str], set[str]]:
    # Archives que LibreOffice vient d'écrire pour ce script, pas des données reçues.
    racine = ET.fromstring(archive.read("[Content_Types].xml"))  # noqa: S314
    defauts = {
        e.get("Extension", "").lower(): e.get("ContentType", "")
        for e in racine.iter(f"{TYPES}Default")
    }
    surcharges = {
        e.get("PartName", "").lstrip("/").lower(): e.get("ContentType", "")
        for e in racine.iter(f"{TYPES}Override")
    }
    types = {}
    for nom in archive.namelist():
        extension = nom.rpartition(".")[2].lower() if "." in nom.rpartition("/")[2] else None
        declare = surcharges.get(nom.lower(), defauts.get(extension) if extension else None)
        if declare is not None:
            types[nom] = declare
    liens = ET.fromstring(archive.read("_rels/.rels"))  # noqa: S314
    vignettes = {
        e.get("Target", "").lstrip("/")
        for e in liens.iter(f"{RELATIONS}Relationship")
        if e.get("Type") == VIGNETTE
    }
    return types, vignettes


def declarations_odt(archive: zipfile.ZipFile) -> tuple[dict[str, str], set[str], set[str]]:
    racine = ET.fromstring(archive.read("META-INF/manifest.xml"))  # noqa: S314
    types, chiffrees = {}, set()
    for entree in racine.iter(f"{MANIFESTE}file-entry"):
        chemin = entree.get(f"{MANIFESTE}full-path", "")
        types[chemin] = entree.get(f"{MANIFESTE}media-type", "")
        if entree.find(f"{MANIFESTE}encryption-data") is not None:
            chiffrees.add(chemin)
    return types, {"Thumbnails/thumbnail.png"}, chiffrees


def oracle(chemin: pathlib.Path) -> dict[str, object]:
    with zipfile.ZipFile(chemin) as archive:
        if chemin.suffix == ".docx":
            types, vignettes = declarations_docx(archive)
            chiffrees: set[str] = set()
        else:
            types, vignettes, chiffrees = declarations_odt(archive)
        entrees = []
        for info in archive.infolist():
            declare = types.get(info.filename, "")
            if not declare.startswith("image/"):
                continue
            entree: dict[str, object] = {
                "nom": info.filename,
                "type": declare,
                "compression": "stockee" if info.compress_type == zipfile.ZIP_STORED else "deflate",
                "vignette": info.filename in vignettes,
                "chiffree": info.filename in chiffrees,
            }
            if info.filename not in chiffrees:
                entree["sha256"] = hashlib.sha256(archive.read(info)).hexdigest()
            entrees.append(entree)
    return {"chiffre": bool(chiffrees), "images": entrees}


def main() -> None:
    dossier = pathlib.Path(tempfile.mkdtemp())
    try:
        shutil.copy(DONNEES / "doublejpeg" / "double_60_90.jpg", dossier / "ia.jpg")
        lancer(
            "exiftool",
            "-q",
            "-overwrite_original",
            f"-XMP-iptcExt:DigitalSourceType={IA}",
            "-XMP-xmp:CreatorTool=Générateur d'essai",
            "ia.jpg",
            dossier=dossier,
        )
        lancer(
            "magick", "-size", "120x80", "gradient:red-blue", "png24:degrade.png", dossier=dossier
        )
        lancer("magick", "-size", "90x60", "gradient:green-yellow", "dessin.gif", dossier=dossier)
        source = dossier / "document.fodt"
        source.write_text(a_plat(dossier), encoding="utf-8")
        office = Office(dossier)
        try:
            office.ecrire(source)
        finally:
            office.fermer()
        origines = {nom: hashlib.sha256((dossier / nom).read_bytes()).hexdigest() for nom in IMAGES}
    finally:
        shutil.rmtree(dossier, ignore_errors=True)
    resultat = {
        "outils": {"LibreOffice": "25.2.3.2", "ImageMagick": "7.1.1-43", "exiftool": "13.25"},
        "images": origines,
        "echantillons": {
            nom: oracle(ICI / nom) for nom in ("libreoffice.odt", "libreoffice.docx", "chiffre.odt")
        },
    }
    texte_ = json.dumps(resultat, ensure_ascii=False, indent=1)
    (ICI / "oracle.json").write_text(texte_ + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
