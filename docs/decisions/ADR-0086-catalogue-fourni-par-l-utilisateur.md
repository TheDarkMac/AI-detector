# ADR-0086 — Catalogue fourni par l'utilisateur : il remplace le catalogue livré

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T15
- **Exigences liées** : F-26, NF-06, NF-07 ; ES-09 ; M-11, M-12 ; ADR-0029, ADR-0063, ADR-0075

## Contexte

ADR-0029 accepte un catalogue fourni par l'utilisateur et veut que le rapport le signale. Il restait à dire comment il est fourni et comment il se combine avec le catalogue livré, ce qui décide de ce que décrivent la version et l'empreinte inscrites au rapport.

## Options envisagées

### Option A — Il remplace le catalogue livré en entier

Option `--catalogue DOSSIER` et paramètre `catalogue` de `analyser()` : le dossier remplace le catalogue livré, validé de la même façon.

- Avantages : la version, la date et l'empreinte au rapport sont celles d'un seul catalogue, celui qui a servi ; le contrôle est le même que pour le catalogue livré.
- Inconvénients : pour ajouter une règle, l'utilisateur copie tout le catalogue livré.

### Option B — Il complète le catalogue livré

Les règles du dossier s'ajoutent à celles livrées, ou les remplacent identifiant par identifiant.

- Avantages : plus souple pour une règle ajoutée.
- Inconvénients : la version et l'empreinte au rapport décrivent un mélange qu'aucun fichier ne contient ; reproduire l'analyse exige les deux catalogues.

### Option C — Reporté

T15 ne livre que le catalogue intégré ; l'option vient avec une tâche ultérieure.

- Avantages : moins de travail en T15.
- Inconvénients : ADR-0029 reste à moitié réalisé ; aucun moyen d'essayer une règle sans reconstruire l'outil.

## Décision

Option A.

- `vk --catalogue DOSSIER FICHIER...` et `analyser(chemin, catalogue=DOSSIER)` emploient le catalogue du dossier à la place du catalogue livré. Il suit la même forme (ADR-0088), le même schéma et les mêmes contrôles, cohérence avec les modules livrés comprise : il porte les règles « module » que citent leurs manifestes (ADR-0084), et seulement des règles de modules livrés.
- Le catalogue est validé une fois, avant le premier fichier : un catalogue invalide arrête la commande (code 2, comme une commande invalide) ou lève `CatalogueInvalide`, sans qu'aucun fichier soit lu.
- Le rapport inscrit sa version, sa date, son empreinte, et `fourni_par_utilisateur` vrai ; le résumé du terminal ajoute « fourni par l'utilisateur ».
- `vk --regles` affiche la version, la date, l'empreinte et la liste des règles du catalogue employé, livré ou fourni : c'est aussi le moyen de vérifier un catalogue avant de s'en servir.
- La liste des techniques hors de cette version ne fait pas partie du catalogue : un catalogue fourni ne la change pas (ADR-0087).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un rapport doit permettre de reproduire l'analyse (NF-06) ; une empreinte qui ne correspond à aucun dossier ne le permet pas.
- Option C écartée : elle laisse ADR-0029 sans réalisation, pour peu d'économie.

## Conséquences

- Le signalement au rapport porte la défense contre M-11 pour un catalogue fourni : T16 le met en évidence, au même rang que l'isolation réduite.
- Les messages d'erreur peuvent citer le nom d'un fichier du dossier de l'utilisateur, jamais une donnée d'un fichier analysé.
- Une PR qui modifie le catalogue livré peut être essayée sans reconstruire l'outil, en passant le dossier des sources à `--catalogue`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
| 2026-10-28 | Réalisé en T16 : catalogue fourni annoncé parmi les alertes en tête du résumé et du rapport (ADR-0098) |
