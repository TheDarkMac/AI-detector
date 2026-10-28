# ADR-0084 — Langage des règles : conditions fermées, toutes requises ; règles appliquées par un module

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T15
- **Exigences liées** : F-12, F-26, NF-06, NF-07 ; ES-09 ; A-32, A-37 ; ADR-0016, ADR-0018, ADR-0019, ADR-0021, ADR-0038, ADR-0039, ADR-0058, ADR-0064

## Contexte

L'architecture sépare l'observation, relevée par un module, du constat, que tire une règle du catalogue (§6) : c'est ce qui garde les règles hors du moteur (F-26). Elle admet aussi qu'un module produise un constat directement quand la vérification est déterministe (signature C2PA). Restait à dire ce qu'une règle sait exprimer : de quoi dépend la mise à jour du catalogue sans nouvelle version de l'outil, et ce qu'un relecteur doit savoir lire (ADR-0019).

## Options envisagées

### Option A — Conditions fermées, toutes requises

Une liste fermée de tests sur une observation nommée (`egal`, `parmi`, `motif` RE2, `seuil`, `presente`), combinés par « et » seulement, évalués par le moteur ; une vérification que seul du code sait faire reste une règle « appliquée par le module », dont le catalogue fixe la phrase, la catégorie, la direction, le fondement et le niveau.

- Avantages : ajouter une signature de générateur, un seuil ou une liste de référence (A-32) se fait dans un fichier TOML ; chaque règle se lit d'un coup d'œil ; schéma simple, tests exhaustifs possibles.
- Inconvénients : pas de « ou » ni de « non » ; aucune comparaison entre deux observations.

### Option B — Expressions logiques

Les mêmes tests, combinés librement par « et », « ou », « non », imbriqués.

- Avantages : plus expressif, moins de règles pour une même signature.
- Inconvénients : règles plus longues à relire et à tester ; schéma récursif ; une négation peut faire d'une absence un constat, contre F-14 (« absence ≠ authenticité »).

### Option C — Paramètres seuls

Le catalogue ne porte que des données (listes de signatures, seuils, niveaux) ; toute la logique est dans le code des modules.

- Avantages : moteur plus simple.
- Inconvénients : une nouvelle forme de règle exige une nouvelle version de l'outil ; F-26 n'est tenue que pour les valeurs.

## Décision

Option A.

- Une règle `application = "moteur"` porte de 1 à 16 conditions, **toutes requises**. Chaque condition nomme une observation (vocabulaire du module, sa fiche technique) et porte un seul test : `egal` (une valeur), `parmi` (une liste de 1 à 4 096 valeurs), `motif` (expression RE2, ADR-0039, ADR-0089), `seuil` (opérateur `<`, `<=`, `>`, `>=` et nombre), `presente`. Une condition peut nommer le paramètre de la phrase qui renvoie à l'observation retenue.
- Une règle `application = "module"` n'a pas de condition : le code de son module l'applique et la cite par son identifiant (ADR-0090). Elle déclare les paramètres de sa phrase.
- Dans les deux cas, c'est la règle qui fixe le **gabarit** de la phrase, la **catégorie**, la **direction**, le **fondement**, et pour un indice le **niveau** et l'**évaluation** qui le fonde (ADR-0018) ; s'y ajoutent le titre, la description, les **limites connues** (au moins une, ADR-0019) et, pour une règle à seuil, le **calibrage** (méthode manuelle ou corpus, procédure, version du corpus, ADR-0016).
- Une règle dont la catégorie, le fondement, la direction et le niveau ne pourraient former aucun constat valide (ADR-0058) rend le catalogue invalide.
- Un « ou » s'écrit par `parmi`, par l'alternative d'un motif, ou par deux règles ; une absence se teste sur l'observation qui la dit (`xmp.present` égal à `false`), jamais par l'absence d'une observation.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : son gain d'expression ne justifie pas des règles plus difficiles à relire, alors que tout est public pour être vérifié (ADR-0019) ; la négation ouvre la porte aux constats tirés d'une absence.
- Option C écartée : F-26 demande de mettre le catalogue à jour sans modifier le moteur, pas seulement ses valeurs.
- Conjonction seule : un constat cite les observations qui l'ont fait naître ; avec « et », chaque condition en fournit une, sans ambiguïté.

## Conséquences

- Le moteur applique les règles « moteur » d'un module à ses observations, après lui, dans le processus de travail (ADR-0089) ; le processus principal n'applique jamais un motif à une donnée du fichier (ADR-0039).
- Le champ `regles` d'un manifeste cite les règles « module » de ce module, et elles seules ; les règles « moteur » ne sont citées par aucun manifeste : en ajouter une ne change pas l'outil (précision d'ADR-0064, vérifiée au chargement).
- Une incohérence entre deux observations (F-13 : date de création postérieure à la modification) ne s'écrit pas avec ces tests : T23 l'écrira en règle « module », ou proposera un test de comparaison, qui sera un nouveau format du catalogue (ADR-0085).
- Le schéma est `schemas/regles.schema.json` ; le code est `src/voight_kampff/_regles.py`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
| 2026-10-28 | Complété en T16 : la règle porte aussi le texte de sa phrase, `phrase.fr` (ADR-0091) |
