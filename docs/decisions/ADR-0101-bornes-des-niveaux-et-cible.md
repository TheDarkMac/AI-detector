# ADR-0101 — Bornes des niveaux d'indice et cible du taux par fichier : 1 % et 5 %, borne de Wilson

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T17
- **Exigences liées** : §8 du cahier (seuils d'acceptation), F-80, NF-14 ; ADR-0016, ADR-0018 ; A-07, A-54

## Contexte

ADR-0018 donne à chaque règle d'indice un niveau fixe (faible, modéré, fort) d'après son taux de faux positifs mesuré sur la partie évaluation du corpus, et ajoute un critère d'acceptation : le taux de faux positifs par fichier. Les bornes entre niveaux et la valeur cible sont laissées à T17. A-54 rappelle qu'un taux mesuré sur 50 fichiers ne vaut pas un taux mesuré sur 5 000 : chaque taux doit être publié avec son effectif et un intervalle de confiance.

## Options envisagées

### Option A — 1 % et 5 %, appliqués à la borne supérieure de l'intervalle de Wilson

On compare la borne supérieure de l'intervalle de Wilson à 95 % du taux de faux positifs : « fort » jusqu'à 1 %, « modéré » jusqu'à 5 %, « faible » au-delà. Cible par fichier : borne supérieure au plus 5 % sur les authentiques.

- Avantages : l'effectif est dans le critère : sans aucun faux positif, il faut 381 fichiers pour « fort », 73 pour « modéré », 73 pour la cible ; une règle mesurée sur peu de fichiers ne peut pas monter de niveau par chance.
- Inconvénients : il faut de grands corpus pour atteindre « fort ».

### Option B — 1 % et 5 %, appliqués au taux mesuré, effectif minimal fixe

- Avantages : plus favorable aux règles mesurées sur peu de fichiers.
- Inconvénients : un effectif minimal choisi à la main (200) ne tient pas compte du nombre de faux positifs ; avec 1 faux positif sur 200, le taux vaut 0,5 % mais l'intervalle monte à 2,8 %.

### Option C — 2 % et 10 %, borne de Wilson

- Avantages : plus de règles atteignent « modéré ».
- Inconvénients : plus de faux indices au rapport ; A-07 montre qu'une vingtaine de règles à quelques pour cent suffit à marquer une part importante des fichiers authentiques.

## Décision

Option A :

- **Méthode** : intervalle de Wilson, confiance bilatérale de 95 % (z = 1,96), publié avec chaque taux et son effectif.
- **Bornes** : niveau permis « fort » si la borne supérieure est au plus 1 %, « modéré » si elle est au plus 5 %, « faible » sinon. Une règle sans évaluation reste au niveau « faible » (ADR-0018).
- **Cible par fichier** : la borne supérieure du taux de faux positifs par fichier, sur les fichiers authentiques de la partie évaluation, est au plus 5 %. Un taux non mesurable (aucun fichier authentique analysé) ne satisfait pas la cible.

## Raisons

- Option A retenue : elle publie un taux avec ce qu'on en sait réellement (A-54), et ne laisse pas un petit corpus fonder un niveau élevé.
- Option B écartée : l'effectif minimal fixe ignore le nombre de faux positifs observés.
- Option C écartée : elle aggrave le risque d'A-07, que le taux par fichier sert justement à borner.
- 1 % et 5 % : ordres de grandeur courants pour un contrôle qui doit rester rare sur des fichiers authentiques ; la même borne de 5 % sert au niveau « modéré » et à la cible par fichier, qui ne compte que les indices modérés ou forts et les preuves (ADR-0104).

## Conséquences

- Les bornes sont des constantes du paquet (`BORNE_FORT`, `BORNE_MODERE` de `_regles.py`), que le banc réemploie : l'outil refuse au chargement une règle dont le niveau dépasse ce que permet son évaluation (ADR-0107).
- Le banc signale comme écart un indice dont le niveau du catalogue dépasse ce que permet sa mesure, et une cible par fichier non atteinte ou non mesurable (ADR-0104, ADR-0105).
- Le registre des arbitrages passe « Seuils d'acceptation » à « Tranché ».
- Ces valeurs ont été fixées avant toute mesure : aucune règle ne les a influencées.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
