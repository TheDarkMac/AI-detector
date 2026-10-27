"""Tests du modèle de données : invariants, sérialisation, analyse interrompue (T11, T13)."""

import dataclasses
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from voight_kampff.rapport.modele import (
    LONGUEUR_MAX_IDENTIFIANT,
    LONGUEUR_MAX_TEXTE,
    NOMBRE_MAX_ELEMENTS,
    NOMBRE_MAX_PARTIES,
    RAISONS_D_INTERRUPTION,
    RAISONS_D_UNE_PARTIE,
    RAISONS_PROPRES_A_UNE_TECHNIQUE,
    VERSION_SCHEMA,
    Categorie,
    Constat,
    Couverture,
    Dependance,
    Direction,
    EtatIsolation,
    EtatTechnique,
    Fondement,
    Graduation,
    Identification,
    Intervalle,
    Localisation,
    ManqueIsolation,
    Niveau,
    NiveauIsolation,
    NonMenee,
    Observation,
    Partie,
    Phrase,
    Plage,
    RaisonNonMenee,
    Rapport,
    ReferenceRegle,
    TechniqueCouverte,
    Versions,
    Zone,
)

EMPREINTE = "3f" * 32
JPEG = Partie(1, "jpeg", Plage(0, 2_000_000), fin_connue=True)


def aller_retour(rapport: Rapport) -> Rapport:
    return Rapport.depuis_dict(json.loads(json.dumps(rapport.vers_dict())))


def indice(**modifications: Any) -> Constat:
    valeurs: dict[str, Any] = {
        "phrase": Phrase("gabarit", {"valeur": "o1"}),
        "donnees": ("o1",),
        "regle": ReferenceRegle("R-1", "1"),
        "module": "m",
        "fondement": Fondement.MESURE,
        "categorie": Categorie.INDICE,
        "direction": Direction.RETOUCHE,
        "graduation": Graduation(Niveau.MODERE, evaluee=True),
    }
    return Constat(**(valeurs | modifications))


# Sérialisation


def test_aller_retour_json(rapport: Rapport) -> None:
    assert aller_retour(rapport) == rapport


def test_aucun_null_dans_le_json(rapport: Rapport) -> None:
    assert "null" not in json.dumps(rapport.vers_dict())


def test_version_du_schema_inscrite(rapport: Rapport) -> None:
    assert rapport.vers_dict()["version_schema"] == VERSION_SCHEMA


def test_version_de_schema_inconnue_refusee(rapport: Rapport) -> None:
    document = rapport.vers_dict() | {"version_schema": "99.0.0"}
    with pytest.raises(ValueError, match="version de schéma"):
        Rapport.depuis_dict(document)


def test_interrompue_incoherente_refusee(rapport: Rapport) -> None:
    document = rapport.vers_dict() | {"interrompue": True}
    with pytest.raises(ValueError, match="interrompue"):
        Rapport.depuis_dict(document)


def test_objets_figes(rapport: Rapport) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        rapport.identification.nom = "autre.jpg"  # type: ignore[misc]


def test_parametres_de_phrase_copies_et_figes() -> None:
    parametres = {"valeur": "o1"}
    phrase = Phrase("gabarit", parametres)
    parametres["autre"] = "o2"
    assert dict(phrase.parametres) == {"valeur": "o1"}
    with pytest.raises(TypeError):
        phrase.parametres["autre"] = "o2"  # type: ignore[index]


def test_le_modele_ne_charge_pas_jsonschema() -> None:
    # Le processus de travail construit ses résultats sans la bibliothèque de validation.
    resultat = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys, voight_kampff.rapport.modele; print('jsonschema' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert resultat.stdout.strip() == "False"


# Analyse interrompue (ADR-0023)


@pytest.mark.parametrize("raison", [r for r in RaisonNonMenee if r not in RAISONS_D_UNE_PARTIE])
def test_interrompue_selon_la_raison(rapport: Rapport, raison: RaisonNonMenee) -> None:
    non_menee = NonMenee(raison, "jpeg", partie=1)
    modifie = dataclasses.replace(rapport, non_menees=(*rapport.non_menees, non_menee))
    assert modifie.interrompue is (raison in RAISONS_D_INTERRUPTION)
    assert aller_retour(modifie) == modifie


def test_rapport_complet_non_interrompu(rapport: Rapport) -> None:
    assert rapport.interrompue is False


# Constat (§6, ADR-0021, ADR-0058, ES-20)


@pytest.mark.parametrize(
    ("modifications", "motif"),
    [
        pytest.param(
            {"categorie": Categorie.PREUVE, "fondement": Fondement.DECLARATION, "graduation": None},
            "vérification",
            id="preuve-sur-declaration",
        ),
        pytest.param(
            {"categorie": Categorie.PREUVE, "fondement": Fondement.MESURE, "graduation": None},
            "vérification",
            id="preuve-sur-mesure",
        ),
        pytest.param(
            {"categorie": Categorie.PREUVE, "fondement": Fondement.VERIFICATION_DETERMINISTE},
            "niveau",
            id="preuve-avec-niveau",
        ),
        pytest.param({"graduation": None}, "niveau", id="indice-sans-niveau"),
        pytest.param(
            {"direction": Direction.RIEN_DE_PARTICULIER}, "hypothèse", id="indice-sans-direction"
        ),
        pytest.param(
            {"categorie": Categorie.INFORMATION_NEUTRE, "direction": Direction.RIEN_DE_PARTICULIER},
            "niveau",
            id="neutre-avec-niveau",
        ),
        pytest.param(
            {"categorie": Categorie.INFORMATION_NEUTRE, "graduation": None},
            "ne pointe vers rien",
            id="neutre-avec-direction",
        ),
        pytest.param({"donnees": ()}, "aucune donnée", id="sans-donnee"),
        pytest.param({"donnees": ("o1", "o1")}, "doublon", id="donnee-en-double"),
        pytest.param({"donnees": ("o1",) * 257}, "trop de données", id="trop-de-donnees"),
        pytest.param(
            {"phrase": Phrase("gabarit", {"valeur": "o2"})},
            "paramètre",
            id="parametre-hors-donnees",
        ),
        pytest.param({"module": "a b"}, "identifiant", id="module-invalide"),
    ],
)
def test_constat_incoherent_refuse(modifications: dict[str, Any], motif: str) -> None:
    with pytest.raises(ValueError, match=motif):
        indice(**modifications)


@pytest.mark.parametrize("fondement", list(Fondement))
@pytest.mark.parametrize("categorie", list(Categorie))
@pytest.mark.parametrize("direction", list(Direction))
def test_combinaisons_admises(
    fondement: Fondement, categorie: Categorie, direction: Direction
) -> None:
    preuve_admise = fondement in {
        Fondement.VERIFICATION_CRYPTOGRAPHIQUE,
        Fondement.VERIFICATION_DETERMINISTE,
    }
    admise = {
        Categorie.PREUVE: preuve_admise,
        Categorie.INDICE: direction is not Direction.RIEN_DE_PARTICULIER,
        Categorie.INFORMATION_NEUTRE: direction is Direction.RIEN_DE_PARTICULIER,
    }[categorie]
    graduation = Graduation(Niveau.FAIBLE, evaluee=False) if categorie is Categorie.INDICE else None
    modifications = {
        "fondement": fondement,
        "categorie": categorie,
        "direction": direction,
        "graduation": graduation,
    }
    if admise:
        indice(**modifications)
    else:
        with pytest.raises(ValueError, match="constat"):
            indice(**modifications)


def test_cinq_directions() -> None:
    assert [d.value for d in Direction] == [
        "origine_ia",
        "retouche",
        "transformation",
        "authenticite",
        "rien_de_particulier",
    ]


@pytest.mark.parametrize("niveau", [Niveau.MODERE, Niveau.FORT])
def test_regle_non_evaluee_au_niveau_faible(niveau: Niveau) -> None:
    with pytest.raises(ValueError, match="non évaluée"):
        Graduation(niveau, evaluee=False)


def test_phrase_bornee() -> None:
    with pytest.raises(ValueError, match="trop de paramètres"):
        Phrase("gabarit", {f"p{i}": "o1" for i in range(33)})


@pytest.mark.parametrize(
    "identifiant",
    ["", "a b", "-debut", "é", "abc\n", "x" * (LONGUEUR_MAX_IDENTIFIANT + 1)],
)
def test_identifiant_invalide_refuse(identifiant: str) -> None:
    with pytest.raises(ValueError, match="identifiant invalide"):
        ReferenceRegle(identifiant, "1")


@pytest.mark.parametrize("version", ["", "1 0", "v1\n", "1" * 65])
def test_version_invalide_refusee(version: str) -> None:
    with pytest.raises(ValueError, match="version invalide"):
        ReferenceRegle("R-1", version)


# Observation (ADR-0057, ADR-0058)


@pytest.mark.parametrize(
    "valeur",
    [
        "texte",
        "",
        True,
        0,
        -(2**63),
        2**63 - 1,
        1.5,
        (),
        ("a", 1, 2.5, False),
        tuple(range(NOMBRE_MAX_ELEMENTS)),
        "x" * LONGUEUR_MAX_TEXTE,
    ],
)
def test_valeurs_admises(valeur: Any) -> None:
    observation = Observation("o1", "m", "nom", valeur)
    assert Observation.depuis_dict(json.loads(json.dumps(observation.vers_dict()))) == observation


@pytest.mark.parametrize(
    ("valeur", "motif"),
    [
        pytest.param(float("nan"), "non fini", id="nan"),
        pytest.param(float("inf"), "non fini", id="infini"),
        pytest.param(2**63, "hors bornes", id="entier-trop-grand"),
        pytest.param(-(2**63) - 1, "hors bornes", id="entier-trop-petit"),
        pytest.param(1e19, "hors bornes", id="reel-trop-grand"),
        pytest.param("x" * (LONGUEUR_MAX_TEXTE + 1), "trop long", id="texte-trop-long"),
        pytest.param("\ud800", "UTF-8", id="substitut-isole"),
        pytest.param(tuple(range(NOMBRE_MAX_ELEMENTS + 1)), "trop d'éléments", id="liste-longue"),
        pytest.param(((1,),), "type", id="liste-imbriquee"),
        pytest.param(None, "type", id="none"),
    ],
)
def test_valeurs_refusees(valeur: Any, motif: str) -> None:
    with pytest.raises((ValueError, TypeError), match=motif):
        Observation("o1", "m", "nom", valeur)


def test_valeur_de_type_inconnu_refusee_a_la_lecture() -> None:
    document = {"identifiant": "o1", "module": "m", "nom": "n", "valeur": {"objet": 1}}
    with pytest.raises(TypeError, match="type"):
        Observation.depuis_dict(document)


@pytest.mark.parametrize("unite", ["", "u" * 33])
def test_unite_invalide_refusee(unite: str) -> None:
    with pytest.raises(ValueError, match="unite"):
        Observation("o1", "m", "nom", 1, unite=unite)


def test_message_d_erreur_sans_la_valeur_recue() -> None:
    # Une valeur venue d'un fichier hostile ne doit jamais atteindre un message (ES-15).
    with pytest.raises(ValueError, match="identifiant invalide") as erreur:
        Observation("SECRET source", "m", "nom", 1)
    assert "SECRET" not in str(erreur.value)
    with pytest.raises(ValueError, match="trop long") as erreur:
        Observation("o1", "m", "nom", "SECRET" * 1000)
    assert "SECRET" not in str(erreur.value)


# Localisation (A-46)


@pytest.mark.parametrize(
    ("fabrique", "motif"),
    [
        pytest.param(Localisation, "vide", id="localisation-vide"),
        pytest.param(lambda: Localisation(chemin=""), "vide", id="chemin-vide"),
        pytest.param(lambda: Localisation(chemin="\udc00"), "UTF-8", id="chemin-substitut"),
        pytest.param(lambda: Localisation(page=0), "hors bornes", id="page-zero"),
        pytest.param(lambda: Plage(debut=-1, longueur=1), "hors bornes", id="plage-negative"),
        pytest.param(lambda: Plage(debut=0, longueur=0), "hors bornes", id="plage-vide"),
        pytest.param(lambda: Zone(0, 0, 0, 1), "hors bornes", id="zone-vide"),
        pytest.param(lambda: Zone(-1, 0, 1, 1), "hors bornes", id="zone-negative"),
        pytest.param(lambda: Intervalle(2.0, 1.0), "incohérentes", id="intervalle-inverse"),
        pytest.param(lambda: Intervalle(-1.0, 1.0), "incohérentes", id="intervalle-negatif"),
        pytest.param(lambda: Intervalle(0.0, float("nan")), "non fini", id="intervalle-nan"),
        pytest.param(lambda: Plage(debut=True, longueur=1), "hors bornes", id="booleen"),
    ],
)
def test_localisation_invalide_refusee(fabrique: Any, motif: str) -> None:
    with pytest.raises(ValueError, match=motif):
        fabrique()


# Identification (ES-14, ADR-0031)


@pytest.mark.parametrize(
    ("modifications", "motif"),
    [
        pytest.param({"nom": ""}, "sans chemin", id="nom-vide"),
        pytest.param({"nom": "/home/source/photo.jpg"}, "sans chemin", id="chemin-posix"),
        pytest.param({"nom": "C:\\Users\\source\\photo.jpg"}, "sans chemin", id="chemin-windows"),
        pytest.param({"nom": "photo\x00.jpg"}, "sans chemin", id="nul"),
        pytest.param({"nom": "\ud800.jpg"}, "UTF-8", id="nom-substitut"),
        pytest.param({"empreinte": EMPREINTE.upper()}, "SHA-256", id="empreinte-majuscules"),
        pytest.param({"empreinte": EMPREINTE[:-1]}, "SHA-256", id="empreinte-courte"),
        pytest.param({"taille": -1}, "hors bornes", id="taille-negative"),
        pytest.param({"format_reel": "png"}, "partie 1", id="format-autre-que-la-partie-1"),
        pytest.param({"parties": ()}, "aucun format reconnu", id="sans-partie"),
        pytest.param(
            {"format_reel": "zip", "parties": (Partie(1, "zip", Plage(0, 10), fin_connue=True),)},
            "aucun format du périmètre",
            id="hors-perimetre-seulement",
        ),
        pytest.param(
            {"parties": (dataclasses.replace(JPEG, rang=2),)}, "consécutifs", id="rang-initial"
        ),
        pytest.param(
            {
                "parties": (
                    Partie(1, "jpeg", Plage(10, 100), fin_connue=True),
                    Partie(2, "pdf", Plage(0, 10), fin_connue=True),
                )
            },
            "ordre des débuts",
            id="debuts-en-desordre",
        ),
        pytest.param(
            {"parties": (Partie(1, "jpeg", Plage(0, 2_048_577), fin_connue=True),)},
            "hors du fichier",
            id="plage-au-dela",
        ),
        pytest.param(
            {"parties": (dataclasses.replace(JPEG, fin_connue=False),)},
            "hors du fichier",
            id="fin-inconnue-avant-la-fin-du-fichier",
        ),
        pytest.param(
            {
                "parties": tuple(
                    Partie(rang, "jpeg", Plage(rang, 1), fin_connue=True)
                    for rang in range(1, NOMBRE_MAX_PARTIES + 2)
                )
            },
            "trop de parties",
            id="trop-de-parties",
        ),
        pytest.param({"date_analyse": datetime(2026, 10, 26, 14, 3)}, "UTC", id="date-sans-fuseau"),
        pytest.param(
            {"date_analyse": datetime(2026, 10, 26, 14, 3, tzinfo=timezone(timedelta(hours=2)))},
            "UTC",
            id="date-hors-utc",
        ),
        pytest.param(
            {"date_analyse": datetime(2026, 10, 26, 14, 3, 0, 5, tzinfo=UTC)},
            "seconde",
            id="date-microsecondes",
        ),
    ],
)
def test_identification_invalide_refusee(
    rapport: Rapport, modifications: dict[str, Any], motif: str
) -> None:
    with pytest.raises(ValueError, match=motif):
        dataclasses.replace(rapport.identification, **modifications)


def test_date_d_analyse_en_utc_a_la_seconde(rapport: Rapport) -> None:
    assert rapport.vers_dict()["identification"]["date_analyse"] == "2026-10-26T14:03:00Z"


def test_format_de_partie_inconnu_refuse() -> None:
    with pytest.raises(ValueError, match="format inconnu"):
        Partie(1, "jpeg2000", Plage(0, 1), fin_connue=True)


def test_partie_tronquee_sans_fin_connue() -> None:
    with pytest.raises(ValueError, match="tronquée"):
        Partie(1, "jpeg", Plage(0, 1), fin_connue=True, tronquee=True)


def test_signalements_deduits(rapport: Rapport) -> None:
    identification = rapport.identification
    assert identification.extension == "jpg"
    assert identification.extension_concordante is True
    # Les 576 octets qui suivent l'archive : après la fin logique de la dernière partie.
    assert identification.octets_non_reconnus == (Plage(2_048_000, 576),)
    document = rapport.vers_dict()["identification"]
    assert document["extension_concordante"] is True
    assert document["octets_non_reconnus"] == [{"debut": 2_048_000, "longueur": 576}]


@pytest.mark.parametrize(
    ("nom", "extension", "concordante"),
    [
        ("photo.JPG", "jpg", True),
        ("photo.png", "png", False),
        ("archive.tar.gz", "gz", False),
        ("sans-extension", None, None),
        (".profil", None, None),
        ("nom." + "x" * 33, None, None),
    ],
)
def test_extension_et_concordance(
    rapport: Rapport, nom: str, extension: str | None, concordante: bool | None
) -> None:
    identification = dataclasses.replace(rapport.identification, nom=nom)
    assert identification.extension == extension
    assert identification.extension_concordante is concordante
    assert Identification.depuis_dict(identification.vers_dict()) == identification


def test_octets_non_reconnus_avant_entre_et_apres() -> None:
    identification = Identification(
        nom="f.pdf",
        format_reel="pdf",
        taille=100,
        empreinte=EMPREINTE,
        date_analyse=datetime(2026, 10, 27, tzinfo=UTC),
        parties=(
            Partie(1, "pdf", Plage(10, 30), fin_connue=True),
            Partie(2, "pdf", Plage(20, 20), fin_connue=True),  # chevauche la première
            Partie(3, "zip", Plage(60, 30), fin_connue=True),
        ),
    )
    assert identification.octets_non_reconnus == (Plage(0, 10), Plage(40, 20), Plage(90, 10))


@pytest.mark.parametrize(
    ("champ", "valeur"),
    [
        ("extension", "png"),
        ("extension_concordante", False),
        ("octets_non_reconnus", []),
    ],
)
def test_signalement_incoherent_refuse_a_la_lecture(
    rapport: Rapport, champ: str, valeur: object
) -> None:
    document = rapport.vers_dict()["identification"] | {champ: valeur}
    with pytest.raises(ValueError, match=champ):
        Identification.depuis_dict(document)


# Versions, isolation (ADR-0023, ADR-0035)


def test_dependance_en_double_refusee(rapport: Rapport) -> None:
    with pytest.raises(ValueError, match="doublon"):
        Versions("0.1.0", rapport.versions.catalogue, (Dependance("a", "1"), Dependance("a", "2")))


def test_catalogue_a_empreinte_invalide_refuse(rapport: Rapport) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        dataclasses.replace(rapport.versions.catalogue, empreinte="0")


@pytest.mark.parametrize(
    ("niveau", "manques", "motif"),
    [
        (NiveauIsolation.COMPLETE, (ManqueIsolation.RESEAU,), "réduite si et seulement si"),
        (NiveauIsolation.REDUITE, (), "réduite si et seulement si"),
        (NiveauIsolation.REDUITE, (ManqueIsolation.LECTURE,) * 2, "doublon"),
    ],
)
def test_isolation_incoherente_refusee(
    niveau: NiveauIsolation, manques: tuple[ManqueIsolation, ...], motif: str
) -> None:
    with pytest.raises(ValueError, match=motif):
        EtatIsolation(niveau, manques)


# Analyses non menées et couverture (ADR-0056, ADR-0059)


@pytest.mark.parametrize("raison", list(RaisonNonMenee))
def test_module_obligatoire_selon_la_raison(raison: RaisonNonMenee) -> None:
    if raison in RAISONS_PROPRES_A_UNE_TECHNIQUE:
        with pytest.raises(ValueError, match="propre à une technique"):
            NonMenee(raison)
    elif raison in RAISONS_D_UNE_PARTIE:
        with pytest.raises(ValueError, match="propre à une partie"):
            NonMenee(raison)
        with pytest.raises(ValueError, match="propre à une partie"):
            NonMenee(raison, "jpeg", partie=1)
        assert NonMenee(raison, partie=2).module is None
    else:
        assert NonMenee(raison).module is None


def test_partie_obligatoire_avec_un_module() -> None:
    with pytest.raises(ValueError, match="obligatoire avec un module"):
        NonMenee(RaisonNonMenee.ERREUR_MODULE, "jpeg")
    with pytest.raises(ValueError, match="hors bornes"):
        NonMenee(RaisonNonMenee.ERREUR_MODULE, "jpeg", partie=0)


@pytest.mark.parametrize(
    "fabrique",
    [
        lambda: Observation("m/1", "m", "n", 1, partie=0),
        lambda: TechniqueCouverte("m", EtatTechnique.APPLIQUEE, "1", partie=0),
        lambda: Partie(0, "jpeg", Plage(0, 1), fin_connue=True),
        lambda: indice(partie=0),
    ],
)
def test_rang_de_partie_a_partir_de_un(fabrique: Any) -> None:
    with pytest.raises(ValueError, match="hors bornes"):
        fabrique()


def test_version_absente_seulement_pour_une_technique_non_menee() -> None:
    with pytest.raises(ValueError, match="version"):
        TechniqueCouverte("stylometrie", EtatTechnique.APPLIQUEE)
    with pytest.raises(ValueError, match="version"):
        TechniqueCouverte("stylometrie", EtatTechnique.PARTIELLE)


def test_technique_hors_v1_non_applicable_sans_version(rapport: Rapport) -> None:
    # Sur la partie d'un polyglotte qui n'est pas de ses formats (ADR-0087).
    couverture = Couverture(
        (*rapport.couverture.techniques, TechniqueCouverte("enf", EtatTechnique.NON_APPLICABLE)),
        rapport.couverture.marquages_recherches,
    )
    assert dataclasses.replace(rapport, couverture=couverture).couverture == couverture
    # Une technique livrée, non menée pour une autre raison que hors_v1, garde sa version.
    sans_version = tuple(
        dataclasses.replace(t, version=None) if t.module == "prnu" else t
        for t in rapport.couverture.techniques
    )
    with pytest.raises(ValueError, match="version absente seulement si hors V1"):
        dataclasses.replace(rapport, couverture=Couverture(sans_version, ()))


@pytest.mark.parametrize(
    ("techniques", "marquages"),
    [
        (
            (
                TechniqueCouverte("m", EtatTechnique.APPLIQUEE, "1"),
                TechniqueCouverte("m", EtatTechnique.PARTIELLE, "1"),
            ),
            (),
        ),
        ((), ("c2pa", "c2pa")),
    ],
)
def test_couverture_en_double_refusee(
    techniques: tuple[TechniqueCouverte, ...], marquages: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError, match="doublon"):
        Couverture(techniques, marquages)


def test_une_technique_par_partie() -> None:
    couverture = Couverture(
        (
            TechniqueCouverte("m", EtatTechnique.APPLIQUEE, "1", partie=1),
            TechniqueCouverte("m", EtatTechnique.NON_APPLICABLE, "1", partie=2),
        ),
        (),
    )
    assert len(couverture.techniques) == 2


def avec_couverture(rapport: Rapport, *techniques: TechniqueCouverte) -> Couverture:
    remplacees = {technique.module for technique in techniques}
    conservees = tuple(t for t in rapport.couverture.techniques if t.module not in remplacees)
    return Couverture((*conservees, *techniques), rapport.couverture.marquages_recherches)


@pytest.mark.parametrize(
    ("modifier", "motif"),
    [
        pytest.param(
            lambda r: {"constats": (*r.constats, indice(module="jpeg"))},
            "observation absente",
            id="renvoi-vers-observation-absente",
        ),
        pytest.param(
            lambda r: {"observations": (*r.observations, r.observations[0])},
            "doublon",
            id="observation-en-double",
        ),
        pytest.param(
            lambda r: {"observations": (*r.observations, Observation("x/1", "inconnu", "n", 1))},
            "ni appliquée ni partielle",
            id="observation-d-une-technique-inconnue",
        ),
        pytest.param(
            lambda r: {"observations": (*r.observations, Observation("x/1", "prnu", "n", 1))},
            "ni appliquée ni partielle",
            id="observation-d-une-technique-non-menee",
        ),
        pytest.param(
            lambda r: {"observations": (*r.observations, Observation("x/1", "pdf", "n", 1))},
            "ni appliquée ni partielle",
            id="observation-d-une-technique-non-applicable",
        ),
        pytest.param(
            lambda r: {
                "non_menees": (*r.non_menees, NonMenee(RaisonNonMenee.HORS_V1, "audio", partie=1))
            },
            "absente de la couverture",
            id="non-menee-hors-couverture",
        ),
        pytest.param(
            lambda r: {
                "non_menees": (
                    *r.non_menees,
                    NonMenee(RaisonNonMenee.ERREUR_MODULE, "c2pa", partie=1),
                )
            },
            "état incohérent",
            id="appliquee-avec-non-menee",
        ),
        pytest.param(
            lambda r: {"non_menees": r.non_menees[:1] + r.non_menees[2:]},
            "état incohérent",
            id="non-menee-sans-raison",
        ),
        pytest.param(
            lambda r: {
                "couverture": avec_couverture(
                    r, TechniqueCouverte("stylometrie", EtatTechnique.NON_MENEE, "0.1.0")
                )
            },
            "hors V1",
            id="hors-v1-avec-version",
        ),
        pytest.param(
            lambda r: {
                "couverture": avec_couverture(r, TechniqueCouverte("prnu", EtatTechnique.NON_MENEE))
            },
            "hors V1",
            id="sans-version-pour-une-autre-raison",
        ),
        pytest.param(
            lambda r: {
                "observations": (*r.observations, Observation("x/1", "c2pa", "n", 1, partie=2))
            },
            "ni appliquée ni partielle",
            id="observation-d-une-partie-non-analysee",
        ),
        pytest.param(
            lambda r: {
                "observations": (*r.observations, Observation("c2pa/9", "c2pa", "n", 1)),
                "constats": (
                    *r.constats,
                    dataclasses.replace(
                        r.constats[0], donnees=("c2pa/9", "jpeg/1"), phrase=Phrase("g")
                    ),
                ),
            },
            "autre technique ou partie",
            id="constat-citant-une-autre-technique",
        ),
        pytest.param(
            lambda r: {
                "couverture": avec_couverture(
                    r, TechniqueCouverte("c2pa", EtatTechnique.NON_APPLICABLE, "0.1.0", partie=2)
                )
            },
            "une entrée par technique et par partie",
            id="technique-sur-une-partie-hors-perimetre",
        ),
        pytest.param(
            lambda r: {"non_menees": r.non_menees[:-1]},
            "une non menée « hors_perimetre » par partie",
            id="partie-hors-perimetre-sans-non-menee",
        ),
        pytest.param(
            lambda r: {
                "non_menees": (*r.non_menees, NonMenee(RaisonNonMenee.HORS_PERIMETRE, partie=1))
            },
            "une non menée « hors_perimetre » par partie",
            id="hors-perimetre-sur-une-partie-analysee",
        ),
        pytest.param(
            lambda r: {
                "non_menees": (*r.non_menees, NonMenee(RaisonNonMenee.FICHIER_TRONQUE, partie=3))
            },
            "partie absente",
            id="non-menee-d-une-partie-inconnue",
        ),
        pytest.param(
            lambda r: {
                "non_menees": tuple(
                    n for n in r.non_menees if n.raison is not RaisonNonMenee.FORMAT_PARTIEL
                )
            },
            "« format_partiel » attendu",
            id="plage-non-reconnue-sans-non-menee",
        ),
        pytest.param(
            lambda r: {
                "identification": dataclasses.replace(
                    r.identification,
                    parties=(
                        r.identification.parties[0],
                        Partie(2, "zip", Plage(2_000_000, 48_576), False, tronquee=True),
                    ),
                )
            },
            "« fichier_tronque » attendu",
            id="partie-tronquee-sans-non-menee",
        ),
    ],
)
def test_rapport_incoherent_refuse(rapport: Rapport, modifier: Any, motif: str) -> None:
    with pytest.raises(ValueError, match=motif):
        dataclasses.replace(rapport, **modifier(rapport))


def test_couverture_incomplete_pour_un_polyglotte(rapport: Rapport) -> None:
    # Deux parties analysées : chaque technique doit figurer pour chacune des deux.
    polyglotte = dataclasses.replace(
        rapport.identification,
        parties=(JPEG, Partie(2, "pdf", Plage(2_000_000, 48_576), fin_connue=False)),
    )
    with pytest.raises(ValueError, match="une entrée par technique et par partie"):
        dataclasses.replace(
            rapport,
            identification=polyglotte,
            non_menees=tuple(
                n for n in rapport.non_menees if n.raison is not RaisonNonMenee.HORS_PERIMETRE
            ),
        )


def test_rapport_minimal(rapport: Rapport) -> None:
    minimal = Rapport(
        identification=dataclasses.replace(
            rapport.identification, parties=(Partie(1, "jpeg", Plage(0, 2_048_576), True),)
        ),
        versions=rapport.versions,
        isolation=EtatIsolation(NiveauIsolation.COMPLETE),
        couverture=Couverture((), ()),
    )
    assert aller_retour(minimal) == minimal
    assert minimal.interrompue is False
