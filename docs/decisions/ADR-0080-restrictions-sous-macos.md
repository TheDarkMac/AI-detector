# ADR-0080 — Restrictions sous macOS : profil Seatbelt, mémoire surveillée par le principal

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T14, validée pendant la revue de la PR de T14
- **Tâche** : T14
- **Exigences liées** : NF-01, NF-02, ES-02, ES-03, ES-15 ; M-01, M-04, M-05, M-19 ; ADR-0028, ADR-0035, ADR-0077, ADR-0078

## Contexte

ADR-0035 retient pour macOS un profil Seatbelt (`sandbox_init`) : réseau refusé, aucune écriture, lecture limitée à l'installation de Python, exécution refusée ; `RLIMIT_CORE` à zéro. Il marque un point « à confirmer en T14 » : la limite de mémoire, que macOS n'applique pas de façon fiable, serait surveillée par le processus principal. Restent à écrire le profil et la surveillance.

## Options envisagées

Sur le point qui demande un arbitrage, la mémoire :

### Option A — Surveillance par le processus principal

Pendant qu'il attend les messages, le principal mesure tous les dixièmes de seconde l'empreinte physique du travail (`proc_pid_rusage`) et l'arrête au-delà de 2 Gio.

- Avantages : ne dépend pas d'une limite que macOS n'applique pas ; même raison que sur les autres systèmes ; aucune dépendance.
- Inconvénients : une surveillance, pas une limite stricte : entre deux mesures, le travail peut dépasser la limite de ce qu'il alloue en un dixième de seconde.

### Option B — `RLIMIT_AS` dans le processus de travail

- Avantages : même code que sous Linux.
- Inconvénients : macOS ne l'applique pas aux allocations par `mmap` (ADR-0035) ; le rapport dirait une limite qui n'existe pas.

### Option C — Mémoire déclarée manquante

- Avantages : aucune surveillance à écrire.
- Inconvénients : une bombe peut épuiser la mémoire du poste ; l'isolation serait toujours réduite sous macOS.

## Décision

Option A, et le profil suivant, appliqué par `_travail/restrictions/macos.py` :

```text
(version 1)
(deny default)
(allow file-read* (subpath "<installation de Python et dossier du paquet>"))
(allow file-write-data (literal "/dev/null"))
(allow sysctl-read)
```

- Lecture permise : `sys.prefix`, `sys.base_prefix`, `sys.exec_prefix`, le dossier de l'interpréteur et celui du paquet, chemins réels ; écriture permise sur `/dev/null` seulement, où part la sortie d'erreur ; lecture des paramètres du système, dont l'interpréteur peut avoir besoin.
- `RLIMIT_CPU` à 120 s et `RLIMIT_CORE` à zéro, comme sous Linux.
- La mémoire n'est pas comptée parmi les manques du processus de travail : le principal la surveille. S'il ne peut pas mesurer le travail (`proc_pid_rusage` absent ou refusé), il ajoute lui-même `memoire` aux manques reçus.
- Profil refusé ou `sandbox_init` absente : manquent `reseau`, `lecture`, `ecriture`, `nouveaux_programmes`.

## Raisons

- Option A retenue : la seule qui borne réellement la mémoire sous macOS sans privilège.
- Option B écartée : elle afficherait une restriction absente ; son effet n'a pas été mesuré en T14, ADR-0035 l'ayant déjà écartée.
- Option C écartée : elle laisse le poste sans défense contre une bombe.
- Empreinte physique plutôt que mémoire résidente : c'est la mesure que macOS emploie pour arbitrer la mémoire, mémoire compressée comprise.
- Lecture de l'installation : un module peut encore importer à la demande ; ces fichiers sont publics.
- Mesuré par la CI macOS de T14 (Python 3.12 à 3.14) : depuis un module, lecture d'un fichier du dépôt, écriture, connexion TCP et exécution d'un programme sont refusées (`PermissionError`) ; un module qui remplit 3 Gio est arrêté par le principal, `memoire_depassee`.
- Écart constaté : Seatbelt laisse **créer** une socket, et refuse la connexion. Le réseau reste bloqué ; le test le vérifie sous cette forme.

## Conséquences

- L'isolation est complète sous macOS tant que Seatbelt et `proc_pid_rusage` existent ; `sandbox_init` est marquée obsolète par Apple depuis 2011, mais reste employée par les navigateurs. Sa disparition se lirait dans les manques et ferait échouer les tests d'isolation de la CI.
- Un dépassement de mémoire arrête toute l'analyse sous macOS, alors que Linux et Windows ne rendent non mené que le module en cours.
- Le principal mesure le travail tous les dixièmes de seconde pendant qu'il attend ; ailleurs, il attend sans réveil.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR de T14 : statut « Accepté » |
