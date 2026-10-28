# ADR-0107 — Évaluation d'une règle : effectif et borne supérieure au catalogue, niveau contrôlé

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T17, validée pendant la revue de la PR de T17
- **Tâche** : T17
- **Exigences liées** : F-80, NF-07, NF-14 ; ADR-0018, ADR-0084, ADR-0085, ADR-0101 ; A-54

## Contexte

Depuis T15, l'évaluation d'une règle au catalogue porte un taux de faux positifs, la version du corpus et une date (ADR-0084). A-54 demande de publier chaque taux avec son effectif et un intervalle ; ADR-0101 fonde le niveau sur la borne supérieure de cet intervalle. Le catalogue ne peut donc pas en rester au seul taux, et rien n'empêchait jusqu'ici une règle de déclarer un niveau que son taux ne permet pas.

## Options envisagées

### Option A — `effectif` et `borne_superieure` obligatoires, niveau contrôlé au chargement

- Avantages : le rapport montre le taux avec ce qu'on en sait ; l'outil refuse un catalogue dont un niveau est usurpé, livré ou fourni par l'utilisateur.
- Inconvénients : deux champs de plus ; les bornes deviennent des constantes du paquet.

### Option B — Champs facultatifs

- Avantages : aucune contrainte nouvelle.
- Inconvénients : un taux sans effectif resterait possible, contrairement à A-54.

### Option C — Banc seul gardien du niveau

- Avantages : le paquet ne connaît pas les bornes.
- Inconvénients : un catalogue fourni par l'utilisateur (ADR-0086), qui ne passe pas par le banc, pourrait déclarer « fort » une règle à 4 %.

## Décision

Option A :

- `evaluation` exige `taux_faux_positifs`, `effectif` (entier, au moins 1), `borne_superieure` (borne supérieure de l'intervalle de Wilson à 95 %), `corpus` et `date` ; le schéma `regles` et la classe `Evaluation` le vérifient, avec 0 ≤ taux ≤ borne ≤ 1.
- Une règle dont le niveau dépasse celui que permet sa borne (`niveau_permis`, ADR-0101) est refusée au chargement.
- Le rapport affiche : « taux de faux positifs mesuré : 0.2 % sur 1 500 fichiers, au plus 0.586 % avec une confiance de 95 % (corpus …, date) ».
- Le `format` du catalogue reste 1 : aucune règle n'a encore d'évaluation, aucune version publiée de l'outil n'a lu de règle (même raisonnement qu'ADR-0091).

## Raisons

- Option A retenue : la règle d'ADR-0101 est tenue par l'outil lui-même, pour tout catalogue.
- Option B écartée : contraire à A-54.
- Option C écartée : le catalogue fourni par l'utilisateur y échapperait.

## Conséquences

- Écart avec ADR-0084, qui listait l'évaluation sans effectif ni borne : précisé par cet ADR.
- Le guide du catalogue décrit les deux champs ; le banc donne les trois valeurs à recopier (taux, effectif, borne) pour chaque règle mesurée (ADR-0104, ADR-0105).
- Le texte « evaluee » de `rapport/textes.toml`, validé en T16, change pour citer l'effectif et la borne.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
| 2026-10-28 | Validé par TheDarkMac pendant la revue de la PR de T17 : statut « Accepté » |
