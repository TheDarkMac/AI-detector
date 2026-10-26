# Documentation du projet

Toute règle, convention, étape, décision et erreur du projet est consignée ici. C'est la seule source de référence : ce qui n'est pas écrit dans `docs/` n'est pas une règle du projet.

## Arborescence

| Dossier | Contenu | Quand écrire |
| --- | --- | --- |
| [`00-cahier-des-charges/`](00-cahier-des-charges/) | Cahier des charges source, versionné, non modifié | À chaque nouvelle version reçue |
| [`00-plan/`](00-plan/) | Découpage du travail en tâches | À chaque changement de plan |
| [`decisions/`](decisions/) | Décisions d'architecture et de méthode (ADR) : option retenue, options écartées, raisons | Dès qu'un choix est fait, ou qu'une option est rejetée |
| [`journal/`](journal/) | Journal d'étape : une entrée par tâche, ce qui a été fait et dans quel ordre | Dans la branche de chaque tâche |
| [`errata/`](errata/) | Erreurs d'analyse, de documentation ou d'exécution, et leur correction | Dès qu'une erreur est constatée |

[`01-analyse/`](01-analyse/) contient l'analyse critique du cahier des charges (T01) ; [`02-arbitrages/`](02-arbitrages/) le registre des arbitrages des points ouverts (T02), qui renvoie aux ADR.

Les dossiers suivants seront créés par les tâches qui les concernent : `modele-de-menace/` (T03), `techniques/` (fiches par technique, NF-09).

## Distinction entre les trois registres

- **Décision (ADR)** : un choix qui engage la suite. Il reste valable tant qu'un ADR ultérieur ne le remplace pas.
- **Journal** : le récit d'une tâche. Il ne décide rien ; il renvoie aux ADR et aux errata.
- **Erratum** : la trace d'une erreur. On ne réécrit jamais l'histoire en silence : le document fautif est corrigé *et* l'erratum explique quoi, pourquoi et comment.

Les documents vivants (découpage, catalogue, etc.) portent en plus une table « Historique des modifications ».

## Langue

La documentation est rédigée en français (ADR-0004).
