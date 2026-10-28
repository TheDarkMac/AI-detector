# ADR-0119 — Données identifiantes des métadonnées : champs marqués par chaque module

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T20, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : ES-13, NF-13, NF-18, F-90 ; menace M-22 ; ADR-0057, ADR-0093, ADR-0095

## Contexte

ADR-0057 fait marquer par le module chaque observation identifiante, dans l'une des catégories d'ES-13 : métadonnée nominative, numéro de série, GPS, nom de fichier, empreinte. Le rapport les masque par défaut et l'export JSON les omet (ADR-0093, ADR-0095). Les modules de T20 sont les premiers à en produire. Une donnée non marquée part en clair dans tout rapport transmis ; une donnée marquée à tort est seulement masquée.

## Options envisagées

### Option A — Liste fermée par famille, au plus près de la norme

Chaque module marque les champs que sa norme définit comme nom de personne, identifiant d'appareil, position ou nom de fichier.

- Avantages : liste courte, lisible dans la fiche, testée par catégorie ; le marquage est fait par le code qui lit le champ (ADR-0057).
- Inconvénients : un champ libre (légende, commentaire) peut contenir un nom sans être marqué.

### Option B — Tout marquer

- Avantages : aucune fuite possible.
- Inconvénients : un rapport tout masqué n'apprend rien ; l'utilisateur lève le masquage par catégorie et l'oubli devient général.

### Option C — Marquer aussi les textes libres et les lieux

- Avantages : moins de fuites par une légende ou une ville.
- Inconvénients : aucune catégorie d'ES-13 ne couvre un lieu ou un texte libre ; il faudrait en créer, donc changer le modèle et le schéma.

## Décision

Option A. Champs marqués :

| Catégorie | EXIF | XMP | IPTC-IIM | PNG |
| --- | --- | --- | --- | --- |
| `metadonnee_nominative` | `Artist`, `HostComputer`, `Copyright`, `XPAuthor`, `CameraOwnerName`, `Photographer`, `ImageEditor` | `dc:creator`, `dc:rights`, `dc:contributor`, `dc:publisher`, `xmpRights:Owner`, `photoshop:AuthorsPosition`, `photoshop:CaptionWriter`, `photoshop:Credit`, `Iptc4xmpCore:CreatorContactInfo`, `Iptc4xmpExt:PersonInImage`, `Iptc4xmpExt:AOCreator`, `plus:Licensor`, `plus:CopyrightOwner`, `plus:ImageCreator`, `plus:ImageSupplier`, `aux:OwnerName`, `exifEX:CameraOwnerName`, `exifEX:Photographer`, `exifEX:ImageEditor`, `tiff:Artist`, `tiff:Copyright`, `mwg-rs:Name` | `By-line`, `By-lineTitle`, `Credit`, `CopyrightNotice`, `Contact`, `Writer-Editor` | `Author`, `Copyright` |
| `numero_de_serie` | `BodySerialNumber`, `LensSerialNumber`, `ImageUniqueID` | `aux:SerialNumber`, `aux:LensSerialNumber`, `exifEX:BodySerialNumber`, `exifEX:LensSerialNumber`, `exif:ImageUniqueID`, `exifEX:ImageUniqueID` | — | — |
| `gps` | Tout le répertoire GPS | `GPS…` des espaces `exif`, `exifEX`, `Iptc4xmpExt` | — | — |
| `nom_de_fichier` | `DocumentName`, `RelatedSoundFile` | `stRef:filePath`, `xmpMM:PreservedFileName`, `crs:RawFileName`, `exif:RelatedSoundFile` | — | — |

- Une propriété XMP est marquée par le premier composant identifiant de son nom : tous les champs de `Iptc4xmpCore:CreatorContactInfo` sont nominatifs, `stRef:filePath` l'est dans toute structure (`xmpMM:DerivedFrom`, `xmpMM:Ingredients`…).
- Une donnée binaire identifiante observée par sa taille garde sa catégorie.

## Raisons

- Option A : elle suit ADR-0057 (marquage par le code qui lit le champ) et reste vérifiable ligne à ligne.
- Option B écartée : un rapport illisible pousse à tout révéler.
- Option C écartée : changement du modèle (ES-13) hors du périmètre de T20 ; les lieux et textes libres sont une limite connue, écrite dans les fiches, et relèvent du contrôle avant publication (T25).
- `ImageUniqueID` marqué numéro de série : certains appareils le dérivent de leur numéro de série et il relie entre eux les fichiers d'un même appareil. Les identifiants `xmpMM:DocumentID` et `InstanceID`, propres au document et non à l'appareil, ne le sont pas.
- `HostComputer` marqué nominatif : un nom de machine désigne souvent son propriétaire.

## Conséquences

- Chaque module a un test par catégorie qu'il produit (ADR-0057).
- T25 (contrôle avant publication) s'appuie sur ces catégories, et examine les textes libres et les lieux.
- Un champ oublié se corrige par une nouvelle version du module, sans changer le modèle.
- La liste de garde par nom d'observation que P1 pourrait tenir (ADR-0057) n'est pas ajoutée : un processus de travail compromis peut encore omettre un marquage (RR-01). À décider avant T25, qui en dépend le plus.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
