# ADR-0038 — Format du catalogue : TOML validé par JSON Schema

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : F-12, F-24, F-26, NF-07, NF-09 ; ES-09 ; constat A-37 ; ADR-0016, ADR-0018, ADR-0019, ADR-0029

## Contexte

Le catalogue est un ensemble de fichiers de données séparés du moteur, livrés avec l'outil et validés par schéma au chargement (ADR-0029). Il porte des signatures, des règles, leurs seuils, leur procédure de calibrage (ADR-0016), leur niveau et le taux qui le fonde (ADR-0018). Tout y est public (ADR-0019) : il doit pouvoir être lu et relu par une personne. Le découpage confie à T04 le format du catalogue, et ADR-0029 confie à T15 son schéma : T04 fixe le format d'écriture, T15 le contenu.

## Options envisagées

### Option A — TOML

- Avantages : lisible, commentable ; analyseur dans la bibliothèque standard (`tomllib`) ; types explicites ; aucune construction qui exécute du code.
- Inconvénients : tableaux imbriqués profonds peu lisibles ; pas de schéma natif.

### Option B — YAML

- Avantages : commentable, compact.
- Inconvénients : spécification complexe ; types implicites (« no » lu comme faux, nombres mal interprétés) ; chargement dangereux s'il est mal configuré ; une dépendance de plus.

### Option C — JSON

- Avantages : aucune dépendance ; même langage que le schéma.
- Inconvénients : pas de commentaires ; pénible à relire et à modifier à la main.

## Décision

- Les fichiers du catalogue sont écrits en **TOML** et lus par `tomllib`.
- Une fois lus, ils sont **validés par un JSON Schema** publié et versionné avec eux ; un catalogue invalide arrête l'analyse avec un message explicite (ADR-0029).
- La version et l'empreinte du catalogue (ADR-0040) sont calculées sur ses fichiers tels que livrés.
- La liste de confiance C2PA garde le format défini par sa source ; T30 en décide.

## Raisons

- Option A retenue : lisible et commentable pour des règles publiques et documentées, sans dépendance ni type implicite.
- Option B écartée : ses types implicites peuvent changer le sens d'une règle sans erreur visible, ce qui touche la justesse des constats (B7).
- Option C écartée : l'absence de commentaires nuit à la relecture des règles.
- JSON Schema : le même outil valide le catalogue, les messages du processus de travail (ADR-0036) et l'export JSON (ADR-0025).

## Conséquences

- T15 écrit le schéma du catalogue, son découpage en fichiers et le calcul de son empreinte.
- La validation par JSON Schema ajoute une dépendance (ADR-0043).
- Les expressions régulières du catalogue relèvent d'ADR-0039.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
