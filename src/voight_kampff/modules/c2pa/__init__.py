"""Module ``c2pa`` : manifeste C2PA, vérification et déclarations (F-20 à F-23 ; fiche
``provenance-c2pa``).

La lecture et la vérification sont celles de l'implémentation de référence, c2pa-rs, par sa
liaison ``c2pa-python`` (ADR-0043, ADR-0164) : signature du manifeste, empreintes du contenu
signé, chaîne de certificats jusqu'aux ancres de la liste de confiance remise par le processus
principal (ADR-0165, ADR-0171). La bibliothèque est chargée à l'import, avant les restrictions ;
elle lit la partie par un flux à positions explicites, sans jamais toucher au disque. Aucune
adresse n'est consultée : récupération des manifestes distants et requêtes OCSP coupées, liste
des hôtes permis vide (ADR-0033, ADR-0166).

L'état de la vérification (ADR-0169) est observé sous ``c2pa.etat`` : ``absent``, ``valide``
(signataire reconnu), ``valide_hors_liste``, ``invalide`` ou ``non_verifiable``. Les
déclarations du manifeste actif suivent, sous les noms de la sortie JSON de c2pa-rs : outil
d'origine, titre, signataire, actions et leur source numérique (IPTC), ingrédients et codes de
validation (F-23). Le module cite ensuite les règles « module » du catalogue qui s'appliquent
(ADR-0167, ADR-0168, ADR-0170) : une phrase par état, et pour une source numérique déclarée, une
preuve si le signataire est reconnu, un indice faible sinon.
"""

import io
import json
from collections.abc import Iterator, Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

import c2pa

from voight_kampff._limites import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Ancres, Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.rapport.modele import CategorieIdentifiante, RaisonNonMenee

__all__ = [
    "FORMATS",
    "analyser",
    "code_iptc",
    "etat_de",
    "genre_d_erreur",
    "hote",
    "illisible",
    "reglages",
]

FORMATS = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "heic": "image/heic",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "flac": "audio/flac",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text",
}
"""Type de média remis à c2pa-rs pour chaque format du manifeste du module."""

_VOCABULAIRE = "cv.iptc.org/newscodes/digitalsourcetype/"
_CONTENEUR_ILLISIBLE = "asset could not be parsed"

_GENERATION = frozenset({"trainedalgorithmicmedia"})
_RETOUCHE = frozenset({"compositewithtrainedalgorithmicmedia", "compositesynthetic"})
_CAPTURE = frozenset({"digitalcapture", "computationalcapture"})
"""Codes IPTC, en minuscules : mêmes valeurs et mêmes directions que le XMP (ADR-0143) ; la
capture n'a de constat que sous un signataire reconnu (ADR-0168)."""

_INTEGRITE = frozenset(
    {
        "assertion.dataHash.mismatch",
        "assertion.bmffHash.mismatch",
        "assertion.boxesHash.mismatch",
        "assertion.collectionHash.mismatch",
        "assertion.hashedURI.mismatch",
        "claimSignature.mismatch",
    }
)
"""Codes de validation de la C2PA qui disent un contenu ou un manifeste changé depuis la
signature (ADR-0167)."""

_SIGNATURE = (
    ("alg", None),
    ("issuer", None),
    ("common_name", CategorieIdentifiante.METADONNEE_NOMINATIVE),
    ("cert_serial_number", CategorieIdentifiante.NUMERO_DE_SERIE),
    ("time", None),
)
"""Champs de ``signature_info`` : l'organisation du certificat n'identifie pas la source, son nom
commun et son numéro peuvent nommer une personne ou un appareil (ES-13, ADR-0169)."""


_REGLES_D_ETAT = {
    "valide": "R-C2PA-007",
    "valide_hors_liste": "R-C2PA-008",
    "invalide": "R-C2PA-009",
}


def reglages(ancres: Ancres) -> dict[str, Any]:
    """Réglages de c2pa-rs pour une lecture sans réseau, ancres de la liste remises (ADR-0164)."""
    listes = [
        {"trust_kind": nature, "trust_anchors": texte}
        for nature, texte in (("manifest", ancres.signataires), ("tsa", ancres.horodatage))
        if texte
    ]
    return {
        "core": {"allowed_network_hosts": [], "decode_identity_assertions": False},
        "verify": {
            "verify_after_reading": True,
            "verify_trust": True,
            "verify_timestamp_trust": True,
            "ocsp_fetch": False,
            "remote_manifest_fetch": False,
        },
        "trust": {"anchors": listes},
    }


class _Flux(io.RawIOBase):
    """La partie analysée, en lecture seule, pour c2pa-rs : lectures bornées (ES-03)."""

    def __init__(self, contexte: Contexte) -> None:
        super().__init__()
        self._contexte = contexte
        self._position = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def readinto(self, tampon: Any) -> int:
        """Remplit ``tampon`` depuis la position courante ; 0 en fin de partie."""
        vue = memoryview(tampon).cast("B")
        donnees = self._contexte.lire(self._position, min(len(vue), TAILLE_MAX_LECTURE))
        vue[: len(donnees)] = donnees
        self._position += len(donnees)
        return len(donnees)

    def seek(self, position: int, origine: int = io.SEEK_SET) -> int:
        depart = {io.SEEK_SET: 0, io.SEEK_CUR: self._position, io.SEEK_END: self._contexte.taille}
        nouvelle = depart[origine] + position
        if nouvelle < 0:
            raise ValueError("position négative")
        self._position = nouvelle
        return nouvelle

    def tell(self) -> int:
        return self._position

    def write(self, _donnees: object) -> int:
        raise io.UnsupportedOperation("lecture seule")


def genre_d_erreur(erreur: Exception) -> str:
    """Genre d'une erreur de c2pa-rs, tiré du début de son message (``Remote: ...``).

    Ce début est le nom de la variante d'erreur de la bibliothèque ; la suite du message, qui
    peut citer le fichier, n'est jamais reprise.
    """
    genre = str(erreur).partition(":")[0].strip()
    return genre if 0 < len(genre) <= 32 and genre.isascii() and genre.isalpha() else "Other"


def illisible(erreur: Exception) -> bool:
    """Erreur de c2pa-rs sur le conteneur lui-même, avant toute recherche d'un manifeste.

    C'est la variante ``InvalidAsset`` de c2pa-rs, que c2pa-python rend sous le genre ``Other``
    et dont le message commence par ``asset could not be parsed``.
    """
    message = str(erreur).partition(":")[2].strip()
    return genre_d_erreur(erreur) == "Other" and message.startswith(_CONTENEUR_ILLISIBLE)


def hote(erreur: Exception) -> str | None:
    """Hôte du manifeste distant que cite l'erreur de c2pa-rs, s'il s'y lit sans ambiguïté."""
    message = str(erreur)
    _, trouve, adresse = message.partition(" from url ")
    if not trouve or genre_d_erreur(erreur) != "Remote":
        return None
    try:
        decoupee = urlsplit(adresse.strip())
        nom = decoupee.hostname
    except ValueError:
        return None
    if decoupee.scheme not in ("http", "https") or not nom or len(nom) > 253:
        return None
    permis = set("abcdefghijklmnopqrstuvwxyz0123456789.-")
    return nom if set(nom) <= permis else None


def etat_de(document: Mapping[str, Any]) -> str:
    """État de la vérification (F-22, ADR-0169) d'après ``validation_state`` de c2pa-rs."""
    match document.get("validation_state"):
        case "Trusted":
            return "valide"
        case "Valid":
            return "valide_hors_liste"
        case "Invalid":
            return "invalide"
        case _:
            return "non_verifiable"


def code_iptc(valeur: str) -> str:
    """Code d'une source numérique IPTC, écrit avec ou sans l'adresse du vocabulaire (ADR-0143)."""
    code = valeur.strip().lower().removeprefix("https://").removeprefix("http://")
    return code.removeprefix(_VOCABULAIRE).removesuffix("/")


def analyser(contexte: Contexte) -> None:
    """Lit et vérifie le manifeste de la partie, puis restitue ce qu'il déclare."""
    # Hors du bloc qui suit : des ancres que c2pa-rs refuse sont un défaut de la liste, pas un
    # constat sur le fichier ; le module est alors en erreur (ADR-0060).
    reglage = c2pa.Context.from_dict(reglages(contexte.ancres))
    try:
        lecteur = c2pa.Reader.try_create(
            FORMATS[contexte.format_reel], _Flux(contexte), context=reglage
        )
        if lecteur is None:
            contexte.observer("c2pa.present", False)
            contexte.constater("R-C2PA-012", [contexte.observer("c2pa.etat", "absent")])
            return
        with lecteur:
            document = json.loads(lecteur.json())
    except c2pa.C2paError as erreur:
        _non_verifiable(contexte, erreur)
        return
    _restituer(contexte, document)


def _non_verifiable(contexte: Contexte, erreur: Exception) -> None:
    """Manifeste présent que c2pa-rs ne vérifie pas : distant, mal formé, non pris en charge.

    Un conteneur que c2pa-rs ne sait pas lire ne dit rien d'un manifeste : la recherche est alors
    non menée (``format_partiel``), sans observation (ADR-0169).
    """
    if illisible(erreur):
        contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL)
        return
    present = contexte.observer("c2pa.present", True)
    etat = contexte.observer("c2pa.etat", "non_verifiable")
    genre = contexte.observer("c2pa.erreur", genre_d_erreur(erreur))
    distant = hote(erreur)
    if distant is None:
        contexte.constater("R-C2PA-010", [present, etat, genre], {"erreur": genre})
        return
    nom = contexte.observer("c2pa.distant.hote", distant)
    contexte.constater("R-C2PA-011", [present, etat, genre, nom], {"hote": nom})
    # La vérification demandait une requête vers l'hôte choisi par l'auteur du fichier (RS-02).
    contexte.non_mener(RaisonNonMenee.RESEAU_DESACTIVE)


def _restituer(contexte: Contexte, document: Mapping[str, Any]) -> None:
    """Observations du manifeste actif lu par c2pa-rs, puis constats des règles qui s'appliquent."""
    present = contexte.observer("c2pa.present", True)
    etat = etat_de(document)
    observe_etat = contexte.observer("c2pa.etat", etat)
    manifestes = _objet(document.get("manifests"))
    contexte.observer("c2pa.manifestes", len(manifestes))
    actif = _objet(manifestes.get(str(document.get("active_manifest"))))
    resultats = _objet(_objet(document.get("validation_results")).get("activeManifest"))
    # Sans résultats détaillés, les codes d'état de c2pa-rs sont ceux du manifeste actif.
    echecs = _codes(resultats.get("failure") if resultats else document.get("validation_status"))
    observe_echecs = valeurs.observer(contexte, "c2pa.validation_results.failure", echecs)
    valeurs.observer(
        contexte, "c2pa.validation_results.informational", _codes(resultats.get("informational"))
    )
    signature = [
        valeurs.observer(contexte, f"c2pa.signature_info.{cle}", texte, identifiante=categorie)
        for cle, categorie in _SIGNATURE
        if (texte := _texte(_objet(actif.get("signature_info")).get(cle))) is not None
    ]
    actions = list(_actions(actif))
    _declarations(contexte, actif, actions)
    sources = [source for _, source, _ in actions if source is not None]
    observe_sources = (
        valeurs.observer(contexte, "c2pa.actions.digitalSourceType", sources) if sources else None
    )
    _ingredients(contexte, actif, document)

    donnees = [present, observe_etat, *signature]
    match etat:
        case "valide" | "valide_hors_liste":
            contexte.constater(_REGLES_D_ETAT[etat], donnees)
        case "invalide":
            contexte.constater("R-C2PA-009", [*donnees, observe_echecs], {"codes": observe_echecs})
            if _INTEGRITE.intersection(echecs):
                contexte.constater(
                    "R-C2PA-006", [*donnees, observe_echecs], {"codes": observe_echecs}
                )
        case _:  # état que c2pa-rs n'a pas donné, ou qu'il donnerait d'une autre version
            genre = contexte.observer("c2pa.erreur", "ValidationState")
            contexte.constater("R-C2PA-010", [*donnees, genre], {"erreur": genre})
            return
    if observe_sources is None:
        return
    codes = {code_iptc(source) for source in sources}
    reconnu = etat == "valide"
    for famille, preuve, indice in (
        (_GENERATION, "R-C2PA-001", "R-C2PA-004"),
        (_RETOUCHE, "R-C2PA-002", "R-C2PA-005"),
        (_CAPTURE, "R-C2PA-003", None),
    ):
        regle = preuve if reconnu else indice
        if regle is not None and codes & famille:
            contexte.constater(regle, [*donnees, observe_sources], {"source": observe_sources})


def _declarations(
    contexte: Contexte,
    actif: Mapping[str, Any],
    actions: Sequence[tuple[str, str | None, str | None]],
) -> None:
    """Outil d'origine, titre et actions du manifeste actif (F-23)."""
    outils = [
        " ".join(texte for cle in ("name", "version") if (texte := _texte(outil.get(cle))))
        for outil in map(_objet, _suite(actif.get("claim_generator_info")))
    ]
    outils = [outil for outil in outils if outil]
    if not outils and (ancien := _texte(actif.get("claim_generator"))) is not None:
        outils = [ancien]  # manifeste de la version 1 de la spécification
    if outils:
        valeurs.observer(contexte, "c2pa.claim_generator_info", outils)
    if (titre := _texte(actif.get("title"))) is not None:
        valeurs.observer(
            contexte, "c2pa.title", titre, identifiante=CategorieIdentifiante.TEXTE_LIBRE
        )
    if actions:
        valeurs.observer(contexte, "c2pa.actions.action", [action for action, _, _ in actions])
        agents = [agent for _, _, agent in actions if agent is not None]
        if agents:
            valeurs.observer(contexte, "c2pa.actions.softwareAgent", agents)


def _actions(actif: Mapping[str, Any]) -> Iterator[tuple[str, str | None, str | None]]:
    """Actions des assertions ``c2pa.actions`` : nom, source numérique, logiciel."""
    for assertion in map(_objet, _suite(actif.get("assertions"))):
        etiquette = _texte(assertion.get("label")) or ""
        if etiquette != "c2pa.actions" and not etiquette.startswith("c2pa.actions.v"):
            continue
        for action in map(_objet, _suite(_objet(assertion.get("data")).get("actions"))):
            nom = _texte(action.get("action"))
            if nom is None:
                continue
            agent = action.get("softwareAgent")
            yield (
                nom,
                _texte(action.get("digitalSourceType")),
                _texte(_objet(agent).get("name")) or _texte(agent),
            )


def _ingredients(contexte: Contexte, actif: Mapping[str, Any], document: Mapping[str, Any]) -> None:
    """Ingrédients du manifeste actif et codes d'échec de leurs propres manifestes (F-23)."""
    ingredients = [_objet(ingredient) for ingredient in _suite(actif.get("ingredients"))]
    contexte.observer("c2pa.ingredients", len(ingredients))
    for cle, categorie in (("title", CategorieIdentifiante.TEXTE_LIBRE), ("relationship", None)):
        trouves = [texte for i in ingredients if (texte := _texte(i.get(cle))) is not None]
        if trouves:
            valeurs.observer(contexte, f"c2pa.ingredients.{cle}", trouves, identifiante=categorie)
    deltas = _suite(_objet(document.get("validation_results")).get("ingredientDeltas"))
    echecs = [
        code
        for delta in map(_objet, deltas)
        for code in _codes(_objet(delta.get("validationDeltas")).get("failure"))
    ]
    if echecs:
        valeurs.observer(contexte, "c2pa.ingredients.validationDeltas.failure", echecs)


# Lecture défensive de la sortie JSON de c2pa-rs : son contenu vient du fichier.


def _objet(valeur: object) -> Mapping[str, Any]:
    return valeur if isinstance(valeur, dict) else {}


def _suite(valeur: object) -> Sequence[Any]:
    return valeur if isinstance(valeur, list) else ()


def _texte(valeur: object) -> str | None:
    return valeur if isinstance(valeur, str) and valeur else None


def _codes(valeur: object) -> list[str]:
    """Codes d'une liste d'états de validation de c2pa-rs (``[{"code": ...}, ...]``)."""
    return [code for etat in map(_objet, _suite(valeur)) if (code := _texte(etat.get("code")))]
