# T15 — Catalogue de règles versionné et daté

- **Branche** : `tache/T15-catalogue-de-regles`
- **Dates** : 2026-10-27 → 2026-10-27
- **Exigences couvertes** : F-26, NF-06, NF-07 ; ES-09 ; F-81 (direction par règle), F-82 (`hors_v1`) ; A-23, A-32, A-37, A-47
- **Décisions** : ADR-0084 à ADR-0090
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : catalogue de règles versionné et daté, séparé du moteur, avec schéma de validation, livré avec l'outil, version et empreinte au rapport (ADR-0029) ; fichiers TOML et JSON Schema (ADR-0038), expressions RE2 (ADR-0039). S'y ajoutaient les points laissés à T15 : règles citées par les manifestes et leurs directions (ADR-0064), liste des techniques hors V1 par format (ADR-0059, architecture §12), contenu du catalogue (A-37), identifiants de règle (A-47), listes de référence (A-32), empreinte du catalogue dans la release (ADR-0041).

## État initial

- PR [#14](https://github.com/TheDarkMac/AI-detector/pull/14) (T14) : CI verte sur `7f73e06` (code 40455310503, 15 vérifications, test du lanceur de Windows exécuté, étape 20 du journal de T14) puis sur `238b1a6` (code 40456086595, docs 40456086612 ; 15 vérifications, CodeRabbit « skipped »), après la validation d'ADR-0078 à ADR-0081 et ADR-0083 (commit `238b1a6`, étape 21 du journal de T14). Description de la PR mise à jour par l'API REST.
- Mergée le 2026-10-27 à 05:37:44 UTC à la demande explicite de TheDarkMac (« merge la PR #14 une fois la CI verte ») : `gh pr merge 14 --merge --subject "Merge: T14 — Sécurité d'exécution (#14)"`. Commit de merge `273c88b`, à l'adresse noreply (ADR-0007). Lancements de push sur `273c88b` : `docs` 40456401668 et `code` 40456401652, réussis. La ligne de T14 dans l'index du journal portait « à venir » : corrigée en #14 dans cette tâche.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`273c88b`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : T15 dépend de T11 et T12, mergées ; aucun module n'est livré, le catalogue livré sera donc vide de règles. Lecture du découpage, des journaux de T13 et T14, d'ADR-0012, ADR-0016, ADR-0018, ADR-0019, ADR-0029, ADR-0038, ADR-0039, ADR-0059, ADR-0061, ADR-0064, de l'architecture (§4, §6, §8, §12), du modèle de données, et du code des manifestes, de l'orchestration, du contexte et du déroulé du travail.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation ; les quatre recommandations ont été suivies, sans raison supplémentaire :
   - langage des règles : conditions fermées, toutes requises, et règles appliquées par un module ([ADR-0084](../decisions/ADR-0084-langage-des-regles.md)) ;
   - numérotation : version propre au catalogue et registre vérifié ([ADR-0085](../decisions/ADR-0085-version-date-et-registre-du-catalogue.md)) ;
   - catalogue fourni par l'utilisateur : il remplace le catalogue livré ([ADR-0086](../decisions/ADR-0086-catalogue-fourni-par-l-utilisateur.md)) ;
   - techniques hors V1 : données de l'outil, hors du catalogue ([ADR-0087](../decisions/ADR-0087-techniques-hors-v1.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0088](../decisions/ADR-0088-fichiers-et-empreinte-du-catalogue.md) (fichiers, empreinte, limites), [ADR-0089](../decisions/ADR-0089-motifs-re2-et-evaluation.md) (motifs RE2 et évaluation), [ADR-0090](../decisions/ADR-0090-constat-d-une-regle.md) (constat d'une règle).
3. Branche `tache/T15-catalogue-de-regles` créée depuis `detector` à jour (`273c88b`) ; 692 tests verts au départ, un sauté (lanceur de Windows).
4. `google-re2` ajouté (`uv add "google-re2>=1.1.20251105"`) : version 1.1.20251105, publiée le 2025-11-05, donc depuis plus de 7 jours (ADR-0052). Essais de l'interface : références arrière et assertions de contexte refusées à la compilation ; taille du programme compilé mesurable (`programsize`) ; erreurs journalisées sur la sortie d'erreur par défaut (voir ci-dessous).
5. `_limites.py` : limites du catalogue. `_regles.py` : conditions, règles, compilation des motifs, évaluation, conformité d'un constat à sa règle.
6. Schémas `catalogue` (en-tête), `regles` (fichier de règles), `hors_v1` ; liste `modules/hors_v1.toml` (16 techniques) et son chargement dans `manifestes.py`.
7. `_orchestration/catalogue.py` : lecture bornée, structure du dossier, schémas, règles, cohérence avec les manifestes, empreinte. Catalogue livré 0.1.0 du 2026-10-27, en-tête seul : l'empreinte calculée par le code (`39835180…7356d87`) est celle que donne la commande publiée (`find … | sha256sum`). `.gitattributes` empêche la conversion des fins de ligne de ces fichiers.
8. Processus de travail : le contexte reçoit les règles de son module, `constater` cite une règle par son identifiant, le moteur applique les règles « moteur » après le module. Processus principal : règles des modules actifs dans la configuration, constat refusé s'il n'est pas conforme à sa règle ; la soumission ajoute la version du catalogue et les techniques hors V1 ; `analyser(catalogue=…)`, `vk --catalogue`, `vk --regles`.
9. Premier passage de toute la suite : 9 échecs, tous attendus des tests à adapter (couverture qui contient désormais les techniques hors V1, configuration sans `regles`, constat du factice citant une règle absente du catalogue), sauf un : la couverture d'un polyglotte refusée par le modèle (voir ci-dessous).
10. Tests ajoutés : `test_regles.py`, `test_catalogue.py`, cas nouveaux dans `test_travail.py`, `test_orchestration.py` (trois constats non conformes du factice), `test_soumission.py`, `test_cli.py`, `test_manifestes.py`, `test_modele.py` ; aide commune `tests/catalogues.py`.
11. CI : script `.github/scripts/catalogue.py` (bibliothèque standard seule) avec deux commandes : `base` compare le registre et les règles à la branche cible (job `qualite`, historique complet) ; `paquet` recalcule le catalogue d'un wheel sans l'installer (jobs `paquet` et `construction` de la publication, qui joint `CATALOGUE.txt` à la release). Essai local : wheel construit avec les contraintes épinglées, il contient `donnees/catalogue/catalogue.toml` et `modules/hors_v1.toml` ; `paquet` y retrouve l'empreinte du registre ; `base origin/detector` passe (pas encore de registre sur `detector`).
12. Mesures sur le poste : catalogue livré chargé en 1,4 ms (médiane de 50) ; 1 000 règles à motif construites en 144 ms ; import de RE2, 20 ms.
13. Vérification locale : `uv lock --check` ; pip-audit, aucune faille connue ; 819 tests verts, un sauté (lanceur de Windows), couverture 100 % lignes et branches ; Ruff et mypy sans remarque. Exemples TOML du guide du catalogue validés par les schémas et le modèle.
14. Documentation : ADR-0084 à ADR-0090 ; renvois dans ADR-0012, ADR-0016, ADR-0018, ADR-0019, ADR-0029, ADR-0038, ADR-0039, ADR-0041, ADR-0043, ADR-0059, ADR-0061, ADR-0064 ; guide [`docs/catalogue/`](../catalogue/README.md) et registre des versions ; architecture v1.8, modèle de données v1.4, glossaire v1.4, découpage v0.14, registre des arbitrages v1.7 ; `README.md`, `CONTRIBUTING.md` (§5, §8, §9), `docs/README.md` ; index des ADR et du journal.
15. Lint Markdown en local (`npx --yes markdownlint-cli2@0.23.2`) ; aucun fichier interdit suivi. Commits, branche poussée, PR ouverte vers `detector`.

### Critères d'admission de `google-re2` (ADR-0043)

| Critère | Constat pour 1.1.20251105 |
| --- | --- |
| Licence compatible, sans copyleft fort | BSD (classificateur ; RE2 est sous BSD-3-Clause) |
| Maintenue | Versions de juillet, août et novembre 2025, publiées par le projet RE2 |
| Aucun accès réseau | Aucun : bibliothèque de calcul |
| Exécutée dans le processus de travail si elle lit le fichier | Les motifs ne s'appliquent qu'aux observations, dans le processus de travail ; le principal ne fait que compiler ceux du catalogue (ADR-0039) |
| Arbre de dépendances | Aucune dépendance |
| Paquets précompilés | Python 3.10 à 3.14, Linux, macOS, Windows (examen de T10) ; confirmé par la CI des trois systèmes |
| Failles connues | Aucune (pip-audit) |

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Un motif refusé écrivait sur la sortie d'erreur | RE2 journalise ses erreurs de compilation par défaut (`log_errors`) | Option désactivée ; test qui lance un interpréteur et vérifie que la sortie d'erreur reste vide |
| mypy : « missing library stubs » pour `re2` | `google-re2` ne publie pas ses types | `ignore_missing_imports` pour `re2` seulement, avec commentaire dans `pyproject.toml` |
| Couverture d'un polyglotte refusée (« une entrée par technique et par partie analysée ») | Une technique figure pour chaque partie analysée ; une technique hors V1 ne s'applique pas à toutes, et le modèle n'admettait sans version que l'état « non menée » | ADR-0087 : non applicable sans version sur les autres parties ; modèle et schéma du rapport ajustés, règle 4 d'ADR-0059 précisée |
| Techniques hors V1 sans rapport avec le fichier | Première version : chaque technique inscrite sur toutes les parties | Seules celles qui s'appliquent à une partie analysée figurent (ADR-0087) |
| Test « programme trop grand » en échec | `\pL{1000}` dépasse la mémoire de RE2 avant d'atteindre la borne du programme | Deux cas : `\pL{5}` (5 984 instructions) pour la borne, `\pL{1000}` refusé par RE2 |
| Test « règle d'un autre module » mal écrit | La règle du cas portait le module de son fichier | Cas corrigé : règle d'`alpha` dans `regles/beta.toml` |
| Empreinte différente possible sous Windows | La CI Windows convertit les fins de ligne à l'extraction | Prévenu : `.gitattributes` (`-text`) sur le dossier du catalogue (ADR-0088) |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. La règle 4 d'ADR-0059, écrite avant les parties (T13), ne prévoyait pas un polyglotte ; elle est précisée par ADR-0087 et l'historique d'ADR-0059.

## Écarts par rapport au découpage

- **Écart avec ADR-0012** : la liste des techniques hors V1 n'est pas dans le catalogue mais dans `modules/hors_v1.toml` (ADR-0087).
- **Écart avec ADR-0061** : nouvelle signature de `constater` (ADR-0090) ; aucun module livré n'était à adapter.
- **Écart avec l'architecture** : `_regles.py` est un fichier, non un dossier `_regles/` (§4, corrigé).
- **Ajout** : `vk --regles` (NF-07, consultable) ; contrôle de conformité des constats par le principal (ADR-0090) ; registre des versions et contrôles de la CI (ADR-0085).
- **Non fait** : aucune règle livrée, faute de module ; marquages recherchés (F-25) dans le catalogue, laissés à T31 ; comparaison de deux observations, laissée à T23 (ADR-0084).
- **Modèle de menace inchangé** : ES-09 est réalisée par ces ADR, sans menace nouvelle ; RR-01 est réduit sans être levé (ADR-0090).

## Résultat

- Catalogue livré 0.1.0 du 2026-10-27, validé au chargement, version, date et empreinte jointes à chaque analyse et affichées par `vk --regles`.
- Règles « moteur » écrites en TOML, évaluées par RE2 dans le processus de travail ; règles « module » citées par leur identifiant ; tout constat contrôlé contre sa règle par le processus principal.
- Catalogue fourni par l'utilisateur (`--catalogue`), validé de la même façon et signalé.
- Techniques hors V1 inscrites à la couverture, non menées (`hors_v1`) ou non applicables.
- Registre des versions vérifié par les tests et la CI ; catalogue joint à la release.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent (819 tests, couverture 100 %).

## Reste à faire

- T16 : lire dans le catalogue le titre, les limites et l'évaluation de chaque règle citée ; mettre en évidence un catalogue fourni par l'utilisateur ; gabarits des phrases.
- T20, T22 : premiers modules et premières règles, avec une nouvelle version du catalogue.
- T23 : comparaison de deux observations (ADR-0084). T31 : marquages recherchés. T30 : format de la liste de confiance.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
