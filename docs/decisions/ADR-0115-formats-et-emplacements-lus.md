# ADR-0115 — Formats couverts et emplacements lus : JPEG, PNG, WebP et HEIC

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac pour les formats, parmi les options proposées par l'assistant ; emplacements lus et non lus proposés par l'assistant, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : F-10, F-25, A-23 ; ADR-0070, ADR-0114

## Contexte

Le périmètre compte quatre formats d'image (ADR-0070) : JPEG, PNG, WebP et HEIC. Les trois premiers portent leurs métadonnées dans des blocs simples ; HEIC les range dans des éléments de la boîte `meta` d'ISOBMFF, localisés par `iinf` et `iloc`, ce qui demande un lecteur de plus. Un module qui ne déclare pas un format est « non applicable » à la couverture de ce format (ADR-0059) : ne pas lire HEIC le ferait apparaître ainsi, alors qu'il a des métadonnées.

## Options envisagées

### Option A — Les quatre formats

- Avantages : couverture exacte pour toutes les images du périmètre.
- Inconvénients : lecteur ISOBMFF à écrire et à soumettre au fuzzing.

### Option B — Sans HEIC

- Avantages : moins de code en T20.
- Inconvénients : la couverture d'un HEIC dirait « non applicable », ce qui est inexact ; une tâche de plus.

## Décision

Option A. Emplacements lus, par format et par module (proposés par l'assistant) :

| Format | `exif` | `xmp` | `iptc` | `textepng` |
| --- | --- | --- | --- | --- |
| JPEG | APP1 `Exif` | APP1 XMP ; APP1 XMP étendu | APP13 `Photoshop 3.0`, ressource `0x0404` | — |
| PNG | `eXIf` | `iTXt` `XML:com.adobe.xmp` | — | `tEXt`, `zTXt`, `iTXt` |
| WebP | `EXIF` | `XMP` | — | — |
| HEIC | Élément `Exif` | Élément `mime` `application/rdf+xml` | — | — |

- JPEG : segments parcourus jusqu'au premier SOS ou à EOI ; les métadonnées les précèdent (T.81, annexe B).
- PNG : blocs parcourus jusqu'à `IEND`, avant comme après les données d'image.
- HEIC : premier `meta` de premier niveau ; éléments dont les données sont dans le fichier (`construction_method` 0) ou dans `idat` (1) ; un élément dans un autre fichier (`data_reference_index` non nul) ou d'une autre méthode n'est pas lu (format partiel).
- Ne sont pas lus en T20, et chaque fiche le dit : MakerNote, `SubIFDs`, ressources Photoshop autres que `0x0404`, EXIF, XMP ou IPTC logés dans un autre bloc (étiquettes `XMLPacket` et `IPTC-NAA` d'EXIF, ressources `0x0422` et `0x0424`, textes « Raw profile type » d'un PNG), bloc `tIME`, segments après le premier SOS.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : couverture inexacte pour HEIC.
- `iptc` réduit au JPEG : aucun des trois autres formats ne prévoit d'emplacement pour l'IIM ; « non applicable » y est exact.
- Emplacements non lus : rares en pratique, ou propres à un fabricant (MakerNote) ; les lire demanderait chacun un décodeur, sans changer ce que T22 et T23 ont besoin de lire d'abord. Leur taille, quand elle est connue, est observée.

## Conséquences

- Le lecteur ISOBMFF de `conteneurs` est soumis au fuzzing avec les autres (ES-19).
- Les emplacements non lus sont des limites connues des fiches ; T22 ou une tâche ultérieure pourra en ajouter un, par un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création ; emplacements à valider pendant la revue de la PR de T20 |
