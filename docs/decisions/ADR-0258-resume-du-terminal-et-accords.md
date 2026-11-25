# ADR-0258 — Résumé du terminal : techniques par partie et par état ; textes accordés au nombre

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T90
- **Exigences liées** : NF-11, F-25 ; ADR-0073, ADR-0098

## Contexte

Le résumé du terminal (ADR-0098) écrivait une ligne par technique et par partie : « technique X, partie 1 : non applicable ». Avec 25 modules livrés et 15 techniques hors de cette version, le JPEG `tests/donnees/ela/collage_60_92.jpg` en donnait 29 sur les 51 de son résumé, dont 17 pour des techniques sans objet pour son format, et le DOCX à deux images `tests/donnees/imagesbureau/libreoffice.docx` 93 sur 121 : le reste du résumé s'y perdait. Les nombres s'écrivaient « 2 indice(s) », « 4 information(s) neutre(s) », et le détail des indices « vers transformation : 2 faible », qu'il faut connaître pour lire.

## Options envisagées

### Option A — Une ligne par état, non applicables comptées (recommandée)

Par partie, une ligne par état qui nomme ses techniques ; les non applicables seulement comptées ; textes accordés au nombre ; détail des indices réécrit.

- Avantages : de 51 à 25 lignes pour ce JPEG, de 121 à 37 pour ce DOCX ; chaque technique appliquée ou non menée reste nommée, ce que F-25 demande ; rien n'est perdu, la liste complète est au rapport HTML et JSON.
- Inconvénients : les lignes des états sont longues (huit techniques appliquées pour un JPEG).

### Option B — Option `--detail`

- Avantages : résumé court par défaut, liste complète sur demande.
- Inconvénients : une option de plus ; le résumé par défaut devrait alors taire des techniques, ou les compter seulement.

### Option C — Garder la liste

- Avantages : rien ne change.
- Inconvénients : la longueur reste ; seules les phrases seraient lisibles.

## Décision

Option A.

- Pour chaque partie, dans l'ordre de la couverture : « partie N, techniques appliquées : … », puis partielles, non menées, hors de cette version, chacune s'il y en a, ses techniques nommées (ADR-0257) ; puis « partie N : K techniques non applicables à son format ».
- Une technique hors de cette version qui ne s'appliquerait pas au format de la partie (bruit du capteur pour un DOCX) est comptée avec les non applicables : la dire « hors de cette version » laissait croire qu'elle aurait pu s'appliquer.
- Les textes de l'outil qui portent un nombre ont deux formes dans `textes.toml`, `un` et `plusieurs` ; `accorder(cle, quantite, …)` choisit la première pour zéro et un, comme le veut le français, et écrit le nombre groupé par milliers. « (s) » ne figure plus dans aucun texte de l'outil ; un test le vérifie.
- Le résumé des techniques ne cite que les états présents : « Techniques : 8 appliquées, 4 non menées, 17 non applicables. », « Techniques : aucune. » s'il n'y en a pas.
- Le détail des indices devient « vers l'hypothèse « transformation » : 2 de niveau faible ».

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : F-25 demande de dire ce qui a été appliqué ou non ; un résumé par défaut qui tairait des techniques s'en écarterait, et un résumé qui les nomme toutes n'a pas besoin d'une seconde forme.
- Option C écartée : contraire à NF-11.

## Conséquences

- Le HTML reprend les mêmes textes du résumé (accords, détail des indices) ; sa couverture reste un tableau d'une ligne par technique et par partie.
- Les phrases des règles du catalogue gardent leur « (s) » : elles sont remplies par des valeurs que l'outil ne connaît qu'à l'exécution, et les accorder demanderait un mécanisme dans le format du catalogue (ADR-0085). Renvoyé à une tâche qui touchera ce format.
- Les tests qui comparaient des lignes du résumé sont mis à jour ; l'export JSON est inchangé.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
