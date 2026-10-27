# ADR-0079 — Restrictions sous Linux : Landlock sans règle, liste de refus seccomp

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T14, validée pendant la revue de la PR de T14
- **Tâche** : T14
- **Exigences liées** : NF-01, NF-02, ES-02, ES-03, ES-15 ; M-01, M-04, M-05, M-19 ; ADR-0028, ADR-0035, ADR-0036, ADR-0077

## Contexte

ADR-0035 fait de Linux le système de référence et choisit les mécanismes : Landlock, seccomp, `no_new_privs`, `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_CORE`, `PR_SET_DUMPABLE`, appelés par `ctypes`, appliqués par le processus de travail à lui-même avant toute lecture. Restent à fixer l'ensemble de règles de Landlock, la forme du filtre seccomp, ce qui se passe selon la version du noyau, et ce que le processus de travail doit faire avant de se fermer l'accès au disque.

## Options envisagées

Sur le point qui demande un arbitrage, le filtre seccomp :

### Option A — Liste de refus

Tout est permis, sauf une courte liste d'appels refusés avec `EPERM` ; un appel d'une autre architecture tue le processus.

- Avantages : l'interpréteur et les bibliothèques de décodage fonctionnent sans qu'on recense leurs appels ; une liste courte se relit en entier ; `EPERM` donne une exception Python que le module peut constater.
- Inconvénients : un appel dangereux oublié reste permis ; Landlock doit couvrir le reste.

### Option B — Liste d'autorisation

Seuls les appels nécessaires sont permis.

- Avantages : surface minimale.
- Inconvénients : la liste dépend de la version de Python, de la libc et de chaque bibliothèque ; un appel manquant tue le processus de travail sur certains postes seulement.

## Décision

Option A. Dans l'ordre, par `_travail/restrictions/linux.py` :

1. `RLIMIT_AS` à 2 Gio, `RLIMIT_CPU` à 120 s (limite dure à 121 s), `RLIMIT_CORE` à zéro et `PR_SET_DUMPABLE` à zéro ; une limite déjà plus stricte est gardée.
2. `PR_SET_NO_NEW_PRIVS` ; s'il échoue, Landlock et seccomp ne sont pas tentés et tout ce qu'ils couvrent manque.
3. Landlock **sans aucune règle** : chaque droit connu de l'ABI du noyau est géré, aucun n'est accordé. Système de fichiers : rien (le fichier et les tubes, déjà ouverts, restent utilisables) ; TCP à partir de l'ABI 4 ; signaux et sockets abstraites hors du domaine à partir de l'ABI 6. Les attributs sont passés à la taille que le noyau connaît.
4. seccomp : `socket`, `socketpair`, `execve`, `execveat`, `ptrace`, `process_vm_readv`, `process_vm_writev`, `io_uring_setup`, `io_uring_enter`, `io_uring_register` refusés par `EPERM` ; tout appel d'une autre architecture, et sous x86-64 tout appel de l'ABI x32, tue le processus. Architectures : x86-64 et AArch64 ; ailleurs, ou avec un Python 32 bits, seccomp n'est pas appliqué.

Manques déclarés :

| Situation | Manques |
| --- | --- |
| Landlock absent ou désactivé | `lecture`, `ecriture` |
| Landlock ABI 1 ou 2 (troncature non gérée) | `ecriture` |
| seccomp non appliqué | `reseau`, `nouveaux_programmes` |
| Une limite de ressources refusée | `memoire`, `temps` ou `vidage_memoire` |

Avant les restrictions, le processus de travail importe tout ce qu'il emploiera : modules livrés, décodeurs de texte de l'identification. Un module importe à son chargement tout ce dont il a besoin ; un import différé échouerait.

## Raisons

- Option A retenue : la liste d'autorisation casserait l'outil selon le poste, pour un gain faible, Landlock refusant déjà tout accès au système de fichiers.
- Option B écartée pour la même raison.
- Réseau sans Landlock TCP : refuser `socket` suffit, aucune socket n'étant héritée ; Landlock TCP s'y ajoute là où il existe. `io_uring` est refusé parce qu'il crée des sockets sans passer par seccomp.
- `ptrace` et `process_vm_*` refusés : un processus compromis ne lit pas la mémoire d'un autre processus de l'utilisateur ; Landlock le refuse aussi hors de son domaine.
- Landlock sans règle plutôt qu'une lecture de l'installation de Python : tout est importé avant ; un accès en moins, c'est une fuite de moins.
- ABI 1 ou 2 notée « écriture manquante » : un processus pourrait encore tronquer un fichier par son chemin. Mieux vaut un rapport qui le dit.
- Mesuré en T14 : sur le poste de développement (noyau 6.12, ABI 6) et sur les runners Ubuntu de la CI, l'isolation est complète ; lecture, écriture, sockets, connexion, exécution d'un programme et signal à un autre processus sont refusés depuis un module, une allocation de 3 Gio échoue. L'application des restrictions prend 14 à 19 ms.

## Conséquences

- Les modules ne peuvent rien lire ni écrire sur le disque après le verrouillage, ni importer à la demande : règle à rappeler dans le guide des modules et vérifiée par leurs tests.
- Les droits de Landlock apparus après l'ABI 6 ne sont pas gérés, donc permis, tant que le code ne les connaît pas : à revoir avec chaque nouvelle ABI.
- Une nouvelle architecture demande ses numéros d'appel dans la table du module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR de T14 : statut « Accepté » |
