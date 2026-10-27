# ADR-0074 — Texte collé : reporté à T80

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T13
- **Exigences liées** : F-01, F-02, F-03, F-05, F-73 ; A-29 ; ADR-0013, ADR-0036

## Contexte

Le §3 du cahier range le « texte collé » parmi les médias. A-29 relève qu'il n'est pas un fichier : F-02 (format par le contenu), F-03 (extension) et F-05 (empreinte du fichier) ne s'y appliquent pas, et aucune exigence ne décrit sa saisie. ADR-0013 ne lui laisse en V1 que F-73 (caractères invisibles, homoglyphes), dont le module est T80.

## Options envisagées

### Option A — Reporté à T80

- Avantages : la saisie arrive avec le seul module qui peut l'analyser ; T13 reste centrée sur les fichiers.
- Inconvénients : la commande d'analyse n'accepte pas encore de texte.

### Option B — Dès T13

Texte lu sur l'entrée standard et transmis au processus de travail sans fichier temporaire (ES-15).

- Avantages : la commande couvre tout le §3 dès T13.
- Inconvénients : il faut un autre canal que le descripteur d'un fichier régulier (ADR-0036) ; aucun module ne pourrait encore l'analyser.

## Décision

Option A. T13 ne traite que des fichiers. Une exigence de saisie de texte est ajoutée au registre des arbitrages (§4) et rattachée à T80, qui en fixe la forme (entrée standard, canal vers le processus de travail, analyses applicables).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un canal nouveau vers le processus de travail, à sécuriser, pour une entrée qu'aucune analyse n'exploiterait avant T80.

## Conséquences

- Un texte enregistré dans un fichier est déjà accepté : il est identifié comme `texte` (ADR-0070).
- T80 traite A-29 : exigence de saisie, analyses applicables au texte collé, absence d'empreinte de fichier au rapport.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
