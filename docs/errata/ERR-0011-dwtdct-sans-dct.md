# ERR-0011 — La méthode dwtDct décrite avec une DCT qu'elle n'emploie pas

- **Date de constat** : 2026-11-16
- **Tâche en cours** : T32
- **Document ou élément touché** : [inventaire des marquages](../catalogue/inventaire-des-marquages.md), §3, étape 4 de l'algorithme ; [ADR-0174](../decisions/ADR-0174-inventaire-et-lecteur-dwtdct.md), contexte ; entrée `M-DWTDCT` du catalogue 0.6.0 à 0.9.0 (`marquages.toml`, description) ; tous écrits pendant T31
- **Nature** : analyse

## Ce qui était écrit ou fait

- Inventaire, §3, étape 4 : « chaque bloc donne un score tiré de son plus grand coefficient DCT non trivial, quantifié à l'échelle 36 ».
- ADR-0174, contexte : lire le dwtDct demande « conversion YUV, ondelettes de Haar, DCT de blocs 4 × 4 ».
- Catalogue, `M-DWTDCT` : « Message fixe caché dans les coefficients DCT d'une transformée en ondelettes de la chrominance ».

## Ce qui est juste

La méthode `dwtDct` d'invisible-watermark 0.2.0 (`imwatermark/maxDct.py`, identique dans la roue publiée sur PyPI et sur la branche `main` du dépôt le 2026-11-16) n'applique aucune DCT. `encode_frame` et `decode_frame` passent chaque bloc de 4 × 4 valeurs de la bande basse fréquence de Haar (`ca1`) tel quel à `diffuse_dct_matrix` et `infer_dct_matrix`, qui prennent la plus grande valeur absolue du bloc hors de la première (`np.argmax(abs(block.flatten()[1:])) + 1`) et la quantifient à l'échelle 36. Seule la méthode `dwtDctSvd` (fichier `dwtDctSvd.py`) et la fonction inutilisée `diffuse_dct_svd` emploient `cv2.dct`. Le nom de la méthode et de ses fonctions évoque une DCT ; le code n'en fait pas.

## Comment l'erreur a été trouvée

Par la lecture ligne à ligne de `maxDct.py` au début de T32, pour écrire le lecteur, puis par l'essai : le lecteur écrit sans DCT retrouve les messages posés par la bibliothèque elle-même (136 bits sur 136, 48 sur 48, 46 sur 46 sur 38 photographies, journal de T32).

## Cause

Pendant T31, l'algorithme a été résumé à partir des noms des fonctions (`diffuse_dct_matrix`, `infer_dct_matrix`) et du nom de la méthode, sans suivre ce que reçoit chaque fonction. L'inventaire ne demandait pas d'écrire un lecteur : rien n'a éprouvé la description.

## Correction appliquée

- Inventaire, §3 : étape 4 réécrite, entrée d'historique qui renvoie à cet erratum.
- ADR-0174 : entrée d'historique qui renvoie à cet erratum ; le contexte, décision acceptée, est laissé tel quel.
- Catalogue 0.10.0 : nouvelle description de `M-DWTDCT`, qui dit que la méthode n'emploie aucune DCT.
- Le docstring du module `dwtdct` le dit aussi.

## Prévention

L'algorithme est désormais éprouvé par le code : les tests de `tests/test_dwtdct.py` lisent des échantillons marqués par la bibliothèque de référence elle-même (`tests/donnees/dwtdct/generer.py`). Pour un résumé d'algorithme sans lecteur, suivre les données d'une fonction à l'autre plutôt que se fier aux noms.
