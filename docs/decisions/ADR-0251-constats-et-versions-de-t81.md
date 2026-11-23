# ADR-0251 — Constats de T81 : huit informations neutres, dont deux incohérences de dates ; versions

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (règles, seuils et versions précisés par l'assistant)
- **Tâche** : T81
- **Exigences liées** : F-71, F-13, F-80, F-81 ; ADR-0022, ADR-0147 à ADR-0152, ADR-0248 à ADR-0250

## Contexte

F-71 fixe qu'une valeur absente ou nulle de l'historique d'édition reste une information neutre ; elle ne dit rien d'une valeur courte ou faible. Or un long texte écrit en une seule session, en moins d'une minute, est ce que laisse un texte collé depuis un générateur, mais aussi un texte collé depuis un brouillon écrit ailleurs, une conversion ou un « Enregistrer sous » : les hypothèses ne se distinguent pas (ADR-0022), et aucun corpus ne mesure encore ces cas (T100).

## Options envisagées

### Option A — Informations neutres, et des incohérences neutres (recommandée)

Tous les constats sont des informations neutres : temps d'édition, enregistrements, sessions du texte, modifications suivies et commentaires sont rapportés. S'y ajoutent deux incohérences, comme les règles de T23 : un temps d'édition plus long que l'écart entre création et dernier enregistrement, et des modifications ou commentaires datés après ce dernier enregistrement.

- Avantages : le rapport dit ce que le document déclare de son écriture, sans le lire comme un indice ; deux contradictions internes, que ni un copier-coller ni une conversion n'expliquent d'ordinaire, sont relevées.
- Inconvénients : un constat neutre sur un temps d'édition nul peut tout de même être lu comme un indice par un lecteur pressé.

### Option B — Informations neutres seules

- Avantages : plus court.
- Inconvénients : les deux contradictions ne sont pas relevées.

### Option C — Un indice faible vers l'origine IA

Un long texte écrit en une session, en moins d'une minute, fait un indice faible.

- Avantages : le rapport dit ce que beaucoup cherchent dans un historique.
- Inconvénients : faux positifs sur tout texte rédigé ailleurs puis collé, sans mesure sur corpus (T100) ; contraire à la lecture que F-71 fait des valeurs nulles.

## Décision

Option A. Précisions de l'assistant :

| Règle | Condition | Fondement |
| --- | --- | --- |
| R-HISTORIQUE-001 — Aucun historique d'édition | `historique.present` = faux | vérification déterministe |
| R-HISTORIQUE-002 — Temps d'édition déclaré | `historique.duree` observée, zéro compris | déclaration |
| R-HISTORIQUE-003 — Nombre d'enregistrements déclaré | `historique.revisions` observée | déclaration |
| R-HISTORIQUE-004 — Sessions d'édition du texte | `historique.texte.sessions` ≥ 1, avec la part de la plus représentée | déclaration |
| R-HISTORIQUE-005 — Modifications suivies | `historique.modifications` ≥ 1, avec les auteurs distincts | déclaration |
| R-HISTORIQUE-006 — Commentaires | `historique.commentaires` ≥ 1, avec les auteurs distincts | déclaration |
| R-HISTORIQUE-007 — Temps d'édition plus long que l'écart | `historique.duree` > `historique.ecart` (comparaison de deux observations, format 2, ADR-0147) | déclaration |
| R-HISTORIQUE-008 — Dates après le dernier enregistrement | `historique.posterieures` ≥ 1 | déclaration |

- Toutes de catégorie « information neutre », direction « rien de particulier ». Les seuils « ≥ 1 » sont fixés par définition, calibrage manuel (ADR-0016).
- R-HISTORIQUE-007 : l'écart est le plus grand que permettent les deux dates, arrondi à la minute supérieure (ADR-0249) ; une date sans fuseau l'allonge de 26 heures. R-HISTORIQUE-008 : la date d'une modification est lue sans fuseau (ADR-0250) ; une date antérieure à la création n'est pas relevée, le texte copié d'un autre document gardant ses modifications.
- Les phrases ne répètent pas l'unité, que le rapport écrit après la valeur (« 0 minutes », « 52 % »).

| Élément | Version |
| --- | --- |
| Module `historique` | 0.1.0 (nouveau) : formats `docx`, `odt` ; bibliothèque `expat` ; exigence F-71 ; direction « rien de particulier » ; aucune règle « module » |
| Catalogue | 0.19.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.12.0, inchangés |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : deux contradictions internes, déterministes à lire, resteraient tues.
- Option C écartée : un indice sans mesure, sur un historique que bien des usages ordinaires donnent aussi.
- Fondement « déclaration » : chaque valeur est ce que le fichier dit de lui-même ; R-HISTORIQUE-001 constate une absence, comme les règles d'absence de T23.

## Conséquences

- La part de documents ordinaires qui déclenchent R-HISTORIQUE-007 et R-HISTORIQUE-008 se mesurera sur le corpus de référence (T100), qui dira aussi si un historique court mérite un jour un indice.
- Le registre des empreintes reçoit la version 0.19.0 du catalogue.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création ; option choisie par TheDarkMac au début de T81 |
