# T11 — Modèle de données

- **Branche** : `tache/T11-modele-de-donnees`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : F-80, F-81, F-82, §6 du cahier ; ES-04, ES-20 ; constats A-02, A-03, A-10, A-23, A-46, A-47
- **Décisions** : ADR-0054 à ADR-0059
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : modèle de données, avec le **constat** (phrase, donnée observée, règle, catégorie, direction), le **rapport**, l'analyse non menée et la couverture. Les ADR antérieurs y ajoutent : les schémas des messages du processus de travail (ADR-0036), la forme des observations (ADR-0042), le niveau du constat (ADR-0018), la direction contrainte par la fiche technique (ADR-0022), les phrases en gabarits (ADR-0020), le glossaire du projet (ADR-0021), et les exigences de sécurité ES-04 et ES-20.

## État initial

- PR [#6](https://github.com/TheDarkMac/AI-detector/pull/6) (T10) : 16 vérifications vertes sur le commit `9047043` (docs : `lint-markdown`, `fichiers-interdits` ; code : `qualite`, 9 × `tests` sur Linux, macOS et Windows × Python 3.12 à 3.14, `audit-dependances`, `paquet`, `code-ok`) ; CodeRabbit « skipped ».
- À la demande explicite de TheDarkMac, l'assistant a ajouté `code-ok` aux vérifications obligatoires de `detector` (désormais `lint-markdown`, `fichiers-interdits`, `code-ok` ; mode strict, `enforce_admins`, conversations résolues, 0 approbation, force-push et suppression interdits ; relu par l'API), puis a mergé la PR le 2026-10-26 à 13:05 UTC : `gh pr merge 6 --merge --subject "Merge: T10 — Squelette du projet Python et outillage (#6)"`. Commit de merge `3abfa71`, à l'adresse noreply (ADR-0007). La ligne T10 de l'index du journal portait encore « à venir » : corrigée en #6 dans cette tâche.
- Après T10, TheDarkMac a demandé pourquoi `main`, vide, restait la branche par défaut. L'examen a montré que Dependabot et le lancement hebdomadaire du workflow `code` ne lisent que la branche par défaut : ils étaient inactifs → [ERR-0005](../errata/ERR-0005-branche-par-defaut-ignoree.md). Sur le « ok » de TheDarkMac, `detector` est devenue la branche par défaut par l'API ([ADR-0053](../decisions/ADR-0053-branche-par-defaut.md)) ; la protection de `main` a été relue, inchangée. Un lancement manuel du workflow `code` sur `detector` (40328970897, tête `3abfa71`) a été accepté, ce qui prouve la disponibilité, mais annulé par le groupe de concurrence avant de tourner. PR [#7](https://github.com/TheDarkMac/AI-detector/pull/7) (commit `d129c64`) : 16 vérifications vertes ; mergée à 13:23 UTC à la demande explicite de TheDarkMac, `gh pr merge 7 --merge --subject "Merge: ERR-0005 — Branche par défaut ignorée (#7)"`, commit de merge `bdc445a`.
- Le lancement de push de `bdc445a` (40330138384) a réussi. [ERR-0006](../errata/ERR-0006-annulation-des-lancements-de-ci.md) (concurrence de la CI) : PR [#8](https://github.com/TheDarkMac/AI-detector/pull/8) (commit `2ad3619`), 16 vérifications vertes ; mergée à 13:27 UTC à la demande explicite de TheDarkMac, `gh pr merge 8 --merge --subject "Merge: ERR-0006 — La CI du code annulait ses propres lancements sur detector (#8)"`, commit de merge `51c4d48`. Vérification : un lancement manuel (40330702329) démarré pendant le lancement de push 40330669433 n'a pas annulé ce dernier, qui a réussi ; ancienne configuration, il l'aurait été.
- Relu au démarrage de T11 : le lancement manuel 40330702329, encore « en file d'attente » dix minutes après sa création à la fin de T10, s'est terminé avec succès à 13:37 UTC (tête `51c4d48`).
- Premier passage hebdomadaire de Dependabot (lundi) : aucune PR de Dependabot à ce jour ; à observer (prévention d'ERR-0005).
- Les alertes et mises à jour de sécurité de Dependabot sont **désactivées** sur le dépôt (l'API répond « Dependabot alerts are disabled for this repository ») ; elles ne font pas partie d'ADR-0052, qui ne porte que sur les mises à jour de versions. Optionnel : à proposer à TheDarkMac, sans action de l'assistant.
- Toujours en attente (TheDarkMac) : éditeur de confiance PyPI pour `voight-kampff-forensics` (workflow `publication.yml`, environnement `pypi`) ; la première publication attend aussi le fichier `LICENSE`, qui attend @Jean. Dire à @Jean que le dépôt et son cahier sont publics (ADR-0046) ; reformulations du registre (§4) et six questions.
- uv n'est pas installé sur le poste ; l'assistant utilise uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`51c4d48`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Lecture du cahier (§5.5, §6, §11), de l'analyse critique (A-02, A-03, A-10, A-23, A-46, A-47), du modèle de menace (ES-04, ES-13, ES-14, ES-20), de l'architecture (§4, §6, §12) et des ADR qui renvoient à T11 (ADR-0018, ADR-0020, ADR-0021, ADR-0022, ADR-0036, ADR-0042, ADR-0043).
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation : représentation dans le code, directions de F-81, raisons des analyses non menées, marquage des données identifiantes. Recommandation suivie pour les quatre, sans raison supplémentaire : les ADR reprennent les raisons présentées avec les options (ADR-0054 à ADR-0057).
3. Branche `tache/T11-modele-de-donnees` créée depuis `detector` à jour (`51c4d48`).
4. `uv add 'jsonschema>=4.26'` : cinq paquets ajoutés au verrou (`jsonschema`, `referencing`, `jsonschema-specifications`, `attrs`, `rpds-py`, plus `typing-extensions` sous Python 3.12). Examen sur PyPI selon ADR-0043 (licences, paquets précompilés, dépendances) : consigné dans ADR-0054. mypy strict demandant les annotations de `jsonschema`, absentes du paquet : `types-jsonschema` ajouté au groupe `dev`.
5. Modèle `src/voight_kampff/rapport/modele.py` : énumérations, dataclasses figées, invariants à la construction, `vers_dict` et `depuis_dict`. Choix de structure (observation séparée du constat, fondement, phrase dont les paramètres renvoient à des observations, état « partielle » de la couverture, technique hors V1 sans version) : ADR-0058 et ADR-0059, au statut « Proposé », soumis dans la PR.
6. Schémas `rapport.schema.json` et `messages.schema.json` (Draft 2020-12), chargement et validation dans `schemas/__init__.py`. Essai manuel : rapport complet et six types de message valides ; nom de fichier avec chemin refusé.
7. Ruff et mypy : deux lignes trop longues, un type d'itération à préciser ; corrigés.
8. Tests : `tests/conftest.py` (un rapport qui emploie chaque élément du modèle), `tests/test_modele.py`, `tests/test_schemas.py`. Premier passage : une altération attendue « refusée par le schéma et le modèle » (champ inconnu) n'était refusée que par le schéma. Le modèle lit un document déjà validé : le cas a été déplacé dans un test propre, et la répartition des vérifications documentée (modèle de données, §7).
9. Interruption de la session de l'assistant pendant le passage de la couverture ; reprise sur la même branche, rien de perdu. 266 tests verts ; une branche impossible (`match` sans autre catégorie) laissait la couverture à 99 % : écrite `case _`, couverture à 100 %.
10. L'environnement temporaire de uv ayant disparu avec la session, uv 0.13.5 a été réinstallé dans un nouvel environnement temporaire. Construction faite deux fois : fichiers identiques ; le wheel contient `rapport/` et les deux schémas ; installé dans un environnement neuf, les schémas s'y chargent en mode isolé (`python -I`). pip-audit : aucune faille connue.
11. CI : étape ajoutée au job `paquet` pour charger les schémas depuis le wheel installé (ADR-0054).
12. Documentation : ADR-0054 à ADR-0059, [modèle de données](../modele-de-donnees/modele-de-donnees.md), [glossaire du projet](../glossaire.md), renvois dans ADR-0018, ADR-0020, ADR-0021, ADR-0022, ADR-0036, ADR-0042, ADR-0043 ; architecture v1.2, découpage v0.10, registre v1.4 ; index des ADR et du journal ; `docs/README.md`.
13. Lint Markdown en local, vérification des fichiers interdits, commits ; branche poussée et PR ouverte vers `detector`.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| `$` d'une expression de schéma acceptait `"abc\n"` | En Python, `$` accepte un saut de ligne final ; ECMAScript non | `$(?!\n)` dans les expressions d'identifiant et de version ; longueur fixe pour l'empreinte et les dates ; testé (ADR-0054) |
| Un entier hors bornes passait par la branche « nombre » du schéma | JSON Schema ne distingue pas 1 de 1.0 : borner seulement les entiers ne suffit pas | Tous les nombres bornés à l'intervalle des entiers signés sur 64 bits, dans le schéma et dans le modèle |
| Un champ inconnu n'était refusé que par le schéma | `depuis_dict` lit un document supposé validé | Comportement gardé et documenté (§7 du modèle de données), testé à part |
| mypy refusait `jsonschema` | Paquet publié sans annotations de types | `types-jsonschema` dans le groupe `dev` |
| Session de l'assistant interrompue pendant les tests | Fin de session côté outil | Reprise ; état vérifié par `git status` et un nouveau passage des tests |
| uv introuvable à la reprise | L'environnement temporaire de l'assistant avait été nettoyé | uv 0.13.5 réinstallé dans un nouvel environnement temporaire |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. La phrase de l'architecture sur les expressions régulières dans P1 a été précisée (v1.2, §6), sans être fausse : elle visait le catalogue.

## Écarts par rapport au découpage

- **Ajout** : le glossaire du projet, demandé par ADR-0021 à T11 et T103 ; T11 crée la version de référence, T103 en tirera le glossaire utilisateur.
- **Ajout** : une étape de la CI (job `paquet`) qui charge les schémas depuis le wheel.
- **Reporté** à T30 : liste de confiance C2PA et données externes dans la rubrique Versions (ADR-0023), qui n'existent pas encore.
- **Reporté** à T13 : concordance des empreintes (ES-08) ; à T16 : résumé, avertissement, masquage et rédaction des gabarits.

## Résultat

- Modèle `voight_kampff.rapport.modele` : observation, constat, analyse non menée, couverture, identification, versions, isolation, rapport ; aucune dépendance hors bibliothèque standard (testé).
- Schémas du rapport et des messages, version `0.1.0`, validés sans accès réseau ; `jsonschema` première dépendance d'exécution du projet.
- Six ADR (dont deux proposés), modèle de données v1.0, glossaire v1.0, architecture v1.2, découpage v0.10, registre v1.4.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent (266 tests, couverture 100 %) ; construction reproductible ; `npx --yes markdownlint-cli2@0.23.2` sans erreur ; aucun fichier interdit suivi.

## Reste à faire

- TheDarkMac : valider ou modifier ADR-0058 et ADR-0059 (statut « Proposé ») dans la PR.
- T12 : décodage JSON strict, puis schéma, puis `depuis_dict` pour chaque message ; conversion des échecs en analyses non menées ; couverture tirée des manifestes ; directions permises par règle (ADR-0022).
- T15 : forme des identifiants de règle ; fondement, catégorie, directions, niveau, taux et limites de chaque règle ; liste des techniques hors V1 par format (ou T12).
- T16 : gabarits des constats et des raisons ; masquage par catégorie ; numérotation de la version du schéma à sa première publication.
- T30 : liste de confiance et données externes au rapport ; éventuelle structure de la source d'une preuve.
- Toujours en attente : éditeur de confiance PyPI et `LICENSE` (TheDarkMac, @Jean) ; messages à @Jean ; premier passage de Dependabot à consigner ; alertes de sécurité de Dependabot à proposer.
