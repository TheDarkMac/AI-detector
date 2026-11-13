# ADR-0142 — Constats tirés d'une déclaration du fichier : indices faibles, dirigés par ce que le champ déclare

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T22
- **Exigences liées** : F-11, F-12, F-14, F-81 ; ES-20 ; C-02 ; ADR-0018, ADR-0021, ADR-0022, ADR-0055, ADR-0058, ADR-0064, ADR-0084, ADR-0101

## Contexte

T22 écrit les premières règles du catalogue : la propriété IPTC `DigitalSourceType` (F-11), les paramètres de génération et le nom du logiciel (F-12). Toutes lisent une **déclaration** du fichier, que quiconque peut écrire ou effacer (cas d'abus C-02). ES-20 et ADR-0021 bornent déjà leur catégorie : une déclaration n'est jamais une preuve, seulement un indice ou une information neutre.

ADR-0022 ajoute une contrainte : une technique ne produit la direction « origine IA » que si elle distingue la génération des transformations banales sur la partie évaluation du corpus. Aucun corpus de référence n'existe avant T100 : aucune règle ne peut être mesurée. Il fallait choisir entre un indice dirigé et une information neutre.

Une règle « moteur » ne porte qu'une direction permise par le manifeste de son module (ADR-0064, ADR-0084). Les douze modules de métadonnées n'admettent que « rien de particulier » depuis T20 et T21.

## Options envisagées

### Option A — Indice faible, dirigé par ce que le champ déclare

Catégorie « indice », fondement « déclaration », niveau « faible », non évalué. La direction suit la déclaration : « origine IA » pour une génération, « retouche » pour une retouche par IA (ADR-0143). Les manifestes des modules concernés admettent ces directions.

- Avantages : le résumé compte ces indices par direction, ce que F-11 et F-12 demandent de repérer ; un indice faible ne compte pas dans le taux de faux positifs par fichier, qui ne retient que les niveaux modéré et fort (ADR-0018, ADR-0104), et la cible par fichier n'en dépend donc pas ; la mesure du corpus (T100) pourra relever le niveau, ou montrer qu'il faut le laisser faible.
- Inconvénients : lecture d'ADR-0022 à écrire : la distinction vient du contenu de la déclaration, pas d'une mesure.

### Option B — Information neutre jusqu'au corpus

Catégorie « information neutre », direction « rien de particulier » : « le fichier déclare… ».

- Avantages : lecture stricte d'ADR-0022 ; aucun manifeste ne change.
- Inconvénients : le résumé ne compte aucun indice d'origine IA, même pour un fichier qui déclare sa génération ; F-11 est tenue dans le corps du rapport, pas dans sa synthèse ; il faudra changer toutes les règles quand le corpus existera.

## Décision

Option A.

- Chaque règle de T22 est un indice, de fondement `declaration`, de niveau `faible`, sans évaluation : le rapport la signale « non évaluée » (ADR-0018). Elle est appliquée par le moteur (ADR-0084) : aucun module n'émet lui-même de constat.
- Direction : celle de ce que déclare le champ (ADR-0143, ADR-0144, ADR-0145).
- Les manifestes des douze modules de métadonnées admettent `origine_ia` en plus de `rien_de_particulier` ; celui de `xmp` admet aussi `retouche`. Leurs exigences citent F-12, F-11 en plus pour `xmp`. Version de chaque module augmentée (ADR-0146).
- Lecture d'ADR-0022 pour une déclaration : la règle ne prétend pas distinguer la génération d'une transformation banale, elle dit ce que le fichier déclare ; une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer. La rubrique « hypothèses distinguées » de chaque fiche le dit, et laisse la mesure au corpus (T100) ; tant qu'elle manque, le niveau reste « faible ».

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle tait dans la synthèse ce que le fichier déclare de lui-même, alors que c'est l'indice le plus direct que l'outil puisse lire dans des métadonnées ; le risque qu'ADR-0022 veut éviter, attribuer à l'IA une simple recompression, ne se pose pas pour une règle qui lit une déclaration de génération.
- Niveau faible imposé : ADR-0018 et ADR-0107 le veulent pour une règle sans mesure ; le chargement du catalogue refuse tout autre niveau.

## Conséquences

- Un fichier qui déclare sa génération porte au rapport un ou plusieurs indices faibles vers l'origine IA ; sans déclaration, aucun constat (F-14).
- Le taux par fichier et sa cible (ADR-0101) ne changent pas tant que les règles restent faibles ; le banc compte leurs faux positifs dès qu'un corpus le permet.
- Une déclaration effacée ou forgée échappe à ces règles ou les trompe : c'est une limite de chaque règle, inscrite au catalogue (ADR-0019).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création |
