# ERR-0007 — PR #18 mergée sans titre fixé ni validation des ADR proposés

- **Date de constat** : 2026-10-28
- **Tâche en cours** : T20
- **Document ou élément touché** : commit de merge `4526ccd` de `detector` ; `docs/decisions/ADR-0112-…`, `docs/decisions/ADR-0113-…`
- **Nature** : exécution

## Ce qui était écrit ou fait

La PR [#18](https://github.com/TheDarkMac/AI-detector/pull/18) (T18) a été mergée le 2026-10-28 à 13:06:41 UTC, depuis le compte TheDarkMac, deux minutes et demie après la fin de sa CI verte (code 40692511706, docs 40692511663, sur `1755043`). Deux règles du déroulé n'ont pas été suivies :

- le commit de merge porte le titre par défaut de GitHub, « Merge pull request #18 from TheDarkMac/tache/T18-reproductibilite », au lieu de « Merge: T18 — Test de reproductibilité (#18) » (ADR-0044, `CONTRIBUTING.md` §3, étape 6) ;
- ADR-0112 et ADR-0113, au statut « Proposé » et à valider pendant la revue de la PR, sont entrés dans `detector` sans validation ni changement de statut ; les réglages d'ADR-0110, soumis à la même revue, n'ont pas non plus de validation consignée. Pour T17, la validation avait été consignée et les statuts changés avant le merge (`5f78bf1`).

## Ce qui est juste

- Titre du commit de merge fixé par `--subject` (ADR-0044).
- Chaque ADR « Proposé » d'une tâche passe à « Accepté » (ou est retiré) sur validation de TheDarkMac, consignée dans la branche, avant le merge.

## Comment l'erreur a été trouvée

Lecture de l'historique de `detector` et des statuts des ADR au début de T20, pour l'« État initial » de son journal.

## Cause

Non établie : aucune trace de la commande de merge n'est disponible dans la session de T20. Le titre par défaut est celui que donnent l'interface web de GitHub et `gh pr merge --merge` sans `--subject`. Le journal de T18 annonçait bien les ADR à valider pendant la revue, mais l'étape 6 du déroulé ne rappelait pas cette validation au moment du merge.

## Correction appliquée

- ADR-0112 et ADR-0113 passés à « Accepté » sur validation de TheDarkMac au début de T20, avec une ligne d'historique, dans la branche `tache/T20-extraction-image`.
- Les réglages d'ADR-0110 sont soumis à la revue de la PR de T20.
- Le commit `4526ccd` n'est pas réécrit : `detector` est protégée et son historique n'est jamais modifié (ADR-0001), comme pour la PR #4 (ADR-0044).

## Prévention

L'étape 6 du déroulé (`CONTRIBUTING.md` §3) rappelle désormais, avant le merge, la validation des ADR « Proposé » de la tâche, en plus du titre.
