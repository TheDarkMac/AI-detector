# T92 — Affichage de la conservation des données

- **Branche** : `tache/T92-affichage-de-la-conservation`
- **Dates** : 2026-11-25
- **Exigences couvertes** : NF-05 ; NF-13 (partielle) ; NF-04 (affichage)
- **Décisions** : ADR-0264 à ADR-0267
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : « Affichage de la conservation des données (durée, lieu) », exigences NF-04, NF-05, NF-13. ADR-0010 en avait fixé le fond : l'outil ne conserve aucun fichier et n'écrit que les rapports demandés, à l'emplacement choisi, « c'est ce qu'il affiche au titre de NF-05 ». NF-13 (RGPD, ADR-0020) est partagée avec T103. Demandé par TheDarkMac le 2026-11-25 (« T92 (affichage de la conservation des données) »).

## État initial

- PR [#46](https://github.com/TheDarkMac/AI-detector/pull/46) (T91) : les 16 vérifications vertes sur `13b412c` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-25 à 07:08:29 UTC après le « Oui, merge si vert » de TheDarkMac, commit de merge `7966cc9`. Lancements de push sur `7966cc9` : code 45565824975 et docs 45565825163 verts, vérifiés le 2026-11-25.
- Rien n'affichait la conservation : seule la ligne « rapport : 1.html et 1.json » donnait un lieu, sans durée. NF-05 et NF-13 « à venir » dans la matrice.
- Catalogue 0.20.0, schémas 0.13.0, 25 modules ; depuis T91, une commande peut aussi écrire des jetons d'horodatage et un journal, et envoyer une empreinte à une autorité (RS-03).
- Toujours en attente : voir les journaux de T91, T90, du complément de T81, de T81 et de T80 (« Reste à faire »).

## Déroulé

1. Lecture du découpage, d'ADR-0010, ADR-0020, ADR-0030, ADR-0098, ADR-0260 à ADR-0262, du modèle de menace (M-22, M-23, M-26, M-27, ES-13 à ES-17), de la matrice (NF-04, NF-05, NF-13, ES-15), de `cli.py`, du rapport HTML et de `tests/test_traces.py`. Inventaire de ce que l'outil lit, écrit et envoie : fichier lu par un descripteur passé au processus de travail, aucune écriture hors des options (`tempfile` absent du paquet) ; rapports, jetons et journal créés en `0o600`, droits qui ne valent que sous Linux et macOS (sous Windows, le mode d'`os.open` ne règle que la lecture seule).
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation, sans raison supplémentaire : un bloc à la fin de chaque commande et `vk --conservation` ([ADR-0264](../decisions/ADR-0264-affichage-de-la-conservation-au-terminal.md)) ; rubrique au rapport HTML, JSON inchangé ([ADR-0265](../decisions/ADR-0265-rubrique-conservation-du-rapport.md)) ; ce qui échappe à l'outil nommé sans promesse ([ADR-0266](../decisions/ADR-0266-ce-qui-echappe-a-l-outil.md)) ; analyse écrite, NF-13 partielle ([ADR-0267](../decisions/ADR-0267-analyse-des-traitements-rgpd.md)).
3. Branche `tache/T92-affichage-de-la-conservation` créée depuis `detector` à jour (`7966cc9`).
4. Code : table `[conservation.donnees]` de `textes.toml` (énoncé, rubrique, bloc) ; `cli.py` : option `--conservation`, bloc `lignes_conservation` après l'avertissement, boucle d'analyse séparée (`_analyser_chacun`) pour que le bloc s'affiche aussi après un arrêt par le journal, suivi de ce qui a été écrit ou envoyé (`_Ecrits`) ; `_html.py` : rubrique `conservation` avant le glossaire ; `journal.Journal.chemin`, en lecture seule, pour afficher le chemin du journal.
5. Essai à la main dans le dossier temporaire de la session : `vk --rapport r` sur `tests/donnees/ela/collage_60_92.jpg` et un fichier absent, `vk --texte`, `vk --conservation`, `vk --conservation x` (code 2) ; rubrique lue dans `r/1.html`.
6. Relecture de l'énoncé contre le code et les tests, phrase par phrase : « ni copié sur le disque » (descripteur, `tests/test_traces.py`) ; « processus de travail ouvert pour lui seul » (ADR-0015) ; « privé de réseau et d'écriture quand son isolation est complète » (ADR-0028, rubrique Isolation) ; « lisibles par leur seul propriétaire » restreint à Linux et macOS ; « jamais écrasés » (ADR-0092) ; contenu du journal repris des champs d'ADR-0261 (le nom déclaré par `--qui` ajouté à la première rédaction, qui l'omettait).
7. Analyse des traitements : [`docs/verification/donnees-personnelles.md`](../verification/donnees-personnelles.md). Deux renvois à des fichiers de tests qui n'existent pas (`test_texte.py`, `test_comparaison.py`) corrigés avant commit (`test_caracteres.py`, `test_reproductibilite.py`) ; un renvoi à ADR-0016, qui porte sur les méthodes de l'outil et non sur les fichiers des utilisateurs, retiré.
8. Tests : `tests/test_conservation_donnees.py` (énoncé, option seule, chaque option nommée, bloc sans rapport, avec rapports et journal, rapports jamais écrits, horodatage obtenu et non obtenu, texte collé et comparaison, arrêt par le journal, chemin neutralisé, rubrique sans chemin, rubrique d'un texte collé) ; `test_rapport.py` (ordre des rubriques) et `test_cli.py` (sortie d'une commande dont tous les fichiers sont refusés) mis à la nouvelle sortie.
9. Matrice : NF-05 « réalisée », NF-13 « partielle », NF-04 avec T92 ; matrice régénérée (`python -m banc.matrice`).
10. Suite complète sous coverage, en 24 minutes 13 : 3 464 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), 3 en échec, attendus : les tests de `vk --comparer` de `test_reproductibilite.py` comparaient toute la sortie, qui se termine maintenant par le bloc. Couverture de tout le paquet et du banc à 100 %. Attentes mises à jour (le bloc est vérifié puis retiré), `test_reproductibilite.py` et `test_matrice.py` relancés : 51 verts.
11. PR [#47](https://github.com/TheDarkMac/AI-detector/pull/47) ouverte vers `detector` (commits `1b51a67`, `560ff1b`, `bb7d8a8`, `fd60159`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Droits `0o600` annoncés pour tous les systèmes dans la première rédaction | Sous Windows, le mode passé à `os.open` ne règle que l'attribut lecture seule ; les droits viennent du dossier | Énoncé et analyse restreints à Linux et macOS |
| Trois tests de `vk --comparer` en échec dans la suite complète | Ils comparaient toute la sortie | Bloc vérifié puis retiré avant la comparaison |
| `test_lot_avec_un_refus` en échec | Il attendait une sortie vide quand tous les fichiers sont refusés ; le bloc s'y affiche (ADR-0264) | Attente mise à jour |
| Caractère `U+202E` écrit en clair dans un test | L'outil d'écriture de l'assistant écrit les échappements `\u` en caractères | Échappement rétabli |
| mypy : `cli.journal` non exporté | Le test remplaçait les fonctions par le module `cli` | Remplacement par les modules `horodatage` et `journal` eux-mêmes |
| Preuve introuvable à la régénération de la matrice | La preuve de NF-05 cite ce journal, pas encore écrit | Journal écrit avant la régénération |

## Écarts par rapport au découpage

- NF-13 n'est que partielle : les mentions destinées à l'utilisateur sont à T103 (ADR-0267).
- Aucune relecture juridique : non prévue par le découpage ; inscrite au §6 de l'analyse.

## Résultat

- `vk FICHIER…`, `vk --texte`, `vk --comparer A B` : bloc « Conservation des données » à la fin, une ligne par donnée lue ou écrite, avec son lieu et sa durée.
- `vk --conservation` : énoncé complet, ce qui échappe à l'outil compris.
- Rapport HTML : rubrique « Conservation des données », au sommaire, sans chemin. Rapport JSON, schémas, catalogue et modules inchangés.
- `docs/verification/donnees-personnelles.md` : analyse des traitements au regard du RGPD.
- Matrice : NF-05 « réalisée », NF-13 « partielle ».
- Vérification locale : suite complète (étape 10) ; Ruff, mypy et markdownlint sans erreur.

## Reste à faire

- T103 : mentions tirées du §5 de l'analyse (base légale, information des personnes, durée de conservation des rapports et du journal, choix de l'autorité, limiter les traces hors de l'outil).
- Complément de T30 : ajouter RS-01 et RS-02 à l'analyse et à l'énoncé avant leur livraison (« Rien d'autre ne quitte le poste » deviendrait faux).
- Relecture juridique de l'analyse : à décider par TheDarkMac.
