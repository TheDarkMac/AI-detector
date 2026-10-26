# ADR-0054 — Représentation du modèle : dataclasses figées et JSON Schema écrits à la main

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; réglages fins fixés par l'assistant
- **Tâche** : T11
- **Exigences liées** : F-83, §6 ; ES-04, ES-15 ; ADR-0025, ADR-0036, ADR-0043, ADR-0047

## Contexte

T11 doit donner une forme aux observations, constats, analyses non menées, à la couverture et au rapport, et écrire les schémas des messages du processus de travail (ADR-0036) et du rapport (ADR-0025). Ces objets sont construits dans le processus de travail P2, qui lit un fichier hostile, puis transmis en JSON au processus principal P1, qui doit les valider avant d'y croire (ES-04). Le schéma du rapport est un contrat publié (ADR-0025).

## Options envisagées

### Option A — Dataclasses figées de la bibliothèque standard, JSON Schema écrits à la main, validés par `jsonschema`

- Avantages : aucune dépendance pour construire les objets ; invariants vérifiés dès la construction, dans P1 comme dans P2 ; le schéma publié est un texte lu et versionné tel quel ; `jsonschema` est déjà la bibliothèque prévue par ADR-0043.
- Inconvénients : la même règle est écrite deux fois (code et schéma) ; il faut des tests pour garantir qu'elles disent la même chose.

### Option B — pydantic : modèle et schéma générés depuis le code

- Avantages : une seule écriture ; validation rapide.
- Inconvénients : dépendance lourde (`pydantic-core`, en Rust) hors de la liste d'ADR-0043 ; le schéma publié dépend de la version de pydantic qui le génère et peut changer sans que le modèle change.

### Option C — Dictionnaires typés (`TypedDict`) et JSON Schema

- Avantages : très léger.
- Inconvénients : aucun invariant vérifié à la construction ; un constat incohérent peut circuler dans P1 tant que personne n'appelle le valideur.

## Décision

- Le modèle est écrit en **dataclasses figées** (`frozen`, `slots`) dans `voight_kampff/rapport/modele.py`, qui n'importe que la bibliothèque standard : P2 l'utilise sans charger `jsonschema`. Chaque classe vérifie ses invariants à la construction et offre `vers_dict` et `depuis_dict`.
- Les schémas sont **écrits à la main**, en JSON Schema Draft 2020-12 : `schemas/rapport.schema.json` et `schemas/messages.schema.json`, livrés dans le paquet. Le schéma des messages reprend les définitions de celui du rapport.
- **Validation dans P1** : un document reçu passe toujours par le schéma, puis par `depuis_dict`. Les renvois entre objets (paramètres de phrase, observations citées, couverture) et certaines contraintes de valeur ne s'expriment pas en JSON Schema : seul le code les vérifie (liste au §7 du [modèle de données](../modele-de-donnees/modele-de-donnees.md)).
- **Dépendances** : `jsonschema` (≥ 4.26) en dépendance d'exécution ; `types-jsonschema` en dépendance de développement, `jsonschema` ne publiant pas ses annotations de types (mypy strict, ADR-0047).

Réglages fixés par l'assistant :

- **Version unique** `VERSION_SCHEMA = "0.1.0"` pour le modèle, le schéma du rapport et celui des messages (ADR-0036) ; elle figure dans chaque rapport et dans le premier message de P2.
- **Identifiants des schémas** en URN (`urn:voight-kampff:schema:rapport`, `urn:voight-kampff:schema:messages`) ; le registre de `referencing` ne connaît que ces deux fichiers et n'a **aucune fonction de récupération** : un renvoi inconnu échoue au lieu d'être téléchargé (NF-16). Testé.
- **Messages d'erreur** : `DocumentInvalide` ne cite que l'emplacement de la règle dans le schéma ; les erreurs du modèle ne citent que le nom du champ. Aucune valeur reçue n'y figure (ES-15). Testé.
- **Expressions des schémas** : seulement des classes de caractères ancrées, sans répétition imbriquée (temps linéaire), toujours accompagnées d'une longueur maximale. `$` est suivi de `(?!\n)`, parce que le `$` de Python accepte un saut de ligne final que celui d'ECMAScript refuse.
- **Bornes de structure** : identifiants de 128 caractères, versions de 64, textes de 4 096, listes de 4 096 éléments, nombres dans l'intervalle des entiers signés sur 64 bits. Les limites de taille d'un message et d'un rapport restent à T14.

## Raisons

- Option A retenue : elle garde le contrat publié lisible et stable, ne charge rien de plus dans P2, et place les invariants là où les objets naissent.
- Option B écartée : dépendance lourde hors politique (ADR-0043) et schéma publié soumis aux versions d'un générateur.
- Option C écartée : un objet incohérent pourrait exister dans P1, ce que ES-04 cherche justement à empêcher.

### Examen de `jsonschema` (critères d'ADR-0043)

Fait le 2026-10-26 sur PyPI, aux versions verrouillées.

| Paquet | Version | Licence | Paquets | Remarque |
| --- | --- | --- | --- | --- |
| `jsonschema` | 4.26.0 (janv. 2026) | MIT | Python pur | Ne résout aucun renvoi distant par défaut depuis `referencing` |
| `referencing` | 0.37.0 | MIT | Python pur | `typing-extensions` (PSF-2.0) sous Python 3.12 seulement |
| `jsonschema-specifications` | 2025.9.1 | MIT | Python pur | Métaschémas livrés dans le paquet |
| `attrs` | 26.1.0 | MIT | Python pur | — |
| `rpds-py` | 2026.9.1 | MIT | Rust, précompilé pour Linux, macOS et Windows, Python 3.12 à 3.14 | Déjà relevé en T10 (architecture §9) |
| `types-jsonschema` | 4.26.0.20261006 | Apache-2.0 | Annotations seules | Développement seulement |

Licences compatibles avec Apache-2.0, aucun accès réseau, exécuté dans P1 sur des données venues de P2 (jamais sur le fichier lui-même). pip-audit ne signale aucune faille connue.

## Conséquences

- Toute règle du modèle est écrite deux fois ; les tests comparent les énumérations, les bornes et la version, et confrontent code et schéma sur une liste d'altérations qui doivent être refusées par les deux.
- T12 applique la séquence « décodage JSON strict (sans `NaN` ni infini), schéma, `depuis_dict` » à chaque message ; un échec donne une analyse non menée de raison `message_invalide` (ADR-0056).
- Changer le modèle change `VERSION_SCHEMA` ; la règle de numérotation sera fixée avec la première publication du schéma (T16).
- La phrase de l'architecture « une donnée hostile n'est jamais confrontée à une expression régulière dans P1 » vise les expressions du catalogue ; les expressions fixes et linéaires des schémas en sont exclues (architecture v1.2, §6).
- Le job `paquet` de la CI vérifie que les schémas sont livrés dans le wheel et chargeables.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
