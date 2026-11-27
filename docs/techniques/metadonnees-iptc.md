# Fiche technique — Métadonnées IPTC-IIM

- **Module** : `iptc` (version 0.4.0)
- **Tâche** : T20, T22, T23, T24, T25
- **Exigences** : F-10, F-12, F-90, ES-13
- **Formats** : `jpeg`
- **Directions permises** : `origine_ia`, `transformation`, `rien_de_particulier`
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

| Catégorie | Jeux de données |
| --- | --- |
| `metadonnee_nominative` | `By-line`, `By-lineTitle`, `Credit`, `CopyrightNotice`, `Contact`, `Writer-Editor` ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)) |
| `numero_de_serie` | `SpecialInstructions` dont une valeur commence par `FBMD`, identifiant d'une image diffusée par Facebook ([ADR-0161](../decisions/ADR-0161-valeur-fbmd.md)) |
| `lieu` | `ContentLocationCode`, `ContentLocationName`, `City`, `Sub-location`, `Province-State`, `Country-PrimaryLocationCode`, `Country-PrimaryLocationName` |
| `texte_libre` | `ObjectName`, `Keywords`, `SpecialInstructions` (hors FBMD), `Headline`, `Caption-Abstract`, `LocalCaption` |

Ces données sont comptées et nommées, sans leur valeur, par la rubrique « Contrôle avant publication » du rapport et par le résumé ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Ce que le fichier en déclare : `SpecialInstructions` commençant par `FBMD`, marque que Facebook écrit (IPTC, 2019) (T24) |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `OriginatingProgram` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations.

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices fondés sur une déclaration du fichier, chacun au niveau que permet sa mesure (« Taux d'erreur ») :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-IPTC-001` Générateur nommé par le programme d'origine IPTC ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `iptc.OriginatingProgram` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-IPTC-002` Aucune métadonnée IPTC-IIM | `iptc.present` | faux |

Une absence d'IPTC est l'observation `iptc.present` à faux ; la règle `R-IPTC-002` en fait une information neutre, jamais un indice (F-14).

Règle de T24, un indice vers la transformation, au niveau que permet sa mesure, fondé sur une déclaration du fichier ([ADR-0153](../decisions/ADR-0153-indices-de-transfert-retenus.md), [ADR-0155](../decisions/ADR-0155-nature-d-un-indice-de-transfert.md)) :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-IPTC-003` Marque de Facebook dans les instructions IPTC (SpecialInstructions) | `iptc.SpecialInstructions` | motif `^FBMD` | transformation |

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `iptc` 0.4.0, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 1776 | 1/609 : 0,2 % [0,0 % ; 0,9 %] | 0/608 : 0,0 % [0,0 % ; 0,6 %] | — | 0 |
| Générés | 424 | 330 | 0/94 : 0,0 % [0,0 % ; 3,9 %] | — | 94/94 : 100,0 % [96,1 % ; 100,0 %] | 0 |
| Transformés | 1294 | 781 | 0/513 : 0,0 % [0,0 % ; 0,7 %] | 0/335 : 0,0 % [0,0 % ; 1,1 %] | 178/178 : 100,0 % [97,9 % ; 100,0 %] | 0 |
| Retouchés | 273 | 162 | 0/111 : 0,0 % [0,0 % ; 3,3 %] | — | 111/111 : 100,0 % [96,7 % ; 100,0 %] | 0 |
| Malformés | 91 | 46 | 22/45 : 48,9 % [35,0 % ; 63,0 %] | 0/20 : 0,0 % [0,0 % ; 16,1 %] | 2/2 : 100,0 % [34,2 % ; 100,0 %] | 0 |

| Règle | Catégorie | Direction | Faux positifs | Niveau permis | Niveau |
| --- | --- | --- | --- | --- | --- |
| R-IPTC-001 v2 | indice | origine_ia | 0/608 : 0,0 % [0,0 % ; 0,6 %] | fort | fort |
| R-IPTC-003 v2 | indice | transformation | 0/608 : 0,0 % [0,0 % ; 0,6 %] | fort | fort |

<!-- Fin des taux mesurés. -->

Le niveau de chaque indice est celui que permet son taux de faux positifs, mesuré ci-dessus (ADR-0018, [ADR-0278](../decisions/ADR-0278-evaluation-et-niveau-des-indices-au-catalogue.md)). Le déclenchement des règles est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, par le nom de chaque jeu ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`). La règle de T24 est un indice, au niveau que permet sa mesure ; son déclenchement est vérifié sur des échantillons construits (`tests/test_transfert.py`).

## Limites connues

- Seule la ressource `0x0404` est décodée ; les autres ressources Photoshop sont seulement listées (dont `0x0425`, empreinte MD5 de l'IIM, et `0x0422`, `0x0424`, EXIF et XMP logés dans Photoshop).
- L'IIM logé ailleurs n'est pas lu : étiquette `IPTC-NAA` d'un bloc EXIF (sa taille est observée par `exif`), texte « Raw profile type iptc » d'un PNG (relevé par `textepng`).
- `Source` et `OriginalTransmissionReference` ne sont pas marqués : le premier nomme un organisme, que la liste nominative d'ADR-0119 ne couvre pas ; le second est une référence de travail (ADR-0160).
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
| 2026-11-14 | 0.3.0 | Direction transformation permise : indice de transfert du catalogue sur ses observations, `R-IPTC-003` (T24, ADR-0153 à ADR-0157) ; code du module inchangé |
| 2026-11-14 | 0.4.0 | Lieux et textes libres marqués ; valeur FBMD marquée `numero_de_serie` ; contrôle avant publication (T25, ADR-0158 à ADR-0163) |
