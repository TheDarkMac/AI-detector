"""Diagnostic temporaire de T30 : arrêt du processus de travail sous macOS (à retirer)."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from voight_kampff._orchestration import manifestes, travail


@pytest.mark.skipif(sys.platform != "darwin", reason="diagnostic propre à macOS")
def test_diagnostic_arret_sous_macos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    erreurs = tmp_path / "stderr.txt"
    sortie = erreurs.open("wb")
    lances: list[Any] = []
    origine = subprocess.Popen

    def popen(commande: list[str], **options: Any) -> Any:
        options["stderr"] = sortie
        commande = [commande[0], "-X", "faulthandler", *commande[1:]]
        processus = origine(commande, **options)
        lances.append(processus)
        return processus

    monkeypatch.setattr(travail.subprocess, "Popen", popen)
    chemin = tmp_path / "photo.jpg"
    chemin.write_bytes((Path(__file__).parent / "donnees/metadonnees/photo.jpg").read_bytes())
    for desactives in ((), ("c2pa",)):
        descripteur = os.open(chemin, os.O_RDONLY)
        try:
            resultat = travail.executer(descripteur, manifestes.decouvrir(), desactives)
        finally:
            os.close(descripteur)
        print("DESACTIVES", desactives, "CODE", lances[-1].returncode)
        print("NON MENEES", [(n.raison.value, n.module) for n in resultat.non_menees])
    sortie.close()
    print("STDERR", erreurs.read_text(errors="replace")[-6000:])
    pytest.fail("diagnostic : voir la sortie")
