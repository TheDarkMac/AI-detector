"""Objets communs aux tests du modèle de données et des schémas (T11) ; profils du fuzzing (T14) ;
contrôle des marqueurs d'exigence (T17, ADR-0102)."""

import os
from datetime import UTC, date, datetime

import pytest
from hypothesis import settings

from banc import matrice
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
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
    VersionCatalogue,
    Versions,
    Zone,
)

# Fuzzing (ES-19, ADR-0082). « defaut » : exemples tirés d'une graine fixe, identiques à chaque
# passage et sur chaque système, pour une CI reproductible ; aucune base d'exemples écrite sur
# le disque. « campagne » : recherche longue et aléatoire, lancée à la main.
settings.register_profile(
    "defaut", max_examples=300, derandomize=True, database=None, deadline=None, print_blob=True
)
settings.register_profile("campagne", max_examples=200_000, database=None, deadline=None)
settings.load_profile(os.environ.get("VK_FUZZING", "defaut"))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Refuse un marqueur ``exigence`` vide ou qui cite une exigence absente de la matrice."""
    connues = matrice.identifiants()
    for item in items:
        for marqueur in item.iter_markers("exigence"):
            inconnues = sorted(set(marqueur.args) - connues) if marqueur.args else ["(aucune)"]
            if inconnues:
                raise pytest.UsageError(f"{item.nodeid} : exigence inconnue {', '.join(inconnues)}")


EMPREINTE = "3f" * 32
TAILLE = 2_048_576
PARTIES = (
    Partie(1, "jpeg", Plage(0, 2_000_000), fin_connue=True),
    Partie(2, "zip", Plage(2_000_000, 48_000), fin_connue=True),
)
"""Un JPEG suivi d'une archive ZIP, hors périmètre, puis de 576 octets non reconnus."""


def construire_rapport() -> Rapport:
    """Rapport qui emploie chaque élément du modèle au moins une fois."""
    observations = (
        Observation(
            "metadonnees/1",
            "metadonnees",
            "iptc.DigitalSourceType",
            "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
            localisation=Localisation(chemin="APP13/IPTC/2:DigitalSourceType"),
        ),
        Observation(
            "metadonnees/2",
            "metadonnees",
            "exif.ifd0.Artist",
            "Jeanne Martin",
            localisation=Localisation(octets=Plage(debut=24, longueur=13)),
            identifiante=CategorieIdentifiante.METADONNEE_NOMINATIVE,
        ),
        Observation("metadonnees/3", "metadonnees", "xmp.present", False),
        Observation(
            "c2pa/1",
            "c2pa",
            "c2pa.signature.etat",
            "valide",
            localisation=Localisation(chemin="APP11/JUMBF/c2pa", page=1),
        ),
        Observation(
            "jpeg/1",
            "jpeg",
            "jpeg.quantification.luminance",
            tuple(range(1, 65)),
            localisation=Localisation(zone=Zone(x=0, y=0, largeur=8, hauteur=8)),
        ),
        Observation(
            "jpeg/2",
            "jpeg",
            "jpeg.double_compression.score",
            0.875,
            unite="ratio",
            localisation=Localisation(intervalle=Intervalle(debut=0.0, fin=1.5)),
        ),
    )
    constats = (
        Constat(
            phrase=Phrase("c2pa.manifeste-valide", {"etat": "c2pa/1"}),
            donnees=("c2pa/1",),
            regle=ReferenceRegle("R-C2PA-001", "1"),
            module="c2pa",
            fondement=Fondement.VERIFICATION_CRYPTOGRAPHIQUE,
            categorie=Categorie.PREUVE,
            direction=Direction.ORIGINE_IA,
        ),
        Constat(
            phrase=Phrase("metadonnees.origine-ia-declaree", {"valeur": "metadonnees/1"}),
            donnees=("metadonnees/1",),
            regle=ReferenceRegle("R-META-001", "2"),
            module="metadonnees",
            fondement=Fondement.DECLARATION,
            categorie=Categorie.INDICE,
            direction=Direction.ORIGINE_IA,
            graduation=Graduation(Niveau.FORT, evaluee=True),
            localisation=Localisation(chemin="APP13/IPTC"),
        ),
        Constat(
            phrase=Phrase("jpeg.double-compression"),
            donnees=("jpeg/1", "jpeg/2"),
            regle=ReferenceRegle("R-JPEG-002", "1"),
            module="jpeg",
            fondement=Fondement.MESURE,
            categorie=Categorie.INDICE,
            direction=Direction.TRANSFORMATION,
            graduation=Graduation(Niveau.FAIBLE, evaluee=False),
        ),
        Constat(
            phrase=Phrase("metadonnees.xmp-absent"),
            donnees=("metadonnees/3",),
            regle=ReferenceRegle("R-META-010", "1"),
            module="metadonnees",
            fondement=Fondement.VERIFICATION_DETERMINISTE,
            categorie=Categorie.INFORMATION_NEUTRE,
            direction=Direction.RIEN_DE_PARTICULIER,
        ),
    )
    return Rapport(
        identification=Identification(
            nom="photo virale.jpg",
            format_reel="jpeg",
            taille=TAILLE,
            empreinte=EMPREINTE,
            date_analyse=datetime(2026, 10, 26, 14, 3, 0, tzinfo=UTC),
            parties=PARTIES,
        ),
        versions=Versions(
            outil="0.1.0.dev0",
            catalogue=VersionCatalogue("2026.10.0", date(2026, 10, 26), EMPREINTE, False),
            dependances=(Dependance("numpy", "2.5.4"), Dependance("c2pa-python", "0.38.1")),
        ),
        isolation=EtatIsolation(NiveauIsolation.REDUITE, (ManqueIsolation.RESEAU,)),
        couverture=Couverture(
            techniques=(
                TechniqueCouverte("metadonnees", EtatTechnique.APPLIQUEE, "0.1.0"),
                TechniqueCouverte("c2pa", EtatTechnique.APPLIQUEE, "0.1.0"),
                TechniqueCouverte("jpeg", EtatTechnique.PARTIELLE, "0.1.0"),
                TechniqueCouverte("prnu", EtatTechnique.NON_MENEE, "0.1.0"),
                TechniqueCouverte("pdf", EtatTechnique.NON_APPLICABLE, "0.1.0"),
                TechniqueCouverte("stylometrie", EtatTechnique.NON_MENEE),
            ),
            marquages_recherches=("c2pa", "iptc.digital_source_type"),
        ),
        observations=observations,
        constats=constats,
        non_menees=(
            NonMenee(
                RaisonNonMenee.FORMAT_PARTIEL,
                "jpeg",
                localisation=Localisation(page=2),
                partie=1,
            ),
            NonMenee(RaisonNonMenee.REFERENCE_MANQUANTE, "prnu", partie=1),
            NonMenee(RaisonNonMenee.HORS_V1, "stylometrie", partie=1),
            NonMenee(RaisonNonMenee.FICHIER_TRONQUE),
            NonMenee(
                RaisonNonMenee.FORMAT_PARTIEL,
                localisation=Localisation(octets=Plage(2_048_000, 576)),
            ),
            NonMenee(
                RaisonNonMenee.HORS_PERIMETRE,
                localisation=Localisation(octets=Plage(2_000_000, 48_000)),
                partie=2,
            ),
        ),
    )


@pytest.fixture
def rapport() -> Rapport:
    return construire_rapport()
