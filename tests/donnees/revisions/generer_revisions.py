"""Échantillons et oracle du module revisionspdf (T50, ADR-0207 à ADR-0212).

Chaque échantillon part d'une page écrite par Ghostscript (flux de références croisées et flux
d'objets) ou par LibreOffice (table classique), puis reçoit des mises à jour incrémentales
écrites par pyHanko, comme les écrirait un logiciel de signature ou de formulaire :

- ``formulaire.pdf`` : champ de texte et champ de signature ajoutés, puis le champ rempli ;
- ``signe.pdf`` : ``formulaire.pdf`` signé (signature d'approbation) ;
- ``signe_annote.pdf`` : ``signe.pdf`` puis une annotation de texte ;
- ``signe_modifie.pdf`` : ``signe.pdf`` puis un flux de contenu ajouté à la page ;
- ``modifie.pdf`` : page de LibreOffice, puis un flux de contenu ajouté ;
- ``certifie.pdf`` : page de Ghostscript certifiée, aucune modification permise (DocMDP 1) ;
- ``lineaire.pdf`` : deux pages linéarisées par Ghostscript (``-dFastWebView``), puis
  ``lineaire_maj.pdf`` : le même, auteur écrit par exiftool en mise à jour incrémentale.

La clé et le certificat de signature sont tirés à chaque génération et ne sont pas gardés.
``oracle.json`` consigne ensuite, pour chaque échantillon, ce qu'en disent pyHanko (nombre de
révisions, couverture et niveau de modification de chaque signature, droits DocMDP) et
``pdfsig`` de Poppler (signature couvrant tout le document ou non).

Outils de la version du dépôt : Ghostscript 10.05.1, LibreOffice 25.2.3.2, exiftool 13.25,
pdfsig de Poppler 25.03.0, pyHanko 0.38.1 (pyhanko-certvalidator 0.33.0, cryptography
50.0.2), sous Debian 13. À lancer depuis ce dossier, avec l'interpréteur d'un environnement où
pyHanko est installé : ``python -I generer_revisions.py``. Les PDF changent à chaque génération
(dates, identifiants, clé) : ne régénérer que pour changer les échantillons.
"""
# mypy: ignore-errors
# (pyHanko et asn1crypto ne sont pas dans l'environnement du projet.)

import datetime
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from asn1crypto import keys, x509
from cryptography import x509 as cx509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.registry import SimpleCertificateStore

ICI = Path(__file__).resolve().parent


def outil(nom: str) -> str:
    """Chemin complet d'un outil du poste."""
    chemin = shutil.which(nom)
    if chemin is None:
        raise SystemExit(f"{nom} introuvable")
    return chemin


PAGE_PS = b"%!PS\n/Helvetica findfont 12 scalefont setfont 72 720 moveto (Bonjour) show showpage\n"
DEUX_PAGES_PS = PAGE_PS.replace(b"showpage\n", b"showpage 72 720 moveto (Page 2) show showpage\n")


def certificat() -> tuple[x509.Certificate, keys.PrivateKeyInfo, cx509.Certificate]:
    cle = ec.generate_private_key(ec.SECP256R1())
    nom = cx509.Name([cx509.NameAttribute(NameOID.COMMON_NAME, "Signataire d'essai")])
    maintenant = datetime.datetime.now(datetime.UTC)
    brut = (
        cx509.CertificateBuilder()
        .subject_name(nom)
        .issuer_name(nom)
        .public_key(cle.public_key())
        .serial_number(cx509.random_serial_number())
        .not_valid_before(maintenant - datetime.timedelta(days=1))
        .not_valid_after(maintenant + datetime.timedelta(days=3650))
        .add_extension(
            cx509.KeyUsage(True, True, False, False, False, False, False, False, False), True
        )
        .sign(cle, hashes.SHA256())
    )
    der = brut.public_bytes(serialization.Encoding.DER)
    privee = cle.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return x509.Certificate.load(der), keys.PrivateKeyInfo.load(privee), brut


def ghostscript(source: bytes, sortie: Path, *options: str) -> None:
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
                *options,
                f"-sOutputFile={sortie}",
                str(page),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )


def libreoffice(sortie: Path) -> None:
    with tempfile.TemporaryDirectory() as dossier:
        texte = Path(dossier) / "document.txt"
        texte.write_text("Bonjour\n", encoding="utf-8")
        subprocess.run(
            [
                outil("libreoffice"),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                dossier,
                str(texte),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        shutil.copy(Path(dossier) / "document.pdf", sortie)


def ecrire(chemin: Path, modifier: Callable[[IncrementalPdfFileWriter], object]) -> None:
    """Une mise à jour incrémentale de ``chemin`` par ``modifier(écrivain)``."""
    with chemin.open("rb+") as fichier:
        ecrivain = IncrementalPdfFileWriter(fichier, strict=False)
        modifier(ecrivain)
        ecrivain.write_in_place()


def premiere_page(
    ecrivain: IncrementalPdfFileWriter,
) -> tuple[generic.IndirectObject, generic.DictionaryObject]:
    reference = ecrivain.root["/Pages"]["/Kids"].raw_get(0)
    return reference, reference.get_object()


def police(ecrivain: IncrementalPdfFileWriter) -> generic.IndirectObject:
    return ecrivain.add_object(
        generic.DictionaryObject(
            {
                generic.NameObject("/Type"): generic.NameObject("/Font"),
                generic.NameObject("/Subtype"): generic.NameObject("/Type1"),
                generic.NameObject("/BaseFont"): generic.NameObject("/Helvetica"),
            }
        )
    )


def ajouter_champs(ecrivain: IncrementalPdfFileWriter) -> None:
    """Champ de texte « Nom » (sans valeur) et le formulaire qui le contient."""
    page_ref, page = premiere_page(ecrivain)
    helv = police(ecrivain)
    champ = ecrivain.add_object(
        generic.DictionaryObject(
            {
                generic.NameObject("/Type"): generic.NameObject("/Annot"),
                generic.NameObject("/Subtype"): generic.NameObject("/Widget"),
                generic.NameObject("/FT"): generic.NameObject("/Tx"),
                generic.NameObject("/T"): generic.TextStringObject("Nom"),
                generic.NameObject("/Rect"): generic.ArrayObject(
                    [generic.FloatObject(v) for v in (72, 600, 300, 620)]
                ),
                generic.NameObject("/F"): generic.NumberObject(4),
                generic.NameObject("/P"): page_ref,
                generic.NameObject("/DA"): generic.TextStringObject("/Helv 12 Tf 0 g"),
            }
        )
    )
    ressources = generic.DictionaryObject(
        {generic.NameObject("/Font"): generic.DictionaryObject({generic.NameObject("/Helv"): helv})}
    )
    formulaire = ecrivain.add_object(
        generic.DictionaryObject(
            {
                generic.NameObject("/Fields"): generic.ArrayObject([champ]),
                generic.NameObject("/DA"): generic.TextStringObject("/Helv 12 Tf 0 g"),
                generic.NameObject("/DR"): ressources,
            }
        )
    )
    ecrivain.root[generic.NameObject("/AcroForm")] = formulaire
    ecrivain.update_root()
    annotations = page.get("/Annots", generic.ArrayObject())
    annotations.append(champ)
    page[generic.NameObject("/Annots")] = annotations
    ecrivain.update_container(page)


def remplir(ecrivain: IncrementalPdfFileWriter) -> None:
    """Valeur du champ « Nom » et son apparence, comme l'écrit un lecteur de formulaires."""
    formulaire = ecrivain.root["/AcroForm"]
    champ_ref = formulaire["/Fields"].raw_get(0)
    champ = champ_ref.get_object()
    helv = formulaire["/DR"]["/Font"].raw_get("/Helv")
    apparence = generic.StreamObject(
        {
            generic.NameObject("/Type"): generic.NameObject("/XObject"),
            generic.NameObject("/Subtype"): generic.NameObject("/Form"),
            generic.NameObject("/BBox"): generic.ArrayObject(
                [generic.FloatObject(v) for v in (0, 0, 228, 20)]
            ),
            generic.NameObject("/Resources"): generic.DictionaryObject(
                {
                    generic.NameObject("/Font"): generic.DictionaryObject(
                        {generic.NameObject("/Helv"): helv}
                    )
                }
            ),
        },
        stream_data=b"/Tx BMC BT /Helv 12 Tf 0 g 2 5 Td (Jeanne Exemple) Tj ET EMC",
    )
    champ[generic.NameObject("/V")] = generic.TextStringObject("Jeanne Exemple")
    champ[generic.NameObject("/AP")] = generic.DictionaryObject(
        {generic.NameObject("/N"): ecrivain.add_object(apparence)}
    )
    ecrivain.mark_update(champ_ref)


def annoter(ecrivain: IncrementalPdfFileWriter) -> None:
    """Note de texte sur la page, comme en ajoute un lecteur de PDF."""
    page_ref, page = premiere_page(ecrivain)
    note = ecrivain.add_object(
        generic.DictionaryObject(
            {
                generic.NameObject("/Type"): generic.NameObject("/Annot"),
                generic.NameObject("/Subtype"): generic.NameObject("/Text"),
                generic.NameObject("/Rect"): generic.ArrayObject(
                    [generic.FloatObject(v) for v in (400, 700, 420, 720)]
                ),
                generic.NameObject("/Contents"): generic.TextStringObject("Relu"),
                generic.NameObject("/P"): page_ref,
            }
        )
    )
    annotations = page.get("/Annots", generic.ArrayObject())
    annotations.append(note)
    page[generic.NameObject("/Annots")] = annotations
    ecrivain.update_container(page)


def modifier_contenu(ecrivain: IncrementalPdfFileWriter) -> None:
    """Texte ajouté à la page par un second flux de contenu : la page affiche autre chose."""
    _, page = premiere_page(ecrivain)
    helv = police(ecrivain)
    flux = ecrivain.add_object(
        generic.StreamObject(stream_data=b"BT /FAjout 12 Tf 72 690 Td (Montant : 9 000 EUR) Tj ET")
    )
    contenus = page.raw_get("/Contents")
    if not isinstance(contenus, generic.ArrayObject):
        contenus = generic.ArrayObject([contenus])
    contenus.append(flux)
    page[generic.NameObject("/Contents")] = contenus
    anciennes = page["/Resources"]
    ressources = generic.DictionaryObject({cle: anciennes.raw_get(cle) for cle in anciennes})
    polices = generic.DictionaryObject()
    if "/Font" in anciennes:
        polices.update({cle: anciennes["/Font"].raw_get(cle) for cle in anciennes["/Font"]})
    polices[generic.NameObject("/FAjout")] = helv
    ressources[generic.NameObject("/Font")] = polices
    page[generic.NameObject("/Resources")] = ressources
    ecrivain.update_container(page)


def signer(chemin: Path, signataire: signers.SimpleSigner, **options: object) -> None:
    with chemin.open("rb+") as fichier:
        ecrivain = IncrementalPdfFileWriter(fichier, strict=False)
        nom = options.pop("champ", "Signature")
        if nom == "Certification":
            fields.append_signature_field(
                ecrivain, fields.SigFieldSpec(nom, box=(72, 72, 272, 132), on_page=0)
            )
        meta = signers.PdfSignatureMetadata(field_name=nom, **options)
        signers.sign_pdf(ecrivain, meta, signer=signataire, in_place=True)


def oracle(chemin: Path, racine: x509.Certificate) -> dict[str, object]:
    with chemin.open("rb") as fichier:
        lecteur = PdfFileReader(fichier, strict=False)
        signatures = []
        for signature in lecteur.embedded_signatures:
            etat = validate_pdf_signature(signature, ValidationContext(trust_roots=[racine]))
            signatures.append(
                {
                    "champ": signature.field_name,
                    "fin": signature.byte_range[2] + signature.byte_range[3],
                    "intacte": etat.intact,
                    "couverture": etat.coverage.name,
                    "modification": etat.modification_level.name
                    if etat.modification_level is not None
                    else None,
                    "docmdp": signature.docmdp_level.value
                    if signature.docmdp_level is not None
                    else None,
                    "docmdp_respecte": etat.docmdp_ok,
                }
            )
        revisions = lecteur.xrefs.total_revisions
    pdfsig = subprocess.run(
        [outil("pdfsig"), "-nocert", str(chemin)], capture_output=True, text=True, check=False
    ).stdout
    entiers = [ligne.strip() for ligne in pdfsig.splitlines() if "document signed" in ligne]
    return {
        "taille": chemin.stat().st_size,
        "revisions_pyhanko": revisions,
        "signatures": signatures,
        "pdfsig": entiers,
    }


def main() -> None:
    racine, privee, _ = certificat()
    signataire = signers.SimpleSigner(
        signing_cert=racine,
        signing_key=privee,
        cert_registry=SimpleCertificateStore.from_certs([racine]),
    )
    formulaire = ICI / "formulaire.pdf"
    ghostscript(PAGE_PS, formulaire)
    ecrire(formulaire, ajouter_champs)
    ecrire(
        formulaire,
        lambda e: fields.append_signature_field(
            e, fields.SigFieldSpec("Signature", box=(72, 72, 272, 132), on_page=0)
        ),
    )
    ecrire(formulaire, remplir)

    signe = ICI / "signe.pdf"
    shutil.copy(formulaire, signe)
    signer(signe, signataire)
    for nom, modifier in (("signe_annote.pdf", annoter), ("signe_modifie.pdf", modifier_contenu)):
        shutil.copy(signe, ICI / nom)
        ecrire(ICI / nom, modifier)

    modifie = ICI / "modifie.pdf"
    libreoffice(modifie)
    ecrire(modifie, modifier_contenu)

    certifie = ICI / "certifie.pdf"
    ghostscript(PAGE_PS, certifie)
    signer(
        certifie,
        signataire,
        champ="Certification",
        certify=True,
        docmdp_permissions=fields.MDPPerm.NO_CHANGES,
    )

    lineaire = ICI / "lineaire.pdf"
    ghostscript(DEUX_PAGES_PS, lineaire, "-dFastWebView=true")
    shutil.copy(lineaire, ICI / "lineaire_maj.pdf")
    subprocess.run(
        [
            outil("exiftool"),
            "-q",
            "-overwrite_original",
            "-PDF:Author=Jeanne Exemple",
            str(ICI / "lineaire_maj.pdf"),
        ],
        check=True,
    )

    noms = sorted(p.name for p in ICI.glob("*.pdf"))
    resultat = {nom: oracle(ICI / nom, racine) for nom in noms}
    (ICI / "oracle.json").write_text(
        json.dumps(resultat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    json.dump(resultat, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
