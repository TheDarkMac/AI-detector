# ADR-0044 — Titre des commits de merge : toujours fixé à la main

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : méthode de travail ; ADR-0001, ADR-0005, ADR-0007

## Contexte

Les PR #1 à #3 ont été mergées avec un titre au format « Merge: TNN — titre (#N) ». La PR #4 (T03) a été mergée sans l'option `--subject` : son commit de merge porte le titre par défaut de GitHub, « Merge pull request #4 from TheDarkMac/tache/T03-modele-de-menace ». Ce format n'était écrit nulle part.

## Options envisagées

### Option A — Toujours passer `--subject`

- Avantages : l'historique de `detector` nomme la tâche de chaque merge ; format déjà employé pour trois PR sur quatre.
- Inconvénients : une option à ne pas oublier.

### Option B — Titre par défaut de GitHub

- Avantages : aucun effort.
- Inconvénients : le titre nomme la branche, pas la tâche ; historique moins lisible.

## Décision

Toute PR est mergée par :

```bash
gh pr merge N --merge --subject "Merge: TNN — titre (#N)"
```

où « TNN — titre » est le titre de la PR (ADR-0005). Le commit de merge de la PR #4 n'est pas réécrit : `detector` est protégée et son historique n'est jamais modifié (ADR-0001).

## Raisons

- Option A retenue : historique lisible, format déjà en usage.
- Option B écartée : le titre par défaut ne dit pas quelle tâche a été intégrée.

## Conséquences

- `CONTRIBUTING.md` (étape 6) donne la commande.
- L'écart de la PR #4 reste visible dans l'historique ; il est expliqué ici et au journal de T04.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
