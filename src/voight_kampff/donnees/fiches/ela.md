# Fiche technique — Niveau d'erreur de recompression (ELA)

- **Module** : `ela` (version 0.1.0)
- **Tâche** : T42
- **Exigences** : F-32, F-84
- **Formats** : `jpeg`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : numpy

## Question

Quand on réenregistre la luminance d'un JPEG à une qualité connue, de combien change chaque bloc de 8 × 8 pixels, et comment ces changements se répartissent-ils sur l'image ?

## Principe

Une image JPEG est quantifiée bloc par bloc. Réenregistrer une image déjà compressée change peu les blocs déjà « usés » par une compression comparable, davantage ceux qui ne le sont pas : l'erreur introduite par une nouvelle compression dépend de ce que le bloc a déjà subi (Krawetz, « A Picture's Worth: Digital Image Analysis and Forensics », Black Hat USA 2007, livre blanc, §3.4.2, qui nomme la technique et réenregistre « at a known error rate, such as 95% » ; texte lu le 2026-11-15). Une zone collée ou retouchée après la dernière compression peut donc ressortir. La technique ne dit pas pourquoi un bloc change plus qu'un autre : le contenu y compte autant que l'histoire du fichier. Elle ne produit donc qu'une carte, sans seuil ni constat ([ADR-0198](../decisions/ADR-0198-carte-sans-constat.md)).

Calcul ([ADR-0199](../decisions/ADR-0199-methode-et-etendue-de-l-ela.md)) :

1. **Coefficients** : le décodage entropique du projet (`modules/_lecture/jpeg.py`, celui de T41) lit les coefficients quantifiés de la première composante, la luminance d'un JPEG en YCbCr ; sur toute l'image jusqu'à 65 536 blocs, sur les lignes du haut au-delà.
2. **Luminance** : transformée inverse (IDCT) des coefficients déquantifiés, arrondie au plus proche et bornée de 0 à 255 (`modules/_lecture/dct.py`, commun avec T41).
3. **Recompression** : chaque bloc est transformé de nouveau (DCT), quantifié par la table de luminance de libjpeg à la qualité 95 (annexe K de T.81 mise à l'échelle comme libjpeg), arrondi la moitié loin de zéro comme libjpeg (`jcdctmgr.c`), déquantifié et recalculé en pixels. Seule la quantification est simulée : ni chrominance, ni codage entropique, qui ne changent pas les pixels de luminance.
4. **Carte** : la valeur d'un bloc est la somme des écarts absolus de ses 64 pixels entre les deux luminances, multipliée par 2 et bornée à 255 ; un écart moyen de 2 niveaux par pixel donne le blanc. Le gain est fixe : deux cartes se comparent, et une image peu sensible reste sombre au lieu d'être étirée.

Tout le calcul est fait en entiers de 64 bits, cosinus en virgule fixe (2^12), comme pour T41 ([ADR-0189](../decisions/ADR-0189-calcul-en-entiers-et-region.md)). La carte est écrite en PNG en niveaux de gris sur huit bits, une valeur par bloc, sans filtre et sans compression (blocs « stockés » de deflate écrits par le module) : ses octets, donc son empreinte, ne dépendent ni de la machine ni de la version de zlib (NF-06).

## Entrées

| Format | Emplacement lu |
| --- | --- |
| JPEG | Tous les segments jusqu'à EOI : DQT, DHT, SOF0 à SOF2, DRI, SOS ; données entropiques des balayages qui portent la première composante, jusqu'à la dernière ligne lue ; les autres balayages sont sautés |

Étendue : toute l'image si sa luminance compte au plus 65 536 blocs (2 048 × 2 048 pixels, ou 2 560 × 1 600) ; au-delà, les premières lignes de blocs jusqu'à ce nombre. Au plus 524 288 blocs décodés en tout, balayages et autres composantes compris : un JPEG progressif, qui décode plusieurs fois chaque bloc, peut voir sa carte réduite à moins de lignes. Le nombre de lignes se déduit des balayages annoncés, avant tout décodage ([ADR-0199](../decisions/ADR-0199-methode-et-etendue-de-l-ela.md)).

Données de référence, recopiées dans le code : la table de luminance de l'annexe K de T.81 (tableau K.1) ; la matrice de la DCT de taille 8 en virgule fixe.

## Sorties

| Nom | Valeur |
| --- | --- |
| `ela.procede` | `sequentiel` ou `progressif` |
| `ela.qualite` | 95, qualité de libjpeg de la recompression |
| `ela.blocs` | Blocs de luminance sur la carte ; localisation : zone couverte, en pixels |
| `ela.blocs_image` | Blocs de luminance de l'image entière |
| `ela.ecart_moyen` | Écart absolu moyen par pixel sur la carte, en niveaux, arrondi au centième |
| `ela.ecart_moyen_max` | Plus grand écart moyen par pixel d'un bloc, en niveaux, arrondi au centième |

Visualisation ([ADR-0200](../decisions/ADR-0200-visualisations-au-rapport.md)) : `carte_ela`, PNG d'une valeur par bloc (`ela.blocs` pixels), avec son empreinte SHA-256 et la zone couverte. Le rapport HTML l'affiche dans la rubrique « Visualisations », sous son avertissement d'interprétation ; le JSON la porte en base64.

Une analyse non menée de ce module ne rend pas le contrôle avant publication incomplet : il ne lit aucune métadonnée ([ADR-0201](../decisions/ADR-0201-module-et-versions-de-t42.md)).

## Avertissement d'interprétation (F-32)

Affiché au rapport au-dessus de la carte, et repris ici (`rapport/textes.toml`, `visualisations.carte_ela.avertissement`) :

- Cette carte n'est ni une preuve ni un indice, et ne désigne aucune zone retouchée : c'est une aide à la lecture, sans seuil ni constat.
- Chaque point est un bloc de 8 × 8 pixels de la luminance : plus il est clair, plus le bloc change quand l'image est réenregistrée en JPEG à la qualité 95 de libjpeg.
- Les contours, les textures fines et le texte sont naturellement plus clairs, les aplats et les ciels plus sombres : deux zones ne se comparent que si leur contenu est de même nature.
- Une zone nettement plus claire que des zones semblables peut avoir été ajoutée ou modifiée après la dernière compression ; elle peut aussi venir du contenu lui-même, ou d'un réenregistrement de toute l'image.
- Une image enregistrée une seule fois à une qualité élevée est claire partout, et un collage n'y ressort pas ; une image réenregistrée plusieurs fois, ou à faible qualité, est sombre partout et ne montre plus rien.
- La carte ne distingue pas une image générée par IA d'une photo : une image générée puis enregistrée en JPEG donne une carte ordinaire.

## Données identifiantes

La carte : elle montre le contenu de l'image, réduit d'un facteur 8 (contours, silhouettes, texte en gros caractères). Catégorie identifiante `contenu`, masquée par défaut avec son empreinte ; `--reveler contenu` l'affiche, et la levée est annoncée en tête du rapport ([ADR-0200](../decisions/ADR-0200-visualisations-au-rapport.md)). Les observations chiffrées ne le sont pas.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien : une image compressée une seule fois par un appareil donne une carte claire et régulière, que le contenu module |
| Transformation banale (recompression, redimensionnement) | Une image réenregistrée en entier s'assombrit partout, sauf ce qui n'avait pas subi les compressions antérieures ; un redimensionnement brouille la grille des blocs et atténue les contrastes. Rien n'est établi |
| Retouche | Une zone collée ou retouchée après la dernière compression peut ressortir plus claire que des zones de même nature ; elle peut aussi ne pas ressortir (image compressée une seule fois à qualité élevée, retouche réenregistrée plusieurs fois). La carte montre, elle n'établit rien |
| Génération | Rien : une image générée puis enregistrée en JPEG donne une carte ordinaire |

## Ce qui déclenche un constat

Rien : le module n'émet aucun constat et aucune règle du catalogue ne lit ses observations ([ADR-0198](../decisions/ADR-0198-carte-sans-constat.md)). Sa direction déclarée, `rien_de_particulier`, n'est employée par aucun constat ; le manifeste en exige une ([ADR-0201](../decisions/ADR-0201-module-et-versions-de-t42.md)).

## Taux d'erreur

Sans objet au sens du §8 : aucun constat, donc ni faux positif ni faux négatif à compter. Ce qui est mesurable, et mesuré sur les essais de T42 ([journal](../journal/T42-ela.md)) : sur une image de synthèse avec bruit de 1 600 × 1 200 pixels, compressée à 60, où un carré de 300 × 300 pixels non compressé est collé, puis enregistrée à 92, l'écart moyen est de 1,07 niveau par pixel dans le carré contre 0,11 ailleurs (valeurs 143 et 13 sur la carte) ; la même image compressée une seule fois à 92 donne 1,04 partout, carré compris, qui ne ressort pas ; réenregistrée à 85, 0,35 partout ; l'image au carré collé, réenregistrée à 92, garde son carré (1,07 contre 0,15). La lecture d'une carte par des personnes n'est pas mesurée ; elle relève de l'étude d'usage (T104, hors V1).

## Limites connues

- **Interprétation** : la carte dépend autant du contenu (contours, textures, aplats) que de l'histoire du fichier ; aucune zone n'est désignée par l'outil.
- **Compression unique à qualité élevée** : un collage enregistré avec le reste de l'image en une seule compression ne ressort pas.
- **Réenregistrements répétés ou faible qualité** : la carte s'assombrit partout et ne montre plus rien. Un redimensionnement ou un recadrage qui décale la grille atténue les contrastes : sur l'essai du carré collé, réduit à 75 % puis enregistré à 92, 0,76 niveau par pixel dans le carré contre 0,55 ailleurs, au lieu de 1,07 contre 0,11.
- **Luminance seule** : la chrominance n'est pas examinée ; une retouche des seules couleurs n'apparaît pas.
- **Étendue** : au-delà de 65 536 blocs, seul le haut de l'image est couvert, et le rapport le dit ; un JPEG progressif peut être couvert sur moins de lignes.
- **Qualité fixe** : la recompression est faite à la qualité 95 de libjpeg ; un fichier dont les tables sont plus fines est clair partout (essais : 1,53 et 1,52 niveau par pixel, environ 195 sur 255, pour une même image enregistrée une fois à 98 et à 100).
- **JPEG non lus** : comme T41 (codage arithmétique, procédés sans perte et hiérarchique, douze bits, DNL, tables de Huffman absentes) : analyse non menée.
- **Recompression simulée** : la DCT en virgule fixe et l'arrondi suivent libjpeg sans être bit à bit ceux de `cjpeg`. Sur les essais de T42, comparés à `cjpeg -grayscale -quality 95 -dct int` puis `djpeg -dct int` de libjpeg-turbo 2.1.5 : jusqu'à 7 niveaux d'écart sur un pixel, mais un écart moyen par pixel, ce que montre la carte, égal au millième près (1,045 contre 1,046 ; 0,148 contre 0,149 ; 0,157 contre 0,156). La luminance décodée diffère de celle de `djpeg` d'au plus un niveau, sur 2 % des pixels environ.

## Sécurité

- Lecture par le décodage entropique du projet (T41), en Python pur ; numpy calcule sur les coefficients décodés, en entiers, sans lire le fichier ([ADR-0185](../decisions/ADR-0185-lecture-des-coefficients-dct.md)).
- Limites propres au module : 65 536 blocs de carte, 524 288 blocs décodés ; les limites du lecteur (64 balayages, 256 tables de Huffman, objets comptés, dimensions vérifiées avant tout décodage) s'appliquent.
- La carte n'est pas une donnée du fichier : c'est un PNG écrit par le module, vérifié par le modèle du rapport (signature, dimensions, taille d'au plus 768 Kio, empreinte) avant d'entrer dans un rapport ; le HTML ne l'admet que comme image `data:` (politique `img-src data:`).
- Aucune exécution, aucun réseau, aucune écriture.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-15 | 0.1.0 | Création (T42, ADR-0197 à ADR-0201) |
