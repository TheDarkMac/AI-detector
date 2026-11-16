# ADR-0203 — Lecture du dwtDct : chaque message dans son domaine, bits décidés par rang, SDXL dans les deux ordres des couleurs

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (méthode) ; précisions de l'assistant, mesurées
- **Tâche** : T32
- **Exigences liées** : F-24, NF-06 ; ADR-0016, ADR-0021, ADR-0174, ADR-0189

## Contexte

La bibliothèque invisible-watermark 0.2.0 (`imwatermark/maxDct.py`) convertit l'image en YUV par OpenCV, prend la bande basse fréquence de Haar de la composante U, la découpe en blocs de 4 × 4 et quantifie à l'échelle 36 la plus grande valeur absolue de chaque bloc hors de la première ; sa lecture moyenne les scores des blocs de chaque bit et décide le bit au seuil de 127/255 (inventaire des marquages, §3 ; la méthode n'emploie aucune DCT, [ERR-0011](../errata/ERR-0011-dwtdct-sans-dct.md)). Le détecteur de Stability (`scripts/demo/detect.py` de generative-models) lit l'image par `cv2.imread`, en entiers.

La lecture du code de chaque générateur montre trois choses :

- **Domaine.** Stable Diffusion 1 passe une image en entiers : OpenCV calcule U sur huit bits, centrée sur 128. SDXL et FLUX.1 passent une image en flottants de 0 à 255 : OpenCV calcule U en flottant, centrée sur 0,5 (vérifié : U de (B, G, R) = (255, 0, 0) vaut 111,6576 en flottant, soit 0,492 (B - Y) + 0,5). Lue en entiers, la bande basse de U est décalée de 255 : 255 modulo 36 vaut 3, et le signe d'une valeur négative est perdu. Les bits posés en flottant se lisent mal en entiers.
- **Ordre des couleurs.** Le pipeline SDXL de diffusers passait l'image en RVB à la bibliothèque, qui attend du BVR, du 2023-07-06 (commit `bc9a8cef6f`) au 2024-04-26 (PR huggingface/diffusers#7013, commit `ebc99a77aa`).
- **Images non marquées.** Avec le seuil d'un demi, leurs bits valent presque tous 0 : une valeur quantifiée tombe au-delà de la moitié de l'échelle avec une probabilité proche de 17/36. Le nombre de bits concordants d'une image non marquée est donc proche du nombre de 0 du message.

Essais du 2026-11-16 (journal de T32) : 40 vignettes de 960 pixels de Wikimedia Commons, versées avant 2022, dont 38 en couleurs, marquées par la bibliothèque elle-même comme chaque code le fait, puis enregistrées comme il le fait (Stable Diffusion 1 et SDXL en PNG, FLUX.1 en JPEG de qualité 95 en 4:4:4). Bits concordants, médiane (minimum) :

| Lecture | SD 1 (136) | SDXL (48) | SDXL en RVB (48) | FLUX.1 (46) |
| --- | --- | --- | --- | --- |
| A — Bibliothèque : entiers, seuil d'un demi | 135 (68) | 33 (18) | 44 (21) | 31 (3) |
| B — Domaine du code, seuil d'un demi | 136 (68) | 48 (33) | 48 (27) | 46 (41) |
| C — Domaine du code, décision par rang | 136 (136) | 48 (48) | 48 (28) | 46 (46) |
| C sur les mêmes images, non marquées : maximum | 76 | 31 | 34 | 32 |

Avec le seuil d'un demi, Stable Diffusion 1 échoue sur les images à chrominance lisse : abaisser la plus grande valeur d'un bloc pour un 0 laisse souvent une voisine devenir la plus grande, et les bits à 0 dépassent alors la moitié en moyenne (45 % et 57 % des blocs gardent la position de leur plus grande valeur sur les deux images examinées).

## Options envisagées (question posée à TheDarkMac)

### Option A — Fidèle à la bibliothèque

- Avantages : comparable aux seuils publiés par Stability (48 bits : plus de 33 « probablement marquée », 0,02 % de faux positifs ; plus de 35 « très probablement », aucun sur 10 000 images).
- Inconvénients : manque la moitié des images de SDXL et de FLUX.1 ; la loi des bits d'une image non marquée dépend du message.

### Option B — Domaine du code, seuil d'un demi

- Avantages : bien plus sensible pour SDXL et FLUX.1 ; reste la décision de la bibliothèque.
- Inconvénients : Stable Diffusion 1 échoue sur les images à chrominance lisse ; même loi déséquilibrée des images non marquées.

### Option C — Domaine du code, décision par rang (recommandée)

- Avantages : chaque photographie marquée lue en entier ; les k bits aux scores les plus élevés valent 1, k étant le nombre de 1 du message : si l'ordre des scores d'une image non marquée ne dépend pas du message, le nombre de bits concordants suit une loi hypergéométrique, calculable exactement (ADR-0204).
- Inconvénients : s'écarte du décodeur de référence ; la décision emploie le nombre de 1 du message, ce qui est permis parce que le message est public et fixe.

## Décision

Option C, avec ces précisions de l'assistant :

| Point | Choix | Raison |
| --- | --- | --- |
| U sur huit bits (SD 1) | Y = (1868 B + 9617 G + 4899 R + 2^13) >> 14, U = ((B - Y) x 8061 + 128 x 2^14 + 2^13) >> 14, bornée à 0 et 255 | Égal à `cv2.cvtColor(..., COLOR_BGR2YUV)` d'OpenCV 5.0.0 sur les 2^24 couleurs (vérifié pendant T32) |
| U en flottant (SDXL, FLUX.1) | 10^6 U = 492 (1000 B - (299 R + 587 G + 114 B)) + 500 000, entier exact | Coefficients d'OpenCV en flottant (0,299, 0,587, 0,114, 0,492, décalage 0,5) ; OpenCV calcule en flottants de 32 bits, l'écart ne compte pas devant la demi-échelle |
| Bande basse de Haar | a + b + c + d sur chaque carré de 2 x 2 (le double de la valeur de PyWavelets), entiers ; l'échelle est doublée d'autant | Calcul exact en entiers (ADR-0189) |
| Grille | Image recadrée au multiple de 8 pixels en haut à gauche ; `largeur // 8` blocs par ligne | Celle de la bibliothèque, qui recadre au multiple de 4 puis découpe la bande en blocs de 4 |
| Égalités | La première des plus grandes valeurs, comme `np.argmax` ; des scores égaux de part et d'autre du rang k laissent leurs bits indéterminés, comptés comme non concordants | Une image uniforme, dont tous les scores sont égaux, ne donne aucun bit concordant |
| SDXL | Lu dans l'ordre BVR, puis le rouge et le bleu échangés ; la meilleure des deux lectures est gardée, et l'échange est observé s'il lit strictement mieux | Un message posé dans un ordre se lit en partie dans l'autre (48 et 46 bits sur un essai) : deux règles distinctes compteraient deux fois le même filigrane |
| SD 1 et FLUX.1 | Un seul ordre | Leurs codes passent l'image en BVR ; aucun changement connu |

## Raisons

- C retenue par TheDarkMac, sur recommandation de l'assistant : seule option qui lit toutes les images marquées des essais, et dont la loi sous l'hypothèse nulle se calcule.
- A écartée : manque la moitié des images de SDXL et de FLUX.1. B écartée : Stable Diffusion 1 manqué sur les images à chrominance lisse.
- Les seuils publiés par Stability ne s'appliquent pas à cette lecture : ADR-0204 fixe les siens.

## Conséquences

- Les nombres de bits concordants du rapport ne se comparent pas à ceux de `detect.py` : la fiche `filigrane-dwtdct` le dit, avec les valeurs des deux lectures sur les échantillons des tests.
- Les échantillons des tests sont marqués par la bibliothèque elle-même (`tests/donnees/dwtdct/generer.py`, environnement séparé avec OpenCV et PyWavelets, que le projet n'a pas).
- L'hypothèse de la loi hypergéométrique (un ordre des scores indépendant du message) se vérifie sur un relevé d'images non marquées (ADR-0204).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création |
