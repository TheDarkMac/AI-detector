# ADR-0082 — Fuzzing des analyseurs par Hypothesis

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T14
- **Exigences liées** : ES-04, ES-19, NF-02, NF-03 ; M-01 à M-05, M-10 ; ADR-0037, ADR-0043, ADR-0048, ADR-0052, ADR-0070

## Contexte

ES-19 demande le fuzzing des analyseurs de chaque format de la V1, identification comprise (ADR-0070). Aucun module d'analyse n'existe encore ; trois analyseurs lisent déjà des données hostiles : l'identification (le fichier), le décodage strict des lignes et la réception des messages par le processus principal (ce qu'envoie un processus de travail peut-être compromis). ADR-0048 laissait à T14 le choix de l'outil, intégré à pytest ou lancé à part.

## Options envisagées

### Option A — Hypothesis

- Avantages : dépendance de développement seulement ; intégrée à pytest, jouée par la CI sur les trois systèmes ; exemples tirés d'une graine fixe, donc identiques d'un passage à l'autre ; réduction automatique d'un exemple en échec.
- Inconvénients : exploration guidée par des stratégies, pas par la couverture du code.

### Option B — Atheris

- Avantages : fuzzing guidé par la couverture (libFuzzer), le plus efficace pour trouver des failles.
- Inconvénients : extension C, Linux et macOS seulement, paquets souvent en retard sur les versions de Python ; lancé à part de pytest.

### Option C — Fuzzeur écrit dans les tests

- Avantages : aucune dépendance.
- Inconvénients : exploration plus pauvre ; code de plus à maintenir.

## Décision

Option A. `hypothesis` rejoint le groupe `dev` de `pyproject.toml`, en version 6.170.4. `tests/test_fuzzing.py` vérifie, pour chaque analyseur, qu'il rend un résultat valide ou refuse par l'erreur prévue, jamais autre chose :

- identification : octets quelconques et échantillons valides mutés (octets remplacés, insérés, supprimés, coupés, échantillons recollés) ; parties conformes au modèle, même résultat à chaque appel ;
- décodage strict : octets quelconques ; aller-retour d'un objet JSON ;
- réception : suites de messages valides dont des champs ont été remplacés ; seul refus admis, `message_invalide`.

Deux profils, dans `tests/conftest.py` :

| Profil | Exemples | Graine | Usage |
| --- | --- | --- | --- |
| `defaut` | 300 par test | Fixe | Chaque passage de pytest, CI comprise |
| `campagne` | 200 000 par test | Aléatoire | Recherche longue, lancée à la main : `VK_FUZZING=campagne` |

Aucun des deux n'écrit de base d'exemples ; un échec affiche de quoi le rejouer (`@reproduce_failure`). Le cache de constantes qu'Hypothesis garde dans `.hypothesis/` est ignoré par git.

## Raisons

- Option A retenue : seule des trois à tourner partout dans la CI à chaque PR, de façon reproductible.
- Option B écartée : elle exclut Windows, système de la V1 (ADR-0035), et suit mal les versions de Python (ADR-0051). Elle reste possible pour une campagne ponctuelle sous Linux, par un nouvel ADR.
- Option C écartée : Hypothesis fait mieux pour le même usage, sans code à maintenir.
- Version 6.170.4 plutôt que la dernière (6.170.12, publiée la veille) : publiée depuis plus de 7 jours, comme le veut le délai appliqué à Dependabot (ADR-0052). Seule dépendance ajoutée : `sortedcontainers` 2.4.0.
- Graine fixe en CI : un échec se rejoue à l'identique ; la variété vient des campagnes.

## Conséquences

- Chaque module d'analyse de la V1 ajoute ses propriétés de fuzzing à côté de ses tests (T20 et suivantes), avec ses échantillons.
- Le fuzzing ajoute une vingtaine de secondes à la suite de tests ; à surveiller quand les modules s'ajouteront.
- La catégorie « malformés » du corpus (T100, T102) reste à constituer.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
