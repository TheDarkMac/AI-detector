# ADR-0225 — Images d'un PDF acheminées : les JPEG écrits tels quels ; les autres comptées par filtre

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (recherche des images précisée par l'assistant)
- **Tâche** : T53
- **Exigences liées** : F-63, F-82, NF-01, ES-03 ; ADR-0124, ADR-0125, ADR-0126, ADR-0221, ADR-0224

## Contexte

Une image d'un PDF est un flux de sous-type `/Image` (ISO 32000-2, §8.9.5), compressé par un ou plusieurs filtres (§7.4). Avec le seul filtre `DCTDecode` (§7.4.8), les données du flux sont un JPEG complet, écrit tel quel. Avec `FlateDecode`, `LZWDecode` ou `RunLengthDecode`, ce sont des pixels compressés, sans en-tête de format ; `JPXDecode` donne un JPEG 2000, hors du périmètre ; `CCITTFaxDecode` et `JBIG2Decode` des images au trait.

Les modules d'image lisent une partie au format JPEG, PNG, WebP ou HEIC (métadonnées, C2PA, tables de quantification, double compression, ELA) ; seul `dwtdct` lit des pixels, et ceux d'un JPEG ou d'un PNG.

## Options envisagées

### Option A — JPEG intacts seuls (recommandée)

Une image au seul filtre `DCTDecode` est acheminée, par sa plage d'octets ; rien n'est décodé par T53. Les autres sont comptées par filtre, non analysées.

- Avantages : les modules d'image lisent ces JPEG comme s'ils avaient été soumis seuls, toutes leurs analyses s'appliquent ; aucun décodeur nouveau à durcir.
- Inconvénients : les images en pixels compressés (captures, schémas, la plupart des images converties depuis un PNG) ne sont pas analysées.

### Option B — JPEG et pixels bruts

En plus, les images `FlateDecode` décodées en pixels et remises à `dwtdct` par une lecture en mémoire ajoutée au contexte.

- Avantages : plus de couverture pour le filigrane dwtDct.
- Inconvénients : un nouveau mode de lecture du contexte (ADR-0061), des pixels sans format à interpréter (espace colorimétrique, bits par composante, masque), à durcir et à fuzzer ; un seul module en profiterait.

## Décision

Option A. Précisions de l'assistant :

- **Recherche** : dans la dernière version, depuis l'arbre des pages (parcours du lecteur, ADR-0221) : les `/XObject` des ressources de chaque page, et ceux des formes (`/Form`) qu'elles listent, sur au plus 8 niveaux. Une image ou une forme reprise par plusieurs pages est lue une fois, à la première. Une image listée est retenue, qu'elle soit dessinée ou non : les flux de contenu ne sont pas lus. Les images en ligne (`BI` … `EI`), les images des annotations, motifs et polices Type 3, les masques (`/SMask`) ne sont pas cherchés.
- **Filtres** : liste fermée des dix filtres de la norme (§7.4, tableau 6), tout autre nom observé `autre` ; une chaîne de filtres s'écrit jointe par « + » (`FlateDecode+DCTDecode`), une image sans filtre `aucun`. Aucun nom de ressource (`/Im1`) ni aucune chaîne du document n'est lu.
- **Acheminement** : image dont la liste de filtres est exactement `DCTDecode` ; localisée par sa page et son objet (`image (objet n g)`).
- **Document chiffré** : les données de ses flux le sont aussi ; ses images sont comptées par la structure, jamais déchiffrées ni acheminées (ADR-0126).
- **Bornes** : 4 096 pages, 65 536 images retenues ; recherche arrêtée avant le budget d'objets, comme `actifspdf` (ADR-0213, ADR-0221) ; une page illisible n'arrête pas les autres.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un décodeur de plus pour un seul module ; la question pourra revenir avec un module qui lise des pixels sans format.
- Liste fermée des filtres : un nom tiré du fichier ne passe pas au rapport tel quel.

## Conséquences

- Un PDF dont les images sont toutes en pixels compressés n'a aucune partie extraite ; R-IMAGESPDF-002 le dit (ADR-0227).
- Une image `FlateDecode+DCTDecode` (JPEG compressé une seconde fois) n'est pas analysée : il faudrait la décompresser en mémoire, comme l'option B.
- Les métadonnées XMP attachées à une image (`/Metadata` du flux) ne sont pas lues : elles le seront avec les paquets XMP des objets (ADR-0127).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T53 |
