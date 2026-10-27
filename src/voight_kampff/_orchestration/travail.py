"""Lancement du processus de travail et réception de ses messages (ADR-0036, ADR-0062, ADR-0065).

Le processus principal ne lit jamais le fichier pour l'interpréter : il transmet un descripteur
déjà ouvert, envoie la configuration une fois l'isolation annoncée, puis valide chaque ligne
reçue, dans cet ordre : taille, JSON strict, schéma, modèle, place dans le protocole.

Après l'isolation vient l'identification : les parties reconnues (ADR-0071). Les résultats
arrivent ensuite partie par partie, chaque module actif dans l'ordre pour chaque partie du
périmètre ; une partie hors périmètre est déclarée non analysée ici, pas par le travail.

Tout écart arrête le processus de travail. Les modules terminés gardent leurs résultats ; les
autres deviennent des analyses non menées, avec la raison de l'arrêt, et l'analyse est
interrompue (ADR-0056). Un délai et des tailles, fixés par ADR-0077, bornent l'échange ; sous
macOS, la mémoire du travail est surveillée pendant l'attente (ADR-0079).
"""

import os
import queue
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from typing import IO, Any

from voight_kampff import schemas
from voight_kampff._limites import DELAI, DELAI_ARRET
from voight_kampff._orchestration import surveillance
from voight_kampff._orchestration.manifestes import Manifeste, selectionner
from voight_kampff._protocole import (
    TAILLE_MAX_CONFIGURATION,
    TAILLE_MAX_MESSAGE,
    TAILLE_MAX_SORTIE,
    MessageInvalide,
    decoder,
    encoder,
)
from voight_kampff.rapport.modele import (
    RAISONS_D_INTERRUPTION,
    VERSION_SCHEMA,
    Constat,
    Couverture,
    Dependance,
    EtatIsolation,
    EtatTechnique,
    Localisation,
    ManqueIsolation,
    NiveauIsolation,
    NonMenee,
    Observation,
    Partie,
    RaisonNonMenee,
    TechniqueCouverte,
    plages_non_reconnues,
    verifier_parties,
)

__all__ = ["DELAI", "ResultatTravail", "commande_travail", "executer"]

_RAISONS_DU_FICHIER = frozenset(
    {RaisonNonMenee.FORMAT_PARTIEL, RaisonNonMenee.FICHIER_TRONQUE, RaisonNonMenee.LIMITE_DEPASSEE}
)
"""Raisons qu'une analyse non menée sans module peut porter quand elle vient du travail."""

_RAISONS_DU_MOTEUR = frozenset(
    {
        RaisonNonMenee.ERREUR_MODULE,
        RaisonNonMenee.LIMITE_DEPASSEE,
        RaisonNonMenee.MEMOIRE_DEPASSEE,
    }
)
"""Raisons posées par le moteur à la place des résultats d'un module (ADR-0060)."""

_RAISONS_D_UN_MODULE = _RAISONS_DU_MOTEUR | {
    RaisonNonMenee.FORMAT_PARTIEL,
    RaisonNonMenee.FICHIER_TRONQUE,
    RaisonNonMenee.REFERENCE_MANQUANTE,
    RaisonNonMenee.RESEAU_DESACTIVE,
}

_ISOLATION_INCONNUE = EtatIsolation(NiveauIsolation.REDUITE, tuple(ManqueIsolation))
"""Retenue si le processus de travail s'arrête avant d'annoncer son isolation."""


def _avec_manque(isolation: EtatIsolation, manque: ManqueIsolation) -> EtatIsolation:
    manques = {*isolation.manques, manque}
    return EtatIsolation(NiveauIsolation.REDUITE, tuple(m for m in ManqueIsolation if m in manques))


def _arret_par_le_temps(code: int) -> bool:
    """Processus tué par sa limite de temps processeur (``SIGXCPU``, ADR-0078)."""
    return sys.platform != "win32" and code == -signal.SIGXCPU


def _raison_de_l_arret(processus: "subprocess.Popen[bytes]", echeance: float) -> RaisonNonMenee:
    """Raison d'un flux fermé avant la fin : limite de temps processeur, ou arrêt anormal."""
    try:
        code = processus.wait(max(0.0, min(DELAI_ARRET, echeance - time.monotonic())))
    except subprocess.TimeoutExpired:
        return RaisonNonMenee.ARRET_PROCESSUS
    return (
        RaisonNonMenee.DELAI_DEPASSE
        if _arret_par_le_temps(code)
        else RaisonNonMenee.ARRET_PROCESSUS
    )


@dataclass(frozen=True, slots=True)
class ResultatTravail:
    """Ce que le processus de travail a établi pour un fichier, validé par le principal.

    La soumission (ADR-0075) y ajoute le nom, la taille et l'empreinte du processus principal ;
    le rapport (T16), les versions de l'outil et du catalogue (T15).
    """

    parties: tuple[Partie, ...] | None
    """Parties reconnues par le travail ; ``None`` s'il s'est arrêté avant de les envoyer."""
    isolation: EtatIsolation
    couverture: Couverture
    observations: tuple[Observation, ...]
    constats: tuple[Constat, ...]
    non_menees: tuple[NonMenee, ...]
    dependances: tuple[Dependance, ...]
    empreinte: str | None
    """Empreinte recalculée en fin d'analyse ; comparée à celle du principal (ES-08)."""

    @property
    def interrompue(self) -> bool:
        """Analyse interrompue, hors garantie de reproductibilité (ADR-0023)."""
        return any(non_menee.raison in RAISONS_D_INTERRUPTION for non_menee in self.non_menees)


def commande_travail(descripteur: int) -> list[str]:
    """Commande du processus de travail : Python isolé (``-I``), sans fichier ``.pyc`` (``-B``)."""
    return [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "voight_kampff._travail",
        "--descripteur",
        str(descripteur),
    ]


def executer(
    descripteur: int,
    manifestes: Sequence[Manifeste],
    desactives: Collection[str] = (),
    *,
    taille: int | None = None,
    delai: float = DELAI,
    commande: Callable[[int], Sequence[str]] = commande_travail,
) -> ResultatTravail:
    """Analyse le fichier ouvert en ``descripteur`` dans un processus de travail neuf.

    ``manifestes`` est dans l'ordre d'exécution (``decouvrir``) ; ``desactives`` nomme les
    modules désactivés par l'utilisateur. ``taille``, celle que le principal a hachée, borne
    les parties reçues ; à défaut, celle du descripteur. ``commande`` remplace, pour les
    tests, le processus de travail livré.
    """
    actifs, eteints = selectionner(manifestes, desactives)
    reception = _Reception(actifs, os.fstat(descripteur).st_size if taille is None else taille)
    configuration = encoder(
        {
            "version_schema": VERSION_SCHEMA,
            "modules": [
                {
                    "identifiant": manifeste.identifiant,
                    "formats": list(manifeste.formats),
                    "directions": list(manifeste.directions),
                }
                for manifeste in actifs
            ],
        }
    )
    if len(configuration) > TAILLE_MAX_CONFIGURATION:
        raise ValueError("configuration : trop longue pour le processus de travail")
    echeance = time.monotonic() + delai
    with _lancer(descripteur, commande) as processus:
        try:
            reception.surveiller(surveillance.memoire_depassee(processus.pid))
            reception.recevoir(processus, configuration, echeance)
        except _Interruption as interruption:
            reception.interrompre(interruption.raison)
        finally:
            if processus.poll() is None:
                processus.kill()
            processus.wait(DELAI_ARRET)
    return reception.resultat(manifestes, {manifeste.identifiant for manifeste in eteints})


# Lancement


def _environnement() -> dict[str, str]:
    """Environnement vidé ; Windows ne démarre pas Python sans ``SYSTEMROOT``."""
    if sys.platform == "win32" and "SYSTEMROOT" in os.environ:  # pragma: no cover - CI Windows
        return {"SYSTEMROOT": os.environ["SYSTEMROOT"]}
    return {}


def _lancer(
    descripteur: int, commande: Callable[[int], Sequence[str]]
) -> "subprocess.Popen[bytes]":
    """Lance le processus de travail ; seuls le fichier et les trois flux standard sont hérités."""
    options: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        # Jamais lue ni recopiée : rien de ce que le processus de travail y écrit n'est gardé.
        "stderr": subprocess.DEVNULL,
        "env": _environnement(),
        "close_fds": True,
    }
    if sys.platform == "win32":  # pragma: no cover - exécuté par la CI Windows
        import msvcrt

        handle = msvcrt.get_osfhandle(descripteur)
        os.set_handle_inheritable(handle, True)
        try:
            options["startupinfo"] = subprocess.STARTUPINFO(
                lpAttributeList={"handle_list": [handle]}
            )
            return subprocess.Popen(commande(handle), **options)  # noqa: S603 - commande fixe
        finally:
            os.set_handle_inheritable(handle, False)
    return subprocess.Popen(commande(descripteur), pass_fds=(descripteur,), **options)  # noqa: S603


# Lecture bornée de la sortie


@dataclass(frozen=True, slots=True)
class _Evenement:
    ligne: bytes | None = None
    """Ligne complète, saut de ligne compris ; absente pour un événement de flux."""
    raison: RaisonNonMenee | None = None
    """Raison d'arrêt détectée par la lecture : ligne ou sortie trop longue, ligne coupée."""


_FIN_DU_FLUX = _Evenement()


def _lire(flux: IO[bytes], file: "queue.Queue[_Evenement]") -> None:
    total = 0
    while ligne := flux.readline(TAILLE_MAX_MESSAGE + 1):
        total += len(ligne)
        if len(ligne) > TAILLE_MAX_MESSAGE or total > TAILLE_MAX_SORTIE:
            # Le contexte d'un module refuse ces tailles avant l'envoi : seul un travail
            # défaillant ou compromis les dépasse (ADR-0076).
            file.put(_Evenement(raison=RaisonNonMenee.MESSAGE_INVALIDE))
            return
        if not ligne.endswith(b"\n"):
            file.put(_Evenement(raison=RaisonNonMenee.MESSAGE_INVALIDE))
            return
        file.put(_Evenement(ligne=ligne))
    file.put(_FIN_DU_FLUX)


def _ecrire(flux: IO[bytes], donnees: bytes) -> None:
    try:
        flux.write(donnees)
        flux.close()
    except (OSError, ValueError):
        pass  # processus de travail arrêté, tube fermé : la lecture le constatera


# Réception


class _Interruption(Exception):
    """Arrêt de l'échange, avec la raison qui rendra l'analyse non menée."""

    def __init__(self, raison: RaisonNonMenee) -> None:
        super().__init__(raison)
        self.raison = raison


def _invalide(condition: bool) -> None:
    if not condition:
        raise _Interruption(RaisonNonMenee.MESSAGE_INVALIDE)


@dataclass(slots=True)
class _Module:
    """Un module actif sur une partie du périmètre."""

    manifeste: Manifeste
    partie: int
    observations: list[Observation] = field(default_factory=list)
    constats: list[Constat] = field(default_factory=list)
    non_menees: list[NonMenee] = field(default_factory=list)
    remplace: bool = False
    """Résultats remplacés par une raison du moteur : plus rien n'est admis ensuite."""
    applicable: bool | None = None
    """Fixé par le message « module » ; ``None`` tant que le module n'est pas terminé."""

    @property
    def vide(self) -> bool:
        return not (self.observations or self.constats or self.non_menees)

    def etat(self) -> EtatTechnique:
        if not self.applicable:
            return EtatTechnique.NON_APPLICABLE
        if not self.non_menees:
            return EtatTechnique.APPLIQUEE
        if self.observations or self.constats:
            return EtatTechnique.PARTIELLE
        return EtatTechnique.NON_MENEE


class _Reception:
    """Suit le protocole message par message ; tout écart lève :class:`_Interruption`."""

    def __init__(self, actifs: Sequence[Manifeste], taille: int) -> None:
        self._actifs = tuple(actifs)
        self._taille = taille
        self._parties: tuple[Partie, ...] | None = None
        self._modules: list[_Module] = []
        """Modules attendus, partie par partie ; connus à la réception de l'identification."""
        self._rang = 0
        self._identifiants: set[str] = set()
        self._isolation: EtatIsolation | None = None
        self._dependances: tuple[Dependance, ...] | None = None
        self._non_menees_du_fichier: list[NonMenee] = []
        self._empreinte: str | None = None
        self._interruption: RaisonNonMenee | None = None
        self._memoire_depassee: Callable[[], bool] | None = None
        self._memoire_non_surveillee = False

    def surveiller(self, memoire_depassee: Callable[[], bool] | None) -> None:
        """Sous macOS, mesure la mémoire du travail pendant l'attente (ADR-0079)."""
        self._memoire_depassee = memoire_depassee
        self._memoire_non_surveillee = sys.platform == "darwin" and memoire_depassee is None

    # Déroulé

    def recevoir(
        self, processus: "subprocess.Popen[bytes]", configuration: bytes, echeance: float
    ) -> None:
        if processus.stdin is None or processus.stdout is None:
            raise RuntimeError("processus de travail lancé sans ses tubes")
        evenements: queue.Queue[_Evenement] = queue.Queue()
        threading.Thread(target=_lire, args=(processus.stdout, evenements), daemon=True).start()

        premier = self._message(evenements, processus, echeance)
        _invalide(premier["type"] == "isolation")
        self._isolation = EtatIsolation.depuis_dict(premier["isolation"])
        if self._memoire_non_surveillee:  # pragma: no cover - exécuté par la CI macOS
            self._isolation = _avec_manque(self._isolation, ManqueIsolation.MEMOIRE)
        # La configuration part seulement maintenant : le travail a fini de se verrouiller.
        ecriture = threading.Thread(
            target=_ecrire, args=(processus.stdin, configuration), daemon=True
        )
        ecriture.start()

        second = self._message(evenements, processus, echeance)
        _invalide(second["type"] == "identification")
        self._traiter(second)
        while self._empreinte is None:
            self._traiter(self._message(evenements, processus, echeance))
        dernier = self._evenement(evenements, echeance)
        _invalide(dernier is _FIN_DU_FLUX)
        try:
            code = processus.wait(max(0.0, echeance - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise _Interruption(RaisonNonMenee.DELAI_DEPASSE) from None
        if code != 0:
            raise _Interruption(RaisonNonMenee.ARRET_PROCESSUS)

    def _evenement(self, evenements: "queue.Queue[_Evenement]", echeance: float) -> _Evenement:
        while True:
            reste = max(0.0, echeance - time.monotonic())
            attente = reste if self._memoire_depassee is None else min(reste, surveillance.PERIODE)
            try:
                return evenements.get(timeout=attente)
            except queue.Empty:
                if attente >= reste:
                    raise _Interruption(RaisonNonMenee.DELAI_DEPASSE) from None
                if self._memoire_depassee is not None and self._memoire_depassee():
                    raise _Interruption(RaisonNonMenee.MEMOIRE_DEPASSEE) from None

    def _message(
        self,
        evenements: "queue.Queue[_Evenement]",
        processus: "subprocess.Popen[bytes]",
        echeance: float,
    ) -> dict[str, Any]:
        evenement = self._evenement(evenements, echeance)
        if evenement.raison is not None:
            raise _Interruption(evenement.raison)
        if evenement.ligne is None:  # flux fermé avant le message de fin
            raise _Interruption(_raison_de_l_arret(processus, echeance))
        try:
            message = decoder(evenement.ligne)
            schemas.valider("messages", message)
        except (MessageInvalide, schemas.DocumentInvalide):
            raise _Interruption(RaisonNonMenee.MESSAGE_INVALIDE) from None
        return message

    # Messages

    def _traiter(self, message: dict[str, Any]) -> None:
        try:
            match message["type"]:
                case "identification":
                    _invalide(self._parties is None)
                    self._identification(message["parties"])
                case "observation":
                    self._observation(Observation.depuis_dict(message["observation"]))
                case "constat":
                    self._constat(Constat.depuis_dict(message["constat"]))
                case "non_menee":
                    self._non_menee(NonMenee.depuis_dict(message["non_menee"]))
                case "module":
                    self._fin_de_module(message["module"], message["partie"], message["applicable"])
                case "versions":
                    _invalide(self._dependances is None)
                    self._versions(message["dependances"])
                case "fin":
                    _invalide(self._rang == len(self._modules) and self._dependances is not None)
                    self._empreinte = message["empreinte"]
                case _:  # « isolation » une seconde fois
                    raise _Interruption(RaisonNonMenee.MESSAGE_INVALIDE)
        except (ValueError, TypeError, KeyError):
            # Invariant du modèle refusé ; le message d'erreur, qui peut citer un nom de
            # champ, n'est pas gardé.
            raise _Interruption(RaisonNonMenee.MESSAGE_INVALIDE) from None

    def _identification(self, documents: list[dict[str, Any]]) -> None:
        parties = tuple(Partie.depuis_dict(document) for document in documents)
        verifier_parties(parties, self._taille)
        self._parties = parties
        self._modules = [
            _Module(manifeste, partie.rang)
            for partie in parties
            if partie.dans_perimetre
            for manifeste in self._actifs
        ]

    def _courant(self, identifiant: str | None, partie: int | None) -> _Module:
        """Module en cours : les modules rendent leurs résultats un par un, dans l'ordre."""
        _invalide(self._rang < len(self._modules))
        module = self._modules[self._rang]
        _invalide(identifiant == module.manifeste.identifiant and not module.remplace)
        _invalide(partie == module.partie)
        return module

    def _observation(self, observation: Observation) -> None:
        module = self._courant(observation.module, observation.partie)
        _invalide(observation.identifiant.startswith(f"{observation.module}/"))
        _invalide(observation.identifiant not in self._identifiants)
        self._identifiants.add(observation.identifiant)
        module.observations.append(observation)

    def _constat(self, constat: Constat) -> None:
        module = self._courant(constat.module, constat.partie)
        siennes = {observation.identifiant for observation in module.observations}
        _invalide(set(constat.donnees) <= siennes)
        _invalide(constat.direction in module.manifeste.directions)
        module.constats.append(constat)

    def _non_menee(self, non_menee: NonMenee) -> None:
        if non_menee.module is None:
            _invalide(non_menee.raison in _RAISONS_DU_FICHIER)
            rangs = {partie.rang for partie in self._parties or ()}
            _invalide(non_menee.partie is None or non_menee.partie in rangs)
            self._non_menees_du_fichier.append(non_menee)
            return
        module = self._courant(non_menee.module, non_menee.partie)
        _invalide(non_menee.raison in _RAISONS_D_UN_MODULE)
        if non_menee.raison in _RAISONS_DU_MOTEUR:
            # Les résultats du module ont été écartés : la raison est seule (ADR-0060).
            _invalide(module.vide)
            module.remplace = True
        module.non_menees.append(non_menee)

    def _fin_de_module(self, identifiant: str, partie: int, applicable: bool) -> None:
        _invalide(self._rang < len(self._modules))
        module = self._modules[self._rang]
        _invalide(identifiant == module.manifeste.identifiant and partie == module.partie)
        _invalide(applicable or module.vide)
        module.applicable = applicable
        self._rang += 1

    def _versions(self, dependances: list[dict[str, Any]]) -> None:
        lues = tuple(Dependance.depuis_dict(dependance) for dependance in dependances)
        _invalide(len({dependance.nom for dependance in lues}) == len(lues))
        self._dependances = lues

    # Résultat

    def interrompre(self, raison: RaisonNonMenee) -> None:
        self._interruption = raison

    def resultat(self, manifestes: Sequence[Manifeste], eteints: set[str]) -> ResultatTravail:
        executes = {
            (module.manifeste.identifiant, module.partie): module for module in self._modules
        }
        techniques: list[TechniqueCouverte] = []
        observations: list[Observation] = []
        constats: list[Constat] = []
        non_menees: list[NonMenee] = []
        for partie in self._parties or ():
            # Ce que l'identification n'a pas pu analyser est déclaré ici (ADR-0056, ADR-0071).
            localisation = Localisation(octets=partie.octets)
            if partie.tronquee:
                non_menees.append(
                    NonMenee(RaisonNonMenee.FICHIER_TRONQUE, None, localisation, partie.rang)
                )
            if not partie.dans_perimetre:
                non_menees.append(
                    NonMenee(RaisonNonMenee.HORS_PERIMETRE, None, localisation, partie.rang)
                )
                continue
            for manifeste in manifestes:
                identifiant, version, rang = manifeste.identifiant, manifeste.version, partie.rang
                module = executes.get((identifiant, rang))
                if identifiant in eteints or module is None:
                    techniques.append(
                        TechniqueCouverte(identifiant, EtatTechnique.NON_MENEE, version, rang)
                    )
                    non_menees.append(
                        NonMenee(RaisonNonMenee.MODULE_DESACTIVE, identifiant, partie=rang)
                    )
                elif module.applicable is None:  # pas terminé : ses résultats sont écartés
                    # Seule une interruption laisse un module inachevé : « fin » exige les autres.
                    raison = self._interruption or RaisonNonMenee.ARRET_PROCESSUS
                    techniques.append(
                        TechniqueCouverte(identifiant, EtatTechnique.NON_MENEE, version, rang)
                    )
                    non_menees.append(NonMenee(raison, identifiant, partie=rang))
                else:
                    techniques.append(TechniqueCouverte(identifiant, module.etat(), version, rang))
                    observations.extend(module.observations)
                    constats.extend(module.constats)
                    non_menees.extend(module.non_menees)
        if self._parties:
            non_menees.extend(
                NonMenee(RaisonNonMenee.FORMAT_PARTIEL, localisation=Localisation(octets=plage))
                for plage in plages_non_reconnues(self._parties, self._taille)
            )
        non_menees.extend(self._non_menees_du_fichier)
        if self._interruption is not None:
            non_menees.append(NonMenee(self._interruption))
        return ResultatTravail(
            parties=self._parties,
            isolation=self._isolation or _ISOLATION_INCONNUE,
            couverture=Couverture(tuple(techniques), ()),
            observations=tuple(observations),
            constats=tuple(constats),
            non_menees=tuple(non_menees),
            dependances=self._dependances or (),
            empreinte=self._empreinte if self._interruption is None else None,
        )
