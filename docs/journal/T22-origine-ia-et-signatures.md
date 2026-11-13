# T22 — Origine IA déclarée et signatures de générateurs

- **Branche** : `tache/T22-origine-ia-et-signatures`
- **Dates** : 2026-11-13
- **Exigences couvertes** : F-11 (réalisée), F-12 (réalisée), F-14 (absence sans constat), ES-20 (déclaration restituée en indice), NF-09
- **Décisions** : ADR-0142 à ADR-0146, tous acceptés
- **Errata** : ERR-0010

## Objectif

Écrire les premières règles du catalogue (découpage, T22) : repérer les champs qui déclarent une origine IA, dont les valeurs IPTC `DigitalSourceType` (F-11), et les traces d'outils de génération connus, paramètres de génération et nom du logiciel, à partir d'un catalogue de signatures (F-12). Les ADR antérieurs adressaient à T22 : la vérification du vocabulaire IPTC (A-33), la lecture de `DigitalSourceType` (fiche `metadonnees-xmp`), les noms d'observation que citent les règles (ADR-0117, ADR-0133, ADR-0140), la coupe des textes longs (ADR-0118), la réécriture de la description du catalogue (journal de T20).

## État initial

- PR [#22](https://github.com/TheDarkMac/AI-detector/pull/22) (complément bureautique de T21). Sur `5fe416f` : docs 43386773114 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129) ; code 43386773261 vert sur tous les systèmes. ADR-0139, ADR-0140 et ADR-0141 validés par TheDarkMac (« Yes, all three », 2026-11-13), passés à « Accepté » (`c68e05b`) : docs et code verts, Windows compris.
- L'assistant a mergé la PR le 2026-11-13 vers 08:42 UTC, après le « Merge when green » de TheDarkMac : commit de merge `6126686` « Merge: T21 (complément 2) — Extraction bureautique : propriétés de DOCX et d'ODT (#22) », à l'adresse noreply (ADR-0007). Lancements de push sur `6126686` verts : docs 43395283572 (étape du titre de merge comprise), code 43395283561.
- La ligne « T21 (complément 2) » de l'index du journal portait « à venir » : corrigée en #22 dans cette tâche. T21 est complète.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (option B d'ADR-0129), qui demande un changement des réglages du dépôt par TheDarkMac.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire. Outils : exiftool 13.25, Node 24.16 (pour `markdownlint-cli2`).
- `detector` à jour avec `origin/detector` (`6126686`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : ADR-0018, ADR-0021, ADR-0022, ADR-0055, ADR-0058, ADR-0064, ADR-0084 à ADR-0091, ADR-0101, ADR-0104, ADR-0117, ADR-0118 ; guide du catalogue ; chargeur (`_orchestration/catalogue.py`), moteur (`_regles.py`, `Contexte.appliquer_catalogue`) ; fiches des douze modules de métadonnées. Constat : le catalogue livré (0.1.0) n'a aucune règle, et chaque règle doit avoir une direction que permet le manifeste de son module, tous à « rien de particulier ».
2. Vérification des sources, en ligne, le 2026-11-13 :
   - vocabulaire IPTC « Digital Source Type » (vingt valeurs, trois retirées), IPTC Photo Metadata Standard 2025.1 (propriété `Iptc4xmpExt:DigitalSourceType`, adresse, XMP seul), guide IPTC des médias générés (2023) : [ADR-0143](../decisions/ADR-0143-valeurs-iptc-de-la-source-numerique.md) ;
   - code public d'AUTOMATIC1111 (`modules/images.py`, `modules/processing.py`), de ComfyUI (`nodes.py`, `execution.py`), d'InvokeAI (`image_files_disk.py`, et `pngwriter.py` de la version 2.3.5) : [ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md) ;
   - NovelAI et Midjourney : aucune source de l'éditeur ; descriptions de tiers divergentes ; aucune signature propre retenue ;
   - pages des produits de la liste de noms : chacune répond (six refusent une requête automatique) : [ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md).
3. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes suivies :
   - nature des constats d'une déclaration : indice faible dirigé ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)) ;
   - direction des valeurs IPTC : une par valeur, génération vers l'origine IA, retouche et montage vers la retouche (ADR-0143) ;
   - nom du logiciel : liste de noms distinctifs appliquée à chaque champ logiciel (ADR-0144) ;
   - comparaison de `DigitalSourceType` : motif tolérant (ADR-0143).

   Les autres choix, faits par l'assistant, ont été soumis dans la PR et validés par TheDarkMac pendant sa revue (« Oui, les deux », 2026-11-13) : ADR-0145 (signatures de paramètres retenues), [ADR-0146](../decisions/ADR-0146-versions-des-modules-et-du-catalogue-de-t22.md) (versions des modules et du catalogue, forme des règles).
4. Branche `tache/T22-origine-ia-et-signatures` créée depuis `detector` à jour (`6126686`).
5. Catalogue 0.2.0 : vingt-quatre règles « moteur » dans douze fichiers `regles/<module>.toml` ; les seize règles de nom du logiciel écrites à partir d'une même table, par un script temporaire hors du dépôt, puis relues ; description de l'en-tête réécrite ; entrée ajoutée au registre `versions.toml`.
6. Manifestes des douze modules : directions `origine_ia` (et `retouche` pour `xmp`), exigence F-12 (et F-11 pour `xmp`), version augmentée (ADR-0146) ; docstrings des modules mises à jour. Code des modules inchangé.
7. Essai sur le poste : un PNG fabriqué (XMP `trainedAlgorithmicMedia` et `CreatorTool` Midjourney, blocs `parameters`, `prompt`, `invokeai_metadata`) donne cinq indices faibles vers l'origine IA ; rapport HTML relu.
8. Tests :
   - `tests/test_signatures.py` : chaque règle livrée déclenchée par un échantillon construit, avec la valeur de ses paramètres, et éprouvée (le test échoue si une règle du catalogue n'a pas d'échantillon) ; règles toutes indices faibles de déclaration, appliquées par le moteur ; une seule liste de générateurs ; graphies de `DigitalSourceType` reconnues et refusées, valeurs sans règle, ressource et liste, préfixe choisi ; noms reconnus et logiciels ordinaires ; blocs texte sans signature, compressés et internationaux, coupe à 4 096 caractères ; absence sans constat ; un constat par règle ; boîte de piste non lue ; deux analyses complètes dans un vrai processus de travail (PNG, DOCX) ;
   - un test du vrai processus de travail sans catalogue désigné : il applique le catalogue livré ;
   - tests adaptés : versions des modules (`test_soumission.py`, `test_cli.py`), manifestes de métadonnées (`test_manifestes.py`), catalogue livré non vide (`test_catalogue.py`), liste des règles de `vk --regles` (`test_cli.py`), nouveau test du message « Aucune règle » sur un catalogue fourni vide ;
   - tests à modules factices : ils prenaient le catalogue livré, vide jusqu'ici ; ils reçoivent désormais le catalogue de test (`tests/catalogues.py`), comme les autres tests de leurs fichiers (`test_isolation.py`, `test_limites.py`, `test_soumission.py`, `test_cli.py`).
9. Fiches des douze modules : en-tête, hypothèses distinguées, règles qui lisent leurs observations, taux d'erreur, historique ; index des fiches.
10. Vérification locale : Ruff (format et analyse) et mypy sans remarque ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans erreur ; matrice régénérée (F-11 et F-12 réalisées) ; suite complète verte, couverture de 100 % des lignes et des branches ; banc sur le corpus d'essai, sans réseau (`unshare -rn`) : code 1 et le seul écart attendu, la cible par fichier non établie sur quatre authentiques (ADR-0105) ; aucune des vingt-quatre règles ne se déclenche sur les fichiers authentiques. Code des modules inchangé : campagne de fuzzing non relancée.
11. Documentation : ADR-0142 à ADR-0146 ; ERR-0010 ; renvois dans ADR-0022, ADR-0064, ADR-0088, ADR-0117, ADR-0118 ; analyse critique v1.2 (A-33 vérifiée) ; guide du catalogue v1.3 ; découpage v0.22 ; matrice ; index des ADR, des errata, du journal et des fiches.
12. PR [#23](https://github.com/TheDarkMac/AI-detector/pull/23) ouverte ; `lint-markdown` rouge sur l'étape « Aucun ADR au statut Proposé », comme prévu (ADR-0129). ADR-0145 et ADR-0146 validés par TheDarkMac pendant la revue, le 2026-11-13 : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Le test de la procédure d'empreinte du catalogue échouait, l'empreinte du chargeur et celle du registre concordant | Le test triait les lignes par empreinte, la procédure trie par chemin ; indiscernable avec un seul fichier | ERR-0010 : test corrigé ; aucune empreinte publiée ne change |
| Onze tests à modules factices refusés : « module exif absent de cette version » | Ils validaient le catalogue livré avec leurs seuls modules factices ; sans règle, il passait | Catalogue de test passé explicitement, comme le font déjà les autres tests de ces fichiers |
| `vk --desactiver` d'un test refusé (code 2) | Même cause : un manifeste factice `exif` seul face aux règles des autres modules | Catalogue fourni vide dans ce test |
| La branche « Aucune règle dans cette version du catalogue » de `vk --regles` n'était plus couverte | Le catalogue livré a des règles | Test sur un catalogue fourni vide |
| Couverture à 99 % : le catalogue livré par défaut de `travail.executer` n'était plus exercé | Seuls les tests à modules factices l'employaient, et ils reçoivent désormais le catalogue de test | Test dans un vrai processus de travail, sans catalogue désigné, avec les modules livrés |
| Le lint Markdown refusait le motif des paramètres d'AUTOMATIC1111, écrit avec un espace final, dans un code en ligne | Espace à la fin d'un code en ligne (MD038) | Espace retiré du motif lui-même, aussi précis sans |
| La première version des fiches disait « liste des générateurs » pour les règles `DigitalSourceType` | Le script temporaire reconnaissait la liste à la longueur du motif | Fiches rétablies depuis `detector` et script corrigé avant tout commit |
| Décompte des règles faux dans un test (17 au lieu de 16 règles de nom) | Erreur de l'assistant en écrivant le test | Test corrigé : il compare les motifs et compte les gabarits en `-generateur` |
| Gabarits numérotés (`infopdf.logiciel-generateur-002`) | Premier jet du script temporaire | Gabarits en mots (`infopdf.producteur-generateur`), forme fixée par ADR-0146 |
| La limite « règle non évaluée » redisait la ligne « Évaluation » du rapport | Premier jet des règles | Limite retirée de toutes les règles (ADR-0146) |
| Un bloc de code Python cité dans ERR-0010 était reformaté par Ruff | Ruff formate les blocs Python des fichiers Markdown | Bloc marqué `text` : la citation reste exacte |

Seul le premier problème touche un élément déjà mergé (ERR-0010).

## Écarts par rapport au découpage

- **Ajouté** : direction « retouche » pour deux valeurs IPTC ; nom du générateur dans seize champs de douze modules, sons, vidéos et documents compris ; erratum sur un test de T15.
- **Écarté** : valeurs IPTC sans lien avec l'IA générative (ADR-0143) ; noms communs de produits (ADR-0144) ; blocs `workflow`, `Dream`, `invokeai_graph` (ADR-0145) ; lecture entière des textes longs (ADR-0145, option C).
- **Non fait** : aucune règle n'est évaluée, faute de corpus de référence (T100) ; aucune signature propre à NovelAI ni à Midjourney, faute de source.

## Résultat

- Un fichier qui déclare une génération par IA, par sa propriété XMP `DigitalSourceType`, par les paramètres d'un outil connu ou par le nom d'un générateur dans un champ logiciel, porte au rapport un indice faible, dirigé vers l'origine IA ou la retouche, de fondement « déclaration », qui cite sa règle, sa phrase et ses limites.
- Un fichier sans déclaration n'en porte aucun (F-14) ; une déclaration n'est jamais une preuve (ES-20).
- `vk --regles` liste les vingt-quatre règles du catalogue 0.2.0 ; son empreinte est au registre.
- F-11 et F-12 sont réalisées.

## Reste à faire

- T23 : incohérences internes (dates, logiciel et appareil, dimensions).
- T30 : la même déclaration IPTC dans un manifeste C2PA (actions `digitalSourceType`).
- T100 : corpus de référence, avec des fichiers réels des outils ; mesure des règles de T22 et niveau qui en découle.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande ; contrôle des ADR en tâche séparée (ADR-0129, option B).
