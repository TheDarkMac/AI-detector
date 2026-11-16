# ADR-0195 — Tables de Photoshop : tous les jeux d'un niveau, une règle par niveau

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : complément de T40
- **Exigences liées** : F-30 ; ADR-0191, ADR-0193

## Contexte

Photoshop enregistre un JPEG à l'un de 13 niveaux de qualité (0 à 12), qu'il écrit dans la ressource 0x0406 de son bloc APP13. La règle de concordance du 2026-11-15 (ADR-0193) excluait tout niveau dont des fichiers ont des tables différentes sans explication. Le relevé a montré qu'à chaque niveau, Photoshop écrit plusieurs jeux de tables, dans toutes ses versions de 7.0 à CC, et en a donné l'explication :

- deux jeux selon la taille de l'image : côté long d'au plus 1 296 pixels pour l'un, d'au moins 1 305 pixels pour l'autre ; la séparation vaut à tous les niveaux, et ni le nombre de pixels, ni la largeur, ni le côté court ne séparent les deux jeux ;
- un jeu propre aux images en niveaux de gris, qui n'ont qu'une table.

Aucune empreinte n'est partagée entre deux niveaux. Les mêmes empreintes se trouvent sur des fichiers de Photoshop Elements et, pour un jeu, de Lightroom.

## Options envisagées

### Option A — Tous les jeux, une règle par niveau

- Avantages : chaque fichier de Photoshop d'un niveau retenu est reconnu ; la phrase dit le niveau ; la séparation par taille est décrite dans la fiche sans être une condition, puisque son seuil exact n'est pas connu.
- Inconvénients : neuf règles.

### Option B — Deux règles par niveau, par taille

Une règle par jeu, avec une condition sur le côté long (≥ 1 305 ou ≤ 1 296 pixels).

- Avantages : plus stricte.
- Inconvénients : elle fige un seuil observé, qu'Adobe ne documente pas ; un fichier entre 1 297 et 1 304 pixels ne serait reconnu par aucune.

### Option C — Une seule règle Photoshop

- Avantages : plus simple.
- Inconvénients : le niveau n'est plus dans la phrase.

## Décision

Option A : `R-IMAGE-008` (niveau 3) et `R-IMAGE-009` à `R-IMAGE-016` (niveaux 5 à 12), chacune avec les empreintes retenues du niveau, couleur et gris, petites et grandes images. Les niveaux 0, 1, 2 et 4 n'ont pas assez de fichiers (ADR-0193) et ne sont pas livrés. Indice faible vers la transformation (ADR-0191), sans condition sur les métadonnées (ADR-0192). La phrase nomme Photoshop et dit que d'autres logiciels d'Adobe (Photoshop Elements, Lightroom) écrivent les mêmes tables.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un seuil non documenté deviendrait une condition du catalogue.
- Option C écartée : le niveau aide à confronter le fichier à ce que déclare sa source.

## Conséquences

- La discordance « sans explication » de la règle du 2026-11-15 est levée par la taille et la couleur ; la fiche donne, pour chaque empreinte, le nombre de fichiers et l'étendue des côtés longs.
- Un fichier enregistré par Photoshop sans ressource 0x0406 n'est pas dans le relevé, qui lit le niveau dans cette ressource : si ses tables diffèrent de celles relevées, elles ne sont pas reconnues.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création |
