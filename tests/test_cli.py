"""Tests de la ligne de commande (T10, T12, T13, T15, T16)."""

import dataclasses
import hashlib
import json
import os
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
    CategorieIdentifiante,
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
    assert sortie.splitlines()[:10] == [
        "[1/1] format réel : jpeg",
        "  nom : [masqué : nom du fichier]",
        "  empreinte : [masqué : empreinte du fichier]",
        "  L'extension « png » ne correspond pas au format réel (jpeg) : le fichier a pu être "
        "renommé.",
        "  Le fichier est reconnu dans 2 formats : chaque partie du périmètre est analysée "
        "séparément.",
        "  La partie 2 (zip) est dans un format que l'outil reconnaît sans l'analyser.",
        f"  Les octets {len(contenu) - 2} à {len(contenu) - 1} suivent la fin logique du fichier "
        ": des données y ont pu être ajoutées ; elles ne sont pas analysées.",
        f"  partie 1 : jpeg, octets 0 à {fin_jpeg}, analysée",
        f"  partie 2 : zip, octets {fin_jpeg + 1} à {len(contenu) - 3}, "
        "non analysée : hors du périmètre de l'outil",
        "  isolation : complète",
    ]
    assert "  technique ela, partie 1 : hors de cette version" in sortie
    assert "non livrée" not in sortie  # dit une fois, avec la technique
    livre = catalogue.charger(manifestes.decouvrir()).version
    assert (
        f"  catalogue : {livre.version} du {livre.date.isoformat()}, "
        f"empreinte {livre.empreinte}\n\n"
        "Ce rapport ne délivre aucun verdict"
    ) in sortie
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
    assert sorties.out.startswith("[2/2] format réel : pdf\n  nom : [masqué : nom du fichier]\n")
    assert "  L'extension « pdf » correspond au format réel.\n" in sorties.out
    assert sorties.out.count("Ce rapport ne délivre aucun verdict") == 1
    # Aucun fichier analysé : aucun avertissement à rappeler.
    assert main([str(vide)]) == 1
    assert capsys.readouterr().out == ""


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
    assert (
        "  non menée : Technique désactivée à la demande de l'utilisateur. (exif, partie 1)\n"
    ) in sortie


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
    tronque = "Structure interrompue avant sa fin : fichier tronqué ou corrompu."
    assert resume(analyse) == [
        "format réel : pdf",
        "attention : Analyse interrompue : les résultats sont partiels et hors garantie de "
        "reproductibilité.",
        "nom : [masqué : nom du fichier]",
        "empreinte : [masqué : empreinte du fichier]",
        "Le nom du fichier n'a pas d'extension.",
        "Le fichier est reconnu dans 2 formats : chaque partie du périmètre est analysée "
        "séparément.",
        "La partie 1 (pdf) s'interrompt avant sa fin : fichier tronqué ou corrompu.",
        "La fin logique de la partie 2 (gif) n'a pas pu être établie.",
        "La partie 2 (gif) est dans un format que l'outil reconnaît sans l'analyser.",
        "partie 1 : pdf, octets 0 à 9, analysée, tronquée ou corrompue",
        "partie 2 : gif, octets 5 à 9, non analysée : hors du périmètre de l'outil, "
        "fin logique non établie",
        "isolation : complète",
        "technique a, partie 1 : appliquée",
        "technique b, partie 1 : partielle",
        "technique c, partie 1 : non applicable",
        "technique d, partie 1 : hors de cette version",
        "Aucune preuve.",
        "Aucun indice.",
        "0 information(s) neutre(s).",
        "Techniques : 1 appliquée(s), 1 partielle(s), 1 non menée(s), 1 non applicable(s).",
        "5 analyse(s) non menée(s).",
        f"non menée : {tronque} (b, partie 1)",
        f"non menée : {tronque} (partie 1, octets 0 à 9)",
        "non menée : Délai dépassé : l'analyse a été interrompue.",
        f"catalogue : 0.0.1 du 2026-10-27, empreinte {'c' * 64}",
    ]
    # Isolation réduite (Windows, ou système sans Landlock) : ce qui manque est nommé en tête.
    manques = (ManqueIsolation.RESEAU, ManqueIsolation.LECTURE)
    reduite = dataclasses.replace(
        analyse, isolation=EtatIsolation(NiveauIsolation.REDUITE, manques)
    )
    assert resume(reduite)[1] == (
        "attention : Isolation réduite : le processus qui a lu le fichier n'avait pas toutes "
        "ses restrictions (réseau non bloqué, lecture d'autres fichiers non bloquée)."
    )
    assert "isolation : réduite" in resume(reduite)
    du_fichier = tuple(n for n in analyse.non_menees if n.module is None)
    vide = dataclasses.replace(analyse, couverture=Couverture((), ()), non_menees=du_fichier)
    assert (
        "Techniques : 0 appliquée(s), 0 partielle(s), 0 non menée(s), 0 non applicable(s)."
        in resume(vide)
    )
    # Levée du masquage : le nom et l'empreinte apparaissent, et la levée est annoncée en tête.
    revele = resume(analyse, [CategorieIdentifiante.NOM_DE_FICHIER, "empreinte"])
    assert revele[1].startswith(
        "attention : Masquage levé à la demande de l'utilisateur pour : nom du fichier, "
        "empreinte du fichier."
    )
    assert "nom : sans-extension" in revele
    assert f"empreinte : {'0' * 64}" in revele


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
    sortie = capsys.readouterr().out
    assert ", fourni par l'utilisateur" in sortie
    assert "  attention : Catalogue de règles fourni par l'utilisateur" in sortie


def test_catalogue_invalide(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--catalogue", str(tmp_path / "absent"), "f.pdf"])
    assert sortie.value.code == 2
    assert "catalogue invalide : catalogue : dossier introuvable" in capsys.readouterr().err


# Rapports et masquage (T16, ADR-0092, ADR-0093)


def test_rapports_ecrits_par_rang(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    vide = tmp_path / "vide.pdf"
    vide.write_bytes(b"")
    document = tmp_path / "SOURCE.pdf"
    document.write_bytes(PDF)
    sortie = tmp_path / "rapports"
    assert main(["--rapport", str(sortie), str(vide), str(document)]) == 1
    # Le fichier refusé n'a pas de rapport ; l'autre porte son rang, jamais son nom.
    assert sorted(p.name for p in sortie.iterdir()) == ["2.html", "2.json"]
    assert f"  rapport : {sortie / '2.html'} et {sortie / '2.json'}\n" in capsys.readouterr().out
    html = (sortie / "2.html").read_text(encoding="utf-8")
    contenu = json.loads((sortie / "2.json").read_text(encoding="utf-8"))
    assert "SOURCE" not in html
    assert "nom" not in contenu["identification"]
    if os.name == "posix":  # lisibles par leur seul propriétaire
        assert {(sortie / n).stat().st_mode & 0o777 for n in ("2.html", "2.json")} == {0o600}


def test_rapports_revelent_ce_qui_est_demande(tmp_path: Path) -> None:
    document = tmp_path / "SOURCE.pdf"
    document.write_bytes(PDF)
    sortie = tmp_path / "rapports"
    assert main(["--rapport", str(sortie), "--reveler", "nom_de_fichier", str(document)]) == 0
    contenu = json.loads((sortie / "1.json").read_text(encoding="utf-8"))
    assert contenu["identification"]["nom"] == "SOURCE.pdf"
    assert "empreinte" not in contenu["identification"]
    assert contenu["masquage"]["levees"] == ["nom_de_fichier"]
    assert "SOURCE.pdf" in (sortie / "1.html").read_text(encoding="utf-8")


def test_categorie_inconnue_refusee(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--reveler", "tout", "f.pdf"])
    assert sortie.value.code == 2
    assert "invalid choice: 'tout'" in capsys.readouterr().err


def test_rapport_existant_jamais_ecrase(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sortie = tmp_path / "rapports"
    sortie.mkdir()
    (sortie / "2.json").write_text("à garder")
    document = tmp_path / "document.pdf"
    document.write_bytes(PDF)
    with pytest.raises(SystemExit) as code:
        main(["--rapport", str(sortie), str(document), str(document)])
    assert code.value.code == 2
    erreur = capsys.readouterr()
    assert "--rapport : 2.json existe déjà ; aucun rapport n'est écrasé" in erreur.err
    assert erreur.out == ""  # rien n'est analysé
    assert sorted(p.name for p in sortie.iterdir()) == ["2.json"]
    assert (sortie / "2.json").read_text() == "à garder"


def test_dossier_des_rapports_inutilisable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "fichier"
    fichier.write_text("")
    for dossier in (fichier, tmp_path / "absent" / "rapports"):
        with pytest.raises(SystemExit) as code:
            main(["--rapport", str(dossier), "f.pdf"])
        assert code.value.code == 2
        assert "--rapport : dossier inutilisable" in capsys.readouterr().err


def test_rapport_non_ecrit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    document = tmp_path / "document.pdf"
    document.write_bytes(PDF)
    sortie = tmp_path / "rapports"
    # Rapport apparu entre la vérification et l'écriture : la création exclusive échoue.
    monkeypatch.setattr("voight_kampff.cli._preparer", lambda dossier, _nombre: Path(dossier))
    sortie.mkdir()
    (sortie / "1.html").write_text("à garder")
    assert main(["--rapport", str(sortie), str(document)]) == 1
    sorties = capsys.readouterr()
    assert sorties.err.startswith("[1/1] rapport non écrit : ")
    assert "  rapport : " not in sorties.out
    assert (sortie / "1.html").read_text() == "à garder"


def test_sortie_du_terminal_neutralisee(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Un nom qui inverse l'affichage (U+202E) : montré, jamais actif (ES-12, M-21). Un caractère
    # de contrôle (ESC) est vérifié par test_rapport.py : Windows l'interdit dans un nom.
    document = tmp_path / "doc\u202efdp.pdf"
    document.write_bytes(PDF)
    assert main(["--reveler", "nom_de_fichier", str(document)]) == 0
    sortie = capsys.readouterr().out
    assert "  nom : doc⟨U+202E⟩fdp.pdf\n" in sortie
    assert "\u202e" not in sortie
