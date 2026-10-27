# ADR-0050 — Numéro de version écrit dans `pyproject.toml`

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T10
- **Exigences liées** : NF-06 ; ES-18 ; ADR-0023, ADR-0041, ADR-0049

## Contexte

La version de l'outil figure au rapport (ADR-0023) et déclenche la publication (étiquette, ADR-0041). Il faut décider où elle est fixée.

## Options envisagées

### Option A — Écrite dans `pyproject.toml`

- Avantages : lisible dans le dépôt ; modifiée par une PR comme tout changement ; aucune dépendance de construction.
- Inconvénients : il faut penser à la modifier avant d'étiqueter.

### Option B — Tirée de l'étiquette git (setuptools-scm, hatch-vcs)

- Avantages : rien à modifier à la main.
- Inconvénients : une dépendance de construction de plus ; la version dépend de l'état du dépôt au moment de construire (étiquettes présentes, copie superficielle), ce qui nuit à la reproductibilité.

## Décision

La version est **écrite dans `pyproject.toml`** (champ `version`). Le workflow de publication refuse une étiquette qui ne vaut pas `v` suivi de cette version. Le code la lit dans les métadonnées du paquet installé (`importlib.metadata`). Version de départ : `0.1.0.dev0`.

## Raisons

- Option A retenue : la version est une donnée du dépôt, vérifiable sans outil, et la construction ne dépend pas de l'historique git.
- Option B écartée : dépendance et comportement implicite pour éviter une modification d'une ligne.

## Conséquences

- Préparer une version : une PR qui modifie `version`, puis une étiquette `vX.Y.Z` sur le commit de merge.
- Numérotation : versions de développement (`.devN`) avant la première version publiée ; règles de numérotation des versions publiées à fixer avant la première publication.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Renvoi : règles de numérotation fixées (ADR-0068) ; étiquette limitée aux commits de `detector` et pré-versions marquées (ADR-0069) |
