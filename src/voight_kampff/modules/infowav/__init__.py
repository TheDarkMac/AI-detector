"""Module ``infowav`` : liste ``INFO`` et bloc ``bext`` d'un WAV (F-10, ADR-0114, ADR-0131,
ADR-0132, ADR-0133 ; fiche ``metadonnees-info-wav``).

Lit chaque sous-bloc d'une liste ``LIST`` de type ``INFO`` (Microsoft RIFF, 1991) et l'observe
sous ``infowav.<identifiant>`` (``infowav.ISFT``, ``infowav.INAM``…) ; puis les champs du bloc
``bext`` d'un WAV de diffusion (EBU Tech 3285), sous ``infowav.bext.<champ>``. Observe aussi
``infowav.present`` dans tous les cas (F-14). Les balises ID3 d'un WAV sont lues par ``id3``,
son paquet XMP par ``xmp``.

Aucune règle : T22 et T23 lisent ces observations.
"""

from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.conteneurs import Bloc, Nature, lire_bloc, relever
from voight_kampff.rapport.modele import CategorieIdentifiante, RaisonNonMenee

__all__ = ["analyser"]

_NOMINATIVES = frozenset(
    {"IART", "ICMS", "ICOP", "IENG", "ITCH", "IMUS", "IPRO", "ISTR", "IWRI", "IEDT"}
)
"""Artiste, commanditaire, droits, ingénieur, technicien (RIFF, 1991) ; compositeur,
producteur, interprètes, auteur, monteur (extensions usuelles) : ADR-0119, ADR-0133."""
_BEXT = (
    ("Description", 0, 256),
    ("Originator", 256, 288),
    ("OriginatorReference", 288, 320),
    ("OriginationDate", 320, 330),
    ("OriginationTime", 330, 338),
)
"""Champs de texte du bloc ``bext`` : nom, début, fin (EBU Tech 3285)."""
_BEXT_IDENTIFIANTS = {
    "Originator": CategorieIdentifiante.METADONNEE_NOMINATIVE,
    "OriginatorReference": CategorieIdentifiante.NUMERO_DE_SERIE,
    "UMID": CategorieIdentifiante.NUMERO_DE_SERIE,
}
"""``OriginatorReference`` (EBU R 99) et ``UMID`` (SMPTE 330M) portent le numéro de série de
l'appareil."""
_HISTORIQUE = 602
"""Début de ``CodingHistory``, après les champs fixes et les 180 octets réservés."""


def analyser(contexte: Contexte) -> None:
    releve = relever(contexte)
    blocs = [b for b in releve.blocs if b.nature in (Nature.INFO_RIFF, Nature.BEXT)]
    contexte.observer("infowav.present", bool(blocs))
    if blocs:
        contexte.observer("infowav.blocs", len(blocs))
    for bloc in blocs:
        if bloc.nature is Nature.INFO_RIFF:
            _info(contexte, bloc)
        else:
            _bext(contexte, bloc)
    if releve.arret is not None:
        contexte.non_mener(releve.arret, localisation=releve.localisation_arret())


def _info(contexte: Contexte, bloc: Bloc) -> None:
    """Sous-blocs : identifiant de quatre octets, longueur, texte terminé par un nul."""
    donnees = lire_bloc(contexte, bloc)
    position = 0
    while position + 8 <= len(donnees):
        contexte.compter_objets()
        identifiant = donnees[position : position + 4].decode("latin-1")
        longueur = int.from_bytes(donnees[position + 4 : position + 8], "little")
        debut = position + 8
        localisation = bloc.localisation(identifiant)
        if debut + longueur > len(donnees):
            contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
            return
        texte = valeurs.texte(donnees[debut : debut + longueur].split(b"\x00", 1)[0])
        if texte:
            valeurs.observer(
                contexte,
                f"infowav.{valeurs.composant(identifiant)}",
                texte,
                localisation=localisation,
                identifiante=(
                    CategorieIdentifiante.METADONNEE_NOMINATIVE
                    if identifiant in _NOMINATIVES
                    else None
                ),
            )
        position = debut + longueur + (longueur & 1)
    if position < len(donnees):
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=bloc.localisation())


def _bext(contexte: Contexte, bloc: Bloc) -> None:
    """Champs du bloc ``bext`` : textes ASCII de taille fixe, référence temporelle, version,
    UMID (version 1 et suivantes), historique de codage."""
    donnees = lire_bloc(contexte, bloc)
    localisation = bloc.localisation()
    if len(donnees) < _HISTORIQUE:
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=localisation)
        return
    for nom, debut, fin in _BEXT:
        _texte(contexte, bloc, nom, donnees[debut:fin])
    reference = int.from_bytes(donnees[338:346], "little")
    contexte.observer(
        "infowav.bext.TimeReference",
        valeurs.entier(reference),
        unite="échantillons",
        localisation=localisation,
    )
    version = int.from_bytes(donnees[346:348], "little")
    contexte.observer("infowav.bext.Version", version, localisation=localisation)
    umid = donnees[348:412]
    if version >= 1 and any(umid):
        contexte.observer(
            "infowav.bext.UMID",
            umid.rstrip(b"\x00").hex().upper(),
            localisation=localisation,
            identifiante=_BEXT_IDENTIFIANTS["UMID"],
        )
    _texte(contexte, bloc, "CodingHistory", donnees[_HISTORIQUE:])


def _texte(contexte: Contexte, bloc: Bloc, nom: str, octets: bytes) -> None:
    texte = valeurs.texte(octets.split(b"\x00", 1)[0])
    if texte:
        valeurs.observer(
            contexte,
            f"infowav.bext.{nom}",
            texte,
            localisation=bloc.localisation(),
            identifiante=_BEXT_IDENTIFIANTS.get(nom),
        )
