# T12 — Moteur de modules

- **Branche** : `tache/T12-moteur-de-modules`
- **Dates** : 2026-10-26 → 2026-10-27
- **Exigences couvertes** : modularité (§2), NF-03, NF-10 ; ES-01 (lancement), ES-04, ES-17 (garde) ; F-25 et F-82 pour la couverture
- **Décisions** : ADR-0060 à ADR-0065 ; ADR-0066 (licence MIT, abandonnée)
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : moteur de modules, avec la découverte et les manifestes (ADR-0042), l'activation et la désactivation, l'isolation des erreurs par module, le lancement du processus de travail et le protocole (ADR-0036). Les ADR antérieurs y ajoutent : décodage JSON strict, puis schéma, puis modèle pour chaque message (modèle de données §7) ; conversion des échecs en analyses non menées (ADR-0056) ; couverture tirée des manifestes (ADR-0059) ; directions permises par la fiche technique (ADR-0022) ; garde des analyseurs (ES-17).

## État initial

- PR [#9](https://github.com/TheDarkMac/AI-detector/pull/9) (T11) : 16 vérifications vertes sur le commit `1678a6f` (docs : `lint-markdown`, `fichiers-interdits` ; code : `qualite`, 9 × `tests` sur Linux, macOS et Windows × Python 3.12 à 3.14, `audit-dependances`, `paquet` avec la nouvelle étape « schémas livrés dans le wheel », `code-ok`) ; CodeRabbit « skipped ».
- Pendant la revue, TheDarkMac a validé ADR-0058 et ADR-0059, passés au statut « Accepté » (commit `1678a6f`, journal de T11, étape 14). La description de la PR a été mise à jour par l'API REST : `gh pr edit` échoue sur une erreur de dépréciation des « Projects classic » de l'API GraphQL.
- Mergée le 2026-10-26 à 19:59:50 UTC à la demande explicite de TheDarkMac : `gh pr merge 9 --merge --subject "Merge: T11 — Modèle de données (#9)"`. Commit de merge `b79bb67`, à l'adresse noreply (ADR-0007). Lancements de push `docs` et `code` sur `b79bb67` : réussis.
- La ligne T11 de l'index du journal portait encore « à venir » : corrigée en #9 dans cette tâche.
- Avant T12, TheDarkMac a proposé de passer à la licence MIT. L'assistant a rappelé qu'ADR-0011 avait retenu Apache-2.0 pour sa clause sur les brevets, absente de MIT, et ce qu'un changement imposait de reprendre (nouvel ADR, ADR-0043, déclaration de licence du paquet). TheDarkMac a gardé Apache-2.0. L'option est consignée dans [ADR-0066](../decisions/ADR-0066-licence-mit-abandonnee.md), au statut « Abandonné », avec un renvoi dans l'historique d'ADR-0011. L'assistant avait d'abord annoncé l'ajouter comme option de plus dans ADR-0011 ; la règle du registre (une option sérieusement envisagée et rejetée a son propre ADR ; un ADR accepté n'est pas modifié sur le fond) a conduit à l'ADR séparé.
- Dependabot : lundi 2026-10-26, à 20:45 UTC, aucune PR de Dependabot. Explication probable : le verrou est récent et le délai d'attente des nouvelles versions est de 7 jours (ADR-0052). À observer le lundi suivant.
- Toujours en attente : éditeur de confiance PyPI (TheDarkMac) ; fichier `LICENSE` (Apache-2.0), qui attend la réponse de @Jean sur son cahier ; messages à @Jean (dépôt public, reformulations du registre §4 dont F-81, six questions) ; alertes de sécurité de Dependabot, désactivées sur le dépôt, à proposer.
- uv n'est pas installé sur le poste ; l'assistant utilise uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`b79bb67`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Lecture d'ADR-0036, ADR-0042, ADR-0028, ADR-0035, ADR-0038, ADR-0012, ADR-0017, ADR-0022, ADR-0056, ADR-0059, de l'architecture (§3 à §7, §12), du modèle de données, du modèle de menace (ES-01, ES-04, ES-15, ES-17, M-10, RR-01) et du code de T10 et T11.
2. Branche `tache/T12-moteur-de-modules` créée depuis `detector` à jour (`b79bb67`) ; uv 0.13.5 réinstallé ; 266 tests verts au départ.
3. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation : résultats d'un module en erreur, interface d'un module, fin de module dans le protocole, désactivation en ligne de commande. Recommandation suivie pour les quatre, sans raison supplémentaire : [ADR-0060](../decisions/ADR-0060-resultats-d-un-module-en-erreur.md) à [ADR-0063](../decisions/ADR-0063-desactivation-et-liste-des-modules.md). Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0064](../decisions/ADR-0064-manifeste-des-modules.md) (manifeste) et [ADR-0065](../decisions/ADR-0065-lancement-et-reception.md) (lancement et réception).
4. Schémas : `manifeste.schema.json` créé et ajouté au registre des schémas ; définition `module` ajoutée à `messages.schema.json`, version `0.1.0` inchangée (ADR-0062).
5. `modules/__init__.py` (découverte des dossiers, commune aux deux processus) et `_orchestration/manifestes.py` (lecture TOML, validation, ordre d'exécution, désactivation).
6. Processus de travail : `_protocole.py` (lignes JSON, décodage strict, tailles provisoires), `_travail/garde.py` (ES-17), `_travail/fichier.py` (lectures à position, empreinte), `_travail/contexte.py` (ADR-0061), `_travail/principal.py` et `_travail/__main__.py` (déroulé d'ADR-0036, sortie standard réservée au protocole).
7. Processus principal : `_orchestration/travail.py` (lancement, fil de lecture, échéance, contrôles de chaque message, couverture). Essai manuel : fichier de 7 octets, aucun module, 0,35 s ; empreinte reçue égale à celle de `hashlib`.
8. Ligne de commande : option `--modules` (ADR-0063).
9. Ruff et mypy : deux lignes trop longues ; des `noqa` visant des règles non activées, retirés (Ruff les signale comme inutiles) ; des `assert` du code remplacés par des contrôles explicites.
10. Tests : `test_manifestes.py`, `test_protocole.py`, `test_travail.py` (processus de travail dans le processus des tests, flux en mémoire), `test_orchestration.py` et `travail_factice.py` (vrai processus de travail, et processus de travail factice : analyseurs de test, puis un scénario valide et 34 de processus défaillant ou compromis). Premier passage : 44 tests d'orchestration verts.
11. Vérification des tests eux-mêmes : treize contrôles du processus principal retirés un à un ; à chaque fois, le scénario qui le vise échoue. Les contrôles sont donc bien exercés.
12. Couverture : le code exécuté dans le processus de travail n'était pas mesuré, l'environnement vidé empêchant coverage de s'y inviter. Les tests qui se terminent normalement lancent le processus de travail sous `coverage run --parallel-mode`. Premier essai sur tous les scénarios : fichiers de mesure corrompus, `coverage combine` en échec (voir ci-dessous) ; mesure limitée aux processus qui se terminent d'eux-mêmes. Couverture : 100 %.
13. 384 tests verts ; trois passages successifs des tests d'orchestration, identiques (environ 23 s, dont 9 s pour trois délais de 3 s).
14. Construction faite deux fois : fichiers identiques ; le wheel contient `_protocole.py`, `_orchestration/`, `_travail/`, `modules/` et le schéma des manifestes. Installé dans un environnement neuf : le processus de travail se lance depuis le wheel, rend l'empreinte attendue, et n'écrit aucun fichier `.pyc` (`_travail/` sans `__pycache__`, alors que les paquets importés par le processus principal en ont un) ; `vk --modules` répond. Étape correspondante ajoutée au job `paquet` de la CI.
15. Documentation : ADR-0060 à ADR-0066 ; renvois dans ADR-0011, ADR-0036, ADR-0042, ADR-0056, ADR-0059 ; architecture v1.3, modèle de données v1.1, glossaire v1.1, découpage v0.11 ; index des ADR et du journal.
16. Lint Markdown en local, vérification des fichiers interdits, commits ; branche poussée et PR [#10](https://github.com/TheDarkMac/AI-detector/pull/10) ouverte vers `detector`.
17. CI (lancement 40398924617, tête `eedc50e`) : Linux et macOS verts ; Windows en échec sur les trois versions de Python, 9 tests sur 384, tous dans `test_travail.py` (`OSError: [Errno 9] Bad file descriptor`). Les tests qui lancent un vrai processus de travail passent sous Windows : transmission du handle, lecture sans `pread` et environnement réduit à `SYSTEMROOT` fonctionnent. Défaut des tests : ils passaient à `--descripteur` un descripteur, alors que sous Windows le processus de travail attend un handle, ce que le principal envoie. Corrigé dans les tests.
18. Pendant la revue, TheDarkMac a validé ADR-0064 et ADR-0065 : statut « Accepté ». Il a demandé le merge de la PR une fois la CI verte.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Code du processus de travail non mesuré par la couverture | `patch = ["subprocess"]` transmet la mesure par l'environnement, que le lancement vide (ADR-0065) | Tests concernés lancés sous `coverage run --parallel-mode --rcfile=pyproject.toml` |
| `coverage combine` : « database disk image is malformed », puis aucun fichier combiné | Processus de travail arrêtés de force par le principal pendant qu'ils écrivaient leurs mesures | Mesure réservée aux processus qui se terminent d'eux-mêmes ; anciens fichiers supprimés |
| Fichiers de mesure corrompus encore présents au passage suivant | `rm .coverage.*` sous zsh : un motif sans correspondance annule toute la commande | `find . -maxdepth 1 -name '.coverage*' -delete` |
| Collision de nom dans un utilitaire de test (`identifiant` en position et en mot-clé) | Paramètre et champ du manifeste de même nom | Paramètre renommé |
| `RUF001` sur un séparateur de ligne Unicode littéral dans un test | Caractère ambigu dans le source | Écrit `chr(0x2028)` |
| 9 tests en échec sous Windows seulement (`Bad file descriptor`) | Les tests du processus de travail dans le processus des tests passaient un descripteur là où Windows attend un handle | Fonction `transmis` dans `test_travail.py`, qui passe le handle sous Windows comme le principal |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. Les écarts avec ADR-0036 (`-B`, sortie d'erreur, Job Object) sont des décisions nouvelles, consignées dans ADR-0065 et signalées dans l'historique d'ADR-0036.

## Écarts par rapport au découpage

- **Ajout** : message `module` dans le protocole (ADR-0062) et option `--modules` (ADR-0063).
- **Ajout** : délai global, bornes de taille et raisons `limite_depassee` et `delai_depasse`, avec des valeurs provisoires ; sans eux, la lecture de la sortie pouvait bloquer. T14 fixe les valeurs.
- **Reporté** à T13 : identification du format (aucun module n'est applicable d'ici là), transmission du format au principal, comparaison des empreintes, ouverture du fichier par le principal, interface publique `analyser`, option de désactivation de la commande d'analyse.
- **Reporté** à T14 : Job Object sous Windows (ADR-0035, ADR-0065), restrictions du processus de travail ; d'ici là, il annonce une isolation réduite où tout manque.
- **Reporté** à T15 : techniques hors V1 par format (`hors_v1`), existence des règles citées par les manifestes.
- **Reporté** au premier module qui emploie une bibliothèque : versions des bibliothèques au manifeste et au message `versions`, vide en T12.

## Résultat

- Moteur de modules : manifestes validés et ordonnés, désactivation avec propagation aux modules dépendants, processus de travail neuf par fichier, protocole contrôlé message par message, couverture et analyses non menées conformes au modèle de données, y compris après un arrêt.
- Aucun module livré : `vk --modules` le dit, et la couverture d'un rapport est vide jusqu'à T13.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent (384 tests, couverture 100 %) ; construction reproductible ; processus de travail lancé depuis le wheel installé.

## Reste à faire

- T13 : identification et transmission du format, comparaison des empreintes, ouverture du fichier, commande d'analyse avec `--desactiver`, interface publique ; retirer le test « aucun module livré en T12 » avec le premier module.
- T14 : restrictions et Job Object (lanceur de l'environnement virtuel compris), valeurs des tailles et du délai ; mesure du coût de démarrage (0,35 s ici, sans module).
- T15 : catalogue dans la configuration, règles citées par les manifestes, techniques hors V1.
- T53 : acheminement entre modules et constat citant les observations d'un autre module (ADR-0061).
- Toujours en attente : éditeur de confiance PyPI et `LICENSE` (TheDarkMac, @Jean) ; messages à @Jean ; Dependabot à observer ; alertes de sécurité de Dependabot à proposer.
