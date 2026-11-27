# ERR-0014 — Description du corpus de référence : total des parties faux

- **Date de constat** : 2026-11-26
- **Tâche en cours** : T101
- **Document ou élément touché** : `docs/verification/corpus-de-reference.md` v1.0 (§1 et ligne « Total » du tableau par catégorie et partie) ; `docs/journal/T100-constitution-du-corpus.md` (« Résultat ») ; repris par la description de la PR [#49](https://github.com/TheDarkMac/AI-detector/pull/49), mergée, laissée telle quelle, et, avant correction, par `docs/decisions/ADR-0277-banc-en-parallele-avec-reprise.md` et le journal de T101
- **Nature** : documentation

## Ce qui était écrit ou fait

« 6 734 fichiers […] ; **4 509 en évaluation**, 2 225 en calibrage », et la ligne « Total » du tableau par catégorie et partie : 4 509 en évaluation, 2 225 en calibrage. Les lignes de chaque catégorie, elles, étaient justes.

## Ce qui est juste

4 467 fichiers en évaluation et 2 267 en calibrage : la somme des lignes du tableau (2 385 + 424 + 1 294 + 273 + 91, et 1 212 + 216 + 655 + 134 + 50), et le compte du manifeste. Le total général, 6 734, était juste.

## Comment l'erreur a été trouvée

La première passe de T101 a évalué 4 467 fichiers de la partie évaluation, et non les 4 509 annoncés ; le manifeste, relu, en compte bien 4 467.

## Cause

Les totaux de la description ont été écrits à la main, et non tirés du manifeste ; les tests de T100 vérifiaient l'accord d'`effectifs.json` avec le manifeste, pas celui de la description.

## Correction appliquée

- `docs/verification/corpus-de-reference.md` : §1 et ligne « Total » corrigés, historique v1.1.
- `docs/journal/T100-constitution-du-corpus.md`, `ADR-0277` et le journal de T101 : nombre corrigé, renvoi à cet erratum.
- Aucune mesure n'est touchée : le banc lit le manifeste, jamais la description.

## Prévention

`tests/test_corpus_reference.py::test_description_accordee_au_manifeste` relit le tableau par catégorie et partie de la description, total compris, et la phrase du §1, et les compare au manifeste. Vérifié : le test échoue sur la version 1.0 de la description.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-26 | Création |
