"""Tests du codage des lignes du protocole (T12, modèle de données §7)."""

import pytest

from voight_kampff._protocole import MessageInvalide, decoder, encoder


def test_aller_retour() -> None:
    message = {
        "type": "observation",
        "texte": "é\n" + chr(0x2028),
        "nombre": 1.5,
        "liste": [True, None],
    }
    ligne = encoder(message)
    assert ligne.endswith(b"\n")
    assert ligne.count(b"\n") == 1  # le saut de ligne d'un texte est échappé
    assert decoder(ligne) == message


def test_encodage_refuse_nan() -> None:
    with pytest.raises(ValueError, match="JSON compliant"):
        encoder({"nombre": float("nan")})


@pytest.mark.parametrize(
    "ligne",
    [
        pytest.param(b"{", id="json-invalide"),
        pytest.param(b'{"a":NaN}', id="nan"),
        pytest.param(b'{"a":-Infinity}', id="infini"),
        pytest.param(b'{"a":1e400}', id="depassement"),
        pytest.param(b'{"a":1,"a":2}', id="cle-double"),
        pytest.param(b'{"a":"\xff"}', id="utf8-invalide"),
        pytest.param(b"[]", id="tableau"),
        pytest.param(b'"texte"', id="texte"),
        pytest.param(b"[" * 100_000 + b"]" * 100_000, id="imbrication"),
    ],
)
def test_decodage_strict(ligne: bytes) -> None:
    with pytest.raises(MessageInvalide) as erreur:
        decoder(ligne)
    # Le message d'erreur est l'un des textes fixes du module : il ne cite pas la ligne (ES-15).
    assert str(erreur.value) in {
        "message : JSON invalide",
        "message : NaN ou infini",
        "message : nombre hors des réels finis",
        "message : clé en double",
        "message : objet JSON attendu",
    }
