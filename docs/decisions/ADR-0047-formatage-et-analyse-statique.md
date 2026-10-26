# ADR-0047 — Formatage et analyse statique : Ruff et mypy strict

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; réglages fins fixés par l'assistant
- **Tâche** : T10
- **Exigences liées** : NF-09 (outillage) ; ES-04, ES-09, ES-18 ; ADR-0034, ADR-0036

## Contexte

T10 met en place l'outillage de développement (découpage). Le code lira des fichiers hostiles et échangera des messages entre processus (ADR-0036) : une erreur de type sur un message, ou une construction dangereuse (`eval`, `pickle`, `subprocess` avec interpréteur de commandes), doit être attrapée avant la revue.

## Options envisagées

### Option A — Ruff et mypy en mode strict

- Avantages : Ruff formate et analyse en un seul outil rapide, avec les règles de sécurité issues de Bandit ; mypy, la référence pour les types Python, en mode strict, refuse le code non annoté.
- Inconvénients : deux outils ; le mode strict demande d'annoter aussi les tests.

### Option B — Ruff et pyright

- Avantages : pyright est plus rapide et plus précis sur certains cas.
- Inconvénients : il tire Node.js dans l'outillage, soit une chaîne d'approvisionnement de plus (ES-18).

### Option C — Ruff seul

- Avantages : un seul outil.
- Inconvénients : aucune vérification de types, alors que les protocoles entre processus (T11, T12) en tirent le plus de profit.

## Décision

- **Ruff** formate le code et l'analyse ; **mypy en mode strict** vérifie les types de `src/` et de `tests/`.
- Réglages fixés par l'assistant (dans `pyproject.toml`) :
  - lignes de 100 caractères au plus ; cible Python 3.12 ;
  - familles de règles Ruff : pycodestyle (E, W), pyflakes (F), tri des imports (I), bugbear (B), syntaxe moderne (UP), **sécurité (S)**, simplifications (SIM), compréhensions (C4), style pytest (PT), règles propres à Ruff (RUF) ;
  - dans les tests seulement, `assert` (S101) et le lancement de l'interpréteur courant (S603) sont admis ;
  - le dossier du cahier des charges est exclu, comme pour le lint Markdown (ADR-0006) : `ruff format` ne doit jamais le modifier.
- Les versions de Ruff et de mypy sont fixées par le verrou (ADR-0037).

## Raisons

- Option A retenue : la vérification de types la plus répandue, sans ajouter Node.js, et les règles de sécurité dès le premier fichier.
- Option B écartée : le gain de précision ne justifie pas une seconde chaîne d'outils.
- Option C écartée : elle renonce à vérifier les types là où le projet en a le plus besoin.
- Règles S dès T10 : elles signalent `pickle`, `eval`, `subprocess` avec `shell=True`, contraires à ES-04 et ADR-0036.

## Conséquences

- Le job `qualite` de la CI exécute `ruff format --check`, `ruff check` et `mypy` (ADR-0051).
- Une règle désactivée localement (`# noqa`, `# type: ignore`) doit être justifiée par un commentaire dans le code.
- Les bibliothèques sans annotations de type ajoutées plus tard (T20 et suivantes) demanderont des déclarations de types ou une exception ciblée dans `pyproject.toml`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
