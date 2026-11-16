# Complément de T40 — Tables de Photoshop et d'appareils

- **Branche** : `tache/T40-complement-photoshop-appareils`
- **Dates** : 2026-11-15 → 2026-11-16
- **Exigences couvertes** : F-30 (réalisée) ; F-26 (tables fixes au catalogue, sans nouvelle version de l'outil)
- **Décisions** : ADR-0191 à ADR-0196, tous acceptés (ADR-0196 validé pendant la revue de la PR)
- **Errata** : aucun

## Objectif

Relever les tables de quantification de Photoshop (niveaux 0 à 12) et de quelques appareils sur des fichiers publics de provenance établie, et les livrer au catalogue par leur empreinte (ADR-0180, ADR-0181), sans données de JPEGsnoop ni des préréglages de Pillow.

## État initial

- PR [#31](https://github.com/TheDarkMac/AI-detector/pull/31) (T42). Commits : `fe2638b` (ELA), `a536a06` (tests), `f07306c` (documentation), `6090c90` (ADR-0201 passé à « Accepté » après le « Oui, valide ADR-0201 » de TheDarkMac). CI sur `f07306c` : docs 43751480381 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code 43751480444 vert ; sur `6090c90` : docs 43752671844 et code 43752671806 verts (16 contrôles, CodeRabbit ignoré).
- L'assistant a mergé la PR le 2026-11-15 à 19:34:32 UTC, après le « Oui, merge si vert » de TheDarkMac : commit de merge `b9df73d`. Lancements de push sur `b9df73d` : docs 43753194333 et code 43753194293 verts. Catalogue 0.8.0 inchangé par T42.
- La ligne « T42 » de l'index du journal portait « à venir » : corrigée en #31 dans cette tâche.
- Le complément avait commencé le 2026-11-15, dans une session et un arbre de travail séparés : quatre questions posées à TheDarkMac et tranchées (constats et directions, métadonnées non exigées, concordance, appareils adaptatifs), relevé lancé. Cet arbre a été supprimé à la demande de TheDarkMac et le travail remis dans le dossier principal ; on a constaté pendant T42 que le relevé et les brouillons d'ADR, gardés dans le dossier temporaire de la session, avaient disparu. Il restait le manifeste du module `image` (0.3.0, direction `authenticite`), deux attentes de test, et les quatre décisions, consignées hors du dépôt. TheDarkMac a choisi de refaire le relevé (journal de T42) ; ADR-0191 et ADR-0192 ont été écrits pendant la collecte, puis le travail gardé par un commit local pendant T42.

## Déroulé

1. Relevé refait, avec ses données dans le dossier de travail du dépôt cette fois (`banc/releves/tables-T40c/`) :
   - phase 1, métadonnées de 37 006 JPEG par l'API de Commons, 216 mois de 2008 à 2025, sans `extmetadata` (trop lent sur le poste) ;
   - phase 2, en-têtes de 2 646 candidats par requêtes partielles, une toutes les 3 s ; sélection des appareils limitée, après un premier essai trop dispersé (1 à 3 fichiers par modèle), aux modèles qui ont au moins 3 fichiers de 2 comptes en phase 1.
   Le poste avait un débit d'environ 6 Ko/s le 2026-11-15, avec des coupures de la résolution de noms : scripts rendus tolérants aux coupures (journal de T42).
2. Branche rebasée sur `detector` à jour (`b9df73d`), après le merge de T42 ; un conflit dans `tests/test_cli.py` (liste des modules : `ela` et `image` 0.3.0) résolu à la main.
3. Analyse (phase 3) :
   - Photoshop : à chaque niveau, plusieurs jeux de tables, dans toutes les versions de 7.0 à CC. Les en-têtes APP14, la ressource 0x0406, le logiciel et l'année ne les séparent pas ; la taille, si : médiane de 6,7 Mpx pour un jeu, 0,4 Mpx pour l'autre au niveau 12. Le côté long sépare les deux jeux à tous les niveaux (au plus 1 296 pixels, au moins 1 305), ni le nombre de pixels, ni la largeur, ni le côté court ; un troisième jeu, d'une seule table, porte les images en niveaux de gris. Aucune empreinte commune à deux niveaux.
   - Appareils : tables communes à des familles (un jeu sur 31 compacts Canon) ; 28 modèles adaptatifs ; empreintes partagées entre marques (Nikon et Panasonic), ou vues sur des fichiers d'autres logiciels (GIMP, Picasa, Windows) ; fichiers d'appareils aux tables de Photoshop (Nikon D90).
4. Deux questions à TheDarkMac, chacune avec une recommandation, toutes deux retenues : Photoshop, tous les jeux et une règle par niveau ([ADR-0195](../decisions/ADR-0195-tables-de-photoshop.md)) ; appareils, une seule marque, jamais sur Photoshop, autres logiciels tolérés ([ADR-0194](../decisions/ADR-0194-tables-d-appareils.md)).
5. Phase 4 : sélection, licences de chaque fichier retenu par l'API (`LicenseShortName`), `tables.toml`, `fichiers.csv`, `entetes.csv`. 37 empreintes : 21 de Photoshop (niveaux 3, 5 à 12, 880 fichiers), 16 d'appareils (6 marques, 213 fichiers) ; 1 093 fichiers sources, tous sous licence libre ou dans le domaine public (CC BY et CC BY-SA, CC0, domaine public, GFDL, FAL, OGL 3, et les mentions « Attribution », « Copyrighted free use » et « No restrictions » de Commons).
6. Règles `R-IMAGE-008` à `R-IMAGE-022` écrites par un script à partir de `tables.toml` (empreintes recopiées sans saisie à la main) ; catalogue 0.9.0, description réécrite (959 caractères), empreinte `d6309484…b6c4` au registre.
7. Scripts du relevé mis au niveau de ruff et de mypy strict pour être au dépôt (`noqa: S310` motivé : adresses https fixes).
8. Tests : `tests/test_tables_relevees.py` (empreinte recalculée pour chaque jeu, règle déclenchée avec et sans EXIF, une règle par empreinte, nature des règles, concordance et licences des sources, appareils d'une seule marque) ; attentes mises à jour (directions du module `image`, nombre de règles du catalogue).
9. Documentation : ADR-0193 à ADR-0196, fiche [`structure-image`](../techniques/structure-image.md) (0.3.0), [`README` du relevé](../../banc/releves/tables-T40c/README.md), guide du catalogue (v1.10), découpage (v0.31), matrice (F-30 réalisée), ce journal.
10. PR [#32](https://github.com/TheDarkMac/AI-detector/pull/32) ouverte (commits `871481a`, `c06bc2e`, `20ece1f`, qui remplacent le commit local de travail en cours). ADR-0196 validé par TheDarkMac pendant la revue (« Oui, valide ADR-0196 ») : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Premier relevé et brouillons d'ADR perdus | Gardés dans le dossier temporaire d'une session, effacé avec elle | Relevé refait ; données et scripts dans le dépôt (ADR-0193) |
| Collecte lente, coupures | Débit du poste, résolution de noms | Lectures partielles, nouveaux essais sans abandon |
| « Discordance sans explication » à chaque niveau de Photoshop | Deux jeux selon la taille de l'image, un jeu pour le gris | Explication trouvée dans les données, question posée (ADR-0195) |
| Erreur 414 à la lecture des licences | 50 titres de fichiers par requête, adresse trop longue | 15 titres par requête |
| Compte des appareils annoncé faux dans la question | Le chiffrage de la question (22 empreintes, 7 marques, 235 fichiers) n'écartait pas encore les fichiers des modèles adaptatifs ; la sélection, si : 16 empreintes, 6 marques (sans Nikon), 213 fichiers | Critère inchangé ; écart consigné ici et dans ADR-0194, et signalé à TheDarkMac |
| Tournures fausses dans les règles générées (« l'un des 1 jeu ») | Gabarit du script | Corrigées avant tout commit |

## Écarts par rapport au découpage

- Livré par niveau de Photoshop et par marque d'appareil, pas par modèle : les tables sont communes à des familles.
- Données du relevé au dépôt, ce que le découpage ne prévoyait pas (ADR-0193).

## Résultat

- Module `image` 0.3.0 (direction `authenticite`) ; catalogue 0.9.0, quinze règles ; schéma du rapport inchangé (0.7.0).
- Vérification : `tests/test_tables_relevees.py` ; suite complète sous coverage.

## Reste à faire

- Mesurer les règles de tables sur le corpus (T100).
- Relevés plus larges (autres appareils, autres logiciels, niveaux 0, 1, 2 et 4 de Photoshop) avec les mêmes scripts.
- Comparer les tables à l'appareil déclaré dans l'EXIF : point ouvert de l'architecture (§12).
