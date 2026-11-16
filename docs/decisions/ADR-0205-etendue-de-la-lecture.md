# ADR-0205 — Étendue de la lecture du dwtDct : 4 Mpx, puis le haut de l'image ; 65 536 pixels au moins

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (étendue) ; minimum repris de la bibliothèque, précision de l'assistant
- **Tâche** : T32
- **Exigences liées** : F-24, NF-02, NF-06 ; ADR-0076, ADR-0189, ADR-0199

## Contexte

Le décodage entropique d'un JPEG est en Python pur : environ 4,6 s pour 65 536 blocs (mesure de T42). Une image de 1 024 × 1 024 en 4:4:4 compte environ 49 000 blocs, toutes composantes ; une photographie de 24 Mpx en 4:2:0, environ 560 000. Les sorties des générateurs dépassent rarement 2 Mpx. Le délai d'une analyse est de 120 s (ADR-0076). Chaque bloc de la bande basse de U correspond à un bit connu du message, quelle que soit la part de l'image lue : lire le haut de l'image seulement donne moins de blocs par bit, pas d'autres bits.

## Options envisagées (question posée à TheDarkMac)

### Option A — 4 Mpx, puis le haut (recommandée)

- Avantages : toute sortie de générateur lue en entier ; au-delà, les lignes du haut jusqu'au budget, et le rapport dit la part couverte ; même règle que l'ELA (ADR-0199).
- Inconvénients : un filigrane posé sur une grande image n'est lu que sur son haut.

### Option B — Toujours l'image entière

- Avantages : fidèle à la bibliothèque.
- Inconvénients : une grande photographie peut prendre une minute, ou atteindre le délai.

### Option C — 2 Mpx, puis le haut

- Avantages : plus rapide ; couvre encore les sorties de SDXL et de FLUX.1 en 1 024 × 1 024.
- Inconvénients : moins de blocs par bit sur les grandes images.

## Décision

Option A : au plus 4 194 304 pixels (2 048 × 2 048), soit 65 536 blocs de 8 × 8 pour la première composante d'un JPEG, et au plus 524 288 blocs décodés en tout, balayages compris ; au-delà, les lignes du haut de l'image (de MCU entières pour un JPEG). Précision de l'assistant : une image de moins de 65 536 pixels (256 × 256) n'est pas lue, comme dans la bibliothèque, qui refuse d'y poser comme d'y lire un message ; le module n'en observe que le nombre de pixels.

## Raisons

- A retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : le délai. C écartée : sans gain utile pour les images courantes.
- Le minimum de la bibliothèque : aucun des codes de référence ne peut poser de message sur une image plus petite.

## Conséquences

- La localisation des observations dit « image entière » ou « haut de l'image », avec la zone lue ; `dwtdct.blocs` et `dwtdct.blocs_image` disent la part couverte.
- Un JPEG progressif dont les balayages dépassent le budget des blocs décodés est lu sur moins de lignes, comme pour T41.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création |
