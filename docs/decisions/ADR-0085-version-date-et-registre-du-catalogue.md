# ADR-0085 — Version, date et registre du catalogue

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T15
- **Exigences liées** : NF-06, NF-07, F-26 ; ES-09 ; M-11 ; ADR-0016, ADR-0023, ADR-0029, ADR-0041, ADR-0068

## Contexte

NF-07 exige que chaque version du catalogue soit « datée, versionnée et consultable ». ADR-0029 met au rapport sa version et son empreinte, et publie les empreintes des versions avec elles. ADR-0016 veut qu'un changement de seuil donne une nouvelle version. Une règle est citée par un constat avec sa propre version (A-47, ADR-0058). Il fallait choisir la numérotation, et un moyen de garantir qu'un contenu modifié ne garde pas un numéro déjà employé.

## Options envisagées

### Option A — Version propre au catalogue, registre vérifié

Numéro `X.Y.Z` et date d'édition dans l'en-tête du catalogue ; chaque règle a sa version ; un registre versionné (version, date, empreinte) est vérifié par les tests et la CI.

- Avantages : une correction de règle se voit dans le numéro du catalogue, indépendamment de l'outil ; un contenu modifié sans nouvelle version fait échouer la CI.
- Inconvénients : un second numéro à tenir, et une entrée de registre à écrire à chaque changement.

### Option B — Version de l'outil

Le catalogue prend la version et la date de publication de l'outil.

- Avantages : un seul numéro.
- Inconvénients : une version de développement porte des catalogues différents sous le même numéro ; le numéro ne dit pas si le catalogue a changé entre deux versions de l'outil ; un catalogue fourni par l'utilisateur n'en a pas.

### Option C — Version égale à la date

Numéro de la forme `2026.10.27`.

- Avantages : lisible.
- Inconvénients : ne dit pas si un changement peut modifier les constats ; deux éditions le même jour se distinguent mal.

## Décision

Option A.

- L'en-tête `catalogue.toml` porte `format` (format du catalogue que l'outil sait lire, 1 en V1), `version` (`X.Y.Z`), `date` (`AAAA-MM-JJ`, date d'édition de cette version) et `description`. Version et date sont celles du rapport (`versions.catalogue`), avec l'empreinte (ADR-0088).
- Sens du numéro : `X` augmente avec le format du catalogue, qui exige un outil capable de le lire ; `Y` pour tout changement qui peut modifier un constat (règle ajoutée, retirée, condition, seuil, liste, catégorie, direction, fondement, niveau, évaluation, gabarit, paramètres) ; `Z` pour un changement de texte seul (titre, description, limites, procédure). Une version qui commence à `0.` n'est pas encore celle d'une version stable de l'outil.
- Chaque règle a une version entière, qui augmente à **chaque** changement de la règle, texte compris ; un constat cite cette version.
- Registre `docs/catalogue/versions.toml` : une entrée par version (version, date, empreinte), dans l'ordre. Sa dernière entrée décrit le catalogue livré ; une entrée présente sur `detector` ne change plus.
- Vérifications :
  - les tests (`tests/test_catalogue.py`) : dernière entrée égale au catalogue des sources ; versions croissantes sans doublon, dates dans l'ordre, empreintes distinctes ;
  - la CI (`qualite`, `.github/scripts/catalogue.py base`) : les entrées du registre de la branche cible sont toujours là, à l'identique ; une règle présente sur la branche cible sous une version garde, à cette version, le même contenu ; sa version ne diminue jamais ;
  - la CI (`paquet`) : le catalogue du wheel, recalculé sans installer le paquet, est la dernière entrée du registre ; `vk --regles` affiche la même empreinte ;
  - la publication : même contrôle, et version, date et empreinte jointes à la release (`CATALOGUE.txt`, ADR-0041).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : le numéro de l'outil ne suffit pas à dire quel catalogue a produit un constat, ce que veulent NF-06 et NF-07.
- Option C écartée : un numéro qui ne dit pas la portée d'un changement n'aide pas à comparer deux rapports.
- Registre dans `docs/` plutôt que dans le catalogue : l'empreinte d'un catalogue ne peut pas figurer dans les fichiers qu'elle couvre.

## Conséquences

- Toute modification d'un fichier du catalogue demande, dans la même PR : nouvelle version et date dans l'en-tête, version augmentée des règles touchées, nouvelle entrée au registre (procédure : `docs/catalogue/README.md`).
- Deux rapports qui portent la même version de catalogue ont été produits avec les mêmes règles, à condition que le catalogue ne soit pas fourni par l'utilisateur (ADR-0086) : l'empreinte le confirme.
- Le catalogue initial est la version 0.1.0 du 2026-10-27, sans règle : aucun module n'est encore livré.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
