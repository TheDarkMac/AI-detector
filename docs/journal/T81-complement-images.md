# Complément de T81 — Images d'un DOCX ou d'un ODT, analysées comme des parties extraites

- **Branche** : `tache/T81-complement-images`
- **Dates** : 2026-11-23
- **Exigences couvertes** : F-63, étendue au DOCX et à l'ODT par A-24
- **Décisions** : ADR-0252 à ADR-0254, acceptées au début du complément ; ADR-0255, proposée par l'assistant
- **Errata** : aucun

## Objectif

Extraire les images d'un DOCX ou d'un ODT et les faire analyser par les modules d'image, comme celles d'un PDF depuis T53 : la symétrie de F-63 que demandait A-24, renvoyée à ce complément par ADR-0248. Demandé par TheDarkMac le 2026-11-23 (« t90 est il le suivant ? si oui, vas y », puis, sur la réponse de l'assistant que le complément de T81 venait avant T90 dans l'ordre de la V1, « Oui, complément T81 »).

## État initial

- PR [#43](https://github.com/TheDarkMac/AI-detector/pull/43) (T81) : les 16 vérifications vertes sur `eae47ec` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-23 à 11:46:28 UTC après le « Yes, merge if green » de TheDarkMac, commit de merge `90e9542`. Lancements de push sur `90e9542` : code 45168190012 et docs 45168190061 verts. Empreinte du catalogue 0.19.0 : `c7db425b…2b7f` ; schémas 0.12.0.
- Les modules `actifsbureau`, `caracteres` et `historique` lisent l'archive d'un DOCX ou d'un ODT pour leur propre compte ; `imagespdf` extrait les JPEG d'un PDF comme des parties extraites, lues en place (ADR-0224, ADR-0225) ; aucun module n'achemine une image d'un document bureautique.
- Toujours en attente : voir les journaux de T81, de T80 et de ses compléments (« Reste à faire ») ; signature d'un manifeste C2PA d'un texte ; inventaire des marquages à refaire en entier ; `$OutputEncoding` de PowerShell (T103).

## Déroulé

1. Lecture d'ADR-0248, d'ADR-0224 à ADR-0227, du journal de T53, du module `imagespdf`, du lecteur ZIP (`_lecture/zip.py`), du contexte et du moteur (`_travail/contexte.py`, `principal.py`, `fichier.py`), du modèle (`Partie`, `Origine`, `verifier_extraites`), du schéma du rapport et de l'affichage des parties extraites (`_html.py`, `cli.py`, `_presentation.py`).
2. Essai sur un document de LibreOffice 25.2.3.2 à trois images (JPEG, PNG, GIF), écrit depuis un document à plat aux images en données binaires : l'ODT range chaque image telle quelle (méthode 0) et ajoute la vignette `Thumbnails/thumbnail.png` ; le DOCX compresse chaque image par deflate (méthode 8). LibreOffice recopie les images sans les réencoder. Une image d'un DOCX n'a donc pas de plage lisible en place, ce que le mécanisme de T53 supposait.
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : images stockées et compressées, ces dernières décompressées et analysées en mémoire ([ADR-0254](../decisions/ADR-0254-parties-extraites-decompressees.md)) ; toutes les entrées déclarées image, vignette à part, et type déclaré vérifié par l'identification ([ADR-0253](../decisions/ADR-0253-images-cherchees-dans-un-docx-et-un-odt.md)) ; nouveau module `imagesbureau` ([ADR-0252](../decisions/ADR-0252-module-imagesbureau.md)). L'assistant avait écrit dans la première question que Word compresse ses images « comme » LibreOffice : aucun document de Word n'a été lu sur le poste ; les ADR et la fiche disent seulement ce qu'ECMA-376 permet et ce que construisent les tests. Précisions de l'assistant, écrites dans ces ADR : F-63 étendue sans nouvel identifiant d'exigence, lecture des types de contenu et du manifeste, vignette d'un DOCX par la relation du paquet, entrées chiffrées, borne de 16 Mio par image décompressée, plage des données compressées pour la partie, `decompression` à l'origine, contenu compté pour sa taille décompressée.
4. Modèle et schémas (0.13.0) : `Decompression` (méthode, taille du contenu, plage du format dans ce contenu), champ `decompression` de l'`Origine`, contrôle d'une fin non connue ; schéma du rapport (et des messages, qui le citent).
5. Moteur : `Extraction.contenu` et sa taille ; `Contexte.extraire(…, contenu)`, `Contexte.extraction_possible`, `Contexte.decompresser(…, maximum)` et `TailleDepassee` ; dans `principal`, reconnaissance d'un contenu décompressé dans un `FichierEnMemoire`, contenu gardé par rang, modules exécutés sur ce contenu avec la plage du format. Lecteur ZIP : `Archive.donnees` (plage des données d'une entrée) et `Archive.lire(entree, maximum)`, mêmes contrôles et dans le même ordre qu'avant pour les autres modules.
6. Module `imagesbureau` 0.1.0 et ses observations ; premier essai sur les deux documents de l'étape 2 : les parties extraites du DOCX sont décompressées et analysées, celles de l'ODT lues en place. Rapport : origine « décompressée (deflate, N octets) : les positions de ses résultats se lisent dans ce contenu » ; le signalement des parties extraites disait « (PDF) » en dur : il dit désormais « (PDF, DOCX ou ODT) » ; `imagesbureau` rejoint les modules sans métadonnées du résumé.
7. Catalogue 0.20.0 : `regles/imagesbureau.toml`, R-IMAGESBUREAU-001 à R-IMAGESBUREAU-005, proposées par l'assistant ([ADR-0255](../decisions/ADR-0255-constats-et-versions-du-complement-de-t81.md), statut « Proposé ») ; description resserrée (1 021 caractères) ; empreinte `a8eaba47…61ea1` inscrite au registre.
8. Échantillons : `tests/donnees/imagesbureau/generer_imagesbureau.py` fait écrire par LibreOffice (UNO), depuis un document à plat, `libreoffice.odt`, `libreoffice.docx` et `chiffre.odt` (mot de passe), avec un JPEG à l'origine IA déclarée dans son XMP (exiftool, comme en T53), un PNG et un GIF (ImageMagick) ; `oracle.json` consigne ce qu'en lisent `zipfile` et `xml.etree`. Constat : LibreOffice 25.2 chiffre le paquet entier dans une seule entrée, `encrypted-package` (ODF 1.4), et le manifeste ne déclare plus d'images. La règle prévue sur le nombre d'images chiffrées devient R-IMAGESBUREAU-005, sur le seul chiffrement ; le chiffrement entrée par entrée reste lu, éprouvé sur un ODT construit par les tests. Sur les trois échantillons : R-XMP-001 (origine IA déclarée) dans la partie extraite du JPEG, lue en place dans l'ODT et décompressée dans le DOCX.
9. Tests : `tests/test_images_bureau.py` (DOCX à la manière de Word, types déclarés, surcharges, casse et paramètres, vignette et ses cibles, ODT lu en place, entrées chiffrées, déclarations absentes, mal formées ou en double, archive illisible, entrées illisibles, entrée tronquée, vides, trop grandes, places et octets épuisés, dix-huit images, échantillons contre l'oracle, règles sur des analyses complètes, contenu d'un autre format que celui déclaré, budget de bout en bout sur trois JPEG décompressés, phrases, rapport, contrôle avant publication) ; moteur dans `tests/test_travail.py` (analyse en mémoire, fin inconnue, autre format, taille décompressée contre le seuil, contenu vide refusé, décompression bornée) ; modèle et schémas ; attentes mises à jour (listes des modules, compte des règles, versions des schémas, bibliothèques des modules désactivés, document de LibreOffice sans image, modules d'un PDF) ; fuzzing : `imagesbureau` sur le DOCX et l'ODT, trois échantillons de plus. Une attente d'un test du lecteur ZIP a montré que l'ordre de ses contrôles avait changé (entrée trop grande lue avant d'être tronquée) : l'ordre d'avant est rétabli. Couverture du module : 100 %.
10. Campagne de fuzzing à part, sur le seul module : 20 000 documents (graine 81), sept sur dix tirés des trois échantillons ou d'un DOCX construit à la manière de Word, dont les déclarations (`[Content_Types].xml`, `_rels/.rels`, `META-INF/manifest.xml`) et les images sont mutées (octets changés, jetons insérés : types par extension et par nom de partie, entrées du manifeste, chiffrement, vignette hors de la racine, DTD, déclaration d'encodage, signatures d'image, type démesuré ; morceaux retirés ou recopiés), parfois une entrée retirée ou changée de compression, puis réécrits en archive ; les autres mutés octet par octet ; chaque document analysé deux fois, mêmes messages, chaque message validé par le schéma des messages, chaque extraction vérifiée (plage dans la partie, contenu non vide) puis reconnue par l'identification. Aucun échec, aucune limite dépassée, 13 957 extractions dont 8 054 décompressées, en 358 secondes.
11. Suite complète sous coverage, en 19 minutes 18 (avec la campagne de fuzzing en parallèle) : 3 349 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), 1 en échec : le compte des règles du catalogue de `test_incoherences.py`, qui n'avait pas les cinq règles du module ; corrigé. Couverture de tout le paquet et du banc à 100 %. Relancé ensuite, `test_fuzzing.py` a trouvé un ODT muté dont une entrée PNG était déclarée : l'aide `contexte` des tests ne donnait que `jpeg` aux formats extraits, que le contexte refuse alors ; elle donne désormais les quatre formats des deux modules qui extraient. Fichiers concernés relancés (fuzzing, incohérences, images d'un PDF, documents bureautiques) : 513 tests verts.
12. Rapport de `libreoffice.docx` relu dans le navigateur intégré, servi par un serveur local : tableau « Parties extraites » avec l'origine et sa décompression.
13. PR [#44](https://github.com/TheDarkMac/AI-detector/pull/44) ouverte vers `detector` (commits `cb3c8b8`, `49dd9df`, `082fc6c`). ADR-0255 reste au statut « Proposé » jusqu'à la validation de TheDarkMac : le contrôle des ADR échoue d'ici là (ADR-0129).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Images d'un DOCX sans plage lisible en place | LibreOffice les compresse par deflate | Question à TheDarkMac : parties extraites décompressées (ADR-0254) |
| Aucune image déclarée dans l'ODT chiffré | LibreOffice 25.2 chiffre le paquet entier (`encrypted-package`) | R-IMAGESBUREAU-005 sur le chiffrement seul ; chiffrement entrée par entrée éprouvé par un ODT construit |
| Signalement « (PDF) » sur un DOCX | Texte écrit en dur pour T53 | « (PDF, DOCX ou ODT) » |
| Ordre des contrôles du lecteur ZIP changé | `Archive.lire` réécrite sur `Archive.donnees` | Contrôle de la taille d'une lecture avant celui de la troncature, comme avant |
| Affirmation non vérifiée sur Word dans une question | Supposée par l'assistant | Retirée des ADR et de la fiche ; consignée ici |
| Version de LibreOffice supposée dans une règle (« depuis la 24.2 ») | Écrite sans vérification | Ramenée à la version essayée, 25.2 |
| Compte des règles du catalogue faux d'un test | Les cinq règles du module n'y étaient pas | Ajoutées au compte |
| Extraction d'un PNG refusée dans le fuzzing de la suite | Aide `contexte` des tests limitée au format `jpeg` d'`imagespdf` | Formats des deux modules qui extraient |

## Écarts par rapport au découpage

- Ajout : parties extraites décompressées, analysées en mémoire (ADR-0254), qui changent le moteur et les schémas (0.13.0).
- Ajout : F-63 portée par T81 à la matrice, à côté de T53.

## Résultat

- Module `imagesbureau` 0.1.0 (`docx`, `odt`) ; catalogue 0.20.0 ; schémas 0.13.0 ; autres modules inchangés.
- `vk document.docx` ou `vk document.odt` analyse chaque image JPEG, PNG, WebP ou HEIC que le document déclare (seize au plus, jusqu'à 2 Mio), lue en place ou décompressée, comme une partie extraite, par les modules d'image ; le rapport dit d'où vient chaque partie extraite, si elle a été décompressée, quelles images ne sont pas analysées et pourquoi.

## Reste à faire

- Un DOCX écrit par Word dans l'oracle (comme pour T21 et T81).
- Images des documents incorporés (objets OLE, sous-documents) ; images liées hors de l'archive, que `actifsbureau` signale.
- GIF, EMF, WMF, SVG, TIFF, BMP : aucun module d'image ne les lit.
- Mesure sur le corpus (T100) : part de documents dont des images ne sont pas analysées.
