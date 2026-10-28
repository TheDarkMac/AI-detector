# ADR-0110 — Conditions variées : sur un poste, et entre systèmes et versions de Python en CI

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac (question posée pendant T18, recommandation suivie) ; réglages fixés par l'assistant, à valider pendant la revue de la PR de T18
- **Tâche** : T18
- **Exigences liées** : NF-06, P-05, critère du §8 ; ES-14 ; ADR-0023, ADR-0035, ADR-0051, ADR-0065

## Contexte

Deux analyses identiques, dans le même environnement, ne détectent ni une dépendance au chemin, à la langue ou au fuseau horaire, ni un ordre tiré d'un ensemble (graine de hachage), ni une différence entre systèmes. Il fallait choisir ce qui varie entre les deux analyses comparées.

## Options envisagées

### Option A — Variations locales et comparaison entre systèmes en CI

Sur un poste : chemin et nom du fichier, dossier courant, graine de hachage, fuseau horaire, langue, rang dans un lot, processus de travail. En CI : chaque job (trois systèmes, trois versions de Python) écrit les rapports du corpus d'essai ; un dernier job les compare.

- Avantages : couvre les causes connues de variation, systèmes compris.
- Inconvénients : un job et neuf artefacts de plus ; la CI échoue si une technique donne un résultat différent sous une autre version de Python.

### Option B — Variations locales seulement

- Avantages : CI inchangée.
- Inconvénients : un écart entre Linux, macOS et Windows passerait inaperçu.

### Option C — Deux analyses à l'identique

- Avantages : le minimum de l'énoncé.
- Inconvénients : ne détecte aucune des dépendances ci-dessus.

## Décision

Option A.

Réglages fixés par l'assistant :

- **Sur un poste** (`tests/test_reproductibilite.py`) : deux lancements de `python -m voight_kampff`, l'un avec `PYTHONHASHSEED=1`, `TZ=UTC`, `LC_ALL=C`, l'autre avec `PYTHONHASHSEED=4242`, `TZ=Pacific/Kiritimati` (UTC+14), `LC_ALL=fr_FR.UTF-8` ; autres dossiers, autres noms à la même extension, dossier courant différent, ordre du lot inversé. Une langue absente du poste revient à `C` : la variation est alors moindre, jamais fausse.
- **Processus de travail** : son environnement est vidé (ADR-0065), donc sa graine de hachage est tirée à chaque analyse ; les analyses répétées le varient sans réglage.
- **Entre systèmes** : le job `tests` écrit, après les tests, les rapports de huit fichiers du corpus d'essai, toutes catégories levées, et les joint (`rapports-<système>-<python>`). Le job `reproductibilite` les compare au jeu `ubuntu-latest` sous Python 3.13 par `vk --comparer`, qui doit rendre 0 : aucun écart de résultat.
- **Entre versions de Python** : la version de l'interpréteur est une condition (ADR-0111), donc hors garantie si elle diffère ; la CI exige pourtant les mêmes résultats. Si une technique future en donnait d'autres, l'écart serait consigné et tranché par un ADR, pas masqué.
- `reproductibilite` entre dans `code-ok`, seule vérification obligatoire sur `detector`.

## Raisons

- Option A retenue : la garantie ne dit rien du système ; seule la comparaison entre systèmes montre qu'il ne compte pas.
- Option B écartée : les analyses de signal à venir (T40, T41) dépendent de bibliothèques compilées par système.
- Option C écartée : elle ne détecte rien de ce qui fait varier un rapport en pratique.
- Référence sous Linux et Python 3.13 : version médiane de la matrice ; le choix est indifférent, chaque jeu étant comparé à elle.

## Conséquences

- `actions/download-artifact` v8.0.2, épinglé par empreinte de commit (`9000827…`), publié le 2026-10-07, entre dans la CI.
- La CI dure un job de plus, lancé après les neuf jobs de tests.
- Chaque technique livrée ensuite est comparée entre systèmes dès qu'un fichier du corpus d'essai la concerne.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création ; choix de l'option par TheDarkMac, réglages proposés par l'assistant |
