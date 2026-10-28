"""Module ``exif`` : métadonnées EXIF d'une image (F-10, ADR-0114 ; fiche ``metadonnees-exif``).

Lit chaque bloc EXIF de la partie (segment APP1 d'un JPEG, bloc ``eXIf`` d'un PNG, bloc ``EXIF``
d'un WebP, élément ``Exif`` d'un HEIC) et observe chaque étiquette de chaque répertoire, sous le
nom ``exif.<répertoire>.<étiquette>`` (ADR-0117). Observe aussi ``exif.present`` dans tous les
cas : une absence est une observation, jamais un constat (F-14, ADR-0058).

Aucune règle : ce module extrait, il n'interprète pas. Les règles qui lisent ses observations
viennent avec T22 et T23.
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.modules._lecture.tiff import Entree, Tiff, nombres
from voight_kampff.modules.exif import etiquettes
from voight_kampff.rapport.modele import (
    NOMBRE_MAX_ELEMENTS,
    CategorieIdentifiante,
    RaisonNonMenee,
    Scalaire,
)

__all__ = ["analyser"]

_VERSIONS = frozenset({("exif", 0x9000), ("exif", 0xA000), ("interop", 0x0002)})
"""Versions écrites en quatre caractères dans des octets indéfinis."""
_COMMENTAIRES = frozenset({("exif", 0x9286), ("gps", 0x001B), ("gps", 0x001C)})
"""Textes précédés d'un code de jeu de caractères de huit octets (EXIF 3.0)."""
_OCTETS = frozenset({("exif", 0x9101), ("exif", 0xA300), ("exif", 0xA301)})
"""Octets indéfinis qui sont des nombres."""
_BINAIRES = frozenset(
    {
        ("tiff", 0x02BC),  # XMLPacket
        ("tiff", 0x83BB),  # IPTC-NAA
        ("tiff", 0x8649),  # PhotoshopSettings
        ("tiff", 0x8773),  # InterColorProfile
        ("tiff", 0xC4A5),  # PrintImageMatching
        ("tiff", 0xEA1C),  # Padding
        ("exif", 0x927C),  # MakerNote
        ("exif", 0xEA1C),  # Padding
    }
)
"""Données binaires ou d'un autre format, observées par leur taille seulement (ADR-0118)."""


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [bloc for bloc in releve.blocs if bloc.nature is Nature.EXIF]
    contexte.observer("exif.present", bool(blocs))
    if blocs:
        contexte.observer("exif.blocs", len(blocs))
    for bloc in blocs:
        _bloc(contexte, bloc)
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _bloc(contexte: Contexte, bloc: Bloc) -> None:
    donnees = lire_bloc(contexte, bloc)
    if bloc.chemin.startswith("élément"):
        # HEIC : quatre octets donnent la position de l'en-tête TIFF (ISO/CEI 23008-12).
        decalage = int.from_bytes(donnees[:4], "big") if len(donnees) >= 4 else len(donnees)
        donnees = donnees[4 + decalage :]
    tiff = Tiff(contexte, donnees)
    if tiff.ordre:
        contexte.observer("exif.ordre", tiff.ordre, localisation=bloc.localisation())
    for entree in tiff.entrees():
        _entree(contexte, bloc, entree)
    if tiff.partiel:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())


def _entree(contexte: Contexte, bloc: Bloc, entree: Entree) -> None:
    table = etiquettes.table(entree.repertoire)
    cle = (table, entree.etiquette)
    nom = f"exif.{entree.repertoire}.{etiquettes.nom(entree.repertoire, entree.etiquette)}"
    identifiante = (
        CategorieIdentifiante.GPS if table == "gps" else etiquettes.IDENTIFIANTES.get(cle)
    )
    localisation = bloc.localisation(entree.repertoire)
    if cle in _BINAIRES or (entree.type == 7 and cle not in _VERSIONS | _COMMENTAIRES | _OCTETS):
        contexte.observer(
            f"{nom}.taille",
            len(entree.brut),
            unite="octets",
            localisation=localisation,
            identifiante=identifiante,
        )
        return
    valeur: Scalaire | list[Scalaire]
    if entree.etiquette in etiquettes.TEXTES_UTF16 and table == "tiff":
        valeur = bytes(entree.brut).decode("utf-16-le", "replace").rstrip("\x00")
    elif entree.type == 2 or cle in _VERSIONS:
        valeur = _texte(bytes(entree.brut).split(b"\x00", 1)[0])
    elif entree.type == 129:
        valeur = bytes(entree.brut).decode("utf-8", "replace").rstrip("\x00")
    elif cle in _COMMENTAIRES:
        valeur = _commentaire(entree)
    else:
        lus = [_nombre(n) for n in nombres(entree, NOMBRE_MAX_ELEMENTS + 1)]
        valeur = lus[0] if entree.compte == 1 else lus
        if not lus:
            valeur = []
    if isinstance(valeur, list):
        valeurs.observer(
            contexte,
            nom,
            valeur,
            localisation=localisation,
            identifiante=identifiante,
            total=entree.compte,
        )
    else:
        valeurs.observer(
            contexte, nom, valeur, localisation=localisation, identifiante=identifiante
        )


def _texte(octets: bytes) -> str:
    """UTF-8 s'il est valide, Latin-1 sinon : aucun octet n'est perdu."""
    try:
        return octets.decode("utf-8")
    except UnicodeDecodeError:
        return octets.decode("latin-1")


def _commentaire(entree: Entree) -> str:
    code, corps = bytes(entree.brut[:8]), bytes(entree.brut[8:])
    if code.startswith(b"UNICODE"):
        texte = corps.decode("utf-16-le" if entree.ordre == "<" else "utf-16-be", "replace")
    elif code.startswith(b"JIS"):
        texte = corps.decode("shift_jis", "replace")
    else:
        texte = _texte(corps)
    return texte.rstrip("\x00 ")


def _nombre(valeur: int | float | tuple[int, int]) -> Scalaire:
    if isinstance(valeur, tuple):
        numerateur, denominateur = valeur
        if denominateur == 0:
            return f"{numerateur}/{denominateur}"
        return valeurs.nombre(numerateur / denominateur)
    if isinstance(valeur, float):
        return valeurs.nombre(valeur)
    return valeur
