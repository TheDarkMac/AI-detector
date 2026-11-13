# ADR-0123 — Découpage de T21 : le PDF d'abord, l'audio, la vidéo et la bureautique en compléments

- **Statut** : Accepté
- **Date** : 2026-11-12
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21
- **Exigences liées** : F-10 ; méthode de travail (ADR-0001, ADR-0005)

## Contexte

Le [découpage](../00-plan/decoupage-taches.md) (v0.18) range sous T21 trois extractions sans rien en commun hormis F-10 : le dictionnaire d'information et le XMP d'un PDF, les balises des conteneurs audio et vidéo (ID3, Vorbis, ISOBMFF, Matroska), les propriétés des documents DOCX et ODT. Chacune demande son lecteur de structure, ses échantillons d'oracle et son fuzzing (ADR-0043, ADR-0082, ADR-0122). TheDarkMac a lancé la tâche sous le titre « T21 | Extraction PDF ».

## Options envisagées

### Option A — Le PDF dans cette branche, les deux autres en compléments de T21

Une branche et une PR par complément, comme T10 et ses deux compléments (`tache/T10-licence-et-publication`, `tache/T10-versions-et-publication`).

- Avantages : des PR de taille relisible ; chaque lecteur est fuzzé et comparé à exiftool avant le suivant ; le lecteur PDF, qui servira aussi à T50 à T53, est relu seul.
- Inconvénients : trois PR au lieu d'une ; F-10 reste partielle jusqu'au dernier complément.

### Option B — Tout T21 en une PR

- Avantages : conforme au découpage tel qu'écrit ; F-10 complète en une fois.
- Inconvénients : une PR très large (trois lecteurs, trois familles d'échantillons), longue à relire, dont un défaut dans un lecteur retarde les deux autres.

## Décision

Option A : `tache/T21-extraction-pdf` livre l'extraction PDF ; l'audio et la vidéo, puis DOCX et ODT, suivent en compléments de T21, chacun dans sa branche.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : taille de la PR, et dépendance artificielle entre trois lecteurs indépendants.

## Conséquences

- Le découpage passe en v0.19 : T21 porte le PDF, et ses deux compléments sont nommés à la ligne de T21.
- F-10 reste partielle dans la matrice jusqu'au dernier complément.
- Le XML de DOCX et ODT (ADR-0116) et les conteneurs audio et vidéo sont hors de cette branche.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création ; option choisie par TheDarkMac au début de T21 |
| 2026-11-13 | Renvoi : complément audio et vidéo réalisé, les neuf formats en une branche (ADR-0130) ; reste DOCX et ODT (T21, complément audio et vidéo) |
