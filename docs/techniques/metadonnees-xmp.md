# Fiche technique — Métadonnées XMP

- **Module** : `xmp` (version 0.4.0)
- **Tâche** : T20, T21, T22, T23
- **Exigences** : F-10, F-11, F-12, ES-05, ES-13
- **Formats** : `jpeg`, `png`, `webp`, `heic`, `pdf`, `wav`, `m4a`, `mp4`, `mov`
- **Directions permises** : `origine_ia`, `retouche`, `rien_de_particulier`
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

Le module n'émet aucun constat. La propriété `Iptc4xmpExt:DigitalSourceType`, qui peut déclarer une origine IA (F-11), est observée telle quelle ; les règles R-XMP-001 à R-XMP-003 la lisent ([ADR-0143](../decisions/ADR-0143-valeurs-iptc-de-la-source-numerique.md)).

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
| Retouche | Ce que le fichier en déclare, sans vérification : `DigitalSourceType` à `compositeWithTrainedAlgorithmicMedia` ou `compositeSynthetic` |
| Génération | Ce que le fichier en déclare, sans vérification : `DigitalSourceType` à `trainedAlgorithmicMedia`, nom d'un générateur dans `xmp:CreatorTool` ou l'historique |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. Une déclaration XMP n'est jamais une preuve (ADR-0021, cas d'abus C-02).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-XMP-001` Création par IA générative déclarée (IPTC) ([ADR-0143](../decisions/ADR-0143-valeurs-iptc-de-la-source-numerique.md)) | `xmp.Iptc4xmpExt:DigitalSourceType` | valeur IPTC `trainedAlgorithmicMedia`, adresse ou code seul | origine IA |
| `R-XMP-002` Retouche par IA générative déclarée (IPTC) ([ADR-0143](../decisions/ADR-0143-valeurs-iptc-de-la-source-numerique.md)) | `xmp.Iptc4xmpExt:DigitalSourceType` | valeur IPTC `compositeWithTrainedAlgorithmicMedia`, adresse ou code seul | retouche |
| `R-XMP-003` Montage avec un élément généré par IA déclaré (IPTC) ([ADR-0143](../decisions/ADR-0143-valeurs-iptc-de-la-source-numerique.md)) | `xmp.Iptc4xmpExt:DigitalSourceType` | valeur IPTC `compositeSynthetic`, adresse ou code seul | retouche |
| `R-XMP-004` Générateur nommé par l'outil de création XMP ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `xmp.xmp:CreatorTool` | liste des générateurs (ADR-0144) | origine IA |
| `R-XMP-005` Générateur nommé dans l'historique XMP ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `xmp.xmpMM:History.stEvt:softwareAgent` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-XMP-006` Date de création impossible (xmp:CreateDate) | `xmp.xmp:CreateDate` | date impossible (`date-iso8601`) |
| `R-XMP-007` Date de modification impossible (xmp:ModifyDate) | `xmp.xmp:ModifyDate` | date impossible (`date-iso8601`) |
| `R-XMP-008` Date des métadonnées impossible (xmp:MetadataDate) | `xmp.xmp:MetadataDate` | date impossible (`date-iso8601`) |
| `R-XMP-009` Création postérieure à la modification (xmp:CreateDate, xmp:ModifyDate) | `xmp.xmp:CreateDate`, `xmp.xmp:ModifyDate` | certainement postérieure à `xmp.xmp:ModifyDate`, lues par `date-iso8601` |
| `R-XMP-010` Création postérieure aux métadonnées (xmp:CreateDate, xmp:MetadataDate) | `xmp.xmp:CreateDate`, `xmp.xmp:MetadataDate` | certainement postérieure à `xmp.xmp:MetadataDate`, lues par `date-iso8601` |
| `R-XMP-011` Appareil déclaré et générateur nommé (tiff:Make, xmp:CreatorTool) | `xmp.tiff:Make`, `xmp.xmp:CreatorTool` | présente ; liste des générateurs (ADR-0144) |
| `R-XMP-012` Aucune métadonnée XMP | `xmp.present` | faux |

Une absence de XMP est l'observation `xmp.present` à faux ; la règle `R-XMP-012` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, par le nom local de chaque propriété ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)) ; pour la vidéo, sur un MP4 et un MOV dont exiftool a écrit le paquet ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

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
| 2026-11-13 | 0.4.0 | Directions origine IA, retouche permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.4.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
