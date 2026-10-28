# ADR-0109 — Forme du test de reproductibilité : tests, banc et commande `vk --comparer`

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac (question posée pendant T18 ; option différente de la recommandation)
- **Tâche** : T18
- **Exigences liées** : NF-06, P-05, critère du §8 ; ADR-0023, ADR-0099, ADR-0108

## Contexte

T18 livre le test de reproductibilité. Aucun module d'analyse n'est encore livré : un test sur les seuls échantillons des tests ne vérifierait pas les techniques à venir sur le corpus de référence (T100). Il fallait choisir où le test vit.

## Options envisagées

### Option A — Tests et contrôle du banc

`tests/test_reproductibilite.py` en CI, et le banc d'évaluation qui analyse chaque fichier deux fois et compte une différence comme un écart.

- Avantages : chaque future technique est vérifiée sur le corpus de référence, sans test à écrire.
- Inconvénients : le banc analyse deux fois plus.

### Option B — Tests seuls

- Avantages : rien ne change au banc.
- Inconvénients : chaque technique devra ajouter ses propres cas.

### Option C — Tests, banc, et une commande qui compare deux rapports

En plus de l'option A, `vk --comparer A B` compare deux rapports JSON du même fichier.

- Avantages : un utilisateur, un expert ou un relecteur vérifie lui-même la reproductibilité de deux rapports, produits sur deux postes ou à deux dates ; la CI s'en sert pour comparer les systèmes.
- Inconvénients : une fonction nouvelle, hors du découpage de T18 ; une sortie de plus à tenir sans fuite de données identifiantes.

## Décision

Option C, choisie par TheDarkMac ; l'assistant recommandait l'option A, au motif que la commande est une fonction nouvelle hors du découpage. Aucune raison supplémentaire n'a été donnée.

## Raisons

- Option C retenue : la reproductibilité devient vérifiable par l'utilisateur, pas seulement par le projet ; la même commande sert la CI entre systèmes (ADR-0110).
- Option A écartée : elle ne donne aucun moyen de comparer deux rapports produits hors du dépôt.
- Option B écartée : elle laisse le corpus de référence sans contrôle de reproductibilité.

## Conséquences

- Écart au découpage : T18 ajoute une option à la ligne de commande (`--comparer`), décrite par ADR-0112.
- Le banc analyse chaque fichier deux fois (ADR-0113).
- La documentation utilisateur (T103) explique la commande et ses codes.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
