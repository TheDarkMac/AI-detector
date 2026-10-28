# ADR-0104 — Définition des mesures : par technique et catégorie, par règle, par fichier

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T17, validée pendant la revue de la PR de T17
- **Tâche** : T17
- **Exigences liées** : §8 du cahier, NF-03, NF-09 ; ADR-0016, ADR-0018, ADR-0055, ADR-0101 ; A-07, A-54, A-55

## Contexte

Le §8 demande, pour chaque technique et chaque catégorie du corpus, le taux de faux positifs, le taux de faux négatifs et la part de fichiers non analysables ; ADR-0018 y ajoute le taux de faux positifs de chaque règle, qui fixe son niveau, et le taux par fichier. Aucun de ces termes n'est défini avec la précision qu'exige un calcul : sur quels fichiers, quels constats comptent, que faire d'une technique qui ne s'applique pas.

## Options envisagées

Le point qui demande un choix est la population de chaque taux.

### Option A — Population restreinte aux fichiers où la technique a été menée

- Avantages : un taux de faux positifs ne mélange pas « faux » et « non mené » ; la part non analysable est publiée à côté.
- Inconvénients : une technique qui échoue souvent peut afficher un bon taux ; il faut lire les deux ensemble.

### Option B — Population de tous les fichiers de la catégorie

- Avantages : un seul nombre.
- Inconvénients : un fichier non analysé compte comme « sans faux positif » : la technique la plus fragile paraîtrait la plus sûre.

## Décision

Option A. Une technique est un module (architecture §7). Pour un fichier, son état est : **analysé** si elle est appliquée ou partielle sur au moins une partie du fichier ; **non analysable** si elle est seulement non menée, ou si le fichier est refusé ou l'analyse arrêtée brutalement ; **non applicable** sinon (format sans objet), et le fichier sort alors de ses mesures.

Un constat **dirigé** est une preuve ou un indice ; un constat **probant** est une preuve ou un indice de niveau modéré ou fort.

| Mesure | Population | Compté |
| --- | --- | --- |
| Non analysables (technique × catégorie) | Fichiers de la catégorie où la technique s'applique | Fichiers non analysables |
| Faux positifs (technique × catégorie) | Fichiers analysés d'origine authentique | Au moins un constat dirigé de la technique vers l'origine IA ou la retouche |
| Faux négatifs (technique × catégorie) | Fichiers analysés d'origine IA ou retouchée | Aucun constat dirigé de la technique vers cette origine |
| Confusions (technique × catégorie) | Mêmes fichiers | Génération prise pour retouche, ou l'inverse (§8 : « Retouchés ») |
| Faux positifs d'une règle de preuve ou d'indice | Vers l'origine IA, la retouche ou la transformation : fichiers de la catégorie « authentiques » où son module est analysé. Vers l'authenticité : fichiers « générés » et « retouchés » où son module est analysé | Fichiers qui portent un constat de la règle |
| Taux par fichier (ADR-0018) | Fichiers « authentiques » analysés (ni refusés ni arrêtés), et à titre d'information « transformés » d'origine authentique | Au moins un constat probant, toutes techniques confondues, vers l'origine IA ou la retouche |

Chaque taux est publié avec son effectif et l'intervalle de Wilson à 95 % (ADR-0101). Une règle d'information neutre n'a pas de taux.

**Écarts**, qui font échouer l'évaluation (code 1, ADR-0105) :

- un arrêt brutal d'une analyse (exception autre qu'un refus), sur n'importe quel fichier : critère du §8 « aucun fichier malformé ne provoque d'arrêt brutal », étendu à tout le corpus ;
- sur la partie évaluation seulement : un indice dont le niveau au catalogue dépasse le niveau permis par sa mesure (sans mesure, seul « faible » est permis) ; une preuve qui a un faux positif ; une cible par fichier non atteinte ou non mesurable.

## Raisons

- Option A retenue : le §8 publie la part non analysable à côté des taux ; la mêler aux faux positifs la cacherait.
- Option B écartée : elle récompenserait l'échec.
- Taux par technique sur tout constat dirigé, taux par fichier sur les constats probants : le premier mesure la technique, le second ce que voit le lecteur du rapport, conformément à ADR-0018. Les preuves y sont ajoutées aux indices modérés et forts : une preuve fausse sur un fichier authentique est l'erreur la plus grave.
- Population d'une règle limitée aux « authentiques » : les transformés authentiques portent légitimement des constats de transformation, et le §8 les réserve à la robustesse.
- Contrôles déterministes (A-55) : leur taux est mesuré comme les autres, mais une preuve n'a pas de niveau ; un seul faux positif est un écart, et la vérification de fond reste le test de conformité de leur technique.

## Conséquences

- Un arrêt brutal est noté par le seul nom de l'exception, jamais par son message, qui pourrait contenir des données du fichier (ES-15).
- Le banc ne propose pas de nouveau seuil : il mesure. Recalibrer est une procédure de la fiche de chaque technique, sur la partie calibrage (ADR-0016).
- Les règles « module » et « moteur » sont mesurées de la même façon ; celles d'un module désactivé (`--desactiver`) ne le sont pas.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
| 2026-10-28 | Validé par TheDarkMac pendant la revue de la PR de T17 : statut « Accepté » |
