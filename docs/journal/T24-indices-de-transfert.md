# T24 — Indices de transfert par messagerie ou capture d'écran

- **Branche** : `tache/T24-indices-de-transfert`
- **Dates** : 2026-11-13 au 2026-11-14
- **Exigences couvertes** : F-06 (réalisée), F-30 (partielle : tables de libjpeg), F-26, NF-06, ES-19
- **Décisions** : ADR-0153 à ADR-0157, tous acceptés
- **Errata** : aucun

## Objectif

Signaler les indices de transfert par messagerie ou de capture d'écran (recompression, dimensions typiques, métadonnées absentes), qui réduisent la portée des analyses, et recommander d'obtenir l'original (F-06). A-32 demandait la liste des dimensions typiques dans le catalogue ; A-34 et ADR-0151 laissaient à T24 l'usage de l'absence de métadonnées comme indice de transfert, avec ses propres règles et sa propre direction.

## État initial

- PR [#24](https://github.com/TheDarkMac/AI-detector/pull/24) (T23). Sur `2995b22` : docs 43445583584 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129), code 43445583589 vert. ADR-0148, ADR-0150 et ADR-0152 validés par TheDarkMac pendant la revue (« Yes, all three », 2026-11-13), passés à « Accepté » (`0ae150b`) : docs 43447082966 et code 43447082928 verts.
- L'assistant a mergé la PR le 2026-11-13 à 18:58:51 UTC, après le « Merge it » de TheDarkMac : commit de merge `baba539` « Merge: T23 — Incohérences internes (#24) », à l'adresse noreply (ADR-0007). Une première commande `gh pr merge` a échoué : `--match-head-commit` demande l'empreinte entière du commit. Lancements de push sur `baba539` verts : docs 43487801173, code 43487800864.
- La ligne « T23 » de l'index du journal portait « à venir » : corrigée en #24 dans cette tâche.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (option B d'ADR-0129), qui demande un changement des réglages du dépôt par TheDarkMac.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`baba539`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : F-06, A-32, A-34, ADR-0055, ADR-0146, ADR-0149 à ADR-0151 ; lecteur de conteneurs, modules `exif`, `xmp`, `iptc`, `textepng`, résumé du rapport. Constats : les signatures de capture et de plateforme se lisent sur les observations existantes ; aucun module n'observe les dimensions réelles ni les tables de quantification ; une règle ne compare que les observations d'un module ; le résumé ne porte aucune recommandation.
2. Recherche des sources, en ligne, le 2026-11-13 et le 2026-11-14 : tailles des plateformes (Giudice et al., arXiv:1610.06347, 2016, tableau III ; Bertini et al., arXiv:2006.03903, 2020, tableau 1, textes extraits par `pdftotext`) ; marque FBMD de Facebook (IPTC, 22 juillet 2019) ; `tEXt::Software` de gnome-screenshot (commit `4e03093f`, archive `commits-list` de GNOME) ; `UserComment` « Screenshot » d'Apple (témoignages de la communauté d'Apple, aucune documentation d'Apple trouvée). Aucune taille n'est documentée par un éditeur ; les deux études ne concordent pas pour Telegram (2 560 puis 1 280).
3. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation :
   - familles d'indices : les trois recommandées (signatures documentées, « Screenshot » d'Apple, dimensions typiques) et la recompression, que l'assistant recommandait de laisser à T40 ([ADR-0153](../decisions/ADR-0153-indices-de-transfert-retenus.md)) ;
   - nature : indice faible vers la transformation ([ADR-0155](../decisions/ADR-0155-nature-d-un-indice-de-transfert.md)) ;
   - recommandation d'obtenir l'original : une phrase du résumé ([ADR-0156](../decisions/ADR-0156-recommandation-d-obtenir-l-original.md)) ;
   - tailles : liste sourcée et datée (ADR-0153).

   Les autres choix, faits par l'assistant, ont été soumis dans la PR et validés par TheDarkMac pendant sa revue (« Oui, les deux », 2026-11-14) : [ADR-0154](../decisions/ADR-0154-module-image.md) (module `image`, forme des règles, écartés), [ADR-0157](../decisions/ADR-0157-versions-de-t24.md) (versions).
4. Essai préalable de la reconnaissance des tables de libjpeg, par un script temporaire hors du dépôt : chaque qualité de 1 à 100 donne une table de luminance différente ; les JPEG d'ImageMagick 7.1.1-43 aux qualités 5, 50, 75, 92, 100 et en niveaux de gris à 80 sont reconnus à leur qualité ; celui de ffmpeg 7.1.5 (tables propres de l'encodeur MJPEG) ne l'est pas.
5. Branche `tache/T24-indices-de-transfert` créée depuis `detector` à jour (`baba539`).
6. Lecteur de conteneurs : natures `TRAME` (SOF, `IHDR`, `VP8X`, `"VP8 "`, `VP8L`) et `QUANTIFICATION` (DQT), ensemble `STRUCTURE`.
7. Module `image` 0.1.0 : dimensions du premier en-tête d'image, compte des blocs de métadonnées si le parcours est complet, tables en vigueur au premier balayage et qualité libjpeg ; manifeste, direction « transformation ».
8. Catalogue 0.4.0 : huit règles, indices faibles vers la transformation (`R-EXIF-014`, `R-XMP-013`, `R-IPTC-003`, `R-TEXTEPNG-007`, `R-IMAGE-001` à `R-IMAGE-004`), écrites par un script temporaire hors du dépôt, puis relues ; description de l'en-tête ; manifestes de `exif` (0.3.0), `iptc` (0.3.0), `textepng` (0.3.0), `xmp` (0.5.0) ; entrée au registre `versions.toml`.
9. Rapport : clé `resume.transformation` de `textes.toml`, ajoutée une fois au résumé si un constat pointe vers « transformation ».
10. Tests :
    - `tests/test_transfert.py` : chaque règle de T24 déclenchée par un échantillon construit, avec ses paramètres, et éprouvée ; règles toutes indices faibles, fondement selon la famille, une seule liste de côtés ; douze échantillons sans constat (commentaire voisin, casse, FBMD pas au début, logiciel ordinaire, EXIF présent, PNG, autre taille, côté court en paysage et en portrait, libjpeg avec XMP, chrominance d'une autre qualité, trois tables) ; parcours interrompu sans compte des métadonnées ; observations du module sur JPEG, JPEG progressif à hauteur nulle, PNG, WebP `VP8X`, `"VP8 "`, `VP8L` ; en-têtes illisibles non menés ; tables de seize bits et redéfinition ; table invalide ; une qualité par table ; oracle ImageMagick (cinq qualités) et ffmpeg, ignorés si l'outil manque ; trois analyses complètes (JPEG de messagerie avec la recommandation une fois, JPEG sans indice ni recommandation, capture de gnome-screenshot) ;
    - échantillons communs dans `tests/metadonnees.py` (tables de l'annexe K, DQT, SOF, JPEG, `"VP8 "`, `VP8L`, WebP sans `VP8X`) ;
    - tests adaptés : `test_signatures.py` ne vise que les indices de T22, hors transformation ; `test_incoherences.py` compte les huit règles de T24 ; `test_manifestes.py` connaît le module `image` et la direction des quatre modules ; `test_soumission.py`, `test_cli.py` et `test_travail.py` suivent la liste et les versions des modules ;
    - fuzzing (ES-19) : module `image` ajouté aux formats JPEG, PNG, WebP, avec trois échantillons de structure.
11. Fiches : `structure-image` créée ; `exif`, `xmp`, `iptc`, `texte-png` (version, direction, règle de T24, hypothèse « transformation banale », taux d'erreur, historique) ; index des fiches.
12. Vérification locale : Ruff (format et analyse) et mypy sans remarque ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans erreur ; matrice régénérée (F-06 réalisée, F-30 partielle). Suite complète : première passe, trois échecs (listes des modules, voir plus bas) ; seconde passe, mesurée par coverage comme en CI, 1 809 tests verts et un ignoré (lanceur de l'environnement virtuel), couverture de 99 % ; deux échantillons ajoutés ensuite, couverture de 100 % du lecteur de conteneurs et du module `image` sur `test_transfert.py`, `test_manifestes.py` et `test_metadonnees.py` (195 tests verts), les autres fichiers déjà à 100 %. Banc sur le corpus d'essai, sans réseau (`unshare -rn`) : code 1 et le seul écart attendu, la cible par fichier non établie sur quatre authentiques (ADR-0105) ; aucune des huit règles de T24 ne se déclenche sur les fichiers authentiques. Essai sur le poste : un JPEG d'ImageMagick de 1 600 × 1 200, sans métadonnées, à la qualité 80, donne `R-IMAGE-001` et `R-IMAGE-004`, trois informations neutres d'absence, la recommandation une fois au résumé du terminal et du HTML, et la qualité 80 lue. Fuzzing (ES-19), code du lecteur de conteneurs changé : une première campagne (`VK_FUZZING=campagne`, échantillons mutés puis octets quelconques, 25 min au plus) a signalé un échec du test des échantillons mutés, sans exemple conservé, puis a été coupée par le délai ; une seconde campagne du même test est passée ; deux recherches ciblées hors du dépôt, sur le même générateur d'échantillons mutés avec affichage de l'exemple fautif, sont passées : 60 000 exemples sur les formats d'image (modules `exif`, `xmp`, `iptc`, `textepng`, `image`), 40 000 sur tous les formats. L'échec n'est pas reproduit et sa cause reste inconnue (voir « Reste à faire »).
13. Documentation : ADR-0153 à ADR-0157 ; renvois dans ADR-0055, ADR-0150, ADR-0151 ; guide du catalogue v1.5 ; architecture v1.17 ; analyse critique v1.4 (A-32, A-34) ; découpage v0.24 (T24, T40) ; matrice (F-06 réalisée, F-30 partielle) ; index des ADR, du journal et des fiches.
14. PR [#25](https://github.com/TheDarkMac/AI-detector/pull/25) ouverte ; ADR-0154 et ADR-0157 validés par TheDarkMac pendant la revue, le 2026-11-14 (« Oui, les deux ») : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| WebFetch ne lisait pas les deux articles d'arXiv | PDF compressés | Fichiers téléchargés par l'outil, texte extrait par `pdftotext` dans le dossier temporaire |
| Ruff refusait le signe × et le signe − dans le code et les tests | Règles RUF001 à RUF003 (caractères ambigus) | « 8 sur 8 », « 200 - 2q », « largeur - 1 » |
| Premier jet de `test_transfert.py` maladroit : un paramètre factice, une constante du rapport inexistante, un test sans objet | Erreurs de l'assistant | Corrigés avant le premier lancement |
| Une limite de `R-IPTC-003` disait la valeur qui suit FBMD « ni lue ni rapportée » | Erreur de l'assistant : le module observe le jeu, et le rapport l'affiche parmi les observations | Limite réécrite avant tout commit : la valeur n'est pas interprétée |
| `test_signatures.py` comptait tous les indices du catalogue comme règles de T22 | Hypothèse de T22 : les seuls indices étaient les siens | Règles de T22 : indices hors direction « transformation » |
| Trois échecs à la première suite complète : `test_cli.py` (deux) et `test_travail.py` | Listes des modules livrés écrites en dur, sans `image` ni les nouvelles versions | Listes mises à jour |
| La description des règles de dimensions omettait Google+ (2 048) et Instagram (1 080) du tableau 1 de Bertini et al. | Lecture incomplète du tableau par l'assistant, vue en écrivant ADR-0153 | Descriptions corrigées avant tout commit ; empreinte recalculée |
| Couverture à 99 % : une ligne (`VP8X` trop court) et une branche du lecteur de conteneurs (bloc WebP d'une autre nature) | Depuis que `VP8X` est un bloc de structure, plus aucun échantillon WebP ne portait de bloc ignoré | Deux échantillons ajoutés, dont un profil ICC non compté parmi les métadonnées |
| Un échec de la première campagne de fuzzing, non reproduit | Inconnue : le profil « campagne » ne garde pas les exemples (`database=None`) et la sortie a été coupée par le délai avant le résumé | Trois recherches ultérieures sans échec ; cause à rechercher par une campagne qui affiche l'exemple |
| Le lint Markdown refusait `` `VP8 ` `` | MD038 : espace à la fin d'un code en ligne | Écrit `"VP8 "` |

## Écarts par rapport au découpage

- **Ajouté** : module `image` et blocs de structure du lecteur de conteneurs ; tables de libjpeg (partie de T40, F-30) ; recommandation au résumé.
- **Écarté** (ADR-0154) : HEIC ; autres outils de capture et autres marques de plateformes, sans source ; nom du fichier ; dimensions d'écrans ; qualité estimée de n'importe quelles tables.
- **Non fait** : aucune règle n'est évaluée, faute de corpus de référence (T100) ; la double compression reste à T41.

## Résultat

- Une capture d'écran de macOS, d'iOS ou de gnome-screenshot qui garde sa marque, une image qui porte la marque de Facebook, un JPEG sans métadonnées à un côté long de messagerie ou encodé aux tables de libjpeg portent au rapport un indice faible vers la transformation, avec sa règle, ses limites et ses sources.
- Le résumé dit alors, une fois, que la portée des autres analyses est réduite et recommande d'obtenir l'original.
- Les dimensions réelles d'une image JPEG, PNG ou WebP et la qualité libjpeg d'un JPEG sont observées.
- `vk --regles` liste les soixante-dix règles du catalogue 0.4.0 ; son empreinte est au registre.
- F-06 est réalisée ; F-30 est partielle.

## Reste à faire

- T25 : contrôle avant publication ; la valeur qui suit FBMD, identifiant constant d'une image publiée, est à examiner comme marque identifiante.
- T40 : comparaison des tables à d'autres tables connues ; T41 : double compression.
- T100 : mesure des règles de T22, T23 et T24 sur le corpus de référence.
- Fuzzing : l'échec unique de la première campagne de T24 n'est pas reproduit ; une campagne qui affiche l'exemple fautif (`print_blob`) le recherchera, et le profil « campagne » pourrait l'afficher de lui-même.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande ; contrôle des ADR en tâche séparée (ADR-0129, option B).
