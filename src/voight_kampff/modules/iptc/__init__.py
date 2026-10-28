"""Module ``iptc`` : métadonnées IPTC-IIM d'un JPEG (F-10, ADR-0114 ; fiche ``metadonnees-iptc``).

Lit les ressources Photoshop du segment APP13 et, dans la ressource ``0x0404``, chaque jeu de
données IPTC-IIM, observé sous le nom de la norme (``iptc.By-line``) ou, s'il n'y figure pas,
sous ``iptc.<enregistrement>:<numéro>`` (ADR-0117). Les propriétés IPTC écrites en XMP
(``Iptc4xmpCore``, ``Iptc4xmpExt``) sont lues par le module ``xmp``. Observe aussi
``iptc.present`` dans tous les cas (F-14).

Aucune règle : T22 et T23 lisent ces observations.
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.modules._lecture.iim import IPTC_NAA, JeuDeDonnees, jeux_de_donnees, ressources
from voight_kampff.rapport.modele import CategorieIdentifiante, RaisonNonMenee, Scalaire

__all__ = ["NOMS", "analyser"]

NOMS = {
    (1, 0): "EnvelopeRecordVersion",
    (1, 5): "Destination",
    (1, 20): "FileFormat",
    (1, 22): "FileVersion",
    (1, 30): "ServiceIdentifier",
    (1, 40): "EnvelopeNumber",
    (1, 50): "ProductID",
    (1, 60): "EnvelopePriority",
    (1, 70): "DateSent",
    (1, 80): "TimeSent",
    (1, 90): "CodedCharacterSet",
    (1, 100): "UniqueObjectName",
    (1, 120): "ARMIdentifier",
    (1, 122): "ARMVersion",
    (2, 0): "ApplicationRecordVersion",
    (2, 3): "ObjectTypeReference",
    (2, 4): "ObjectAttributeReference",
    (2, 5): "ObjectName",
    (2, 7): "EditStatus",
    (2, 8): "EditorialUpdate",
    (2, 10): "Urgency",
    (2, 12): "SubjectReference",
    (2, 15): "Category",
    (2, 20): "SupplementalCategories",
    (2, 22): "FixtureIdentifier",
    (2, 25): "Keywords",
    (2, 26): "ContentLocationCode",
    (2, 27): "ContentLocationName",
    (2, 30): "ReleaseDate",
    (2, 35): "ReleaseTime",
    (2, 37): "ExpirationDate",
    (2, 38): "ExpirationTime",
    (2, 40): "SpecialInstructions",
    (2, 42): "ActionAdvised",
    (2, 45): "ReferenceService",
    (2, 47): "ReferenceDate",
    (2, 50): "ReferenceNumber",
    (2, 55): "DateCreated",
    (2, 60): "TimeCreated",
    (2, 62): "DigitalCreationDate",
    (2, 63): "DigitalCreationTime",
    (2, 65): "OriginatingProgram",
    (2, 70): "ProgramVersion",
    (2, 75): "ObjectCycle",
    (2, 80): "By-line",
    (2, 85): "By-lineTitle",
    (2, 90): "City",
    (2, 92): "Sub-location",
    (2, 95): "Province-State",
    (2, 100): "Country-PrimaryLocationCode",
    (2, 101): "Country-PrimaryLocationName",
    (2, 103): "OriginalTransmissionReference",
    (2, 105): "Headline",
    (2, 110): "Credit",
    (2, 115): "Source",
    (2, 116): "CopyrightNotice",
    (2, 118): "Contact",
    (2, 120): "Caption-Abstract",
    (2, 121): "LocalCaption",
    (2, 122): "Writer-Editor",
    (2, 125): "RasterizedCaption",
    (2, 130): "ImageType",
    (2, 131): "ImageOrientation",
    (2, 135): "LanguageIdentifier",
    (2, 150): "AudioType",
    (2, 151): "AudioSamplingRate",
    (2, 152): "AudioSamplingResolution",
    (2, 153): "AudioDuration",
    (2, 154): "AudioOutcue",
    (2, 200): "ObjectPreviewFileFormat",
    (2, 201): "ObjectPreviewFileVersion",
    (2, 202): "ObjectPreviewData",
}
"""Jeux de données de l'IIM 4.2 (enregistrements 1 et 2), noms de la norme."""

_REPETABLES = frozenset(
    {(1, 5), (2, 4), (2, 12), (2, 20), (2, 25), (2, 26), (2, 27), (2, 80), (2, 85)}
    | {(2, 118), (2, 122)}
)
"""Jeux de données répétables : toujours observés en liste, même présents une fois."""
_ENTIERS = frozenset({(1, 0), (1, 20), (1, 22), (1, 120), (1, 122), (2, 0), (2, 200), (2, 201)})
"""Jeux de données binaires de deux octets : des nombres."""
_BINAIRES = frozenset({(2, 125), (2, 202)})
"""Image de la légende et vignette : observées par leur taille."""
_NOMINATIVES = frozenset({(2, 80), (2, 85), (2, 110), (2, 116), (2, 118), (2, 122)})
"""Auteur, titre de l'auteur, crédit, droits, contact, rédacteur (ADR-0119)."""

_UTF8 = b"\x1b%G"
"""Valeur de CodedCharacterSet qui déclare UTF-8 (ISO 2022)."""


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [bloc for bloc in releve.blocs if bloc.nature is Nature.PHOTOSHOP]
    trouve = False
    for bloc in blocs:
        trouve = _bloc(contexte, bloc, trouve)
    contexte.observer("iptc.present", trouve)
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _bloc(contexte: Contexte, bloc: Bloc, trouve: bool) -> bool:
    localisation = bloc.localisation()
    lues, partiel = ressources(contexte, lire_bloc(contexte, bloc))
    contexte.observer(
        "iptc.photoshop.ressources",
        [ressource.identifiant for ressource in lues],
        localisation=localisation,
    )
    for ressource in lues:
        if ressource.identifiant != IPTC_NAA:
            continue
        trouve = True
        jeux, incomplet = jeux_de_donnees(contexte, ressource.donnees)
        _jeux(contexte, bloc, jeux)
        partiel = partiel or incomplet
    if partiel:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
    return trouve


def _jeux(contexte: Contexte, bloc: Bloc, jeux: list[JeuDeDonnees]) -> None:
    utf8 = any((j.enregistrement, j.numero) == (1, 90) and j.valeur == _UTF8 for j in jeux)
    lus: dict[tuple[int, int], list[Scalaire]] = {}
    for jeu in jeux:
        lus.setdefault((jeu.enregistrement, jeu.numero), []).append(_valeur(jeu, utf8))
    localisation = bloc.localisation("IPTC-NAA")
    for cle, liste in lus.items():
        enregistrement, numero = cle
        nom = f"iptc.{NOMS.get(cle, f'{enregistrement}:{numero}')}"
        identifiante = CategorieIdentifiante.METADONNEE_NOMINATIVE if cle in _NOMINATIVES else None
        if cle in _BINAIRES:
            for taille in liste:
                contexte.observer(
                    f"{nom}.taille", taille, unite="octets", localisation=localisation
                )
            continue
        valeur = liste if cle in _REPETABLES or len(liste) > 1 else liste[0]
        valeurs.observer(
            contexte, nom, valeur, localisation=localisation, identifiante=identifiante
        )


def _valeur(jeu: JeuDeDonnees, utf8: bool) -> Scalaire:
    cle = (jeu.enregistrement, jeu.numero)
    if cle in _BINAIRES:
        return len(jeu.valeur)
    if cle in _ENTIERS and len(jeu.valeur) <= 8:
        return int.from_bytes(jeu.valeur, "big")
    if utf8:
        return jeu.valeur.decode("utf-8", "replace")
    try:
        return jeu.valeur.decode("utf-8")
    except UnicodeDecodeError:
        return jeu.valeur.decode("latin-1")
