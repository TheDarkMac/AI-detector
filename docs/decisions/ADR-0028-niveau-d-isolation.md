# ADR-0028 — Niveau d'isolation : un processus restreint par fichier

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T03
- **Exigences liées** : NF-01, NF-02, NF-03, NF-08 ; constats A-16, A-53 ; menaces M-01 à M-05, M-09, M-10, M-19, M-29

## Contexte

NF-01 exige que l'analyse s'exécute « de façon isolée » sans fixer le niveau (A-53). Les bibliothèques de décodage et d'analyse de formats les plus utilisées sont écrites en C et ont un historique de failles ; la V1 lit des images, des PDF, des archives bureautiques, du XML et des structures C2PA (ASN.1, CBOR). Distribué en bibliothèque (ADR-0010), l'outil s'exécuterait par défaut dans le processus de l'appelant (A-16). Ce choix fixe l'objectif ; les mécanismes de chaque système relèvent de T04.

## Options envisagées

### Option A — Processus de travail restreint, un par fichier

- Avantages : une faille d'analyseur reste confinée à un processus sans réseau ni accès aux autres fichiers de l'utilisateur ; un fichier hostile n'affecte pas les autres fichiers d'un lot (ADR-0015) ; aucune installation supplémentaire.
- Inconvénients : les mécanismes de restriction diffèrent selon les systèmes, et certains ne permettent pas tout ; coût de démarrage d'un processus par fichier.

### Option B — Conteneur ou machine virtuelle obligatoire

- Avantages : l'isolation la plus forte.
- Inconvénients : installation lourde pour le public visé (ADR-0009) ; machine virtuelle nécessaire sous macOS et Windows ; incompatible avec un usage simple en bibliothèque.

### Option C — Processus séparé, limites de ressources seulement

- Avantages : simple et portable.
- Inconvénients : une faille dans un analyseur donne accès, avec les droits de l'utilisateur, à tous ses fichiers et au réseau : exactement ce qu'il faut protéger (B1 à B3).

## Décision

- Chaque fichier est analysé dans **un processus de travail qui lui est propre**, sans accès réseau, avec le fichier en lecture seule, sans écriture hors d'un éventuel répertoire temporaire privé, avec les limites de ressources de NF-02 et les privilèges les plus réduits que le système permet.
- Le processus principal ne lit le fichier que pour en calculer l'empreinte, sans l'interpréter ; il valide par schéma les résultats renvoyés.
- Si le système ne permet pas toutes ces restrictions, l'analyse a lieu et le rapport porte « isolation réduite », avec ce qui manque.
- La bibliothèque n'expose aucune fonction d'analyse dans le processus appelant.
- Un mode d'exécution en conteneur est documenté, en option, pour les profils exposés.

## Raisons

- Option A retenue : elle protège le poste et les sources contre la menace la plus probable (faille d'analyseur, M-01) sans imposer d'installation.
- Option B écartée : son coût d'installation écarterait une partie du public visé ; elle reste proposée en option documentée.
- Option C écartée : elle laisse sans protection les biens que NF-15 désigne.

## Conséquences

- T04 choisit, par système visé, les mécanismes de restriction et la façon de lancer le processus de travail ; il dit ce que chaque système ne permet pas.
- T12 et T14 réalisent ES-01 à ES-04 et ES-17 du [modèle de menace](../modele-de-menace/modele-de-menace.md) ; T14 fixe les valeurs des limites.
- Le rapport gagne une mention de l'isolation effective.
- Un processus de travail compromis peut encore falsifier le rapport de son propre fichier (RR-01).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : mécanismes par système fixés par ADR-0035, processus de travail par ADR-0036 (T04) |
| 2026-10-27 | Réalisé en T14 : ADR-0079 (Linux), ADR-0080 (macOS), ADR-0081 (Windows) ; valeurs des limites fixées par ADR-0077 |
