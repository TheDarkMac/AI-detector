# ADR-0196 — Versions du complément de T40 : module `image` 0.3.0, catalogue 0.9.0, règles R-IMAGE-008 à R-IMAGE-022

- **Statut** : Proposé
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant le complément de T40, à valider pendant la revue de sa PR
- **Tâche** : complément de T40
- **Exigences liées** : NF-06, NF-07, F-26 ; ADR-0064, ADR-0085, ADR-0146, ADR-0184, ADR-0201

## Contexte

Le complément ajoute la direction `authenticite` au manifeste du module `image` (ADR-0191), quinze règles au catalogue (ADR-0194, ADR-0195), et aucune observation : l'empreinte des tables existe depuis T40 (ADR-0181). Le schéma du rapport est celui de T42 (0.7.0).

## Options envisagées

### Module `image`

- **A — 0.3.0** : une direction ajoutée au manifeste change ce que les règles du catalogue peuvent constater sur ses observations ; précédent d'ADR-0146 (directions des modules de métadonnées, `Y`).
- **B — 0.2.0 inchangé** : le code du module ne change pas.

### Catalogue

- **A — 0.9.0, format 3 inchangé** : règles ajoutées, donc `Y` (guide du catalogue, §5).
- **B — 0.8.1** : réservé à un texte seul.

### Numérotation des règles

- **A — `R-IMAGE-008` à `R-IMAGE-016` pour Photoshop (niveaux 3, 5 à 12), `R-IMAGE-017` à `R-IMAGE-022` pour les marques, par ordre alphabétique (Apple, Canon, Kodak, Olympus, Panasonic, Sony)**, version 1 chacune.
- **B — Un préfixe propre (`R-TABLES-…`)** : les règles lisent une observation du module `image`, dont elles portent le préfixe depuis T24.

## Décision

Option A dans les trois cas. Schéma du rapport inchangé (0.7.0, ADR-0201). Les règles de T24 et de T40 (`R-IMAGE-001` à `R-IMAGE-007`) ne changent pas : aucune empreinte retenue n'est celle d'un encodeur qu'elles reconnaissent, ces fichiers ayant été écartés du relevé (ADR-0193).

## Raisons

- Module A : deux rapports sous un même numéro pourraient différer par les directions permises ; B écartée pour cette raison, comme pour ADR-0146.
- Catalogue A : des constats nouveaux apparaissent ; B le contredirait.
- Numérotation A : continuité des identifiants du module ; B écartée parce qu'un identifiant de règle porte le nom du module qu'elle lit.

## Conséquences

- `vk --comparer` voit un écart de versions entre un rapport de T42 et un rapport du complément sur le même JPEG, ce qui est exact.
- Les tests qui citent la version du module (`tests/test_cli.py`, `tests/test_soumission.py`) et le nombre de règles la suivent ; empreinte du catalogue 0.9.0 au registre `docs/catalogue/versions.toml`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création, statut « Proposé » |
