# ADR-0184 — Versions de T40 : module `image` 0.2.0, catalogue 0.7.0, R-IMAGE-004 en version 2

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T40, validée pendant la revue de la PR de T40
- **Tâche** : T40
- **Exigences liées** : NF-06, NF-07, F-26 ; ADR-0064, ADR-0085, ADR-0152, ADR-0157, ADR-0179

## Contexte

T40 ajoute des observations au module `image`, trois règles au catalogue et change le texte d'une limite de R-IMAGE-004, qui annonçait mozjpeg comme non reconnu. Le schéma du rapport et le format du catalogue ne changent pas.

## Options envisagées

### Module `image`

- **A — 0.2.0** : de nouvelles observations, donc ce que lit une règle change (ADR-0157).
- **B — 0.1.1** : réservé à une correction sans observation nouvelle.

### Catalogue

- **A — 0.7.0, format 3 inchangé** : règles ajoutées, donc `Y` (guide du catalogue, §5).
- **B — 0.6.1** : réservé à un texte seul.

### R-IMAGE-004

- **A — Version 2** : sa description de limite change ; toute modification d'une règle, texte compris, augmente sa version (§5).
- **B — Version 1** : la CI refuserait la règle modifiée sans nouvelle version (ADR-0085).

## Décision

Option A dans les trois cas : module `image` 0.2.0 ; catalogue 0.7.0 du 2026-11-14, format 3, nouvelle entrée au registre ; `R-IMAGE-004` en version 2 ; `R-IMAGE-005` à `R-IMAGE-007` en version 1. Schéma du rapport inchangé (0.6.0), les observations étant des noms libres du module (ADR-0058).

## Raisons

- Module A : deux rapports sous un même numéro auraient des observations différentes ; B écartée pour cette raison.
- Catalogue A : un constat peut changer ; B le contredirait.
- R-IMAGE-004 A : la règle de version du guide ; B est refusée par la CI.

## Conséquences

- `vk --comparer` voit un écart de versions entre un rapport de T31 et un rapport de T40 sur le même JPEG, ce qui est exact.
- Les tests qui citent la version du module la suivent (`tests/test_soumission.py`, `tests/test_cli.py`).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-15 | Validé par TheDarkMac pendant la revue de la PR de T40 (« Oui, les deux ») : statut « Accepté » |
