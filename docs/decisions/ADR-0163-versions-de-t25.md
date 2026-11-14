# ADR-0163 — Versions de T25 : schéma 0.4.0, douze modules à une nouvelle version, catalogue inchangé

- **Statut** : Proposé
- **Date** : 2026-11-14
- **Décideur** : assistant, proposition non posée en question pendant T25, à valider pendant la revue de la PR de T25
- **Tâche** : T25
- **Exigences liées** : NF-06, NF-07 ; ADR-0050, ADR-0054, ADR-0085, ADR-0112, ADR-0146, ADR-0157, ADR-0159, ADR-0160

## Contexte

T25 ajoute deux catégories identifiantes au modèle (ADR-0159) et change le marquage des douze modules de métadonnées (ADR-0160, ADR-0161). Aucune règle du catalogue ne change. Restait à fixer les versions.

## Options envisagées

### Schéma

- **A — 0.4.0** : l'énumération des catégories s'élargit, un rapport nouveau n'est pas valide sous 0.3.0 ; version commune au modèle, au rapport et aux messages (ADR-0054).
- **B — 0.3.1** : réservé à un changement qui ne change pas ce qui est valide.

### Modules dont le marquage change

- **A — Version `Y` augmentée** : `exif` 0.4.0, `xmp` 0.6.0, `iptc` 0.4.0, `textepng` 0.4.0, `infopdf` 0.3.0, `id3` 0.3.0, `infowav` 0.3.0, `vorbis` 0.3.0, `quicktime` 0.3.0, `matroska` 0.3.0, `ooxml` 0.3.0, `odf` 0.3.0 ; `image` inchangé (0.1.0).
- **B — Version inchangée** : les noms et les valeurs observés ne changent pas.

### Catalogue

- **A — Inchangé (0.4.0)** : aucune règle, aucun texte de règle ne change.

## Décision

Option A dans les trois cas. Les manifestes des douze modules citent aussi F-90 parmi leurs exigences.

## Raisons

- Schéma A : ce qui est valide change ; B le cacherait.
- Modules A : la catégorie d'une observation fait partie de son résultat (le masquage en dépend) ; deux marquages sous un même numéro rendraient comparables deux rapports différents (ADR-0112), raison déjà retenue par ADR-0146 et ADR-0157. B écartée pour cette raison.
- Catalogue A : la règle de version du guide (§5) ne s'applique qu'à un changement du catalogue.

## Conséquences

- `vk --comparer` refuse un rapport de schéma 0.3.0 et voit un écart de versions entre un rapport de T24 et un rapport de T25 sur le même fichier, ce qui est exact.
- Les tests qui citent les versions des modules les suivent (`tests/test_soumission.py`, `tests/test_cli.py`).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
