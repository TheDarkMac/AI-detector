# ADR-0243 — Couche texte native d'un PDF analysée par le module `caracteres` ; positions par page, ligne et caractère

- **Statut** : Accepté
- **Date** : 2026-11-19
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (forme des positions et lecteur des polices partagé précisés par l'assistant)
- **Tâche** : T53 (complément texte)
- **Exigences liées** : F-63, F-73 ; ADR-0042, ADR-0061, ADR-0213, ADR-0221, ADR-0223, ADR-0224, ADR-0241

## Contexte

ADR-0223 a renvoyé à un complément de T53 la couche texte native d'un PDF, « acheminée vers les modules texte », quand un module texte existerait. T80 a livré le module `caracteres` (format `texte`), et son complément l'a étendu au DOCX et à l'ODT (ADR-0241), dont le texte, décodé de parties XML compressées, n'est pas une plage d'octets du fichier.

Le texte d'un PDF ne l'est pas davantage : il se décode des flux de contenu des pages, compressés, par les polices (codes, CMap, encodages). ADR-0224 prévoyait pourtant, en conséquence, qu'un module qui extrairait le texte d'un PDF passerait par les parties extraites, qui sont des plages d'octets.

## Options envisagées

### Option A — Module `caracteres` étendu (recommandée)

Le module traite aussi le format `pdf` : il en tire le texte par un lecteur des polices partagé dans `modules/_lecture/` et lui applique la même analyse ; mêmes observations, mêmes règles. Version 0.3.0.

- Avantages : une analyse, un vocabulaire, des règles uniques pour le texte, le DOCX, l'ODT et le PDF ; positions par page et ligne, que l'on retrouve dans un lecteur.
- Inconvénients : le parcours ne suit pas la conséquence d'ADR-0224 ; le module lit maintenant des PDF.

### Option B — Parties extraites élargies

ADR-0224 serait élargi pour qu'une partie extraite porte un texte décodé en mémoire, acheminé vers `caracteres` comme un texte collé.

- Avantages : le parcours prévu par ADR-0223 et ADR-0224.
- Inconvénients : nouvelles formes au schéma et au protocole (0.12.0) ; positions perdues : un relevé ne dirait qu'une position dans le texte décodé, pas une page.

### Option C — Nouveau module `textepdf`

- Avantages : chaque module lit un seul genre de fichier.
- Inconvénients : observations sous un autre préfixe, règles du catalogue doublées.

## Décision

Option A. Précisions de l'assistant :

- `caracteres` 0.3.0 : formats `texte`, `docx`, `odt`, `pdf` ; exigence F-63 ajoutée au manifeste. La lecture du texte est dans `modules/caracteres/_pdf.py` ; l'analyse de T80 s'applique à chaque ligne comme à un segment.
- Les polices sont lues par `modules/_lecture/polices.py`, où la lecture de `pagespdf` (largeurs, encodages, 14 polices standard, ADR-0215) est déplacée sans changement, comme le parcours de l'arbre des pages l'a été en T52 (ADR-0221) ; ses tables `_polices14.py` passent dans `_lecture/`. Le texte d'un code s'y lit à part (ADR-0246) : `pagespdf` ne lit ni ne compte rien de plus, et sa version reste 0.1.0.
- Position d'un relevé : « page N, ligne L, caractère C » ; pour une annotation, « page N, annotation K, ligne L, caractère C » (son apparence) ou « page N, annotation K, commentaire, ligne L, caractère C » (son `/Contents`) ; suivie de « texte invisible » s'il y a lieu (ADR-0245). L compte les lignes qui portent du texte, à partir de 1, dans la page, l'apparence ou le commentaire ; C les points de code de la ligne, à partir de 1. Plage d'octets : les flux de contenu de la page (du premier au dernier), le flux de l'apparence, ou l'objet de l'annotation.
- Observations propres au PDF : `caracteres.pages`, `caracteres.pages_lues`, `caracteres.arret_avant_budget` (comme `pagespdf`, ADR-0213), `caracteres.non_decodes` (ADR-0246), `caracteres.texte_invisible` (ADR-0245), `caracteres.pages_sans_texte` et sa liste (ADR-0247) ; pas de `caracteres.encodage`. Une marque d'ordre (U+FEFF) n'est jamais ordinaire dans une ligne.
- Un document chiffré n'est pas lu (ADR-0126) : analyse non menée pour format partiel, « texte des pages (document chiffré) ».

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : le schéma changerait pour perdre la page d'un relevé.
- Option C écartée : deux vocabulaires pour une même analyse.
- Lecteur des polices partagé plutôt que copié : les largeurs et les encodages sont ceux que `pagespdf` lit et vérifie depuis T51 ; deux copies divergeraient.

## Conséquences

- La conséquence d'ADR-0224 sur le texte d'un PDF ne vaut plus : le texte n'est pas une partie extraite. Le mécanisme reste celui des contenus qui sont des plages d'octets (images, T71).
- F-63 est réalisée pour les images et le texte ; la matrice le dit.
- Le constat qui citerait les observations de deux modules reste ouvert (ADR-0223, architecture §12).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-19 | Création ; option choisie par TheDarkMac au début du complément de T53 |
