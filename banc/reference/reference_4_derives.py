"""Phase 4 du corpus de référence (T100) : fichiers dérivés, fabriqués sur le poste (ADR-0275).

À partir des originaux téléchargés en phase 3, avec les outils du poste (ImageMagick, ffmpeg,
Ghostscript, LibreOffice sans affichage) :

- **transformés** : chaque original tiré subit toutes les transformations de sa famille
  (:data:`TRANSFORMATIONS`) : recompression, réduction, capture d'écran et passage par une
  messagerie simulés, conversions ;
- **retouchés** : chaque original authentique tiré subit une retouche de sa famille
  (:data:`RETOUCHES`), à tour de rôle ; un collage prend sa pièce dans un autre original de la
  même partie ;
- **malformés** : troncature, octets altérés ou en-tête altéré, à tour de rôle, plus des fichiers
  piégés fabriqués de toutes pièces (:func:`pieges`), sans original ;
- **générés** : les textes écrits par l'assistant (``textes-ia/``), en texte brut, DOCX, ODT et
  PDF.

Un dérivé est dans le groupe et la partie de son original. Les retouches qui passent par
l'interface de LibreOffice sont confiées à la phase 5 (``uno.json``). ``derives.jsonl`` décrit
chaque fichier produit ou confié ; reprend là où il s'est arrêté (par le chemin).
"""

from __future__ import annotations

import io
import json
import random
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib
from collections.abc import Callable
from pathlib import Path

from banc.reference.reference_commun import GRAINE, ICI, Fiche, ecrire_jsonl, lire_jsonl

CHOIX = ICI / "choix.jsonl"
TELECHARGEMENTS = ICI / "telechargements.jsonl"
SORTIE = ICI / "derives.jsonl"
TACHES_UNO = ICI / "uno.json"
TEXTES_IA = ICI / "textes-ia"
GENERATEUR_TEXTES = "Claude Opus 5.5 (claude-opus-5-5), dans Claude Code, pendant T100"
DUREE_MAX = 600

DERIVES: dict[str, tuple[int, int, int]] = {
    # format : originaux tirés pour (transformés, retouchés, malformés)
    "jpeg": (100, 100, 20),
    "png": (30, 30, 10),
    "webp": (20, 20, 5),
    "ia": (120, 0, 10),
    "pdf": (60, 60, 20),
    "mp3": (20, 15, 5),
    "wav": (20, 15, 5),
    "ogg": (10, 10, 5),
    "flac": (10, 10, 5),
    "webm": (60, 30, 15),
    "docx": (45, 45, 15),
    "odt": (15, 15, 5),
    "texte": (60, 60, 10),
}
TRANSFORMATIONS = {
    "image": ("recompression", "reduction", "capture-ecran", "messagerie", "conversion-heic"),
    "pdf": ("recompression", "rasterisation"),
    "audio": ("reencodage", "conversion-m4a"),
    "video": ("reencodage", "conversion-mp4"),
    "bureau": ("conversion", "export-pdf"),
    "texte": ("fins-de-ligne-crlf", "export-docx"),
}
RETOUCHES = {
    "image": ("clonage", "collage", "effacement", "texte-ajoute"),
    "pdf": ("surimpression", "edition-libreoffice"),
    "audio": ("coupure",),
    "video": ("coupure",),
    "bureau": ("paragraphe-ajoute", "remplacement"),
    "texte": ("collage", "chiffres-changes"),
}
ALTERATIONS = ("troncature", "octets-alteres", "entete-altere")
LEGENDES = ("© 2019", "12/03/2018", "Photo : archives", "Exclusif", "Document interne")
"""Textes ajoutés aux images retouchées : courts, sans contenu écrit par une IA."""


def outil(commande: list[str]) -> str:
    """Première ligne de la version d'un outil, pour la provenance."""
    resultat = subprocess.run(commande, capture_output=True, text=True, check=False)  # noqa: S603
    return (resultat.stdout or resultat.stderr).splitlines()[0].strip()


OUTILS: dict[str, str] = {}


def version(nom: str) -> str:
    if nom not in OUTILS:
        commandes = {
            "magick": ["magick", "-version"],
            "ffmpeg": ["ffmpeg", "-hide_banner", "-version"],
            "gs": ["gs", "--version"],
            "soffice": ["soffice", "--version"],
        }
        texte = outil(commandes[nom])
        if nom == "gs":
            texte = f"Ghostscript {texte}"
        OUTILS[nom] = re.sub(r"\s+https?://\S+.*$", "", texte)[:120]
    return OUTILS[nom]


def lancer(commande: list[str]) -> None:
    subprocess.run(  # noqa: S603 (outils du poste, arguments construits ici)
        commande, check=True, capture_output=True, timeout=DUREE_MAX
    )


def chemin(relatif: str) -> Path:
    return ICI.joinpath(*relatif.split("/"))


def derive_de(original: Fiche, categorie: str, operation: str, extension: str) -> str:
    dossier = {"transforme": "transformes", "retouche": "retouches", "malforme": "malformes"}
    return f"{dossier[categorie]}/{original['famille']}/{original['id']}.{operation}.{extension}"


# --- Transformations ---------------------------------------------------------------------------


def transformer(original: Fiche, operation: str, sortie_relative: str) -> tuple[str, str]:
    """Produit le fichier ; rend l'outil et la description de l'opération."""
    entree = chemin(original["chemin"])
    sortie = chemin(sortie_relative)
    famille = original["famille"]
    if famille == "image":
        commandes = {
            "recompression": (["-quality", "75"], "JPEG de qualité 75"),
            "reduction": (["-resize", "50%"], "réduction de moitié, même format"),
            "capture-ecran": (
                [
                    "-auto-orient",
                    "-resize",
                    "1920x1080>",
                    "-strip",
                    "-define",
                    "png:exclude-chunks=date,time",
                ],
                "capture d'écran simulée : au plus 1920 par 1080, sans métadonnées, PNG",
            ),
            "messagerie": (
                ["-auto-orient", "-resize", "1600x1600>", "-strip", "-quality", "80"],
                "messagerie simulée : au plus 1600 pixels, sans métadonnées, JPEG de qualité 80",
            ),
            "conversion-heic": (["-quality", "80"], "conversion en HEIC de qualité 80"),
        }
        arguments, description = commandes[operation]
        prefixe = "PNG24:" if operation == "capture-ecran" else ""
        lancer(["magick", f"{entree}[0]", *arguments, f"{prefixe}{sortie}"])
        return version("magick"), description
    if famille == "pdf":
        if operation == "recompression":
            arguments = ["-sDEVICE=pdfwrite", "-dPDFSETTINGS=/ebook"]
            description = "réécriture par Ghostscript, réglages « ebook »"
        else:
            arguments = ["-sDEVICE=pdfimage24", "-r150"]
            description = "pages rendues en images à 150 ppp, PDF d'images"
        lancer(
            [
                "gs",
                "-q",
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                *arguments,
                "-o",
                str(sortie),
                str(entree),
            ]
        )
        return version("gs"), description
    if famille in {"audio", "video"}:
        arguments, description = parametres_ffmpeg(original, operation)
        lancer(
            [
                "ffmpeg",
                "-nostdin",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(entree),
                *arguments,
                str(sortie),
            ]
        )
        return version("ffmpeg"), description
    if famille == "bureau":
        return convertir_bureau(entree, sortie, operation)
    # texte
    if operation == "fins-de-ligne-crlf":
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_bytes(entree.read_bytes().replace(b"\n", b"\r\n"))
        return "script du corpus", "fins de ligne CRLF, comme un texte copié sous Windows"
    return convertir_bureau(entree, sortie, operation)


def parametres_ffmpeg(original: Fiche, operation: str) -> tuple[list[str], str]:
    format_ = original["format"]
    if operation == "conversion-m4a":
        return ["-vn", "-c:a", "aac", "-b:a", "128k"], "conversion en AAC 128 kbit/s, conteneur M4A"
    if operation == "conversion-mp4":
        return (
            [
                # Côtés ramenés à un nombre pair et pixels en 4:2:0, que H.264 exige du lecteur
                # courant ; sans cela, une vidéo de largeur impaire échoue.
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
            ],
            "conversion en H.264 et AAC, conteneur MP4",
        )
    reencodages = {
        "mp3": (["-c:a", "libmp3lame", "-b:a", "96k"], "réencodage MP3 96 kbit/s"),
        "wav": (["-c:a", "pcm_s16le", "-ar", "22050"], "réencodage PCM 16 bits, 22 050 Hz"),
        "ogg": (["-vn", "-c:a", "libvorbis", "-q:a", "2"], "réencodage Vorbis, qualité 2"),
        "flac": (
            ["-c:a", "flac", "-compression_level", "8", "-ar", "22050"],
            "réencodage FLAC, 22 050 Hz",
        ),
        "webm": (
            [
                "-c:v",
                "libvpx-vp9",
                "-crf",
                "45",
                "-b:v",
                "0",
                "-deadline",
                "realtime",
                # Réglage le plus rapide et encodage sur plusieurs fils : sinon une vidéo HD de
                # quelques secondes dépasse la durée permise (DUREE_MAX).
                "-cpu-used",
                "8",
                "-row-mt",
                "1",
                "-threads",
                "4",
                "-c:a",
                "libopus",
            ],
            "réencodage VP9 et Opus, qualité réduite",
        ),
    }
    return reencodages[format_]


def convertir_bureau(entree: Path, sortie: Path, operation: str) -> tuple[str, str]:
    """Conversion par LibreOffice sans affichage, dans un dossier temporaire puis renommée."""
    cibles = {
        ".odt": ("odt", "conversion en ODT par LibreOffice"),
        ".docx": ("docx:MS Word 2007 XML", "conversion en DOCX par LibreOffice"),
        ".pdf": ("pdf:writer_pdf_Export", "export en PDF par LibreOffice"),
    }
    filtre, description = cibles[sortie.suffix]
    if operation == "export-docx":
        description = "texte ouvert puis enregistré en DOCX par LibreOffice"
    with tempfile.TemporaryDirectory() as temporaire:
        dossier = Path(temporaire)
        commande = [
            "soffice",
            f"-env:UserInstallation={(dossier / 'profil').as_uri()}",
            "--headless",
            "--norestore",
        ]
        if entree.suffix == ".txt":
            commande.append("--infilter=Text (encoded):UTF8,LF,,,")
        lancer([*commande, "--convert-to", filtre, "--outdir", str(dossier), str(entree)])
        produit = dossier / (entree.stem + sortie.suffix)
        if not produit.exists():
            raise subprocess.CalledProcessError(1, "soffice")
        sortie.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(produit, sortie)
    return version("soffice"), description


def extension_transformee(original: Fiche, operation: str) -> str:
    famille = original["famille"]
    extension = str(original["chemin"]).rsplit(".", 1)[1]
    table = {
        "recompression": "jpg" if famille == "image" else extension,
        "capture-ecran": "png",
        "messagerie": "jpg",
        "conversion-heic": "heic",
        "conversion-m4a": "m4a",
        "conversion-mp4": "mp4",
        "export-pdf": "pdf",
        "export-docx": "docx",
        "conversion": "odt" if extension == "docx" else "docx",
    }
    return table.get(operation, extension)


# --- Retouches ---------------------------------------------------------------------------------


def dimensions(fichier: Path) -> tuple[int, int]:
    resultat = subprocess.run(  # noqa: S603
        ["magick", "identify", "-format", "%w %h", f"{fichier}[0]"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
        timeout=DUREE_MAX,
    )
    largeur, hauteur = resultat.stdout.split()
    return int(largeur), int(hauteur)


def retoucher_image(
    original: Fiche, operation: str, sortie: Path, donneur: Fiche | None, hasard: random.Random
) -> str:
    entree = chemin(original["chemin"])
    largeur, hauteur = dimensions(entree)
    w, h = max(8, largeur // 5), max(8, hauteur // 5)
    x1, y1 = hasard.randrange(0, largeur - w), hasard.randrange(0, hauteur - h)
    x2, y2 = hasard.randrange(0, largeur - w), hasard.randrange(0, hauteur - h)
    qualite = ["-quality", "92"] if sortie.suffix == ".jpg" else []
    source = f"{entree}[0]"
    if operation == "clonage":
        arguments = ["(", "+clone", "-crop", f"{w}x{h}+{x1}+{y1}", "+repage", ")"]
        arguments += ["-geometry", f"+{x2}+{y2}", "-composite"]
        description = "zone d'un cinquième des côtés copiée ailleurs dans l'image"
    elif operation == "collage":
        if donneur is None:
            raise ValueError("collage sans donneur")
        piece = f"{chemin(donneur['chemin'])}[0]"
        arguments = [
            "(",
            piece,
            "-resize",
            f"{w}x{h}^",
            "-gravity",
            "center",
            "-extent",
            f"{w}x{h}",
            ")",
        ]
        arguments += ["-gravity", "northwest", "-geometry", f"+{x2}+{y2}", "-composite"]
        description = f"pièce de {donneur['id']} collée dans l'image"
    elif operation == "effacement":
        arguments = ["(", "+clone", "-crop", f"{w}x{h}+{x1}+{y1}", "+repage", "-blur", "0x12", ")"]
        arguments += ["-geometry", f"+{x1}+{y1}", "-composite"]
        description = "zone floutée sur place, comme un objet effacé"
    else:
        legende = hasard.choice(LEGENDES)
        taille = max(12, hauteur // 25)
        arguments = ["-gravity", "southeast", "-font", "DejaVu-Sans", "-pointsize", str(taille)]
        arguments += ["-fill", "white", "-stroke", "black", "-annotate", "+20+20", legende]
        description = f"légende « {legende} » ajoutée"
    lancer(["magick", source, *arguments, *qualite, str(sortie)])
    return description + " (métadonnées de l'original gardées par ImageMagick)"


def retoucher_pdf_ghostscript(original: Fiche, sortie: Path) -> str:
    """Un rectangle blanc et un texte posés sur la première page, PDF réécrit par Ghostscript."""
    procedure = (
        "<< /EndPage { exch pop 0 eq { gsave 1 setgray 72 72 180 28 rectfill "
        "0 setgray /Helvetica findfont 14 scalefont setfont 78 80 moveto "
        "(Montant : 1 250 EUR) show "
        "grestore } if true } >> setpagedevice"
    )
    entree = chemin(original["chemin"])
    lancer(
        [
            "gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
            "-o", str(sortie), "-c", procedure, "-f", str(entree),
        ]
    )  # fmt: skip
    return "rectangle blanc et montant posés sur la première page, PDF réécrit par Ghostscript"


def couper(original: Fiche, sortie: Path) -> str:
    """Le cinquième central de la durée retiré, les deux morceaux recollés."""
    entree = chemin(original["chemin"])
    resultat = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(entree),
        ],
        capture_output=True, text=True, check=True, timeout=DUREE_MAX,
    )  # fmt: skip
    duree = float(resultat.stdout.strip())
    debut, fin = duree * 0.4, duree * 0.6
    arguments, _ = parametres_ffmpeg(original, "reencodage")
    if original["format"] == "webm":
        filtre = (
            f"[0:v]trim=0:{debut:.3f},setpts=PTS-STARTPTS[v0];"
            f"[0:v]trim={fin:.3f},setpts=PTS-STARTPTS[v1];"
            "[v0][v1]concat=n=2:v=1:a=0[v]"
        )
        carte = ["-map", "[v]"]
        arguments = [a for a in arguments if a not in {"-c:a", "libopus"}] + ["-an"]
    else:
        filtre = (
            f"[0:a]atrim=0:{debut:.3f},asetpts=PTS-STARTPTS[a0];"
            f"[0:a]atrim={fin:.3f},asetpts=PTS-STARTPTS[a1];"
            "[a0][a1]concat=n=2:v=0:a=1[a]"
        )
        carte = ["-map", "[a]"]
        arguments = [a for a in arguments if a not in {"-ar", "22050"}]
    lancer(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(entree),
         "-filter_complex", filtre, *carte, *arguments, str(sortie)]
    )  # fmt: skip
    return f"passage de {debut:.1f} s à {fin:.1f} s retiré, morceaux recollés"


def retoucher_texte(original: Fiche, operation: str, sortie: Path, donneur: Fiche | None) -> str:
    texte = chemin(original["chemin"]).read_text(encoding="utf-8")
    if operation == "collage":
        if donneur is None:
            raise ValueError("collage sans donneur")
        piece = chemin(donneur["chemin"]).read_text(encoding="utf-8").split("\n\n")[0]
        paragraphes = texte.rstrip("\n").split("\n\n")
        paragraphes.insert(min(1, len(paragraphes)), piece)
        resultat = "\n\n".join(paragraphes) + "\n"
        description = f"premier paragraphe de {donneur['id']} inséré"
    else:
        resultat = re.sub(r"\d", lambda m: str((int(m.group()) + 3) % 10), texte, count=12)
        if resultat == texte:
            resultat = texte.replace(" ", "  ", 3)
            description = "trois espaces doublées (aucun chiffre à changer)"
        else:
            description = "douze premiers chiffres changés"
    sortie.write_text(resultat, encoding="utf-8", newline="\n")
    return description


# --- Malformés ---------------------------------------------------------------------------------


def alterer(original: Fiche, operation: str, sortie: Path, hasard: random.Random) -> str:
    octets = bytearray(chemin(original["chemin"]).read_bytes())
    if operation == "troncature":
        garde = max(1, len(octets) // 2)
        sortie.write_bytes(bytes(octets[:garde]))
        return f"tronqué à {garde} octets sur {len(octets)}"
    if operation == "octets-alteres":
        debut, fin = len(octets) // 3, max(len(octets) // 3 + 1, 2 * len(octets) // 3)
        for _ in range(32):
            position = hasard.randrange(debut, fin)
            octets[position] ^= 1 << hasard.randrange(8)
        sortie.write_bytes(bytes(octets))
        return "32 bits inversés dans le tiers central"
    for position in range(4, min(36, len(octets))):
        octets[position] = hasard.randrange(256)
    sortie.write_bytes(bytes(octets))
    return "octets 4 à 35 remplacés au hasard, signature de format gardée"


def png_morceau(type_: bytes, donnees: bytes) -> bytes:
    return (
        struct.pack(">I", len(donnees))
        + type_
        + donnees
        + struct.pack(">I", zlib.crc32(type_ + donnees))
    )


def pieges() -> dict[str, tuple[bytes, str]]:
    """Fichiers piégés fabriqués de toutes pièces : nom → (octets, description)."""
    resultat: dict[str, tuple[bytes, str]] = {}
    # PNG de 20 000 par 20 000 pixels, 1,2 Go une fois décompressé.
    compresseur = zlib.compressobj(9)
    ligne = b"\x00" + bytes(3 * 20000)
    flux = io.BytesIO()
    for _ in range(20000):
        flux.write(compresseur.compress(ligne))
    flux.write(compresseur.flush())
    ihdr = struct.pack(">IIBBBBB", 20000, 20000, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + png_morceau(b"IHDR", ihdr) + png_morceau(b"IDAT", flux.getvalue())
    resultat["png-bombe.png"] = (
        png + png_morceau(b"IEND", b""),
        "PNG de 20 000 par 20 000 pixels (1,2 Go décompressé)",
    )
    # JPEG qui annonce 65 500 par 65 500 pixels, sans données d'image.
    sof = (
        b"\xff\xc0"
        + struct.pack(">HBHHB", 17, 8, 65500, 65500, 3)
        + b"\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    )
    resultat["jpeg-geant.jpg"] = (
        b"\xff\xd8" + sof + b"\xff\xd9",
        "JPEG qui annonce 65 500 par 65 500 pixels, sans données",
    )
    # DOCX et ODT dont la partie principale fait 1 Gio une fois décompressée.
    for nom, partie, type_ in (
        ("docx-bombe.docx", "word/document.xml", None),
        ("odt-bombe.odt", "content.xml", "application/vnd.oasis.opendocument.text"),
    ):
        tampon = io.BytesIO()
        with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            if type_ is not None:
                archive.writestr(
                    zipfile.ZipInfo("mimetype"), type_, compress_type=zipfile.ZIP_STORED
                )
            else:
                archive.writestr(
                    "[Content_Types].xml",
                    '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
                    'package/2006/content-types"><Override PartName="/word/document.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.'
                    'wordprocessingml.document.main+xml"/></Types>',
                )
            with archive.open(partie, "w", force_zip64=True) as sortie:
                sortie.write(b"<?xml version='1.0'?><a>")
                bloc = b" " * (1 << 20)
                for _ in range(1024):
                    sortie.write(bloc)
                sortie.write(b"</a>")
        resultat[nom] = (tampon.getvalue(), f"{partie} de 1 Gio une fois décompressé")
    # PDF : tableaux imbriqués sur 100 000 niveaux ; arbre des pages qui boucle.
    imbrique = b"[" * 100000 + b"]" * 100000
    resultat["pdf-imbrication.pdf"] = (
        b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R /X " + imbrique + b" >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R /Size 3 >>\n%%EOF\n",
        "tableaux imbriqués sur 100 000 niveaux, sans table des références",
    )
    corps = (
        b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Pages /Kids [2 0 R] /Count 1 /Parent 2 0 R >>\nendobj\n"
    )
    resultat["pdf-boucle.pdf"] = (
        corps + b"trailer\n<< /Root 1 0 R /Size 4 /Prev 0 >>\nstartxref\n0\n%%EOF\n",
        "arbre des pages qui boucle, table des références qui renvoie au début du fichier",
    )
    # MP3 dont l'étiquette ID3v2 annonce 256 Mio ; WAV dont les tailles débordent.
    resultat["id3-geant.mp3"] = (
        b"ID3\x04\x00\x00"
        + bytes([0x7F, 0x7F, 0x7F, 0x7F])
        + b"TIT2\x7f\x7f\x7f\x7f\x00\x00\x03abc",
        "étiquette ID3v2 qui annonce 256 Mio, trame qui annonce plus encore",
    )
    resultat["wav-debordement.wav"] = (
        b"RIFF\xff\xff\xff\xffWAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00"
        b"\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00LIST\xff\xff\xff\x7fINFOINAM\xf0\xff\xff\xffabc",
        "tailles de RIFF, de LIST et d'INAM qui débordent du fichier",
    )
    # WebM : éléments EBML de taille inconnue imbriqués sur 10 000 niveaux.
    resultat["webm-imbrication.webm"] = (
        b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08"
        b"\x42\x82\x84webm\x42\x87\x81\x04\x42\x85\x81\x02"
        + b"\x18\x53\x80\x67\x01\xff\xff\xff\xff\xff\xff\xff"
        * 10000,
        "segments EBML de taille inconnue imbriqués sur 10 000 niveaux",
    )
    # Textes : un million de diacritiques combinants ; UTF-8 invalide.
    resultat["texte-diacritiques.txt"] = (
        ("a" + "́" * 1_000_000 + "\n").encode("utf-8"),
        "une lettre suivie d'un million de diacritiques combinants",
    )
    resultat["texte-utf8-invalide.txt"] = (
        b"Texte ordinaire, puis des octets invalides : "
        + b"\xc3\x28\xa0\xa1\xe2\x28\xa1\xf0\x28\x8c\xbc\xff\xfe\n",
        "texte dont la fin n'est pas de l'UTF-8 valide",
    )
    return resultat


# --- Orchestration -----------------------------------------------------------------------------


def originaux() -> list[Fiche]:
    telecharges = {f["id"]: f for f in lire_jsonl(TELECHARGEMENTS) if f.get("sha256")}
    return [f for f in lire_jsonl(CHOIX) if f["id"] in telecharges]


def tirer(liste: list[Fiche], nombre: int, cle: str) -> list[Fiche]:
    hasard = random.Random(f"{GRAINE}:{cle}")  # noqa: S311 (tirage reproductible)
    melange = sorted(liste, key=lambda f: str(f["id"]))
    hasard.shuffle(melange)
    return melange[:nombre]


def format_de(original: Fiche) -> str:
    return "ia" if original["categorie"] == "genere" else str(original["format"])


def produire(
    faits: set[str],
    sortie: object,
    fiche: Fiche,
    fabriquer: Callable[[Path], tuple[str, str]],
) -> None:
    """Fabrique un dérivé s'il ne l'est pas déjà, puis l'inscrit ; un échec est inscrit aussi."""
    if fiche["chemin"] in faits:
        return
    cible = chemin(fiche["chemin"])
    cible.parent.mkdir(parents=True, exist_ok=True)
    try:
        outil_, description = fabriquer(cible)
        fiche = {**fiche, "outil": outil_, "description": description, "etat": "fait"}
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
        ValueError,
    ) as erreur:
        cible.unlink(missing_ok=True)
        fiche = {**fiche, "etat": "echec", "erreur": type(erreur).__name__}
    ecrire_jsonl(sortie, fiche)
    faits.add(fiche["chemin"])
    print(f"{fiche['chemin']} : {fiche['etat']}", flush=True)


def base(original: Fiche, categorie: str, operation: str, extension: str) -> Fiche:
    fiche: Fiche = {
        "chemin": derive_de(original, categorie, operation, extension),
        "categorie": categorie,
        "origine": original["origine"] if categorie != "retouche" else "retouche",
        "partie": original["partie"],
        "groupe": original["groupe"],
        "parent": original["id"],
        "operation": operation,
        "famille": original["famille"],
        "licence": original["licence"],
    }
    if categorie == "transforme":
        fiche["transformation"] = operation
    if original.get("generateur") and categorie != "retouche":
        fiche["generateur"] = original["generateur"]
    return fiche


def main() -> None:
    faits = {f["chemin"] for f in lire_jsonl(SORTIE)}
    tous = originaux()
    par_format: dict[str, list[Fiche]] = {}
    for original in tous:
        par_format.setdefault(format_de(original), []).append(original)
    with SORTIE.open("a", encoding="utf-8") as sortie:
        # Textes écrits par l'assistant : générés, en quatre formats.
        for rang, source in enumerate(sorted(TEXTES_IA.glob("ia-*.txt"))):
            identifiant = f"texte-{source.stem}"
            commun = {
                "categorie": "genere",
                "origine": "ia",
                "partie": "calibrage" if rang % 3 == 0 else "evaluation",
                "groupe": identifiant,
                "parent": f"textes-ia/{source.name}",
                "generateur": GENERATEUR_TEXTES,
                "licence": "Apache-2.0",
            }
            for famille, extension in (
                ("texte", "txt"),
                ("bureau", "docx"),
                ("bureau", "odt"),
                ("pdf", "pdf"),
            ):
                fiche = {
                    **commun,
                    "chemin": f"generes/{famille}/{identifiant}.{extension}",
                    "famille": famille,
                }
                if extension == "txt":

                    def copier(cible: Path, source: Path = source) -> tuple[str, str]:
                        cible.write_bytes(source.read_bytes())
                        return "script du corpus", "texte écrit par l'assistant, tel quel"

                    produire(faits, sortie, {**fiche, "operation": "texte"}, copier)
                else:

                    def rendre(cible: Path, source: Path = source) -> tuple[str, str]:
                        outil_, _ = convertir_bureau(source, cible, "rendu")
                        return (
                            outil_,
                            f"texte de l'assistant enregistré en {cible.suffix[1:].upper()} "
                            "par LibreOffice",
                        )

                    produire(faits, sortie, {**fiche, "operation": f"rendu-{extension}"}, rendre)
        for format_, (n_transformes, n_retouches, n_malformes) in DERIVES.items():
            liste = par_format.get(format_, [])
            # Transformés : toutes les transformations de la famille.
            for original in tirer(liste, n_transformes, f"transformes:{format_}"):
                for operation in TRANSFORMATIONS[original["famille"]]:
                    extension = extension_transformee(original, operation)
                    fiche = base(original, "transforme", operation, extension)

                    def faire(
                        _: Path,
                        original: Fiche = original,
                        operation: str = operation,
                        fiche: Fiche = fiche,
                    ) -> tuple[str, str]:
                        return transformer(original, operation, fiche["chemin"])

                    produire(faits, sortie, fiche, faire)
            # Retouchés : une retouche par original, à tour de rôle.
            hasard = random.Random(f"{GRAINE}:retouches:{format_}")  # noqa: S311
            for rang, original in enumerate(tirer(liste, n_retouches, f"retouches:{format_}")):
                retouches = RETOUCHES[original["famille"]]
                operation = retouches[rang % len(retouches)]
                extension = original["chemin"].rsplit(".", 1)[1]
                fiche = base(original, "retouche", operation, extension)
                donneurs = [
                    f
                    for f in liste
                    if f["partie"] == original["partie"] and f["groupe"] != original["groupe"]
                ]
                donneur = (
                    hasard.choice(sorted(donneurs, key=lambda f: str(f["id"])))
                    if donneurs
                    else None
                )
                famille = original["famille"]
                if operation == "edition-libreoffice" or famille == "bureau":
                    if fiche["chemin"] not in faits:
                        ecrire_jsonl(
                            sortie, {**fiche, "etat": "confie", "outil": version("soffice")}
                        )
                        faits.add(fiche["chemin"])
                    continue
                graine = hasard.random()

                def retoucher(
                    cible: Path, original: Fiche = original, operation: str = operation,
                    donneur: Fiche | None = donneur, graine: float = graine,
                ) -> tuple[str, str]:  # fmt: skip
                    famille = original["famille"]
                    if famille == "image":
                        local = random.Random(graine)  # noqa: S311
                        return version("magick"), retoucher_image(
                            original, operation, cible, donneur, local
                        )
                    if famille == "pdf":
                        return version("gs"), retoucher_pdf_ghostscript(original, cible)
                    if famille in {"audio", "video"}:
                        return version("ffmpeg"), couper(original, cible)
                    return "script du corpus", retoucher_texte(original, operation, cible, donneur)

                produire(faits, sortie, fiche, retoucher)
            # Malformés : une altération par original, à tour de rôle.
            for rang, original in enumerate(tirer(liste, n_malformes, f"malformes:{format_}")):
                operation = ALTERATIONS[rang % len(ALTERATIONS)]
                extension = original["chemin"].rsplit(".", 1)[1]
                fiche = base(original, "malforme", operation, extension)
                graine = random.Random(f"{GRAINE}:{fiche['chemin']}").random()  # noqa: S311

                def abimer(
                    cible: Path,
                    original: Fiche = original,
                    operation: str = operation,
                    graine: float = graine,
                ) -> tuple[str, str]:
                    local = random.Random(graine)  # noqa: S311
                    return "script du corpus", alterer(original, operation, cible, local)

                produire(faits, sortie, fiche, abimer)
        # Pièges fabriqués de toutes pièces : sans origine, chacun son groupe.
        for rang, (nom, (octets, description)) in enumerate(sorted(pieges().items())):
            identifiant = "piege-" + nom.rsplit(".", 1)[0]
            fiche = {
                "chemin": f"malformes/pieges/{nom}",
                "categorie": "malforme",
                "partie": "calibrage" if rang % 3 == 0 else "evaluation",
                "groupe": identifiant,
                "operation": "piege",
                "famille": "pieges",
                "licence": "Apache-2.0",
            }

            def ecrire(
                cible: Path, octets: bytes = octets, description: str = description
            ) -> tuple[str, str]:
                cible.write_bytes(octets)
                return "script du corpus", description

            produire(faits, sortie, fiche, ecrire)
    # Tâches de la phase 5 : toutes celles inscrites, y compris par un passage interrompu avant
    # cette ligne (la liste est refaite à chaque passage, à partir de derives.jsonl).
    chemins = {original["id"]: original["chemin"] for original in tous}
    taches_uno = [
        {**fiche, "entree": chemins[fiche["parent"]]}
        for fiche in lire_jsonl(SORTIE)
        if fiche.get("etat") == "confie"
    ]
    TACHES_UNO.write_text(json.dumps(taches_uno, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
