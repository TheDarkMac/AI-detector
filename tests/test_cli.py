"""Tests de la ligne de commande (T10, T12)."""

import subprocess
import sys

import pytest

from voight_kampff import __version__
from voight_kampff._orchestration import manifestes
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff.cli import main


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
