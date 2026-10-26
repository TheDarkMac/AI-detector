# ERR-0005 — Branche par défaut ignorée : Dependabot et l'audit hebdomadaire inactifs

- **Date de constat** : 2026-10-26
- **Tâche en cours** : après T10 (avant T11)
- **Document ou élément touché** : `docs/decisions/ADR-0051-integration-continue-du-code.md`, `docs/decisions/ADR-0052-surveillance-des-failles.md`, `.github/workflows/code.yml`, `.github/dependabot.yml`
- **Nature** : décision

## Ce qui était écrit ou fait

ADR-0051 :

> Workflow `code`, déclenché par chaque PR et chaque push vers `detector`, chaque lundi (ADR-0052) et à la demande

ADR-0052 :

> Le workflow tourne aussi chaque lundi, sans PR.
>
> **Dependabot** propose chaque semaine les mises à jour de `uv.lock` (préfixe `build`) et des actions GitHub (préfixe `ci`), vers `detector`

La PR #6 a été mergée avec ces deux mécanismes présentés comme actifs.

## Ce qui est juste

Tant que `main` était la branche par défaut du dépôt :

- Dependabot ne lisait pas `.github/dependabot.yml`, présent seulement sur `detector` : aucune PR de mise à jour ne pouvait être ouverte ;
- le déclenchement planifié du workflow `code` ne s'exécutait pas, GitHub ne planifiant que les workflows de la branche par défaut ;
- le lancement à la demande n'était proposé que pour les workflows présents sur la branche par défaut.

Les vérifications à chaque PR et à chaque push vers `detector` fonctionnaient. Depuis qu'ADR-0053 a fait de `detector` la branche par défaut, les deux ADR décrivent l'état réel ; leur texte n'est pas modifié.

## Comment l'erreur a été trouvée

Question de TheDarkMac après le merge de T10 : la branche par défaut, `main`, ne contient rien ; cela gêne-t-il la publication ? En y répondant, l'assistant a relu ce que GitHub fait de la branche par défaut. La publication n'est pas concernée (un workflow déclenché par une étiquette est lu dans le commit étiqueté) ; Dependabot et la planification le sont.

## Cause

ADR-0051 et ADR-0052 ont été rédigés en considérant `detector` comme la branche du projet, sans vérifier sur quelle branche GitHub lit la configuration de Dependabot et les planifications. ADR-0001 avait laissé `main` par défaut « pour l'instant », et ce point n'a pas été relu en T10, alors que T10 ajoutait les premiers éléments qui en dépendent.

## Correction appliquée

- `detector` devient la branche par défaut (ADR-0053), par l'API GitHub, le 2026-10-26 ; protection de `main` relue, inchangée.
- Lancement à la demande du workflow `code` sur `detector`, pour vérifier qu'il est désormais disponible (journal de T11, État initial).
- Historique d'ADR-0001, ADR-0051 et ADR-0052 : renvoi à cet erratum et à ADR-0053.
- `CONTRIBUTING.md` : `detector` indiquée comme branche par défaut.

## Prévention

Rejoint la règle d'ERR-0003 : toute hypothèse d'un ADR sur le comportement d'un service externe est vérifiée au premier usage réel. Pour une fonction de GitHub, la vérification inclut la branche sur laquelle elle lit sa configuration. Pour Dependabot, le premier passage hebdomadaire est à constater après le merge, et consigné au journal de T11.
