# Fiche technique — Images d'un PDF, analysées comme des parties extraites

- **Module** : `imagespdf` (version 0.1.0)
- **Tâche** : T53
- **Exigences** : F-63
- **Formats** : `pdf`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune
- **Contenus extraits** : `jpeg`

## Question

Quelles images porte le PDF, et lesquelles l'outil peut-il faire analyser par ses modules d'image, comme s'il s'agissait de fichiers soumis à part (F-63) ? Une photographie générée, retouchée ou transformée garde ses traces quand elle est placée dans un document ; seule une image écrite telle quelle dans le fichier se lit sans rien décoder.

## Principe

Le module cherche les images de la dernière version, par le lecteur PDF du projet ([ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md)), depuis l'arbre des pages ([ADR-0225](../decisions/ADR-0225-images-jpeg-intactes.md)) :

| Où | Ce qui est lu (ISO 32000-2) |
| --- | --- |
| Ressources de chaque page, `/XObject` | Les flux de sous-type `/Image` (§8.9.5) et `/Form` (§8.10) ; ressources héritées des nœuds de l'arbre des pages (§7.7.3.4) |
| Ressources de chaque forme, `/XObject` | De même, sur au plus 8 niveaux de formes |
| Chaque image | Ses filtres (`/Filter`, §7.4), sa plage de données dans le fichier |

Une image ou une forme reprise par plusieurs pages est lue une fois, à la première. Une image listée dans des ressources est comptée qu'elle soit dessinée ou non : les flux de contenu ne sont pas lus.

Une image dont la liste de filtres est exactement `DCTDecode` est un JPEG complet, écrit tel quel (§7.4.8) : le module en donne la plage au moteur, qui la **reconnaît par l'identification** et en fait une **partie extraite**, analysée par chaque module d'image comme une partie ([ADR-0224](../decisions/ADR-0224-parties-extraites.md)) : métadonnées EXIF, XMP et IPTC, manifeste C2PA, structure et tables de quantification, double compression, ELA, filigrane dwtDct. La partie extraite est numérotée à la suite des parties reconnues et dit d'où elle vient : partie qui la contient, module, page et objet.

Seize images au plus le sont pour un fichier, dans l'ordre des pages, tant que leur taille cumulée n'a pas atteint 2 Mio ; celle qui franchit ce seuil l'est encore, les suivantes sont comptées et la première d'entre elles est déclarée non menée, pour limite dépassée ([ADR-0226](../decisions/ADR-0226-borne-des-images-extraites.md)). La borne garde l'analyse d'un document illustré dans son délai : sur le poste de développement, une photographie de 4 000 sur 3 000 pixels (3,2 Mio) coûte environ 21 s de modules d'image, une image de 534 Kio environ 10,5 s.

Les autres images sont comptées par filtre (liste fermée des dix filtres de la norme, `autre` pour un nom inconnu, `aucun` sans filtre, une chaîne jointe par « + ») et ne sont pas analysées : l'outil ne décode pas de pixels.

Sur les échantillons de `tests/donnees/images` (`generer_images.py`) :

| Échantillon | Écrit par | Relevé |
| --- | --- | --- |
| `imagemagick.pdf` | ImageMagick, depuis un JPEG à l'origine IA déclarée dans son XMP | un JPEG acheminé ; la partie extraite garde son XMP, R-XMP-001 s'y déclenche |
| `libreoffice.pdf` | LibreOffice, page HTML : un JPEG et un PNG | un JPEG acheminé (réencodé, sans métadonnées), une image `FlateDecode` |
| `ghostscript.pdf` | Ghostscript (`viewjpeg.ps`), deux JPEG sur deux pages | un JPEG acheminé, recopié tel quel, suivi de deux octets dans son flux (la partie extraite s'arrête à sa fin logique) ; le petit JPEG (8 sur 8) devenu image en ligne n'est pas compté |
| `formes.pdf` | Écrit objet par objet : formes imbriquées, image reprise, filtres variés | deux JPEG acheminés ; cinq images d'autres filtres (`FlateDecode`, `FlateDecode+DCTDecode`, `JPXDecode`, `aucun`, `autre`) |
| `faux.pdf` | Écrit objet par objet : flux `DCTDecode` qui ne sont pas des JPEG complets | un PNG et des octets quelconques non menés pour format partiel ; un JPEG coupé, partie extraite tronquée |
| `nombreuses.pdf` | Écrit objet par objet : dix-huit JPEG | seize acheminés, deux au-delà |
| `chiffre.pdf` | `libreoffice.pdf` chiffré par Ghostscript (RC4 de 128 bits) | deux images comptées, aucune acheminée |

Oracle (`oracle.json`) : `pdfimages -list` de Poppler 25.03.0 liste les images dessinées, sa page et son objet ; `pdfimages -j` recopie les données de chaque JPEG. Sur chaque échantillon, chaque partie extraite est ce JPEG, octet pour octet, à la page de sa première apparition, et les autres images sont autant que celles que liste Poppler (images en ligne exceptées). Poppler compte un JPEG compressé une seconde fois (`FlateDecode` puis `DCTDecode`) parmi les JPEG, qu'il décompresse ; le module ne l'achemine pas.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| PDF | Dernière version : arbre des pages et ressources héritées ; de chaque ressource `/XObject`, le flux désigné, son `/Subtype`, son `/Filter`, et pour une forme ses `/Resources`. Aucune donnée de flux n'est lue ni décodée par le module ; aucun nom de ressource ni aucune chaîne du document n'est lu. |

## Sorties

| Observation | Forme |
| --- | --- |
| `imagespdf.pages`, `imagespdf.pages_lues` | Pages de l'arbre des pages ; pages parcourues en entier |
| `imagespdf.images` | Images distinctes trouvées |
| `imagespdf.jpeg` | Images au seul filtre `DCTDecode` |
| `imagespdf.acheminees`, `.pages` | JPEG acheminés comme parties extraites ; pages où ils se trouvent |
| `imagespdf.au_dela` | JPEG au-delà de la borne (s'il y en a) |
| `imagespdf.non_acheminees`, `.filtres`, `.pages` | Autres images ; s'il y en a, leurs filtres et leurs pages |
| `imagespdf.chiffre` | Vrai pour un document chiffré : seuls les nombres d'images et de pages sont observés |
| `imagespdf.arret_avant_budget` | Vrai si la recherche s'est arrêtée pour garder du budget |
| `imagespdf.recherche_coupee` | Vrai si une limite (formes imbriquées, images) a été atteinte |

Chaque partie extraite figure à l'identification (`extraites`), avec son origine ; les résultats des modules d'image y portent son rang.

## Données identifiantes

Aucune pour ce module : il n'observe que des nombres, des filtres et des numéros de page. Les modules d'image marquent, dans une partie extraite, les données identifiantes qu'ils y lisent (auteur, numéro de série, coordonnées GPS), comme dans un fichier soumis seul ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien par elle-même : les modules d'image le disent, sur la partie extraite |
| Transformation banale (recompression, redimensionnement) | Rien par elle-même ; le logiciel qui écrit le PDF peut réencoder l'image (LibreOffice et ImageMagick sur les échantillons ; Ghostscript recopie le JPEG) |
| Retouche | Rien par elle-même |
| Génération | Rien par elle-même |

Les constats du module sont des informations neutres, de direction « rien de particulier » : ils disent quelles images sont analysées et lesquelles ne le sont pas.

## Ce qui déclenche un constat

Le module n'émet aucun constat ; quatre règles « moteur » du catalogue lisent ses observations ([ADR-0227](../decisions/ADR-0227-constats-et-versions-de-t53.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-IMAGESPDF-001 | `imagespdf.acheminees` ≥ 1 | Information neutre : JPEG analysés comme des parties extraites, et leurs pages |
| R-IMAGESPDF-002 | `imagespdf.non_acheminees` ≥ 1 | Information neutre : images d'autres filtres, non analysées |
| R-IMAGESPDF-003 | `imagespdf.au_dela` ≥ 1 | Information neutre : JPEG au-delà de la borne |
| R-IMAGESPDF-004 | `imagespdf.chiffre` vrai et `imagespdf.images` ≥ 1 | Information neutre : images d'un document chiffré, non analysées |

## Taux d'erreur

Sans objet pour une information neutre qui compte ce que le document déclare. Les relevés et les plages ont été vérifiés sur les échantillons ci-dessus, contre Poppler, et sur des documents synthétiques des tests. Les constats des modules d'image sur une partie extraite gardent les taux de leurs règles. La part de documents ordinaires dont des images ne sont pas analysées se mesurera sur le corpus de référence (T100).

## Limites connues

- Seule la dernière version est parcourue : une image remplacée par une mise à jour n'est pas analysée ; `revisionspdf` dit qu'un objet a changé.
- Seules les images des ressources des pages et de leurs formes (8 niveaux) sont cherchées : celles des annotations (apparences), des motifs, des polices Type 3, les masques (`/SMask`) et les images en ligne (`BI` … `EI`) ne le sont pas.
- Une image listée est analysée, dessinée ou non ; une image dessinée en partie, ou recadrée par la page, l'est entière.
- Seuls les JPEG écrits tels quels sont analysés : pixels compressés (`FlateDecode`, `LZWDecode`, `RunLengthDecode`), JPEG 2000, CCITT, JBIG2 et JPEG compressé une seconde fois ne le sont pas, ni par le filigrane dwtDct qui lit des pixels.
- Les métadonnées XMP attachées à une image (`/Metadata` de son flux) ne sont pas lues.
- Un JPEG dans un PDF a pu être réencodé ou dépouillé de ses métadonnées par le logiciel qui a écrit le document : l'absence de métadonnées, les tables d'un encodeur courant ou une double compression dans une partie extraite peuvent venir de cette conversion.
- Seize images au plus, jusqu'à 2 Mio de données, dans l'ordre des pages : une image retouchée placée loin dans un document illustré peut rester hors de la borne.
- Document chiffré : aucune image n'est analysée, rien n'est déchiffré ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md)).
- Au plus 4 096 pages et 65 536 images ; la recherche s'arrête quand il ne reste plus que 262 144 objets du budget du module.

## Sécurité

Le module lit la structure du document et rien d'autre : il ne lit ni ne décode aucune donnée de flux. La plage qu'il donne est vérifiée par le contexte (dans sa partie) et reconnue par l'identification, le code qui reconnaît déjà chaque partie et qui est fuzzé depuis T14, avant d'être remise aux modules d'image ; chacun la lit avec son propre budget, comme une partie (ES-03). Une partie extraite n'est pas extraite à son tour. Les formes sont parcourues sans récursion, celles déjà vues écartées ; chaque image et chaque forme compte un objet du budget.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-17 | 0.1.0 | Création |
