"""Module ``id3`` : balises ID3 d'un MP3, d'un AAC, d'un FLAC ou d'un WAV (F-10, ADR-0114,
ADR-0131, ADR-0132, ADR-0133 ; fiche ``metadonnees-id3``).

Lit chaque balise ID3v2 (versions 2.2, 2.3 et 2.4) : en tête d'un MP3, d'un AAC ou d'un FLAC,
dans le bloc ``id3 `` d'un WAV ; et la balise ID3v1 en fin d'un MP3. Chaque trame est observée
sous ``id3.<identifiant>`` (``id3.TIT2``, ``id3.TSSE``…), une trame de texte libre sous
``id3.TXXX.<description>``, un commentaire sous ``id3.COMM[.<description>]`` ; une trame
binaire (image, objet, données privées) par sa seule taille. La balise ID3v1 donne
``id3.v1.<champ>``. Observe aussi ``id3.present`` dans tous les cas (F-14).

Désynchronisation et compression des trames sont défaites ; une trame chiffrée n'est pas lue.
Aucune règle « module » : les règles du catalogue lisent ces observations (T22, T23).
"""

import codecs
import zlib

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.rapport.modele import CategorieIdentifiante, Localisation, RaisonNonMenee

__all__ = ["analyser"]

# Codecs chargés à l'import : après les restrictions, plus rien n'est lu sur le disque, et
# Python charge un codec à sa première utilisation (ADR-0079, ERR-0009).
for _codec in ("utf-16-le", "utf-16-be"):
    codecs.lookup(_codec)

_NOMINATIVES = frozenset(
    {
        # ID3v2.3 et v2.4
        "TPE1",
        "TPE2",
        "TPE3",
        "TPE4",
        "TCOM",
        "TEXT",
        "TOLY",
        "TOPE",
        "TENC",
        "TCOP",
        "TOWN",
        "TPUB",
        "TIPL",
        "TMCL",
        "IPLS",
        # ID3v2.2
        "TP1",
        "TP2",
        "TP3",
        "TP4",
        "TCM",
        "TXT",
        "TOL",
        "TOA",
        "TEN",
        "TCR",
        "TPB",
        "IPL",
    }
)
"""Trames qui nomment une personne ou un organisme : interprètes, auteurs, encodeur, ayants
droit, propriétaire, éditeur (ADR-0119, ADR-0133)."""
_FICHIERS = frozenset({"TOFN", "TOF"})
"""Nom du fichier d'origine."""
_TEXTES_LIBRES = frozenset(
    {
        # ID3v2.3 et v2.4
        "TIT1",
        "TIT2",
        "TIT3",
        "TALB",
        "TOAL",
        "TSST",
        "TXXX",
        "COMM",
        "USLT",
        # ID3v2.2
        "TT1",
        "TT2",
        "TT3",
        "TAL",
        "TOT",
        "TXX",
        "COM",
        "ULT",
    }
)
"""Titres, album, sous-titre, textes libres, commentaires, paroles (ADR-0160)."""
_V1_IDENTIFIANTES = {
    "id3.v1.Artist": CategorieIdentifiante.METADONNEE_NOMINATIVE,
    "id3.v1.Title": CategorieIdentifiante.TEXTE_LIBRE,
    "id3.v1.Album": CategorieIdentifiante.TEXTE_LIBRE,
    "id3.v1.Comment": CategorieIdentifiante.TEXTE_LIBRE,
}
_TEXTES = frozenset({"IPLS", "IPL"})
"""Trames de texte dont l'identifiant ne commence pas par ``T``."""
_DECRITS = frozenset({"TXXX", "TXX", "WXXX", "WXX"})
"""Texte ou adresse libres, nommés par leur description."""
_COMMENTAIRES = frozenset({"COMM", "COM", "USLT", "ULT"})
"""Langue, description, texte."""
_ENCODAGES = {0: "latin-1", 3: "utf-8"}
_V1 = (("Title", 3, 33), ("Artist", 33, 63), ("Album", 63, 93), ("Year", 93, 97))


class _Illisible(Exception):
    """Trame ou balise qui ne se lit pas comme elle est déclarée."""


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    balises = [b for b in releve.blocs if b.nature in (Nature.ID3V2, Nature.ID3V1)]
    contexte.observer("id3.present", bool(balises))
    if balises:
        contexte.observer("id3.blocs", len(balises))
    for bloc in balises:
        if bloc.nature is Nature.ID3V1:
            _v1(contexte, bloc)
        else:
            _v2(contexte, bloc)
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _v1(contexte: Contexte, bloc: Bloc) -> None:
    """Balise ID3v1 ou v1.1 : champs de taille fixe, Latin-1, complétés par des nuls."""
    donnees = lire_bloc(contexte, bloc)
    localisation = bloc.localisation()
    for nom, debut, fin in _V1:
        _v1_texte(contexte, f"id3.v1.{nom}", donnees[debut:fin], localisation)
    commentaire = donnees[97:127]
    if commentaire[28] == 0 and commentaire[29]:  # v1.1 : numéro de piste
        _v1_texte(contexte, "id3.v1.Comment", commentaire[:28], localisation)
        contexte.observer("id3.v1.Track", commentaire[29], localisation=localisation)
    else:
        _v1_texte(contexte, "id3.v1.Comment", commentaire, localisation)
    if donnees[127] != 255:  # 255 : aucun genre
        contexte.observer("id3.v1.Genre", donnees[127], localisation=localisation)


def _v1_texte(contexte: Contexte, nom: str, octets: bytes, localisation: Localisation) -> None:
    texte = octets.split(b"\x00", 1)[0].decode("latin-1").rstrip(" ")
    if texte:
        identifiante = _V1_IDENTIFIANTES.get(nom)
        contexte.observer(nom, texte, localisation=localisation, identifiante=identifiante)


def _v2(contexte: Contexte, bloc: Bloc) -> None:
    donnees = lire_bloc(contexte, bloc)
    version, revision, drapeaux = donnees[3], donnees[4], donnees[5]
    contexte.observer("id3.version", f"2.{version}.{revision}", localisation=bloc.localisation())
    corps = donnees[10 : 10 + _syncsafe(donnees[6:10])]
    if version == 2 and drapeaux & 0x40:
        # Compression de la v2.2 : aucune méthode n'a été définie.
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())
        return
    desynchronisee = bool(drapeaux & 0x80)
    if desynchronisee and version < 4:
        corps = _resynchroniser(corps)  # balise entière ; en v2.4, trame par trame
    position = 0
    try:
        if version > 2 and drapeaux & 0x40:  # en-tête étendu
            taille = int.from_bytes(corps[:4], "big")
            position = _syncsafe(corps[:4]) if version == 4 else 4 + taille
            if len(corps) < 4 or position > len(corps):
                raise _Illisible
        _trames(contexte, bloc, corps, position, version, desynchronisee)
    except _Illisible:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())


def _trames(
    contexte: Contexte,
    bloc: Bloc,
    corps: bytes,
    position: int,
    version: int,
    desynchronisee: bool,
) -> None:
    """Trames du corps, jusqu'au bourrage ou à la fin ; une trame mal formée arrête la lecture."""
    longueur_id, longueur_entete = (3, 6) if version == 2 else (4, 10)
    while position + longueur_entete <= len(corps) and corps[position] != 0:
        contexte.compter_objets()
        brut = corps[position : position + longueur_id]
        if not all(0x30 <= c <= 0x39 or 0x41 <= c <= 0x5A for c in brut):
            raise _Illisible
        identifiant = brut.decode("ascii")
        octets_taille = corps[position + longueur_id : position + 2 * longueur_id]
        if version == 4:
            if any(octet & 0x80 for octet in octets_taille):
                raise _Illisible
            taille = _syncsafe(octets_taille)
        else:
            taille = int.from_bytes(octets_taille, "big")
        debut = position + longueur_entete
        if debut + taille > len(corps):
            raise _Illisible
        format_ = corps[position + 9] if version > 2 else 0
        localisation = bloc.localisation(f"trame {identifiant}")
        try:
            donnees = _contenu(
                contexte, corps[debut : debut + taille], version, format_, desynchronisee
            )
        except _Illisible:
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
        else:
            _trame(contexte, identifiant, donnees, localisation)
        position = debut + taille


def _contenu(
    contexte: Contexte, donnees: bytes, version: int, format_: int, desynchronisee: bool
) -> bytes:
    """Données d'une trame, une fois défaits désynchronisation et compression.

    v2.3 : compression ``0x80`` (taille décompressée sur quatre octets), chiffrement ``0x40``,
    groupe ``0x20`` ; v2.4 : groupe ``0x40``, compression ``0x08``, chiffrement ``0x04``,
    désynchronisation ``0x02``, longueur des données ``0x01``.
    """
    if version == 3:
        compressee, chiffree = format_ & 0x80, format_ & 0x40
        extra = (4 if compressee else 0) + (1 if chiffree else 0) + (1 if format_ & 0x20 else 0)
    elif version == 4:
        compressee, chiffree = format_ & 0x08, format_ & 0x04
        extra = sum(n for drapeau, n in ((0x40, 1), (0x04, 1), (0x01, 4)) if format_ & drapeau)
        if desynchronisee or format_ & 0x02:
            donnees = donnees[:extra] + _resynchroniser(donnees[extra:])
    else:
        return donnees
    if chiffree or extra > len(donnees):
        raise _Illisible
    donnees = donnees[extra:]
    if compressee:
        try:
            return contexte.decompresser(donnees, "zlib")
        except zlib.error:
            raise _Illisible from None
    return donnees


def _trame(
    contexte: Contexte, identifiant: str, donnees: bytes, localisation: Localisation
) -> None:
    nom = f"id3.{identifiant}"
    if identifiant in _DECRITS:
        description, valeur = _description(donnees, adresse=identifiant.startswith("W"))
        if description:
            nom = f"{nom}.{valeurs.composant(description)}"
        _observer(contexte, identifiant, nom, valeur, localisation)
    elif identifiant in _COMMENTAIRES:
        if len(donnees) < 4:
            raise _Illisible
        encodage = _encodage(donnees[0])
        description, *textes = _champs(donnees[4:], encodage) or [""]
        if description:
            nom = f"{nom}.{valeurs.composant(description)}"
        _observer(contexte, identifiant, nom, [t for t in textes if t], localisation)
    elif identifiant.startswith("T") or identifiant in _TEXTES:
        if not donnees:
            return
        champs = _champs(donnees[1:], _encodage(donnees[0]))
        _observer(contexte, identifiant, nom, [c for c in champs if c], localisation)
    elif identifiant.startswith("W"):
        adresse = _latin(donnees)
        _observer(contexte, identifiant, nom, [adresse] if adresse else [], localisation)
    else:
        valeurs.observer(
            contexte,
            f"{nom}.taille",
            len(donnees),
            unite="octets",
            localisation=localisation,
            identifiante=_identifiante(identifiant),
        )


def _observer(
    contexte: Contexte,
    identifiant: str,
    nom: str,
    textes: list[str],
    localisation: Localisation,
) -> None:
    """Un texte, ou une liste s'il y en a plusieurs ; rien si la trame est vide."""
    if not textes:
        return
    valeurs.observer(
        contexte,
        valeurs.borner(nom),
        textes[0] if len(textes) == 1 else textes,
        localisation=localisation,
        identifiante=_identifiante(identifiant),
    )


def _identifiante(identifiant: str) -> CategorieIdentifiante | None:
    if identifiant in _NOMINATIVES:
        return CategorieIdentifiante.METADONNEE_NOMINATIVE
    if identifiant in _FICHIERS:
        return CategorieIdentifiante.NOM_DE_FICHIER
    if identifiant in _TEXTES_LIBRES:
        return CategorieIdentifiante.TEXTE_LIBRE
    return None


def _description(donnees: bytes, *, adresse: bool) -> tuple[str, list[str]]:
    """``TXXX`` : description et textes ; ``WXXX`` : description et adresse en Latin-1."""
    if not donnees:
        raise _Illisible
    encodage = _encodage(donnees[0])
    if not adresse:
        description, *textes = _champs(donnees[1:], encodage) or [""]
        return description, [t for t in textes if t]
    fin = _terminaison(donnees, 1, encodage)
    description = _decoder(donnees[1:fin], encodage)
    debut = fin + (2 if encodage.startswith("utf-16") else 1)
    adresse_ = _latin(donnees[debut:])
    return description, [adresse_] if adresse_ else []


def _encodage(octet: int) -> str:
    """0 Latin-1, 1 UTF-16 avec marque d'ordre, 2 UTF-16BE, 3 UTF-8 ; un autre code est
    illisible."""
    if octet in _ENCODAGES:
        return _ENCODAGES[octet]
    if octet == 1:
        return "utf-16"
    if octet == 2:
        return "utf-16-be"
    raise _Illisible


def _terminaison(donnees: bytes, debut: int, encodage: str) -> int:
    """Position de la terminaison qui suit ``debut``, ou la fin des données."""
    if not encodage.startswith("utf-16"):
        fin = donnees.find(b"\x00", debut)
        return len(donnees) if fin == -1 else fin
    for position in range(debut, len(donnees) - 1, 2):
        if donnees[position] == 0 and donnees[position + 1] == 0:
            return position
    return len(donnees)


def _champs(donnees: bytes, encodage: str) -> list[str]:
    """Textes séparés par des terminaisons ; la dernière, si elle termine les données, n'en
    ouvre pas un nouveau."""
    champs: list[str] = []
    largeur = 2 if encodage.startswith("utf-16") else 1
    position = 0
    while position < len(donnees):
        fin = _terminaison(donnees, position, encodage)
        champs.append(_decoder(donnees[position:fin], encodage))
        position = fin + largeur
    return champs


def _decoder(octets: bytes, encodage: str) -> str:
    """Texte dans l'encodage de la trame ; un octet invalide devient le caractère de
    remplacement (ADR-0118). UTF-16 sans marque d'ordre est lu petit-boutiste."""
    if encodage == "utf-16":
        if octets.startswith(b"\xfe\xff"):
            return octets[2:].decode("utf-16-be", "replace")
        if octets.startswith(b"\xff\xfe"):
            octets = octets[2:]
        return octets.decode("utf-16-le", "replace")
    return octets.decode(encodage, "replace")


def _latin(octets: bytes) -> str:
    return octets.split(b"\x00", 1)[0].decode("latin-1")


def _syncsafe(octets: bytes) -> int:
    """Entier de quatre octets dont seuls les sept bits de poids faible comptent."""
    return sum((octet & 0x7F) << (7 * (len(octets) - 1 - i)) for i, octet in enumerate(octets))


def _resynchroniser(octets: bytes) -> bytes:
    """Défait la désynchronisation : chaque ``FF 00`` redevient ``FF`` (v2.4, §6.1)."""
    return octets.replace(b"\xff\x00", b"\xff")
