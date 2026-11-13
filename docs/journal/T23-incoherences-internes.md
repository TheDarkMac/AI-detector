# T23 — Incohérences internes

- **Branche** : `tache/T23-incoherences-internes`
- **Dates** : 2026-11-13
- **Exigences couvertes** : F-13 (réalisée), F-14 (réalisée), P-04 (réalisée), F-26 (format 2 du catalogue), NF-06
- **Décisions** : ADR-0147 à ADR-0152, tous acceptés
- **Errata** : aucun

## Objectif

Relever les incohérences internes des métadonnées : dates impossibles, logiciel incompatible avec l'appareil déclaré, dimensions atypiques (F-13) ; présenter l'absence de métadonnées comme une information neutre (F-14, A-34). ADR-0084 laissait à T23 la comparaison de deux observations, par une règle « module » ou un nouveau format du catalogue ; ADR-0128, ADR-0133 et ADR-0140 lui laissaient l'interprétation des dates, observées telles qu'écrites ; A-32 demandait les listes de référence dans le catalogue.

## État initial

- PR [#23](https://github.com/TheDarkMac/AI-detector/pull/23) (T22). Sur `3f36db1` : docs 43403223403 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129). ADR-0142, ADR-0143 et ADR-0144 acceptés dès la tâche (choix de TheDarkMac) ; ADR-0145 et ADR-0146 validés par TheDarkMac pendant la revue (« Oui, les deux », 2026-11-13), passés à « Accepté » (`394ddc2`) : docs 43403549578 et code 43403549571 verts, sur tous les systèmes.
- Le jeton de `gh` du trousseau était devenu invalide avant le merge ; TheDarkMac a relancé `gh auth login`.
- L'assistant a mergé la PR le 2026-11-13 à 13:46:36 UTC, après le « Merge quand vert » de TheDarkMac : commit de merge `22809de` « Merge: T22 — Origine IA déclarée et signatures de générateurs (#23) », à l'adresse noreply (ADR-0007). Lancements de push sur `22809de` verts : docs 43436617093, code 43436617288.
- La ligne « T22 » de l'index du journal portait « à venir » : corrigée en #23 dans cette tâche.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (option B d'ADR-0129), qui demande un changement des réglages du dépôt par TheDarkMac.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`22809de`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : ADR-0022, ADR-0055, ADR-0058, ADR-0084, ADR-0085, ADR-0089, ADR-0128, ADR-0133, ADR-0140, ADR-0142, ADR-0146 ; moteur (`_regles.py`, `Contexte.appliquer_catalogue`), chargeur, schémas ; fiches des douze modules. Constats : une condition ne teste qu'une observation ; un constat ne cite que les observations de son module ; aucun module n'observe les dimensions réelles d'une image ; « rien de particulier » est déjà permis à tous les modules.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes suivies :
   - comparaison de deux observations : test du catalogue, format 2 ([ADR-0147](../decisions/ADR-0147-comparaison-de-deux-observations.md)) ;
   - nature d'une incohérence : information neutre ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md)) ;
   - dimensions atypiques : liste dans le catalogue ([ADR-0150](../decisions/ADR-0150-incoherences-retenues.md)) ;
   - absence de métadonnées : une règle par module ([ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)).

   Les autres choix, faits par l'assistant, ont été soumis dans la PR et validés par TheDarkMac pendant sa revue (« Yes, all three », 2026-11-13) : [ADR-0148](../decisions/ADR-0148-lecture-des-dates.md) (lecture des dates), ADR-0150 hors dimensions (incohérences retenues et écartées), [ADR-0152](../decisions/ADR-0152-versions-de-t23.md) (versions).
3. Vérification des sources, en ligne, le 2026-11-13 : référence de l'API d'images d'OpenAI (tailles fixes) ; écriture des dates EXIF (copies de la norme CIPA DC-008), PDF (manuels de cpdf, Apryse, `DateTime::Format::PDF` ; la norme ISO 32000 est payante), XMP (page des types de données et de l'espace `xmp` d'Adobe, dont « It should be the same as or more recent than xmp:ModifyDate » pour `xmp:MetadataDate`).
4. Branche `tache/T23-incoherences-internes` créée depuis `detector` à jour (`22809de`).
5. Lecture des dates : `src/voight_kampff/_dates.py`, quatre écritures, intervalles d'instants UTC, états impossible, non renseignée, non reconnue (ADR-0148).
6. Moteur : tests `comparer` et `impossible`, champ `lecture`, opérateurs `<`, `>`, `=` ; format de chaque condition et de chaque règle ; première paire retenue, trouvée en temps linéaire (ADR-0147). Schémas : format 1 ou 2 à l'en-tête, nouveaux champs des conditions ; le chargeur refuse une règle du format 2 dans un catalogue du format 1.
7. Catalogue 0.3.0, format 2 : trente-huit règles « moteur », informations neutres, dans les douze fichiers `regles/<module>.toml`, écrites à partir d'une même table par un script temporaire hors du dépôt, puis relues ; description de l'en-tête réécrite ; entrée ajoutée au registre `versions.toml`. Manifestes et code des modules inchangés (ADR-0152).
8. Tests :
   - `tests/test_dates.py` : chaque écriture, ses formes admises et refusées, chaque état, les bornes (an 9999, 24:00, seconde intercalaire, fraction au-delà de la microseconde), l'ordre certain entre dates avec et sans fuseau, `True` lu à part de `1` ;
   - `tests/test_regles.py` : conditions du format 2 refusées et relues, date impossible, comparaison de valeurs brutes et de dates, première paire retenue ; recherche linéaire égale à l'essai de chaque paire (Hypothesis) ; 2 048 × 2 048 observations en moins de 5 s ;
   - `tests/test_catalogue.py` : catalogue du format 2 lu, format 3 refusé, règle du format 2 refusée dans un catalogue du format 1 ;
   - `tests/test_incoherences.py` : chaque règle de T23 déclenchée par un échantillon construit, avec la valeur de ses paramètres, et éprouvée (le test échoue si une règle d'information neutre n'a pas d'échantillon) ; règles toutes informations neutres, une absence par module, même liste de générateurs que T22 ; dix-huit échantillons cohérents sans constat (dates dans l'ordre, à moins de 26 heures, inconnues, d'une autre écriture, au même instant, au même jour, à l'année près ; `mvhd` à 0 ; logiciel ordinaire, générateur sans appareil, dimensions d'un appareil, hors liste, croisées, sans appareil) ; un constat par règle ; deux analyses complètes (JPEG sans métadonnées, JPEG incohérent) ;
   - tests de T22 adaptés : `test_signatures.py` ne vise que les vingt-quatre indices de T22 ; ses analyses complètes ne comptent que les indices ; `catalogues.py` déclare le paramètre de la seconde observation.
9. Fiches des douze modules, par un second script temporaire hors du dépôt, puis relues : tâche, tableau des règles de T23 à la rubrique « Ce qui déclenche un constat », phrase de l'absence, taux d'erreur ; à la main, dates lues ou non par les règles, limite d'EXIF ; historique ; index des fiches.
10. Vérification locale : Ruff (format et analyse) et mypy sans remarque ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans erreur ; matrice régénérée (F-13, F-14 et P-04 réalisées) ; suite complète verte, couverture de 100 % des lignes et des branches ; banc sur le corpus d'essai, sans réseau (`unshare -rn`) : code 1 et le seul écart attendu, la cible par fichier non établie sur quatre authentiques (ADR-0105) ; le banc ne compte que les indices, et les vingt-quatre de T22 restent sans déclenchement sur les fichiers authentiques. Essai sur le poste : un JPEG fabriqué (appareil Canon, prise de vue une semaine après la modification, 1 024 × 1 024) donne quatre informations neutres et aucun indice ; rapport HTML relu. Code des modules inchangé : campagne de fuzzing non relancée.
11. Documentation : ADR-0147 à ADR-0152 ; renvois dans ADR-0084, ADR-0085, ADR-0089, ADR-0128, ADR-0133, ADR-0140 ; guide du catalogue v1.4 ; architecture v1.16 ; analyse critique v1.3 (A-32, A-34) ; découpage v0.23 ; matrice ; index des ADR, du journal et des fiches.
12. PR [#24](https://github.com/TheDarkMac/AI-detector/pull/24) ouverte ; sur `2995b22`, code 43445583589 vert sur tous les systèmes, docs 43445583584 rouge sur l'étape « Aucun ADR au statut Proposé », comme prévu (ADR-0129). ADR-0148, ADR-0150 et ADR-0152 validés par TheDarkMac pendant la revue, le 2026-11-13 (« Yes, all three ») : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Un écart d'un jour entre les instants lus et ceux des tests | `date.toordinal()` compte le 0001-01-01 comme jour 1 | Origine décalée d'un jour dans `_dates.py` ; la docstring disait déjà « depuis 0001-01-01 » |
| Le cache de la lecture aurait rendu pour `True` la date lue pour `1` | `lru_cache` tient `True == 1`, comme Python | Cache typé (`typed=True`), éprouvé par un test |
| Le catalogue refusé par son schéma au premier chargement | Une condition de la règle des dimensions carrées portait deux tests (`parmi` et `comparer`) | Deux conditions : largeur parmi la liste, largeur égale à la hauteur |
| Titres de règles trop longs et redondants (« Date impossible : La date de… »), parenthèses doublées dans les phrases | Premier jet du script temporaire | Titres courts donnés par une table, phrases reformulées ; fichiers rétablis depuis `detector` et règles regénérées avant tout commit |
| La comparaison de 2 048 × 2 048 dates prenait 31 s | Chaque paire était essayée | Recherche linéaire (ADR-0147) : 18 ms, même paire retenue |
| Deux lignes de `_regles.py` non couvertes par la suite complète | Une garde devenue inaccessible (textes et booléens déjà écartés avant un ordre) ; `paire` d'une condition sans comparaison jamais appelée | Garde retirée ; test ajouté |
| Le statut en gras du découpage affichait v0.20, celui de l'architecture v1.14 | Les PR des compléments de T21 et de T22 ont complété la phrase du statut sans changer le numéro en gras | Numéros corrigés (v0.23, v1.16) ; simple libellé, sans erratum |
| mypy refusait l'aide `instant` de `tests/test_dates.py` | Champs passés par `*champs` à `datetime`, avec `tzinfo` nommé | Paramètres nommés un à un |
| Le statut en gras du guide du catalogue restait à v1.3 dans le premier commit de documentation | Oubli de l'assistant, qui avait ajouté la v1.4 à l'historique seulement | Corrigé dans le commit de validation des ADR |
| Trois échantillons de test faux | Erreurs de l'assistant : une date de numérisation qui déclenchait une seconde règle, un MP4 sans balise qui déclenchait l'absence, une paire « sans ordre » qui en avait un | Échantillons corrigés |

Seul le statut en gras du découpage et de l'architecture touche un élément déjà mergé : un libellé de version, non une analyse ni une décision, donc sans erratum.

## Écarts par rapport au découpage

- **Ajouté** : lecture des dates dans le moteur ; format 2 du catalogue ; fondement « vérification déterministe » pour l'absence.
- **Écarté** (ADR-0150) : dates sans paire que fixe une définition (IPTC-IIM, ID3, RIFF, Vorbis, blocs texte PNG, Matroska, impression) ; comparaisons entre modules ; dates antérieures à un format ou postérieures à l'analyse ; listes de modèles par fabricant ; tailles de générateurs sans source de l'éditeur.
- **Non fait** : aucune règle n'est évaluée, faute de corpus de référence (T100) ; les dimensions réelles d'une image ne sont pas observées.

## Résultat

- Un fichier dont deux dates se contredisent, quel que soit le fuseau, dont une date n'existe pas, ou qui déclare un appareil photo avec un générateur ou des dimensions de générateur, porte au rapport une information neutre qui cite sa règle, sa phrase, les valeurs et ses limites.
- Un fichier sans métadonnées d'une famille porte une information neutre qui le dit, jamais un indice (F-14).
- `vk --regles` liste les soixante-deux règles du catalogue 0.3.0 ; son empreinte est au registre.
- F-13, F-14 et P-04 sont réalisées.

## Reste à faire

- T24 : indices de transfert par messagerie ou capture d'écran, qui pourront citer les règles d'absence (A-34).
- Comparaison d'observations de deux modules (EXIF contre XMP) : point ouvert de l'architecture (§12).
- T100 : mesure des règles de T22 et T23 sur le corpus de référence.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande ; contrôle des ADR en tâche séparée (ADR-0129, option B).
