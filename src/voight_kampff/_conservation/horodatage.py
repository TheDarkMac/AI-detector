"""Horodatage RFC 3161 d'un rapport écrit, optionnel (NF-17, RS-03, ADR-0262, ADR-0263).

Pour chaque fichier de rapport, l'outil envoie à l'autorité choisie par l'utilisateur
(``--horodater URL``) l'empreinte SHA-256 du fichier, et rien d'autre : ni le rapport, ni le
fichier analysé, ni son nom. La requête demande le certificat de l'autorité et porte un nonce
aléatoire. La réponse est écrite telle quelle à côté du rapport (``1.json.tsr``), où
``openssl ts -verify`` la vérifie.

L'outil vérifie le **contenu** de la réponse : statut accordé, jeton signé (``SignedData``) d'un
``TSTInfo``, algorithme SHA-256, empreinte et nonce égaux à ceux envoyés ; il en lit l'heure. Il
ne vérifie **ni la signature, ni la chaîne de certificats** de l'autorité (ADR-0263) : l'heure
lue est celle que la réponse annonce, et le terminal le dit.

La requête ne suit aucune redirection : elle irait à un hôte que l'utilisateur n'a pas choisi.
Elle passe par le mandataire que nomment les variables d'environnement, comme toute requête de
la bibliothèque standard.
"""

import secrets
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from voight_kampff._conservation import _der

__all__ = [
    "DELAI",
    "TAILLE_MAX_REPONSE",
    "HorodatageImpossible",
    "Jeton",
    "horodater",
    "lire_reponse",
    "requete",
    "verifier_url",
]

DELAI = 30.0
"""Attente maximale de la réponse d'une autorité, en secondes."""
TAILLE_MAX_REPONSE = 1 << 20
"""Taille maximale d'une réponse : 1 Mio ; un jeton en fait quelques kio."""
TAILLE_MAX_URL = 2048

_SHA256 = "2.16.840.1.101.3.4.2.1"
_SIGNED_DATA = "1.2.840.113549.1.7.2"
_TST_INFO = "1.2.840.113549.1.9.16.1.4"
_ACCORDES = {0, 1}  # granted, grantedWithMods
_STATUTS = {
    2: "demande rejetée",
    3: "réponse différée",
    4: "certificat de l'autorité bientôt révoqué",
    5: "certificat de l'autorité révoqué",
}
_TYPE_REQUETE = "application/timestamp-query"
_TYPE_REPONSE = "application/timestamp-reply"


class HorodatageImpossible(Exception):
    """Horodatage non obtenu ; le message dit pourquoi, sans citer d'octet reçu."""


@dataclass(frozen=True, slots=True)
class Jeton:
    """Réponse d'une autorité, vérifiée sur son contenu (ADR-0263)."""

    reponse: bytes
    """Réponse entière (``TimeStampResp``), telle que reçue : c'est le fichier ``.tsr``."""
    heure: datetime
    """Heure annoncée par l'autorité (``genTime``), en UTC, à la seconde ; non vérifiée."""
    numero: int
    """Numéro de série du jeton, attribué par l'autorité."""
    politique: str
    """Politique d'horodatage de l'autorité, identifiant d'objet."""


def verifier_url(url: str) -> str:
    """L'URL d'une autorité, si elle est en ``http`` ou ``https``, avec un hôte, sans
    identifiants ; lève ``ValueError`` avec le message à afficher sinon."""
    if len(url) > TAILLE_MAX_URL or not url.isascii() or not url.isprintable():
        raise ValueError("adresse illisible : URL en ASCII, sans espace, attendue")
    try:
        parties = urlsplit(url)
        parties.port  # noqa: B018 - lève ValueError si le port est invalide
    except ValueError:
        raise ValueError("adresse illisible") from None
    if parties.scheme not in {"http", "https"} or not parties.hostname:
        raise ValueError("adresse http:// ou https:// attendue, avec un nom d'hôte")
    if parties.username is not None or " " in url:
        raise ValueError("adresse sans identifiants ni espace attendue")
    return url


def requete(empreinte: bytes, nonce: int) -> bytes:
    """``TimeStampReq`` d'une empreinte SHA-256 : version 1, nonce, certificat demandé."""
    algorithme = _der.suite(_der.oid(_SHA256), _der.encoder(_der.NUL, b""))
    empreinte_message = _der.suite(algorithme, _der.encoder(_der.OCTETS, empreinte))
    return _der.suite(_der.entier(1), empreinte_message, _der.entier(nonce), _der.booleen(True))


def _jeton_signe(jeton: _der.Element) -> _der.Element:
    """``TSTInfo`` d'un ``ContentInfo`` de type ``SignedData``."""
    type_, *contenu = jeton.attendre(_der.SUITE, "jeton").enfants()
    if _der.valeur_oid(type_) != _SIGNED_DATA or len(contenu) != 1:
        raise _der.DerInvalide("jeton : données signées attendues")
    (donnees_signees,) = contenu[0].attendre(_der.CONTEXTE_0, "jeton").enfants()
    elements = donnees_signees.attendre(_der.SUITE, "données signées").enfants()
    if len(elements) < 4:
        raise _der.DerInvalide("données signées incomplètes")
    encapsule = elements[2].attendre(_der.SUITE, "contenu signé").enfants()
    if len(encapsule) != 2 or _der.valeur_oid(encapsule[0]) != _TST_INFO:
        raise _der.DerInvalide("contenu signé : TSTInfo attendu")
    (octets,) = encapsule[1].attendre(_der.CONTEXTE_0, "contenu signé").enfants()
    return _der.lire(octets.attendre(_der.OCTETS, "TSTInfo").contenu)


def lire_reponse(reponse: bytes, empreinte: bytes, nonce: int) -> Jeton:
    """Vérifie le contenu d'une ``TimeStampResp`` ; lève :class:`HorodatageImpossible`.

    Ni la signature ni les certificats ne sont vérifiés (ADR-0263).
    """
    try:
        statut, *jeton = _der.lire(reponse).attendre(_der.SUITE, "réponse").enfants()
        code = _der.valeur_entiere(statut.attendre(_der.SUITE, "statut").enfants()[0])
        if code not in _ACCORDES:
            raise HorodatageImpossible(_STATUTS.get(code, f"statut inconnu {code}"))
        if len(jeton) != 1:
            raise _der.DerInvalide("réponse accordée sans jeton")
        info = _jeton_signe(jeton[0]).attendre(_der.SUITE, "TSTInfo").enfants()
        if len(info) < 5 or _der.valeur_entiere(info[0]) != 1:
            raise _der.DerInvalide("TSTInfo : version 1 attendue")
        algorithme, condensat = info[2].attendre(_der.SUITE, "empreinte").enfants()
        if _der.valeur_oid(algorithme.attendre(_der.SUITE, "algorithme").enfants()[0]) != _SHA256:
            raise HorodatageImpossible("l'autorité a répondu pour un autre algorithme que SHA-256")
        if condensat.attendre(_der.OCTETS, "empreinte").contenu != empreinte:
            raise HorodatageImpossible("l'autorité a horodaté une autre empreinte")
        nonces = [e for e in info[5:] if e.etiquette == _der.ENTIER]
        if [_der.valeur_entiere(e) for e in nonces[:1]] != [nonce]:
            raise HorodatageImpossible("le nonce de la réponse n'est pas celui de la demande")
        return Jeton(
            reponse=reponse,
            heure=_der.heure(info[4]),
            numero=_der.valeur_entiere(info[3]),
            politique=_der.valeur_oid(info[1]),
        )
    except (_der.DerInvalide, IndexError, ValueError) as erreur:
        raise HorodatageImpossible(f"réponse illisible ({erreur})") from None


class _SansRedirection(urllib.request.HTTPRedirectHandler):
    """Refuse toute redirection : urllib lève alors ``HTTPError`` avec son code."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def _envoyer(url: str, corps: bytes, delai: float) -> bytes:
    """Envoie la requête, sans redirection ; corps de la réponse, au plus 1 Mio et un octet."""
    ouvreur = urllib.request.build_opener(_SansRedirection)
    demande = urllib.request.Request(  # noqa: S310 - schéma vérifié par verifier_url
        url,
        data=corps,
        headers={"Content-Type": _TYPE_REQUETE, "Accept": _TYPE_REPONSE},
        method="POST",
    )
    with ouvreur.open(demande, timeout=delai) as reponse:
        contenu: bytes = reponse.read(TAILLE_MAX_REPONSE + 1)
        return contenu


def horodater(
    url: str,
    empreinte: bytes,
    *,
    delai: float = DELAI,
    envoyer: Callable[[str, bytes, float], bytes] = _envoyer,
) -> Jeton:
    """Fait horodater une empreinte SHA-256 par l'autorité ``url`` (RS-03).

    ``envoyer`` remplace, pour les tests, l'envoi par le réseau. Lève
    :class:`HorodatageImpossible`, avec un message sans octet reçu.
    """
    nonce = secrets.randbits(63)
    try:
        reponse = envoyer(url, requete(empreinte, nonce), delai)
    except urllib.error.HTTPError as erreur:
        raise HorodatageImpossible(f"l'autorité a répondu {erreur.code}") from None
    except urllib.error.URLError as erreur:
        if isinstance(erreur.reason, TimeoutError):
            raise HorodatageImpossible(f"aucune réponse en {delai:.0f} s") from None
        raison = getattr(erreur.reason, "strerror", None) or str(erreur.reason)
        raise HorodatageImpossible(f"autorité injoignable ({raison})") from None
    except TimeoutError:
        raise HorodatageImpossible(f"aucune réponse en {delai:.0f} s") from None
    except OSError as erreur:
        raise HorodatageImpossible(f"échange interrompu ({erreur.strerror or erreur})") from None
    if len(reponse) > TAILLE_MAX_REPONSE:
        raise HorodatageImpossible(f"réponse de plus de {TAILLE_MAX_REPONSE >> 20} Mio")
    return lire_reponse(reponse, empreinte, nonce)
