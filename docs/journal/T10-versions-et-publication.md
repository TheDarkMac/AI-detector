# T10 (complément 2) — Numérotation des versions et contrôles de la publication

- **Branche** : `tache/T10-versions-et-publication`
- **Dates** : 2026-10-27 → 2026-10-27
- **Exigences couvertes** : ES-18 (canal de distribution) ; NF-06 (version au rapport)
- **Décisions** : ADR-0068 (proposé, choix attendu de TheDarkMac), ADR-0069
- **Errata** : aucun

## Objectif

Préparer la première publication sur PyPI, à la demande de TheDarkMac : proposer les règles de numérotation des versions publiées, qu'ADR-0050 demande de fixer avant elle ; marquer la release GitHub comme pré-version quand la version en est une ; refuser une étiquette qui n'est pas posée sur un commit de `detector`. Comme le complément précédent, ce n'est pas une tâche du découpage : la branche garde le préfixe de T10.

## État initial

- PR [#11](https://github.com/TheDarkMac/AI-detector/pull/11) (T10, complément) : CI verte sur `3f2236c` (lancements `docs` 40408454703 et `code` 40408454724, dont le nouveau contrôle de `LICENSE` dans le job `paquet`). TheDarkMac a validé ADR-0067, passé au statut « Accepté » (commit `89fbd7d`, journal du complément, étape 12). CI verte sur `89fbd7d` (lancements 40408650393 et 40408650386, 16 vérifications).
- Mergée le 2026-10-26 à 21:58:52 UTC à la demande explicite de TheDarkMac : `gh pr merge 11 --merge --subject "Merge: T10 (complément) — Fichier LICENSE et éditeur de confiance PyPI (#11)"`. Commit de merge `c9031fd`, à l'adresse noreply (ADR-0007). Lancements de push `code` et `docs` sur `c9031fd` : réussis.
- La ligne du complément dans l'index du journal portait « à venir » : corrigée en #11 ici.
- Après le merge, TheDarkMac a demandé ce qui, côté PyPI, demandait encore sa validation. Réponse de l'assistant : la numérotation des versions (ADR-0050) ; le moment et la version de la première publication ; la release GitHub jamais marquée comme pré-version ; deux renforcements facultatifs, le contrôle de l'origine de l'étiquette et le contournement de la relecture de l'environnement `pypi` par un administrateur (`can_admins_bypass`). TheDarkMac a demandé une PR pour les trois premiers points, la numérotation sous forme d'options.
- Constaté par l'API à cette occasion : TheDarkMac est le seul collaborateur (administrateur) ; aucune règle GitHub (« ruleset ») sur le dépôt ; aucune étiquette.
- Toujours en attente : messages à @Jean (reformulations du registre §4 dont F-81, six questions) ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot, désactivées, à proposer. L'accord de @Jean sur la licence de son cahier a été rapporté par TheDarkMac, sans date ni canal.
- `detector` à jour avec `origin/detector` (`c9031fd`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>` ; uv 0.13.5 dans un environnement temporaire.

## Déroulé

1. Lecture d'ADR-0050, ADR-0029, ADR-0023, ADR-0054, ADR-0062 et du workflow `publication.yml`.
2. Branche `tache/T10-versions-et-publication` créée depuis `detector` à jour (`c9031fd`).
3. Essai de normalisation : dans une copie du dépôt, `version` mise à `0.1.0-dev0`, `0.1.0.dev0`, `1.0.0RC1`, `1.0.0.post1`. `uv version --short` rend la forme normalisée (`0.1.0.dev0`, `1.0.0rc1`…), identique au nom des paquets construits. Le contrôle de pré-version peut donc travailler sur cette forme.
4. Workflow : historique complet récupéré (`fetch-depth: 0`) ; deux étapes ajoutées au job `construction`, avant la construction : l'étiquette doit viser un commit de l'historique de premier parent de `origin/detector` ; la version doit être une version publique PEP 440, et la sortie `pre-version` vaut `true` pour `aN`, `bN`, `rcN` ou `.devN`. Le job `release-github` lit cette sortie et passe `--prerelease` ([ADR-0069](../decisions/ADR-0069-controles-de-la-publication.md)).
5. Relecture du premier jet : deux défauts corrigés avant tout essai. Les numéros de groupes de l'expression régulière étaient décalés (3 et 6 au lieu de 2 et 5). Un tube `git rev-list | grep -q` peut échouer sous `pipefail` quand `grep` s'arrête tôt : remplacé par une substitution de processus.
6. Essais en local des trois scripts, extraits du YAML. Étiquette : `c9031fd` et `239f646` (commits de merge de `detector`) acceptés ; `89fbd7d` et `53d61d6` (commits de branches de tâche, mergés) refusés. Version : `0.1.0.dev0`, `0.1.0a1`, `1.0.0rc2`, `1.0.0b1.post1`, `1.0.0.post1.dev3` → pré-version ; `1.0.0`, `1.0.0.post1`, `2.1` → version ; `1.0.0+local` → refusée. Release : `--prerelease` présent seulement pour une pré-version.
7. [ADR-0068](../decisions/ADR-0068-numerotation-des-versions.md) rédigé avec les options (forme des numéros ; publication avant une version stable) et une recommandation, au statut « Proposé » : le choix revient à TheDarkMac.
8. Documents mis à jour : historique d'ADR-0041 et ADR-0050 (renvois) ; index des ADR ; architecture §11 (version 1.5) ; index du journal.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Numéros de groupes décalés dans le premier jet du contrôle de version | Groupe imbriqué `(a\|b\|rc)` mal compté | Groupes 2 et 5, commentés dans le workflow ; vérifié sur neuf formes |
| Risque d'échec à tort du contrôle de l'étiquette | `pipefail` et arrêt anticipé de `grep -q` dans un tube | Substitution de processus |

Les deux défauts ont été trouvés à la relecture, avant tout lancement : pas d'erratum.

## Écarts par rapport au découpage

- **Ajout** : second complément de T10, hors numérotation du découpage.
- **Non fait** : règle GitHub réservant les étiquettes `v*` et retrait de `can_admins_bypass` sur l'environnement `pypi` : réglages du dépôt, non demandés dans cette PR (ADR-0069, option C).

## Résultat

- Workflow de publication : étiquette refusée hors de `detector`, version non publique refusée, release marquée pré-version quand il le faut. Vérifié en local seulement : ces étapes ne tournent qu'à une vraie publication.
- ADR-0068 en attente du choix de TheDarkMac.

## Reste à faire

- Choix de numérotation (ADR-0068) ; selon ce choix, procédure de version dans `CONTRIBUTING.md`.
- Première publication, après ce choix : avec l'option D, étiquette `v0.1.0.dev0` sur le commit de merge de cette PR, puis approbation dans l'environnement `pypi`. Ce sera le premier essai réel des contrôles d'ADR-0069.
- Facultatif, sur demande : règle GitHub sur les étiquettes `v*` ; `can_admins_bypass` désactivé.
- Messages à @Jean ; Dependabot à observer ; alertes de sécurité de Dependabot à proposer.
