"""Échantillons et oracle du module actifspdf (T52, ADR-0219 à ADR-0222).

Trois documents de départ, écrits comme les écrirait un auteur :

- ``liens.pdf`` : une page de LibreOffice (page HTML convertie) : un lien vers un site, un lien
  ``mailto:``, un renvoi interne et un titre (signet) ;
- ``formulaire.pdf`` : une page de LibreOffice, formulaire HTML importé dans Writer et exporté
  en champs PDF : deux champs de texte et un bouton qui envoie le formulaire ;
- ``ghostscript.pdf`` : une page de Ghostscript (PostScript et pdfmark écrits ici) : un script
  JavaScript à l'ouverture du document, un lien qui lance un programme, une pièce jointe.

Puis des ajouts, chacun en une mise à jour incrémentale écrite par pypdf, comme les écrirait un
outil d'édition de PDF :

- ``javascript.pdf`` : ``liens.pdf`` et un script au niveau du document (arbre de noms
  ``/JavaScript``) ;
- ``piece_jointe.pdf`` : ``liens.pdf`` et une pièce jointe (arbre ``/EmbeddedFiles``) ;
- ``balise.pdf`` : ``liens.pdf`` et une adresse ouverte à l'affichage de la page (``/AA``
  ``/O``, action ``URI``), procédé d'une balise de pistage ;
- ``calcul.pdf`` : ``formulaire.pdf`` et des scripts de mise en forme et de calcul sur un champ
  (``/AA`` ``/F`` et ``/C``) ;
- ``xfa.pdf`` : ``formulaire.pdf`` et un paquet XFA dans le formulaire (``/XFA``).

Et ``chiffre.pdf`` : ``ghostscript.pdf`` réécrit et chiffré par pypdf (RC4 de 128 bits, mot de passe
d'ouverture vide).

``oracle.json`` consigne ensuite ce qu'en dit Poppler : ``pdfinfo`` (formulaire, JavaScript,
chiffrement), les scripts que liste ``pdfinfo -js`` (leurs en-têtes) et le nombre de fichiers
incorporés que liste ``pdfdetach -list``.

Outils de la version du dépôt : Ghostscript 10.05.1, LibreOffice 25.2.3.2, pdfinfo et pdfdetach
de Poppler 25.03.0, pypdf 6.1.1 (depuis PyPI), sous Debian 13. À lancer depuis ce dossier, avec
l'interpréteur d'un environnement où pypdf est installé : ``python -I generer_actifs.py``. Les
PDF changent à chaque génération (dates, identifiants) : ne régénérer que pour changer les
échantillons. Les adresses sont celles du domaine réservé ``example.org`` (RFC 2606).
"""
# mypy: ignore-errors
# (pypdf n'est pas dans l'environnement du projet.)

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    TextStringObject,
)

ICI = Path(__file__).resolve().parent

LIENS_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Rapport</title></head>
<body style="font-family: 'Liberation Serif'; font-size: 12pt">
<h1 id="debut">Rapport annuel</h1>
<p>Voir le <a href="https://www.example.org/rapport">site de l'association</a> et écrire à
<a href="mailto:contact@example.org">contact</a>.</p>
<h2>Annexe</h2>
<p>Retour au <a href="#debut">début</a>.</p>
</body></html>
"""

FORMULAIRE_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Inscription</title></head>
<body style="font-family: 'Liberation Serif'; font-size: 12pt">
<h1>Inscription</h1>
<form action="https://www.example.org/inscription" method="post">
<p>Nom : <input type="text" name="nom"></p>
<p>Âge : <input type="text" name="age"></p>
<p><input type="submit" value="Envoyer"></p>
</form>
</body></html>
"""

GHOSTSCRIPT_PS = b"""%!PS
[ {Catalog} << /OpenAction << /S /JavaScript /JS (app.alert\\("Bonjour"\\);) >> >> /PUT pdfmark
[ /_objdef {note} /type /stream /OBJ pdfmark
[ {note} (Contenu de la note jointe.) /PUT pdfmark
[ /Name (note.txt) /FS << /Type /Filespec /F (note.txt) /EF << /F {note} >> >> /EMBED pdfmark
/Helvetica findfont 14 scalefont setfont
72 720 moveto (Document de Ghostscript) show
72 690 moveto (Lancer la calculatrice) show
[ /Rect [70 685 260 705] /Border [0 0 0] /Action << /Subtype /Launch /F (calc.exe) >>
  /Subtype /Link /ANN pdfmark
showpage
"""

XFA = b"""<?xml version="1.0" encoding="UTF-8"?>
<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<template xmlns="http://www.xfa.org/schema/xfa-template/3.3/">
<subform name="formulaire"><field name="age">
<event activity="initialize"><script contentType="application/x-javascript">
this.rawValue = 18;</script></event>
</field></subform>
</template>
</xdp:xdp>
"""


def outil(nom: str) -> str:
    """Chemin complet d'un outil du poste."""
    chemin = shutil.which(nom)
    if chemin is None:
        raise SystemExit(f"{nom} introuvable")
    return chemin


def ghostscript(source: bytes, sortie: Path) -> None:
    with tempfile.TemporaryDirectory() as dossier:
        page = Path(dossier) / "page.ps"
        page.write_bytes(source)
        subprocess.run(
            [
                outil("gs"),
                "-q",
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                "-sDEVICE=pdfwrite",
                "-dPDFSETTINGS=/prepress",
                "-dEmbedAllFonts=true",
                f"-sOutputFile={sortie}",
                str(page),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )


def libreoffice(html: str, sortie: Path, *options: str) -> None:
    """Page HTML convertie par LibreOffice ; ``options`` choisit le filtre d'import et
    d'export."""
    with tempfile.TemporaryDirectory() as dossier:
        page = Path(dossier) / f"{sortie.stem}.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [outil("libreoffice"), "--headless", *options, "--outdir", dossier, str(page)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        shutil.move(Path(dossier) / f"{sortie.stem}.pdf", sortie)


def retoucher(source: Path, sortie: Path, modifier) -> None:
    shutil.copy(source, sortie)
    writer = PdfWriter(sortie, incremental=True)
    modifier(writer)
    with sortie.open("wb") as fichier:
        writer.write(fichier)


def javascript(code: str) -> DictionaryObject:
    return DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Action"),
            NameObject("/S"): NameObject("/JavaScript"),
            NameObject("/JS"): TextStringObject(code),
        }
    )


def balise(writer: PdfWriter) -> None:
    ouvrir = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Action"),
            NameObject("/S"): NameObject("/URI"),
            NameObject("/URI"): TextStringObject("https://pistage.example.org/ouvert"),
        }
    )
    writer.pages[0][NameObject("/AA")] = DictionaryObject(
        {NameObject("/O"): writer._add_object(ouvrir)}
    )


def calcul(writer: PdfWriter) -> None:
    champs = writer._root_object["/AcroForm"]["/Fields"]
    age = next(c.get_object() for c in champs if c.get_object().get("/T") == "age")
    age[NameObject("/AA")] = DictionaryObject(
        {
            NameObject("/F"): writer._add_object(
                javascript('AFNumber_Format(0, 0, 0, 0, "", true);')
            ),
            NameObject("/C"): writer._add_object(javascript("event.value = 18;")),
        }
    )


def xfa(writer: PdfWriter) -> None:
    paquet = DecodedStreamObject()
    paquet.set_data(XFA)
    writer._root_object["/AcroForm"][NameObject("/XFA")] = writer._add_object(paquet)


def chiffrer(source: Path, sortie: Path) -> None:
    writer = PdfWriter(clone_from=PdfReader(source))
    # Mot de passe de propriétaire d'un échantillon public : rien à protéger.
    writer.encrypt(user_password="", owner_password="proprietaire", algorithm="RC4-128")  # noqa: S106
    with sortie.open("wb") as fichier:
        writer.write(fichier)


def poppler(chemin: Path) -> dict:
    """Ce que disent pdfinfo et pdfdetach d'un échantillon."""
    info = subprocess.run(
        [outil("pdfinfo"), str(chemin)], check=True, capture_output=True, text=True
    ).stdout
    champs = dict(re.findall(r"^([A-Za-z ]+):\s+(.*)$", info, re.MULTILINE))
    scripts = subprocess.run(
        [outil("pdfinfo"), "-js", str(chemin)], check=True, capture_output=True, text=True
    ).stdout
    # pdfinfo -js écrit chaque script en un bloc, après une ligne d'en-tête qui finit par « : »
    # (« Name Dictionary "…" », « Open Document Action », « Format Field », « Calculate Field »…),
    # les blocs séparés par une ligne vide.
    blocs = [b for b in scripts.split("\n\n") if b.strip()]
    entetes = [b.lstrip("\n").split("\n", 1)[0].removesuffix(":") for b in blocs]
    detach = subprocess.run(
        [outil("pdfdetach"), "-list", str(chemin)], check=True, capture_output=True, text=True
    ).stdout
    incorpores = re.match(r"(\d+) embedded files", detach)
    return {
        "formulaire": champs["Form"],
        "javascript": champs["JavaScript"],
        "chiffre": champs["Encrypted"].split()[0],
        "scripts": entetes,
        "fichiers": int(incorpores.group(1)) if incorpores else 0,
    }


def main() -> None:
    liens = ICI / "liens.pdf"
    formulaire = ICI / "formulaire.pdf"
    gs = ICI / "ghostscript.pdf"
    libreoffice(LIENS_HTML, liens, "--convert-to", "pdf:writer_web_pdf_Export")
    libreoffice(
        FORMULAIRE_HTML,
        formulaire,
        "--infilter=HTML (StarWriter)",
        "--convert-to",
        'pdf:writer_pdf_Export:{"ExportFormFields":{"type":"boolean","value":"true"},'
        '"FormsType":{"type":"long","value":"0"}}',
    )
    ghostscript(GHOSTSCRIPT_PS, gs)

    retoucher(liens, ICI / "javascript.pdf", lambda w: w.add_js("app.alert('Ouvert');"))
    retoucher(
        liens,
        ICI / "piece_jointe.pdf",
        lambda w: w.add_attachment("releve.csv", b"date;montant\n2026-10-31;1250,00\n"),
    )
    retoucher(liens, ICI / "balise.pdf", balise)
    retoucher(formulaire, ICI / "calcul.pdf", calcul)
    retoucher(formulaire, ICI / "xfa.pdf", xfa)
    chiffrer(gs, ICI / "chiffre.pdf")

    oracle = {"echantillons": {c.stem: poppler(c) for c in sorted(ICI.glob("*.pdf"))}}
    (ICI / "oracle.json").write_text(
        json.dumps(oracle, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
