# ADR-0136 — Un module par famille de propriétés bureautiques : `ooxml` et `odf`

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21 (complément bureautique)
- **Exigences liées** : F-10, F-25, F-82, NF-03, NF-10 ; ADR-0114, ADR-0123, ADR-0131

## Contexte

ADR-0123 laisse à un dernier complément de T21 les propriétés des documents DOCX et ODT, et ADR-0114 y annonçait « ses propres modules pour […] les propriétés bureautiques ». Les deux formats sont des archives ZIP de parties XML, mais leurs métadonnées relèvent de deux normes distinctes : les propriétés d'un paquet OPC (ECMA-376), réparties en trois parties (principales, étendues, personnalisées), et l'entrée `meta.xml` d'OpenDocument (OASIS). Il fallait dire combien de modules les lisent.

## Options envisagées

### Option A — Un module par famille

`ooxml` pour DOCX (`docProps/core.xml`, `app.xml`, `custom.xml`), `odf` pour ODT (`meta.xml`, propriétés utilisateur comprises).

- Avantages : même logique qu'ADR-0114 et ADR-0131 ; une erreur dans un module ne fait perdre que sa famille ; la couverture dit ce qui a été lu ; chacun se désactive seul ; un futur tableur ou une présentation (OOXML, ODF) rejoindrait le module de sa famille.
- Inconvénients : deux manifestes et deux fiches.

### Option B — Un seul module `bureautique`

- Avantages : un manifeste.
- Inconvénients : une erreur fait perdre les deux familles (NF-03) ; la couverture est moins précise (F-25) ; option B déjà écartée par ADR-0114 et ADR-0131.

### Option C — Un module par partie

Modules distincts pour les propriétés principales, étendues, personnalisées et pour `meta.xml`.

- Avantages : isolation plus fine.
- Inconvénients : quatre modules pour quelques dizaines de propriétés, et les trois premiers relisent les mêmes relations du paquet.

## Décision

Option A : modules `ooxml` et `odf`, version 0.1.0, sans dépendance entre eux (`requiert = []`), bibliothèque `expat` (ADR-0120). Lecteurs communs dans `modules/_lecture/` : `zip` (ADR-0137), `arbre` (XML par expat, déplacé de `xmp` sans changement de comportement, ADR-0116), `proprietes` (valeurs typées et rangement des propriétés, ADR-0140).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : isolation des erreurs et couverture moins précises.
- Option C écartée : découpage sans gain réel, pour des parties lues par le même parcours.
- Lecture du XML déplacée dans `arbre` : `xmp`, `ooxml` et `odf` lisent le XML avec les mêmes refus ; une seule copie du code qui les applique.

## Conséquences

- La couverture d'un DOCX liste `ooxml`, celle d'un ODT `odf` ; les autres modules y sont non applicables.
- La rubrique Versions d'un rapport cite expat dès que `xmp`, `ooxml` ou `odf` est actif, même sur un format qu'ils ne lisent pas (ADR-0120 : bibliothèques des modules actifs).
- F-10 est réalisée pour tous les formats du périmètre qui portent des métadonnées (le texte brut n'en a pas).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; découpage choisi par TheDarkMac au début du complément |
