"""Fuzzing des analyseurs (ES-19, ADR-0081), avec Hypothesis.

Trois analyseurs lisent aujourd'hui des données hostiles :

- l'identification, dans le processus de travail, lit le fichier (ADR-0070) ;
- le décodage strict des lignes, dans le processus principal, lit ce qu'envoie un processus de
  travail peut-être compromis (ES-04) ;
- la réception, qui valide chaque message par le schéma puis par le modèle (ADR-0065).

Pour chacun, la propriété est la même : quelle que soit l'entrée, il rend un résultat valide
ou refuse par l'erreur prévue, jamais autre chose. Les entrées sont des octets quelconques et
des échantillons valides mutés (octets remplacés, insérés, supprimés, coupés, recollés).

Le profil ``defaut`` (``conftest.py``) tire 300 exemples d'une graine fixe ; ``VK_FUZZING=campagne``
lance une recherche longue (``CONTRIBUTING.md``).
"""

import json
import tempfile
from typing import Any

import pytest
from echantillons import (
    PDF,
    TRAME_MP3,
    archive,
    docx,
    ebml,
    id3,
    iso,
    jpeg,
    odt,
    page_ogg,
    png,
    riff,
    trame_adts,
)
from hypothesis import given
from hypothesis import strategies as st

from voight_kampff import schemas
from voight_kampff._orchestration import travail
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff._protocole import MessageInvalide, decoder, encoder
from voight_kampff._travail import garde
from voight_kampff._travail.fichier import Fichier
from voight_kampff._travail.identification import identifier
from voight_kampff.rapport.modele import Direction, Partie, RaisonNonMenee, verifier_parties

ECHANTILLONS = (
    jpeg(),
    png(),
    PDF,
    riff(b"WAVE"),
    riff(b"WEBP", b"VP8 \x00\x00\x00\x00"),
    iso(b"isom", b"isom"),
    iso(b"heic", b"mif1"),
    ebml(b"webm"),
    page_ogg() + page_ogg(),
    id3(TRAME_MP3) + TRAME_MP3,
    trame_adts() * 3,
    docx(),
    odt(),
    archive(("a.txt", b"abc")),
    jpeg() + docx(),
    jpeg() + PDF,
    "Texte accentué\n".encode(),
    "﻿UTF-16".encode("utf-16"),
)
"""Un échantillon par famille de structure parcourue, et deux polyglottes."""


@pytest.fixture(autouse=True, scope="module")
def verrouille() -> None:
    garde.verrouiller()


@st.composite
def mutes(draw: st.DrawFn) -> bytes:
    """Échantillon valide transformé par quelques mutations."""
    octets = bytearray(draw(st.sampled_from(ECHANTILLONS)))
    for _ in range(draw(st.integers(0, 6))):
        position = draw(st.integers(0, len(octets)))
        match draw(st.sampled_from(("remplacer", "inserer", "supprimer", "couper", "coller"))):
            case "remplacer" if position < len(octets):
                octets[position] = draw(st.integers(0, 255))
            case "inserer":
                octets[position:position] = draw(st.binary(min_size=1, max_size=64))
            case "supprimer":
                del octets[position : position + draw(st.integers(1, 64))]
            case "couper":
                del octets[position:]
            case "coller":
                octets[position:position] = draw(st.sampled_from(ECHANTILLONS))
    return bytes(octets)


def identifier_octets(contenu: bytes) -> tuple[Partie, ...]:
    with tempfile.TemporaryFile() as fichier:
        fichier.write(contenu)
        fichier.flush()
        return identifier(Fichier(fichier.fileno()), len(contenu))


def verifier_identification(contenu: bytes) -> None:
    parties = identifier_octets(contenu)
    verifier_parties(parties, len(contenu))
    assert all(Partie.depuis_dict(partie.vers_dict()) == partie for partie in parties)
    assert identifier_octets(contenu) == parties  # même fichier, même identification


# Identification


@given(st.binary(max_size=4096))
def test_identification_octets_quelconques(contenu: bytes) -> None:
    verifier_identification(contenu)


@given(mutes())
def test_identification_echantillons_mutes(contenu: bytes) -> None:
    verifier_identification(contenu)


# Décodage strict des lignes


@given(st.binary(max_size=512))
def test_decodage_octets_quelconques(ligne: bytes) -> None:
    try:
        document = decoder(ligne)
    except MessageInvalide:
        return
    assert isinstance(document, dict)


JSON = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=8),
    lambda enfants: (
        st.lists(enfants, max_size=4) | st.dictionaries(st.text(max_size=8), enfants, max_size=4)
    ),
    max_leaves=8,
)


@given(st.dictionaries(st.text(max_size=12), JSON, max_size=6))
def test_decodage_aller_retour(document: dict[str, Any]) -> None:
    assert decoder(encoder(document)) == document


# Réception par le processus principal

MODULE = Manifeste(
    "alpha", "1.0", ("jpeg",), ("F-10",), (), "test", (Direction.RIEN_DE_PARTICULIER,)
)
MESSAGES: tuple[dict[str, Any], ...] = (
    {
        "type": "identification",
        "parties": [
            {
                "rang": 1,
                "format": "jpeg",
                "octets": {"debut": 0, "longueur": 100},
                "fin_connue": True,
                "tronquee": False,
            }
        ],
    },
    {
        "type": "observation",
        "observation": {
            "identifiant": "alpha/1",
            "module": "alpha",
            "nom": "taille",
            "valeur": 100,
            "partie": 1,
        },
    },
    {"type": "non_menee", "non_menee": {"raison": "format_partiel", "module": "alpha"}},
    {"type": "module", "module": "alpha", "partie": 1, "applicable": True},
    {"type": "versions", "dependances": [{"nom": "zlib", "version": "1.3"}]},
    {"type": "fin", "empreinte": "0" * 64},
)
"""Messages valides, dans l'ordre du protocole, que les mutations dérangent."""


@st.composite
def messages_mutes(draw: st.DrawFn) -> dict[str, Any]:
    message: dict[str, Any] = json.loads(json.dumps(draw(st.sampled_from(MESSAGES))))
    for _ in range(draw(st.integers(0, 3))):
        cible = message
        while True:  # descend dans un objet ou une liste du message
            cles = list(cible) if isinstance(cible, dict) else list(range(len(cible)))
            if not cles:
                break
            cle = draw(st.sampled_from(cles))
            if not isinstance(cible[cle], dict | list) or draw(st.booleans()):
                break
            cible = cible[cle]
        if cles:
            cible[cle] = draw(JSON)
    return message


@given(st.lists(messages_mutes(), min_size=1, max_size=5))
def test_reception_messages_mutes(suite: list[dict[str, Any]]) -> None:
    reception = travail._Reception((MODULE,), 100)
    for message in suite:
        try:
            schemas.valider("messages", decoder(encoder(message)))
        except (schemas.DocumentInvalide, MessageInvalide, ValueError):
            continue  # refusé avant le modèle : rien d'autre ne doit arriver
        try:
            reception._traiter(message)
        except travail._Interruption as interruption:
            raison = interruption.raison
            break
    else:
        raison = RaisonNonMenee.MESSAGE_INVALIDE
    assert raison is RaisonNonMenee.MESSAGE_INVALIDE  # seul refus possible d'un message
    reception.interrompre(raison)
    reception.resultat((MODULE,), set())  # le résultat se construit quoi qu'il soit arrivé
