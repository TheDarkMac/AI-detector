# T101 — Rapport d'évaluation : taux par technique et catégorie

- **Branche** : `tache/T101-rapport-d-evaluation`
- **Dates** : 2026-11-26 → 2026-11-27
- **Exigences couvertes** : §8 et §9 (livrables 4 et 5) du cahier, NF-09 ; A-54
- **Décisions** : ADR-0277 à ADR-0280
- **Errata** : [ERR-0014](../errata/ERR-0014-total-des-parties-du-corpus.md)

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : « Rapport d'évaluation : taux par technique et catégorie », livrables 4 et 5. Demandé par TheDarkMac le 2026-11-26 (« T101 »), puis « ok, continue jusqu'à la fin comme d'habitude » et « préviens-moi quand la passe 1 est finie, et continue ».

## État initial

- PR [#49](https://github.com/TheDarkMac/AI-detector/pull/49) (T100) : les 16 vérifications vertes sur `05ac7aa` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-26 à 08:31:48 UTC après le « Oui, merge si vert » et le « Oui, valide ADR-0276 » de TheDarkMac, commit de merge `9b48ca1`. Lancements de push sur `9b48ca1` : code 45783940300 et docs 45783940366 verts, vérifiés le 2026-11-26.
- Corpus de référence 1.0.0 constitué (T100) : 6 734 fichiers, 4 467 en évaluation (et non 4 509, ERR-0014), sur le poste seulement. Catalogue 0.20.1 : 63 indices, tous « faible », aucun évalué. Les rubriques « Taux d'erreur » des fiches disent qu'aucun corpus n'a mesuré leurs règles.
- Toujours en attente : voir les journaux de T100, T95, T92, T91, T90, du complément de T81, de T81 et de T80 (« Reste à faire »).

## Déroulé

1. Lecture d'ADR-0016, ADR-0018, ADR-0101, ADR-0104, ADR-0105, ADR-0107, ADR-0113, ADR-0274, ADR-0276, de `banc/` (commande, évaluation, sortie), du guide du catalogue (§5) et des rubriques « Taux d'erreur » des fiches.
2. Durée mesurée : trois fichiers tirés au hasard par format, analysés une fois sur le poste : de 1,8 à 3,5 secondes par analyse pour la plupart des formats, 19 secondes pour un PDF, 21 pour un JPEG ; environ 22 heures pour les deux analyses de chaque fichier de la partie évaluation, un fichier à la fois, sans reprise possible.
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : banc en parallèle avec reprise ([ADR-0277](../decisions/ADR-0277-banc-en-parallele-avec-reprise.md)) ; évaluation et niveau permis inscrits au catalogue, puis seconde passe ([ADR-0278](../decisions/ADR-0278-evaluation-et-niveau-des-indices-au-catalogue.md)) ; rubrique des fiches écrite par le banc ([ADR-0279](../decisions/ADR-0279-taux-ecrits-dans-les-fiches.md)) ; mesure publiée telle quelle, écarts corrigés ensuite ([ADR-0280](../decisions/ADR-0280-publication-des-rapports-et-ecarts.md)).
4. Branche `tache/T101-rapport-d-evaluation` créée depuis `detector` à jour (`9b48ca1`).
5. Banc : `--processus N` (fils qui attendent chacun les processus de travail de leur fichier, résultats dans l'ordre du manifeste) et `--reprise FICHIER` (`banc/reprise.py`, en-tête avec l'empreinte du code du paquet). Les processus de travail sont lancés par `python -I` : ils chargent toujours le paquet installé, celui des sources ; le code ne doit donc pas changer pendant une passe. Essai sur le corpus d'essai : rapports identiques avec trois fils et un seul, et seconde passe reprise entièrement du journal.
6. Première passe lancée le 2026-11-26 à 12:58 (heure du poste), détachée de la session : partie évaluation, trois fichiers à la fois, catalogue 0.20.1, journal hors du dépôt (`.evaluation/`, exclu par `.git/info/exclude`).
7. Pendant la passe : `banc/inscription.py` (inscription au catalogue, essayée sur une copie avec un rapport fabriqué), `python -m banc.fiches --taux` (essayé sur une copie des fiches), tests (`tests/test_reprise.py`, `tests/test_taux_publies.py`), lancés un fichier à la fois pour ne pas charger le poste pendant la passe ; ADR-0277 à ADR-0280 ; guides de la vérification et du catalogue.
8. Première passe finie le 2026-11-26 à 20:56 (heure du poste), en 8 heures : 4 467 fichiers (et non 4 509 : ERR-0014), aucune tentative de réseau, aucun fichier non reproduit, 3 analyses interrompues (PDF longs), 22 refus de fichiers malformés ; taux par fichier 0/2 384 ; un écart, l'arrêt brutal de `pdf-0371.pdf` (`ValueError`). TheDarkMac n'en a pas été prévenu à la fin : l'attente, `pgrep -f` sur un motif présent dans sa propre ligne de commande, se trouvait elle-même et ne finissait pas ; signalé à TheDarkMac à sa question suivante (« toujours pas terminé ? »), et l'attente de la seconde passe suit le numéro du processus.
9. Cause de l'arrêt brutal, reproduite hors du banc, sans changer le code : l'analyse de `pdf-0371.pdf` produit plus de 16 visualisations, que le processus principal refuse à la validation (« visualisations : trop nombreuses », `NOMBRE_MAX_VISUALISATIONS`) ; rien ne les borne là où elles sont produites. Renvoyée à un correctif (ADR-0280).
10. Inscription : `python -m banc.inscription` sur le rapport de la première passe, 61 indices évalués, 38 « fort », 15 « modéré », 8 « faible », et 2 sans effectif restés « faible » (R-QUICKTIME-001 et R-QUICKTIME-002 : aucun fichier authentique analysé par le module `quicktime`, le corpus n'ayant pas d'original MP4, MOV ou M4A). En-tête du catalogue 0.21.0 et sa description récrite (elle disait « indices faibles ») ; dix textes de règles qui disaient « pas mesuré sur le corpus de référence (T100) » ou « indice faible, non évalué » récrits avec la mesure, avant la seconde passe, pour que son rapport cite l'empreinte du catalogue livré ; registre des versions.
11. Suite complète avant la seconde passe, pour qu'aucune correction de `src/` ne vienne après elle : 3 561 tests verts, 11 en échec, tous des attentes de tests (niveaux « faible, non évalué » de T22, T24, T30, T40, T41, version des règles relevées, attentes de mes tests d'inscription) ou un défaut du banc sur le corpus d'essai (chaque indice « fort » y devenait un écart de niveau) ; la matrice à régénérer. Aucun ne demandait de changer `src/`.
12. Seconde passe lancée le 2026-11-26 vers 21:25 avec le catalogue 0.21.0 (commit `2113d42`), finie le 2026-11-27 à 04:11. Pendant la passe : le banc ne contrôle plus le niveau d'un indice que sur un corpus de référence (ADR-0278) ; tests adaptés (`niveau_mesure` dans `tests/catalogues.py`) ; ERR-0014 et un test qui relie la description du corpus au manifeste ; textes rédigés des fiches, sans « non évalué » ni « indice faible » ; matrice (NF-09 « réalisée »), découpage v0.48, guides.
13. Seconde passe : mêmes taux pour chaque règle ; mêmes faux positifs, faux négatifs et confusions pour chaque technique ; `pdf-0203.pdf` interrompu à la première passe seulement, ce qui change d'un fichier les parts non applicables et non analysables des authentiques ; taux par fichier 8/2 384, 0,3 % [0,2 % ; 0,7 %], cible atteinte ; même écart unique. Rapports copiés dans `docs/verification/evaluations/`, tels quels ; `python -m banc.fiches --taux` sur le rapport de la seconde passe ; [page des rapports](../verification/evaluations/README.md) ; description du corpus v1.1 ; `CONTRIBUTING.md`.
14. Suite complète sous coverage, en 16 minutes 22 : 3 580 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), aucun échec ; couverture à 100 % sauf `banc/fiches.py` et `banc/inscription.py` : leurs tests copiaient les fiches et le catalogue des sources, qui portent désormais des blocs de taux et des évaluations, et ne passaient plus par l'ajout d'un premier bloc ni d'une première évaluation. Ces tests partent maintenant d'une copie ramenée à l'état d'avant T101 ; les deux fichiers sont de nouveau couverts à 100 % (tests de publication relancés). Ruff, mypy et markdownlint sans erreur.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Inscription refusée par le schéma | Date écrite comme date TOML, le schéma attend une chaîne | Date entre guillemets |
| Catalogue de l'essai modifié malgré le refus | Fichiers écrits avant la validation | Inscription faite dans une copie, validée, puis recopiée |
| Attente fausse d'un test de parallélisme | Chaque fichier est analysé deux fois : la barrière de l'essai était franchie deux fois | Test réécrit avec un événement |
| Poste chargé pendant la première passe | Navigateur et application de bureau sur deux des quatre processeurs, mémoire presque pleine | Trois fichiers à la fois ; 8 heures par passe au lieu des 22 estimées sur un seul fil |
| Fin de la première passe non signalée | `pgrep -f` d'une attente dont la ligne de commande contenait le motif | Attente sur le numéro du processus (`kill -0`) |
| Arrêt brutal sur `pdf-0371.pdf` | Plus de 16 visualisations, refusées à la validation et non bornées à leur production | Publié tel quel, correctif à part (ADR-0280) |
| 4 467 fichiers évalués au lieu de 4 509 annoncés | Totaux de la description du corpus écrits à la main | ERR-0014, test de la description |
| Écarts de niveau sur le corpus d'essai | Chaque indice « fort » du catalogue livré y était contrôlé sur neuf fichiers | Niveau contrôlé sur un corpus de référence seulement (ADR-0278) |
| Faux positifs de techniques différents d'une passe à l'autre attendus par un test | Une analyse interrompue au délai, en temps écoulé, peut ne l'être qu'à une passe | Test restreint aux faux positifs, faux négatifs et confusions |
| Test de l'écriture des fiches en échec après la publication | Il comparait à la fiche source, sans bloc jusque-là | Comparaison sans le bloc |
| Couverture du banc sous 100 % | Tests partis du catalogue et des fiches des sources, déjà inscrits | Copies ramenées à l'état d'avant T101 |

## Écarts par rapport au découpage

- T101 change aussi le catalogue (0.21.0) : les taux mesurés fixent le niveau des indices (ADR-0278), ce que le découpage ne disait pas mais qu'ADR-0018 demandait.
- Le banc a deux options de plus (ADR-0277), faute de quoi l'évaluation ne tenait pas sur ce poste.

## Résultat

- Rapports publiés : `docs/verification/evaluations/reference-1.0.0-catalogue-0.20.1/` et `…-0.21.0/` ; taux par fichier de l'outil livré : 8/2 384 (0,3 %, au plus 0,7 %), cible atteinte ; aucune preuve fautive ; un écart, l'arrêt brutal de `pdf-0371.pdf`.
- Catalogue 0.21.0 : 61 indices évalués, 38 « fort », 15 « modéré », 10 « faible » ; empreinte `358c60e329923356d161ee671935c827288ef2e86f27102c831d1e249862c465`.
- Rubrique « Taux d'erreur » des 25 fiches écrite par le banc, copiée dans le paquet ; matrice : NF-09 « réalisée ».
- Vérification locale : 3 580 tests verts, 4 ignorés, aucun échec ; couverture de tout le paquet et du banc à 100 % (étape 14) ; Ruff, mypy et markdownlint sans erreur.

## Reste à faire

- Correctif de l'arrêt brutal de `pdf-0371.pdf` : borner les visualisations là où elles sont produites, analyse partielle signalée ; erratum ; nouvelle évaluation publiée dans un nouveau dossier (ADR-0280).
- Relire, pendant la revue de la PR, le texte rédigé des rubriques « Taux d'erreur » (NF-09) et la page des rapports.
- Détection faible : 39 des 320 images générées, 9 des 43 PDF retouchés reconnus, aucun texte ni document généré ; à mettre en avant dans la documentation utilisateur (T103) et à éprouver par l'équipe rouge (T102).
- Indices vers la transformation à fort taux de faux positifs (R-IMAGE-004 sur 97 des 825 authentiques, R-IMAGE-016 sur 46) : un recalibrage éventuel se ferait sur la partie calibrage, dans une tâche à part.
- Copie des fichiers du corpus hors du poste, par TheDarkMac (journal de T100).
