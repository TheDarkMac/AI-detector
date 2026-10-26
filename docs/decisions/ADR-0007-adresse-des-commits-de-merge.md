# ADR-0007 — Adresse e-mail des commits de merge créés par GitHub

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac
- **Tâche** : T02 (décision prise à la fin de T01, consignée en T02)
- **Exigences liées** : méthode de travail ; complète ADR-0003

## Contexte

ADR-0003 fixe l'identité des commits : `TheDarkMac <hei.ando14@gmail.com>`, configurée localement. Les merges de PR se font sur GitHub (ADR-0001), et les commits de merge créés par GitHub portent l'adresse `152582682+TheDarkMac@users.noreply.github.com` : constaté sur la PR #1 (`3b7d3a5`, ERR-0003), puis confirmé sur la PR #2 (`016ba73`). Le nom est correct et aucun co-auteur n'est ajouté.

## Options envisagées

### Option A — Accepter l'adresse noreply sur les commits de merge

- Avantages : aucune action ; l'adresse est rattachée au même compte GitHub ; elle ne publie aucune adresse personnelle.
- Inconvénients : deux adresses coexistent dans l'historique ; une lecture de `git log` doit savoir pourquoi.

### Option B — Merger en local, puis pousser `detector`

- Avantages : tous les commits porteraient `hei.ando14@gmail.com`.
- Inconvénients : impossible, la protection de `detector` interdit le push direct, administrateurs compris (ADR-0001).

### Option C — Changer le réglage de confidentialité de l'adresse du compte GitHub

- Avantages : GitHub utiliserait probablement l'adresse principale (lien de cause non vérifié, ERR-0003).
- Inconvénients : rend l'adresse personnelle publique aussi pour les commits faits depuis l'interface web, sur tous les dépôts du compte ; réglage du compte, hors du ressort du projet.

## Décision

Les commits de merge créés par GitHub portent l'adresse noreply du compte TheDarkMac ; c'est accepté. Les commits faits en local gardent `hei.ando14@gmail.com` (ADR-0003, inchangé).

## Raisons

- Option A : le nom est le bon, il n'y a aucun co-auteur, et l'adresse appartient au même compte ; l'exigence de fond d'ADR-0003 est respectée.
- Option B écartée : contredit la protection de `detector`, qui prime.
- Option C écartée : effet sur tout le compte, disproportionné pour un écart de forme.

## Conséquences

- Un contrôle d'identité sur l'historique accepte deux adresses : `hei.ando14@gmail.com` pour les commits ordinaires, l'adresse noreply pour les commits de merge.
- Si GitHub change ce comportement, le constat sera noté dans le journal de la tâche suivante, sans nouvel ADR tant que le nom reste correct.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
