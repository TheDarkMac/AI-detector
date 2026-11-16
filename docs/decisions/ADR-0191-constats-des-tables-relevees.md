# ADR-0191 — Constats des tables relevées : Photoshop vers la transformation, appareil vers l'authenticité

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : complément de T40
- **Exigences liées** : F-30, F-80, F-81 ; ADR-0018, ADR-0055, ADR-0155, ADR-0180, ADR-0181, ADR-0182

## Contexte

Le complément de T40 (ADR-0180) livre au catalogue, par leur empreinte (ADR-0181), des tables de quantification fixes relevées sur des fichiers publics : celles de Photoshop et celles d'appareils photo. Il fallait dire ce que dit un constat sur ces tables : sa catégorie, sa direction, son niveau et son fondement. Les règles de T24 et de T40 sur les tables d'encodeurs logiciels sont des indices faibles vers la transformation (ADR-0155, ADR-0182).

## Options envisagées

### Option A — Indice faible ; Photoshop vers la transformation, appareil vers l'authenticité

Des tables de Photoshop disent que le fichier a été enregistré par ce logiciel, donc qu'il n'est plus celui de l'appareil ; des tables d'appareil disent que la dernière compression est celle d'un appareil, ce qui va dans le sens d'un fichier original.

- Avantages : chaque direction dit ce que la table montre ; même niveau que les autres règles de tables ; un appareil n'est pas une transformation.
- Inconvénients : la direction « authenticité » entre dans le module `image`, qui ne l'avait pas (une version du module).

### Option B — Deux indices vers la transformation

- Avantages : aucune direction nouvelle.
- Inconvénients : faux pour un appareil, dont les tables sont celles d'un fichier qui n'a pas été réencodé.

### Option C — Informations neutres (`rien_de_particulier`)

- Avantages : rien d'affirmé avant la mesure sur le corpus.
- Inconvénients : le résumé ne verrait pas un enregistrement par Photoshop, qu'il voit pour libjpeg ou mozjpeg ; la catégorie « information » est celle d'une absence (ADR-0151), pas d'une observation qui oriente.

## Décision

Option A : catégorie `indice`, niveau `faible`, fondement `verification_deterministe` ; direction `transformation` pour les tables de Photoshop, `authenticite` pour celles d'un appareil. Le manifeste du module `image` déclare les deux directions.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle dirait d'un fichier sorti d'un appareil qu'il a été transformé.
- Option C écartée : elle traiterait autrement deux observations de même nature que les règles de T24 et de T40.
- Niveau faible : des tables se recopient (un logiciel peut écrire celles d'un appareil, et l'inverse), et aucun taux n'est mesuré avant le corpus (T100).

## Conséquences

- Le manifeste du module `image` passe à la version 0.3.0 (ADR-0196).
- Un fichier d'appareil retouché puis réenregistré par Photoshop porte les tables de Photoshop : le constat dit la dernière compression, pas l'histoire du fichier ; les limites des règles le disent.
- La mesure sur le corpus (T100) pourra changer le niveau.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création ; décision prise par TheDarkMac le 2026-11-15, avant le relevé, dans la première session du complément |
