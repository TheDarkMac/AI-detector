# ADR-0024 — Une méthode de vérification par exigence

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac (adoption de la proposition A-08 de l'analyse critique)
- **Tâche** : T02
- **Exigences liées** : §8 (critère « chaque exigence couverte par un test ») ; constat A-08

## Contexte

Le §8 exige que chaque exigence F et NF soit couverte par au moins un test. Plusieurs ne se testent pas automatiquement : NF-12 (accessibilité), NF-13 (conformité), NF-14 (honnêteté des textes), NF-15 (un document à rédiger), l'étude d'usage (A-08).

## Options envisagées

### Option A — Un test automatisé par exigence

- Avantages : fidèle au cahier.
- Inconvénients : impossible pour plusieurs exigences ; pousserait à écrire des tests factices.

### Option B — Une méthode de vérification par exigence

- Avantages : chaque exigence a une vérification réelle et identifiée ; méthode classique d'ingénierie des exigences.
- Inconvénients : les vérifications non automatisées doivent être refaites à la main à chaque version.

## Décision

Chaque exigence reçoit une **méthode de vérification** parmi quatre : **inspection** (relecture), **analyse** (raisonnement, calcul), **démonstration** (essai manuel consigné), **test** (automatisé). Le critère du §8 est reformulé pour le projet : « Chaque exigence F et NF a une méthode de vérification identifiée et un résultat consigné. » La méthode « test » est la règle par défaut ; une autre méthode est justifiée dans la matrice.

## Raisons

- Option B retenue : elle donne une vérification réelle à chaque exigence.
- Option A écartée : A-08.

## Conséquences

- T17 : la matrice de traçabilité porte une colonne « méthode » et une colonne « résultat ».
- La reformulation du critère est inscrite au registre des arbitrages.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
