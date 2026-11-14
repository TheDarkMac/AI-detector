# ADR-0175 — Marquages au catalogue : fichier `marquages.toml`, format 3

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T31, validée pendant la revue de la PR de T31
- **Tâche** : T31
- **Exigences liées** : F-24, F-25, F-26 ; ES-09 ; ADR-0029, ADR-0038, ADR-0085, ADR-0088, ADR-0147

## Contexte

F-24 demande que les filigranes recherchés viennent d'un catalogue, F-26 que ce catalogue se mette à jour sans changer le moteur, F-25 que le rapport liste les marquages recherchés. Le rapport porte depuis T11 une liste `marquages_recherches` d'identifiants « dans le catalogue », toujours vide : le catalogue n'a pas encore de marquages (architecture, §12).

## Options envisagées

### Option A — Un fichier `marquages.toml` à la racine du catalogue, au format 3

Chaque entrée : identifiant `M-<NOM>`, nom, nature (manifeste, déclaration, filigrane), description, formats, références, date de vérification, et soit le module livré qui le recherche, soit la raison de ne pas le rechercher.

- Avantages : les marquages restent publics, versionnés, comptés dans l'empreinte et signés avec le reste du catalogue (ADR-0029) ; un marquage non recherché s'ajoute sans code ; un catalogue fourni par l'utilisateur peut en inscrire ; le numéro de format dit à une version plus ancienne de l'outil pourquoi elle refuse ce catalogue.
- Inconvénients : un format de plus à lire ; un marquage recherché exige un module, donc une version de l'outil.

### Option B — Un champ `marquages` dans le manifeste des modules

- Avantages : le module et ce qu'il recherche sont au même endroit.
- Inconvénients : le manifeste appartient à l'outil, pas au catalogue : un marquage non recherché n'a pas de module où s'inscrire, et la liste ne se met pas à jour sans nouvelle version (F-26).

### Option C — Les marquages comme des règles

- Inconvénients : une règle tire un constat d'observations ; un marquage dit ce qui est cherché, qu'il y ait un constat ou non. Les mêler brouille la phrase et la catégorie des règles.

## Décision

Option A. `marquages.toml` est facultatif et n'est admis qu'au format 3 ; le catalogue livré passe au format 3. Au chargement : schéma `marquages`, identifiants uniques, au plus 256 marquages (`MARQUAGES_MAX`), date existante, module existant qui traite chacun des formats du marquage.

## Raisons

- A retenue : seule option où un marquage non recherché s'inscrit sans code, comme l'exige ADR-0177.
- B écartée pour F-26 ; C écartée parce qu'un marquage n'est pas un constat.

## Conséquences

- Guide du catalogue (§1 à §3) et schéma `catalogue` mis à jour ; nouveau schéma `marquages`.
- `vk --regles` liste aussi les marquages, avec leur module ou leur raison.
- Une version de l'outil antérieure à T31 refuse le catalogue 0.6.0 (format inconnu), comme le prévoit ADR-0147.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T31 (« Yes, all four ») : statut « Accepté » |
