# ADR-0181 — Empreinte des tables de quantification : point d'extension du catalogue

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (écriture canonique précisée par l'assistant)
- **Tâche** : T40
- **Exigences liées** : F-26, F-30 ; A-32 ; ADR-0038, ADR-0040, ADR-0084, ADR-0089, ADR-0180

## Contexte

Les familles de tables retenues par ADR-0180 se calculent (une base mise à l'échelle par une qualité ou un qscale) : leur place est dans le code du module, comme les tables de libjpeg depuis T24. Les tables d'un appareil ou d'un logiciel comme Photoshop sont fixes, relevées une à une ; F-26 et A-32 demandent que de telles listes de référence soient dans le catalogue, versionnées, et s'ajoutent sans nouvelle version de l'outil. Le complément de T40 (ADR-0180) en livrera.

## Options envisagées

### Option A — Empreinte des tables, nommée par une règle

Le module observe `image.jpeg.empreinte_tables`, le SHA-256 d'une écriture canonique et documentée des tables ; une règle du catalogue nomme des tables par `parmi`.

- Avantages : aucun changement du format du catalogue, du chargeur ni du protocole ; les tests existants (`parmi`, jusqu'à 4 096 valeurs) suffisent ; l'empreinte se recalcule hors de l'outil.
- Inconvénients : une empreinte ne se lit pas ; la règle doit dire en clair de quelles tables il s'agit et d'où elles viennent.

### Option B — Fichier `tables.toml` au catalogue

Tables en clair avec leurs sources, format 4 du catalogue, transmises au processus de travail.

- Avantages : tables lisibles dans le catalogue.
- Inconvénients : schéma, chargeur, protocole et format à changer, sans aucune table fixe à livrer dans T40.

### Option C — Aucun point d'extension dans T40

- Avantages : rien à écrire.
- Inconvénients : le complément devrait ajouter le point d'extension, et toute table fixe une nouvelle version du module.

## Décision

Option A, avec cette écriture canonique (précision de l'assistant) : une ligne par table en vigueur au premier balayage, dans l'ordre des identifiants, `<identifiant>:<v1>,<v2>,…,<v64>`, les valeurs en décimal dans l'ordre du segment DQT ; lignes séparées par un saut de ligne, sans saut final, en ASCII ; SHA-256 en hexadécimal minuscule (ADR-0040). La précision (huit ou seize bits) n'en fait pas partie. L'empreinte est observée pour toutes tables, reconnues ou non. Aucune table fixe n'est livrée par T40.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un nouveau format pour un fichier vide ; elle reste possible si les tables fixes deviennent nombreuses au point qu'une empreinte ne se vérifie plus à la main.
- Option C écartée : elle reporterait sur le complément un changement du module.
- Précision exclue : elle dit comment les valeurs sont écrites (T.81, B.2.4.1), pas ce qu'elles sont ; une table relevée à partir de ses valeurs, sans le fichier, garde ainsi la même empreinte. L'ordre zigzag est celui du fichier, que tout lecteur de DQT donne sans conversion.

## Conséquences

- Une règle du complément de T40, ou d'un catalogue fourni, nomme des tables fixes sans nouvelle version de l'outil (F-26).
- Toute table au rapport porte une empreinte, même inconnue : elle se compare entre deux fichiers, ou à une liste tenue hors de l'outil.
- Changer l'écriture canonique changerait toutes les empreintes : ce serait une nouvelle version du module et de chaque règle qui les cite.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
