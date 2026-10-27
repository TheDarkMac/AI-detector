# T14 — Sécurité d'exécution

- **Branche** : `tache/T14-securite-d-execution`
- **Dates** : 2026-10-27 → 2026-10-27
- **Exigences couvertes** : NF-01, NF-02, NF-03, NF-08, F-04 ; ES-02, ES-03, ES-11 (mesure de l'isolation), ES-15, ES-19 (identification et protocole) ; A-05, A-53
- **Décisions** : ADR-0076 à ADR-0083
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : limites de taille, de temps et de mémoire, bombes de décompression, processus restreint par fichier (ADR-0028), mécanismes par système (ADR-0035) dont le Job Object sous Windows, lanceur de l'environnement virtuel compris (ADR-0065), valeurs des limites et du délai provisoires de T12, aucune trace sur le poste (ES-15), fuzzing des analyseurs (ES-19) dont l'identification (ADR-0070), rapport partiel en cas d'échec, refus « hors limites » (F-04, ADR-0075). S'y ajoutaient le choix laissé par ADR-0023 (budget de travail) et la mesure du coût de démarrage du processus de travail (ADR-0036).

## État initial

- PR [#13](https://github.com/TheDarkMac/AI-detector/pull/13) (T13) : CI verte sur `9264da4` (docs 40448587342, code 40448587400) et sur `8420b5d` (docs 40448744722, code 40448744629 ; 15 vérifications, CodeRabbit « skipped »). Pendant la revue, TheDarkMac a validé ADR-0070 et ADR-0075 : statut « Accepté » (commit `8420b5d`, étape 15 du journal de T13, description de la PR mise à jour).
- Mergée le 2026-10-27 à 04:25:09 UTC à la demande explicite de TheDarkMac (« Merge la PR #13 une fois la CI verte ») : `gh pr merge 13 --merge --subject "Merge: T13 — Soumission et identification (#13)"`. Commit de merge `7bc863b`, à l'adresse noreply (ADR-0007). Lancements de push sur `7bc863b` : `docs` 40449626709 et `code` 40449626819, réussis. La ligne de T13 dans l'index du journal portait « à venir » : corrigée en #13 dans cette tâche.
- Rappel de T13 : pour ADR-0071, TheDarkMac a retenu l'analyse de chaque format d'un polyglotte, contre la recommandation de l'assistant (format principal seul).
- Toujours en attente : messages à @Jean ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`7bc863b`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : T14 dépend de T12 et T13, mergées. Le noyau du poste (6.12) offre Landlock ABI 6. Lecture du découpage, des journaux de T12 et T13, d'ADR-0023, ADR-0028, ADR-0035, ADR-0036, ADR-0056, ADR-0065, ADR-0075, du modèle de menace (ES-02, ES-03, ES-15, ES-19) et du code du processus de travail et de l'orchestration.
2. Vérification préalable : sans mesure de couverture dans les processus lancés, seuls `__main__.py` et la réservation de la sortie (`canal_du_protocole`) n'étaient couverts que par eux. Un processus restreint ne pouvant plus écrire ses mesures, la conception en tient compte (ADR-0083).
3. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation ; les quatre recommandations ont été suivies, sans raison supplémentaire :
   - budget de travail (ADR-0023) : mixte ([ADR-0076](../decisions/ADR-0076-limites-comptees-et-limites-du-systeme.md)) ;
   - valeurs : modérées, 1 Gio, 2 Gio, 120 s ([ADR-0077](../decisions/ADR-0077-valeurs-des-limites.md)) ;
   - réglage : fixes en V1 (ADR-0077) ;
   - fuzzing : Hypothesis ([ADR-0082](../decisions/ADR-0082-fuzzing-par-hypothesis.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0078](../decisions/ADR-0078-budget-d-un-module-et-raisons.md) (budget et raisons), [ADR-0079](../decisions/ADR-0079-restrictions-sous-linux.md) (Linux), [ADR-0080](../decisions/ADR-0080-restrictions-sous-macos.md) (macOS), [ADR-0081](../decisions/ADR-0081-restrictions-sous-windows.md) (Windows), [ADR-0083](../decisions/ADR-0083-verification-de-l-isolation.md) (vérification).
4. Branche `tache/T14-securite-d-execution` créée depuis `detector` à jour (`7bc863b`) ; 626 tests verts au départ, couverture 100 %.
5. `_limites.py` : toutes les valeurs, lues par les deux processus ; `_protocole.py` y prend ses tailles.
6. Contexte d'un module : budget compté (`compter_objets`, `verifier_dimensions`, `imbrication`, `compter_decompression`, `decompresser`). Le processus de travail rend `MemoryError` en non menée plutôt qu'en erreur du module.
7. Restrictions sous Linux (`_travail/restrictions/linux.py`) : limites de ressources, `no_new_privs`, Landlock sans règle, filtre seccomp. Essai manuel dans un interpréteur restreint : isolation complète ; lecture, écriture, `socket`, `socketpair`, `execv`, `subprocess`, `listdir`, signal au processus 1 refusés (`PermissionError`), allocation de 3 Gio refusée (`MemoryError`).
8. En relisant l'identification : le décodeur UTF-16 était cherché au premier fichier texte, donc chargé depuis le disque après les restrictions. Décodeurs désormais cherchés à l'import.
9. Branchement dans le déroulé : restricteur injectable (`restreindre`), comme l'identification. Premier passage des tests : un test du déroulé dans le processus des tests a verrouillé pytest lui-même (voir ci-dessous).
10. Processus principal : refus `hors_limites` avant toute lecture, délai de 120 s, arrêt par `SIGXCPU` compté comme délai dépassé, surveillance de la mémoire sous macOS (`_orchestration/surveillance.py`).
11. Restrictions sous macOS (Seatbelt) et Windows (Job Object, niveau d'intégrité bas, `SetErrorMode`), écrites sans pouvoir les essayer sur le poste : vérifiées par la CI.
12. Test de la mémoire : `limite_depassee` y rendait l'analyse interrompue, alors qu'ADR-0076 garde dans la garantie ce qui est compté. Raison `memoire_depassee` ajoutée, `limite_depassee` retirée des raisons qui interrompent, ligne ou sortie trop longue reçue par le principal passée à `message_invalide` (ADR-0078).
13. Hypothesis ajouté au groupe `dev` : `uv add` a d'abord pris la 6.170.12, publiée la veille ; ramené à la 6.170.4, publiée depuis plus de 7 jours, comme le veut ADR-0052 (`uv lock --upgrade-package "hypothesis==6.170.4"`).
14. Tests : `test_isolation.py` (effet depuis un module, fonctions pures, programme seccomp interprété), `test_limites.py`, `test_traces.py` (ES-15), `test_fuzzing.py`, `systeme.py` ; factice complété (`sonde`, `memoire`, `temps_processeur`, `ferme_trop_tot`, `--sans-restriction`). Le fuzzing a d'abord échoué sur une erreur de la stratégie de test (voir ci-dessous).
15. Mesures sur le poste : analyse d'un petit PDF par un vrai processus de travail, restrictions comprises, 0,35 s en médiane sur 15 essais (0,32 à 0,40 s), comme en T12 ; application des restrictions : 14 à 19 ms ; import du paquet par le processus de travail : 170 à 200 ms. Validation d'un message par le schéma dans le principal : 1,4 à 1,7 ms.
16. Vérification locale : 692 tests verts, un sauté (lanceur de Windows), couverture 100 % lignes et branches ; Ruff et mypy sans remarque. Commit du code, branche poussée, CI lancée sur la branche par `workflow_dispatch` (lancement 40453990734) : Linux et Windows verts ; macOS en échec sur un seul point, la création d'une socket (voir ci-dessous). Test adapté, renvois aux ADR renumérotés ; second lancement 40454391963 : tout vert.
17. Le test du lanceur de Windows saute désormais explicitement si `sys.executable` n'est pas un lanceur, pour que le journal de la CI dise s'il a vraiment porté.
18. Documentation : ADR-0076 à ADR-0083 ; renvois dans ADR-0023, ADR-0028, ADR-0035, ADR-0036, ADR-0048, ADR-0054, ADR-0056, ADR-0061, ADR-0065, ADR-0075 ; architecture v1.7, modèle de données v1.3, glossaire v1.3, découpage v0.13, registre des arbitrages v1.6 ; `README.md`, `CONTRIBUTING.md`, `.gitignore` ; index des ADR et du journal.
19. Lint Markdown en local (`npx --yes markdownlint-cli2@0.23.2`) : aucune remarque ; aucun fichier interdit suivi. Commits, branche poussée, PR ouverte vers `detector`.
20. CI de la PR (lancement `code` 40455310503) : verte sur les 15 vérifications. Sous Windows, le test du lanceur a été exécuté, pas sauté, sur Python 3.12 à 3.14 : `sys.executable` y est un lanceur, et son arrêt arrête le véritable interpréteur (ADR-0081).
21. Pendant la revue, TheDarkMac a validé ADR-0078, ADR-0079, ADR-0080, ADR-0081 et ADR-0083 : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| `PermissionError` dans pytest lui-même, à la fin de la session | Deux tests appelaient le déroulé dans le processus des tests, avec les vraies restrictions par défaut : pytest s'est verrouillé | Restricteur factice passé à ces appels ; garde-fou `test_rien_n_est_restreint_dans_le_processus_des_tests` |
| Trois tests sous coverage en échec (`arret_processus`) | Le processus de travail mesuré ne pouvait plus écrire ses mesures après les restrictions | Factice lancé avec `--sans-restriction` sous coverage ; point d'entrée mesuré par un lancement arrêté avant les restrictions (ADR-0083) |
| Décodeur UTF-16 chargé à la demande | `codecs.getincrementaldecoder` cherche le codec au premier appel | Décodeurs cherchés à l'import de l'identification |
| `limite_depassee` rendait l'analyse interrompue | ADR-0056 classait cette raison parmi celles qui interrompent | ADR-0078 : raison `memoire_depassee`, `limite_depassee` n'interrompt plus |
| Arrêt par `SIGXCPU` lu comme un arrêt anormal | Le flux se ferme avant la fin : l'arrêt était constaté sans lire le code de sortie | Le principal attend la fin du processus (au plus 5 s) et lit son code ; test `ferme_trop_tot` pour le cas où il ne se termine pas |
| Fuzzing en échec : `ValueError: Out of range float values` | Stratégie JSON du test autorisant les infinis, que l'encodeur refuse à juste titre | `allow_infinity=False` dans la stratégie ; le code était juste |
| mypy : `WinDLL` inconnu | mypy tourne sous Linux, où `ctypes.WinDLL` n'existe pas | Fonction `_bibliotheque` unique, avec un `type: ignore` justifié |
| Tests de `linux.py` impossibles sous Windows | `import resource` en tête du module | `resource` importé dans les fonctions qui s'exécutent dans le travail ; limites de ressources mises en commun dans `posix.py` |
| CI macOS : `socket` « permise » | Seatbelt laisse créer une socket et refuse la connexion | Attente du test adaptée ; écart noté dans ADR-0080 et ADR-0035 |
| Fuzzing lent (35 s) | Validation par schéma d'environ 1,5 ms par message, génération récursive | Stratégies allégées (24 s) ; coût de la validation transmis à T20 |
| Lint Markdown d'abord lancé avec markdownlint-cli2 0.18.1 | Version reprise de mémoire, au lieu de celle de `CONTRIBUTING.md` (même erreur qu'en T00) | Relancé avec 0.23.2, version de l'action CI : aucune remarque |
| Modèle de données §5 : tableau des raisons coupé | Paragraphe inséré au milieu du tableau en T13 | Paragraphe déplacé après le tableau (correction de forme) |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. Le changement de sens de `limite_depassee` découle du choix d'ADR-0076 et suit la règle d'ADR-0056, qui ne retient comme interruptives que les raisons dépendant de la machine ; il est consigné dans ADR-0078 et l'historique d'ADR-0056.

## Écarts par rapport au découpage

- **Ajout** : raison `memoire_depassee` (ADR-0078) ; fonction de décompression bornée dans le contexte.
- **Écart avec l'architecture** : restrictions dans `_travail/restrictions/` plutôt que dans `_isolation/` (§4) ; elles appartiennent au processus de travail, qui les importe seul.
- **Écart avec ADR-0065** : les limites ne passent pas par la configuration (ADR-0077) ; ligne ou sortie trop longue : `message_invalide` (ADR-0078).
- **Non fait** : effet de `RLIMIT_AS` sous macOS non mesuré, la surveillance par le principal ayant été retenue d'emblée (ADR-0035, ADR-0080).
- **Reporté** à T20 : coût de la validation des messages par le principal, pour un module qui produit beaucoup d'observations.
- **Reporté** à T100, T102 : catégorie « malformés » du corpus (ES-19) ; à chaque module : ses propriétés de fuzzing.
- **Reporté** à un nouvel ADR : conteneur d'application sous Windows.

## Résultat

- Processus de travail restreint avant toute lecture : isolation complète sous Linux et macOS, réduite sous Windows (réseau, lecture, vidages), vérifiée depuis un module par la CI des trois systèmes.
- Limites fixées : refus « hors limites » au-delà de 1 Gio, 2 Gio de mémoire, 120 s ; budget compté de chaque module, bombe de décompression arrêtée.
- Une analyse n'écrit rien dans les dossiers personnels, temporaires, de cache ni de travail (ES-15).
- Fuzzing de l'identification, du décodage strict et de la réception par Hypothesis, joué à chaque passage de la CI.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent (692 tests, couverture 100 %) ; CI de la branche verte sur les trois systèmes et les trois versions de Python.

## Reste à faire

- T15 : catalogue, règles citées par les manifestes, techniques hors V1 par format.
- T16 : rapport à partir d'une analyse, gabarits des raisons dont `memoire_depassee`.
- T20 : coût de la validation des messages ; premier module, avec ses propriétés de fuzzing et son budget.
- T103 : niveau d'isolation par système ; conteneur recommandé sous Windows.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
