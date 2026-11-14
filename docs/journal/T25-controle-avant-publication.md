# T25 — Contrôle avant publication : marques identifiantes des métadonnées

- **Branche** : `tache/T25-controle-avant-publication`
- **Dates** : 2026-11-14
- **Exigences couvertes** : F-90 (partie métadonnées réalisée ; points de traçage à T94), ES-13, CU-5
- **Décisions** : ADR-0158 à ADR-0163 ; ADR-0160 et ADR-0163 proposés, à valider pendant la revue
- **Errata** : aucun

## Objectif

Signaler, avant la publication d'un fichier reçu, les marques des métadonnées qui peuvent identifier sa source : auteur, numéro de série, coordonnées GPS (F-90, partie métadonnées, ADR-0014). ADR-0119, ADR-0128, ADR-0133 et ADR-0140 laissaient à T25 les lieux nommés et les textes libres ; ADR-0057 et ADR-0119, la liste de garde par nom d'observation ; le journal de T24, la valeur qui suit FBMD.

## État initial

- PR [#25](https://github.com/TheDarkMac/AI-detector/pull/25) (T24). Sur `f16b0be` : docs 43556016915 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129) ; code 43556016894 annulé, remplacé par le lancement du push suivant. ADR-0154 et ADR-0157 validés par TheDarkMac pendant la revue (« Oui, les deux », 2026-11-14), passés à « Accepté » (`2e275c3`) : docs 43556154945 et code 43556154791 verts.
- L'assistant a mergé la PR le 2026-11-14 à 04:26:35 UTC, après le « CI verte, merge » de TheDarkMac : commit de merge `4033c56` « Merge: T24 — Indices de transfert par messagerie ou capture d'écran (#25) », à l'adresse noreply (ADR-0007). Lancements de push sur `4033c56`, en cours au moment du merge : docs 43556677794 et code 43556677791 verts.
- La ligne « T24 » de l'index du journal portait « à venir » : corrigée en #25 dans cette tâche.
- Reste ouvert de T24 : l'échec unique de la première campagne de fuzzing, non reproduit (voir « Reste à faire »).
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (option B d'ADR-0129), qui demande un changement des réglages du dépôt par TheDarkMac.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`4033c56`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : F-90, CU-5, §5.6 du cahier ; ADR-0014, ADR-0031, ADR-0032, ADR-0057, ADR-0093, ADR-0095, ADR-0098, ADR-0119 ; modèle (`CategorieIdentifiante`, `Observation`), présentation, HTML, ligne de commande ; marquage des douze modules de métadonnées ; règle `R-IPTC-003`. Constats : chaque module marque déjà ses champs identifiants, le rapport les masque, mais rien ne dit que le fichier les porte ; aucune catégorie ne couvre un lieu ni un texte libre ; aucune phrase de constat ne cite un texte libre ; la phrase de `R-IPTC-003` ne cite pas la valeur FBMD.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation ; les quatre recommandations retenues :
   - forme : rubrique et ligne du résumé dérivées des catégories, plutôt que des règles du catalogue ou une commande séparée ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)) ;
   - lieux et textes libres : deux catégories masquées par défaut, plutôt qu'un lieu masqué et des textes seulement signalés, ou rien de masqué ([ADR-0159](../decisions/ADR-0159-lieux-nommes-et-textes-libres.md)) ;
   - valeur FBMD : numéro de série quand la valeur commence par FBMD, plutôt que texte libre toujours ou non marquée ([ADR-0161](../decisions/ADR-0161-valeur-fbmd.md)) ;
   - liste de garde dans P1 : non ajoutée ([ADR-0162](../decisions/ADR-0162-liste-de-garde-non-ajoutee.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0160](../decisions/ADR-0160-champs-lieux-et-textes-libres.md) (champs marqués par module), [ADR-0163](../decisions/ADR-0163-versions-de-t25.md) (versions).
3. Branche `tache/T25-controle-avant-publication` créée depuis `detector` à jour (`4033c56`).
4. Modèle : catégories `lieu` et `texte_libre` entre `gps` et `nom_de_fichier` ; `VERSION_SCHEMA` 0.4.0 dans le modèle, le schéma du rapport (énumération, sept catégories dans `masquage`) et celui des messages ; libellés dans `textes.toml`. `--reveler` suit l'énumération sans autre changement.
5. Modules : listes `_LIEUX` et `_TEXTES_LIBRES` dans les douze modules de métadonnées, selon ADR-0160 ; propriétés personnalisées d'un DOCX et utilisateur d'un ODT toutes marquées texte libre ; `iptc.SpecialInstructions` marqué numéro de série si une valeur commence par FBMD (ADR-0161) ; versions augmentées et F-90 ajoutée aux exigences des manifestes (ADR-0163).
6. Rapport : `Presentation.marques()`, `controle_incomplet()` et `publication()` ; lignes du contrôle à la fin du résumé ; rubrique HTML « Contrôle avant publication » entre « Couverture » et « Données identifiantes », sans aucune valeur ; une ligne par catégorie au terminal, avec les noms des observations.
7. Tests :
   - `tests/test_controle_publication.py` : champs `lieu` et `texte_libre` d'`exif` (le GPS reste GPS), `xmp` (une ville et une latitude dans une même structure de lieu), `iptc`, `infowav`, `vorbis`, `quicktime` (clés `mdta`), `matroska`, `ooxml` (propriétés personnalisées de tout type) ; valeur FBMD marquée numéro de série et `R-IPTC-003` toujours déclenchée, FBMD pas au début marquée texte libre ; marques par catégorie dans l'ordre d'ES-13 ; ligne du résumé ; contrôle complet sur un JPEG sans métadonnées, incomplet avec un module désactivé ; rubrique HTML sans valeur, masquée ou levée ; lignes du terminal sans valeur ; masquage par défaut et levée de `lieu` dans le JSON ; `--reveler` des deux catégories ; analyse complète d'une photo à GPS, ville, titre et marque FBMD ;
   - tests adaptés : catégories attendues des tests de chaque module (`test_metadonnees.py`, `test_metadonnees_medias.py`, `test_metadonnees_pdf.py`, `test_metadonnees_bureautique.py`) ; ordre des rubriques (`test_rapport.py`) ; résumé du terminal (`test_cli.py`) ; versions des modules (`test_cli.py`, `test_soumission.py`) ; version du schéma des messages (`travail_factice.py`, `test_travail.py`).
8. Fiches : en-têtes des douze fiches de métadonnées (version, tâche, F-90) ; champs marqués `lieu` et `texte_libre`, limites et historique.
9. Vérification locale : voir « Vérification ».
10. Documentation : ADR-0158 à ADR-0163 ; renvois dans ADR-0014, ADR-0054, ADR-0057, ADR-0093, ADR-0095, ADR-0098, ADR-0119, ADR-0128, ADR-0133, ADR-0140, ADR-0153 ; modèle de menace v1.3 (M-22, ES-13) ; modèle de données v1.8 ; glossaire v1.9 ; architecture v1.18 ; découpage v0.25 ; matrice (F-90, ES-13) ; index des ADR et du journal.

## Vérification

- Ruff (format et analyse) et mypy sans remarque ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans erreur sur 233 fichiers ; matrice régénérée (`python -m banc.matrice`).
- Premières passes ciblées : dix-neuf échecs attendus (catégories des tests de modules, ordre des rubriques, résumé du terminal, versions, concordance des fiches), corrigés en mettant les attentes à jour ; deux échecs de `test_controle_publication.py` corrigés (voir « Problèmes rencontrés »).
- Suite complète, mesurée par coverage comme en CI : 1 833 tests verts et un ignoré (lanceur de l'environnement virtuel), en 8 min 40 s ; couverture de 100 % (7 814 instructions, 2 700 branches). Les fiches ont été écrites après cette passe ; `test_manifestes.py` et `test_matrice.py`, qui les relisent, relancés ensuite : verts.
- Banc sur le corpus d'essai, sans réseau (`unshare -rn`) : code 1 et le seul écart attendu, la cible par fichier non établie (ADR-0105), comme en T24.
- Essai sur le poste : JPEG d'ImageMagick de 64 × 48, métadonnées écrites par exiftool 13.25 (`Artist`, latitude GPS, `City` et `ObjectName` IPTC, `SpecialInstructions` à `FBMD…`, `dc:title` XMP). Le résumé compte 8 données dans cinq catégories ; le terminal nomme `exif.ifd0.Artist`, `iptc.SpecialInstructions`, les trois étiquettes GPS, `iptc.City`, `iptc.ObjectName` et `xmp.dc:title` ; `R-IPTC-003` est relevé ; la rubrique HTML est entre « Couverture » et « Données identifiantes ». Aucune valeur (« Lyon », « Jeanne », la suite de FBMD) n'est dans la rubrique, ni dans le HTML ni dans le JSON masqués ; « FBMD » n'y figure que dans la phrase et les limites de la règle. Les cinq analyses non menées sont hors V1 : le contrôle est dit complet.
- Fuzzing : non relancé, aucun lecteur de structure n'a changé ; les modules ne changent que la catégorie posée sur leurs observations.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| `RECORDING_LOCATION` de Matroska non marqué au premier essai | Le module compare le nom passé par la règle des composants (ADR-0117), où `_` devient `-` ; la liste ne l'était pas | Liste des lieux passée par la même règle que `_NOMINATIVES` |
| Tests de module du nouveau fichier refusés hors processus de travail | Garde d'ES-17 ; les autres fichiers de tests de modules posent un verrou par une fixture | Même fixture dans `test_controle_publication.py` |
| Observations ajoutées au rapport de test refusées | Elles nommaient un module absent de la couverture du rapport de test, ce que le modèle refuse | Observations rattachées au module `metadonnees` du rapport de test |
| Contrôle « complet » impossible sur le rapport de test commun | Il porte une partie hors périmètre, donc une non menée qui rend le contrôle incomplet | Test fait sur l'analyse réelle d'un JPEG sans métadonnées |
| mypy refusait l'aide `rubrique` des tests (`no-any-return`), et Ruff demandait de reformater la liste des lieux de `matroska`, vus après la suite complète | `re.findall` est typé `list[Any]` ; ligne écrite à la main | Liste annotée et forme de Ruff appliquée ; tests de `matroska` et de T25 relancés, verts |

## Écarts par rapport au découpage

- **Ajouté** : catégories `lieu` et `texte_libre`, schéma 0.4.0 (ADR-0159) ; marquage de la valeur FBMD (ADR-0161).
- **Écarté** : règles du catalogue et commande séparée pour le contrôle (ADR-0158) ; liste de garde dans P1 (ADR-0162).
- **Non fait** : « logiciel nominatif » d'ADR-0014, faute de champ normalisé qui nomme le titulaire d'une licence ; points de traçage d'imprimante (T94, V2) ; anonymisation, hors périmètre (ADR-0014).

## Résultat

- Le résumé dit combien de données des métadonnées peuvent identifier la source, dans quelles catégories, et rappelle que l'outil ne les retire pas ; il dit aussi quand le contrôle est incomplet.
- La rubrique « Contrôle avant publication » du HTML et le terminal nomment chaque marque, sans jamais sa valeur.
- Lieux nommés et textes libres sont masqués par défaut, comme les cinq autres catégories, et se lèvent par `--reveler lieu` et `--reveler texte_libre`.
- La valeur FBMD est masquée comme un numéro de série ; `R-IPTC-003` se déclenche comme avant.
- F-90 reste partielle : sa partie métadonnées est réalisée, les points de traçage restent à T94.

## Reste à faire

- T94 (V2) : points de traçage d'imprimante, présence seulement (ADR-0032).
- Revue d'ADR-0119 : `Organization` de Vorbis et `Source` d'IPTC, qui nomment un organisme, ne sont pas marqués nominatifs (ADR-0160).
- Fuzzing : l'échec unique de la première campagne de T24 n'est pas reproduit ; une campagne qui affiche l'exemple fautif (`print_blob`) le recherchera.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande ; contrôle des ADR en tâche séparée (ADR-0129, option B).
