# ADR-0239 — Texte d'un DOCX ou d'un ODT : corps, notes, en-têtes et pieds de page, commentaires

- **Statut** : Accepté
- **Date** : 2026-11-18
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (éléments lus précisés par l'assistant)
- **Tâche** : T80 (complément bureautique)
- **Exigences liées** : F-73 ; ADR-0013, ADR-0116, ADR-0137, ADR-0232

## Contexte

ADR-0232 a renvoyé à un complément de T80 l'analyse des caractères du texte d'un DOCX et d'un ODT. Ce texte est réparti dans plusieurs parties XML de l'archive : le corps, mais aussi les notes, les en-têtes et pieds de page, les commentaires, et, plus loin, le glossaire, les parties XML personnalisées, le texte des SmartArt et des graphiques. Un caractère caché hors du corps voyage avec le document comme les autres.

## Options envisagées

### Option A — Corps, notes, en-têtes et pieds de page, commentaires (recommandée)

DOCX : la partie principale, que désigne la relation `officeDocument` du paquet (zones de texte comprises), puis, par ses relations, ses en-têtes, pieds de page, notes de bas de page et de fin et commentaires. ODT : `content.xml` (corps, notes, annotations) et les en-têtes et pieds de page des pages types de `styles.xml`.

- Avantages : tout le texte qu'un lecteur peut voir dans le logiciel.
- Inconvénients : le texte d'un glossaire ou d'un graphique n'est pas lu.

### Option B — Corps seul

- Avantages : plus simple.
- Inconvénients : un texte caché dans une note ou un en-tête échappe à l'analyse.

### Option C — Tout le XML texte

Ajoute le glossaire, les parties XML personnalisées, le texte des SmartArt et des graphiques.

- Avantages : couverture maximale.
- Inconvénients : beaucoup plus de cas à écrire et à vérifier, pour du texte rarement affiché.

## Décision

Option A. Précisions de l'assistant :

- DOCX (ECMA-376, partie 1, §17) : texte de `w:t`, et de `w:delText` (ADR-0240) ; `w:tab` en tabulation, `w:br` et `w:cr` en saut de ligne, `w:noBreakHyphen` et `w:softHyphen` en trait d'union insécable (U+2011) et conditionnel (U+00AD). Les codes de champ (`w:instrText`) ne s'affichent pas : ils ne sont pas lus. Espaces de noms transitionnel et strict. Les relations sont lues comme le fait `actifsbureau` (ADR-0229) : cible relative à la partie source, cible externe ignorée.
- Ordre de lecture : partie principale, en-têtes, pieds de page, notes de bas de page, notes de fin, commentaires ; parties d'un même type dans l'ordre de leurs noms.
- ODT (OpenDocument 1.3, partie 3) : texte des paragraphes (`text:p`, `text:h`), hors des métadonnées (`dc:`, `meta:`, auteur et date d'une annotation ou d'une modification) et des descriptions d'images (`svg:`) ; `text:s` en espaces (1 024 au plus), `text:tab`, `text:line-break`. Dans `styles.xml`, seuls les en-têtes et pieds des pages types (`style:master-page`) sont lus.
- Un paragraphe contenu dans un autre (zone de texte, note d'un ODT) est un paragraphe à part, numéroté dans l'ordre où il s'ouvre, dans sa partie.
- Une partie manquante est non menée pour référence manquante ; illisible (archive, deux entrées du même nom, en-tête local) ou XML coupé, pour format partiel, le texte lu avant l'arrêt étant gardé. La lecture passe alors à la partie suivante.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : une note ou un en-tête est un endroit commode pour cacher un caractère.
- Option C écartée : coût hors de proportion pour du texte rarement affiché ; reste possible plus tard.

## Conséquences

- Les documents incorporés d'un ODT (`Object 1/`), le glossaire et les parties personnalisées d'un DOCX ne sont pas lus : limites de la fiche.
- Échantillons écrits et relus par LibreOffice 25.2.3.2 (`tests/donnees/caracteres/generer_bureau.py`) : le texte que relit LibreOffice se retrouve dans le texte lu.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-18 | Création ; option choisie par TheDarkMac au début du complément de T80 |
