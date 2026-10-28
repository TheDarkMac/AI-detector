# ADR-0023 — Reproductibilité à entrées égales et analyse non interrompue

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac (adoption de la proposition A-05 de l'analyse critique)
- **Tâche** : T02
- **Exigences liées** : NF-06, NF-08, F-21, F-72, §6 (rubrique Versions), §8 ; constat A-05

## Contexte

NF-06 et le critère du §8 exigent les mêmes constats pour le même fichier et les mêmes versions de l'outil et du catalogue. Trois éléments l'empêchent (A-05) : la limite de temps (NF-08), qui interrompt une analyse plus tôt sur une machine lente ; les données externes qui changent (liste de confiance, révocation, bases bibliographiques) ; les décodeurs, dont la sortie peut varier d'une version à l'autre.

## Options envisagées

### Option A — Garder NF-06 telle quelle

- Avantages : aucun écart avec le cahier.
- Inconvénients : exigence impossible à satisfaire, donc critère d'acceptation impossible à atteindre.

### Option B — Reformuler NF-06

- Avantages : exigence vérifiable ; les causes de variation deviennent visibles au rapport.
- Inconvénients : rapport plus chargé (rubrique Versions étendue).

## Décision

NF-06 est reformulée pour le projet : « Même fichier ; mêmes versions de l'outil, du catalogue et des dépendances ; mêmes données externes ; analyse non interrompue : mêmes constats. » En conséquence :

- la rubrique **Versions** du rapport inscrit la version de l'outil, du catalogue, des dépendances qui décodent ou analysent le fichier, et de la liste de confiance C2PA ;
- toute donnée externe utilisée (réponse réseau, date de vérification) est inscrite au rapport ;
- une analyse **interrompue** est hors garantie et le rapport le signale.

## Raisons

- Option B retenue : elle rend le critère du §8 atteignable et vérifiable.
- Option A écartée : A-05.

## Conséquences

- T14 choisit entre un budget de travail déterministe et la seule exclusion des analyses interrompues de la garantie ; ce choix n'est pas fait ici.
- T04 fige les versions des dépendances.
- T18 teste la reproductibilité dans ces conditions.
- Les résultats des services tiers sont hors garantie (ADR-0017).
- Le fonctionnement hors ligne par défaut (ADR-0010) réduit les données externes aux fichiers livrés avec l'outil.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : versions des dépendances figées par ADR-0037 (T04) |
| 2026-10-27 | Tranché par ADR-0076 (T14) : budget mixte ; limites comptées dans la garantie, mémoire et temps du système hors garantie |
| 2026-10-28 | Réalisé en T18 : rapport entier comparé à la date et au nom près (ADR-0108), interpréteur ajouté aux versions (ADR-0111), comparaison et `vk --comparer` (ADR-0112), banc et CI entre systèmes (ADR-0110, ADR-0113) |
