# ADR-0150 — Incohérences retenues : dates, appareil et générateur, dimensions d'un générateur

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac pour les dimensions (liste du catalogue), parmi les options proposées par l'assistant ; l'assistant pour le reste, sur proposition non posée en question, à valider par TheDarkMac pendant la revue de la PR de T23
- **Tâche** : T23
- **Exigences liées** : F-13, F-26 ; A-32 ; ADR-0084, ADR-0144, ADR-0147, ADR-0148, ADR-0149

## Contexte

F-13 nomme trois familles d'incohérences : dates impossibles, logiciel incompatible avec l'appareil déclaré, dimensions atypiques. Les douze modules de métadonnées observent des dates, des appareils, des logiciels et des dimensions ; ADR-0147 permet de comparer deux observations d'un même module. Restait à dire lesquelles comparer.

Aucun module n'observe les dimensions réelles d'une image (en-têtes SOF, IHDR…) : seules les dimensions que déclare l'EXIF (`PixelXDimension`, `PixelYDimension`) sont lues. A-32 demande que les listes de référence soient dans le catalogue.

## Options envisagées

### Dimensions atypiques (question posée)

- **A — Liste dans le catalogue** : dimensions EXIF qui sont des tailles de sortie documentées de générateurs, alors qu'un appareil photo est déclaré (`Make`).
- **B — Dimensions réelles contre dimensions déclarées** : une nouvelle observation des dimensions de l'image, puis une comparaison entre modules, que T23 n'écrit pas (ADR-0147, option C).
- **C — Reporter à T24**, avec les dimensions typiques des messageries.

### Dates

- **A — Dans chaque module, les paires que fixe la définition des champs** : création au plus tard à la modification, prise de vue au plus tard à la numérisation ; et chaque date de ces paires, si elle est impossible.
- **B — Toutes les dates observées, deux à deux** : sans définition qui fixe leur ordre, une paire n'est pas une incohérence (date de prise de vue d'une photo ancienne numérisée, date d'impression).

### Logiciel et appareil

- **A — Appareil déclaré et générateur nommé** : une marque d'appareil (`Make`, `tiff:Make`) et, dans le champ logiciel du même module, un nom de la liste des générateurs (ADR-0144).
- **B — Listes de modèles et de logiciels par fabricant** : marque et modèle qui ne vont pas ensemble, logiciel interne d'un autre fabricant ; listes longues, sans source publique complète, à tenir à jour.

## Décision

Dimensions A, dates A, logiciel et appareil A : trente-huit règles, dont douze d'absence (ADR-0151).

| Module | Dates impossibles | Ordre renversé | Autres |
| --- | --- | --- | --- |
| `exif` | `DateTime`, `DateTimeOriginal`, `DateTimeDigitized` | prise de vue après modification, numérisation après modification, prise de vue après numérisation | `Make` et générateur dans `Software` ; `Make` et dimensions d'un générateur (carrées, paysage, portrait) |
| `xmp` | `xmp:CreateDate`, `xmp:ModifyDate`, `xmp:MetadataDate` | création après modification, création après la date des métadonnées | `tiff:Make` et générateur dans `xmp:CreatorTool` |
| `infopdf` | `CreationDate`, `ModDate` | création après modification | — |
| `ooxml` | `dcterms:created`, `dcterms:modified` | création après modification | — |
| `odf` | `meta:creation-date`, `dc:date` | création après modification | — |
| `quicktime` | — | création après modification (`mvhd`) | — |

- Dimensions : tailles fixes de l'API d'images d'OpenAI, la seule source d'éditeur trouvée (référence de l'API, lue le 2026-11-13) : 256 × 256, 512 × 512, 1 024 × 1 024, 1 536 × 1 024, 1 024 × 1 536, 1 792 × 1 024, 1 024 × 1 792. Trois règles : carré (largeur parmi 256, 512, 1 024 et hauteur égale), paysage (1 536 ou 1 792 sur 1 024), portrait (1 024 sur 1 536 ou 1 792).
- Écartés, avec leur raison :
  - dates IPTC-IIM (`DateCreated` et `TimeCreated` en deux enregistrements, aucune date de modification), ID3, RIFF, Vorbis, blocs texte PNG (texte libre ou date unique), Matroska (une seule date) : aucune paire que fixe une définition ;
  - `cp:lastPrinted`, `meta:print-date` : une impression peut précéder une modification comme la suivre ;
  - dates d'une famille contre celles d'une autre (EXIF contre XMP) : comparaison entre modules (ADR-0147) ;
  - date antérieure à l'existence d'un format, ou à l'invention de la photographie : une photo ancienne numérisée la déclare légitimement ;
  - date postérieure à l'analyse : NF-06 (ADR-0148) ;
  - appareil et générateur dans une vidéo (`com-apple-quicktime-make` et `©swr`) : aucune source d'un fichier réel qui écrive les deux ;
  - autres tailles de générateurs (Stable Diffusion, Midjourney) : aucune source de l'éditeur ; tailles libres des modèles récents d'OpenAI (`gpt-image-2`, multiples de 16) : aucune liste possible.

## Raisons

- Dimensions A retenue par TheDarkMac, sur recommandation de l'assistant ; B écartée parce qu'elle demande une comparaison entre modules, C parce qu'elle laisserait F-13 partielle à la fin de T23.
- Dates A : une paire ne se contredit que si la définition des champs fixe leur ordre (EXIF 3.0 pour `DateTimeOriginal` et `DateTimeDigitized`, XMP pour `xmp:MetadataDate` « égale ou postérieure » à `xmp:ModifyDate`, PDF, OOXML et ODF pour la création et la modification) ; B produirait des constats sur des fichiers cohérents.
- Logiciel A : la liste des générateurs existe et est sourcée (ADR-0144) ; B demanderait des listes que le projet ne peut ni sourcer ni tenir.

## Conséquences

- F-13 est réalisée dans les limites écrites dans chaque règle ; la mesure sur le corpus (T100) dira ce que valent ces informations.
- Une nouvelle paire de dates ou une nouvelle taille s'ajoute au catalogue sans nouvelle version de l'outil (F-26).
- La fiche de chaque module liste les règles qui lisent ses observations.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
