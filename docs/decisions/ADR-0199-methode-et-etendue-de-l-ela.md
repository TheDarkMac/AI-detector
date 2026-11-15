# ADR-0199 — ELA : une valeur par bloc, qualité 95 en entiers, gain fixe, 65 536 blocs puis le haut de l'image

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (paramètres chiffrés précisés par l'assistant)
- **Tâche** : T42
- **Exigences liées** : F-32, F-84, NF-06, NF-02 ; ADR-0185, ADR-0187, ADR-0189

## Contexte

L'ELA réenregistre l'image à une qualité connue et montre de combien chaque partie change (Krawetz, « A Picture's Worth », Black Hat USA 2007, livre blanc, §3.4.2 : « such as 95% » ; l'erreur est confinée aux blocs de 8 × 8). Le projet ne décode que la luminance d'un JPEG, par son décodage entropique en Python pur (T41, ADR-0185), sans conversion de couleurs. Trois choix étaient à faire : la forme de la carte, le réglage de la recompression et de l'échelle, l'étendue lue. Mesures de T42 sur ce poste : décoder une photo de 24 Mpx prend 33 s, plus 18 s d'IDCT, et le lecteur y dépasse la limite d'objets en progressif ; pour 4 Mpx (65 536 blocs), 5 s de décodage en séquentiel, environ 10 s en progressif, et 3 s de calcul.

## Options envisagées

### Forme de la carte

- **A — Une valeur par bloc** : écart moyen de chaque bloc 8 × 8 ; 750 × 500 pour 24 Mpx ; suit la grille où l'ELA a un sens ; un PNG de quelques dizaines de Kio, dans la limite d'1 Mio d'un message du processus de travail.
- **B — Par pixel, réduite** : erreur par pixel comme les outils courants, réduite à 1 024 pixels au plus long côté par le maximum de chaque zone ; plus proche de ce que le public connaît, plus lourde, et la réduction mêle des blocs.

### Recompression et échelle

- **A — Qualité 95, gain fixe** : tables de libjpeg à la qualité 95, calcul en entiers comme T41 ; erreur multipliée par un gain fixe et bornée à 255 : deux cartes se comparent, une image peu sensible reste sombre.
- **B — Qualité 95, gain normalisé** : carte étirée pour que l'erreur maximale soit blanche ; tout se voit, mais le bruit d'une image régulière est grossi et deux cartes ne se comparent pas.

### Étendue

- **A — 4 Mpx, puis le haut** : image entière jusqu'à 65 536 blocs de luminance (2 048 × 2 048, ou 2 560 × 1 600 : la taille des images qui circulent sur les messageries) ; au-delà, les lignes du haut jusqu'à ce budget, et le rapport dit quelle part de l'image la carte couvre, comme la région de T41.
- **B — 4 Mpx, sinon non menée** : pas de carte partielle qui pourrait tromper.
- **C — 8 Mpx, puis le haut** : 131 072 blocs, 20 à 25 s par image.

## Décision

Option A dans les trois cas, avec ces paramètres (précisés par l'assistant, dans le code du module et dans la fiche `ela`) :

| Paramètre | Valeur | Raison |
| --- | --- | --- |
| Qualité de recompression | 95, tables de luminance de libjpeg (annexe K de T.81 mise à l'échelle) | Valeur citée par Krawetz 2007 ; libjpeg est l'encodeur le plus courant |
| Quantification | DCT en virgule fixe (2^12), arrondi la moitié loin de zéro (`jcdctmgr.c`), déquantification, IDCT en entiers | Même calcul que T41 (ADR-0189) : même résultat sur toutes les machines |
| Valeur d'un bloc | Somme des écarts absolus de ses 64 pixels, fois 2, bornée à 255 | Un écart moyen de 2 niveaux par pixel donne le blanc. Sur les essais : collage 143 contre 13 autour ; compression unique à 92 vers 133, non saturée. Avec la somme seule (gain 1), la carte était trop sombre (68 contre 7) |
| PNG | Niveaux de gris sur huit bits, sans filtre, blocs stockés de deflate écrits par le module | Les octets d'un flux compressé dépendent de la version de zlib : l'empreinte de la carte changerait d'une machine à l'autre (NF-06) |
| Blocs de la carte | 65 536 au plus | Choix de TheDarkMac (option A) |
| Blocs décodés | 524 288 au plus | Un JPEG progressif décode plusieurs fois chaque bloc ; en deçà de la limite d'objets du contexte (2^20) |

Le lecteur de T41 reçoit ces bornes en paramètres ; ses valeurs par défaut, celles de T41, ne changent pas.

## Raisons

- Les trois options A retenues par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec les options.
- Forme B écartée : plus lourde, et une réduction par zones efface la grille des blocs sur laquelle se lit l'ELA.
- Échelle B écartée : deux cartes ne se compareraient plus, et une image régulière paraîtrait pleine de « zones ».
- Étendue B écartée : la plupart des photos d'appareils dépassent 4 Mpx, et une carte du haut de l'image, annoncée comme telle, reste utile ; C, pour le délai.
- Le gain 2 et le PNG non compressé sont des précisions de l'assistant, mesurées sur les essais de T42 (journal).

## Conséquences

- La recompression simulée n'est pas bit à bit celle de `cjpeg` : jusqu'à 7 niveaux d'écart sur un pixel, mais un écart moyen égal au centième (essais de T42 ; test-oracle `tests/test_ela.py` quand cjpeg et djpeg sont présents).
- Au-delà de 65 536 blocs, seul le haut de l'image est couvert ; la localisation de la carte et la rubrique du rapport le disent.
- La chrominance n'est pas examinée.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
