# T03 — Modèle de menace

- **Branche** : `tache/T03-modele-de-menace`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : NF-15 (livrable 7), NF-01, NF-16, NF-18 ; NF-17 (portée en local)
- **Décisions** : ADR-0027 à ADR-0033
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : rédiger le modèle de menace (adversaires, biens à protéger, surfaces d'attaque : fichiers hostiles, requêtes sortantes, fuite de sources) avant tout choix d'architecture (NF-15). S'y ajoutent les points renvoyés à T03 par l'analyse critique (A-14, A-16, A-31, A-37, A-42, A-48, A-53) et par T02 : double usage (ADR-0014), flux vers les services tiers (ADR-0017), portée de NF-17 en local (ADR-0010), isolation, authentification du catalogue.

## État initial

- PR [#3](https://github.com/TheDarkMac/AI-detector/pull/3) (T02) : vérifications vertes (`lint-markdown`, `fichiers-interdits`) ; CodeRabbit présent, revue non effectuée (« skipped »), sans incidence.
- Une première tentative de merge par l'assistant (`gh pr merge --merge`) a été **bloquée** par le classifieur de permissions du mode automatique de l'outil d'assistance, qui l'a jugée comme un merge sans revue. Après le feu vert explicite de TheDarkMac dans la conversation, l'assistant a mergé la PR le 2026-10-26 à 08:35 UTC ; commit de merge `a4adfb8`, de nouveau à l'adresse noreply, conformément à ADR-0007.
- La PR #3 ne contient aucun commentaire sur les points soumis à validation : reformulation de NF-16 (ADR-0017), statut V1 des tâches P9 et P10 (ADR-0012), points reportés ou non tranchés du registre (nom du projet, principe « sans IA » définitif, articulation avec le cahier compagnon). Le feu vert portait sur le merge ; TheDarkMac a confirmé ensuite, pendant la revue de la PR de T03, que ces points sont acceptés (étape 11).
- En attente : réponses de l'auteur du cahier aux six questions (§8 de l'analyse), et transmission des reformulations (registre §4).
- `detector` à jour avec `origin/detector`, arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Branche `tache/T03-modele-de-menace` créée depuis `detector` à jour.
2. Relecture du cahier (§7, §10), des constats de l'analyse adressés à T03, du registre des arbitrages et des ADR qui renvoient à T03 (ADR-0010, ADR-0012, ADR-0014, ADR-0017, ADR-0019).
3. Premier jet de l'analyse : biens, adversaires, diagramme de flux, surface d'analyse de la V1. Six choix identifiés qui relèvent de TheDarkMac ; chacun formulé avec trois options et une recommandation de l'assistant.
4. Questions posées en deux lots :
   - lot 1, sécurité du poste et de l'outil : méthode, niveau d'isolation, intégrité du catalogue ;
   - lot 2, protection des sources : portée de NF-17, traitement de l'empreinte, double usage.
5. Réponses : recommandation suivie pour les six questions. Aucune raison supplémentaire n'a été donnée ; les ADR reprennent les raisons présentées avec les options.
6. Rédaction du [modèle de menace](../modele-de-menace/modele-de-menace.md) : 8 biens, 7 adversaires, 5 hypothèses, diagramme avec 5 frontières de confiance, 33 menaces STRIDE, 5 cas d'abus, inventaire des requêtes sortantes (NF-16), 22 exigences de sécurité rattachées aux tâches, 9 risques résiduels.
7. En rédigeant l'inventaire des requêtes sortantes, constat d'une menace de cote haute non couverte par les questions : une URL écrite dans le fichier (manifeste C2PA distant, modèle distant d'un DOCX) peut servir de balise de pistage (M-14). Politique proposée par l'assistant dans ADR-0033, au statut « Proposé », soumise dans la PR.
8. Rédaction des ADR-0027 à ADR-0033 ; renvois ajoutés à l'historique d'ADR-0010, ADR-0012, ADR-0014 et ADR-0017.
9. Registre des arbitrages v1.1 (points 8 à 10 du §3, NF-17, reformulations de NF-01, NF-16, NF-17, F-05) ; découpage v0.7 (T04, T13 à T17, T30, T45, T91, T93, T94 précisées) ; index des ADR et du journal ; `docs/README.md`.
10. Lint Markdown en local, vérification des fichiers interdits, commits ; PR [#4](https://github.com/TheDarkMac/AI-detector/pull/4) ouverte, vérifications vertes.
11. Pendant la revue de la PR, TheDarkMac a validé ADR-0033 et confirmé que les points soumis dans la PR de T02 sont acceptés. ADR-0033 passe au statut « Accepté » ; les mentions « proposé » sont retirées du modèle de menace, du registre, de l'index des ADR et des renvois d'ADR-0010 et ADR-0017.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Une décision (requêtes vers des URL issues du fichier) n'a pas été posée en question | Identifiée en rédigeant l'inventaire des requêtes, après les deux lots | ADR-0033 au statut « Proposé », signalé dans la PR, puis validé par TheDarkMac pendant la revue (étape 11) |
| F-05 (empreinte inscrite) et NF-17 (journal) ne sont pas satisfaites à la lettre par les choix retenus | Les deux exigences créent une trace qui peut désigner une source (A-48, M-27) | Interprétation (F-05) et reformulation (NF-17) inscrites au registre §4, à faire valider par l'auteur du cahier |
| Numérotation des menaces non continue dans le premier jet (sections 6.3 et 6.4 inversées) | Ordre de rédaction | Sections réordonnées avant le commit ; aucun document publié touché |
| Une menace forgée par un processus de travail compromis (« signature valide » inventée) n'est pas entièrement évitable | Revérifier hors du bac à sable exposerait le processus principal aux mêmes analyseurs | Risque résiduel RR-01, confiné au fichier en cause |

## Écarts par rapport au découpage

- **Ajout** : exigences de sécurité numérotées (ES-01 à ES-22), rattachées aux tâches ; elles précisent T04, T13 à T17, T30, T91 au découpage v0.7.
- **Ajout** : décision sur le double usage (ADR-0032), que le découpage prévoyait « après T03 » sans la rattacher à une tâche.
- Le livrable est un dossier `docs/modele-de-menace/`, comme annoncé dans `docs/README.md`.

## Résultat

- Le modèle de menace v1.0, sept ADR acceptés (ADR-0027 à ADR-0033), le registre v1.1, le découpage v0.7.
- Vérification : `npx --yes markdownlint-cli2@0.23.2` ne signale aucune erreur ; aucun fichier interdit n'est suivi.

## Reste à faire

- Transmettre à l'auteur du cahier les nouvelles reformulations (NF-01, NF-16, NF-17, F-05) avec celles de T02, et relancer les six questions.
- T04 : mécanismes d'isolation par système (ADR-0028), canal de distribution et publication des empreintes (ADR-0029), exigences ES-xx rattachées à T04.
- T17 : intégrer les exigences ES-xx à la matrice de vérification (ADR-0024).
