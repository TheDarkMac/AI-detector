"""Réponse d'une autorité d'horodatage RFC 3161 réelle, écrite par OpenSSL (T91, ADR-0263).

La requête est celle de l'outil (``horodatage.requete``) pour l'empreinte SHA-256 de
``EMPREINTE_DE`` et le nonce ``NONCE`` ; OpenSSL y répond (``openssl ts -reply``) en autorité
d'essai : une autorité racine et une autorité d'horodatage (usage étendu ``timeStamping``
critique) créées pour l'occasion dans un dossier temporaire, puis effacées avec leurs clés.
OpenSSL vérifie ensuite la réponse (``openssl ts -verify``) contre l'autorité racine, ce qui
établit que l'outil écrit une requête que comprend une autorité réelle, et que la réponse qu'il
lit est vérifiable.

Écrit ``requete.tsq``, ``reponse.tsr`` et ``oracle.json`` (empreinte, nonce, heure, numéro de
série et politique, lus par ``openssl ts -reply -text``). Outil de la version du dépôt : OpenSSL
3.5.9, sous Debian 13. À lancer depuis la racine du dépôt :
``.venv/bin/python tests/donnees/horodatage/generer_horodatage.py``. La réponse change à chaque
génération (heure, clés) : ne régénérer que pour changer l'échantillon.
"""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from voight_kampff._conservation import horodatage

ICI = pathlib.Path(__file__).parent
EMPREINTE_DE = b"Rapport d'essai de l'horodatage.\n"
NONCE = 0x1234_5678_9ABC_DEF0
POLITIQUE = "1.2.3.4.1"
CONFIGURATION = f"""
[ req ]
distinguished_name = dn
prompt = no
[ dn ]
CN = Autorite d'essai
[ ext_racine ]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign
[ ext_horodatage ]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature
extendedKeyUsage = critical,timeStamping
[ tsa ]
default_tsa = essai
[ essai ]
serial = ./serie
signer_cert = ./horodatage.pem
signer_key = ./horodatage.key
certs = ./racine.pem
signer_digest = sha256
default_policy = {POLITIQUE}
digests = sha256
accuracy = secs:1
ordering = no
tsa_name = no
ess_cert_id_chain = no
ess_cert_id_alg = sha256
"""


def openssl(dossier: str, *arguments: str) -> str:
    programme = shutil.which("openssl")
    if programme is None:
        raise SystemExit("openssl introuvable")
    resultat = subprocess.run(
        [programme, *arguments], cwd=dossier, check=True, capture_output=True, text=True
    )
    return resultat.stdout


def main() -> None:
    empreinte = hashlib.sha256(EMPREINTE_DE).digest()
    requete = horodatage.requete(empreinte, NONCE)
    (ICI / "requete.tsq").write_bytes(requete)
    with tempfile.TemporaryDirectory() as dossier:
        d = pathlib.Path(dossier)
        (d / "openssl.cnf").write_text(CONFIGURATION, encoding="ascii")
        (d / "serie").write_text("2a\n", encoding="ascii")
        (d / "requete.tsq").write_bytes(requete)
        cle = ["-newkey", "rsa:2048", "-nodes", "-config", "openssl.cnf"]
        openssl(
            dossier,
            "req",
            "-x509",
            "-new",
            *cle,
            "-keyout",
            "racine.key",
            "-out",
            "racine.pem",
            "-days",
            "36500",
            "-extensions",
            "ext_racine",
            "-subj",
            "/CN=Racine d'essai",
        )
        openssl(
            dossier,
            "req",
            "-new",
            *cle,
            "-keyout",
            "horodatage.key",
            "-out",
            "horodatage.csr",
            "-subj",
            "/CN=Horodatage d'essai",
        )
        openssl(
            dossier,
            "x509",
            "-req",
            "-in",
            "horodatage.csr",
            "-CA",
            "racine.pem",
            "-CAkey",
            "racine.key",
            "-CAcreateserial",
            "-out",
            "horodatage.pem",
            "-days",
            "36500",
            "-extfile",
            "openssl.cnf",
            "-extensions",
            "ext_horodatage",
        )
        openssl(
            dossier,
            "ts",
            "-reply",
            "-config",
            "openssl.cnf",
            "-queryfile",
            "requete.tsq",
            "-out",
            "reponse.tsr",
        )
        (d / "rapport").write_bytes(EMPREINTE_DE)
        openssl(
            dossier,
            "ts",
            "-verify",
            "-data",
            "rapport",
            "-in",
            "reponse.tsr",
            "-CAfile",
            "racine.pem",
            "-untrusted",
            "horodatage.pem",
        )
        texte = openssl(dossier, "ts", "-reply", "-in", "reponse.tsr", "-text")
        reponse = (d / "reponse.tsr").read_bytes()
    (ICI / "reponse.tsr").write_bytes(reponse)
    heure = re.search(r"^Time stamp: (.+)$", texte, re.MULTILINE)
    serie = re.search(r"^Serial number: 0x([0-9A-F]+)$", texte, re.MULTILINE)
    if heure is None or serie is None:
        raise SystemExit("sortie d'openssl inattendue :\n" + texte)
    oracle = {
        "empreinte": empreinte.hex(),
        "nonce": NONCE,
        "heure_openssl": heure.group(1),
        "numero": int(serie.group(1), 16),
        "politique": POLITIQUE,
        "openssl": openssl(".", "version").strip(),
    }
    (ICI / "oracle.json").write_text(json.dumps(oracle, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
