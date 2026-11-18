# Correctif ERR-0013 — Sortie de `vk` redirigée sous Windows, écrite en UTF-8

- **Branche** : `correctif/ERR-0013-sortie-redirigee-en-cp1252`
- **Dates** : 2026-11-18
- **Exigences couvertes** : ES-12 (neutralisation écrite sur toute sortie redirigée)
- **Décisions** : [ADR-0238](../decisions/ADR-0238-sortie-redirigee-en-utf8.md), accepté au début du correctif
- **Errata** : [ERR-0013](../errata/ERR-0013-sortie-redirigee-en-cp1252.md)

## Objectif

Corriger le défaut relevé pendant T80 (journal de T80, étape 13 et « Reste à faire ») : sous Windows, une sortie de `vk` redirigée vers un fichier ou un tube s'écrit en cp1252, où la neutralisation `⟨U+XXXX⟩` (ADR-0096) lève `UnicodeEncodeError`. Correctif hors tâche, sur sa propre branche (ADR-0005), demandé à la suite de T80.

## État initial

- PR [#39](https://github.com/TheDarkMac/AI-detector/pull/39) (T80) mergée le 2026-11-18 à 01:02:44 UTC, après le « Oui, merge si vert » puis le « corriges et merges quand ca passe » de TheDarkMac : commit de merge `90c9310`. Lancements de push sur `90c9310` : code 44212724164 et docs 44212724154 verts, vérifiés au début de ce correctif.
- Toujours en attente : les points du « Reste à faire » de T80, et ceux de son « État initial », inchangés, sauf celui que traite ce correctif.

## Déroulé

1. Lecture du journal de T80 (étape 13, « Reste à faire »), d'ADR-0096, de `neutraliser` (`rapport/_presentation.py`) et des écritures de `cli.py`. Relevé des caractères des sources que cp1252 n'a pas : `⟨` et `⟩` (U+27E8, U+27E9) de la neutralisation, `≤` (U+2264) d'un message d'erreur du catalogue (sortie d'erreur, écrite en échappement par Python), `‧` (U+2027) des motifs du catalogue (jamais affichés). Hors des sources, toute valeur révélée (`--reveler`) ou tout titre d'un catalogue de l'utilisateur (`--regles`) peut en porter.
2. Reproduction sous Linux, l'encodage imposé : `PYTHONIOENCODING=cp1252 python -m voight_kampff --reveler nom_de_fichier` sur un fichier nommé `a`, U+202E, `b.txt`, sortie dans un fichier : `UnicodeEncodeError` sur U+27E8, code 1, la ligne du nom et l'avertissement jamais écrits.
3. Deux questions à TheDarkMac, en un lot, options recommandées retenues : sortie et erreur en UTF-8 hors d'un terminal ; `backslashreplace` pour un substitut isolé ([ADR-0238](../decisions/ADR-0238-sortie-redirigee-en-utf8.md), options écartées comprises).
4. `cli.py` : `_sortie_en_utf8`, appelée au début de `main`. La reproduction de l'étape 2 écrit alors un fichier en UTF-8, avec la ligne `nom : a⟨U+202E⟩b.txt`, code 0.
5. Tests : trois dans `tests/test_cli.py` (interpréteur lancé sous cp1252, flux reconfigurés et substitut échappé, terminal et flux d'un autre type laissés) ; `-X utf8` retiré du test de `vk --texte` de T80 ; sortie lue en UTF-8 par `tests/test_traces.py`, qui la décodait dans l'encodage local. Sans l'appel à `_sortie_en_utf8`, les deux premiers tests échouent sur `UnicodeEncodeError` ; rétabli, ils passent.
6. Ruff, `ruff format --check`, mypy strict et markdownlint propres.
7. Suite complète sous coverage, sous Linux, en 12 minutes 31 : 3 056 tests verts, 4 ignorés ; couverture du paquet et du banc à 100 % ; matrice de vérification à jour (`python -m banc.matrice --verifier`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Premier lancement de la suite arrêté aussitôt | `uv` n'est pas installé sur le poste | Commandes de la CI lancées par `.venv/bin/coverage` |
| `'\u27e8'` de la citation du message d'erreur écrit en caractère dans l'erratum | L'outil d'écriture de l'assistant convertit les échappements `\uXXXX` (déjà relevé pendant T80) | Échappement remis ; recherche des caractères hors du français dans les fichiers écrits |
| `git revert -n HEAD` lancé par erreur par l'assistant | Commande sans objet, tapée à la suite d'une modification | Sans effet : `HEAD` est un commit de merge, que `git revert` refuse sans `-m` ; arbre de travail et index vérifiés inchangés |

## Écarts par rapport au découpage

Aucun : correctif hors du découpage (ADR-0005).

## Résultat

- Hors d'un terminal, `vk` écrit sa sortie et son erreur en UTF-8 sur tout système ; un terminal garde son encodage. La neutralisation et les rapports ne changent pas.
- Vérification : `tests/test_cli.py -k "redirige or terminal_et"` ; sous Linux et macOS, `PYTHONIOENCODING=cp1252 vk … > sortie.txt` reproduit l'encodage local de Windows.

## Reste à faire

- Documentation utilisateur (T103) : lecture de la sortie de `vk` sous PowerShell, avec la page de code employée pour lire une commande externe et la valeur par défaut de `$OutputEncoding` (ADR-0233, ADR-0238).
