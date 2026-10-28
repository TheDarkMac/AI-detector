# Contribuer au projet

Ce fichier résume les règles de travail. Chaque règle renvoie à la décision qui la fonde, dans [`docs/decisions/`](docs/decisions/).

## 1. Préparer son poste (une fois par clone)

### Identité git — ADR-0003

Configuration **locale au dépôt** (sans `--global`) :

```bash
git config user.name "TheDarkMac"
```

```bash
git config user.email "hei.ando14@gmail.com"
```

Aucun commit ne porte de trailer `Co-Authored-By` ni de mention d'un outil d'assistance.

### Exclusion des fichiers de l'assistant — ADR-0002

`CLAUDE.md`, `CLAUDE.local.md` et `.claude/` ne sont **jamais** commités. L'exclusion est locale : `.git/info/exclude` n'est pas versionné, il faut donc l'ajouter sur chaque clone.

```bash
printf '%s\n' 'CLAUDE.md' 'CLAUDE.local.md' '**/CLAUDE.md' '**/CLAUDE.local.md' '.claude/' >> .git/info/exclude
```

Vérification : après `touch CLAUDE.md`, la commande `git status --short` ne doit rien afficher pour ce fichier.

La CI (job `fichiers-interdits`) refuse de toute façon une PR qui en contiendrait.

### Outillage Python — ADR-0037, ADR-0047, ADR-0048

Installer [uv](https://docs.astral.sh/uv/) (version 0.13.5, celle de la CI), puis, à la racine du dépôt, installer l'environnement depuis le verrou :

```bash
uv sync --locked
```

Avant de pousser, lancer les mêmes vérifications que la CI :

```bash
uv run --locked ruff format --check .
```

```bash
uv run --locked ruff check .
```

```bash
uv run --locked mypy
```

```bash
uv run --locked coverage run -m pytest
```

Les tests de fuzzing (ADR-0082) tirent 300 exemples par test d'une graine fixe. Une recherche longue, aléatoire, se lance à la main ; un échec affiche de quoi le rejouer :

```bash
VK_FUZZING=campagne uv run --locked pytest tests/test_fuzzing.py
```

Les tests d'isolation (ADR-0083) vérifient l'effet des restrictions depuis un vrai processus de travail ; leurs attentes par système sont dans `tests/systeme.py`.

Un test qui vérifie une exigence la cite par le marqueur `exigence` ; après un test ajouté, retiré ou déplacé, ou un état d'exigence changé, régénérer la matrice de vérification (ADR-0102, procédure : [`docs/verification/`](docs/verification/README.md)) :

```bash
uv run --locked python -m banc.matrice
```

Sous Linux, le test du banc complet s'exécute dans un espace de noms réseau vide (`unshare -rn`) ; il est sauté si le système le refuse, sauf sur la CI (ADR-0100).

Ajouter ou mettre à jour une dépendance : `uv add` ou `uv lock --upgrade-package <nom>`, puis commiter `uv.lock` avec `pyproject.toml`. Les critères d'admission d'une bibliothèque (ADR-0043) sont consignés dans la PR.

## 2. Branches — ADR-0001, ADR-0005, ADR-0053

| Branche | Rôle | Règle |
| --- | --- | --- |
| `main` | Commit initial | Jamais supprimée ni réécrite |
| `detector` | Intégration du travail, **branche par défaut** (ADR-0053) | **Aucun push direct** : uniquement des PR, CI verte obligatoire |
| `tache/TNN-slug` | Une tâche du [découpage](docs/00-plan/decoupage-taches.md) | Créée depuis `detector` à jour, conservée après merge |
| `correctif/ERR-NNNN-slug` | Correction d'une erreur constatée après merge | Idem |

## 3. Déroulé d'une tâche

1. Mettre `detector` à jour, puis créer la branche : `git switch -c tache/TNN-slug detector`.
2. Travailler en commits courts et explicites (format ci-dessous).
3. Documenter dans la branche (ADR-0004) :
   - l'entrée de journal `docs/journal/TNN-….md` ;
   - un ADR pour chaque choix fait **ou écarté** ;
   - un erratum pour chaque erreur constatée ;
   - l'historique des documents vivants modifiés.
4. Vérifier qu'aucun fichier interdit n'est suivi : `git ls-files | grep -E '(^|/)(CLAUDE(\.local)?\.md$|\.claude/)'` ne doit rien afficher.
5. Pousser la branche et ouvrir une PR vers `detector` (titre `TNN — titre`), en remplissant le modèle.
6. Merger par **commit de merge** quand toutes les vérifications sont vertes, avec un titre au format `Merge: TNN — titre (#N)` (ADR-0044) : `gh pr merge N --merge --subject "Merge: TNN — titre (#N)"`. Squash et rebase sont désactivés.
7. Consigner le résultat de la CI et du merge dans la section « État initial » du journal de la tâche suivante.

## 4. Messages de commit — ADR-0005

```text
type(portée): description en français, 72 caractères au plus

Corps facultatif : le pourquoi, avec renvois aux ADR et errata.
```

Types : `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`.

## 5. Vérifications automatiques — ADR-0006

| Workflow | Job | Contrôle |
| --- | --- | --- |
| `docs` | `lint-markdown` | Forme du Markdown (markdownlint-cli2, configuration `.markdownlint-cli2.jsonc`) |
| `docs` | `fichiers-interdits` | Aucun `CLAUDE.md`, `CLAUDE.local.md` ni `.claude/` suivi par git |
| `code` | `qualite` | Verrou à jour, Ruff, mypy (ADR-0047) ; versions publiées du catalogue inchangées face à la branche cible (ADR-0085) |
| `code` | `tests` | pytest et couverture, Linux, macOS et Windows × Python 3.12 à 3.14 (ADR-0048, ADR-0051) ; matrice de vérification à jour, et jointe remplie avec le résultat de chaque test (ADR-0102) |
| `code` | `audit-dependances` | Aucune faille connue dans les dépendances verrouillées (ADR-0052) |
| `code` | `paquet` | Construction reproductible et installable (ADR-0049) ; catalogue du wheel inscrit au registre (ADR-0085) ; rapports HTML et JSON écrits depuis le wheel, JSON conforme à son schéma, nom et empreinte masqués (ADR-0092, ADR-0095) ; banc d'évaluation depuis le wheel : refus avec le réseau, corpus d'essai évalué sans réseau (ADR-0100, ADR-0105) |
| `code` | `code-ok` | Résume les quatre jobs précédents |

Vérifications obligatoires pour merger dans `detector` : `lint-markdown`, `fichiers-interdits` et `code-ok` (ADR-0001, ADR-0051).

Lancer le lint en local, avec la version embarquée par l'action CI (v24.2.0) :

```bash
npx --yes markdownlint-cli2@0.23.2
```

## 6. Mettre à jour uv — ADR-0049

Dependabot ne voit ni la version de uv des workflows ni l'outil de construction. Pour passer à une nouvelle version de uv, dans une même PR :

1. remplacer `UV_VERSION` dans `.github/workflows/code.yml` et `.github/workflows/publication.yml` ;
2. ajuster la borne de `uv_build` dans `[build-system]` de `pyproject.toml` ;
3. régénérer les contraintes de construction avec leurs empreintes, en remplaçant `X.Y.Z` par la nouvelle version, puis remettre l'en-tête du fichier :

```bash
printf 'uv_build==X.Y.Z\n' | uv pip compile - --generate-hashes --universal --no-header -o contraintes-construction.txt
```

## 7. PR de Dependabot — ADR-0052

Dependabot ouvre chaque lundi des PR vers `detector` (dépendances de `uv.lock`, actions GitHub). Par exception à ADR-0003 et ADR-0005, elles sont mergées telles quelles quand `code-ok` est vert, avec le titre `Merge: dépendances — <objet> (#N)`. Une version majeure, un changement de licence ou une nouvelle dépendance transitive est d'abord vérifié selon ADR-0043, et consigné dans la PR.

## 8. Publier une version — ADR-0041, ADR-0050, ADR-0068, ADR-0069

Numérotation : versionnage sémantique écrit en PEP 440 (`X.Y.Z`, pré-versions `aN`, `bN`, `rcN`). Tant que `X` vaut 0, `Y` augmente pour un changement incompatible de l'interface publique (options et codes de sortie de la ligne de commande, format JSON du rapport, interface Python d'analyse, interface des modules), `Z` pour le reste. Avant la première version stable, les versions de développement `.devN` peuvent être publiées.

1. Si la version à publier n'est pas déjà celle de `pyproject.toml`, une PR la change ; la commande met à jour `pyproject.toml` et `uv.lock` :

   ```bash
   uv version X.Y.Z
   ```

2. Après le merge, étiqueter le **commit de merge** de `detector`, et lui seul : le workflow refuse un commit de branche de tâche. L'étiquette vaut `v` suivi de la version, sous sa forme normalisée (`uv version --short`).

   ```bash
   git switch detector && git pull --ff-only
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

3. Le workflow `publication` construit les paquets, puis attend : approuver le déploiement dans l'environnement `pypi` (onglet Actions, « Review deployments »), seulement si le job `construction` est vert.
4. Vérifier la page PyPI et la release GitHub : paquets, `SHA256SUMS`, `installation-verrouillee.txt`, `CATALOGUE.txt` (version, date et empreinte du catalogue) ; une pré-version est marquée comme telle.

Une version publiée est définitive : en cas d'erreur, la retirer de l'affichage sur PyPI (« yank ») et publier un nouveau numéro, jamais le même.

## 9. Modifier le catalogue de règles — ADR-0085

Toute modification d'un fichier de `src/voight_kampff/donnees/catalogue/` demande, dans la même PR : la version de chaque règle touchée augmentée, une nouvelle version et une nouvelle date dans `catalogue.toml`, et une nouvelle entrée à la fin de `docs/catalogue/versions.toml`, avec l'empreinte calculée dans le dossier du catalogue :

```bash
find . -type f -printf '%P\n' | LC_ALL=C sort | xargs sha256sum | sha256sum
```

Une entrée du registre déjà sur `detector` ne se modifie jamais. Détail du format et de la procédure : [`docs/catalogue/README.md`](docs/catalogue/README.md).

La phrase d'une règle (`phrase.fr`) et les textes du rapport (`src/voight_kampff/rapport/textes.toml`) sont lus par l'utilisateur : ils ne présentent jamais un indice comme une certitude (NF-14), et les textes de l'outil ont un libellé pour chaque valeur des énumérations du modèle (`tests/test_rapport.py`) — ADR-0091, ADR-0098.
