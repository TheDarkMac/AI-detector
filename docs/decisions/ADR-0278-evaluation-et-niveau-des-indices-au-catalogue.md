# ADR-0278 — Évaluation et niveau permis inscrits au catalogue, puis seconde passe

- **Statut** : Accepté
- **Date** : 2026-11-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; commande d'inscription précisée par l'assistant
- **Tâche** : T101
- **Exigences liées** : §8 du cahier, F-80, NF-07, NF-14 ; ADR-0018, ADR-0085, ADR-0101, ADR-0104, ADR-0107 ; A-54

## Contexte

Avant T101, les 63 indices du catalogue 0.20.1 sont tous au niveau « faible », et aucun n'a d'évaluation : faute de corpus, aucun taux n'avait été mesuré. ADR-0018 fixe le niveau d'un indice d'après son taux de faux positifs mesuré sur la partie évaluation, ADR-0101 par la borne supérieure de Wilson de ce taux, et ADR-0107 fait porter au catalogue le taux, l'effectif et la borne. Le taux par fichier (ADR-0104) ne compte que les preuves et les indices modérés ou forts : il dépend donc des niveaux du catalogue, et un taux par fichier publié doit avoir été mesuré avec le catalogue livré.

## Options envisagées

### Option A — Évaluation et niveau permis inscrits, puis seconde passe (recommandée)

Après la première passe (catalogue 0.20.1), chaque indice mesuré reçoit son évaluation et le niveau que permet sa borne ; le banc évalue ensuite à nouveau la partie évaluation avec ce catalogue.

- Avantages : le catalogue livré applique ADR-0018 ; le taux par fichier publié est celui du catalogue livré ; la seconde passe vérifie qu'aucun niveau ne dépasse sa mesure (guide du catalogue, §5).
- Inconvénients : deux passes ; des indices montent de niveau, ce qui change ce que lit l'utilisateur du rapport.

### Option B — Évaluation inscrite, niveaux inchangés

- Avantages : une seule passe ; le rapport de l'outil cite le taux de chaque indice.
- Inconvénients : ADR-0018 n'est pas appliqué ; le taux par fichier publié ne compterait que les preuves.

### Option C — Catalogue inchangé

- Avantages : T101 se limite aux rapports.
- Inconvénients : les taux mesurés restent hors de l'outil, qui continue d'annoncer ses indices comme non évalués.

## Décision

Option A, par une commande du banc plutôt qu'une recopie à la main :

- `python -m banc.inscription EVALUATION.json [--catalogue DOSSIER]` lit un rapport **publiable** (partie évaluation du corpus de référence, ADR-0105) écrit avec le catalogue même qu'il modifie (même empreinte, catalogue non fourni par l'utilisateur) ;
- pour chaque indice dont la population (ADR-0104) compte au moins un fichier : la table `[regle.evaluation]` est écrite ou remplacée (taux, effectif, borne supérieure, corpus `reference-1.0.0`, date du rapport), le niveau devient le niveau permis par la borne (« fort » jusqu'à 1 %, « modéré » jusqu'à 5 %, « faible » au-delà), et la version de la règle augmente de un, que le niveau change ou non ;
- une preuve, une information neutre ou un indice sans effectif ne changent pas ;
- les fichiers sont modifiés ligne à ligne, mise en forme et commentaires gardés, dans une copie du catalogue rechargée et validée par l'outil avant que les fichiers modifiés ne soient recopiés : une inscription refusée ne change rien ; un même rapport ne peut pas être inscrit deux fois, la première inscription changeant l'empreinte ;
- l'en-tête du catalogue (version Y, date), le registre `versions.toml` et l'empreinte sont mis à jour à la main, comme pour toute version (guide du catalogue, §5) ;
- la seconde passe évalue la partie évaluation avec le catalogue ainsi obtenu ; c'est elle que citent les fiches.

## Raisons

- Option A retenue : elle applique la règle décidée avant toute mesure (ADR-0018, ADR-0101), et publie un taux par fichier qui correspond à l'outil livré.
- Option B écartée : elle garderait « faible » des indices que la mesure permet de dire plus sûrs, ce qu'ADR-0018 voulait éviter.
- Option C écartée : un taux mesuré mais absent du catalogue n'atteint pas l'utilisateur du rapport.
- Commande plutôt que recopie : 63 règles, trois nombres chacune ; la recopie à la main est la source d'erreur que la commande supprime, et la vérification de l'outil au chargement (ADR-0107) s'applique au résultat.
- Version augmentée même sans changement de niveau : l'évaluation fait partie de la règle (guide du catalogue, §5, point 1).

## Conséquences

- Le niveau d'un indice monte ou reste « faible » selon sa seule mesure ; aucun seuil n'est réglé sur la partie évaluation (M-33, ADR-0280).
- Les constats de la seconde passe sont ceux de la première, niveaux mis à part : les niveaux ne changent ni les observations ni les règles qui se déclenchent. Ses taux par technique et par règle doivent être identiques ; seul le taux par fichier peut changer.
- Une nouvelle version du corpus, ou un changement de règle, demande une nouvelle évaluation et une nouvelle inscription.
- Le banc ne contrôle plus le niveau d'un indice que sur un corpus de référence : sur le corpus d'essai, de neuf fichiers, aucune mesure ne permet plus que « faible », et chaque indice « fort » du catalogue livré y serait un écart. Une preuve fautive reste un écart sur tout corpus. Précisé par l'assistant pendant T101, quand la suite des tests a montré ces écarts sur le corpus d'essai (`mesurer(…, reference=…)`, journal de T101).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-26 | Création |
