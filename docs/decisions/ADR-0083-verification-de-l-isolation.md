# ADR-0083 — Vérification de l'isolation : depuis un module, et code restreint hors de la couverture

- **Statut** : Proposé
- **Date** : 2026-10-27
- **Décideur** : l'assistant, proposition non posée en question pendant T14, soumise dans la PR de T14
- **Tâche** : T14
- **Exigences liées** : ES-02, ES-11, ES-15 ; ADR-0024, ADR-0035, ADR-0048, ADR-0051

## Contexte

ADR-0035 demande de mesurer l'effet des restrictions par des tentatives d'accès depuis le processus de travail, sur les trois systèmes de la CI. Or un processus restreint ne peut plus écrire sur le disque : coverage, qui y écrit ses mesures en fin de processus, ne peut plus rien enregistrer. Avant T14, plusieurs tests mesuraient la couverture dans le processus de travail lancé. Et les tests qui exécutent le déroulé dans le processus des tests appliqueraient les restrictions à pytest lui-même.

## Options envisagées

Sur le point qui demande un arbitrage, la mesure de couverture du code restreint :

### Option A — Effet vérifié depuis un module, appels au système exclus de la mesure

Les fonctions qui construisent les restrictions sont pures et testées dans le processus des tests ; celles qui appellent le système sont marquées `pragma: no cover` et vérifiées par leur effet, depuis un module du factice, dans un vrai processus de travail restreint.

- Avantages : le vrai déroulé, sans option de contournement dans le code livré ; l'effet est mesuré là où il compte.
- Inconvénients : quelques dizaines de lignes hors de la mesure de couverture.

### Option B — Option de l'outil qui désactive les restrictions

- Avantages : tout est mesuré.
- Inconvénients : une option du code livré qui retire l'isolation est une surface d'attaque, et les tests ne vérifieraient plus le vrai déroulé.

### Option C — Transmettre les mesures par le protocole

- Avantages : tout est mesuré, sans option de contournement.
- Inconvénients : coverage n'offre pas d'interface stable pour cela ; le protocole porterait des données de test.

## Décision

Option A :

- `tests/test_isolation.py` lance le factice, qui exécute le vrai déroulé avec ses vraies restrictions. Le module `sonde` y tente : lire un fichier du dépôt, y créer un fichier, créer une socket, se connecter en TCP, lancer un programme ; il renvoie pour chaque essai « permise » ou le nom de l'exception. Le module `memoire` remplit 3 Gio. Les attentes par système sont dans `tests/systeme.py`.
- Le déroulé exécuté dans le processus des tests reçoit un restricteur factice (`restreindre`), comme il reçoit déjà une identification factice.
- Sous coverage, le factice est lancé avec `--sans-restriction` : option du script de test, pas de l'outil. Le point d'entrée du processus de travail est mesuré par un lancement qui s'arrête avant les restrictions, faute de descripteur.
- `tests/test_traces.py` (ES-15) lance une analyse avec des dossiers personnels, temporaires, de cache et de travail neufs, et vérifie qu'ils restent vides et que le dossier du fichier n'a pas changé.

## Raisons

- Option A retenue : elle vérifie ce qu'ES-02 exige (ce que le processus de travail ne peut pas faire), et le code livré n'a aucun moyen de se passer de l'isolation.
- Option B écartée : une option qui retire l'isolation finirait par être employée hors des tests.
- Option C écartée : du code de test dans le protocole, pour une interface de coverage non garantie.
- Effet testé depuis un module : c'est l'endroit où un analyseur compromis agirait.

## Conséquences

- La couverture reste à 100 % sous Linux, lignes et branches ; le code d'appel au système de chaque plateforme est marqué, et sa vérification est l'échec ou la réussite des tests d'isolation de la CI de la plateforme.
- Un module de test qui doit lire ou écrire sur le disque doit le faire avant les restrictions, ou être lancé avec `--sans-restriction`.
- La matrice de vérification (T17) cite ces tests pour ES-02, ES-11 et ES-15.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
