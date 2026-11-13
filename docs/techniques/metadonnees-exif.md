# Fiche technique — Métadonnées EXIF

- **Module** : `exif` (version 0.2.0)
- **Tâche** : T20, T22
- **Exigences** : F-10, F-12, ES-13
- **Formats** : `jpeg`, `png`, `webp`, `heic`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Quelles métadonnées EXIF le fichier déclare-t-il : appareil, logiciel, dates, réglages de prise de vue, position ?

## Principe

Le module trouve chaque bloc EXIF du conteneur, puis lit sa structure TIFF (TIFF 6.0 ; EXIF 3.0, CIPA DC-008-2023) : en-tête, IFD0, répertoires chaînés (IFD1 pour la vignette, puis IFD2…), sous-répertoires EXIF, GPS et interopérabilité désignés par leur étiquette. Chaque entrée devient une observation. Rien n'est interprété : une date reste le texte écrit dans le fichier, une fraction devient le nombre qu'elle vaut.

Le lecteur est écrit par le projet, en Python pur, sans bibliothèque tierce ([ADR-0043](../decisions/ADR-0043-politique-des-bibliotheques.md), [ADR-0114](../decisions/ADR-0114-un-module-par-famille-de-metadonnees.md)).

## Entrées

| Format | Emplacement lu ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)) |
| --- | --- |
| JPEG | Segments APP1 commençant par `Exif` et deux octets, avant le premier SOS |
| PNG | Blocs `eXIf` |
| WebP | Blocs `EXIF`, avec ou sans le préfixe `Exif\0\0` recopié du JPEG |
| HEIC | Éléments de type `Exif` (boîtes `iinf` et `iloc` de `meta`), données dans le fichier ou dans `idat` ; les quatre premiers octets donnent la position de l'en-tête TIFF |

Aucune donnée de référence.

## Sorties

Noms d'observation ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md)) :

| Nom | Valeur |
| --- | --- |
| `exif.present` | Vrai si au moins un bloc EXIF a été trouvé ; toujours observé (F-14) |
| `exif.blocs` | Nombre de blocs EXIF, s'il y en a |
| `exif.ordre` | `II` (Intel) ou `MM` (Motorola), ordre des octets de chaque bloc |
| `exif.<répertoire>.<étiquette>` | Valeur de l'étiquette ; répertoire `ifd0`, `ifd1`…, `exif`, `gps`, `interop` |
| `exif.<répertoire>.<étiquette>.taille` | Taille en octets d'une donnée binaire non décodée (`MakerNote`, profil ICC, paquet XMP ou IPTC logé dans TIFF, motif CFA…) |
| `<nom>.longueur` | Longueur entière d'une valeur coupée ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |

Une étiquette porte le nom de la norme EXIF 3.0 ou de TIFF 6.0 (`Make`, `DateTimeOriginal`, `PhotographicSensitivity`, `PixelXDimension`…) ; quelques étiquettes courantes hors norme portent celui de leur auteur (`XPAuthor`, `Rating`, `PrintImageMatching`) ; une étiquette inconnue, son numéro (`exif.ifd0.0x1234`). Les noms diffèrent parfois de ceux d'exiftool (`ISO` chez exiftool, `PhotographicSensitivity` ici) ; la table est dans `modules/exif/etiquettes.py`.

Valeurs, par type TIFF : texte ASCII jusqu'au premier octet nul, en UTF-8 s'il est valide, en Latin-1 sinon ; texte UTF-8 (type 129 d'EXIF 3.0) ; entier, ou liste d'entiers s'il y en a plusieurs ; fraction rendue en nombre réel, ou en texte `n/0` si son dénominateur est nul ; réel non fini en texte (`nan`). Les versions (`ExifVersion`, `FlashpixVersion`, `InteroperabilityVersion`) sont rendues en texte, `UserComment`, `GPSProcessingMethod` et `GPSAreaInformation` décodés selon leur code de huit octets (ASCII, UNICODE dans l'ordre du bloc, JIS), les étiquettes `XP…` en UTF-16. Les autres octets indéfinis sont observés par leur taille.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

Marquées par le module ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)) :

| Catégorie | Étiquettes |
| --- | --- |
| `metadonnee_nominative` | `Artist`, `HostComputer`, `Copyright`, `XPAuthor` ; `CameraOwnerName`, `Photographer`, `ImageEditor` |
| `numero_de_serie` | `BodySerialNumber`, `LensSerialNumber`, `ImageUniqueID` |
| `gps` | Toutes les étiquettes du répertoire GPS |
| `nom_de_fichier` | `DocumentName`, `RelatedSoundFile` |

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien : le module rapporte ce que le fichier déclare, sans le juger |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `Software`, paramètres d'AUTOMATIC1111 dans `UserComment` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations.

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-EXIF-001` Générateur nommé par l'étiquette Software ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `exif.ifd0.Software` | liste des générateurs (ADR-0144) | origine IA |
| `R-EXIF-002` Paramètres de génération au format d'AUTOMATIC1111 dans le commentaire EXIF ([ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md)) | `exif.exif.UserComment` | motif `Steps: [0-9]+, Sampler:` | origine IA |

Une absence d'EXIF est l'observation `exif.present` à faux, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). La fidélité de l'extraction est vérifiée contre exiftool sur des échantillons des quatre formats ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)).

## Limites connues

- `MakerNote` n'est pas décodé : un numéro de série ou un réglage propre au fabricant qui ne figure que là n'est pas observé (sa taille l'est).
- Les répertoires `SubIFDs` (TIFF, DNG) ne sont pas suivis ; IFD1 et suivants sont lus par le chaînage d'IFD0.
- Les blocs EXIF portés autrement ne sont pas lus : texte brut « Raw profile type exif » d'un PNG (relevé par le module `textepng`), ressource Photoshop `0x0422`, segment APP1 après le premier SOS.
- Les positions des valeurs ne sont pas données une à une : la localisation est celle du bloc et du répertoire.
- Le module ne vérifie ni les dates ni la cohérence entre étiquettes (T23).

## Sécurité

- Lecture bornée par le contexte ; un bloc de plus de 16 Mio n'est pas lu (format partiel).
- Chaque entrée compte un objet, chaque répertoire un niveau d'imbrication (ADR-0078) ; un répertoire déjà lu n'est pas relu (boucle).
- Les valeurs sont des vues sur le bloc, sans copie ; une liste est décodée jusqu'à 4 097 éléments au plus.
- Aucune décompression, aucun décodage d'image.
- Les codecs UTF-16 et Shift_JIS sont chargés à l'import du module, avant les restrictions du processus de travail (ADR-0079, ERR-0009).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-10-28 | 0.1.0 | Création (T20) |
| 2026-11-12 | 0.1.1 | Étiquettes `XP…` et commentaires `UNICODE` ou `JIS` lus dans le processus de travail restreint, où ils mettaient le module en erreur (ERR-0009, T21) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
