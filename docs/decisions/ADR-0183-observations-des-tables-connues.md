# ADR-0183 — Observations des tables connues : une paire par famille, premier encodeur reconnu

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T40, validée pendant la revue de la PR de T40
- **Tâche** : T40
- **Exigences liées** : F-30, NF-06 ; ADR-0058, ADR-0154, ADR-0180, ADR-0181

## Contexte

ADR-0180 retient trois familles de plus que libjpeg à une même qualité. Restait à dire sous quels noms le module les observe, ce qu'il fait quand une table est écrite par plusieurs familles, et quels réglages de chaque famille il reconnaît.

## Options envisagées

### Noms des observations

- **A — Des observations par famille** : `image.jpeg.qualite_ijg` inchangée ; `image.jpeg.qualite_ijg_luminance` et `image.jpeg.qualite_ijg_chrominance` ; `image.jpeg.jeu_mozjpeg` et `image.jpeg.qualite_mozjpeg` ; `image.jpeg.qscale_ffmpeg`. Avantages : R-IMAGE-004 et ses rapports antérieurs ne changent pas ; chaque règle lit des nombres, avec leurs paramètres. Inconvénient : six noms.
- **B — Deux observations génériques** (`image.jpeg.encodeur` en texte, `image.jpeg.qualite` en nombre). Avantage : deux noms. Inconvénients : le qscale de ffmpeg n'est pas une qualité ; deux qualités ne tiennent pas dans une valeur ; R-IMAGE-004 changerait d'observation.

### Table écrite par plusieurs familles

- **A — Premier encodeur reconnu, dans un ordre fixé** : libjpeg, libjpeg à deux qualités, mozjpeg, ffmpeg ; seul le premier est observé. Avantage : au plus un encodeur, donc au plus une des règles R-IMAGE-004 à R-IMAGE-007 ; le comportement de T24 ne change pas. Inconvénient : une table dégénérée est attribuée à libjpeg alors que mozjpeg l'écrit aussi.
- **B — Tous les encodeurs reconnus**. Inconvénient : deux constats pour une même table, et deux qualités à choisir pour la phrase.

### Réglages reconnus

- mozjpeg : jeux 2 à 8 seulement ; le jeu 0 est l'annexe K (libjpeg) ; le jeu 1, plat, donne la même table à plusieurs qualités (jusqu'à cinq), donc aucune qualité unique ; luminance et chrominance du même jeu à la même qualité ; qualités entières.
- libjpeg à deux qualités : tables 0 et 1 seulement, à deux qualités différentes, la qualité de la chrominance unique ; en huit bits, les qualités 1 à 3 de la chrominance donnent la même table (toutes ses valeurs à 255), qui ne donne donc pas de seconde qualité.
- ffmpeg : qscale de 1 à 31 (`qmax` par défaut), coefficient continu à 8 (précision `dc` par défaut), une table ou deux tables égales, de huit bits.
- Une table qu'écrivent deux couples de la même famille n'est attribuée à aucun.

## Décision

Option A pour les noms et pour l'ordre ; les réglages ci-dessus. Chaque qualité ou qscale reconnu est unique dans sa famille, ce que vérifient les tests (`tests/test_tables_connues.py`).

## Raisons

- Noms par famille : une observation garde le sens qu'elle a dans les rapports déjà produits (NF-06, `vk --comparer`) ; B mêlerait des grandeurs différentes sous un nom.
- Premier reconnu : une table dégénérée ne désigne aucun encodeur en particulier ; l'attribuer au premier essayé garde le résultat de T24, et les limites de la fiche le disent. B donnerait deux indices pour un seul fait.
- Réglages : seuls des réglages dont la table est unique donnent une observation déterministe (ADR-0154) ; les autres sont dans les limites des règles et de la fiche.

## Conséquences

- Un rapport de T24 et un rapport de T40 sur le même fichier ont la même `image.jpeg.qualite_ijg` ; le second a en plus l'empreinte des tables, et l'une des nouvelles observations si l'encodeur est reconnu.
- Un encodeur ajouté plus tard prend sa place dans l'ordre ; s'il écrit une table déjà attribuée, il ne la reçoit pas sans nouvelle décision.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-15 | Validé par TheDarkMac pendant la revue de la PR de T40 (« Oui, les deux ») : statut « Accepté » |
