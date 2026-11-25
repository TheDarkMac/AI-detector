"""Conservation des données affichée à l'utilisateur (T92, NF-05, ADR-0264 à ADR-0266).

À la fin d'une analyse ou d'une comparaison, un bloc dit où est gardé ce que la commande a lu
ou écrit, et jusqu'à quand ; ``vk --conservation`` affiche l'énoncé complet ; le rapport HTML
porte une rubrique sans chemin.
"""

import io
import re
import sys
from pathlib import Path

import pytest
from conftest import construire_rapport
from echantillons import PDF
from test_conservation import autorite  # noqa: F401 - autorité d'horodatage locale
from test_rapport import analyse_de

from voight_kampff._conservation import horodatage, journal
from voight_kampff.analyse import Analyse, analyser_texte
from voight_kampff.cli import construire_analyseur, main
from voight_kampff.rapport._presentation import textes
from voight_kampff.rapport.export import exporter_html

pytestmark = pytest.mark.exigence("NF-05")

_TITRE = "Conservation des données (énoncé complet : vk --conservation) :"


def _bloc(sortie: str) -> list[str]:
    """Lignes du bloc de conservation, la dernière chose écrite sur la sortie."""
    lignes = sortie.splitlines()
    return lignes[lignes.index(_TITRE) :]


@pytest.fixture
def analyse() -> Analyse:
    return analyse_de(construire_rapport())


@pytest.fixture
def document(tmp_path: Path) -> Path:
    chemin = tmp_path / "SOURCE.pdf"
    chemin.write_bytes(PDF)
    return chemin


def _enonce() -> list[str]:
    paragraphes: list[str] = textes()["conservation"]["donnees"]["enonce"]
    return paragraphes


def test_enonce_complet(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--conservation"]) == 0
    assert capsys.readouterr().out.splitlines() == _enonce()


@pytest.mark.parametrize(
    "autres",
    [["x.pdf"], ["--texte"], ["--modules"], ["--rapport", "r"], ["--reveler", "empreinte"]],
    ids=["fichier", "texte", "modules", "rapport", "reveler"],
)
def test_enonce_s_emploie_seul(autres: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as sortie:
        main(["--conservation", *autres])
    assert sortie.value.code == 2
    assert "--conservation s'emploie seule" in capsys.readouterr().err


def test_enonce_couvre_chaque_option_qui_ecrit_ou_envoie() -> None:
    """Chaque option qui lit une saisie, écrit un fichier ou envoie une requête y est nommée."""
    enonce = " ".join(_enonce())
    for option in ("--texte", "--rapport", "--horodater", "--journal", "--comparer", "--reveler"):
        assert option in enonce
    options = {o for action in construire_analyseur()._actions for o in action.option_strings}
    assert {"--texte", "--rapport", "--horodater", "--journal"} <= options
    # Ce qui échappe à l'outil est nommé, sans promesse (ADR-0266).
    assert "Hors de l'outil" in enonce
    assert "historique de votre shell" in enonce
    assert "selon sa propre politique, que l'outil ne connaît pas" in enonce
    # Les droits de lecture ne sont annoncés que là où l'outil les fixe (0o600, ADR-0092).
    assert enonce.count("sous Linux et macOS, lisible") == 2


def test_bloc_sans_rapport(document: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(document)]) == 0
    assert _bloc(capsys.readouterr().out) == [
        _TITRE,
        "  fichier analysé : lu là où il se trouve, ni copié ni modifié ; rien n'en est gardé",
        "  rapports : aucun écrit",
    ]


def test_bloc_avec_rapports_et_journal(
    tmp_path: Path, document: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sortie, tenu = tmp_path / "rapports", tmp_path / "journal.jsonl"
    absent = tmp_path / "absent.pdf"
    commande = ["--rapport", str(sortie), "--journal", str(tenu), str(document), str(absent)]
    assert main(commande) == 1  # le second fichier est refusé
    bloc = _bloc(capsys.readouterr().out)
    assert bloc == [
        _TITRE,
        "  fichiers analysés : lus là où ils se trouvent, ni copiés ni modifiés ; rien n'en est "
        "gardé",
        f"  rapports : dans {sortie}, gardés jusqu'à ce que vous les supprimiez",
        f"  journal de conservation : {tenu}, gardé jusqu'à ce que vous le supprimiez",
    ]
    assert "SOURCE" not in "\n".join(bloc)  # aucun nom de fichier analysé


def test_bloc_rapports_jamais_ecrits(
    tmp_path: Path, document: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vide = tmp_path / "vide.pdf"
    vide.write_bytes(b"")
    assert main(["--rapport", str(tmp_path / "rapports"), str(vide)]) == 1
    assert _bloc(capsys.readouterr().out)[2] == "  rapports : aucun écrit"


def test_bloc_avec_horodatage(
    tmp_path: Path,
    document: Path,
    autorite: str,  # noqa: F811 - fixture importée
    capsys: pytest.CaptureFixture[str],
) -> None:
    sortie = tmp_path / "rapports"
    assert main(["--rapport", str(sortie), "--horodater", autorite, str(document)]) == 0
    assert _bloc(capsys.readouterr().out)[2:] == [
        f"  rapports et jetons d'horodatage : dans {sortie}, gardés jusqu'à ce que vous les "
        "supprimiez",
        "  autorité d'horodatage : a reçu l'empreinte de chaque rapport et la garde selon sa "
        "propre politique, que l'outil ne connaît pas",
    ]


def test_bloc_horodatage_non_obtenu(
    tmp_path: Path,
    document: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une demande partie sans réponse a pu être reçue : l'autorité reste nommée."""

    def refuser(url: str, empreinte: bytes) -> object:
        raise horodatage.HorodatageImpossible("autorité injoignable")

    monkeypatch.setattr(horodatage, "horodater", refuser)
    sortie = tmp_path / "rapports"
    commande = ["--rapport", str(sortie), "--horodater", "http://127.0.0.1:9/", str(document)]
    assert main(commande) == 1
    bloc = _bloc(capsys.readouterr().out)
    assert bloc[2] == f"  rapports : dans {sortie}, gardés jusqu'à ce que vous les supprimiez"
    assert bloc[3].startswith("  autorité d'horodatage : a reçu l'empreinte")


def test_bloc_du_texte_colle_et_de_la_comparaison(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    sortie, tenu = tmp_path / "rapports", tmp_path / "journal.jsonl"
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO("Un texte collé.".encode())))
    assert main(["--rapport", str(sortie), "--texte"]) == 0
    assert _bloc(capsys.readouterr().out)[1] == (
        "  texte collé : lu en mémoire seulement ; rien n'en est gardé"
    )
    rapport = str(sortie / "1.json")
    assert main(["--journal", str(tenu), "--comparer", rapport, rapport]) == 0
    assert _bloc(capsys.readouterr().out) == [
        _TITRE,
        "  rapports comparés : lus là où ils se trouvent, ni copiés ni modifiés",
        f"  journal de conservation : {tenu}, gardé jusqu'à ce que vous le supprimiez",
    ]


def test_bloc_apres_un_arret_du_journal(
    tmp_path: Path,
    document: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La commande arrêtée par une entrée non écrite dit encore ce qu'elle a laissé."""

    def refuser(*args: object, **champs: object) -> int:
        raise journal.JournalInvalide("disque plein")

    tenu = tmp_path / "journal.jsonl"
    monkeypatch.setattr(journal.Journal, "soumission", refuser)
    assert main(["--journal", str(tenu), str(document)]) == 1
    assert _bloc(capsys.readouterr().out)[3] == (
        f"  journal de conservation : {tenu}, gardé jusqu'à ce que vous le supprimiez"
    )
    monkeypatch.setattr(journal.Journal, "consultation", refuser)
    assert main(["--rapport", str(tmp_path / "r"), str(document)]) == 0
    capsys.readouterr()
    rapport = str(tmp_path / "r" / "1.json")
    assert main(["--journal", str(tenu), "--comparer", rapport, rapport]) == 2
    assert _bloc(capsys.readouterr().out)[1].startswith("  rapports comparés : ")


def test_bloc_neutralise(
    tmp_path: Path, document: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Un chemin choisi par l'utilisateur est affiché neutralisé, comme tout le terminal (ES-12)."""
    sortie = tmp_path / "rapports\u202e"
    assert main(["--rapport", str(sortie), str(document)]) == 0
    ligne = _bloc(capsys.readouterr().out)[2]
    assert "\u202e" not in ligne
    assert ligne.startswith(f"  rapports : dans {tmp_path}")


def test_rubrique_du_rapport(analyse: Analyse) -> None:
    """Rubrique fixe, avant le glossaire, sans aucun chemin (ES-14, ADR-0265)."""
    document = exporter_html(analyse)
    rubrique = re.search(r'<section id="conservation".*?</section>', document)
    assert rubrique is not None
    paragraphes = re.findall(r"<p>(.*?)</p>", rubrique.group(0))
    assert len(paragraphes) == 4
    assert paragraphes[0].startswith("L&#x27;outil n&#x27;a rien gardé du fichier analysé")
    assert paragraphes[-1] == "Énoncé complet : vk --conservation."
    assert "/" not in rubrique.group(0).replace("</", "")
    assert document.index('id="conservation"') < document.index('id="glossaire"')
    assert '<a href="#conservation">Conservation des données</a>' in document


def test_rubrique_du_texte_colle() -> None:
    document = exporter_html(analyser_texte("Un texte collé.".encode()))
    assert "L&#x27;outil n&#x27;a rien gardé du texte collé" in document
    assert "rien gardé du fichier analysé" not in document
