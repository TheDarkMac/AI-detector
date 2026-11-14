# T31 — Filigranes invisibles : inventaire, point d'extension du catalogue, marquages recherchés

- **Branche** : `tache/T31-filigranes-invisibles`
- **Dates** : 2026-11-14
- **Exigences couvertes** : F-25 ; F-24 en partie (point d'extension, lecteur en T32)
- **Décisions** : ADR-0174 à ADR-0179, tous acceptés
- **Errata** : aucun

## Objectif

Recenser les filigranes invisibles dont un lecteur public et non neuronal existe, ouvrir un point d'extension du catalogue pour les marquages, et lister au rapport les marquages recherchés, pour borner la portée d'un résultat négatif (F-24, F-25, ADR-0012).

## État initial

- PR [#27](https://github.com/TheDarkMac/AI-detector/pull/27) (T30). Commits poussés après l'ouverture : `06268ef` (adresse d'un manifeste distant masquée, ADR-0173) ; `bb7a455` (`.gitattributes` pour les PEM livrés, et première tentative de correction sous macOS, fausse) ; `452e514` (ADR-0164, ADR-0169 à ADR-0172 passés à « Accepté » après le « Oui, les cinq » de TheDarkMac) ; `c02d10d` (test de diagnostic temporaire sous macOS, retiré ensuite) ; `5e30d6e` (correction réelle sous macOS : flux c2pa créé à l'import et gardé vivant, pour les trampolines de libffi sous Seatbelt, Python 3.12 et 3.13). ADR-0164 à ADR-0173 tous acceptés.
- CI sur `5e30d6e` : docs 43588354143 verte ; code 43588354122 verte après relance de macOS 3.12 (téléversement d'un artefact en échec, `ENOTFOUND`, incident de GitHub).
- L'assistant a mergé la PR le 2026-11-14 à 11:16:23 UTC, après le « ok, c est vert, alors merge » de TheDarkMac : commit de merge `c2a1afe`, à l'adresse noreply (ADR-0007). Lancements de push sur `c2a1afe` : docs 43589229780 et code 43589229776 verts.
- Toujours en attente : complément de T30 (requêtes de P1 sur confirmation, RS-01, RS-02, ADR-0166) ; le banc n'inscrit pas la liste de confiance ; échec unique de la première campagne de fuzzing de T24, non reproduit ; ORGANIZATION de Vorbis et Source de l'IPTC non marquées nominatives (ADR-0160) ; messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).
- `detector` à jour avec `origin/detector` (`c2a1afe`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : F-24 à F-26, A-03, A-21, A-35 ; ADR-0012, ADR-0016, ADR-0021, ADR-0043 ; modèle (`Couverture.marquages_recherches`, vide depuis T11), chargeur du catalogue, manifestes, rendu de la couverture.
2. Inventaire sur sources primaires, consigné dans l'[inventaire des marquages](../catalogue/inventaire-des-marquages.md) : code d'invisible-watermark (`maxDct.py`, `watermark.py`, `setup.py`), scripts de CompVis, de Stability-AI (generative-models), de Black Forest Labs (FLUX.1) et de diffusers ; liste C2PA des liaisons souples (28 entrées, empreinte consignée) ; spécification C2PA 2.2 et 2.3 (annexe A.7, texte brut) ; dépôts et articles de TrustMark, Video Seal, AudioSeal, Watermark Anything, InvisMark, WavMark, SynthID Text, Kirchenbauer et al., Stable Signature, Tree-Ring, audiowmark ; presse pour le portail SynthID Detector. Résultat : un seul filigrane lisible sans réseau de neurones ni clé, le dwtDct.
3. Trois questions à TheDarkMac, en un lot, chacune avec une recommandation ; les trois recommandations retenues : lecteur dwtDct dans une tâche à part, T32 ([ADR-0174](../decisions/ADR-0174-inventaire-et-lecteur-dwtdct.md)) ; marquages de provenance, sans les signatures de générateurs ([ADR-0176](../decisions/ADR-0176-marquages-de-provenance.md)) ; marquages connus non recherchés au rapport, avec leur raison ([ADR-0177](../decisions/ADR-0177-marquages-non-recherches-au-rapport.md)). Les autres choix, faits par l'assistant, ont été soumis dans la PR et validés par TheDarkMac pendant sa revue (« Yes, all four », 2026-11-14) : [ADR-0175](../decisions/ADR-0175-marquages-au-catalogue.md), [ADR-0178](../decisions/ADR-0178-couverture-des-marquages.md), [ADR-0179](../decisions/ADR-0179-versions-de-t31.md), et le statut V1 de T32, après T40 et T41 (ADR-0174).
4. Branche `tache/T31-filigranes-invisibles` créée depuis `detector` à jour (`c2a1afe`).
5. Modèle : `RaisonNonRecherche`, `MarquageNonRecherche`, `Couverture.marquages_non_recherches`, `VERSION_SCHEMA` 0.6.0 ; schéma du rapport et des messages.
6. Catalogue : schéma `marquages`, format 3, `marquages.toml` lu par le chargeur, limite `MARQUAGES_MAX` ; `_marquages.py` (entrée du catalogue et calcul de la couverture) ; calcul dans la soumission, `Analyse.marquages` et ses contrôles.
7. Rendu : rubrique Couverture du HTML (liste des recherchés, tableau des non recherchés), lignes du terminal, `vk --regles` ; textes, libellés des raisons et des natures, deux termes au glossaire du rapport.
8. Catalogue livré 0.6.0 au format 3 : dix marquages, deux recherchés (`M-C2PA`, `M-IPTC-DST`), huit non recherchés ; empreinte au registre.
9. Tests : `tests/test_marquages.py` ; attentes mises à jour (version du schéma dans le processus de travail factice, rapport des tests, `vk --regles`, format inconnu du catalogue).
10. Documentation : inventaire ; guide du catalogue, modèle de données, architecture, glossaire, découpage (T32 ajoutée) ; matrice (F-24, F-25) régénérée.
11. PR [#28](https://github.com/TheDarkMac/AI-detector/pull/28) ouverte ; étape docs « Aucun ADR au statut Proposé » en échec, comme prévu (ADR-0129). ADR-0175, ADR-0178, ADR-0179 et le statut V1 de T32 validés par TheDarkMac (« Yes, all four ») : statut « Accepté ».

## Vérification

- Ruff (format et analyse) et mypy sans remarque.
- Premier passage complet, sans coverage : 17 échecs et 34 erreurs sur 1 948 tests, tous des attentes à mettre à jour (voir « Problèmes rencontrés »).
- Second passage complet, mesuré par coverage comme en CI : 1 980 tests verts et un ignoré (lanceur de l'environnement virtuel), en 11 min 30 s ; couverture de 100 %. Lint Markdown sans erreur, liens relatifs vérifiés ; matrice régénérée.
- Essai sur le poste : `tests/donnees/metadonnees/photo.jpg` ; `M-C2PA` et `M-IPTC-DST` recherchés, cinq filigranes d'image non recherchés avec leur raison ; avec `--desactiver c2pa`, `M-C2PA` non recherché pour `technique_non_menee`, au terminal et dans le HTML.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Le processus de travail factice rendait `message_invalide` | Il écrit la version du schéma en clair (`0.5.0`) | Version 0.6.0 dans `travail_factice.py` et `test_travail.py` |
| Le rapport des tests citait des marquages hors catalogue (`c2pa`, `iptc.digital_source_type`) | Identifiants libres, écrits avant que le catalogue ait des marquages | Identifiants du catalogue livré ; l'analyse des tests joint leurs entrées |
| Description du catalogue au-delà de 1 024 caractères | Phrase de T31 ajoutée à une description déjà longue | Phrase raccourcie |
| Le dépôt d'origine de Stable Diffusion 2 répond 404 | Dépôt retiré ou renommé | Message « SDV2 » non retenu : seules des copies l'attestent |
| Le README d'audiowmark ne dit pas si une clé est obligatoire | Documentation muette sur la clé par défaut | Inventaire limité à ce que dit le README : clé recommandée, sans laquelle un message ainsi posé ne se lit pas |

## Écarts par rapport au découpage

- **Ajouté** : marquages connus non recherchés au rapport (ADR-0177) ; raison `technique_non_menee` (ADR-0178) ; tâche T32, lecteur dwtDct.
- **Reporté** : lecteur dwtDct (T32) ; manifeste C2PA dans un texte brut (T80).
- **Non fait** : examen un par un des filigranes commerciaux de la liste C2PA des liaisons souples (inventaire, §5).

## Résultat

- Le rapport d'un fichier liste les marquages recherchés et les marquages connus qui pourraient s'y trouver sans être recherchés, avec la raison de chacun ; un résultat négatif dit ainsi ce qu'il ne couvre pas (SynthID, TrustMark, etc.).
- Un marquage s'ajoute au catalogue sans changer le moteur ; un catalogue fourni peut en porter.

## Reste à faire

- T32 : lecteur dwtDct (décodage des pixels avec T40 et T41, seuil et faux positifs mesurés).
- T80 : manifeste C2PA dans un texte brut (`M-C2PA-TEXTE`).
- Refaire l'inventaire avant chaque version du catalogue qui touche aux marquages ; examiner les filigranes commerciaux de la liste C2PA.
