# ADR-0152 — Versions de T23 : catalogue 0.3.0 au format 2, modules inchangés

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : l'assistant, sur proposition non posée en question pendant T23 ; à valider par TheDarkMac pendant la revue de la PR de T23
- **Tâche** : T23
- **Exigences liées** : NF-06, NF-07, F-26 ; ADR-0064, ADR-0068, ADR-0085, ADR-0146, ADR-0147

## Contexte

Le catalogue passe au format 2 (ADR-0147) et reçoit trente-huit règles. ADR-0085 dit que `X` augmente avec le format, et qu'une version qui commence à `0.` n'est pas encore celle d'une version stable de l'outil : les deux phrases se contredisent pour un changement de format avant la première version stable. Les règles de T23 lisent les observations de douze modules, dont le code ne change pas ; leurs manifestes permettent déjà « rien de particulier ».

## Options envisagées

### Version du catalogue

- **A — 0.3.0** : tant que la version commence à `0.`, un nouveau format augmente `Y`, comme le fait le versionnage sémantique avant 1.0. Inconvénient : il faut le préciser dans ADR-0085.
- **B — 1.0.0** : lecture littérale de `X`. Inconvénient : annonce une version stable que l'outil n'a pas.

### Versions des modules

- **A — Inchangées** : ni le code ni ce que le manifeste permet de constater ne changent ; les exigences du manifeste restent celles du module (F-10, F-12…) ; les règles de T23 sur ses observations sont listées dans sa fiche. Inconvénient : F-13 et F-14 n'apparaissent pas dans les manifestes.
- **B — Augmentées, avec F-13 et F-14 dans les manifestes** : comme T22 a ajouté F-12. Inconvénient : douze versions nouvelles sans changement du code ni des directions ; T22 l'a fait parce que les directions changeaient (ADR-0146).

## Décision

Option A dans les deux cas.

- Catalogue : format 2, version 0.3.0 du 2026-11-13 (`Y` : règles ajoutées, et nouveau format avant la version stable), description réécrite, nouvelle entrée au registre `docs/catalogue/versions.toml`.
- ADR-0085 précisé : avant 1.0.0, un nouveau format augmente `Y` ; à partir de 1.0.0, `X`.
- Modules : versions, manifestes et code inchangés. La rubrique « Tâche » de leur fiche cite T23, la rubrique « Ce qui déclenche un constat » liste les règles de T23, et l'historique de la fiche le dit.
- Règles : forme d'ADR-0146 (identifiants numérotés à la suite dans chaque module, gabarits en mots, limites qui commencent par la nature de déclaration ou d'absence).

## Raisons

- Catalogue A : un numéro 1.0.0 serait lu comme le premier catalogue stable ; B écartée pour cette raison.
- Modules A : la version d'un module dit ce qu'il observe et ce qu'il permet de constater (ADR-0146) ; rien de cela ne change. Le rapport cite déjà la version du catalogue, qui dit quelles règles ont été appliquées (ADR-0023) ; B écartée parce qu'elle changerait douze versions sans changement de comportement du module.

## Conséquences

- `vk --comparer` voit, entre un rapport de T22 et un rapport de T23 sur le même fichier, un écart de version du catalogue, pas de version des modules.
- La première version stable de l'outil portera le catalogue 1.0.0, au format alors en vigueur.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
