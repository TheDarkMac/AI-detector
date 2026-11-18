# T80 (complément bureautique) — Caractères invisibles ou substitués du texte d'un DOCX ou d'un ODT

- **Branche** : `tache/T80-complement-bureautique`
- **Dates** : 2026-11-18
- **Exigences couvertes** : F-73 (étendue au DOCX et à l'ODT)
- **Décisions** : ADR-0239 à ADR-0242, tous acceptés au début du complément
- **Errata** : aucun

## Objectif

Appliquer l'analyse du module `caracteres` (caractères invisibles, homoglyphes, lettres de compatibilité) au texte d'un DOCX et d'un ODT, que T80 avait renvoyé à ce complément (ADR-0232). Demandé par TheDarkMac le 2026-11-18 (« Oui, lance-le »), sur la proposition de l'assistant de passer à la tâche suivante de la V1.

## État initial

- PR [#39](https://github.com/TheDarkMac/AI-detector/pull/39) (T80). Après son ouverture, la CI Windows est restée bloquée des heures, sans journal : un identifiant de test de 16 Mi caractères, recopié dans `PYTEST_CURRENT_TEST`, que Windows limite à 32 767 caractères (journal de T80, étape 13). Corrigé par `514cf92`, puis `e61b065` (sortie de `vk --texte` lue en UTF-8 sous Windows) et `595b710` (journal). Sur `595b710`, toutes les vérifications vertes (code 44211658748, docs 44211658753). L'assistant a mergé la PR le 2026-11-18 à 01:02:44 UTC, après le « Oui, merge si vert » puis le « corriges et merges quand ca passe » de TheDarkMac : commit de merge `90c9310`. Lancements de push sur `90c9310` : docs 44212724154 et code 44212724164 verts. Le lancement à la demande de `code` sur `detector` (`2356e2d`, 44170072895), fait pour le diagnostic, a conclu en échec pour un seul job macOS annulé sans machine attribuée ; Windows y était vert.
- Correctif ERR-0013, fait dans une session à part, sur la proposition de l'assistant acceptée par TheDarkMac : sortie de `vk` écrite en UTF-8 hors d'un terminal (ADR-0238). PR [#40](https://github.com/TheDarkMac/AI-detector/pull/40), mergée par l'assistant le 2026-11-18 à 04:08:09 UTC après le « ok, merge maintenant » de TheDarkMac et une CI verte sur `0a50d82` : commit de merge `0d43d35`. Lancements de push sur `0d43d35` : docs 44235210972 et code 44235210933 verts, vérifiés au début du complément.
- Empreinte du catalogue 0.16.0 : `88ad0446…1916` ; schémas 0.11.0.
- Toujours en attente : voir le journal de T80 (« État initial » et « Reste à faire ») ; signature d'un manifeste C2PA d'un texte ; inventaire des marquages à refaire en entier ; `$OutputEncoding` de PowerShell (T103).

## Déroulé

1. Lecture d'ADR-0136, ADR-0137, ADR-0229, ADR-0232, des lecteurs ZIP et XML et des modules `ooxml`, `odf` et `actifsbureau`.
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation : corps, notes, en-têtes et pieds de page, commentaires ([ADR-0239](../decisions/ADR-0239-parties-lues-d-un-docx-et-d-un-odt.md)) ; texte supprimé analysé et signalé ([ADR-0240](../decisions/ADR-0240-texte-supprime-d-une-modification-suivie.md)) ; module `caracteres` étendu ([ADR-0241](../decisions/ADR-0241-texte-bureautique-dans-le-module-caracteres.md)) ; texte masqué analysé et compté ([ADR-0242](../decisions/ADR-0242-texte-masque-et-versions-du-complement-de-t80.md)). Précisions de l'assistant, écrites dans ces ADR : éléments lus de chaque format, ordre des parties, paragraphes emboîtés, styles communs et automatiques d'un ODT, forme des positions, observations, règle et versions.
3. Extraction dans `modules/caracteres/_bureau.py` ; analyse par paragraphe, localisée par partie, paragraphe et caractère. Premier essai sur les DOCX et ODT de LibreOffice du dépôt : texte attendu. Les styles automatiques de `styles.xml` et de `content.xml` portent souvent les mêmes noms (`P1`, `T1`) : seuls les styles communs de `styles.xml` valent pour `content.xml`.
4. Échantillons : `tests/donnees/caracteres/generer_bureau.py` écrit par LibreOffice 25.2.3.2 (UNO) `texte.odt` et `texte.docx` : mot mêlé, espace sans chasse, portion masquée, suppression suivie d'un forçage bidirectionnel, note en étiquettes, en-tête à espace cadratin, commentaire à usage privé ; `oracle.json` consigne ce que LibreOffice en relit. Lecture des suppressions par `RedlineStart` et `RedlineEnd`, `getString` d'une modification levant une exception. Premier passage du module : chaque caractère semé relevé à sa place dans les deux formats, 16 caractères supprimés et 16 masqués, comme écrits.
5. Catalogue 0.17.0 : `R-CARACTERES-013` (texte masqué) ; description resserrée (1 014 caractères) ; empreinte inscrite au registre.
6. Tests : `tests/test_caracteres.py` (échantillons contre LibreOffice, parties lues et leur ordre, espaces strict et cible absolue, texte d'un paragraphe DOCX et ODT, relations et parties manquantes, archives et entrées illisibles, entrées en double, en-tête local illisible, styles et pages types, XML coupés, positions, règles sur les échantillons, Hypothesis sur un texte quelconque dans un DOCX) ; attentes mises à jour (versions, couverture d'un DOCX et d'un ODT, bibliothèques des modules actifs, formats du marquage, compte des règles) ; fuzzing : `caracteres` sur DOCX et ODT. Couverture du module : 100 %.
7. Le fuzzing de la suite a trouvé une archive à deux entrées du même nom, que le lecteur ZIP refuse : l'exception de `Archive.trouver` n'était pas attrapée. Campagne à part de 20 000 documents mutés (graine 80 ; octets de l'archive, ou d'une partie XML avant de réécrire l'archive), sur le seul module, messages validés par le schéma : 438 échecs, tous `Illisible` levée en déclarant non menée une entrée illisible, par sa localisation, qui relit l'en-tête local défaillant. Correction : la localisation de l'arrêt, donnée par le lecteur ; test de non-régression, qui échoue sans la correction. Campagne relancée : 20 000 documents, aucun échec, en 227 secondes.
8. Suite complète sous coverage, en 11 minutes 46 : 3 080 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent) ; couverture de tout le paquet et du banc à 100 %.
9. Documentation : ADR-0239 à ADR-0242 ; renvois dans ADR-0013, ADR-0229, ADR-0232, ADR-0237 ; fiche [`caracteres-invisibles`](../techniques/caracteres-invisibles.md) (version 0.2.0) et index des fiches ; architecture (v1.31), découpage (v0.39), guide du catalogue (v1.18), glossaire (v1.18), matrice (F-73), index du journal, ce journal.

10. PR [#41](https://github.com/TheDarkMac/AI-detector/pull/41) ouverte vers `detector` (commits `ebb7547`, `fd1fa58`, `39d99d7`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Caractères réels à la place des échappements `\uXXXX` | Un `\uXXXX` simple dans un paramètre d'outil de l'assistant devient le caractère lui-même, heredoc du shell compris | Échappements doublés dans les commandes, recherche de tout caractère hors du latin et de la typographie française, remis en échappements |
| Styles masqués d'un ODT appliqués à tort | Mêmes noms de styles automatiques dans `styles.xml` et `content.xml` | Seuls les styles communs de `styles.xml` partagés |
| Suppressions relues par LibreOffice en erreur | `getString` d'une modification lève une exception UNO | Curseur de `RedlineStart` à `RedlineEnd` |
| Module en erreur sur une archive à entrées en double | `Archive.trouver` lève `Illisible`, non attrapée | Partie déclarée non menée, lecture des suivantes |
| 438 échecs de la campagne de fuzzing | Localisation d'une entrée illisible relue par son en-tête local | Localisation de l'arrêt |
| Numéro d'ADR déjà pris | La PR #40 a pris ADR-0238 pendant le complément | ADR-0239 à ADR-0242 |

## Écarts par rapport au découpage

- Aucun : le complément suit ADR-0232.

## Résultat

- Module `caracteres` 0.2.0 (`texte`, `docx`, `odt`) ; catalogue 0.17.0 ; schémas inchangés (0.11.0).
- `vk document.docx` ou `vk document.odt` relève dans le corps, les notes, les en-têtes et pieds de page et les commentaires les caractères invisibles inhabituels, le texte caché par des étiquettes, les mots mêlés d'écritures confusables et les lettres de compatibilité, y compris dans le texte supprimé d'une modification suivie et dans le texte masqué par la mise en forme, que ses positions désignent ; le texte masqué fait une information neutre.

## Reste à faire

- Glossaire, parties XML personnalisées, texte des SmartArt et des graphiques d'un DOCX ; documents incorporés d'un ODT.
- Texte masqué par un style d'un DOCX, ou par un style parent d'un ODT ; texte blanc sur blanc ou minuscule.
- Mesure de R-CARACTERES-013 sur le corpus de référence (T100).
