# ADR-0252 — Module `imagesbureau` pour les images d'un DOCX ou d'un ODT ; F-63 étendue par A-24

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (exigence et manifeste précisés par l'assistant)
- **Tâche** : complément de T81
- **Exigences liées** : F-63, F-82 ; A-24 ; ADR-0224, ADR-0228, ADR-0248

## Contexte

A-24 relevait qu'un DOCX ou un ODT est un conteneur, dont les images ne passent par aucun module d'image, alors que celles d'un PDF y passent (F-63, T53). ADR-0248 a renvoyé ces images à un complément de T81, sur sa propre branche et sa propre PR. Au début du complément, trois modules lisent déjà l'archive d'un DOCX ou d'un ODT pour leur propre compte : `actifsbureau` (éléments actifs, F-62), `caracteres` (texte, F-73) et `historique` (historique d'édition, F-71) ; `imagespdf` extrait les JPEG d'un PDF comme des parties extraites (ADR-0224).

## Options envisagées

### Option A — Un nouveau module `imagesbureau` (recommandée)

Symétrique d'`imagespdf`, comme `actifsbureau` l'est d'`actifspdf` (ADR-0228) : formats `docx` et `odt`, contenus extraits `jpeg`, `png`, `webp`, `heic`.

- Avantages : un module par sujet ; les modules existants restent dans leur exigence ; la couverture dit à part si les images ont été cherchées.
- Inconvénients : une lecture de plus du répertoire central de l'archive.

### Option B — Dans `historique`

- Avantages : le module de T81 lit déjà l'archive.
- Inconvénients : il sortirait de F-71.

### Option C — Dans `actifsbureau`

- Avantages : il lit déjà les déclarations de l'archive (relations, manifeste).
- Inconvénients : il sortirait des éléments actifs (F-62).

## Décision

Option A. Précisions de l'assistant :

| Élément | Valeur |
| --- | --- |
| Identifiant | `imagesbureau` (images d'un document bureautique, comme `actifsbureau`) |
| Formats | `docx`, `odt` |
| Exigence | F-63, étendue au DOCX et à l'ODT par A-24, sans nouvel identifiant d'exigence : la matrice le dit dans la note de F-63, qui gagne la tâche T81 |
| Bibliothèque | `expat`, pour les types de contenu et le manifeste |
| Contenus extraits | `jpeg`, `png`, `webp`, `heic` : les formats que lisent les modules d'image |
| Constats | Aucun du module ; règles « moteur » du catalogue (ADR-0255) |
| Fiche | [`images-bureau`](../techniques/images-bureau.md) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : hors de F-71.
- Option C écartée : hors de F-62.
- Pas de nouvel identifiant d'exigence : le cahier des charges v0.1 reste la référence des identifiants, et A-24 demandait une exigence « symétrique de F-63 », que la note de F-63 décrit.

## Conséquences

- A-24 est traité en entier : modifications suivies et identifiants de révision par `historique` (ADR-0248), images par `imagesbureau`.
- Les listes de modules codées dans les tests reçoivent `imagesbureau`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création ; option choisie par TheDarkMac au début du complément de T81 |
