# ADR-0277 — Banc : plusieurs fichiers analysés à la fois, journal de reprise

- **Statut** : Accepté
- **Date** : 2026-11-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T101
- **Exigences liées** : §8 du cahier, NF-06, ES-11, ES-15, ES-22 ; ADR-0099, ADR-0100, ADR-0105, ADR-0113

## Contexte

La partie évaluation du corpus de référence compte 4 467 fichiers (ADR-0274 ; total corrigé par ERR-0014), et le banc analyse chaque fichier deux fois, l'un après l'autre (ADR-0113). Mesuré le 2026-11-26 sur trois fichiers tirés au hasard par format, sur le poste de développement peu chargé : de 1,8 à 3,5 secondes par analyse pour la plupart des formats, 19 secondes pour un PDF, 21 secondes pour un JPEG, soit environ 22 heures pour toute la partie. Le banc gardait tous ses résultats en mémoire jusqu'à la fin : une coupure du réseau, une fermeture de session ou un redémarrage, survenus deux fois pendant T100, faisaient tout recommencer.

## Options envisagées

### Option A — Plusieurs fichiers à la fois et journal de reprise (recommandée)

`--processus N` analyse jusqu'à N fichiers à la fois ; `--reprise FICHIER` note chaque résultat dès qu'il est connu et, relancé avec le même journal, ne réanalyse que les fichiers qui n'y sont pas.

- Avantages : durée divisée par le nombre de processeurs libres ; une coupure ne coûte que les analyses en cours.
- Inconvénients : du code et des tests de plus dans le banc ; des analyses simultanées se disputent le processeur, ce qui allonge chacune et la rapproche du délai de 120 secondes (`DELAI`).

### Option B — Banc tel quel

- Avantages : aucun changement.
- Inconvénients : environ 22 heures sans interruption, deux fois (ADR-0278), et tout à recommencer après une coupure.

### Option C — Plusieurs fichiers à la fois, sans reprise

- Avantages : moins de code.
- Inconvénients : une coupure fait encore tout recommencer.

## Décision

Option A :

- **Parallélisme** : un fil par fichier en cours, au plus N ; chaque fil lance les deux analyses de son fichier, chacune dans son processus de travail, comme avant. Des fils plutôt que des processus : le crochet d'audit qui refuse le réseau (ADR-0100) est propre au processus du banc et reste actif dans ses fils ; un `ProcessPoolExecutor` sous Python 3.14 démarre ses processus par un serveur joint par une socket, que ce crochet refuserait. N vaut 1 par défaut, au plus 64.
- **Ordre** : les résultats sont rendus dans l'ordre du manifeste, quel que soit l'ordre où les analyses finissent ; les mesures ne dépendent pas de l'ordre, et le rapport est le même qu'avec un seul fil (vérifié sur le corpus d'essai et par les tests).
- **Arrêt** : un fichier absent ou modifié, ou une tentative d'accès au réseau, arrête l'évaluation comme avant ; les résultats déjà obtenus sont notés au journal avant que l'erreur ne remonte, et aucune analyse nouvelle n'est lancée.
- **Journal** (`banc/reprise.py`) : une ligne JSON par fichier, écrite d'un bloc et mise sur le disque (`fsync`) avant la suivante. La première ligne décrit l'évaluation : corpus (nom, version, empreinte du manifeste), partie, version de l'outil et **empreinte de son code** (SHA-256 des fichiers du paquet installé, `__pycache__` exclu), version et empreinte du catalogue, modules mesurés et désactivés. Un journal dont l'en-tête diffère est refusé (code 2) : la version de l'outil ne change pas à chaque modification d'un dépôt de travail, l'empreinte du code, si. Une dernière ligne incomplète est retirée à la reprise ; toute autre ligne illisible fait refuser le journal.
- **Contenu du journal** : ce que les mesures emploient de chaque fichier (chemin, empreinte, états des techniques, règles, catégories, directions et niveaux des constats, motif d'un refus, nom de l'exception d'un arrêt brutal, écarts de reproduction), rien de plus ; aucun contenu de fichier ni message d'erreur (ES-15). Il reste sur le poste, à l'endroit choisi par qui lance le banc, et n'est pas publié : les taux ne viennent que du rapport écrit à la fin.

## Raisons

- Option A retenue : l'évaluation tient en une nuit, et une coupure ne la fait pas recommencer.
- Option B écartée : deux passes de 22 heures sans coupure n'étaient pas réalistes sur ce poste.
- Option C écartée : la reprise coûte peu, et une coupure était probable sur une telle durée.
- Fils plutôt que processus : voir la décision ; le travail lourd est déjà dans les processus de travail, que les fils attendent.
- Empreinte du code dans l'en-tête : sans elle, un journal commencé avant une modification de l'outil serait repris après, et mêlerait deux codes dans un même rapport.

## Conséquences

- Des analyses simultanées rapprochent chacune du délai de 120 secondes, mesuré en temps écoulé : une analyse interrompue sort de la garantie et sa technique compte comme non analysable. Le nombre d'analyses interrompues est au rapport ; N est choisi selon les processeurs libres du poste (3 sur le poste de T101, qui en a 4).
- Le code du paquet ne doit pas changer pendant une évaluation : les processus de travail le chargent à chaque analyse. Le journal ne le détecte qu'à la reprise ; pendant une passe, c'est une règle de conduite (journal de T101).
- Le guide du dossier de vérification décrit les deux options (§3).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-26 | Création |
