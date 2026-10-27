# ADR-0048 — Tests : pytest et coverage.py

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; réglages fins fixés par l'assistant
- **Tâche** : T10
- **Exigences liées** : §8 du cahier ; NF-09 ; ES-11, ES-19 ; ADR-0024, ADR-0035

## Contexte

Chaque exigence a une méthode de vérification (ADR-0024), et la plupart seront vérifiées par des tests automatiques. Certains tests ne valent que sur un système (isolation, T14 et ADR-0035) ; d'autres porteront sur de nombreux fichiers d'exemple (T17, T20).

## Options envisagées

### Option A — pytest et coverage.py

- Avantages : standard de fait ; paramétrage d'un test par une liste de fichiers ; marqueurs pour les tests propres à un système ; couverture mesurée, y compris dans les processus lancés par les tests.
- Inconvénients : deux dépendances de développement.

### Option B — unittest seul

- Avantages : bibliothèque standard, aucune dépendance.
- Inconvénients : plus verbeux ; paramétrage pauvre ; aucune mesure de couverture.

## Décision

- Les tests sont écrits pour **pytest** dans `tests/` ; la couverture est mesurée par **coverage.py**, branches comprises.
- Réglages fixés par l'assistant : marqueurs et options de configuration inconnus refusés (`--strict-markers`, `--strict-config`) ; un test marqué « échec attendu » qui réussit fait échouer la suite (`xfail_strict`) ; import des tests sans modifier le chemin d'import (`--import-mode=importlib`).
- La couverture suit aussi les interpréteurs lancés par les tests (`patch = ["subprocess"]`) : le processus de travail (ADR-0036) sera mesuré.
- Aucun seuil minimal de couverture n'est imposé en T10 : le squelette est couvert à 100 %, mais un seuil fixé sur trois fichiers ne voudrait rien dire. À fixer quand le socle existe (T12 à T14).

## Raisons

- Option A retenue : paramétrage et marqueurs par système sont nécessaires dès T13 et T14 ; la couverture des processus lancés évite un angle mort sur le code le plus exposé.
- Option B écartée : elle ne mesure pas ce que les tests laissent de côté.

## Conséquences

- La CI lance les tests sur les trois systèmes et trois versions de Python (ADR-0051).
- Le fuzzing des analyseurs (ES-19, T14) choisira son propre outil ; il s'intégrera à pytest ou tournera à part.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Précisé en T14 : fuzzing par Hypothesis, intégré à pytest (ADR-0082) ; code d'appel au système des restrictions exclu de la couverture, vérifié par son effet (ADR-0083) |
