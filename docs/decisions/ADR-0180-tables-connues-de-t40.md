# ADR-0180 — Tables connues de T40 : mozjpeg, ffmpeg, libjpeg à deux qualités ; Photoshop et appareils dans un complément

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (deux questions successives)
- **Tâche** : T40
- **Exigences liées** : F-30, F-06, F-26 ; A-32 ; ADR-0043, ADR-0153, ADR-0154

## Contexte

F-30 demande de comparer les tables de quantification d'un JPEG à des tables connues (appareils, logiciels). T24 a avancé une partie de T40 : les tables de libjpeg, reconnues à l'identique à une même qualité de 1 à 100 (ADR-0153, ADR-0154). Restait à choisir les autres tables connues, et leurs sources.

Faisabilité, établie avant la question, sur sources primaires lues le 2026-11-14 :

- **mozjpeg** : `jcparam.c` donne neuf jeux de tables (`std_luminance_quant_tbl[9]`, `std_chrominance_quant_tbl[9]`), mis à l'échelle comme libjpeg ; le profil par défaut (`JCP_MAX_COMPRESSION`) prend le jeu 3, la table de N. Robidoux. Tables identiques dans mozjpeg 4.1.1 (dernière version publiée, 2022) et sur la branche principale. Licence IJG et BSD, compatible avec Apache-2.0 (ADR-0011).
- **ffmpeg** : l'encodeur MJPEG écrit la matrice intra par défaut de MPEG-1 multipliée par le qscale puis divisée par 8, le coefficient continu à 8 (`encode_picture` de `mpegvideo_enc.c`, `ff_mpeg1_default_intra_matrix` de `mpeg12data.c`, FFmpeg 7.1) ; vérifié sur le poste aux qscale 2, 5 et 31 (ffmpeg 7.1.5). T24 avait relevé que ces tables ne sont pas celles de libjpeg.
- **libjpeg à deux qualités** : `cjpeg -quality 90,70` et `q_scale_factor` (libjpeg 7 et suivantes) mettent la luminance et la chrominance à deux qualités ; vérifiable par le cjpeg de libjpeg-turbo 2.1.5 du poste.
- **Photoshop et appareils** : aucune source publique ne donne les valeurs. Farid (« Digital Image Ballistics from JPEG Quantization », TR2006-583, Dartmouth, 2006) a relevé 13 niveaux de Photoshop, identiques de Photoshop 3 à CS2, et les tables de 204 appareils, sans les publier (une seule figure, Nikon Coolpix 2500) ; l'article de Kornblum (DFRWS 2008) n'a pas pu être lu (accès refusé, HTTP 403) ; la base de JPEGsnoop est sous GPL-2.0 ; les préréglages de Pillow (`JpegPresets.py`) se disent « équivalents aux réglages de Photoshop » sans dire comment ni à quelle qualité.
- Collisions, calculées par un script temporaire hors du dépôt sur les neuf jeux de mozjpeg, les qualités 1 à 100 en huit et seize bits, et les qscale 1 à 31 de ffmpeg : hors du jeu plat (1), seules les tables dégénérées (toutes à 1, toutes à 255) sont écrites par plusieurs familles.

## Options envisagées

Première question, plusieurs choix permis : quelles tables connues, en plus de libjpeg ?

- **mozjpeg** (recommandée) : jeux 2 à 8, qualités 1 à 100, jeu plat exclu. Avantages : source primaire, encodeur d'optimiseurs d'images. Inconvénient : pas d'oracle sur le poste.
- **ffmpeg MJPEG** (recommandée) : qscale 1 à 31. Avantages : profil d'une image extraite d'une vidéo ; vérifiable par ffmpeg sur le poste. Inconvénient : réglages par défaut seulement.
- **libjpeg à deux qualités** (déconseillée par l'assistant) : avantage, vérifiable par cjpeg ; inconvénients, réglage rare hors de cjpeg, une observation et une règle de plus.
- **Photoshop et appareils** (déconseillée par l'assistant) : avantage, ce que F-30 nomme d'abord (appareils) et le logiciel de retouche le plus répandu ; inconvénient, aucune source primaire.

Seconde question, après le choix des quatre : comment obtenir les tables de Photoshop et des appareils ?

- **Complément de T40** (recommandé) : T40 livre les trois autres familles et le point d'extension (ADR-0181) ; un complément, sur sa propre branche et sa propre PR, relève les tables sur des fichiers publics de provenance établie (originaux de Wikimedia Commons sous licence libre ; qualité de Photoshop lue dans sa ressource 0x0406), chacune citée par son adresse, et les livre au catalogue par empreinte.
- **Échantillons dans T40** : même relevé dans cette branche ; une PR plus longue, qui mêle code et recherche de corpus.
- **Préréglages de Pillow** : source secondaire et invérifiable ; ne couvre pas les appareils.
- **Base de JPEGsnoop** : la recopier dans un outil Apache-2.0 pose une question de licence que l'assistant ne peut pas trancher.

## Décision

T40 reconnaît, en plus des tables de libjpeg à une même qualité : libjpeg à deux qualités, mozjpeg (jeux 2 à 8) et l'encodeur MJPEG de ffmpeg. Les tables de Photoshop et des appareils sont relevées dans un complément de T40, sur des fichiers publics de provenance établie, et livrées au catalogue par leur empreinte (ADR-0181).

## Raisons

- Les quatre familles retenues par TheDarkMac : mozjpeg et ffmpeg sur recommandation de l'assistant ; libjpeg à deux qualités, Photoshop et appareils contre sa recommandation, sans raison supplémentaire donnée.
- Complément retenu par TheDarkMac, sur recommandation de l'assistant : il garde une PR de code et une PR de relevé, comme les compléments de T21 et de T30 (ADR-0123, ADR-0166), et le relevé se fait sur le point d'extension livré par T40.
- Échantillons dans T40 écartés : une seule PR mêlerait deux sujets (découpage, §1).
- Préréglages de Pillow écartés : la correspondance avec Photoshop n'est pas sourcée (ERR-0002).
- Base de JPEGsnoop écartée : licence GPL-2.0, et des signatures relevées par un tiers, dont la provenance de chaque entrée ne se vérifie pas.

## Conséquences

- F-30 reste partielle : les logiciels sont couverts (libjpeg, mozjpeg, ffmpeg), pas encore Photoshop ni les appareils.
- Le complément de T40 s'ajoute au découpage ; il dépend du point d'extension d'ADR-0181 et ne change pas le module.
- Les tables de mozjpeg ne sont vérifiées que contre `jcparam.c` tant qu'aucun cjpeg de mozjpeg n'est installé : la compilation de mozjpeg sur le poste, essayée pendant T40, a été refusée par l'outil d'assistance ; le test d'oracle est écrit et ignoré si l'outil manque.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
| 2026-11-16 | Renvoi : complément de T40 livré, tables de Photoshop et d'appareils relevées (ADR-0191 à ADR-0196) |
