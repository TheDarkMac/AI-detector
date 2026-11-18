# ADR-0232 — Périmètre de T80 : texte brut et texte collé, module `caracteres` ; corps des DOCX et ODT renvoyé à un complément

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (nom du module précisé par l'assistant)
- **Tâche** : T80
- **Exigences liées** : F-73, F-24, F-25 ; A-29, A-43 ; ADR-0013, ADR-0074, ADR-0223

## Contexte

F-73 demande de relever les caractères invisibles ou substitués : caractères de largeur nulle, homoglyphes. ADR-0013 range F-73 dans le module texte de la V1, pour le texte brut, le DOCX, l'ODT et le texte collé ; ADR-0074 a renvoyé à T80 la saisie du texte collé ; ADR-0223 a renvoyé la couche texte d'un PDF à un complément de T53, fait après T80. L'inventaire des marquages (T31, ADR-0177) attend aussi de T80 le lecteur du manifeste C2PA écrit dans un texte (`M-C2PA-TEXTE`, annexe A.7 de la spécification C2PA 2.3), qui s'écrit justement en caractères invisibles. Il fallait fixer ce que T80 lit.

Au début de T80, aucun module ne lit le corps d'un DOCX ou d'un ODT : `ooxml` et `odf` en lisent les propriétés (ADR-0139), `actifsbureau` les relations et les éléments actifs (ADR-0229).

## Options envisagées

### Option A — Texte brut et texte collé ; manifeste C2PA décrit (recommandée)

Un module lit le texte brut, enregistré dans un fichier ou collé. Le corps des DOCX et des ODT est renvoyé à un complément de T80, la couche texte d'un PDF au complément de T53 déjà prévu. Le manifeste C2PA d'un texte est cherché, trouvé et décrit ; sa signature n'est pas vérifiée (ADR-0236).

- Avantages : T80 reste centrée sur l'analyse des caractères ; la lecture du corps d'un document bureautique (paragraphes, notes, en-têtes, commentaires) arrive dans sa propre PR, comme les compléments de T21, T40 et T52 ; le marquage `M-C2PA-TEXTE` devient recherché.
- Inconvénients : un DOCX ou un ODT n'a pas encore de relevé de ses caractères.

### Option B — Texte brut, texte collé, DOCX et ODT

- Avantages : F-73 couverte pour tous les formats texte dès T80.
- Inconvénients : T80 grossit d'autant et mêle deux sujets, la lecture bureautique et l'analyse des caractères (découpage, §1).

### Option C — Texte brut et texte collé, sans le manifeste C2PA

- Avantages : T80 plus courte.
- Inconvénients : `M-C2PA-TEXTE` reste « lecteur à venir », alors que sa recherche se confond avec celle des sélecteurs de variante, qu'il faut de toute façon relever.

## Décision

Option A. Précision de l'assistant : le module s'appelle **`caracteres`** (caractères invisibles ou substitués, titre de F-73). Il traite le format `texte` (ADR-0070), qu'il vienne d'un fichier ou d'un texte collé (ADR-0233), et cherche le marquage `M-C2PA-TEXTE`.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : deux sujets dans une tâche, contre le §1 du découpage.
- Option C écartée : le lecteur de l'enveloppe C2PA tient en quelques dizaines de lignes une fois les sélecteurs de variante relevés.
- Nom `caracteres` plutôt que `invisibles` : le module relève aussi les homoglyphes, qui sont visibles.

## Conséquences

- Un complément de T80, sur sa propre branche et sa propre PR, lira le corps des DOCX et des ODT et y appliquera la même analyse ; il s'ajoute à l'ordre de la V1 après T80 (découpage, §4).
- Le complément de T53 (couche texte d'un PDF) pourra acheminer le texte vers le module `caracteres`.
- La stylométrie (T82) et les références (T83) restent hors V1 (ADR-0013) et figurent, non menées, à la couverture d'un texte.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T80 |
