# ADR-0060 — Résultats d'un module en erreur : écartés

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T12
- **Exigences liées** : NF-03, F-82 ; ADR-0042, ADR-0056, ADR-0059

## Contexte

ADR-0042 veut qu'une erreur dans un module ne touche que ce module : ses analyses deviennent « non menées », les autres continuent. Il ne dit pas ce que deviennent les observations et constats que le module avait déjà produits avant son exception. ADR-0059 donne deux états possibles : « partielle » (appliquée, une partie non menée) et « non menée ».

## Options envisagées

### Option A — Tout écarter

Le moteur garde les résultats d'un module en mémoire jusqu'à ce qu'il rende la main. Si le module lève une exception, ils sont jetés ; la technique passe « non menée », raison `erreur_module`.

- Avantages : simple et déterministe ; aucun constat ne repose sur une analyse inachevée ; l'état « partielle » garde son sens premier, une partie du fichier non lue (A-25).
- Inconvénients : les observations valides relevées avant l'erreur sont perdues pour le lecteur.

### Option B — Garder, état « partielle »

Les résultats déjà produits restent au rapport, la technique passe « partielle ».

- Avantages : plus d'information.
- Inconvénients : un constat peut reposer sur une analyse que le module n'a pas pu finir ; « partielle » mêlerait deux sens (partie du fichier non lue, module arrêté en route).

## Décision

Option A : les résultats d'un module en erreur sont **écartés** ; la technique est « non menée », raison `erreur_module`.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un rapport ne doit pas porter de constat tiré d'une analyse inachevée, et « partielle » doit garder un seul sens.

## Conséquences

- Le processus de travail garde les résultats de chaque module dans son contexte (ADR-0061) et ne les envoie qu'au retour du module. Une exception, ou un dépassement des tailles du protocole (`limite_depassee`), remplace ces résultats par une seule analyse non menée.
- Le processus principal le vérifie de son côté : une raison du moteur (`erreur_module`, `limite_depassee`) n'est admise que pour un module qui n'a rien envoyé d'autre, et rien n'est admis ensuite pour ce module (ADR-0065).
- Le même principe vaut pour un arrêt du processus de travail : les modules terminés gardent leurs résultats, le module en cours et les suivants deviennent non menés, avec la raison de l'arrêt (ADR-0062).
- Un module qui peut lire une partie du fichier seulement le dit lui-même (`format_partiel`, `fichier_tronque`) et garde ses résultats : c'est l'état « partielle ».

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
