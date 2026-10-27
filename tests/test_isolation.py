"""Tests des restrictions du processus de travail (ES-02, ES-03, ES-11, ADR-0079 à ADR-0083).

Deux familles :

- l'effet réel, vérifié depuis un module du factice (``sonde``, ``memoire``) exécuté dans un
  vrai processus de travail restreint, sur chacun des trois systèmes de la CI ;
- les fonctions pures qui construisent les restrictions (attributs de Landlock, programme
  seccomp, profil Seatbelt, limites du Job Object), testées partout dans le processus des tests.

Le code qui appelle le système ne s'exécute que dans un processus restreint, qui ne peut plus
écrire ses mesures de couverture : il est exclu de la mesure, et vérifié par la première
famille (ADR-0083).
"""

import ctypes
import os
import platform
import struct
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from systeme import MANQUES_ATTENDUS

from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff._orchestration.travail import ResultatTravail, executer
from voight_kampff._travail import restrictions
from voight_kampff._travail.restrictions import linux, macos, windows
from voight_kampff.rapport.modele import (
    Direction,
    EtatIsolation,
    ManqueIsolation,
    NiveauIsolation,
    RaisonNonMenee,
)

FACTICE = Path(__file__).with_name("travail_factice.py")
ECRITURE = FACTICE.with_name("ecriture-interdite.tmp")


def manifeste(identifiant: str) -> Manifeste:
    return Manifeste(
        identifiant=identifiant,
        version="1.0",
        formats=("jpeg",),
        exigences=("NF-01",),
        regles=(),
        fiche="test",
        directions=(Direction.RIEN_DE_PARTICULIER,),
    )


def factice(descripteur: int) -> list[str]:
    return [sys.executable, "-I", "-B", str(FACTICE), "modules", "--descripteur", str(descripteur)]


@pytest.fixture
def descripteur(tmp_path: Path) -> Iterator[int]:
    chemin = tmp_path / "analyse.bin"
    chemin.write_bytes(b"VKFT" + bytes(256))
    ouvert = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    yield ouvert
    os.close(ouvert)


def analyser_avec(descripteur: int, module: str) -> ResultatTravail:
    return executer(descripteur, (manifeste(module),), commande=factice)


# Effet réel, depuis un module


def test_isolation_annoncee(descripteur: int) -> None:
    resultat = analyser_avec(descripteur, "alpha")
    assert set(resultat.isolation.manques) == MANQUES_ATTENDUS
    assert (resultat.isolation.niveau is NiveauIsolation.COMPLETE) == (not MANQUES_ATTENDUS)


def test_ce_que_les_restrictions_refusent(descripteur: int) -> None:
    try:
        resultat = analyser_avec(descripteur, "sonde")
    finally:
        ECRITURE.unlink(missing_ok=True)
    essais = {o.nom.removeprefix("sonde."): o.valeur for o in resultat.observations}
    assert set(essais) == {"lecture", "ecriture", "socket", "connexion", "programme"}
    # Partout : ni écriture hors du processus, ni nouveau programme (ADR-0035).
    assert essais["ecriture"] != "permise"
    assert essais["programme"] != "permise"
    if sys.platform == "win32":
        # Windows ne bloque ni la lecture ni le réseau : le rapport le dit (ADR-0081).
        assert essais["lecture"] == "permise"
        assert essais["socket"] == "permise"
        assert essais["connexion"] != "PermissionError"
    else:
        # Seatbelt laisse créer une socket mais refuse toute connexion (ADR-0080).
        socket = "permise" if sys.platform == "darwin" else "PermissionError"
        assert essais == {
            "lecture": "PermissionError",
            "ecriture": "PermissionError",
            "socket": socket,
            "connexion": "PermissionError",
            "programme": "PermissionError",
        }


def test_memoire_limitee(descripteur: int) -> None:
    # 3 Gio remplis, pour une limite de 2 Gio : sous Linux et Windows le système refuse
    # l'allocation ; sous macOS le processus principal arrête le travail (ADR-0080).
    resultat = analyser_avec(descripteur, "memoire")
    raisons = {(non_menee.raison, non_menee.module) for non_menee in resultat.non_menees}
    assert (RaisonNonMenee.MEMOIRE_DEPASSEE, "memoire") in raisons
    assert resultat.interrompue  # limite du système : hors garantie (ADR-0078)


@pytest.mark.skipif(sys.platform != "win32", reason="lanceur de l'environnement virtuel")
def test_arret_du_lanceur_arrete_le_travail() -> None:  # pragma: no cover - CI Windows
    # Dans un environnement virtuel, sys.executable est un lanceur qui démarre le véritable
    # interpréteur ; arrêter le premier, comme le fait le principal, doit arrêter le second.
    code = "import os, time; print(os.getpid(), flush=True); time.sleep(60)"
    with subprocess.Popen([sys.executable, "-I", "-c", code], stdout=subprocess.PIPE) as processus:
        assert processus.stdout is not None
        pid = int(processus.stdout.readline())
        processus.kill()
        processus.wait(5)
    noyau = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined,unused-ignore]
    noyau.OpenProcess.restype = ctypes.c_void_p
    handle = noyau.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if handle:  # processus encore connu : il doit se terminer
        try:
            assert noyau.WaitForSingleObject(ctypes.c_void_p(handle), 5000) == 0
        finally:
            noyau.CloseHandle(ctypes.c_void_p(handle))


# État de l'isolation


def test_etat_complet_ou_reduit() -> None:
    assert restrictions.etat(()) == EtatIsolation(NiveauIsolation.COMPLETE)
    assert restrictions.etat({ManqueIsolation.TEMPS, ManqueIsolation.RESEAU}) == EtatIsolation(
        NiveauIsolation.REDUITE, (ManqueIsolation.RESEAU, ManqueIsolation.TEMPS)
    )


@pytest.mark.skipif(sys.platform != "linux", reason="aiguillage vers le module de Linux")
def test_appliquer_aiguille_vers_le_systeme(monkeypatch: pytest.MonkeyPatch) -> None:
    # Les vraies restrictions verrouilleraient le processus des tests.
    monkeypatch.setattr(linux, "appliquer", lambda: {ManqueIsolation.MEMOIRE})
    assert restrictions.appliquer() == EtatIsolation(
        NiveauIsolation.REDUITE, (ManqueIsolation.MEMOIRE,)
    )


# Linux : Landlock


@pytest.mark.parametrize(
    ("abi", "attendu"),
    [
        (0, (0, 0, 0)),
        (1, (0x1FFF, 0, 0)),
        (2, (0x3FFF, 0, 0)),
        (3, (0x7FFF, 0, 0)),
        (4, (0x7FFF, 0b11, 0)),
        (5, (0xFFFF, 0b11, 0)),
        (6, (0xFFFF, 0b11, 0b11)),
        (7, (0xFFFF, 0b11, 0b11)),
    ],
)
def test_droits_landlock(abi: int, attendu: tuple[int, int, int]) -> None:
    assert linux.droits_landlock(abi) == attendu


@pytest.mark.parametrize(("abi", "taille"), [(1, 8), (3, 8), (4, 16), (5, 16), (6, 24), (7, 24)])
def test_attributs_landlock_a_la_taille_du_noyau(abi: int, taille: int) -> None:
    attributs = linux.attributs_landlock(abi)
    assert len(attributs) == taille
    assert struct.unpack_from("=Q", attributs)[0] == linux.droits_landlock(abi)[0]


def test_manques_landlock() -> None:
    assert linux.manques_landlock(0) == {ManqueIsolation.LECTURE, ManqueIsolation.ECRITURE}
    assert linux.manques_landlock(2) == {ManqueIsolation.ECRITURE}  # troncature permise
    assert linux.manques_landlock(3) == frozenset()


# Linux : seccomp


def executer_bpf(programme: list[linux.Instruction], numero: int, architecture: int) -> int:
    """Interprète le filtre comme le noyau, pour ``struct seccomp_data`` réduite à deux champs."""
    donnees = struct.pack("=iI", numero, architecture)
    accumulateur, rang = 0, 0
    while True:
        code, vrai, faux, constante = programme[rang]
        if code == 0x20:  # BPF_LD | BPF_W | BPF_ABS
            accumulateur = struct.unpack_from("=I", donnees, constante)[0]
            rang += 1
        elif code in (0x15, 0x35):  # BPF_JEQ, BPF_JGE
            condition = accumulateur == constante if code == 0x15 else accumulateur >= constante
            rang += 1 + (vrai if condition else faux)
        else:
            assert code == 0x06  # BPF_RET
            return constante


TUER, PERMETTRE, EPERM = 0x80000000, 0x7FFF0000, 0x00050001


@pytest.mark.parametrize("nom", ["x86_64", "aarch64"])
def test_programme_seccomp(nom: str) -> None:
    architecture = linux.ARCHITECTURES[nom]
    programme = linux.programme_seccomp(architecture)
    for appel, numero in architecture.appels.items():
        assert executer_bpf(programme, numero, architecture.audit) == EPERM, appel
    for permis in (0, 1, 3, 60, 63, 231, 262, 435):  # lecture, écriture, fermeture, sortie…
        assert executer_bpf(programme, permis, architecture.audit) == PERMETTRE
    autre = linux.ARCHITECTURES["aarch64" if nom == "x86_64" else "x86_64"].audit
    assert executer_bpf(programme, 0, autre) == TUER
    assert executer_bpf(programme, 0, 0x40000003) == TUER  # i386


def test_appels_x32_tues() -> None:
    architecture = linux.ARCHITECTURES["x86_64"]
    programme = linux.programme_seccomp(architecture)
    assert executer_bpf(programme, 0x40000000 | 41, architecture.audit) == TUER
    assert executer_bpf(programme, 0x40000000, architecture.audit) == TUER


def test_programme_encode() -> None:
    programme = linux.programme_seccomp(linux.ARCHITECTURES["aarch64"])
    octets = linux.encoder_programme(programme)
    assert len(octets) == 8 * len(programme)
    assert struct.unpack_from("=HBBI", octets, 8 * (len(programme) - 1)) == (0x06, 0, 0, TUER)


def test_architecture_courante(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "machine", lambda: "aarch64")
    assert linux.architecture_courante() is linux.ARCHITECTURES["aarch64"]
    monkeypatch.setattr(platform, "machine", lambda: "riscv64")
    assert linux.architecture_courante() is None
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(sys, "maxsize", (1 << 31) - 1)  # Python 32 bits
    assert linux.architecture_courante() is None


# macOS : Seatbelt


def test_profil_seatbelt() -> None:
    texte = macos.profil(("/opt/python", '/chemin "cité"\\'))
    lignes = texte.splitlines()
    assert lignes[:2] == ["(version 1)", "(deny default)"]
    assert '(allow file-read* (subpath "/opt/python") (subpath "/chemin \\"cité\\"\\\\"))' in lignes
    assert '(allow file-write-data (literal "/dev/null"))' in lignes
    assert not any("network" in ligne or "process-exec" in ligne for ligne in lignes)


def test_dossiers_lisibles() -> None:
    import voight_kampff

    dossiers = macos.dossiers_lisibles()
    assert os.path.realpath(sys.base_prefix) in dossiers
    assert os.path.realpath(Path(voight_kampff.__file__).parent) in dossiers
    assert len(dossiers) == len(set(dossiers))


# Windows : Job Object


def test_limites_du_job() -> None:
    limites = windows.limites_du_job()
    base = limites.BasicLimitInformation
    assert base.LimitFlags == 0x2 | 0x8 | 0x100 | 0x400 | 0x2000
    assert base.ActiveProcessLimit == 1
    assert base.PerProcessUserTimeLimit == 120 * 10_000_000
    assert limites.ProcessMemoryLimit == 2 << 30


def test_manques_permanents_de_windows() -> None:
    assert {
        ManqueIsolation.RESEAU,
        ManqueIsolation.LECTURE,
        ManqueIsolation.VIDAGE_MEMOIRE,
    } == windows.MANQUES_PERMANENTS


def test_rien_n_est_restreint_dans_le_processus_des_tests() -> None:
    # Garde-fou : si un test avait appliqué les restrictions ici, ceci échouerait.
    verifier: Callable[[], bytes] = Path(__file__).read_bytes
    assert verifier()
