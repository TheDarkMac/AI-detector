# ADR-0052 — Surveillance des failles : pip-audit et Dependabot

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; réglages fixés par l'assistant
- **Tâche** : T10
- **Exigences liées** : ES-18 ; menace M-31 ; ADR-0003, ADR-0005, ADR-0007, ADR-0037

## Contexte

ADR-0037 demande de prévoir en T10 la surveillance des failles connues des dépendances. Deux besoins distincts : **détecter** qu'une version verrouillée a une faille connue, et **proposer** la mise à jour. Les PR ouvertes par Dependabot ne suivent pas les règles du projet : commits au nom de `dependabot[bot]` (contre ADR-0003), messages en anglais et branches `dependabot/…` (contre ADR-0005).

## Options envisagées

### Surveillance

#### Option A — pip-audit en CI et Dependabot

- Avantages : pip-audit bloque une PR qui introduirait une version vulnérable, et revérifie chaque semaine ; Dependabot propose les mises à jour pour uv et pour les actions épinglées par empreinte.
- Inconvénients : des PR automatiques à traiter.

#### Option B — pip-audit seul

- Avantages : aucune PR automatique.
- Inconvénients : mises à jour à la main, donc correctifs plus lents.

#### Option C — Dependabot seul

- Avantages : rien à maintenir dans la CI.
- Inconvénients : rien n'empêche une PR d'ajouter une dépendance vulnérable.

### PR de Dependabot

#### Option D — Exception admise

- Avantages : correctifs rapides ; l'auteur réel de chaque modification reste visible.
- Inconvénients : écart aux règles d'identité et de nommage.

#### Option E — Reprise à la main sur une branche `correctif/`

- Avantages : règles respectées.
- Inconvénients : chaque mise à jour est faite deux fois ; correctifs plus lents.

#### Option F — Alertes seulement, sans PR

- Avantages : aucune PR étrangère aux règles.
- Inconvénients : toutes les mises à jour à la main.

## Décision

- **pip-audit** vérifie, dans le job `audit-dependances` (ADR-0051), **toutes** les dépendances verrouillées, outillage compris, exportées avec leurs empreintes depuis `uv.lock` ; toute faille connue fait échouer la vérification (`--strict`). Le workflow tourne aussi chaque lundi, sans PR.
- **Dependabot** propose chaque semaine les mises à jour de `uv.lock` (préfixe `build`) et des actions GitHub (préfixe `ci`), vers `detector`, groupées par écosystème. Une version publiée depuis moins de 7 jours n'est pas proposée.
- **Exception admise** : les PR de Dependabot sont mergées telles quelles quand `code-ok` est vert, par commit de merge, avec le titre habituel (ADR-0044) : `Merge: dépendances — <objet> (#N)`. Leurs commits gardent l'auteur `dependabot[bot]`, leur message et leur branche d'origine. C'est la seule exception à ADR-0003 et ADR-0005, avec celle des commits de merge (ADR-0007).

## Raisons

- Option A retenue : détection bloquante et mises à jour proposées, deux besoins que ni B ni C ne couvrent seules.
- Option B écartée : correctifs plus lents.
- Option C écartée : aucune garde dans la CI.
- Option D retenue : la règle d'identité vise à ce que tout commit humain du projet porte la même identité, sans mention d'outil ; un commit de Dependabot n'est pas un commit humain, et l'attribuer à TheDarkMac masquerait sa vraie origine.
- Option E écartée : le double travail ralentit précisément les correctifs de sécurité.
- Option F écartée : elle renonce au gain principal de Dependabot.
- Délai de 7 jours : un paquet compromis publié sur PyPI est en général retiré en quelques jours (M-31) ; pip-audit reste le contrôle bloquant pour les failles déjà connues.

## Conséquences

- Les mises à jour de Dependabot n'ont pas d'entrée de journal ; elles apparaissent dans l'historique de `detector` et dans la rubrique Versions des rapports (ADR-0023).
- Une mise à jour qui change un comportement (version majeure, licence, nouvelle dépendance transitive) est vérifiée selon les critères d'ADR-0043 avant le merge, et consignée dans la PR.
- Dependabot ne voit ni `contraintes-construction.txt` ni `UV_VERSION` (ADR-0049) : mise à jour manuelle.
- Les PR ouvertes par Dependabot pendant une tâche sont traitées après le merge de la tâche, pour ne pas mélanger deux sujets.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
