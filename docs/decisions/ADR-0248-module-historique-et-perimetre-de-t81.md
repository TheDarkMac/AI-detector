# ADR-0248 — Module `historique` pour T81 ; images d'un DOCX ou d'un ODT renvoyées à un complément

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (nom du module précisé par l'assistant)
- **Tâche** : T81
- **Exigences liées** : F-71, F-63 ; A-24 ; ADR-0013, ADR-0139, ADR-0140, ADR-0228, ADR-0240

## Contexte

F-71 demande l'historique d'édition des documents bureautiques, temps d'édition et sessions de révision, une valeur absente ou nulle restant une information neutre. ADR-0013 l'a mise en V1, en T81, et lui a renvoyé deux questions : l'extension de F-71 aux modifications suivies, et l'extraction des images d'un DOCX ou d'un ODT vers les modules d'image (A-24, symétrique de F-63 pour le PDF). ADR-0139 a laissé à T81 les identifiants de révision et les modifications suivies ; ADR-0240, les auteurs et les dates des modifications.

Au début de T81, les modules `ooxml` et `odf` observent déjà, sans les interpréter, `TotalTime`, `cp:revision`, `meta:editing-cycles` et `meta:editing-duration`, la dernière telle qu'écrite (ADR-0140) ; aucun module ne lit les identifiants de session de Word ou de LibreOffice, ni les auteurs et dates des modifications et des commentaires.

## Options envisagées

### Ce qui est lu

#### Option A — Un module `historique` (recommandée)

Un module pour le DOCX et l'ODT, qui lit pour son propre compte temps d'édition et enregistrements, sessions d'édition (identifiants de révision des réglages et du corps), modifications suivies et commentaires (nombre, auteurs, dates), comme `actifsbureau` lit pour son compte les parties qui le concernent (ADR-0228, ADR-0229).

- Avantages : F-71 couverte en entier, sessions et modifications suivies comprises ; `ooxml` et `odf` restent ce que fixe F-10 ; une durée lue en nombre, comparable entre les deux formats.
- Inconvénients : les propriétés de temps et de révisions sont lues deux fois, par `ooxml` ou `odf` et par `historique`.

#### Option B — Des règles seules

Aucune nouvelle lecture : des règles du catalogue sur les quatre propriétés déjà observées.

- Avantages : plus court ; aucun code de lecture.
- Inconvénients : ni sessions ni modifications suivies, qu'ADR-0013 et ADR-0139 renvoyaient pourtant à T81 ; la durée d'un ODT, écrite en `xsd:duration`, ne se compare pas sans une lecture nouvelle du moteur (ADR-0140).

#### Option C — Étendre `ooxml` et `odf`

- Avantages : un module par format.
- Inconvénients : les deux modules de propriétés sortent de F-10 (ADR-0139) pour lire réglages et corps, et grossissent d'autant.

### Images d'un DOCX ou d'un ODT (A-24)

#### Option A — Un complément de T81 (recommandée)

Sur sa propre branche et sa propre PR, après T81, avec les parties extraites de T53 (routage vers les modules d'image, ADR-0224).

- Avantages : T81 reste centrée sur l'historique ; un sujet par PR, comme les compléments de T21, T40, T52, T53 et T80.
- Inconvénients : les images d'un DOCX ou d'un ODT restent sans analyse jusqu'au complément.

#### Option B — Dans T81

- Avantages : A-24 fermé d'un coup.
- Inconvénients : deux sujets dans une tâche (découpage, §1).

#### Option C — Candidate V2

- Avantages : V1 plus courte.
- Inconvénients : une image générée collée dans un document bureautique reste hors de l'outil en V1 ; elle figure seulement, non menée, à la couverture (F-82).

## Décision

- Ce qui est lu : option A. Précision de l'assistant : le module s'appelle **`historique`** (historique d'édition, titre de F-71) ; formats `docx` et `odt`, bibliothèque `expat`, exigence F-71. Les parties lues sont celles d'[ADR-0249](ADR-0249-historique-lu-dans-un-docx-et-un-odt.md).
- Images : option A, un complément de T81 ajouté à l'ordre de la V1 (découpage, §4).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, pour les deux questions, sans raison supplémentaire : celles présentées avec les options.
- Ce qui est lu, option B écartée : laisserait sessions et modifications suivies, renvoyées à T81, sans lecteur.
- Ce qui est lu, option C écartée : hors de F-10 pour `ooxml` et `odf`, contre ADR-0139.
- Images, option B écartée : deux sujets dans une tâche.
- Images, option C écartée : la symétrie avec F-63, que demandait A-24, se ferait attendre au-delà de la V1.

## Conséquences

- `ooxml` et `odf` ne changent pas : ils observent toujours les propriétés telles qu'écrites.
- Un complément de T81, sur sa propre branche et sa propre PR, extraira les images d'un DOCX et d'un ODT vers les modules d'image.
- A-24 reste « non tranché » au registre des arbitrages jusqu'à ce complément ; la partie « modifications suivies » de son traitement est faite.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création ; options choisies par TheDarkMac au début de T81 |
| 2026-11-23 | Renvoi : images d'un DOCX ou d'un ODT extraites par le module `imagesbureau` ; A-24 tranché ([ADR-0252](ADR-0252-module-imagesbureau.md) à [ADR-0255](ADR-0255-constats-et-versions-du-complement-de-t81.md)) (complément de T81) |
