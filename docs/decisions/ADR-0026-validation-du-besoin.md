# ADR-0026 — Validation du besoin sur prototype, étude d'usage hors V1

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §8 (étude d'usage, critère d'acceptation) ; §10 (validation du besoin) ; constat A-57

## Contexte

Le §10 demande de valider le besoin auprès d'utilisateurs réels avant de figer le périmètre. Le §8 prévoit une étude d'usage (biais d'automatisation) comme critère d'acceptation ; elle implique des participants humains (protocole, consentement, données personnelles) et « erreur grave » n'est pas défini (A-57).

## Options envisagées

### Option A — Recueil d'avis sur un prototype, étude d'usage après la V1

- Avantages : les utilisateurs réagissent à un outil réel, pas à une description ; le démarrage n'est pas retardé.
- Inconvénients : une part du socle est construite avant toute validation.

### Option B — Entretiens avant le code

- Avantages : périmètre confirmé avant d'investir.
- Inconvénients : retarde le démarrage ; avis sur une description plutôt que sur un outil.

### Option C — Aucune validation externe

- Avantages : aucun coût.
- Inconvénients : périmètre fondé sur la seule analyse ; critère d'étude d'usage abandonné.

## Décision

- Le périmètre V1 (ADR-0012) est **provisoire**. Dès que les métadonnées et C2PA fonctionnent (après T30), un **prototype** est soumis à quelques vérificateurs ; leurs avis sont consignés dans `docs/`, et un changement de périmètre donne un nouvel ADR.
- L'**étude d'usage** est hors V1 : le critère du §8 qui la concerne ne s'applique pas à l'acceptation de la V1. Son protocole sera rédigé en T104.
- Définition retenue de l'**erreur grave**, pour T104 : conclure « généré » ou « retouché » sur un fichier authentique.

## Raisons

- Option A retenue : un avis sur un outil réel vaut mieux qu'un avis sur une description, sans retarder le travail.
- Option B écartée : retarde le démarrage pour un avis moins fiable.
- Option C écartée : le risque de construire un outil inadapté est réel (A-15).

## Conséquences

- Une tâche T105 « recueil d'avis sur prototype » est ajoutée au découpage, placée après T30.
- Le recueil d'avis implique des personnes : consentement et minimisation des données collectées, à prévoir dans T105.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
