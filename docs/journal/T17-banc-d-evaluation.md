# T17 — Banc d'évaluation

- **Branche** : `tache/T17-banc-d-evaluation`
- **Dates** : 2026-10-28
- **Exigences couvertes** : §8 du cahier, NF-09 ; ES-11, ES-22 (partie banc), NF-16 (vérification) ; A-07, A-08, A-11, A-27, A-52, A-54, A-55, A-58
- **Décisions** : ADR-0099 à ADR-0107
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : corpus séparé calibrage / évaluation (ADR-0016), calcul des faux positifs, faux négatifs et non analysables par technique et catégorie, taux de faux positifs par fichier et bornes des niveaux d'indice (ADR-0018) ; matrice exigence → méthode de vérification → résultat (ADR-0024), exigences ES comprises ; analyse exécutée sans réseau (ES-11). S'y ajoutaient les constats de l'analyse adressés à T17 : taux par fichier (A-07), méthode par exigence (A-08), principes numérotés (A-11), cas d'usage reliés (A-27), vérification de NF-16 (A-52), effectif et intervalle (A-54), contrôles déterministes (A-55), matrice livrée (A-58).

## État initial

- PR [#16](https://github.com/TheDarkMac/AI-detector/pull/16) (T16). Déjà consigné dans le journal de T16 (étapes 17 et 18) : ADR-0095 à ADR-0098 acceptés (`c48be5d`), échec de la CI sous Windows sur `c95b774` corrigé par `653d680`.
- CI sur `c48be5d` : code 40621272454, en échec sous Windows seulement (les deux mêmes tests du résumé, le commit précédait le correctif) ; docs 40621272629 verte.
- CI sur `653d680` verte : code 40621637450, docs 40621637491 ; 15 vérifications, CodeRabbit « skipped » ; vérifiée avant le merge (`code-ok` revérifié une fois terminé).
- Mergée le 2026-10-28 à 02:36:35 UTC à la demande explicite de TheDarkMac (« La CI de la PR #16 sur 653d680 devrait être finie : vérifie-la, puis merge avec le titre … si elle est verte ») : `gh pr merge 16 --merge --subject "Merge: T16 — Génération du rapport (#16)"`. Commit de merge `3830b18`, à l'adresse noreply (ADR-0007). Lancements de push sur `3830b18` : docs 40621946393 réussi ; code 40621946233, encore en attente au moment du merge, réussi à 02:39:39 UTC. La ligne de T16 dans l'index du journal portait « à venir » : corrigée en #16 dans cette tâche.
- `gh pr edit` échoue (abandon des Projects classiques dans l'API GraphQL) : le corps d'une PR se met à jour par `gh api -X PATCH repos/TheDarkMac/AI-detector/pulls/N -F body=@fichier`.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`3830b18`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : T17 dépend de T11 à T16, mergées. Aucun module d'analyse n'est livré : le banc ne peut encore mesurer aucune technique ; il est éprouvé sur des résultats construits à la main, sur une analyse factice, et de bout en bout sur un corpus d'essai. Lecture du découpage, du journal de T16, d'ADR-0016, ADR-0018, ADR-0024, ADR-0036, ADR-0083, des §2, §4, §5, §7 et §8 du cahier, des constats A-07 à A-12, A-27, A-52 à A-58 de l'analyse, des exigences ES et de l'inventaire des requêtes du modèle de menace, de l'architecture, du registre des arbitrages (reformulations), du modèle, de l'analyse, des règles, des tests et de la CI. Vérifié que `unshare -rn` fonctionne sur le poste (connexion : « Network is unreachable »).
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation. La session s'est coupée avant la réponse ; les questions ont été reposées à l'identique. Les quatre recommandations ont été suivies, sans raison supplémentaire :
   - forme du banc : outil du dépôt, hors du paquet ([ADR-0099](../decisions/ADR-0099-banc-outil-du-depot.md)) ;
   - sans réseau : espace de noms réseau vide et crochet d'audit ([ADR-0100](../decisions/ADR-0100-evaluation-sans-reseau.md)) ;
   - bornes : 1 % et 5 % sur la borne supérieure de l'intervalle de Wilson, cible par fichier 5 % ([ADR-0101](../decisions/ADR-0101-bornes-des-niveaux-et-cible.md)) ;
   - matrice : marqueurs pytest et fichier TOML, rendu vérifié ([ADR-0102](../decisions/ADR-0102-matrice-de-verification.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0103](../decisions/ADR-0103-manifeste-du-corpus.md) (manifeste du corpus), [ADR-0104](../decisions/ADR-0104-definition-des-mesures.md) (définition des mesures), [ADR-0105](../decisions/ADR-0105-rapport-d-evaluation-et-corpus-d-essai.md) (rapport, codes de sortie, corpus d'essai), [ADR-0106](../decisions/ADR-0106-contenu-et-controles-de-la-matrice.md) (contenu et contrôles de la matrice), [ADR-0107](../decisions/ADR-0107-effectif-et-borne-dans-l-evaluation.md) (effectif et borne au catalogue).
3. Branche `tache/T17-banc-d-evaluation` créée depuis `detector` à jour (`3830b18`).
4. Paquet : l'évaluation d'une règle porte `effectif` et `borne_superieure` (schéma `regles`, classe `Evaluation`) ; `BORNE_FORT`, `BORNE_MODERE` et `niveau_permis` dans `_regles.py` ; une règle dont le niveau dépasse ce que permet sa borne est refusée ; le rapport cite l'effectif et la borne (`rapport/textes.toml`, `_presentation.py`). Tests de `test_regles.py` et `test_rapport.py` adaptés, bornes testées à leurs limites.
5. Banc : `banc/corpus.py` et `banc/corpus.schema.json` (manifeste, groupes, empreintes) ; `banc/reseau.py` (interfaces lues dans `/proc/self/net/dev`, crochet d'audit) ; `banc/mesures.py` (taux, intervalle de Wilson) ; `banc/evaluation.py` (analyse du corpus, mesures, écarts) ; `banc/sortie.py` (JSON, Markdown, écriture sans écraser) ; `banc/cli.py` et `banc/__main__.py`. `pyproject.toml` : `banc` dans le chemin d'import des tests, mypy et la couverture.
6. Corpus d'essai `banc/essai/` : neuf fichiers fabriqués à partir des échantillons des tests (texte, PDF, JPEG, PNG ; un PNG « généré », un JPEG « transformé » par messagerie, un PDF « retouché », un PDF tronqué et un fichier vide « malformés ») ; empreintes inscrites au manifeste ; `.gitattributes` empêche toute conversion de fin de ligne. Essai : sans espace de noms, refus (code 2, dix-huit interfaces du poste citées) ; sous `unshare -rn`, évaluation menée (code 1), seul écart la cible par fichier, que quatre authentiques ne peuvent pas établir (borne supérieure 49,0 %) ; le PDF tronqué est analysé, le fichier vide refusé.
7. Matrice : `docs/verification/matrice.toml` (95 exigences : 48 F, 19 NF, 22 ES, 6 principes ; 5 cas d'usage), `banc/matrice.py` (sources des exigences, collecte des tests, contrôles, rendu, résultats JUnit), contrôle des marqueurs dans `tests/conftest.py`, marqueur déclaré dans `pyproject.toml`. Marqueurs posés sur les seize fichiers de tests existants (sujet principal par `pytestmark`, exigences annexes par test). `matrice.md` généré : 35 exigences réalisées, 15 partielles, 28 à venir, 17 hors V1.
8. Tests : `tests/test_banc.py` (taux et intervalles, manifeste et ses refus, groupes, fichier modifié, lien hors du corpus, interfaces, crochet, mesures sur des résultats construits, analyse d'un corpus avec refus, arrêt brutal et tentative de réseau, rapport JSON et Markdown, commande et ses codes, banc complet sous `unshare -rn`, refus avec le réseau) ; `tests/test_matrice.py` (matrice du dépôt à jour par `--verifier`, sources, chaque contrôle, rendu, résultats JUnit, collecte, commande, marqueurs refusés).
9. CI : job `tests`, espaces de noms permis sous Linux, rapport JUnit, matrice remplie jointe en artefact (`actions/upload-artifact` v7.0.2, épinglé par empreinte de commit, publié le 2026-10-07) ; job `paquet`, étape « Banc d'évaluation sans réseau depuis le wheel (T17) » : refus avec le réseau, corpus d'essai évalué sous `unshare -rn`, code et écarts vérifiés. Étape répétée en local sur un wheel construit avec les contraintes épinglées ; vérifié que ni le wheel ni le paquet source ne contiennent `banc/`.
10. Relecture : les règles d'un module désactivé auraient été mesurées sur zéro fichier, donc signalées à tort ; elles sont exclues des mesures (ADR-0104).
11. Vérification locale : `uv lock --check` ; Ruff (format et analyse) et mypy sans remarque ; pip-audit, aucune faille connue ; matrice vérifiée ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans remarque ; 977 tests verts, un sauté (lanceur de Windows), couverture 100 % lignes et branches. Un premier passage, lancé pendant que le code changeait encore, donnait 99 % ; relancé seul sur l'état final, 100 %.
12. Documentation : ADR-0099 à ADR-0107 ; renvois dans ADR-0016, ADR-0018, ADR-0024, ADR-0027, ADR-0083, ADR-0084, ADR-0086 ; découpage v0.16, architecture v1.10, modèle de menace v1.2, registre des arbitrages v1.9, guide du catalogue v1.2, glossaire v1.6 ; `docs/verification/README.md` ; `CONTRIBUTING.md` (§1, §5), `docs/README.md` ; index des ADR et du journal.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| La session s'est coupée pendant les questions | Interruption de la session | Questions reposées à l'identique ; réponses consignées à l'étape 2 |
| `/sys/class/net` ne convient pas pour savoir si le banc a le réseau | Il montre les interfaces de l'espace de noms qui a monté `/sys`, pas celui du processus | Lecture de `/proc/self/net/dev`, propre à l'espace de noms réseau du processus, sans socket |
| Trois lignes du crochet d'audit hors de la mesure de couverture | Python exécute les crochets d'audit sans traçage | `pragma: no cover` avec la raison ; effet vérifié par `test_crochet_refuse_et_note` et `test_commande_tentative_de_reseau` |
| Une `ReseauInterdit` levée sans événement noté aurait laissé la commande sans résultat | Cas impossible par le crochet, possible par une bibliothèque qui la lèverait elle-même | La commande rend le code 3 dans les deux cas, et cite l'exception si aucun événement n'est noté |
| Une analyse factice « partielle » refusée par le modèle | Une technique partielle exige une analyse non menée qui l'explique | Le test ajoute `format_partiel` pour une technique partielle, `erreur_module` pour une non menée |
| Cellules vides de la matrice refusées par le lint Markdown (MD060) | « `\|  \|` » n'a pas le style de tableau attendu | Remarque vide rendue « — » |
| Le corpus d'essai ne peut pas atteindre la cible par fichier | Il faudrait 73 authentiques sans faux positif (ADR-0101) | Code 1 attendu par la CI, avec cet unique écart ; le chemin du code 0 est testé avec 73 fichiers et une analyse factice |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum.

## Écarts par rapport au découpage

- **Écart avec ADR-0084** : l'évaluation d'une règle porte en plus l'effectif et la borne supérieure, et le niveau est contrôlé au chargement (ADR-0107) ; le `format` du catalogue reste 1, aucune règle n'ayant d'évaluation et aucune version publiée n'ayant lu de règle.
- **Ajout** : texte « evaluee » des règles au rapport, validé en T16, changé pour citer l'effectif et la borne ; confusions entre génération et retouche comptées par technique ; arrêts brutaux comptés sur tout le corpus ; corpus d'essai dans le dépôt.
- **Non fait** : aucune technique n'est mesurée (aucun module livré) ; le corpus de référence et la publication des taux restent à T100 et T101 ; NF-06 et P-05 attendent le test de reproductibilité (T18).
- **Modèle de menace** : ES-11 réalisée par ADR-0100, sans menace nouvelle.

## Résultat

- `unshare -rn python -m banc CORPUS --sortie DOSSIER` analyse une partie du corpus sans réseau et écrit `evaluation.json` et `evaluation.md` : taux par technique et catégorie, par règle, par fichier, chacun avec son effectif et son intervalle de Wilson, et les écarts ; codes 0 à 3.
- Le catalogue refuse un niveau que son évaluation ne permet pas.
- `docs/verification/matrice.md` relie les 95 exigences à leur état, leurs méthodes et leur résultat ; tout écart fait échouer les tests ; la CI joint la matrice remplie.

## Reste à faire

- T18 : reproductibilité.
- T100 : corpus de référence, avec son manifeste ; T101 : rapports d'évaluation publiés.
- Chaque tâche suivante : marqueurs et états de la matrice à jour dans sa PR.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
