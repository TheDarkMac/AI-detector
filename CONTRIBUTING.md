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

## 2. Branches — ADR-0001, ADR-0005

| Branche | Rôle | Règle |
| --- | --- | --- |
| `main` | Commit initial | Jamais supprimée ni réécrite |
| `detector` | Intégration du travail | **Aucun push direct** : uniquement des PR, CI verte obligatoire |
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
6. Merger par **commit de merge** quand toutes les vérifications sont vertes. Squash et rebase sont désactivés.
7. Consigner le résultat de la CI et du merge dans la section « État initial » du journal de la tâche suivante.

## 4. Messages de commit — ADR-0005

```text
type(portée): description en français, 72 caractères au plus

Corps facultatif : le pourquoi, avec renvois aux ADR et errata.
```

Types : `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`.

## 5. Vérifications automatiques — ADR-0006

| Job | Contrôle |
| --- | --- |
| `lint-markdown` | Forme du Markdown (markdownlint-cli2, configuration `.markdownlint-cli2.jsonc`) |
| `fichiers-interdits` | Aucun `CLAUDE.md`, `CLAUDE.local.md` ni `.claude/` suivi par git |

Lancer le lint en local :

```bash
npx markdownlint-cli2
```
