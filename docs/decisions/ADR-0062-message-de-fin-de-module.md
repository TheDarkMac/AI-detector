# ADR-0062 — Message « module » : fin de chaque module dans le protocole

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T12
- **Exigences liées** : F-25, F-82, NF-03 ; ES-04 ; ADR-0036, ADR-0054, ADR-0059, ADR-0060

## Contexte

Le processus principal construit la couverture (ADR-0059) : pour chaque module, appliqué, partiel, non mené ou non applicable. Les messages fixés en T11 (`isolation`, `observation`, `constat`, `non_menee`, `versions`, `fin`) ne lui permettent pas de distinguer « non applicable à ce format » de « appliqué sans résultat », ni de savoir, si le processus de travail s'arrête, quels modules étaient terminés.

## Options envisagées

### Option A — Un message « module » après les résultats de chaque module

`{"type": "module", "module": "<identifiant>", "applicable": true | false}`.

- Avantages : ajout minimal ; le principal sait quels modules sont terminés et lesquels étaient applicables ; les messages par élément de T11 restent inchangés et bornés.
- Inconvénients : un type de message de plus à valider et à ordonner.

### Option B — Un seul message par module

Un message regroupe toutes les observations, constats et analyses non menées d'un module.

- Avantages : la fin du module est implicite.
- Inconvénients : remplace les messages par élément de T11 ; un module volumineux donne un message volumineux, plus difficile à borner.

### Option C — Aucun ajout, le principal déduit

- Avantages : protocole inchangé.
- Inconvénients : « non applicable » et « appliqué sans résultat » se confondent ; après un arrêt, impossible de savoir quels modules avaient fini.

## Décision

Option A. Ordre du protocole, imposé par le processus principal :

1. `isolation`, une seule fois, en premier ;
2. pour chaque module actif, **dans l'ordre de la configuration** : ses résultats (`observation`, `constat`, `non_menee` portant ce module), puis son message `module` ; un module non applicable n'a aucun résultat ;
3. à tout moment après l'isolation : `non_menee` sans module (fichier entier : `format_partiel`, `fichier_tronque`, `limite_depassee`) ;
4. `versions`, une seule fois ;
5. `fin`, après le message `module` du dernier module et les versions ; plus rien ensuite.

L'état de chaque module terminé en découle : non applicable ; appliqué sans analyse non menée ; partiel s'il a des résultats et une analyse non menée ; non mené s'il n'a qu'une analyse non menée.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle défait les messages bornés de T11 pour un gain que le message de fin apporte à moindre coût.
- Option C écartée : la couverture serait fausse, et un arrêt ne pourrait pas être rapporté module par module.

## Conséquences

- `messages.schema.json` gagne la définition `module`. `VERSION_SCHEMA` reste `0.1.0` : aucune version du schéma n'a été publiée, sa numérotation sera fixée à la première publication (T16, ADR-0054).
- Après un arrêt (délai, limite, message invalide, arrêt du processus), les modules terminés gardent leurs résultats ; chacun des autres devient non mené avec la raison de l'arrêt, et une analyse non menée sans module porte la même raison : le rapport est interrompu (ADR-0056).
- Le modèle de données (§8) et l'architecture (§6) décrivent ce message.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Précisé par ADR-0071 (T13) : le message `module` porte la partie ; un message par module et par partie du périmètre |
