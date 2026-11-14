# ADR-0157 — Versions de T24 : catalogue 0.4.0, module `image` 0.1.0, quatre modules à une nouvelle version

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T24, validée pendant la revue de la PR de T24
- **Tâche** : T24
- **Exigences liées** : NF-06, NF-07, F-26 ; ADR-0064, ADR-0085, ADR-0146, ADR-0152, ADR-0155

## Contexte

T24 ajoute huit règles au catalogue, un module, et la direction « transformation » aux manifestes de quatre modules dont le code ne change pas. Le lecteur de conteneurs partagé relève deux natures de blocs de plus, que ces modules ignorent. Restait à fixer les versions.

## Options envisagées

### Catalogue

- **A — 0.4.0, format 2 inchangé** : règles ajoutées, donc `Y` (ADR-0085, ADR-0152) ; aucun test nouveau.
- **B — 0.3.1** : réservé à un texte seul ; un constat peut changer.

### Modules dont seul le manifeste change

- **A — Version `Y` augmentée** (`exif` 0.3.0, `iptc` 0.3.0, `textepng` 0.3.0, `xmp` 0.5.0), comme en T22 (ADR-0146) : les constats permis changent.
- **B — Version inchangée** : écartée en T22 pour la même situation.

### Lecteur de conteneurs

- **A — Sans version propre** : il n'en a pas ; les observations des modules de métadonnées ne changent pas, ce que vérifient leurs tests et l'oracle exiftool.

## Décision

Option A dans les trois cas : catalogue 0.4.0 du 2026-11-14, format 2, nouvelle entrée au registre ; modules `exif` 0.3.0, `iptc` 0.3.0, `textepng` 0.3.0, `xmp` 0.5.0 ; module `image` 0.1.0. Règles : `R-EXIF-014`, `R-XMP-013`, `R-IPTC-003`, `R-TEXTEPNG-007` à la suite de leur module, `R-IMAGE-001` à `R-IMAGE-004` ; gabarits `<module>.<objet>` en mots (ADR-0146).

## Raisons

- Catalogue A : la règle de version du guide (§5) ; B la contredirait.
- Modules A : deux manifestes sous un même numéro rendraient comparables deux rapports dont les constats permis diffèrent (ADR-0112) ; B écartée pour cette raison, comme en T22.
- Lecteur A : une version des modules dit ce qu'ils observent ; celle des modules de métadonnées ne change pas, puisque leurs observations ne changent pas.

## Conséquences

- `vk --comparer` voit un écart de versions entre un rapport de T23 et un rapport de T24 sur le même fichier, ce qui est exact.
- Les tests qui citent les versions des modules les suivent (`tests/test_soumission.py`).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T24 (« Oui, les deux ») : statut « Accepté » |
