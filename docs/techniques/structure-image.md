# Fiche technique — Structure d'une image

- **Module** : `image` (version 0.3.0)
- **Tâche** : T24, T40 et son complément
- **Exigences** : F-06, F-30
- **Formats** : `jpeg`, `png`, `webp`
- **Directions permises** : `transformation`, `authenticite`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Quelles dimensions l'image a-t-elle réellement, combien de blocs de métadonnées porte-t-elle, et de quel encodeur connu viennent les tables de quantification d'un JPEG (libjpeg, mozjpeg, ffmpeg ; Photoshop et appareils relevés, par le catalogue) ?

## Principe

Le module reprend le parcours du conteneur des modules de métadonnées ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)), qui relève aussi, depuis T24, les blocs de structure d'une image ([ADR-0154](../decisions/ADR-0154-module-image.md)) : segments SOF et DQT d'un JPEG jusqu'au premier SOS (T.81, annexe B), bloc `IHDR` d'un PNG (PNG, 3e édition), blocs `VP8X`, `"VP8 "` et `VP8L` d'un WebP (RFC 9649). Aucune donnée d'image n'est décodée.

- **Dimensions** : celles de l'en-tête de l'image, pas celles que déclare l'EXIF (`PixelXDimension`, lues par le module `exif`). Premier bloc de structure trouvé : SOF (hauteur, largeur), `IHDR` (largeur, hauteur), `VP8X` (toile, 24 bits plus un), `VP8L` (14 bits plus un), `"VP8 "` (14 bits d'une trame clé, RFC 6386, 9.1).
- **Blocs de métadonnées** : ceux que lisent les modules du projet, EXIF, XMP, XMP étendu, ressources Photoshop (IPTC), blocs texte PNG ; le profil de couleur ICC, le segment JFIF et les commentaires JPEG (COM) ne sont pas des métadonnées pour ce compte.
- **Tables de quantification** (JPEG) : chaque table définie avant le premier balayage, la dernière définition d'un identifiant l'emportant (T.81, B.2.4.1). La qualité libjpeg est reconnue si la table 0 est exactement la table de luminance de l'annexe K (tableau K.1) mise à l'échelle par libjpeg à une qualité de 1 à 100 (`jpeg_quality_scaling` et `jpeg_add_quant_table` de `jcparam.c` : facteur 5 000 / q sous 50, 200 − 2q au-delà, arrondi, borné à 1 et à 255 pour une table de huit bits, à 32 767 pour une table de seize bits), et la table 1, s'il y en a une, la table de chrominance (K.2) à la même qualité ; aucune autre table. Chaque qualité donne une table de luminance différente (vérifié par les tests) : la qualité lue est unique.
- **Tables connues de T40** ([ADR-0180](../decisions/ADR-0180-tables-connues-de-t40.md), [ADR-0183](../decisions/ADR-0183-observations-des-tables-connues.md)) : les tables sont comparées, à l'identique et dans cet ordre, à celles de quatre réglages d'encodeurs ; le premier reconnu est seul observé.
  1. libjpeg à une même qualité (ci-dessus).
  2. libjpeg à deux qualités : table 0 de luminance à une qualité, table 1 de chrominance à une autre (`cjpeg -quality 90,70`, `q_scale_factor` de l'interface de libjpeg 7 et suivantes ; `rdswitch.c` et `jcparam.c` de libjpeg-turbo). En huit bits, les qualités 1 à 3 de la chrominance donnent la même table (toutes ses valeurs à 255) : cette table ne donne pas de seconde qualité.
  3. mozjpeg, jeux 2 à 8 de `jcparam.c` (mozjpeg 4.1.1, tables identiques sur la branche principale lue le 2026-11-14), mis à l'échelle comme libjpeg, la luminance et la chrominance du même jeu à la même qualité ; le jeu 3 (table de N. Robidoux) est celui du profil par défaut de mozjpeg. Le jeu 0 est l'annexe K, déjà reconnue comme libjpeg ; le jeu 1, plat, n'est pas reconnu, plusieurs qualités y donnant la même table. Une table qu'écrivent deux couples (jeu, qualité), ou que libjpeg écrit aussi, n'est pas attribuée à mozjpeg : seules les tables dégénérées, toutes à 1 (qualité 100) ou toutes à 255, sont dans ce cas (vérifié par les tests).
  4. ffmpeg, encodeur MJPEG : coefficient continu à 8, les autres à `(m × qscale) >> 3` bornés à 255, où m est la matrice intra par défaut de MPEG-1 (`encode_picture` de `mpegvideo_enc.c`, `ff_mpeg1_default_intra_matrix` de `mpeg12data.c`, FFmpeg 7.1), pour un qscale de 1 à 31 ; une table, ou deux tables égales, de huit bits.
- **Empreinte des tables** ([ADR-0181](../decisions/ADR-0181-empreinte-des-tables.md)) : SHA-256, en hexadécimal minuscule, de l'écriture canonique des tables en vigueur : une ligne par table, dans l'ordre des identifiants, `<identifiant>:<v1>,<v2>,…,<v64>`, valeurs en décimal dans l'ordre du segment DQT (zigzag), lignes séparées par un saut de ligne (LF), sans saut final, en ASCII ; la précision (huit ou seize bits) n'en fait pas partie. Elle est observée pour toutes tables, reconnues ou non : une règle du catalogue peut nommer des tables fixes par leur empreinte (test `parmi`), sans nouvelle version de l'outil (F-26).
- **Tables relevées** (complément de T40, [ADR-0191](../decisions/ADR-0191-constats-des-tables-relevees.md) à [ADR-0196](../decisions/ADR-0196-versions-du-complement-de-t40.md)) : les tables de Photoshop et d'appareils ne se calculent pas ; elles ont été relevées sur des originaux de Wikimedia Commons et sont nommées par le catalogue, par leur empreinte, sans code dans le module. Relevé : 37 006 JPEG parcourus par l'API de Commons (2008 à 2025), 2 646 en-têtes lus, 37 empreintes retenues sur 1 093 fichiers sources, chacune portée par au moins 3 fichiers de 2 comptes ([ADR-0193](../decisions/ADR-0193-releve-des-tables.md)). Scripts, tables en clair, fichiers sources et licences : [`banc/releves/tables-T40c/`](../../banc/releves/tables-T40c/README.md).
  - **Photoshop** ([ADR-0195](../decisions/ADR-0195-tables-de-photoshop.md)) : niveau de qualité (0 à 12) lu dans la ressource 0x0406 de son bloc APP13 (valeur brute signée + 4). À chaque niveau, Photoshop écrit plusieurs jeux, dans toutes ses versions de 7.0 à CC : un pour les images dont le côté long fait au plus 1 296 pixels, un autre au-delà de 1 305 pixels (seuil observé, non documenté par Adobe ; ni le nombre de pixels, ni la largeur, ni le côté court ne séparent les jeux), et un jeu d'une seule table pour les images en niveaux de gris. Aucune empreinte n'est commune à deux niveaux. Niveaux retenus : 3 et 5 à 12 (21 empreintes) ; 0, 1, 2 et 4 n'ont pas assez de fichiers. Photoshop Elements et Lightroom écrivent les mêmes tables.
  - **Appareils** ([ADR-0194](../decisions/ADR-0194-tables-d-appareils.md)) : les tables sont communes à des familles entières (un même jeu sur des dizaines de compacts Canon). Retenue : une seule marque, jamais sur un fichier de Photoshop, au moins 3 fichiers de 2 comptes ; 16 empreintes, Apple (2), Canon (8), Kodak (1), Olympus (1), Panasonic (3), Sony (1). Les modèles qui semblent calculer leurs tables pour chaque image (au moins 4 fichiers lus, presque tous à des tables différentes) sont exclus : Casio EX-Z50 ; Canon EOS 30D et 350D ; Fujifilm FinePix S5500, S5600, S5700 ; Nikon D40, D50, D70, Coolpix L10, P50, S200, E2500 ; Olympus C770UZ, E-410, FE100, FE320, SP510UZ, u40D ; Panasonic DMC-FX01, FX100, FZ8, LX3, TZ10 ; Samsung ES55 et Digimax S600 ; Sony DSC-HX1 et S750.

## Entrées

| Format | Emplacement lu |
| --- | --- |
| JPEG | Premier segment SOF0 à SOF15 (hors DHT, JPG, DAC) ; segments DQT avant le premier SOS ; segments des métadonnées (APP1 EXIF et XMP, APP13 Photoshop) comptés |
| PNG | Bloc `IHDR` ; blocs `eXIf`, `tEXt`, `zTXt`, `iTXt` comptés |
| WebP | Premier bloc `VP8X`, `"VP8 "` ou `VP8L` ; blocs `EXIF` et `"XMP "` comptés |

Données de référence, recopiées dans le code du module : les deux tables de l'annexe K de T.81 ; les tables de luminance et de chrominance des jeux 2 à 8 de mozjpeg 4.1.1 (`std_luminance_quant_tbl`, `std_chrominance_quant_tbl` de `jcparam.c`, licence IJG et BSD) ; la matrice intra par défaut de MPEG-1 de FFmpeg 7.1 (`mpeg12data.c`). Les littéraux de mozjpeg ont été produits par un script qui lit `jcparam.c`, pas recopiés à la main. Les tables relevées ne sont pas dans le code : leurs empreintes sont dans les règles `R-IMAGE-008` à `R-IMAGE-022`, leurs valeurs dans `banc/releves/tables-T40c/tables.toml`.

## Sorties

| Nom | Valeur |
| --- | --- |
| `image.metadonnees` | Nombre de blocs de métadonnées ; observé seulement si le parcours du conteneur est allé à son terme |
| `image.trame` | Bloc qui porte les dimensions : `SOF0` à `SOF15`, `IHDR`, `VP8X`, `VP8`, `VP8L` |
| `image.largeur` | Largeur, en pixels (`px`) |
| `image.hauteur` | Hauteur, en pixels ; absente d'un JPEG dont le SOF la laisse à 0 (donnée par un segment DNL, non lu) |
| `image.jpeg.tables` | Nombre de tables de quantification définies (JPEG) |
| `image.jpeg.empreinte_tables` | Empreinte SHA-256 des tables, en hexadécimal (JPEG) |
| `image.jpeg.qualite_ijg` | Qualité libjpeg de 1 à 100, si les tables sont celles de libjpeg à une même qualité (JPEG) |
| `image.jpeg.qualite_ijg_luminance`, `image.jpeg.qualite_ijg_chrominance` | Qualités libjpeg de la luminance et de la chrominance, si les tables sont celles de libjpeg à deux qualités (JPEG) |
| `image.jpeg.jeu_mozjpeg`, `image.jpeg.qualite_mozjpeg` | Jeu (2 à 8) et qualité (1 à 100), si les tables sont celles de mozjpeg (JPEG) |
| `image.jpeg.qscale_ffmpeg` | qscale de 1 à 31, si les tables sont celles de l'encodeur MJPEG de ffmpeg (JPEG) |

## Données identifiantes

Aucune.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Un profil : les tables d'un appareil relevé disent que la dernière compression est celle d'un appareil de cette marque (indice vers l'authenticité) ; un appareil peut aussi employer les tables de libjpeg, ou ne pas être reconnu |
| Transformation banale (recompression, redimensionnement) | Un profil, sans mesure : JPEG sans métadonnées à un côté long que des plateformes imposent, ou encodé aux tables d'un encodeur connu (libjpeg, mozjpeg, ffmpeg) ; JPEG aux tables de Photoshop |
| Retouche | Rien d'établi : des tables de Photoshop disent un enregistrement par Photoshop, pas une retouche |
| Génération | Rien : un générateur peut écrire un JPEG sans métadonnées, à ces tailles et à ces tables |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas une transformation d'un premier encodage par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent un profil, en indice vers la transformation ([ADR-0155](../decisions/ADR-0155-nature-d-un-indice-de-transfert.md)), ou vers l'authenticité pour les tables d'appareils ([ADR-0191](../decisions/ADR-0191-constats-des-tables-relevees.md)).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices fondés sur la lecture de la structure, chacun au niveau que permet sa mesure (« Taux d'erreur »), vers la transformation sauf les tables d'appareils, vers l'authenticité (T24, [ADR-0153](../decisions/ADR-0153-indices-de-transfert-retenus.md) ; T40, [ADR-0182](../decisions/ADR-0182-regles-des-tables-connues.md) ; complément de T40, [ADR-0191](../decisions/ADR-0191-constats-des-tables-relevees.md), [ADR-0192](../decisions/ADR-0192-metadonnees-non-exigees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-IMAGE-001` JPEG sans métadonnées au côté long d'une messagerie, en paysage | `image.metadonnees`, `image.jpeg.tables`, `image.largeur`, `image.hauteur` | aucun bloc ; JPEG ; largeur parmi 960, 1 080, 1 280, 1 600, 2 048, 2 560 ; largeur > hauteur |
| `R-IMAGE-002` JPEG sans métadonnées au côté long d'une messagerie, en portrait | mêmes | aucun bloc ; JPEG ; hauteur parmi la même liste ; hauteur > largeur |
| `R-IMAGE-003` JPEG sans métadonnées au côté d'une messagerie, carré | mêmes | aucun bloc ; JPEG ; largeur parmi la même liste ; largeur = hauteur |
| `R-IMAGE-004` JPEG sans métadonnées encodé aux tables de libjpeg | `image.metadonnees`, `image.jpeg.qualite_ijg` | aucun bloc ; qualité libjpeg reconnue |
| `R-IMAGE-005` JPEG sans métadonnées encodé aux tables de libjpeg à deux qualités | `image.metadonnees`, `image.jpeg.qualite_ijg_luminance`, `image.jpeg.qualite_ijg_chrominance` | aucun bloc ; deux qualités libjpeg reconnues |
| `R-IMAGE-006` JPEG sans métadonnées encodé aux tables de mozjpeg | `image.metadonnees`, `image.jpeg.jeu_mozjpeg`, `image.jpeg.qualite_mozjpeg` | aucun bloc ; jeu et qualité de mozjpeg reconnus |
| `R-IMAGE-007` JPEG sans métadonnées encodé par ffmpeg | `image.metadonnees`, `image.jpeg.qscale_ffmpeg` | aucun bloc ; qscale de ffmpeg reconnu |
| `R-IMAGE-008` à `R-IMAGE-016` JPEG aux tables de quantification d'Adobe Photoshop, qualité 3, 5, 6, 7, 8, 9, 10, 11, 12 | `image.jpeg.empreinte_tables` | empreinte parmi celles du niveau (1 à 4) ; métadonnées quelconques |
| `R-IMAGE-017` à `R-IMAGE-022` JPEG aux tables de quantification d'appareils Apple, Canon, Kodak, Olympus, Panasonic, Sony | `image.jpeg.empreinte_tables` | empreinte parmi celles de la marque (1 à 8) ; métadonnées quelconques ; direction authenticité |

Les tailles viennent de deux études, citées dans chaque règle : Giudice et al. 2016 (arXiv:1610.06347, tableau III) et Bertini et al. 2020 (arXiv:2006.03903, tableau 1). Le résumé du rapport recommande d'obtenir l'original dès qu'un indice vers la transformation est relevé ([ADR-0156](../decisions/ADR-0156-recommandation-d-obtenir-l-original.md)).

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `image` 0.3.0, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 1559 | 1/826 : 0,1 % [0,0 % ; 0,7 %] | 0/825 : 0,0 % [0,0 % ; 0,5 %] | — | 0 |
| Générés | 424 | 104 | 0/320 : 0,0 % [0,0 % ; 1,2 %] | — | 320/320 : 100,0 % [98,8 % ; 100,0 %] | 0 |
| Transformés | 1294 | 518 | 0/776 : 0,0 % [0,0 % ; 0,5 %] | 0/472 : 0,0 % [0,0 % ; 0,8 %] | 304/304 : 100,0 % [98,8 % ; 100,0 %] | 0 |
| Retouchés | 273 | 120 | 0/153 : 0,0 % [0,0 % ; 2,4 %] | — | 153/153 : 100,0 % [97,6 % ; 100,0 %] | 0 |
| Malformés | 91 | 39 | 28/52 : 53,8 % [40,5 % ; 66,7 %] | 0/19 : 0,0 % [0,0 % ; 16,8 %] | 4/4 : 100,0 % [51,0 % ; 100,0 %] | 0 |

| Règle | Catégorie | Direction | Faux positifs | Niveau permis | Niveau |
| --- | --- | --- | --- | --- | --- |
| R-IMAGE-001 v2 | indice | transformation | 11/825 : 1,3 % [0,7 % ; 2,4 %] | modere | modere |
| R-IMAGE-002 v2 | indice | transformation | 2/825 : 0,2 % [0,1 % ; 0,9 %] | fort | fort |
| R-IMAGE-003 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-004 v3 | indice | transformation | 97/825 : 11,8 % [9,7 % ; 14,1 %] | faible | faible |
| R-IMAGE-005 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-006 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-007 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-008 v2 | indice | transformation | 1/825 : 0,1 % [0,0 % ; 0,7 %] | fort | fort |
| R-IMAGE-009 v2 | indice | transformation | 4/825 : 0,5 % [0,2 % ; 1,2 %] | modere | modere |
| R-IMAGE-010 v2 | indice | transformation | 4/825 : 0,5 % [0,2 % ; 1,2 %] | modere | modere |
| R-IMAGE-011 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-012 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-013 v2 | indice | transformation | 1/825 : 0,1 % [0,0 % ; 0,7 %] | fort | fort |
| R-IMAGE-014 v2 | indice | transformation | 4/825 : 0,5 % [0,2 % ; 1,2 %] | modere | modere |
| R-IMAGE-015 v2 | indice | transformation | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort | fort |
| R-IMAGE-016 v2 | indice | transformation | 46/825 : 5,6 % [4,2 % ; 7,4 %] | faible | faible |
| R-IMAGE-017 v2 | indice | authenticite | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort | fort |
| R-IMAGE-018 v2 | indice | authenticite | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort | fort |
| R-IMAGE-019 v2 | indice | authenticite | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort | fort |
| R-IMAGE-020 v2 | indice | authenticite | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort | fort |
| R-IMAGE-021 v2 | indice | authenticite | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort | fort |
| R-IMAGE-022 v2 | indice | authenticite | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort | fort |

<!-- Fin des taux mesurés. -->

Le niveau de chaque indice est celui que permet son taux de faux positifs, mesuré ci-dessus (ADR-0018, [ADR-0278](../decisions/ADR-0278-evaluation-et-niveau-des-indices-au-catalogue.md)). Le déclenchement des règles est vérifié sur des échantillons construits (`tests/test_transfert.py`) ; la qualité libjpeg, sur des JPEG d'ImageMagick et de ffmpeg (`tests/test_transfert.py`, ignoré si `magick` ou `ffmpeg` manque). Tables connues de T40 (`tests/test_tables_connues.py`) : chaque couple (jeu, qualité) de mozjpeg, chaque qscale de ffmpeg et chaque qualité de chrominance reconnus sur des tables construites ; oracles cjpeg de libjpeg-turbo (une et deux qualités, huit et seize bits), ffmpeg (qscale 2, 5, 31) et cjpeg de mozjpeg (jeux 2, 3, 6), chacun ignoré si l'outil manque. Le cjpeg de mozjpeg n'était pas installé sur le poste de T40 : les tables de mozjpeg n'y ont été vérifiées que contre le texte de `jcparam.c`. Tables relevées (`tests/test_tables_relevees.py`) : l'empreinte de chacune est recalculée à partir de ses valeurs en clair, chaque règle est déclenchée par un JPEG construit avec ses tables, avec et sans EXIF, et chaque fichier source est compté et cité avec une licence libre. Sur le relevé, aucune empreinte de Photoshop n'est commune à deux niveaux, et aucune empreinte d'appareil retenue n'est vue sur un fichier de Photoshop ni sur une autre marque ; les collisions avec d'autres logiciels sont nommées dans chaque règle (GIMP, Picasa, galerie et visionneuse de photos de Windows, Photoshop Album, Photoshop Elements, Lightroom).

## Limites connues

- Le HEIC n'est pas lu : ses dimensions sont dans une propriété `ispe` associée à l'élément principal, que le lecteur ne suit pas ([ADR-0154](../decisions/ADR-0154-module-image.md)).
- Seul le premier en-tête d'image est lu : un JPEG hiérarchique (plusieurs SOF) ou un WebP animé (trames dans `ANMF`) donnent les dimensions de la toile ou de la première trame.
- Les tables d'un balayage postérieur au premier (DQT entre deux balayages d'un JPEG progressif) ne sont pas lues.
- Seules les tables de libjpeg, de mozjpeg (jeux 2 à 8) et de l'encodeur MJPEG de ffmpeg sont reconnues, à l'identique, aux qualités entières de 1 à 100 et aux qscale de 1 à 31 : une qualité fractionnaire de mozjpeg, des qualités séparées dans mozjpeg, un qscale au-delà de 31, une matrice ou une précision du continu choisies dans ffmpeg, les tables d'une plateforme ne donnent aucun encodeur. Les tables de Photoshop et d'appareils relevées sont nommées par le catalogue, par leur empreinte : un niveau de Photoshop rare (0, 1, 2, 4), un enregistrement de Photoshop sans ressource 0x0406, un appareil rare ou qui calcule ses tables pour chaque image ne sont pas reconnus ; des tables d'appareil se recopient (rotation sans perte, GIMP avec la qualité de l'original), et la règle ne compare pas l'appareil reconnu à celui que déclare l'EXIF ; la double compression est mesurée par le module `doublejpeg` (T41, fiche [`double-compression-jpeg`](double-compression-jpeg.md)).
- Une table dégénérée, toute à 1 ou toute à 255, est écrite par plusieurs encodeurs ; elle est attribuée à libjpeg, premier essayé (ADR-0183).
- L'empreinte ne distingue pas deux tables égales écrites à deux précisions ; elle change si l'ordre des identifiants ou une seule valeur changent.
- Un segment SOF, `IHDR` ou `VP8*` trop court, ou un `VP8L` sans signature, rendent l'analyse non menée (format partiel) ; un DQT de précision ou d'identifiant invalide aussi, les tables lues jusque-là restant observées.

## Sécurité

- Aucune décompression ; aucune lecture au-delà des blocs relevés par le parcours, chacun d'au plus 16 Mio.
- Chaque segment ou bloc parcouru compte un objet (ADR-0078), comme pour les modules de métadonnées.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-14 | 0.1.0 | Création (T24, ADR-0153 à ADR-0157) |
| 2026-11-14 | 0.2.0 | Tables connues : libjpeg à deux qualités, mozjpeg, ffmpeg ; empreinte des tables ; règles `R-IMAGE-005` à `R-IMAGE-007` (T40, ADR-0180 à ADR-0184) |
| 2026-11-16 | 0.3.0 | Direction `authenticite` ; tables relevées de Photoshop et d'appareils, règles `R-IMAGE-008` à `R-IMAGE-022` au catalogue 0.9.0 (complément de T40, ADR-0191 à ADR-0196) |
