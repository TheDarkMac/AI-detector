# Fiche technique — Double compression JPEG

- **Module** : `doublejpeg` (version 0.1.0)
- **Tâche** : T41
- **Exigences** : F-31
- **Formats** : `jpeg`
- **Directions permises** : `transformation`
- **Règles** : aucune
- **Bibliothèques** : numpy

## Question

La luminance d'un JPEG garde-t-elle la trace d'une compression antérieure à d'autres pas que ceux de ses tables, c'est-à-dire l'image a-t-elle été décompressée puis enregistrée de nouveau en JPEG ?

## Principe

Une image JPEG enregistrée une seconde fois, sans recadrage ni redimensionnement, est quantifiée deux fois sur la même grille de blocs : d'abord au pas q1 de la première table, puis au pas q2 de la table du fichier. Pour une fréquence donnée, l'histogramme des coefficients quantifiés en garde un motif périodique : des valeurs presque absentes quand q1 > q2, des pics ou des creux réguliers dans l'autre cas (Lukáš et Fridrich, « Estimation of Primary Quantization Matrix in Double Compressed JPEG Images », DFRWS 2003, §2 et §4.1 ; texte lu le 2026-11-15). Le module applique leur « test de compatibilité » (§4.1), fréquence par fréquence ([ADR-0186](../decisions/ADR-0186-methode-de-detection.md)) :

1. **Coefficients** : le décodage entropique écrit par le projet (`modules/_lecture/jpeg.py`, en Python pur) lit les coefficients quantifiés de la première composante, la luminance d'un JPEG en YCbCr, sur une région du haut de l'image ([ADR-0185](../decisions/ADR-0185-lecture-des-coefficients-dct.md), [ADR-0187](../decisions/ADR-0187-jpeg-lus.md), [ADR-0189](../decisions/ADR-0189-calcul-en-entiers-et-region.md)). Procédés séquentiel (SOF0, SOF1) et progressif (SOF2), codage de Huffman, huit bits ; intervalles de redémarrage, tables redéfinies entre deux balayages, sous-échantillonnage quelconque.
2. **Luminance recalculée** : transformée inverse (IDCT) des coefficients déquantifiés, arrondie au plus proche et bornée de 0 à 255, comme le fait un décodeur.
3. **Calibrage** : l'image est recadrée de 4 pixels vers le bas et la droite, puis découpée en blocs et transformée de nouveau (DCT). Désaccordés de la grille d'origine, ces coefficients estiment ceux de l'image avant toute compression.
4. **Comparaison** : pour chacune des 9 premières fréquences après le coefficient continu (ordre en zigzag) qui porte au moins 256 coefficients non nuls, l'histogramme des coefficients du fichier (de −b à b, b la plus petite borne de 8 à 128 qui contient 99,5 % des valeurs, le zéro retiré) est comparé à ceux qu'on obtient en quantifiant les estimations au pas q1, puis le résultat au pas q2, pour chaque q1 de 1 à min(255, 4 q2 + 16). Écart : somme des carrés des différences des histogrammes normalisés. Un q1 qui divise q2 ne laisse aucune trace (quantifier à q1 puis à q2 revient à quantifier à q2) : le meilleur de ces q1 représente la simple compression ; le meilleur des autres, la double.
5. **Trace** : la fréquence porte une trace si l'écart de la simple compression est non nul et vaut au moins 4 fois celui de la double ; le q1 de la double est alors le pas antérieur estimé.
6. **Qualité antérieure** : si au moins 3 fréquences portent une trace, les qualités de libjpeg (1 à 100, huit bits) dont la table de luminance a exactement ces pas à ces fréquences sont observées ; c'est le « closest standard matrix » de Lukáš et Fridrich (§4.1).

Écarts à l'article, choisis sur les essais de T41 : histogrammes signés et écart quadratique au lieu des valeurs absolues et de la norme L1 ; simulation dans le domaine des coefficients, sans retour aux pixels entre les deux quantifications (l'article fait la même simplification, §4.1.1) ; décision « trace ou non » par le rapport des écarts. L'article retient surtout un classifieur à réseau de neurones (§4.3), que l'outil n'emploie pas : aucune IA embarquée.

Tout le calcul est fait en entiers de 64 bits ([ADR-0189](../decisions/ADR-0189-calcul-en-entiers-et-region.md)) : cosinus en virgule fixe (2^12, écrits en entiers dans le code), quantifications arrondies la moitié loin de zéro comme libjpeg (`jcdctmgr.c`), écarts comparés en fractions exactes. Le résultat est le même sur toutes les machines (NF-06).

## Entrées

| Format | Emplacement lu |
| --- | --- |
| JPEG | Tous les segments jusqu'à EOI : DQT, DHT, SOF0 à SOF2, DRI, SOS ; données entropiques des balayages qui portent la première composante, jusqu'à la dernière ligne de la région ; les autres balayages sont sautés |

Région : les premières lignes de blocs de la première composante, au plus 32 768 blocs (environ 2,1 millions de pixels) et au plus 262 144 blocs décodés en tout, balayages et autres composantes compris ; le nombre de lignes se déduit des balayages annoncés, avant tout décodage.

Données de référence, recopiées dans le code du module : la table de luminance de l'annexe K de T.81 (tableau K.1), mise à l'échelle comme libjpeg ; la matrice de la DCT de taille 8 en virgule fixe.

## Sorties

| Nom | Valeur |
| --- | --- |
| `doublejpeg.procede` | `sequentiel` ou `progressif` |
| `doublejpeg.blocs` | Blocs de la première composante examinés (la région) |
| `doublejpeg.blocs_image` | Blocs de la première composante dans l'image entière |
| `doublejpeg.frequences_examinees` | Nombre de fréquences examinées, de 0 à 9 |
| `doublejpeg.frequences` | Rangs en zigzag des fréquences examinées (1 à 9) ; absent si aucune |
| `doublejpeg.pas` | Pas de la table du fichier à ces fréquences, dans le même ordre |
| `doublejpeg.traces` | Nombre de fréquences qui portent une trace ; absent si aucune n'est examinée |
| `doublejpeg.frequences_tracees` | Rangs des fréquences qui portent une trace ; absent si aucune |
| `doublejpeg.pas_anterieurs` | Pas antérieur estimé pour chacune, dans le même ordre |
| `doublejpeg.qualites_ijg_anterieures` | Qualités de libjpeg compatibles avec ces pas, si 3 traces au moins et si une qualité convient |

Une analyse non menée de ce module ne rend pas le contrôle avant publication incomplet : il ne lit aucune métadonnée ([ADR-0190](../decisions/ADR-0190-module-et-versions-de-t41.md)).

Une image trop petite pour le calibrage (moins de 12 pixels de côté) ou dont aucune fréquence n'a assez de coefficients non nuls donne `doublejpeg.frequences_examinees` à 0.

## Données identifiantes

Aucune.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien en général : un appareil compresse une fois. Une trace dit seulement que le fichier n'est pas sorti tel quel d'une seule compression |
| Transformation banale (recompression, redimensionnement) | Une mesure : la trace d'un réenregistrement en JPEG sans recadrage ni redimensionnement ; un redimensionnement l'efface |
| Retouche | Un logiciel de retouche réenregistre l'image et peut laisser la même trace ; la technique ne localise pas la zone retouchée et ne distingue pas une retouche d'un simple réenregistrement |
| Génération | Rien : une image générée puis enregistrée deux fois en JPEG porte la même trace |

## Ce qui déclenche un constat

Le module n'émet aucun constat. La règle « moteur » du catalogue qui lit ses observations ([ADR-0188](../decisions/ADR-0188-constat-de-double-compression.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-DOUBLEJPEG-001` Luminance d'un JPEG quantifiée deux fois | `doublejpeg.traces`, `doublejpeg.frequences_examinees` | au moins 4 traces |

Indice vers la transformation, fondé sur une mesure, de niveau « faible » d'après son taux de faux positifs (« Taux d'erreur ») ; le résumé recommande alors d'obtenir l'original ([ADR-0156](../decisions/ADR-0156-recommandation-d-obtenir-l-original.md)).

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `doublejpeg` 0.1.0, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 1776 | 1/609 : 0,2 % [0,0 % ; 0,9 %] | 0/608 : 0,0 % [0,0 % ; 0,6 %] | — | 0 |
| Générés | 424 | 330 | 0/94 : 0,0 % [0,0 % ; 3,9 %] | — | 94/94 : 100,0 % [96,1 % ; 100,0 %] | 0 |
| Transformés | 1294 | 781 | 0/513 : 0,0 % [0,0 % ; 0,7 %] | 0/335 : 0,0 % [0,0 % ; 1,1 %] | 178/178 : 100,0 % [97,9 % ; 100,0 %] | 0 |
| Retouchés | 273 | 162 | 0/111 : 0,0 % [0,0 % ; 3,3 %] | — | 111/111 : 100,0 % [96,7 % ; 100,0 %] | 0 |
| Malformés | 91 | 46 | 33/45 : 73,3 % [59,0 % ; 84,0 %] | 0/12 : 0,0 % [0,0 % ; 24,2 %] | — | 0 |

| Règle | Catégorie | Direction | Faux positifs | Niveau permis | Niveau |
| --- | --- | --- | --- | --- | --- |
| R-DOUBLEJPEG-001 v2 | indice | transformation | 27/608 : 4,4 % [3,1 % ; 6,4 %] | faible | faible |

<!-- Fin des taux mesurés. -->

Sur le corpus de référence, la règle se déclenche sur 27 des 608 JPEG authentiques analysés (tableau ci-dessus) : une photographie ordinaire de Wikimedia Commons peut avoir été enregistrée deux fois en JPEG (par l'appareil, puis par un logiciel), ce que la règle constaterait à bon droit ; le banc la compte pourtant comme faux positif, faute de connaître son histoire. Son niveau reste « faible ». Le rapport des écarts (4) et le seuil de la règle (4 traces sur 9) ont été fixés à la main, avant toute mesure, sur les essais de T41, consignés au [journal](../journal/T41-double-compression.md) et dans le calibrage de la règle. Sur ces essais : aucune image compressée une seule fois ne dépasse 2 traces (images de synthèse et aplats compris) ; 22 des 24 doubles compressions à qualité croissante d'images sans perte en portent 4 ou plus, et la qualité antérieure de libjpeg y est retrouvée quand elle est observée ; une photographie de qualité 80 réenregistrée à 90 ou 95 porte 7 ou 9 traces et la qualité 80, réenregistrée à 85, 3 traces seulement. Les tests (`tests/test_double_compression.py`) vérifient le déclenchement sur des échantillons écrits par cjpeg de libjpeg-turbo, livrés avec les tests.

## Limites connues

- **Double compression non alignée** : un recadrage qui décale la grille des blocs, un redimensionnement, une rotation autre qu'un multiple de 90° sans transcodage efface la trace ; elle n'est pas cherchée.
- **Mêmes tables** : deux compressions aux mêmes tables ne laissent pas cette trace ; une fréquence où q2 est un multiple de q1 non plus. La trace est la plus nette quand la seconde compression est plus fine (q1 > q2) ; à qualités proches (70 puis 75, 80 puis 85), elle reste souvent sous le seuil.
- **Images de synthèse, aplats, graphiques** : leurs histogrammes s'écartent du modèle et peuvent porter une ou deux traces isolées après une seule compression.
- **Région** : seule la première composante, sur le haut de l'image, est examinée ; un collage limité au reste de l'image ne pèse pas, et aucune zone n'est localisée.
- **Qualité antérieure** : seules les tables de luminance de libjpeg, en huit bits, sont essayées ; plusieurs qualités voisines ont souvent les mêmes pas aux 9 premières fréquences (49 à 51 par exemple), d'où une liste.
- **JPEG non lus** : codage arithmétique, procédés sans perte et hiérarchique, précision de douze bits, hauteur donnée par un segment DNL, tables de Huffman absentes (JPEG d'une vidéo MJPEG qui compte sur les tables par défaut) : analyse non menée, format partiel. Des données entropiques qui manquent avant la fin de la région : fichier tronqué si le fichier s'arrête, format partiel sinon. Les composantes RGB ou CMJN sans transformation de couleur sont lues comme des composantes ordinaires : la première est examinée.
- **Coefficients** : un coefficient déquantifié au-delà de ±2^15 est borné, comme les entiers de 16 bits de libjpeg ; les numéros des marqueurs RSTn ne sont pas vérifiés.

## Sécurité

- Le décodage entropique est écrit par le projet, en Python pur ; numpy ne lit pas le fichier, il calcule sur les coefficients décodés, en entiers. Il est chargé à l'import du module, avant les restrictions, avec un seul fil d'OpenBLAS ([ADR-0185](../decisions/ADR-0185-lecture-des-coefficients-dct.md)).
- Limites comptées propres au lecteur (ADR-0189) : 32 768 blocs de région, 262 144 blocs décodés, 64 balayages, 256 tables de Huffman ; au-delà, région réduite ou format partiel. Chaque segment compte un objet et chaque bloc décodé un objet (ADR-0078) ; les dimensions sont vérifiées avant tout décodage (`verifier_dimensions`).
- Les données entropiques sont lues par morceaux d'au plus 16 Mio, et seulement jusqu'à une borne calculée sur les blocs de la région (420 octets par bloc) ; la fin d'un balayage est cherchée par une expression régulière de la bibliothèque standard.
- Aucune exécution, aucun réseau, aucune écriture.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-15 | 0.1.0 | Création (T41, ADR-0185 à ADR-0190) |
