# ADR-0155 — Nature d'un indice de transfert : indice faible vers la transformation

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (fondement précisé par l'assistant)
- **Tâche** : T24
- **Exigences liées** : F-06, F-80, F-81 ; ES-20 ; ADR-0018, ADR-0022, ADR-0055, ADR-0058, ADR-0104, ADR-0142, ADR-0149

## Contexte

ADR-0055 a ajouté la direction « transformation » pour ce que révèlent la recompression, la capture d'écran et le passage par une messagerie, sans qu'aucune règle ne la produise jusqu'ici. T23 a fait des incohérences internes des informations neutres (ADR-0149), parce qu'elles ne disent pas laquelle des causes possibles les a produites. Il fallait choisir la nature des règles d'ADR-0153.

## Options envisagées

### Option A — Indice faible, transformation

Catégorie « indice », direction « transformation », niveau « faible », non évalué.

- Avantages : le résumé compte ces constats parmi les indices, sur leur propre ligne (ADR-0055) ; F-06 demande de « signaler les indices » ; une capture d'écran ou une marque de plateforme désignent une hypothèse d'ADR-0022, la transformation banale.
- Inconvénients : les manifestes de `exif`, `xmp`, `iptc` et `textepng` doivent admettre « transformation », d'où une nouvelle version de chaque module (ADR-0146).

### Option B — Information neutre

Comme les incohérences de T23 : direction « rien de particulier ».

- Avantages : aucun manifeste ne change.
- Inconvénients : le résumé ne montre aucun indice de transformation, alors que c'est ce qui borne la portée des autres analyses.

## Décision

Option A.

- Chaque règle de T24 est un indice, direction `transformation`, niveau `faible`, sans évaluation ; elle n'entre pas dans le taux de faux positifs par fichier, qui ne compte que les indices modérés et forts (ADR-0104).
- Fondement, précision de l'assistant : `declaration` pour une signature lue dans un champ de métadonnées (C-02 : quiconque peut l'écrire) ; `verification_deterministe` pour une règle du module `image`, qui lit la structure du fichier comme les règles d'absence (ADR-0151).
- Limites : d'abord la nature de déclaration ou ce que la règle ne mesure pas, puis ce qu'elle ne voit pas, enfin qu'une transformation ne dit rien de ce qu'était le fichier avant.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle tairait ce que F-06 demande de signaler.
- Fondement « mesure » écarté pour le module `image` : aucune grandeur n'est estimée, les dimensions et les tables sont lues telles qu'écrites.

## Conséquences

- Un fichier passé par une messagerie peut porter, à la fois, des informations neutres d'absence (T23) et des indices faibles de transformation (T24) : les premières disent qu'il manque quelque chose, les seconds où cela mène.
- La mesure sur le corpus (T100), catégorie « transformés » du §8, pourra porter une règle au niveau « modéré » ou « fort ».

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
