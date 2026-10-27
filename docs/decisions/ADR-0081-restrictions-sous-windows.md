# ADR-0081 — Restrictions sous Windows : Job Object posé par le travail, intégrité basse

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T14, validée pendant la revue de la PR de T14
- **Tâche** : T14
- **Exigences liées** : NF-01, NF-02, ES-02, ES-03, ES-15 ; M-01, M-04, M-05, M-19 ; ADR-0028, ADR-0035, ADR-0065, ADR-0077

## Contexte

ADR-0035 retient pour Windows un Job Object (un seul processus actif, mémoire, temps processeur), le niveau d'intégrité « bas » et `SetErrorMode` ; le réseau et la lecture n'y sont pas bloqués sans conteneur d'application. Deux points sont « à confirmer en T14 » : l'effet réel du niveau d'intégrité et celui des réglages sur les vidages mémoire. ADR-0065 ajoute que, dans un environnement virtuel, l'interpréteur lancé est un lanceur qui démarre le véritable interpréteur : il faut vérifier que le Job Object couvre ce dernier.

## Options envisagées

Sur le point qui demande un arbitrage, qui pose le Job Object :

### Option A — Le processus de travail s'y affecte lui-même

Avant de lire le fichier, comme les autres restrictions (ADR-0035).

- Avantages : couvre le processus qui lit le fichier, quel que soit le lanceur ; même déroulé que sous Linux et macOS ; aucun intervalle pendant lequel le travail tourne sans Job Object.
- Inconvénients : le lanceur, parent du travail, n'est pas dans le Job Object.

### Option B — Le processus principal y affecte le processus lancé

- Avantages : le lanceur est couvert aussi.
- Inconvénients : le lanceur démarre le véritable interpréteur aussitôt lancé ; l'affectation arrive peut-être après, et le travail serait hors du Job Object. Le lancer suspendu demanderait une fonction non documentée de Windows pour le reprendre.

## Décision

Option A, par `_travail/restrictions/windows.py` :

- Job Object : un seul processus actif ; 2 Gio de mémoire et 120 s de temps processeur par processus ; arrêt à la première exception non traitée ; arrêt du travail à la fermeture du Job Object ; aucun accès au presse-papiers, aux atomes globaux, au bureau ni aux fenêtres des autres processus. Le handle reste ouvert jusqu'à la fin du processus.
- Jeton du processus abaissé au niveau d'intégrité bas (`S-1-16-4096`) ; le fichier et les tubes, déjà ouverts, restent utilisables.
- `SetErrorMode` : aucune fenêtre d'erreur.
- Manques toujours déclarés : `reseau`, `lecture`, `vidage_memoire`. Job Object refusé : `nouveaux_programmes`, `memoire`, `temps` en plus ; niveau bas refusé : `ecriture`.

## Raisons

- Option A retenue : elle couvre à coup sûr le processus exposé. Le lanceur ne lit rien du fichier ; il ne fait qu'attendre le véritable interpréteur.
- Option B écartée : l'intervalle avant l'affectation laisse le travail hors du Job Object, et la reprise d'un processus suspendu passe par une fonction non documentée.
- Lanceur : la CI Windows de T14 vérifie qu'arrêter le lanceur, comme le fait le principal au délai, arrête aussi le véritable interpréteur. Le point d'ADR-0065 est confirmé.
- Niveau bas, confirmé par la CI Windows de T14 (Python 3.12 à 3.14) : depuis un module, l'écriture dans le dossier du dépôt est refusée et l'exécution d'un programme échoue (Job Object) ; la lecture d'un fichier et la création d'une socket restent permises, comme prévu. Une allocation de 3 Gio échoue : `memoire_depassee`.
- Vidages mémoire déclarés manquants : `SetErrorMode` et l'arrêt à la première exception suppriment la fenêtre d'erreur, mais rien ne garantit que le Rapport d'erreurs Windows n'écrive pas de vidage quand le poste est réglé pour le faire ; l'exclure demanderait d'écrire dans le registre, donc une trace durable (ES-15). Le point « à confirmer » d'ADR-0035 l'est par la négative.

## Conséquences

- Sous Windows, l'isolation est toujours réduite : réseau, lecture et vidages manquent, et le rapport le dit. Le conteneur d'application (AppContainer) reste la piste pour aller plus loin, par un nouvel ADR (ADR-0035).
- Le niveau bas laisse écrire dans les rares dossiers marqués « bas » (`LocalLow`) : le processus de travail n'y écrit pas, mais un travail compromis le pourrait.
- La documentation utilisateur (T103) recommande un conteneur sous Windows pour les profils exposés.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR de T14 : statut « Accepté » |
