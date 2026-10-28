"""Module ``xmp`` : métadonnées XMP d'une image (F-10, ES-05, ADR-0114 ; fiche
``metadonnees-xmp``).

Lit chaque paquet XMP de la partie (segment APP1 d'un JPEG et ses morceaux étendus, bloc ``iTXt``
``XML:com.adobe.xmp`` d'un PNG, bloc ``XMP`` d'un WebP, élément XMP d'un HEIC). Chaque propriété
est observée sous le nom ``xmp.<préfixe>:<propriété>``, les champs d'une structure à la suite,
séparés par un point (ADR-0117). Observe aussi ``xmp.present`` dans tous les cas (F-14).

Le XML est lu sans DTD par expat (ADR-0116). Aucune règle : T22 et T23 lisent ces observations.
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import (
    Bloc,
    Nature,
    lire_bloc,
    relever,
    texte_png,
)
from voight_kampff.modules._lecture.xmp import Propriete, Xmp, lire_xmp
from voight_kampff.rapport.modele import CategorieIdentifiante, RaisonNonMenee

__all__ = ["analyser"]

_ETENDU = "xmpNote:HasExtendedXMP"
"""Propriété du paquet principal qui désigne, par son GUID, le paquet étendu (XMP, partie 3)."""

_NOMINATIVES = frozenset(
    {
        "dc:creator",
        "dc:rights",
        "dc:contributor",
        "dc:publisher",
        "xmpRights:Owner",
        "photoshop:AuthorsPosition",
        "photoshop:CaptionWriter",
        "photoshop:Credit",
        "Iptc4xmpCore:CreatorContactInfo",
        "Iptc4xmpExt:PersonInImage",
        "Iptc4xmpExt:AOCreator",
        "plus:Licensor",
        "plus:CopyrightOwner",
        "plus:ImageCreator",
        "plus:ImageSupplier",
        "aux:OwnerName",
        "exifEX:CameraOwnerName",
        "exifEX:Photographer",
        "exifEX:ImageEditor",
        "tiff:Artist",
        "tiff:Copyright",
        "mwg-rs:Name",
    }
)
_SERIES = frozenset(
    {
        "aux:SerialNumber",
        "aux:LensSerialNumber",
        "exifEX:BodySerialNumber",
        "exifEX:LensSerialNumber",
        "exif:ImageUniqueID",
        "exifEX:ImageUniqueID",
    }
)
_FICHIERS = frozenset(
    {"stRef:filePath", "xmpMM:PreservedFileName", "crs:RawFileName", "exif:RelatedSoundFile"}
)
_GPS = ("exif:GPS", "exifEX:GPS", "Iptc4xmpExt:GPS")


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    paquets = [bloc for bloc in releve.blocs if bloc.nature is Nature.XMP]
    morceaux = [bloc for bloc in releve.blocs if bloc.nature is Nature.XMP_ETENDU]
    contexte.observer("xmp.present", bool(paquets))
    if paquets:
        contexte.observer("xmp.blocs", len(paquets))
    attendus: list[str] = []
    for bloc in paquets:
        donnees = _paquet(contexte, bloc)
        if donnees is None:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())
            continue
        xmp = lire_xmp(contexte, donnees)
        _observer(contexte, bloc, xmp)
        attendus.extend(v for p in xmp.proprietes if p.nom == _ETENDU for v in p.valeurs)
    if morceaux:
        contexte.observer("xmp.etendu.blocs", len(morceaux))
        _etendus(contexte, morceaux, attendus)
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _paquet(contexte: Contexte, bloc: Bloc) -> bytes | str | None:
    if bloc.chemin != "iTXt":
        return lire_bloc(contexte, bloc)
    return texte_png(contexte, bloc).texte


def _observer(contexte: Contexte, bloc: Bloc, xmp: Xmp) -> None:
    localisation = bloc.localisation()
    for rang, adresse in enumerate(xmp.inconnus, start=1):
        valeurs.observer(contexte, f"xmp.espace.ns{rang}", adresse, localisation=localisation)
    for propriete in xmp.proprietes:
        valeurs.observer(
            contexte,
            valeurs.borner(f"xmp.{propriete.nom}"),
            list(propriete.valeurs) if propriete.tableau else propriete.valeurs[0],
            localisation=localisation,
            identifiante=_identifiante(propriete),
        )
    if xmp.partiel:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)


def _identifiante(propriete: Propriete) -> CategorieIdentifiante | None:
    """Catégorie du premier composant identifiant du chemin (ADR-0119)."""
    for composant in propriete.composants:
        if composant in _NOMINATIVES:
            return CategorieIdentifiante.METADONNEE_NOMINATIVE
        if composant in _SERIES:
            return CategorieIdentifiante.NUMERO_DE_SERIE
        if composant in _FICHIERS:
            return CategorieIdentifiante.NOM_DE_FICHIER
        if composant.startswith(_GPS):
            return CategorieIdentifiante.GPS
    return None


def _etendus(contexte: Contexte, morceaux: list[Bloc], attendus: list[str]) -> None:
    """Paquets étendus d'un JPEG, réassemblés par GUID (XMP, partie 3).

    Seul un paquet complet que le paquet principal désigne est lu, comme le prévoit la norme ;
    les autres morceaux sont non menés.
    """
    paquets: dict[str, tuple[int, list[tuple[int, bytes]], Bloc]] = {}
    ecartes: list[Bloc] = []
    for bloc in morceaux:
        donnees = lire_bloc(contexte, bloc)
        guid = donnees[:32].decode("latin-1")
        total = int.from_bytes(donnees[32:36], "big")
        position = int.from_bytes(donnees[36:40], "big")
        contenu = donnees[40:]
        connu = paquets.setdefault(guid, (total, [], bloc))
        if len(donnees) < 40 or position + len(contenu) > total or connu[0] != total:
            ecartes.append(bloc)
            continue
        connu[1].append((position, contenu))
    for guid, (total, parts, premier) in paquets.items():
        if guid not in attendus or not _couvert(parts, total):
            ecartes.append(premier)
            continue
        # Assemblé seulement une fois couvert : la taille ne dépasse pas les octets lus.
        paquet = bytearray(total)
        for position, contenu in parts:
            paquet[position : position + len(contenu)] = contenu
        _observer(contexte, premier, lire_xmp(contexte, bytes(paquet)))
    for bloc in ecartes:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())


def _couvert(parts: list[tuple[int, bytes]], total: int) -> bool:
    """Vrai si les morceaux couvrent les ``total`` octets du paquet sans trou."""
    atteint = 0
    for debut, contenu in sorted(parts, key=lambda part: part[0]):
        if debut > atteint:
            return False
        atteint = max(atteint, debut + len(contenu))
    return atteint >= total
