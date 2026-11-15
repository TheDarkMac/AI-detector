# ADR-0201 — Module `ela`, DCT commune avec T41, contrôle avant publication, versions de T42

- **Statut** : Proposé
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T42, à valider pendant la revue de la PR de T42
- **Tâche** : T42
- **Exigences liées** : F-32, F-84, NF-06, NF-07, ES-13 ; ADR-0064, ADR-0158, ADR-0184, ADR-0190

## Contexte

T42 ajoute un module, partage le calcul de T41, change le modèle du rapport (ADR-0200) et ne touche pas au catalogue. Restaient à fixer, sans question posée : l'organisation du code, la direction déclarée d'un module sans constat, l'effet de ses analyses non menées sur le contrôle avant publication, et les versions.

## Options envisagées

### Code

- **A — Module `ela` ; DCT en entiers sortie de `doublejpeg` vers `modules/_lecture/dct.py`, commune aux deux** : un seul calcul, vérifié par les tests de T41 et de T42 ; les produits de matrices écrits en un seul produit à deux dimensions, entier pour entier identique et 2,5 fois plus rapide (0,9 s au lieu de 2,2 s pour 65 536 blocs).
- **B — `ela` importe les fonctions de `doublejpeg`** : un module en dépendrait d'un autre.
- **C — Copie du calcul dans `ela`** : deux copies à tenir.

### Direction déclarée

Le schéma du manifeste exige au moins une direction (ADR-0064), alors que le module n'émet aucun constat (ADR-0198).

- **A — `rien_de_particulier`** : la seule qui n'oriente vers aucune hypothèse.
- **B — Changer le schéma pour admettre une liste vide** : une version du schéma du manifeste pour un cas unique.

### Contrôle avant publication

- **A — Une analyse non menée d'`ela` ne rend pas le contrôle incomplet**, comme pour `doublejpeg` (ADR-0190) : le module ne lit aucune métadonnée.
- **B — Elle le rend incomplet**, comme celle d'un module de métadonnées : faux, aucune marque identifiante ne reste non lue par sa faute.

### Versions

- **A — Module `ela` 0.1.0 ; `doublejpeg` 0.1.0 inchangé ; schéma du rapport et des messages 0.7.0 ; catalogue 0.8.0 inchangé.**
- **B — `doublejpeg` 0.1.1** : son code change de place.

## Décision

Option A dans les quatre cas. Le lecteur JPEG reçoit ses bornes en paramètres (ADR-0199), ses valeurs par défaut inchangées. `ela` rejoint `doublejpeg` dans la liste des modules qui ne lisent aucune métadonnée (`rapport/_presentation.py`).

## Raisons

- Code A : un calcul en un seul endroit ; B et C écartées pour la dépendance entre modules et la double copie.
- Direction A : sans effet, puisqu'aucun constat ne l'emploie ; B écartée pour son coût.
- Contrôle A : fidèle à la raison d'ADR-0158, comme pour `doublejpeg` ; B écartée parce qu'elle annoncerait à tort des marques non lues.
- Versions A : `doublejpeg` donne exactement les mêmes observations (106 tests de T41 inchangés), donc rien ne distingue deux rapports (ADR-0184) ; le schéma change (nouvel objet, nouvelle catégorie identifiante), d'où 0.7.0 ; aucune règle, aucun texte du catalogue ne change.

## Conséquences

- Les tests qui citent la liste des modules (`test_cli`, `test_manifestes`, `test_travail`, `test_soumission`, `test_fuzzing`) et la version du schéma (`travail_factice`, `test_travail`) la suivent.
- Le complément de T40, mergé après T42, partira de ce modèle (schéma 0.7.0).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création, statut « Proposé » |
