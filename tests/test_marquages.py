"""Tests des marquages : catalogue, couverture d'un fichier, rapport (T31, ADR-0175 à ADR-0178)."""

import dataclasses
import tomllib
from datetime import date
from pathlib import Path

import pytest
from catalogues import (
    ENTETE,
    MARQUAGES_LIVRES,
    ecrire_catalogue,
    marquage,
    marquage_dict,
    toml_marquages,
)
from conftest import construire_rapport
from metadonnees import jpeg_image
from test_rapport import analyse_de

from voight_kampff import _limites, exporter_html, exporter_json, schemas
from voight_kampff._marquages import RAISONS_DU_CATALOGUE, Marquage, Nature, couvrir
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration.catalogue import CatalogueInvalide, charger
from voight_kampff._orchestration.manifestes import Manifeste, decouvrir
from voight_kampff.analyse import analyser
from voight_kampff.cli import main, resume
from voight_kampff.rapport._presentation import libelle
from voight_kampff.rapport.modele import (
    Couverture,
    Direction,
    EtatTechnique,
    MarquageNonRecherche,
    Partie,
    Plage,
    RaisonNonRecherche,
    Rapport,
    TechniqueCouverte,
)

pytestmark = pytest.mark.exigence("F-24", "F-25")

RACINE_DU_DEPOT = Path(__file__).resolve().parents[1]
MARQUAGES_TOML = (
    RACINE_DU_DEPOT / "src" / "voight_kampff" / "donnees" / "catalogue" / "marquages.toml"
)

ALPHA = Manifeste(
    "alpha", "1.0", ("jpeg", "png"), ("F-24",), (), "test", (Direction.RIEN_DE_PARTICULIER,)
)
FORMAT_3 = ENTETE.replace("format = 1", "format = 3")
RECHERCHE = marquage_dict("M-ALPHA", raison=None, module="alpha", formats=["jpeg"])


def ecrire(dossier: Path, contenu: str, entete: str = FORMAT_3) -> Path:
    ecrire_catalogue(dossier, entete=entete)
    (dossier / catalogues.MARQUAGES).write_bytes(contenu.encode())
    return dossier


# Catalogue (ADR-0175)


def test_catalogue_livre() -> None:
    livre = charger(decouvrir())
    recherches = {m.identifiant: m.module for m in livre.marquages if m.module is not None}
    assert recherches == {"M-C2PA": "c2pa", "M-IPTC-DST": "xmp"}
    assert [m.identifiant for m in livre.marquages] == sorted(MARQUAGES_LIVRES)
    assert MARQUAGES_LIVRES["M-DWTDCT"].raison is RaisonNonRecherche.LECTEUR_A_VENIR
    assert MARQUAGES_LIVRES["M-SYNTHID"].raison is RaisonNonRecherche.LECTEUR_PROPRIETAIRE
    # Le marquage C2PA est recherché partout où le module c2pa lit un manifeste.
    par_module = {manifeste.identifiant: manifeste for manifeste in decouvrir()}
    assert MARQUAGES_LIVRES["M-C2PA"].formats == par_module["c2pa"].formats
    assert MARQUAGES_LIVRES["M-IPTC-DST"].formats == par_module["xmp"].formats
    for entree in livre.marquages:
        assert entree.verifie == date(2026, 11, 14)
        assert all(reference.startswith("https://") for reference in entree.references)


def test_catalogue_livre_ordre_du_fichier_indifferent() -> None:
    # Triés par identifiant au chargement : le fichier les regroupe par raison.
    document = tomllib.loads(MARQUAGES_TOML.read_text(encoding="utf-8"))
    identifiants = [entree["identifiant"] for entree in document["marquage"]]
    assert identifiants != sorted(identifiants)
    assert sorted(identifiants) == sorted(MARQUAGES_LIVRES)


def test_catalogue_fourni_avec_marquages(tmp_path: Path) -> None:
    contenu = toml_marquages(marquage_dict("M-ZETA"), RECHERCHE)
    fourni = charger((ALPHA,), ecrire(tmp_path, contenu))
    assert [m.identifiant for m in fourni.marquages] == ["M-ALPHA", "M-ZETA"]
    assert fourni.marquages[0] == Marquage(
        identifiant="M-ALPHA",
        nom="Marquage de test",
        nature=Nature.FILIGRANE,
        description="Marquage employé par les tests.",
        formats=("jpeg",),
        references=("https://exemple.org/marquage",),
        verifie=date(2026, 11, 14),
        module="alpha",
    )
    assert fourni.marquages[1].raison is RaisonNonRecherche.LECTEUR_NEURONAL


def test_catalogue_sans_marquages(tmp_path: Path) -> None:
    assert charger((ALPHA,), ecrire_catalogue(tmp_path, entete=FORMAT_3)).marquages == ()


@pytest.mark.parametrize(
    ("contenu", "entete", "attendu"),
    [
        pytest.param(
            toml_marquages(marquage_dict()),
            ENTETE.replace("format = 1", "format = 2"),
            "marquages dans un catalogue du format 2",
            id="format-2",
        ),
        pytest.param("marquage = 1\n", FORMAT_3, "marquages.toml : document", id="type"),
        pytest.param("marquage = [", FORMAT_3, "TOML illisible", id="illisible"),
        pytest.param(
            toml_marquages(marquage_dict(module="alpha")),
            FORMAT_3,
            "marquages.toml",
            id="module-et-raison",
        ),
        pytest.param(
            toml_marquages(marquage_dict(raison=None)),
            FORMAT_3,
            "marquages.toml",
            id="ni-module-ni-raison",
        ),
        pytest.param(
            toml_marquages(marquage_dict(raison="technique_non_menee")),
            FORMAT_3,
            "marquages.toml",
            id="raison-de-l-analyse",
        ),
        pytest.param(
            toml_marquages(marquage_dict("R-TEST")),
            FORMAT_3,
            "marquages.toml",
            id="identifiant",
        ),
        pytest.param(
            toml_marquages(marquage_dict(references=["http://exemple.org"])),
            FORMAT_3,
            "marquages.toml",
            id="reference-sans-https",
        ),
        pytest.param(
            toml_marquages(marquage_dict(formats=["gif"])),
            FORMAT_3,
            "marquages.toml",
            id="format-hors-perimetre",
        ),
        pytest.param(
            toml_marquages(marquage_dict(), marquage_dict()),
            FORMAT_3,
            "marquage défini deux fois : M-TEST",
            id="identifiant-en-double",
        ),
        pytest.param(
            toml_marquages(marquage_dict(verifie="2026-02-30")),
            FORMAT_3,
            "marquage M-TEST : date inexistante",
            id="date-inexistante",
        ),
        pytest.param(
            toml_marquages(marquage_dict(raison=None, module="gamma")),
            FORMAT_3,
            "marquage M-TEST : module gamma absent",
            id="module-inconnu",
        ),
        pytest.param(
            toml_marquages(marquage_dict(raison=None, module="alpha", formats=["pdf"])),
            FORMAT_3,
            "format que le module alpha ne traite pas",
            id="format-non-traite",
        ),
    ],
)
def test_catalogue_refuse(tmp_path: Path, contenu: str, entete: str, attendu: str) -> None:
    with pytest.raises(CatalogueInvalide) as erreur:
        charger((ALPHA,), ecrire(tmp_path, contenu, entete))
    assert attendu in str(erreur.value)


def test_trop_de_marquages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalogues, "MARQUAGES_MAX", 1)
    dossier = ecrire(tmp_path, toml_marquages(marquage_dict("M-A"), marquage_dict("M-B")))
    with pytest.raises(CatalogueInvalide, match="plus de 1 marquages"):
        charger((ALPHA,), dossier)
    assert _limites.MARQUAGES_MAX == 256


def test_marquage_module_ou_raison() -> None:
    with pytest.raises(ValueError, match="l'un des deux seulement"):
        marquage(module="alpha")
    with pytest.raises(ValueError, match="l'un des deux seulement"):
        marquage(raison=None)
    with pytest.raises(ValueError, match="constatée à l'analyse"):
        dataclasses.replace(marquage(), raison=RaisonNonRecherche.TECHNIQUE_NON_MENEE)
    assert RaisonNonRecherche.TECHNIQUE_NON_MENEE not in RAISONS_DU_CATALOGUE


# Couverture d'un fichier (ADR-0178)

JPEG = Partie(1, "jpeg", Plage(0, 100), fin_connue=True)
PNG = Partie(2, "png", Plage(100, 100), fin_connue=True)
ZIP = Partie(3, "zip", Plage(200, 100), fin_connue=True)
CATALOGUE = (
    marquage("M-SON", formats=["wav"]),
    marquage("M-IMAGE", formats=["jpeg", "png"]),
    marquage("M-ALPHA", raison=None, module="alpha", formats=["png"]),
)


def techniques(*etats: tuple[int, EtatTechnique]) -> tuple[TechniqueCouverte, ...]:
    return tuple(TechniqueCouverte("alpha", etat, "1.0", rang) for rang, etat in etats)


@pytest.mark.parametrize("etat", [EtatTechnique.APPLIQUEE, EtatTechnique.PARTIELLE])
def test_recherche_si_le_module_est_applique(etat: EtatTechnique) -> None:
    couverture = couvrir(
        CATALOGUE, (JPEG, PNG), techniques((1, EtatTechnique.NON_APPLICABLE), (2, etat))
    )
    assert couverture == (
        ("M-ALPHA",),
        (MarquageNonRecherche("M-IMAGE", RaisonNonRecherche.LECTEUR_NEURONAL),),
    )


@pytest.mark.parametrize("etat", [EtatTechnique.NON_MENEE, EtatTechnique.NON_APPLICABLE])
def test_technique_non_menee(etat: EtatTechnique) -> None:
    # Module désactivé, en erreur, ou analyse interrompue : le marquage reste à la couverture.
    recherches, non_recherches = couvrir(CATALOGUE, (PNG,), techniques((2, etat)))
    assert recherches == ()
    assert non_recherches == (
        MarquageNonRecherche("M-ALPHA", RaisonNonRecherche.TECHNIQUE_NON_MENEE),
        MarquageNonRecherche("M-IMAGE", RaisonNonRecherche.LECTEUR_NEURONAL),
    )
    # Sans entrée de couverture pour son module, de même.
    assert couvrir(CATALOGUE, (PNG,), ())[1][0].raison is RaisonNonRecherche.TECHNIQUE_NON_MENEE


def test_seulement_les_formats_des_parties_analysees() -> None:
    # Le module alpha appliqué au JPEG ne recherche pas M-ALPHA, propre au PNG ; une partie hors
    # périmètre ne compte pas, même si un marquage en citait le format.
    assert couvrir(CATALOGUE, (JPEG, ZIP), techniques((1, EtatTechnique.APPLIQUEE))) == (
        (),
        (MarquageNonRecherche("M-IMAGE", RaisonNonRecherche.LECTEUR_NEURONAL),),
    )
    assert couvrir((), (JPEG,), ()) == ((), ())


# Modèle et analyse


def test_couverture_un_marquage_une_fois() -> None:
    non_recherche = MarquageNonRecherche("M-A", RaisonNonRecherche.LECTEUR_NEURONAL)
    with pytest.raises(ValueError, match=r"couverture\.marquages : doublon"):
        Couverture((), ("M-A",), (non_recherche,))
    with pytest.raises(ValueError, match=r"couverture\.marquages : doublon"):
        Couverture((), (), (non_recherche, non_recherche))
    with pytest.raises(ValueError, match=r"marquage\.identifiant : identifiant invalide"):
        MarquageNonRecherche("", RaisonNonRecherche.LECTEUR_NEURONAL)


def test_rapport_avec_marquages_valide_et_relu() -> None:
    rapport = construire_rapport()
    document = rapport.vers_dict()
    assert document["couverture"]["marquages_non_recherches"] == [
        {"identifiant": "M-DWTDCT", "raison": "lecteur_a_venir"},
        {"identifiant": "M-SYNTHID", "raison": "lecteur_proprietaire"},
    ]
    schemas.valider("rapport", document)
    assert Rapport.depuis_dict(document) == rapport
    document["couverture"]["marquages_non_recherches"][0]["raison"] = "inconnue"
    with pytest.raises(schemas.DocumentInvalide):
        schemas.valider("rapport", document)


def test_analyse_verifie_ses_marquages() -> None:
    analyse = analyse_de(construire_rapport())
    assert analyse.marquage("M-SYNTHID").nom == "SynthID (Google) : images, audio, vidéo"
    with pytest.raises(ValueError, match="ceux de la couverture"):
        dataclasses.replace(analyse, marquages=analyse.marquages[1:])
    with pytest.raises(ValueError, match="ceux de la couverture"):
        dataclasses.replace(
            analyse, marquages=(*analyse.marquages, MARQUAGES_LIVRES["M-TRUSTMARK"])
        )
    with pytest.raises(ValueError, match="ceux de la couverture"):
        dataclasses.replace(analyse, marquages=(*analyse.marquages, analyse.marquages[0]))
    # Recherché sans module.
    couverture = dataclasses.replace(
        analyse.couverture, marquages_recherches=("M-C2PA", "M-TRUSTMARK")
    )
    sans_iptc = (analyse.marquages[0], *analyse.marquages[2:], MARQUAGES_LIVRES["M-TRUSTMARK"])
    with pytest.raises(ValueError, match="recherché sans module"):
        dataclasses.replace(analyse, couverture=couverture, marquages=sans_iptc)
    # Raison qui n'est pas la sienne ; « technique_non_menee » seulement avec un module.
    for raison, identifiant in [
        (RaisonNonRecherche.LECTEUR_NEURONAL, "M-SYNTHID"),
        (RaisonNonRecherche.TECHNIQUE_NON_MENEE, "M-SYNTHID"),
    ]:
        couverture = dataclasses.replace(
            analyse.couverture,
            marquages_non_recherches=(MarquageNonRecherche(identifiant, raison),),
        )
        with pytest.raises(ValueError, match="raison d'un marquage non recherché"):
            dataclasses.replace(
                analyse,
                couverture=couverture,
                marquages=(*analyse.marquages[:2], MARQUAGES_LIVRES[identifiant]),
            )
    couverture = dataclasses.replace(
        analyse.couverture,
        marquages_recherches=("M-IPTC-DST",),
        marquages_non_recherches=(
            MarquageNonRecherche("M-C2PA", RaisonNonRecherche.TECHNIQUE_NON_MENEE),
        ),
    )
    dataclasses.replace(analyse, couverture=couverture, marquages=analyse.marquages[:2])


# Rapport : HTML, JSON, terminal (ADR-0177)


def test_exports_nomment_les_marquages() -> None:
    analyse = analyse_de(construire_rapport())
    document = exporter_html(analyse)
    assert "Manifeste C2PA intégré (M-C2PA)" in document
    assert "Marquages connus non recherchés, avec leur raison" in document
    assert "SynthID (Google) : images, audio, vidéo (M-SYNTHID)" in document
    assert libelle("raisons_marquage", "lecteur_proprietaire") in document
    assert libelle("natures_marquage", "filigrane") in document
    assert '"marquages_non_recherches"' in exporter_json(analyse)
    lignes = resume(analyse)
    assert (
        "marquages recherchés : Manifeste C2PA intégré, "
        "Type de source numérique IPTC (DigitalSourceType)"
    ) in lignes
    assert (
        "marquage non recherché : SynthID (Google) : images, audio, vidéo "
        f"({libelle('raisons_marquage', 'lecteur_proprietaire')})"
    ) in lignes


def test_exports_sans_marquage() -> None:
    rapport = construire_rapport()
    sans = dataclasses.replace(
        rapport.couverture, marquages_recherches=(), marquages_non_recherches=()
    )
    analyse = analyse_de(dataclasses.replace(rapport, couverture=sans))
    document = exporter_html(analyse)
    assert "Marquages connus non recherchés</dt><dd>aucun" in document
    assert "Marquages recherchés</dt><dd>aucun" in document
    assert not any(ligne.startswith("marquage") for ligne in resume(analyse))


def test_regles_listent_les_marquages(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--regles"]) == 0
    lignes = capsys.readouterr().out.splitlines()
    assert "M-C2PA (c2pa) : Manifeste C2PA intégré" in lignes
    assert "M-SYNTHID-TEXTE (non recherché : cle_du_fournisseur) : SynthID Text" in lignes


# Analyses réelles


def test_analyse_d_un_jpeg(tmp_path: Path) -> None:
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(jpeg_image(640, 480))
    analyse = analyser(chemin)
    couverture = analyse.couverture
    assert couverture.marquages_recherches == ("M-C2PA", "M-IPTC-DST")
    attendus = {
        m.identifiant for m in MARQUAGES_LIVRES.values() if m.module is None and "jpeg" in m.formats
    }
    assert {m.identifiant for m in couverture.marquages_non_recherches} == attendus
    assert {m.identifiant for m in analyse.marquages} == attendus | {"M-C2PA", "M-IPTC-DST"}
    # Le module c2pa désactivé : son marquage n'est plus recherché, et le rapport le dit.
    desactive = analyser(chemin, desactiver=("c2pa",))
    assert desactive.couverture.marquages_recherches == ("M-IPTC-DST",)
    assert (
        MarquageNonRecherche("M-C2PA", RaisonNonRecherche.TECHNIQUE_NON_MENEE)
        in desactive.couverture.marquages_non_recherches
    )


def test_analyse_avec_un_catalogue_sans_marquages(tmp_path: Path) -> None:
    # Catalogue fourni au format 2, sans marquages.toml : deux listes vides, comme avant T31.
    source = catalogues.livre()
    dossier = tmp_path / "catalogue"
    (dossier / "regles").mkdir(parents=True)
    entete = (source / "catalogue.toml").read_text(encoding="utf-8")
    (dossier / "catalogue.toml").write_text(
        entete.replace("format = 3", "format = 2"), encoding="utf-8"
    )
    for fichier in (source / "regles").iterdir():
        (dossier / "regles" / fichier.name).write_bytes(fichier.read_bytes())
    chemin = tmp_path / "image.jpg"
    chemin.write_bytes(jpeg_image(640, 480))
    analyse = analyser(chemin, catalogue=dossier)
    assert analyse.couverture.marquages_recherches == ()
    assert analyse.couverture.marquages_non_recherches == ()
    assert analyse.marquages == ()
