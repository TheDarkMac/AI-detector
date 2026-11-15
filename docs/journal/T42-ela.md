# T42 — ELA, avertissement d'interprétation et carte

- **Branche** : `tache/T42-ela`
- **Dates** : 2026-11-15
- **Exigences couvertes** : F-32 ; F-84 (carte ELA, premier élément) ; ES-12 et ES-13 (image du rapport, masquage) ; NF-06 (carte identique sur toutes les machines)
- **Décisions** : ADR-0197 à ADR-0201, tous acceptés (ADR-0201 validé pendant la revue de la PR)
- **Errata** : aucun

## Objectif

Livrer l'ELA (F-32) avec son avertissement d'interprétation et sa carte (F-84), demandée par TheDarkMac le 2026-11-15 (« T42 | ELA + avertissement d'interprétation + carte »), alors que T42 était une candidate V2 (ADR-0012).

## État initial

- PR [#30](https://github.com/TheDarkMac/AI-detector/pull/30) (T41). Commits : `0e3f973` (double compression), `e568709` (tests), `7045436` (documentation), `4547c60` (ADR-0189 et ADR-0190 passés à « Accepté » après le « Oui, les deux » de TheDarkMac). CI sur `7045436` : docs 43678429778 en échec, comme prévu (ADR au statut Proposé, ADR-0129), code 43678429725 vert ; sur `4547c60` : docs 43679524161 et code 43679524201 verts.
- L'assistant a mergé la PR le 2026-11-15 à 09:39:49 UTC, après le « Oui, merge si vert » de TheDarkMac : commit de merge `ff2ad02`. Lancements de push sur `ff2ad02` : docs 43700320579 et code 43700320589, verts (vérifiés au début de T42). Empreinte du catalogue 0.8.0 : `435b199c…cde9`.
- La ligne « T41 » de l'index du journal portait « à venir » : corrigée en #30 dans cette tâche.
- Complément de T40 (tables de Photoshop et d'appareils) : à la demande de TheDarkMac, son arbre de travail séparé avait été supprimé et son travail remis dans le dossier principal, sur sa branche `tache/T40-complement-photoshop-appareils` (locale, non poussée). Au début de T42, on a constaté que son relevé et ses brouillons d'ADR, gardés dans le dossier temporaire de sa première session, avaient disparu ; il ne restait que le manifeste du module `image` (0.3.0, direction `authenticite`) et deux attentes de test. Les quatre décisions de TheDarkMac sur le complément restaient consignées. Sa dernière question (deux jeux de tables de Photoshop au même niveau) était sans réponse.
- Toujours en attente : mesure de `R-DOUBLEJPEG-001` et des règles de T24 et T40 sur le corpus (T100) ; double compression non alignée ; oracle mozjpeg jamais lancé ; T32 ; `M-C2PA-TEXTE` avec T80 ; filigranes commerciaux de la liste C2PA ; complément de T30 ; le banc n'inscrit pas la liste de confiance ; échec unique de la première campagne de fuzzing de T24 ; ORGANIZATION de Vorbis et Source de l'IPTC non marquées nominatives (ADR-0160) ; messages à @Jean ; alertes de Dependabot ; protection des étiquettes `v*` ; contrôle des ADR en tâche requise séparée (ADR-0129, option B).

## Déroulé

1. Cadrage : T42 est une candidate V2 (ADR-0012, option C écartée pour la lecture abusive de l'ELA) et la suite prévue de la V1 était le complément de T40, puis T32. Question à TheDarkMac : « Finir T40c, puis T42 » retenu ([ADR-0197](../decisions/ADR-0197-t42-en-v1.md)).
2. Reprise du complément de T40 : relevé perdu ; question à TheDarkMac : « Refaire le relevé ». Collecte relancée sur Wikimedia Commons, cette fois avec ses données dans le dossier de travail du dépôt (`banc/releves/tables-T40c/`, non suivi) : phase 1, métadonnées de 37 006 JPEG par l'API (216 mois de 2008 à 2025) ; phase 2, en-têtes des candidats. Le débit du poste était d'environ 6 Ko/s, avec des coupures de la résolution de noms : les scripts ont été rendus tolérants aux coupures. ADR-0191 et ADR-0192 du complément écrits pendant la collecte.
3. Pendant la collecte, quatre questions de conception de T42 posées en un lot, toutes retenues sur recommandation : carte seule ([ADR-0198](../decisions/ADR-0198-carte-sans-constat.md)) ; une valeur par bloc ; qualité 95 et gain fixe ([ADR-0199](../decisions/ADR-0199-methode-et-etendue-de-l-ela.md)) ; rubrique « Visualisations » ([ADR-0200](../decisions/ADR-0200-visualisations-au-rapport.md)). Source primaire lue : Krawetz, « A Picture's Worth », livre blanc de Black Hat USA 2007, §3.4.2 (PDF de blackhat.com, texte extrait par `pdftotext`).
4. TheDarkMac a demandé de commencer T42 sans attendre la fin du relevé (« start it »). Le travail du complément a été gardé par un commit local sur sa branche ; branche `tache/T42-ela` créée depuis `origin/detector` (`ff2ad02`).
5. Mesures de faisabilité sur le poste, lecteur de T41 sans ses bornes : une image de synthèse de 24 Mpx (6 000 × 4 000) demande 33 s de décodage et 18 s d'IDCT ; en progressif, la limite d'objets du contexte est dépassée. Pour 4 Mpx (2 048 × 2 048, 65 536 blocs) : 4,6 s de décodage en séquentiel, 5,3 s en progressif pour 36 864 blocs (bornée par les visites). L'IDCT réécrite en un seul produit à deux dimensions donne les mêmes entiers en 0,86 s au lieu de 2,2 s. Cinquième question, l'étendue : « 4 Mpx, puis le haut » retenu (ADR-0199). Sixième question, le masquage de la carte : « masquée par défaut », catégorie `contenu` (ADR-0200).
6. Code :
   - `modules/_lecture/dct.py` : DCT et IDCT en entiers, tables de libjpeg, sorties de `doublejpeg` (mêmes calculs ; les 106 tests de T41 passent sans changement de résultat) ;
   - lecteur JPEG : bornes de la région en paramètres, valeurs par défaut inchangées ;
   - modèle : objet `Visualisation`, catégorie `contenu`, `VERSION_SCHEMA` 0.7.0 ; schémas du rapport et des messages ; `Contexte.visualiser()` ; réception du message `visualisation` par le processus principal ; `Analyse.visualisations` ;
   - exports : JSON masqué (données et empreinte de la carte retirées), comparaison sans les cartes masquées, rubrique HTML « Visualisations » (avertissement, couverture, image `data:`), politique `img-src data:`, ligne du résumé ; textes dans `textes.toml` ;
   - module `ela` 0.1.0 ; l'ELA quitte `modules/hors_v1.toml`.
7. Essais du gain sur une image de synthèse avec bruit (1 600 × 1 200), compressée à 60, un carré de 300 × 300 pixels sans perte collé, enregistrée à 92 : écart moyen 1,07 niveau par pixel dans le carré, 0,11 ailleurs. Avec la somme des écarts d'un bloc pour valeur (gain 1), la carte était trop sombre dans le navigateur (68 contre 7) ; gain 2 retenu (143 contre 13). Même image compressée une fois à 92 : 1,04 partout, carré compris ; réenregistrée à 85 : 0,35. À 98 et 100 : 1,53 et 1,52, environ 195 sur 255. Réduite à 75 % puis enregistrée à 92 : 0,76 contre 0,55. Rapport HTML vérifié dans le navigateur intégré (serveur local du dossier temporaire) : avertissement au-dessus, carte affichée, carré visible.
8. Oracle : la recompression simulée, comparée à `cjpeg -grayscale -quality 95 -dct int` puis `djpeg -dct int` (libjpeg-turbo 2.1.5), diffère jusqu'à 7 niveaux sur un pixel, mais l'écart moyen est égal au millième (1,045 contre 1,046 ; 0,148 contre 0,149 ; 0,157 contre 0,156). La phrase de la fiche, d'abord écrite de mémoire (« au plus un niveau »), a été corrigée par cette mesure avant tout commit.
9. Tests : `tests/test_ela.py` (carte des échantillons à empreinte fixée, collage visible, gain et borne, oracle libjpeg-turbo, étendue réduite, JPEG non lu, PNG relu par zlib et sans compression, modèle et refus, exports masqués et révélés, HTML, résumé, comparaison) ; `tests/donnees/ela/` : trois JPEG de 256 × 192 pixels écrits par `generer.sh` ; scénarios du travail factice (visualisation seule rendant un module partiel, empreinte falsifiée, module étranger) ; attentes mises à jour (liste des modules, version du schéma, ordre des rubriques, techniques hors V1).
10. Documentation : ADR-0197 à ADR-0201, fiche [`ela`](../techniques/ela.md), modèle de données (v1.11), architecture (v1.23), découpage (v0.30), matrice (F-32 réalisée, F-84 partielle), ce journal.
11. PR [#31](https://github.com/TheDarkMac/AI-detector/pull/31) ouverte (commits `fe2638b`, `a536a06`, `f07306c`). ADR-0201 validé par TheDarkMac pendant la revue (« Oui, valide ADR-0201 ») : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Relevé du complément de T40 introuvable | Gardé dans le dossier temporaire d'une session, effacé avec elle | Relevé refait, données gardées dans `banc/releves/tables-T40c/` du dossier de travail |
| Collecte très lente, puis arrêtée | Débit du poste d'environ 6 Ko/s, coupures de la résolution de noms ; un arrêt par `pkill -f` a aussi tué le shell qui le lançait | Lectures de 32 Kio d'abord ; nouveaux essais sans abandon ; arrêts par numéro de processus |
| Image entière trop longue à décoder | Décodage entropique en Python pur (T41) | Étendue bornée à 65 536 blocs, choix de TheDarkMac (ADR-0199) |
| Empreinte de la carte variable d'une machine à l'autre, possible | Un flux zlib compressé dépend de la version de zlib | PNG à blocs stockés écrits par le module (ADR-0199) |
| `Visualisation` sans place dans le modèle | Une observation est un scalaire ou une liste, bornée à 4 096 caractères | Nouvel objet du modèle (ADR-0200) |
| Affirmation inexacte dans la fiche (écart avec cjpeg) | Écrite avant la mesure | Mesurée, corrigée (étape 8) |
| Le manifeste exige une direction | Schéma des manifestes (ADR-0064) | `rien_de_particulier` (ADR-0201, proposé) |

## Écarts par rapport au découpage

- T42 avancée en V1, avant T32 (ADR-0197) ; le complément de T40 est commencé mais sera mergé après T42.
- Le découpage prévoyait un « avertissement d'interprétation » : il est double, dans la fiche et au rapport, juste au-dessus de la carte.
- Ajouté : la DCT commune avec T41, plus rapide ; la catégorie identifiante `contenu`.

## Résultat

- Module `ela` 0.1.0 ; schéma du rapport et des messages 0.7.0 ; catalogue 0.8.0 inchangé.
- `vk image.jpg --rapport DOSSIER` écrit la carte au rapport, masquée ; `--reveler contenu` l'affiche.
- Vérification : `uv run --locked coverage run -m pytest`, puis `coverage combine` et `coverage report` (100 %) ; `tests/test_ela.py` seul en quelques secondes.

## Reste à faire

- Finir le complément de T40 (relevé fini le 2026-11-15, analyse, question des deux jeux de tables de Photoshop, règles, ADR-0193 à ADR-0196) ; il partira du schéma 0.7.0 et prendra le catalogue 0.9.0.
- Lecture des cartes par des personnes : étude d'usage (T104, hors V1). Chrominance non examinée.
- Autres visualisations de F-84 : spectre (T43), spectrogramme (T60), chronologie des révisions PDF (T50).
