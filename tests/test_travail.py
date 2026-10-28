"""Tests du processus de travail exécuté dans le processus des tests (T12, T13).

Le déroulé est appelé avec des flux en mémoire : on lit ce qu'il enverrait au processus
principal. La garde (ES-17) est remise à zéro avant chaque test. Les restrictions ne sont pas
appliquées : elles verrouilleraient le processus des tests ; ``test_isolation.py`` les vérifie
dans un processus de travail.
"""

import contextlib
import hashlib
import importlib
import io
import json
import os
import sys
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from catalogues import moteur, regle, regle_dict

from voight_kampff import modules, schemas
from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._regles import Regle
from voight_kampff._travail import garde, principal
from voight_kampff._travail.contexte import Contexte, LimiteDepassee
from voight_kampff._travail.fichier import Fichier
from voight_kampff._travail.principal import Analyseur, lire_configuration
from voight_kampff.rapport.modele import (
    VERSION_SCHEMA,
    Direction,
    EtatIsolation,
    Localisation,
    ManqueIsolation,
    NiveauIsolation,
    Partie,
    Plage,
    RaisonNonMenee,
)

CONTENU = b"0123456789"
PARTIE = Partie(1, "jpeg", Plage(0, len(CONTENU)), fin_connue=True)
SANS_RESTRICTION = EtatIsolation(NiveauIsolation.REDUITE, (ManqueIsolation.RESEAU,))


def sans_restriction() -> EtatIsolation:
    return SANS_RESTRICTION


@pytest.fixture(autouse=True)
def hors_travail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", False)


@pytest.fixture
def chemin(tmp_path: Path) -> Path:
    fichier = tmp_path / "f.bin"
    fichier.write_bytes(CONTENU)
    return fichier


@pytest.fixture
def descripteur(chemin: Path) -> Iterator[int]:
    ouvert = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    yield ouvert
    os.close(ouvert)


def transmis(descripteur: int) -> str:
    """Valeur de ``--descripteur`` : un handle sous Windows, comme l'envoie le principal."""
    if sys.platform == "win32":  # pragma: no cover - exécuté par la CI Windows
        import msvcrt

        return str(msvcrt.get_osfhandle(descripteur))
    return str(descripteur)


REGLE_DU_MODULE = regle("R-TEST-001", parametres=["valeur"])
"""Règle « module » d'alpha dans les tests du contexte."""


def configuration(
    *identifiants: str,
    formats: tuple[str, ...] = ("jpeg", "pdf"),
    regles: Sequence[dict[str, Any]] = (),
) -> io.BytesIO:
    modules_actifs = [
        {"identifiant": i, "formats": list(formats), "directions": ["rien_de_particulier"]}
        for i in identifiants
    ]
    document = {"version_schema": VERSION_SCHEMA, "modules": modules_actifs, "regles": list(regles)}
    return io.BytesIO(json.dumps(document).encode() + b"\n")


def derouler(
    descripteur: int,
    *identifiants: str,
    analyseurs: Mapping[str, Analyseur] | None = None,
    parties: tuple[Partie, ...] = (PARTIE,),
    regles: Sequence[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    sortie = io.BytesIO()
    code = principal.principal(
        ["--descripteur", transmis(descripteur)],
        configuration(*identifiants, regles=regles),
        sortie,
        analyseurs=analyseurs,
        identifier=lambda _fichier, _taille: parties,
        restreindre=sans_restriction,
    )
    assert code == 0
    messages = [json.loads(ligne) for ligne in sortie.getvalue().splitlines()]
    for message in messages:
        schemas.valider("messages", message)
    return messages


def types(messages: list[dict[str, Any]]) -> list[str]:
    return [message["type"] for message in messages]


def contexte(budget: int = 1 << 20, regles: Sequence[Regle] = (REGLE_DU_MODULE,)) -> Contexte:
    garde.verrouiller()
    directions = {Direction.RIEN_DE_PARTICULIER}
    return Contexte("alpha", directions, Fichier(-1), PARTIE, budget, regles=regles)


# Déroulé


def test_deroule_sans_module(descripteur: int) -> None:
    messages = derouler(descripteur)
    assert types(messages) == ["isolation", "identification", "versions", "fin"]
    assert messages[1]["parties"] == [PARTIE.vers_dict()]
    assert messages[-1]["empreinte"] == hashlib.sha256(CONTENU).hexdigest()


def test_empreinte_calculee_apres_les_modules(chemin: Path, descripteur: int) -> None:
    # ES-08 : l'empreinte envoyée est celle de ce que les modules ont lu, en fin d'analyse.
    def modifie_le_fichier(_contexte: Contexte) -> None:
        with chemin.open("r+b") as fichier:
            fichier.write(b"X")

    messages = derouler(descripteur, "alpha", analyseurs={"alpha": modifie_le_fichier})
    assert messages[-1]["empreinte"] == hashlib.sha256(b"X" + CONTENU[1:]).hexdigest()


def test_garde_posee_avant_l_isolation(descripteur: int) -> None:
    derouler(descripteur)
    garde.exiger()  # ne lève plus : le déroulé a verrouillé le processus


def test_identification_par_defaut(descripteur: int) -> None:
    sortie = io.BytesIO()
    principal.principal(
        ["--descripteur", transmis(descripteur)],
        configuration("alpha"),
        sortie,
        restreindre=sans_restriction,
    )
    identification, module = (json.loads(ligne) for ligne in sortie.getvalue().splitlines()[1:3])
    # Dix chiffres ASCII : du texte brut, que alpha (JPEG, PDF) ne traite pas.
    assert [partie["format"] for partie in identification["parties"]] == ["texte"]
    assert module == {"type": "module", "module": "alpha", "partie": 1, "applicable": False}


def test_parties_hors_perimetre_sautees_numerotation_continue(descripteur: int) -> None:
    parties = (
        Partie(1, "jpeg", Plage(0, 2), fin_connue=True),
        Partie(2, "zip", Plage(2, 2), fin_connue=True),
        Partie(3, "pdf", Plage(4, 6), fin_connue=False),
    )

    def module(contexte: Contexte) -> None:
        contexte.observer("debut", contexte.lire(0, 1).decode("ascii"))

    messages = derouler(descripteur, "alpha", analyseurs={"alpha": module}, parties=parties)
    resultats = [
        (m["observation"]["identifiant"], m["observation"]["partie"], m["observation"]["valeur"])
        for m in messages
        if m["type"] == "observation"
    ]
    assert resultats == [("alpha/1", 1, "0"), ("alpha/2", 3, "4")]
    assert [(m["module"], m["partie"]) for m in messages if m["type"] == "module"] == [
        ("alpha", 1),
        ("alpha", 3),
    ]


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

    png = (Partie(1, "png", Plage(0, len(CONTENU)), fin_connue=True),)
    messages = derouler(descripteur, "alpha", analyseurs={"alpha": interdit}, parties=png)
    assert messages[2] == {"type": "module", "module": "alpha", "partie": 1, "applicable": False}


def test_exception_ecarte_les_resultats(descripteur: int) -> None:
    def fautif(contexte: Contexte) -> None:
        contexte.observer("avant", 1)
        raise ValueError

    messages = derouler(descripteur, "alpha", analyseurs={"alpha": fautif})
    assert types(messages) == [
        "isolation",
        "identification",
        "non_menee",
        "module",
        "versions",
        "fin",
    ]
    assert messages[2]["non_menee"] == {"raison": "erreur_module", "module": "alpha", "partie": 1}


def test_module_absent_ou_non_importe(descripteur: int, monkeypatch: pytest.MonkeyPatch) -> None:
    messages = derouler(descripteur, "alpha", analyseurs={})
    assert messages[2]["non_menee"]["raison"] == "erreur_module"

    monkeypatch.setattr(principal, "importer", lambda: ({"alpha": lambda c: None}, {"alpha"}))
    messages = derouler(descripteur, "alpha")
    assert messages[2]["non_menee"]["raison"] == "erreur_module"


def test_resultats_dans_l_ordre(descripteur: int) -> None:
    def module(contexte: Contexte) -> None:
        premiere = contexte.observer("premiere", "a")
        contexte.constater("R-TEST-001", [premiere], {"valeur": premiere})
        contexte.non_mener(RaisonNonMenee.FICHIER_TRONQUE)

    regles = [regle_dict("R-TEST-001", parametres=["valeur"])]
    messages = derouler(descripteur, "alpha", analyseurs={"alpha": module}, regles=regles)
    assert types(messages)[2:6] == ["observation", "constat", "non_menee", "module"]
    assert messages[3]["constat"]["regle"] == {"identifiant": "R-TEST-001", "version": "1"}
    assert messages[3]["constat"]["phrase"] == {
        "gabarit": "test.regle",
        "parametres": {"valeur": "alpha/1"},
    }


def test_regles_du_moteur_apres_le_module(descripteur: int) -> None:
    def module(contexte: Contexte) -> None:
        contexte.observer("logiciel", "Autre")
        contexte.observer("logiciel", "Générateur 5")
        contexte.observer("largeur", 1024)

    regles = [
        # Satisfaite : la seconde observation « logiciel » est retenue, avec la largeur.
        regle_dict(
            "R-TEST-002",
            **moteur(
                {"observation": "logiciel", "motif": "^Générateur", "parametre": "logiciel"},
                {"observation": "largeur", "parmi": [512, 1024]},
            ),
        ),
        regle_dict("R-TEST-003", **moteur({"observation": "hauteur", "presente": True})),
        regle_dict("R-TEST-004", module="beta", **moteur({"observation": "largeur", "egal": 1024})),
    ]
    messages = derouler(descripteur, "alpha", analyseurs={"alpha": module}, regles=regles)
    constats = [m["constat"] for m in messages if m["type"] == "constat"]
    assert constats == [
        {
            "phrase": {"gabarit": "test.regle", "parametres": {"logiciel": "alpha/2"}},
            "donnees": ["alpha/2", "alpha/3"],
            "regle": {"identifiant": "R-TEST-002", "version": "1"},
            "module": "alpha",
            "fondement": "mesure",
            "categorie": "information_neutre",
            "direction": "rien_de_particulier",
            "partie": 1,
        }
    ]
    assert types(messages)[2:7] == ["observation"] * 3 + ["constat", "module"]


def test_regles_du_moteur_comptees_dans_le_budget(
    descripteur: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(principal, "TAILLE_MAX_SORTIE", principal._RESERVE + 600)

    def module(contexte: Contexte) -> None:
        contexte.observer("n", 1)

    regles = [
        regle_dict(f"R-TEST-{numero:03}", **moteur({"observation": "n", "presente": True}))
        for numero in range(1, 4)
    ]
    messages = derouler(descripteur, "alpha", analyseurs={"alpha": module}, regles=regles)
    assert messages[2]["non_menee"]["raison"] == "limite_depassee"


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
        assert messages[2]["non_menee"] == {
            "raison": "limite_depassee",
            "module": "alpha",
            "partie": 1,
        }


def test_message_trop_long() -> None:
    with pytest.raises(LimiteDepassee):
        contexte().observer("n", ["x" * 4096] * 4096)


# Contexte


def test_garde_hors_processus_de_travail() -> None:
    with pytest.raises(garde.HorsProcessusDeTravail):
        Contexte("alpha", (), Fichier(-1), PARTIE, 0)


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


INDICE_IA = regle(
    "R-TEST-005", categorie="indice", direction="origine_ia", niveau="faible", parametres=["valeur"]
)
DU_MOTEUR = regle("R-TEST-006", **moteur({"observation": "a", "presente": True}))


@pytest.mark.parametrize(
    ("identifiant", "donnee", "parametres", "attendu"),
    [
        ("R-TEST-005", "alpha/1", {"valeur": "alpha/1"}, "direction"),
        ("R-TEST-001", "beta/1", {"valeur": "beta/1"}, "donnees"),
        ("R-TEST-009", "alpha/1", {}, "absente"),
        ("R-TEST-006", "alpha/1", {}, "moteur"),
        ("R-TEST-001", "alpha/1", {}, "paramètres"),
        ("R-TEST-001", "alpha/1", {"valeur": "alpha/1", "autre": "alpha/1"}, "paramètres"),
    ],
)
def test_constat_refuse(
    identifiant: str, donnee: str, parametres: dict[str, str], attendu: str
) -> None:
    c = contexte(regles=(REGLE_DU_MODULE, INDICE_IA, DU_MOTEUR))
    c.observer("a", 1)
    with pytest.raises(ValueError, match=attendu):
        c.constater(identifiant, [donnee], parametres)


def test_constat_d_un_indice_gradue_par_sa_regle() -> None:
    c = contexte(regles=(INDICE_IA,))
    c._directions = frozenset(Direction)
    valeur = c.observer("a", 1)
    c.constater("R-TEST-005", [valeur], {"valeur": valeur})
    constat = json.loads(c.lignes[1])["constat"]
    assert constat["graduation"] == {"niveau": "faible", "evaluee": False}
    assert (constat["categorie"], constat["direction"]) == ("indice", "origine_ia")


@pytest.mark.parametrize(
    "raison",
    [RaisonNonMenee.ERREUR_MODULE, RaisonNonMenee.MODULE_DESACTIVE, RaisonNonMenee.DELAI_DEPASSE],
)
def test_raison_reservee_au_moteur(raison: RaisonNonMenee) -> None:
    with pytest.raises(ValueError, match="moteur"):
        contexte().non_mener(raison)


def test_contexte_lit_le_fichier(descripteur: int) -> None:
    garde.verrouiller()
    c = Contexte("alpha", (), Fichier(descripteur), PARTIE, 1 << 20)
    assert c.lire(3, 2) == b"34"
    assert (c.format_reel, c.taille, c.partie) == ("jpeg", len(CONTENU), 1)


def test_contexte_lit_sa_partie_seulement(descripteur: int) -> None:
    garde.verrouiller()
    partie = Partie(2, "pdf", Plage(4, 4), fin_connue=True)
    c = Contexte("alpha", {Direction.RIEN_DE_PARTICULIER}, Fichier(descripteur), partie, 1 << 20, 7)
    assert (c.format_reel, c.taille, c.partie) == ("pdf", 4, 2)
    assert c.lire(0, 2) == b"45"
    assert c.lire(3, 5) == b"7"  # la partie s'arrête avant la fin du fichier
    assert c.lire(10, 1) == b""
    for position, taille in [(-1, 1), (0, -1), (0, TAILLE_MAX_LECTURE + 1)]:
        with pytest.raises(ValueError, match="lecture"):
            c.lire(position, taille)
    # Numérotation reprise après 7 ; plages ramenées à des positions dans le fichier.
    assert c.observer("n", 1, localisation=Localisation(octets=Plage(1, 2))) == "alpha/8"
    c.observer("sans_plage", 1, localisation=Localisation(chemin="xref"))
    c.non_mener(RaisonNonMenee.FICHIER_TRONQUE, localisation=Localisation(octets=Plage(0, 1)))
    lignes = [json.loads(ligne) for ligne in c.lignes]
    assert lignes[0]["observation"]["localisation"] == {"octets": {"debut": 5, "longueur": 2}}
    assert lignes[0]["observation"]["partie"] == 2
    assert lignes[1]["observation"]["localisation"] == {"chemin": "xref"}
    assert lignes[2]["non_menee"]["localisation"] == {"octets": {"debut": 4, "longueur": 1}}
    assert lignes[2]["non_menee"]["partie"] == 2
    assert c.numero == 9


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
    assert Fichier(descripteur).taille() == 10


# Configuration et import


@pytest.mark.parametrize(
    "ligne",
    [
        pytest.param(b"", id="absente"),
        pytest.param(b'{"version_schema":"0.2.0","modules":[]}', id="sans-fin-de-ligne"),
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


def test_configuration_avec_ses_regles() -> None:
    regles = [regle_dict("R-TEST-002"), regle_dict("R-TEST-001", module="beta")]
    alpha, beta = lire_configuration(configuration("alpha", "beta", regles=regles))
    assert alpha.regles == (regle("R-TEST-002"),)
    assert beta.regles == (regle("R-TEST-001", module="beta"),)


def test_import_des_modules_livres() -> None:
    # Aucun module n'est livré en T12 ni en T13.
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
