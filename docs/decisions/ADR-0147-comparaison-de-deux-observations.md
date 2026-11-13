# ADR-0147 — Comparaison de deux observations : test du catalogue, format 2

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T23
- **Exigences liées** : F-13, F-26, NF-06, NF-07 ; ES-03, ES-09 ; ADR-0039, ADR-0084, ADR-0085, ADR-0089, ADR-0121

## Contexte

F-13 demande de relever les incohérences internes : dates impossibles, logiciel incompatible avec l'appareil déclaré, dimensions atypiques. Une incohérence oppose souvent deux observations : une date de création postérieure à la date de modification. Le langage des règles d'ADR-0084 ne sait pas l'écrire : chaque condition porte un seul test sur une seule observation, et les dates sont observées telles qu'écrites, sans conversion (ADR-0118, ADR-0128, ADR-0133, ADR-0140). ADR-0084 laissait à T23 le choix entre une règle « module » et un nouveau test, qui serait un nouveau format du catalogue (ADR-0085).

Un constat ne cite que les observations de son module (`rapport/modele.py`, `Contexte`), et le moteur applique les règles d'un module à ses seules observations, dans le processus de travail (ADR-0089).

## Options envisagées

### Option A — Test du catalogue, format 2

Une condition peut **comparer** son observation à une seconde observation du même module, et lire les dates selon une écriture que déclare la règle. Le moteur l'applique comme les autres tests.

- Avantages : la comparaison reste écrite et relue dans le catalogue, comme toutes les règles (ADR-0019) ; une nouvelle comparaison s'ajoute sans nouvelle version de l'outil (F-26) ; le code des modules ne change pas.
- Inconvénients : un format 2 du catalogue, qu'un outil antérieur ne sait pas lire ; une lecture des dates dans le moteur, à documenter (ADR-0148).

### Option B — Règles « module »

Chaque module compare ses propres dates dans son code et cite la règle (ADR-0090).

- Avantages : aucun changement du format ni du moteur.
- Inconvénients : la logique répartie dans le code de huit modules ; une nouvelle comparaison demande une nouvelle version de l'outil, et F-26 n'est tenue que pour les textes.

### Option C — Test du catalogue, entre modules aussi

L'option A, et des règles appliquées à toutes les observations d'une partie : la date EXIF contre la date XMP, la marque EXIF contre la marque XMP.

- Avantages : relève les écarts entre familles de métadonnées, fréquents quand un logiciel n'en réécrit qu'une.
- Inconvénients : change l'invariant du modèle (un constat ne cite que les observations de son module) et le schéma du rapport ; le moteur devrait attendre la fin de tous les modules d'une partie ; un module en erreur priverait les règles d'un autre de ses observations.

## Décision

Option A.

- Deux tests s'ajoutent à ceux d'ADR-0084, toujours un seul par condition :
  - `comparer = { observation, operateur, parametre }` : satisfaite par une paire formée d'une observation du nom de la condition et d'une observation du nom donné, dans l'ordre que dit `operateur` : `<`, `>` (nombres, ou dates, ADR-0148) ou `=` (égalité au sens d'`egal`, jamais pour deux dates) ; `parametre` nomme le paramètre de la phrase qui renvoie à la seconde observation ;
  - `impossible = true` : satisfaite par une valeur qui suit l'écriture de date de la condition, mais ne désigne aucune date du calendrier (ADR-0148).
- `lecture` donne l'écriture des dates (`date-exif`, `date-pdf`, `date-iso8601`, `date-1904`) ; elle est obligatoire pour `impossible`, permise pour `comparer`, refusée avec les autres tests.
- Paire retenue : la première dans l'ordre des premières observations, puis des secondes, comme la première observation d'ADR-0089 ; le constat cite les deux observations.
- La recherche de la paire est linéaire : pour un ordre, la seconde valeur la plus facile à dépasser dit si une première observation a une partenaire ; pour l'égalité, un index des secondes valeurs.
- Format du catalogue : 2. L'outil lit les formats 1 et 2 ; une règle qui emploie `comparer`, `impossible` ou `lecture` dans un catalogue du format 1 le rend invalide, pour qu'un catalogue du format 1 reste lisible par un outil antérieur (ADR-0085, ADR-0152).
- Comparaisons entre modules : hors de T23. Le point reste ouvert à l'architecture (§12, avec l'acheminement des résultats d'un module vers un autre, T53).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle remet dans le code ce qu'ADR-0084 a voulu dans le catalogue ; chaque nouvelle date comparée demanderait une nouvelle version d'un module et de l'outil.
- Option C écartée : son gain ne justifie pas, dans T23, un changement du modèle de données, du schéma du rapport et de l'ordre d'exécution ; les comparaisons au sein d'un module couvrent déjà les trois familles de F-13.
- Recherche linéaire : un module peut produire jusqu'à 4 096 observations (ADR-0121), toutes d'un même nom si le fichier répète un champ ; essayer chaque paire a pris 31 s pour 2 048 × 2 048 dates sur le poste de l'assistant, au-delà de ce que permet le délai de 120 s de l'analyse (ADR-0077). La recherche linéaire en prend 18 ms et retient la même paire (test par Hypothesis dans `tests/test_regles.py`).

## Conséquences

- `schemas/regles.schema.json` et `schemas/catalogue.schema.json` admettent le format 2 ; `_regles.py` porte les deux tests, `_dates.py` la lecture des dates (ADR-0148).
- Une règle « moteur » cite jusqu'à 32 observations (deux par condition), sous la borne de 256 données d'un constat.
- Le catalogue livré passe au format 2 (ADR-0152) ; un catalogue fourni par l'utilisateur au format 1 reste accepté.
- La comparaison d'observations de deux modules reste à écrire ; un écart entre EXIF et XMP n'est pas relevé (limite des règles de T23, ADR-0150).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création |
