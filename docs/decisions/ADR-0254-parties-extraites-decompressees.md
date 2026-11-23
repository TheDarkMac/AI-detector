# ADR-0254 — Partie extraite décompressée : une image compressée dans l'archive, analysée en mémoire

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (mécanisme, protocole et borne précisés par l'assistant)
- **Tâche** : complément de T81
- **Exigences liées** : F-63, F-82, NF-06, ES-03, ES-04, ES-05 ; ADR-0061, ADR-0071, ADR-0224, ADR-0226, ADR-0253

## Contexte

Le mécanisme de T53 (ADR-0224) achemine un contenu lu en place : une plage d'octets du fichier, que l'identification reconnaît et que les modules d'image lisent par position. Un essai au début du complément, sur un document de LibreOffice 25.2.3.2 à trois images, montre deux écritures :

| Format | Entrées des images |
| --- | --- |
| ODT | Stockées telles quelles (méthode 0) : lisibles en place |
| DOCX | Compressées par deflate (méthode 8), comme les autres parties |

Aucun DOCX écrit par Word n'a été lu sur le poste de développement : ECMA-376 permet les deux méthodes, et les tests construisent des DOCX aux images compressées « à la manière de Word ». Une image compressée n'a pas de plage lisible en place.

## Options envisagées

### Option A — Stockées et compressées (recommandée)

Une entrée compressée est décompressée en mémoire et analysée comme une partie extraite ; son origine dit qu'elle l'a été, et les positions de ses résultats se lisent dans le contenu décompressé.

- Avantages : les images d'un DOCX sont analysées, celles de LibreOffice comme celles que les tests écrivent à la manière de Word.
- Inconvénients : nouvelle forme au schéma (0.13.0) ; les positions d'une telle partie ne sont pas des positions du fichier ; de la mémoire pour chaque contenu gardé.

### Option B — Stockées seules

Mécanisme de T53 inchangé.

- Avantages : plus court ; toutes les positions restent dans le fichier.
- Inconvénients : les images d'un DOCX, presque toujours compressées, resteraient sans analyse : comptées, non menées.

### Option C — Stockées maintenant, compressées dans un second complément

- Avantages : chaque PR plus petite.
- Inconvénients : le DOCX attend une PR de plus ; le module change deux fois.

## Décision

Option A. Précisions de l'assistant :

| Étape | Où | Ce qui est fait |
| --- | --- | --- |
| Décompression | Module, par le contexte | `Archive.lire(entree, maximum)` : deflate par `Contexte.decompresser`, chaque bloc compté contre le budget du module (ES-03) ; au-delà de `maximum` octets, `TailleDepassee` arrête la décompression, sans dépasser le budget |
| Borne | Module | 16 Mio décompressés au plus par image (`TAILLE_MAX_IMAGE`, la taille d'une lecture, `TAILLE_MAX_LECTURE`) ; au-delà, l'image est comptée (`trop_grandes`), non acheminée. Une image stockée, lue en place, n'a pas de borne, comme un JPEG d'un PDF |
| Place | Module, par le contexte | `Contexte.extraction_possible` : sans place, l'image n'est pas décompressée ; l'extraction est déclarée sans contenu, refusée, et la première refusée est retenue (ADR-0226) |
| Extraction | Contexte | `extraire(format, plage, localisation, contenu)` : `plage` est celle des données compressées dans la partie, `contenu` le contenu décompressé, non vide ; il compte contre le seuil de 2 Mio pour sa taille décompressée |
| Reconnaissance | Moteur | Dans le contenu, de son début à sa fin, par l'identification (`Fichier` en mémoire, celui du texte collé, ADR-0233) |
| Partie extraite | Moteur | Plage : celle des données compressées dans le fichier, dans son contenant ; origine : `decompression` = méthode (`deflate`), taille du contenu, plage du format dans le contenu (de 0 à sa fin logique, ou à la fin du contenu si elle n'est pas connue) |
| Analyse | Moteur | Chaque module actif lit la partie dans le contenu gardé en mémoire, par position, comme une partie ; ses localisations y restent : elles ne sont pas ramenées au fichier |
| Contrôle | Processus principal | Comme en T53 (plage dans le contenant) ; en plus, une fin non connue s'étend jusqu'à la fin du contenu décompressé |
| Rapport | Identification | Origine : « décompressée (deflate, N octets) : les positions de ses résultats se lisent dans ce contenu » ; signalement des parties extraites généralisé au PDF, au DOCX et à l'ODT |

Mémoire gardée : au plus seize contenus, 2 Mio cumulés, plus celui qui franchit le seuil (16 Mio au plus).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : la moitié bureautique d'A-24 resterait sans effet sur le DOCX.
- Option C écartée : une PR de plus pour un mécanisme dont le reste est déjà écrit.
- Plage des données compressées : la partie reste désignée par où elle est dans le fichier, et le contrôle « dans son contenant » vaut toujours.
- Borne de 16 Mio : la taille qu'une lecture d'entrée admet déjà ; une photo de quelques dizaines de millions de pixels l'atteint rarement en JPEG, et la mémoire du processus de travail reste bornée.

## Conséquences

- `VERSION_SCHEMA` passe à 0.13.0 : `decompression` à l'origine d'une partie extraite, au schéma du rapport et des messages ; les parties lues en place gardent leur forme.
- Les localisations d'une partie extraite décompressée ne désignent pas des octets du fichier : un lecteur du rapport JSON lit l'origine avant de s'en servir.
- `Archive.lire` lit d'abord la plage des données (`Archive.donnees`) ; l'ordre des contrôles d'une lecture ne change pas.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création ; option choisie par TheDarkMac au début du complément de T81 |
