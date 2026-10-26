# ERR-0003 — Adresse e-mail du commit de merge non anticipée

- **Date de constat** : 2026-10-26
- **Tâche en cours** : T01
- **Document ou élément touché** : `docs/decisions/ADR-0003-identite-des-commits.md`, section « Décision »
- **Nature** : décision

## Ce qui était écrit ou fait

> Les commits de merge créés par GitHub (ADR-0001) sont faits au nom du compte authentifié, TheDarkMac.

## Ce qui est juste

Le commit de merge de la PR #1 (`3b7d3a5`) porte bien le nom TheDarkMac, sans co-auteur, mais avec l'adresse `152582682+TheDarkMac@users.noreply.github.com`, et non `hei.ando14@gmail.com`. Les commits faits en local portent l'adresse prévue. L'ADR ne mentionnait pas que GitHub choisit lui-même l'adresse des commits qu'il crée.

## Comment l'erreur a été trouvée

Relecture de l'historique après le merge de T00 : `git log --format='%h %an <%ae>'`.

## Cause

L'ADR a supposé que le commit de merge reprendrait l'identité configurée en local. Un commit créé par GitHub (bouton ou API de merge) ne lit pas la configuration git du poste. Cause probable du choix de l'adresse noreply : le réglage de confidentialité de l'adresse e-mail du compte GitHub. **Non vérifié** : ce réglage n'est pas lisible par l'API utilisée.

## Correction appliquée

- ADR-0003 : précision ajoutée dans son historique, avec renvoi à cet erratum. La décision n'est pas modifiée sur le fond.
- Proposition à TheDarkMac, à valider dans la PR de T01 : **accepter l'écart**. Le nom est correct, il n'y a aucun co-auteur, et l'adresse noreply est rattachée au même compte. Les autres options sont :
  - faire les merges en local puis pousser `detector` : impossible, la protection de `detector` interdit le push direct (ADR-0001) ;
  - changer le réglage de confidentialité du compte : il rendrait l'adresse personnelle publique aussi dans les commits faits depuis l'interface web, et n'est pas du ressort de l'assistant.

## Prévention

Toute hypothèse d'un ADR sur le comportement d'un service externe est vérifiée au premier usage réel, et le résultat est noté dans le journal de la tâche suivante.
