# ADR-0188 — Constat de double compression : indice faible vers la transformation

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T41
- **Exigences liées** : F-31, F-06, NF-14, ES-20 ; ADR-0018, ADR-0022, ADR-0155, ADR-0156

## Contexte

Une trace de double quantification dit que l'image a été enregistrée au moins deux fois en JPEG. L'analyse critique la rangeait déjà ainsi : « le fichier a été réenregistré », ce que fait toute image passée par une messagerie ou un réseau social (analyse critique, §2). Il fallait dire comment le rapport la restitue.

## Options envisagées

### Option A — Indice faible vers la transformation (recommandée)

- Avantages : même nature que les indices de transfert de T24 et T40 (ADR-0155), qui disent qu'une étape de transformation a eu lieu ; le résumé recommande alors d'obtenir l'original (ADR-0156) ; niveau « faible » tant que la règle n'est pas évaluée (ADR-0018).
- Inconvénients : la direction « transformation » ne distingue pas un simple réenregistrement d'une retouche suivie d'un enregistrement.

### Option B — Information neutre

- Avantages : aucune direction, donc aucune interprétation.
- Inconvénients : rien au résumé ; une mesure qui réduit la portée des autres analyses passerait inaperçue.

## Décision

Option A : une règle « moteur » du catalogue, `R-DOUBLEJPEG-001`, catégorie indice, direction transformation, fondement « mesure », niveau faible, non évaluée, calibrage « manuel » décrit dans la règle. Forme de la règle et seuils : ADR-0189.

## Raisons

- Retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : la trace a une direction claire (une transformation a eu lieu) ; la taire au résumé irait contre ADR-0156.
- « Retouche » écartée sans être proposée : la technique ne localise rien et la plupart des réenregistrements sont banals (NF-14, pas de promesse de détection).

## Conséquences

- La question proposait de citer dans la phrase la qualité antérieure de libjpeg quand elle est reconnue. Le langage des règles n'a pas de négation : deux règles, avec et sans qualité, donneraient deux constats pour une même trace. La qualité est donc une observation du module, au rapport à côté du constat, et non un paramètre de la phrase (ADR-0189).
- Le constat reste sous les règles de T24 et T40 qui lisent les tables (R-IMAGE-004 à 007) : un même JPEG peut porter les deux, l'un par profil, l'autre par mesure.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
