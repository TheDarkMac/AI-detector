# T80 — Caractères invisibles ou substitués d'un texte, et saisie du texte collé

- **Branche** : `tache/T80-caracteres-invisibles`
- **Dates** : 2026-11-17
- **Exigences couvertes** : F-73 (réalisée pour le texte brut et le texte collé) ; F-01 (texte collé soumis) ; F-24, F-25 (manifeste C2PA d'un texte recherché) ; ES-12 (caractères relevés, neutralisés à l'affichage) ; A-29, A-43
- **Décisions** : ADR-0232 à ADR-0237, tous acceptés au début de T80
- **Errata** : aucun

## Objectif

Relever les caractères invisibles et les homoglyphes d'un texte (F-73), donner sa saisie au texte collé (A-29, renvoyée à T80 par ADR-0074), et lire le manifeste C2PA écrit dans un texte (`M-C2PA-TEXTE`, confié à T80 par T31). Demandé par TheDarkMac le 2026-11-17 (« T80 »).

## État initial

- PR [#38](https://github.com/TheDarkMac/AI-detector/pull/38) (complément bureautique de T52). Commits : `cc6221c` (module), `158e117` (tests), `6decc21` (documentation), `3e749e8` (PR au journal). Sur `3e749e8`, la CI de la PR a échoué sous macOS et Windows seulement (code 44084064704) : `test_vrai_processus_encodage_qu_expat_ne_lit_pas` attendait une lecture partielle, et le processus restreint charge encore le codec `windows-1252` sur ces deux systèmes. Corrigé par `893fe28` (le test admet une lecture entière ou partielle pour ce codec ; ERR-0012 et l'étape 14 du journal le disent). Sur `893fe28`, toutes les vérifications vertes (docs 44093102864, code 44093102731 ; CodeRabbit ignoré).
- L'assistant a mergé la PR le 2026-11-17 à 13:38:48 UTC, après le « Oui, merge si vert » de TheDarkMac : commit de merge `2356e2d`. Lancements de push sur `2356e2d` : docs 44094812639 et code 44094812628 verts, vérifiés au début de T80. Empreinte du catalogue 0.15.0 : `fbabf93b…e6ce` ; schémas 0.10.0.
- Toujours en attente : mesure des règles de T24, T40, T41, T32, T50, T51, T52, T53 et du complément bureautique sur le corpus (T100) ; WebP et HEIC pour le dwtDct, recherche de sa grille après un recadrage ; double compression non alignée ; oracle mozjpeg jamais lancé ; coût d'import de numpy sans bytecode compilé ; filigranes commerciaux de la liste C2PA ; complément de T30 ; liste de confiance au banc ; échec unique de la première campagne de fuzzing de T24 ; champs nominatifs d'ADR-0160 ; droits DocMDP comparés aux changements, métadonnées des versions antérieures (T50) ; images et courbes sur un texte, CMap autres qu'Identity-H, tolérance sur les réels d'un objet changé (T51) ; contenu des annotations multimédias, paquet XFA (T52) ; images Flate, XMP des images, règles entre modules, phrases d'absence qui disent « le fichier » pour une partie extraite (T53) ; codes de champ d'un DOCX, macros VBA qui se lancent seules, documents incorporés d'un ODT (complément bureautique de T52) ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B). `M-C2PA-TEXTE` avec T80 : traité ici.

## Déroulé

1. Lecture d'ADR-0012, ADR-0013, ADR-0070, ADR-0074, ADR-0096, ADR-0177, ADR-0206 et ADR-0223, de F-73, A-29 et A-43, de l'inventaire des marquages ; du déroulé des deux processus (`soumission`, `travail`, `principal`, `fichier`, `identification`), du contexte des modules et du module `actifsbureau`.
2. Annexe A.7 de la spécification C2PA 2.3 lue sur `spec.c2pa.org` : enveloppe `C2PATXT`, sélecteurs de variante, détection, codes d'échec. c2pa-python 0.39.0 ne déclare aucun type de texte parmi ceux qu'il lit (`Reader.get_supported_mime_types()`). Données Unicode : 18.0.0 est la dernière version finale publiée sur `unicode.org`, données de sécurité comprises (19.0.0 n'y a pas de `confusables.txt`).
3. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : texte brut et texte collé, corps des DOCX et ODT renvoyé à un complément, manifeste C2PA décrit ([ADR-0232](../decisions/ADR-0232-perimetre-de-t80.md), [ADR-0236](../decisions/ADR-0236-manifeste-c2pa-dans-un-texte.md)) ; entrée standard et empreinte du texte ([ADR-0233](../decisions/ADR-0233-saisie-du-texte-colle.md)) ; table Unicode 18.0 figée ([ADR-0234](../decisions/ADR-0234-caracteres-invisibles.md)) ; UTS #39 en information neutre ([ADR-0235](../decisions/ADR-0235-homoglyphes.md)). Précisions de l'assistant, écrites dans ces ADR et dans [ADR-0237](../decisions/ADR-0237-constats-et-versions-de-t80.md) : nom du module, familles et emplois ordinaires, découpage des mots, écriture dominante, lecture de l'enveloppe, protocole du texte collé, champ `saisie`, refus, règles.
4. Six fichiers d'Unicode 18.0.0 téléchargés dans le dossier de travail de la session, avec la licence ; `tests/donnees/caracteres/generer_unicode.py` vérifie leurs empreintes et écrit `_unicode.py` (139 Kio). Contrôles : U+0430 (a cyrillique) confusable avec le latin, U+0061 (a latin) avec le cyrillique et le grec.
5. Module `caracteres` 0.1.0 : familles, emplois ordinaires, texte des étiquettes, homoglyphes, lettres de compatibilité, enveloppe C2PATXT ; positions en octets, ligne et colonne, résolues en une passe à la fin de chaque segment. Premier essai sur une douzaine de textes construits : relevés attendus, sauf la position d'un mot qui contient un invisible, demandée après celle de l'invisible : le curseur de positions, qui avançait sans reculer, est devenu une résolution groupée.
6. Catalogue 0.16.0 : règles `R-CARACTERES-001` à `R-CARACTERES-012`, `M-C2PA-TEXTE` recherché par `caracteres` ; description resserrée pour tenir dans 1 024 caractères (1 014) ; trois gabarits refusés par le schéma (tiret bas) renommés.
7. Texte collé : `TAILLE_MAX_TEXTE`, motifs de refus, `analyser_texte`, `soumettre_texte`, `executer` sans descripteur, commande `--texte` du travail, configuration qui annonce la longueur, `lire_texte`, `FichierEnMemoire`, `identifier_texte` ; modèle (`Saisie`, nom absent), schémas 0.11.0, présentation (« aucun : texte collé »), export (nom absent). Premier essai par un tube : l'export JSON tombait sur l'absence du nom (suppression sans défaut), corrigé.
8. Tests : `tests/test_caracteres.py` (tables, encodages, positions en UTF-8 et UTF-16, blocs et segments, familles et emplois ordinaires, bornes, texte des étiquettes, homoglyphes, compatibilité, enveloppes complètes, corrompues et multiples, Hypothesis sur des textes, des octets et des enveloppes quelconques, règles et phrases, masquage et neutralisation du rapport, texte collé de bout en bout, commande, protocole) ; attentes mises à jour (listes des modules, couverture d'un PDF, marquages livrés, exemple de rapport qui citait `M-C2PA-TEXTE` non recherché, règles exclues des tests de T23, schéma 0.11.0) ; fuzzing : format `texte` et deux échantillons de plus. Défauts trouvés par les tests : remplisseurs hangûl en fin de texte jamais ordinaires ; mot de deux lettres de deux écritures sans écriture dominante ; plage de l'écriture d'un caractère vérifiée par un test qui ne pouvait échouer (retiré, la première plage commence à U+0000).
9. Mesures de durée, commande `vk` entière : 200 Mo d'anglais en 45 s ; 64 Mo de français et 64 Mo de russe dépassaient le délai de 120 s. Profil : expression des mots non ASCII qui revenait en arrière sur chaque mot, classe des lettres de compatibilité mêlant plan de base et plans astraux, espaces insécables traitées une à une. Réécriture : écritures du segment par `str.translate` et une table remplie à la demande, mots examinés seulement dans les lignes qui ont deux écritures, expressions du plan de base sans caractère astral, espaces toujours ordinaires comptées par `str.count`. Après : 64 Mo de français en 47 s, de russe en 31 s.
10. Suite complète sous coverage, premier passage, en 19 minutes 52 : 3 047 tests verts, 4 ignorés, 4 en échec : fiche et matrice pas encore écrites (attendu : les tests lisent ces fichiers, qui ne s'écrivent pas pendant la suite) ; compte des règles du catalogue de `test_incoherences.py`, qui n'ajoutait pas les douze de T80. Couverture à 99 % : l'empreinte reçue différente et le catalogue déjà chargé d'un texte collé n'étaient pas éprouvés ; une sortie de boucle d'`identifier_texte` ne pouvait pas être atteinte (texte en mémoire), réécrite. Tests ajoutés, marqueurs F-01, F-24, F-25 et ES-12 posés sur les tests qui les vérifient ; 323 tests des fichiers touchés verts, `caracteres` couvert à 100 %. Second passage, en 19 minutes 59 : 3 053 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent) ; couverture de tout le paquet et du banc à 100 %.
11. Documentation : ADR-0232 à ADR-0237 ; renvois dans ADR-0013, ADR-0036, ADR-0070, ADR-0074, ADR-0096, ADR-0158, ADR-0177, ADR-0200, ADR-0206, ADR-0223 ; fiche [`caracteres-invisibles`](../techniques/caracteres-invisibles.md) et index des fiches (où la fiche `actifs-bureau` du complément bureautique de T52 manquait aussi) ; architecture (v1.30), découpage (v0.38 : complément de T80 placé dans l'ordre de la V1), registre des arbitrages (v1.11 : A-29, A-43), modèle de données (v1.15), glossaire (v1.17), guide du catalogue (v1.17), inventaire des marquages (v1.2), matrice (F-01, F-24, F-25, F-73), index du journal, ce journal.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Caractères invisibles écrits tels quels dans les sources (forçages bidirectionnels compris) | L'outil d'écriture de l'assistant a converti les échappements `\uXXXX` du plan de base en caractères ; Ruff n'en signale qu'une partie (RUF001, ambigus) | Recherche de tout caractère hors du latin et de la typographie française dans les fichiers écrits, remis en échappements ; les ADR et les règles citent les points de code, jamais les caractères |
| `_unicode.py` réécrit par `ruff format` sur 9 000 lignes | Tables de tuples imbriqués, éclatées par le formateur | Ensembles d'écritures en chaînes, plages en triplets ; le script écrit ce que le formateur laisse tel quel |
| Lettres cerclées absentes des tables | Ce sont des symboles (So), pas des lettres | Nature retirée ; seules `<font>` et `<wide>` sont gardées |
| 64 Mo de texte non ASCII au-delà du délai | Voir l'étape 9 | Voir l'étape 9 |
| Suite complète arrêtée aussitôt lancée | Motif `.coverage.*` sans correspondance, qui fait échouer la ligne sous zsh | Fichiers retirés par `find -delete` |
| Fiche `actifs-bureau` absente de l'index des fiches | Oubli dans la PR du complément bureautique de T52 | Ligne ajoutée |
| Valeur par défaut de `$OutputEncoding` sous PowerShell non vérifiée | La page de Microsoft lue ne la donne pas | ADR-0233 ne l'affirme pas, et la renvoie à la documentation utilisateur (T103) |

## Écarts par rapport au découpage

- Ajouté : le manifeste C2PA d'un texte (`M-C2PA-TEXTE`), confié à T80 par T31 mais absent de sa ligne du découpage ; F-01 et F-24 aux exigences de T80.
- Ajouté : un complément de T80 (corps des DOCX et ODT) à l'ordre de la V1.
- Retiré : DOCX et ODT, renvoyés à ce complément (ADR-0232).

## Résultat

- Module `caracteres` 0.1.0, tables Unicode 18.0.0 ; catalogue 0.16.0 (empreinte `88ad0446…1916`) ; schémas du rapport et des messages 0.11.0.
- `vk texte.txt` dit, en information neutre, les caractères invisibles inhabituels d'un texte par famille et leurs positions, le texte caché par des étiquettes (masqué par défaut), les mots qui mêlent des lettres d'écritures confusables, les lettres de compatibilité, et l'enveloppe C2PA d'un manifeste écrit dans le texte, sans la vérifier. `vk --texte` fait de même pour un texte collé ou reçu d'un tube.
- Vérification : `coverage run -m pytest`, puis `coverage combine` et `coverage report` ; `tests/test_caracteres.py` seul en une quarantaine de secondes.

## Reste à faire

- Complément de T80 : corps des DOCX et des ODT (paragraphes, notes, en-têtes, commentaires), même analyse.
- Vérification de la signature d'un manifeste C2PA d'un texte, quand c2pa-python lira le texte brut (ADR-0236).
- Inventaire des marquages à refaire en entier avant la prochaine version du catalogue qui touche aux marquages : seule l'entrée du texte a été revue.
- Valeur par défaut de `$OutputEncoding` sous PowerShell, pour la documentation utilisateur (T103).
- Mesure des règles de `caracteres` sur le corpus de référence (T100) : part de textes ordinaires (copier-coller du web, textes bilingues) qui déclenchent chaque règle.
