# T21 — Extraction PDF

- **Branche** : `tache/T21-extraction-pdf`
- **Dates** : 2026-11-12
- **Exigences couvertes** : F-10 (PDF), F-14 (absence observée), F-82, ES-03, ES-05 (XMP du PDF), ES-13, ES-19, NF-09
- **Décisions** : ADR-0123 à ADR-0129 ; ADR-0117 à ADR-0122 acceptés, emplacements d'ADR-0115 et réglages d'ADR-0110 validés
- **Errata** : [ERR-0008](../errata/ERR-0008-merge-de-la-pr-19.md), [ERR-0009](../errata/ERR-0009-codecs-charges-apres-les-restrictions.md)

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) (v0.18) : extraire les métadonnées du PDF (dictionnaire Info, XMP), des conteneurs audio et vidéo (balises) et des documents DOCX et ODT (propriétés), F-10. Les ADR antérieurs adressaient à T21 : l'extension de `xmp` au PDF et un module pour le dictionnaire d'information (ADR-0114), l'oracle exiftool complété (ADR-0043, ADR-0122), les analyseurs de structure écrits par le projet et leur fuzzing (ADR-0043, ADR-0082), le XML de DOCX et ODT par expat (ADR-0116). Cette branche est réduite au PDF (ADR-0123).

## État initial

- PR [#19](https://github.com/TheDarkMac/AI-detector/pull/19) (T20), ouverte le 2026-10-28 à 15:48:44 UTC. CI sur `74d3e76` verte : docs 40719733735, code 40719733948 (terminé à 16:01:33 UTC) ; CodeRabbit n'a pas relu la PR (dépôt de moins de 10 étoiles).
- Mergée le 2026-10-28 à 16:05:14 UTC depuis le compte TheDarkMac. Commit de merge `dfd0216`, à l'adresse noreply (ADR-0007), mais au titre par défaut de GitHub ; ADR-0117 à ADR-0122 encore « Proposé », emplacements d'ADR-0115 et réglages d'ADR-0110 sans validation consignée : [ERR-0008](../errata/ERR-0008-merge-de-la-pr-19.md), récidive d'ERR-0007. La ligne de T20 dans l'index du journal portait « à venir » : corrigée en #19 dans cette tâche.
- Lancements de push sur `dfd0216` réussis : docs 40722476682, code 40722476597 (terminé à 16:12:33 UTC).
- Depuis : lancements hebdomadaires du code réussis (41453428339 le 2026-11-02, 42629550684 le 2026-11-09) ; Dependabot a vérifié uv et GitHub Actions le lundi 2026-11-02 (41426698412, 41426711201), sans ouvrir de PR : la revue de Dependabot prévue ce jour-là est faite.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement. `gh pr edit` échouait à T20 : le corps d'une PR se met à jour par `gh api -X PATCH repos/TheDarkMac/AI-detector/pulls/N -F body=@fichier`.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire. Outils présents : exiftool 13.25, ImageMagick 7.1.1-43, LibreOffice 25.2.3.2, Ghostscript 10.05.1, Poppler 25.03.0 (`pdfinfo`) ; ni qpdf ni mutool.
- `detector` à jour avec `origin/detector` (`dfd0216`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : lecture du découpage, du journal de T20, d'ADR-0043, ADR-0044, ADR-0079, ADR-0114 à ADR-0122, de l'architecture (§4, §9), du module `xmp`, des lecteurs communs, du contexte, du processus de travail, des tests de T20 et de l'oracle.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes suivies :
   - périmètre : le PDF seul, l'audio et la vidéo puis DOCX et ODT en compléments ([ADR-0123](../decisions/ADR-0123-decoupage-de-t21.md)) ;
   - structure du PDF : lecteur écrit par le projet plutôt que `pypdf` ([ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md)) ;
   - PDF chiffré : reconnu, non lu, dit au rapport ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md)) ;
   - ADR de T20 : tous acceptés, et un erratum dont la prévention empêche la récidive (ERR-0008, [ADR-0129](../decisions/ADR-0129-controle-des-adr-et-du-titre-de-merge.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0125](../decisions/ADR-0125-lecture-stricte-du-pdf.md) (lecture stricte), [ADR-0127](../decisions/ADR-0127-metadonnees-pdf-lues.md) (emplacements lus), [ADR-0128](../decisions/ADR-0128-observations-du-dictionnaire-info.md) (noms et valeurs).
3. Branche `tache/T21-extraction-pdf` créée depuis `detector` à jour (`dfd0216`). ADR-0117 à ADR-0122 passés à « Accepté » ; validation des emplacements d'ADR-0115 et des réglages d'ADR-0110 consignée.
4. Essais de PDF produits par LibreOffice (table classique), ImageMagick (PDF 1.3), Ghostscript (flux de références croisées, flux d'objets) et exiftool (mise à jour incrémentale), pour voir les formes à lire.
5. Lecteur `modules/_lecture/pdf.py` : analyse lexicale (§7.2, §7.3), `startxref`, tables classiques (entrées de 19 à 21 octets), flux de références croisées (`/W`, `/Index`), sections antérieures (`/Prev`, `/XRefStm`), trailer complété, objets indirects vérifiés par numéro et génération, flux d'objets, `FlateDecode` et prédicteurs PNG et TIFF, chaînes de texte (PDFDocEncoding, UTF-16BE, UTF-8) ; fenêtres de lecture croissantes ; références suivies jusqu'au bout, boucles refusées.
6. Module `infopdf` 0.1.0 et `xmp` 0.2.0 (flux `/Metadata` du catalogue) ; fiche `metadonnees-info-pdf`, fiche `metadonnees-xmp` complétée.
7. Tests :
   - `tests/metadonnees.py` : constructeur de PDF (table ou flux, flux d'objets, prédicteur, mise à jour incrémentale) et prédicteur PNG des tests ; les échantillons construits ont été relus par exiftool et `pdfinfo` avant d'être employés ;
   - `tests/test_metadonnees_pdf.py` : formes de valeur, absence, chiffrement, tables et flux, prédicteurs, sections, objets et flux illisibles, analyse lexicale, limites ;
   - oracle : `generer_pdf.sh` (LibreOffice, Ghostscript, exiftool), `relire.sh` appelé par les deux scripts ; deux PDF comparés à exiftool dans les deux sens, `chiffre.pdf` (Ghostscript, RC4 128 bits) gardé hors de l'oracle ;
   - fuzzing : six échantillons PDF parmi ceux des modules de métadonnées ;
   - vrai processus de travail sur le PDF de Ghostscript, et sur des textes UTF-16 et JIS (ERR-0009) ;
   - tests existants adaptés : liste des modules, couverture d'un PDF, versions.
8. ERR-0009 : le premier test dans un vrai processus de travail a mis `infopdf` en erreur ; cause, un codec chargé après les restrictions ; même défaut dans `exif` (étiquettes `XP…`, commentaires `UNICODE` et `JIS`), confirmé par `vk` sur `detector`. Codecs chargés à l'import, `exif` 0.1.1, test qui échoue sans la correction.
9. Contrôle de la CI (ADR-0129) : étapes « Aucun ADR au statut Proposé » et « Titre du commit de merge » dans `lint-markdown` ; motif du titre essayé sur les titres de `detector`.
10. Vérification locale : `uv lock --check` ; Ruff (format et analyse) et mypy sans remarque ; matrice régénérée et vérifiée ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans remarque ; 1 282 tests verts, un sauté (lanceur de Windows) ; couverture 100 % des lignes et des branches ; campagne de fuzzing des modules de métadonnées, 40 000 exemples par propriété (profil temporaire, hors du dépôt), sans échec, en 18 min 32 s. Deux passages de la suite ont d'abord été faussés par des fichiers modifiés pendant qu'ils tournaient (versions, matrice, numéros de ligne) : refaits sans rien toucher.
11. Documentation : ADR-0123 à ADR-0129 ; ERR-0008, ERR-0009 ; fiche `metadonnees-info-pdf`, fiches `metadonnees-xmp` et `metadonnees-exif` ; renvois dans ADR-0006, ADR-0043, ADR-0044, ADR-0079, ADR-0114, ADR-0122 ; matrice (F-10, F-14, ES-05) ; découpage v0.19, architecture v1.13 ; `CONTRIBUTING.md` (§1, oracle ; §3, étape 6) ; index des ADR, des errata, du journal et des fiches.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Une chaîne `(R)` aurait été lue comme le mot-clé `R` | Chaînes et mots-clés représentés tous deux par des octets | Mot-clé d'un type à part (`_Mot`), comparaisons par `_est` |
| Un objet coupé par la fenêtre de lecture pouvait être lu de travers (`5 0` au lieu de `5 0 R`) | Fin du tampon prise pour une fin de mot | Tampon « complet » ou non : hors fin de partie, une lecture plus large est demandée |
| Objet qui ne contient qu'une référence, `5 0 obj 5 0 R` | Une seule résolution | Références suivies jusqu'au bout, boucles refusées |
| Échantillons des tests illisibles (descripteur fermé) | Fichier temporaire ramassé avant la lecture | Fichiers gardés ouverts jusqu'à la fin du test (fixture) |
| `infopdf` en erreur dans le vrai processus de travail | Codec UTF-16BE chargé après les restrictions ; même défaut dans `exif` de T20 | ERR-0009 |
| exiftool relève dans le groupe « PDF » des entrées du catalogue | `PageMode`, `Lang`, `Marked`, `Version`, `Count` ne sont pas du dictionnaire Info | Écartées de la comparaison (ADR-0127) |
| Dates et mots-clés différents chez exiftool | exiftool convertit les dates et sépare `Keywords` | Comparaison ramenée aux chiffres des dates, mots-clés séparés par « , » |
| Tableaux de cas de test plus longs que 100 colonnes | Littéraux d'octets écrits en une ligne | Constructeurs `section` et `section_en_flux` |
| Une affirmation sur des failles publiées de `pypdf` dans ADR-0124 | Écrite de mémoire, non vérifiable sur le poste | Retirée avant le premier commit (précédent d'ERR-0002) |

Seuls deux de ces problèmes touchent un élément déjà mergé : le merge de la PR #19 (ERR-0008) et le module `exif` (ERR-0009).

## Écarts par rapport au découpage

- **Réduit** : T21 au PDF ; audio et vidéo, puis DOCX et ODT, en compléments (ADR-0123).
- **Ajouté** : lecteur de structure PDF qui servira à T50 (ADR-0124) ; contrôle des ADR « Proposé » et du titre de merge par la CI (ADR-0129) ; correction d'`exif` (ERR-0009).
- **Écarté** : `pypdf` pour la structure (ADR-0124) ; déchiffrement (ADR-0126) ; reconstruction des tables fausses (ADR-0125).
- **Non fait** : révisions antérieures (T50) ; métadonnées des pages, images et polices (T53) ; filtres autres que `FlateDecode`.
- **Inchangé** : le catalogue (0.1.0, sans règle).

## Résultat

- Un PDF a son dictionnaire d'information et le XMP de son catalogue au rapport, `Author` masqué par défaut ; un PDF chiffré, abîmé ou incomplet le dit par une analyse non menée.
- Les extractions concordent avec exiftool sur deux PDF de structures différentes, mis à jour de façon incrémentale.
- `exif` lit dans le processus de travail les textes UTF-16 et JIS qui le mettaient en erreur.
- La CI empêche le merge d'une PR dont un ADR attend sa validation.

## Reste à faire

- Compléments de T21 : conteneurs audio et vidéo ; DOCX et ODT (XML par expat, ADR-0116) ; oracle complété.
- T50 : révisions incrémentales (le lecteur garde les sections), déchiffrement à trancher (ADR-0126).
- T22 : signatures de générateurs dans `Producer` et `Creator` ; nouvelle version du catalogue.
- T23 : dates PDF converties dans la règle qui les compare (ADR-0128).
- T25 : marquage de `Title`, `Subject`, `Keywords` (ADR-0128).
- Revue de la PR : ADR-0125, ADR-0127, ADR-0128 ; la CI reste rouge (`lint-markdown`) tant qu'ils sont « Proposé » (ADR-0129).
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
