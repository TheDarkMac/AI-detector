# ADR-0105 — Rapport d'évaluation, codes de sortie et corpus d'essai

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : Assistant, proposition non posée en question pendant T17, soumise à la revue de la PR de T17
- **Tâche** : T17
- **Exigences liées** : §8 du cahier, NF-06, NF-09, ES-11, ES-22 ; ADR-0016, ADR-0092, ADR-0099 à ADR-0104

## Contexte

Le banc doit rendre ses mesures sous une forme publiable dans une fiche technique (NF-09) et vérifiable par la CI, et dire clairement quand une évaluation échoue. Avant T100, il n'existe aucun corpus de référence : il faut pourtant éprouver le banc de bout en bout, sans qu'un taux mesuré sur des fichiers de démonstration soit un jour publié.

## Options envisagées

### Option A — JSON et Markdown rendu depuis le JSON ; corpus d'essai déclaré comme tel

- Avantages : un document pour les machines, un pour les fiches, qui ne peuvent pas diverger ; la nature du corpus est écrite dans son manifeste et reprise au rapport.
- Inconvénients : deux fichiers par évaluation.

### Option B — Markdown seul

- Avantages : un seul fichier.
- Inconvénients : la CI et les outils devraient analyser du texte.

### Option C — Pas de corpus d'essai, banc testé seulement par des analyses factices

- Avantages : aucun fichier de démonstration dans le dépôt.
- Inconvénients : le chemin réel (analyse par le processus de travail, sans réseau, depuis le wheel) ne serait jamais éprouvé avant T100.

## Décision

Option A :

- `python -m banc CORPUS --sortie DOSSIER [--partie evaluation|calibrage] [--catalogue DOSSIER] [--desactiver MODULE]`. La partie par défaut est l'évaluation ; `--catalogue` évalue un catalogue candidat avant sa publication.
- Le dossier est créé au besoin (pas ses parents) ; `evaluation.json` et `evaluation.md` y sont créés sans rien écraser, comme les rapports d'analyse (ADR-0092). Le dossier est vérifié avant toute analyse.
- Le document cite : format, date UTC, corpus (nom, version, date, nature, empreinte du manifeste), versions de l'outil, du catalogue et de chaque technique, interfaces réseau vues, bornes et méthode d'intervalle, effectifs, refus par motif, arrêts brutaux, analyses interrompues, mesures d'ADR-0104, écarts. Il ne cite aucun chemin absolu ; les chemins relatifs au corpus n'apparaissent que pour les faux positifs d'une règle.
- `publiable` est vrai seulement pour un corpus de nature `reference` et la partie évaluation ; sinon le Markdown s'ouvre sur « Aucun taux de ce rapport n'est publiable » et dit pourquoi.
- Codes de sortie : 0 sans écart ; 1 avec au moins un écart ; 2 si rien n'est évalué (réseau présent, corpus invalide ou modifié, dossier inutilisable, catalogue invalide, module inconnu) ; 3 en cas de tentative d'accès au réseau, sans rapport écrit.
- Corpus d'essai : `banc/essai/`, neuf fichiers minimaux fabriqués pour T17, couvrant les cinq catégories, de nature `essai`. Leurs octets sont protégés de toute conversion de fin de ligne (`.gitattributes`). La CI l'évalue depuis le wheel, sous `unshare -rn`, et attend le code 1 avec un seul écart : quatre authentiques ne suffisent pas à établir la cible par fichier (ADR-0101).

## Raisons

- Option A retenue : un rapport exploitable par la CI et lisible dans une fiche, et un chemin réel éprouvé à chaque PR.
- Option B écartée : vérifier du texte est fragile.
- Option C écartée : le banc ne serait éprouvé qu'à moitié.
- Code 1 attendu sur le corpus d'essai : le banc dit vrai ; un code 0 sur quatre fichiers serait un défaut.

## Conséquences

- Le format du document porte un numéro (`format` = 1) ; un changement incompatible l'augmente.
- Un rapport d'évaluation n'est pas reproductible octet pour octet (date) ; ses mesures le sont à corpus, outil et catalogue identiques (T18).
- T101 publiera les rapports d'évaluation du corpus de référence.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
