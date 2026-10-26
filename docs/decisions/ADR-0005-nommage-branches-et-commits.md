# ADR-0005 — Nommage des branches et messages de commit

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : proposition de l'assistant, soumise à TheDarkMac dans la PR de T00 (relecture a posteriori, ADR-0001)
- **Tâche** : T00
- **Exigences liées** : méthode de travail ; NF-07

## Contexte

Chaque tâche du découpage a sa branche (ADR-0001). Il faut pouvoir relier une branche, un commit et une PR à la tâche correspondante sans ambiguïté.

## Options envisagées

### Nommage des branches

- **`feat/…`, `fix/…`** (usage courant) : renseigne sur la nature, pas sur la tâche du découpage.
- **`tache/TNN-slug`** *(retenu)* : identifiant de tâche en tête, lien direct avec le découpage et le journal.

### Format des messages de commit

- **Texte libre** : aucune homogénéité.
- **Conventional Commits** *(retenu)* : format répandu, lisible, outillable plus tard (génération de notes de version).

## Décision

### Règle des branches

- `main` et `detector` : branches permanentes (ADR-0001).
- `tache/TNN-slug-court` : une par tâche, `TNN` étant l'identifiant du découpage, `slug` en minuscules, sans accents, mots séparés par des tirets. Exemple : `tache/T00-init-depot`.
- `correctif/ERR-NNNN-slug` : correction d'une erreur constatée après merge, hors tâche en cours.

### Règle des commits

Format : `type(portée optionnelle): description`

- `type` en anglais, parmi : `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`.
- `description` en français, à l'impératif présent ou au présent de l'indicatif, sans point final, 72 caractères au plus.
- Corps facultatif, en français, expliquant le **pourquoi** ; il renvoie aux ADR / errata concernés.
- Aucun trailer de co-auteur (ADR-0003).

### Règle des PR

- Titre : `TNN — titre de la tâche`.
- Corps : modèle `.github/pull_request_template.md` (exigences couvertes, documents produits, checklist).

## Raisons

- Le préfixe `tache/TNN` rend la traçabilité exigence → tâche → branche → PR immédiate.
- Garder les types Conventional Commits en anglais conserve la compatibilité avec l'outillage existant, tandis que le texte reste en français (ADR-0004).

## Conséquences

- Les messages des commits déjà faits avant cet ADR (commit initial de `main`) suivent déjà ce format.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : titre des commits de merge fixé par ADR-0044 (T04) |
| 2026-10-26 | Renvoi : exception pour les branches et messages de Dependabot (ADR-0052) (T10) |
