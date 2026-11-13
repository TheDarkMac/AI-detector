# ADR-0146 — Versions des modules et du catalogue de T22 ; forme des règles

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T22, à valider pendant la revue de la PR de T22
- **Tâche** : T22
- **Exigences liées** : NF-06, NF-07, F-26 ; ADR-0019, ADR-0064, ADR-0068, ADR-0085, ADR-0091, ADR-0142

## Contexte

ADR-0142 étend les directions permises des douze modules de métadonnées ; leur code ne change pas, seuls leurs manifestes. Le catalogue reçoit ses premières règles. Restait à dire ce que deviennent les versions des modules, celle du catalogue, et la forme commune des règles (identifiants, gabarits, limites), que les tâches suivantes reprendront.

## Options envisagées

### Version des modules

- **A — Version `Y` augmentée** (`0.1.0` devient `0.2.0`, `xmp` passe de `0.3.0` à `0.4.0`) : le manifeste fait partie du module ; ce qu'il permet de constater a changé. Inconvénient : une version nouvelle sans changement du code.
- **B — Version inchangée** : le code est le même ; la version du catalogue dit déjà ce qui change dans les constats. Inconvénient : deux manifestes différents sous un même numéro.

### Limite « règle non évaluée »

- **A — Absente des limites** : le rapport dit déjà, pour chaque constat, que sa règle n'est pas évaluée (ADR-0018, ADR-0098). Inconvénient : aucun.
- **B — Écrite dans chaque règle** : redit l'évaluation ; il faudrait changer le texte, donc la version, de chaque règle à sa première mesure.

## Décision

Option A dans les deux cas.

- Modules : `exif` 0.2.0, `id3` 0.2.0, `infopdf` 0.2.0, `infowav` 0.2.0, `iptc` 0.2.0, `matroska` 0.2.0, `odf` 0.2.0, `ooxml` 0.2.0, `quicktime` 0.2.0, `textepng` 0.2.0, `vorbis` 0.2.0, `xmp` 0.4.0. Le champ `regles` de leurs manifestes reste vide : il ne cite que les règles « module » (ADR-0084) ; les règles du catalogue sur leurs observations sont listées dans leur fiche, à la rubrique « Ce qui déclenche un constat ».
- Catalogue : version 0.2.0 du 2026-11-13 (`Y` : règles ajoutées, ADR-0085), description réécrite, nouvelle entrée au registre `docs/catalogue/versions.toml`. Format inchangé (1).
- Forme commune des règles :
  - identifiant `R-<MODULE>-<NNN>`, numéroté à partir de 001 dans chaque module, dans l'ordre où la règle a été écrite ;
  - gabarit `<module>.<objet>`, en mots (`xmp.source-ia-generative`, `infopdf.producteur-generateur`), jamais un numéro ;
  - phrase qui nomme le champ lu, en mots du rapport, et dit ce que le fichier déclare, jamais ce que le fichier est (NF-11, ADR-0021) ;
  - limites : d'abord la nature de déclaration (C-02, F-14), puis ce que la règle ne voit pas.
- Règles livrées dans un fichier par module (ADR-0088) ; les seize règles de nom du logiciel ont été écrites à partir d'une même table, pour garder leurs textes parallèles ; le fichier du catalogue est la seule source.

## Raisons

- Version A : un rapport cite la version de chaque technique (ADR-0023) ; deux manifestes sous un même numéro rendraient deux rapports comparables (ADR-0112) alors que les constats permis diffèrent.
- Version B écartée pour cette raison ; le coût de A est nul pour l'utilisateur.
- Limite A : la mesure d'une règle (T100) ne doit changer que son évaluation et son niveau, pas son texte.

## Conséquences

- Les tests qui citent les versions des modules les suivent (`tests/test_soumission.py`).
- Le relevé des versions d'un rapport de T21 et d'un rapport de T22 sur le même fichier diffère : `vk --comparer` y voit un écart de condition (versions, ADR-0112), ce qui est exact.
- Les tâches suivantes (T23, T25, T30) reprennent la forme des identifiants, gabarits, phrases et limites.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
