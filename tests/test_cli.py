"""Tests de la ligne de commande (T10, T12, T13)."""

import dataclasses
import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from catalogues import VERSION, ecrire_catalogue, moteur, regle_dict, toml_regles
from echantillons import PDF, archive, jpeg

from voight_kampff import Analyse, __version__
from voight_kampff._orchestration import catalogue, manifestes
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff.cli import main, resume
from voight_kampff.rapport.modele import (
    Couverture,
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
    TechniqueCouverte,
)


def test_version_affichee(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--version"])
    assert sortie.value.code == 0
    assert capsys.readouterr().out.strip() == f"voight-kampff {__version__}"


def test_sans_argument_affiche_l_aide(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: voight-kampff" in capsys.readouterr().out


def test_liste_des_modules(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--modules"]) == 0
    assert capsys.readouterr().out == "Aucun module d'analyse livré dans cette version.\n"


def test_liste_des_modules_livres(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    livre = Manifeste("exif", "1.2.0", ("jpeg",), ("F-10",), (), "exif", ())
    monkeypatch.setattr(manifestes, "decouvrir", lambda: (livre,))
    assert main(["--modules"]) == 0
    assert capsys.readouterr().out == "exif 1.2.0\n"


def test_option_inconnue_refusee(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--option-inexistante"])
    assert sortie.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_lancement_par_module() -> None:
    # Mode isolé (-I), comme le processus de travail le sera (ADR-0036).
    resultat = subprocess.run(
        [sys.executable, "-I", "-m", "voight_kampff", "--version"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert resultat.stdout.strip() == f"voight-kampff {__version__}"


# Commande d'analyse (T13, ADR-0073, ADR-0075)


def test_resume_d_un_polyglotte(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    contenu = jpeg() + archive(("a.txt", b"a")) + b"\x00\x00"
    chemin = tmp_path / "SOURCE-photo.png"
    chemin.write_bytes(contenu)
    assert main([str(chemin)]) == 0
    sortie = capsys.readouterr().out
    fin_jpeg = len(jpeg()) - 1
    assert sortie.splitlines()[:5] == [
        "[1/1] format réel : jpeg",
        "  extension : png, discordante",
        f"  partie 1 : jpeg, octets 0 à {fin_jpeg}",
        f"  partie 2 : zip, octets {fin_jpeg + 1} à {len(contenu) - 3}, "
        "hors périmètre, non analysée",
        f"  non reconnus : octets {len(contenu) - 2} à {len(contenu) - 1}",
    ]
    assert "  technique ela, partie 1 : hors de cette version" in sortie
    assert "hors_v1" not in sortie  # dit une fois, avec la technique
    livre = catalogue.charger(manifestes.decouvrir()).version
    assert sortie.endswith(
        f"  catalogue : {livre.version} du {livre.date.isoformat()}, "
        f"empreinte {livre.empreinte}\n"
        "  nom et empreinte du fichier : masqués\n"
    )
    # Ni le nom ni l'empreinte n'apparaissent (ADR-0031).
    assert "SOURCE" not in sortie
    assert hashlib.sha256(contenu).hexdigest() not in sortie


def test_lot_avec_un_refus(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    vide = tmp_path / "vide.pdf"
    vide.write_bytes(b"")
    document = tmp_path / "document.pdf"
    document.write_bytes(PDF)
    assert main([str(vide), str(document)]) == 1
    sorties = capsys.readouterr()
    assert sorties.err == "[1/2] refusé : fichier vide : aucun format à identifier\n"
    assert sorties.out.startswith("[2/2] format réel : pdf\n  extension : pdf, concordante\n")


def test_desactiver_un_module_inconnu(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--desactiver", "omega", "f.pdf"])
    assert sortie.value.code == 2
    assert "module inconnu : omega ; modules livrés : aucun" in capsys.readouterr().err


def test_desactiver_un_module_livre(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    livre = Manifeste("exif", "1.2.0", ("pdf",), ("F-10",), (), "exif", (Direction.ORIGINE_IA,))
    monkeypatch.setattr(manifestes, "decouvrir", lambda: (livre,))
    document = tmp_path / "document.pdf"
    document.write_bytes(PDF)
    assert main(["--desactiver", "exif", str(document)]) == 0
    sortie = capsys.readouterr().out
    assert "  technique exif, partie 1 : non menée\n" in sortie
    assert "  non menée : module_desactive (exif, partie 1)\n" in sortie


def test_resume_de_chaque_element() -> None:
    analyse = Analyse(
        identification=Identification(
            nom="sans-extension",
            format_reel="pdf",
            taille=10,
            empreinte="0" * 64,
            date_analyse=datetime(2026, 10, 27, tzinfo=UTC),
            parties=(
                Partie(1, "pdf", Plage(0, 10), fin_connue=False, tronquee=True),
                Partie(2, "gif", Plage(5, 5), fin_connue=False),
            ),
        ),
        isolation=EtatIsolation(NiveauIsolation.COMPLETE),
        couverture=Couverture(
            (
                TechniqueCouverte("a", EtatTechnique.APPLIQUEE, "1"),
                TechniqueCouverte("b", EtatTechnique.PARTIELLE, "1"),
                TechniqueCouverte("c", EtatTechnique.NON_APPLICABLE, "1"),
                TechniqueCouverte("d", EtatTechnique.NON_MENEE),
            ),
            (),
        ),
        observations=(),
        constats=(),
        non_menees=(
            NonMenee(RaisonNonMenee.FICHIER_TRONQUE, "b", partie=1),
            NonMenee(
                RaisonNonMenee.FICHIER_TRONQUE,
                localisation=Localisation(octets=Plage(0, 10)),
                partie=1,
            ),
            NonMenee(RaisonNonMenee.HORS_PERIMETRE, partie=2),
            NonMenee(RaisonNonMenee.HORS_V1, "d", partie=1),
            NonMenee(RaisonNonMenee.DELAI_DEPASSE),
        ),
        dependances=(),
        catalogue=VERSION,
    )
    assert resume(analyse) == [
        "format réel : pdf",
        "extension : aucune",
        "partie 1 : pdf, octets 0 à 9, tronquée ou corrompue",
        "partie 2 : gif, octets 5 à 9, fin logique non établie, hors périmètre, non analysée",
        "isolation : complète",
        "technique a, partie 1 : appliquée",
        "technique b, partie 1 : partielle",
        "technique c, partie 1 : non applicable",
        "technique d, partie 1 : hors de cette version",
        "observations : 0 ; constats : 0",
        "non menée : fichier_tronque (b, partie 1)",
        "non menée : fichier_tronque (partie 1, octets 0 à 9)",
        "non menée : delai_depasse",
        "analyse interrompue : résultats partiels, hors garantie de reproductibilité",
        f"catalogue : 0.0.1 du 2026-10-27, empreinte {'c' * 64}",
        "nom et empreinte du fichier : masqués",
    ]
    # Isolation réduite (Windows, ou système sans Landlock) : ce qui manque est nommé.
    manques = (ManqueIsolation.RESEAU, ManqueIsolation.LECTURE)
    reduite = dataclasses.replace(
        analyse, isolation=EtatIsolation(NiveauIsolation.REDUITE, manques)
    )
    assert "isolation : réduite ; manque : reseau, lecture" in resume(reduite)
    du_fichier = tuple(n for n in analyse.non_menees if n.module is None)
    vide = dataclasses.replace(analyse, couverture=Couverture((), ()), non_menees=du_fichier)
    assert "techniques : aucune dans cette version" in resume(vide)


# Catalogue (T15, ADR-0086, NF-07)


def test_regles_du_catalogue_livre(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--regles"]) == 0
    livre = catalogue.charger(manifestes.decouvrir()).version
    assert capsys.readouterr().out == (
        f"catalogue : {livre.version} du {livre.date.isoformat()}, empreinte {livre.empreinte}\n"
        "Aucune règle dans cette version du catalogue.\n"
    )


def test_regles_d_un_catalogue_fourni(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    livre = Manifeste("exif", "1.2.0", ("pdf",), ("F-10",), (), "exif", (Direction.ORIGINE_IA,))
    monkeypatch.setattr(manifestes, "decouvrir", lambda: (livre,))
    regles = toml_regles(
        regle_dict(
            "R-EXIF-001",
            "exif",
            titre="Logiciel générateur déclaré",
            categorie="indice",
            direction="origine_ia",
            fondement="declaration",
            niveau="faible",
            **moteur({"observation": "logiciel", "parmi": ["Générateur"]}),
        )
    )
    dossier = ecrire_catalogue(tmp_path / "catalogue", {"exif": regles})
    assert main(["--catalogue", str(dossier), "--regles"]) == 0
    lignes = capsys.readouterr().out.splitlines()
    assert lignes[0].startswith("catalogue : 1.2.3 du 2026-10-20, fourni par l'utilisateur")
    assert lignes[1:] == ["R-EXIF-001 version 1 (exif) : Logiciel générateur déclaré"]

    document = tmp_path / "document.pdf"
    document.write_bytes(PDF)
    assert main(["--catalogue", str(dossier), str(document)]) == 0
    assert ", fourni par l'utilisateur, empreinte" in capsys.readouterr().out


def test_catalogue_invalide(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--catalogue", str(tmp_path / "absent"), "f.pdf"])
    assert sortie.value.code == 2
    assert "catalogue invalide : catalogue : dossier introuvable" in capsys.readouterr().err
