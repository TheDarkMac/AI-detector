# ADR-0265 — Rubrique « Conservation des données » au rapport HTML, sans chemin ; rapport JSON et schéma inchangés

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T92
- **Exigences liées** : NF-05, ES-14 ; ADR-0098, ADR-0259, ADR-0264

## Contexte

Un rapport est souvent lu par un autre que celui qui a lancé l'analyse : un collègue, un juriste, un rédacteur en chef. Le terminal (ADR-0264) ne l'atteint pas. Le rapport ne peut pas dire où il est gardé : il est produit avant d'être écrit, et n'inscrit aucun chemin (ES-14).

## Options envisagées

### Option A — Rubrique au rapport HTML, texte fixe, JSON inchangé (recommandée)

- Avantages : le lecteur d'un rapport transmis apprend que l'outil n'a pas gardé le fichier, et que la conservation de sa copie dépend de qui l'a reçue ; le texte ne dépend que de la saisie, sans donnée de l'analyse ; le schéma du rapport ne change pas.
- Inconvénients : une rubrique de plus au rapport.

### Option B — Rubrique HTML et champ du rapport JSON

- Avantages : l'information est aussi dans l'export de données.
- Inconvénients : un champ qui ne dépend pas du fichier, dans un export de résultats ; nouvelle version du schéma (0.14.0) pour un texte fixe.

### Option C — Rien dans le rapport

- Avantages : le rapport ne change pas.
- Inconvénients : le lecteur d'un rapport transmis ne sait rien de la conservation.

## Décision

Option A.

- Rubrique `conservation`, « Conservation des données », entre « Observations » et « Glossaire », reprise au sommaire (ADR-0259). Quatre paragraphes :
  - l'outil n'a rien gardé du fichier analysé, lu là où il se trouvait, ni copié sur le disque ni modifié, dans un processus de travail terminé avec l'analyse ; pour un texte collé, lu en mémoire seulement ;
  - ce rapport est gardé là où il a été écrit, jusqu'à sa suppression ; l'outil ne l'envoie nulle part ; si son horodatage a été demandé, seule son empreinte est partie, vers l'autorité choisie, qui la garde selon sa propre politique ;
  - une fois transmis, chaque copie est gardée par qui la reçoit, selon ses propres règles ;
  - l'énoncé complet : `vk --conservation`.
- Aucun chemin, aucun nom, aucune date : la rubrique est identique pour deux rapports d'une même saisie, et ne change rien à la reproductibilité (ADR-0108).
- Le rapport JSON et son schéma (0.13.0) sont inchangés.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : l'export JSON porte des résultats ; un texte fixe n'y apprend rien qu'un programme ne sache déjà, et coûte une version du schéma.
- Option C écartée : le lecteur d'un rapport transmis est celui qui sait le moins ce que l'outil a gardé.

## Conséquences

- ADR-0098 : l'ordre du rapport HTML gagne cette rubrique (renvoi à son historique).
- `tests/test_rapport.py` (ordre des rubriques) et `tests/test_conservation_donnees.py` (texte, absence de chemin, texte collé) la vérifient.
- La grille d'accessibilité (ADR-0256) n'est pas à refaire : la rubrique n'emploie que des titres et des paragraphes, déjà couverts.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
