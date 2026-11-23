# ADR-0253 — Images cherchées dans un DOCX ou un ODT : toutes les entrées déclarées, vignette à part ; format déclaré, vérifié par l'identification

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (lecture des déclarations précisée par l'assistant)
- **Tâche** : complément de T81
- **Exigences liées** : F-63, F-82 ; A-24 ; ADR-0224, ADR-0226, ADR-0252

## Contexte

Une image d'un DOCX est une partie de l'archive (`word/media/…` chez Word et LibreOffice), que des relations relient au corps ; une image d'un ODT est une entrée (`Pictures/…` chez LibreOffice), que `content.xml` cite par `draw:image`. Les deux formats déclarent le type de chaque entrée : les types de contenu d'OPC (`[Content_Types].xml`, ECMA-376, partie 2, §10.1.2) et le manifeste d'ODF (`META-INF/manifest.xml`, ODF 1.3, partie 2, §4). Chacun a aussi une vignette, rendue par le logiciel à partir de la première page. Les modules d'image lisent JPEG, PNG, WebP et HEIC ; pour un PDF, seize images au plus sont acheminées, jusqu'à 2 Mio (ADR-0226).

Deux questions : quelles entrées chercher, et qui dit le format qu'on donne au moteur.

## Options envisagées

### Entrées cherchées

#### Option A — Toutes les entrées déclarées image (recommandée)

Chaque entrée que le document déclare `image/…`, dans l'ordre du répertoire central, qu'un texte la cite ou non ; la vignette comptée à part, non acheminée ; les images d'un autre format (GIF, EMF, WMF, SVG, TIFF, BMP) comptées par type.

- Avantages : une image présente mais jamais affichée est analysée aussi ; aucune lecture du corps.
- Inconvénients : l'ordre n'est pas celui du texte.

#### Option B — Les images citées par le corps

Relations de `word/document.xml`, `draw:image` de `content.xml`, dans l'ordre du texte.

- Avantages : l'ordre de lecture du document.
- Inconvénients : une image présente sans être affichée reste sans analyse ; en-têtes, pieds de page, notes et objets demandent chacun leur lecture.

#### Option C — Toutes, vignette comprise

- Avantages : rien n'est mis de côté.
- Inconvénients : la vignette, rendue par le logiciel, ne dit rien de l'image d'origine et consomme le budget des seize.

### Format donné au moteur

#### Option A — Le type déclaré, vérifié par l'identification (recommandée)

Le module donne le format du type déclaré ; le moteur reconnaît le contenu, comme en T53 (ADR-0224) : un contenu d'un autre format, ou non reconnu, est déclaré non mené pour format partiel, localisé à l'entrée.

- Avantages : la reconnaissance reste au code fuzzé qui reconnaît chaque partie ; un écart entre type déclaré et contenu se voit au rapport.
- Inconvénients : une image renommée et mal déclarée n'est pas analysée.

#### Option B — La signature, lue par le module

- Avantages : une image mal déclarée serait analysée quand même.
- Inconvénients : la reconnaissance se ferait deux fois ; l'écart entre type déclaré et contenu ne se verrait plus.

## Décision

Option A pour les deux questions. Précisions de l'assistant :

| Point | Lecture |
| --- | --- |
| Type d'une entrée d'un DOCX | `Override` dont le `PartName` (décodé de ses `%xx`, sans la barre initiale) nomme l'entrée, sans casse ; sinon `Default` de son extension, sans casse (OPC) ; aucun type sinon |
| Type d'une entrée d'un ODT | `manifest:media-type` du `manifest:file-entry` dont le `manifest:full-path` (sans `./`) nomme l'entrée ; aucun type sinon |
| Image | Type `image/…`, sans casse ni paramètres (RFC 2045, §5.1) |
| Formats acheminés | `image/jpeg` → `jpeg`, `image/png` → `png`, `image/webp` → `webp`, `image/heic` et `image/heif` → `heic` |
| Vignette d'un DOCX | Cible interne de la relation `http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail` du paquet, relative à la racine |
| Vignette d'un ODT | `Thumbnails/thumbnail.png` (ODF 1.3, partie 2, §3.3) |
| Entrée chiffrée d'un ODT | Déclarée par `manifest:encryption-data` : comptée parmi les images, ni lue ni acheminée ; le document est dit chiffré |
| Dossier | Entrée dont le nom finit par `/` : ignorée |
| Déclarations illisibles | XML mal formé, entrée en double : non mené pour format partiel, une fois ; aucune entrée n'est alors déclarée |
| Bornes | Celles d'un PDF : seize parties extraites au plus, 2 Mio cumulés (ADR-0226) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, pour les deux questions, sans raison supplémentaire : celles présentées avec les options.
- Entrées, option B écartée : une image cachée resterait hors de l'outil.
- Entrées, option C écartée : la vignette ne vient pas de l'auteur.
- Format, option B écartée : deux reconnaissances, et l'écart entre déclaration et contenu perdu.

## Conséquences

- Une image qu'aucune déclaration ne cite n'est pas cherchée ; la fiche le dit dans ses limites.
- L'ordre des seize est celui du répertoire central : R-IMAGESBUREAU-003 le dit (ADR-0255).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création ; options choisies par TheDarkMac au début du complément de T81 |
