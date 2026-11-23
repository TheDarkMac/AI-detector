# ADR-0224 — Contenu extrait d'un fichier : une partie extraite, analysée comme une partie, numérotée à la suite

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (mécanisme, protocole et vérifications précisés par l'assistant)
- **Tâche** : T53
- **Exigences liées** : F-63, F-25, F-82, NF-03, NF-06, NF-10, ES-04 ; ADR-0042, ADR-0060, ADR-0061, ADR-0062, ADR-0064, ADR-0070, ADR-0071, ADR-0223

## Contexte

ADR-0042 prévoit qu'un module qui a besoin du résultat d'un autre (images extraites d'un PDF, T53) le déclare, et que l'acheminement se fasse dans le même processus de travail. Jusqu'à T53, un module ne lit que sa partie du fichier, par position (ADR-0061, ADR-0071) ; les modules d'image lisent une partie au format JPEG, PNG, WebP ou HEIC.

Une image JPEG d'un PDF, au seul filtre `DCTDecode`, est un JPEG complet écrit tel quel dans le fichier (ADR-0225) : sa plage d'octets se lit comme une partie. Il fallait dire qui la trouve, qui la reconnaît, comment les modules d'image s'y appliquent, et comment le rapport la montre.

## Options envisagées

### Option A — Partie extraite, à part dans l'identification (recommandée)

Une image extraite devient une **partie extraite** : rang à la suite des parties reconnues, format, plage, fin logique, et une **origine** (partie qui la contient, module qui l'a trouvée, page et objet). Elle est rangée dans une liste à part de l'identification ; les modules s'y appliquent comme à une partie, couverture comprise.

- Avantages : tout ce qui vaut pour une partie vaut pour elle (couverture par partie, règles, marquages, techniques hors V1, non menées) ; les polyglottes et les octets non reconnus restent ceux de l'identification.
- Inconvénients : nouvelle forme au schéma (0.10.0) ; un nouveau message du protocole.

### Option B — Résultats rattachés à la partie du PDF

Les modules d'image s'appliquent à la plage de l'image, mais leurs résultats sont rangés sous la partie du PDF, avec page et objet en localisation.

- Avantages : pas de nouvelle forme.
- Inconvénients : la couverture ne distingue plus un module appliqué au document de celui appliqué à ses images ; la numérotation des observations et le contrôle des constats par partie (ADR-0071) ne tiennent plus.

## Décision

Option A. Précisions de l'assistant :

| Étape | Où | Ce qui est fait |
| --- | --- | --- |
| Déclaration | Manifeste | Champ `extrait` : formats que le module peut extraire (vide pour les autres) ; validé par le schéma, formats du périmètre seulement (ADR-0064) |
| Extraction | Module, par le contexte | `Contexte.extraire(format, plage, localisation)` : plage relative à la partie, localisation sans plage (page, objet) ; refusée pour un format hors du manifeste, une plage hors de la partie, ou une partie elle-même extraite ; faux si le fichier n'a plus de place (ADR-0226) |
| Reconnaissance | Moteur | Après le module, s'il n'a pas levé d'exception (ADR-0060) : la plage est reconnue par l'identification (`identification.reconnaitre`), comme une partie (ADR-0070) ; un contenu d'un autre format, ou non reconnu, est déclaré non mené pour `format_partiel`, localisé dans son contenant |
| Annonce | Protocole | Message `extraction`, une fois, après les modules des parties reconnues et avant les versions : les parties extraites, dans l'ordre |
| Analyse | Moteur | Chaque module actif sur chaque partie extraite, comme sur une partie (messages « module » compris) ; une partie extraite n'est pas extraite à son tour |
| Contrôle | Processus principal | Rangs à la suite, plage dans le contenant, contenant reconnu et analysé, module actif terminé sur lui sans résultats écartés, format cité par son `extrait` ; tout écart arrête le travail (`message_invalide`, ES-04) |
| Rapport | Identification | Liste `extraites` (au plus 16), à côté de `parties` ; signalement, tableau « Parties extraites » avec l'origine, ligne de la commande ; couverture, techniques hors V1 et marquages pour chaque partie, extraite comprise |

- La fin logique d'une partie extraite est cherchée dans la plage que son module lui donne ; ce qui la suit dans le flux n'est pas déclaré non reconnu.
- Une partie extraite tronquée est déclarée non menée pour `fichier_tronque`, comme une partie reconnue.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : la couverture, la numérotation et le contrôle des constats perdraient leur partie.
- Reconnaissance par l'identification plutôt que par le module : le module ne lit que la structure du PDF ; c'est le code qui reconnaît déjà chaque partie, fuzzé depuis T14, qui dit si les octets sont un JPEG.
- Numérotation à la suite des parties : une partie reste désignée par un seul entier dans tous les résultats.

## Conséquences

- `VERSION_SCHEMA` passe à 0.10.0 : `partie_extraite` et `origine` au schéma du rapport, message `extraction` au schéma des messages ; les parties reconnues gardent leur forme.
- Tous les manifestes portent `extrait` ; seul `imagespdf` en cite un format (`jpeg`).
- Un module qui extraira un autre contenu (texte d'un PDF, complément de T53 ; images clés d'une vidéo, T71) passera par le même mécanisme, et le dira dans son manifeste.
- ADR-0061 n'est pas élargi : chaque constat ne cite toujours que des observations de son module et de sa partie (ADR-0223).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T53 |
| 2026-11-19 | Renvoi : le texte d'un PDF n'est pas une plage d'octets ; il est lu par le module `caracteres` et ne passe pas par les parties extraites, contrairement à ce qu'annonçaient les conséquences ([ADR-0243](ADR-0243-couche-texte-d-un-pdf-dans-le-module-caracteres.md)) (complément de T53) |
| 2026-11-23 | Renvoi : un contenu compressé dans le fichier (entrée deflate d'un DOCX) est remis décompressé par son module et analysé en mémoire ; la plage de la partie extraite est celle des données compressées, son origine dit sa décompression ([ADR-0254](ADR-0254-parties-extraites-decompressees.md)) (complément de T81) |
