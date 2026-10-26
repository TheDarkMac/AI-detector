# ADR-0017 — Services tiers à base d'IA optionnels, lecture des documents numérisés exclue

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §2 (aucune IA embarquée), F-24, F-63, NF-04, NF-06, NF-16

## Contexte

Le §10 demande si des services tiers de vérification fondés sur l'IA (par exemple des détecteurs de filigranes propriétaires) sont admis, optionnels ou exclus, et si la lecture des documents numérisés (F-63), dont les moteurs courants reposent sur des réseaux de neurones, est admise.

## Options envisagées

### Option A — Services tiers et OCR exclus

- Avantages : principe « sans IA » sans exception ; aucune requête sortante portant sur le contenu.
- Inconvénients : certains filigranes ne se lisent qu'avec le service de leur fournisseur.

### Option B — Services tiers optionnels, OCR exclu

- Avantages : l'utilisateur peut, s'il le choisit, interroger un détecteur de fournisseur, souvent le seul moyen de lire un filigrane propriétaire.
- Inconvénients : un service tiers reçoit en général le contenu ; ses résultats ne sont ni explicables ni reproductibles par l'outil.

### Option C — OCR classique non neuronal admis, services tiers exclus

- Avantages : documents numérisés lus sans réseau de neurones.
- Inconvénients : qualité nettement inférieure ; un texte mal reconnu produirait de faux constats dans le module texte.

## Décision

- **Services tiers à base d'IA : optionnels.** Désactivés par défaut, activés explicitement par l'utilisateur pour une analyse donnée. Leurs résultats figurent dans une rubrique séparée du rapport, marquée « hors principe sans IA », ne sont jamais classés comme preuves et sont exclus de la garantie de reproductibilité (ADR-0023). Aucun service tiers n'est prévu dans le périmètre V1 (ADR-0012).
- **Lecture des documents numérisés : exclue.** Une page PDF sans couche texte native donne une analyse non menée (F-82), avec cette raison ; ses images restent analysées par le module image.

## Raisons

- Option B retenue par TheDarkMac, alors que l'assistant recommandait l'option A. Aucune raison supplémentaire n'a été donnée ; l'avantage présenté avec l'option était de laisser à l'utilisateur l'accès à des vérifications qu'aucune règle écrite ne remplace, sans les mêler aux constats de l'outil.
- Option A écartée : elle interdisait par principe une vérification que l'utilisateur peut juger utile et consentir. Raison de la recommandation initiale, pour mémoire : aucune requête sortante portant sur le contenu, et pas de tension avec NF-16.
- Option C écartée : un OCR de faible qualité produirait des constats texte faux, pire qu'une analyse non menée.

## Conséquences

- **Tension avec NF-16** : NF-16 interdit qu'une requête sortante emporte le fichier, ce qu'exige en général un service tiers. La décision suppose de reformuler NF-16 : « sauf service tiers activé explicitement par l'utilisateur, avec son consentement pour ce fichier (NF-04) ». Reformulation inscrite au registre des arbitrages, à faire valider par l'auteur du cahier.
- T03 analyse ce flux sortant (fuite du contenu, dépendance à un fournisseur).
- T04 prévoit un point d'extension pour ces services, sans en implémenter en V1.
- L'articulation avec le cahier « Vérification assistée par IA open source » n'est pas tranchée : ce cahier n'est pas disponible (question 3 du §8 de l'analyse). L'export machine (ADR-0025) permettra à un autre outil d'appeler celui-ci.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : flux vers les services tiers analysé au modèle de menace (M-15, RS-04), politique fixée par ADR-0033 (T03) |
| 2026-10-26 | Renvoi : point d'extension des services tiers décrit par ADR-0042 (T04) |
