# ADR-0018 — Synthèse sans verdict et graduation fixe des indices

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §6, §8, F-80, F-81, NF-11, NF-14 ; constat A-07

## Contexte

Le §10 laisse ouverts la forme de la synthèse globale (aucune, niveaux qualitatifs, score chiffré), la graduation des indices et les règles de combinaison entre constats. L'analyse a montré que les taux d'erreur par technique ne bornent pas l'erreur du rapport : avec une vingtaine de règles à 1 % de faux positifs chacune, un fichier authentique porterait souvent au moins un indice (A-07).

## Options envisagées

### Option A — Résumé structuré sans verdict, niveau fixe par règle

- Avantages : aucune conclusion que l'outil ne peut pas justifier ; le lecteur voit d'abord les preuves ; chaque niveau d'indice s'explique par une mesure publiée.
- Inconvénients : le lecteur doit lui-même peser les indices.

### Option B — Niveaux qualitatifs globaux

- Avantages : une conclusion lisible par fichier.
- Inconvénients : suppose des règles de combinaison calibrées ; renforce le biais d'automatisation que le §8 veut mesurer.

### Option C — Score chiffré

- Avantages : lecture immédiate.
- Inconvénients : précision illusoire ; difficile à justifier sans modèle appris (ADR-0016) ; contraire à NF-14.

## Décision

- **Aucun score, aucun verdict.** Le rapport s'ouvre sur un résumé structuré : les preuves d'abord, avec l'énoncé exact de ce qu'elles établissent (ADR-0021) ; puis le nombre d'indices par direction et par niveau ; puis la couverture et les analyses non menées.
- **Graduation** : chaque règle porte dans le catalogue un niveau fixe (faible, modéré, fort), attribué d'après son taux de faux positifs mesuré sur la partie évaluation du corpus (ADR-0016). Une règle sans taux mesuré est au niveau « faible » et signalée « non évaluée ». Les bornes entre niveaux sont fixées en T17.
- **Aucune combinaison arithmétique** entre constats : le rapport peut regrouper les constats par direction, jamais en déduire une conclusion.
- **Critère d'acceptation ajouté** : taux de faux positifs **par fichier**, soit la part des fichiers authentiques dont le rapport contient au moins un indice de niveau modéré ou fort dirigé vers l'origine IA ou la retouche. Il est mesuré et publié ; sa valeur cible est fixée en T17.

## Raisons

- Option A retenue : elle applique « preuve ≠ indice » et NF-14 sans inventer de conclusion.
- Option B écartée : des règles de combinaison ne se justifient qu'avec un corpus important, et une conclusion par fichier est exactement ce que le biais d'automatisation surexploite.
- Option C écartée : un chiffre global suggère une précision que l'outil n'a pas.

## Conséquences

- T11 : le constat porte la référence à la règle et à son niveau.
- T15 : le catalogue porte le niveau de chaque règle et le taux qui le fonde.
- T16 : ordre du résumé fixé ci-dessus ; aucune formulation de conclusion globale.
- T17 : mesure du taux par fichier, bornes des niveaux.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : le constat porte sa règle et sa graduation (niveau, règle évaluée ou non), ADR-0058 (T11) |
| 2026-10-27 | Réalisé en T15 : niveau et évaluation (taux, corpus, date) portés par la règle ; sans évaluation, niveau « faible » imposé (ADR-0084) |
| 2026-10-28 | Réalisé en T16 : résumé dans l'ordre fixé, indices comptés par direction et niveau sans combinaison, aucune conclusion globale (ADR-0098) |
| 2026-10-28 | Réalisé en T17 : bornes des niveaux (1 % et 5 %) et cible par fichier (5 %) sur la borne supérieure de l'intervalle de Wilson (ADR-0101) ; taux par fichier compté sur les preuves et les indices modérés ou forts (ADR-0104) ; niveau contrôlé au chargement du catalogue (ADR-0107) |
