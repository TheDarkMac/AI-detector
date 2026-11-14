# ADR-0182 — Règles des tables connues : sur le modèle de R-IMAGE-004

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T40
- **Exigences liées** : F-06, F-30, F-80, F-81 ; ES-20 ; ADR-0018, ADR-0153, ADR-0155, ADR-0180

## Contexte

R-IMAGE-004 (T24) relève un JPEG sans métadonnées encodé aux tables de libjpeg, en indice faible vers la transformation (ADR-0155). Il fallait dire ce que produit la reconnaissance des autres tables d'ADR-0180.

## Options envisagées

### Option A — Comme R-IMAGE-004

Une règle par famille : JPEG sans aucun bloc de métadonnées, encodé aux tables de cet encodeur ; indice, direction « transformation », niveau « faible », fondement `verification_deterministe`.

- Avantages : même lecture que la règle de T24 ; F-06 nomme la recompression ; l'encodeur et sa qualité sont observés même sans constat.
- Inconvénients : trois règles de plus, non évaluées.

### Option B — Observations seules

Famille et qualité observées, aucune règle avant la mesure sur le corpus (T100).

- Avantages : rien d'affirmé sans mesure.
- Inconvénients : le résumé ne verrait pas une image réencodée par mozjpeg ou extraite d'une vidéo par ffmpeg, qu'il voit pour libjpeg.

## Décision

Option A : `R-IMAGE-005` (libjpeg à deux qualités), `R-IMAGE-006` (mozjpeg), `R-IMAGE-007` (ffmpeg), chacune avec la condition d'absence de métadonnées de R-IMAGE-004 (ADR-0154). Leurs limites disent d'abord ce que la règle ne mesure pas (pas de double compression, T41), puis ce qu'elle ne voit pas, enfin qu'une transformation ne dit rien de ce qu'était le fichier avant (ADR-0155).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle traiterait autrement deux profils de même nature.
- Absence de métadonnées gardée : sans elle, un JPEG qui garde son EXIF après un passage par l'un de ces encodeurs serait relevé autant qu'un JPEG dépouillé ; c'est la raison donnée pour R-IMAGE-004 (ADR-0154).
- Une comparaison avec l'appareil déclaré dans l'EXIF (tables d'un logiciel sous une marque d'appareil) n'est pas possible : une règle ne compare que les observations d'un même module (ADR-0147). Elle reste un point ouvert de l'architecture (§12).

## Conséquences

- Le résumé recommande d'obtenir l'original pour ces trois profils comme pour les autres indices vers la transformation (ADR-0156).
- La mesure sur le corpus (T100), catégorie « transformés » du §8, pourra changer leur niveau.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
