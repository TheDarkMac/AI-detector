# ADR-0108 — Résultats identiques : le rapport entier, à la date et au nom du fichier près

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac (question posée pendant T18, recommandation suivie)
- **Tâche** : T18
- **Exigences liées** : NF-06, P-05, critère du §8 ; ES-13, ES-14 ; ADR-0023, ADR-0059, ADR-0095

## Contexte

NF-06, reformulée par ADR-0023, demande « mêmes constats » pour le même fichier, dans les mêmes conditions. Le test de T18 doit dire ce qui est comparé entre deux analyses. Deux champs changent par construction : la date de l'analyse (ES-14) et le nom du fichier, qui n'est pas son contenu.

## Options envisagées

### Option A — Tout le rapport, sauf la date et le nom

Identification (format, taille, empreinte, parties, extension), versions, isolation, couverture, observations, constats, analyses non menées, ordre compris ; et l'export JSON identique octet pour octet une fois la date neutralisée.

- Avantages : un écart d'observation ou de non menée, qui précède souvent un écart de constat, est vu ; l'ordre, que le rapport affiche, est vérifié ; l'export publié est vérifié tel qu'il est lu.
- Inconvénients : plus strict que la lettre de NF-06 ; un changement voulu de l'ordre d'affichage doit rester déterministe.

### Option B — Les constats seuls

- Avantages : lecture littérale de NF-06.
- Inconvénients : une observation ou une analyse non menée qui varierait passerait inaperçue, alors que le rapport l'affiche.

### Option C — L'export JSON octet pour octet

- Avantages : simple.
- Inconvénients : un écart se lit mal (différence de texte) ; dans un export masqué, les données masquées ne sont pas comparées.

## Décision

Option A. Ne sont pas comparés : `identification.date_analyse` et `identification.nom`. L'extension, tirée du nom, est comparée comme une condition (ADR-0112). Les données masquées dans l'un des deux exports ne sont comparées dans aucun.

## Raisons

- Option A retenue : le rapport entier est ce que l'utilisateur lit ; une différence partout ailleurs que la date et le nom est un défaut ou s'explique par une condition.
- Option B écartée : elle laisse varier ce que le rapport montre.
- Option C écartée : elle ne dit pas où est l'écart et dépend du masquage ; elle est gardée comme contrôle supplémentaire dans les tests, à côté de la comparaison champ par champ.

## Conséquences

- La comparaison est écrite une fois, dans le paquet (`voight_kampff.rapport.comparaison`, ADR-0112), et employée par les tests, le banc (ADR-0113) et `vk --comparer` (ADR-0109).
- Les tests vérifient aussi que les exports JSON et HTML de deux analyses sont identiques octet pour octet, à la date près.
- Toute future technique doit produire ses résultats dans un ordre déterministe.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
