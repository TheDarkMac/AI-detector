# T20 — Extraction image

- **Branche** : `tache/T20-extraction-image`
- **Dates** : 2026-10-28
- **Exigences couvertes** : F-10 (images), F-14 (absence observée), F-90 (marquage), ES-03, ES-05 (XMP), ES-13, ES-19, NF-09
- **Décisions** : ADR-0114 à ADR-0122 ; ADR-0112 et ADR-0113 acceptés
- **Errata** : [ERR-0007](../errata/ERR-0007-merge-de-la-pr-18.md)

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : extraire les métadonnées des images, EXIF, XMP, IPTC et blocs texte PNG (F-10). Les ADR antérieurs adressaient à T20 : les analyseurs de structure écrits par le projet et leur fuzzing (ADR-0043, ADR-0082), la comparaison de `defusedxml` aux protections de la bibliothèque standard et l'oracle exiftool (ADR-0043, architecture §9 et §12), le gabarit des fiches techniques (ADR-0022), les noms d'observation (ADR-0058), le marquage des données identifiantes (ADR-0057), les versions des bibliothèques au manifeste (ADR-0064), le coût de la validation des messages (architecture §12) et la règle de décompression des modules (ADR-0078).

## État initial

- PR [#18](https://github.com/TheDarkMac/AI-detector/pull/18) (T18). Déjà consigné dans le journal de T18 : étapes 1 à 12, dont l'échec de la CI sous Windows sur `1bd7905` et sa correction.
- CI sur `1755043` verte : code 40692511706 (terminé à 13:04:06 UTC), docs 40692511663 ; CodeRabbit n'a pas relu la PR (dépôt de moins de 10 étoiles).
- Mergée le 2026-10-28 à 13:06:41 UTC depuis le compte TheDarkMac. Commit de merge `4526ccd`, à l'adresse noreply (ADR-0007), mais au titre par défaut de GitHub et non au format d'ADR-0044 ; ADR-0112 et ADR-0113 encore « Proposé », réglages d'ADR-0110 sans validation consignée : [ERR-0007](../errata/ERR-0007-merge-de-la-pr-18.md).
- Lancements de push sur `4526ccd` réussis : docs 40693483511, code 40693483621 (terminé à 13:10:41 UTC). La ligne de T18 dans l'index du journal portait « à venir » : corrigée en #18 dans cette tâche.
- `gh pr edit` échoue toujours : le corps d'une PR se met à jour par `gh api -X PATCH repos/TheDarkMac/AI-detector/pulls/N -F body=@fichier`.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire. exiftool 13.25 et ImageMagick 7.1.1-43 sont installés sur le poste.
- `detector` à jour avec `origin/detector` (`4526ccd`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : T20 dépend du socle (T11 à T18), mergé. Aucun module n'était livré : T20 livre les premiers. Lecture du découpage, des journaux de T17 et T18, d'ADR-0022, ADR-0042, ADR-0043, ADR-0057, ADR-0058, ADR-0061, ADR-0064, ADR-0078, ADR-0079, ADR-0084, ADR-0090, de l'architecture (§9, §12), du modèle de menace (M-02, M-04, M-14, M-22, ES-05, ES-13), du contexte, du processus de travail, de la réception, des schémas, de l'identification et des tests.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes suivies :
   - découpage : un module par famille, `exif`, `xmp`, `iptc`, `textepng` ([ADR-0114](../decisions/ADR-0114-un-module-par-famille-de-metadonnees.md)) ;
   - formats : JPEG, PNG, WebP et HEIC ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)) ;
   - XML : expat de la bibliothèque standard, DTD refusée, plutôt que `defusedxml` ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)) ;
   - ADR-0112 et ADR-0113 : acceptés (ERR-0007).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : emplacements lus et non lus (ADR-0115), [ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md) (noms d'observation), [ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md) (valeurs), [ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md) (champs identifiants), [ADR-0120](../decisions/ADR-0120-bibliotheques-au-manifeste.md) (bibliothèques au manifeste), [ADR-0121](../decisions/ADR-0121-cout-de-la-validation.md) (coût de la validation), [ADR-0122](../decisions/ADR-0122-oracle-exiftool.md) (oracle exiftool).
3. Branche `tache/T20-extraction-image` créée depuis `detector` à jour (`4526ccd`). ADR-0112 et ADR-0113 passés à « Accepté ».
4. Lecteurs communs, `modules/_lecture/` : `conteneurs` (segments JPEG, blocs PNG et WebP, boîtes `meta`, `iinf`, `iloc` et `idat` de HEIC, blocs texte PNG), `tiff` (IFD chaînés et sous-répertoires, vues sans copie), `xmp` (expat sans DTD, RDF, espaces de noms canoniques), `iim` (ressources Photoshop, jeux IIM), `valeurs` (coupure, nombres, noms).
5. Modules `exif`, `xmp`, `iptc`, `textepng` : manifestes, `analyser`, table des étiquettes EXIF et TIFF, table des jeux IIM, marquage des champs identifiants ; aucune règle, direction « rien de particulier » seule.
6. Bibliothèques : champ `bibliotheques` du manifeste et de son schéma, transmis dans la configuration ; versions lues avant les restrictions (`principal.versions_des_bibliotheques`) ; réception qui exige exactement celles des modules actifs.
7. Coût de la validation : un PNG de 5 005 propriétés XMP demandait une vingtaine de secondes, dont l'essentiel dans `jsonschema`. Profil : résolution des `$ref` et `oneOf` des messages. Valideurs aux références résolues au chargement, branche des messages choisie par `type`, valideur livré gardé pour l'emplacement des erreurs, et refus si les deux sont en désaccord. Mesures finales à charge variable (trois passages, ADR-0121) : 1,62–3,45 ms → 0,38–0,83 ms par message ; 13,7–19,3 s → 4,2–5,4 s pour un PNG de 4 000 propriétés. Limite comptée `RESULTATS_MAX` : 4 096 résultats par module et par partie.
8. Tests :
   - `tests/metadonnees.py` : constructeurs d'échantillons (TIFF, JPEG, PNG, WebP, HEIC, XMP, ressources Photoshop, IIM) et exécution d'un module sur un contexte réel ;
   - `tests/test_metadonnees.py` : absence observée par chaque module, toutes les formes de valeur, chaque format et emplacement, structures interrompues ou incohérentes, DTD et entités refusées, préfixe XMP usurpé, paquet étendu, bombe de décompression, valeurs coupées, nombre de résultats, une catégorie identifiante au moins par module ;
   - `tests/donnees/metadonnees/` : quatre images créées par ImageMagick, métadonnées écrites par exiftool, sortie d'exiftool enregistrée (`generer.sh`) ; `tests/test_oracle_exiftool.py` compare dans les deux sens, et relance exiftool s'il est installé dans la version enregistrée ;
   - `tests/test_fuzzing.py` : deux propriétés pour les modules (échantillons mutés, octets quelconques), messages conformes au schéma et analyses répétées identiques ; une campagne de 40 000 exemples par propriété a trouvé un défaut (voir ci-dessous), corrigé, puis relancée ;
   - vrai processus de travail sur l'échantillon JPEG de l'oracle, bibliothèques des seuls modules actifs, scénario `dependance_non_declaree` du processus factice, versions envoyées, concordance des fiches et des manifestes, valideurs rapides ;
   - tests existants adaptés aux modules livrés (liste des modules, couverture d'un PDF, import, champ `bibliotheques` des configurations et manifestes de test).
9. Vérification locale : `uv lock --check` ; Ruff (format et analyse) et mypy sans remarque ; matrice régénérée et vérifiée ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans remarque ; 1 153 tests verts, un sauté (lanceur de Windows), puis le test du désaccord des valideurs ; couverture 100 % des lignes et des branches (la seule branche manquante, ce désaccord, a été couverte) ; campagne de fuzzing des modules, 40 000 exemples par propriété, sans échec après correction.
10. Documentation : ADR-0114 à ADR-0122 ; ERR-0007 ; `docs/techniques/` (README, gabarit, quatre fiches) ; renvois dans ADR-0022, ADR-0023, ADR-0043, ADR-0054, ADR-0057, ADR-0058, ADR-0064, ADR-0078 ; matrice (F-10, F-14, F-90, ES-05 partielles ; ES-03, ES-13, ES-19, NF-09 complétées) ; découpage v0.18, architecture v1.12, modèle de données v1.7, glossaire v1.8 ; terme « Métadonnées » au glossaire du rapport ; `CONTRIBUTING.md` (§1, oracle ; §3, étape 6), `README.md`, `docs/README.md` ; commentaire du job `reproductibilite` ; index des ADR, des errata et du journal.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| 36 tests existants en échec dès les modules ajoutés | Ils supposaient aucun module livré, ou des manifestes et configurations sans `bibliotheques` | Tests adaptés ; le test « aucun module livré » de T12 remplacé par celui des quatre modules |
| `exif` en erreur sur un JPEG écrit par exiftool | Octets indéfinis lus comme nombres (`ComponentsConfiguration`) sans format `struct` pour le type 7 | Type 7 lu octet par octet |
| Un chemin rapide par `is_valid` seul ne gagnait rien | Le `oneOf` de `jsonschema` évalue chaque branche en entier, même pour `is_valid` | Branche choisie par `type` (ADR-0121) |
| Bloc EXIF réduit à son préfixe : erreur du module | Plage d'octets de longueur nulle, refusée par le modèle | Bloc vide ignoré (JPEG, WebP) |
| Boîte `meta` de moins de quatre octets ignorée sans le dire | Lecture des enfants à partir d'une position après la fin | Format partiel |
| Couverture du paquet XMP étendu tenue par un ensemble d'octets | Jusqu'à 16 millions d'entiers en mémoire | Plages triées |
| Paquet étendu alloué dès son premier morceau | Un fichier hostile aurait fait allouer la taille annoncée, par GUID | Assemblage seulement une fois couvert |
| Campagne de fuzzing : segment JPEG de longueur 2, erreur du module | Le contrôle des bornes construisait une plage, vide ici ; même risque pour une boîte HEIC vide | Contrôle des bornes séparé de la plage ; test de régression |
| Échantillons HEIC des tests mal construits | Décalages absolus faussés par une boîte ajoutée en tête, contenu vide, iloc de version 2 | Constructeur corrigé (versions d'`infe` et d'`iloc`, `iloc` brut, contenus non vides) |
| Paragraphes de normes cités de mémoire dans le code et les fiches | Numéros non vérifiables sur le poste | Retirés avant le premier commit ; nom de la norme seul (précédent d'ERR-0002) |
| ADR-0119 citait la menace M-27 | Confusion avec M-22, fuite des données identifiantes | Corrigé avant le premier commit |
| Premières mesures de temps faussées | Prises pendant que la suite de tests ou une campagne de fuzzing tournait | Refaites une fois les deux terminées, trois passages, valeurs extrêmes consignées (la charge des autres programmes reste variable) |
| Une branche de `schemas.valider` non couverte | Désaccord des deux valideurs : le document aurait été accepté | Refus dans ce cas, et test |

Aucun de ces problèmes n'est une erreur d'un document déjà mergé, sauf le merge de la PR #18 : ERR-0007. Le coût de validation estimé par l'architecture (1,5 ms) est de cet ordre (1,6 à 3,5 ms selon la charge) : pas d'erratum.

## Écarts par rapport au découpage

- **Ajout** : champ `bibliotheques` du manifeste et contrôle des versions reçues (ADR-0120) ; validation accélérée et limite de 4 096 résultats (ADR-0121) ; gabarit et dossier des fiches techniques (ADR-0022) ; terme « Métadonnées » au glossaire du rapport.
- **Écarté** : `defusedxml`, candidate d'ADR-0043 (ADR-0116).
- **Non fait** : emplacements rares ou propres à un fabricant (MakerNote, ressources Photoshop autres que `0x0404`, textes « Raw profile type », `tIME`), listés dans les fiches (ADR-0115). Liste de garde de P1 par nom d'observation (ADR-0057), laissée à décider avant T25 (ADR-0119).
- **Inchangé** : le catalogue (0.1.0, sans règle) ; sa description dit encore qu'aucun module n'est livré. La modifier changerait son empreinte et demanderait une version sans aucune règle nouvelle (ADR-0085) : elle sera réécrite avec les premières règles (T22).

## Résultat

- Quatre modules d'analyse livrés : la couverture d'une image dit ce qui a été lu, famille par famille ; chaque champ EXIF, XMP, IPTC-IIM et texte PNG figure au rapport comme observation, les champs identifiants masqués par défaut.
- Le XML est lu sans DTD ni entité ; la version d'expat figure à la rubrique Versions.
- La validation des messages est quatre à cinq fois plus rapide, et un module ne peut plus envoyer plus de 4 096 résultats par partie.
- F-10 est partielle (images faites, T21 à venir) ; les extractions concordent avec exiftool sur les quatre formats.

## Reste à faire

- T21 : PDF, conteneurs audio et vidéo, DOCX et ODT ; `xmp` étendu au PDF ; XML de DOCX et ODT par expat ; oracle complété.
- T22 : règles sur `Iptc4xmpExt:DigitalSourceType` et signatures de générateurs ; nouvelle version du catalogue et de sa description ; textes longs coupés (ADR-0118) à revoir si une signature en a besoin.
- T23 : incohérences et présentation neutre de l'absence (F-14).
- T25 : liste de garde des données identifiantes, lieux et textes libres (ADR-0119).
- Revue de la PR : ADR-0117 à ADR-0122, emplacements d'ADR-0115, réglages d'ADR-0110.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
