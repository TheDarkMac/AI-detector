"""Noms des glyphes de l'Adobe Glyph List, pour le texte d'un PDF (complément de T53, ADR-0246).

Écrit ``src/voight_kampff/modules/_lecture/_glyphes.py`` : chaque nom de l'Adobe Glyph List
(``glyphlist.txt``, version 2.0) et de l'ITC Zapf Dingbats Glyph List (``zapfdingbats.txt``),
avec les points de code qu'il désigne. Le lecteur des polices du projet en tire le texte d'un
code dont la police ne dit que le nom du glyphe (ISO 32000-2, §9.10.2 ; spécification de l'AGL,
§2).

Source : les deux listes que fontTools 4.57.0 reproduit dans ``fontTools/agl.py`` (paquet Debian
``python3-fonttools``, sous Debian 13) : ``_aglText``, texte de ``glyphlist.txt`` avec sa notice,
et ``_AGL_ZAPF_DINGBATS``, où le caractère de rang ``n`` est celui du glyphe ``an`` (une espace :
aucun). Dépôt d'origine : ``https://github.com/adobe-type-tools/agl-aglfn``, licence BSD à trois
clauses, reproduite dans le fichier écrit. À lancer depuis la racine du dépôt : ``python3 -I
tests/donnees/caracteres/generer_glyphes.py``, avec un interpréteur où fontTools est installé.
"""
# mypy: ignore-errors
# (fontTools n'est pas dans l'environnement du projet.)

import hashlib
import sys
from pathlib import Path

import fontTools
import fontTools.agl

SORTIE = Path("src/voight_kampff/modules/_lecture/_glyphes.py")
VERSION_FONTTOOLS = "4.57.0"
EMPREINTE_AGL = "a3b2f61ced9f3644cc0d4ecde5c59df34ca286c689d9484a43a710a81c466789"
"""SHA-256 du texte de ``glyphlist.txt`` que reproduit fontTools 4.57.0, en UTF-8."""


def notice(texte: str) -> list[str]:
    """Lignes de commentaire d'en-tête de ``glyphlist.txt`` : copyright, licence, version."""
    lignes = []
    for ligne in texte.splitlines():
        if not ligne.startswith("#"):
            break
        lignes.append(ligne[1:].strip())
    return [ligne for ligne in lignes if not set(ligne) <= {"-"}]


def chaine(jetons: list[str], retrait: str = "    ") -> str:
    """Littéral Python coupé en morceaux de 88 caractères au plus."""
    morceaux, ligne = [], ""
    for jeton in jetons:
        if ligne and len(ligne) + len(jeton) + 1 > 84:
            morceaux.append(ligne + " ")
            ligne = jeton
        else:
            ligne = f"{ligne} {jeton}" if ligne else jeton
    morceaux.append(ligne)
    return "\n".join(f'{retrait}"{m}"' for m in morceaux)


def main() -> None:
    if fontTools.version != VERSION_FONTTOOLS:
        sys.exit(f"fontTools {fontTools.version} au lieu de {VERSION_FONTTOOLS}")
    texte = fontTools.agl._aglText
    if hashlib.sha256(texte.encode("utf-8")).hexdigest() != EMPREINTE_AGL:
        sys.exit("glyphlist.txt : empreinte inattendue")
    agl = []
    for ligne in texte.splitlines():
        if not ligne or ligne.startswith("#"):
            continue
        nom, points = ligne.split(";")
        agl.append(f"{nom}={'+'.join(points.split())}")
    zapf = [
        f"a{rang}={ord(caractere):04X}"
        for rang, caractere in enumerate(fontTools.agl._AGL_ZAPF_DINGBATS)
        if caractere != " "
    ]
    sortie = [
        '"""Noms des glyphes de l\'Adobe Glyph List et de l\'ITC Zapf Dingbats Glyph List.',
        "",
        "Fichier écrit par ``tests/donnees/caracteres/generer_glyphes.py`` (complément de T53,",
        "ADR-0246) : ne pas le modifier à la main. Chaque nom est suivi des points de code qu'il",
        "désigne, en hexadécimal, joints par « + » ; seule la forme change, pas les données.",
        "",
        "Notice de ``glyphlist.txt``, reproduite sans changement, hors lignes vides et de tirets :",
        "",
        *(f"    {ligne}" if ligne else "" for ligne in notice(texte)),
        '"""',
        "",
        "AGL: str = (",
        chaine(agl),
        ")",
        '"""Adobe Glyph List 2.0 : « nom=points » séparés par une espace."""',
        "",
        "ZAPF_DINGBATS: str = (",
        chaine(zapf),
        ")",
        '"""ITC Zapf Dingbats Glyph List : « nom=point » séparés par une espace."""',
    ]
    SORTIE.write_text("\n".join(sortie) + "\n", encoding="utf-8")
    print(f"{SORTIE} : {len(agl)} noms, {len(zapf)} dingbats", file=sys.stderr)


if __name__ == "__main__":
    main()
