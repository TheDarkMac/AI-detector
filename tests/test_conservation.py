"""Tests du journal de conservation et de l'horodatage des rapports (T91, ADR-0260 à ADR-0263)."""

import contextlib
import hashlib
import http.server
import io
import json
import multiprocessing
import os
import sys
import threading
import urllib.error
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import pytest
from echantillons import PDF
from hypothesis import given, settings
from hypothesis import strategies as st

from voight_kampff import cli
from voight_kampff._conservation import _der, horodatage, journal
from voight_kampff.cli import main

pytestmark = pytest.mark.exigence("NF-17", "ES-16")

DONNEES = Path(__file__).parent / "donnees" / "horodatage"
SHA256 = "2.16.840.1.101.3.4.2.1"
SIGNED_DATA = "1.2.840.113549.1.7.2"
TST_INFO = "1.2.840.113549.1.9.16.1.4"
EMPREINTE = hashlib.sha256(b"rapport").digest()
NONCE = 0x0123_4567_89AB_CDEF


# Réponses construites : la structure d'une TimeStampResp, signature absente (ADR-0263).


def tst_info(
    empreinte: bytes = EMPREINTE,
    nonce: int | None = NONCE,
    *,
    version: int = 1,
    algorithme: str = SHA256,
    heure: bytes = b"20261125103000.25Z",
) -> bytes:
    champs = [
        _der.entier(version),
        _der.oid("1.2.3.4.1"),
        _der.suite(
            _der.suite(_der.oid(algorithme), _der.encoder(_der.NUL, b"")),
            _der.encoder(_der.OCTETS, empreinte),
        ),
        _der.entier(42),
        _der.encoder(_der.HEURE_GENERALISEE, heure),
        _der.suite(_der.entier(1)),  # accuracy
    ]
    if nonce is not None:
        champs.append(_der.entier(nonce))
    return _der.suite(*champs)


def jeton(info: bytes, *, type_contenu: str = TST_INFO, type_jeton: str = SIGNED_DATA) -> bytes:
    encapsule = _der.suite(
        _der.oid(type_contenu), _der.encoder(_der.CONTEXTE_0, _der.encoder(_der.OCTETS, info))
    )
    signees = _der.suite(
        _der.entier(3), _der.encoder(_der.ENSEMBLE, b""), encapsule, _der.encoder(0xA0, b"")
    )
    return _der.suite(_der.oid(type_jeton), _der.encoder(_der.CONTEXTE_0, signees))


def reponse(info: bytes | None = None, *, statut: int = 0, contenu: bytes | None = None) -> bytes:
    corps = jeton(tst_info() if info is None else info) if contenu is None else contenu
    return _der.suite(_der.suite(_der.entier(statut)), corps)


def nonce_de(requete: bytes) -> tuple[bytes, int]:
    """Empreinte et nonce d'une requête de l'outil."""
    _, imprint, nonce, _ = _der.lire(requete).enfants()
    return imprint.enfants()[1].contenu, _der.valeur_entiere(nonce)


# DER


def test_der_aller_retour() -> None:
    long = _der.encoder(_der.OCTETS, b"x" * 300)
    assert long[:4] == b"\x04\x82\x01\x2c"
    assert _der.lire(long).contenu == b"x" * 300
    for texte in ("2.16.840.1.101.3.4.2.1", "1.2.840.113549.1.9.16.1.4", "2.999.3"):
        assert _der.valeur_oid(_der.lire(_der.oid(texte))) == texte
    for valeur in (0, 127, 128, 255, 256, NONCE, 2**63 - 1):
        assert _der.valeur_entiere(_der.lire(_der.entier(valeur))) == valeur
    assert _der.lire(_der.booleen(True)).contenu == b"\xff"
    assert _der.lire(_der.booleen(False)).contenu == b"\x00"
    element = _der.lire(_der.encoder(_der.HEURE_GENERALISEE, b"20261125103000Z"))
    assert _der.heure(element) == datetime(2026, 11, 25, 10, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    "donnees",
    [
        b"\x30",
        b"\x1f\x01\x00",
        b"\x30\x80\x00\x00",
        b"\x04\x85\x00\x00\x00\x00\x01",
        b"\x04\x82\x01",
        b"\x04\x05abc",
        b"\x04\x01a\x00",
    ],
    ids=[
        "tronque",
        "etiquette-longue",
        "longueur-indefinie",
        "longueur-de-5-octets",
        "longueur-tronquee",
        "plus-long-que-les-donnees",
        "octets-en-trop",
    ],
)
def test_der_illisible(donnees: bytes) -> None:
    with pytest.raises(_der.DerInvalide):
        _der.lire(donnees)


def test_der_valeurs_illisibles() -> None:
    with pytest.raises(_der.DerInvalide, match="construit"):
        _der.lire(_der.encoder(_der.OCTETS, b"")).enfants()
    with pytest.raises(_der.DerInvalide, match="entier"):
        _der.valeur_entiere(_der.lire(_der.encoder(_der.OCTETS, b"\x01")))
    with pytest.raises(_der.DerInvalide, match="vide"):
        _der.valeur_entiere(_der.Element(_der.ENTIER, b""))
    for contenu in (b"", b"\x2a\x86"):
        with pytest.raises(_der.DerInvalide, match="tronqué"):
            _der.valeur_oid(_der.Element(_der.OID, contenu))
    for heure in (
        b"\xff",
        b"20261125103000",
        b"202611251030Z",
        b"20261325103000Z",
        b"20261125103000.Z",
        b"+0261125103000Z",
    ):
        with pytest.raises(_der.DerInvalide, match="heure"):
            _der.heure(_der.Element(_der.HEURE_GENERALISEE, heure))


# Réponse de l'autorité


def test_requete_rfc_3161() -> None:
    version, imprint, nonce, certificat = _der.lire(horodatage.requete(EMPREINTE, NONCE)).enfants()
    assert _der.valeur_entiere(version) == 1
    algorithme, condensat = imprint.enfants()
    assert _der.valeur_oid(algorithme.enfants()[0]) == SHA256
    assert algorithme.enfants()[1] == _der.Element(_der.NUL, b"")
    assert condensat.contenu == EMPREINTE
    assert _der.valeur_entiere(nonce) == NONCE
    assert certificat == _der.Element(_der.BOOLEEN, b"\xff")


def test_reponse_d_openssl() -> None:
    oracle = json.loads((DONNEES / "oracle.json").read_text(encoding="utf-8"))
    empreinte = bytes.fromhex(oracle["empreinte"])
    requete = horodatage.requete(empreinte, oracle["nonce"])
    assert requete == (DONNEES / "requete.tsq").read_bytes()
    obtenu = horodatage.lire_reponse(
        (DONNEES / "reponse.tsr").read_bytes(), empreinte, oracle["nonce"]
    )
    attendue = datetime.strptime(oracle["heure_openssl"], "%b %d %H:%M:%S %Y GMT")
    assert obtenu.heure == attendue.replace(tzinfo=UTC)
    assert obtenu.numero == oracle["numero"]
    assert obtenu.politique == oracle["politique"]
    with pytest.raises(horodatage.HorodatageImpossible, match="nonce"):
        horodatage.lire_reponse((DONNEES / "reponse.tsr").read_bytes(), empreinte, 1)


def test_reponse_construite_accordee() -> None:
    for statut in (0, 1):
        obtenu = horodatage.lire_reponse(reponse(statut=statut), EMPREINTE, NONCE)
        assert obtenu.heure == datetime(2026, 11, 25, 10, 30, tzinfo=UTC)
        assert (obtenu.numero, obtenu.politique) == (42, "1.2.3.4.1")


@pytest.mark.parametrize(
    ("contenu", "message"),
    [
        (reponse(statut=2), "demande rejetée"),
        (reponse(statut=9), "statut inconnu 9"),
        (_der.suite(_der.suite(_der.entier(0))), "sans jeton"),
        (reponse(contenu=jeton(tst_info(), type_jeton="1.2.840.113549.1.7.1")), "signées"),
        (reponse(contenu=jeton(tst_info(), type_contenu="1.2.840.113549.1.7.1")), "TSTInfo"),
        (
            reponse(contenu=_der.suite(_der.oid(SIGNED_DATA), _der.encoder(0xA0, _der.suite()))),
            "incomplètes",
        ),
        (reponse(tst_info(version=2)), "version 1"),
        (reponse(tst_info(algorithme="1.3.14.3.2.26")), "SHA-256"),
        (reponse(tst_info(b"\x00" * 32)), "autre empreinte"),
        (reponse(tst_info(nonce=None)), "nonce"),
        (reponse(tst_info(nonce=NONCE + 1)), "nonce"),
        (reponse(tst_info(heure=b"hier")), "illisible"),
        (reponse()[:-3], "illisible"),
        (b"", "illisible"),
    ],
    ids=[
        "rejetee",
        "statut-inconnu",
        "sans-jeton",
        "pas-signe",
        "pas-tstinfo",
        "signees-incompletes",
        "version",
        "sha1",
        "autre-empreinte",
        "sans-nonce",
        "autre-nonce",
        "heure",
        "tronquee",
        "vide",
    ],
)
def test_reponse_refusee(contenu: bytes, message: str) -> None:
    with pytest.raises(horodatage.HorodatageImpossible, match=message):
        horodatage.lire_reponse(contenu, EMPREINTE, NONCE)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://tsa.example/",
        "https:///chemin",
        "https://moi:secret@tsa.example/",
        "https://tsa.example:99999/",
        "https://tsa.example/é",
        "https://tsa.example/ a",
        "https://[::1/",
        "https://tsa.example/" + "a" * 2048,
    ],
    ids=["ftp", "sans-hote", "identifiants", "port", "non-ascii", "espace", "crochet", "longue"],
)
def test_url_refusee(url: str) -> None:
    with pytest.raises(ValueError, match="adresse"):
        horodatage.verifier_url(url)


def test_url_acceptee() -> None:
    for url in ("http://127.0.0.1:8318/", "https://tsa.example/tsr?x=1"):
        assert horodatage.verifier_url(url) == url


def _repondre(url: str, corps: bytes, delai: float) -> bytes:
    empreinte, nonce = nonce_de(corps)
    return reponse(tst_info(empreinte, nonce))


def test_horodater_par_un_envoi_remplace() -> None:
    obtenu = horodatage.horodater("http://tsa", EMPREINTE, envoyer=_repondre)
    assert obtenu.numero == 42


@pytest.mark.parametrize(
    ("erreur", "message"),
    [
        (urllib.error.HTTPError("http://tsa", 503, "", None, None), "répondu 503"),  # type: ignore[arg-type]
        (
            urllib.error.URLError(ConnectionRefusedError(111, "refusée")),
            "injoignable \\(refusée\\)",
        ),
        (urllib.error.URLError("nom inconnu"), "injoignable \\(nom inconnu\\)"),
        (urllib.error.URLError(TimeoutError()), "aucune réponse en 30 s"),
        (TimeoutError(), "aucune réponse en 30 s"),
        (ConnectionResetError(104, "coupée"), "interrompu \\(coupée\\)"),
        (OSError(), "interrompu"),
    ],
    ids=["http", "refusee", "nom", "delai-connexion", "delai-lecture", "coupure", "oserror"],
)
def test_horodater_echange_en_echec(erreur: Exception, message: str) -> None:
    def envoyer(url: str, corps: bytes, delai: float) -> bytes:
        raise erreur

    with pytest.raises(horodatage.HorodatageImpossible, match=message):
        horodatage.horodater("http://tsa", EMPREINTE, envoyer=envoyer)


def test_horodater_reponse_trop_longue() -> None:
    def envoyer(url: str, corps: bytes, delai: float) -> bytes:
        return b"\x00" * (horodatage.TAILLE_MAX_REPONSE + 1)

    with pytest.raises(horodatage.HorodatageImpossible, match="plus de 1 Mio"):
        horodatage.horodater("http://tsa", EMPREINTE, envoyer=envoyer)


# Autorité locale, sur 127.0.0.1 : la requête passe par urllib, sans redirection.


class _Autorite(http.server.BaseHTTPRequestHandler):
    recues: ClassVar[list[tuple[str, str | None, bytes]]] = []

    def do_POST(self) -> None:
        corps = self.rfile.read(int(self.headers["Content-Length"]))
        _Autorite.recues.append((self.path, self.headers["Content-Type"], corps))
        if self.path == "/redirige":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.2/")
            self.end_headers()
            return
        contenu = _repondre(self.path, corps, 0)
        self.send_response(200)
        self.send_header("Content-Type", "application/timestamp-reply")
        self.send_header("Content-Length", str(len(contenu)))
        self.end_headers()
        self.wfile.write(contenu)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def autorite(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    for variable in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy"):
        monkeypatch.delenv(variable, raising=False)
    serveur = http.server.HTTPServer(("127.0.0.1", 0), _Autorite)
    fil = threading.Thread(target=serveur.serve_forever, daemon=True)
    fil.start()
    _Autorite.recues = []
    try:
        yield f"http://127.0.0.1:{serveur.server_address[1]}"
    finally:
        serveur.shutdown()
        serveur.server_close()


@pytest.mark.exigence("NF-16")
def test_horodater_par_le_reseau_local(autorite: str) -> None:
    obtenu = horodatage.horodater(autorite + "/tsa", EMPREINTE)
    chemin, type_, corps = _Autorite.recues[-1]
    assert (chemin, type_) == ("/tsa", "application/timestamp-query")
    assert nonce_de(corps)[0] == EMPREINTE  # l'empreinte, et rien d'autre du rapport
    assert obtenu.numero == 42
    with pytest.raises(horodatage.HorodatageImpossible, match="répondu 302"):
        horodatage.horodater(autorite + "/redirige", EMPREINTE)


# Journal


def _horloge() -> datetime:
    return datetime(2026, 11, 25, 10, 0, tzinfo=UTC)


def _tenir(chemin: Path, qui: str | None = None) -> journal.Journal:
    return journal.Journal(chemin, qui, horloge=_horloge)


def test_journal_chaine(tmp_path: Path) -> None:
    chemin = tmp_path / "journal.jsonl"
    tenu = _tenir(chemin, "Ann Onyme")
    assert tenu.bilan == journal.Bilan(0, None, None, journal.ORIGINE)
    empreinte = "a" * 64
    assert tenu.soumission(saisie="fichier", empreinte=empreinte, format_reel="pdf", levees=[]) == 1
    assert tenu.export(soumission=1, rapport="json", empreinte="b" * 64) == 2
    horo = {"autorite": "http://tsa/", "heure": "2026-11-25T10:00:01Z", "jeton": "c" * 64}
    assert tenu.export(soumission=1, rapport="html", empreinte="d" * 64, horodatage=horo) == 3
    assert tenu.refus(saisie="texte_colle", motif="texte_vide") == 4
    assert tenu.consultation(empreinte="b" * 64) == 5
    lignes = chemin.read_bytes().split(b"\n")
    assert lignes[-1] == b""
    entrees = [json.loads(ligne) for ligne in lignes[:-1]]
    assert [e["evenement"] for e in entrees] == [
        "soumission",
        "export",
        "export",
        "refus",
        "consultation",
    ]
    assert entrees[0]["precedente"] == journal.ORIGINE
    for avant, entree in zip(lignes, entrees[1:], strict=False):
        assert entree["precedente"] == hashlib.sha256(avant).hexdigest()
    assert {e["qui"] for e in entrees} == {"Ann Onyme"}
    assert entrees[2]["horodatage"] == horo
    assert "nom" not in json.dumps(entrees)  # ni nom de fichier, ni chemin
    bilan = journal.lire(chemin)
    assert (bilan.entrees, bilan.premiere, bilan.derniere) == (5, _horloge(), _horloge())
    assert bilan.derniere_empreinte == hashlib.sha256(lignes[-2]).hexdigest()
    reouvert = _tenir(chemin)
    assert reouvert.bilan == bilan
    assert reouvert.consultation(empreinte="e" * 64) == 6
    assert "qui" not in json.loads(chemin.read_bytes().split(b"\n")[-2])
    if os.name == "posix":
        assert chemin.stat().st_mode & 0o777 == 0o600


def _journal_de(tmp_path: Path, nombre: int = 3) -> Path:
    chemin = tmp_path / "journal.jsonl"
    tenu = _tenir(chemin)
    numero = tenu.soumission(saisie="fichier", empreinte="a" * 64, format_reel="pdf", levees=[])
    for _ in range(nombre - 1):
        tenu.export(soumission=numero, rapport="json", empreinte="b" * 64)
    return chemin


def _remplacer(chemin: Path, rang: int, **champs: object) -> None:
    lignes = chemin.read_bytes().split(b"\n")
    entree = json.loads(lignes[rang - 1]) | champs
    lignes[rang - 1] = json.dumps(entree, separators=(",", ":")).encode()
    chemin.write_bytes(b"\n".join(lignes))


@pytest.mark.parametrize(
    ("alteration", "numero", "message"),
    [
        (lambda c: _remplacer(c, 1, empreinte="f" * 64), 2, "précédente"),
        (lambda c: _remplacer(c, 2, numero=7), 2, "numéro 7 à la place de 2"),
        (lambda c: _remplacer(c, 2, soumission=2), 2, "export sans soumission"),
        (lambda c: _remplacer(c, 3, evenement="autre"), 3, "schéma"),
        (lambda c: c.write_bytes(c.read_bytes()[:-1]), 3, "inachevée"),
        (lambda c: c.write_bytes(c.read_bytes() + b"{\n"), 4, "illisible"),
        (lambda c: c.write_bytes(b"\n".join(c.read_bytes().split(b"\n")[1:])), 1, "numéro 2"),
    ],
    ids=[
        "entree-modifiee",
        "renumerotee",
        "export-orphelin",
        "evenement-inconnu",
        "derniere-inachevee",
        "ligne-illisible",
        "premiere-supprimee",
    ],
)
def test_journal_rompu(tmp_path: Path, alteration: object, numero: int, message: str) -> None:
    chemin = _journal_de(tmp_path)
    alteration(chemin)  # type: ignore[operator]
    with pytest.raises(journal.JournalInvalide, match=message) as erreur:
        journal.lire(chemin)
    assert erreur.value.numero == numero
    with pytest.raises(journal.JournalInvalide):
        _tenir(chemin)  # un journal rompu n'est pas prolongé


def test_journal_inutilisable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(journal.JournalInvalide, match="illisible") as erreur:
        journal.lire(tmp_path / "absent")
    assert erreur.value.numero is None
    with pytest.raises(journal.JournalInvalide, match="inutilisable"):
        _tenir(tmp_path / "absent" / "journal")
    if os.name == "posix":
        with pytest.raises(journal.JournalInvalide, match="régulier"):
            journal.lire("/dev/null")
        with pytest.raises(journal.JournalInvalide, match="régulier"):
            _tenir(Path("/dev/null"))
    monkeypatch.setattr(journal, "TAILLE_MAX_JOURNAL", 10)
    gros = tmp_path / "gros"
    gros.write_bytes(b"x" * 11)
    with pytest.raises(journal.JournalInvalide, match="commencez-en un autre"):
        journal.lire(gros)


def test_journal_pres_de_sa_limite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chemin = _journal_de(tmp_path, 1)
    tenu = _tenir(chemin)
    monkeypatch.setattr(journal, "TAILLE_MAX_JOURNAL", chemin.stat().st_size + 10)
    with pytest.raises(journal.JournalInvalide, match="il atteindrait"):
        tenu.consultation(empreinte="e" * 64)
    # Grossi au-delà de la limite par une autre commande : la lecture s'arrête à la limite.
    monkeypatch.setattr(journal, "TAILLE_MAX_JOURNAL", 10)
    with pytest.raises(journal.JournalInvalide, match="plus de 0 Mio"):
        tenu.consultation(empreinte="e" * 64)
    monkeypatch.undo()
    assert journal.lire(chemin).entrees == 1


def test_journal_change_entre_deux_ajouts(tmp_path: Path) -> None:
    chemin = _journal_de(tmp_path, 2)
    tenu = _tenir(chemin)
    contenu = chemin.read_bytes()
    chemin.write_bytes(contenu[:-1])
    with pytest.raises(journal.JournalInvalide, match="inachevée"):
        tenu.consultation(empreinte="e" * 64)
    chemin.write_bytes(contenu + contenu.split(b"\n")[1] + b"\n")
    with pytest.raises(journal.JournalInvalide, match="numérotation") as erreur:
        tenu.consultation(empreinte="e" * 64)
    assert erreur.value.numero == 3


def test_journal_ecriture_en_echec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chemin = _journal_de(tmp_path, 1)
    tenu = _tenir(chemin)
    monkeypatch.setattr(os, "write", lambda _d, donnees: len(donnees) - 1)
    with pytest.raises(journal.JournalInvalide, match="incomplète"):
        tenu.consultation(empreinte="e" * 64)

    def plein(_descripteur: int, _donnees: bytes) -> int:
        raise OSError(28, "plus de place")

    monkeypatch.setattr(os, "write", plein)
    with pytest.raises(journal.JournalInvalide, match="non écrite \\(plus de place\\)"):
        tenu.consultation(empreinte="e" * 64)


def _ajouter(chemin: str, nombre: int) -> None:
    tenu = journal.Journal(chemin)
    for _ in range(nombre):
        tenu.consultation(empreinte="e" * 64)


def test_journal_tenu_par_deux_commandes(tmp_path: Path) -> None:
    chemin = str(tmp_path / "journal.jsonl")
    journal.Journal(chemin)
    contexte = multiprocessing.get_context("spawn")
    processus = [contexte.Process(target=_ajouter, args=(chemin, 25)) for _ in range(2)]
    for p in processus:
        p.start()
    for p in processus:
        p.join(120)
        assert p.exitcode == 0
    assert journal.lire(chemin).entrees == 50


@pytest.mark.parametrize(
    "qui", ["", " Ann", "Ann ", "a" * 129, "Ann\u200bOnyme", "Ann\nOnyme", "Ann\u2028"]
)
def test_qui_refuse(qui: str) -> None:
    with pytest.raises(ValueError, match="caractère"):
        journal.verifier_qui(qui)


def test_qui_accepte() -> None:
    for qui in ("Ann Onyme", "Rédaction « Société »", "a" * 128):
        assert journal.verifier_qui(qui) == qui


# Ligne de commande


@pytest.fixture
def document(tmp_path: Path) -> Path:
    chemin = tmp_path / "SOURCE.pdf"
    chemin.write_bytes(PDF)
    return chemin


def _entrees(chemin: Path) -> list[dict[str, object]]:
    return [json.loads(ligne) for ligne in chemin.read_text(encoding="utf-8").splitlines()]


@pytest.mark.exigence("NF-16", "NF-18")
def test_analyse_journalisee_et_horodatee(
    tmp_path: Path, document: Path, autorite: str, capsys: pytest.CaptureFixture[str]
) -> None:
    tenu = tmp_path / "journal.jsonl"
    sortie = tmp_path / "rapports"
    vide = tmp_path / "vide.pdf"
    vide.write_bytes(b"")
    arguments = ["--journal", str(tenu), "--qui", "Ann", "--rapport", str(sortie)]
    arguments += ["--horodater", autorite, "--reveler", "empreinte", str(document), str(vide)]
    assert main(arguments) == 1  # le second fichier est refusé
    sorties = capsys.readouterr()
    assert sorties.err.startswith("Journal de conservation activé : ")
    assert "Horodatage activé : " in sorties.err
    assert sorted(p.name for p in sortie.iterdir()) == [
        "1.html",
        "1.html.tsr",
        "1.json",
        "1.json.tsr",
    ]
    assert "  1.json horodaté : 2026-11-25 10:30:00 UTC selon l'autorité, jeton " in sorties.out
    assert "openssl ts -verify -data " in sorties.out
    soumission, html, json_, refus = _entrees(tenu)
    empreinte = hashlib.sha256(PDF).hexdigest()
    assert soumission | {"precedente": ""} == {
        "format": 1,
        "numero": 1,
        "date": soumission["date"],
        "evenement": "soumission",
        "precedente": "",
        "qui": "Ann",
        "saisie": "fichier",
        "empreinte": empreinte,
        "format_reel": "pdf",
        "levees": ["empreinte"],
    }
    for entree, nom in ((html, "1.html"), (json_, "1.json")):
        ecrit = (sortie / nom).read_bytes()
        assert entree["empreinte"] == hashlib.sha256(ecrit).hexdigest()
        assert entree["rapport"] == nom[2:]
        jeton_ = (sortie / f"{nom}.tsr").read_bytes()
        assert entree["horodatage"] == {
            "autorite": autorite,
            "heure": "2026-11-25T10:30:00Z",
            "jeton": hashlib.sha256(jeton_).hexdigest(),
        }
    for (_, _, requete), nom in zip(_Autorite.recues, ("1.html", "1.json"), strict=True):
        # Chaque jeton écrit est la réponse à la requête de son fichier.
        empreinte_, nonce = nonce_de(requete)
        assert empreinte_ == hashlib.sha256((sortie / nom).read_bytes()).digest()
        horodatage.lire_reponse((sortie / f"{nom}.tsr").read_bytes(), empreinte_, nonce)
    assert (refus["evenement"], refus["motif"]) == ("refus", "vide")
    assert "SOURCE" not in tenu.read_text(encoding="utf-8")
    assert main(["--verifier-journal", str(tenu)]) == 0
    assert capsys.readouterr().out.startswith("Journal cohérent : 4 entrées, du ")


def test_texte_et_comparaison_journalises(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    tenu = tmp_path / "journal.jsonl"
    sortie = tmp_path / "rapports"
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO("Un texte collé.".encode())))
    assert main(["--journal", str(tenu), "--rapport", str(sortie), "--texte"]) == 0
    rapport = str(sortie / "1.json")
    assert main(["--journal", str(tenu), "--comparer", rapport, rapport]) == 0
    capsys.readouterr()
    soumission, _, export_json, premiere, seconde = _entrees(tenu)
    assert soumission["saisie"] == "texte_colle"
    assert soumission["empreinte"] == hashlib.sha256("Un texte collé.".encode()).hexdigest()
    assert premiere["evenement"] == seconde["evenement"] == "consultation"
    assert premiere["empreinte"] == seconde["empreinte"] == export_json["empreinte"]


def test_horodatage_non_obtenu(
    tmp_path: Path,
    document: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuser(url: str, empreinte: bytes) -> horodatage.Jeton:
        raise horodatage.HorodatageImpossible("demande rejetée")

    monkeypatch.setattr(horodatage, "horodater", refuser)
    tenu = tmp_path / "journal.jsonl"
    sortie = tmp_path / "rapports"
    arguments = ["--journal", str(tenu), "--rapport", str(sortie), "--horodater", "http://tsa/"]
    assert main([*arguments, str(document)]) == 1
    sorties = capsys.readouterr()
    assert "[1/1] 1.html non horodaté : demande rejetée\n" in sorties.err
    assert "openssl" not in sorties.out
    assert sorted(p.name for p in sortie.iterdir()) == ["1.html", "1.json"]
    assert [("horodatage" in e) for e in _entrees(tenu)] == [False, False, False]


def test_jeton_non_ecrit(
    tmp_path: Path,
    document: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jeton_ = horodatage.Jeton(b"r", datetime(2026, 11, 25, tzinfo=UTC), 1, "1.2")
    monkeypatch.setattr(horodatage, "horodater", lambda url, empreinte: jeton_)
    ecrire = cli._ecrire

    def ecrire_sauf_jeton(chemin: Path, contenu: bytes) -> None:
        if chemin.suffix == ".tsr":
            raise OSError(28, "plus de place")
        ecrire(chemin, contenu)

    monkeypatch.setattr(cli, "_ecrire", ecrire_sauf_jeton)
    sortie = tmp_path / "rapports"
    assert main(["--rapport", str(sortie), "--horodater", "http://tsa/", str(document)]) == 1
    assert "[1/1] jeton de 1.json non écrit : plus de place\n" in capsys.readouterr().err


def test_journal_non_ecrit_arrete_la_commande(
    tmp_path: Path,
    document: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def plein(*_args: object, **_champs: object) -> int:
        raise journal.JournalInvalide("entrée non écrite (plus de place)")

    tenu = tmp_path / "journal.jsonl"
    for methode, attendu in (("soumission", "[1/2]"), ("refus", "[1/2]"), ("export", "[1/2]")):
        with monkeypatch.context() as m:
            m.setattr(journal.Journal, methode, plein)
            premier = tmp_path / "vide.pdf" if methode == "refus" else document
            premier.write_bytes(b"" if methode == "refus" else PDF)
            sortie = tmp_path / f"rapports-{methode}"
            arguments = ["--journal", str(tenu), "--rapport", str(sortie), str(premier)]
            assert main([*arguments, str(document)]) == 1
            sorties = capsys.readouterr()
            assert f"{attendu} journal non écrit : entrée non écrite (plus de place) ; arrêt" in (
                sorties.err
            )
            assert "[2/2]" not in sorties.out + sorties.err
    with monkeypatch.context() as m:
        m.setattr(journal.Journal, "consultation", plein)
        main(["--rapport", str(tmp_path / "r"), str(document)])
        rapport = str(tmp_path / "r" / "1.json")
        capsys.readouterr()
        assert main(["--journal", str(tenu), "--comparer", rapport, rapport]) == 2
        assert "Résultats" not in capsys.readouterr().out


def test_rapport_non_ecrit_n_est_pas_journalise(
    tmp_path: Path,
    document: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sortie = tmp_path / "rapports"
    sortie.mkdir()
    (sortie / "1.json").write_text("à garder")
    monkeypatch.setattr(cli, "_preparer", lambda dossier, _nombre, jetons: Path(dossier))
    tenu = tmp_path / "journal.jsonl"
    assert main(["--journal", str(tenu), "--rapport", str(sortie), str(document)]) == 1
    assert "[1/1] rapport non écrit : " in capsys.readouterr().err
    # Le HTML, écrit, est journalisé ; le JSON, non écrit, ne l'est pas.
    assert [e["evenement"] for e in _entrees(tenu)] == ["soumission", "export"]


def test_verifier_journal_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    vide = tmp_path / "vide.jsonl"
    vide.write_bytes(b"")
    assert main(["--verifier-journal", str(vide)]) == 0
    assert capsys.readouterr().out.startswith("Journal vide : aucune entrée.\nCohérent ne veut")
    un = _journal_de(tmp_path, 1)
    assert main(["--verifier-journal", str(un)]) == 0
    assert "Journal cohérent : 1 entrée, du 2026-11-25 10:00:00 au 2026-11-25 10:00:00 UTC." in (
        capsys.readouterr().out
    )
    _remplacer(un, 1, numero=2)
    assert main(["--verifier-journal", str(un)]) == 1
    assert capsys.readouterr().out == "Journal rompu à l'entrée 1 : numéro 2 à la place de 1.\n"
    assert main(["--verifier-journal", str(tmp_path / "absent")]) == 2
    assert capsys.readouterr().err.startswith("Journal illisible : fichier illisible (")
    with pytest.raises(SystemExit) as code:
        main(["--journal", str(un), str(tmp_path / "f.pdf")])
    assert code.value.code == 2
    assert "--journal : entrée 1 : numéro 2 à la place de 1 ; --verifier-journal le détaille" in (
        capsys.readouterr().err
    )
    with pytest.raises(SystemExit):
        main(["--journal", str(tmp_path / "absent" / "j"), str(tmp_path / "f.pdf")])
    assert "--journal : fichier inutilisable (" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["--verifier-journal", "j", "f.pdf"], "--verifier-journal s'emploie seule"),
        (["--qui", "Ann", "f.pdf"], "--qui s'emploie avec --journal"),
        (["--journal", "j", "--qui", " Ann", "f.pdf"], "--qui : de 1 à 128 caractères"),
        (["--horodater", "http://tsa/", "f.pdf"], "--horodater s'emploie avec --rapport"),
        (["--rapport", "r", "--horodater", "ftp://tsa/", "f.pdf"], "--horodater : adresse"),
        (
            ["--rapport", "r", "--horodater", "http://tsa/", "--comparer", "a", "b"],
            "--horodater s'emploie avec une analyse",
        ),
        (["--journal", "j", "--modules"], "--journal s'emploie avec une analyse"),
        (["--journal", "j"], "--journal s'emploie avec une analyse"),
    ],
    ids=[
        "verifier-avec-fichier",
        "qui-sans-journal",
        "qui-invalide",
        "horodater-sans-rapport",
        "horodater-ftp",
        "horodater-comparer",
        "journal-modules",
        "journal-seul",
    ],
)
def test_options_incompatibles(
    arguments: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as code:
        main(arguments)
    assert code.value.code == 2
    assert message in capsys.readouterr().err


def test_jeton_existant_jamais_ecrase(
    tmp_path: Path, document: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sortie = tmp_path / "rapports"
    sortie.mkdir()
    (sortie / "1.json.tsr").write_bytes(b"garder")
    with pytest.raises(SystemExit):
        main(["--rapport", str(sortie), "--horodater", "http://tsa/", str(document)])
    assert "--rapport : 1.json.tsr existe déjà" in capsys.readouterr().err
    # Sans horodatage, un jeton laissé là ne gêne pas.
    assert main(["--rapport", str(sortie), str(document)]) == 0


@pytest.mark.exigence("NF-18")
def test_date_du_rapport_non_certifiee(tmp_path: Path, document: Path) -> None:
    sortie = tmp_path / "rapports"
    assert main(["--rapport", str(sortie), str(document)]) == 0
    html = (sortie / "1.html").read_text(encoding="utf-8")
    assert " UTC, horloge du poste, non certifiée</p></header>" in html
    assert "Date de l&#x27;analyse (UTC, horloge du poste, non certifiée)" in html


def test_sans_option_ni_journal_ni_requete(
    tmp_path: Path, document: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def interdit(*_args: object, **_champs: object) -> object:
        raise AssertionError("aucune trace ni requête sans option")

    monkeypatch.setattr(journal.Journal, "__init__", interdit)
    monkeypatch.setattr(horodatage, "horodater", interdit)
    assert main(["--rapport", str(tmp_path / "rapports"), str(document)]) == 0


@pytest.mark.exigence("ES-04")
@settings(max_examples=500, deadline=None)
@given(st.binary(max_size=64), st.integers(0, 2297), st.integers(0, 255))
def test_reponse_hostile_jamais_d_autre_erreur(aleatoire: bytes, rang: int, octet: int) -> None:
    # Une réponse quelconque, ou celle d'OpenSSL altérée d'un octet, n'est jamais qu'illisible ou
    # refusée : aucune autre exception, aucune réponse retouchée acceptée pour une autre heure.
    oracle = json.loads((DONNEES / "oracle.json").read_text(encoding="utf-8"))
    empreinte = bytes.fromhex(oracle["empreinte"])
    vraie = (DONNEES / "reponse.tsr").read_bytes()
    alteree = vraie[:rang] + bytes([octet]) + vraie[rang + 1 :]
    for contenu in (aleatoire, alteree):
        with contextlib.suppress(horodatage.HorodatageImpossible):
            horodatage.lire_reponse(contenu, empreinte, oracle["nonce"])
