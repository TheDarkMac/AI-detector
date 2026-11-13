# Fiche technique — Métadonnées XMP

- **Module** : `xmp` (version 0.3.0)
- **Tâche** : T20, T21
- **Exigences** : F-10, ES-05, ES-13
- **Formats** : `jpeg`, `png`, `webp`, `heic`, `pdf`, `wav`, `m4a`, `mp4`, `mov`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`

## Question

Quelles propriétés XMP le fichier, image, document, son ou vidéo, déclare-t-il : auteur, logiciel, historique d'édition, droits, déclarations IPTC (dont `DigitalSourceType`) ?

## Principe

Le module trouve chaque paquet XMP du conteneur et le lit comme du XML, par l'expat de la bibliothèque standard, sans DTD ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)). Il parcourt ensuite le RDF (XMP, partie 1) : descriptions `rdf:Description`, propriétés écrites en attributs ou en éléments, tableaux `rdf:Bag`, `rdf:Seq` et `rdf:Alt`, structures (`rdf:parseType="Resource"`, description imbriquée, attributs), valeurs qualifiées (`rdf:value`), ressources (`rdf:resource`). Chaque propriété devient une observation.

## Entrées

| Format | Emplacement lu ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)) |
| --- | --- |
| JPEG | Segment APP1 `http://ns.adobe.com/xap/1.0/` ; morceaux du paquet étendu (APP1 `http://ns.adobe.com/xmp/extension/`), réassemblés par GUID |
| PNG | Bloc `iTXt` de mot-clé `XML:com.adobe.xmp`, décompressé au besoin |
| WebP | Bloc `XMP` |
| HEIC | Éléments `mime` de type `application/rdf+xml` |
| PDF | Flux `/Metadata` du catalogue courant (ISO 32000-2, §14.3.2), décodé au besoin (`FlateDecode`) ; structure lue par le lecteur PDF du projet ([ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md), [ADR-0127](../decisions/ADR-0127-metadonnees-pdf-lues.md)) |
| WAV | Bloc `_PMX` ([ADR-0134](../decisions/ADR-0134-xmp-des-fichiers-audio-et-video.md)) |
| M4A, MP4, MOV | Boîte `uuid` de premier niveau d'identifiant `BE7ACFCB-97A9-42E8-9C71-999491E3AFAC` ; boîte `XMP_` de `moov/udta` (ADR-0134) |

Aucune donnée de référence.

## Sorties

Noms d'observation ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md)) :

| Nom | Valeur |
| --- | --- |
| `xmp.present` | Vrai si au moins un paquet a été trouvé ; toujours observé (F-14) |
| `xmp.blocs` | Nombre de paquets principaux ; pour un PDF, 1 si le catalogue désigne un paquet ; pour un MP4, un MOV ou un M4A, les boîtes `uuid` XMP et `XMP_` ensemble |
| `xmp.etendu.blocs` | Nombre de morceaux de paquet étendu (JPEG), s'il y en a |
| `xmp.<préfixe>:<propriété>` | Valeur d'une propriété simple (texte), ou liste pour un tableau, même d'un seul élément |
| `xmp.<p>:<propriété>.<p>:<champ>` | Champ d'une structure ; pour un tableau de structures, liste des valeurs de ce champ, dans l'ordre |
| `xmp.x:xmptk` | Outil qui a écrit le paquet (attribut de `x:xmpmeta`) |
| `xmp.espace.ns<k>` | Adresse de l'espace de noms inconnu numéro `k` |
| `<nom>.longueur` | Longueur entière d'une valeur coupée ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |

Le préfixe vient de l'adresse de l'espace de noms, jamais du préfixe écrit dans le fichier : `dc`, `xmp`, `xmpMM`, `photoshop`, `exif`, `tiff`, `Iptc4xmpCore`, `Iptc4xmpExt`, `crs`, `GPano`… (table `ESPACES` de `modules/_lecture/xmp.py`) ; un espace inconnu prend `ns1`, `ns2`… dans l'ordre de première apparition. Un caractère d'un nom local hors des lettres ASCII, des chiffres et du tiret devient un tiret (le point compris, qui sépare les parties d'un nom). Le qualificatif `xml:lang` n'est pas observé : un `rdf:Alt` de langues donne la liste de ses valeurs, dans l'ordre du fichier. Le paquet étendu n'est lu que complet et désigné par la propriété `xmpNote:HasExtendedXMP` du paquet principal (XMP, partie 3) ; ses propriétés suivent celles du paquet principal, sous les mêmes noms.

Aucun constat. La propriété `Iptc4xmpExt:DigitalSourceType`, qui peut déclarer une origine IA (F-11), est observée telle quelle ; la règle qui la lit vient avec T22.

## Données identifiantes

Marquées par le module, d'après le premier composant identifiant du nom ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)) :

| Catégorie | Propriétés |
| --- | --- |
| `metadonnee_nominative` | `dc:creator`, `dc:rights`, `dc:contributor`, `dc:publisher`, `xmpRights:Owner`, `photoshop:AuthorsPosition`, `photoshop:CaptionWriter`, `photoshop:Credit`, `Iptc4xmpCore:CreatorContactInfo` (tous ses champs), `Iptc4xmpExt:PersonInImage`, `Iptc4xmpExt:AOCreator`, `plus:Licensor`, `plus:CopyrightOwner`, `plus:ImageCreator`, `plus:ImageSupplier`, `aux:OwnerName`, `exifEX:CameraOwnerName`, `exifEX:Photographer`, `exifEX:ImageEditor`, `tiff:Artist`, `tiff:Copyright`, `mwg-rs:Name` |
| `numero_de_serie` | `aux:SerialNumber`, `aux:LensSerialNumber`, `exifEX:BodySerialNumber`, `exifEX:LensSerialNumber`, `exif:ImageUniqueID`, `exifEX:ImageUniqueID` |
| `gps` | Propriétés `GPS…` des espaces `exif`, `exifEX` et `Iptc4xmpExt` |
| `nom_de_fichier` | `stRef:filePath` (dans toute structure), `xmpMM:PreservedFileName`, `crs:RawFileName`, `exif:RelatedSoundFile` |

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Rien |

Le module ne distingue aucune hypothèse et n'émet aucun constat ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)). Une déclaration XMP n'est jamais une preuve (ADR-0021, cas d'abus C-02) : les règles de T22 qui liront `DigitalSourceType` en feront au mieux une déclaration.

## Ce qui déclenche un constat

Aucun constat en T20. Une absence de XMP est l'observation `xmp.present` à faux (F-14).

## Taux d'erreur

Sans objet : aucun constat. Fidélité de l'extraction vérifiée contre exiftool, par le nom local de chaque propriété ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)) ; pour la vidéo, sur un MP4 et un MOV dont exiftool a écrit le paquet ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)).

## Limites connues

- Les qualificatifs autres que `rdf:value` ne sont pas observés (langue d'un `rdf:Alt`, qualificatifs `xmpidq`).
- Un paquet étendu incomplet, ou que le paquet principal ne désigne pas, n'est pas lu (non mené pour format partiel).
- PDF : seuls le catalogue courant et son flux `/Metadata` sont lus. Les paquets attachés aux pages, images, polices ou formulaires ne le sont pas (T53), ni ceux des révisions antérieures (T50). Un document chiffré n'a son paquet lu que si `/EncryptMetadata` vaut faux ; sinon le paquet est non mené, jamais déchiffré ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md)). Une structure PDF illisible (table des références croisées, objet, flux) est non menée pour format partiel ou fichier tronqué, sans reconstruction ([ADR-0125](../decisions/ADR-0125-lecture-stricte-du-pdf.md)).
- Les paquets portés autrement ne sont pas lus : étiquette `XMLPacket` d'un bloc EXIF (sa taille est observée par `exif`), ressource Photoshop `0x0424`, texte « Raw profile type xmp » d'un PNG (relevé par `textepng`), trame ID3 `PRIV` de propriétaire `XMP` (sa taille est observée par `id3`).
- Audio et vidéo : FLAC, Ogg, WebM, MP3 et AAC n'ont pas d'emplacement XMP normalisé, `xmp` ne s'y applique pas. Dans un MP4, un MOV ou un M4A, un paquet des pistes (`trak`) n'est pas lu ([ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md)). Un `udta` mal formé arrête le parcours : `xmp` le dit par l'arrêt du conteneur, `quicktime` par le bloc qu'il n'a pas lu.
- Un paquet dont le XML est invalide est lu jusqu'à l'erreur ; ce qui précède est observé, et le paquet est non mené pour format partiel.
- Des noms locaux qui ne diffèrent que par un caractère remplacé par un tiret donnent le même nom d'observation.

## Sécurité

- DTD, déclaration d'entité et entité externe refusées : la lecture s'arrête (ES-05, M-02, M-04) ; aucune résolution réseau ni lecture de fichier.
- Chaque élément XML compte un objet, chaque niveau un niveau d'imbrication (64 au plus, ADR-0078).
- Le texte d'un `iTXt` compressé et un flux PDF `FlateDecode` sont décompressés par `Contexte.decompresser`, donc comptés dans le budget de décompression ; aucune autre décompression.
- PDF : chaque objet lu compte un objet, chaque résolution de référence un niveau d'imbrication ; les références circulaires sont refusées.
- Le paquet étendu n'est assemblé qu'une fois couvert par ses morceaux : sa taille ne dépasse pas ce qui a été lu du fichier.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-10-28 | 0.1.0 | Création (T20) |
| 2026-11-12 | 0.2.0 | PDF : paquet du catalogue (T21, ADR-0127) |
| 2026-11-13 | 0.3.0 | WAV, M4A, MP4, MOV : blocs `_PMX`, boîtes `uuid` et `XMP_` (T21, complément audio et vidéo, ADR-0134) |
