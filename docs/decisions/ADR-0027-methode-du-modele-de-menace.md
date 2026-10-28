# ADR-0027 — Méthode du modèle de menace : STRIDE et cas d'abus

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T03
- **Exigences liées** : NF-15 ; §9 livrable 7

## Contexte

NF-15 impose un modèle de menace avant tout choix d'architecture, sans en fixer la forme. La méthode détermine ce que le modèle risque d'oublier. Deux familles de risques coexistent ici : la sécurité d'un outil qui lit des fichiers hostiles, et la protection des sources, où l'outil peut nuire même en fonctionnant comme prévu (double usage, A-14).

## Options envisagées

### Option A — STRIDE par élément d'un diagramme de flux, plus des cas d'abus, cotation qualitative

- Avantages : STRIDE oblige à examiner six catégories pour chaque élément, ce qui limite les oublis ; les cas d'abus couvrent les usages nuisibles d'un outil qui fonctionne bien ; une grille à trois niveaux suffit à ordonner l'effort.
- Inconvénients : la cotation qualitative reste une appréciation.

### Option B — STRIDE et LINDDUN complet

- Avantages : LINDDUN examine sept catégories de menaces sur la vie privée pour chaque élément ; le plus exhaustif sur les sources.
- Inconvénients : environ deux fois plus long ; pour un outil local sans compte, beaucoup de catégories se recoupent avec STRIDE (divulgation) ou ne s'appliquent pas (liaison entre comptes).

### Option C — Arbres d'attaque par bien

- Avantages : bonne lecture des scénarios à plusieurs étapes.
- Inconvénients : ne couvre que les chemins qu'on a pensé à dessiner.

## Décision

Option A : diagramme de flux avec frontières de confiance, STRIDE par élément, cas d'abus, cotation vraisemblance × gravité à trois niveaux avant mesures, exigences de sécurité numérotées (ES-xx) rattachées aux tâches.

## Raisons

- Option A retenue : elle couvre les deux familles de risques à un coût proportionné au projet.
- Option B écartée : le surcroît de longueur porte surtout sur des catégories qui ne s'appliquent pas à un outil local sans compte ; les menaces sur les sources sont traitées par la catégorie « divulgation » de STRIDE et par les cas d'abus.
- Option C écartée : sa couverture dépend de l'imagination du rédacteur, ce que STRIDE cherche justement à corriger.

## Conséquences

- Le [modèle de menace](../modele-de-menace/modele-de-menace.md) suit cette structure ; chaque révision la conserve.
- Les exigences ES-xx entrent dans la matrice de vérification de T17 (ADR-0024).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-28 | Réalisé en T17 : exigences ES-01 à ES-22 dans la matrice de vérification (ADR-0102) |
