# T52 — Éléments actifs d'un PDF, signalés, jamais exécutés

- **Branche** : `tache/T52-elements-actifs-pdf`
- **Dates** : 2026-11-17
- **Exigences couvertes** : F-62 (réalisée pour le PDF) ; NF-01 (contenu embarqué d'un PDF) ; ES-06 (réalisée)
- **Décisions** : ADR-0219 à ADR-0222, tous acceptés au début de T52
- **Errata** : aucun

## Objectif

Signaler les éléments actifs d'un PDF (scripts, actions automatiques, lancements, envois, fichiers incorporés) sans jamais les exécuter (F-62, NF-01), et fermer la partie PDF d'ES-06 : aucune adresse écrite dans le fichier n'est résolue (ADR-0033). Demandée par TheDarkMac le 2026-11-17 (« T52 »), suite prévue de la V1 (découpage, §4).

## État initial

- PR [#35](https://github.com/TheDarkMac/AI-detector/pull/35) (T51). Commits : `f783665` (module), `f048a6d` (tests), `0053e03` (documentation), `488ac75` (PR au journal), `6319016` (ADR-0215 passé à « Accepté » après le « Oui, valide ADR-0215 » de TheDarkMac), `b515d99` (`Contexte` importé de `_travail.contexte` dans `tests/test_pages_pdf.py`, pour mypy strict). CI : docs 43966169623 et 43966234677 en échec, comme prévu (ADR-0215 au statut Proposé, ADR-0129) ; code 43966234988 en échec sur le seul job `qualite` (mypy), tous les tests verts ; sur `b515d99`, les 16 vérifications vertes (CodeRabbit ignoré), reproductibilité 43995353546.
- L'assistant a mergé la PR le 2026-11-17 à 01:31:27 UTC, après le « Oui, merge » de TheDarkMac : commit de merge `b42bd42`. Lancements de push sur `b42bd42` : docs 43996232424 vert ; code 43996232397 vert (tous les jobs, `reproductibilite` et `code-ok` compris), terminé au début de T52. Empreinte du catalogue 0.12.0 : `e953ad9e…2bca`.
- Leçon de T51, appliquée ici : mypy lancé sur tout le dépôt (`.venv/bin/mypy` sans argument : `src`, `tests`, `banc`) avant chaque commit.
- Toujours en attente : mesure des règles de T24, T40, T41, T32, T50 et T51 sur le corpus (T100) ; WebP et HEIC pour le dwtDct, recherche de sa grille après un recadrage ; double compression non alignée ; oracle mozjpeg jamais lancé ; coût d'import de numpy sans bytecode compilé ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 ; liste de confiance au banc ; échec unique de la première campagne de fuzzing de T24 ; champs nominatifs d'ADR-0160 ; droits DocMDP comparés aux changements, métadonnées des versions antérieures (T50) ; images et courbes sur un texte, CMap autres qu'Identity-H, tolérance sur les réels d'un objet changé (T51) ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).

## Déroulé

1. Lecture du découpage, de F-62, NF-01 et ES-06, de M-07 et M-14, d'ADR-0033, ADR-0138, ADR-0166, du journal de T51, du lecteur `_lecture/pdf.py`, des modules `pagespdf`, `revisionspdf` et `infopdf`, du langage des règles et du rendu des phrases (une liste s'y écrit éléments séparés par des virgules).
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : PDF seul, bureautique renvoyée à un complément ([ADR-0219](../decisions/ADR-0219-perimetre-de-t52.md)) ; nature et déclencheur, sans adresse, nom ni code ([ADR-0220](../decisions/ADR-0220-nature-et-declencheur.md)) ; recherche depuis le catalogue de la dernière version ([ADR-0221](../decisions/ADR-0221-elements-actifs-depuis-le-catalogue.md)) ; une information neutre par famille ([ADR-0222](../decisions/ADR-0222-constats-et-versions-de-t52.md)). Précisions de l'assistant, écrites dans ces ADR : liste fermée des déclencheurs et des natures (`autre` pour un type inconnu), actions d'affichage jamais comptées automatiques, `Named` comptée, document chiffré lu par sa structure, bornes et arrêt avant le budget, parcours des pages partagé.
3. Lecteur PDF : `pages`, le parcours de l'arbre des pages écrit en T51 pour `pagespdf`, déplacé dans le lecteur ; `pagespdf._pages` l'appelle avec `PAGES_MAX`. Les 173 tests de `pagespdf` passent sans changement : sa version reste 0.1.0.
4. Module `actifspdf` 0.1.0 : catalogue (`/OpenAction`, `/AA`, arbres `/JavaScript` et `/EmbeddedFiles`, `/AF`, `/AcroForm` et `/XFA`, arbre des champs, signets), pages et annotations (`/A`, `/AA`, `FileAttachment`, `/AF`), chaînes `/Next` ; une action lue une fois, avec tous ses déclencheurs ; cinq familles observées avec leurs natures, leurs déclencheurs et leurs pages ; une partie illisible n'arrête pas les autres. Premier essai sur un PDF synthétique : relevés attendus du premier coup.
5. Défauts trouvés à la relecture, avant tout test, et corrigés : des résolutions du catalogue hors de la garde des parties (une action illisible aurait arrêté tout le module) ; une page jugée lue en entier quand une partie antérieure était déjà illisible ; le compte des actions observé à part des autres familles.
6. Catalogue 0.13.0 : règles `R-ACTIFSPDF-001` à `R-ACTIFSPDF-005` ; description resserrée pour tenir dans 1 024 caractères (1 024) ; empreinte `f11f83d2…1a85` inscrite au registre, vérifiée aussi par la commande du guide (§4).
7. Échantillons : environnement Python à part, dans le dossier temporaire de la session (pypdf 6.1.1, depuis PyPI). Essais : LibreOffice convertit une page HTML en liens `URI` ; un formulaire HTML exporté par le filtre Writer/Web devient des images, importé par le filtre Writer (`HTML (StarWriter)`) avec `ExportFormFields`, il devient des champs et un bouton `SubmitForm` (déclenché au clic, `/AA` `/D`) ; Ghostscript écrit par pdfmark un script à l'ouverture, un lien `Launch` et une pièce jointe. `tests/donnees/actifs/generer_actifs.py` écrit ces trois documents, cinq ajouts par mise à jour incrémentale (script du document, pièce jointe, adresse ouverte à l'affichage de la page, mise en forme et calcul d'un champ, paquet XFA), un document chiffré, puis `oracle.json` (`pdfinfo`, `pdfinfo -js`, `pdfdetach -list` de Poppler 25.03.0). Le chiffrement AES demande la bibliothèque `cryptography` à pypdf : RC4 de 128 bits retenu, le module ne déchiffrant rien. Premier oracle : les en-têtes des scripts de champ (« Format Field: ») n'étaient pas reconnus ; lecture par blocs séparés d'une ligne vide.
8. Premier passage sur les neuf échantillons : relevés attendus du premier coup, document chiffré compris ; `document.pdf` et `ghostscript.pdf` de T51 ne portent rien.
9. Tests : `tests/test_actifs_pdf.py` (catalogue, arbres de noms, actions du document, des pages, des annotations et des champs, chaînes, signets, XFA, fichiers incorporés, rien lu ni suivi, lecture partielle, limites, arrêt avant le budget en chacun des 21 points où il se vérifie, échantillons comparés à Poppler, règles, phrases, contrôle avant publication) ; attentes mises à jour (listes des modules, nombre de règles, règles de T22 et T23, états d'un PDF dans l'orchestration et la soumission) ; fuzzing : `actifspdf` sur le PDF, deux échantillons de plus. Couverture d'`actifspdf` : 100 %. Campagne à part de 20 000 PDF mutés (graine fixe, échantillons de `actifs`, `pages`, `revisions` et `metadonnees`) sur le seul module `actifspdf`, messages validés par le schéma : aucun échec, aucune limite dépassée, en 72 secondes.
10. Suite complète sous coverage, en 14 minutes : 2 749 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent) ; une ligne du parcours des pages restait non couverte (nœud de l'arbre écrit en flux, cas que `pagespdf` acceptait déjà) : test ajouté, couverture du lecteur PDF, de `pagespdf` et d'`actifspdf` à 100 %.
11. Rapports de `ghostscript.pdf` et `balise.pdf` relus dans le navigateur, servis par un serveur local : informations neutres R-ACTIFSPDF-001, 002, 003 et 005 pour le premier, 002 (« déclencheurs : page ; natures : URI ») et 004 pour le second, avec leurs limites ; aucune adresse dans le HTML ni le JSON (le mot « pistage » n'y vient que de la limite de R-ACTIFSPDF-004).
12. Documentation : ADR-0219 à ADR-0222, renvois dans ADR-0033, ADR-0043, ADR-0124, ADR-0126, ADR-0138, ADR-0208 et ADR-0213 ; fiche [`actifs-pdf`](../techniques/actifs-pdf.md), fiches `pages-pdf` et `metadonnees-info-pdf` (historique, renvoi) ; architecture (v1.27), découpage (v0.35), guide du catalogue (v1.14), glossaire (v1.14), matrice (F-62 et ES-06 réalisées, T52 à NF-01), ce journal. Modèle de données inchangé : aucun schéma ne change.
13. PR [#36](https://github.com/TheDarkMac/AI-detector/pull/36) ouverte vers `detector` (commits `028d4ef`, `ae3a66b`, `04d1e77`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Une action illisible du catalogue aurait arrêté le module entier | Résolutions faites avant d'entrer dans la garde des parties | Chaque partie du catalogue se résout dans sa garde (`_ouverture`, `_noms`, `_formulaire`) |
| Formulaire HTML devenu des images dans le PDF de LibreOffice | Filtre d'export Writer/Web | Import par le filtre Writer, export avec `ExportFormFields` |
| pypdf refuse de chiffrer en AES | `cryptography` absente de l'environnement des échantillons | RC4 de 128 bits ; le module ne déchiffre rien |
| Oracle sans les scripts de champ | En-têtes de `pdfinfo -js` sans le mot « Action » (« Format Field ») | Scripts lus par blocs séparés d'une ligne vide |
| Test d'une page illisible faux | Remplacer « 20 » par « x » décale le fichier d'un octet, et la table des références croisées ne se lit plus | Objet à un chiffre |
| Ligne du parcours des pages non couverte | Nœud de l'arbre des pages écrit en flux, accepté depuis T51 sans test qui passe par le lecteur | Test d'une page en flux |
| Description du catalogue trop longue (1 034 caractères) | Limite de 1 024 du schéma | Formulations resserrées, sens gardé |

## Écarts par rapport au découpage

- Ajouté : ES-06 aux exigences de T52 (déjà listée à ES-06 dans la matrice), réalisée pour le PDF.
- Ajouté : parcours de l'arbre des pages déplacé dans le lecteur PDF, partagé avec `pagespdf`.
- Retiré : macros et modèle distant des documents bureautiques, renvoyés à un complément bureautique de T52 (ADR-0219).

## Résultat

- Module `actifspdf` 0.1.0 ; catalogue 0.13.0 (empreinte `f11f83d2…1a85`) ; schémas inchangés (0.9.0) ; `pagespdf` inchangé (0.1.0).
- `vk document.pdf` d'un PDF qui porte des éléments actifs dit, en information neutre, ses scripts, ses actions automatiques et leurs déclencheurs, ses lancements, ses envois et liens, ses fichiers incorporés ; l'outil n'en exécute, n'en ouvre ni n'en résout aucun.
- Vérification : `coverage run -m pytest`, puis `coverage combine` et `coverage report` ; `tests/test_actifs_pdf.py` seul en une quarantaine de secondes.

## Reste à faire

- Complément bureautique de T52 : macros ODF et VBA, objets OLE, modèle distant d'un DOCX (ADR-0138, ADR-0219).
- Mesure des règles d'`actifspdf` sur le corpus de référence (T100) : part de documents ordinaires qui ont des liens, des scripts de formulaire, des pièces jointes (factures électroniques).
- Contenu propre des annotations multimédias (`RichMedia`, `3D`, `Screen`), qui peut porter des scripts ; paquet XFA, lu seulement par sa présence.
