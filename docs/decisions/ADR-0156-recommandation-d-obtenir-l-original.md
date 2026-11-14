# ADR-0156 — Recommandation d'obtenir l'original : une phrase du résumé

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T24
- **Exigences liées** : F-06, NF-11, NF-14 ; ADR-0018, ADR-0091, ADR-0098

## Contexte

F-06 demande de dire que les indices de transfert réduisent la portée des analyses et de recommander d'obtenir l'original. Les phrases des constats sont dans les règles (ADR-0091), les textes fixes du rapport dans `textes.toml` (ADR-0098).

## Options envisagées

### Option A — Phrase du résumé

Un texte fixe, affiché une seule fois au résumé dès qu'un constat pointe vers « transformation ».

- Avantages : une recommandation, quel que soit le nombre d'indices ; vaudra aussi pour les règles de T40 et T41.
- Inconvénients : le code du résumé doit connaître la direction « transformation » ; le JSON, qui ne porte pas le résumé, ne la contient pas.

### Option B — Phrase de chaque règle

- Avantages : catalogue seul, sans code du rapport.
- Inconvénients : la recommandation est répétée à chaque constat et dépend de la rédaction de chaque règle.

### Option C — Les deux

- Inconvénients : redondant.

## Décision

Option A : clé `resume.transformation` de `textes.toml`, ajoutée par `Presentation.resume` après le compte des indices, une fois, si un constat au moins pointe vers « transformation ». Elle paraît au résumé de la sortie de `vk` et du rapport HTML.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : la même phrase à chaque constat, et une règle qui l'oublierait ne la donnerait pas.
- Option C écartée : redondante.

## Conséquences

- Le JSON n'a pas de résumé : un programme qui le lit trouve la direction de chaque constat et en tire la même conclusion.
- Le texte ne promet rien (NF-14) : il dit que les autres analyses ne voient que ce que la transformation a laissé, et invite à obtenir l'original « si vous le pouvez ».

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
