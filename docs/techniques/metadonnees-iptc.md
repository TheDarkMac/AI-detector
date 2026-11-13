# Fiche technique — Métadonnées IPTC-IIM

- **Module** : `iptc` (version 0.2.0)
- **Tâche** : T20, T22, T23
- **Exigences** : F-10, F-12, ES-13
- **Formats** : `jpeg`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Quelles métadonnées IPTC-IIM le fichier déclare-t-il : légende, mots-clés, auteur, crédit, lieu, dates ?

## Principe

Le module lit les ressources Photoshop du segment APP13 (« Image Resource Blocks » d'Adobe) et, dans la ressource `0x0404` (IPTC-NAA), la suite des jeux de données IIM (IPTC-NAA IIM 4.2) : marqueur `0x1C`, enregistrement, numéro, longueur (étendue jusqu'à 4 octets), valeur. Les enregistrements 1 (enveloppe) et 2 (application) ont leurs noms ; les autres jeux sont observés par leur numéro.

Les propriétés IPTC écrites en XMP (`Iptc4xmpCore`, `Iptc4xmpExt`, dont `DigitalSourceType`) sont lues par le module `xmp` ; celui-ci ne lit que l'IIM.

## Entrées

| Format | Emplacement lu ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)) |
| --- | --- |
| JPEG | Segments APP13 `Photoshop 3.0`, ressources de signature `8BIM`, `PHUT`, `AgHg` ou `DCSR` |

Pas de PNG, de WebP ni de HEIC : aucun de ces formats ne prévoit d'emplacement pour l'IIM, et leur couverture dit « non applicable ». Aucune donnée de référence.

## Sorties

Noms d'observation ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md)) :

| Nom | Valeur |
| --- | --- |
| `iptc.present` | Vrai si une ressource IPTC-NAA a été trouvée ; toujours observé (F-14) |
| `iptc.photoshop.ressources` | Identifiants des ressources Photoshop de chaque segment, dans l'ordre |
| `iptc.<jeu>` | Valeur du jeu de données, sous le nom de l'IIM 4.2 (`ObjectName`, `Keywords`, `By-line`, `City`, `Caption-Abstract`…) |
| `iptc.<enregistrement>:<numéro>` | Valeur d'un jeu absent de la table |
| `iptc.<jeu>.taille` | Taille en octets d'un jeu binaire (`RasterizedCaption`, `ObjectPreviewData`) |
| `<nom>.longueur` | Longueur entière d'une valeur coupée ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |

Un jeu répétable selon la norme (`Keywords`, `By-line`, `SupplementalCategories`, `Contact`…) est toujours une liste ; un jeu non répétable présent plusieurs fois aussi. Les versions et formats (`ApplicationRecordVersion`, `FileFormat`…) sont des entiers. Le texte est décodé en UTF-8 si `CodedCharacterSet` le déclare (`ESC % G`) ; sinon en UTF-8 s'il est valide, en Latin-1 à défaut.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

Marquées `metadonnee_nominative` ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)) : `By-line`, `By-lineTitle`, `Credit`, `CopyrightNotice`, `Contact`, `Writer-Editor`.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `OriginatingProgram` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations.

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-IPTC-001` Générateur nommé par le programme d'origine IPTC ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `iptc.OriginatingProgram` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-IPTC-002` Aucune métadonnée IPTC-IIM | `iptc.present` | faux |

Une absence d'IPTC est l'observation `iptc.present` à faux ; la règle `R-IPTC-002` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, par le nom de chaque jeu ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

## Limites connues

- Seule la ressource `0x0404` est décodée ; les autres ressources Photoshop sont seulement listées (dont `0x0425`, empreinte MD5 de l'IIM, et `0x0422`, `0x0424`, EXIF et XMP logés dans Photoshop).
- L'IIM logé ailleurs n'est pas lu : étiquette `IPTC-NAA` d'un bloc EXIF (sa taille est observée par `exif`), texte « Raw profile type iptc » d'un PNG (relevé par `textepng`).
- Les lieux (`City`, `Sub-location`, `Province-State`, `Country-PrimaryLocationName`) ne sont pas marqués identifiants : aucune catégorie d'ES-13 ne les couvre (ADR-0119).
- Un segment APP13 coupé en plusieurs morceaux n'est pas recollé : chaque segment est lu seul.

## Sécurité

- Lecture bornée par le contexte ; chaque ressource et chaque jeu comptent un objet (ADR-0078).
- Aucune décompression, aucun décodage d'image de la vignette.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-10-28 | 0.1.0 | Création (T20) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
