# ERR-0012 — Encodage déclaré qu'expat ne lit pas : modules `xmp`, `ooxml` et `odf` en erreur

- **Date de constat** : 2026-11-17
- **Tâche en cours** : T52 (complément bureautique)
- **Document ou élément touché** : `src/voight_kampff/modules/_lecture/arbre.py` (lecteur XML, écrit en T20 dans `modules/_lecture/xmp.py`, déplacé en T21) ; modules `xmp`, `ooxml`, `odf` ; application d'ADR-0116
- **Nature** : exécution

## Ce qui était écrit ou fait

Le lecteur XML arrêtait la lecture sur une DTD, une entité, ou une erreur d'expat (`ExpatError`), et rendait alors une lecture partielle (ADR-0116). Expat ne lit seul que UTF-8, UTF-16, ISO-8859-1 et ASCII ; pour tout autre encodage déclaré (`<?xml version="1.0" encoding="…"?>`), il demande le codec à Python, et l'exception de Python sort telle quelle de la lecture : `LookupError` pour un encodage inconnu ou un codec qui n'est pas de texte, `ValueError` pour un encodage multioctet, et, dans le processus de travail, `PermissionError` pour un codec connu que le processus restreint ne peut plus lire sur le disque (`windows-1252`, ADR-0079). Le module qui lisait la partie tombait en erreur, et tous ses résultats sur la partie étaient écartés (ADR-0060). Vérifié par `vk` sur un DOCX dont `docProps/core.xml` déclare `UTF-C`, `windows-1252` ou `shift_jis` : `ooxml` « non menée » pour erreur du module dans les trois cas.

## Ce qui est juste

Un encodage qu'expat ne lit pas arrête la lecture comme un XML mal formé : la partie est lue en partie (`format_partiel`), le module n'est pas en erreur. XMP, DOCX et ODT s'écrivent en UTF-8 ou en UTF-16 : aucun document conforme n'est touché.

## Comment l'erreur a été trouvée

La campagne de fuzzing du module `actifsbureau` (20 000 documents mutés, graine fixe) a trouvé 6 échecs, tous `LookupError('unknown encoding: …')`, sur des déclarations XML dont une lettre de `UTF-8` avait été changée. Le même document fait tomber `ooxml`, qui partage le lecteur.

## Cause

Les campagnes de fuzzing de T20 et T21 mutaient les octets des archives, rarement ceux d'une partie XML décompressée ; aucune n'a changé une déclaration d'encodage. Les tests du lecteur ne vérifiaient que les refus de DTD et d'entités et le XML mal formé.

## Correction appliquée

- Lecteur XML : `LookupError`, `ValueError` et `OSError` sortis d'expat arrêtent la lecture, comme `ExpatError`. Les exceptions des rappels (budget, imbrication, arrêt d'`actifsbureau`) sont mises à part pendant la lecture et remontent telles quelles : elles ne sont jamais prises pour une erreur d'encodage.
- Tests : `test_encodage_qu_expat_ne_lit_pas` et `test_encodage_au_codec_illisible` (`tests/test_metadonnees_bureautique.py`, `ooxml` et `odf`), `test_odt_encodage_qu_expat_ne_lit_pas` (`tests/test_actifs_bureau.py`), `test_vrai_processus_encodage_qu_expat_ne_lit_pas` (`tests/test_orchestration.py`, `windows-1252` et `UTF-C` dans un vrai processus de travail) ; ils échouent sans la correction, vérifié.
- Versions (ADR-0068, `Z` pour une correction, comme `exif` 0.1.1 pour ERR-0009) : `xmp` 0.7.1, `ooxml` 0.3.1, `odf` 0.3.1 ; rien de ce qu'ils observent d'un document lisible ne change, un document qui les faisait tomber en erreur est désormais lu en partie. Fiches `metadonnees-xmp`, `metadonnees-ooxml` et `metadonnees-odf` mises à jour.

## Prévention

- `test_lecteur_xml_encodage_declare_quelconque` (`tests/test_fuzzing.py`) : Hypothesis fait varier le nom de l'encodage déclaré, pour `ooxml`, `odf` et `actifsbureau` ; aucun ne doit tomber en erreur.
- La campagne de fuzzing de ce complément (script hors du dépôt, comme celles de T52 et de T53) mute aussi le contenu des entrées avant de réécrire l'archive ; relancée après la correction : aucun échec.
- ADR-0116 renvoie à cet erratum.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création |
