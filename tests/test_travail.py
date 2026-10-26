"""Tests du processus de travail exécuté dans le processus des tests (T12).

Le déroulé est appelé avec des flux en mémoire : on lit ce qu'il enverrait au processus
principal. La garde (ES-17) est remise à zéro avant chaque test.
"""

import contextlib
import hashlib
import importlib
import io
import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from voight_kampff import modules, schemas
from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail import garde, principal
from voight_kampff._travail.contexte import Contexte, LimiteDepassee
from voight_kampff._travail.fichier import Fichier
from voight_kampff._travail.principal import Analyseur, lire_configuration
from voight_kampff.rapport.modele import (
    VERSION_SCHEMA,
    Categorie,
    Direction,
    Fondement,
    Phrase,
    RaisonNonMenee,
    ReferenceRegle,
)

CONTENU = b"0123456789"


@pytest.fixture(autouse=True)
def hors_travail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", False)


@pytest.fixture
def descripteur(tmp_path: Path) -> Iterator[int]:
    chemin = tmp_path / "f.bin"
    chemin.write_bytes(CONTENU)
    ouvert = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    yield ouvert
    os.close(ouvert)


def configuration(*identifiants: str, formats: tuple[str, ...] = ("test",)) -> io.BytesIO:
    modules_actifs = [
        {"identifiant": i, "formats": list(formats), "directions": ["rien_de_particulier"]}
        for i in identifiants
    ]
    texte = json.dumps({"version_schema": VERSION_SCHEMA, "modules": modules_actifs})
    return io.BytesIO(texte.encode() + b"\n")


def derouler(
    descripteur: int,
    *identifiants: str,
    analyseurs: Mapping[str, Analyseur] | None = None,
    format_reel: str | None = "test",
) -> list[dict[str, Any]]:
    sortie = io.BytesIO()
    code = principal.principal(
        ["--descripteur", str(descripteur)],
        configuration(*identifiants),
        sortie,
        analyseurs=analyseurs,
        identifier=lambda _fichier: format_reel,
    )
    assert code == 0
    messages = [json.loads(ligne) for ligne in sortie.getvalue().splitlines()]
    for message in messages:
        schemas.valider("messages", message)
    return messages


def types(messages: list[dict[str, Any]]) -> list[str]:
    return [message["type"] for message in messages]


def contexte(budget: int = 1 << 20) -> Contexte:
    garde.verrouiller()
    return Contexte(
        "alpha", {Direction.RIEN_DE_PARTICULIER}, Fichier(-1), "test", len(CONTENU), budget
    )


# Déroulé


def test_deroule_sans_module(descripteur: int) -> None:
    messages = derouler(descripteur)
    assert types(messages) == ["isolation", "versions", "fin"]
    assert messages[-1]["empreinte"] == hashlib.sha256(CONTENU).hexdigest()


def test_garde_posee_avant_l_isolation(descripteur: int) -> None:
    derouler(descripteur)
    garde.exiger()  # ne lève plus : le déroulé a verrouillé le processus


def test_identification_par_defaut_aucun_format(descripteur: int) -> None:
    sortie = io.BytesIO()
    principal.principal(["--descripteur", str(descripteur)], configuration("alpha"), sortie)
    module = json.loads(sortie.getvalue().splitlines()[1])
    assert module == {"type": "module", "module": "alpha", "applicable": False}


def test_modules_dans_l_ordre_de_la_configuration(descripteur: int) -> None:
    vus: list[str] = []

    def temoin(nom: str) -> Analyseur:
        return lambda _contexte: vus.append(nom)

    analyseurs = {nom: temoin(nom) for nom in ("b", "a")}
    messages = derouler(descripteur, "b", "a", analyseurs=analyseurs)
    assert vus == ["b", "a"]
    assert [m["module"] for m in messages if m["type"] == "module"] == ["b", "a"]


def test_module_non_applicable_jamais_appele(descripteur: int) -> None:
    def interdit(_contexte: Contexte) -> None:
        raise AssertionError

    messages = derouler(descripteur, "alpha", analyseurs={"alpha": interdit}, format_reel="autre")
    assert messages[1] == {"type": "module", "module": "alpha", "applicable": False}


def test_exception_ecarte_les_resultats(descripteur: int) -> None:
    def fautif(contexte: Contexte) -> None:
        contexte.observer("avant", 1)
        raise ValueError

    messages = derouler(descripteur, "alpha", analyseurs={"alpha": fautif})
    assert types(messages) == ["isolation", "non_menee", "module", "versions", "fin"]
    assert messages[1]["non_menee"] == {"raison": "erreur_module", "module": "alpha"}


def test_module_absent_ou_non_importe(descripteur: int, monkeypatch: pytest.MonkeyPatch) -> None:
    messages = derouler(descripteur, "alpha", analyseurs={})
    assert messages[1]["non_menee"]["raison"] == "erreur_module"

    monkeypatch.setattr(principal, "importer", lambda: ({"alpha": lambda c: None}, {"alpha"}))
    messages = derouler(descripteur, "alpha")
    assert messages[1]["non_menee"]["raison"] == "erreur_module"


def test_resultats_dans_l_ordre(descripteur: int) -> None:
    def module(contexte: Contexte) -> None:
        premiere = contexte.observer("premiere", "a")
        contexte.constater(
            Phrase("g"),
            [premiere],
            ReferenceRegle("R-1", "1"),
            fondement=Fondement.MESURE,
            categorie=Categorie.INFORMATION_NEUTRE,
            direction=Direction.RIEN_DE_PARTICULIER,
        )
        contexte.non_mener(RaisonNonMenee.FICHIER_TRONQUE)

    messages = derouler(descripteur, "alpha", analyseurs={"alpha": module})
    assert types(messages)[1:5] == ["observation", "constat", "non_menee", "module"]


def test_limite_de_la_sortie(descripteur: int, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(principal, "TAILLE_MAX_SORTIE", principal._RESERVE + 1000)

    def bavard(contexte: Contexte) -> None:
        for numero in range(100):
            contexte.observer("n", numero)

    def obstine(contexte: Contexte) -> None:
        with contextlib.suppress(LimiteDepassee):
            bavard(contexte)
        contexte.observer("encore", 1)  # le dépassement reste acquis : lève de nouveau

    for analyseur in (bavard, obstine):
        messages = derouler(descripteur, "alpha", analyseurs={"alpha": analyseur})
        assert messages[1]["non_menee"] == {"raison": "limite_depassee", "module": "alpha"}


def test_message_trop_long() -> None:
    with pytest.raises(LimiteDepassee):
        contexte().observer("n", ["x" * 4096] * 4096)


# Contexte


def test_garde_hors_processus_de_travail() -> None:
    with pytest.raises(garde.HorsProcessusDeTravail):
        Contexte("alpha", (), Fichier(-1), "test", 0, 0)


def test_observations_numerotees() -> None:
    c = contexte()
    assert c.observer("a", [1, 2]) == "alpha/1"
    assert c.observer("b", "texte") == "alpha/2"
    assert json.loads(c.lignes[0])["observation"]["valeur"] == [1, 2]


def test_observation_invalide_non_comptee() -> None:
    c = contexte()
    with pytest.raises(ValueError, match="identifiant"):
        c.observer("nom invalide", 1)
    assert c.observer("a", 1) == "alpha/1"


@pytest.mark.parametrize(
    ("direction", "donnee", "attendu"),
    [
        (Direction.ORIGINE_IA, "alpha/1", "direction"),
        (Direction.RIEN_DE_PARTICULIER, "beta/1", "donnees"),
    ],
)
def test_constat_refuse(direction: Direction, donnee: str, attendu: str) -> None:
    c = contexte()
    c.observer("a", 1)
    with pytest.raises(ValueError, match=attendu):
        c.constater(
            Phrase("g"),
            [donnee],
            ReferenceRegle("R-1", "1"),
            fondement=Fondement.MESURE,
            categorie=Categorie.INFORMATION_NEUTRE,
            direction=direction,
        )


@pytest.mark.parametrize(
    "raison",
    [RaisonNonMenee.ERREUR_MODULE, RaisonNonMenee.MODULE_DESACTIVE, RaisonNonMenee.DELAI_DEPASSE],
)
def test_raison_reservee_au_moteur(raison: RaisonNonMenee) -> None:
    with pytest.raises(ValueError, match="moteur"):
        contexte().non_mener(raison)


def test_contexte_lit_le_fichier(descripteur: int) -> None:
    garde.verrouiller()
    c = Contexte("alpha", (), Fichier(descripteur), "test", len(CONTENU), 1 << 20)
    assert c.lire(3, 2) == b"34"


# Fichier


def test_lectures_a_position(descripteur: int) -> None:
    fichier = Fichier(descripteur)
    assert fichier.lire(2, 3) == b"234"
    assert fichier.lire(8, 100) == b"89"
    assert fichier.lire(100, 1) == b""
    assert fichier.lire(0, 0) == b""
    # Aucune position partagée : relire le début donne le début.
    assert fichier.lire(0, 2) == b"01"


@pytest.mark.parametrize(("position", "taille"), [(-1, 1), (0, -1), (0, TAILLE_MAX_LECTURE + 1)])
def test_lecture_hors_bornes(descripteur: int, position: int, taille: int) -> None:
    with pytest.raises(ValueError, match="lecture"):
        Fichier(descripteur).lire(position, taille)


def test_empreinte(descripteur: int) -> None:
    assert Fichier(descripteur).empreinte() == (hashlib.sha256(CONTENU).hexdigest(), 10)


# Configuration et import


@pytest.mark.parametrize(
    "ligne",
    [
        pytest.param(b"", id="absente"),
        pytest.param(b'{"version_schema":"0.1.0","modules":[]}', id="sans-fin-de-ligne"),
        pytest.param(b'{"version_schema":"9.9.9","modules":[]}\n', id="autre-version"),
    ],
)
def test_configuration_refusee(ligne: bytes) -> None:
    with pytest.raises(ValueError, match="configuration"):
        lire_configuration(io.BytesIO(ligne))


def test_configuration_trop_longue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(principal, "TAILLE_MAX_CONFIGURATION", 8)
    with pytest.raises(ValueError, match="configuration"):
        lire_configuration(configuration())


def test_import_des_modules_livres() -> None:
    # Aucun module n'est livré en T12.
    assert principal.importer() == ({}, frozenset())


def test_import_en_echec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for nom in ("bon", "casse", "sansfonction"):
        (tmp_path / nom).mkdir()
        (tmp_path / nom / modules.MANIFESTE).write_text("")
    dossiers = modules.dossiers
    monkeypatch.setattr(modules, "dossiers", lambda: dossiers(tmp_path))

    class Bon:
        @staticmethod
        def analyser(_contexte: Contexte) -> None:
            pass

    class SansFonction:
        analyser = "pas une fonction"

    def importer(nom: str) -> object:
        match nom.rsplit(".", 1)[1]:
            case "bon":
                return Bon
            case "sansfonction":
                return SansFonction
            case _:
                raise ImportError

    monkeypatch.setattr(importlib, "import_module", importer)
    analyseurs, echecs = principal.importer()
    assert set(analyseurs) == {"bon"}
    assert echecs == {"casse", "sansfonction"}
