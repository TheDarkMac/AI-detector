# ERR-0001 — Exigence « F-94 » inexistante citée dans le découpage

- **Date de constat** : 2026-10-26
- **Tâche en cours** : T00
- **Document ou élément touché** : `docs/00-plan/decoupage-taches.md`, §5, remarque 6 (versions 0.1 à 0.3)
- **Nature** : analyse

## Ce qui était écrit ou fait

> **F-63** et **F-94** (documents numérisés, points de traçage) touchent la frontière « sans IA » (OCR).

## Ce qui est juste

Le cahier des charges ne contient aucune exigence F-94 : la section 5.6 s'arrête à F-91. Les points de traçage d'imprimante relèvent de **F-90**. « 94 » est le numéro de la **tâche** T94 du découpage, qui couvre cette partie de F-90.

## Comment l'erreur a été trouvée

Relecture du découpage avant son premier commit, en vérifiant chaque identifiant cité contre le cahier des charges.

## Cause

Confusion entre l'identifiant de tâche (T94) et l'identifiant d'exigence (F-xx) au moment de rédiger les remarques, les deux numérotations étant proches.

## Correction appliquée

Remarque 6 réécrite : « F-63 et F-90 pour sa partie points de traçage (tâche T94) ». Historique du découpage, version 0.4.

## Prévention

Toute citation d'exigence est vérifiée contre la liste du cahier des charges avant commit. La matrice de traçabilité prévue en T17 rendra cette vérification systématique.
