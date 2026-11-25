# T90 — Interface de la V1 : ligne de commande et rapport HTML lisibles, WCAG 2.2 AA vérifié

- **Branche** : `tache/T90-interface`
- **Dates** : 2026-11-25
- **Exigences couvertes** : NF-11, NF-12
- **Décisions** : ADR-0256 à ADR-0259
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : « Interface : en V1, ligne de commande et rapport HTML (ADR-0010, ADR-0025) ; interface web locale ensuite ». Les deux existent depuis T16 ; la tâche les rend lisibles sans connaissances techniques (NF-11) et établit, critère par critère, la conformité du rapport à WCAG 2.2 AA, qu'aucun audit n'avait vérifiée (NF-12, journal de T16, « Non fait »). Demandé par TheDarkMac le 2026-11-25 (« T90, l'interface »).

## État initial

- PR [#44](https://github.com/TheDarkMac/AI-detector/pull/44) (complément de T81) : les 16 vérifications vertes sur `722ea21` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-23 à 19:02:11 UTC après le « Oui, merge si vert » de TheDarkMac, commit de merge `c5b0981`. Lancements de push sur `c5b0981` : code 45244660392 et docs 45244660512 verts, vérifiés le 2026-11-25.
- Catalogue 0.20.0 (`a8eaba47…61ea1`), schémas 0.13.0, 25 modules livrés, 15 techniques hors de cette version.
- Le rapport HTML est structuré pour WCAG 2.2 AA depuis T16 (langue, titres, tableaux légendés, lien d'évitement, contrastes calculés) ; la matrice garde NF-12 « partielle », faute d'audit par un outil, et NF-11 « partielle », la documentation utilisateur étant à T103.
- Toujours en attente : voir les journaux du complément de T81, de T81 et de T80 (« Reste à faire ») ; signature d'un manifeste C2PA d'un texte ; inventaire des marquages à refaire en entier ; `$OutputEncoding` de PowerShell (T103).

## Déroulé

1. Lecture du découpage, d'ADR-0010, ADR-0025, ADR-0073, ADR-0098, du journal de T16, de NF-11 et NF-12 dans le cahier et la matrice, du code de la commande (`cli.py`), de la présentation (`rapport/_presentation.py`), du rapport HTML (`rapport/_html.py`) et de ses textes (`rapport/textes.toml`).
2. Essai sur trois échantillons (`tests/donnees/ela/collage_60_92.jpg`, `tests/donnees/imagesbureau/libreoffice.docx`, `tests/donnees/revisions/signe_modifie.pdf`), rapports servis sur 127.0.0.1 et lus dans le navigateur intégré, les captures d'écran n'aboutissant pas : lecture par le texte et l'inspection de la page. Constats : le résumé du terminal écrit une ligne par technique et par partie (29 sur les 51 lignes du JPEG, 93 sur 121 pour le DOCX), sous l'identifiant du module, et des nombres en « indice(s) » ; le rapport n'a pas de sommaire ; à 320 px, la valeur d'une liste de définitions n'a que 94 px.
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation, sans raison supplémentaire : grille des critères et passage d'axe-core hors de la CI ([ADR-0256](../decisions/ADR-0256-verification-de-wcag-2-2-aa.md)) ; sommaire et écrans étroits ([ADR-0259](../decisions/ADR-0259-sommaire-et-ecrans-etroits.md)) ; une ligne par état au terminal ([ADR-0258](../decisions/ADR-0258-resume-du-terminal-et-accords.md)) ; nom de chaque technique dans `textes.toml` ([ADR-0257](../decisions/ADR-0257-nom-des-techniques.md)). Deux chiffres de ces questions étaient approchés et sont corrigés dans les ADR : le résumé d'un JPEG faisait 51 lignes, non « environ 45 », et 25 modules sont livrés, non 26.
4. Branche `tache/T90-interface` créée depuis `detector` à jour (`c5b0981`).
5. Textes : table `[techniques]`, 40 noms (25 modules, 15 techniques hors de cette version) ; formes `un` et `plusieurs` pour chaque texte qui porte un nombre, dont le résumé, le contrôle avant publication et la comparaison de deux rapports ; lignes des techniques au terminal ; titre « Sommaire » ; définition de « Partie » du glossaire, qui ne citait que le PDF pour les parties extraites.
6. Code : `accorder` et `technique` dans `rapport/_presentation.py` ; résumé des techniques limité aux états présents ; lignes des techniques par partie et par état dans `cli.py` ; noms des techniques dans les tableaux de couverture et des analyses non menées, dans la précision d'une non menée au terminal et dans l'origine d'une partie extraite ; sommaire construit depuis la liste des rubriques, alertes comprises, entre l'en-tête et le contenu principal, non imprimé ; listes de définitions empilées sous 30 rem.
7. Premier essai du terminal : les techniques hors de cette version qui ne s'appliquent pas au format (bruit du capteur pour un DOCX) étaient dites « hors de cette version », comme avant T90 ; elles sont désormais comptées avec les non applicables (ADR-0258).
8. Audit (ADR-0256) : axe-core 4.14.0, la dernière version publiée depuis plus de deux semaines (4.14.1 l'a été le 2026-11-16), installé par npm dans un dossier temporaire ; copies des rapports sans politique de sécurité, avec `axe.min.js` et un script d'audit. Premier passage : une violation, `landmark-unique` (rubrique et tableau des observations du même nom), corrigée par la légende du tableau. Mesures à 320 px : un titre de constat qui cite l'adresse `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia` portait la page à 676 px de large (1.4.10), corrigé en laissant couper titres, paragraphes et éléments de liste ; liens du sommaire de 22 px de haut (2.5.8), portés à plus de 24 px. Contour du focus des zones de défilement aligné sur celui des liens. La carte ELA étant masquée par défaut, un cinquième rapport, `--reveler contenu`, a été ajouté pour vérifier son alternative.
9. Second passage, sur cinq rapports, en mode clair et sombre, à la largeur du panneau et à 320 px : aucune violation ; contraste de chaque élément de texte d'au moins 8,04:1 en clair et 10,40:1 en sombre ; espacement de 1.4.12 sans débordement ni coupure ; liens de moins de 24 px tous sous l'exception d'espacement ; parcours au clavier et défilement d'un tableau par la flèche droite. Grille de chaque critère A et AA dans [`docs/verification/accessibilite.md`](../verification/accessibilite.md).
10. Tests : `tests/test_interface.py` (sommaire avec et sans alertes, feuille de style des petits écrans, accords, aucun « (s) » dans les textes de l'outil, un nom pour chaque technique et rien de plus, nom d'une technique inconnue, lignes des techniques des trois parties du DOCX) ; attentes mises à jour dans `test_cli.py`, `test_rapport.py`, `test_controle_publication.py`, `test_reproductibilite.py`.
11. Suite complète sous coverage, en 14 minutes 44 : 3 357 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), 5 en échec, tous des attentes à mettre à jour : deux tests d'`ela` et de `revisionspdf` appelaient `texte("resume.visualisations")`, devenu un texte accordé (`accorder`) ; deux tests des parties extraites (`imagespdf`, `imagesbureau`) attendaient l'origine sous l'identifiant seul ; la matrice rendue n'était pas régénérée après les marques d'exigence de `test_interface.py`. Couverture de tout le paquet et du banc à 100 %. Corrigés, puis matrice mise à jour (NF-12 « réalisée », NF-11 complétée), grille copiée dans `docs/verification/` après la suite, qui lit ce dossier, et fichiers concernés relancés : voir « Résultat ».
12. PR [#45](https://github.com/TheDarkMac/AI-detector/pull/45) ouverte vers `detector` (commits `81e079d`, `fe7a7fe`, `1c4eaba`, `80dfaf7`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Captures d'écran du navigateur intégré en échec | Page non dessinée dans le temps imparti, la fenêtre de l'application étant probablement en arrière-plan | Lecture par le texte, l'inspection de la page et des mesures en JavaScript |
| La politique de sécurité du rapport interdit le script d'axe-core | `default-src 'none'`, voulu (ADR-0094) | Audit sur une copie sans la balise de politique, page sinon identique |
| Carte ELA absente des quatre premiers rapports | Masquée par défaut, catégorie `contenu` (ADR-0200) | Cinquième rapport avec `--reveler contenu` |
| Régions du même nom | Légende du tableau des observations égale au titre de sa rubrique | Légende « Données relevées, une par ligne » |
| Débordement à 320 px | Titres et paragraphes non coupables dans un mot | `overflow-wrap:anywhere` sur titres, paragraphes et éléments de liste |
| Liens du sommaire de 22 px | Hauteur de ligne seule | Marges verticales de 0,2 rem |
| Technique hors V1 non applicable dite « hors de cette version » | Version absente testée avant l'état | Comptée avec les non applicables |
| Chiffres approchés dans les questions | Comptés de tête par l'assistant | Recomptés sur les échantillons, corrigés dans les ADR |
| Cinq attentes de tests périmées dans la suite complète | Textes accordés et noms des techniques non repris partout ; matrice rendue non régénérée | Attentes mises à jour, matrice régénérée |
| Espace fine insécable écrite en clair dans un test | L'outil d'écriture de l'assistant écrit l'échappement `\u202f` en caractère | Échappement rétabli |

## Écarts par rapport au découpage

- Interface web locale : non faite, comme prévu (après la V1, ADR-0010).
- Lien d'évitement : la question à TheDarkMac proposait de le faire mener au sommaire ; il mène toujours au résumé, le sommaire suivant immédiatement l'en-tête (ADR-0259).
- Phrases des règles du catalogue : elles gardent leur « (s) », leur accord demandant un changement du format du catalogue (ADR-0258).

## Résultat

- `vk FICHIER` : techniques par partie et par état, nommées en langage courant, non applicables comptées ; nombres accordés ; détail des indices en phrase.
- Rapport HTML : sommaire, noms des techniques, lecture à 320 px ; conforme aux critères A et AA de WCAG 2.2 d'après la grille (ADR-0256).
- Export JSON, schémas, catalogue et modules inchangés.
- Matrice : NF-12 « réalisée » (grille et tests) ; NF-11 reste « partielle », la documentation utilisateur étant à T103.
- Vérification locale : suite complète (étape 11) avec couverture à 100 %, puis les dix fichiers de tests touchés relancés après correction (461 verts) ; Ruff, mypy et markdownlint sans erreur.

## Reste à faire

- Interface web locale, après la V1.
- Accord au nombre des phrases des règles du catalogue (format du catalogue, ADR-0085).
- T103 : codes de sortie dans `vk --help` ; messages d'`argparse` en anglais (« usage: », « options: », erreurs de syntaxe).
- Repasser la grille à chaque changement de la structure ou de la feuille de style du rapport, et sur un rapport à visualisation nouvelle.
