"""Tests du banc d'évaluation (T17, ADR-0099 à ADR-0105).

Les mesures sont vérifiées sur des résultats construits à la main ; l'analyse d'un corpus et la
commande, avec une analyse factice ; le banc complet, sur le corpus d'essai, dans un espace de
noms réseau vide quand le système le permet (ES-11).
"""

import contextlib
import dataclasses
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from catalogues import VERSION, regle

from banc import cli, evaluation, reseau, sortie
from banc import corpus as corpora
from banc.corpus import Categorie as C
from banc.corpus import Entree, Origine, Partie
from banc.evaluation import ConstatRetenu, EtatFichier, ResultatFichier, mesurer
from banc.mesures import Taux
from voight_kampff import Analyse, AnalyseRefusee, MotifRefus
from voight_kampff.rapport.modele import (
    Categorie,
    Constat,
    Couverture,
    Direction,
    EtatIsolation,
    EtatTechnique,
    Fondement,
    Graduation,
    Identification,
    Niveau,
    NiveauIsolation,
    NonMenee,
    Observation,
    Phrase,
    Plage,
    RaisonNonMenee,
    ReferenceRegle,
    TechniqueCouverte,
)
from voight_kampff.rapport.modele import Partie as PartieFichier

pytestmark = pytest.mark.exigence("NF-09")

RACINE = Path(__file__).resolve().parent.parent
ESSAI = RACINE / "banc" / "essai" / "corpus.toml"
PROVENANCE = 'provenance = { source = "Test", licence = "CC0-1.0", date = "2026-10-28" }'


# Mesures (A-54)


def borne(taux: Taux) -> float:
    valeur = taux.borne_superieure
    assert valeur is not None
    return valeur


def test_taux_et_intervalle_de_wilson() -> None:
    assert borne(Taux(0, 381)) == pytest.approx(0.009982, abs=1e-6)
    # Effectifs minimaux qu'impose la borne supérieure (ADR-0101) : 381 pour « fort », 73 pour
    # « modéré », sans aucun faux positif.
    assert borne(Taux(0, 381)) <= 0.01 < borne(Taux(0, 380))
    assert borne(Taux(0, 73)) <= 0.05 < borne(Taux(0, 72))
    assert Taux(3, 1500).vers_dict()["intervalle"] == [
        pytest.approx(0.00068, abs=1e-5),
        pytest.approx(0.00586, abs=1e-5),
    ]
    assert Taux(0, 10).vers_dict()["intervalle"] == [0.0, pytest.approx(0.2775, abs=1e-4)]
    assert Taux(10, 10).vers_dict()["intervalle"] == [pytest.approx(0.7225, abs=1e-4), 1.0]
    assert Taux(2, 4).valeur == 0.5
    assert Taux(2, 4).mesure


def test_taux_sans_effectif() -> None:
    taux = Taux(0, 0)
    assert not taux.mesure
    assert taux.valeur is None
    assert taux.intervalle is None
    assert taux.borne_superieure is None
    assert taux.vers_dict() == {"nombre": 0, "effectif": 0, "valeur": None, "intervalle": None}


@pytest.mark.parametrize(("nombre", "effectif"), [(-1, 3), (4, 3)])
def test_taux_incoherent_refuse(nombre: int, effectif: int) -> None:
    with pytest.raises(ValueError, match="nombre"):
        Taux(nombre, effectif)


# Corpus (ADR-0103, ES-22)


@pytest.mark.exigence("ES-22")
def test_corpus_d_essai() -> None:
    corpus = corpora.charger(ESSAI)
    assert (corpus.nom, corpus.version, corpus.nature) == ("essai", "0.1.0", corpora.Nature.ESSAI)
    assert {e.categorie for e in corpus.entrees} == set(C)
    assert corpus.partie(Partie.CALIBRAGE) == ()
    assert len(corpus.partie(Partie.EVALUATION)) == len(corpus.entrees)
    for entree in corpus.entrees:
        assert corpus.verifier(entree).is_file()


def ecrire_corpus(dossier: Path, fichiers: dict[str, bytes], **champs: dict[str, str]) -> Path:
    """Corpus d'authentiques dans ``dossier`` ; ``champs`` remplace des champs d'un fichier."""
    lignes = [
        "format = 1",
        'nom = "test"',
        'version = "1.0"',
        'date = "2026-10-28"',
        'nature = "reference"',
        'description = "Corpus de test."',
    ]
    for chemin, octets in fichiers.items():
        (dossier / chemin).parent.mkdir(parents=True, exist_ok=True)
        (dossier / chemin).write_bytes(octets)
        entree = {
            "chemin": f'"{chemin}"',
            "empreinte": f'"{hashlib.sha256(octets).hexdigest()}"',
            "categorie": '"authentique"',
            "partie": '"evaluation"',
            "groupe": f'"{chemin.replace("/", "-").replace(".", "-").lower()}"',
            "origine": '"authentique"',
        } | champs.get(chemin, {})
        lignes += ["", "[[fichiers]]", *(f"{c} = {v}" for c, v in entree.items() if v), PROVENANCE]
    manifeste = dossier / "corpus.toml"
    manifeste.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return manifeste


@pytest.mark.exigence("ES-22")
@pytest.mark.parametrize(
    ("champs", "attendu"),
    [
        pytest.param({"categorie": '"genere"'}, "non conforme", id="genere-authentique"),
        pytest.param(
            {"categorie": '"genere"', "origine": '"ia"'}, "provenance", id="ia-sans-generateur"
        ),
        pytest.param(
            {"categorie": '"transforme"'}, "non conforme", id="transforme-sans-transformation"
        ),
        pytest.param({"transformation": '"capture"'}, "non conforme", id="transformation-hors"),
        pytest.param({"origine": ""}, "non conforme", id="sans-origine"),
        pytest.param({"chemin": '"../a.txt"'}, "chemin", id="chemin-remontant"),
        pytest.param({"empreinte": '"ABC"'}, "empreinte", id="empreinte-invalide"),
        pytest.param({"partie": '"test"'}, "partie", id="partie-inconnue"),
    ],
)
def test_entree_non_conforme(tmp_path: Path, champs: dict[str, str], attendu: str) -> None:
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a"}, **{"a.txt": champs})
    with pytest.raises(corpora.CorpusInvalide, match=attendu):
        corpora.charger(manifeste)


def test_malforme_sans_origine_admis(tmp_path: Path) -> None:
    champs = {"categorie": '"malforme"', "origine": ""}
    manifeste = ecrire_corpus(tmp_path, {"a.bin": b"\x00"}, **{"a.bin": champs})
    (entree,) = corpora.charger(manifeste).entrees
    assert entree.origine is None


@pytest.mark.parametrize(
    ("remplacer", "attendu"),
    [
        pytest.param(("format = 1", "format = 2"), "non conforme : format", id="format"),
        pytest.param(('date = "2026-10-28"', 'date = "2026-02-30"'), "date", id="date-impossible"),
        pytest.param(('2026-10-28" }', '2026-13-01" }'), "provenance", id="provenance-date"),
        pytest.param(("format = 1", "format = "), "illisible", id="toml-invalide"),
        pytest.param(('nom = "test"', 'nom = "Test"'), "nom", id="nom"),
    ],
)
def test_manifeste_non_conforme(tmp_path: Path, remplacer: tuple[str, str], attendu: str) -> None:
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a"})
    manifeste.write_text(manifeste.read_text(encoding="utf-8").replace(*remplacer, 1))
    with pytest.raises(corpora.CorpusInvalide, match=attendu):
        corpora.charger(manifeste)


def test_manifeste_illisible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(corpora.CorpusInvalide, match="illisible"):
        corpora.charger(tmp_path / "absent.toml")
    (tmp_path / "latin1.toml").write_bytes(b'nom = "\xe9"\n')
    with pytest.raises(corpora.CorpusInvalide, match="illisible"):
        corpora.charger(tmp_path / "latin1.toml")
    monkeypatch.setattr(corpora, "TAILLE_MAX_MANIFESTE", 10)
    with pytest.raises(corpora.CorpusInvalide, match="trop volumineux"):
        corpora.charger(ecrire_corpus(tmp_path, {"a.txt": b"a"}))


def test_doublons_refuses(tmp_path: Path) -> None:
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a", "b.txt": b"a"})
    with pytest.raises(corpora.CorpusInvalide, match="même contenu"):
        corpora.charger(manifeste)
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a", "A.txt": b"b"})
    with pytest.raises(corpora.CorpusInvalide, match="chemin en double"):
        corpora.charger(manifeste)


def test_groupe_dans_une_seule_partie(tmp_path: Path) -> None:
    """Un original et sa version transformée ne se partagent pas entre les parties (A-12)."""
    champs = {
        "a.txt": {"groupe": '"g"'},
        "b.txt": {"groupe": '"g"', "partie": '"calibrage"'},
    }
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a", "b.txt": b"b"}, **champs)
    with pytest.raises(corpora.CorpusInvalide, match="groupe g : dans les deux parties"):
        corpora.charger(manifeste)
    champs["b.txt"]["partie"] = '"evaluation"'
    corpus = corpora.charger(ecrire_corpus(tmp_path, {"a.txt": b"a", "b.txt": b"b"}, **champs))
    assert len(corpus.partie(Partie.EVALUATION)) == 2


@pytest.mark.exigence("ES-22")
def test_fichier_absent_ou_modifie(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, {"a.txt": b"a", "b.txt": b"b"}))
    (tmp_path / "a.txt").write_bytes(b"modifie")
    (tmp_path / "b.txt").unlink()
    a, b = corpus.entrees
    with pytest.raises(corpora.CorpusInvalide, match="empreinte différente"):
        corpus.verifier(a)
    with pytest.raises(corpora.CorpusInvalide, match="illisible"):
        corpus.verifier(b)


@pytest.mark.skipif(sys.platform == "win32", reason="lien symbolique : droits requis sous Windows")
def test_lien_hors_du_corpus(tmp_path: Path) -> None:
    (tmp_path / "corpus").mkdir()
    corpus = corpora.charger(ecrire_corpus(tmp_path / "corpus", {"a.txt": b"a"}))
    (tmp_path / "dehors.txt").write_bytes(b"a")
    (tmp_path / "corpus" / "a.txt").unlink()
    (tmp_path / "corpus" / "a.txt").symlink_to(tmp_path / "dehors.txt")
    with pytest.raises(corpora.CorpusInvalide, match="hors du dossier"):
        corpus.verifier(corpus.entrees[0])


# Réseau (ES-11, ADR-0100)

DEV = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets
    lo:       0       0    0    0    0     0          0         0        0       0
"""


@pytest.mark.exigence("ES-11")
def test_interfaces_lues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    source = tmp_path / "dev"
    source.write_text(DEV, encoding="ascii")
    assert reseau.verifier_absence(source) == ("lo",)
    source.write_text(DEV + "  eth0: 1 2 3\n", encoding="ascii")
    assert reseau.interfaces(source) == ("lo", "eth0")
    with pytest.raises(reseau.ReseauPresent, match=r"\(eth0\).*unshare -rn"):
        reseau.verifier_absence(source)
    with pytest.raises(reseau.ReseauPresent, match="illisible"):
        reseau.interfaces(tmp_path / "absent")


@pytest.mark.exigence("ES-11")
def test_banc_limite_a_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(reseau.ReseauPresent, match="Linux"):
        reseau.verifier_absence()


@pytest.mark.exigence("ES-11")
def test_crochet_refuse_et_note() -> None:
    with reseau.surveiller() as tentatives:
        with pytest.raises(reseau.ReseauInterdit, match=r"socket\.__new__"):
            socket.socket()
        with pytest.raises(reseau.ReseauInterdit, match="getaddrinfo"):
            socket.getaddrinfo("localhost", 80)
    assert tentatives == ["socket.__new__", "socket.getaddrinfo"]
    # Hors du bloc, le crochet reste installé mais n'agit plus ; un nouveau bloc repart de zéro.
    socket.socket().close()
    with reseau.surveiller() as autres:
        pass
    assert autres == []


# Mesures d'une partie (§8, ADR-0018, ADR-0104)


def entree(
    chemin: str, categorie: C, origine: Origine | None, partie: Partie = Partie.EVALUATION
) -> Entree:
    return Entree(chemin, "0" * 64, categorie, partie, chemin, origine)


def resultat(
    chemin: str,
    categorie: C,
    origine: Origine | None,
    *constats: ConstatRetenu,
    etat: EtatFichier = EtatFichier.ANALYSE,
    **champs: Any,
) -> ResultatFichier:
    return ResultatFichier(entree(chemin, categorie, origine), {"alpha": etat}, constats, **champs)


IA_FORT = ConstatRetenu("R-ALPHA-001", "alpha", Categorie.INDICE, Direction.ORIGINE_IA, Niveau.FORT)
IA_FAIBLE = ConstatRetenu(
    "R-ALPHA-002", "alpha", Categorie.INDICE, Direction.ORIGINE_IA, Niveau.FAIBLE
)
RETOUCHE = ConstatRetenu("R-ALPHA-003", "alpha", Categorie.PREUVE, Direction.RETOUCHE)
NEUTRE = ConstatRetenu(
    "R-ALPHA-004", "alpha", Categorie.INFORMATION_NEUTRE, Direction.RIEN_DE_PARTICULIER
)
AUTHENTICITE = ConstatRetenu(
    "R-ALPHA-005", "alpha", Categorie.INDICE, Direction.AUTHENTICITE, Niveau.FAIBLE
)

REGLES = (
    regle(
        "R-ALPHA-001",
        categorie="indice",
        direction="origine_ia",
        fondement="mesure",
        niveau="fort",
        evaluation={
            "taux_faux_positifs": 0.0,
            "effectif": 400,
            "borne_superieure": 0.0095,
            "corpus": "1",
            "date": "2026-10-01",
        },
    ),
    regle("R-ALPHA-002", categorie="indice", direction="origine_ia", niveau="faible"),
    regle(
        "R-ALPHA-003",
        categorie="preuve",
        direction="retouche",
        fondement="verification_deterministe",
    ),
    regle("R-ALPHA-004"),
    regle("R-ALPHA-005", categorie="indice", direction="authenticite", niveau="faible"),
)

RESULTATS = [
    resultat("a1", C.AUTHENTIQUE, Origine.AUTHENTIQUE),
    resultat("a2", C.AUTHENTIQUE, Origine.AUTHENTIQUE, IA_FAIBLE, NEUTRE),
    resultat("a3", C.AUTHENTIQUE, Origine.AUTHENTIQUE, IA_FORT),
    resultat("a4", C.AUTHENTIQUE, Origine.AUTHENTIQUE, etat=EtatFichier.NON_APPLICABLE),
    resultat("a5", C.AUTHENTIQUE, Origine.AUTHENTIQUE, etat=EtatFichier.NON_ANALYSABLE),
    resultat("g1", C.GENERE, Origine.IA, IA_FORT),
    resultat("g2", C.GENERE, Origine.IA, RETOUCHE, AUTHENTICITE),
    resultat("g3", C.GENERE, Origine.IA, NEUTRE),
    resultat("r1", C.RETOUCHE, Origine.RETOUCHE, RETOUCHE),
    resultat("t1", C.TRANSFORME, Origine.AUTHENTIQUE, RETOUCHE),
    resultat("t2", C.TRANSFORME, Origine.IA),
    resultat("m1", C.MALFORME, None, etat=EtatFichier.NON_ANALYSABLE, refus="vide"),
    resultat("m2", C.MALFORME, Origine.AUTHENTIQUE, etat=EtatFichier.NON_ANALYSABLE, erreur="X"),
]


def par_categorie(mesures: evaluation.Evaluation) -> dict[C, evaluation.MesureTechnique]:
    return {m.categorie: m for m in mesures.techniques if m.module == "alpha"}


def test_taux_par_technique_et_categorie() -> None:
    mesures = par_categorie(mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES))
    authentiques = mesures[C.AUTHENTIQUE]
    assert (authentiques.effectif, authentiques.non_applicables) == (5, 1)
    assert authentiques.non_analysables == Taux(1, 4)
    # a2 : indice faible vers l'IA, compté aussi par technique ; a3 : indice fort.
    assert authentiques.faux_positifs == Taux(2, 3)
    assert authentiques.faux_negatifs == Taux(0, 0)
    generes = mesures[C.GENERE]
    assert generes.faux_negatifs == Taux(2, 3)  # g2 pris pour retouché, g3 sans indice
    assert generes.confusions == 1
    assert mesures[C.RETOUCHE].faux_negatifs == Taux(0, 1)
    transformes = mesures[C.TRANSFORME]
    assert (transformes.faux_positifs, transformes.faux_negatifs) == (Taux(1, 1), Taux(1, 1))
    malformes = mesures[C.MALFORME]
    assert malformes.non_analysables == Taux(2, 2)
    assert malformes.faux_positifs == Taux(0, 0)


def test_taux_par_regle_et_ecarts() -> None:
    mesures = mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES)
    regles = {m.regle.identifiant: m for m in mesures.regles}
    assert "R-ALPHA-004" not in regles  # information neutre : aucun taux
    fort = regles["R-ALPHA-001"]
    assert (fort.faux_positifs, fort.chemins) == (Taux(1, 3), ("a3",))
    assert fort.niveau_permis is Niveau.FAIBLE
    assert fort.ecart is not None
    assert "au plus « faible »" in fort.ecart
    assert regles["R-ALPHA-002"].ecart is None  # faible : toujours permis
    # Preuve de retouche : population des authentiques non transformés ; aucun faux positif.
    assert regles["R-ALPHA-003"].faux_positifs == Taux(0, 3)
    assert regles["R-ALPHA-003"].niveau_permis is None
    # Indice d'authenticité : faux sur les générés et retouchés.
    assert regles["R-ALPHA-005"].faux_positifs == Taux(1, 4)
    assert regles["R-ALPHA-005"].chemins == ("g2",)
    assert list(mesures.ecarts) == [
        "m2 : arrêt brutal de l'analyse (X)",
        fort.ecart,
        "taux par fichier : borne supérieure de 62,4 % au-delà de la cible de 5 %",
    ]


def test_preuve_fautive() -> None:
    resultats = [resultat("a1", C.AUTHENTIQUE, Origine.AUTHENTIQUE, RETOUCHE)]
    mesures = mesurer(Partie.EVALUATION, resultats, ["alpha"], REGLES)
    (preuve,) = (m for m in mesures.regles if m.regle.identifiant == "R-ALPHA-003")
    assert preuve.ecart == "la preuve R-ALPHA-003 a des faux positifs"


def test_taux_par_fichier() -> None:
    """Seules les preuves et les indices modérés ou forts comptent (ADR-0018)."""
    mesures = mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES)
    # a1, a2 (indice faible), a3 (fort), a4, a5 ; m2 n'est pas analysé.
    assert mesures.par_fichier[C.AUTHENTIQUE] == Taux(1, 5)
    assert mesures.par_fichier[C.TRANSFORME] == Taux(1, 1)
    assert mesures.cible_atteinte is False


def test_cible_atteinte_sur_un_effectif_suffisant() -> None:
    resultats = [resultat(f"a{n}", C.AUTHENTIQUE, Origine.AUTHENTIQUE) for n in range(73)]
    mesures = mesurer(Partie.EVALUATION, resultats, ["alpha"], REGLES[1:])
    assert mesures.cible_atteinte is True
    assert mesures.ecarts == ()
    sans = mesurer(Partie.EVALUATION, resultats[:72], ["alpha"], REGLES[1:])
    assert sans.cible_atteinte is False


def test_cible_non_mesurable() -> None:
    mesures = mesurer(Partie.EVALUATION, RESULTATS[5:9], ["alpha"], ())
    assert mesures.cible_atteinte is None
    assert mesures.ecarts == ("taux par fichier non mesurable : aucun fichier authentique analysé",)


def test_calibrage_sans_ecart_sur_les_taux() -> None:
    """La partie calibrage ne fonde aucun taux publié (ADR-0016) ; un arrêt brutal, si."""
    mesures = mesurer(Partie.CALIBRAGE, RESULTATS, ["alpha"], REGLES)
    assert mesures.ecarts == ("m2 : arrêt brutal de l'analyse (X)",)


def test_regles_d_un_module_desactive_non_mesurees() -> None:
    assert mesurer(Partie.EVALUATION, RESULTATS, ["beta"], REGLES).regles == ()


def test_regle_sans_mesure() -> None:
    mesures = mesurer(Partie.EVALUATION, [], ["alpha"], REGLES)
    fort = next(m for m in mesures.regles if m.regle.identifiant == "R-ALPHA-001")
    assert fort.faux_positifs == Taux(0, 0)
    assert fort.niveau_permis is None
    assert (
        fort.ecart
        == "l'indice R-ALPHA-001 est au niveau « fort » ; la mesure permet au plus « faible »"
    )


# Analyse d'un corpus


def analyse_alpha(*etats: EtatTechnique, constat: bool = False) -> Analyse:
    """Analyse d'un PDF en deux parties ; ``alpha`` a l'état donné sur chacune."""
    parties = (
        PartieFichier(1, "pdf", Plage(0, 10), fin_connue=True),
        PartieFichier(2, "jpeg", Plage(10, 10), fin_connue=True),
    )
    raisons = {
        EtatTechnique.NON_MENEE: RaisonNonMenee.ERREUR_MODULE,
        EtatTechnique.PARTIELLE: RaisonNonMenee.FORMAT_PARTIEL,
    }
    observations: tuple[Observation, ...] = ()
    constats: tuple[Constat, ...] = ()
    if constat:
        observations = (Observation("alpha/1", "alpha", "n", 1),)
        constats = (
            Constat(
                Phrase("test.regle"),
                ("alpha/1",),
                ReferenceRegle("R-ALPHA-001", "1"),
                "alpha",
                Fondement.MESURE,
                Categorie.INDICE,
                Direction.ORIGINE_IA,
                Graduation(Niveau.FORT, evaluee=True),
            ),
        )
    return Analyse(
        identification=Identification(
            nom="a.pdf",
            format_reel="pdf",
            taille=20,
            empreinte="a" * 64,
            date_analyse=datetime(2026, 10, 28, tzinfo=UTC),
            parties=parties,
        ),
        isolation=EtatIsolation(NiveauIsolation.COMPLETE, ()),
        couverture=Couverture(
            tuple(
                TechniqueCouverte("alpha", etat, "0.1.0", partie=rang)
                for rang, etat in enumerate(etats, start=1)
            ),
            (),
        ),
        observations=observations,
        constats=constats,
        non_menees=tuple(
            NonMenee(raisons[etat], "alpha", partie=rang)
            for rang, etat in enumerate(etats, start=1)
            if etat in raisons
        ),
        dependances=(),
        catalogue=VERSION,
        regles=REGLES[:1] if constat else (),
    )


@pytest.mark.parametrize(
    ("etats", "attendu"),
    [
        ((EtatTechnique.NON_APPLICABLE, EtatTechnique.APPLIQUEE), EtatFichier.ANALYSE),
        ((EtatTechnique.PARTIELLE, EtatTechnique.NON_MENEE), EtatFichier.ANALYSE),
        ((EtatTechnique.NON_MENEE, EtatTechnique.NON_APPLICABLE), EtatFichier.NON_ANALYSABLE),
        ((EtatTechnique.NON_APPLICABLE, EtatTechnique.NON_APPLICABLE), EtatFichier.NON_APPLICABLE),
    ],
)
def test_etat_d_une_technique(etats: tuple[EtatTechnique, ...], attendu: EtatFichier) -> None:
    resultat = evaluation.depuis_analyse(
        entree("a", C.AUTHENTIQUE, Origine.AUTHENTIQUE), analyse_alpha(*etats), ["alpha", "beta"]
    )
    assert resultat.techniques == {"alpha": attendu, "beta": EtatFichier.NON_APPLICABLE}


def test_constats_retenus() -> None:
    analyse = analyse_alpha(EtatTechnique.APPLIQUEE, EtatTechnique.APPLIQUEE, constat=True)
    resultat = evaluation.depuis_analyse(entree("a", C.GENERE, Origine.IA), analyse, ["alpha"])
    assert resultat.constats == (IA_FORT,)
    assert resultat.analyse
    assert not resultat.interrompue


@pytest.mark.exigence("NF-03")
def test_analyser_corpus(tmp_path: Path) -> None:
    fichiers = {"a.txt": b"a", "b.txt": b"b", "c.txt": b"c", "d.txt": b"d"}
    corpus = corpora.charger(ecrire_corpus(tmp_path, fichiers))

    def analyser(chemin: Path) -> Analyse:
        match chemin.name:
            case "b.txt":
                raise AnalyseRefusee(MotifRefus.VIDE)
            case "c.txt":
                raise RuntimeError("contenu du fichier")
            case _:
                return analyse_alpha(EtatTechnique.APPLIQUEE, EtatTechnique.APPLIQUEE)

    a, b, c, d = evaluation.analyser_corpus(corpus, Partie.EVALUATION, analyser, ["alpha"])
    assert a.techniques == d.techniques == {"alpha": EtatFichier.ANALYSE}
    assert (b.refus, b.techniques) == ("vide", {"alpha": EtatFichier.NON_ANALYSABLE})
    # Arrêt brutal : seul le nom de l'exception est gardé, jamais son message.
    assert (c.erreur, c.analyse) == ("RuntimeError", False)
    assert evaluation.analyser_corpus(corpus, Partie.CALIBRAGE, analyser, ["alpha"]) == []


@pytest.mark.exigence("ES-11")
def test_tentative_de_reseau_arrete_l_analyse(tmp_path: Path) -> None:
    corpus = corpora.charger(ecrire_corpus(tmp_path, {"a.txt": b"a"}))

    def analyser(chemin: Path) -> Analyse:
        raise reseau.ReseauInterdit("socket.connect")

    with pytest.raises(reseau.ReseauInterdit):
        evaluation.analyser_corpus(corpus, Partie.EVALUATION, analyser, [])


# Rapport d'évaluation (ADR-0105)


def doc_de(mesures: evaluation.Evaluation, nature: str = "reference") -> dict[str, Any]:
    corpus = dataclasses.replace(
        corpora.charger(ESSAI), nature=corpora.Nature(nature), nom="test", version="2.0"
    )
    return sortie.document(
        corpus,
        mesures,
        outil="0.1.0",
        catalogue=VERSION,
        techniques={"alpha": "0.1.0"},
        interfaces=("lo",),
        date=datetime(2026, 10, 28, 4, 5, 6, tzinfo=UTC),
    )


def test_document_json() -> None:
    doc = doc_de(mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES))
    assert doc["date"] == "2026-10-28T04:05:06Z"
    assert doc["corpus"]["version"] == "2.0"
    assert doc["publiable"] is True
    assert doc["bornes"] == {"methode": "wilson", "confiance": 0.95, "fort": 0.01, "modere": 0.05}
    assert doc["fichiers"]["total"] == 13
    assert doc["fichiers"]["refus"] == {"vide": 1}
    assert doc["fichiers"]["arrets_brutaux"] == {"X": 1}
    assert doc["par_fichier"]["cible_atteinte"] is False
    assert len(doc["techniques"]) == 5
    regle_forte = doc["regles"][0]
    assert regle_forte["identifiant"] == "R-ALPHA-001"
    assert regle_forte["niveau_permis"] == "faible"
    assert regle_forte["chemins"] == ["a3"]
    json.dumps(doc, allow_nan=False)


def test_rapport_markdown() -> None:
    doc = doc_de(mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES))
    texte = sortie.markdown(doc)
    assert texte.startswith("# Évaluation du corpus test 2.0\n")
    assert "publiable" not in texte
    assert "| Authentiques | 1/5 : 20,0 % [3,6 % ; 62,4 %] |" in texte
    assert "| alpha | Malformés | 2 | 0 | 2/2 : 100,0 % [34,2 % ; 100,0 %] | — | — | 0 |" in texte
    assert "| R-ALPHA-002 v1 (alpha) | indice | origine_ia | faible, non évaluée |" in texte
    assert (
        "| R-ALPHA-003 v1 (alpha) | preuve | retouche | — | 0/3 : 0,0 % [0,0 % ; 56,1 %] | — |"
        in texte
    )
    assert "- m2 : arrêt brutal de l'analyse (X)" in texte
    assert "Techniques : alpha 0.1.0" in texte


def test_rapport_non_publiable() -> None:
    vide = mesurer(Partie.EVALUATION, [], [], ())
    essai = sortie.markdown(doc_de(vide, "essai"))
    assert "**Aucun taux de ce rapport n'est publiable** : corpus d'essai" in essai
    calibrage = doc_de(mesurer(Partie.CALIBRAGE, [], [], ()))
    assert calibrage["publiable"] is False
    texte = sortie.markdown(calibrage | {"versions": calibrage["versions"] | {"techniques": {}}})
    assert "partie calibrage, qui sert à régler les seuils" in texte
    assert "Aucune technique livrée dans cette version de l'outil." in texte
    assert "Aucune règle de preuve ou d'indice dans ce catalogue." in texte
    assert "Techniques : aucune technique livrée" in texte
    assert "\n## Écarts\n\nAucun.\n" in texte


def test_ecriture_sans_ecraser(tmp_path: Path) -> None:
    dossier = sortie.preparer(tmp_path / "rapport")
    doc = doc_de(mesurer(Partie.EVALUATION, RESULTATS, ["alpha"], REGLES))
    sortie.ecrire(dossier, doc)
    assert json.loads((dossier / "evaluation.json").read_text(encoding="utf-8")) == doc
    assert (dossier / "evaluation.md").read_text(encoding="utf-8") == sortie.markdown(doc)
    with pytest.raises(ValueError, match=r"evaluation\.json existe déjà"):
        sortie.preparer(dossier)
    (tmp_path / "fichier").write_bytes(b"")
    with pytest.raises(ValueError, match="dossier inutilisable"):
        sortie.preparer(tmp_path / "fichier")


# Commande, dans le processus des tests


@pytest.fixture
def sans_reseau(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le banc croit être dans un espace de noms vide : la vraie vérification est testée à part."""
    monkeypatch.setattr(reseau, "verifier_absence", lambda: ("lo",))


def analyser_factice(fonction: Callable[[Path], Analyse]) -> Callable[..., Analyse]:
    def analyser(chemin: Path, **_options: object) -> Analyse:
        return fonction(chemin)

    return analyser


@pytest.mark.usefixtures("sans_reseau")
def test_commande_sans_ecart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fichiers = {f"a{n}.txt": str(n).encode() for n in range(73)}
    manifeste = ecrire_corpus(tmp_path, fichiers)
    analyse = analyse_alpha(EtatTechnique.APPLIQUEE, EtatTechnique.APPLIQUEE)
    monkeypatch.setattr(cli, "analyser", analyser_factice(lambda _chemin: analyse))
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r")]) == 0
    assert "73 fichiers de la partie evaluation évalués" in capsys.readouterr().out
    doc = json.loads((tmp_path / "r" / "evaluation.json").read_text(encoding="utf-8"))
    assert doc["par_fichier"]["cible_atteinte"] is True
    assert doc["reseau"] == {"interfaces": ["lo"], "tentatives": 0}


@pytest.mark.exigence("ES-11")
@pytest.mark.usefixtures("sans_reseau")
def test_commande_tentative_de_reseau(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a"})

    def analyser(_chemin: Path) -> Analyse:
        # Une bibliothèque qui avalerait l'erreur : la tentative reste notée.
        with contextlib.suppress(reseau.ReseauInterdit):
            socket.create_connection(("192.0.2.1", 80), timeout=0.1)
        return analyse_alpha(EtatTechnique.APPLIQUEE, EtatTechnique.APPLIQUEE)

    monkeypatch.setattr(cli, "analyser", analyser_factice(analyser))
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r")]) == 3
    assert "accès au réseau pendant l'évaluation (socket.getaddrinfo)" in capsys.readouterr().err
    assert not (tmp_path / "r" / "evaluation.json").exists()

    def interdit(_chemin: Path) -> Analyse:
        raise reseau.ReseauInterdit("socket.connect")

    monkeypatch.setattr(cli, "analyser", analyser_factice(interdit))
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r")]) == 3
    assert "(socket.connect)" in capsys.readouterr().err


@pytest.mark.usefixtures("sans_reseau")
def test_commande_refuse(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a"})
    sortie_ = str(tmp_path / "r")
    assert cli.main([str(tmp_path / "absent.toml"), "--sortie", sortie_]) == 2
    assert cli.main([str(manifeste), "--sortie", sortie_, "--desactiver", "inconnu"]) == 2
    assert cli.main([str(manifeste), "--sortie", sortie_, "--catalogue", str(tmp_path)]) == 2
    (tmp_path / "r").mkdir()
    (tmp_path / "r" / "evaluation.md").write_bytes(b"")
    assert cli.main([str(manifeste), "--sortie", sortie_]) == 2
    erreurs = capsys.readouterr().err.splitlines()
    assert erreurs[0].startswith("banc : manifeste illisible")
    assert erreurs[1] == "banc : module inconnu : inconnu"
    assert erreurs[2].startswith("banc : ")
    assert erreurs[3] == "banc : evaluation.md existe déjà ; aucun rapport n'est écrasé"
    assert len(erreurs) == 4


@pytest.mark.usefixtures("sans_reseau")
def test_commande_fichier_modifie(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifeste = ecrire_corpus(tmp_path, {"a.txt": b"a"})
    (tmp_path / "a.txt").write_bytes(b"b")
    assert cli.main([str(manifeste), "--sortie", str(tmp_path / "r")]) == 2
    assert "a.txt : empreinte différente du manifeste" in capsys.readouterr().err


@pytest.mark.exigence("ES-11")
def test_commande_refusee_avec_reseau(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def present() -> tuple[str, ...]:
        raise reseau.ReseauPresent("interfaces réseau présentes (eth0)")

    monkeypatch.setattr(reseau, "verifier_absence", present)
    assert cli.main([str(ESSAI), "--sortie", "inutilise"]) == 2
    assert capsys.readouterr().err == "banc : interfaces réseau présentes (eth0)\n"


# Banc complet, processus séparé


def _unshare() -> list[str] | None:
    """Préfixe qui lance une commande dans un espace de noms réseau vide, si possible."""
    commande = shutil.which("unshare")
    if commande is None:
        return None
    essai = subprocess.run([commande, "-rn", "true"], capture_output=True, check=False)
    return [commande, "-rn"] if essai.returncode == 0 else None


def lancer(*arguments: str, prefixe: list[str] = []) -> subprocess.CompletedProcess[str]:  # noqa: B006
    return subprocess.run(
        [*prefixe, sys.executable, "-m", "banc", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=RACINE,
        check=False,
    )


@pytest.mark.exigence("ES-11", "ES-22", "NF-16")
def test_banc_sur_le_corpus_d_essai(tmp_path: Path) -> None:
    prefixe = _unshare()
    if prefixe is None:
        # La CI Linux permet les espaces de noms (code.yml) : le test n'y est jamais sauté.
        if sys.platform.startswith("linux") and os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("unshare -rn indisponible sur la CI Linux")
        pytest.skip("espace de noms réseau non disponible (Linux et unshare requis)")
    fini = lancer(str(ESSAI), "--sortie", str(tmp_path / "r"), prefixe=prefixe)
    # Quatre authentiques ne suffisent pas à établir la cible : c'est le seul écart attendu.
    assert fini.returncode == 1, fini.stderr
    doc = json.loads((tmp_path / "r" / "evaluation.json").read_text(encoding="utf-8"))
    assert doc["reseau"] == {"interfaces": ["lo"], "tentatives": 0}
    assert doc["publiable"] is False
    assert doc["fichiers"]["total"] == 9
    assert doc["fichiers"]["refus"] == {"vide": 1}
    assert doc["fichiers"]["arrets_brutaux"] == {}
    assert doc["par_fichier"]["categories"]["authentique"]["effectif"] == 4
    assert [e.split(" :")[0] for e in doc["ecarts"]] == ["taux par fichier"]


@pytest.mark.exigence("ES-11")
def test_banc_refuse_de_demarrer_avec_le_reseau(tmp_path: Path) -> None:
    if sys.platform.startswith("linux") and reseau.interfaces() == ("lo",):
        pytest.skip("le système des tests est déjà sans réseau")
    fini = lancer(str(ESSAI), "--sortie", str(tmp_path / "r"))
    assert fini.returncode == 2
    assert fini.stderr.startswith("banc : ")
    assert not (tmp_path / "r").exists()
