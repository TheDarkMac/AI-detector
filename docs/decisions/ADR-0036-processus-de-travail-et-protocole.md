# ADR-0036 — Processus de travail : un interpréteur neuf par fichier, échange en JSON

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : NF-01, NF-03, NF-08 ; ES-01, ES-04, ES-08, ES-15, ES-17 ; ADR-0015, ADR-0028

## Contexte

ADR-0028 impose un processus de travail par fichier et des résultats validés par schéma ; ES-04 interdit les objets sérialisés ; ES-08 impose que le processus de travail analyse le fichier que le processus principal a identifié. Il faut choisir comment créer ce processus, comment lui confier le fichier, et comment il rend ses résultats, de façon identique sur les trois systèmes (ADR-0035).

## Options envisagées

### Option A — Un interpréteur neuf par fichier

- Avantages : aucun état hérité ; même déroulé sur les trois systèmes ; échange en données simples.
- Inconvénients : coût de démarrage de l'interpréteur et des imports à chaque fichier.

### Option B — Processus modèle dupliqué (`fork`)

- Avantages : démarrage rapide, imports déjà faits.
- Inconvénients : `fork` n'existe pas sous Windows et est déconseillé sous macOS ; le processus dupliqué hérite de tout l'état du modèle.

### Option C — `multiprocessing` de la bibliothèque standard

- Avantages : le plus simple à écrire.
- Inconvénients : l'échange se fait par `pickle`, donc par objets sérialisés ; un processus compromis pourrait attaquer le processus principal au moment de la désérialisation (M-10).

## Décision

1. **Ouverture** : le processus principal ouvre le fichier en lecture seule, sans blocage, puis vérifie sur le descripteur qu'il s'agit d'un fichier régulier (ES-08, M-30). Il calcule l'empreinte (ADR-0040) par lectures à position explicite.
2. **Lancement** : pour chaque fichier, il lance `python -I -m <paquet>._travail` (mode isolé de Python : ni variables d'environnement Python, ni répertoire courant dans le chemin d'import), avec un environnement vidé, sans autre descripteur hérité que le fichier et trois tubes. Sous Windows, il place le processus dans un Job Object avant de lui envoyer quoi que ce soit.
3. **Verrouillage** : le processus de travail importe ses modules, applique ses restrictions (ADR-0035), puis envoie un premier message, l'état de l'isolation. Tant que ce message n'est pas parti, il n'a lu aucun octet du fichier : ce message est donc fiable.
4. **Configuration** : le processus principal envoie ensuite, sur l'entrée standard, le catalogue validé, les limites et les modules actifs.
5. **Analyse** : le processus de travail lit le fichier par le descripteur hérité, recalcule l'empreinte (ES-08), exécute les modules, et écrit ses résultats sur sa sortie standard en **lignes JSON**, chaque message et l'ensemble étant bornés en taille.
6. **Réception** : le processus principal lit au plus la taille permise, décode le JSON, valide chaque message par schéma (ES-04). Un message invalide, un dépassement de taille ou de délai, un arrêt anormal deviennent des analyses non menées, avec leur raison, sans contenu du fichier. La sortie d'erreur est lue, bornée et jamais recopiée au rapport ni à l'écran (ES-15).
7. **Lot** : chaque fichier a son processus ; aucun état n'est partagé ; les fichiers sont traités l'un après l'autre en V1.
8. **Bibliothèque** : l'interface publique ne propose que l'analyse par ce chemin ; les analyseurs refusent de s'exécuter hors d'un processus de travail verrouillé (ES-17).

## Raisons

- Option A retenue : elle donne le même déroulé et les mêmes garanties sur les trois systèmes, et n'échange que des données simples.
- Option B écartée : indisponible sous Windows, fragile sous macOS, et l'état hérité contredit « aucun état partagé ».
- Option C écartée : ES-04.
- Descripteur ouvert par le processus principal : le processus de travail n'a plus besoin d'ouvrir de chemin, ce qui permet de lui retirer tout accès au système de fichiers ; le fichier analysé est bien celui qui a été identifié.
- Lectures à position explicite : les deux processus partagent la position de lecture du descripteur ; lire à une position donnée évite qu'ils se gênent.

## Conséquences

- T12 réalise le lancement, le protocole et l'isolation des erreurs par module ; T11 définit les schémas des messages avec le modèle de données ; T13 l'ouverture et l'empreinte ; T14 les limites et le délai.
- Le coût de démarrage (ordre de grandeur : quelques dixièmes de seconde) est mesuré en T14 ; un lot de nombreux petits fichiers en pâtit. Un traitement en parallèle borné pourra être ajouté, sans partage d'état.
- Le schéma des messages est versionné avec le schéma du rapport (ADR-0025).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : schéma des messages et version commune avec le rapport (ADR-0054, modèle de données §8) (T11) |
| 2026-10-26 | Réalisé en T12. Précisé par ADR-0065 : `-B` ajouté à la commande (point 2), Job Object reporté à T14 (point 2), sortie d'erreur envoyée vers le néant au lieu d'être lue (point 6) ; message « module » ajouté (ADR-0062) |
