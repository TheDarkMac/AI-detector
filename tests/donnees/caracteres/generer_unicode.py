"""Tables Unicode du module caracteres (T80, ADR-0234, ADR-0235).

Lit six fichiers de la version 18.0.0 de l'Unicode Character Database et des mécanismes de
sécurité (UTS #39), et écrit ``src/voight_kampff/modules/caracteres/_unicode.py`` : familles
des caractères invisibles, écriture de chaque caractère, écritures avec lesquelles un caractère
se confond, pictogrammes d'émoji et lettres de compatibilité. Les tables du module ne dépendent
ainsi pas de la version d'Unicode de l'interpréteur (NF-06).

Sources, téléchargées le 2026-11-17 sur ``https://www.unicode.org/Public/18.0.0/`` :
``ucd/DerivedCoreProperties.txt``, ``ucd/Scripts.txt``,
``ucd/extracted/DerivedGeneralCategory.txt``, ``ucd/UnicodeData.txt``,
``ucd/emoji/emoji-data.txt``, ``security/confusables.txt`` ; licence :
``https://www.unicode.org/license.txt``. Leurs empreintes SHA-256 sont vérifiées ci-dessous.

À lancer depuis la racine du dépôt : ``python3 -I tests/donnees/caracteres/generer_unicode.py
DOSSIER``, où ``DOSSIER`` contient les six fichiers et ``license.txt``.
"""

import hashlib
import sys
from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

SORTIE = Path("src/voight_kampff/modules/caracteres/_unicode.py")
VERSION = "18.0.0"
SOURCES = {
    "DerivedCoreProperties.txt": (
        "09c928886a178fcafd93c29e4bd59073a058e5a100b716d425cb563ab50f68c9"
    ),
    "Scripts.txt": "0071fd81b6aeae25f6e8bce8efec3066a6476a91b49bdb2f52dc76e817862a6a",
    "DerivedGeneralCategory.txt": (
        "d6b151d2d40ee9b1876d26f417980f45ffae47b6055ccf7203cb31f07a030f94"
    ),
    "UnicodeData.txt": "0736451de439ae7baf1425136617da495e09ee5afbe6e394374db7009ea08950",
    "emoji-data.txt": "80d00f8e616a0ef27fd6b8de3b758c06383b5d917e2977709578e68baf733bf1",
    "confusables.txt": "6ed3ee967c9dfdf6677d563c9985182fbc50a2efb7d6059cd57b2e2ce18f5b92",
}
MAXIMUM = 0x10FFFF

# Familles des caractères invisibles (ADR-0234). L'ordre compte : un caractère reçoit la
# première famille qui le contient.
BIDIRECTIONNELS = {0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)}
ETIQUETTES = set(range(0xE0000, 0xE0080))
SELECTEURS = {*range(0xFE00, 0xFE10), *range(0xE0100, 0xE01F0), *range(0x180B, 0x180E), 0x180F}
CONTROLES_PERMIS = {0x09, 0x0A, 0x0C, 0x0D}
"""Tabulation, saut de ligne, saut de page, retour chariot : la mise en page d'un texte."""
COMPATIBILITE = {"<font>": "police", "<wide>": "pleine_chasse"}
"""Décompositions de compatibilité retenues ; les lettres cerclées sont des symboles (So), pas des
lettres, et ne sont pas comptées."""


def lignes(chemin: Path) -> Iterator[list[str]]:
    """Champs de chaque ligne de données, commentaires retirés."""
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.split("#", 1)[0].strip()
        if ligne:
            yield [champ.strip() for champ in ligne.split(";")]


def points(champ: str) -> range:
    if ".." in champ:
        debut, fin = champ.split("..")
        return range(int(debut, 16), int(fin, 16) + 1)
    return range(int(champ, 16), int(champ, 16) + 1)


def propriete(chemin: Path, nom: str) -> set[int]:
    trouves: set[int] = set()
    for champs in lignes(chemin):
        if champs[1] == nom:
            trouves.update(points(champs[0]))
    return trouves


def plages(valeurs: Mapping[int, object]) -> list[tuple[int, int, object]]:
    """Plages contiguës de même valeur, dans l'ordre des points de code."""
    resultat: list[tuple[int, int, object]] = []
    for point in sorted(valeurs):
        valeur = valeurs[point]
        if resultat and resultat[-1][1] == point - 1 and resultat[-1][2] == valeur:
            debut, _fin, _valeur = resultat[-1]
            resultat[-1] = (debut, point, valeur)
        else:
            resultat.append((point, point, valeur))
    return resultat


def main(dossier: Path) -> None:
    for nom, attendue in SOURCES.items():
        trouvee = hashlib.sha256((dossier / nom).read_bytes()).hexdigest()
        if trouvee != attendue:
            sys.exit(f"{nom} : empreinte {trouvee}, attendue {attendue}")
    licence = (dossier / "license.txt").read_text(encoding="utf-8").strip()

    categories: dict[int, str] = {}
    for champs in lignes(dossier / "DerivedGeneralCategory.txt"):
        for point in points(champs[0]):
            categories[point] = champs[1]
    ignorables = propriete(dossier / "DerivedCoreProperties.txt", "Default_Ignorable_Code_Point")

    familles: dict[int, str] = {}
    for point in range(MAXIMUM + 1):
        categorie = categories.get(point, "Cn")
        if categorie == "Cc" and point not in CONTROLES_PERMIS:
            familles[point] = "controles"
        elif point in BIDIRECTIONNELS:
            familles[point] = "bidirectionnels"
        elif point in ETIQUETTES:
            familles[point] = "etiquettes"
        elif point in SELECTEURS:
            familles[point] = "selecteurs"
        elif (categorie == "Zs" and point != 0x20) or categorie in {"Zl", "Zp"}:
            familles[point] = "espaces"
        elif categorie == "Co":
            familles[point] = "prive"
        elif point in ignorables or categorie == "Cf":
            familles[point] = "sans_chasse"

    ecritures: dict[int, str] = {}
    for champs in lignes(dossier / "Scripts.txt"):
        for point in points(champs[0]):
            ecritures[point] = champs[1]
    noms = sorted(set(ecritures.values()) | {"Unknown"})
    indices = {nom: rang for rang, nom in enumerate(noms)}

    # Confusables (UTS #39, §4) : deux caractères qui ont le même squelette se confondent.
    groupes: dict[str, set[int]] = defaultdict(set)
    for champs in lignes(dossier / "confusables.txt"):
        source = int(champs[0], 16)
        cible = "".join(chr(int(p, 16)) for p in champs[1].split())
        groupes[cible].add(source)
        if len(cible) == 1:
            groupes[cible].add(ord(cible))
    neutres = {"Common", "Inherited", "Unknown"}
    confusables: dict[int, set[str]] = defaultdict(set)
    for cible, membres in groupes.items():
        presentes = {ecritures.get(m, "Unknown") for m in membres}
        if len(cible) > 1:
            presentes |= {ecritures.get(ord(c), "Unknown") for c in cible}
        presentes -= neutres
        for membre in membres:
            autres = presentes - {ecritures.get(membre, "Unknown")}
            if autres and ecritures.get(membre, "Unknown") not in neutres:
                confusables[membre] |= autres

    pictogrammes = propriete(dossier / "emoji-data.txt", "Extended_Pictographic")
    modificateurs = propriete(dossier / "emoji-data.txt", "Emoji_Modifier")

    compatibles: dict[int, str] = {}
    for champs in lignes(dossier / "UnicodeData.txt"):
        point, decomposition = int(champs[0], 16), champs[5]
        etiquette = decomposition.split(" ", 1)[0] if decomposition.startswith("<") else ""
        categorie = categories.get(point, "Cn")
        if etiquette in COMPATIBILITE and (categorie.startswith("L") or categorie == "Nd"):
            compatibles[point] = COMPATIBILITE[etiquette]

    ecrire(
        licence,
        familles,
        ecritures,
        noms,
        indices,
        confusables,
        pictogrammes,
        modificateurs,
        compatibles,
    )


def _ranges(
    nom: str, valeurs: Mapping[int, object], format_valeur: Callable[[object], str] = str
) -> list[str]:
    entrees = [
        f"(0x{debut:04X}, 0x{fin:04X}, {format_valeur(valeur)})"
        for debut, fin, valeur in plages(valeurs)
    ]
    if len(entrees) == 1:  # écrit comme ruff format l'écrirait
        return [f"{nom} = ({entrees[0]},)"]
    return [f"{nom} = (", *(f"    {entree}," for entree in entrees), ")"]


def ecrire(
    licence: str,
    familles: dict[int, str],
    ecritures: dict[int, str],
    noms: list[str],
    indices: dict[str, int],
    confusables: dict[int, set[str]],
    pictogrammes: set[int],
    modificateurs: set[int],
    compatibles: dict[int, str],
) -> None:
    sources = "\n".join(f"- ``{nom}`` : ``{empreinte}``" for nom, empreinte in SOURCES.items())
    notice = "\n".join(f"    {ligne}".rstrip() for ligne in licence.splitlines())
    sortie = [
        f'"""Tables Unicode {VERSION} du module caracteres (T80, ADR-0234, ADR-0235).',
        "",
        "Fichier écrit par ``tests/donnees/caracteres/generer_unicode.py`` : ne pas le modifier",
        "à la main. Tiré de l'Unicode Character Database et des mécanismes de sécurité (UTS #39),",
        f"version {VERSION}. **Modification des fichiers de données** : seules les propriétés",
        "employées par le module sont gardées, regroupées en plages.",
        "",
        "Sources et empreintes SHA-256 :",
        "",
        sources,
        "",
        "Licence des fichiers de données d'Unicode, reproduite sans changement :",
        "",
        notice,
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        f'VERSION = "{VERSION}"',
        "",
        "ECRITURES = (",
        *(f'    "{nom}",' for nom in noms),
        ")",
        '"""Noms des écritures (propriété Script), dans l\'ordre de leurs indices."""',
        "",
    ]
    sortie += _ranges("FAMILLES", familles, lambda famille: f'"{famille}"')
    sortie.append('"""Plages (début, fin, famille) des caractères invisibles (ADR-0234)."""')
    sortie.append("")
    sortie += _ranges("PLAGES_ECRITURES", {p: indices[e] for p, e in ecritures.items()}, str)
    sortie.append('"""Plages (début, fin, indice de l\'écriture) ; ailleurs, « Unknown »."""')
    sortie.append("")
    ensembles = sorted({tuple(sorted(indices[e] for e in a)) for a in confusables.values()})
    rangs = {ensemble: rang for rang, ensemble in enumerate(ensembles)}
    sortie.append("ENSEMBLES = (")
    sortie += [f'    "{" ".join(map(str, ensemble))}",' for ensemble in ensembles]
    sortie.append(")")
    sortie.append(
        '"""Ensembles d\'écritures, indices séparés par une espace ; écritures Common, '
        'Inherited et Unknown omises."""'
    )
    sortie.append("")
    par_point = {p: rangs[tuple(sorted(indices[e] for e in a))] for p, a in confusables.items()}
    sortie += _ranges("CONFUSABLES", par_point)
    sortie.append(
        '"""Plages (début, fin, rang dans ENSEMBLES) des caractères qui se confondent avec un '
        'caractère de chacune des écritures de l\'ensemble (même squelette, UTS #39)."""'
    )
    sortie.append("")
    sortie += _ranges("PICTOGRAMMES", dict.fromkeys(pictogrammes, 0), str)
    sortie.append('"""Plages de la propriété Extended_Pictographic (UTS #51)."""')
    sortie.append("")
    sortie += _ranges("MODIFICATEURS", dict.fromkeys(modificateurs, 0), str)
    sortie.append('"""Plages de la propriété Emoji_Modifier (teintes de peau)."""')
    sortie.append("")
    sortie += _ranges("COMPATIBILITE", compatibles, lambda nature: f'"{nature}"')
    sortie.append(
        '"""Lettres et chiffres dont la décomposition de compatibilité est <font> ou <wide> : '
        'variantes de police, pleine chasse."""'
    )
    sortie.append("")
    SORTIE.write_text("\n".join(sortie), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
