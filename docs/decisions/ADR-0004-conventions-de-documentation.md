# ADR-0004 — Conventions de documentation

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac (exigence) ; organisation proposée par l'assistant
- **Tâche** : T00
- **Exigences liées** : méthode de travail ; NF-07, NF-09

## Contexte

Consigne de TheDarkMac : toute règle et convention est documentée, ainsi que chaque étape réalisée, chaque décision prise **ou non prise** (pourquoi tel choix, pourquoi pas tel autre), et chaque erreur ou modification.

## Options envisagées

### Support

- **Wiki GitHub** : séparé du code, non versionné avec lui, non soumis aux PR.
- **Outil externe** (documents partagés) : hors du dépôt, sans lien avec les commits.
- **Markdown dans le dépôt** *(retenu)* : versionné avec le code, relu dans les mêmes PR, lisible sur GitHub.

### Organisation

- **Un seul journal chronologique** : simple, mais les décisions et les erreurs s'y perdent.
- **Trois registres séparés** *(retenu)* : décisions (ADR), journal par tâche, errata ; plus une table d'historique dans chaque document vivant.

### Format des décisions

- **Format ADR de Nygard** (contexte, décision, conséquences) : court, mais ne garde pas trace des options rejetées.
- **Format ADR enrichi** *(retenu)* : ajoute « Options envisagées » et « Raisons », pour répondre à l'exigence « pourquoi ceci n'a pas été choisi ».

### Langue

- **Anglais** : vocabulaire technique standard.
- **Français** *(retenu)* : langue du cahier des charges et de TheDarkMac. Les identifiants techniques (noms de code, types de commit) restent en anglais.

## Décision

- Documentation en Markdown, en français, sous `docs/`, organisée comme décrit dans `docs/README.md`.
- Toute PR de tâche contient son entrée de journal ; tout choix donne un ADR ; toute erreur donne un erratum.
- Un ADR accepté n'est jamais réécrit sur le fond : il est remplacé par un nouvel ADR.
- Un erratum est écrit même pour une erreur corrigée aussitôt.

## Raisons

- Le dépôt est la seule source qui garantit que la documentation correspond à l'état du code à chaque commit.
- La séparation en registres permet de retrouver une décision ou une erreur sans relire tout le récit.
- Remplacer plutôt que réécrire préserve la trace des changements d'avis.

## Conséquences

- Chaque PR coûte un peu de rédaction en plus ; la checklist du modèle de PR le rappelle.
- Le lint Markdown (ADR-0006) garde une forme homogène.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
