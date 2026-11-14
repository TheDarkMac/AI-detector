"""Manifestes C2PA d'essai, signés pendant les tests (T30, ADR-0170).

Une autorité de certification d'essai, créée par ``cryptography`` (dépendance de c2pa-python),
signe un certificat de signataire ; c2pa-python écrit le manifeste dans une copie d'un
échantillon du dépôt. Rien n'est téléchargé, et aucun fichier signé n'est gardé dans le dépôt :
les certificats expireraient. La liste de confiance d'essai ne contient que l'autorité d'essai.
"""

import datetime as dt
import io
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import c2pa
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ECHANTILLONS = Path(__file__).parent / "donnees" / "metadonnees"
IPTC = "http://cv.iptc.org/newscodes/digitalsourcetype/"
SIGNATAIRE = "Jeanne Martin"
"""Nom commun du certificat de signature : un nom de personne, masqué par défaut (ES-13)."""
NUMERO = 424242
"""Numéro de série du certificat de signature, masqué par défaut."""
TITRE = "Portrait de Jeanne"
INGREDIENT = "original"
"""Étiquette de l'ingrédient joint, que cite l'action d'ouverture."""

FICHIERS = {
    "jpeg": "photo.jpg",
    "png": "image.png",
    "webp": "image.webp",
    "heic": "image.heic",
    "pdf": "document.pdf",
    "wav": "son.wav",
    "mp3": "son.mp3",
    "m4a": "son.m4a",
    "flac": "son.flac",
    "mp4": "video.mp4",
    "mov": "video.mov",
    "docx": "document.docx",
    "odt": "document.odt",
}
"""Échantillon du dépôt pour chaque format du module c2pa."""


def _nom(nom_commun: str) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, nom_commun),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Essai"),
        ]
    )


def _pem(certificat: x509.Certificate) -> bytes:
    return certificat.public_bytes(serialization.Encoding.PEM)


@dataclass(frozen=True)
class Autorite:
    """Autorité d'essai et signataire qu'elle a certifié."""

    racine: bytes
    """Certificat de l'autorité, en PEM : la seule ancre de la liste d'essai."""
    chaine: bytes
    cle: bytes

    def signataire(self) -> Any:
        info = c2pa.C2paSignerInfo(
            alg=b"es256", sign_cert=self.chaine, private_key=self.cle, ta_url=None
        )
        return c2pa.Signer.from_info(info)


@cache
def autorite() -> Autorite:
    """Autorité d'essai, une par session de tests."""
    maintenant = dt.datetime.now(dt.UTC)
    cle_racine = ec.generate_private_key(ec.SECP256R1())
    racine = (
        x509.CertificateBuilder()
        .subject_name(_nom("Autorité d'essai"))
        .issuer_name(_nom("Autorité d'essai"))
        .public_key(cle_racine.public_key())
        .serial_number(1)
        .not_valid_before(maintenant - dt.timedelta(days=1))
        .not_valid_after(maintenant + dt.timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, True, True, False, False),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(cle_racine.public_key()), critical=False
        )
        .sign(cle_racine, hashes.SHA256())
    )
    cle = ec.generate_private_key(ec.SECP256R1())
    certificat = (
        x509.CertificateBuilder()
        .subject_name(_nom(SIGNATAIRE))
        .issuer_name(racine.subject)
        .public_key(cle.public_key())
        .serial_number(NUMERO)
        .not_valid_before(maintenant - dt.timedelta(days=1))
        .not_valid_after(maintenant + dt.timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, False, False, False, False),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.EMAIL_PROTECTION]), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(cle_racine.public_key()),
            critical=False,
        )
        .sign(cle_racine, hashes.SHA256())
    )
    privee = cle.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return Autorite(_pem(racine), _pem(certificat) + _pem(racine), privee)


def ecrire_liste(dossier: Path, signataires: bytes | None = None) -> Path:
    """Liste de confiance d'essai : l'autorité d'essai seule, sauf ``signataires`` donné."""
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "confiance.toml").write_text(
        'format = 1\nnom = "Liste d\'essai"\nversion = "1"\ndate = "2026-11-14"\n'
        'description = "Autorité d\'essai des tests."\n',
        encoding="utf-8",
    )
    (dossier / "signataires.pem").write_bytes(
        autorite().racine if signataires is None else signataires
    )
    return dossier


def manifeste(source: str | None = "trainedAlgorithmicMedia", **champs: Any) -> dict[str, Any]:
    """Manifeste d'une création de source numérique IPTC ``source``, ou de l'ouverture d'un
    ingrédient sans source ; ``champs`` le complète."""
    # c2pa-rs exige une source numérique pour une création ; sans source, l'ouverture d'un
    # ingrédient, qu'il faut alors joindre (``signer(ingredient=...)``).
    action: dict[str, Any] = {
        "action": "c2pa.opened",
        "softwareAgent": {"name": "GenX"},
        "parameters": {"ingredientIds": [INGREDIENT]},
    }
    if source is not None:
        action = {
            "action": "c2pa.created",
            "softwareAgent": {"name": "GenX"},
            "digitalSourceType": IPTC + source,
        }
    return {
        "claim_generator_info": [{"name": "GenX", "version": "2.1"}],
        "title": TITRE,
        "assertions": [{"label": "c2pa.actions", "data": {"actions": [action]}}],
        **champs,
    }


def _builder(definition: dict[str, Any]) -> Any:
    contexte = c2pa.Context.from_dict({"builder": {"thumbnail": {"enabled": False}}})
    return c2pa.Builder(json.dumps(definition), context=contexte)


def signer(
    format_: str = "jpeg",
    definition: dict[str, Any] | None = None,
    *,
    contenu: bytes | None = None,
    ingredient: bytes | None = None,
) -> bytes:
    """Échantillon du format, ou ``contenu``, signé avec ``definition`` (par défaut, IA)."""
    from voight_kampff.modules.c2pa import FORMATS

    type_ = FORMATS[format_]
    builder = _builder(manifeste() if definition is None else definition)
    if ingredient is not None:
        builder.add_ingredient(
            json.dumps({"title": "Original", "relationship": "parentOf", "label": INGREDIENT}),
            type_,
            io.BytesIO(ingredient),
        )
    source = (ECHANTILLONS / FICHIERS[format_]).read_bytes() if contenu is None else contenu
    cible = io.BytesIO()
    builder.sign(autorite().signataire(), type_, io.BytesIO(source), cible)
    return cible.getvalue()


def signer_distant(adresse: str, format_: str = "jpeg") -> bytes:
    """Échantillon dont le manifeste n'est pas intégré : le fichier ne porte que son adresse."""
    from voight_kampff.modules.c2pa import FORMATS

    builder = _builder(manifeste())
    builder.set_no_embed()
    builder.set_remote_url(adresse)
    cible = io.BytesIO()
    source = io.BytesIO((ECHANTILLONS / FICHIERS[format_]).read_bytes())
    builder.sign(autorite().signataire(), FORMATS[format_], source, cible)
    return cible.getvalue()
