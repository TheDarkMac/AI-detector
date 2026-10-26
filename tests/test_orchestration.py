"""Tests du processus principal face à un vrai processus de travail ou à un factice (T12).

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
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from voight_kampff._orchestration import manifestes, travail
from voight_kampff._orchestration.manifestes import Manifeste, ModuleInconnu
from voight_kampff._orchestration.travail import ResultatTravail, executer
from voight_kampff.rapport.modele import (
    Direction,
    EtatTechnique,
    Identification,
    ManqueIsolation,
    NiveauIsolation,
    NonMenee,
    RaisonNonMenee,
    Rapport,
    VersionCatalogue,
    Versions,
)

FACTICE = Path(__file__).with_name("travail_factice.py")
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
CONTENU = b"VKFT" + bytes(range(256)) * 4
DELAI_COURT = 3.0


def manifeste(
    identifiant: str,
    formats: Sequence[str] = ("test",),
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
    """
    return ["-m", "coverage", "run", "--parallel-mode", f"--rcfile={PYPROJECT}"]


def factice(scenario: str, *, mesure_couverture: bool = False) -> Callable[[int], list[str]]:
    def commande(descripteur: int) -> list[str]:
        script = [str(FACTICE), scenario, "--descripteur", str(descripteur)]
        avant = mesure() if mesure_couverture else []
        return [sys.executable, "-I", "-B", *avant, *script]

    return commande


@pytest.fixture
def descripteur(tmp_path: Path) -> Iterator[int]:
    chemin = tmp_path / "analyse.bin"
    chemin.write_bytes(CONTENU)
    ouvert = os.open(chemin, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    yield ouvert
    os.close(ouvert)


def rapport_de(resultat: ResultatTravail) -> Rapport:
    """Le résultat doit toujours donner un rapport valide : le modèle vérifie la cohérence."""
    return Rapport(
        identification=Identification(
            nom="analyse.bin",
            format_reel="test",
            taille=len(CONTENU),
            empreinte=resultat.empreinte or "0" * 64,
            date_analyse=datetime(2026, 10, 26, tzinfo=UTC),
        ),
        versions=Versions(
            outil="0.1.0",
            catalogue=VersionCatalogue("0", date(2026, 10, 26), "0" * 64, False),
            dependances=resultat.dependances,
        ),
        isolation=resultat.isolation,
        couverture=resultat.couverture,
        observations=resultat.observations,
        constats=resultat.constats,
        non_menees=resultat.non_menees,
    )


def etats(resultat: ResultatTravail) -> dict[str, EtatTechnique]:
    return {technique.module: technique.etat for technique in resultat.couverture.techniques}


def raisons(resultat: ResultatTravail) -> set[tuple[RaisonNonMenee, str | None]]:
    return {(non_menee.raison, non_menee.module) for non_menee in resultat.non_menees}


# Vrai processus de travail


def test_vrai_processus_sans_module(descripteur: int) -> None:
    resultat = executer(descripteur, manifestes.decouvrir())
    assert resultat.empreinte == hashlib.sha256(CONTENU).hexdigest()
    # Aucune restriction avant T14 : l'isolation est réduite et tout manque.
    assert resultat.isolation.niveau is NiveauIsolation.REDUITE
    assert set(resultat.isolation.manques) == set(ManqueIsolation)
    assert resultat.couverture.techniques == ()
    assert not resultat.interrompue
    rapport_de(resultat)


def test_vrai_processus_mesure(descripteur: int) -> None:
    # Même processus, sous coverage : mesure le point d'entrée du processus de travail.
    def commande(valeur: int) -> list[str]:
        arguments = ["-m", "voight_kampff._travail", "--descripteur", str(valeur)]
        return [sys.executable, "-I", "-B", *mesure(), *arguments]

    resultat = executer(descripteur, (), commande=commande)
    assert resultat.empreinte == hashlib.sha256(CONTENU).hexdigest()


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


def test_vrai_processus_sans_identification_aucun_module_applicable(descripteur: int) -> None:
    # Avant T13, aucun format n'est identifié : un module actif est « non applicable ».
    resultat = executer(descripteur, (manifeste("alpha"),))
    assert etats(resultat) == {"alpha": EtatTechnique.NON_APPLICABLE}
    assert resultat.non_menees == ()
    rapport_de(resultat)


# Déroulé réel avec des analyseurs de test


def test_modules_isoles_les_uns_des_autres(descripteur: int) -> None:
    actifs = [manifeste("alpha"), manifeste("beta"), manifeste("gamma", ("autre",))]
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
    rapport_de(resultat)


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
    rapport_de(resultat)


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
    assert rapport_de(resultat).interrompue


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
    rapport_de(resultat)


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
    rapport_de(resultat)


MESSAGE_INVALIDE = [
    "sans_isolation",
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
        ("ligne_trop_longue", RaisonNonMenee.LIMITE_DEPASSEE),
        ("sortie_trop_longue", RaisonNonMenee.LIMITE_DEPASSEE),
        ("rien", RaisonNonMenee.ARRET_PROCESSUS),
        ("code_non_nul", RaisonNonMenee.ARRET_PROCESSUS),
        ("silence", RaisonNonMenee.DELAI_DEPASSE),
        ("ferme_et_attend", RaisonNonMenee.DELAI_DEPASSE),
    ],
)
def test_factice_refuse(descripteur: int, scenario: str, raison: RaisonNonMenee) -> None:
    resultat = executer(
        descripteur,
        (manifeste("alpha"), manifeste("beta")),
        delai=DELAI_COURT if scenario in {"silence", "ferme_et_attend"} else travail.DELAI,
        commande=factice(scenario),
    )
    assert NonMenee(raison) in resultat.non_menees
    assert {n.raison for n in resultat.non_menees} == {raison}
    assert resultat.interrompue
    assert resultat.empreinte is None
    rapport = rapport_de(resultat)
    # Les modules inachevés n'ont aucun résultat : seul un module terminé en garde.
    termines = {
        t.module for t in rapport.couverture.techniques if t.etat is not EtatTechnique.NON_MENEE
    }
    assert {o.module for o in rapport.observations} <= termines


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
        travail._Reception(()).recevoir(sans_tubes, b"", 0.0)
