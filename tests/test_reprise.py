"""Tests de l'évaluation en parallèle et du journal de reprise du banc (T101, ADR-0277).

Comme ``test_banc.py``, avec une analyse factice : l'ordre des résultats, l'accord avec
l'évaluation sur un seul fil, l'arrêt sur un fichier modifié, le journal (création, reprise,
dernière ligne coupée, journal d'une autre évaluation) et la commande.
"""

import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from catalogues import VERSION
from test_banc import (
    AUTHENTICITE,
    IA_FAIBLE,
    IA_FORT,
    NEUTRE,
    analyse_alpha,
    analyser_factice,
    ecrire_corpus,
    sans_reseau,  # noqa: F401 (fixture)
)

from banc import cli, evaluation, reprise, reseau
from banc import corpus as corpora
from banc.corpus import Partie
from banc.evaluation import ConstatRetenu, EtatFichier, ResultatFichier
from voight_kampff import Analyse, AnalyseRefusee, MotifRefus
from voight_kampff.rapport.modele import EtatTechnique

pytestmark = pytest.mark.exigence("NF-09")

FICHIERS = {f"f{rang:02}.txt": str(rang).encode() for rang in range(12)}


def _analyse(chemin: Path) -> Analyse:
    """Analyse factice : un refus, un constat ou rien, selon le fichier."""
    rang = int(chemin.stem[1:])
    if rang % 4 == 1:
        raise AnalyseRefusee(MotifRefus.VIDE)
    return analyse_alpha(EtatTechnique.APPLIQUEE, EtatTechnique.APPLIQUEE, constat=rang % 4 == 2)


# Exécution en parallèle


@pytest.mark.parametrize("processus", [1, 2, 5, 32])
def test_resultats_dans_l_ordre_du_manifeste(tmp_path: Path, processus: int) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    verrou, en_cours, maximum = threading.Lock(), [0], [0]

    def analyser(chemin: Path) -> Analyse:
        with verrou:
            en_cours[0] += 1
            maximum[0] = max(maximum[0], en_cours[0])
        try:
            # Les derniers fichiers finissent les premiers : l'ordre ne vient pas de la fin.
            time.sleep(0.002 * (12 - int(chemin.stem[1:])))
            return _analyse(chemin)
        finally:
            with verrou:
                en_cours[0] -= 1

    notes: list[str] = []
    resultats = evaluation.analyser_corpus(
        corpus,
        Partie.EVALUATION,
        analyser,
        ["alpha"],
        processus=processus,
        noter=lambda r: notes.append(r.entree.chemin),
    )
    sequentiel = evaluation.analyser_corpus(corpus, Partie.EVALUATION, _analyse, ["alpha"])
    assert resultats == sequentiel
    assert [r.entree.chemin for r in resultats] == list(FICHIERS)
    assert sorted(notes) == list(FICHIERS)
    assert maximum[0] <= processus
    if processus > 1:
        assert maximum[0] > 1


def test_au_moins_un_processus(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    with pytest.raises(ValueError, match="au moins un processus"):
        evaluation.analyser_corpus(corpus, Partie.EVALUATION, _analyse, [], processus=0)


def test_fichiers_deja_analyses_non_reanalyses(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    complet = evaluation.analyser_corpus(corpus, Partie.EVALUATION, _analyse, ["alpha"])
    deja = {r.entree.chemin: r for r in complet[:5]}
    appels: list[str] = []

    def analyser(chemin: Path) -> Analyse:
        appels.append(chemin.name)
        return _analyse(chemin)

    notes: list[ResultatFichier] = []
    resultats = evaluation.analyser_corpus(
        corpus, Partie.EVALUATION, analyser, ["alpha"], processus=3, deja=deja, noter=notes.append
    )
    assert resultats == complet
    assert sorted(appels) == sorted(2 * list(FICHIERS)[5:])
    assert {r.entree.chemin for r in notes} == set(list(FICHIERS)[5:])


def test_fichier_modifie_arrete_apres_les_resultats_obtenus(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    (tmp_path / "f06.txt").write_bytes(b"autre")
    notes: list[str] = []
    with pytest.raises(corpora.CorpusInvalide, match=r"f06\.txt"):
        evaluation.analyser_corpus(
            corpus,
            Partie.EVALUATION,
            _analyse,
            ["alpha"],
            processus=4,
            noter=lambda r: notes.append(r.entree.chemin),
        )
    # Les fichiers qui précèdent ont été notés ; aucun n'est noté deux fois.
    assert {"f00.txt", "f01.txt"} <= set(notes)
    assert "f06.txt" not in notes
    assert len(notes) == len(set(notes)) < len(FICHIERS)


def test_erreurs_d_autres_fichiers_apres_les_resultats(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, dict(list(FICHIERS.items())[:3])))
    fini = threading.Event()
    appels: list[str] = []

    def analyser(chemin: Path) -> Analyse:
        appels.append(chemin.name)
        if chemin.name != "f00.txt":
            # Erreur après la fin du premier fichier, analysé en même temps.
            fini.wait(timeout=10)
            time.sleep(0.2)
            raise reseau.ReseauInterdit("socket.connect")
        if appels.count("f00.txt") == 2:
            fini.set()
        return _analyse(chemin)

    notes: list[str] = []
    with pytest.raises(reseau.ReseauInterdit):
        evaluation.analyser_corpus(
            corpus,
            Partie.EVALUATION,
            analyser,
            ["alpha"],
            processus=3,
            noter=lambda r: notes.append(r.entree.chemin),
        )
    assert notes == ["f00.txt"]


# Résultat d'un fichier, aller et retour


RESULTAT = ResultatFichier(
    corpora.Entree("a.txt", "a" * 64, corpora.Categorie.GENERE, Partie.EVALUATION, "a", None),
    {"alpha": EtatFichier.ANALYSE, "beta": EtatFichier.NON_APPLICABLE},
    (IA_FORT, IA_FAIBLE, NEUTRE, AUTHENTICITE),
    refus="vide",
    erreur="ValueError",
    interrompue=True,
    non_reproduit=("constats[0]",),
)


def test_resultat_aller_et_retour() -> None:
    document = json.loads(json.dumps(RESULTAT.vers_dict()))
    assert ResultatFichier.depuis_dict(RESULTAT.entree, document) == RESULTAT
    assert document["constats"][2] == {
        "regle": "R-ALPHA-004",
        "module": "alpha",
        "categorie": "information_neutre",
        "direction": "rien_de_particulier",
        "niveau": None,
    }
    sans = ResultatFichier(RESULTAT.entree, {})
    assert ResultatFichier.depuis_dict(sans.entree, sans.vers_dict()) == sans


@pytest.mark.parametrize(
    ("champ", "valeur", "erreur"),
    [
        ("chemin", "b.txt", ValueError),
        ("empreinte", "b" * 64, ValueError),
        ("interrompue", 1, TypeError),
        ("refus", 3, TypeError),
        ("techniques", {"alpha": "inconnu"}, ValueError),
        (
            "constats",
            [IA_FORT.vers_dict() | {"regle": 1}],
            TypeError,
        ),
        ("non_reproduit", [None], TypeError),
    ],
)
def test_resultat_illisible(champ: str, valeur: object, erreur: type[Exception]) -> None:
    document = RESULTAT.vers_dict() | {champ: valeur}
    with pytest.raises(erreur):
        ResultatFichier.depuis_dict(RESULTAT.entree, document)


def test_constat_retenu_sans_niveau() -> None:
    assert ConstatRetenu.depuis_dict(NEUTRE.vers_dict()) == NEUTRE


# Journal de reprise


def _entete(corpus: corpora.Corpus, **champs: Any) -> dict[str, Any]:
    return (
        reprise.entete(
            corpus,
            Partie.EVALUATION,
            outil="0.1.0",
            catalogue=VERSION,
            modules=["alpha"],
            desactiver=["zeta", "beta"],
        )
        | champs
    )


def test_entete(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    entete = _entete(corpus)
    assert entete == {
        "reprise": 1,
        "corpus": {"nom": "test", "version": "1.0", "empreinte": corpus.empreinte},
        "partie": "evaluation",
        "outil": {"version": "0.1.0", "code": reprise.empreinte_du_code()},
        "catalogue": {"version": VERSION.version, "empreinte": VERSION.empreinte},
        "modules": ["alpha"],
        "desactiver": ["beta", "zeta"],
    }


def _ouvrir(chemin: Path, corpus: corpora.Corpus, **champs: Any) -> reprise.Journal:
    return reprise.Journal.ouvrir(chemin, corpus, _entete(corpus, **champs))


def test_journal_cree_puis_repris(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    chemin = tmp_path / "reprise.jsonl"
    journal = _ouvrir(chemin, corpus)
    assert journal.resultats == {}
    complet = evaluation.analyser_corpus(corpus, Partie.EVALUATION, _analyse, ["alpha"])
    for resultat in complet[:4]:
        journal.noter(resultat)
    journal.fermer()
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    assert json.loads(lignes[0]) == _entete(corpus)
    assert [json.loads(ligne)["chemin"] for ligne in lignes[1:]] == list(FICHIERS)[:4]
    repris = _ouvrir(chemin, corpus)
    assert list(repris.resultats.values()) == complet[:4]
    repris.noter(complet[4])
    repris.fermer()
    assert len(_ouvrir(chemin, corpus).resultats) == 5


def test_derniere_ligne_coupee_retiree(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    chemin = tmp_path / "reprise.jsonl"
    journal = _ouvrir(chemin, corpus)
    complet = evaluation.analyser_corpus(corpus, Partie.EVALUATION, _analyse, ["alpha"])
    journal.noter(complet[0])
    journal.fermer()
    entier = chemin.read_bytes()
    with chemin.open("ab") as fichier:
        fichier.write(b'{"chemin": "f01.t')
    journal = _ouvrir(chemin, corpus)
    assert list(journal.resultats) == ["f00.txt"]
    journal.fermer()
    assert chemin.read_bytes() == entier
    # Coupé dans l'en-tête : le journal est réécrit, rien n'avait été noté.
    chemin.write_bytes(entier[:20])
    _ouvrir(chemin, corpus).fermer()
    assert chemin.read_text(encoding="utf-8").splitlines() == [
        entier.decode("utf-8").splitlines()[0]
    ]


@pytest.mark.parametrize(
    "champs",
    [
        pytest.param({"partie": "calibrage"}, id="partie"),
        pytest.param({"outil": {"version": "0.1.0", "code": "0" * 64}}, id="code"),
        pytest.param({"catalogue": {"version": "9.9.9", "empreinte": "0" * 64}}, id="catalogue"),
        pytest.param({"modules": ["beta"]}, id="modules"),
        pytest.param({"desactiver": []}, id="desactiver"),
        pytest.param({"reprise": 2}, id="format"),
    ],
)
def test_journal_d_une_autre_evaluation(tmp_path: Path, champs: dict[str, Any]) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    chemin = tmp_path / "reprise.jsonl"
    _ouvrir(chemin, corpus, **champs).fermer()
    with pytest.raises(reprise.JournalInvalide, match="journal de reprise d'une autre évaluation"):
        _ouvrir(chemin, corpus)


def _ligne(document: object) -> str:
    return json.dumps(document, ensure_ascii=False)


@pytest.mark.parametrize(
    ("lignes", "numero"),
    [
        pytest.param(["{"], 1, id="entete"),
        pytest.param(["ENTETE", "[]"], 2, id="pas-un-objet"),
        pytest.param(["ENTETE", '{"chemin": "absent.txt"}'], 2, id="chemin-inconnu"),
        pytest.param(["ENTETE", "R0", "R0"], 3, id="doublon"),
        pytest.param(["ENTETE", "CALIBRAGE"], 2, id="autre-partie"),
        pytest.param(["ENTETE", "R0", "{", "R1"], 3, id="ligne-du-milieu"),
    ],
)
def test_journal_illisible(tmp_path: Path, lignes: list[str], numero: int) -> None:
    fichiers = FICHIERS | {"c.txt": b"c"}
    manifeste = ecrire_corpus(tmp_path, fichiers, **{"c.txt": {"partie": '"calibrage"'}})
    corpus = corpora.charger(manifeste)
    complet = evaluation.analyser_corpus(corpus, Partie.EVALUATION, _analyse, ["alpha"])
    (calibrage,) = evaluation.analyser_corpus(corpus, Partie.CALIBRAGE, _analyse, ["alpha"])
    remplacements = {
        "ENTETE": _ligne(_entete(corpus)),
        "R0": _ligne(complet[0].vers_dict()),
        "R1": _ligne(complet[1].vers_dict()),
        "CALIBRAGE": _ligne(calibrage.vers_dict()),
    }
    chemin = tmp_path / "reprise.jsonl"
    texte = "\n".join(remplacements.get(ligne, ligne) for ligne in lignes) + "\n"
    chemin.write_text(texte, encoding="utf-8")
    with pytest.raises(reprise.JournalInvalide, match=rf"illisible \(ligne {numero}\)"):
        _ouvrir(chemin, corpus)


def test_journal_inutilisable(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, FICHIERS))
    with pytest.raises(reprise.JournalInvalide, match="journal de reprise inutilisable"):
        _ouvrir(tmp_path / "absent" / "reprise.jsonl", corpus)


def test_empreinte_du_code(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_bytes(b"a")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "a.pyc").write_bytes(b"x")
    premiere = reprise.empreinte_du_code(tmp_path)
    (tmp_path / "__pycache__" / "a.pyc").write_bytes(b"y")
    assert reprise.empreinte_du_code(tmp_path) == premiere
    (tmp_path / "a.py").write_bytes(b"b")
    assert reprise.empreinte_du_code(tmp_path) != premiere
    # Le chemin compte : le même contenu sous un autre nom est un autre code.
    (tmp_path / "a.py").rename(tmp_path / "b.py")
    (tmp_path / "b.py").write_bytes(b"a")
    assert reprise.empreinte_du_code(tmp_path) != premiere
    assert len(reprise.empreinte_du_code()) == 64


# Commande


@pytest.mark.usefixtures("sans_reseau")
def test_commande_en_parallele_et_reprise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifeste = ecrire_corpus(tmp_path, FICHIERS)
    journal = tmp_path / "reprise.jsonl"
    appels: list[str] = []
    coupure = [True]

    def analyser(chemin: Path) -> Analyse:
        appels.append(chemin.name)
        if chemin.name == "f07.txt" and coupure[0]:
            coupure[0] = False
            raise reseau.ReseauInterdit("socket.connect")
        return _analyse(chemin)

    monkeypatch.setattr(cli, "analyser", analyser_factice(analyser))
    options = ["--processus", "1", "--reprise", str(journal)]
    # Première passe arrêtée au huitième fichier : rien n'est écrit, le journal reste.
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r1"), *options]) == 3
    notes = len(journal.read_text(encoding="utf-8").splitlines()) - 1
    assert notes == 7
    appels.clear()
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r1"), *options]) == 1
    assert sorted(appels) == sorted(2 * list(FICHIERS)[7:])
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r2"), "--processus", "4"]) == 1
    premier, second = (
        json.loads((tmp_path / r / "evaluation.json").read_text(encoding="utf-8"))
        for r in ("r1", "r2")
    )
    assert {**premier, "date": None} == {**second, "date": None}
    capsys.readouterr()


@pytest.mark.usefixtures("sans_reseau")
def test_commande_journal_d_une_autre_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifeste = ecrire_corpus(tmp_path, FICHIERS)
    journal = tmp_path / "reprise.jsonl"
    journal.write_text('{"reprise": 1}\n', encoding="utf-8")
    monkeypatch.setattr(cli, "analyser", analyser_factice(_analyse))
    arguments = [str(manifeste), "--sortie", str(tmp_path / "r"), "--reprise", str(journal)]
    assert cli.main(arguments) == 2
    assert "journal de reprise d'une autre évaluation" in capsys.readouterr().err
    assert not (tmp_path / "r" / "evaluation.json").exists()


@pytest.mark.parametrize("valeur", ["0", "65", "deux"])
def test_commande_processus_invalide(valeur: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as fin:
        cli.main(["corpus.toml", "--sortie", "r", "--processus", valeur])
    assert fin.value.code == 2
    assert "entier de 1 à 64 attendu" in capsys.readouterr().err
