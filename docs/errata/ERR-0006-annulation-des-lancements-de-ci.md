# ERR-0006 — La CI du code annulait ses propres lancements sur `detector`

- **Date de constat** : 2026-10-26
- **Tâche en cours** : après T10 (avant T11), pendant le merge de la PR #7
- **Document ou élément touché** : `.github/workflows/code.yml`, bloc `concurrency`
- **Nature** : exécution

## Ce qui était écrit ou fait

```yaml
concurrency:
  group: code-${{ github.ref }}
  cancel-in-progress: true
```

Sur une même référence, tout nouveau lancement du workflow `code` annulait celui en cours, et GitHub annule de toute façon un lancement en attente quand un plus récent arrive dans le même groupe. Ce comportement est voulu pour une PR, inutile et nuisible sur `detector` : chaque commit de `detector` doit avoir sa CI menée à terme, et le lancement du lundi (ADR-0051, ADR-0052) peut tomber pendant un push.

Constaté le 2026-10-26 :

| Lancement | Commit | Événement | Issue |
| --- | --- | --- | --- |
| 40327564171 | `3abfa71` (merge de T10) | push | Annulé par le lancement suivant |
| 40328970897 | `3abfa71` | lancement à la demande (vérification d'ERR-0005) | Annulé par le merge de la PR #7 |
| 40330138384 | `bdc445a` (merge de la PR #7) | push | Réussi |

Le commit `3abfa71` n'a donc aucune CI menée à terme sur `detector`. Le code de ce commit avait été vérifié dans la PR #6, sur le même contenu, mais pas la branche après merge.

## Ce qui est juste

```yaml
concurrency:
  group: code-${{ github.event_name == 'pull_request' && github.ref || github.run_id }}
  cancel-in-progress: true
```

- Pour une PR, le groupe est la référence de la PR : un nouveau commit annule le lancement précédent, dont le résultat ne sert plus.
- Pour tout autre événement (push sur `detector`, lundi, lancement à la demande), le groupe est l'identifiant du lancement, unique : rien n'est annulé ni mis en attente.

Option écartée : garder le groupe par référence et ne passer que `cancel-in-progress` à `false` hors PR. Un lancement en cours ne serait plus annulé, mais GitHub annulerait encore un lancement en attente dès qu'un troisième arrive dans le groupe.

## Comment l'erreur a été trouvée

Après le merge de la PR #7, relecture des lancements du workflow `code` sur `detector`, pour vérifier le lancement à la demande d'ERR-0005 : deux lancements sur trois étaient annulés.

## Cause

Le bloc `concurrency` a été écrit en T10 en pensant aux seules PR, sans tenir compte des lancements sur `detector`, que T10 ajoutait en même temps (push, planification, lancement à la demande). Les deux merges et le lancement manuel faits à quelques minutes d'intervalle ont révélé le problème.

## Correction appliquée

- `.github/workflows/code.yml` : bloc `concurrency` remplacé, avec un commentaire qui renvoie à cet erratum.
- ADR-0051 n'est pas touché : il ne fixait rien sur la concurrence. Renvoi ajouté à son historique.
- Le commit `3abfa71` n'est pas revérifié à part : `bdc445a` le contient, et sa CI a réussi.

## Prévention

Un workflow déclenché par plusieurs événements est relu événement par événement : ce qu'il fait sur une PR, sur un push, en planification et à la demande. La correction est constatée sur `detector` après le merge de ce correctif, et consignée au journal de T11.
