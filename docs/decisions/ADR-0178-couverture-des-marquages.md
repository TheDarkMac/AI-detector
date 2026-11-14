# ADR-0178 — Couverture des marquages : marquages qui pourraient se trouver dans le fichier, calculée par P1

- **Statut** : Proposé
- **Date** : 2026-11-14
- **Décideur** : assistant, proposition non posée en question pendant T31, soumise dans la PR
- **Tâche** : T31
- **Exigences liées** : F-25, NF-06 ; ADR-0059, ADR-0071, ADR-0087, ADR-0097, ADR-0176, ADR-0177

## Contexte

ADR-0176 et ADR-0177 fixent ce que la couverture liste ; il reste à dire, pour un fichier donné, quels marquages y figurent, avec quelles raisons, et qui le calcule.

## Options envisagées

### Option A — Marquages des formats des parties analysées, calcul par P1

Un marquage figure si l'une des parties analysées du fichier est dans l'un de ses formats. Il est recherché si son module a été appliqué, même en partie, à l'une de ces parties ; sinon il est non recherché, pour la raison du catalogue, ou, s'il a un module, pour la raison `technique_non_menee` (module désactivé, en erreur, analyse interrompue). Le processus principal le calcule après le processus de travail, à partir de la couverture des techniques et du catalogue.

- Avantages : chaque marquage applicable figure exactement une fois ; un module désactivé ne fait pas disparaître le marquage qu'il recherche ; un PDF ne liste pas les filigranes du son ; aucun changement du protocole du processus de travail ; même résultat à entrées égales (NF-06).
- Inconvénients : une raison de plus, constatée à l'analyse et non inscrite au catalogue.

### Option B — Tous les marquages du catalogue, quel que soit le fichier

- Inconvénients : un PDF listerait SynthID audio et Video Seal ; bruit sans information.

### Option C — Calcul dans le processus de travail

- Inconvénients : le catalogue des marquages devrait lui être transmis ; la couverture des techniques hors V1 est déjà complétée par P1 (ADR-0087).

## Décision

Option A. Les marquages sont listés dans l'ordre de leurs identifiants ; l'analyse joint ceux que cite sa couverture (nom, nature, description), comme elle joint les règles que citent ses constats (ADR-0097). La raison au rapport est l'une de cinq : `lecteur_neuronal` (lecteur public, mais réseau de neurones, ADR-0016), `lecteur_proprietaire` (aucun lecteur public), `cle_du_fournisseur` (lecteur public, clé secrète), `lecteur_a_venir` (lecteur public et déterministe, pas encore livré), `technique_non_menee`.

## Raisons

- A retenue : seule option qui reste exacte quand l'utilisateur désactive un module.
- B écartée pour le bruit ; C écartée pour la transmission inutile du catalogue.

## Conséquences

- `Couverture.marquages_non_recherches`, `Analyse.marquages` ; l'analyse vérifie que les marquages cités sont ceux du catalogue joints, une fois chacun, et que chaque raison est la leur.
- Un catalogue fourni sans `marquages.toml` donne deux listes vides, comme avant T31.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
