# ADR-0139 — Parties lues dans un DOCX et dans un ODT

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : proposition de l'assistant, à valider par TheDarkMac pendant la revue de la PR du complément
- **Tâche** : T21 (complément bureautique)
- **Exigences liées** : F-10, F-14, F-71, F-82 ; ADR-0127, ADR-0132, ADR-0136, ADR-0138

## Contexte

F-10 demande « les propriétés (documents bureautiques) ». Un DOCX en a trois parties, que le paquet désigne par ses relations : principales, étendues, personnalisées ; un ODT les range dans `meta.xml`. Les deux formats portent aussi, ailleurs, des informations voisines : identifiants de révision et modifications suivies dans le corps, réglages de l'application, signatures, vignette. Comme pour le PDF (ADR-0127) et les conteneurs audio et vidéo (ADR-0132), il faut dire ce qui est lu, ce qui ne l'est pas, et comment les parties sont trouvées.

## Options envisagées

### Option A — Les parties de propriétés seules, trouvées comme le font les logiciels

- DOCX : relations du paquet (`_rels/.rels`), types transitionnels et stricts d'ECMA-376 et type des premières versions d'Office 2007 ; cible résolue depuis la racine du paquet, noms de parties comparés sans la casse ASCII (OPC) ; première relation de chaque sorte.
- ODT : entrée `meta.xml`, nom fixé par OpenDocument, comparé avec sa casse ; enfants d'`office:meta`, et version d'OpenDocument de sa racine.

- Avantages : exactement ce que montre la boîte « Propriétés » d'un traitement de texte ; un DOCX qui range ses propriétés ailleurs que dans `docProps/` est lu comme Word le lit.
- Inconvénients : un paquet sans relations n'a pas de propriétés au sens d'OPC, même si `docProps/core.xml` existe.

### Option B — Noms d'entrées usuels (`docProps/core.xml`…), sans les relations

- Avantages : plus simple ; lit un paquet aux relations abîmées.
- Inconvénients : ce n'est pas ce que lisent les logiciels ; un fichier peut montrer à l'outil une partie que Word ignore, et cacher celle que Word affiche.

### Option C — Aussi le corps, les réglages et les signatures

- Avantages : couverture plus large (identifiants de révision `w:rsid`, `settings.xml`).
- Inconvénients : relève de l'historique d'édition (F-71, T81) et de la structure (T52) ; le corps est la partie la plus grosse et la plus variée à lire.

## Décision

Option A. Ne sont pas lus, et chaque fiche le dit : le corps et ses relations (`word/document.xml`, `content.xml`, `styles.xml`), les réglages (`word/settings.xml`, `settings.xml`), la liste des liens (`HLinks`) et les références `xlink` (ADR-0138), la vignette, le manifeste (`META-INF/manifest.xml`, `manifest.rdf`), les signatures, les identifiants de révision et modifications suivies.

- Une relation de propriétés externe, sans cible ou en double est non menée (format partiel) ; une cible absente de l'archive est une référence manquante.
- `ooxml.present` est vrai dès qu'une relation désigne une partie de propriétés ; `odf.present`, dès que `meta.xml` existe. Un `meta.xml` absent n'est pas une analyse non menée : OpenDocument ne l'exige pas.

## Raisons

- Option A : elle répond à F-10 pour ce que le document déclare de lui-même, comme ADR-0127 et ADR-0132 ; le fichier ne peut pas faire lire à l'outil d'autres propriétés que celles qu'un traitement de texte affiche.
- Option B écartée : écart possible entre ce que lit l'outil et ce que voit l'utilisateur.
- Option C écartée : hors de F-10 ; T81 et T52 en sont chargées.
- Temps d'édition, nombre de révisions, cycles et durée d'édition (`TotalTime`, `cp:revision`, `meta:editing-cycles`, `meta:editing-duration`) : ce sont des propriétés, donc lues ici ; leur interprétation est celle de F-71, en T81.

## Conséquences

- Les fiches `metadonnees-ooxml` et `metadonnees-odf` listent les parties lues et non lues.
- T81 lira les identifiants de révision et les modifications suivies, et pourra s'appuyer sur les observations de temps et de cycles d'édition.
- Lire une partie de plus demandera un nouvel ADR et une nouvelle version du module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
