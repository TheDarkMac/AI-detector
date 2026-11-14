# Fiche technique — Structure d'une image

- **Module** : `image` (version 0.1.0)
- **Tâche** : T24
- **Exigences** : F-06, F-30
- **Formats** : `jpeg`, `png`, `webp`
- **Directions permises** : `transformation`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Quelles dimensions l'image a-t-elle réellement, combien de blocs de métadonnées porte-t-elle, et un JPEG est-il encodé avec les tables de quantification de la bibliothèque libjpeg ?

## Principe

Le module reprend le parcours du conteneur des modules de métadonnées ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)), qui relève aussi, depuis T24, les blocs de structure d'une image ([ADR-0154](../decisions/ADR-0154-module-image.md)) : segments SOF et DQT d'un JPEG jusqu'au premier SOS (T.81, annexe B), bloc `IHDR` d'un PNG (PNG, 3e édition), blocs `VP8X`, `"VP8 "` et `VP8L` d'un WebP (RFC 9649). Aucune donnée d'image n'est décodée.

- **Dimensions** : celles de l'en-tête de l'image, pas celles que déclare l'EXIF (`PixelXDimension`, lues par le module `exif`). Premier bloc de structure trouvé : SOF (hauteur, largeur), `IHDR` (largeur, hauteur), `VP8X` (toile, 24 bits plus un), `VP8L` (14 bits plus un), `"VP8 "` (14 bits d'une trame clé, RFC 6386, 9.1).
- **Blocs de métadonnées** : ceux que lisent les modules du projet, EXIF, XMP, XMP étendu, ressources Photoshop (IPTC), blocs texte PNG ; le profil de couleur ICC, le segment JFIF et les commentaires JPEG (COM) ne sont pas des métadonnées pour ce compte.
- **Tables de quantification** (JPEG) : chaque table définie avant le premier balayage, la dernière définition d'un identifiant l'emportant (T.81, B.2.4.1). La qualité libjpeg est reconnue si la table 0 est exactement la table de luminance de l'annexe K (tableau K.1) mise à l'échelle par libjpeg à une qualité de 1 à 100 (`jpeg_quality_scaling` et `jpeg_add_quant_table` de `jcparam.c` : facteur 5 000 / q sous 50, 200 − 2q au-delà, arrondi, borné à 1 et à 255 pour une table de huit bits, à 32 767 pour une table de seize bits), et la table 1, s'il y en a une, la table de chrominance (K.2) à la même qualité ; aucune autre table. Chaque qualité donne une table de luminance différente (vérifié par les tests) : la qualité lue est unique.

## Entrées

| Format | Emplacement lu |
| --- | --- |
| JPEG | Premier segment SOF0 à SOF15 (hors DHT, JPG, DAC) ; segments DQT avant le premier SOS ; segments des métadonnées (APP1 EXIF et XMP, APP13 Photoshop) comptés |
| PNG | Bloc `IHDR` ; blocs `eXIf`, `tEXt`, `zTXt`, `iTXt` comptés |
| WebP | Premier bloc `VP8X`, `"VP8 "` ou `VP8L` ; blocs `EXIF` et `"XMP "` comptés |

Données de référence : les deux tables de l'annexe K de T.81, recopiées dans le code du module.

## Sorties

| Nom | Valeur |
| --- | --- |
| `image.metadonnees` | Nombre de blocs de métadonnées ; observé seulement si le parcours du conteneur est allé à son terme |
| `image.trame` | Bloc qui porte les dimensions : `SOF0` à `SOF15`, `IHDR`, `VP8X`, `VP8`, `VP8L` |
| `image.largeur` | Largeur, en pixels (`px`) |
| `image.hauteur` | Hauteur, en pixels ; absente d'un JPEG dont le SOF la laisse à 0 (donnée par un segment DNL, non lu) |
| `image.jpeg.tables` | Nombre de tables de quantification définies (JPEG) |
| `image.jpeg.qualite_ijg` | Qualité libjpeg de 1 à 100, si les tables sont celles de libjpeg (JPEG) |

## Données identifiantes

Aucune.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien : un appareil peut employer les tables de libjpeg et des dimensions quelconques |
| Transformation banale (recompression, redimensionnement) | Un profil, sans mesure : JPEG sans métadonnées à un côté long que des plateformes imposent, ou encodé aux tables de libjpeg |
| Retouche | Rien |
| Génération | Rien : un générateur peut écrire un JPEG sans métadonnées, à ces tailles et à ces tables |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas une transformation d'un premier encodage par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent un profil, en indice faible vers la transformation ([ADR-0155](../decisions/ADR-0155-nature-d-un-indice-de-transfert.md)).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles vers la transformation, fondés sur la lecture de la structure (T24, [ADR-0153](../decisions/ADR-0153-indices-de-transfert-retenus.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-IMAGE-001` JPEG sans métadonnées au côté long d'une messagerie, en paysage | `image.metadonnees`, `image.jpeg.tables`, `image.largeur`, `image.hauteur` | aucun bloc ; JPEG ; largeur parmi 960, 1 080, 1 280, 1 600, 2 048, 2 560 ; largeur > hauteur |
| `R-IMAGE-002` JPEG sans métadonnées au côté long d'une messagerie, en portrait | mêmes | aucun bloc ; JPEG ; hauteur parmi la même liste ; hauteur > largeur |
| `R-IMAGE-003` JPEG sans métadonnées au côté d'une messagerie, carré | mêmes | aucun bloc ; JPEG ; largeur parmi la même liste ; largeur = hauteur |
| `R-IMAGE-004` JPEG sans métadonnées encodé aux tables de libjpeg | `image.metadonnees`, `image.jpeg.qualite_ijg` | aucun bloc ; qualité libjpeg reconnue |

Les tailles viennent de deux études, citées dans chaque règle : Giudice et al. 2016 (arXiv:1610.06347, tableau III) et Bertini et al. 2020 (arXiv:2006.03903, tableau 1). Le résumé du rapport recommande d'obtenir l'original dès qu'un indice vers la transformation est relevé ([ADR-0156](../decisions/ADR-0156-recommandation-d-obtenir-l-original.md)).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_transfert.py`) ; la qualité libjpeg, sur des JPEG d'ImageMagick et de ffmpeg (`tests/test_transfert.py`, ignoré si `magick` ou `ffmpeg` manque).

## Limites connues

- Le HEIC n'est pas lu : ses dimensions sont dans une propriété `ispe` associée à l'élément principal, que le lecteur ne suit pas ([ADR-0154](../decisions/ADR-0154-module-image.md)).
- Seul le premier en-tête d'image est lu : un JPEG hiérarchique (plusieurs SOF) ou un WebP animé (trames dans `ANMF`) donnent les dimensions de la toile ou de la première trame.
- Les tables d'un balayage postérieur au premier (DQT entre deux balayages d'un JPEG progressif) ne sont pas lues.
- Seules les tables de libjpeg sont reconnues, à l'identique : mozjpeg, les tables propres d'un appareil ou d'une plateforme, et les tables d'une autre bibliothèque ne donnent pas de qualité. La comparaison avec d'autres tables connues reste à T40 (F-30) ; la double compression à T41 (F-31).
- Un segment SOF, `IHDR` ou `VP8*` trop court, ou un `VP8L` sans signature, rendent l'analyse non menée (format partiel) ; un DQT de précision ou d'identifiant invalide aussi, les tables lues jusque-là restant observées.

## Sécurité

- Aucune décompression ; aucune lecture au-delà des blocs relevés par le parcours, chacun d'au plus 16 Mio.
- Chaque segment ou bloc parcouru compte un objet (ADR-0078), comme pour les modules de métadonnées.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-14 | 0.1.0 | Création (T24, ADR-0153 à ADR-0157) |
