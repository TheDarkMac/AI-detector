"""Tests de la soumission d'un fichier et de l'interface publique (F-01 à F-05, ES-08, T13).

Le processus principal ouvre, hache, lance le processus de travail, contrôle l'empreinte
finale, puis rend une analyse ou un refus explicite.
"""

import dataclasses
import hashlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from catalogues import CATALOGUE, ecrire_catalogue
from echantillons import PDF, archive, docx, jpeg

from voight_kampff import Analyse, AnalyseRefusee, MotifRefus, analyser
from voight_kampff._orchestration import catalogue, manifestes, soumission
from voight_kampff._orchestration.catalogue import CatalogueInvalide
from voight_kampff._orchestration.manifestes import Manifeste, ModuleInconnu
from voight_kampff._orchestration.travail import ResultatTravail
from voight_kampff.rapport.modele import (
    Couverture,
    Direction,
    EtatIsolation,
    EtatTechnique,
    NiveauIsolation,
    Partie,
    Plage,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("F-01", "F-04", "F-05", "ES-01", "ES-08")

FACTICE = Path(__file__).with_name("travail_factice.py")
MODULES = tuple(
    Manifeste(nom, "1.0", ("jpeg",), ("F-10",), (), "test", (Direction.RIEN_DE_PARTICULIER,))
    for nom in ("alpha", "beta")
)


def factice(scenario: str) -> Callable[[int], list[str]]:
    def commande(descripteur: int) -> list[str]:
        return [
            sys.executable,
            "-I",
            "-B",
            str(FACTICE),
            scenario,
            "--descripteur",
            str(descripteur),
        ]

    return commande


def ecrire(dossier: Path, nom: str, contenu: bytes) -> Path:
    chemin = dossier / nom
    chemin.write_bytes(contenu)
    return chemin


# Analyses livrées


def test_analyse_d_un_pdf(tmp_path: Path) -> None:
    analyse = analyser(ecrire(tmp_path, "rapport.pdf", PDF))
    identification = analyse.identification
    assert identification.nom == "rapport.pdf"
    assert identification.format_reel == "pdf"
    assert identification.taille == len(PDF)
    assert identification.empreinte == hashlib.sha256(PDF).hexdigest()
    assert identification.extension_concordante is True
    assert identification.date_analyse.microsecond == 0
    # Aucun module livré : seules figurent les techniques hors V1 qui s'appliquent au PDF.
    assert {(t.module, t.etat, t.version) for t in analyse.couverture.techniques} == {
        (technique, EtatTechnique.NON_MENEE, None)
        for technique in ("referencepdf", "references", "pointstracage")
    }
    assert {n.raison for n in analyse.non_menees} == {RaisonNonMenee.HORS_V1}
    assert analyse.catalogue == catalogue.charger(manifestes.decouvrir()).version
    assert not analyse.catalogue.fourni_par_utilisateur
    assert not analyse.interrompue


def test_polyglotte_et_extension_discordante(tmp_path: Path) -> None:
    contenu = jpeg() + docx() + b"\x00\x00"
    analyse = analyser(str(ecrire(tmp_path, "photo.png", contenu)))
    identification = analyse.identification
    assert [(p.format, p.octets.debut) for p in identification.parties] == [
        ("jpeg", 0),
        ("docx", len(jpeg())),
    ]
    assert identification.extension == "png"
    assert identification.extension_concordante is False
    assert identification.octets_non_reconnus == (Plage(len(contenu) - 2, 2),)
    # Chaque technique hors V1 figure sur les deux parties : non menée sur celle de ses
    # formats, non applicable sur l'autre (ADR-0087).
    etats = {(t.module, t.partie): t.etat for t in analyse.couverture.techniques}
    assert etats[("ela", 1)] is EtatTechnique.NON_MENEE
    assert etats[("ela", 2)] is EtatTechnique.NON_APPLICABLE
    assert etats[("stylometrie", 1)] is EtatTechnique.NON_APPLICABLE
    assert etats[("stylometrie", 2)] is EtatTechnique.NON_MENEE
    assert ("enf", 1) not in etats  # ne s'applique à aucune des deux parties


def test_partie_hors_perimetre_declaree_non_analysee(tmp_path: Path) -> None:
    contenu = jpeg() + archive(("a.txt", b"a"))
    analyse = analyser(ecrire(tmp_path, "photo.jpg", contenu))
    assert [
        (n.raison, n.partie) for n in analyse.non_menees if n.raison is not RaisonNonMenee.HORS_V1
    ] == [(RaisonNonMenee.HORS_PERIMETRE, 2)]


@pytest.mark.exigence("NF-03")
def test_arret_apres_l_identification_resultat_partiel(tmp_path: Path) -> None:
    # Pas d'empreinte finale du travail : le principal hache de nouveau, à l'identique.
    analyse = soumission.soumettre(
        ecrire(tmp_path, "f.jpg", b"contenu"),
        manifestes=MODULES,
        hors_v1=(),
        delai=3.0,
        commande=factice("silence_apres_identification"),
    )
    assert analyse.interrompue
    assert {(t.module, t.etat) for t in analyse.couverture.techniques} == {
        ("alpha", EtatTechnique.NON_MENEE),
        ("beta", EtatTechnique.NON_MENEE),
    }


# Refus (F-04, ES-08)


@pytest.mark.parametrize(
    ("contenu", "motif", "extrait"),
    [
        pytest.param(b"", MotifRefus.VIDE, "fichier vide", id="vide"),
        pytest.param(b"\x00\x01\x02", MotifRefus.FORMAT_INCONNU, "non reconnu", id="inconnu"),
        pytest.param(b"GIF89a" + b"\x00" * 10, MotifRefus.HORS_PERIMETRE, "(gif)", id="gif"),
    ],
)
@pytest.mark.exigence("ES-14")
def test_contenu_refuse(tmp_path: Path, contenu: bytes, motif: MotifRefus, extrait: str) -> None:
    with pytest.raises(AnalyseRefusee) as refus:
        analyser(ecrire(tmp_path, "SECRET.bin", contenu))
    assert refus.value.motif is motif
    assert extrait in str(refus.value)
    assert "SECRET" not in str(refus.value)  # le nom est identifiant (ES-14)


def test_dossier_refuse(tmp_path: Path) -> None:
    with pytest.raises(AnalyseRefusee) as refus:
        analyser(tmp_path)
    # Sous Windows, ouvrir un dossier échoue avant même le contrôle du type.
    assert refus.value.motif in {MotifRefus.NON_REGULIER, MotifRefus.ILLISIBLE}


def test_fichier_absent_refuse(tmp_path: Path) -> None:
    with pytest.raises(AnalyseRefusee) as refus:
        analyser(tmp_path / "absent.jpg")
    assert refus.value.motif is MotifRefus.ILLISIBLE
    assert str(refus.value).startswith("fichier illisible : ")


@pytest.mark.skipif(sys.platform == "win32", reason="tubes nommés et /dev/null POSIX")
def test_fichiers_speciaux_refuses(tmp_path: Path) -> None:
    tube = tmp_path / "tube"
    os.mkfifo(tube)
    for chemin in (tube, Path("/dev/null")):
        # L'ouverture ne bloque pas sur un tube sans écrivain (M-30).
        with pytest.raises(AnalyseRefusee) as refus:
            analyser(chemin)
        assert refus.value.motif is MotifRefus.NON_REGULIER


def test_module_inconnu_refuse_avant_toute_lecture(tmp_path: Path) -> None:
    with pytest.raises(ModuleInconnu):
        analyser(tmp_path / "absent.jpg", desactiver={"omega"})


def test_empreinte_finale_differente(tmp_path: Path) -> None:
    # Le factice annonce une empreinte nulle : ce n'est pas celle du fichier ouvert.
    with pytest.raises(AnalyseRefusee) as refus:
        soumission.soumettre(
            ecrire(tmp_path, "f.jpg", b"contenu"),
            catalogue=CATALOGUE,
            manifestes=MODULES,
            commande=factice("valide"),
        )
    assert refus.value.motif is MotifRefus.FICHIER_MODIFIE


def test_fichier_modifie_pendant_un_arret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chemin = ecrire(tmp_path, "f.jpg", b"contenu")

    def arret_et_modification(*_arguments: Any, **_options: Any) -> ResultatTravail:
        chemin.write_bytes(b"autre contenu")
        return ResultatTravail(
            parties=(Partie(1, "jpeg", Plage(0, 7), fin_connue=True),),
            isolation=EtatIsolation(NiveauIsolation.COMPLETE),
            couverture=Couverture((), ()),
            observations=(),
            constats=(),
            non_menees=(),
            dependances=(),
            empreinte=None,
        )

    monkeypatch.setattr(soumission, "executer", arret_et_modification)
    with pytest.raises(AnalyseRefusee) as refus:
        soumission.soumettre(chemin, manifestes=())
    assert refus.value.motif is MotifRefus.FICHIER_MODIFIE


def test_arret_avant_l_identification(tmp_path: Path) -> None:
    with pytest.raises(AnalyseRefusee) as refus:
        soumission.soumettre(
            ecrire(tmp_path, "f.jpg", b"contenu"), manifestes=MODULES, commande=factice("rien")
        )
    assert refus.value.motif is MotifRefus.ANALYSE_IMPOSSIBLE
    assert refus.value.raison is RaisonNonMenee.ARRET_PROCESSUS
    assert "(arret_processus)" in str(refus.value)


# Éléments de la soumission


@pytest.mark.parametrize(
    ("chemin", "nom"),
    [
        ("dossier/photo.jpg", "photo.jpg"),
        (Path("dossier") / "photo.jpg", "photo.jpg"),
        ("\udcff.jpg", "�.jpg"),  # octet non UTF-8 d'un nom POSIX
        ("", "�"),
        pytest.param(
            "a\\b.jpg",
            "a�b.jpg",
            marks=pytest.mark.skipif(sys.platform == "win32", reason="séparateur sous Windows"),
        ),
    ],
)
def test_nom_affichable(chemin: str | Path, nom: str) -> None:
    assert soumission.nom_affichable(chemin) == nom


def test_empreinte_toujours_depuis_le_debut(tmp_path: Path) -> None:
    descripteur = soumission.ouvrir(ecrire(tmp_path, "f", PDF))
    try:
        os.read(descripteur, 5)
        assert soumission.empreinte(descripteur) == (hashlib.sha256(PDF).hexdigest(), len(PDF))
    finally:
        os.close(descripteur)


def test_analyse_verifiee_comme_un_rapport(tmp_path: Path) -> None:
    analyse = analyser(ecrire(tmp_path, "f.pdf", PDF))
    with pytest.raises(ValueError, match="hors_perimetre"):
        dataclasses.replace(
            analyse,
            identification=dataclasses.replace(
                analyse.identification,
                parties=(*analyse.identification.parties, Partie(2, "zip", Plage(1, 2), True)),
            ),
        )
    assert isinstance(analyse, Analyse)


# Catalogue (T15, ADR-0086)


def test_catalogue_fourni_par_l_utilisateur(tmp_path: Path) -> None:
    dossier = ecrire_catalogue(tmp_path / "catalogue")
    analyse = analyser(ecrire(tmp_path, "f.pdf", PDF), catalogue=dossier)
    assert analyse.catalogue.fourni_par_utilisateur
    assert (analyse.catalogue.version, analyse.catalogue.date.isoformat()) == (
        "1.2.3",
        "2026-10-20",
    )


def test_catalogue_invalide_avant_toute_lecture(tmp_path: Path) -> None:
    dossier = ecrire_catalogue(tmp_path / "catalogue", entete="format = 2\n")
    with pytest.raises(CatalogueInvalide, match=r"catalogue\.toml"):
        analyser(tmp_path / "absent.pdf", catalogue=dossier)
