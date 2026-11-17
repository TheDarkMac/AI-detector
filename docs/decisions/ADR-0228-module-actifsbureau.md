# ADR-0228 — Éléments actifs des documents bureautiques : un module `actifsbureau` pour DOCX et ODT

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T52 (complément bureautique)
- **Exigences liées** : F-62, NF-01, ES-06 ; menaces M-07, M-14 ; ADR-0136, ADR-0139, ADR-0219

## Contexte

ADR-0219 a réservé à T52 les éléments actifs d'un PDF et renvoyé ceux des documents bureautiques (macros ODF et VBA, objets OLE, modèle distant d'un DOCX) à un complément. Les propriétés de DOCX et d'ODT sont lues par deux modules, `ooxml` et `odf`, qui ne lisent que les parties de propriétés (ADR-0136, ADR-0139). Pour le PDF, les éléments actifs ont leur propre module, `actifspdf`, à côté d'`infopdf`. Restait à dire où loger ceux des documents bureautiques.

## Options envisagées

### Option A — Un module `actifsbureau` pour les deux formats (recommandée)

Un nouveau module, formats `docx` et `odt`, à côté d'`ooxml` et d'`odf`, comme `actifspdf` à côté d'`infopdf`.

- Avantages : mêmes familles, mêmes natures et mêmes règles pour les deux formats ; `ooxml` et `odf` restent ce qu'ADR-0139 dit d'eux, et gardent leur version ; un module qui ne lit aucune métadonnée identifiante, à part de ceux qui en lisent.
- Inconvénients : un module qui sert deux formats, avec deux parcours dans le même code.

### Option B — Deux modules, `actifsooxml` et `actifsodf`

- Avantages : calqués sur `ooxml` et `odf` ; un parcours par module.
- Inconvénients : les règles en double, une série par format, pour dire la même chose.

### Option C — Étendre `ooxml` et `odf`

- Avantages : pas de module de plus.
- Inconvénients : mêle des propriétés identifiantes et la structure du document ; contredit ADR-0139 (parties de propriétés seules) ; change la version des deux modules ; leur analyse non menée rendrait incomplet le contrôle avant publication pour une raison étrangère aux métadonnées.

## Décision

Option A : le module `actifsbureau`, formats `docx` et `odt`, bibliothèque `expat` (le lecteur XML du projet, ADR-0116, ADR-0120), lit ses parties par le lecteur ZIP du projet (ADR-0137). Il choisit son parcours par le format de la partie qu'on lui confie.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : deux séries de règles identiques à tenir ensemble.
- Option C écartée : contraire à ADR-0139, et mêle données identifiantes et structure.

## Conséquences

- `ooxml` et `odf` ne changent pas de ce qu'ils lisent ; leurs fiches renvoient à `actifsbureau` pour les éléments actifs. Ils passent en 0.3.1 pour une correction du lecteur XML qu'ils partagent, trouvée pendant ce complément (ERR-0012).
- `actifsbureau` déclare `expat` : la bibliothèque figure aux versions dès qu'il est actif (ADR-0120).
- Le module rejoint les modules sans métadonnées du résumé (ADR-0158, ADR-0231).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début du complément bureautique de T52 |
