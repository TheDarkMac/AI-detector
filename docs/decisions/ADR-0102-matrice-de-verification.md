# ADR-0102 — Matrice de vérification : marqueurs dans les tests, fichier TOML, rendu vérifié

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T17
- **Exigences liées** : §8 du cahier (« chaque exigence couverte par un test »), ADR-0024 ; A-08, A-11, A-27, A-58 ; ERR-0001

## Contexte

ADR-0024 reformule le critère du §8 : chaque exigence a une méthode de vérification identifiée (test, inspection, analyse, démonstration) et un résultat consigné ; la matrice de traçabilité de T17 porte ces colonnes, exigences de sécurité comprises (ADR-0027). ERR-0001 a montré le risque de citer une exigence qui n'existe pas. Il faut choisir où vivent ces liens pour qu'ils ne dérivent pas.

## Options envisagées

### Option A — Marqueurs dans les tests et fichier TOML, rendu Markdown vérifié

Les tests citent leurs exigences par un marqueur pytest `exigence("F-01")` ; `docs/verification/matrice.toml` porte l'état, les tâches, les autres méthodes et leur résultat ; un script en tire `matrice.md` et vérifie la cohérence des deux.

- Avantages : le lien test → exigence est écrit à côté du test et suit ses changements ; un identifiant inexistant est refusé dès la collecte ; la CI peut joindre la matrice remplie avec le résultat de chaque test.
- Inconvénients : un marqueur de plus dans les tests ; `matrice.md` doit être régénéré quand la liste des fichiers de tests d'une exigence change.

### Option B — Tableau Markdown tenu à la main

- Avantages : simple.
- Inconvénients : les tests cités dérivent sans que rien ne le voie.

### Option C — Tout dans le TOML, tests cités par leur nom complet

- Avantages : pas de marqueur dans les tests.
- Inconvénients : liste à tenir à jour à chaque test ajouté, renommé ou paramétré.

## Décision

Option A :

- Marqueur `exigence(*identifiants)` déclaré dans `pyproject.toml` ; posé sur un fichier de tests (`pytestmark`) pour son sujet principal, sur un test pour une exigence annexe. La collecte refuse un marqueur vide ou qui cite une exigence absente de la matrice (`tests/conftest.py`).
- `python -m banc.matrice` lit les exigences à leur source (F et NF du cahier, ES du modèle de menace, principes de la matrice, cas d'usage du cahier), collecte les tests sans les exécuter, vérifie la matrice et écrit `docs/verification/matrice.md`. `--verifier` échoue si la matrice est incohérente ou si `matrice.md` n'est pas à jour : `tests/test_matrice.py` le lance, donc chaque passage de la CI.
- La CI remplit la matrice avec le résultat de chaque test du passage (`--resultats` sur le rapport JUnit de pytest) et la joint à ses artefacts, pour chaque système et chaque version de Python. La version du dépôt renvoie à ces passages pour le résultat des tests.

## Raisons

- Option A retenue : chaque lien est écrit là où il change, et tout écart (exigence inconnue, exigence réalisée sans test, test sur une exigence à venir, rendu périmé) fait échouer la CI.
- Option B écartée : rien n'empêcherait la dérive.
- Option C écartée : la liste nominative des tests serait la première à se périmer.

## Conséquences

- Les contrôles et les états sont fixés par ADR-0106.
- Le résultat d'un test n'est pas recopié dans le dépôt : il change à chaque passage, et un résultat commité serait faux dès le passage suivant.
- Tout test nouveau qui vérifie une exigence porte le marqueur ; toute exigence qui passe à « réalisée » ou « partielle » avec la méthode « test » doit avoir au moins un test marqué.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
