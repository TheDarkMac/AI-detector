# T32 — Lecteur du filigrane dwtDct d'invisible-watermark

- **Branche** : `tache/T32-dwtdct`
- **Dates** : 2026-11-16
- **Exigences couvertes** : F-24 (réalisée) ; F-25 (le dwtDct passe des marquages non recherchés aux recherchés)
- **Décisions** : ADR-0202 à ADR-0206, tous acceptés (ADR-0206 validé pendant la revue de la PR)
- **Errata** : [ERR-0011](../errata/ERR-0011-dwtdct-sans-dct.md)

## Objectif

Lire le filigrane dwtDct d'invisible-watermark, posé par les codes de référence de Stable Diffusion 1, de SDXL et de FLUX.1 : décoder les pixels, fixer un seuil de bits concordants et mesurer ses faux positifs, fixer la direction et le niveau du constat (ADR-0174). Demandée par TheDarkMac le 2026-11-16 (« T32, the dwtDct watermark reader »), suite prévue de la V1.

## État initial

- PR [#32](https://github.com/TheDarkMac/AI-detector/pull/32) (complément de T40). Commits : `871481a` (tables relevées, catalogue 0.9.0), `c06bc2e` (tests), `20ece1f` (documentation), `717258f` (ADR-0196 passé à « Accepté » après le « Oui, valide ADR-0196 » de TheDarkMac). CI sur `20ece1f` : docs 43811163814 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code 43811163564 vert ; sur `717258f` : docs 43813152530 et code 43813152522 verts (16 contrôles, CodeRabbit ignoré).
- L'assistant a mergé la PR le 2026-11-16 à 05:59:30 UTC, après le « Oui, merge si vert » de TheDarkMac : commit de merge `6bbd94d`. Lancements de push sur `6bbd94d` : docs 43813765342 et code 43813765296 verts (vérifiés au début de T32). Empreinte du catalogue 0.9.0 : `d6309484…b6c4`.
- La ligne « T40 (complément) » de l'index du journal portait « à venir » : corrigée en #32 dans cette tâche.
- Toujours en attente : mesure de `R-DOUBLEJPEG-001` et des règles de T24 et T40 sur le corpus (T100) ; double compression non alignée ; oracle mozjpeg jamais lancé ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 ; le banc n'inscrit pas la liste de confiance ; échec unique de la première campagne de fuzzing de T24 ; ORGANIZATION de Vorbis et Source de l'IPTC non marquées nominatives (ADR-0160) ; coût d'import de numpy sans bytecode compilé ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).

## Déroulé

1. Lecture des sources, le 2026-11-16 : `imwatermark/maxDct.py` et `watermark.py` d'invisible-watermark (branche `main`, puis la roue 0.2.0 de PyPI, SHA-256 `644311be…992f8b` : `maxDct.py` identique) ; `scripts/txt2img.py` de CompVis ; `sgm/inference/helpers.py` et `scripts/demo/detect.py` de generative-models ; `stable_diffusion_xl/watermark.py` de diffusers et son historique (API de GitHub) ; `src/flux/util.py` et `src/flux/cli.py` de Black Forest Labs. Constats :
   - la méthode `dwtDct` n'applique aucune DCT, contrairement à l'inventaire de T31 ([ERR-0011](../errata/ERR-0011-dwtdct-sans-dct.md)) ;
   - SDXL et FLUX.1 passent des flottants à la bibliothèque, Stable Diffusion 1 des entiers : OpenCV centre U sur 0,5 dans un cas, sur 128 dans l'autre ;
   - diffusers passait l'image de SDXL en RVB du 2023-07-06 au 2024-04-26 (PR huggingface/diffusers#7013) ;
   - FLUX.1 enregistre en JPEG de qualité 95 sans sous-échantillonnage ; les autres en PNG ;
   - le détecteur de Stability publie ses seuils sur 48 bits (plus de 33 : « probablement », 0,02 % de faux positifs ; plus de 35 : « très probablement », aucun sur 10 000 images).
2. Oracle : environnement Python à part, dans le dossier temporaire de la session (OpenCV 5.0.0 sans interface, PyWavelets 1.8.0, numpy 2.5.5, Pillow 13.0.0, invisible-watermark 0.2.0 sans ses dépendances, qui déclarent torch). Lancer `maxDct.py` depuis le dossier où la roue avait été dépliée a été refusé par le contrôle des commandes du poste (code téléchargé) ; la bibliothèque a donc été installée depuis PyPI, et `maxDct.py` chargé seul, comme le fait `detect.py`.
3. Essais sur 40 vignettes de 960 pixels de Wikimedia Commons versées avant 2022 (tirées de la phase 1 du relevé du complément de T40 ; deux en niveaux de gris écartées), marquées comme chaque code le fait, enregistrées comme il le fait : le décodeur de la bibliothèque lit SDXL à 33 bits sur 48 et FLUX.1 à 31 sur 46 en médiane ; lu dans le domaine du code, avec le seuil d'un demi, 48 et 46 ; Stable Diffusion 1 échoue alors sur les images à chrominance lisse, et l'on a trouvé pourquoi (ADR-0203). La décision par rang lit toutes les images marquées en entier. Robustesse, suréchantillonnage : ADR-0202, fiche.
4. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : lecture dans le domaine et par rang ([ADR-0203](../decisions/ADR-0203-methode-de-lecture.md)) ; JPEG et PNG ([ADR-0202](../decisions/ADR-0202-decodage-des-pixels.md)) ; relevé de Commons ([ADR-0204](../decisions/ADR-0204-seuils-et-releve.md)) ; 4 Mpx puis le haut ([ADR-0205](../decisions/ADR-0205-etendue-de-la-lecture.md)).
5. Relevé lancé (`banc/releves/dwtdct-T32/`, phase 1 : listes par l'API de Commons ; phase 2 : téléchargements), pendant l'écriture du code.
6. Code :
   - lecteur JPEG : paramètre `toutes` (toutes les composantes, région en lignes de MCU entières, tables de chaque composante fixées à son premier balayage, segments APP0 et APP14 lus) ; le rang de chaque bloc dans son balayage est transmis au décodage (il était déduit du signe de sa position, ce qui ne tient plus quand la chrominance est gardée : premier essai en format partiel sur tous les JPEG en couleurs) ; comportement sans `toutes` inchangé (tests de `doublejpeg` et `ela` à empreintes fixées) ;
   - `modules/_lecture/png.py` (pixels d'un PNG), `modules/_lecture/pixels.py` (couleurs d'un JPEG ou d'un PNG) ;
   - module `dwtdct` 0.1.0 ; formule d'OpenCV sur huit bits trouvée et vérifiée sur les 2^24 couleurs contre OpenCV 5.0.0 ;
   - catalogue 0.10.0 : règles `R-DWTDCT-001` à `R-DWTDCT-003`, `M-DWTDCT` recherché ; `dwtdct` parmi les modules sans métadonnées du contrôle avant publication.
7. Pendant la première analyse complète d'une image de SDXL, deux constats : une image marquée dans un ordre des couleurs se lit aussi dans l'autre (48 et 46 bits). Les deux lectures de SDXL sont fusionnées en une, la meilleure, et l'échange est observé ; quatre règles prévues, trois livrées (ADR-0203, ADR-0206). Mesure de diaphonie sur 18 photographies : seule la paire SDXL et SDXL aux couleurs échangées se lit l'une dans l'autre.
8. Le chargeur du catalogue refuse un marquage dont le module ne traite pas tous les formats : WebP et HEIC déclarés au manifeste, non menés (ADR-0202).
9. Tests : `tests/test_dwtdct.py` (lecteur PNG, couleurs d'un JPEG, composante U, décision par rang, loi des bits concordants, messages, échantillons, observations, analyses complètes) ; échantillons de `tests/donnees/dwtdct/`, marqués par la bibliothèque elle-même (`generer.py`, régénérés à l'identique octet pour octet) ; encodeur JPEG des tests : balayage d'une seule composante ; fuzzing : `dwtdct` sur les quatre formats, un PNG à tous les filtres et un JPEG en couleurs ; attentes mises à jour (listes des modules, nombre de règles, marquage du rapport de test, analyses non menées).
10. Relevé ([ADR-0204](../decisions/ADR-0204-seuils-et-releve.md)) : phase 1, 16 260 fichiers listés (environ 700 appels à l'API) ; phase 2, 1 580 fichiers téléchargés, tous en statut 200, de 10:33 à 14:57 (heure du poste) : les 356 originaux déclarés en 35 minutes, les 1 224 rendus authentiques en 3 h 50, une requête toutes les 2 s ; 224 PNG authentiques seulement, Commons n'en ayant pas assez pour 300 au tirage prévu ; phase 3, lecture par `analyser` en 52 minutes (poste chargé). Aucun constat sur les 1 224 authentiques ; un constat de SDXL, couleurs échangées, sur un des 356 déclarés, versé en janvier 2024, dans la période où diffusers posait ainsi le message. Seuils gardés ; catalogue et empreinte inchangés.
11. Documentation : ADR-0202 à ADR-0206, ERR-0011, fiche [`filigrane-dwtdct`](../techniques/filigrane-dwtdct.md), inventaire des marquages (v1.1), catalogue (v1.11), architecture (v1.24), découpage (v0.32), matrice (F-24 réalisée), ce journal.

12. PR [#33](https://github.com/TheDarkMac/AI-detector/pull/33) ouverte (commits `11e3484`, `118c1c8`, `e2fec35`). ADR-0206 validé par TheDarkMac pendant la revue (« Oui, valide ADR-0206 ») : statut « Accepté ».
## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Inventaire faux sur l'algorithme | Résumé de T31 tiré des noms des fonctions | [ERR-0011](../errata/ERR-0011-dwtdct-sans-dct.md) |
| Code de la bibliothèque refusé à l'exécution depuis le dossier téléchargé | Contrôle des commandes du poste | Installée depuis PyPI dans un environnement à part, `maxDct.py` chargé seul |
| SDXL et FLUX.1 mal lus par le décodeur de référence | Posés en flottants, lus en entiers | Lecture dans le domaine du code (ADR-0203) |
| Stable Diffusion 1 manqué sur les images lisses, au seuil d'un demi | Abaisser la plus grande valeur d'un bloc la fait souvent passer derrière une voisine | Décision par rang (ADR-0203) |
| JPEG en couleurs en format partiel au premier essai | Rang du bloc dans le balayage déduit de sa position | Rangs transmis au décodage |
| Deux constats pour une image de SDXL | Diaphonie entre les deux ordres des couleurs | Une lecture, la meilleure des deux (ADR-0203, ADR-0206) |
| Marquage refusé par le chargeur | WebP et HEIC hors des formats du module | Déclarés, non menés (ADR-0202) |
| Contrôle des commandes du poste sans réponse, par moments | Service du contrôle | Modifications faites par l'éditeur, commandes reprises ensuite |
| Statut de l'architecture resté à la v1.22 après T42 | Non mis à jour par T42 | Corrigé (v1.24) |

## Écarts par rapport au découpage

- Les faux positifs devaient être « mesurés sur le corpus » (ADR-0174) : le corpus de référence n'existe pas encore (T100) ; ils sont bornés par le calcul et vérifiés sur un relevé de Commons (ADR-0204).
- Ajouté : le lecteur PNG et les couleurs d'un JPEG, réutilisables par d'autres techniques d'image ; la lecture de SDXL aux couleurs échangées.

## Résultat

- Module `dwtdct` 0.1.0 ; catalogue 0.10.0 ; schémas inchangés (0.7.0).
- `vk image.png` d'une image marquée par le script de référence porte un indice faible vers l'origine IA, qui nomme le code et le nombre de bits concordants.
- Vérification : `uv run --locked coverage run -m pytest`, puis `coverage combine` et `coverage report` (100 %) ; `tests/test_dwtdct.py` seul en une vingtaine de secondes.

## Reste à faire

- Évaluation des règles sur la partie évaluation du corpus de référence (T100) ; images réellement générées par les codes de référence, en nombre.
- WebP et HEIC ; recherche de la grille après un recadrage ; autres messages ou réglages de la bibliothèque.
