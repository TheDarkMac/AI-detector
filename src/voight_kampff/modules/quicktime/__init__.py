"""Module ``quicktime`` : métadonnées de la boîte ``moov`` d'un M4A, d'un MP4 ou d'un MOV (F-10,
ADR-0114, ADR-0131, ADR-0132, ADR-0133 ; fiche ``metadonnees-quicktime``).

Lit, dans le premier ``moov`` (ISO/CEI 14496-12 ; Apple, QuickTime File Format) :

- les dates de ``mvhd``, telles qu'écrites, en secondes depuis 1904 :
  ``quicktime.mvhd.CreationTime``, ``quicktime.mvhd.ModificationTime`` ;
- les données d'utilisateur ``udta`` : textes QuickTime (``©nam``, ``©swr``…), boîtes de texte
  ISO et 3GPP (``cprt``, ``titl``…), sous ``quicktime.udta.<code>`` ;
- les listes ``ilst`` d'une boîte ``meta`` de ``moov`` ou de ``moov/udta`` : codes iTunes
  (``©too``, ``©ART``…) sous ``quicktime.ilst.<code>``, entrées libres ``----`` sous
  ``quicktime.ilst.----.<domaine>.<nom>``, clés QuickTime (gestionnaire ``mdta``) sous
  ``quicktime.mdta.<clé>``.

Un code est passé par la règle des composants d'ADR-0117 : ``©`` y devient un tiret
(``quicktime.ilst.-too``). Une donnée binaire (pochette, structure inconnue) est observée par sa
taille. Observe aussi ``quicktime.present`` dans tous les cas (F-14). Le paquet XMP est lu par
``xmp`` ; les métadonnées des pistes ne sont pas lues (ADR-0132).

Aucune règle « module » : les règles du catalogue lisent ces observations (T22, T23).
"""

import codecs
import struct
from collections.abc import Iterator, Sequence

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.rapport.modele import (
    CategorieIdentifiante,
    Localisation,
    RaisonNonMenee,
    Scalaire,
)

__all__ = ["analyser"]

# Codecs chargés à l'import : après les restrictions, plus rien n'est lu sur le disque, et
# Python charge un codec à sa première utilisation (ADR-0079, ERR-0009).
for _codec in ("utf-16-be", "mac_roman", "shift_jis"):
    codecs.lookup(_codec)

_DATE = "s depuis 1904-01-01 UTC"
_NOMINATIFS = frozenset(
    {
        "©ART",
        "aART",
        "©aut",
        "©wrt",
        "©com",
        "©cpy",
        "©dir",
        "©prd",
        "©PRD",
        "©prf",
        "©ope",
        "©own",
        "©enc",
        "©pub",
        "cprt",
        "ownr",
        "apID",
        "auth",
        "perf",
    }
)
"""Codes qui nomment une personne ou un organisme : artiste, auteur, compositeur, droits,
réalisateur, producteur, interprètes, propriétaire, encodeur, éditeur, compte iTunes
(ADR-0119, ADR-0133)."""
_GPS = frozenset({"©xyz", "loci"})
"""Position ISO 6709 (QuickTime), lieu 3GPP."""
_CLES_NOMINATIVES = frozenset(
    f"com.apple.quicktime.{cle}"
    for cle in ("artist", "author", "copyright", "director", "producer", "publisher")
)
_CLES_GPS = frozenset({"com.apple.quicktime.location.ISO6709"})
_TEXTES_ISO = frozenset({b"cprt", b"titl", b"dscp", b"perf", b"auth", b"gnre"})
"""Boîtes de ``udta`` : version, langue, texte terminé par un nul (ISO/CEI 14496-12, §8.10.2 ;
3GPP TS 26.244)."""
_SIGNES = frozenset({21, 65, 66, 67, 74})
_NON_SIGNES = frozenset({22, 75, 76, 77, 78})
_TEXTES = {1: "utf-8", 4: "utf-8", 2: "utf-16-be", 5: "utf-16-be", 3: "shift_jis"}
"""Types de données d'``ilst`` (QuickTime File Format, « Well-known types »)."""


class _Illisible(Exception):
    """Boîte qui ne se lit pas comme elle est déclarée."""


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [bloc for bloc in releve.blocs if bloc.nature is Nature.QUICKTIME]
    metadonnees = [bloc for bloc in blocs if bloc.chemin != "moov/mvhd"]
    contexte.observer("quicktime.present", bool(metadonnees))
    if metadonnees:
        contexte.observer("quicktime.blocs", len(metadonnees))
    for bloc in blocs:
        donnees = lire_bloc(contexte, bloc)
        try:
            if bloc.chemin == "moov/mvhd":
                _mvhd(contexte, bloc, donnees)
            elif bloc.chemin == "moov/udta":
                _udta(contexte, bloc, donnees)
            else:
                _meta(contexte, bloc, donnees, 0, len(donnees))
        except _Illisible:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _boites(
    donnees: bytes, debut: int, fin: int, *, terminal: bool = False
) -> Iterator[tuple[bytes, int, int]]:
    """Type, début et fin du contenu de chaque boîte entre ``debut`` et ``fin``."""
    position = debut
    while position + 8 <= fin:
        taille, entete = _gros(donnees[position : position + 4]), 8
        nature = donnees[position + 4 : position + 8]
        if taille == 1:
            if position + 16 > fin:
                raise _Illisible
            taille, entete = _gros(donnees[position + 8 : position + 16]), 16
        elif taille == 0:
            taille = fin - position
        if taille < entete or position + taille > fin:
            raise _Illisible
        yield nature, position + entete, position + taille
        position += taille
    if terminal and fin - position == 4 and donnees[position:fin] == b"\x00" * 4:
        return  # fin de liste de ``udta``
    if position < fin:
        raise _Illisible


def _mvhd(contexte: Contexte, bloc: Bloc, donnees: bytes) -> None:
    """Dates de création et de modification, sur 32 bits (version 0) ou 64 bits (version 1)."""
    largeur = 8 if donnees[:1] == b"\x01" else 4
    if len(donnees) < 4 + 2 * largeur:
        raise _Illisible
    localisation = bloc.localisation()
    for rang, nom in enumerate(("CreationTime", "ModificationTime")):
        debut = 4 + rang * largeur
        date = _gros(donnees[debut : debut + largeur])
        contexte.observer(
            f"quicktime.mvhd.{nom}", valeurs.entier(date), unite=_DATE, localisation=localisation
        )


def _udta(contexte: Contexte, bloc: Bloc, donnees: bytes) -> None:
    for nature, debut, fin in _boites(donnees, 0, len(donnees), terminal=True):
        contexte.compter_objets()
        code = nature.decode("latin-1")
        if nature == b"meta":
            _meta(contexte, bloc, donnees, debut, fin)
            continue
        if nature == b"XMP_":
            continue  # lu par le module ``xmp``
        localisation = bloc.localisation(code)
        nom = valeurs.borner(f"quicktime.udta.{valeurs.composant(code)}")
        contenu = donnees[debut:fin]
        try:
            if contenu[4:8] == b"data":
                _donnees(contexte, nom, code, donnees, debut, fin, localisation)
            elif nature[:1] == b"\xa9":
                _observer(contexte, nom, code, _textes_quicktime(contenu), localisation)
            elif nature in _TEXTES_ISO:
                _observer(contexte, nom, code, _texte_iso(contenu), localisation)
            else:
                _taille(contexte, nom, code, len(contenu), localisation)
        except _Illisible:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)


def _textes_quicktime(contenu: bytes) -> list[str]:
    """Textes d'une boîte ``©xxx`` de ``udta`` : longueur, langue, texte, répétés.

    Une langue inférieure à 0x400 est un code Macintosh, texte en Mac Roman ; au-delà, code
    ISO 639-2 compacté, texte en UTF-8, ou UTF-16 s'il commence par sa marque d'ordre.
    """
    textes: list[str] = []
    position = 0
    while position + 4 <= len(contenu):
        longueur = _gros(contenu[position : position + 2])
        langue = _gros(contenu[position + 2 : position + 4])
        brut = contenu[position + 4 : position + 4 + longueur]
        if len(brut) < longueur:
            raise _Illisible
        if langue < 0x400:
            textes.append(brut.decode("mac_roman"))
        elif brut.startswith(b"\xfe\xff"):
            textes.append(brut[2:].decode("utf-16-be", "replace"))
        else:
            textes.append(brut.decode("utf-8", "replace"))
        position += 4 + longueur
    if position != len(contenu):
        raise _Illisible
    return [texte.rstrip("\x00") for texte in textes]


def _texte_iso(contenu: bytes) -> list[str]:
    """Texte d'une boîte ISO ou 3GPP : quatre octets de version, langue, texte terminé par un
    nul, en UTF-8, ou en UTF-16 s'il commence par sa marque d'ordre."""
    if len(contenu) < 6:
        raise _Illisible
    brut = contenu[6:]
    if brut.startswith(b"\xfe\xff"):
        return [brut[2:].decode("utf-16-be", "replace").split("\x00", 1)[0]]
    return [brut.split(b"\x00", 1)[0].decode("utf-8", "replace")]


def _meta(contexte: Contexte, bloc: Bloc, donnees: bytes, debut: int, fin: int) -> None:
    """Boîte ``meta`` : gestionnaire, clés, liste ``ilst``.

    Dans ``udta`` (iTunes), ``meta`` porte une version et des drapeaux ; directement dans
    ``moov`` (QuickTime), non : on le reconnaît à ce que ``hdlr`` suit l'en-tête.
    """
    if donnees[debut + 4 : debut + 8] != b"hdlr":
        debut += 4
    enfants = list(_boites(donnees, debut, fin))
    gestionnaire = b"mdir"
    cles: dict[int, str] = {}
    for nature, d, f in enfants:
        if nature == b"hdlr" and f - d >= 12:
            gestionnaire = donnees[d + 8 : d + 12]
        elif nature == b"keys":
            cles = _cles(contexte, donnees, d, f)
    for nature, d, f in enfants:
        if nature == b"ilst":
            _ilst(contexte, bloc, donnees, d, f, cles if gestionnaire == b"mdta" else None)


def _cles(contexte: Contexte, donnees: bytes, debut: int, fin: int) -> dict[int, str]:
    """Clés de ``keys`` (gestionnaire ``mdta``), numérotées à partir de 1."""
    cles: dict[int, str] = {}
    for rang, (_espace, d, f) in enumerate(_boites(donnees, debut + 8, fin), start=1):
        contexte.compter_objets()
        cles[rang] = donnees[d:f].decode("utf-8", "replace")
    return cles


def _ilst(
    contexte: Contexte,
    bloc: Bloc,
    donnees: bytes,
    debut: int,
    fin: int,
    cles: dict[int, str] | None,
) -> None:
    """Éléments d'``ilst`` : nommés par leur code, ou par le rang de leur clé (``mdta``)."""
    for nature, d, f in _boites(donnees, debut, fin):
        contexte.compter_objets()
        if cles is not None:
            cle = cles.get(_gros(nature))
            localisation = bloc.localisation(f"ilst / clé {_gros(nature)}")
            if cle is None:
                contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
                continue
            nom, code = f"quicktime.mdta.{valeurs.composant(cle)}", cle
        else:
            code = nature.decode("latin-1")
            localisation = bloc.localisation(f"ilst / {code}")
            nom = f"quicktime.ilst.{valeurs.composant(code)}"
            if nature == b"----":
                nom = f"{nom}.{_libre(donnees, d, f)}"
        try:
            _donnees(contexte, valeurs.borner(nom), code, donnees, d, f, localisation)
        except _Illisible:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)


def _libre(donnees: bytes, debut: int, fin: int) -> str:
    """Domaine et nom d'une entrée libre ``----`` : boîtes ``mean`` et ``name``."""
    parties = {b"mean": "", b"name": ""}
    for nature, d, f in _boites(donnees, debut, fin):
        if nature in parties and f - d >= 4:
            parties[nature] = donnees[d + 4 : f].decode("utf-8", "replace")
    return ".".join(valeurs.composant(partie) for partie in parties.values())


def _donnees(
    contexte: Contexte,
    nom: str,
    code: str,
    donnees: bytes,
    debut: int,
    fin: int,
    localisation: Localisation,
) -> None:
    """Boîtes ``data`` d'un élément : type sur quatre octets, langue, valeur."""
    scalaires: list[Scalaire] = []
    binaire = 0
    for nature, d, f in _boites(donnees, debut, fin):
        if nature != b"data":
            continue
        if f - d < 8:
            raise _Illisible
        type_, valeur = _gros(donnees[d + 1 : d + 4]), donnees[d + 8 : f]
        scalaire = _valeur(type_, valeur)
        if scalaire is None:
            binaire += len(valeur)
        else:
            scalaires.append(scalaire)
    _observer(contexte, nom, code, scalaires, localisation)
    if binaire:
        _taille(contexte, nom, code, binaire, localisation)


def _valeur(type_: int, valeur: bytes) -> Scalaire | None:
    """Texte, entier ou réel ; ``None`` pour une donnée binaire (image, type implicite)."""
    if type_ in _TEXTES:
        return valeur.decode(_TEXTES[type_], "replace")
    if 1 <= len(valeur) <= 8 and type_ in _SIGNES | _NON_SIGNES:
        return valeurs.entier(int.from_bytes(valeur, "big", signed=type_ in _SIGNES))
    if type_ == 23 and len(valeur) == 4:
        return valeurs.nombre(struct.unpack(">f", valeur)[0])
    if type_ == 24 and len(valeur) == 8:
        return valeurs.nombre(struct.unpack(">d", valeur)[0])
    return None


def _observer(
    contexte: Contexte,
    nom: str,
    code: str,
    scalaires: Sequence[Scalaire],
    localisation: Localisation,
) -> None:
    gardes = [s for s in scalaires if s != ""]
    if not gardes:
        return
    valeurs.observer(
        contexte,
        nom,
        gardes[0] if len(gardes) == 1 else gardes,
        localisation=localisation,
        identifiante=_identifiante(code),
    )


def _taille(
    contexte: Contexte, nom: str, code: str, taille: int, localisation: Localisation
) -> None:
    contexte.observer(
        f"{nom}.taille",
        taille,
        unite="octets",
        localisation=localisation,
        identifiante=_identifiante(code),
    )


def _identifiante(code: str) -> CategorieIdentifiante | None:
    if code in _NOMINATIFS or code in _CLES_NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if code in _GPS or code in _CLES_GPS:
        return CategorieIdentifiante.GPS
    return None


def _gros(octets: bytes) -> int:
    return int.from_bytes(octets, "big")
