# T21 (complément 2) — Extraction bureautique : propriétés de DOCX et d'ODT

- **Branche** : `tache/T21-extraction-bureautique`
- **Dates** : 2026-11-13
- **Exigences couvertes** : F-10 (documents bureautiques, F-10 réalisée), F-14 (absence observée), F-82, ES-03, ES-05 (archives, ES-05 réalisée), ES-06 (DOCX et ODT), ES-13, ES-19, NF-09
- **Décisions** : ADR-0136 à ADR-0141 ; ADR-0136, ADR-0137 et ADR-0138 acceptés, ADR-0139, ADR-0140 et ADR-0141 proposés, à valider pendant la revue
- **Errata** : aucun

## Objectif

Dernier complément de T21 (ADR-0123) : extraire les propriétés des documents DOCX et ODT (F-10). Les ADR antérieurs adressaient à ce complément : ses propres modules (ADR-0114), le XML lu par expat comme celui de XMP (ADR-0116), l'oracle exiftool complété (ADR-0122), et la garantie que les liens et références distantes des DOCX et ODT ne sont jamais suivis (ADR-0033). Comme le complément audio et vidéo, la branche garde le préfixe de T21, avec un slug distinct.

## État initial

- PR [#21](https://github.com/TheDarkMac/AI-detector/pull/21) (complément audio et vidéo de T21). Sur `08ce03d` : docs 43377325783 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129) ; code 43377325816 annulé, remplacé par le lancement suivant. ADR-0132 et ADR-0133 validés par TheDarkMac (« Oui, les deux », 2026-11-13), passés à « Accepté » (`af2d6f6`) : docs 43377734353 et code 43377734260 verts.
- L'assistant a mergé la PR le 2026-11-13 à 06:22:58 UTC : commit de merge `eba1efd` « Merge: T21 (complément) — Extraction audio et vidéo (#21) », à l'adresse noreply (ADR-0007). Lancements de push sur `eba1efd` verts : docs 43378309635, code 43378309646.
- La ligne du complément audio et vidéo dans l'index du journal portait « à venir » : corrigée en #21 dans cette tâche.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (option B d'ADR-0129), qui demande un changement des réglages du dépôt par TheDarkMac.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire. Outils : exiftool 13.25, ffmpeg 7.1.5, ImageMagick 7.1.1-43, LibreOffice 25.2.3.2, Ghostscript 10.05.1, Poppler 25.03.0.
- `detector` à jour avec `origin/detector` (`eba1efd`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : ADR-0013, ADR-0033, ADR-0043, ADR-0070, ADR-0114 à ADR-0123, ADR-0130 à ADR-0135 ; identification des archives (`_travail/identification.py`), contexte (`Contexte.decompresser`, déjà prévu pour le deflate brut d'un ZIP), lecteur XMP, modules `xmp` et `infopdf`, tests et oracle. Essai sur le poste : LibreOffice écrit un DOCX (trois parties de propriétés) et un ODT (`meta.xml`) ; exiftool les lit (groupes `XML`, `XMP-dc`, `XMP-meta`) sans les écrire.
2. Trois questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes suivies :
   - modules : un par famille, `ooxml` et `odf` ([ADR-0136](../decisions/ADR-0136-un-module-par-famille-de-proprietes-bureautiques.md)) ;
   - lecture de l'archive : lecteur du projet plutôt que `zipfile` ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)) ;
   - relations externes et références : ni lues ni suivies, garantie testée ([ADR-0138](../decisions/ADR-0138-relations-et-references-non-suivies.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0139](../decisions/ADR-0139-parties-lues-dans-docx-et-odt.md) (parties lues et non lues, résolution des relations), [ADR-0140](../decisions/ADR-0140-noms-et-valeurs-des-proprietes-bureautiques.md) (noms, valeurs typées, données identifiantes), [ADR-0141](../decisions/ADR-0141-oracle-bureautique-par-libreoffice.md) (échantillons de LibreOffice).
3. Branche `tache/T21-extraction-bureautique` créée depuis `detector` à jour (`eba1efd`).
4. Lecteurs : `arbre` reçoit la lecture du XML par expat (DOCTYPE et entités refusés, budget), déplacée de `xmp` sans changement de comportement ; `zip` lit l'enregistrement de fin (ZIP64 compris), le répertoire central et les entrées stockées ou deflate, strictement ; `proprietes` range les propriétés et lit les types de XML Schema.
5. Modules `ooxml` et `odf` 0.1.0 (bibliothèque `expat`) ; fiches `metadonnees-ooxml` et `metadonnees-odf`.
6. Oracle : `generer_bureautique.sh` (un `.fodt` aux métadonnées choisies, converti par LibreOffice en `document.odt` et `document.docx`) ; `relire.sh` relit aussi ces deux fichiers et exclut le groupe ZIP ; test d'oracle étendu, dans les deux sens.
7. Tests :
   - `tests/bureautique.py` : parties XML d'un DOCX et d'un ODT, archives écrites par `zipfile`, et archive écrite octet par octet (ZIP64, données avant l'archive, positions relatives au fichier, en-tête local différent, entrées en double, drapeaux, méthodes) ;
   - `tests/test_metadonnees_bureautique.py` : trois parties d'un DOCX, types stricts et transitionnels, résolution des cibles, valeurs typées et listes, binaires, espaces inconnus, parties absentes ou illisibles, DTD refusée, bombe de décompression, relations externes et modèle distant sans connexion ni adresse au rapport, `meta.xml` et ses attributs, propriétés utilisateur, références `xlink` non lues, cas limites du lecteur ZIP ;
   - vrai processus de travail sur le DOCX et l'ODT de l'oracle (noms CP437, deflate, expat après les restrictions) ;
   - fuzzing : échantillons construits et échantillons de l'oracle des deux formats parmi ceux des modules de métadonnées ;
   - tests existants adaptés : liste des modules (CLI, travail, manifestes), couverture d'un PDF, bibliothèques des seuls modules actifs (expat sert désormais à trois modules).
8. Vérification locale : Ruff (format et analyse) et mypy sans remarque ; matrice régénérée ; suite complète verte avec une couverture de 100 % des lignes et des branches ; exiftool 13.25 redonne exactement `exiftool.json` ; campagne de fuzzing des modules de métadonnées à 40 000 exemples par propriété (profil temporaire, hors du dépôt), échantillons de l'oracle et construits des seize formats, DOCX et ODT compris : sans échec (10 min 38 s).
9. Documentation : ADR-0136 à ADR-0141 ; fiches ; renvois dans ADR-0013, ADR-0033, ADR-0043, ADR-0114, ADR-0116 à ADR-0120, ADR-0122, ADR-0123 ; matrice (F-10 et ES-05 réalisées, ES-06 partielle) ; découpage v0.21, architecture v1.15 ; `CONTRIBUTING.md` (§1, oracle) ; index des ADR, du journal et des fiches.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Le déplacement de la lecture XML hors de `xmp.py` emportait les classes `Propriete` et `Xmp` | Découpe du fichier entre deux repères trop éloignés, par l'assistant | Vu par Ruff avant tout commit ; classes rétablies depuis `detector` |
| Le test de la sortie d'exiftool échouait après le test d'oracle | La remise en forme des balises d'un ODT modifiait les entrées d'`exiftool.json` partagées entre les tests | Entrées copiées avant d'être remises en forme |
| Les propriétés utilisateur d'un ODT ne se retrouvaient pas chez exiftool | exiftool numérote ensemble le nom et la valeur (`Copy1`), mais pas le type, qui manque pour une propriété texte : les numéros se décalent | Paires nom et valeur seules ; type ignoré dans la comparaison (ADR-0141) |
| Une donnée binaire mal écrite avait une taille nulle | `binascii.a2b_base64` ignore, par défaut, les caractères hors de l'alphabet | Blancs retirés, puis décodage strict ; taille du texte si le décodage échoue |
| Un `meta.xml` illisible était dit absent | La présence était observée après la lecture de l'entrée | Présence observée dès que l'entrée existe ; échec de lecture non mené |
| Un test supposait que seul `xmp` employait expat | Hypothèse d'ADR-0120 vraie jusqu'ici | Le test désactive `xmp`, `ooxml` et `odf` ; conséquence consignée dans ADR-0136 |
| Attentes fausses ou appels mal formés dans les premiers tests (argument positionnel passé pour une autre partie, champ ZIP64 visé par une recherche d'octets ambiguë) | Erreurs de l'assistant en écrivant les tests | Tests corrigés ; le champ ZIP64 est cherché dans le répertoire central seulement |
| Avertissement `javaldx` de LibreOffice pendant la génération | Java absent du poste ; inutile à la conversion | Sans effet sur les fichiers ; ignoré |

Aucun de ces problèmes ne touche un élément déjà mergé.

## Écarts par rapport au découpage

- **Ajouté** : propriétés personnalisées d'un DOCX et propriétés utilisateur d'un ODT ; version d'OpenDocument ; lecteur ZIP commun ; lecture du XML commune à trois modules.
- **Écarté** : `zipfile` dans l'outil (ADR-0137) ; cibles des relations externes et références `xlink` au rapport (ADR-0138) ; corps, réglages, signatures et modifications suivies (ADR-0139).
- **Non fait** : historique d'édition (F-71, T81) ; un DOCX écrit par Word dans l'oracle (ADR-0141).
- **Inchangé** : le catalogue (0.1.0, sans règle).

## Résultat

- Un DOCX a ses propriétés principales, étendues et personnalisées au rapport, un ODT ses métadonnées (`meta.xml`) ; noms de personnes, modèle et base des liens masqués par défaut.
- Les extractions concordent avec exiftool, dans les deux sens, sur un DOCX et un ODT écrits par LibreOffice.
- Une archive malformée, ambiguë ou trop compressée le dit par une analyse non menée ou un dépassement du budget ; aucune relation n'est suivie, aucune adresse n'est au rapport.
- F-10 est réalisée : tous les formats du périmètre qui portent des métadonnées sont lus.

## Reste à faire

- T22 : signatures de générateurs (`ooxml.app.Application`, `ooxml.app.AppVersion`, `odf.meta:generator`).
- T23 : dates des propriétés, converties dans la règle qui les compare.
- T25 : textes libres des propriétés (titres, mots-clés, propriétés personnalisées).
- T52, T81 : modèle distant et liens d'un document, signatures ; historique d'édition (`TotalTime`, `cp:revision`, `meta:editing-cycles`, `meta:editing-duration`, identifiants de révision).
- Validation par TheDarkMac d'ADR-0139, ADR-0140 et ADR-0141 avant le merge (ADR-0129).
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande ; contrôle des ADR en tâche séparée (ADR-0129, option B).
