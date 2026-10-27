# ADR-0071 — Fichiers polyglottes : chaque format reconnu est analysé

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T13
- **Exigences liées** : ES-07, F-82 ; M-08 ; A-25, A-31 ; ADR-0056, ADR-0059, ADR-0061, ADR-0062, ADR-0070

## Contexte

ES-07 : « un fichier reconnu dans plusieurs formats […] est signalé comme tel ; chaque format reconnu est analysé, ou déclaré non analysé avec la raison ». Un fichier peut être un JPEG suivi d'une archive ZIP, un JPEG qui porte un PDF dans son commentaire, une photo animée (JPEG puis MP4), ou un JPEG à plusieurs images (MPF). L'identification (ADR-0070) situe chacun de ces formats dans le fichier. Reste à décider ce que l'analyse en fait.

## Options envisagées

### Option A — Format principal seul, les autres déclarés non analysés

Seule la partie 1 est analysée ; chaque autre format reconnu est signalé, avec sa plage, et déclaré non analysé avec une raison nouvelle `format_secondaire`.

- Avantages : surface d'attaque inchangée (un passage des modules par fichier) ; modèle presque inchangé.
- Inconvénients : le contenu caché derrière le premier format n'est jamais examiné, alors que c'est souvent lui qui compte dans un polyglotte.

### Option B — Chaque format reconnu analysé

Les modules sont exécutés pour chaque partie dont le format est dans le périmètre.

- Avantages : rien de ce que l'outil sait lire n'est laissé de côté ; une photo animée ou un JPEG MPF reçoivent les analyses de chacune de leurs parties.
- Inconvénients : un fichier hostile peut faire passer les modules plusieurs fois (borné à 16 parties) ; le modèle doit dire à quelle partie se rapporte chaque résultat.

## Décision

Option B.

- **Partie** : format reconnu, rang à partir de 1 (ordre des débuts), plage d'octets, fin connue ou non, tronquée ou non (ADR-0070). La rubrique Identification porte la liste des parties (ADR-0072).
- **Exécution** : pour chaque partie du périmètre, dans l'ordre des rangs, chaque module actif dans l'ordre de la configuration ; il est applicable si le format de la partie est l'un des siens.
- **Lecture** : le module lit sa partie comme un fichier autonome. `contexte.lire(position, taille)` compte depuis le début de la partie et s'arrête à sa fin ; `contexte.taille` et `contexte.format_reel` sont ceux de la partie, `contexte.partie` son rang. Les plages d'octets de ses localisations sont ramenées par le contexte à des positions dans le fichier entier.
- **Modèle** : `partie` (rang) ajouté à l'observation, au constat et à la technique couverte ; à l'analyse non menée, obligatoire quand elle nomme un module. La couverture compte une entrée par technique et par partie du périmètre. La numérotation `<module>/<n>` des observations continue d'une partie à l'autre.
- **Protocole** : le message `identification` (liste des parties) suit l'état de l'isolation ; le message `module` porte la partie. Le processus principal vérifie l'ordre partie par partie.
- **Ce qui n'est pas analysé** est déclaré non mené par le processus principal, à partir de l'identification :

| Cas | Raison | Module | Partie | Localisation |
| --- | --- | --- | --- | --- |
| Partie hors périmètre | `hors_perimetre` (nouvelle) | Non | Oui | Plage de la partie |
| Partie tronquée ou corrompue | `fichier_tronque` | Non | Oui | Plage de la partie |
| Plage qu'aucune partie ne couvre | `format_partiel` | Non | Non | La plage |

- La raison `hors_perimetre` complète la liste fermée d'ADR-0056 : elle désigne une partie, jamais un module, et n'interrompt pas l'analyse. `VERSION_SCHEMA` reste `0.1.0` : aucune version du schéma n'est publiée (ADR-0054, ADR-0062).

## Raisons

- Option B retenue par TheDarkMac, contre la recommandation de l'assistant (option A), sans raison supplémentaire : celles présentées avec l'option.
- Option A écartée par TheDarkMac : laisser de côté le contenu caché d'un polyglotte.
- Les inconvénients de l'option B sont bornés : 16 parties au plus, un seul processus de travail par fichier, et les limites de T14 valent pour l'analyse entière.
- Lecture relative à la partie : un module écrit pour un JPEG lit un JPEG, qu'il soit en tête du fichier ou derrière autre chose ; les positions au rapport restent celles du fichier, que le lecteur peut vérifier.
- Non menées tirées de l'identification par le principal : elles ne dépendent d'aucun module, et ADR-0056 attribuait déjà `format_partiel` et `fichier_tronque` à T13.

## Conséquences

- ADR-0061 (interface d'un module) : `lire`, `taille`, `format_reel` se rapportent à la partie ; `partie` s'ajoute. Aucun module n'existe encore : rien à reprendre.
- ADR-0059 (couverture) et ADR-0062 (message « module ») sont précisés, sans changement de principe.
- T16 présente les résultats partie par partie ; T15 tient la matrice format × technique par format, donc par partie.
- Les contenus multiples internes à un format (A-25) restent l'affaire de chaque module (`format_partiel` avec localisation).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
