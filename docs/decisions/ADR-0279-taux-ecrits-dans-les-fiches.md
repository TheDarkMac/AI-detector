# ADR-0279 — Taux de chaque fiche écrits par le banc, entre deux marqueurs

- **Statut** : Accepté
- **Date** : 2026-11-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; forme du bloc précisée par l'assistant
- **Tâche** : T101
- **Exigences liées** : NF-09, §8 et §9 (livrable 4) du cahier ; ADR-0104, ADR-0105, ADR-0268 ; A-54

## Contexte

Chaque fiche technique a une rubrique « Taux d'erreur » (NF-09), rédigée jusqu'ici sans corpus : elle dit ce que les essais de chaque tâche ont vérifié, et que rien n'est mesuré. Les fiches sont copiées dans le paquet et affichées par `vk --fiche` (ADR-0268). T101 doit y mettre les taux mesurés, pour 25 modules, chacun sur cinq catégories et plusieurs règles.

## Options envisagées

### Option A — Bloc écrit par une commande du banc, contrôlé par les tests (recommandée)

`python -m banc.fiches --taux EVALUATION.json` écrit dans chaque fiche, entre deux marqueurs, les tableaux de son module tirés du rapport, puis recopie les fiches dans le paquet.

- Avantages : les chiffres de la fiche sont ceux du rapport publié, et un test le vérifie ; une nouvelle évaluation se reporte par une commande.
- Inconvénients : un bloc dans un format fixé, moins lisible qu'un texte rédigé.

### Option B — Résumé rédigé à la main, avec un lien vers le rapport

- Avantages : texte adapté à chaque technique.
- Inconvénients : 25 fiches à recopier à chaque évaluation, sans garantie d'accord avec le rapport.

## Décision

Option A :

- le bloc s'ouvre par `<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->` et se ferme par `<!-- Fin des taux mesurés. -->`, en tête de la rubrique ; s'il existe, il est remplacé, sinon ajouté ;
- il donne : date, corpus et partie, lien vers le rapport Markdown publié, version du module, de l'outil et du catalogue ; un tableau par catégorie (fichiers, non applicables, non analysables, faux positifs, faux négatifs, confusions), chaque taux avec son effectif et son intervalle de Wilson à 95 % ; un tableau des règles de preuve et d'indice du module (taux de faux positifs, niveau permis, niveau au catalogue) ;
- le texte rédigé de la rubrique, hors des marqueurs, reste à la main : il dit comment lire ces chiffres pour la technique, et ce que les essais antérieurs ont vérifié ;
- la commande refuse un rapport non publiable ; un test vérifie que le bloc de chaque fiche est celui que donne le rapport publié de T101.

## Raisons

- Option A retenue : l'accord entre fiche et rapport est vérifié, non espéré.
- Option B écartée : 25 recopies manuelles à chaque évaluation divergeraient tôt ou tard.
- Texte rédigé gardé hors des marqueurs : un tableau ne dit pas ce qu'un faux positif signifie pour une technique donnée, ni pourquoi une catégorie n'a pas d'effectif.

## Conséquences

- Une fiche ne se modifie plus à la main entre les marqueurs ; une modification de fiche demande toujours `python -m banc.fiches` (ADR-0268), que `--taux` lance aussi.
- Le lien vers le rapport est relatif au dépôt ; dans la copie du paquet (`vk --fiche`), il ne mène nulle part hors du dépôt, comme les autres liens des fiches.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-26 | Création |
