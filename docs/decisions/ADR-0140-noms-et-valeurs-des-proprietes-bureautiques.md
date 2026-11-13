# ADR-0140 — Noms et valeurs des propriétés de DOCX et d'ODT

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : proposition de l'assistant, à valider par TheDarkMac pendant la revue de la PR du complément
- **Tâche** : T21 (complément bureautique)
- **Exigences liées** : F-10, F-14, ES-13, NF-06, NF-11 ; ADR-0057, ADR-0117, ADR-0118, ADR-0119, ADR-0128, ADR-0133

## Contexte

ADR-0117 fixe la forme des noms d'observation (nom tiré de la norme, préfixé par la famille ; préfixe XML déduit de l'adresse de l'espace, jamais celui qu'écrit le fichier), ADR-0118 celle des valeurs, ADR-0119 le marquage des données identifiantes, ADR-0128 et ADR-0133 les dates (telles qu'écrites). Les propriétés d'un DOCX sont des éléments XML de trois parties, celles des propriétés étendues sans préfixe ; les propriétés personnalisées et les propriétés utilisateur d'un ODT sont nommées par le document ; plusieurs valeurs sont typées par leur schéma (entiers, booléens) ou par le document (`docPropsVTypes`, `meta:value-type`).

## Options envisagées

### Option A — Noms de la norme, préfixés par la famille et la partie ; valeurs dans le type du schéma

| Module | Nom | Partie variable |
| --- | --- | --- |
| Les deux | `<famille>.present`, `<famille>.blocs` | Comme ADR-0117 |
| `ooxml` | `ooxml.core.<préfixe>:<nom>` | Élément de `coreProperties` ; préfixes `cp`, `dc`, `dcterms`, `dcmitype` |
| `ooxml` | `ooxml.app.<nom>` | Élément des propriétés étendues, sans préfixe (espace par défaut de la partie) |
| `ooxml` | `ooxml.custom.<nom>` | Attribut `name` d'une propriété personnalisée |
| `odf` | `odf.<préfixe>:<nom>`, `odf.<préfixe>:<nom>.<préfixe>:<attribut>` | Enfant d'`office:meta` et ses attributs ; préfixes `office`, `meta`, `dc` |
| `odf` | `odf.meta:user-defined.<nom>` | Attribut `meta:name` |
| `odf` | `odf.version` | `office:version` de `meta.xml` |
| Les deux | `<famille>.espace.ns<k>` ; `<nom>.taille`, `<nom>.longueur` | Comme ADR-0117 et ADR-0118 |

- Partie tirée du fichier (nom local, nom d'une propriété personnalisée) : règle des composants d'ADR-0117.
- Textes tels qu'écrits, encodage du document XML ; entiers et booléens de XML Schema pour les propriétés que le schéma type ainsi (propriétés étendues `TotalTime`, `Pages`, `Words`… et `ScaleCrop`, `SharedDoc`… ; `meta:editing-cycles`, attributs de `meta:document-statistic`) ; type `docPropsVTypes` d'une propriété personnalisée, `meta:value-type` d'une propriété utilisateur (réel pour `float` et `percentage`, booléen pour `boolean`) ; une écriture que le type n'admet pas reste un texte ; un entier hors des 64 bits signés, un réel non fini, en texte (ADR-0118).
- Listes : `vt:vector` et `vt:array` (même d'un élément), élément répété (`meta:keyword`, propriété écrite deux fois) ; texte vide : rien n'est observé.
- Données binaires (`vt:blob`, `DigSig`…) : leur taille, base 64 décodée.
- Dates et durées : telles qu'écrites (W3CDTF, ISO 8601), sans conversion.
- Données identifiantes, liste fermée (ADR-0119) :
  - `metadonnee_nominative` : `ooxml.core.dc:creator`, `ooxml.core.cp:lastModifiedBy`, `ooxml.app.Company`, `ooxml.app.Manager` ; `odf.meta:initial-creator`, `odf.dc:creator`, `odf.meta:printed-by` ;
  - `nom_de_fichier` : `ooxml.app.Template`, `ooxml.app.HyperlinkBase`.

- Avantages : noms des normes, que connaît un vérificateur ; un fichier ne choisit pas le nom d'une propriété connue ; la partie d'un DOCX est dans le nom, ce qui distingue `dc:creator` (auteur) de `cp:lastModifiedBy` et de `app.Company` ; une règle de T81 compare `TotalTime` ou `meta:editing-cycles` comme des nombres.
- Inconvénients : les mêmes informations portent des noms différents dans les deux familles (`ooxml.app.Application`, `odf.meta:generator`) ; les règles de T22 citent les deux.

### Option B — Noms communs aux deux familles (`bureautique.Auteur`, `bureautique.Logiciel`)

- Avantages : une seule règle par information.
- Inconvénients : table d'équivalences qui interprète déjà (l'auteur ODT est-il `initial-creator` ou `creator` ?) ; contraire à ADR-0117 (la norme fait foi).

### Option C — Toutes les valeurs en texte

- Avantages : aucune conversion, « telles qu'écrites » au sens strict.
- Inconvénients : une règle de T81 sur le temps d'édition devrait convertir elle-même ; écart avec les autres modules, qui observent leurs nombres comme des nombres.

## Décision

Option A.

## Raisons

- Option A : même principe qu'ADR-0117 et ADR-0133 ; le type de la norme est une information du fichier, non une interprétation.
- Option B écartée : interprétation prématurée et noms hors norme.
- Option C écartée : écart sans gain avec les autres modules ; un texte mal typé reste visible tel qu'écrit.
- `cp:revision` et `AppVersion` restent des textes : le schéma les déclare ainsi.
- `Template` et `HyperlinkBase` marqués nom de fichier : le premier nomme le modèle, souvent avec son chemin local ; le second est un chemin ou une adresse, qui peut nommer un poste ou un partage.
- Titres, mots-clés, propriétés personnalisées et utilisateur non marqués : textes libres, comme ADR-0119 (T25).

## Conséquences

- Les règles de T22 (générateurs : `ooxml.app.Application`, `ooxml.app.AppVersion`, `odf.meta:generator`), de T23 (dates) et de T81 (`ooxml.app.TotalTime`, `ooxml.core.cp:revision`, `odf.meta:editing-cycles`, `odf.meta:editing-duration`) citent ces noms.
- Un changement de nom est un changement de version du module et des règles qui le citent.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
