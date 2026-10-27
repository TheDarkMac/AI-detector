# ADR-0035 — Systèmes de la V1 et mécanismes d'isolation : Linux en référence, macOS et Windows

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : NF-01, NF-02, NF-08 ; ES-02, ES-03, ES-15 ; constat A-53 ; ADR-0009, ADR-0028

## Contexte

ADR-0028 fixe l'objectif : un processus de travail par fichier, sans réseau, fichier en lecture seule, sans écriture, avec des limites de ressources et les privilèges les plus réduits que le système permet ; « isolation réduite » au rapport si le système ne permet pas tout. Il laisse à T04 le choix des systèmes et des mécanismes. Les trois systèmes courants n'offrent pas les mêmes moyens à un programme non privilégié, et le public visé (ADR-0009) en utilise plusieurs.

## Options envisagées

### Option A — Linux, macOS et Windows ; Linux en référence

- Avantages : couvre le public visé ; chaque système donne ce qu'il peut, et le rapport dit ce qui manque.
- Inconvénients : trois jeux de mécanismes à écrire et à tester ; isolation inégale selon le système.

### Option B — Linux seul en V1

- Avantages : isolation complète ; un seul système à tester.
- Inconvénients : macOS et Windows passent par un conteneur, l'installation lourde qu'ADR-0028 a écartée comme obligation ; une grande part du public est exclue.

### Option C — Linux et macOS

- Avantages : isolation forte sur les deux systèmes.
- Inconvénients : Windows reporté sans raison technique bloquante, ses manques pouvant être signalés au rapport.

## Décision

Les trois systèmes sont pris en charge en V1. Linux sert de référence : c'est le seul où toutes les restrictions d'ADR-0028 sont visées. Mécanismes retenus, tous appliqués par le processus de travail **à lui-même, avant de lire le moindre octet du fichier** (ADR-0036), sans privilège administrateur :

| Restriction | Linux | macOS | Windows |
| --- | --- | --- | --- |
| Réseau | Landlock (TCP, noyau 6.7 ou ultérieur) et filtre seccomp interdisant la création de socket | Profil Seatbelt (`sandbox_init`) : réseau refusé | **Non bloqué** sans conteneur d'application : signalé |
| Système de fichiers | Landlock : aucun accès ; le fichier arrive par un descripteur déjà ouvert | Profil Seatbelt : aucune écriture, lecture limitée à l'installation de Python | Niveau d'intégrité abaissé à « bas » : écriture refusée presque partout ; lecture non restreinte, signalée |
| Nouveaux programmes | seccomp : `execve` refusé ; `no_new_privs` | Seatbelt : exécution refusée | Job Object : un seul processus actif |
| Mémoire | `RLIMIT_AS` | Limite peu fiable du système : surveillance par le processus principal, à confirmer en T14 | Job Object : mémoire par processus |
| Temps | `RLIMIT_CPU` ; délai imposé par le processus principal | Idem | Job Object : temps processeur ; délai imposé par le processus principal |
| Vidages mémoire | `RLIMIT_CORE` à zéro ; `PR_SET_DUMPABLE` à zéro | `RLIMIT_CORE` à zéro | Rapport d'erreur Windows désactivé pour le processus (`SetErrorMode`), effet sur les vidages à confirmer en T14 |

- Les mécanismes sont appelés par `ctypes` ou la bibliothèque standard : aucune dépendance ajoutée.
- Avant de lire le fichier, le processus de travail envoie au processus principal la liste des restrictions appliquées et de celles qui ont échoué. Le rapport en tire « isolation complète » ou « isolation réduite », avec ce qui manque (noyau sans Landlock, réseau non bloqué sous Windows, etc.).
- Un conteneur reste documenté, en option, pour les profils exposés (ADR-0028), et recommandé sous Windows.

## Raisons

- Option A retenue : elle sert tout le public visé, et ADR-0028 a déjà prévu le signalement d'une isolation incomplète.
- Option B écartée : elle impose de fait le conteneur qu'ADR-0028 refusait d'imposer.
- Option C écartée : les manques de Windows sont signalables, ils ne justifient pas d'exclure le système.
- Application par le processus lui-même : les trois systèmes le permettent sans privilège, et le même déroulé sert partout ; tant que le fichier n'est pas lu, le processus n'est pas encore exposé.
- Seatbelt est une interface ancienne et peu documentée d'Apple, mais toujours employée par les navigateurs ; c'est le seul moyen sans privilège sous macOS.
- Landlock ne filtre que TCP : seccomp ferme les autres familles de sockets.

## Conséquences

- T14 écrit les trois jeux de mécanismes, mesure leur effet (tentatives d'accès réseau et disque depuis le processus de travail, ES-11) et fixe les valeurs des limites.
- Les points marqués « à confirmer » (limite mémoire sous macOS, effet réel du niveau d'intégrité et des vidages sous Windows) sont vérifiés en T14 ; un écart donne un erratum ou un nouvel ADR.
- La CI (T10) exécute les tests d'isolation sur les trois systèmes.
- Isolation de Windows à renforcer plus tard : conteneur d'application (AppContainer), par un nouvel ADR.
- La documentation utilisateur (T103) indique, par système, le niveau d'isolation obtenu.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Réalisé en T14 : ADR-0079 à ADR-0081. Points « à confirmer » : mémoire sous macOS surveillée par le principal (ADR-0080) ; niveau d'intégrité bas confirmé ; vidages sous Windows non garantis, déclarés manquants (ADR-0081). Sous macOS, Seatbelt laisse créer une socket et refuse la connexion |
