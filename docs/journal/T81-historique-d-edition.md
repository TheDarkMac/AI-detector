# T81 — Historique d'édition d'un DOCX ou d'un ODT

- **Branche** : `tache/T81-historique-d-edition`
- **Dates** : 2026-11-23
- **Exigences couvertes** : F-71
- **Décisions** : ADR-0248 à ADR-0251, toutes acceptées au début de T81
- **Errata** : aucun

## Objectif

Rapporter l'historique d'édition des documents bureautiques, temps d'édition et sessions de révision, une valeur absente ou nulle restant une information neutre (F-71) ; examiner, comme le demandait ADR-0013, l'extension de F-71 aux modifications suivies et l'extraction des images d'un DOCX ou d'un ODT (A-24). Demandé par TheDarkMac le 2026-11-23 (« t81 »), tâche suivante de la V1 au découpage (§4).

## État initial

- PR [#42](https://github.com/TheDarkMac/AI-detector/pull/42) (complément texte de T53) : mergée par l'assistant le 2026-11-19 à 16:01:49 UTC après le « Yes, merge if green » de TheDarkMac, commit de merge `8605903`. Lancements de push sur `8605903` : docs 44561456201 vert ; code 44561456144 en échec au premier essai, le seul `tests (macos-latest, 3.14)` annulé après quinze minutes sans avoir obtenu de machine (aucune étape lancée), ce qui fait échouer `code-ok` ; relancé par l'assistant au début de T81 (`gh run rerun --failed`) : vert.
- Lancements de push sur `20b1ec2` (complément de T80) : code 44246349126 et docs 44246349059 verts, déjà vérifiés au début du complément texte de T53.
- Empreinte du catalogue 0.18.0 : `f9ef0b4f…b273` ; schémas 0.12.0 ; `ooxml` et `odf` 0.3.1 observent `TotalTime`, `cp:revision`, `meta:editing-cycles` et `meta:editing-duration` sans les interpréter (ADR-0140).
- Toujours en attente : voir les journaux de T80, de son complément et du complément texte de T53 (« Reste à faire ») ; signature d'un manifeste C2PA d'un texte ; inventaire des marquages à refaire en entier ; `$OutputEncoding` de PowerShell (T103).

## Déroulé

1. Lecture de F-71, d'ADR-0013, ADR-0139, ADR-0140, ADR-0240, des modules `ooxml`, `odf`, `actifsbureau` et du lecteur bureautique de `caracteres`, du moteur de règles (conditions, comparaison de deux observations) et de la lecture des dates (`_dates.py`).
2. Relevé de ce qu'écrit LibreOffice 25.2.3.2 : les échantillons existants, dont le texte est entré par l'API (`insertString`), n'ont aucun identifiant de session ; un document tapé par le répartiteur de commandes de l'interface (`.uno:InsertText`), rouvert puis complété, porte un `officeooo:rsid` par session dans les styles automatiques de `content.xml`, mais son export DOCX n'en a aucun.
3. Vérification d'une source pour les dates des modifications : Word écrit l'heure locale suivie de `Z` et la relit comme une heure locale (MS-OI29500, §2.1.313), LibreOffice fait de même dans un DOCX (bogue 134589).
4. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : nouveau module `historique` ; constats neutres et deux incohérences neutres ; auteurs comptés, non lus ; images d'un DOCX ou d'un ODT renvoyées à un complément de T81 ([ADR-0248](../decisions/ADR-0248-module-historique-et-perimetre-de-t81.md), [ADR-0250](../decisions/ADR-0250-auteurs-comptes-et-dates-sans-fuseau.md), [ADR-0251](../decisions/ADR-0251-constats-et-versions-de-t81.md)). Précisions de l'assistant, écrites dans ces ADR et dans [ADR-0249](../decisions/ADR-0249-historique-lu-dans-un-docx-et-un-odt.md) : parties lues, session d'un caractère, marques comptées telles qu'écrites, minutes entières, écart le plus grand que permettent les dates, dates des modifications lues sans fuseau, règles, seuils et versions.
5. Module `historique` 0.1.0 (`modules/historique/`) : propriétés, réglages, corps et commentaires d'un DOCX par les relations du paquet et de la partie principale ; `meta.xml` et `content.xml` d'un ODT ; corps lu élément par élément ; dates lues par `_dates.py`. Premier essai sur les échantillons de LibreOffice : un DOCX compte deux marques de révision pour une insertion que LibreOffice relit comme une seule (la fin du paragraphe inséré est marquée à part) : compté tel qu'écrit, et dit dans la phrase du constat.
6. Échantillons : `tests/donnees/historique/generer_historique.py` écrit `sessions.odt` en trois sessions (un paragraphe par session, une insertion suivie, un commentaire) et son export `sessions.docx` ; `oracle.json` consigne ce qu'en relit LibreOffice (longueur et `Rsid` de chaque portion, modifications, commentaires et leurs auteurs, cycles et durée). Le module trouve 207 caractères en trois sessions, la plus représentée à 52 %, comme LibreOffice.
7. Catalogue 0.19.0 : `regles/historique.toml`, R-HISTORIQUE-001 à R-HISTORIQUE-008 ; description resserrée (1 023 caractères) ; empreinte inscrite au registre. Le premier rendu du rapport écrivait l'unité deux fois (« 0 minutes minute(s) », « 52 % % ») : les phrases ne la répètent plus.
8. Tests : `tests/test_historique.py` (durées et fuseaux ; propriétés, relations transitionnelles et strictes, cibles relatives ; sessions du texte d'un DOCX construit à la manière de Word, texte supprimé ou déplacé ; réglages ; marques de révision et commentaires, aucun nom observé ; écart et dates postérieures ; parties absentes, mal formées, en double ou illisibles ; ODT : propriétés, sessions des styles et des portions, texte hors du corps, modifications et annotations ; échantillons contre LibreOffice ; huit règles sur des analyses complètes ; phrases ; contrôle avant publication) ; attentes mises à jour (liste des modules, versions, compte des règles, matrice, bibliothèques des modules désactivés, fuzzing sur DOCX et ODT et lecture d'un encodage déclaré). Deux attentes d'écart fausses d'une minute (la seconde finale d'une date compte dans son intervalle) corrigées dans les tests ; une partie désignée par une relation et absente de l'archive n'était pas signalée : elle l'est, référence manquante (ADR-0139). Couverture du module : 100 %.
9. Campagne de fuzzing à part, sur le seul module : 20 000 documents (graine 81), sept sur dix tirés des deux échantillons ou d'un DOCX construit à la manière de Word dont une à trois parties XML sont mutées (octets changés, jetons insérés : marques de révision, courses et identifiants de session, portions et annotations, DTD, déclaration d'encodage, durées démesurées ; morceaux retirés ou recopiés), parfois une entrée retirée, puis réécrits en archive ; les autres mutés octet par octet ; chaque document analysé deux fois, mêmes messages, chaque message validé par le schéma des messages. Aucun échec, en 341 secondes.
10. Suite complète sous coverage, en 12 minutes 43 : 3 294 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), 2 en échec, une attente que T81 change : sur les documents `document.docx` et `document.odt` de LibreOffice, `historique` s'applique désormais, là où le test voulait tous les autres modules non applicables (`test_orchestration.py`, qui vérifie désormais leur temps et leurs cycles d'édition, 62 minutes et 7). Le fichier relancé : vert. Couverture de tout le paquet et du banc à 100 %.
11. Documentation : ADR-0248 à ADR-0251 ; renvois dans ADR-0013, ADR-0139, ADR-0140, ADR-0240 ; fiche [`historique-edition`](../techniques/historique-edition.md), renvois dans les fiches `metadonnees-ooxml` et `metadonnees-odf`, index des fiches ; architecture (v1.33), découpage (v0.41), guide du catalogue (v1.20), glossaire (v1.20), registre des arbitrages (v1.12, A-24 en partie traité), matrice (F-71 réalisée), index des décisions et du journal, ce journal. Numéros de section d'ECMA-376 et d'OpenDocument que l'assistant n'avait pas vérifiés retirés avant le commit (ERR-0002).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Aucun identifiant de session dans les échantillons de LibreOffice | Texte entré par l'API (`insertString`), qui ne passe pas par le traitement de la saisie | Texte tapé par le répartiteur de commandes (`.uno:InsertText`) |
| Aucun identifiant de session dans un DOCX de LibreOffice | LibreOffice n'en écrit pas à l'export | DOCX construits à la manière de Word dans les tests ; l'échantillon DOCX vérifie le texte sans session |
| Deux marques de révision pour une modification relue par LibreOffice | La fin du paragraphe inséré est marquée à part (`w:pPr/w:rPr/w:ins`) | Marques comptées telles qu'écrites (ADR-0249), dites dans la phrase et les limites |
| Unité écrite deux fois au rapport | Le rapport écrit l'unité de l'observation après sa valeur | Phrases sans unité |
| Écart attendu d'une minute de moins | La seconde finale d'une date est dans son intervalle (ADR-0148) | Attentes des tests corrigées ; le module suit ADR-0148 |
| Partie désignée absente non signalée | Recherche de l'entrée sans distinguer l'absence | Référence manquante, comme le veut ADR-0139 |
| Affirmation trop large sur les dates | « Word et LibreOffice écrivent `Z` » vaut pour le DOCX ; LibreOffice écrit un ODT sans fuseau | Précisé dans la fiche, le module et la règle R-HISTORIQUE-008 |
| Attente d'un test d'orchestration | Elle voulait non applicables tous les modules autres que ceux qu'elle nomme, sur un DOCX et un ODT | `historique` ajouté à ceux qu'elle nomme |
| Description du catalogue trop longue | 1 052 caractères pour 1 024 | Quatre tournures resserrées |

## Écarts par rapport au découpage

- Ajouts : sessions rattachées au texte (part de la plus représentée) ; deux incohérences de dates ; modifications suivies et commentaires.
- Report : extraction des images d'un DOCX ou d'un ODT vers les modules d'image (A-24) à un complément de T81, ajouté à l'ordre de la V1 (ADR-0248).
- F-71 passe à « réalisée ».

## Résultat

- Module `historique` 0.1.0 (`docx`, `odt`) ; catalogue 0.19.0 ; schémas 0.12.0 inchangés ; `ooxml` et `odf` inchangés.
- `vk document.docx` ou `vk document.odt` rapporte en informations neutres le temps d'édition et les enregistrements déclarés, les sessions d'édition du texte du corps et la part de la plus représentée, les modifications suivies et les commentaires avec le nombre de leurs auteurs, sans leurs noms ; il relève un temps d'édition plus long que le document n'a existé, et des modifications ou commentaires datés après le dernier enregistrement ; un document sans historique le dit, neutre.

## Reste à faire

- Complément de T81 : images d'un DOCX ou d'un ODT, extraites vers les modules d'image (A-24).
- En-têtes, pieds de page et notes d'un DOCX ; versions enregistrées d'un ODT (`VersionList.xml`) ; réglages de LibreOffice (`settings.xml`).
- Un DOCX écrit par Word dans l'oracle (comme pour T21, ADR-0141).
- Mesure de R-HISTORIQUE-007 et R-HISTORIQUE-008 sur le corpus de référence (T100).
