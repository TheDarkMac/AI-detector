# ADR-0098 — Contenu, ordre et textes du rapport et du résumé du terminal

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : l'assistant, choix soumis dans la PR de T16 ; textes à relire par TheDarkMac
- **Tâche** : T16
- **Exigences liées** : §6 du cahier, F-80 à F-83, NF-11, NF-14, NF-18 ; ES-13, ES-14 ; ADR-0018, ADR-0020, ADR-0021, ADR-0056, ADR-0059, ADR-0072, ADR-0073, ADR-0086

## Contexte

Le §6 énumère les rubriques du rapport ; ADR-0018 fixe l'ordre du résumé (preuves, indices par direction et niveau, couverture et analyses non menées) ; ADR-0086 demande de mettre en évidence un catalogue fourni « au même rang que l'isolation réduite » ; ADR-0056 et ADR-0072 attendaient de T16 un gabarit par raison et par signalement ; ADR-0073 annonçait la révision du résumé du terminal. ADR-0020 sépare du code les textes destinés à l'utilisateur.

## Options envisagées

### Option A — Rubriques du §6 précédées d'alertes ; textes dans `rapport/textes.toml`

- Avantages : ce qui change la portée du rapport se lit avant tout le reste ; tous les textes se relisent dans un fichier, traduisibles.
- Inconvénients : un fichier de textes de plus à tenir complet (un test le vérifie).

### Option B — Rubriques dans l'ordre du §6, alertes dans leurs rubriques

- Avantages : suit le tableau du cahier à la lettre.
- Inconvénients : l'isolation réduite, le catalogue fourni ou le démasquage se liraient après les constats.

## Décision

Option A.

- **Rapport HTML**, dans cet ordre : titre, version de l'outil et date ; **alertes** (masquage levé, catalogue fourni par l'utilisateur, isolation réduite avec les restrictions manquantes, analyse interrompue) ; **avertissement** ; **résumé** (ADR-0018 : chaque preuve avec sa direction et sa phrase ; nombre d'indices, puis par direction le nombre par niveau ; nombre d'informations neutres ; techniques par état ; nombre d'analyses non menées) ; Identification (avec les signalements d'ADR-0072 et les parties) ; Versions ; Isolation ; Preuves ; Indices (par direction, du plus fort au plus faible) ; Informations neutres ; Analyses non menées ; Couverture ; Données identifiantes ; Observations ; Glossaire.
- **Chaque constat** : sa phrase en titre ; catégorie, direction, niveau et évaluation (taux, corpus, date, ou « règle non évaluée ») pour un indice ; fondement ; règle (identifiant, version, titre) ; données observées (nom et valeur) ; limites connues ; partie et localisation.
- **Avertissement** : trois phrases, aucun verdict, une preuve n'établit que son énoncé, un indice peut apparaître sur un fichier authentique, l'absence de constat ne vaut que pour la couverture.
- **Glossaire** du rapport : seize termes repris du glossaire du projet en langage courant (NF-11) ; les libellés des constats (catégorie, direction, niveau, fondement, règle) renvoient à leur définition.
- **Résumé du terminal** : format réel ; alertes ; nom et empreinte (masqués par défaut) ; signalements ; parties ; isolation ; techniques ; résumé d'ADR-0018 ; analyses non menées autres que `hors_v1` et `hors_perimetre` (déjà dites) ; catalogue ; chemins des rapports écrits. Après le dernier fichier analysé, l'avertissement, une fois.
- **Textes** : `src/voight_kampff/rapport/textes.toml` porte le titre, l'avertissement, les alertes, les libellés de chaque énumération, une phrase par raison de non-menée (ADR-0056), une par signalement (ADR-0072), les formes des valeurs et des lignes du terminal, et le glossaire. Les phrases des constats sont dans les règles (ADR-0091).
- **Valeurs** : un booléen s'écrit « vrai » ou « faux » ; un nombre comme Python le relit ; une liste, ses éléments séparés par des virgules ; l'unité suit la valeur ; une taille en octets est groupée par milliers. Les heures sont en UTC (ES-14).

## Raisons

- Option A retenue : ADR-0086 et ES-13 veulent ces signalements en tête ; ils changent la lecture de tout le reste.
- Option B écartée : un lecteur pressé lirait les indices sans savoir que le catalogue n'est pas celui de l'outil.
- Avertissement après le dernier fichier, au terminal : c'est la dernière chose qui reste à l'écran.
- Indices du plus fort au plus faible : l'ordre de lecture suit la confiance mesurée, sans rien combiner (ADR-0018).

## Conséquences

- Les textes sont proposés dans la PR pour relecture ; les mentions définitives destinées aux utilisateurs restent à T103.
- `tests/test_rapport.py` vérifie qu'il y a un libellé pour chaque valeur des énumérations, et qu'aucun texte ne contient une tournure de certitude.
- Le terminal n'affiche plus le nombre brut d'observations ni les codes des raisons : il dit leurs phrases.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
