# T02 — Arbitrage des points ouverts

- **Branche** : `tache/T02-arbitrages`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : §10 du cahier (points ouverts) ; points du §6 de l'analyse critique
- **Décisions** : ADR-0007 à ADR-0026
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : arbitrer les points ouverts de la section 10 du cahier, un ADR par décision, avec options écartées et raisons. L'analyse critique (T01) y a ajouté douze points (§6) et des constats adressés à T02 (§8).

## État initial

- PR [#2](https://github.com/TheDarkMac/AI-detector/pull/2) (T01) mergée dans `detector` le 2026-10-26 à 06:03 UTC, commit de merge `016ba73`. Vérifications vertes : `lint-markdown`, `fichiers-interdits` ; CodeRabbit présent, revue non effectuée (« skipped »), sans incidence.
- Le commit de merge porte de nouveau l'adresse noreply du compte : ERR-0003 confirmé.
- L'auto-merge GitHub est désactivé sur le dépôt (« Auto merge is not allowed ») : les merges se font à la main par `gh pr merge --merge`, après vérification de la CI, conformément à ADR-0001.
- Décision de TheDarkMac, prise le 2026-10-26 après le merge de T01 : l'adresse noreply des commits de merge est **acceptée** → consignée dans ADR-0007 (premier commit de T02).
- Les six questions posées à l'auteur du cahier (§8 de l'analyse) sont sans réponse.
- `detector` à jour avec `origin/detector`, arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Branche `tache/T02-arbitrages` créée depuis `detector` à jour.
2. ADR-0007 rédigé ; ADR-0003 (historique), ERR-0003 (« Correction appliquée ») et l'index du journal (PR #2 de T01) mis à jour. Commit.
3. Relecture du §10 du cahier (30 points), du §6 et du §8 de l'analyse (12 points ajoutés, 19 constats adressés à T02). Regroupement en 16 questions, chacune avec deux à quatre options et une recommandation de l'assistant.
4. Questions posées à TheDarkMac en quatre lots :
   - lot 1, produit : objectif, public, distribution, licence ;
   - lot 2, périmètre : contenu de la V1, module texte, contrôle avant publication, lots et antériorité ;
   - lot 3, sans IA et rapport : frontière, services tiers et OCR, synthèse et graduation, NF-19 ;
   - lot 4 : langue et pays, propositions de l'analyse à adopter (choix multiple), exports et accessibilité, validation du besoin.
5. Réponses : recommandation suivie pour quatorze des quinze questions à choix unique ; pour les services tiers, option « optionnels » retenue au lieu de « exclus » ; les quatre propositions du choix multiple adoptées.
6. Rédaction d'un ADR par décision (ADR-0008 à ADR-0026). En rédigeant ADR-0017, constat d'une conséquence du choix « services tiers optionnels » : un service tiers reçoit en général le fichier, ce que NF-16 interdit ; la reformulation nécessaire de NF-16 est écrite dans l'ADR et au registre.
7. Rédaction du [registre des arbitrages](../02-arbitrages/registre-des-arbitrages.md) : statut de chaque point (tranché, reporté, non tranché), exigences reformulées, questions en attente de l'auteur.
8. Découpage v0.6 : statut V1, V2 ou hors V1 de chaque tâche ; T13, T16, T17, T31, T90, T91, T95, T104 précisées ; T105 ajoutée. En le faisant, constat que le statut des tâches P9 et P10 n'avait pas été posé en question : statut déduit des NF et du §9, inscrit dans ADR-0012 comme proposition de l'assistant.
9. Renvoi vers le registre dans l'analyse critique (v1.1) et dans `docs/README.md` ; index des ADR et du journal mis à jour.
10. Lint Markdown en local, commits.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| 42 points à arbitrer, trop pour une question chacun | Le §10 et l'analyse se recoupent | Regroupement en 16 questions ; les points sans décision possible maintenant sont reportés avec leur raison (registre §2) |
| Le choix « services tiers optionnels » contredit NF-16 telle qu'écrite | Option présentée avec la mention « requête sortante (NF-16) », sans dire que la requête emporte le fichier | Conséquence écrite dans ADR-0017, reformulation de NF-16 au registre, signalée à TheDarkMac dans la PR |
| Raisons des choix | TheDarkMac a choisi parmi les options sans commenter | Les ADR reprennent les raisons présentées avec les options, et le disent (registre §1) ; aucune raison ne lui est attribuée sans source (leçon d'ERR-0002) |
| Points « principe sans IA définitif » et « nom du projet » non posés | Omis du regroupement en questions | Inscrits « non tranchés » au registre, avec leur effet (aucun sur les tâches suivantes) |

## Écarts par rapport au découpage

- **Ajout** : le dossier `docs/02-arbitrages/` et son registre, non prévus ; ils tiennent lieu des cases à cocher du §10 du cahier, qui n'est pas modifié.
- **Ajout** : ADR-0007 (décision de fin de T01), consigné ici comme le prévoyait le journal de T01.
- **Ajout** : tâche T105 au découpage.

## Résultat

- 20 ADR (ADR-0007 à ADR-0026), le registre des arbitrages, le découpage v0.6.
- Vérification : `npx --yes markdownlint-cli2@0.23.2` ne signale aucune erreur ; aucun fichier interdit n'est suivi.

## Reste à faire

- Validation par TheDarkMac, dans la PR, des points reportés et des deux propositions non posées en question (statut P9 et P10, reformulation de NF-16).
- Transmettre à l'auteur du cahier les reformulations d'exigences (registre §4) et relancer les six questions.
- T03 : double usage (ADR-0014), flux vers les services tiers (ADR-0017), portée de NF-17 en local (ADR-0010), isolation (A-53), authentification du catalogue (A-37).
- T04 : langage, licences des dépendances (ADR-0011), versions figées (ADR-0023), point d'extension pour les services tiers (ADR-0017).
