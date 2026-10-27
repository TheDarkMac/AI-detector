# ADR-0087 — Techniques hors V1 : une liste de l'outil, à côté des modules

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T15
- **Exigences liées** : F-25, F-82 ; A-23 ; ADR-0012, ADR-0059, ADR-0071, ADR-0086

## Contexte

ADR-0012 veut que les techniques hors de la V1 figurent au rapport comme non menées, et ADR-0059 les inscrit à la couverture sans version, avec la seule raison `hors_v1`. T12 a laissé à T15 la liste de ces techniques par format (ADR-0059, architecture §12) ; ADR-0012 dit que la matrice format × technique est tenue « dans les fiches techniques et le catalogue ».

## Options envisagées

### Option A — Données de l'outil

Un fichier TOML validé, `modules/hors_v1.toml`, à côté des modules.

- Avantages : ce que cette version ne fait pas est une propriété de l'outil ; un catalogue fourni par l'utilisateur (ADR-0086) ne peut pas l'effacer du rapport.
- Inconvénients : s'écarte de la lettre d'ADR-0012 (« et le catalogue »).

### Option B — Dans le catalogue

Une section du catalogue.

- Avantages : suit la lettre d'ADR-0012.
- Inconvénients : un catalogue fourni par l'utilisateur pourrait faire disparaître du rapport ce que l'outil ne cherche pas, ce que F-25 sert justement à dire.

## Décision

Option A.

- `src/voight_kampff/modules/hors_v1.toml`, validé par `schemas/hors_v1.schema.json` : pour chaque technique, l'identifiant que prendrait son module, la tâche, les exigences, le statut fixé par ADR-0012 (`candidate_v2` ou `sans_engagement`) et les formats du périmètre où elle s'appliquerait. Aucun identifiant n'est celui d'un module livré.
- Contenu en V1 : ELA, bruit, CFA, PRNU (T42 à T45), comparaison à des documents de référence (T54), spectrogramme, silences, ENF, réencodages audio (T60 à T63), structure, images clés, piste son, ruptures vidéo (T70 à T73), stylométrie (T82), références (T83), points de traçage (T94). N'y figurent pas : les techniques de la V1 pas encore livrées dans une version de développement, et la comparaison d'exemplaires (T93), qui porte sur plusieurs fichiers.
- Inscription au rapport, par le processus principal après le travail : une technique ne figure que si au moins une partie analysée est d'un de ses formats. Elle est alors, sans version, **non menée** pour la raison `hors_v1` sur chaque partie de ses formats, et **non applicable** sur les autres parties d'un polyglotte, puisque chaque technique figure une fois par partie analysée (ADR-0071).
- Le modèle et le schéma du rapport admettent donc une technique sans version à l'état « non applicable » ; la règle 4 d'ADR-0059 devient : « une technique sans version est hors de cette version de l'outil ; elle est non menée pour la seule raison `hors_v1`, ou non applicable ».
- Le résumé du terminal dit « hors de cette version » sur la ligne de la technique, sans répéter la non menée.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : F-25 et F-82 bornent la portée d'un résultat négatif ; cette borne ne doit dépendre que de l'outil.
- Techniques non pertinentes omises : un JPEG ne gagne rien à lire que l'ENF ou la stylométrie ne lui sont pas appliquées ; un module livré, lui, figure toujours, la matrice format × technique de l'outil restant ainsi complète (A-23).
- Non applicable plutôt que non menée sur l'autre partie d'un polyglotte : la technique ne s'y appliquerait pas même si elle était livrée.

## Conséquences

- Quand un module de cette liste est livré, la même PR le retire du fichier ; le chargement refuse sinon les deux à la fois.
- Un changement du périmètre (ADR-0012, après T105) se reporte dans ce fichier.
- La couverture d'une analyse n'est plus vide sans module livré : un PDF montre T54, T83 et T94 hors de cette version.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
