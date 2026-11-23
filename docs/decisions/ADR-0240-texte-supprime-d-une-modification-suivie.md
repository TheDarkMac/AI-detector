# ADR-0240 — Texte supprimé d'une modification suivie : analysé, ses positions le disent

- **Statut** : Accepté
- **Date** : 2026-11-18
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T80 (complément bureautique)
- **Exigences liées** : F-73, F-71 ; ADR-0013, ADR-0239

## Contexte

Le texte supprimé d'une modification suivie (`w:del` et `w:delText` d'un DOCX, `text:deletion` d'un ODT) reste dans le fichier sans s'afficher dans la version finale. Un caractère caché dans une suppression voyage avec le fichier. L'historique d'édition lui-même (auteurs, dates, sessions) relève de T81 (F-71).

## Options envisagées

### Option A — Analysé, signalé à part (recommandée)

Le texte supprimé est analysé ; chaque position dit qu'elle est dans un passage supprimé. Le reste de l'historique reste à T81.

- Avantages : rien de ce que porte le fichier n'échappe ; le lecteur sait qu'un caractère ne s'affiche pas.
- Inconvénients : un mot mêlé d'une suppression ancienne fait un constat sur du texte que plus personne ne voit.

### Option B — Version finale seule

- Avantages : le rapport porte sur ce qu'on lit.
- Inconvénients : une suppression peut cacher un caractère que l'analyse ne verrait pas.

### Option C — Analysé sans le distinguer

- Avantages : plus simple.
- Inconvénients : le rapport ne dit pas qu'un caractère ne s'affiche pas.

## Décision

Option A. Précisions de l'assistant : est supprimé le texte de `w:delText` et de tout `w:t` sous `w:del` ou `w:moveFrom` (texte déplacé, ôté de son ancienne place), et celui des paragraphes d'un `text:deletion` d'un ODT, rangé dans la région des modifications (`text:tracked-changes`) ; une position qui touche ce texte porte « texte supprimé ». Le nombre de caractères supprimés est observé (`caracteres.supprimes`), sans règle propre : le constat de chaque caractère suffit, et T81 dira l'historique.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : laisserait un endroit où cacher.
- Option C écartée : le lecteur doit savoir qu'un caractère ne s'affiche pas.

## Conséquences

- Dans un ODT, le texte supprimé a ses propres paragraphes, numérotés à leur place dans `content.xml` (la région des modifications précède le corps) ; dans un DOCX, il est dans son paragraphe.
- T81 lira auteurs et dates des modifications.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-18 | Création ; option choisie par TheDarkMac au début du complément de T80 |
| 2026-11-23 | Suite en T81 : modifications suivies comptées, auteurs comptés sans être lus, dates lues sans fuseau ([ADR-0250](ADR-0250-auteurs-comptes-et-dates-sans-fuseau.md)) ; le texte supprimé ne compte pas dans les sessions du texte ([ADR-0249](ADR-0249-historique-lu-dans-un-docx-et-un-odt.md)) |
