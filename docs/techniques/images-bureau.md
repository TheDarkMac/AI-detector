# Fiche technique — Images d'un DOCX ou d'un ODT, analysées comme des parties extraites

- **Module** : `imagesbureau` (version 0.1.0)
- **Tâche** : complément de T81
- **Exigences** : F-63
- **Formats** : `docx`, `odt`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`
- **Contenus extraits** : `jpeg`, `png`, `webp`, `heic`

## Question

Quelles images porte le document bureautique, et lesquelles l'outil peut-il faire analyser par ses modules d'image, comme s'il s'agissait de fichiers soumis à part ? C'est la symétrie de F-63 pour le DOCX et l'ODT, que demandait A-24 ([ADR-0252](../decisions/ADR-0252-module-imagesbureau.md)) : une image générée ou retouchée collée dans un document garde ses traces, et un DOCX ou un ODT est une archive ZIP où chaque image est une entrée.

## Principe

Le module lit le répertoire central de l'archive, par le lecteur ZIP du projet ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)), puis ce que le document déclare de ses entrées ([ADR-0253](../decisions/ADR-0253-images-cherchees-dans-un-docx-et-un-odt.md)) :

| Format | Ce qui déclare le type d'une entrée | Vignette |
| --- | --- | --- |
| DOCX | `[Content_Types].xml` : `Override` par nom de partie, sinon `Default` par extension, noms et extensions sans casse (ECMA-376, partie 2, §10.1.2) | Cible de la relation `…/metadata/thumbnail` du paquet (`_rels/.rels`) |
| ODT | `META-INF/manifest.xml` : `manifest:media-type` de chaque `manifest:file-entry` (ODF 1.3, partie 2, §4) | `Thumbnails/thumbnail.png` (ODF 1.3, partie 2, §3.3) |

Toutes les entrées déclarées `image/…` sont des images, qu'un texte les cite ou non, dans l'ordre du répertoire central. La vignette, rendue par le logiciel à partir de la première page, est comptée à part et n'est pas acheminée. Une image déclarée JPEG, PNG, WebP ou HEIC (`image/jpeg`, `image/png`, `image/webp`, `image/heic`, `image/heif`, sans casse ni paramètres) est donnée au moteur dans ce format ; le moteur la **reconnaît par l'identification** et en fait une **partie extraite**, analysée par chaque module d'image comme une partie ([ADR-0224](../decisions/ADR-0224-parties-extraites.md)). Un contenu d'un autre format que celui déclaré est déclaré non mené, pour format partiel. Les autres images (GIF, EMF, WMF, SVG, TIFF, BMP…) sont comptées par type, non analysées.

Une image se lit de deux façons ([ADR-0254](../decisions/ADR-0254-parties-extraites-decompressees.md)) :

| Entrée | Lecture | Plage de la partie extraite | Positions de ses résultats |
| --- | --- | --- | --- |
| Stockée telle quelle (méthode 0) | En place, comme un JPEG d'un PDF | Celle de l'image dans le fichier | Dans le fichier |
| Compressée par deflate (méthode 8) | Décompressée par le module, au plus 16 Mio, et analysée en mémoire | Celle des données compressées | Dans le contenu décompressé, que l'origine décrit (méthode, taille, plage du format) |

Seize images au plus le sont pour un fichier, tant que leur taille cumulée n'a pas atteint 2 Mio ; une image compressée y compte pour sa taille décompressée ; celle qui franchit le seuil l'est encore, les suivantes sont comptées et la première d'entre elles est déclarée non menée, pour limite dépassée ([ADR-0226](../decisions/ADR-0226-borne-des-images-extraites.md)). Quand il ne reste plus de place, une image compressée n'est pas décompressée.

Un ODT protégé par un mot de passe est dit chiffré : rien n'est déchiffré ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md)). Une image chiffrée entrée par entrée est comptée, non acheminée ; un paquet chiffré en entier (`encrypted-package`, comme l'écrit LibreOffice 25.2) ne déclare plus ses images.

Sur les échantillons de `tests/donnees/imagesbureau` (`generer_imagesbureau.py`), un document de LibreOffice 25.2.3.2 à trois images (un JPEG à l'origine IA déclarée dans son XMP, un PNG, un GIF) :

| Échantillon | Écriture de LibreOffice | Relevé |
| --- | --- | --- |
| `libreoffice.odt` | Images stockées telles quelles, vignette PNG | JPEG et PNG acheminés, lus en place ; GIF compté ; vignette comptée à part ; R-XMP-001 dans la partie extraite du JPEG |
| `libreoffice.docx` | Images compressées par deflate, sans vignette | JPEG et PNG acheminés, décompressés ; GIF compté ; R-XMP-001 dans la partie extraite du JPEG |
| `chiffre.odt` | Paquet chiffré en entier (mot de passe `essai`) | Aucune image déclarée ; document chiffré |

LibreOffice recopie les images sans les réencoder : chaque partie extraite a l'empreinte SHA-256 de l'image d'origine. Oracle (`oracle.json`) : `zipfile` (compression et empreinte du contenu de chaque entrée) et `xml.etree` (types déclarés, vignette, chiffrement), indépendants du module ; sur chaque échantillon, les parties extraites sont, dans l'ordre et octet pour octet, les entrées déclarées JPEG ou PNG, vignette exceptée.

Les DOCX « à la manière de Word » (types par extension, images compressées sous `word/media`, vignette sous `docProps`) sont construits par les tests : aucun document écrit par Word n'a été lu sur le poste de développement.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| DOCX | Répertoire central ; `[Content_Types].xml` et `_rels/.rels`, élément par élément ; données de chaque image acheminée |
| ODT | Répertoire central ; `META-INF/manifest.xml`, élément par élément ; données de chaque image acheminée |

Aucune autre partie n'est lue : ni le corps, ni les propriétés.

## Sorties

| Observation | Forme |
| --- | --- |
| `imagesbureau.images` | Entrées déclarées image, vignette exceptée |
| `imagesbureau.vignette` | Vrai si le document a une vignette déclarée image |
| `imagesbureau.acheminables` | Images déclarées JPEG, PNG, WebP ou HEIC |
| `imagesbureau.acheminees`, `.formats` | Images acheminées comme parties extraites ; leurs formats |
| `imagesbureau.decompressees` | Parmi elles, celles qui sont analysées décompressées (s'il y en a) |
| `imagesbureau.au_dela` | Images au-delà de la borne (s'il y en a) |
| `imagesbureau.trop_grandes` | Images compressées de plus de 16 Mio décompressées (s'il y en a) |
| `imagesbureau.non_acheminees`, `.types` | Images d'autres types ; s'il y en a, leurs types déclarés |
| `imagesbureau.chiffre` | Vrai si le manifeste d'un ODT déclare une entrée chiffrée |

Chaque partie extraite figure à l'identification (`extraites`), avec son origine : la partie qui la contient, le module, le nom de l'entrée, et pour une image compressée sa décompression ; les résultats des modules d'image y portent son rang.

## Données identifiantes

Aucune pour ce module : il observe des nombres, des formats et des types déclarés. Le nom de l'entrée de chaque partie extraite figure à son origine, comme le nom des parties lues dans les localisations des modules `ooxml`, `odf`, `actifsbureau` et `historique` ; un logiciel peut nommer une image d'après son fichier d'origine. Les modules d'image marquent, dans une partie extraite, les données identifiantes qu'ils y lisent, comme dans un fichier soumis seul ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien par elle-même : les modules d'image le disent, sur la partie extraite |
| Transformation banale | Rien par elle-même ; un logiciel peut réencoder une image en l'insérant (LibreOffice ne le fait pas sur les échantillons) |
| Retouche | Rien par elle-même |
| Génération | Rien par elle-même |

## Ce qui déclenche un constat

Le module n'émet aucun constat ; cinq règles « moteur » du catalogue lisent ses observations ([ADR-0255](../decisions/ADR-0255-constats-et-versions-du-complement-de-t81.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-IMAGESBUREAU-001 | `imagesbureau.acheminees` ≥ 1 | Information neutre : images analysées comme des parties extraites, et leurs formats |
| R-IMAGESBUREAU-002 | `imagesbureau.non_acheminees` ≥ 1 | Information neutre : images d'autres types, non analysées |
| R-IMAGESBUREAU-003 | `imagesbureau.au_dela` ≥ 1 | Information neutre : images au-delà de la borne |
| R-IMAGESBUREAU-004 | `imagesbureau.trop_grandes` ≥ 1 | Information neutre : images compressées trop grandes |
| R-IMAGESBUREAU-005 | `imagesbureau.chiffre` vrai | Information neutre : ODT chiffré, images non analysées |

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `imagesbureau` 0.1.0, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 2298 | 1/87 : 1,1 % [0,2 % ; 6,2 %] | 0/86 : 0,0 % [0,0 % ; 4,3 %] | — | 0 |
| Générés | 424 | 372 | 0/52 : 0,0 % [0,0 % ; 6,9 %] | — | 52/52 : 100,0 % [93,1 % ; 100,0 %] | 0 |
| Transformés | 1294 | 1210 | 1/84 : 1,2 % [0,2 % ; 6,4 %] | 0/83 : 0,0 % [0,0 % ; 4,4 %] | — | 0 |
| Retouchés | 273 | 233 | 1/40 : 2,5 % [0,4 % ; 12,9 %] | — | 39/39 : 100,0 % [91,0 % ; 100,0 %] | 0 |
| Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/8 : 0,0 % [0,0 % ; 32,4 %] | — | 0 |

Aucune règle de preuve ou d'indice : les règles du module sont des informations neutres, sans taux.

<!-- Fin des taux mesurés. -->

Sans objet pour une information neutre qui compte ce que le document déclare. Les relevés et les plages ont été vérifiés sur les échantillons ci-dessus, contre `zipfile` et `xml.etree`, et sur des documents synthétiques des tests. Les constats des modules d'image sur une partie extraite gardent les taux de leurs règles. La part de documents dont l'extraction n'a pas pu être menée est la colonne « Non analysables » ci-dessus ; celle des documents dont une partie seulement des images est analysée n'est pas comptée par le banc.

## Limites connues

- Une image que le document ne déclare pas (absente des types de contenu ou du manifeste) n'est pas cherchée ; une image déclarée d'un autre type que son contenu est déclarée non menée, pour format partiel.
- Une image déclarée est analysée, que le texte l'affiche ou non ; une image recadrée par le document l'est entière.
- La vignette n'est pas analysée.
- GIF, EMF, WMF, SVG, TIFF et BMP ne sont lus par aucun module d'image ; ils sont comptés.
- L'ordre est celui du répertoire central, pas celui du texte : une image retouchée peut rester hors des seize.
- Les positions des résultats d'une image compressée se lisent dans son contenu décompressé, pas dans le fichier.
- Une image compressée de plus de 16 Mio décompressée n'est pas analysée.
- ODT chiffré : rien n'est déchiffré ; un paquet chiffré en entier ne déclare pas ses images, qui ne sont pas comptées.
- Les documents incorporés (objets OLE, `Object 1/` d'un ODT) ne sont pas ouverts : seules les images déclarées par le paquet lui-même le sont, celles d'un sous-document d'ODT comprises, le manifeste racine les listant.

## Sécurité

Le module lit le répertoire central et deux parties XML, par expat sans DTD ni entité ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)). Une image stockée n'est pas lue par lui : sa plage est vérifiée par le contexte (dans sa partie) et reconnue par l'identification. Une image compressée est décompressée par le contexte, qui compte chaque bloc contre le budget du module (ES-03), et la décompression s'arrête au-delà de 16 Mio : le contenu gardé en mémoire pour les modules d'image est borné. Une partie extraite n'est pas extraite à son tour.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-23 | 0.1.0 | Création |
