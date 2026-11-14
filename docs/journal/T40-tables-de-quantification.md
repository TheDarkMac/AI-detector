# T40 — Tables de quantification JPEG comparées à des tables connues

- **Branche** : `tache/T40-tables-de-quantification`
- **Dates** : 2026-11-14
- **Exigences couvertes** : F-30 en partie (logiciels : libjpeg, mozjpeg, ffmpeg ; Photoshop et appareils au complément), F-06, F-26
- **Décisions** : ADR-0180 à ADR-0184 ; ADR-0180 à ADR-0182 acceptés, ADR-0183 et ADR-0184 proposés
- **Errata** : aucun

## Objectif

Comparer les tables de quantification d'un JPEG à des tables connues (F-30), au-delà des tables de libjpeg reconnues depuis T24 (ADR-0153), et permettre au catalogue d'en nommer d'autres sans nouvelle version de l'outil (F-26, A-32).

## État initial

- PR [#28](https://github.com/TheDarkMac/AI-detector/pull/28) (T31). Commits : `6df15c8` (marquages au catalogue), `ec0ca18` (tests), `515c3b0` (documentation), `76d2089` (ADR-0175, ADR-0178, ADR-0179 passés à « Accepté », T32 en V1, après le « Yes, all four » de TheDarkMac). CI sur `515c3b0` : docs 43593153482 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code annulé par le lancement suivant ; sur `76d2089` : docs et code verts.
- L'assistant a mergé la PR le 2026-11-14 à 12:16:34 UTC, après le « Yes, merge when green » de TheDarkMac : commit de merge `5f711c6`, à l'adresse noreply (ADR-0007). Lancements de push sur `5f711c6` : docs 43594003934 et code 43594003930 verts. Empreinte du catalogue 0.6.0 : `7725a960…3601`.
- La ligne « T31 » de l'index du journal portait « à venir » : corrigée en #28 dans cette tâche.
- Toujours en attente : T32 (lecteur dwtDct) ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA non examinés un par un ; complément de T30 (RS-01, RS-02, ADR-0166) ; le banc n'inscrit pas la liste de confiance ; échec unique de la première campagne de fuzzing de T24, non reproduit ; ORGANIZATION de Vorbis et Source de l'IPTC non marquées nominatives (ADR-0160) ; messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).
- `detector` à jour avec `origin/detector` (`5f711c6`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : F-30, F-31, A-23, A-38 ; ADR-0153 à ADR-0155 ; module `image`, ses règles et ses tests ; outils du poste (cjpeg de libjpeg-turbo 2.1.5, ffmpeg 7.1.5, ImageMagick 7.1.1-43, Pillow 11.1 du système, GIMP ; ni mozjpeg ni cmake).
2. Sources primaires, lues le 2026-11-14 et gardées dans le dossier temporaire de la session :
   - mozjpeg : `jcparam.c`, `cjpeg.c`, `rdswitch.c`, `jcext.c`, `LICENSE.md` (branche principale, `08265790`) ; `jcparam.c` de la version 4.1.1, dernière publiée (2022-08-15) : tables identiques ; jeu 3 par défaut (`quant_tbl_master_idx`, profil `JCP_MAX_COMPRESSION`) ;
   - libjpeg-turbo : `src/jcparam.c` (branche principale, `3ef3367e`) ;
   - FFmpeg 7.1 : `mjpegenc_common.c`, `mjpegenc.c`, `mpegvideo_enc.c`, `mpeg12data.c`, `mpegvideodata.c` ;
   - Farid, TR2006-583 (Dartmouth, 2006), texte extrait par `pdftotext` : 13 niveaux de Photoshop et 204 appareils relevés, valeurs non publiées ;
   - Kornblum (DFRWS 2008) : page et PDF refusés (HTTP 403), non lus ; JPEGsnoop : licence GPL-2.0 (API de GitHub) ; `JpegPresets.py` de Pillow : « équivalents aux réglages de Photoshop », sans source.
3. Essais préalables, par des scripts temporaires hors du dépôt : tables écrites par ffmpeg aux qscale 2, 5 et 31, par `cjpeg -quality 90,70` et `-quality 10` (seize bits), par Pillow ; formule de ffmpeg retrouvée sur les valeurs ; collisions entre les neuf jeux de mozjpeg (qualités 1 à 100, huit et seize bits) et les 31 qscale de ffmpeg : hors du jeu plat, seules les tables dégénérées (toutes à 1, toutes à 255) sont partagées.
4. Trois questions à TheDarkMac, en un lot, chacune avec une recommandation :
   - tables connues : les quatre familles proposées, y compris libjpeg à deux qualités et Photoshop et appareils, que l'assistant déconseillait ([ADR-0180](../decisions/ADR-0180-tables-connues-de-t40.md)) ;
   - point d'extension : empreinte des tables ([ADR-0181](../decisions/ADR-0181-empreinte-des-tables.md)) ;
   - règles : comme R-IMAGE-004 ([ADR-0182](../decisions/ADR-0182-regles-des-tables-connues.md)).

   Puis une quatrième, faute de source pour Photoshop et les appareils : un complément de T40, sur sa propre branche et sa propre PR, qui relèvera les tables sur des fichiers publics de provenance établie (ADR-0180). Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0183](../decisions/ADR-0183-observations-des-tables-connues.md) (noms des observations, ordre, réglages reconnus) et [ADR-0184](../decisions/ADR-0184-versions-de-t40.md) (versions).
5. Branche `tache/T40-tables-de-quantification` créée depuis `detector` à jour (`5f711c6`).
6. Module `image` 0.2.0 : jeux 2 à 8 de mozjpeg, matrice de MPEG-1 de FFmpeg ; reconnaissance de libjpeg à deux qualités, de mozjpeg et de ffmpeg, dans un ordre fixé ; empreinte des tables. Les littéraux de mozjpeg ont été produits par un script qui lit `jcparam.c` de la version 4.1.1.
7. Catalogue 0.7.0 : `R-IMAGE-005` à `R-IMAGE-007` ; `R-IMAGE-004` en version 2 (limite qui annonçait mozjpeg non reconnu) ; description de l'en-tête réécrite, plus courte ; empreinte au registre.
8. Tests :
   - `tests/test_tables_connues.py` : chaque règle de T40 déclenchée et éprouvée, nature des règles, aucun constat avec des métadonnées ; encodeur reconnu sur onze jeux de tables (dont seize bits, niveaux de gris, matrice dupliquée, tables dégénérées attribuées à libjpeg) et non reconnu sur dix ; unicité de chaque couple de mozjpeg, de chaque qscale de ffmpeg, de chaque qualité de chrominance au-delà de 3 ; écriture canonique de l'empreinte ; oracles cjpeg de libjpeg-turbo, cjpeg de mozjpeg et ffmpeg, ignorés si l'outil manque ; analyse complète d'une image écrite par ffmpeg ;
   - tests adaptés : `test_transfert.py` (règles de T24 sans celles de T40, empreinte retirée de la comparaison des observations), `test_incoherences.py` (compte des règles), `test_soumission.py` et `test_cli.py` (version du module).
9. Documentation : fiche `structure-image` (version 0.2.0, principe, sorties, règles, taux d'erreur, limites) et index des fiches ; guide du catalogue v1.8 (exemple d'une règle par empreinte) ; architecture v1.21 (§12) ; découpage v0.28 (T40, complément de T40, T32) ; matrice régénérée (F-30) ; index des ADR et du journal.

## Vérification

- Ruff (format et analyse) et mypy sans remarque ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans erreur ; matrice régénérée ; `vk --catalogue src/voight_kampff/donnees/catalogue --regles` : 85 règles, empreinte `903f026a…0816`.
- Premier passage partiel (catalogue, CLI, soumission, manifestes, signatures, incohérences, rapport, règles) : 2 échecs sur 457, deux attentes à mettre à jour (voir « Problèmes rencontrés »).
- Suite complète, mesurée par coverage comme en CI : 2 021 tests verts, 4 ignorés (lanceur de l'environnement virtuel ; trois oracles de mozjpeg, faute de cjpeg de mozjpeg), en 7 min 50 s ; couverture de 100 %. Le fuzzing ordinaire du module `image` (ES-19) en fait partie ; aucune campagne longue : le lecteur de conteneurs ne change pas, seules les tables déjà lues sont comparées.
- Essai sur le poste : une image de 320 × 240 extraite par ffmpeg (`-q:v 3`) donne `R-IMAGE-007` au qscale 3, la recommandation une fois au résumé du terminal et la phrase dans le HTML, avec `image.jpeg.empreinte_tables` parmi les observations ; un JPEG de `cjpeg -quality 90,70` donne un indice faible vers la transformation.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| La compilation de mozjpeg 4.1.1 dans le dossier temporaire, pour servir d'oracle, a été refusée | Le mode automatique de l'outil d'assistance refuse d'exécuter du code téléchargé | Tables vérifiées contre le texte de `jcparam.c` seulement ; test d'oracle écrit, ignoré sans cjpeg de mozjpeg |
| Article de Kornblum (DFRWS 2008) illisible | HTTP 403 sur le site de DFRWS et sur CORE | Non cité comme source de valeurs ; Farid 2006 suffit à établir qu'aucune valeur n'est publiée |
| Un premier jet du test d'unicité de mozjpeg attendait des tables de huit bits à la qualité 50 pour tous les jeux | Erreur de l'assistant : les jeux 3 et 5 ont des valeurs au-delà de 255 (311, 418), que libjpeg écrit en seize bits | Précision choisie selon la table |
| Ruff refusait l'appel de `cjpeg` par son nom | S607 : exécutable sans chemin complet | Chemin donné par `shutil.which` |
| Deux attentes en échec à un premier passage partiel : version du module dans la fiche, compte des règles du catalogue | Écrits en dur | Fiche en 0.2.0 ; compte des règles de T40 ajouté |
| Description du catalogue proche de la limite de 1 024 caractères (993 en 0.6.0) | Une phrase par tâche, ajoutée à chaque version | Description réécrite, 820 caractères |

## Écarts par rapport au découpage

- **Ajouté** : empreinte des tables (point d'extension, ADR-0181) ; libjpeg à deux qualités ; complément de T40.
- **Reporté** : tables de Photoshop et d'appareils, au complément de T40 ; comparaison avec l'appareil déclaré dans l'EXIF, qui demande une règle sur deux modules (architecture, §12).
- **Non fait** : aucune règle n'est évaluée, faute de corpus de référence (T100) ; aucun oracle mozjpeg n'a tourné.

## Résultat

- Les tables d'un JPEG sont reconnues comme celles de libjpeg (à une ou deux qualités), de mozjpeg (jeu et qualité) ou de l'encodeur MJPEG de ffmpeg (qscale) ; leur empreinte est au rapport pour tout JPEG.
- Un JPEG sans métadonnées encodé par l'un de ces encodeurs porte un indice faible vers la transformation, avec sa règle et ses limites ; le résumé recommande alors d'obtenir l'original.
- Une règle du catalogue peut nommer des tables fixes par leur empreinte, sans nouvelle version de l'outil.
- F-30 reste partielle : Photoshop et les appareils au complément.

## Reste à faire

- Complément de T40 : tables de Photoshop et d'appareils, relevées sur des fichiers publics de provenance établie, au catalogue par empreinte.
- Oracle mozjpeg : lancer `tests/test_tables_connues.py` sur un poste où le cjpeg de mozjpeg est installé.
- T41 : double compression ; T100 : mesure des règles de T24 et T40.
- Toujours en attente : voir « État initial ».
