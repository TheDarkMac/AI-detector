# ADR-0051 — Intégration continue du code : trois systèmes, Python 3.12 à 3.14

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (versions de Python) ; organisation des jobs fixée par l'assistant
- **Tâche** : T10
- **Exigences liées** : NF-09 ; ES-18 ; ADR-0001, ADR-0006, ADR-0034, ADR-0035, ADR-0039

## Contexte

ADR-0034 fixe Python 3.12 au minimum ; ADR-0035 prend en charge Linux, macOS et Windows et demande que la CI exécute les tests sur les trois. Python 3.15 est sorti le 2026-10-09. `google-re2` (ADR-0039), nécessaire en T15, publie des paquets précompilés pour Python 3.10 à 3.14 sur les trois systèmes, mais **pas encore pour 3.15** (version 1.1.20251105, vérifiée sur PyPI le 2026-10-26) ; sa compilation demande les bibliothèques C++ RE2 et Abseil.

## Options envisagées

### Option A — Python 3.12 à 3.14, sur les trois systèmes

- Avantages : la CI teste exactement ce que la V1 pourra installer ; 9 combinaisons.
- Inconvénients : 3.15 n'est pas testé tant que `google-re2` ne le prend pas en charge.

### Option B — Python 3.12 à 3.15 dès maintenant

- Avantages : 3.15 testé tant que le projet n'a pas de dépendance.
- Inconvénients : à retirer probablement en T15, ou à faire compiler RE2 en CI.

### Option C — Python 3.12 et 3.14 seulement

- Avantages : 6 combinaisons, moins de minutes.
- Inconvénients : 3.13 n'est pas testé directement.

## Décision

- Workflow `code`, déclenché par chaque PR et chaque push vers `detector`, chaque lundi (ADR-0052) et à la demande :

  | Job | Contenu |
  | --- | --- |
  | `qualite` | Verrou à jour (`uv lock --check`), installation depuis le verrou, Ruff, mypy (ADR-0047) |
  | `tests` | pytest et couverture sur **Linux, macOS, Windows × Python 3.12, 3.13, 3.14** (ADR-0048) |
  | `audit-dependances` | pip-audit sur toutes les dépendances verrouillées (ADR-0052) |
  | `paquet` | Construction reproductible, contenu du paquet source, installation du wheel (ADR-0049) |
  | `code-ok` | Réussit seulement si tous les jobs précédents ont réussi |

- **`code-ok` est la seule vérification du code rendue obligatoire sur `detector`** (ADR-0001), à côté de `lint-markdown` et `fichiers-interdits` (ADR-0006). Ajout fait après son premier passage sur la PR de T10.
- Toutes les installations passent par le verrou (`--locked`), sans résolution (ADR-0037). Actions épinglées par empreinte de commit (ADR-0006).
- Python 3.15 est ajouté à la matrice et aux classificateurs du paquet quand `google-re2` publie des paquets pour lui.

## Raisons

- Option A retenue : la CI ne promet que ce que la V1 pourra tenir ; ajouter 3.15 plus tard ne coûte qu'une ligne.
- Option B écartée : elle annoncerait une prise en charge qu'il faudrait retirer à T15.
- Option C écartée : le dépôt public (ADR-0046) rend les minutes gratuites ; aucune raison de ne pas tester 3.13.
- Un seul job obligatoire, `code-ok` : la protection de `detector` n'a pas à changer quand la matrice change ; la liste des jobs vit dans le workflow.
- Pas de filtre par chemin : une vérification obligatoire qui ne tourne pas bloquerait les PR de documentation.

## Conséquences

- Chaque PR, y compris de pure documentation, lance les 13 jobs du workflow `code`.
- Le lancement hebdomadaire révèle aussi les changements des images des runners de GitHub, indépendamment de toute PR.
- Les tests d'isolation de T14 s'ajouteront aux jobs `tests` des trois systèmes.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : le lancement planifié et le lancement à la demande ne fonctionnaient pas tant que `main` était la branche par défaut (ERR-0005, ADR-0053) |
