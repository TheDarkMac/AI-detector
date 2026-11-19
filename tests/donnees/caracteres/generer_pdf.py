"""Échantillons et oracle du module caracteres pour le PDF (complément de T53, ADR-0243 à
ADR-0247).

Trois documents :

- ``libreoffice.pdf`` : ``texte.odt`` exporté en PDF par LibreOffice (``soffice --convert-to
  pdf``) : polices incorporées en sous-ensembles avec leur ``/ToUnicode``, a cyrillique dans un mot
  latin, espace cadratin dans l'en-tête, étiquettes Unicode dans la note, écrites en
  ``/ActualText`` sur des glyphes d'espaces ;
- ``ghostscript.pdf`` : un programme PostScript converti par Ghostscript (``pdfwrite``) :
  Helvetica et Times, et un omicron grec de la police Symbol au milieu d'un mot latin ;
- ``construit.pdf`` : écrit objet par objet ci-dessous, pour chaque chemin du décodage : texte
  en Helvetica sans ``/ToUnicode`` (encodage standard et AGL), ajustements de ``TJ`` qui séparent
  les mots, ``/Differences`` à noms ``uniXXXX``, ``/ToUnicode`` qui fait d'un glyphe un espace
  sans chasse, police composite Identity-H et ``bfrange``, texte invisible (mode de rendu 3),
  forme appelée par ``Do``, ``/ActualText``, annotation dont l'apparence porte un texte et dont
  le commentaire (``/Contents``) porte un forçage bidirectionnel ; une deuxième page qui ne peint
  qu'une image.

``oracle_pdf.json`` consigne le texte que ``pdftotext -raw`` de Poppler extrait de chaque page,
en points de code : le texte des pages, dans l'ordre du flux de contenu.

Outils de la version du dépôt : LibreOffice 25.2.3.2, Ghostscript 10.05.1, Poppler 25.03.0, sous
Debian 13. À lancer depuis ce dossier : ``python3 -I generer_pdf.py``. Les documents de
LibreOffice et de Ghostscript changent à chaque génération (dates, identifiants) : ne régénérer
que pour changer les échantillons.
"""

import json
import pathlib
import shutil
import subprocess
import tempfile
import zlib

ICI = pathlib.Path(__file__).resolve().parent


def outil(nom: str) -> str:
    chemin = shutil.which(nom)
    if chemin is None:
        raise SystemExit(f"{nom} introuvable")
    return chemin


POSTSCRIPT = b"""%!PS
/Helvetica findfont 12 scalefont setfont
72 720 moveto (Bonjour tout le monde.) show
/Times-Roman findfont 12 scalefont setfont
72 700 moveto (Bonj) show
/Symbol findfont 12 scalefont setfont (o) show
/Times-Roman findfont 12 scalefont setfont (ur en grec.) show
showpage
"""


def flux(dico: bytes, donnees: bytes, compresser: bool = True) -> bytes:
    if compresser:
        donnees = zlib.compress(donnees)
        dico += b"/Filter/FlateDecode"
    return b"<<" + dico + b"/Length %d>>stream\n" % len(donnees) + donnees + b"\nendstream"


def utf16(texte: str) -> bytes:
    return b"<FEFF" + texte.encode("utf-16-be").hex().upper().encode() + b">"


def cmap(lignes: bytes, espace: bytes = b"<00> <FF>") -> bytes:
    return (
        b"/CIDInit/ProcSet findresource begin 12 dict begin begincmap\n"
        b"/CIDSystemInfo<</Registry(Adobe)/Ordering(UCS)/Supplement 0>>def\n"
        b"/CMapName/Essai-UCS def/CMapType 2 def\n"
        b"1 begincodespacerange "
        + espace
        + b" endcodespacerange\n"
        + lignes
        + b"\nendcmap CMapName currentdict/CMap defineresource pop end end\n"
    )


def ecrire_pdf(objets: dict[int, bytes]) -> bytes:
    tampon = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    positions = {}
    for numero in sorted(objets):
        positions[numero] = len(tampon)
        tampon += b"%d 0 obj\n" % numero + objets[numero] + b"\nendobj\n"
    taille = max(objets) + 1
    debut = len(tampon)
    tampon += b"xref\n0 %d\n0000000000 65535 f \n" % taille
    for numero in range(1, taille):
        tampon += (
            b"%010d 00000 n \n" % positions[numero]
            if numero in positions
            else (b"0000000000 65535 f \n")
        )
    tampon += b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (taille, debut)
    return bytes(tampon)


def construit() -> bytes:
    contenu = b"\n".join(
        [
            b"BT /H 12 Tf 72 740 Td [(Bonjour)-300(le)-300(monde.)] TJ ET",
            # Differences : uni0435 est un e cyrillique, au milieu d'un mot latin.
            b"BT /D 12 Tf 72 720 Td (t\x01xte m\xeal\xe9.) Tj ET",
            # ToUnicode : le code 1 est un espace sans chasse (U+200B).
            b"BT /U 12 Tf 72 700 Td <02030401020305> Tj ET",
            # Identity-H : trois codes de deux octets, cyrilliques par bfrange.
            b"BT /C 12 Tf 72 680 Td <000100020003> Tj ET",
            # Texte invisible, comme la couche de texte d'un document numérisé.
            b"q BT /H 12 Tf 3 Tr 72 660 Td (Consigne invisible au lecteur.) Tj ET Q",
            # Texte de remplacement : les glyphes « X » se lisent « oui ».
            b"BT /H 12 Tf 72 640 Td /Span<</ActualText " + utf16("oui") + b">>BDC (XX) Tj EMC ET",
            b"q 1 0 0 1 72 600 cm /F0 Do Q",
        ]
    )
    forme = b"BT /H 10 Tf 0 0 Td (Dans une forme.) Tj ET"
    apparence = b"BT /H 10 Tf 2 2 Td (Tampon) Tj ET"
    differences = b"<</Type/Encoding/BaseEncoding/WinAnsiEncoding/Differences[1/uni0435]>>"
    unicode_u = cmap(
        b"5 beginbfchar <01> <200B> <02> <0070> <03> <0061> <04> <0079> <05> <006C> endbfchar"
    )
    unicode_c = cmap(b"1 beginbfrange <0001> <0003> <041C> endbfrange", b"<0000> <FFFF>")
    largeurs = b"/FirstChar 1/LastChar 5/Widths[0 556 556 500 222]"
    objets = {
        1: b"<</Type/Catalog/Pages 2 0 R>>",
        2: b"<</Type/Pages/Kids[3 0 R 20 0 R]/Count 2>>",
        3: b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Annots[30 0 R]"
        b"/Resources<</Font<</H 5 0 R/D 6 0 R/U 7 0 R/C 8 0 R>>/XObject<</F0 13 0 R>>>>>>",
        4: flux(b"", contenu),
        5: b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        6: b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding 9 0 R>>",
        7: b"<</Type/Font/Subtype/Type1/BaseFont/Essai" + largeurs + b"/ToUnicode 10 0 R>>",
        8: b"<</Type/Font/Subtype/Type0/BaseFont/Essai/Encoding/Identity-H"
        b"/DescendantFonts[12 0 R]/ToUnicode 11 0 R>>",
        9: differences,
        10: flux(b"", unicode_u),
        11: flux(b"", unicode_c),
        12: b"<</Type/Font/Subtype/CIDFontType2/BaseFont/Essai/DW 600"
        b"/CIDSystemInfo<</Registry(Adobe)/Ordering(Identity)/Supplement 0>>>>",
        13: flux(
            b"/Type/XObject/Subtype/Form/BBox[0 0 300 50]/Resources<</Font<</H 5 0 R>>>>", forme
        ),
        20: b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 21 0 R"
        b"/Resources<</XObject<</I0 22 0 R>>>>>>",
        21: flux(b"", b"q 612 0 0 792 0 0 cm /I0 Do Q"),
        22: flux(
            b"/Type/XObject/Subtype/Image/Width 2/Height 2/ColorSpace/DeviceGray"
            b"/BitsPerComponent 8",
            b"\x00\xff\xff\x00",
            compresser=False,
        ),
        30: b"<</Type/Annot/Subtype/FreeText/Rect[300 600 400 630]/F 4/DA(/H 10 Tf)"
        b"/Contents " + utf16("Note \u202ecach\u00e9e") + b"/AP<</N 31 0 R>>>>",
        31: flux(
            b"/Type/XObject/Subtype/Form/BBox[0 0 100 30]/Resources<</Font<</H 5 0 R>>>>", apparence
        ),
    }
    return ecrire_pdf(objets)


def pdftotext(chemin: pathlib.Path) -> list[list[str]]:
    sortie = subprocess.run(
        [outil("pdftotext"), "-raw", "-enc", "UTF-8", str(chemin), "-"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    pages = sortie.split("\f")[:-1]
    return [[f"U+{ord(c):04X}" for c in page] for page in pages]


def version(commande: list[str]) -> str:
    sortie = subprocess.run(commande, check=True, capture_output=True, text=True)
    return (sortie.stdout or sortie.stderr).split("\n")[0].strip()


def main() -> None:
    with tempfile.TemporaryDirectory() as dossier:
        subprocess.run(
            [
                outil("soffice"),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                dossier,
                str(ICI / "texte.odt"),
            ],
            check=True,
            capture_output=True,
        )
        (ICI / "libreoffice.pdf").write_bytes((pathlib.Path(dossier) / "texte.pdf").read_bytes())
        source = pathlib.Path(dossier) / "texte.ps"
        source.write_bytes(POSTSCRIPT)
        subprocess.run(
            [
                outil("gs"),
                "-q",
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.7",
                f"-sOutputFile={ICI / 'ghostscript.pdf'}",
                str(source),
            ],
            check=True,
        )
    (ICI / "construit.pdf").write_bytes(construit())
    oracle: dict[str, object] = {
        "outils": {
            "LibreOffice": version([outil("soffice"), "--version"]),
            "Ghostscript": version([outil("gs"), "--version"]),
            "Poppler": version([outil("pdftotext"), "-v"]),
        },
    }
    for nom in ("libreoffice.pdf", "ghostscript.pdf", "construit.pdf"):
        oracle[nom] = pdftotext(ICI / nom)
    (ICI / "oracle_pdf.json").write_text(
        json.dumps(oracle, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
