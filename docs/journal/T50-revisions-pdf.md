# T50 — Révisions incrémentales d'un PDF et leur chronologie

- **Branche** : `tache/T50-revisions-pdf`
- **Dates** : 2026-11-16
- **Exigences couvertes** : F-60 (réalisée) ; F-84 (chronologie des révisions PDF)
- **Décisions** : ADR-0207 à ADR-0212 ; ADR-0209 à ADR-0212 acceptés au début de T50, ADR-0207 et ADR-0208 proposés, à valider pendant la revue de la PR
- **Errata** : aucun

## Objectif

Reconstituer les versions successives d'un PDF enregistré par mises à jour incrémentales, distinguer les ajouts légitimes (linéarisation, signature électronique, formulaire rempli) et rendre leur chronologie (F-60, F-84). Demandée par TheDarkMac le 2026-11-16 (« T50 »), suite prévue de la V1 (découpage, §4).

## État initial

- PR [#33](https://github.com/TheDarkMac/AI-detector/pull/33) (T32). Commits : `11e3484` (lecteur), `118c1c8` (tests), `e2fec35` (documentation), `ced6488` (ADR-0206 passé à « Accepté » après le « Oui, valide ADR-0206 » de TheDarkMac), `913a584` (ligne vide manquante du journal : le lancement docs 43902313641 sur `ced6488` avait échoué sur markdownlint, MD022 et MD032). CI sur `e2fec35` : docs 43872918489 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code 43872918818 vert ; sur `913a584` : docs 43902411718 et code 43902411668 verts.
- L'assistant a mergé la PR le 2026-11-16 à 16:13:43 UTC, après le « Oui, merge » de TheDarkMac : commit de merge `ed03aa7`. Lancements de push sur `ed03aa7` : docs 43905153361 et code 43905153086 verts (le second vérifié au début de T50). Empreinte du catalogue 0.10.0 : `9e468b01…5ab2`.
- La ligne T32 de l'index du journal portait « à venir » : corrigée en #33 dans cette tâche.
- Toujours en attente : mesure des règles de T24, T40, T41 et T32 sur le corpus (T100) ; WebP et HEIC pour le dwtDct, recherche de sa grille après un recadrage ; double compression non alignée ; oracle mozjpeg jamais lancé ; coût d'import de numpy sans bytecode compilé ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 ; liste de confiance au banc ; échec unique de la première campagne de fuzzing de T24 ; champs nominatifs d'ADR-0160 ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).

## Déroulé

1. Lecture du découpage, de F-60 et F-84, du journal de T21 (PDF), du lecteur `_lecture/pdf.py`, d'ADR-0124 à ADR-0127 et d'ADR-0200. Le lecteur suivait déjà la chaîne `/Prev` et les sections hybrides, sans les exposer.
2. Essai sur un PDF linéarisé par Ghostscript (`-dFastWebView`) puis mis à jour par exiftool : le dernier `startxref` désigne la table de la première page, dont `/Prev` désigne la table principale ; la mise à jour désigne la table de la première page (ADR-0207).
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : chronologie en tableau ([ADR-0212](../decisions/ADR-0212-chronologie-en-tableau.md)) ; signatures par leur structure ([ADR-0209](../decisions/ADR-0209-signatures-pdf-par-leur-structure.md)) ; une information neutre et deux indices ([ADR-0211](../decisions/ADR-0211-constats-et-versions-de-t50.md)) ; rien déchiffré ([ADR-0210](../decisions/ADR-0210-versions-d-un-pdf-chiffre.md)). Le regroupement des sections ([ADR-0207](../decisions/ADR-0207-versions-d-un-pdf.md)) et le classement des objets ([ADR-0208](../decisions/ADR-0208-nature-d-une-version.md)) sont des propositions de l'assistant.
4. Lecteur PDF : `Section` (position, forme, trailer, fin de la marque `%%EOF`, complément en flux), `Document.chaine`, `Document.entrees`, `Document.entree`, `Document.vue`, `Document.premier_objet` ; comportement des modules `infopdf` et `xmp` inchangé.
5. Module `revisionspdf` 0.1.0 ; modèle : `Visualisation.tableau`, `COLONNES`, nature `chronologie_revisions` ; `Contexte.visualiser_tableau` ; export JSON et HTML ; schémas 0.8.0 ; textes du rapport.
6. Oracle : environnement Python à part, dans le dossier temporaire de la session (pyHanko 0.38.1, pyhanko-certvalidator 0.33.0, cryptography 50.0.2, depuis PyPI) ; `pdfsig` de Poppler 25.03.0 du poste. `tests/donnees/revisions/generer_revisions.py` écrit huit échantillons (Ghostscript, LibreOffice, exiftool, pyHanko ; clé de signature tirée à chaque génération, non gardée) et `oracle.json`.
7. Premiers essais du classement sur les échantillons, trois corrections : la clé `/Version` du catalogue, que pyHanko passe à 2.0, puis `/Extensions` (extension ISO 32002), comptées comme structure ; l'apparence vide que pyHanko écrit sans plus la désigner, trouvée par le parcours des objets orphelins (ADR-0208, points 6 et 7). Tous les échantillons sont alors classés comme attendu. Une première version comparait les entrées dans la vue de la version, aux rangs décalés : corrigée avant les tests.
8. Catalogue 0.11.0 : règles `R-REVISIONSPDF-001` à `R-REVISIONSPDF-003` ; le chargeur exige un calibrage pour toute règle à seuil, ajouté à la première ; description raccourcie pour tenir dans 1 024 caractères (liste des encodeurs de T40 retirée).
9. Rapport d'un PDF signé puis modifié relu dans le navigateur du poste : tableau sous son avertissement, natures nommées, nombres groupés.
10. Tests : `tests/test_revisions_pdf.py` (lecteur, module, linéarisation, signatures, oracle, modèle, exports, règles, contrôle avant publication) ; attentes mises à jour (listes des modules, nombre de règles, règles de T22 et T23, version des schémas, analyse d'un PDF sans table) ; fuzzing : `revisionspdf` sur le PDF, deux échantillons de plus. Campagne à part de 20 000 PDF mutés sur le seul module `revisionspdf` : aucun échec, en 7 minutes.
11. Revue de robustesse du module avant la campagne : un `/Type` ou un tableau `/Annots` de forme inattendue, des listes de plus de 4 096 versions, une entrée illisible pendant l'énumération ; corrigés avant les tests.
12. Suite complète sous coverage, en 14 minutes : 2 484 tests verts, 4 ignorés, couverture de 100 % ; deux échecs, des attentes de `tests/test_orchestration.py` qui ne connaissaient pas encore `revisionspdf` sur un PDF : corrigées, le fichier relancé (80 tests verts).
13. Documentation : ADR-0207 à ADR-0212, renvois dans ADR-0120, ADR-0126 et ADR-0200 ; fiche [`revisions-pdf`](../techniques/revisions-pdf.md) ; modèle de données (v1.12), architecture (v1.25), découpage (v0.33), guide du catalogue (v1.12), glossaire (v1.12), matrice (F-60 réalisée, F-84 complétée), ce journal.

14. PR [#34](https://github.com/TheDarkMac/AI-detector/pull/34) ouverte (commits `7a0065b`, `79471d8`, `e71ac0a`). ADR-0207 et ADR-0208 restent au statut « Proposé » jusqu'à la revue : le job docs échoue d'ici là, comme prévu (ADR-0129).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Signature de pyHanko non reconnue | Clés `/Version` et `/Extensions` du catalogue, apparence orpheline | Clés comptées comme structure ; objets orphelins cherchés depuis le catalogue (ADR-0208) |
| Entrées d'une version introuvables | Rangs de la chaîne pris dans une vue, décalés | Entrées lues dans le document entier |
| Règle refusée par le chargeur | Calibrage obligatoire pour une règle à seuil | Calibrage « manuel » décrit |
| Description du catalogue trop longue | 1 044 caractères pour 1 024 | Liste des encodeurs retirée |
| Écarts avec pyHanko | Linéarisation comptée en deux révisions ; annotation rangée en « OTHER » | Écarts attendus, vérifiés par les tests et dits par la fiche |
| Rapport local non affiché par le navigateur du poste | Page d'un fichier local, non inspectable | Rapport servi par un serveur local le temps de la relecture |
| Deux tests de l'orchestration en échec dans la suite complète | Attentes écrites avant `revisionspdf` (module absent des états d'un PDF) | Attentes complétées, fichier relancé |
| Statut du modèle de données et du glossaire resté à la v1.10 | Non mis à jour par T42 et T31 | Corrigés (v1.12) |

## Écarts par rapport au découpage

- Ajouté : la visualisation en tableau, nouvelle forme dans le modèle (ADR-0212), alors qu'ADR-0200 prévoyait une nature de plus sans nouveau mécanisme.
- Ajouté : la lecture des signatures par leur structure et l'observation des droits DocMDP, nécessaires pour distinguer la signature et ce qui la suit.
- Reporté à T51 : la description des objets ajoutés ou remplacés, un par un (F-61).

## Résultat

- Module `revisionspdf` 0.1.0 ; catalogue 0.11.0 (empreinte `ed79c856…815c`) ; schémas du rapport et des messages 0.8.0.
- `vk document.pdf` d'un PDF mis à jour porte une information neutre, la chronologie des versions dans la rubrique « Visualisations », et un indice faible vers la retouche si une version change des objets non reconnus, un second si c'est après une signature.
- Vérification : `uv run --locked coverage run -m pytest`, puis `coverage combine` et `coverage report` (100 %) ; `tests/test_revisions_pdf.py` seul en une vingtaine de secondes.

## Reste à faire

- Mesure des règles sur le corpus de référence (T100) ; documents réels signés par d'autres logiciels (Acrobat, LibreOffice) au banc.
- Objets ajoutés ou remplacés décrits un par un, textes superposés, polices (T51) ; éléments actifs (T52) ; métadonnées des versions antérieures, qui peuvent garder ce qu'une version ultérieure semble avoir retiré.
- Comparer les droits DocMDP aux changements ; vérifier les signatures (aucune tâche de la V1).
