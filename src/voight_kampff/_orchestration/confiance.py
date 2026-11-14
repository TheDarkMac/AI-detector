"""Liste de confiance C2PA : lecture, validation, empreinte (ES-09, ADR-0165, ADR-0171).

La liste est un dossier, et rien d'autre que ces fichiers :

    confiance.toml      en-tête : format, nom, version, date, description, source, licence
    signataires.pem     ancres des signataires de manifestes, au format publié par la C2PA
    horodatage.pem      ancres des autorités d'horodatage ; facultatif

La liste livrée est dans le paquet (``donnees/confiance``) : la C2PA Trust List et la C2PA TSA
Trust List, recopiées sans modification. L'utilisateur peut en fournir une autre, qui la
remplace en entier et que le rapport signale, comme un catalogue (ADR-0086). Le processus
principal lit chaque fichier une fois, calcule l'empreinte comme celle du catalogue (ADR-0088),
valide l'en-tête par son schéma et la forme de chaque fichier PEM. Les certificats eux-mêmes ne
sont décodés que par la bibliothèque C2PA, dans le processus de travail (ADR-0164) : ici, un
bloc PEM doit seulement être du base64 d'une structure DER. Une liste invalide arrête tout avant
la lecture d'un fichier à analyser, avec un message explicite.
"""

import binascii
import os
import tomllib
from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

from voight_kampff import schemas
from voight_kampff._limites import CERTIFICATS_MAX, TAILLE_MAX_CONFIANCE
from voight_kampff._orchestration.catalogue import empreinte
from voight_kampff.rapport.modele import VersionConfiance

__all__ = [
    "ENTETE",
    "HORODATAGE",
    "SIGNATAIRES",
    "ConfianceInvalide",
    "ListeDeConfiance",
    "charger",
    "livree",
]

ENTETE = "confiance.toml"
SIGNATAIRES = "signataires.pem"
HORODATAGE = "horodatage.pem"
_FICHIERS = frozenset({ENTETE, SIGNATAIRES, HORODATAGE})
_DEBUT = "-----BEGIN CERTIFICATE-----"
_FIN = "-----END CERTIFICATE-----"
_BASE64 = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
_IMPRIMABLES = frozenset(chr(code) for code in range(0x20, 0x7F)) | {"\t"}
_TROP_GRANDE = f"liste de confiance : plus de {TAILLE_MAX_CONFIANCE >> 20} Mio"


class ConfianceInvalide(ValueError):
    """Liste de confiance illisible, non conforme à son schéma ou de forme invalide."""


@dataclass(frozen=True, slots=True)
class ListeDeConfiance:
    """Liste validée : ce qu'en dit le rapport, et les certificats remis au processus de travail."""

    version: VersionConfiance
    signataires: str
    """Ancres des signataires de manifestes, texte PEM tel que lu."""
    horodatage: str = ""
    """Ancres des autorités d'horodatage, texte PEM tel que lu ; vide si le dossier n'en a pas."""

    def configuration(self) -> dict[str, str]:
        """Forme envoyée au processus de travail, dans sa configuration."""
        return {"signataires": self.signataires, "horodatage": self.horodatage}


def livree() -> Traversable:
    """Dossier de la liste de confiance livrée dans le paquet."""
    return files("voight_kampff") / "donnees" / "confiance"


def charger(dossier: str | os.PathLike[str] | Traversable | None = None) -> ListeDeConfiance:
    """Lit et valide la liste livrée, ou celle du dossier ``dossier`` fourni par l'utilisateur."""
    if dossier is None:
        racine: Traversable = livree()
    elif isinstance(dossier, str | os.PathLike):
        racine = Path(dossier)
    else:
        racine = dossier
    contenus = _lire(racine)
    entete = _entete(contenus[ENTETE])
    textes = {nom: _pem(nom, contenu) for nom, contenu in contenus.items() if nom != ENTETE}
    version = VersionConfiance(
        nom=entete["nom"],
        version=entete["version"],
        date=entete["date"],
        empreinte=empreinte(contenus.items()),
        fourni_par_utilisateur=dossier is not None,
    )
    return ListeDeConfiance(version, textes[SIGNATAIRES], textes.get(HORODATAGE, ""))


def _lire(racine: Traversable) -> dict[str, bytes]:
    """Contenu de chaque fichier, par nom ; refuse tout fichier inattendu ou manquant."""
    if not racine.is_dir():
        raise ConfianceInvalide("liste de confiance : dossier introuvable")
    trouves: dict[str, Traversable] = {}
    for element in racine.iterdir():
        if element.name not in _FICHIERS or not element.is_file():
            raise ConfianceInvalide(f"liste de confiance : fichier inattendu : {element.name!r}")
        trouves[element.name] = element
    for requis in (ENTETE, SIGNATAIRES):
        if requis not in trouves:
            raise ConfianceInvalide(f"liste de confiance : {requis} absent")
    contenus: dict[str, bytes] = {}
    total = 0
    for nom, fichier in sorted(trouves.items()):
        # Taille annoncée d'abord, quand le système la donne, pour ne pas lire un fichier énorme.
        if isinstance(fichier, Path) and total + fichier.stat().st_size > TAILLE_MAX_CONFIANCE:
            raise ConfianceInvalide(_TROP_GRANDE)
        contenu = fichier.read_bytes()
        total += len(contenu)
        if total > TAILLE_MAX_CONFIANCE:
            raise ConfianceInvalide(_TROP_GRANDE)
        contenus[nom] = contenu
    return contenus


def _entete(contenu: bytes) -> dict[str, Any]:
    try:
        entete = tomllib.loads(contenu.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise ConfianceInvalide(f"{ENTETE} : TOML illisible") from None
    try:
        schemas.valider("confiance", entete)
    except schemas.DocumentInvalide as erreur:
        raise ConfianceInvalide(f"{ENTETE} : {erreur}") from None
    for champ in ("date", "prochaine_mise_a_jour"):
        if champ in entete:
            try:
                entete[champ] = date.fromisoformat(entete[champ])
            except ValueError:
                raise ConfianceInvalide(f"{ENTETE} : {champ} inexistante") from None
    return entete


def _pem(nom: str, contenu: bytes) -> str:
    """Texte d'un fichier PEM de certificats, vérifié ligne par ligne.

    Hors des blocs, seules des lignes de texte imprimable sont admises : la C2PA fait précéder
    chaque certificat d'une ligne « Subject ». Tout bloc d'une autre nature (une clé privée, par
    exemple) est refusé, comme un bloc non fermé ou dont le contenu n'est pas du base64 d'une
    structure DER.
    """
    try:
        texte = contenu.decode("ascii")
    except UnicodeDecodeError:
        raise ConfianceInvalide(f"{nom} : caractère hors de l'ASCII") from None
    certificats = 0
    bloc: list[str] | None = None
    lignes = texte.replace("\r\n", "\n").split("\n")
    if lignes[-1] == "":
        lignes.pop()  # fin du fichier après le dernier saut de ligne
    for ligne in lignes:
        if bloc is None:
            if ligne == _DEBUT:
                bloc = []
            elif "-----" in ligne or not set(ligne) <= _IMPRIMABLES:
                raise ConfianceInvalide(f"{nom} : ligne hors d'un certificat invalide")
        elif ligne == _FIN:
            _verifier_bloc(nom, "".join(bloc))
            certificats += 1
            if certificats > CERTIFICATS_MAX:
                raise ConfianceInvalide(f"{nom} : plus de {CERTIFICATS_MAX} certificats")
            bloc = None
        elif ligne and set(ligne) <= _BASE64:
            bloc.append(ligne)
        else:
            raise ConfianceInvalide(f"{nom} : ligne invalide dans un certificat")
    if bloc is not None:
        raise ConfianceInvalide(f"{nom} : certificat non fermé")
    if not certificats:
        raise ConfianceInvalide(f"{nom} : aucun certificat")
    return texte


def _verifier_bloc(nom: str, base64: str) -> None:
    try:
        der = binascii.a2b_base64(base64, strict_mode=True)
    except binascii.Error:
        raise ConfianceInvalide(f"{nom} : certificat dont le base64 est invalide") from None
    # Une structure DER de certificat commence par SEQUENCE, de longueur sur au moins un octet.
    if len(der) < 2 or der[0] != 0x30:
        raise ConfianceInvalide(f"{nom} : certificat qui n'est pas une structure DER")
