# ADR-0011 — Logiciel libre et gratuit sous licence Apache-2.0

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §10 (modèle économique et licence) ; NF-07, NF-19 ; constat A-06

## Contexte

Le §10 laisse ouverts le modèle économique et la licence. Le choix pèse sur NF-19 (secret des seuils), puisque dans un logiciel ouvert les seuils sont dans le code (A-06), et sur les dépendances utilisables (T04).

## Options envisagées

### Option A — Open source, licence Apache-2.0

- Avantages : permissive, avec clause explicite sur les brevets ; réutilisable par des rédactions et des intégrateurs ; cohérente avec l'explicabilité et la vérification par un expert.
- Inconvénients : un tiers peut en faire une version fermée.

### Option B — Open source, licence AGPL-3.0

- Avantages : toute version modifiée, même proposée comme service en ligne, reste ouverte.
- Inconvénients : freine les intégrations ; contrainte forte sur les dépendances et les réutilisations.

### Option C — Propriétaire ou payant

- Avantages : permettrait un secret partiel des seuils.
- Inconvénients : contraire à la vérifiabilité par un expert (objectif 4) et à la publication des règles.

### Option D — Principe open source, licence choisie plus tard

- Avantages : laisse le temps de comparer.
- Inconvénients : retarde une contrainte qui pèse sur le choix des dépendances en T04.

## Décision

L'outil est un **logiciel libre et gratuit**, publié sous **licence Apache-2.0**.

## Raisons

- Option A retenue : la diffusion la plus large auprès du public visé (ADR-0009), et la cohérence avec la publication des règles (ADR-0019).
- Option B écartée : le risque qu'elle couvre (service en ligne fermé) n'est pas une priorité pour un outil local (ADR-0010), et elle limite les réutilisations.
- Option C écartée : incompatible avec l'objectif 4 et l'explicabilité.
- Option D écartée : la licence conditionne les dépendances admissibles, à fixer avant T04.

## Conséquences

- T04 : toute dépendance doit avoir une licence compatible avec une diffusion sous Apache-2.0 ; les licences copyleft fortes (GPL, AGPL) sont à éviter pour la bibliothèque.
- Le fichier `LICENSE` est ajouté avec le squelette du projet (T10). Le statut du cahier des charges (document de @Jean versionné dans le dépôt) est à clarifier avec son auteur avant cet ajout : la licence du code ne s'applique pas d'office à un document tiers.
- NF-19 est réexaminée dans ce cadre (ADR-0019).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
