"""Aucune trace sur le poste (ES-15, ADR-0030) : une analyse n'écrit rien hors de sa sortie.

La commande est lancée avec des dossiers personnels, temporaires, de cache et de travail
neufs ; après l'analyse, ils doivent être restés vides, et le dossier du fichier inchangé.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from echantillons import PDF

pytestmark = pytest.mark.exigence("ES-15", "NF-04")

_VARIABLES = (
    "HOME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "TMPDIR",
    "TEMP",
    "TMP",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
)


def contenu(dossier: Path) -> set[str]:
    """Fichiers et dossiers créés, hors mesures de coverage quand les tests en prennent."""
    return {
        str(chemin.relative_to(dossier))
        for chemin in dossier.rglob("*")
        if not chemin.name.startswith(".coverage")
    }


def test_analyse_sans_trace(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    fichier = source / "rapport.pdf"
    fichier.write_bytes(PDF)
    avant = os.stat(fichier)
    surveilles = {nom: tmp_path / nom.lower() for nom in _VARIABLES}
    travail = tmp_path / "travail"
    for dossier in (*surveilles.values(), travail):
        dossier.mkdir(exist_ok=True)
    environnement = {**os.environ, **{nom: str(d) for nom, d in surveilles.items()}}

    termine = subprocess.run(
        [sys.executable, "-m", "voight_kampff", str(fichier)],
        cwd=travail,
        env=environnement,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )

    assert termine.returncode == 0, termine.stderr
    assert "pdf" in termine.stdout
    for dossier in (*surveilles.values(), travail):
        assert contenu(dossier) == set(), dossier.name
    assert contenu(source) == {"rapport.pdf"}
    apres = os.stat(fichier)
    assert (apres.st_size, apres.st_mtime_ns) == (avant.st_size, avant.st_mtime_ns)
