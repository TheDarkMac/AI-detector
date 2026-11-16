# ADR-0210 — Versions d'un PDF chiffré : rien n'est déchiffré

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T50
- **Exigences liées** : F-60, F-82, ES-18 ; ADR-0126

## Contexte

ADR-0126 laissait à T50 la question du déchiffrement des révisions. Dans un PDF chiffré (§7.6), les chaînes et les flux le sont ; les tables de références croisées, les trailers, les noms, les nombres et les références ne le sont pas, ni les flux de références croisées, ni la valeur `/Contents` d'une signature. Les flux d'objets le sont : les objets qu'ils rangent ne se lisent pas.

## Options envisagées

### Option A — Rien déchiffré (recommandée)

Les sections, leurs fins, les entrées et les objets lus directement dans le fichier sont classés comme ailleurs ; les objets d'un flux d'objets sont non lus ; les dates (Info, `/M` des signatures) ne sont pas observées.

- Avantages : aucune dépendance ; même règle qu'ADR-0126.
- Inconvénients : un document chiffré récent, qui range ses objets en flux, a ses versions comptées sans leur nature.

### Option B — Déchiffrer avec le mot de passe utilisateur vide

- Avantages : couvre les documents « protégés » sans mot de passe d'ouverture.
- Inconvénients : RC4 et MD5 s'écrivent en Python, mais AES demande `cryptography` dans le processus de travail (ES-18) ; dérivation des clés (révisions 2 à 6) à écrire et à tester.

## Décision

Option A.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : dépendance exposée au fichier, comme pour ADR-0126.

## Conséquences

- `revisionspdf.chiffre` dit si le trailer désigne un dictionnaire de chiffrement ; la colonne « Date déclarée » de la chronologie est vide.
- Un objet d'un flux d'objets chiffré est de nature « non lue », et l'analyse non menée (`format_partiel`) le dit ; R-REVISIONSPDF-002 ne compte pas les versions non lues.
- La question est close pour toute la V1 : aucune tâche ne déchiffre un PDF.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création ; option choisie par TheDarkMac au début de T50 |
