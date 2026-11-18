# ADR-0241 — Texte d'un DOCX ou d'un ODT analysé par le module `caracteres` ; positions par partie, paragraphe et caractère

- **Statut** : Accepté
- **Date** : 2026-11-18
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (forme des positions précisée par l'assistant)
- **Tâche** : T80 (complément bureautique)
- **Exigences liées** : F-73 ; ADR-0042, ADR-0061, ADR-0224, ADR-0232, ADR-0237

## Contexte

Le module `caracteres` (T80) analyse un texte brut, lu par blocs et localisé en octets, ligne et colonne. Le texte d'un DOCX ou d'un ODT est décodé de parties XML compressées : il n'est pas une plage d'octets du fichier. Il fallait dire où brancher l'analyse, et comment localiser un caractère.

## Options envisagées

### Option A — Module `caracteres` étendu (recommandée)

Le module traite aussi les formats `docx` et `odt` : il en extrait le texte par les lecteurs ZIP et XML du projet et lui applique la même analyse ; mêmes observations, mêmes règles. Positions : partie de l'archive, numéro de paragraphe, colonne. Version 0.2.0.

- Avantages : une analyse, un vocabulaire, des règles uniques ; le rapport d'un DOCX se lit comme celui d'un texte.
- Inconvénients : le module lit maintenant des archives, avec expat.

### Option B — Nouveau module `caracteresbureau`

- Avantages : chaque module lit un seul genre de fichier.
- Inconvénients : observations sous un autre préfixe, règles du catalogue doublées.

### Option C — Parties extraites (ADR-0224)

- Avantages : le mécanisme existe.
- Inconvénients : une partie extraite est une plage d'octets du fichier ; le texte décodé d'un XML ne l'est pas. Il faudrait élargir ADR-0224.

## Décision

Option A. Précisions de l'assistant :

- `caracteres` 0.2.0 : formats `texte`, `docx`, `odt` ; bibliothèque `expat` au manifeste (ADR-0120). L'extraction est dans `modules/caracteres/_bureau.py` ; l'analyse de T80 s'applique à chaque paragraphe comme à un segment.
- Position d'un relevé : « partie, paragraphe N, caractère C », où N compte les paragraphes de la partie à partir de 1 et C les points de code du paragraphe à partir de 1, suivi de « texte supprimé » (ADR-0240) ou « texte masqué » (ADR-0242) s'il y a lieu ; plage d'octets : la partie entière dans l'archive, en-tête local compris.
- Observations propres aux documents : `caracteres.parties` (noms des parties lues), `caracteres.supprimes`, `caracteres.masques` (caractères), `caracteres.longueur` ; pas de `caracteres.encodage`. Une marque d'ordre (U+FEFF) n'est jamais ordinaire dans un paragraphe.
- Le manifeste C2PA d'un texte reste cherché dans le texte brut seul (`M-C2PA-TEXTE`, format `texte`) : un DOCX ou un ODT porte le sien dans son archive (`M-C2PA`). Une enveloppe trouvée dans un paragraphe est décrite comme dans un texte.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : deux vocabulaires pour une même analyse.
- Option C écartée : ADR-0224 suppose une plage d'octets.
- Partie et paragraphe plutôt que ligne et colonne : un saut de ligne dans un paragraphe est rare, la partie et le paragraphe se retrouvent dans le logiciel.

## Conséquences

- Le module rejoint les modules qui lisent par expat ; la version d'expat figure aux versions des bibliothèques d'une analyse où il est actif.
- Le complément de T53 pourra acheminer la couche texte d'un PDF vers le même module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-18 | Création ; option choisie par TheDarkMac au début du complément de T80 |
