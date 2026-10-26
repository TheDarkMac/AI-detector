# T10 (complément) — Fichier LICENSE et éditeur de confiance PyPI

- **Branche** : `tache/T10-licence-et-publication`
- **Dates** : 2026-10-27 → 2026-10-27
- **Exigences couvertes** : §10 (licence) ; ES-18 (canal de distribution)
- **Décisions** : ADR-0067
- **Errata** : aucun

## Objectif

Terminer deux points de T10 restés en attente : le fichier `LICENSE` (ADR-0011), reporté tant que @Jean n'avait pas dit sous quelle licence son cahier des charges peut être diffusé, et l'éditeur de confiance PyPI (ADR-0041, ADR-0045). Le workflow de publication refuse de publier sans `LICENSE`. Ce n'est pas une tâche nouvelle du découpage : la branche garde le préfixe de T10, avec un slug distinct, et l'entrée du journal porte « T10 (complément) ».

## État initial

- PR [#10](https://github.com/TheDarkMac/AI-detector/pull/10) (T12) : premier lancement de la CI (40398924617, commit `eedc50e`) en échec sous Windows seulement. Neuf tests de `test_travail.py`, qui font tourner le processus de travail dans le processus des tests, passaient un descripteur là où Windows attend un handle ; les tests avec un vrai processus de travail passaient. Corrigé par la fonction `transmis` (commit `759ebd7`). TheDarkMac a validé ADR-0064 et ADR-0065, passés au statut « Accepté » (commit `53d61d6`) ; les deux points sont déjà aux étapes 17 et 18 du journal de T12.
- Second lancement (40406917793, commit `53d61d6`) : 16 vérifications vertes, dont 3 sous Windows ; CodeRabbit « skipped ». Mergée le 2026-10-26 à 21:46:47 UTC à la demande explicite de TheDarkMac : `gh pr merge 10 --merge --subject "Merge: T12 — Moteur de modules (#10)"`. Commit de merge `239f646`, à l'adresse noreply (ADR-0007). Lancements de push `code` (40407206570) et `docs` (40407206593) sur `239f646` : réussis.
- La ligne T12 de l'index du journal portait encore « à venir » : corrigée en #10 ici.
- Toujours en attente avant cette tâche : éditeur de confiance PyPI ; `LICENSE`, qui attendait @Jean ; messages à @Jean (dépôt public, reformulations du registre §4 dont F-81, six questions) ; Dependabot (aucune PR le lundi 2026-10-26 à 20:45 UTC, à revoir le lundi suivant) ; alertes de sécurité de Dependabot, désactivées, à proposer.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`239f646`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Lecture d'ADR-0011, ADR-0041, ADR-0045, ADR-0066, du workflow `publication.yml`, du job `paquet` de `code.yml` et des journaux de T10 à T12.
2. Constat : le paquet source ne contient pas `docs/` (vérifié par la CI depuis T10), donc pas le cahier des charges.
3. Deux questions à TheDarkMac, en un lot. Licence : l'assistant recommandait d'ajouter `LICENSE` en excluant `docs/00-cahier-des-charges/` ; TheDarkMac a répondu que @Jean avait donné son accord pour qu'Apache-2.0 couvre aussi son cahier (date et canal de l'accord non précisés). PyPI : l'assistant ne saisit pas de mot de passe ; TheDarkMac se connecte lui-même dans le navigateur intégré, l'assistant remplit le formulaire.
4. Branche `tache/T10-licence-et-publication` créée depuis `detector` à jour (`239f646`).
5. Texte officiel téléchargé depuis <https://www.apache.org/licenses/LICENSE-2.0.txt> : 202 lignes, SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`, empreinte connue du fichier de référence.
6. `pyproject.toml` : `license = "Apache-2.0"` et `license-files = ["LICENSE"]` (PEP 639, [ADR-0067](../decisions/ADR-0067-fichier-licence-et-declaration.md)) ; aucun classificateur de licence. `uv lock --check` : verrou inchangé.
7. Construction faite deux fois avec l'outil épinglé : fichiers identiques. Le paquet source contient `LICENSE` à sa racine, le wheel `.dist-info/licenses/LICENSE` ; les deux portent `License-Expression: Apache-2.0` et `License-File: LICENSE` (métadonnées 2.4). Étape correspondante ajoutée au job `paquet` de la CI.
8. `README.md` : section « Licence ».
9. PyPI : page « Publishing » ouverte dans le navigateur intégré ; TheDarkMac s'est connecté (mot de passe et code à deux facteurs saisis par lui). L'éditeur « en attente » existait déjà, avec les valeurs attendues : projet `voight-kampff-forensics`, dépôt `TheDarkMac/AI-detector`, workflow `publication.yml`, environnement `pypi`. Rien n'a été soumis ; la date de sa création n'est pas affichée.
10. Environnement GitHub `pypi` vérifié par l'API : relecteur obligatoire TheDarkMac, déploiement limité aux étiquettes `v*`. Nom `voight-kampff-forensics` toujours libre sur PyPI (réponse 404 de l'API JSON) le 2026-10-27.
11. Documents mis à jour : historique d'ADR-0011, ADR-0041 et ADR-0045 (renvois) ; index des ADR ; architecture §11 (version 1.4) ; index du journal.

## Problèmes rencontrés

Aucun.

## Écarts par rapport au découpage

- **Ajout** : complément de T10, hors numérotation du découpage, pour deux points que T10 avait reportés.
- La déclaration de l'éditeur de confiance était annoncée comme restant à faire dans les journaux de T10 à T12 ; elle était en fait déjà faite. Ce n'est pas une erreur d'analyse (le dépôt ne pouvait pas le savoir), pas d'erratum.

## Résultat

- `LICENSE` (Apache-2.0, texte intégral) à la racine, couvrant tout le dépôt ; livré dans les deux paquets ; licence déclarée par expression SPDX.
- Prérequis de la première publication réunis : `LICENSE`, éditeur de confiance, environnement protégé. Vérification locale : deux constructions identiques, contrôle des métadonnées de licence.

## Reste à faire

- Première publication (étiquette `v…` égale à la version du paquet, ADR-0050), qui seule réserve le nom sur PyPI (ADR-0045) : à décider par TheDarkMac.
- Messages à @Jean (reformulations du registre §4 dont F-81, six questions) ; Dependabot à observer ; alertes de sécurité de Dependabot à proposer.
