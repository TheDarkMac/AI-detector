# ADR-0099 — Banc d'évaluation : outil du dépôt, hors du paquet publié

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T17
- **Exigences liées** : §8 du cahier, NF-09 ; ADR-0016, ADR-0018, ADR-0024 ; A-12, A-54

## Contexte

Le §8 du cahier fait des taux d'erreur mesurés sur un corpus un critère d'acceptation de chaque technique ; ADR-0016 sépare le corpus en calibrage et évaluation ; ADR-0018 demande un taux de faux positifs par fichier et laisse à T17 les bornes des niveaux. Il faut un outil qui analyse un corpus et calcule ces mesures. Reste à savoir où il vit : dans le paquet publié, à la disposition de chaque utilisateur, ou à côté.

## Options envisagées

### Option A — Outil du dépôt, hors du paquet publié

Paquet `banc/` à la racine du dépôt, lancé par `python -m banc CORPUS` ; il appelle l'interface publique `voight_kampff.analyser()` du paquet installé.

- Avantages : aucune interface ni ligne de code de plus livrée aux utilisateurs ; le banc évalue exactement ce qu'un utilisateur exécute ; il peut employer des outils de développement (pytest pour la matrice).
- Inconvénients : un tiers qui veut refaire l'évaluation doit cloner le dépôt.

### Option B — Sous-commande livrée `vk evaluer`

- Avantages : tout utilisateur peut refaire l'évaluation sans cloner.
- Inconvénients : une interface de plus à maintenir, à documenter et à sécuriser dans le paquet ; elle n'intéresse que ceux qui ont un corpus, c'est-à-dire ceux qui ont déjà le dépôt.

### Option C — Module de bibliothèque `voight_kampff.evaluation`

- Avantages : réutilisable par programme.
- Inconvénients : mêmes coûts que l'option B, sans la commande.

## Décision

Option A. Le banc est le paquet `banc/` du dépôt ; il n'est ni dans le wheel ni dans le paquet source. Il n'emploie que l'interface publique d'analyse, plus la lecture du catalogue et des manifestes (`voight_kampff._orchestration`), pour connaître les règles et les modules à mesurer.

## Raisons

- Option A retenue : le banc mesure l'outil tel qu'il est livré, sans rien ajouter à ce que l'utilisateur installe ni à la surface d'attaque.
- Option B écartée : coût de maintenance et d'interface pour un usage de développement.
- Option C écartée : mêmes raisons.

## Conséquences

- `pyproject.toml` : `banc` sur le chemin d'import de pytest, dans mypy et dans la mesure de couverture ; le paquet construit reste inchangé (vérifié : ni le wheel ni le paquet source ne contiennent `banc/`).
- La CI lance le banc depuis le wheel installé, sur le corpus d'essai (ADR-0105).
- Les mesures sont définies par ADR-0104, le corpus par ADR-0103, l'absence de réseau par ADR-0100, les bornes par ADR-0101.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
