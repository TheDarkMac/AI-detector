# ADR-0276 — Manifeste au dépôt, version 1.0.0, description publiée ; pas de sous-catégorie « références »

- **Statut** : Proposé
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T100, à valider pendant la revue de la PR de T100
- **Tâche** : T100
- **Exigences liées** : §8 et §9 (livrable 5) du cahier, ES-22, NF-16 ; M-33 ; ADR-0103, ADR-0105, ADR-0272 à ADR-0275 ; A-13, A-56

## Contexte

Les fichiers du corpus restent hors du dépôt (ADR-0272). Il faut décider ce qui, au dépôt, décrit le corpus et tient lieu du livrable 5 pour qui n'a pas les fichiers ; ce que le manifeste dit de chaque fichier, sans données personnelles inutiles ; comment la description reste vraie ; et si le corpus a besoin de la sous-catégorie « références » qu'A-56 proposait.

## Options envisagées

### Option A — Manifeste complet au dépôt, écrit par un script, description et effectifs publiés, contrôlés par des tests (proposée)

`banc/reference/corpus.toml` (une entrée par fichier : chemin, empreinte, catégorie, partie, groupe, origine, transformation, provenance), `banc/reference/effectifs.json` (comptes et fichiers écartés), `docs/verification/corpus-de-reference.md` (description lisible). Des tests relisent le manifeste par le banc et vérifient ses propriétés sans les fichiers.

- Avantages : le corpus est décrit fichier par fichier, versionné, relu en PR (M-33) ; la description se vérifie contre le manifeste ; la CI n'a pas besoin des fichiers.
- Inconvénients : un manifeste de plusieurs mégaoctets au dépôt.

### Option B — Description seule au dépôt, manifeste hors du dépôt

- Avantages : dépôt léger.
- Inconvénients : la répartition des parties n'est plus relue ni versionnée au dépôt, contrairement à ADR-0103 et à ES-22.

## Décision

Option A :

- **Manifeste** : écrit par `reference_6_manifeste.py`, jamais à la main ; relu par `banc.corpus.charger`, et chaque empreinte vérifiée sur le poste avant d'être écrite ; nature `reference`, nom `reference`, version `1.0.0`.
- **Provenance** : page de la source (Commons, data.gouv.fr, révision de Wikipédia) ou description du dérivé (original, opération, outil et version) ; licence ; date du versement ou de la révision pour un original, de la fabrication pour un dérivé ; générateur pour une origine IA ; remarque qui dit ce que vaut l'origine. Aucun nom de compte ni d'auteur : la page de chaque fichier porte l'attribution, et le manifeste n'a pas à répéter des noms de personnes.
- **Description** : `docs/verification/corpus-de-reference.md`, avec effectifs par catégorie, partie et format, sources, critères, limites ; elle tient lieu du livrable 5 tant que les fichiers ne sont pas publiés.
- **Version** : un fichier ajouté, retiré ou changé, ou une partie changée, donne une nouvelle version ; un passage des scripts sur des sources qui ont changé aussi.
- **Datation** (A-13) : la date du corpus et celle de chaque original sont au manifeste ; la catégorie « Générés » est à renouveler à chaque nouvelle génération de générateurs, par une nouvelle version.
- **Références** (A-56) : aucune sous-catégorie. Les techniques comparatives qui en auraient besoin (F-35, F-42, F-64) sont hors V1 (ADR-0012) ; le schéma du manifeste reste au format 1.

## Raisons

- Option A retenue : elle garde au dépôt tout ce qu'ES-22 demande, sans les fichiers.
- Option B écartée : la partie de chaque fichier doit être relue et versionnée avant toute mesure.
- Pas de noms de comptes : le plafond par compte n'en a besoin que pendant le choix (phase 2, hors du dépôt) ; les publier n'ajoute rien à la vérité du corpus.
- Pas de sous-catégorie « références » : rien en V1 ne la lirait, et un champ inutile serait un format de plus à maintenir.

## Conséquences

- Des tests (`tests/test_corpus_reference.py`) relisent le manifeste par le banc et vérifient sa nature, sa version, la règle des parties, la provenance de chaque catégorie, et l'accord d'`effectifs.json` avec lui.
- ES-22 passe à « réalisée » : provenance de chaque fichier, corpus versionné, partition fixée par une règle reproductible.
- T101 évalue ce manifeste, sur le poste où sont les fichiers, et publie ses rapports.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création, statut « Proposé » |
