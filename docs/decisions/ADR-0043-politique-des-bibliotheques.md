# ADR-0043 — Politique des bibliothèques : Python pur d'abord

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : NF-01, NF-06, NF-16 ; ES-05, ES-18 ; menaces M-01, M-04, M-19, M-31 ; ADR-0011, ADR-0023, ADR-0034

## Contexte

Chaque bibliothèque qui lit le fichier est une surface d'attaque (M-01), une source possible de requête non inventoriée (M-19) et un maillon de la chaîne d'approvisionnement (M-31). ES-18 demande peu de dépendances et, à fonction égale, des analyseurs écrits dans un langage sûr pour la mémoire ; ADR-0011 exclut les licences copyleft fortes. Pour la V1, la plupart des analyses lisent des **structures** (segments JPEG, blocs PNG, boîtes ISOBMFF, xref PDF, ZIP et XML) sans décoder d'image, de son ni de vidéo (ADR-0012).

## Options envisagées

### Option A — Python pur d'abord

- Avantages : le code qui lit le fichier est, pour l'essentiel, sûr pour la mémoire et maîtrisé ; peu de dépendances ; chaque analyseur fait exactement ce que sa fiche décrit.
- Inconvénients : analyseurs à écrire et à tester (fuzzing, ES-19) ; couverture des cas rares moindre qu'une bibliothèque mûre.

### Option B — Bibliothèques établies partout

- Avantages : couverture plus large, plus vite.
- Inconvénients : beaucoup de C et de C++ exposés au fichier ; dépendances nombreuses ; comportements implicites (accès réseau, correction silencieuse de fichiers malformés) à neutraliser un par un.

### Option C — Tout écrire

- Avantages : aucune dépendance.
- Inconvénients : irréaliste pour C2PA (cryptographie, COSE, X.509, suivi de la spécification) ; une cryptographie maison est une faille probable.

## Décision

1. **Analyseurs de structure écrits par le projet**, en Python pur, quand le format se lit sans décodage : segments et tables de quantification JPEG, blocs PNG, conteneurs WebP (RIFF) et ISOBMFF (HEIC, MP4, MOV, M4A), révisions et xref PDF.
2. **Bibliothèque tierce** seulement quand l'écrire serait déraisonnable. Candidates pour la V1 :

   | Besoin | Bibliothèque | Licence | Langage | Tâche |
   | --- | --- | --- | --- | --- |
   | C2PA | `c2pa-python` (liaison de l'implémentation de référence) | Apache-2.0 ou MIT | Rust | T30 |
   | XML (XMP, DOCX, ODT) | `defusedxml` | PSF-2.0 | Python | T20, T21 |
   | Objets PDF | `pypdf` | BSD-3-Clause | Python | T50 à T53 |
   | Expressions régulières | `google-re2` (ADR-0039) | BSD-3-Clause | C++ | T15 |
   | Validation par schéma | `jsonschema` | MIT | Python | T11, T15 |
   | Calcul numérique | `numpy` | BSD-3-Clause | C | T40, T41 |

   La bibliothèque standard couvre le reste : `zipfile`, `hashlib`, `tomllib`, `json`, `struct`, `argparse`.
3. **Critères d'admission** d'une dépendance, vérifiés et consignés dans la PR qui l'ajoute : licence compatible avec Apache-2.0, sans copyleft fort ; maintenue ; aucun accès réseau, ou désactivable ; exécutée dans le processus de travail si elle lit le fichier ; arbre de dépendances examiné.
4. **Exclues** : les bibliothèques sous GPL ou AGPL (par exemple `mutagen`, PyMuPDF) ; tout lecteur qui résout des entités externes ou suit des liens.
5. **exiftool** sert seulement d'**oracle de test** : les tests de T20 et T21 comparent les métadonnées extraites aux siennes. Il n'est ni livré ni appelé par l'outil.
6. Le **choix final** de chaque bibliothèque est fait par la tâche qui l'utilise, selon ces critères ; un écart à cette liste est consigné dans l'ADR de la tâche.

## Raisons

- Option A retenue : elle réduit la part de code non sûr exposée au fichier à ce qui ne peut raisonnablement pas être écrit, et garde le contrôle de ce que fait chaque analyseur.
- Option B écartée : surface d'attaque et dépendances disproportionnées pour des lectures de structure.
- Option C écartée : C2PA.
- exiftool comme oracle : c'est la référence de fait pour les métadonnées ; il vérifie les analyseurs du projet sans être embarqué (Perl, dépendance système).

## Conséquences

- T20, T21, T40 et T50 écrivent leurs analyseurs de structure et les soumettent au fuzzing (ES-19).
- T41 (double compression) demande les coefficients DCT, qu'aucune des bibliothèques citées ne fournit : décodage entropique en Python avec `numpy`, ou autre bibliothèque, à trancher en T41.
- `jsonschema` et `c2pa-python` tirent leurs propres dépendances (dont du Rust) : T10 les examine.
- La rubrique Versions du rapport liste ces bibliothèques (ADR-0023).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
