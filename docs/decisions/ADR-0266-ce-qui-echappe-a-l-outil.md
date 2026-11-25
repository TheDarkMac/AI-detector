# ADR-0266 — L'énoncé de la conservation nomme ce qui échappe à l'outil, sans rien promettre

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T92
- **Exigences liées** : NF-05, NF-14, NF-15, ES-15 ; ADR-0030, ADR-0262 ; menaces M-26, M-27

## Contexte

L'outil ne garde rien du fichier analysé (ES-15). Mais une analyse laisse des traces que l'outil n'écrit pas : la ligne de commande, noms de fichier compris, reste dans l'historique du shell ; ce qu'il affiche reste dans le défilement du terminal ; le système peut écrire la mémoire du processus sur le disque ; un logiciel de sauvegarde ou de synchronisation peut copier les rapports écrits. L'autorité d'horodatage garde ce qu'elle reçoit selon sa politique, que l'outil ne connaît pas. Lors d'une saisie du poste, ces traces disent ce que l'utilisateur a examiné (M-26). Un énoncé qui ne parlerait que de l'outil laisserait croire que rien ne reste.

## Options envisagées

### Option A — Les nommer, sans promesse (recommandée)

- Avantages : l'utilisateur sait ce qui reste et où le chercher ; l'énoncé ne laisse pas croire à une absence de trace qu'il ne peut garantir (NF-14).
- Inconvénients : l'énoncé est plus long ; il nomme des mécanismes que l'outil ne vérifie pas.

### Option B — L'autorité d'horodatage seulement

- Avantages : l'outil ne parle que de ce qu'il déclenche.
- Inconvénients : l'historique du shell, la trace la plus courante, n'est dit qu'à T103, hors de l'outil.

### Option C — Rien hors de l'outil

- Avantages : l'énoncé ne dit que ce que l'outil fait.
- Inconvénients : « rien n'en est gardé » serait lu comme « rien ne reste sur le poste ».

## Décision

Option A. Le dernier paragraphe de l'énoncé (`vk --conservation`) nomme l'historique du shell et le défilement du terminal, l'écriture de la mémoire sur le disque par le système (fichier d'échange, mise en veille prolongée) et la copie des rapports par d'autres logiciels (sauvegarde, synchronisation, indexation), et dit que rien de cela ne dépend de l'outil, qui ne peut ni le voir ni l'empêcher. Le paragraphe des jetons dit que l'autorité reçoit l'empreinte, l'adresse et l'heure de la demande, et les garde selon sa propre politique, que l'outil ne connaît pas. Le bloc de fin de commande et la rubrique du rapport le disent de l'autorité, quand elle a été sollicitée.

L'énoncé ne donne aucun conseil pour effacer ces traces : la manière dépend du système et du shell, et un conseil incomplet ferait croire à un effacement. Ce sera à la documentation utilisateur (T103).

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : l'historique du shell garde les noms de fichier, que l'outil masque partout ailleurs (ES-13) ; le taire laisserait la trace la plus lisible hors de l'affichage.
- Option C écartée : contraire à NF-14 par omission.

## Conséquences

- `tests/test_conservation_donnees.py` vérifie que l'énoncé nomme ce qui échappe à l'outil, et chaque option qui lit une saisie, écrit un fichier ou envoie une requête.
- T103 : dire comment limiter ces traces (historique du shell, chiffrement du disque, emplacement des rapports hors des dossiers synchronisés), système par système.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
