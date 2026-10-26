# ADR-0030 — Portée de NF-17 en local : journal et horodatage optionnels, aucune trace par défaut

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T03
- **Exigences liées** : NF-15, NF-16, NF-17 ; constat A-16 ; ADR-0010, ADR-0012 ; menaces M-17, M-24 à M-28

## Contexte

NF-17 exige que chaque soumission, consultation et export soit journalisé (« qui, quand ») et que chaque rapport porte un horodatage fiable. En local et sans compte (ADR-0010), « qui » n'est pas connu, un journal local est modifiable par l'utilisateur, et un horodatage fiable suppose une autorité externe, donc une requête sortante (A-16). Surtout, un journal sur le poste d'un journaliste dit, en cas de saisie, quels fichiers il a eus ; une empreinte y suffit à qui détient l'original (M-27). ADR-0012 garde T91 en V1 et renvoie sa portée à T03.

## Options envisagées

### Option A — Optionnel, sans trace par défaut

- Avantages : rien n'est écrit sur le poste sans que l'utilisateur le décide ; ceux qui ont besoin d'une chaîne de conservation (juristes, ADR-0009) l'activent ; l'horodatage n'envoie qu'une empreinte de rapport.
- Inconvénients : NF-17 n'est pas satisfaite à la lettre par défaut.

### Option B — Journal toujours actif

- Avantages : plus proche de la lettre de NF-17.
- Inconvénients : laisse sur le poste la liste des fichiers examinés, contre NF-15.

### Option C — NF-17 hors V1

- Avantages : le plus simple.
- Inconvénients : T91 sort de la V1, contre ADR-0012 ; aucune aide pour les profils qui doivent établir une chaîne de conservation.

## Décision

NF-17 est reformulée pour le projet : « Le rapport porte toujours la date et l'heure de l'analyse, données par l'horloge du poste et marquées non certifiées. Sur activation explicite, l'outil tient un journal des soumissions, consultations et exports, et fait horodater le rapport par une autorité d'horodatage. » En conséquence :

- **par défaut, aucune trace** : ni journal, ni cache, ni historique ;
- le **journal**, s'il est activé, est chaîné (chaque entrée porte l'empreinte de la précédente, ce qui rend une modification détectable sans l'empêcher), ne contient pas les noms des fichiers, et son activation affiche un avertissement : les empreintes qu'il contient permettent à qui détient l'original de confirmer la possession ; il est déclaré **non probant** ;
- « qui » est **déclaratif** : un nom saisi par l'utilisateur, non vérifié ;
- l'**horodatage** est fait selon la RFC 3161, sur l'**empreinte du rapport** seulement, auprès d'une autorité choisie par l'utilisateur ; c'est une requête sortante optionnelle (RS-03).

## Raisons

- Option A retenue : elle protège les sources par défaut (NF-15) et laisse aux profils qui en ont besoin les moyens d'une chaîne de conservation.
- Option B écartée : un journal permanent fait du poste un registre des fichiers reçus, ce que NF-15 interdit de fait.
- Option C écartée : contraire à ADR-0012, et inutilement restrictive.

## Conséquences

- T91 réalise ES-15 et ES-16 du [modèle de menace](../modele-de-menace/modele-de-menace.md).
- RS-03 entre dans l'inventaire des requêtes sortantes (NF-16).
- La reformulation de NF-17 est inscrite au registre des arbitrages, à faire valider par l'auteur du cahier.
- La documentation utilisateur (T103) explique ce que vaut le journal, et ce qu'il révèle.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
