# ADR-0257 — Nom de chaque technique en langage courant, dans les textes du rapport

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T90
- **Exigences liées** : NF-11, F-25, F-82 ; ADR-0020, ADR-0064, ADR-0098

## Contexte

Le terminal et le rapport HTML nommaient chaque technique par l'identifiant de son module (`actifsbureau`, `revisionspdf`, `pointstracage`…) : dans la couverture, les analyses non menées et l'origine d'une partie extraite. Ces identifiants sont lisibles pour qui connaît le code, pas pour un vérificateur (NF-11). Les fiches techniques ont chacune un titre en langage courant, mais le rapport n'y renvoie pas.

## Options envisagées

### Option A — Nom dans `rapport/textes.toml` (recommandée)

Une table `[techniques]` donne un nom à chaque module livré et à chaque technique hors de cette version ; le rapport écrit « nom (identifiant) ».

- Avantages : les textes de l'outil sont déjà là (ADR-0020) ; ni schéma ni manifeste ne change ; l'identifiant reste écrit, pour retrouver la fiche, le module ou l'observation.
- Inconvénients : le nom vit loin du module ; un test doit vérifier que chaque module a le sien.

### Option B — Champ `nom` dans chaque manifeste

- Avantages : le nom suit le module.
- Inconvénients : change le schéma des manifestes (ADR-0064) et les 25 modules ; les techniques hors de cette version (`hors_v1.toml`) demandent le même champ.

### Option C — Garder l'identifiant

- Avantages : rien à faire ; le glossaire et les fiches expliquent les techniques.
- Inconvénients : un lecteur sans connaissances techniques ne sait pas ce que couvre `imagesbureau` ou `dwtdct`.

## Décision

Option A.

- `[techniques]` de `textes.toml` nomme les 25 modules livrés et les 15 techniques de `modules/hors_v1.toml`, d'après le titre de leur fiche ou le libellé de leur exigence, en minuscules.
- `technique(module)` (`rapport/_presentation.py`) écrit « nom (identifiant) » ; un identifiant sans nom, qui ne vient que des rapports construits par les tests, s'écrit seul.
- Le nom remplace l'identifiant seul dans les lignes des techniques du terminal (ADR-0258), dans les tableaux de couverture et des analyses non menées du rapport HTML, dans la précision d'une analyse non menée au terminal et dans l'origine d'une partie extraite. Le tableau des observations garde l'identifiant seul : c'est l'annexe technique du rapport, où chaque observation porte déjà son module dans son identifiant et dans son nom.
- Un test vérifie que les noms et les techniques connues sont les mêmes, ni plus ni moins.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : un changement de schéma et de 25 manifestes pour un texte d'affichage, qui relève de `textes.toml` d'après ADR-0020.
- Option C écartée : contraire à NF-11.

## Conséquences

- Un nouveau module, ou une technique ajoutée à `hors_v1.toml`, doit recevoir son nom dans la même PR : le test `test_chaque_technique_a_un_nom` échoue sinon.
- L'export JSON ne change pas : il garde les identifiants, qu'un programme lit.
- Les phrases des règles du catalogue citent parfois un module par son identifiant ; elles restent telles quelles.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
