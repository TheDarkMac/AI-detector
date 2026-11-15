# T41 — Double compression JPEG

- **Branche** : `tache/T41-double-compression`
- **Dates** : 2026-11-15
- **Exigences couvertes** : F-31 ; F-06 (indice vers la transformation) ; ES-19 (fuzzing du nouveau lecteur)
- **Décisions** : ADR-0185 à ADR-0188, acceptés ; ADR-0189 et ADR-0190, proposés dans la PR
- **Errata** : aucun

## Objectif

Détecter une double compression JPEG (F-31), et trancher le moyen de lire les coefficients DCT que l'architecture (§12) et ADR-0043 renvoyaient à T41.

## État initial

- PR [#29](https://github.com/TheDarkMac/AI-detector/pull/29) (T40). Commits : `ae09e5f` (tables connues), `2d7186e` (tests), `b55bc8e` (documentation), `ad77291` (ADR-0183 et ADR-0184 passés à « Accepté » après le « Oui, les deux » de TheDarkMac). CI sur `b55bc8e` : docs 43637554043 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code 43637554077 vert ; sur `ad77291` : docs 43670554993 et code 43670554999 verts.
- L'assistant a mergé la PR le 2026-11-15 à 03:22:27 UTC, après le « Oui, merge si vert » de TheDarkMac : commit de merge `796a0bc`. Lancements de push sur `796a0bc` : docs 43672071627 et code 43672071625 verts. Empreinte du catalogue 0.7.0 : `903f026a…0816`.
- La ligne « T40 » de l'index du journal portait « à venir » : corrigée en #29 dans cette tâche.
- Le complément de T40 (tables de Photoshop et d'appareils) est mené en parallèle, dans une autre session et un autre arbre de travail (`tache/T40-complement-photoshop-appareils`), sans commit à l'ouverture de T41.
- Toujours en attente : oracle mozjpeg jamais lancé (T40) ; T32 (lecteur dwtDct) ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 (RS-01, RS-02, ADR-0166) ; le banc n'inscrit pas la liste de confiance ; échec unique de la première campagne de fuzzing de T24, non reproduit ; ORGANIZATION de Vorbis et Source de l'IPTC non marquées nominatives (ADR-0160) ; messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).
- `detector` à jour avec `origin/detector` (`796a0bc`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : F-31, A-23, A-38, ADR-0043, ADR-0174, ADR-0180, architecture §9 et §12 ; lecteur de conteneurs (il s'arrête au premier SOS) ; modèle des règles (test `seuil`, `calibrage`) ; restrictions du processus de travail (modules importés avant Landlock, ADR-0079 ; environnement vidé, ADR-0065). Outils du poste : cjpeg, djpeg et jpegtran de libjpeg-turbo 2.1.5, ImageMagick 7.1.1-43, numpy 2.2.4 et Pillow 11.1 du Python du système (prototype seulement).
2. Prototype, dans le dossier temporaire de la session :
   - décodage de Huffman séquentiel en Python pur, validé contre djpeg (`-dct float`, niveaux de gris : un niveau d'écart au plus, sur 0,5 % des pixels) ; 2,7 s pour 2 Mpx, puis 0,4 s une fois la table de lecture construite par tranches ;
   - estimation du premier pas par calibrage, sur 36 images : trois images sans perte livrées avec le système (écran de démarrage de GIMP, avatar de Plasma, fond de GRUB), compressées une fois (qualités 75 et 90) ou deux fois (50 à 95 puis 75 et 90) par cjpeg ; puis sur une photographie (`grace_hopper.jpg` de matplotlib, qualité 80) réenregistrée de 70 à 95, recadrée de 3 et 5 pixels, réduite de moitié ; puis sur les 11 JPEG de `/usr/share` (aucune trace) ;
   - premier critère « simple compression = pas égal à celui du fichier » : jusqu'à 2 traces fortes sur une simple compression d'image de synthèse ; corrigé en prenant le meilleur pas qui divise celui du fichier (une telle double quantification ne laisse aucune trace) ;
   - import de numpy dans un interpréteur lancé comme le processus de travail : 0,45 s sans bytecode (uv n'en compile pas), 0,23 à 0,26 s avec ; chargement de tous les modules de 0,44–0,53 s à 0,55–0,64 s.
3. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes retenues : lecture des coefficients ([ADR-0185](../decisions/ADR-0185-lecture-des-coefficients-dct.md)) ; méthode ([ADR-0186](../decisions/ADR-0186-methode-de-detection.md)) ; JPEG lus ([ADR-0187](../decisions/ADR-0187-jpeg-lus.md)) ; constat ([ADR-0188](../decisions/ADR-0188-constat-de-double-compression.md)). La première comprenait l'installation de uv depuis PyPI et le téléchargement de numpy. Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0189](../decisions/ADR-0189-calcul-en-entiers-et-region.md) (calcul en entiers, région, paramètres, forme de la règle) et [ADR-0190](../decisions/ADR-0190-module-et-versions-de-t41.md) (module à part, un fil pour OpenBLAS, versions).
4. Branche `tache/T41-double-compression` créée depuis `detector` à jour (`796a0bc`). uv 0.13.5 (celui de la CI) installé dans un environnement du dossier temporaire ; `uv add numpy` : numpy 2.5.4 au verrou, critères d'ADR-0043 vérifiés (ADR-0185).
5. Source primaire lue : Lukáš et Fridrich, DFRWS 2003 (PDF de l'université de Binghamton, texte extrait par `pdftotext`). Leur méthode principale est un classifieur à réseau de neurones (§4.3) ; c'est leur « test de compatibilité » (§4.1) que reprend le module, avec les écarts dits par ADR-0186.
6. Décodage entropique `modules/_lecture/jpeg.py` : segments jusqu'à EOI, SOF0 à SOF2, DHT, DQT, DRI, SOS ; balayages séquentiels et progressifs (continu premier et raffiné, alternatif premier et raffiné) ; région et bornes d'ADR-0189 ; balayages des autres composantes sautés. Vérifié contre les transcodages sans perte de jpegtran (progressif, redémarrages, Huffman optimisé) en 4:2:0, 4:2:2, 4:4:4 et niveaux de gris.
7. Module `doublejpeg` 0.1.0 : luminance recalculée par une IDCT en entiers, calibrage, histogrammes, pas antérieurs, qualités de libjpeg ; `numpy` admis par le schéma des manifestes, sa version au rapport ; `OPENBLAS_NUM_THREADS=1` dans l'environnement du processus de travail.
8. Catalogue 0.8.0 : `R-DOUBLEJPEG-001` (règle à seuil, calibrage manuel décrit) ; description de l'en-tête complétée (947 caractères) ; empreinte `435b199c…cde9` au registre.
9. Essais sur le poste par `vk` : isolation complète ; sur la photographie réenregistrée à 95, deux indices faibles vers la transformation (`R-IMAGE-004` et `R-DOUBLEJPEG-001`), 9 traces sur 9, qualité antérieure 80 ; 1,7 s de plus pour une image de 15 Mpx en qualité 98 progressive ; 9 s pour un bruit aléatoire de 12 Mpx en qualité 100, cas défavorable.
10. Tests :
    - `tests/encodeur_jpeg.py` : encodeur séquentiel des tests (codes canoniques choisis, entrelacement, redémarrages) ;
    - `tests/donnees/doublejpeg/` : huit JPEG de 384 sur 256 pixels écrits par `generer.sh` (cjpeg, djpeg, jpegtran sur une fractale d'ImageMagick), 132 Kio ;
    - `tests/test_double_compression.py` : aller-retour avec l'encodeur (Hypothesis) ; mêmes coefficients en séquentiel, progressif et à redémarrages ; oracles jpegtran (options et script de balayages) et djpeg (luminance), ignorés s'ils manquent ; balayages progressifs écrits bit à bit (séries de fins de bande, seize zéros, raffinement, codes invalides, données épuisées) ; 34 JPEG malformés ou non lus ; région et bornes ; estimation, qualités, règle, analyse complète ; un fil pour OpenBLAS ;
    - fuzzing : `doublejpeg` parmi les modules du JPEG, deux JPEG décodables parmi les échantillons mutés ;
    - tests adaptés : contrôle avant publication (`test_controle_publication.py`, ADR-0190) ; liste des modules (`test_manifestes.py`, `test_travail.py`, `test_cli.py`), versions des bibliothèques (`test_travail.py`, `test_orchestration.py`), couverture d'une analyse et non menée de l'échantillon JPEG sans trame (`test_soumission.py`), compte des règles (`test_incoherences.py`), règles de T24 (`test_transfert.py`).
11. Documentation : fiche `double-compression-jpeg` et index des fiches ; limite de la fiche `structure-image` ; architecture v1.22 (§3, §4, §9, §12) ; découpage v0.29 (T41, T32) ; guide du catalogue v1.9 ; matrice régénérée (F-06, F-31) ; renvois dans ADR-0043, ADR-0065, ADR-0158 et ADR-0174 ; index des ADR et du journal.

## Vérification

- Ruff (format et analyse) et mypy sans remarque ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans erreur ; matrice régénérée ; `vk --catalogue src/voight_kampff/donnees/catalogue --regles` : 86 règles, empreinte `435b199c…cde9`.
- `tests/test_double_compression.py` seul, sous coverage : 106 tests verts ; décodeur et module couverts à 100 %, et encore à 100 % sans les oracles jpegtran et djpeg (98 tests), comme dans une CI qui ne les aurait pas.
- Premier passage de la suite complète, mesurée par coverage comme en CI : 1 échec sur 2 127 (voir « Problèmes rencontrés »). Second passage, après correction : 2 127 tests verts, 4 ignorés (lanceur de l'environnement virtuel ; trois oracles de mozjpeg, faute de son cjpeg), en 6 min 23 s ; couverture de 100 %.
- Campagne de fuzzing ponctuelle du module `doublejpeg`, hors du dépôt : 5 000 JPEG décodables mutés (les huit échantillons et un JPEG entrelacé à redémarrages), aucune exception, chaque message conforme au schéma, en 2 min 15 s.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| uv absent du poste | Jamais installé globalement | uv 0.13.5 installé depuis PyPI dans un environnement du dossier temporaire, avec l'accord de TheDarkMac (question 1) |
| Import de numpy deux fois plus lent dans le processus de travail que mesuré d'abord | uv installe sans compiler le bytecode, et le processus de travail est lancé avec `-B` | Bytecode compilé dans le `.venv` du poste pour mesurer ; les deux chiffres sont consignés (ADR-0185) |
| Première version du décodeur lente (2,7 s pour 2 Mpx) | Tables de lecture de 65 536 entrées remplies entrée par entrée | Remplies par tranches : 0,4 s |
| Un JPEG 4:2:0 de 17 pixels de haut perdait sa dernière ligne de blocs (trouvé par Hypothesis) | La région était arrondie à un nombre entier de lignes de MCU, même quand l'image y tenait | Arrondi retiré : une ligne de MCU est décodée entière, les lignes en trop oubliées |
| Rechargement du tampon jamais exécuté dans le raffinement progressif | Code mort : la boucle des corrections laisse toujours au moins 31 bits | Retiré, l'invariant écrit en commentaire |
| Script de balayages refusé par jpegtran | Erreur de l'assistant : un raffinement descend d'un bit à la fois (Ah = Al + 1) | Script corrigé |
| Trois attentes fausses dans un premier jet des tests | Erreurs de l'assistant : différences du continu cumulées par bloc ; qualités 59 et 60 égales aux quatre premiers rangs ; nom de l'attribut des versions de l'analyse | Attentes corrigées |
| La fiche `structure-image` a été modifiée pendant le passage de la suite complète | Erreur de méthode de l'assistant | Seul le corps a changé, pas l'en-tête que lisent les tests ; sans effet sur ce passage |
| Premier passage de la suite complète : 1 échec, `test_publication_sans_marque_ni_partie_non_lue` | Un JPEG sans données d'image rend `doublejpeg` non mené, et le contrôle avant publication se disait alors incomplet (ADR-0158), alors que le module ne lit aucune métadonnée | Les analyses non menées de `doublejpeg` sont exclues, comme celles des techniques hors V1 (ADR-0190, proposé) ; test adapté |
| Statuts du découpage (v0.26), de l'architecture (v1.19) et du guide du catalogue (v1.7) en retard | Non mis à jour par les tâches précédentes, qui ne complétaient que la liste des versions | Corrigés, et dits à l'historique de chaque document |

## Écarts par rapport au découpage

- **Ajouté** : le décodage entropique, partagé avec T32 ; un fil pour OpenBLAS dans l'environnement du processus de travail.
- **Changé** : la qualité antérieure de libjpeg est une observation, pas un paramètre de la phrase du constat (ADR-0188).
- **Non fait** : double compression non alignée ; règle non évaluée, faute de corpus (T100).

## Résultat

- La luminance d'un JPEG séquentiel ou progressif est examinée sur ses 9 premières fréquences ; le pas antérieur de chaque fréquence qui porte une trace, et les qualités de libjpeg compatibles, sont au rapport.
- Au moins 4 traces donnent un indice faible vers la transformation (`R-DOUBLEJPEG-001`), avec ses limites ; le résumé recommande alors d'obtenir l'original.
- Les coefficients DCT d'un JPEG se lisent par un décodeur du projet, en Python pur, éprouvé et soumis au fuzzing.

## Reste à faire

- PR : validation d'ADR-0189 et d'ADR-0190 par TheDarkMac.
- T100 : mesurer la règle et recalibrer ses seuils ; T32 : décoder les autres composantes et convertir les couleurs.
- Coordonner avec le complément de T40 : version du catalogue et numéros d'ADR (ADR-0190).
- Toujours en attente : voir « État initial ».
