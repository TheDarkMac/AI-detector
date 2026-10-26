# ERR-0004 — Points de traçage d'imprimante rattachés à tort à la frontière « OCR »

- **Date de constat** : 2026-10-26
- **Tâche en cours** : T01
- **Document ou élément touché** : `docs/00-plan/decoupage-taches.md`, §5, remarque 6 (versions 0.1 à 0.4)
- **Nature** : analyse

## Ce qui était écrit ou fait

> **F-63** et **F-90** pour sa partie points de traçage (tâche T94) — documents numérisés, points de traçage — touchent la frontière « sans IA » (OCR). *(Corrigé : ERR-0001.)*

## Ce qui est juste

Seule **F-63** touche la frontière de l'OCR : c'est d'ailleurs le seul endroit où le cahier des charges la mentionne. Repérer des points de traçage d'imprimante ne demande pas de lire du texte : c'est un traitement d'image (isoler le canal jaune, chercher une grille de points, la décoder selon un motif documenté), réalisable sans modèle entraîné.

ERR-0001 avait corrigé l'identifiant (F-94 en F-90) sans réexaminer le fond de la remarque.

## Comment l'erreur a été trouvée

Analyse critique du cahier (T01) : en vérifiant, pour chaque exigence, si elle dépend d'une technique fondée sur l'IA.

## Cause

Les deux exigences portent sur des documents imprimés ou numérisés ; l'assistant les a regroupées sous la même contrainte sans vérifier la technique propre à chacune. Lors de ERR-0001, la correction s'est limitée à l'identifiant cité.

## Correction appliquée

Remarque 6 du découpage réécrite ; historique du découpage, version 0.5.

## Prévention

Corriger un erratum, c'est relire toute la phrase fautive, pas seulement l'élément signalé. L'analyse critique (`docs/01-analyse/`) indique désormais, pour chaque exigence concernée, sur quoi repose sa faisabilité « sans IA ».
