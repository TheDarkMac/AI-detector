# ADR-0113 — Banc : deux analyses par fichier, un défaut de reproductibilité est un écart

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T18, validée au début de T20 (PR de T18 mergée avant la validation)
- **Tâche** : T18
- **Exigences liées** : NF-06, P-05, critère du §8 ; ADR-0104, ADR-0105, ADR-0108, ADR-0109, ADR-0112

## Contexte

ADR-0109 fait vérifier la reproductibilité par le banc d'évaluation. Il restait à dire ce que le banc compare, ce qu'il retient et comment il le signale.

## Options envisagées

### Option A — Deux analyses de chaque fichier, mesures sur la première

- Avantages : chaque fichier du corpus est vérifié ; les mesures restent celles d'une analyse, comme avant T18.
- Inconvénients : durée doublée.

### Option B — Option du banc, désactivée par défaut

- Avantages : banc aussi rapide qu'avant.
- Inconvénients : un rapport d'évaluation publié pourrait ne pas avoir vérifié la reproductibilité.

## Décision

Option A.

- Deux analyses par fichier, dans l'ordre du manifeste, chacune dans son processus de travail ; mesures sur la première.
- Deux analyses : rapports comparés en entier, masquage levé (ADR-0108, ADR-0112) ; seul un **défaut** (résultats différents dans la garantie) est relevé. Deux refus : même motif attendu. Un refus et une analyse : relevé.
- Un arrêt brutal à l'une des deux est un arrêt brutal, compté comme avant.
- Chaque fichier non reproduit est un écart de l'évaluation, dans les deux parties du corpus, comme un arrêt brutal : `<chemin> : deux analyses différentes (<au plus cinq chemins>)` ; le document JSON compte `fichiers.non_reproduits` et le Markdown le cite.

## Raisons

- Option A retenue : un taux publié n'a de sens que si l'analyse qui l'a produit se refait.
- Option B écartée : la vérification serait oubliée.
- Mesures sur la première analyse : en cas d'écart, l'évaluation échoue de toute façon ; les taux ne dépendent pas du choix.

## Conséquences

- Une tentative d'accès au réseau peut être notée deux fois pour un fichier.
- T100 et T101 héritent de la double analyse.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
| 2026-10-28 | Validé par TheDarkMac au début de T20, la PR de T18 ayant été mergée sans changement de statut (ERR-0007) : statut « Accepté » |
