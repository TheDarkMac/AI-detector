# ADR-0280 — Rapports publiés tels que mesurés, écarts corrigés ensuite

- **Statut** : Accepté
- **Date** : 2026-11-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; emplacement des rapports précisé par l'assistant
- **Tâche** : T101
- **Exigences liées** : §8 et §9 (livrables 4 et 5) du cahier, NF-09 ; M-33 ; ADR-0016, ADR-0104, ADR-0105, ADR-0274

## Contexte

Le banc signale comme écarts, et fait échouer l'évaluation pour : un arrêt brutal, deux analyses différentes d'un même fichier, un indice dont le niveau dépasse sa mesure, une preuve qui a un faux positif, un taux par fichier au-delà de la cible (ADR-0104, ADR-0113). La première mesure sur le corpus de référence pouvait en montrer. Les corriger dans T101 puis remesurer la même partie reviendrait à régler l'outil sur la partie qui sert à le juger (M-33, ADR-0016).

## Options envisagées

### Option A — Publier la mesure telle quelle, corriger ensuite (recommandée)

Les rapports sont publiés tels que le banc les écrit ; chaque écart est décrit au journal de T101 ; les défauts de code vont dans des correctifs séparés, avec un erratum ; un seuil ne se règle que sur la partie calibrage.

- Avantages : la mesure publiée est celle de l'outil tel qu'il était ; aucune correction n'est faite en regardant la partie évaluation.
- Inconvénients : des écarts restent au rapport publié jusqu'aux correctifs.

### Option B — Corriger dans T101, puis tout remesurer

- Avantages : un rapport publié sans écart.
- Inconvénients : T101 s'allonge sans borne ; corriger en regardant les faux positifs de la partie évaluation adapte l'outil à elle, et ses taux ne mesurent plus rien de neuf.

## Décision

Option A :

- **Rapports publiés** : `docs/verification/evaluations/reference-1.0.0-catalogue-0.20.1/` (première passe, qui fonde les niveaux) et `docs/verification/evaluations/reference-1.0.0-catalogue-0.21.0/` (seconde passe, avec le catalogue livré, ADR-0278), chacun avec `evaluation.json` et `evaluation.md` tels que le banc les a écrits, sans retouche ; les journaux de reprise ne sont pas publiés ;
- **Écarts** : chacun est décrit au journal de T101, avec sa cause quand elle est connue ; un défaut de code devient un correctif séparé (branche, PR, erratum) ; un écart de niveau disparaît par l'inscription d'ADR-0278, qui applique la règle d'ADR-0018 ;
- **Seuils** : aucun seuil, aucune liste, aucune condition n'est modifié d'après la partie évaluation ; un recalibrage emploie la partie calibrage (ADR-0016), dans une tâche à part ;
- **Lecture** : la page `docs/verification/evaluations/README.md` dit ce que contient chaque dossier, et rappelle les limites de la mesure (corpus réel, effectifs par format, vérité des générés déclarés, ADR-0273).

## Raisons

- Option A retenue : un taux publié n'a de valeur que mesuré sur des fichiers qui n'ont pas servi à régler l'outil.
- Option B écartée : elle publierait un rapport sans écart au prix de sa valeur.
- Deux dossiers plutôt qu'un : la première passe est la mesure qui fonde les niveaux ; la seconde, celle de l'outil livré ; les deux sont nécessaires pour vérifier ADR-0278.

## Conséquences

- Les fiches citent la seconde passe (ADR-0279).
- Un correctif qui change un constat demande une nouvelle évaluation, publiée dans un nouveau dossier ; les rapports publiés ne sont jamais réécrits.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-26 | Création |
