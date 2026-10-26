# ADR-0049 — Construction du paquet : uv_build, épinglé avec empreintes

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; épinglage fixé par l'assistant
- **Tâche** : T10
- **Exigences liées** : NF-06 ; ES-18 ; menace M-31 ; ADR-0023, ADR-0037, ADR-0041

## Contexte

Le paquet publié (sdist et wheel, ADR-0041) est produit par un outil de construction déclaré dans `pyproject.toml`. Cet outil fait partie de la chaîne d'approvisionnement (M-31) : il n'est pas couvert par `uv.lock`, qui ne verrouille que les dépendances du projet. La reproductibilité (ADR-0023) gagne à ce que deux constructions du même code donnent des fichiers identiques.

## Options envisagées

### Option A — uv_build

- Avantages : l'outil de construction de uv (ADR-0037) ; binaire sans dépendance Python ; structure `src/` par défaut ; dates des fichiers fixées, d'où des constructions reproductibles.
- Inconvénients : plus récent que les autres ; peu de réglages.

### Option B — hatchling

- Avantages : très répandu, éprouvé, extensible.
- Inconvénients : tire des dépendances de construction en plus (pathspec, pluggy, trove-classifiers).

### Option C — setuptools

- Avantages : historique, le plus compatible.
- Inconvénients : configuration plus lourde ; fichiers inclus selon des règles implicites héritées.

## Décision

- Le paquet est construit par **uv_build**, avec la structure `src/voight_kampff/` (nom de module fixé dans `pyproject.toml`, ADR-0045).
- L'outil est **épinglé avec ses empreintes** dans `contraintes-construction.txt` : la CI et le workflow de publication construisent avec `uv build --build-constraint contraintes-construction.txt --require-hashes`.
- La version de uv utilisée en CI est fixée dans les workflows (`UV_VERSION`) ; elle et `uv_build` évoluent ensemble, par une PR.

## Raisons

- Option A retenue : aucune dépendance de construction en plus, et des fichiers reproductibles sans réglage.
- Option B écartée : trois dépendances de construction de plus, sans besoin qui les justifie pour un paquet en Python pur.
- Option C écartée : ses règles implicites d'inclusion de fichiers vont contre l'exigence de savoir exactement ce qui est publié.
- Épinglage avec empreintes : ES-18 demande des versions figées avec empreintes ; sans lui, la construction installerait la dernière version de `uv_build` compatible, non vérifiée.

## Conséquences

- Le job `paquet` de la CI construit deux fois et compare les empreintes, vérifie que le paquet source ne contient ni `docs/` ni `.github/`, installe le wheel dans un environnement neuf et lance les deux commandes (ADR-0051).
- Vérifié en local le 2026-10-26 : deux constructions identiques ; le paquet source contient `pyproject.toml`, `README.md` et `src/` seulement.
- Dependabot ne met pas à jour `contraintes-construction.txt` ni `UV_VERSION` : mise à jour manuelle, décrite dans `CONTRIBUTING.md`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
