# ADR-0149 — Constat d'une incohérence interne : information neutre

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T23
- **Exigences liées** : F-13, F-80, F-81 ; ES-20 ; ADR-0018, ADR-0021, ADR-0022, ADR-0055, ADR-0058, ADR-0142

## Contexte

Une incohérence interne (date impossible, création postérieure à la modification, appareil photo déclaré avec un générateur nommé ou des dimensions de générateur) dit qu'une déclaration du fichier au moins est fausse. Elle ne dit pas laquelle, ni pourquoi : horloge déréglée, logiciel qui recopie ou réécrit un champ, retouche, falsification. ADR-0022 ne permet une direction que si la technique distingue les hypothèses ; aucun corpus ne le mesure avant T100. Il fallait choisir la nature de ces constats.

## Options envisagées

### Option A — Information neutre

Catégorie « information neutre », direction « rien de particulier », fondement « déclaration ».

- Avantages : dit ce qui est établi, une contradiction entre déclarations, sans prêter une cause ; respecte ADR-0022 sans mesure ; ne change aucun manifeste (« rien de particulier » est déjà permis à tous les modules).
- Inconvénients : le résumé compte ces constats parmi les informations neutres, pas parmi les indices.

### Option B — Indice faible, retouche

Catégorie « indice », direction « retouche », niveau « faible », non évalué.

- Avantages : le résumé les compte comme indices de retouche.
- Inconvénients : suppose que l'incohérence vient d'une modification, ce que la règle ne distingue pas d'une horloge mal réglée ou d'un logiciel ; le manifeste de chaque module concerné devrait admettre « retouche ».

## Décision

Option A.

- Chaque règle d'incohérence de T23 est une information neutre, de fondement `declaration`, sans niveau (ADR-0058, invariant 4) ; sa phrase dit les deux valeurs et qu'une des deux au moins est inexacte, ou que les deux déclarations se contredisent ou décrivent deux étapes.
- Sa première limite le dit : la règle ne dit pas laquelle des causes possibles a produit l'incohérence.
- Le nom d'un générateur dans un champ logiciel reste aussi l'indice faible de T22 (ADR-0144) : la règle d'incohérence s'y ajoute, elle ne le remplace pas.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle attribuerait une hypothèse que la règle ne distingue pas, ce qu'ADR-0022 interdit, et la retouche n'est qu'une des causes possibles.

## Conséquences

- Le taux de faux positifs par fichier, qui ne compte que les indices modérés et forts (ADR-0104), ne change pas.
- Une mesure sur le corpus (T100) pourra montrer qu'une incohérence distingue une hypothèse ; la règle deviendra alors un indice, dans une nouvelle version.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création |
