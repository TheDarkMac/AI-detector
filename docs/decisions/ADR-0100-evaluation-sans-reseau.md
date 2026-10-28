# ADR-0100 — Évaluation sans réseau : espace de noms réseau vide et crochet d'audit

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T17
- **Exigences liées** : ES-11, NF-16 ; M-19 ; A-52 ; ADR-0083, ADR-0099

## Contexte

ES-11 : « Le banc d'évaluation exécute l'analyse sans réseau et échoue à toute tentative de connexion. » Il répond à M-19, une requête non inventoriée introduite par une dépendance (télémétrie, schéma ou police téléchargés). Le processus de travail refuse déjà lui-même le réseau, sous Linux et macOS (ADR-0079, ADR-0080), et cet effet est vérifié depuis un module (ADR-0083). Restent le processus principal, qu'aucune restriction ne couvre, et Windows, où le réseau n'est pas bloqué (ADR-0081).

## Options envisagées

### Option A — Espace de noms réseau vide et crochet d'audit

Le banc refuse de démarrer s'il voit une interface réseau autre que la boucle locale ; on le lance sous `unshare -rn`, qui le place, avec tous les processus qu'il lance, dans un espace de noms réseau sans interface utilisable. Pendant l'évaluation, un crochet d'audit de Python refuse et note toute création de socket ou résolution de nom dans le processus du banc.

- Avantages : aucun processus, processus de travail compris, ne peut joindre le réseau, quelle que soit la bibliothèque, Python ou C ; une tentative du processus principal est en plus nommée et fait échouer le banc.
- Inconvénients : banc limité à Linux ; il faut que le système permette les espaces de noms sans privilège.

### Option B — Crochet d'audit seul

- Avantages : portable sur les trois systèmes.
- Inconvénients : ne voit ni le processus de travail ni le code C ; sous Windows, le processus de travail garde le réseau.

### Option C — Espace de noms seul

- Avantages : barrière complète, sans code dans le banc.
- Inconvénients : une tentative échoue (« réseau injoignable ») sans être signalée ; une bibliothèque qui l'avale passe inaperçue.

## Décision

Option A :

1. Avant tout, le banc lit `/proc/self/net/dev`, propre à l'espace de noms réseau du processus (`/sys/class/net` montre celui qui a monté `/sys`, et ne convient pas), sans ouvrir de socket. Une interface autre que `lo`, une liste illisible ou un système autre que Linux : refus, code 2, rien n'est analysé ni écrit.
2. Pendant l'analyse du corpus, un crochet d'audit refuse les événements `socket.__new__`, `socket.bind`, `socket.connect`, `socket.getaddrinfo`, `socket.gethostbyaddr`, `socket.gethostbyname`, `socket.getnameinfo`, `socket.sendmsg` et `socket.sendto`, et les note. Une seule tentative, même avalée par la bibliothèque qui l'a faite : code 3, aucun rapport écrit.
3. Il n'existe aucune option pour passer outre.

## Raisons

- Option A retenue : elle couvre aussi le processus de travail sous tous les systèmes d'évaluation et le code C, ce que ni B ni les restrictions de T14 ne font seules, et elle rend la faute visible.
- Option B écartée : elle laisserait le réseau au processus de travail sous Windows et aux bibliothèques C.
- Option C écartée : une requête non inventoriée doit être une faute, pas un échec silencieux.
- Linux seulement : le banc tourne sur la CI Linux et sur un poste de développement ; il ne mesure pas l'isolation de chaque système, que vérifient les tests d'isolation (ADR-0083).

## Conséquences

- La CI Linux autorise les espaces de noms sans privilège (`kernel.apparmor_restrict_unprivileged_userns=0`) dans les jobs `tests` et `paquet`. Sur la CI Linux, le test du banc complet échoue au lieu d'être sauté si `unshare -rn` manque.
- Le crochet ne se retire pas : il est installé une fois et n'agit que pendant l'évaluation. Python l'exécute sans traçage, si bien que coverage ne peut pas mesurer ses trois lignes : elles sont exclues de la mesure, et leur effet est testé.
- Une tentative du processus de travail sous Linux est refusée par seccomp (création de socket) avant d'atteindre l'espace de noms : elle rend le module en erreur, donc l'analyse non menée, ce que le rapport d'évaluation compte.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
