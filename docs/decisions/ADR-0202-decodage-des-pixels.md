# ADR-0202 — Décodage des pixels : JPEG et PNG par le projet, chrominance répétée, WebP et HEIC non menés

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (formats) ; précisions de l'assistant, mesurées, dans les tableaux ci-dessous
- **Tâche** : T32
- **Exigences liées** : F-24, F-25, NF-06, ES-18, ES-19 ; menaces M-01, M-31 ; ADR-0043, ADR-0174, ADR-0185, ADR-0189

## Contexte

ADR-0174 demandait à T32 de choisir le décodage des pixels. Le filigrane dwtDct est posé dans la composante U d'une conversion en YUV (inventaire des marquages, §3) : il faut les trois couleurs de chaque pixel. Le décodeur du projet (T41, ADR-0185) ne rend que les coefficients de la première composante d'un JPEG. Les codes de référence enregistrent en PNG (Stable Diffusion 1, SDXL de generative-models et de diffusers) ou en JPEG de qualité 95 sans sous-échantillonnage (FLUX.1, `save_image` de `src/flux/util.py`) ; le marquage est inscrit au catalogue pour les JPEG, PNG, WebP et HEIC. Décoder un WebP demande VP8 ou VP8L, un HEIC le codage HEVC.

## Options envisagées

### Formats décodés (question posée à TheDarkMac)

- **A — JPEG et PNG** : les trois codes de référence tels qu'ils enregistrent ; WebP et HEIC restent non lus.
- **B — PNG d'abord, JPEG plus tard** : plus court (aucune chrominance à décoder), mais les sorties de FLUX.1, en JPEG, ne sont pas lues.
- **C — JPEG, PNG et WebP sans perte** : un décodeur VP8L de plus, pour un format que les codes de référence n'écrivent pas.

### Moyen de décoder

- **Décodeur du projet** : le décodage entropique de T41, étendu à toutes les composantes, et un lecteur PNG en Python pur ; numpy calcule sur des tableaux déjà décodés (ADR-0185).
- **Pillow** : une dépendance de plus, du C (libjpeg, libpng, zlib) directement exposé au fichier (M-01), et un suréchantillonnage de la chrominance que l'outil ne choisit pas.

### Suréchantillonnage de la chrominance d'un JPEG

- **Répétition** : chaque valeur de chrominance couvre les pixels de sa zone (`djpeg -nosmooth`).
- **Lissage de libjpeg** (`do_fancy_upsampling`, par défaut, ce que lit `cv2.imread`) : interpolation triangulaire.

### WebP et HEIC

- **Déclarés au manifeste, non menés** : le module les reçoit et dit qu'il ne les lit pas ; le marquage y est « non recherché, technique non menée ».
- **Retirés des formats du marquage** : le chargeur du catalogue exige qu'un module recherche son marquage dans tous ses formats ; le rapport d'un WebP ne citerait plus du tout le dwtDct.

## Décision

Option A, par le décodeur du projet : coefficients de toutes les composantes par le lecteur JPEG (paramètre `toutes`), chrominance répétée, conversion de couleurs par les tables de libjpeg ; lecteur PNG du projet ; WebP et HEIC déclarés au manifeste, non menés, format partiel. Précisions de l'assistant :

| Point | Choix | Raison |
| --- | --- | --- |
| Région d'un JPEG | Lignes de MCU entières, chaque composante sur les mêmes lignes de l'image | La chrominance d'une ligne de luminance est dans la même ligne de MCU |
| IDCT | Celle de T41, exacte en entiers (`_lecture/dct.py`) | Même calcul sur toutes les machines (ADR-0189) ; écart à `djpeg -dct int` : au plus 3 niveaux, 0,04 en moyenne sur les essais |
| Suréchantillonnage | Répétition | Lit mieux le filigrane (tableau ci-dessous) ; c'est aussi la chrominance telle qu'elle est stockée |
| YCbCr vers RVB | Tables en virgule fixe sur 16 bits de libjpeg (`jdcolor.c`), bornées à 0 et 255 | Le décodeur le plus courant ; en entiers |
| Couleurs d'un JPEG à trois composantes | Règle de libjpeg (`jdapimin.c`) : JFIF, YCbCr ; sinon segment Adobe, RVB si sa transformation vaut 0 ; sinon identifiants « R », « G », « B », RVB ; YCbCr dans les autres cas | Les fichiers s'interprètent comme dans les logiciels courants |
| JPEG à 2 ou 4 composantes (CMYK, YCCK), échantillonnage non entier | Non lus, format partiel | Aucun code de référence ne les écrit |
| JPEG à une composante, PNG de types 0 et 4 | Niveaux de gris : aucune chrominance, rien à lire ; un PNG en gris n'est pas décompressé | Le filigrane est dans U, nul sans couleurs |
| PNG en seize bits | Octet de poids fort | Ce que fait OpenCV en lecture en couleurs |
| PNG : alpha | Ignoré | Idem ; les codes de référence écrivent du RVB |
| PNG : entrelacement Adam7 | Non lu, format partiel | Rare pour une sortie de générateur ; à revoir s'il en apparaît |
| PNG : CRC | Non vérifiés | Comme un décodeur tolérant ; rien du constat n'en dépend |
| PNG : décompression | Par zlib, au fil de la lecture, arrêtée aux lignes nécessaires, comptée contre le budget de décompression du contexte | Une bombe de décompression est arrêtée (ES-18) ; on ne décompresse pas ce qu'on ne lit pas |

Suréchantillonnage, mesuré le 2026-11-16 : 38 photographies de Wikimedia Commons marquées comme le font les codes de référence, réenregistrées par Pillow en JPEG 4:2:0, décodées par `djpeg -dct int` avec et sans `-nosmooth`, lues par la méthode d'ADR-0203. Médiane des bits concordants :

| Message, qualité | Répétition | Lissage de libjpeg |
| --- | --- | --- |
| Stable Diffusion 1 (136 bits), 95 | 124 | 98 |
| Stable Diffusion 1, 85 | 82 | 80 |
| SDXL (48 bits), 95 | 46 | 42 |
| SDXL, 85 | 36 | 34 |
| FLUX.1 (46 bits), 95 | 46 | 44 |
| FLUX.1, 85 | 40 | 40 |

## Raisons

- A retenue par TheDarkMac, sur recommandation de l'assistant. B écartée : FLUX.1 ne serait pas lu. C écartée : beaucoup de code pour un format que les codes de référence n'écrivent pas.
- Pillow écartée sans être posée en question : du C exposé au fichier là où le Python pur suffit, contraire à ADR-0043, comme l'option C d'ADR-0185.
- Lissage écarté : il mêle la chrominance de zones voisines et affaiblit le filigrane (tableau).
- Retrait des formats du marquage écarté : le rapport d'un WebP doit dire que le dwtDct n'y est pas recherché (F-25).

## Conséquences

- Le lecteur JPEG garde son comportement de T41 sans `toutes` : les tests de `doublejpeg` et `ela`, à empreintes fixées, passent sans changement. Le rang de chaque bloc dans son balayage est désormais transmis au décodage, au lieu d'être déduit de sa position (nécessaire dès que la chrominance est gardée).
- Nouveaux fichiers : `modules/_lecture/png.py`, `modules/_lecture/pixels.py` ; à éprouver par le fuzzing (ES-19, `tests/test_fuzzing.py`).
- Coût mesuré sur le poste : 1,1 à 3,3 s pour un JPEG de 960 × 978 à 960 × 1 280, 3,1 s pour un PNG de 960 × 1 280 à filtre Paeth (défaits en Python pur).
- Le rapport d'un WebP ou d'un HEIC montre le module `dwtdct` non mené, format partiel, et le marquage non recherché.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création |
