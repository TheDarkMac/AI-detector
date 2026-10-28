# ADR-0095 — Export JSON : schéma du rapport 0.2.0, données masquées absentes, `masquage` en tête

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : l'assistant, choix soumis dans la PR de T16
- **Tâche** : T16
- **Exigences liées** : F-83, NF-18 ; ES-12, ES-13 ; ADR-0025, ADR-0054, ADR-0057, ADR-0059, ADR-0093

## Contexte

ADR-0025 demande un export JSON conforme à un schéma publié et versionné ; ADR-0059 a fixé le modèle du rapport, sans masquage, propriété d'un export. Un export masqué n'a plus le nom, l'empreinte ni les valeurs identifiantes, que le schéma du rapport 0.1.0 exige. Il faut dire à quoi ressemble ce document et quel schéma le décrit.

## Options envisagées

### Option A — Schéma du rapport étendu : champs masqués absents, objet `masquage`

- Avantages : un seul schéma publié pour le rapport complet et ses exports ; un lecteur voit en tête ce qui manque et pourquoi.
- Inconvénients : le schéma exprime des conditions (`if`/`then`) ; une partie de la vérification reste au code.

### Option B — Valeur de remplacement (`"[masqué]"`)

- Avantages : la forme du document ne change pas.
- Inconvénients : une valeur fausse prend la place d'une valeur vraie ; elle viole les motifs du schéma (empreinte hexadécimale) ou passe pour une donnée du fichier.

### Option C — Schéma d'export séparé

- Avantages : le schéma du rapport ne change pas.
- Inconvénients : deux schémas presque identiques à garder cohérents.

## Décision

Option A.

- `VERSION_SCHEMA` passe à **0.2.0**, pour le modèle, le schéma du rapport et celui des messages (version commune, ADR-0054).
- Un export JSON est le document du rapport (`Rapport.vers_dict`) dont : le nom du fichier est retiré si `nom_de_fichier` est masqué ; l'empreinte si `empreinte` l'est ; la `valeur` de chaque observation dont la catégorie identifiante est masquée. L'objet `masquage` suit `version_schema` : `masquees` et `levees`, qui ensemble nomment chacune des cinq catégories une fois, dans l'ordre de la liste d'ES-13.
- Le schéma vérifie : `masquage` facultatif (le rapport complet du modèle n'en a pas) ; nom et empreinte présents si et seulement si `masquage` ne les masque pas ; une observation sans catégorie identifiante a toujours sa valeur. Le code (`rapport.export.valider`) vérifie en plus que chaque catégorie figure une fois, et qu'une observation n'a pas de valeur si et seulement si sa catégorie est masquée.
- `exporter_json` valide le document avant de le rendre. Le texte est en UTF-8, indenté de deux espaces, terminé par un saut de ligne ; les caractères invisibles y sont échappés (ADR-0096).
- `Rapport.depuis_dict` refuse un export où une catégorie est masquée : il lui manque des données. Un export entièrement levé se relit à l'identique.
- Le JSON ne contient ni résumé, ni avertissement, ni texte des règles : il porte les données ; les règles se lisent dans le catalogue, désigné par sa version et son empreinte (ADR-0059).

## Raisons

- Option A retenue : elle garde un seul schéma et dit, dans le document même, ce qui y manque.
- Option B écartée : une valeur inventée dans un format de données est une erreur qui attend son lecteur.
- Option C écartée : la duplication de schéma est exactement ce qu'ADR-0059 voulait éviter pour le résumé.
- `masquage` facultatif : le schéma reste celui du modèle complet, que les tests et la relecture emploient.

## Conséquences

- Un consommateur du JSON doit lire `masquage` avant de chercher le nom ou l'empreinte.
- Le message `isolation` du processus de travail porte désormais `version_schema` 0.2.0 ; un processus de travail d'une autre version est refusé, comme avant.
- Le modèle de données (§6, §7) décrit l'export ; `tests/test_schemas.py` et `tests/test_rapport.py` couvrent les deux listes de vérifications.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
