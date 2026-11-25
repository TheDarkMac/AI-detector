"""Journal de conservation, optionnel et chaîné (NF-17, ES-16, ADR-0030, ADR-0260, ADR-0261).

Tenu seulement sur ``--journal FICHIER``, à chaque commande : aucun réglage ne l'active pour la
suite. Une ligne par événement, un objet JSON conforme au schéma publié ``journal`` :
soumission (empreinte et format du fichier ou du texte, catégories dont le masquage est levé),
refus (motif), export (empreinte d'un fichier de rapport et de son jeton d'horodatage),
consultation (empreinte d'un rapport lu par ``--comparer``). Jamais de nom de fichier ni de
chemin.

Chaque ligne porte l'empreinte SHA-256 des octets de la précédente : une modification, une
suppression ou une insertion rompt la chaîne, sauf si tout ce qui suit est récrit. La chaîne
rend donc une retouche détectable, sans l'empêcher : le journal n'est pas probant. Les dates
viennent de l'horloge du poste, et « qui » est déclaré, non vérifié.

Chaque ajout se fait sous un verrou exclusif du fichier, après relecture de sa dernière ligne :
deux commandes qui tiennent le même journal ne rompent pas sa chaîne. Le fichier est créé
lisible par son seul propriétaire.
"""

import hashlib
import json
import os
import stat
import sys
import unicodedata
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

__all__ = [
    "FORMAT",
    "ORIGINE",
    "TAILLE_MAX_JOURNAL",
    "TAILLE_MAX_QUI",
    "Bilan",
    "Journal",
    "JournalInvalide",
    "verifier",
    "verifier_qui",
]

FORMAT = 1
ORIGINE = "0" * 64
"""Empreinte « précédente » de la première entrée."""
TAILLE_MAX_JOURNAL = 64 << 20
"""Taille maximale d'un journal : 64 Mio, plus de cent mille entrées ; au-delà, en commencer un
autre."""
TAILLE_MAX_QUI = 128
_FORMAT_DATE = "%Y-%m-%dT%H:%M:%SZ"
_OUVERTURE = os.O_RDWR | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
_INTERDITES = {"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"}


class JournalInvalide(Exception):
    """Journal illisible, rompu ou inutilisable ; le message ne cite ni chemin ni contenu."""

    def __init__(self, message: str, numero: int | None = None) -> None:
        self.numero = numero
        """Numéro de la première entrée en cause, si le journal est rompu."""
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class Bilan:
    """Ce que la vérification établit d'un journal cohérent."""

    entrees: int
    premiere: datetime | None
    derniere: datetime | None
    derniere_empreinte: str
    """Empreinte de la dernière ligne, ou :data:`ORIGINE` pour un journal vide."""


def verifier_qui(qui: str) -> str:
    """Le nom déclaré, s'il a 1 à 128 caractères visibles ou espaces ; ``ValueError`` sinon."""
    if not 0 < len(qui) <= TAILLE_MAX_QUI or qui != qui.strip():
        raise ValueError(f"de 1 à {TAILLE_MAX_QUI} caractères, sans espace au début ni à la fin")
    if any(unicodedata.category(c) in _INTERDITES for c in qui):
        raise ValueError("caractère de contrôle ou invisible")
    return qui


def _empreinte(ligne: bytes) -> str:
    return hashlib.sha256(ligne).hexdigest()


def _date(texte: str) -> datetime:
    return datetime.strptime(texte, _FORMAT_DATE).replace(tzinfo=UTC)


def _entree(ligne: bytes, numero: int) -> dict[str, Any]:
    """Entrée d'une ligne, conforme au schéma ; ``JournalInvalide`` sinon."""
    from voight_kampff import schemas  # jsonschema : seulement dans le processus principal
    from voight_kampff._protocole import MessageInvalide, decoder

    try:
        entree = decoder(ligne)
        schemas.valider("journal", entree)
    except (MessageInvalide, schemas.DocumentInvalide):
        raise JournalInvalide("entrée illisible ou non conforme au schéma", numero) from None
    return entree


def verifier(contenu: bytes) -> Bilan:
    """Vérifie un journal entier ; lève :class:`JournalInvalide` à la première anomalie.

    Chaque ligne doit être une entrée conforme, terminée par un saut de ligne, numérotée à la
    suite, portant l'empreinte de la précédente ; un export doit renvoyer à une soumission
    antérieure.
    """
    if len(contenu) > TAILLE_MAX_JOURNAL:
        raise JournalInvalide(f"plus de {TAILLE_MAX_JOURNAL >> 20} Mio : commencez-en un autre")
    if not contenu:
        return Bilan(0, None, None, ORIGINE)
    lignes = contenu.split(b"\n")
    if lignes.pop() != b"":
        raise JournalInvalide("dernière entrée inachevée, sans saut de ligne", len(lignes) + 1)
    precedente = ORIGINE
    soumissions: set[int] = set()
    dates: list[datetime] = []
    for numero, ligne in enumerate(lignes, start=1):
        entree = _entree(ligne, numero)
        if entree["numero"] != numero:
            raise JournalInvalide(f"numéro {entree['numero']} à la place de {numero}", numero)
        if entree["precedente"] != precedente:
            raise JournalInvalide("empreinte de l'entrée précédente différente", numero)
        if entree["evenement"] == "soumission":
            soumissions.add(numero)
        elif entree["evenement"] == "export" and entree["soumission"] not in soumissions:
            raise JournalInvalide("export sans soumission antérieure de ce numéro", numero)
        dates.append(_date(entree["date"]))
        precedente = _empreinte(ligne)
    return Bilan(len(lignes), dates[0], dates[-1], precedente)


def _lire(descripteur: int) -> bytes:
    os.lseek(descripteur, 0, os.SEEK_SET)
    morceaux = []
    taille = 0
    while morceau := os.read(descripteur, 1 << 20):
        morceaux.append(morceau)
        taille += len(morceau)
        if taille > TAILLE_MAX_JOURNAL:
            break
    return b"".join(morceaux)


@contextmanager
def _verrou(descripteur: int) -> Iterator[None]:
    """Verrou exclusif du fichier, attendu s'il est pris par une autre commande."""
    if sys.platform == "win32":  # pragma: no cover - exécuté par la CI Windows
        import msvcrt

        # Premier octet verrouillé : chaque commande verrouille le même, journal vide compris.
        os.lseek(descripteur, 0, os.SEEK_SET)
        msvcrt.locking(descripteur, msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            os.lseek(descripteur, 0, os.SEEK_SET)
            msvcrt.locking(descripteur, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(descripteur, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(descripteur, fcntl.LOCK_UN)


def _ouvrir(chemin: str | os.PathLike[str]) -> int:
    try:
        descripteur = os.open(chemin, _OUVERTURE, 0o600)
    except OSError as erreur:
        raise JournalInvalide(f"fichier inutilisable ({erreur.strerror})") from None
    if not stat.S_ISREG(os.fstat(descripteur).st_mode):
        os.close(descripteur)
        raise JournalInvalide("pas un fichier régulier")
    return descripteur


def lire(chemin: str | os.PathLike[str]) -> Bilan:
    """Lit et vérifie un journal existant, sans le créer ni le modifier."""
    try:
        with open(chemin, "rb") as fichier:
            if not stat.S_ISREG(os.fstat(fichier.fileno()).st_mode):
                raise JournalInvalide("pas un fichier régulier")
            contenu = fichier.read(TAILLE_MAX_JOURNAL + 1)
    except OSError as erreur:
        raise JournalInvalide(f"fichier illisible ({erreur.strerror})") from None
    return verifier(contenu)


class Journal:
    """Journal ouvert pour une commande ; chaque méthode ajoute une entrée et rend son numéro.

    L'ouverture crée le fichier s'il n'existe pas et vérifie le journal entier : un journal
    rompu n'est pas prolongé. ``horloge`` remplace, pour les tests, l'horloge du poste.
    """

    def __init__(
        self,
        chemin: str | os.PathLike[str],
        qui: str | None = None,
        *,
        horloge: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._chemin = chemin
        self._qui = None if qui is None else verifier_qui(qui)
        self._horloge = horloge
        descripteur = _ouvrir(chemin)
        try:
            with _verrou(descripteur):
                self.bilan = verifier(_lire(descripteur))
        finally:
            os.close(descripteur)

    @property
    def chemin(self) -> str | os.PathLike[str]:
        """Chemin du journal, tel que la commande l'a nommé (affiché au terminal, ADR-0264)."""
        return self._chemin

    def _ajouter(self, evenement: str, champs: dict[str, Any]) -> int:
        descripteur = _ouvrir(self._chemin)
        try:
            with _verrou(descripteur):
                contenu = _lire(descripteur)
                if len(contenu) > TAILLE_MAX_JOURNAL:  # grossi par une autre commande
                    raise JournalInvalide(
                        f"plus de {TAILLE_MAX_JOURNAL >> 20} Mio : commencez-en un autre"
                    )
                numero, precedente = self._suite(contenu)
                entree: dict[str, Any] = {
                    "format": FORMAT,
                    "numero": numero,
                    "date": self._horloge().strftime(_FORMAT_DATE),
                    "evenement": evenement,
                    "precedente": precedente,
                }
                if self._qui is not None:
                    entree["qui"] = self._qui
                entree |= champs
                ligne = json.dumps(entree, ensure_ascii=False, separators=(",", ":"))
                donnees = ligne.encode("utf-8") + b"\n"
                if len(contenu) + len(donnees) > TAILLE_MAX_JOURNAL:
                    raise JournalInvalide(
                        f"il atteindrait {TAILLE_MAX_JOURNAL >> 20} Mio : commencez-en un autre"
                    )
                ecrits = os.write(descripteur, donnees)
                if ecrits != len(donnees):
                    raise JournalInvalide("écriture incomplète : le journal est à vérifier")
                os.fsync(descripteur)
        except OSError as erreur:
            raise JournalInvalide(f"entrée non écrite ({erreur.strerror})") from None
        finally:
            os.close(descripteur)
        return numero

    @staticmethod
    def _suite(contenu: bytes) -> tuple[int, str]:
        """Numéro de la prochaine entrée et empreinte de la dernière ligne.

        Seule la dernière ligne est relue : le journal entier l'a été à l'ouverture, et une
        autre commande n'a pu qu'ajouter des lignes sous le même verrou.
        """
        if not contenu:
            return 1, ORIGINE
        if not contenu.endswith(b"\n"):
            raise JournalInvalide("dernière entrée inachevée : le journal est à vérifier")
        lignes = contenu[:-1].rsplit(b"\n", 1)
        derniere = lignes[-1]
        numero = contenu.count(b"\n")
        if _entree(derniere, numero)["numero"] != numero:
            raise JournalInvalide("numérotation rompue : le journal est à vérifier", numero)
        return numero + 1, _empreinte(derniere)

    def soumission(
        self, *, saisie: str, empreinte: str, format_reel: str, levees: Sequence[str]
    ) -> int:
        """Fichier ou texte analysé."""
        return self._ajouter(
            "soumission",
            {
                "saisie": saisie,
                "empreinte": empreinte,
                "format_reel": format_reel,
                "levees": list(dict.fromkeys(levees)),
            },
        )

    def refus(self, *, saisie: str, motif: str) -> int:
        """Fichier ou texte refusé."""
        return self._ajouter("refus", {"saisie": saisie, "motif": motif})

    def export(
        self,
        *,
        soumission: int,
        rapport: str,
        empreinte: str,
        horodatage: dict[str, str] | None = None,
    ) -> int:
        """Fichier de rapport écrit, et son jeton d'horodatage s'il en a un."""
        champs: dict[str, Any] = {
            "soumission": soumission,
            "rapport": rapport,
            "empreinte": empreinte,
        }
        if horodatage is not None:
            champs["horodatage"] = horodatage
        return self._ajouter("export", champs)

    def consultation(self, *, empreinte: str) -> int:
        """Rapport JSON lu par l'outil."""
        return self._ajouter("consultation", {"empreinte": empreinte})
