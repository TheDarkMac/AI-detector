"""Tests du processus principal face à un vrai processus de travail ou à un factice (T12, T13).

Chaque test lance au moins un interpréteur. Le factice (``travail_factice.py``) exécute le vrai
déroulé avec des analyseurs de test, ou écrit des lignes choisies pour simuler un processus de
travail défaillant ou compromis (ES-04, M-10).
"""

import hashlib
import io
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from systeme import MANQUES_ATTENDUS

from voight_kampff._orchestration import manifestes, travail
from voight_kampff._orchestration.manifestes import Manifeste, ModuleInconnu
from voight_kampff._orchestration.travail import ResultatTravail, executer
from voight_kampff.analyse import Analyse
from voight_kampff.rapport.modele import (
    Direction,
    EtatIsolation,
    EtatTechnique,
    Identification,
    Localisation,
    ManqueIsolation,
    NiveauIsolation,
    NonMenee,
    Partie,
    Plage,
    RaisonNonMenee,
)

FACTICE = Path(__file__).with_name("travail_factice.py")
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
CONTENU = b"VKFT" + bytes(range(256)) * 4
PDF = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
DELAI_COURT = 3.0


def manifeste(
    identifiant: str,
    formats: Sequence[str] = ("jpeg",),
    requiert: Sequence[str] = (),
) -> Manifeste:
    return Manifeste(
        identifiant=identifiant,
        version="1.0",
        formats=tuple(formats),
        exigences=("F-10",),
        regles=(),
        fiche="test",
        directions=(Direction.RIEN_DE_PARTICULIER,),
        requiert=tuple(requiert),
    )


def mesure() -> list[str]:
    """Mesure de couverture dans le processus de travail lancé par le test.

    L'environnement vidé (ADR-0065) empêche coverage de s'inviter seul dans l'interpréteur.
    Seulement pour un processus qui se termine de lui-même : arrêté de force pendant qu'il
    écrit ses mesures, il laisserait un fichier corrompu qui fait échouer ``coverage combine``.
    Et seulement sans restrictions : restreint, il ne peut plus les écrire (ADR-0081).
    """
    return ["-m", "coverage", "run", "--parallel-mode", f"--rcfile={PYPROJECT}"]


def factice(scenario: str, *, mesure_couverture: bool = False) -> Callable[[int], list[str]]:
    def commande(descripteur: int) -> list[str]:
        script = [str(FACTICE), scenario, "--descripteur", str(descripteur)]
        if mesure_couverture:
            return [sys.executable, "-I", "-B", *mesure(), *script, "--sans-restriction"]
        return [sys.executable, "-I", "-B", *script]

    return commande


def ouvrir(chemin: Path, contenu: bytes) -> int:
    chemin.write_bytes(contenu)
    return os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))


@pytest.fixture
def descripteur(tmp_path: Path) -> Iterator[int]:
    ouvert = ouvrir(tmp_path / "analyse.bin", CONTENU)
    yield ouvert
    os.close(ouvert)


@pytest.fixture
def pdf(tmp_path: Path) -> Iterator[int]:
    ouvert = ouvrir(tmp_path / "document.pdf", PDF)
    yield ouvert
    os.close(ouvert)


def analyse_de(resultat: ResultatTravail, taille: int = len(CONTENU)) -> Analyse:
    """Le résultat doit toujours donner une analyse valide : le modèle vérifie la cohérence."""
    assert resultat.parties
    return Analyse(
        identification=Identification(
            nom="analyse.bin",
            format_reel=resultat.parties[0].format,
            taille=taille,
            empreinte=resultat.empreinte or "0" * 64,
            date_analyse=datetime(2026, 10, 26, tzinfo=UTC),
            parties=resultat.parties,
        ),
        isolation=resultat.isolation,
        couverture=resultat.couverture,
        observations=resultat.observations,
        constats=resultat.constats,
        non_menees=resultat.non_menees,
        dependances=resultat.dependances,
    )


def etats(resultat: ResultatTravail, partie: int = 1) -> dict[str, EtatTechnique]:
    techniques = resultat.couverture.techniques
    return {t.module: t.etat for t in techniques if t.partie == partie}


def raisons(resultat: ResultatTravail) -> set[tuple[RaisonNonMenee, str | None]]:
    return {(non_menee.raison, non_menee.module) for non_menee in resultat.non_menees}


# Vrai processus de travail


def test_vrai_processus_identifie_le_format(pdf: int) -> None:
    resultat = executer(pdf, manifestes.decouvrir())
    assert resultat.parties == (Partie(1, "pdf", Plage(0, len(PDF)), fin_connue=True),)
    assert resultat.empreinte == hashlib.sha256(PDF).hexdigest()
    assert set(resultat.isolation.manques) == MANQUES_ATTENDUS
    assert (resultat.isolation.niveau is NiveauIsolation.COMPLETE) == (not MANQUES_ATTENDUS)
    assert resultat.couverture.techniques == ()
    assert not resultat.interrompue
    analyse_de(resultat, len(PDF))


def test_vrai_processus_format_non_reconnu(descripteur: int) -> None:
    resultat = executer(descripteur, manifestes.decouvrir())
    assert resultat.parties == ()
    assert resultat.empreinte == hashlib.sha256(CONTENU).hexdigest()
    assert not resultat.interrompue


def test_point_d_entree_mesure() -> None:
    # Sous coverage, et arrêté avant les restrictions faute de descripteur : le point d'entrée
    # et la réservation de la sortie sont mesurés, ce qu'un processus restreint ne permet pas.
    commande = [sys.executable, "-I", "-B", *mesure(), "-m", "voight_kampff._travail"]
    termine = subprocess.run(commande, capture_output=True, check=False)
    assert termine.returncode == 2
    assert b"--descripteur" in termine.stderr


def test_manque_ajoute_par_le_principal() -> None:
    # Sous macOS, si la mémoire ne peut pas être surveillée (ADR-0079).
    recue = EtatIsolation(NiveauIsolation.REDUITE, (ManqueIsolation.TEMPS,))
    assert travail._avec_manque(recue, ManqueIsolation.MEMOIRE) == EtatIsolation(
        NiveauIsolation.REDUITE, (ManqueIsolation.MEMOIRE, ManqueIsolation.TEMPS)
    )
    complete = EtatIsolation(NiveauIsolation.COMPLETE)
    assert travail._avec_manque(complete, ManqueIsolation.MEMOIRE).manques == (
        ManqueIsolation.MEMOIRE,
    )


def test_commande_du_processus_de_travail() -> None:
    assert travail.commande_travail(7) == [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "voight_kampff._travail",
        "--descripteur",
        "7",
    ]


def test_vrai_processus_module_d_un_autre_format(pdf: int) -> None:
    resultat = executer(pdf, (manifeste("alpha"),))
    assert etats(resultat) == {"alpha": EtatTechnique.NON_APPLICABLE}
    assert resultat.non_menees == ()
    analyse_de(resultat, len(PDF))


# Déroulé réel avec des analyseurs de test


def test_modules_isoles_les_uns_des_autres(descripteur: int) -> None:
    actifs = [manifeste("alpha"), manifeste("beta"), manifeste("gamma", ("png",))]
    resultat = executer(
        descripteur,
        (*actifs, manifeste("delta")),
        commande=factice("modules", mesure_couverture=True),
    )
    assert etats(resultat) == {
        "alpha": EtatTechnique.APPLIQUEE,
        "beta": EtatTechnique.NON_MENEE,
        "gamma": EtatTechnique.NON_APPLICABLE,
        "delta": EtatTechnique.PARTIELLE,
    }
    # L'exception de beta n'a touché que beta, et son observation a été écartée (ADR-0060).
    assert raisons(resultat) == {
        (RaisonNonMenee.ERREUR_MODULE, "beta"),
        (RaisonNonMenee.FORMAT_PARTIEL, "delta"),
    }
    assert [o.identifiant for o in resultat.observations] == ["alpha/1", "alpha/2", "delta/1"]
    assert resultat.observations[0].valeur == "VKFT"
    assert resultat.observations[1].valeur == len(CONTENU)
    assert len(resultat.constats) == 1
    # Le texte affiché par alpha n'a pas atteint le protocole.
    assert not resultat.interrompue
    assert resultat.empreinte == hashlib.sha256(CONTENU).hexdigest()
    analyse_de(resultat)


def test_polyglotte_chaque_format_du_perimetre_analyse(descripteur: int) -> None:
    livres = (manifeste("alpha", ("jpeg", "pdf")), manifeste("delta", ("pdf",)))
    resultat = executer(descripteur, livres, commande=factice("polyglotte", mesure_couverture=True))
    assert [p.format for p in resultat.parties or ()] == ["jpeg", "zip", "pdf"]
    assert etats(resultat, 1) == {
        "alpha": EtatTechnique.APPLIQUEE,
        "delta": EtatTechnique.NON_APPLICABLE,
    }
    assert etats(resultat, 2) == {}  # hors périmètre : aucune technique
    assert etats(resultat, 3) == {
        "alpha": EtatTechnique.APPLIQUEE,
        "delta": EtatTechnique.PARTIELLE,
    }
    # Chaque module lit sa partie comme un fichier autonome ; la numérotation continue.
    valeurs = {(o.identifiant, o.partie): o.valeur for o in resultat.observations}
    assert valeurs == {
        ("alpha/1", 1): "VKFT",
        ("alpha/2", 1): 4,
        ("alpha/3", 3): CONTENU[104:108].decode("ascii"),
        ("alpha/4", 3): len(CONTENU) - 104,
        ("delta/1", 3): CONTENU[104:106].hex(),
    }
    assert (
        NonMenee(
            RaisonNonMenee.HORS_PERIMETRE, localisation=Localisation(octets=Plage(4, 100)), partie=2
        )
        in resultat.non_menees
    )
    # La plage relative à la partie 3 a été ramenée à une position dans le fichier.
    partielle = next(n for n in resultat.non_menees if n.module == "delta")
    assert partielle.localisation == Localisation(octets=Plage(105, 1))
    assert analyse_de(resultat).identification.octets_non_reconnus == ()


def test_module_desactive_et_ceux_qui_le_requierent(descripteur: int) -> None:
    livres = (manifeste("alpha"), manifeste("beta"), manifeste("delta", requiert=("beta",)))
    resultat = executer(
        descripteur, livres, {"beta"}, commande=factice("modules", mesure_couverture=True)
    )
    assert etats(resultat) == {
        "alpha": EtatTechnique.APPLIQUEE,
        "beta": EtatTechnique.NON_MENEE,
        "delta": EtatTechnique.NON_MENEE,
    }
    assert raisons(resultat) == {
        (RaisonNonMenee.MODULE_DESACTIVE, "beta"),
        (RaisonNonMenee.MODULE_DESACTIVE, "delta"),
    }
    analyse_de(resultat)


def test_module_inconnu_a_desactiver(descripteur: int) -> None:
    with pytest.raises(ModuleInconnu):
        executer(descripteur, (manifeste("alpha"),), {"omega"})


@pytest.mark.parametrize("arret", ["epsilon", "eta"], ids=["sys.exit", "os._exit"])
def test_arret_du_processus_pendant_un_module(descripteur: int, arret: str) -> None:
    livres = (manifeste("alpha"), manifeste(arret), manifeste("delta"))
    resultat = executer(descripteur, livres, commande=factice("modules"))
    # Le module terminé garde ses résultats ; les autres deviennent non menés.
    assert etats(resultat) == {
        "alpha": EtatTechnique.APPLIQUEE,
        arret: EtatTechnique.NON_MENEE,
        "delta": EtatTechnique.NON_MENEE,
    }
    assert raisons(resultat) == {
        (RaisonNonMenee.ARRET_PROCESSUS, arret),
        (RaisonNonMenee.ARRET_PROCESSUS, "delta"),
        (RaisonNonMenee.ARRET_PROCESSUS, None),
    }
    assert resultat.interrompue
    assert resultat.empreinte is None
    assert analyse_de(resultat).interrompue


def test_delai_depasse(descripteur: int) -> None:
    debut = time.monotonic()
    resultat = executer(
        descripteur, (manifeste("zeta"),), delai=DELAI_COURT, commande=factice("modules")
    )
    assert time.monotonic() - debut < DELAI_COURT + 10
    assert raisons(resultat) == {
        (RaisonNonMenee.DELAI_DEPASSE, "zeta"),
        (RaisonNonMenee.DELAI_DEPASSE, None),
    }
    analyse_de(resultat)


def test_configuration_trop_longue(descripteur: int, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(travail, "TAILLE_MAX_CONFIGURATION", 10)
    with pytest.raises(ValueError, match="configuration"):
        executer(descripteur, (manifeste("alpha"),))


# Processus de travail défaillant ou compromis


def test_factice_valide(descripteur: int) -> None:
    resultat = executer(
        descripteur,
        (manifeste("alpha"), manifeste("beta")),
        commande=factice("valide", mesure_couverture=True),
    )
    assert etats(resultat) == {
        "alpha": EtatTechnique.APPLIQUEE,
        "beta": EtatTechnique.NON_APPLICABLE,
    }
    assert resultat.isolation.manques == (ManqueIsolation.RESEAU,)
    assert resultat.empreinte == "0" * 64
    # Une non menée sans module porte sur le fichier entier : elle n'interrompt pas l'analyse.
    assert resultat.non_menees == (NonMenee(RaisonNonMenee.FICHIER_TRONQUE),)
    assert not resultat.interrompue
    analyse_de(resultat)


def test_factice_polyglotte_valide(descripteur: int) -> None:
    resultat = executer(
        descripteur, (manifeste("alpha", ("jpeg", "pdf")),), commande=factice("polyglotte_valide")
    )
    assert {(t.module, t.partie): t.etat for t in resultat.couverture.techniques} == {
        ("alpha", 1): EtatTechnique.APPLIQUEE,
        ("alpha", 3): EtatTechnique.APPLIQUEE,
    }
    assert [o.partie for o in resultat.observations] == [3]
    assert {(n.raison, n.partie) for n in resultat.non_menees} == {
        (RaisonNonMenee.HORS_PERIMETRE, 2),
        (RaisonNonMenee.FORMAT_PARTIEL, 2),
    }
    analyse_de(resultat)


def test_factice_partie_tronquee(descripteur: int) -> None:
    livres = (manifeste("alpha"), manifeste("beta"))
    resultat = executer(descripteur, livres, commande=factice("partie_tronquee"))
    # Le principal déclare la partie tronquée non menée : rien ne vient du travail ici.
    assert resultat.non_menees == (
        NonMenee(
            RaisonNonMenee.FICHIER_TRONQUE,
            localisation=Localisation(octets=Plage(0, len(CONTENU))),
            partie=1,
        ),
    )
    assert not resultat.interrompue
    analyse_de(resultat)


def test_factice_aucun_format_reconnu(descripteur: int) -> None:
    resultat = executer(descripteur, (manifeste("alpha"),), commande=factice("identification_vide"))
    assert resultat.parties == ()
    assert resultat.couverture.techniques == ()
    assert resultat.non_menees == ()
    assert not resultat.interrompue


def test_factice_seulement_hors_perimetre(descripteur: int) -> None:
    resultat = executer(descripteur, (manifeste("alpha"),), commande=factice("hors_perimetre"))
    assert [p.format for p in resultat.parties or ()] == ["gif"]
    assert resultat.couverture.techniques == ()
    assert [n.raison for n in resultat.non_menees] == [RaisonNonMenee.HORS_PERIMETRE]


MESSAGE_INVALIDE = [
    "sans_isolation",
    "sans_identification",
    "identification_double",
    "identification_rangs",
    "identification_hors_fichier",
    "partie_d_un_autre_module",
    "module_d_une_autre_partie",
    "non_menee_partie_inconnue",
    "hors_perimetre_par_le_travail",
    "json_invalide",
    "nan",
    "infini",
    "cle_double",
    "utf8_invalide",
    "pas_un_objet",
    "schema",
    "isolation_double",
    "module_inconnu",
    "identifiant_sans_prefixe",
    "identifiant_double",
    "modele",
    "constat_sans_donnee",
    "direction_interdite",
    "raison_reservee",
    "raison_reservee_fichier",
    "erreur_apres_resultats",
    "resultat_apres_erreur",
    "ordre_des_modules",
    "module_en_trop",
    "non_applicable_avec_resultat",
    "fin_trop_tot",
    "fin_sans_versions",
    "versions_double",
    "dependance_double",
    "ligne_apres_fin",
    "ligne_coupee",
]


@pytest.mark.parametrize(
    ("scenario", "raison"),
    [
        *((scenario, RaisonNonMenee.MESSAGE_INVALIDE) for scenario in MESSAGE_INVALIDE),
        ("ligne_trop_longue", RaisonNonMenee.MESSAGE_INVALIDE),
        ("sortie_trop_longue", RaisonNonMenee.MESSAGE_INVALIDE),
        ("rien", RaisonNonMenee.ARRET_PROCESSUS),
        ("code_non_nul", RaisonNonMenee.ARRET_PROCESSUS),
        ("ferme_trop_tot", RaisonNonMenee.ARRET_PROCESSUS),
        ("silence", RaisonNonMenee.DELAI_DEPASSE),
        ("silence_apres_identification", RaisonNonMenee.DELAI_DEPASSE),
        ("ferme_et_attend", RaisonNonMenee.DELAI_DEPASSE),
    ],
)
def test_factice_refuse(descripteur: int, scenario: str, raison: RaisonNonMenee) -> None:
    attente = {"silence", "silence_apres_identification", "ferme_et_attend"}
    resultat = executer(
        descripteur,
        (manifeste("alpha"), manifeste("beta")),
        delai=DELAI_COURT if scenario in attente else travail.DELAI,
        commande=factice(scenario),
    )
    assert NonMenee(raison) in resultat.non_menees
    assert {n.raison for n in resultat.non_menees} == {raison}
    assert resultat.interrompue
    assert resultat.empreinte is None
    if resultat.parties is None:
        # Arrêt avant l'identification : rien à analyser, la soumission refusera le fichier.
        assert resultat.couverture.techniques == ()
        return
    analyse = analyse_de(resultat)
    # Les modules inachevés n'ont aucun résultat : seul un module terminé en garde.
    termines = {
        t.module for t in analyse.couverture.techniques if t.etat is not EtatTechnique.NON_MENEE
    }
    assert {o.module for o in analyse.observations} <= termines


def test_isolation_inconnue_si_aucun_message(descripteur: int) -> None:
    resultat = executer(descripteur, (manifeste("alpha"),), commande=factice("rien"))
    assert resultat.isolation.niveau is NiveauIsolation.REDUITE
    assert set(resultat.isolation.manques) == set(ManqueIsolation)


# Cas que les processus de travail factices ne provoquent pas de façon sûre


def test_ecriture_dans_un_tube_ferme() -> None:
    flux = io.BytesIO()
    flux.close()
    travail._ecrire(flux, b"configuration")  # aucune exception : la lecture constatera l'arrêt


def test_processus_sans_tubes() -> None:
    sans_tubes = cast("subprocess.Popen[bytes]", SimpleNamespace(stdin=None, stdout=None))
    with pytest.raises(RuntimeError, match="tubes"):
        travail._Reception((), 0).recevoir(sans_tubes, b"", 0.0)
