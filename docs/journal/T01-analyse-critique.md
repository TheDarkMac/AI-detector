# T01 — Analyse critique du cahier des charges

- **Branche** : `tache/T01-analyse-critique`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : toutes (lecture critique du cahier v0.1)
- **Décisions** : aucune (T01 ne tranche rien ; les arbitrages relèvent de T02)
- **Errata** : ERR-0003, ERR-0004

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : relever les ambiguïtés, les incohérences et les dépendances cachées du cahier des charges, en développant les remarques du §5 du découpage. Livrable : `docs/01-analyse/`.

## État initial

- PR [#1](https://github.com/TheDarkMac/AI-detector/pull/1) (T00) mergée dans `detector` le 2026-10-26 à 05:47 UTC, commit de merge `3b7d3a5`. Vérifications vertes : `lint-markdown`, `fichiers-interdits`.
- Le commit de merge créé par GitHub porte l'adresse `152582682+TheDarkMac@users.noreply.github.com`, et non l'adresse prévue par ADR-0003 → ERR-0003.
- Une vérification **CodeRabbit** apparaît sur la PR (statut « success », revues désactivées pour la branche de base). C'est une application GitHub installée sur le compte, non configurée par le projet ; elle n'est pas une vérification requise de `detector`.
- `detector` à jour avec `origin/detector`, arbre de travail propre.

## Déroulé

1. Branche `tache/T01-analyse-critique` créée depuis `detector` à jour.
2. Relecture du cahier, du découpage, des errata et du journal de T00. Empreinte du cahier recalculée : identique à celle de T00 (`702b468f…dafc`), le document analysé est bien celui qui a été versionné.
3. Choix d'une grille de lecture (six critères) et d'une échelle de gravité (bloquant, majeur, mineur), décrites au §1 de l'analyse, pour que chaque constat soit classé de la même façon.
4. Vérification des faits cités par le cahier (AI Act, code de bonnes pratiques) par recherche web : résultats et sources au §7 de l'analyse. La date du 2 décembre 2026 est cohérente avec les sources secondaires mais reste à confirmer sur le texte officiel.
5. Rédaction de l'analyse : 16 constats transverses, 41 constats par section, tableau des contradictions, points ouverts à ajouter, questions à l'auteur, entrées pour chaque tâche suivante.
6. En vérifiant la faisabilité « sans IA » de F-90, constat que la remarque 6 du découpage rattachait à tort les points de traçage à l'OCR → ERR-0004, découpage v0.5.
7. Report des constats de la fin de T00 (merge, adresse du commit de merge, CodeRabbit) → ERR-0003, précision dans l'historique d'ADR-0003.
8. Mise à jour des index (`docs/README.md`, journal, errata).
9. Lint Markdown en local, commit.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Sources contradictoires sur la date d'entrée en vigueur de l'omnibus numérique | Sources secondaires (cabinets, blogs), texte officiel non consulté | Résultat noté « à confirmer sur EUR-Lex » ; question posée à l'auteur (A-20) |
| Certaines affirmations techniques reposent sur la connaissance générale de l'assistant (lecteurs de filigranes, vocabulaire IPTC) | Pas de vérification documentaire dans le cadre de T01 | Marquées « à vérifier », avec la tâche qui les vérifiera (T22, T31) |

## Écarts par rapport au découpage

- **Ajout** : vérification des faits cités par le cahier (critère C6), non prévue explicitement en T01.
- **Ajout** : ERR-0003, issu des notes de fin de T00, consigné ici comme le prévoit la règle du journal.
- Le découpage n'est modifié que pour corriger la remarque 6 ; les autres changements de tâches attendent les arbitrages de T02.

## Résultat

- [`docs/01-analyse/analyse-critique-cdc-v0.1.md`](../01-analyse/analyse-critique-cdc-v0.1.md).
- Vérification : `npx --yes markdownlint-cli2@0.23.2` ne signale aucune erreur ; aucun fichier interdit n'est suivi.

## Reste à faire

- Obtenir les réponses de l'auteur du cahier aux six questions du §8 de l'analyse.
- Décision de TheDarkMac sur l'écart d'adresse des commits de merge (ERR-0003) : à consigner dans le journal de T02.
- T02 : arbitrer les points ouverts du §10 du cahier et ceux du §6 de l'analyse.
