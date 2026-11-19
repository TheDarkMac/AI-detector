# ADR-0244 — Texte lu d'un PDF : ce qu'un lecteur affiche, et le commentaire des annotations

- **Statut** : Accepté
- **Date** : 2026-11-19
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (éléments lus précisés par l'assistant)
- **Tâche** : T53 (complément texte)
- **Exigences liées** : F-63, F-73 ; ADR-0207, ADR-0213, ADR-0214, ADR-0239, ADR-0243

## Contexte

Le texte d'un PDF n'est pas seulement dans le flux de contenu des pages : les formes qu'il appelle, les apparences des annotations, le commentaire d'une annotation (`/Contents`), les valeurs des champs de formulaire, les signets et les versions antérieures du document en portent aussi. `pagespdf` interprète déjà les pages de la dernière version, leurs formes et l'apparence normale des annotations visibles (ADR-0214).

## Options envisagées

### Option A — Ce qu'un lecteur affiche, et le commentaire des annotations (recommandée)

Dernière version : contenu de chaque page, formes appelées, apparences normales des annotations visibles, comme `pagespdf` ; puis le commentaire (`/Contents`) de chaque annotation, comme les commentaires d'un DOCX (ADR-0239).

- Avantages : le texte qu'un lecteur voit sur la page ou en survolant une annotation ; même parcours que `pagespdf`.
- Inconvénients : les valeurs des champs, les signets et les versions antérieures ne sont pas lus.

### Option B — Contenu des pages seul

Flux de contenu des pages et formes appelées.

- Avantages : plus simple.
- Inconvénients : un texte caché dans une annotation échappe à l'analyse.

### Option C — Tout le texte du fichier

Ajoute les signets, les valeurs des champs de formulaire et les pages des versions antérieures.

- Avantages : couverture maximale.
- Inconvénients : bien plus de cas à écrire et à vérifier ; les versions antérieures se lisent déjà par `revisionspdf`.

## Décision

Option A. Précisions de l'assistant :

- Pages de l'arbre des pages, 4 096 au plus, comme `pagespdf` ; les ressources héritées valent pour la page.
- Apparences : celles que `pagespdf` interprète (ADR-0214) : annotation sans indicateur qui la cache (invisible, cachée, non vue), hors `Widget` et `Popup`, apparence normale, celle de `/AS` si elle en a par état.
- Commentaire : `/Contents` de chaque annotation, hors `Popup` (qui redit celui de son annotation), cachée ou non, décodé comme une chaîne de texte (UTF-16BE ou UTF-8 annoncés par leur marque, PDFDocEncoding sinon, ADR-0118) et coupé en lignes à ses retours chariot et sauts de ligne.
- Les formes se lisent jusqu'à huit niveaux ; une image appelée par `Do`, ou en ligne (`BI`), est comptée, jamais décodée (ADR-0247).
- La lecture s'arrête, comme `pagespdf`, quand il ne reste plus que 262 144 objets du budget (ADR-0213) : le texte déjà lu est analysé et envoyé, `caracteres.arret_avant_budget` le dit.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : le commentaire d'une annotation est un endroit commode pour cacher un caractère.
- Option C écartée : coût hors de proportion ; les versions antérieures relèvent de `revisionspdf`.

## Conséquences

- Le commentaire d'une annotation de texte libre (`FreeText`) redit souvent son apparence : son texte est lu deux fois, relevé deux fois s'il porte un caractère inhabituel. Limite de la fiche.
- Les valeurs des champs de formulaire (`/V`), les signets et les pages des versions antérieures ne sont pas lus : limites de la fiche.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-19 | Création ; option choisie par TheDarkMac au début du complément de T53 |
