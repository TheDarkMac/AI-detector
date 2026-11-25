"""Publication des règles et des fiches techniques, lisibles hors ligne (NF-19, T95).

Tout est public (ADR-0019) ; ce module le rend lisible depuis l'outil installé, à sa version
exacte. ``fiche`` lit la fiche technique d'un module livré, copiée dans le paquet depuis
``docs/techniques`` (ADR-0268). ``en_toml`` écrit des règles du catalogue dans la forme même de
ses fichiers, décrite par le guide du catalogue : relue par ``tomllib``, elle redonne
``Regle.vers_dict`` (ADR-0269).
"""

import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff._regles import Regle

__all__ = ["en_toml", "fiche", "fiches"]

_ECHAPPEMENTS = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f"}
_ECHAPPEMENTS["\r"] = "\\r"
_A_ECHAPPER = frozenset({"Cc", "Cf", "Zl", "Zp"})
"""Contrôle, que TOML interdit en clair, et caractères qu'un terminal n'affiche pas tels quels
(ES-12) : écrits ``\\uXXXX``, ce qui ne change pas la valeur relue."""
_CLE_NUE = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
_TABLES = ("condition",)
"""Listes de tables écrites ``[[regle.condition]]``, comme dans les fichiers du catalogue."""


def fiches() -> Traversable:
    """Dossier des fiches techniques livrées dans le paquet."""
    return files("voight_kampff") / "donnees" / "fiches"


def fiche(manifeste: Manifeste) -> str:
    """Texte de la fiche technique d'un module livré, en Markdown.

    Lève ``FileNotFoundError`` si le paquet ne la contient pas : un paquet construit hors du
    dépôt sans ``python -m banc.fiches``.
    """
    return (fiches() / f"{manifeste.fiche}.md").read_text(encoding="utf-8")


def _chaine(texte: str) -> str:
    morceaux = ['"']
    for caractere in texte:
        if caractere in _ECHAPPEMENTS:
            morceaux.append(_ECHAPPEMENTS[caractere])
        elif unicodedata.category(caractere) in _A_ECHAPPER:
            point = ord(caractere)
            morceaux.append(f"\\u{point:04X}" if point <= 0xFFFF else f"\\U{point:08X}")
        else:
            morceaux.append(caractere)
    morceaux.append('"')
    return "".join(morceaux)


def _cle(nom: str) -> str:
    return nom if nom and set(nom) <= _CLE_NUE else _chaine(nom)


def _valeur(valeur: Any) -> str:
    # bool avant int : True est un int pour Python.
    if isinstance(valeur, bool):
        return "true" if valeur else "false"
    if isinstance(valeur, int):
        return str(valeur)
    if isinstance(valeur, float):
        return repr(valeur)  # fini (validé par la règle) : repr est une écriture TOML valide
    if isinstance(valeur, str):
        return _chaine(valeur)
    if isinstance(valeur, Mapping):
        paires = ", ".join(f"{_cle(cle)} = {_valeur(v)}" for cle, v in valeur.items())
        return f"{{ {paires} }}" if paires else "{}"
    if isinstance(valeur, Sequence):
        return "[" + ", ".join(_valeur(v) for v in valeur) + "]"
    raise TypeError(f"valeur sans écriture TOML : {type(valeur).__name__}")


def _champ(cle: str, valeur: Any) -> list[str]:
    """Une ligne par champ ; une liste de plusieurs éléments, une ligne par élément."""
    if isinstance(valeur, list) and len(valeur) > 1:
        return [f"{_cle(cle)} = [", *(f"    {_valeur(v)}," for v in valeur), "]"]
    return [f"{_cle(cle)} = {_valeur(valeur)}"]


def _table(document: Mapping[str, Any], chemin: str) -> list[str]:
    lignes = [f"[[{chemin}]]"]
    for cle, valeur in document.items():
        if cle not in _TABLES:
            lignes += _champ(cle, valeur)
    for cle in _TABLES:
        for sous_table in document.get(cle, ()):
            lignes += ["", *_table(sous_table, f"{chemin}.{cle}")]
    return lignes


def en_toml(regles: Iterable[Regle], entete: Sequence[str] = ()) -> str:
    """Règles écrites comme dans un fichier ``regles/<module>.toml``, précédées de lignes de
    commentaire ; chaque ligne d'en-tête doit être sur une ligne."""
    lignes = [f"# {ligne}" for ligne in entete]
    for regle in regles:
        if lignes:
            lignes.append("")
        lignes += _table(regle.vers_dict(), "regle")
    return "\n".join(lignes) + "\n"
