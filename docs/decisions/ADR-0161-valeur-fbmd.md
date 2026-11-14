# ADR-0161 — Valeur FBMD de SpecialInstructions : numéro de série

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T25
- **Exigences liées** : F-90, ES-13 ; ADR-0119, ADR-0153, ADR-0160

## Contexte

D'après l'IPTC (essais de 2019, publiés le 22 juillet 2019), Facebook écrit dans le jeu IPTC-IIM `SpecialInstructions` (2:40) des images qu'il diffuse une valeur qui commence par `FBMD`. `R-IPTC-003` en fait un indice de transformation (T24, ADR-0153) sans interpréter la suite. Cette suite reste la même d'une copie à l'autre de l'image diffusée : elle relie un fichier reçu à sa diffusion, que la plateforme peut rattacher au compte qui l'a publié. Le journal de T24 l'a laissée à T25.

## Options envisagées

### Option A — Numéro de série quand la valeur commence par FBMD

- Avantages : même traitement qu'`ImageUniqueID`, marqué numéro de série parce qu'il relie entre eux des fichiers (ADR-0119) ; la catégorie dit ce qu'est la valeur, un identifiant, non un texte écrit par une personne.
- Inconvénients : la catégorie d'un champ dépend de sa valeur, ce qu'aucun module ne faisait.

### Option B — Texte libre, toujours

- Avantages : une seule règle pour le champ.
- Inconvénients : l'identifiant est rangé avec les légendes ; lever les textes libres pour relire une légende le montrerait.

### Option C — Ne pas marquer

- Avantages : aucun changement.
- Inconvénients : écart avec `ImageUniqueID` ; l'identifiant part en clair.

## Décision

Option A : le module `iptc` marque `iptc.SpecialInstructions` « numéro de série » si l'une de ses valeurs commence par `FBMD` ; sinon « texte libre » (ADR-0160).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un identifiant n'est pas un texte libre, et deux levées différentes protègent mieux qu'une.
- Option C écartée : elle laisse en clair une donnée qui relie le fichier à sa diffusion.

## Conséquences

- `R-IPTC-003` se déclenche comme avant : sa condition est évaluée dans le processus de travail, et sa phrase ne cite pas la valeur.
- La valeur n'est toujours pas interprétée : le projet ne dit pas ce qu'elle code (limite de `R-IPTC-003`).
- `photoshop:Instructions` d'XMP reste un texte libre : la source ne décrit la marque que dans le jeu IPTC-IIM.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
| 2026-11-14 | Renvoi : l'adresse d'un manifeste C2PA distant, `dcterms:provenance`, marquée numéro de série pour la même raison (ADR-0173) (T30) |
