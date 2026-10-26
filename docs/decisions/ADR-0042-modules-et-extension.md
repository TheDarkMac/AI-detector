# ADR-0042 — Modules d'analyse : découverte interne, manifeste déclaratif

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : §2 (modularité), NF-03, NF-09, NF-10 ; F-25, F-82 ; menaces M-31 ; ADR-0017, ADR-0022

## Contexte

Le principe de modularité et NF-10 demandent qu'une technique ou un format s'ajoute, se retire ou se désactive sans toucher aux autres. ADR-0017 demande un point d'extension pour d'éventuels services tiers, sans en livrer en V1. Le rapport doit dire quelles techniques ont été appliquées (F-25) et lesquelles n'ont pas été menées (F-82) : le processus principal doit connaître les modules **sans importer leur code**, puisque ce code ne s'exécute que dans le processus de travail (ADR-0028).

## Options envisagées

### Option A — Découverte interne, manifeste déclaratif

- Avantages : ajouter un module, c'est ajouter un dossier ; seuls les modules livrés avec l'outil sont chargés ; le manifeste se lit sans exécuter de code.
- Inconvénients : un tiers ne peut pas ajouter un module sans modifier le paquet.

### Option B — Extensions tierces (points d'entrée des paquets)

- Avantages : ouvert à des modules publiés à part.
- Inconvénients : n'importe quel paquet installé dans l'environnement peut injecter du code d'analyse et des constats (B6, B7, M-31).

### Option C — Liste centrale explicite

- Avantages : le plus simple.
- Inconvénients : chaque ajout modifie un fichier commun, ce que NF-10 veut éviter à la lettre.

## Décision

- Chaque technique est un **sous-paquet** de `modules/`, qui contient un **manifeste déclaratif** en TOML (ADR-0038) : identifiant, version, formats traités, exigences du cahier, règles du catalogue employées, fiche technique associée (NF-09, ADR-0022).
- Le processus principal lit les manifestes, les valide par schéma et en tire la couverture (F-25, F-82), **sans importer le code** des modules. Seul le processus de travail importe ce code.
- La découverte se limite au dossier `modules/` du paquet de l'outil ; **aucune extension tierce** n'est chargée en V1.
- Chaque module peut être désactivé par l'utilisateur ; le rapport le dit.
- Une erreur dans un module ne touche que ce module : ses analyses deviennent « non menées », avec la raison ; les autres continuent (NF-03, T12).
- Le point d'extension des services tiers (ADR-0017) est une interface documentée, **sans implémentation en V1**. Comme un tel service reçoit le fichier par le réseau, il ne pourra pas s'exécuter dans le processus de travail ; son mode d'exécution sera fixé avec le premier service, par un nouvel ADR, avec révision du modèle de menace.

## Raisons

- Option A retenue : elle satisfait NF-10 sans ouvrir l'analyse à du code non livré par le projet.
- Option B écartée : M-31 ; elle pourra être reconsidérée, avec signature ou liste d'extensions autorisées, par un nouvel ADR.
- Option C écartée : NF-10.

## Conséquences

- T12 réalise la découverte, la validation des manifestes, l'activation et l'isolation des erreurs ; T11 fixe la forme des observations rendues par un module.
- Chaque tâche de technique livre son manifeste avec son code, ses tests et sa fiche.
- Un module qui a besoin du résultat d'un autre (images extraites d'un PDF, T53) le déclare dans son manifeste ; l'acheminement se fait dans le même processus de travail.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : forme de l'observation (ADR-0058) ; états des techniques dans la couverture (ADR-0059) (T11) |
