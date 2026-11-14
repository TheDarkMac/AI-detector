# ADR-0174 — Inventaire des filigranes ; lecteur dwtDct dans une tâche à part (T32)

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T31
- **Tâche** : T31
- **Exigences liées** : F-24, F-25 ; A-21, A-35 ; ADR-0012, ADR-0016, ADR-0043

## Contexte

ADR-0012 limite T31 à l'inventaire des filigranes dont un lecteur public et non neuronal existe, et à un point d'extension du catalogue. L'[inventaire](../catalogue/inventaire-des-marquages.md), fait le 2026-11-14 sur sources primaires, trouve un seul schéma qui le permet : le dwtDct de la bibliothèque invisible-watermark, posé par les codes de référence de Stable Diffusion 1, de SDXL et de FLUX.1. Tous les autres filigranes posés sur des contenus générés ont un lecteur neuronal (TrustMark, Video Seal, AudioSeal, InvisMark, WavMark), propriétaire (SynthID) ou réservé à la clé du fournisseur (SynthID Text, listes vertes).

Lire le dwtDct demande de décoder les pixels d'une image (JPEG, PNG, WebP, HEIC), ce que l'outil ne fait pas encore : conversion YUV, ondelettes de Haar, DCT de blocs 4 × 4. La bibliothèque elle-même dépend d'OpenCV et de PyTorch.

## Options envisagées

### Option A — Inventaire seul ; lecteur dans une nouvelle tâche, T32

- Avantages : respecte ADR-0012 ; le décodage des pixels, nouvelle surface d'attaque (ES-04), se décide une fois, avec T40 et T41 qui en auront aussi besoin ; le lecteur arrive avec une mesure de ses faux positifs sur le corpus.
- Inconvénients : la V1 ne lit aucun filigrane tant que T32 n'est pas faite ; le catalogue inscrit le dwtDct « non recherché, lecteur à venir ».

### Option B — Lecteur dans T31, avec numpy et Pillow dans le processus de travail

- Avantages : un premier filigrane lu dès T31.
- Inconvénients : deux dépendances lourdes ajoutées sans l'examen d'ADR-0043 ; décodage d'images non sûres dans le processus de travail sans décision sur la bibliothèque ; constat de niveau « faible » faute de mesure ; dépasse le périmètre d'ADR-0012.

## Décision

Option A. T31 livre l'inventaire et le point d'extension ; le lecteur dwtDct devient la tâche T32, ajoutée au découpage après T31.

## Raisons

- A retenue pour les raisons ci-dessus, recommandation suivie par TheDarkMac.
- B écartée : le choix du décodage des pixels engage T40 et T41, et un lecteur sans mesure de faux positifs ne donnerait qu'un indice faible d'une portée mal connue.

## Conséquences

- Le catalogue 0.6.0 inscrit `M-DWTDCT` avec la raison `lecteur_a_venir` : le rapport d'une image le dit non recherché.
- T32 est inscrite en V1, après T40 et T41, dont elle partage le décodage des pixels : statut et placement proposés par l'assistant, soumis dans la PR. ADR-0012 ne retient en V1 que le point d'extension de F-24 : la question du statut de T32 (V1 ou candidate V2) reste ouverte jusqu'à la validation de TheDarkMac.
- T32 devra choisir le décodage des pixels (nouvel ADR, avec T40 et T41), mesurer les faux positifs du seuil de bits concordants sur le corpus, et fixer la direction et le niveau du constat ; ce n'est jamais une preuve (ADR-0021 : message public et fixe, schéma non cryptographique).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (réponse de TheDarkMac à la question posée pendant T31) |
