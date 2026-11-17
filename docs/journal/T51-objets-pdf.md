# T51 — Objets changés, textes superposés et polices incohérentes d'un PDF

- **Branche** : `tache/T51-objets-pdf`
- **Dates** : 2026-11-17
- **Exigences couvertes** : F-61 (réalisée) ; F-84 (second tableau des révisions PDF)
- **Décisions** : ADR-0213 à ADR-0218, tous acceptés (ADR-0213, ADR-0214, ADR-0216 à ADR-0218 au début de T51, ADR-0215 pendant la revue de la PR)
- **Errata** : aucun

## Objectif

Décrire un par un les objets qu'ajoute ou remplace chaque version d'un PDF, relever les textes superposés et les polices incohérentes de ses pages (F-61). Demandée par TheDarkMac le 2026-11-17 (« T51 »), suite prévue de la V1 (découpage, §4).

## État initial

- PR [#34](https://github.com/TheDarkMac/AI-detector/pull/34) (T50). Commits : `7a0065b` (module), `79471d8` (tests), `e71ac0a` (documentation), `8dcf7a7` (PR au journal), `bc8626d` (ADR-0207 et ADR-0208 passés à « Accepté » après le « Oui, valide les deux » de TheDarkMac). CI sur `e71ac0a` : docs 43922160829 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code 43922161169 annulé (remplacé) ; sur `8dcf7a7` : docs 43922265784 en échec, comme prévu, code 43922265770 en échec seulement parce que le job `tests (macos-latest, 3.14)` a été annulé après 15 minutes sans qu'un pas ait tourné (aucun exécuteur) ; sur `bc8626d` : docs 43930750488 et code 43930750478 verts (16 vérifications, CodeRabbit ignoré).
- L'assistant a mergé la PR le 2026-11-16 à 20:15:28 UTC, après le « Oui, merge » de TheDarkMac : commit de merge `d82ba11`. Lancements de push sur `d82ba11` : docs 43947896485 vert ; code 43947896464 en échec au premier passage, seulement parce que le job `tests (macos-latest, 3.12)` n'a trouvé aucun exécuteur (« The job was not acquired by Runner of type hosted even after multiple attempts ») ; job relancé par l'assistant au début de T51 (`gh run rerun --failed`) : vert, `code-ok` compris. Empreinte du catalogue 0.11.0 : `ed79c856…815c`.
- La ligne T50 de l'index du journal portait « à venir » : corrigée en #34 dans cette tâche.
- Toujours en attente : mesure des règles de T24, T40, T41, T32 et T50 sur le corpus (T100) ; WebP et HEIC pour le dwtDct, recherche de sa grille après un recadrage ; double compression non alignée ; oracle mozjpeg jamais lancé ; coût d'import de numpy sans bytecode compilé ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 ; liste de confiance au banc ; échec unique de la première campagne de fuzzing de T24 ; champs nominatifs d'ADR-0160 ; droits DocMDP comparés aux changements, métadonnées des versions antérieures (reste à faire de T50) ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).

## Déroulé

1. Lecture du découpage, de F-61, du journal de T50, du lecteur `_lecture/pdf.py`, du module `revisionspdf`, d'ADR-0124, d'ADR-0208, d'ADR-0211 et d'ADR-0212, et du mécanisme des visualisations en tableau (modèle, schémas, export HTML).
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : lecteur du projet pour les flux de contenu ([ADR-0213](../decisions/ADR-0213-contenus-de-pages-par-le-lecteur-du-projet.md)) ; texte sur texte et caches ([ADR-0214](../decisions/ADR-0214-textes-superposes-et-caches.md)) ; familles mélangées et codes hors plage ([ADR-0216](../decisions/ADR-0216-polices-incoherentes.md)) ; objets un par un dans un tableau de `revisionspdf` ([ADR-0217](../decisions/ADR-0217-objets-changes-un-par-un.md)). Les deux options sur les textes et les polices nommaient direction et niveau (« indice faible vers la retouche ») : les règles en découlent ([ADR-0218](../decisions/ADR-0218-constats-et-versions-de-t51.md)). La mesure des textes par les largeurs déclarées et les AFM d'Adobe ([ADR-0215](../decisions/ADR-0215-mesure-des-textes.md)) est une proposition de l'assistant, au statut « Proposé ».
3. Lecteur PDF : `operations` (opérateurs et opérandes d'un flux de contenu, images en ligne passées, flux mal formé arrêté) ; `Contexte.objets`, pour s'arrêter avant le budget.
4. Largeurs des 14 polices standard : les fichiers AFM d'Adobe sont sur le poste (paquet Debian `python-matplotlib-data`), avec les conditions d'Adobe dans `/usr/share/doc/python-matplotlib-data/copyright` ; `tests/donnees/pages/generer_polices14.py` écrit `modules/pagespdf/_polices14.py` (65 Ko : largeurs par nom de glyphe, encodages de l'annexe D par fontTools 4.57.0, mentions et conditions reproduites).
5. Module `pagespdf` 0.1.0 : arbre des pages et ressources héritées ; interprétation (état graphique, état du texte, chemins, formes, apparences des annotations) ; polices simples, composites Identity-H, Type3, standard ; boîtes rangées dans une grille de cases de 16 unités ; observations par relevé avec la première page et la liste des pages.
6. Module `revisionspdf` 0.2.0 : chaque objet changé garde son état, son type et sa nature ; relevé des pages qui le désignent ; tableau `objets_revisions` émis après la chronologie. Modèle : nature `OBJETS_REVISIONS` et ses colonnes ; schéma du rapport : `visualisation_tableau` devient un choix entre deux natures ; schémas 0.9.0 ; export HTML : couverture partielle par nature (paramètre `total`), états et natures nommés, page nulle en tiret ; phrase du résumé au pluriel (« de chacune »).
7. Échantillons : environnement Python à part, dans le dossier temporaire de la session (pypdf 6.1.1, depuis PyPI). `tests/donnees/pages/generer_pages.py` écrit `document.pdf` (LibreOffice, page HTML convertie) et `ghostscript.pdf` (PostScript, polices incorporées en sous-ensembles), puis six retouches par mise à jour incrémentale (montant superposé, cache blanc, cache noir, annotation de texte libre, page fusionnée, codes hors plage) et `oracle.json` (`pdffonts` et `pdftotext -bbox` de Poppler 25.03.0). Premier essai de Ghostscript sans `-dEmbedAllFonts` : Helvetica et Times non incorporées, aucune famille mélangée possible ; options ajoutées.
8. Premier passage sur les échantillons : relevés attendus du premier coup, aucun sur `document.pdf` ni `ghostscript.pdf` (faux gras et petites capitales compris). Boîtes comparées à celles de `pdftotext` : même hauteur, largeur couverte à 92 % au moins (le mot « правда. » finit par un point posé à part).
9. Catalogue 0.12.0 : règles `R-PAGESPDF-001` à `R-PAGESPDF-004` ; description de l'en-tête réécrite pour tenir dans 1 024 caractères (1 021) ; empreinte `e953ad9e…2bca` inscrite au registre.
10. Tests : `tests/test_pages_pdf.py` (flux de contenu, boîtes, état du texte, polices et encodages, superpositions, caches, état graphique, formes, annotations, arbre des pages, limites, échantillons, oracle, règles, phrases) ; `tests/test_revisions_pdf.py` (objets un par un, types, pages désignées, tableau coupé, rendu HTML) ; attentes mises à jour (listes des modules, nombre de règles, règles de T22 et T23, version des schémas, états d'un PDF dans l'orchestration) ; fuzzing : `pagespdf` sur le PDF, deux échantillons de plus. Couverture de `pagespdf` et `revisionspdf` : 100 %. Campagne à part de 20 000 PDF mutés (graine fixe, échantillons de `pages`, `revisions` et `metadonnees`) sur le seul module `pagespdf`, messages validés par le schéma : aucun échec, aucune limite dépassée, en 100 secondes.
11. Suite complète sous coverage, en 11 minutes : 2 674 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), couverture de 100 %.
12. Rapport de `annotation.pdf` relu dans le navigateur, servi par un serveur local : constats R-PAGESPDF-001, R-PAGESPDF-002 et R-REVISIONSPDF-002, chronologie, puis tableau des objets (page remplacée, police, apparence et annotation ajoutées).
13. Documentation : ADR-0213 à ADR-0218, renvois dans ADR-0043, ADR-0124, ADR-0208 et ADR-0212 ; fiche [`pages-pdf`](../techniques/pages-pdf.md), fiche [`revisions-pdf`](../techniques/revisions-pdf.md) (0.2.0) ; modèle de données (v1.13), architecture (v1.26), découpage (v0.34), guide du catalogue (v1.13), glossaire (v1.13), matrice (F-61 réalisée, F-84 complétée), ce journal.

14. PR [#35](https://github.com/TheDarkMac/AI-detector/pull/35) ouverte (commits `f783665`, `f048a6d`, `0053e03`, `488ac75`). CI : docs 43966169623 en échec, comme prévu (ADR-0215 au statut Proposé, ADR-0129). ADR-0215 validé par TheDarkMac pendant la revue (« Oui, valide ADR-0215 ») : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Un module qui dépasse le budget perd tous ses résultats | Flux de contenu longs : chaque opérande compte un objet (ES-03, ADR-0060) | Arrêt de l'interprétation quand il ne reste que 262 144 objets, `Contexte.objets` (ADR-0213) |
| Helvetica ajoutée par un outil sans largeurs | Les 14 polices standard non incorporées peuvent ne pas en déclarer | Largeurs des AFM d'Adobe livrées avec le module (ADR-0215) |
| Polices de Ghostscript non incorporées | Réglages par défaut de `pdfwrite` | `-dPDFSETTINGS=/prepress -dEmbedAllFonts=true -dSubsetFonts=true` |
| Fichier de largeurs différent après `ruff format` | Guillemets simples écrits par le générateur | Le générateur écrit des guillemets doubles ; sortie identique à celle du formateur |
| Tableau des objets avant la chronologie dans le rapport | Ordre d'émission des visualisations | Tableau des objets émis après la chronologie |
| `version_schema` 0.8.0 dans le travail factice des tests | Version écrite en dur | Passée à 0.9.0 |
| Page de `annotation.pdf` rangée « non reconnue » par `revisionspdf` | pypdf réécrit `/MediaBox` en arrondissant ses réels à six décimales : la page change ailleurs que dans `/Annots` | Comportement attendu d'ADR-0208, qui compare les valeurs exactement ; constat R-REVISIONSPDF-002 sur cet échantillon, noté au reste à faire |

## Écarts par rapport au découpage

- Ajouté : les apparences des annotations sont interprétées avec le contenu des pages (ADR-0214), pour voir un texte posé par une annotation que T50 range parmi les ajouts permis.
- Ajouté : données de référence d'Adobe (largeurs des 14 polices standard) livrées avec le module (ADR-0215).
- Ajouté : `Contexte.objets`, premier module qui s'arrête avant son budget.

## Résultat

- Module `pagespdf` 0.1.0 ; module `revisionspdf` 0.2.0 ; catalogue 0.12.0 (empreinte `e953ad9e…2bca`) ; schémas du rapport et des messages 0.9.0.
- `vk document.pdf` d'un PDF retouché porte, s'il y a lieu, un indice faible vers la retouche par relevé (texte sur texte, cache, police en plusieurs incorporations, codes hors plage), avec la première page concernée ; le tableau des objets changés suit la chronologie dans la rubrique « Visualisations ».
- Vérification : `coverage run -m pytest`, puis `coverage combine` et `coverage report` ; `tests/test_pages_pdf.py` et `tests/test_revisions_pdf.py` seuls en une quarantaine de secondes.

## Reste à faire

- Mesure des règles de `pagespdf` sur le corpus de référence (T100) : formulaires aplatis, documents fusionnés, polices découpées en plusieurs sous-ensembles, documents réels retouchés par d'autres outils.
- Images, formes courbes et dégradés posés sur un texte ; CMap autres qu'Identity-H ; glyphes absents d'un sous-ensemble (lecture des programmes de polices).
- `revisionspdf` : comparer les réels d'un objet changé à une tolérance près, pour qu'une réécriture arrondie (pypdf) ne change pas la nature d'une page.
- Éléments actifs (T52) ; extraction des images et du texte (T53).
