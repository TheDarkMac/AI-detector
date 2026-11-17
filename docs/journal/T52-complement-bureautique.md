# T52 (complément bureautique) — Éléments actifs d'un DOCX ou d'un ODT, signalés, jamais exécutés

- **Branche** : `tache/T52-complement-bureautique`
- **Dates** : 2026-11-17
- **Exigences couvertes** : F-62 (réalisée pour le PDF, le DOCX et l'ODT) ; NF-01 (contenu embarqué d'un document bureautique) ; ES-06 (relations et références des DOCX et ODT, désormais signalées)
- **Décisions** : ADR-0228 à ADR-0231, tous acceptés au début du complément
- **Errata** : [ERR-0012](../errata/ERR-0012-encodage-xml-que-expat-ne-lit-pas.md) (encodage déclaré qu'expat ne lit pas : `xmp`, `ooxml` et `odf` en erreur)

## Objectif

Signaler les éléments actifs des documents bureautiques (macros, événements liés à une macro, objets incorporés, ressources hors de l'archive, dont le modèle distant d'un DOCX), sans jamais les exécuter, les ouvrir ni les suivre (F-62, NF-01, ES-06). ADR-0219 les avait renvoyés à ce complément ; ADR-0138 avait renvoyé le signalement du modèle distant à « T52 ou T81 ». Demandé par TheDarkMac le 2026-11-17 (« le complément bureautique de T52 »).

## État initial

- PR [#37](https://github.com/TheDarkMac/AI-detector/pull/37) (T53). Commits : `b305518` (module), `caccc74` (tests), `53f89c0` (documentation), `01cf36d` (PR au journal), `6979943` (ADR-0227 passé à « Accepté » après le « valide ces adr » de TheDarkMac), `4313ec2` (matrice régénérée : `tests/test_matrice` en échec après les derniers tests marqués de F-63). Sur `4313ec2`, les 16 vérifications vertes (CodeRabbit ignoré).
- L'assistant a mergé la PR le 2026-11-17 à 04:43:55 UTC, après le « Oui, merge » de TheDarkMac : commit de merge `b9caf0e`. Lancements de push sur `b9caf0e` : docs 44019189515 et code 44019189290 verts, vérifiés au début du complément. Empreinte du catalogue 0.14.0 : `06316d74…19bb` ; schémas 0.10.0.
- Leçon de T53, appliquée ici : `python -m banc.matrice` relancé après l'ajout de tests marqués d'une exigence.
- L'index du journal n'avait pas de ligne pour T53 : ajoutée dans ce complément.
- Toujours en attente : mesure des règles de T24, T40, T41, T32, T50, T51, T52 et T53 sur le corpus (T100) ; WebP et HEIC pour le dwtDct, recherche de sa grille après un recadrage ; double compression non alignée ; oracle mozjpeg jamais lancé ; coût d'import de numpy sans bytecode compilé ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 ; liste de confiance au banc ; échec unique de la première campagne de fuzzing de T24 ; champs nominatifs d'ADR-0160 ; droits DocMDP comparés aux changements, métadonnées des versions antérieures (T50) ; images et courbes sur un texte, CMap autres qu'Identity-H, tolérance sur les réels d'un objet changé (T51) ; contenu des annotations multimédias, paquet XFA (T52) ; images Flate, XMP des images, règles entre modules, phrases d'absence qui disent « le fichier » pour une partie extraite (T53) ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).

## Déroulé

1. Lecture d'ADR-0136 à ADR-0139, ADR-0219 à ADR-0222, du journal de T52, des modules `ooxml`, `odf` et `actifspdf`, des lecteurs ZIP et XML, de l'identification des archives (un DOCX à macros, qui a `word/document.xml`, est identifié `docx`), de M-07 et M-14.
2. Essais avec LibreOffice 25.2.3.2, piloté par son interface UNO (module Python `uno` du système) : un ODT à bibliothèque Basic et à événement `OnLoad` range ses macros dans `Basic/Standard/` et l'événement dans `content.xml` (`office:scripts` / `office:event-listeners`, `dom:load`) ; enregistré en `.docm`, il ne porte aucun projet VBA (LibreOffice n'en écrit pas depuis du Basic). Relevé des noms ODF des 34 événements du document que propose LibreOffice, dont six levés à l'ouverture. Le premier essai par une prise réseau locale est resté bloqué : liaison par un tube nommé.
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : un module `actifsbureau` pour DOCX et ODT ([ADR-0228](../decisions/ADR-0228-module-actifsbureau.md)) ; macros, objets, événements et références hors de l'archive, corps du DOCX lu par ses seules relations ([ADR-0229](../decisions/ADR-0229-elements-actifs-cherches-dans-un-docx-et-un-odt.md)) ; nature et déclencheur, sans adresse, nom ni code ([ADR-0230](../decisions/ADR-0230-nature-et-declencheur-des-elements-bureautiques.md)) ; une information neutre par famille ([ADR-0231](../decisions/ADR-0231-constats-et-versions-du-complement-bureautique-de-t52.md)). Précisions de l'assistant, écrites dans ces ADR : types de relations reconnus et leurs natures, `package` d'un graphique non compté, référence hors de l'archive (schéma, chemin absolu, chemin qui remonte au-dessus du paquet), événements du document et leurs déclencheurs, documents incorporés ordinaires (graphique, formule) lus dans le manifeste, bornes et arrêt avant le budget.
4. Lecteur XML : `parcourir`, lecture élément par élément sans garder l'arbre ; `lire_arbre` réécrit sur lui. Les 66 tests bureautiques passent sans changement.
5. Module `actifsbureau` 0.1.0 : DOCX par les relations, de proche en proche depuis le paquet, sans récursion ; ODT par les noms des entrées, le manifeste, `content.xml`, `styles.xml` et `meta.xml`. Premier passage sur les échantillons : relevés attendus du premier coup, documents ordinaires de T21 compris.
6. Catalogue 0.15.0 : règles `R-ACTIFSBUREAU-001` à `R-ACTIFSBUREAU-004` ; description resserrée pour tenir dans 1 024 caractères (1 016) ; empreinte `fbabf93b…e6ce` inscrite au registre, vérifiée aussi par la commande du guide (§4).
7. Échantillons : `tests/donnees/actifsbureau/generer_actifsbureau.py` écrit, par LibreOffice, `macros.odt`, `liens.odt` (lien, image liée, section liée, modèle, rechargement automatique), `objet.odt` (tableur incorporé), puis `liens.docx` et `objet.docx`, enregistrés en DOCX par LibreOffice, qui n'y écrit ni la section, ni le modèle, ni le rechargement ; `oracle.json` consigne ce que LibreOffice relit de chacun. Image du premier essai mal écrite (CRC faux, signalé par libpng) : PNG écrit par le script.
8. Tests : `tests/test_actifs_bureau.py` (DOCX : macros VBA et ruban, objets, relations externes de chaque type, espace strict, résolution des cibles, relations du paquet non suivies, partie absente, relations et entrées illisibles, limites, arrêt avant le budget ; ODT : macros par les entrées, événements, objets, références hors de l'archive, chiffrement, parties illisibles, arrêt avant le budget ; échantillons comparés à LibreOffice ; règles, phrases, aucune adresse au rapport, contrôle avant publication) ; attentes mises à jour (listes des modules, nombre de règles, états d'un DOCX, d'un ODT et d'un PDF, bibliothèques des modules actifs) ; fuzzing : `actifsbureau` sur DOCX et ODT, trois échantillons de plus. Couverture d'`actifsbureau` et du lecteur XML : 100 %. Défaut trouvé par les tests : l'ordre des natures mêlait celui des macros à celui des références ; une cible vide désignait le dossier de la partie.
9. Campagne à part de 20 000 documents mutés (graine fixe ; octets de l'archive, ou contenu d'une entrée avant de réécrire l'archive) sur le seul module `actifsbureau`, messages validés par le schéma : 6 échecs, tous `LookupError` sur une déclaration d'encodage XML mutée. Le même document fait tomber `ooxml` : défaut du lecteur XML partagé depuis T20, confirmé dans un vrai processus de travail, où même `windows-1252` met le module en erreur (`PermissionError` à l'import du codec). Erratum [ERR-0012](../errata/ERR-0012-encodage-xml-que-expat-ne-lit-pas.md) : `LookupError`, `ValueError` et `OSError` d'expat arrêtent la lecture comme un XML mal formé, les exceptions des rappels étant mises à part ; tests de non-régression, qui échouent sans la correction ; `xmp` 0.7.1, `ooxml` 0.3.1, `odf` 0.3.1. Test Hypothesis ajouté au fuzzing sur le nom de l'encodage déclaré. Campagne relancée après la correction : 20 000 documents, aucun échec, aucune limite dépassée, en 306 secondes.
10. Suite complète sous coverage, en 15 minutes 45 : 2 915 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent) ; couverture de tout le paquet à 100 %, `actifsbureau` et le lecteur XML compris. Après le passage de `xmp`, `ooxml` et `odf` en version corrective, les fichiers de tests qui citent leurs versions relancés : 252 tests verts.
11. Rapports de `macros.odt` et `liens.docx` produits par `vk --rapport` : R-ACTIFSBUREAU-001 et 002 pour le premier, 002 et 004 pour le second ; aucune adresse dans le HTML ni le JSON.
12. Documentation : ADR-0228 à ADR-0231, renvois dans ADR-0033, ADR-0116, ADR-0120, ADR-0136 à ADR-0139, ADR-0158, ADR-0219 à ADR-0222 ; ERR-0012 ; fiche [`actifs-bureau`](../techniques/actifs-bureau.md), fiches `metadonnees-ooxml`, `metadonnees-odf`, `metadonnees-xmp` et `actifs-pdf` (renvois, versions) ; architecture (v1.29), découpage (v0.37 : le complément manquait à l'ordre de la V1), guide du catalogue (v1.16), glossaire (v1.16), matrice (F-62, NF-01, ES-06), index du journal (T53 et ce complément), ce journal. Modèle de données inchangé : aucun schéma ne change.

13. PR [#38](https://github.com/TheDarkMac/AI-detector/pull/38) ouverte vers `detector` (commits `cc6221c`, `158e117`, `6decc21`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Script UNO bloqué | Liaison à LibreOffice par une prise réseau locale, qui ne répond pas dans le bac à sable | Liaison par un tube nommé |
| Pas de projet VBA dans le `.docm` de LibreOffice | LibreOffice n'écrit pas de VBA depuis du Basic | Projets VBA, ActiveX, OLE, modèles distants d'un DOCX vérifiés sur des documents construits par les tests |
| Ordre des natures faux dans un test | Ordre commun à toutes les familles : `autre` des macros passait devant les références | Ordre propre à chaque famille ; pour les automatiques, événements puis références |
| Cible vide résolue en dossier | Cible relative à la partie source, jointe à son dossier | Une cible qui ne nomme aucune partie est illisible (OPC) |
| Six échecs de la campagne de fuzzing | Exceptions de codec non attrapées par le lecteur XML (ERR-0012) | Lecture partielle, rappels mis à part |
| Description du catalogue trop longue (1 062 caractères) | Limite de 1 024 du schéma | Formulations resserrées |
| Index du journal sans T53 | Oubli dans la PR de T53 | Ligne ajoutée |

## Écarts par rapport au découpage

- Ajouté : le complément, absent de l'ordre de la V1 (§4), placé après T53.
- Ajouté : parcours élément par élément du lecteur XML ; correction du lecteur (ERR-0012), qui touche `xmp`, `ooxml` et `odf`.
- Retiré : codes de champ du corps d'un DOCX (ADR-0229), limites des règles.

## Résultat

- Module `actifsbureau` 0.1.0 ; catalogue 0.15.0 (empreinte `fbabf93b…e6ce`) ; `xmp` 0.7.1, `ooxml` 0.3.1, `odf` 0.3.1 (ERR-0012) ; schémas inchangés (0.10.0).
- `vk document.odt` ou `vk document.docx` d'un document qui porte des éléments actifs dit, en information neutre, ses macros, ses éléments déclenchés ou chargés sans geste de l'utilisateur et leurs déclencheurs, ses objets incorporés, ses ressources hors de l'archive ; l'outil n'en exécute, n'en ouvre ni n'en suit aucun, et aucune adresse ni aucun chemin ne figure au rapport.
- Vérification : `coverage run -m pytest`, puis `coverage combine` et `coverage report` ; `tests/test_actifs_bureau.py` seul en une quinzaine de secondes.

## Reste à faire

- Codes de champ du corps d'un DOCX (`DDEAUTO`, `INCLUDEPICTURE`, `INCLUDETEXT`).
- Macros VBA qui se lancent seules (`AutoOpen`, `Document_Open`) : demanderait de lire le projet VBA (ADR-0230).
- Documents incorporés d'un ODT (`Object 1/`) et bibliothèques Basic liées, non parcourus.
- Mesure des règles d'`actifsbureau` sur le corpus de référence (T100) : part de documents ordinaires qui ont des liens, des tableaux incorporés, des modèles d'entreprise.
