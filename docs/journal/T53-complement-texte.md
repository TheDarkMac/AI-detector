# T53 (complément texte) — Couche texte native d'un PDF, analysée par le module `caracteres`

- **Branche** : `tache/T53-complement-texte`
- **Dates** : 2026-11-19
- **Exigences couvertes** : F-63 (texte, après les images de T53), F-73 (étendue au PDF)
- **Décisions** : ADR-0243 à ADR-0247, toutes acceptées au début du complément
- **Errata** : aucun

## Objectif

Lire la couche texte native d'un PDF et l'analyser par un module texte, ce que T53 avait renvoyé à ce complément, après T80 (ADR-0223) ; dire ce que devient une page sans couche texte native (ADR-0017, ADR-0223). Demandé par TheDarkMac le 2026-11-19 (« text complement of T53 »), tâche suivante de la V1 au découpage (§4).

## État initial

- PR [#41](https://github.com/TheDarkMac/AI-detector/pull/41) (complément de T80) : toutes les vérifications vertes sur `80e0e12` (code 44243620158, docs 44243620166) ; mergée par l'assistant le 2026-11-18 à 05:44:35 UTC après le « Oui, merge » de TheDarkMac (le classifieur du mode automatique avait refusé une première tentative faute d'accord explicite) : commit de merge `20b1ec2`. Lancements de push sur `20b1ec2` : code 44246349126 et docs 44246349059 verts, vérifiés au début du complément.
- Empreinte du catalogue 0.17.0 : `ef8803d5…e253` ; schémas 0.11.0 ; `caracteres` 0.2.0 (`texte`, `docx`, `odt`).
- Toujours en attente : voir les journaux de T80 et de son complément (« Reste à faire ») ; signature d'un manifeste C2PA d'un texte ; inventaire des marquages à refaire en entier ; `$OutputEncoding` de PowerShell (T103).

## Déroulé

1. Lecture d'ADR-0017, ADR-0223, ADR-0224, ADR-0239 à ADR-0242, du lecteur PDF, de `pagespdf` (interprétation des pages, polices) et de `caracteres` (analyse par segments, positions d'un DOCX).
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : module `caracteres` étendu ([ADR-0243](../decisions/ADR-0243-couche-texte-d-un-pdf-dans-le-module-caracteres.md)) ; ce qu'un lecteur affiche et le commentaire des annotations ([ADR-0244](../decisions/ADR-0244-texte-lu-d-un-pdf.md)) ; texte invisible analysé et compté ([ADR-0245](../decisions/ADR-0245-texte-invisible-d-un-pdf.md)) ; `/ToUnicode` puis Adobe Glyph List ([ADR-0246](../decisions/ADR-0246-decodage-du-texte-d-un-pdf.md)). Puis une cinquième, l'assistant ayant vu qu'aucune raison qu'un module peut donner ne dit qu'une page n'est pas lue parce que la lecture des documents numérisés est exclue : nouvelle raison `document_numerise` retenue sur recommandation ([ADR-0247](../decisions/ADR-0247-page-sans-couche-texte-et-versions-du-complement-de-t53.md)). Précisions de l'assistant, écrites dans ces ADR : lecteur des polices partagé, découpage des codes, encodages implicites, usage privé de l'AGL écarté, seuils des espaces et des lignes, forme des positions, définition d'une page sans couche texte, observations, règle et versions.
3. Lecture des polices de `pagespdf` déplacée sans changement dans `modules/_lecture/polices.py`, ses tables `_polices14.py` dans `_lecture/` (`git mv`) : les 173 tests de `pagespdf` passent sans autre retouche que leurs imports. `generer_polices14.py` relancé vers le nouvel emplacement : fichier identique, octet pour octet.
4. Adobe Glyph List : `tests/donnees/caracteres/generer_glyphes.py` écrit `_lecture/_glyphes.py` depuis la copie que livre fontTools 4.57.0 (Debian 13), sans téléchargement, empreinte SHA-256 vérifiée ; 4 281 noms, 201 dingbats ; notice BSD d'Adobe reproduite.
5. Texte des codes (`Polices.correspondance`) et lecture du texte (`modules/caracteres/_pdf.py`), branchés dans `caracteres` 0.3.0 ; positions par page, ligne et caractère. Premier essai sur `texte.odt` exporté par LibreOffice : homoglyphe et espace cadratin relevés à leur ligne, mais les étiquettes Unicode de la note lues comme des espaces, là où `pdftotext` donne les étiquettes. LibreOffice les écrit en `/ActualText` sur des glyphes d'espaces : le texte de remplacement est suivi depuis (ADR-0246) ; texte alors identique à celui de Poppler.
6. Raison `document_numerise` : énumération du modèle, raisons d'un module (contexte et processus principal), schémas du rapport et des messages (0.12.0), phrase du rapport.
7. Échantillons : `tests/donnees/caracteres/generer_pdf.py` écrit `libreoffice.pdf` (LibreOffice 25.2.3.2), `ghostscript.pdf` (Ghostscript 10.05.1 : omicron de Symbol dans un mot latin) et `construit.pdf` (objet par objet : chaque chemin du décodage, texte invisible, forme, `/ActualText`, annotation, page d'image seule) ; `oracle_pdf.json` consigne ce qu'en extrait `pdftotext -raw` de Poppler 25.03.0. Le premier compte du texte invisible de `construit.pdf` (48 caractères au lieu de 30) a montré une erreur de l'échantillon, non du module : `3 Tr` reste dans l'état graphique après `ET` ; texte invisible entouré de `q` et `Q`.
8. Catalogue 0.18.0 : `R-CARACTERES-014` (texte invisible) ; description resserrée (1 024 caractères) ; empreinte inscrite au registre.
9. Tests : `tests/test_texte_pdf.py` (échantillons contre Poppler, mot pour mot, et ligne pour ligne pour celui de LibreOffice ; relevés et positions des échantillons ; règles sur `construit.pdf` ; noms de glyphes ; `bfchar`, `bfrange`, entrées ignorées, plages de codes ; encodages d'une police simple ; espaces et lignes ; opérateurs et opérandes invalides ; coordonnées démesurées ; texte invisible ; texte de remplacement ; formes, images, flux multiples ou illisibles ; annotations ; pages sans couche texte ; budget, document chiffré ou illisible ; `pagespdf` ne lit pas `/ToUnicode`) ; attentes mises à jour (versions, couverture d'un PDF, formats du module, compte des règles, matrice) ; fuzzing : `caracteres` sur le PDF. Un test a montré qu'un texte de remplacement écrit sans position connue ne la perdait pas pour le texte suivant : corrigé. Couverture de `_pdf.py` et de `polices.py` : 100 %.
10. Campagne de fuzzing à part, sur le seul module : 20 000 documents (graine 53), six sur dix tirés de `construit.pdf` dont un objet ou un flux décodé est muté (octets changés, jetons de contenu ou de CMap insérés, morceaux retirés ou recopiés) puis réécrit avec une table exacte, les autres des trois échantillons mutés octet par octet ; chaque message validé par le schéma des messages. Aucun échec, en 625 secondes.
11. Suite complète sous coverage, en 34 minutes 21 (la campagne de fuzzing tournait en même temps) : 3 202 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), 2 en échec, deux attentes que le complément change : `caracteres` s'applique à un PDF (`test_soumission.py`), et l'échantillon d'ImageMagick de T53, une page d'image seule, est dit sans couche texte, ce qui rend le contrôle avant publication incomplet (`test_images_pdf.py`, qui vérifie désormais que cette non menée est la seule qui compte). Les deux fichiers relancés : verts. Couverture de tout le paquet et du banc à 100 %.
12. Documentation : ADR-0243 à ADR-0247 ; renvois dans ADR-0017, ADR-0056, ADR-0215, ADR-0223, ADR-0224, ADR-0241 ; fiches [`caracteres-invisibles`](../techniques/caracteres-invisibles.md) (version 0.3.0) et [`pages-pdf`](../techniques/pages-pdf.md), index des fiches ; architecture (v1.32), découpage (v0.40), modèle de données (v1.16), guide du catalogue (v1.19), glossaire (v1.19), matrice (F-63 et F-73 réalisées), index du journal, ce journal.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Étiquettes Unicode de LibreOffice lues comme des espaces | Écrites en `/ActualText` sur des glyphes d'espaces | Texte de remplacement suivi (ADR-0246) |
| Aucune raison ne disait qu'une page n'est pas lue faute de couche texte | Liste fermée, quatre raisons pour un module | Question à TheDarkMac, raison `document_numerise` (ADR-0247) |
| Texte invisible compté en trop sur l'échantillon construit | `Tr` reste dans l'état graphique après `ET` | Échantillon corrigé (`q` … `Q`) ; le module suivait la norme |
| Noms de variables du lecteur des polices en conflit avec ceux de `pagespdf` | Fonctions `nom`, `dico`, `matrice` homonymes de variables locales | Importées sous leurs anciens noms privés dans `pagespdf`, dont le corps ne change pas |
| Caractères réels à la place des échappements `\uXXXX` | Même cause qu'au complément de T80 | Recherche de tout caractère hors du latin et de la typographie française, remis en échappements |
| Texte de remplacement sans position : le texte suivant restait sur la ligne | La position était fixée par l'écriture même | Position perdue après l'écriture, test qui le vérifie |
| Description du catalogue trop longue | 1 045 caractères pour 1 024 | Trois tournures resserrées |

## Écarts par rapport au découpage

- Le texte ne passe pas par les parties extraites qu'annonçaient ADR-0223 et ADR-0224 : il est lu par `caracteres` lui-même (ADR-0243), comme celui d'un DOCX. Renvois écrits dans les deux ADR.
- Ajouts : lecteur des polices partagé avec `pagespdf` ; texte de remplacement (`/ActualText`) ; raison `document_numerise` et schémas 0.12.0, que le découpage ne prévoyait pas.
- F-73 passe à « réalisée » : son dernier format, le PDF, est lu.

## Résultat

- Module `caracteres` 0.3.0 (`texte`, `docx`, `odt`, `pdf`) ; `pagespdf` 0.1.0 inchangé ; catalogue 0.18.0 ; schémas 0.12.0.
- `vk document.pdf` relève dans le texte des pages, de leurs formes, des apparences et des commentaires des annotations les caractères invisibles inhabituels, le texte caché par des étiquettes, les mots mêlés d'écritures confusables et les lettres de compatibilité, positions par page, ligne et caractère ; le texte invisible fait une information neutre (R-CARACTERES-014) ; une page d'image seule est dite non lue (`document_numerise`), et le contrôle avant publication incomplet, comme pour tout texte que `caracteres` n'a pas lu.

## Reste à faire

- CMap prédéfinis des écritures d'Asie de l'Est ; programme des polices (encodage propre d'une police symbolique).
- Ordre de lecture (colonnes) ; texte blanc sur blanc, minuscule, caché par une image ou hors de la page.
- Valeurs des champs de formulaire, signets ; pages des versions antérieures.
- Mesure de R-CARACTERES-014 sur le corpus de référence (T100).
