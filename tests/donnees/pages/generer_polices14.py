"""Largeurs des 14 polices standard du PDF, pour le module pagespdf (T51, ADR-0215).

Lit les fichiers AFM d'Adobe des 14 polices standard (ISO 32000-2, §9.6.2.2) et écrit
``src/voight_kampff/modules/_lecture/_polices14.py`` : pour chaque police, sa montée et sa
descente, son encodage propre et la largeur de chaque glyphe, par son nom ; et les noms des
glyphes des encodages StandardEncoding, WinAnsiEncoding et MacRomanEncoding (annexe D).

Sources de la version du dépôt : fichiers AFM du paquet Debian ``python-matplotlib-data``
(``/usr/share/matplotlib/mpl-data/fonts/pdfcorefonts``, téléchargés chez Adobe par Matplotlib),
liste des glyphes d'Adobe (AGL) de fontTools 4.57.0, sous Debian 13. StandardEncoding est lu
dans les codes de l'AFM de Helvetica ; WinAnsiEncoding et MacRomanEncoding sont tirés des codecs
``cp1252`` et ``mac_roman`` de Python, ramenés aux noms de l'AGL, avec les écarts de l'annexe D
écrits ci-dessous. À lancer depuis la racine du dépôt : ``python3 -I
tests/donnees/pages/generer_polices14.py``, avec un interpréteur où fontTools est installé.
"""
# mypy: ignore-errors
# (fontTools n'est pas dans l'environnement du projet.)

import sys
from pathlib import Path

import fontTools.agl

AFM = Path("/usr/share/matplotlib/mpl-data/fonts/pdfcorefonts")
SORTIE = Path("src/voight_kampff/modules/_lecture/_polices14.py")
POLICES = (
    "Courier",
    "Courier-Bold",
    "Courier-BoldOblique",
    "Courier-Oblique",
    "Helvetica",
    "Helvetica-Bold",
    "Helvetica-BoldOblique",
    "Helvetica-Oblique",
    "Symbol",
    "Times-Bold",
    "Times-BoldItalic",
    "Times-Italic",
    "Times-Roman",
    "ZapfDingbats",
)
ECARTS = {
    "WinAnsiEncoding": {0xA0: "space", 0xAD: "hyphen"},
    "MacRomanEncoding": {0xBD: "Omega", 0xC6: "Delta", 0xCA: "space", 0xDB: "currency"},
}
"""Codes dont l'annexe D donne un autre nom que l'AGL ou le codec de Python."""
NOTICE = (
    "This file and the 14 PostScript(R) AFM files it accompanies may be used, copied, and "
    "distributed for any purpose and without charge, with or without modification, provided "
    "that all copyright notices are retained; that the AFM files are not distributed without "
    "this file; that all modifications to this file or any of the AFM files are prominently "
    "noted in the modified file(s); and that this paragraph is not modified. Adobe Systems has "
    "no responsibility or obligation to support the use of the AFM files."
)


def lire(nom: str) -> tuple[int, int, dict[int, str], dict[str, int], list[str]]:
    """Montée, descente, codes de l'encodage propre, largeurs par nom, mentions de copyright."""
    montee = descente = None
    boite: list[int] = []
    codes: dict[int, str] = {}
    largeurs: dict[str, int] = {}
    mentions: list[str] = []
    for ligne in (AFM / f"{nom}.afm").read_text(encoding="latin-1").splitlines():
        if ligne.startswith(("Comment Copyright", "Notice")):
            mentions.append(ligne.split(" ", 1)[1].strip())
        elif ligne.startswith("Ascender "):
            montee = int(ligne.split()[1])
        elif ligne.startswith("Descender "):
            descente = int(ligne.split()[1])
        elif ligne.startswith("FontBBox "):
            boite = [int(v) for v in ligne.split()[1:5]]
        elif ligne.startswith("C "):
            champs = dict(
                [*morceau.split(" ", 1), ""][:2]
                for morceau in (m.strip() for m in ligne.split(";"))
                if morceau
            )
            code, glyphe = int(champs["C"]), champs["N"]
            largeurs[glyphe] = round(float(champs["WX"]))
            if code >= 0:
                codes[code] = glyphe
    if montee is None or descente is None:  # Symbol et ZapfDingbats : boîte englobante
        montee, descente = boite[3], boite[1]
    return montee, descente, codes, largeurs, sorted(set(mentions))


def encodage(codec: str, ecarts: dict[int, str]) -> list[str]:
    noms = [""] * 256
    for code in range(32, 256):
        try:
            caractere = bytes([code]).decode(codec)
        except UnicodeDecodeError:
            continue
        if caractere.isprintable() or caractere == "\xa0" or caractere == "\xad":
            noms[code] = fontTools.agl.UV2AGL.get(ord(caractere), "")
    for code, nom in ecarts.items():
        noms[code] = nom
    return noms


def chaine(texte: str, retrait: str = "        ") -> str:
    """Littéral Python coupé en morceaux de 80 caractères au plus."""
    morceaux, ligne = [], ""
    for mot in texte.split(" "):
        if ligne and len(ligne) + len(mot) + 1 > 80:
            morceaux.append(ligne + " ")
            ligne = mot
        else:
            ligne = f"{ligne} {mot}" if ligne else mot
    morceaux.append(ligne)
    return "\n".join(f'{retrait}"{m}"' for m in morceaux)


def main() -> None:
    lues = {nom: lire(nom) for nom in POLICES}
    standard = [""] * 256
    for code, glyphe in lues["Helvetica"][2].items():
        standard[code] = glyphe
    encodages = {
        "StandardEncoding": standard,
        "WinAnsiEncoding": encodage("cp1252", ECARTS["WinAnsiEncoding"]),
        "MacRomanEncoding": encodage("mac_roman", ECARTS["MacRomanEncoding"]),
    }
    for nom in ("Symbol", "ZapfDingbats"):
        propre = [""] * 256
        for code, glyphe in lues[nom][2].items():
            propre[code] = glyphe
        encodages[nom] = propre
    mentions = sorted({m for lue in lues.values() for m in lue[4]})
    sortie = [
        '"""Largeurs des 14 polices standard du PDF (§9.6.2.2), tirées des fichiers AFM d\'Adobe.',
        "",
        "Fichier écrit par ``tests/donnees/pages/generer_polices14.py`` (T51, ADR-0215) : ne pas",
        "le modifier à la main. **Modification des fichiers AFM** : seuls la montée, la descente",
        "(boîte englobante pour Symbol et ZapfDingbats), le nom et la largeur arrondie de chaque",
        "glyphe sont gardés, et les codes de leur encodage ramenés aux encodages ci-dessous.",
        "",
        "Mentions des fichiers AFM :",
        "",
        *(f"- {m}" for m in mentions),
        "",
        "Conditions d'Adobe, reproduites sans changement :",
        "",
        *(f"    {ligne}" for ligne in _paragraphe(NOTICE)),
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "ENCODAGES: dict[str, str] = {",
    ]
    for nom, noms in encodages.items():
        texte = " ".join(n or "." for n in noms)
        sortie.append(f'    "{nom}": (\n{chaine(texte)}\n    ),')
    sortie.append("}")
    sortie.append(
        '"""Noms des glyphes des codes 0 à 255, séparés par une espace ; « . » si aucun."""'
    )
    sortie.append("")
    sortie.append("POLICES: dict[str, tuple[int, int, str, str]] = {")
    for nom, (montee, descente, _, largeurs, _) in lues.items():
        propre = nom if nom in ("Symbol", "ZapfDingbats") else "StandardEncoding"
        texte = " ".join(f"{g} {w}" for g, w in largeurs.items())
        sortie.append(f'    "{nom}": (\n        {montee},\n        {descente},')
        sortie.append(f'        "{propre}",')
        sortie.append(f"{chaine(texte)},\n    ),")
    sortie.append("}")
    sortie.append(
        '"""Montée, descente, encodage propre, et largeurs en millièmes de cadratin : « nom'
        ' largeur » séparés par une espace."""'
    )
    SORTIE.write_text("\n".join(sortie) + "\n", encoding="utf-8")
    print(f"{SORTIE} : {len(lues)} polices", file=sys.stderr)


def _paragraphe(texte: str) -> list[str]:
    lignes, ligne = [], ""
    for mot in texte.split():
        if ligne and len(ligne) + len(mot) + 1 > 88:
            lignes.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}" if ligne else mot
    return [*lignes, ligne]


if __name__ == "__main__":
    main()
