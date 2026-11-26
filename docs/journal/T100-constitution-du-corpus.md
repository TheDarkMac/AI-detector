# T100 — Constitution du corpus de référence

- **Branche** : `tache/T100-constitution-du-corpus`
- **Dates** : 2026-11-25 → 2026-11-26
- **Exigences couvertes** : ES-22 ; §8 et livrable 5 du cahier
- **Décisions** : ADR-0272 à ADR-0276
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : « Constitution du corpus (5 catégories) ou sa description », livrable 5. Demandé par TheDarkMac le 2026-11-25 (« T100 »), puis « ok, fini cette tache comme d'habitude » le 2026-11-26.

## État initial

- PR [#48](https://github.com/TheDarkMac/AI-detector/pull/48) (T95) : les 16 vérifications vertes sur `ae6c055` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-25 à 10:15:49 UTC après le « Oui, merge si vert » de TheDarkMac, commit de merge `d00ff3a`. Lancements de push sur `d00ff3a` : code 45593292644 et docs 45593292784 verts, vérifiés le 2026-11-25.
- Le banc (T17) ne connaissait que le corpus d'essai de neuf fichiers (ADR-0105) ; le registre des arbitrages laissait à T100 sources, volume et droits du corpus ; ES-22 « partielle ».
- Toujours en attente : voir les journaux de T95, T92, T91, T90, du complément de T81, de T81 et de T80 (« Reste à faire »).

## Déroulé

1. Lecture du §8 et du §9 du cahier, d'ADR-0016, ADR-0099 à ADR-0107, ADR-0204, d'A-12, A-13, A-54 à A-56, de `banc/corpus.py`, du schéma du manifeste, du corpus d'essai, des relevés de T32 et du complément de T40, des formats de chaque module (manifestes). Constat : seuls DOCX et ODT sont analysés en bureautique, pas XLSX ni ODS.
2. Sondage des API (quelques requêtes, sans téléchargement de fichier) : recherche de Commons (`filemime:`, `filesize:`, `gsrsort=random`, `deepcat:"AI-generated images"`), API des jeux de data.gouv.fr (138 jeux avec un DOCX, 49 avec un ODT), API de Wikipédia (tirage au hasard, révision antérieure à une date).
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : corpus réel, téléchargement autorisé depuis Commons, data.gouv.fr et Wikipédia ([ADR-0272](../decisions/ADR-0272-corpus-reel-de-sources-libres.md)) ; générés déclarés et textes de l'assistant ([ADR-0273](../decisions/ADR-0273-verite-des-originaux.md)) ; dérivés par scripts locaux ([ADR-0275](../decisions/ADR-0275-derives-fabriques-par-scripts.md)) ; 400 authentiques en évaluation par famille, un tiers en calibrage ([ADR-0274](../decisions/ADR-0274-effectifs-et-parties.md)).
4. Branche `tache/T100-constitution-du-corpus` créée depuis `detector` à jour (`d00ff3a`).
5. Scripts `banc/reference/` : module commun (sources retenues seules, redirections hors sources non suivies, lecture bornée, reprise), puis six phases. Lancés par `python -m banc.reference.…` : un module commun importé par son seul nom n'était pas trouvé par mypy, et `mypy_path` lui faisait voir le fichier sous deux noms.
6. Phase 1 lancée. Les 700 premières lignes ne contenaient que 50 fichiers distincts : le tri au hasard de Commons est mis en cache pour une même requête. Liste refaite en suivant ce tri par décalage (`gsroffset`), ce qui la rend en plus reproductible.
7. Pendant la phase 1 : phases 2 à 6 écrites ; 40 textes écrits par l'assistant (`textes-ia/`) ; fonctions de la phase 4 éprouvées sur des échantillons du dépôt et des sons et vidéos synthétiques, phase 5 sur quatre tâches d'essai ; les onze pièges passés à `vk` : aucun arrêt brutal, deux refusés comme format non reconnu (`id3-geant.mp3`, `texte-utf8-invalide.txt`).
8. Phase 1 rendue lançable par source (`--source`), un fichier de liste et d'état par source, pour lister data.gouv.fr et Wikipédia en parallèle de Commons ; la liste de Commons déjà faite renommée selon ce nommage. Arrêt sur une erreur « cirrussearch-too-busy-error » de Commons : reprise avec attente croissante pour ces erreurs passagères.
9. Premier essai de la phase 2 : trop peu de PDF (138), de sons (48 FLAC), de DOCX (24), le plafond de 3 fichiers par compte tombant sur des formats versés par peu de comptes. Plafonds relevés à 10 (PDF, sons, vidéos, images générées) et 50 (DOCX, ODT), liste de Commons prolongée jusqu'au 10 000e résultat pour ces formats ; tirage de Wikipédia porté à 1 700 articles (562 assez longs sur les 1 100 premiers). Mesures dans ADR-0273.
10. Phase 2 définitive : 3 972 originaux, 5,2 Gio annoncés ; parties écrites avant tout téléchargement.
11. Phase 3 : coupée une première fois au 602e original (réseau perdu, puis redémarrage du poste), relancée détachée de la session (`setsid nohup`), arrêtée une seconde fois au 3 305e sur une révision de Wikipédia masquée depuis (erreur « permissiondenied ») : la révision est désormais écartée. Fin : 3 868 originaux téléchargés, empreinte SHA-1 de la source vérifiée ; 102 textes trop courts.
12. Complément des textes, avant toute mesure : cible des textes portée à tous les éligibles (849), tirage poursuivi dans le même ordre ; les 3 972 choix antérieurs vérifiés identiques ; 249 textes de plus, 461 en évaluation (ADR-0274).
13. Phase 4 : le réencodage VP9 prenait plus de cinq minutes par vidéo, sur un seul fil, et six vidéos ont dépassé la limite de dix minutes ; une conversion MP4 a échoué (largeur impaire). Réglages corrigés (vitesse maximale, plusieurs fils ; côtés pairs et 4:2:0 pour H.264), tous les transformés vidéo refaits avec les mêmes réglages. Fin : 2 661 dérivés, aucun échec.
14. Phase 5 : 60 retouches sur 90 seulement, celles confiées pendant le passage interrompu de la phase 4 manquant à `uno.json` ; la liste est désormais refaite à partir de `derives.jsonl`. Un PDF de 13 pages a bloqué Draw plus de dix minutes : limite de cinq minutes par tâche, LibreOffice relancé après. Fin : 87 retouches faites, 3 en échec.
15. Phase 6 : manifeste de 6 734 fichiers relu par le banc, chaque empreinte vérifiée ; 4 fichiers écartés (`effectifs.json`).
16. Tests : `tests/test_corpus_reference.py` (manifeste lu par le banc, cinq catégories dans les deux parties, un original sur trois en calibrage par format, dérivés dans le groupe et la partie de leur original, provenance de chaque catégorie, aucun nom de compte, accord d'`effectifs.json`, textes de l'assistant identiques à ceux du dépôt, sources retenues et refusées, paramètres de suivi retirés). Scripts de constitution exclus de la mesure de couverture (`pyproject.toml`).
17. Documentation : ADR-0272 à ADR-0276 ; [description du corpus](../verification/corpus-de-reference.md) (livrable 5) ; guide du dossier de vérification v1.4 ; registre des arbitrages v1.15 (constitution du corpus tranchée) ; découpage v0.47 ; historique d'ADR-0103 ; `CONTRIBUTING.md` ; matrice : ES-22 « réalisée », régénérée ; `.gitattributes` (manifeste, effectifs et textes sans conversion des fins de ligne).
18. Suite complète sous coverage : voir « Résultat ».
19. PR [#49](https://github.com/TheDarkMac/AI-detector/pull/49) ouverte vers `detector` (commits `04dc63d`, `3a48371`, `9105d6a`, `da0a838`, `ee43438`).
20. CI de `ee43438` : 15 vérifications vertes, `lint-markdown` en échec sur le seul contrôle des ADR « Proposé » (ADR-0129), comme attendu. ADR-0276 validé par TheDarkMac (« Oui, valide ADR-0276 ») et passé à « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Liste de Commons faite des mêmes 50 fichiers | Tri au hasard mis en cache pour une même requête | Appels suivis par décalage dans ce tri |
| mypy ne trouvait pas le module commun | Scripts dans un dossier sans `__init__.py` ; `mypy_path` faisait voir le fichier sous deux noms | Lancement par `python -m banc.reference.…`, imports qualifiés |
| Arrêt de la phase 1 | Erreur passagère de la recherche de Commons (« too busy ») | Reprise avec attente croissante |
| Trop peu de PDF, de sons et de documents | Formats versés par peu de comptes, plafond de 3 | Plafonds relevés, liste prolongée (ADR-0273) |
| Tous les textes vus comme doublons | Clé « adresse » vide commune aux articles de Wikipédia | Clé ajoutée seulement quand l'adresse existe |
| Téléchargements coupés au 602e original | Réseau perdu, puis redémarrage du poste qui a fermé la session | Reprise par le script ; processus détaché de la session |
| Arrêt au 3 305e original | Révision de Wikipédia masquée depuis la phase 1 | Révision écartée, avec sa raison |
| Seulement 323 textes en évaluation | 102 articles sans paragraphes assez longs | Tirage prolongé dans le même ordre, avant toute mesure |
| Phase 4 très lente, six échecs | VP9 sur un seul fil, réglage lent, poste chargé ; limite de dix minutes | Réglage rapide et plusieurs fils ; transformés vidéo refaits |
| Conversion MP4 en échec | Largeur impaire refusée par H.264 | Côtés ramenés à un nombre pair, pixels 4:2:0 |
| 30 retouches absentes de la phase 5 | `uno.json` écrit à la fin de la phase 4 seulement, passage interrompu | Liste refaite à chaque passage depuis `derives.jsonl` |
| Draw bloqué sur un PDF | Aucune limite de durée par tâche | Limite de cinq minutes, LibreOffice relancé |
| `pkill` arrêtait son propre shell | Motif présent dans la ligne de commande du shell | Arrêt par numéro de processus |
| Test des parties en échec sur les retouchés | Attente fausse : les originaux dérivés sont tirés toutes parties confondues | Test restreint aux originaux, bornes plus serrées |

## Écarts par rapport au découpage

- Aucun sur le fond : le corpus est constitué, et sa description publiée tient lieu du livrable 5 tant que les fichiers ne le sont pas.
- La bureautique reste sous 400 authentiques en évaluation (86), faute de source.

## Résultat

- Corpus `reference` 1.0.0 : 6 734 fichiers, 4 509 en évaluation ; cinq catégories du §8 ; empreinte du manifeste `055a8becce9fbf5a7c656341014145c020fa2e5ffe3de53535fda8ecec0a76d7`.
- Au dépôt : scripts et textes de l'assistant (`banc/reference/`), manifeste et effectifs, description du corpus.
- Matrice : ES-22 « réalisée ».
- Vérification locale : suite complète sous coverage, en 19 minutes 28 : 3 516 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), aucun échec ; couverture de tout le paquet et du banc à 100 % (scripts de constitution exclus) ; Ruff, mypy et markdownlint sans erreur.

## Reste à faire

- T101 : évaluer le corpus (sur le poste où sont les fichiers ; deux analyses par fichier, soit plusieurs heures), publier les taux, remplir la rubrique « Taux d'erreur » des fiches.
- Copie des fichiers du corpus hors du dépôt, à faire par TheDarkMac (7,7 Gio) : sans elle, la version 1.0.0 ne pourra pas être réévaluée si le poste est perdu.
- Bureautique : chercher une autre source libre de DOCX et ODT pour une version suivante du corpus.
- T102 : retouches soignées, faites à la main, que les retouches mécaniques du corpus n'approchent pas.
- A-13 : renouveler les générés à chaque génération de générateurs, par une nouvelle version.
