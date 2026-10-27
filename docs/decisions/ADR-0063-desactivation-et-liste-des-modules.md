# ADR-0063 — Désactivation des modules et liste en ligne de commande

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T12
- **Exigences liées** : NF-10, F-25, F-82 ; ADR-0042, ADR-0056, ADR-0059

## Contexte

ADR-0042 veut que chaque module puisse être désactivé par l'utilisateur, et que le rapport le dise. En T12, la ligne de commande n'a pas encore de commande d'analyse : elle n'affiche que sa version et son aide.

## Options envisagées

### Option A — Dans le moteur, et `--modules` en ligne de commande

Le moteur accepte une liste de modules désactivés. La ligne de commande gagne `--modules`, qui liste les modules livrés et leur version. L'option de désactivation arrive avec la commande d'analyse.

- Avantages : le mécanisme est en place et testé ; l'utilisateur peut déjà voir ce que l'outil contient.
- Inconvénients : la désactivation n'est pas encore accessible en ligne de commande.

### Option B — Dans le moteur seulement

- Avantages : aucune modification de la ligne de commande.
- Inconvénients : rien ne montre à l'utilisateur quels modules existent.

## Décision

Option A.

- `executer(descripteur, manifestes, desactives)` accepte les identifiants des modules désactivés. Un identifiant inconnu est refusé (`ModuleInconnu`), avec la liste de ceux qui le sont : une faute de frappe ne doit pas laisser croire qu'un module a été désactivé.
- Un module **qui requiert un module désactivé est désactivé lui aussi** : il ne pourrait pas s'exécuter.
- Un module désactivé n'est pas envoyé dans la configuration : le processus de travail ne l'exécute pas. Son code est tout de même importé, comme celui des autres, avant le verrouillage (ADR-0036) : la liste des modules actifs n'arrive qu'après.
- Au rapport, il figure dans la couverture à l'état « non mené », avec l'analyse non menée `module_desactive`.
- `voight-kampff --modules` affiche une ligne `<identifiant> <version>` par module livré, ou « Aucun module d'analyse livré dans cette version. ».

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : l'utilisateur doit pouvoir connaître les modules qu'il pourra désactiver.
- Désactivation par dépendance : sinon le module dépendant serait exécuté sans ce dont il a besoin.
- Code importé même désactivé : n'importer que les modules actifs demanderait d'envoyer la configuration avant le verrouillage, donc avant le message d'isolation, ce que l'ordre d'ADR-0036 interdit. Les modules sont livrés avec l'outil : les importer n'exécute pas d'analyse.

## Conséquences

- La commande d'analyse (à partir de T13) ajoute l'option de désactivation, qui appelle ce mécanisme.
- La documentation utilisateur (T103) explique la désactivation et sa trace au rapport.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Réalisé en T13 : option `--desactiver MODULE` de la commande d'analyse (ADR-0073) |
