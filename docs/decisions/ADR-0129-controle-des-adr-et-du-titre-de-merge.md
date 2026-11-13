# ADR-0129 — La CI refuse un ADR « Proposé » et vérifie le titre du commit de merge

- **Statut** : Accepté
- **Date** : 2026-11-12
- **Décideur** : TheDarkMac a validé la mesure ; mise en œuvre proposée par l'assistant
- **Tâche** : T21
- **Exigences liées** : méthode de travail ; ADR-0001, ADR-0004, ADR-0006, ADR-0044 ; ERR-0007, ERR-0008

## Contexte

Trois PR ont été mergées avec le titre par défaut de GitHub (#4, #18, #19), et deux avec des ADR encore « Proposé » (#18 : ERR-0007 ; #19 : ERR-0008). La prévention d'ERR-0007 était un rappel dans `CONTRIBUTING.md` (§3, étape 6) : il n'a pas suffi. La protection de `detector` exige trois vérifications : `lint-markdown`, `fichiers-interdits` et `code-ok`.

## Options envisagées

### Option A — Une étape dans un job déjà exigé

Le job `lint-markdown` du workflow `docs` refuse tout ADR au statut « Proposé ». Sur un push vers `detector`, il vérifie que le commit de merge a un titre au format d'ADR-0044.

- Avantages : la PR ne peut pas être mergée tant qu'un ADR attend sa validation, quel que soit le moyen du merge (commande ou interface de GitHub) ; aucun réglage du dépôt à changer.
- Inconvénients : la PR est rouge tant que TheDarkMac n'a pas validé ses ADR ; le titre ne peut être vérifié qu'une fois le merge fait (il est choisi au moment du merge), donc signalé, pas empêché.

### Option B — Un job à part, ajouté aux vérifications exigées

- Avantages : nom explicite dans la liste des vérifications.
- Inconvénients : demande de changer la protection de `detector`, réglage que TheDarkMac fait lui-même ; possible plus tard sans changer le contrôle.

### Option C — Rappel écrit seulement

- Avantages : rien à changer.
- Inconvénients : c'est la mesure d'ERR-0007, qui a échoué.

### Option D — Titre de merge par défaut réglé dans le dépôt

GitHub permet de prendre le titre de la PR comme titre par défaut d'un commit de merge.

- Avantages : le titre est bon même par l'interface.
- Inconvénients : le format obtenu n'est pas celui d'ADR-0044 (`Merge: TNN — titre (#N)`) ; réglage du dépôt à changer.

## Décision

Option A.

## Raisons

- Option A : le seul moyen, sans réglage du dépôt, d'empêcher le merge d'une PR dont les ADR n'ont pas été validés.
- Option B écartée pour l'instant : même effet, au prix d'un réglage ; à reprendre si TheDarkMac le souhaite.
- Option C écartée : déjà essayée (ERR-0007).
- Option D écartée : format différent d'ADR-0044, et réglage du dépôt.

## Conséquences

- `.github/workflows/docs.yml` : étapes « Aucun ADR au statut Proposé » et « Titre du commit de merge », dans `lint-markdown`.
- Une PR qui ajoute un ADR « Proposé » reste rouge jusqu'au commit qui le passe à « Accepté » (ou « Abandonné ») sur validation consignée : c'est le signal qu'il faut relire.
- `CONTRIBUTING.md` (§3, étape 6) et ADR-0006 renvoient à ce contrôle.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création ; mesure validée par TheDarkMac au début de T21 (ERR-0008) |
