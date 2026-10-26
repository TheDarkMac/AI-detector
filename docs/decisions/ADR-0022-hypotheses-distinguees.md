# ADR-0022 — Hypothèses distinguées : rubrique obligatoire de chaque fiche technique

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac (adoption de la proposition A-02 de l'analyse critique)
- **Tâche** : T02
- **Exigences liées** : F-81, NF-09 ; constats A-02, A-09, A-23

## Contexte

F-81 demande d'indiquer vers quoi pointe chaque constat. La plupart des analyses du signal réagissent à toute transformation, pas spécifiquement à la génération (A-02) : sans règle commune, chaque technique choisirait sa direction et le rapport attribuerait à l'IA une simple recompression.

## Options envisagées

### Option A — Laisser chaque technique fixer ses directions

- Avantages : aucune contrainte nouvelle.
- Inconvénients : directions incohérentes d'une technique à l'autre ; risque d'attribuer à l'IA des transformations banales.

### Option B — Rubrique « hypothèses distinguées » obligatoire

- Avantages : la direction d'un constat découle de ce que la technique sait réellement distinguer, mesuré sur le corpus.
- Inconvénients : chaque fiche demande une mesure par catégorie de corpus.

## Décision

- Chaque fiche technique (NF-09) comporte une rubrique **« hypothèses distinguées »** sur quatre hypothèses : capture brute, transformation banale (recompression, redimensionnement), retouche, génération.
- Une technique ne peut produire la direction « origine IA » que si elle distingue la génération des transformations banales, sur la partie évaluation du corpus. Sinon, ses constats pointent vers ce qu'elle distingue réellement, ou vers « rien de particulier ».
- La fiche précise aussi (A-09) : la question à laquelle la technique répond, les formats où elle s'applique (matrice format × technique, A-23), les données de référence nécessaires, ce qui déclenche un constat.

## Raisons

- Option B retenue : c'est la condition pour implémenter F-81 honnêtement.
- Option A écartée : A-02.

## Conséquences

- Un gabarit de fiche technique est créé avec le dossier `docs/techniques/`, avant la première technique (T20).
- T11 : la direction d'un constat est contrainte par la fiche de sa technique.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : une direction par hypothèse, dont « transformation » (ADR-0055) (T11) |
