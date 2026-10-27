"""Tests des limites d'une analyse (ES-03, NF-02, NF-08, F-04, ADR-0076, ADR-0077).

Les limites comptées par le contexte d'un module sont testées dans le processus des tests ;
le refus « hors limites », l'arrêt par le temps processeur et la surveillance de la mémoire,
avec le processus principal.
"""

import contextlib
import gzip
import io
import json
import os
import signal
import sys
import zlib
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from voight_kampff import AnalyseRefusee, MotifRefus, _limites
from voight_kampff._orchestration import soumission, surveillance, travail
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff._travail import garde, principal
from voight_kampff._travail.contexte import Compression, Contexte, LimiteDepassee
from voight_kampff._travail.fichier import Fichier
from voight_kampff.rapport.modele import (
    RAISONS_D_INTERRUPTION,
    VERSION_SCHEMA,
    Direction,
    EtatIsolation,
    NiveauIsolation,
    NonMenee,
    Partie,
    Plage,
    RaisonNonMenee,
)

FACTICE = Path(__file__).with_name("travail_factice.py")
PARTIE = Partie(1, "jpeg", Plage(0, 10), fin_connue=True)
MODULE = Manifeste(
    "alpha", "1.0", ("jpeg",), ("F-10",), (), "test", (Direction.RIEN_DE_PARTICULIER,)
)


@pytest.fixture
def contexte() -> Contexte:
    garde.verrouiller()
    return Contexte("alpha", {Direction.RIEN_DE_PARTICULIER}, Fichier(-1), PARTIE, 1 << 20)


@pytest.fixture
def descripteur(tmp_path: Path) -> Iterator[int]:
    chemin = tmp_path / "analyse.bin"
    chemin.write_bytes(b"0123456789")
    ouvert = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    yield ouvert
    os.close(ouvert)


def factice(scenario: str) -> Callable[[int], list[str]]:
    def commande(descripteur: int) -> list[str]:
        script = [str(FACTICE), scenario, "--descripteur", str(descripteur)]
        return [sys.executable, "-I", "-B", *script]

    return commande


# Valeurs (ADR-0077)


def test_valeurs_fixees() -> None:
    assert _limites.TAILLE_MAX_FICHIER == 1 << 30
    assert _limites.MEMOIRE_MAX == 2 << 30
    assert _limites.DELAI == travail.DELAI == 120.0
    assert _limites.TEMPS_PROCESSEUR == 120
    # Un module ne décompresse pas plus que la mémoire ne le permet.
    assert _limites.TAILLE_MAX_DECOMPRESSEE < _limites.MEMOIRE_MAX // 2


def test_seule_la_limite_du_systeme_interrompt() -> None:
    # Limites comptées : déterministes, dans la garantie ; mémoire du système : hors garantie.
    assert RaisonNonMenee.LIMITE_DEPASSEE not in RAISONS_D_INTERRUPTION
    assert RaisonNonMenee.MEMOIRE_DEPASSEE in RAISONS_D_INTERRUPTION


# Budget compté d'un module (ADR-0078)


def test_objets_comptes(contexte: Contexte) -> None:
    contexte.compter_objets(_limites.OBJETS_MAX - 1)
    contexte.compter_objets()
    assert not contexte.depasse
    with pytest.raises(LimiteDepassee):
        contexte.compter_objets()
    assert contexte.depasse
    with pytest.raises(LimiteDepassee):  # plus aucun résultat n'est admis ensuite
        contexte.observer("apres", 1)


def test_dimensions_declarees(contexte: Contexte) -> None:
    contexte.verifier_dimensions(1 << 14, 1 << 13)
    with pytest.raises(LimiteDepassee):
        contexte.verifier_dimensions(1 << 14, (1 << 13) + 1)


def test_imbrication(contexte: Contexte) -> None:
    def descendre(niveau: int) -> int:
        with contexte.imbrication():
            return niveau if niveau == _limites.PROFONDEUR_MAX else descendre(niveau + 1)

    assert descendre(1) == _limites.PROFONDEUR_MAX
    with contexte.imbrication():  # le niveau redescend en sortant de chaque bloc
        pass
    with pytest.raises(LimiteDepassee):
        descendre(0)


@pytest.mark.parametrize(
    "appel",
    [
        lambda c: c.compter_objets(-1),
        lambda c: c.verifier_dimensions(-1, 1),
        lambda c: c.compter_decompression(-1, 0),
    ],
)
def test_valeurs_negatives_refusees(contexte: Contexte, appel: Callable[..., None]) -> None:
    with pytest.raises(ValueError, match="négati"):
        appel(contexte)
    assert not contexte.depasse


def test_decompression_cumulee(contexte: Contexte) -> None:
    contexte.compter_decompression(1 << 20, _limites.TAILLE_MAX_DECOMPRESSEE)
    with pytest.raises(LimiteDepassee):
        contexte.compter_decompression(1 << 20, 1)


def test_rapport_de_compression(contexte: Contexte) -> None:
    seuil = _limites.SEUIL_RAPPORT_COMPRESSION
    contexte.compter_decompression(0, seuil)  # sous le seuil, le rapport n'est pas contrôlé
    contexte.compter_decompression(seuil // 1000 + 1000, 1)
    with pytest.raises(LimiteDepassee):
        contexte.compter_decompression(0, 1 << 20)


@pytest.mark.parametrize(
    ("methode", "compresser"),
    [
        ("zlib", zlib.compress),
        ("gzip", gzip.compress),
        ("deflate", lambda donnees: zlib.compress(donnees, wbits=-15)),
    ],
)
def test_decompresser(
    contexte: Contexte, methode: Compression, compresser: Callable[[bytes], bytes]
) -> None:
    donnees = bytes(range(256)) * 9000  # plus de deux blocs décompressés
    assert contexte.decompresser(compresser(donnees) + b"suite", methode) == donnees


def test_bombe_de_decompression(contexte: Contexte) -> None:
    # 64 Mio de zéros tiennent en 64 Kio : arrêtée au premier bloc après le seuil de 16 Mio.
    bombe = zlib.compress(bytes(64 << 20), 9)
    with pytest.raises(LimiteDepassee):
        contexte.decompresser(bombe, "zlib")
    assert contexte.depasse


@pytest.mark.parametrize("flux", [b"pas du zlib", zlib.compress(b"abc" * 1000)[:-8]])
def test_flux_invalide_ou_incomplet(contexte: Contexte, flux: bytes) -> None:
    with pytest.raises(zlib.error):
        contexte.decompresser(flux, "zlib")


def deroule(descripteur: int, analyseur: Callable[[Contexte], None]) -> list[str]:
    configuration = {
        "version_schema": VERSION_SCHEMA,
        "modules": [
            {
                "identifiant": "alpha",
                "formats": ["jpeg"],
                "directions": [Direction.RIEN_DE_PARTICULIER],
            }
        ],
    }
    sortie = io.BytesIO()
    principal.principal(
        ["--descripteur", str(descripteur)],
        io.BytesIO(json.dumps(configuration).encode() + b"\n"),
        sortie,
        analyseurs={"alpha": analyseur},
        identifier=lambda _fichier, _taille: (PARTIE,),
        restreindre=lambda: EtatIsolation(NiveauIsolation.COMPLETE),
    )
    messages = [json.loads(ligne) for ligne in sortie.getvalue().splitlines()]
    return [m["non_menee"]["raison"] for m in messages if m["type"] == "non_menee"]


@pytest.mark.skipif(sys.platform == "win32", reason="descripteur transmis comme sous POSIX")
def test_limite_interceptee_par_le_module(descripteur: int) -> None:
    def obstine(contexte: Contexte) -> None:
        contexte.observer("avant", 1)
        # Le module continue : le moteur a noté le dépassement, ses résultats sont écartés.
        with contextlib.suppress(LimiteDepassee):
            contexte.compter_objets(_limites.OBJETS_MAX + 1)

    assert deroule(descripteur, obstine) == ["limite_depassee"]


@pytest.mark.skipif(sys.platform == "win32", reason="descripteur transmis comme sous POSIX")
def test_memoire_epuisee(descripteur: int) -> None:
    def gourmand(_contexte: Contexte) -> None:
        raise MemoryError

    assert deroule(descripteur, gourmand) == ["memoire_depassee"]


# Refus « hors limites » (F-04)


def test_fichier_trop_grand_refuse_sans_etre_lu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chemin = tmp_path / "enorme.pdf"
    with chemin.open("wb") as fichier:
        fichier.truncate(_limites.TAILLE_MAX_FICHIER + 1)  # fichier creux : rien n'est écrit

    def interdit(*_arguments: object) -> tuple[str, int]:
        raise AssertionError("le fichier ne doit pas être lu")

    monkeypatch.setattr(soumission, "empreinte", interdit)
    with pytest.raises(AnalyseRefusee, match="trop volumineux : l'outil analyse au plus 1 Gio"):
        soumission.soumettre(chemin, manifestes=())


def test_fichier_qui_grandit_pendant_le_hachage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chemin = tmp_path / "grandit.pdf"
    chemin.write_bytes(b"%PDF-1.7\n")
    monkeypatch.setattr(soumission, "empreinte", lambda _d, _m: ("0" * 64, (1 << 30) + 1))
    with pytest.raises(AnalyseRefusee) as refus:
        soumission.soumettre(chemin, manifestes=())
    assert refus.value.motif is MotifRefus.HORS_LIMITES


def test_empreinte_bornee(tmp_path: Path) -> None:
    chemin = tmp_path / "trois-mio"
    chemin.write_bytes(bytes(3 << 20))
    descripteur = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    try:
        assert soumission.empreinte(descripteur, 1 << 20)[1] == 2 << 20  # arrêt au bloc suivant
        assert soumission.empreinte(descripteur)[1] == 3 << 20
    finally:
        os.close(descripteur)


# Temps processeur et mémoire, côté processus principal


@pytest.mark.skipif(sys.platform == "win32", reason="signaux POSIX")
def test_arret_par_le_temps_processeur() -> None:
    assert travail._arret_par_le_temps(-signal.SIGXCPU)
    assert not travail._arret_par_le_temps(-signal.SIGKILL)
    assert not travail._arret_par_le_temps(1)


@pytest.mark.skipif(sys.platform == "win32", reason="signaux POSIX")
def test_temps_processeur_epuise(descripteur: int) -> None:
    resultat = travail.executer(descripteur, (MODULE,), commande=factice("temps_processeur"))
    assert NonMenee(RaisonNonMenee.DELAI_DEPASSE) in resultat.non_menees
    assert resultat.interrompue


def test_aucune_surveillance_hors_macos() -> None:
    if sys.platform != "darwin":
        assert surveillance.memoire_depassee(os.getpid()) is None


@pytest.mark.parametrize(("depassee", "raison"), [(True, "memoire"), (False, "delai")])
def test_surveillance_pendant_l_attente(
    descripteur: int, monkeypatch: pytest.MonkeyPatch, depassee: bool, raison: str
) -> None:
    mesures: list[int] = []

    def mesure(_pid: int) -> Callable[[], bool]:
        def depasse() -> bool:
            mesures.append(1)
            return depassee

        return depasse

    monkeypatch.setattr(surveillance, "memoire_depassee", mesure)
    resultat = travail.executer(descripteur, (MODULE,), delai=1.0, commande=factice("silence"))
    attendue = {
        "memoire": RaisonNonMenee.MEMOIRE_DEPASSEE,
        "delai": RaisonNonMenee.DELAI_DEPASSE,
    }[raison]
    assert {n.raison for n in resultat.non_menees} == {attendue}
    assert mesures  # mesurée pendant l'attente, à chaque période
