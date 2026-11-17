# ADR-0229 — Éléments actifs cherchés dans un DOCX et un ODT : macros, événements, objets, références hors de l'archive

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (parcours, types reconnus, références hors de l'archive et bornes précisés par l'assistant)
- **Tâche** : T52 (complément bureautique)
- **Exigences liées** : F-62, NF-01, ES-03, ES-06 ; menaces M-07, M-14 ; ADR-0137, ADR-0138, ADR-0139, ADR-0219, ADR-0221

## Contexte

Un traitement de texte exécute, active ou va chercher hors du document ce que le document lui désigne. Un DOCX le désigne par les relations de ses parties (ECMA-376, partie 2, §9) : projet VBA (`vbaProject`, [MS-OFFMACRO]), extension du ruban (`customUI`), contrôles ActiveX, objets OLE, documents incorporés, et toute relation dont la cible est hors de l'archive (`TargetMode="External"`), dont le modèle distant (`attachedTemplate`) qu'ADR-0138 n'a pas signalé. Un ODT range ses macros dans `Basic/` et `Scripts/`, ses événements dans `content.xml` (vérifié avec LibreOffice 25.2.3.2 : `office:scripts` / `office:event-listeners`, `dom:load` pour l'ouverture), ses objets et ses références dans `content.xml` et `styles.xml`, son modèle et son rechargement dans `meta.xml`. ADR-0139 a exclu ces parties de la lecture des propriétés et demandé un ADR pour en lire une de plus.

## Options envisagées

### Option A — Macros, objets, événements et références hors de l'archive, trouvés comme le logiciel les trouve (recommandée)

- DOCX : relations du paquet, puis de chaque partie qu'elles désignent, de proche en proche ; le corps n'est lu que par ses relations.
- ODT : noms des entrées (`Basic/`, `Scripts/`), événements, objets, connexions DDE et références `xlink:href` de `content.xml` et `styles.xml`, modèle et rechargement de `meta.xml`, types des documents incorporés dans `META-INF/manifest.xml`.

- Avantages : chaque élément compté est un élément que le logiciel exécute, active ou charge ; aucune partie lourde du DOCX n'est lue.
- Inconvénients : les codes de champ du corps d'un DOCX (`DDEAUTO`, `INCLUDEPICTURE`, `INCLUDETEXT`) ne sont pas lus ; le `content.xml` d'un ODT, la plus grosse de ses parties, l'est.

### Option B — Idem, plus les codes de champ du corps d'un DOCX

- Avantages : plus complet pour M-07 (champ `DDEAUTO`, procédé connu).
- Inconvénients : lit `word/document.xml`, ses en-têtes, pieds et notes, les parties les plus grosses ; reconnaître un champ demande de recoller son code, écrit en morceaux (`w:instrText`) ; une PR bien plus grosse.

### Option C — Le minimum d'ADR-0219

Macros VBA et Basic, objets OLE, modèle distant d'un DOCX.

- Avantages : le plus petit.
- Inconvénients : ni les événements qui lancent une macro à l'ouverture, ni les autres ressources chargées sans geste de l'utilisateur (image liée, cadre), qui sont l'essentiel de M-07 et M-14.

## Décision

Option A. Précisions de l'assistant :

- DOCX. Au niveau du paquet, seules la partie principale (`officeDocument`) et l'extension du ruban sont suivies : les propriétés, la vignette et les signatures ne portent rien d'actif. Les relations de chaque partie sont lues une fois, sans récursion ; une partie désignée deux fois n'est suivie qu'une fois. Types reconnus dans les espaces transitionnel et strict d'ECMA-376 et dans ceux de Microsoft (2006, 2007). Dans l'archive : `vbaProject`, `ui/extensibility`, `control`, `oleObject`, `package` ; un `package` désigné par un graphique en porte les données et n'est pas compté ; un élément dont la partie manque à l'archive est une référence manquante, non compté. Hors de l'archive : toute relation, nature selon son type (tableau de la fiche `actifs-bureau`), `autre` pour un type inconnu.
- ODT. Une bibliothèque Basic compte si elle a une entrée autre que ses index (`script-lb.xml`, `script-lc.xml`, `dialog-lb.xml`, `dialog-lc.xml`) ; les scripts comptent par dossier de langage. Un `script:event-listener` sous `office:scripts` de la racine est un événement du document, levé à l'ouverture pour `dom:load`, `office:new`, `office:create`, `office:load-finished`, `office:view-created`, `office:layout-finished` (noms relevés sur LibreOffice, qui en écrit 34), par un autre événement du document sinon ; ailleurs, c'est l'événement d'un contrôle, d'un lien ou d'une image. Une référence est hors de l'archive si elle a un schéma (sauf `vnd.sun.star.Package:` et `vnd.sun.star.GraphicObject:`, internes), si c'est un chemin absolu, ou si elle remonte au-dessus du paquet ; une référence de schéma `macro:` ou `vnd.sun.star.script:` appelle une macro, au clic. Un `draw:object` dans l'archive est un document incorporé, sauf un graphique ou une formule, d'après le type que déclare le manifeste ; un manifeste qui déclare des entrées chiffrées le fait dire.
- Les parties XML d'un ODT sont lues élément par élément, sans garder leur arbre : un parcours ajouté au lecteur XML (`parcourir`), sur lequel `lire_arbre` est réécrit sans changer de comportement.
- Bornes : au plus 4 096 parties suivies d'un DOCX et 65 536 éléments (`actifsbureau.recherche_coupee`) ; arrêt quand il ne reste que 262 144 objets du budget, comme `actifspdf` (`actifsbureau.arret_avant_budget`, ADR-0221). Une partie illisible n'arrête pas les autres ; elle est non menée.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : taille de la PR et coût de lecture ; les codes de champ restent une limite écrite des règles.
- Option C écartée : elle laisse de côté les éléments déclenchés sans geste de l'utilisateur.

## Conséquences

- ADR-0139 reste vrai pour `ooxml` et `odf` ; `actifsbureau` lit, pour son propre compte, les relations de toutes les parties suivies d'un DOCX, et `content.xml`, `styles.xml`, `meta.xml` et `META-INF/manifest.xml` d'un ODT.
- Les codes de champ d'un DOCX, les documents incorporés d'un ODT et les bibliothèques Basic liées restent hors de la recherche ; les limites des règles le disent.
- ES-06 et ADR-0138 tiennent : aucune référence n'est suivie, un test le vérifie sur un DOCX à modèle distant et un ODT à références externes.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début du complément bureautique de T52 |
