# ADR-0053 — Branche par défaut : `detector`

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, sur proposition de l'assistant
- **Tâche** : correctif ERR-0005 (après T10)
- **Exigences liées** : méthode de travail ; ES-18 ; ADR-0001, ADR-0046, ADR-0051, ADR-0052 ; ERR-0005

## Contexte

ADR-0001 a gardé `main` comme branche par défaut « pour l'instant », point « à revoir lors d'une première version ». `main` ne contient que le commit initial ; tout le travail est sur `detector`. Depuis T10, trois éléments dépendent de la branche par défaut de GitHub (ERR-0005) :

- Dependabot ne lit `.github/dependabot.yml` que sur la branche par défaut ;
- les déclenchements planifiés (`schedule`) ne s'exécutent que pour les workflows de la branche par défaut : l'audit hebdomadaire d'ADR-0051 et ADR-0052 ne tournait pas ;
- la page du dépôt, public depuis ADR-0046, affiche le README de la branche par défaut, encore intitulé « AI-detector ».

La première publication sur PyPI approche : c'est le moment prévu par ADR-0001 pour revoir ce point.

## Options envisagées

### Option A — `detector` devient la branche par défaut

- Avantages : Dependabot et l'audit hebdomadaire fonctionnent ; la page du dépôt montre l'état réel du projet ; les nouvelles PR visent `detector` sans le préciser ; `main` reste intacte.
- Inconvénients : `main` n'est plus la branche que l'on voit en premier, ce qui peut surprendre un lecteur habitué à cette convention.

### Option B — Recopier régulièrement `detector` dans `main`

- Avantages : garde `main` comme branche par défaut, selon l'usage courant.
- Inconvénients : contraire à ADR-0001 (`main` ne contient que le commit initial) ; deux branches à tenir à jour ; entre deux recopies, Dependabot et l'audit portent sur un état périmé.

### Option C — Ne rien changer

- Avantages : aucun réglage à modifier.
- Inconvénients : Dependabot et l'audit hebdomadaire restent inactifs, alors qu'ADR-0052 les a retenus.

## Décision

**`detector` est la branche par défaut du dépôt.** Réglage fait par l'assistant par l'API GitHub le 2026-10-26, sur accord de TheDarkMac. `main` garde son commit initial et sa protection (suppression et force-push interdits, `enforce_admins`), relue par l'API après le changement.

## Raisons

- Option A retenue : elle rend effectifs Dependabot et l'audit hebdomadaire sans toucher à `main`, et répond au point laissé ouvert par ADR-0001.
- Option B écartée : elle modifie `main`, que la consigne de départ demande de laisser intacte, et ajoute une tâche récurrente.
- Option C écartée : elle laisse inactives deux protections décidées en T10.

## Conséquences

- Remplace, dans ADR-0001, le seul choix de la branche par défaut ; le reste d'ADR-0001 reste en vigueur.
- Toute fonction de GitHub qui lit la branche par défaut (Dependabot, planification, page du dépôt, PR par défaut) porte désormais sur `detector`.
- Le README de `main` reste celui du commit initial ; il n'est plus affiché.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
