# Fiche technique — Filigrane dwtDct d'invisible-watermark

- **Module** : `dwtdct` (version 0.1.0)
- **Tâche** : T32
- **Exigences** : F-24
- **Formats** : `jpeg`, `png`, `webp`, `heic`
- **Directions permises** : `origine_ia`
- **Règles** : aucune
- **Bibliothèques** : numpy

## Question

L'image porte-t-elle le message invisible que posent les codes de référence de Stable Diffusion 1, de SDXL ou de FLUX.1, par la méthode dwtDct de la bibliothèque invisible-watermark ?

## Principe

Les scripts de référence de ces générateurs passent chaque image produite à invisible-watermark 0.2.0 (ShieldMnt, licence MIT), qui y cache un message fixe et public ([inventaire des marquages](../catalogue/inventaire-des-marquages.md), §3) :

| Générateur | Code | Message | Image passée à la bibliothèque |
| --- | --- | --- | --- |
| Stable Diffusion 1 | CompVis, `scripts/txt2img.py` | octets de « StableDiffusionV1 », 136 bits | entiers, BVR ; enregistrée en PNG |
| SDXL | Stability-AI, `sgm/inference/helpers.py` ; diffusers, `stable_diffusion_xl/watermark.py` | `0xB3EC907BB19E`, 48 bits | flottants de 0 à 255, BVR (RVB dans diffusers du 2023-07-06 au 2024-04-26) ; enregistrée en PNG |
| FLUX.1 | Black Forest Labs, `src/flux/util.py` | `0x2AFE879CF52E` sans ses deux zéros de tête, 46 bits | flottants de 0 à 255, BVR ; enregistrée en JPEG de qualité 95, sans sous-échantillonnage |

La méthode (`imwatermark/maxDct.py`) :

1. convertit l'image en YUV comme OpenCV (`COLOR_BGR2YUV`) et ne garde que la composante U (bleu moins luminance) ;
2. la recadre au multiple de 4 pixels, en prend la bande basse fréquence de Haar à un niveau (la somme de chaque carré de 2 × 2 pixels, divisée par 2) et la découpe en blocs de 4 × 4 valeurs ; le bit n° k du message va dans les blocs n° k, k + n, k + 2n… dans l'ordre de la trame ;
3. dans chaque bloc, déplace la plus grande valeur absolue hors de la première au quart de l'échelle 36 pour un 0, aux trois quarts pour un 1. La méthode n'emploie aucune DCT, malgré son nom ([ERR-0011](../errata/ERR-0011-dwtdct-sans-dct.md)).

La lecture de l'outil ([ADR-0203](../decisions/ADR-0203-methode-de-lecture.md)) reprend ces étapes, avec deux écarts à celle de la bibliothèque :

- **Domaine** : chaque message est lu là où son code le pose : U sur huit bits pour Stable Diffusion 1, U en flottant pour SDXL et FLUX.1 (centrée sur 0,5 au lieu de 128, et signée) ; SDXL l'est aussi le rouge et le bleu échangés, et la meilleure des deux lectures est gardée.
- **Décision** : le score d'un bit est la part de ses blocs dont la valeur, modulo 36, dépasse 18 ; les k bits aux scores les plus élevés valent 1, k étant le nombre de 1 du message (68, 27 et 28). La bibliothèque compare chaque score à un demi. Des scores égaux de part et d'autre du rang k laissent leurs bits indéterminés, comptés comme non concordants.

Le module compte les bits lus qui concordent avec chaque message. Sur les échantillons des tests, marqués par la bibliothèque elle-même (`tests/donnees/dwtdct/generer.py`, image de 256 × 256 pixels) :

| Échantillon | Bits concordants, outil | Bits concordants, décodeur de la bibliothèque |
| --- | --- | --- |
| Stable Diffusion 1, PNG | 136 sur 136 | 114 |
| Stable Diffusion 1, JPEG progressif 4:2:2 (cjpeg, qualité 95) | 132 | 114 |
| SDXL, PNG | 48 sur 48 | 39 |
| SDXL, PNG, rouge et bleu échangés | 48 | 42 (lu lui aussi les couleurs échangées) |
| SDXL, JPEG 4:2:0 de qualité 95 | 48 | 37 |
| FLUX.1, JPEG de qualité 95 en 4:4:4 | 46 sur 46 | 39 |
| Image non marquée, PNG | 56, 30 et 25 | 65 (message de Stable Diffusion 1) |

Les nombres de l'outil ne se comparent donc pas aux seuils du détecteur de Stability (`scripts/demo/detect.py`, sur 48 bits : plus de 33, « probablement marquée »).

Pixels : le décodage du projet ([ADR-0202](../decisions/ADR-0202-decodage-des-pixels.md)), en Python pur pour la lecture du fichier, numpy pour le calcul ; JPEG par les coefficients de toutes ses composantes (lecteur de T41), IDCT exacte en entiers, chrominance répétée sans lissage, conversion par les tables de libjpeg ; PNG par un lecteur du projet. Tout le calcul est en entiers exacts : U sur huit bits par la formule en virgule fixe d'OpenCV (égale à OpenCV 5.0.0 sur les 2^24 couleurs), U en flottant multipliée par 10^6. Le résultat est le même sur toutes les machines (NF-06).

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| JPEG | Segments jusqu'à EOI, APP0 (JFIF) et APP14 (Adobe) compris ; données entropiques de toutes les composantes jusqu'à la dernière ligne de MCU de la région. Séquentiel et progressif, Huffman, huit bits ; YCbCr, ou RVB selon la règle de libjpeg ; niveaux de gris reconnus |
| PNG | Blocs IHDR, PLTE, IDAT, IEND ; données décompressées jusqu'à la dernière ligne de la région. Types 2, 3 et 6, huit ou seize bits (palette : 1 à 8 bits) ; types 0 et 4 reconnus sans décompression |
| WebP, HEIC | Rien : pixels non décodés, analyse non menée (format partiel) |

Région ([ADR-0205](../decisions/ADR-0205-etendue-de-la-lecture.md)) : l'image entière jusqu'à 4 194 304 pixels (2 048 × 2 048) ; au-delà, les lignes du haut de l'image jusqu'à ce budget (de MCU entières pour un JPEG). Une image de moins de 65 536 pixels n'est pas lue, comme dans la bibliothèque.

Données de référence, recopiées dans le code du module : les trois messages, lus dans les codes cités ; les coefficients d'OpenCV (huit bits en virgule fixe sur 14 bits, flottants) ; les tables de conversion de libjpeg.

## Sorties

| Nom | Valeur |
| --- | --- |
| `dwtdct.pixels_image` | Pixels de l'image (largeur × hauteur), en pixels |
| `dwtdct.chrominance` | `false` pour une image en niveaux de gris, qui n'est pas lue plus avant |
| `dwtdct.blocs` | Blocs de 4 × 4 de la bande basse de U lus ; localisation : image entière ou haut de l'image, avec la zone lue |
| `dwtdct.blocs_image` | Blocs de l'image entière |
| `dwtdct.concordants_sd1` | Bits concordants avec le message de Stable Diffusion 1, sur 136 |
| `dwtdct.concordants_sdxl` | Bits concordants avec le message de SDXL, sur 48, meilleur des deux ordres des couleurs |
| `dwtdct.concordants_flux` | Bits concordants avec le message de FLUX.1, sur 46 |
| `dwtdct.indetermines_<message>` | Bits indéterminés (scores égaux autour du rang k), s'il y en a |
| `dwtdct.rouge_et_bleu_echanges_sdxl` | `true` si le rouge et le bleu échangés lisent strictement plus de bits du message de SDXL |

Une image qui a moins de blocs que de bits d'un message (moins de 8 lignes de pixels, par exemple) n'a pas d'observation pour ce message. Une analyse non menée de ce module ne rend pas le contrôle avant publication incomplet : il ne lit aucune métadonnée.

## Données identifiantes

Aucune.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien : un appareil ne pose pas ce message ; une photographie n'atteint pas les seuils (relevé de T32, ci-dessous) |
| Transformation banale (recompression, redimensionnement) | Une transformation n'écrit pas le message : une compression JPEG en 4:4:4 le conserve, en 4:2:0 l'affaiblit, un redimensionnement, une rotation ou un recadrage d'un seul pixel en haut ou à gauche l'effacent. Les vignettes de Commons, recompressées et réduites, n'atteignent pas les seuils |
| Retouche | Rien de propre : une retouche locale d'une image marquée laisse le reste du message lisible ; une retouche qui recadre l'efface |
| Génération | Un message retrouvé dit que l'image est passée par l'un de ces codes de référence, ou que quelqu'un y a posé le même message : il est public et fixe. Son absence ne dit rien : la plupart des interfaces ne le posent pas, et les transformations l'effacent |

Lecture d'ADR-0022 ([ADR-0206](../decisions/ADR-0206-constat-et-versions-de-t32.md), comme ADR-0142 pour une déclaration) : la technique ne reconnaît pas une image générée à son signal, elle lit un marquage que seuls des codes de génération posent ; la mesure sur la partie évaluation du corpus reste à faire (T100), et le niveau reste « faible ».

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([ADR-0204](../decisions/ADR-0204-seuils-et-releve.md), [ADR-0206](../decisions/ADR-0206-constat-et-versions-de-t32.md)) :

| Règle | Observation | Seuil | Probabilité pour une image non marquée |
| --- | --- | --- | --- |
| `R-DWTDCT-001` Filigrane dwtDct de Stable Diffusion 1 | `dwtdct.concordants_sd1` | au moins 98 sur 136 | 2,2 × 10^-7 |
| `R-DWTDCT-002` Filigrane dwtDct de SDXL | `dwtdct.concordants_sdxl` | au moins 42 sur 48 | au plus 3,6 × 10^-7 (deux ordres) |
| `R-DWTDCT-003` Filigrane dwtDct de FLUX.1 | `dwtdct.concordants_flux` | au moins 39 sur 46 | 9,7 × 10^-7 |

Indices faibles vers l'origine IA, fondés sur une mesure. La probabilité est celle de la loi hypergéométrique, sous l'hypothèse qu'une image non marquée ordonne ses scores sans rapport avec le message ([ADR-0204](../decisions/ADR-0204-seuils-et-releve.md)).

## Taux d'erreur

Non mesuré sur le corpus de référence (T100) : seuils fixés par la loi hypergéométrique ([ADR-0204](../decisions/ADR-0204-seuils-et-releve.md)), vérifiés sur un relevé de Wikimedia Commons fait le 2026-11-16 (`banc/releves/dwtdct-T32/`) :

| Fichiers | Lus | Constats | Plus grand nombre de bits concordants (SD 1 / SDXL / FLUX.1) |
| --- | --- | --- | --- |
| Authentiques, versés avant le 2022-08-22 : 1 000 JPEG et 224 PNG, rendus de 960 pixels | 1 141 (83 en niveaux de gris) | aucun | 82 / 34 / 34, pour des seuils de 98 / 42 / 39 |
| Déclarés générés par Stable Diffusion, SDXL ou FLUX.1 : 356 originaux | 354 | 1 (`R-DWTDCT-002`) | 84 / 48 / 33 |

Sur les authentiques, les queues observées restent sous la loi (ou sous sa borne pour les deux lectures de SDXL) : l'hypothèse n'est pas contredite là où le relevé peut la voir. Aucun faux positif sur 1 141 images : borne supérieure de Wilson à 95 % de 0,34 % par règle ; le relevé ne peut pas vérifier la probabilité calculée, de l'ordre de 10^-7, qui reste une hypothèse.

Le seul fichier déclaré qui porte un message, un PNG de 1 024 × 1 024 versé le 2024-01-15, le porte en entier, le rouge et le bleu échangés : la marque du pipeline SDXL de diffusers de cette période. Les 353 autres n'en portent aucun au-dessus des seuils, sans que le relevé dise pourquoi : sur ces images, l'absence du message est la règle, et ne dit rien.

Sur les essais de T32 (38 photographies marquées par la bibliothèque, comme chaque code le fait) : toutes les images marquées enregistrées comme leur code les enregistre sont lues en entier ; après une compression JPEG en 4:2:0, la médiane des bits concordants de SDXL passe à 42 sur 48 en qualité 95, 36 en qualité 75 ; un recadrage d'un pixel ou une réduction à 0,9 fois l'efface (médiane de 22 à 26 bits sur 48).

## Limites connues

- **Message public** : n'importe qui peut poser ce message sur n'importe quelle image avec la bibliothèque ; le schéma n'est pas cryptographique. Le constat n'établit pas qui l'a posé (ADR-0021).
- **Absence** : la plupart des interfaces de ces modèles (et les services en ligne) ne posent pas ce message ; diffusers ne le pose que si invisible-watermark est installée.
- **Transformations** : un recadrage qui décale la grille, même d'un pixel en haut ou à gauche, un redimensionnement (0,9 fois suffit) ou une rotation l'effacent : la grille n'est pas recherchée. Une compression JPEG en 4:2:0 l'affaiblit : sur les essais de T32, la médiane passe à 42 bits sur 48 pour SDXL en qualité 95, 36 en qualité 75 ; en 4:4:4, même en qualité 75, il reste entier.
- **Images uniformes** : des couleurs très uniformes donnent des scores égaux ou corrélés ; les bits indéterminés comptent comme non concordants, ce qui protège des faux positifs mais peut cacher un message posé sur une image très lisse.
- **Autres usages de la bibliothèque** : un autre message, d'autres échelles, la méthode `dwtDctSvd` ou `rivaGan` ne sont pas lus.
- **Formats** : WebP et HEIC non lus ; JPEG CMYK ou YCCK, à codage arithmétique, sans perte, hiérarchique ou en douze bits, PNG entrelacé : analyse non menée, format partiel. Un PNG en seize bits est lu par son octet de poids fort.
- **Pixels** : l'IDCT de l'outil diffère de celle de libjpeg de quelques niveaux sur quelques pixels (au plus 3 sur les essais de T32, 0,04 en moyenne ; le test-oracle admet 4) ; sans effet mesuré sur la lecture.

## Sécurité

- Lecture du fichier en Python pur (lecteur JPEG de T41, lecteur PNG du projet) ; numpy calcule sur des tableaux déjà décodés ([ADR-0185](../decisions/ADR-0185-lecture-des-coefficients-dct.md), [ADR-0202](../decisions/ADR-0202-decodage-des-pixels.md)).
- Décompression PNG par zlib de la bibliothèque standard, au fil de la lecture, arrêtée aux lignes nécessaires, chaque morceau déclaré par `compter_decompression` (ADR-0078) : le module ne passe pas par `Contexte.decompresser`, qui décompresserait le flux entier.
- Limites : dimensions vérifiées avant tout décodage (`verifier_dimensions`) ; 4 194 304 pixels lus au plus ; pour un JPEG, 65 536 blocs de la première composante et 524 288 blocs décodés au plus, 64 balayages, 256 tables de Huffman ; chaque segment, bloc PNG et bloc JPEG décodé compte un objet.
- Aucune exécution, aucun réseau, aucune écriture.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-16 | 0.1.0 | Création (T32, ADR-0202 à ADR-0206) |
