# ERR-0008 — PR #19 mergée sans titre fixé ni validation des ADR proposés : récidive d'ERR-0007

- **Date de constat** : 2026-11-12
- **Tâche en cours** : T21
- **Document ou élément touché** : commit de merge `dfd0216` de `detector` ; `docs/decisions/ADR-0117-…` à `ADR-0122-…` ; emplacements d'ADR-0115 ; réglages d'ADR-0110 ; prévention d'[ERR-0007](ERR-0007-merge-de-la-pr-18.md)
- **Nature** : exécution

## Ce qui était écrit ou fait

La PR [#19](https://github.com/TheDarkMac/AI-detector/pull/19) (T20) a été mergée le 2026-10-28 à 16:05:14 UTC, depuis le compte TheDarkMac, trois minutes et demie après la fin de sa CI verte (code 40719733948, docs 40719733735, sur `74d3e76`). Les deux règles qu'ERR-0007 rappelait n'ont pas été suivies :

- le commit de merge `dfd0216` porte le titre par défaut de GitHub, « Merge pull request #19 from TheDarkMac/tache/T20-extraction-image », au lieu de « Merge: T20 — Extraction image (#19) » (ADR-0044) ;
- ADR-0117 à ADR-0122, au statut « Proposé », sont entrés dans `detector` sans validation ni changement de statut ; les emplacements d'ADR-0115 et les réglages d'ADR-0110, que le journal de T20 soumettait à la revue, n'ont pas non plus de validation consignée.

## Ce qui est juste

- Titre du commit de merge fixé par `--subject` (ADR-0044).
- Chaque ADR « Proposé » passe à « Accepté » (ou « Abandonné ») sur validation de TheDarkMac, consignée dans la branche, avant le merge (`CONTRIBUTING.md` §3, étape 6).

## Comment l'erreur a été trouvée

Lecture de l'historique de `detector` et des statuts des ADR au début de T21, pour l'« État initial » de son journal.

## Cause

Comme pour ERR-0007, la commande de merge n'est pas connue : aucune session de l'assistant n'en garde la trace, et le titre par défaut est celui de l'interface web de GitHub comme de `gh pr merge --merge` sans `--subject`. Cause de la récidive : la prévention d'ERR-0007 n'était qu'un rappel écrit (`CONTRIBUTING.md` §3, étape 6), que rien ne vérifiait au moment du merge.

## Correction appliquée

- ADR-0117 à ADR-0122 passés à « Accepté », emplacements d'ADR-0115 et réglages d'ADR-0110 validés, sur validation de TheDarkMac au début de T21 (option recommandée par l'assistant), avec une ligne d'historique dans chacun, dans la branche `tache/T21-extraction-pdf`.
- Le commit `dfd0216` n'est pas réécrit : `detector` est protégée et son historique n'est jamais modifié (ADR-0001).

## Prévention

Contrôle automatique, validé par TheDarkMac ([ADR-0129](../decisions/ADR-0129-controle-des-adr-et-du-titre-de-merge.md)) : le job `lint-markdown`, exigé par la protection de `detector`, refuse tout ADR au statut « Proposé », ce qui empêche le merge tant que la validation n'est pas consignée ; sur un push vers `detector`, il vérifie le titre du commit de merge et échoue s'il n'est pas au format d'ADR-0044. Ce second contrôle ne peut que signaler l'erreur, le titre se choisissant au moment du merge.
