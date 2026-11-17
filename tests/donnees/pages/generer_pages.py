"""Échantillons et oracle du module pagespdf (T51, ADR-0213 à ADR-0216).

Deux documents de départ, écrits comme les écrirait un auteur :

- ``document.pdf`` : deux pages de LibreOffice (page HTML convertie) : titres, gras, italique,
  souligné, surligné, tableau aux cellules colorées, montants, mots grecs et cyrilliques ;
- ``ghostscript.pdf`` : une page de Ghostscript (PostScript écrit ici) : Helvetica et Times en
  sous-ensembles incorporés,
  fond gris peint avant le texte, faux gras (le même mot peint deux fois, décalé), petites
  capitales posées côte à côte.

Puis des retouches, chacune en une mise à jour incrémentale écrite par pypdf, comme les écrirait
un outil d'édition de PDF :

- ``superpose.pdf`` : un montant écrit en Helvetica sur le montant du tableau de
  ``document.pdf`` ;
- ``cache.pdf`` : un rectangle blanc sur ce montant, puis le nouveau montant par-dessus ;
- ``cache_seul.pdf`` : un rectangle noir sur ce montant (caviardage qui laisse le texte) ;
- ``annotation.pdf`` : une annotation de texte libre dont l'apparence peint un rectangle blanc
  et un autre montant sur celui du tableau ;
- ``fusion.pdf`` : la page de ``ghostscript.pdf`` fusionnée avec une autre page de Ghostscript,
  dans la même police : deux sous-ensembles d'une même police sur la page ;
- ``hors_plage.pdf`` : ``ghostscript.pdf`` puis un texte écrit avec sa police, en codes que son
  sous-ensemble ne déclare pas.

``oracle.json`` consigne ensuite ce qu'en dit Poppler : les polices de chaque échantillon
(``pdffonts`` : nom, type, incorporée, sous-ensemble) et la boîte de chaque mot
(``pdftotext -bbox``), dans l'espace de la page (origine en bas à gauche), et où chaque
retouche a été posée.

Outils de la version du dépôt : Ghostscript 10.05.1, LibreOffice 25.2.3.2, pdffonts et pdftotext
de Poppler 25.03.0, pypdf 6.1.1 (depuis PyPI), sous Debian 13. À lancer depuis ce dossier, avec
l'interpréteur d'un environnement où pypdf est installé : ``python -I generer_pages.py``. Les PDF
changent à chaque génération (dates, identifiants) : ne régénérer que pour changer les
échantillons.
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
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

ICI = Path(__file__).resolve().parent
MONTANT = "1250,00"
"""Montant du tableau de ``document.pdf`` que les retouches recouvrent."""

HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Facture</title></head>
<body style="font-family: 'Liberation Serif'; font-size: 12pt">
<h1>Facture n° 2026-117</h1>
<p>Bonjour, voici le <b>détail</b> de la prestation <i>réalisée</i> en octobre, avec un
<u>rappel</u> des conditions et une <span style="background: #ffff00">mention surlignée</span>.</p>
<table border="1" cellpadding="4" style="border-collapse: collapse">
<tr style="background: #dddddd"><th>Désignation</th><th>Quantité</th><th>Montant</th></tr>
<tr><td>Conseil</td><td>5</td><td style="background: #eeeeff">1250,00</td></tr>
<tr><td>Déplacement</td><td>1</td><td>80,00</td></tr>
</table>
<p>Mots en grec : <span lang="el">αλήθεια</span> ; en russe : <span lang="ru">правда</span>.</p>
<p style="page-break-before: always">Deuxième page : conditions générales, paiement à trente
jours, pénalités de retard au taux légal.</p>
</body></html>
"""

GHOSTSCRIPT_PS = b"""%!PS
/Helvetica findfont 14 scalefont setfont
0.9 setgray 60 690 300 40 rectfill 0 setgray
72 700 moveto (Fond gris sous le texte) show
72 660 moveto (Gras) show 72.4 660 moveto (Gras) show
/Times-Roman findfont 12 scalefont setfont
72 620 moveto (P) show 79.5 620 moveto (ETITES) show 120 620 moveto (capitales) show
72 590 moveto (Montant : 480,00 EUR) show
showpage
"""
AUTRE_PS = b"""%!PS
/Helvetica findfont 14 scalefont setfont
300 500 moveto (Ajout venu d'ailleurs) show
showpage
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
                "-dSubsetFonts=true",
                f"-sOutputFile={sortie}",
                str(page),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )


def libreoffice(sortie: Path) -> None:
    with tempfile.TemporaryDirectory() as dossier:
        page = Path(dossier) / "document.html"
        page.write_text(HTML, encoding="utf-8")
        subprocess.run(
            [
                outil("libreoffice"),
                "--headless",
                "--convert-to",
                "pdf:writer_web_pdf_Export",
                "--outdir",
                dossier,
                str(page),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        shutil.copy(Path(dossier) / "document.pdf", sortie)


def mots(chemin: Path) -> list[dict]:
    """Mots de ``pdftotext -bbox``, page par page, dans l'espace de la page."""
    with tempfile.TemporaryDirectory() as dossier:
        sortie = Path(dossier) / "mots.html"
        subprocess.run([outil("pdftotext"), "-bbox", str(chemin), str(sortie)], check=True)
        html = sortie.read_text(encoding="utf-8")
    trouves = []
    for numero, page in enumerate(re.findall(r"<page (.*?)</page>", html, re.S), start=1):
        hauteur = float(re.search(r'height="([\d.]+)"', page).group(1))
        for x0, y0, x1, y1, mot in re.findall(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
            page,
        ):
            trouves.append(
                {
                    "page": numero,
                    "mot": mot,
                    "boite": [
                        float(x0),
                        round(hauteur - float(y1), 3),
                        float(x1),
                        round(hauteur - float(y0), 3),
                    ],
                }
            )
    return trouves


def polices(chemin: Path) -> list[dict]:
    """Polices de ``pdffonts`` : nom, type, incorporée, sous-ensemble ; colonnes repérées par
    la ligne de tirets de l'en-tête."""
    sortie = subprocess.run(
        [outil("pdffonts"), str(chemin)], check=True, capture_output=True, text=True
    ).stdout.splitlines()
    tirets = sortie[1]
    colonnes = [(m.start(), m.end()) for m in re.finditer(r"-+", tirets)]
    lues = []
    for ligne in sortie[2:]:
        champs = [ligne[debut : fin + 1].strip() for debut, fin in colonnes]
        lues.append(
            {
                "nom": champs[0],
                "type": champs[1],
                "incorporee": champs[3] == "yes",
                "sous_ensemble": champs[4] == "yes",
            }
        )
    return lues


def boite_du_montant(chemin: Path) -> list[float]:
    trouve = [m for m in mots(chemin) if m["mot"] == MONTANT and m["page"] == 1]
    if len(trouve) != 1:
        raise SystemExit(f"montant {MONTANT} introuvable dans {chemin}")
    return trouve[0]["boite"]


def ajouter_contenu(writer: PdfWriter, page, donnees: bytes, polices_: dict | None = None):
    """Ajoute un flux de contenu à la fin de ceux de la page, et des polices à ses ressources."""
    flux = DecodedStreamObject()
    flux.set_data(donnees)
    ref = writer._add_object(flux)
    contenus = page.get("/Contents")
    anciens = contenus.get_object() if contenus is not None else None
    if isinstance(anciens, ArrayObject):
        nouveaux = ArrayObject([*anciens, ref])
    else:
        nouveaux = ArrayObject([contenus, ref])
    page[NameObject("/Contents")] = nouveaux
    if polices_:
        ressources = page["/Resources"].get_object()
        if "/Font" not in ressources:
            ressources[NameObject("/Font")] = DictionaryObject()
        dico = ressources["/Font"].get_object()
        for nom, police in polices_.items():
            dico[NameObject(nom)] = writer._add_object(police)


HELVETICA = DictionaryObject(
    {
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    }
)
"""Helvetica non incorporée, sans largeurs : celle qu'emploie un outil de retouche."""


def retoucher(source: Path, sortie: Path, modifier) -> None:
    shutil.copy(source, sortie)
    writer = PdfWriter(sortie, incremental=True)
    modifier(writer, writer.pages[0])
    with sortie.open("wb") as fichier:
        writer.write(fichier)


def texte(x: float, y: float, chaine: str, taille: float = 11) -> bytes:
    return f"BT /VkHelv {taille} Tf {x:.2f} {y:.2f} Td ({chaine}) Tj ET\n".encode("latin-1")


def main() -> None:
    document = ICI / "document.pdf"
    gs = ICI / "ghostscript.pdf"
    libreoffice(document)
    ghostscript(GHOSTSCRIPT_PS, gs)
    x0, y0, x1, y1 = boite_du_montant(document)
    base = y0 + (y1 - y0) * 0.22
    rectangle = f"{x0 - 1:.2f} {y0 - 1:.2f} {x1 - x0 + 2:.2f} {y1 - y0 + 2:.2f} re f"
    retouches = {
        "superpose": texte(x0, base, "9999,00"),
        "cache": f"q 1 g {rectangle} Q\n".encode() + texte(x0, base, "9999,00"),
        "cache_seul": f"q 0 g {rectangle} Q\n".encode(),
    }
    for nom, donnees in retouches.items():
        retoucher(
            document,
            ICI / f"{nom}.pdf",
            lambda w, p, d=donnees: ajouter_contenu(w, p, d, {"/VkHelv": HELVETICA}),
        )

    def annoter(writer: PdfWriter, page) -> None:
        largeur, hauteur = x1 - x0 + 2, y1 - y0 + 2
        apparence = DecodedStreamObject()
        apparence.set_data(
            f"1 g 0 0 {largeur:.2f} {hauteur:.2f} re f 0 g "
            f"BT /VkHelv 11 Tf 1 {base - y0 + 1:.2f} Td (8888,00) Tj ET".encode()
        )
        apparence.update(
            {
                NameObject("/Type"): NameObject("/XObject"),
                NameObject("/Subtype"): NameObject("/Form"),
                NameObject("/BBox"): ArrayObject(
                    [NumberObject(0), NumberObject(0), FloatObject(largeur), FloatObject(hauteur)]
                ),
                NameObject("/Resources"): DictionaryObject(
                    {
                        NameObject("/Font"): DictionaryObject(
                            {NameObject("/VkHelv"): writer._add_object(HELVETICA)}
                        )
                    }
                ),
            }
        )
        annotation = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/FreeText"),
                NameObject("/Rect"): ArrayObject(
                    [FloatObject(v) for v in (x0 - 1, y0 - 1, x1 + 1, y1 + 1)]
                ),
                NameObject("/Contents"): TextStringObject("8888,00"),
                NameObject("/DA"): TextStringObject("/Helv 11 Tf 0 g"),
                NameObject("/F"): NumberObject(4),
                NameObject("/AP"): DictionaryObject(
                    {NameObject("/N"): writer._add_object(apparence)}
                ),
            }
        )
        ref = writer._add_object(annotation)
        annotations = page.get("/Annots")
        anciennes = list(annotations.get_object()) if annotations is not None else []
        page[NameObject("/Annots")] = ArrayObject([*anciennes, ref])

    retoucher(document, ICI / "annotation.pdf", annoter)

    with tempfile.TemporaryDirectory() as dossier:
        autre = Path(dossier) / "autre.pdf"
        ghostscript(AUTRE_PS, autre)
        ajout = PdfReader(autre).pages[0]
        retoucher(gs, ICI / "fusion.pdf", lambda w, p: p.merge_page(ajout))

    ressources = PdfReader(gs).pages[0]["/Resources"]["/Font"]
    helvetica = next(n for n in ressources if "Helvetica" in str(ressources[n]["/BaseFont"]))
    retoucher(
        gs,
        ICI / "hors_plage.pdf",
        lambda w, p: ajouter_contenu(
            w, p, f"BT {helvetica} 14 Tf 72 540 Td (xyz 999) Tj ET\n".encode()
        ),
    )

    oracle = {
        "montant": {"page": 1, "boite": [x0, y0, x1, y1]},
        "echantillons": {},
    }
    for chemin in sorted(ICI.glob("*.pdf")):
        oracle["echantillons"][chemin.stem] = {
            "polices": polices(chemin),
            "mots": mots(chemin),
        }
    (ICI / "oracle.json").write_text(
        json.dumps(oracle, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
