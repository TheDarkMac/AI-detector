# ADR-0014 — Contrôle avant publication limité aux métadonnées en V1

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : F-90, F-91, CU-5, NF-15, NF-18 ; §3 (hors périmètre) ; constats A-14, A-45

## Contexte

Le §5.6 sert la protection des sources, un autre besoin que la détection (ADR-0008). Plusieurs de ses fonctions sont à double usage : les points de traçage d'imprimante (F-90) et la comparaison d'exemplaires (F-91) permettent aussi de retrouver l'auteur d'une fuite (A-14). Le §10 demande en outre si l'anonymisation des marques identifiantes est une fonction future.

## Options envisagées

### Option A — Métadonnées identifiantes seulement en V1

- Avantages : utile au public visé (ADR-0009) avant publication ; repose sur l'extraction des métadonnées déjà prévue ; pas de nouvel usage d'identification.
- Inconvénients : les marques invisibles (points de traçage) ne sont pas signalées en V1.

### Option B — Tout le §5.6 en V1

- Avantages : contrôle complet.
- Inconvénients : met en service des fonctions d'identification de source avant que le modèle de menace en ait évalué le double usage.

### Option C — Aucun contrôle avant publication en V1

- Avantages : V1 plus courte.
- Inconvénients : les données identifiantes sont seulement masquées (NF-18), sans être signalées comme risque.

## Décision

- V1 : T25 signale les **marques identifiantes des métadonnées** (auteur, numéro de série d'appareil, coordonnées GPS, logiciel nominatif).
- Points de traçage (T94) et comparaison d'exemplaires (T93) : décision reportée après le modèle de menace (T03), au plus tôt en V2.
- **Anonymisation** des marques : hors périmètre, conformément au §3 (l'outil ne modifie aucun fichier).

## Raisons

- Option A retenue : elle protège les sources sans fournir d'outil d'identification.
- Option B écartée : le modèle de menace doit d'abord dire qui est l'adversaire quand l'outil sert à chercher l'auteur d'une fuite (A-14).
- Option C écartée : le signalement des métadonnées identifiantes coûte peu et sert directement les journalistes.
- Anonymisation écartée : elle contredit le hors-périmètre « modification de fichiers » ; l'outil peut indiquer les marques à retirer, pas les retirer.

## Conséquences

- T03 traite explicitement le double usage de F-35, F-90 et F-91.
- Le nom du fichier est traité comme une donnée identifiante (A-48), masqué par défaut (T16).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
