# ADR-0213 — Contenus de pages et polices d'un PDF : lus par le lecteur du projet ; arrêt avant le budget

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (bornes et arrêt avant le budget précisés par l'assistant)
- **Tâche** : T51
- **Exigences liées** : F-61, ES-03, ES-18, ES-19, NF-01, NF-02 ; menaces M-01, M-31 ; ADR-0043, ADR-0078, ADR-0124, ADR-0125

## Contexte

F-61 demande de relever les textes superposés et les polices incohérentes : il faut lire les flux de contenu des pages (ISO 32000-2, §7.8.2 et §8 : opérateurs et opérandes, images en ligne) et les dictionnaires de polices (§9). ADR-0124 a confié la structure du PDF au lecteur du projet et laissé `pypdf` candidate pour « les contenus de pages et les polices (T51 à T53) », le choix revenant à la tâche qui l'utilise (ADR-0043, point 6).

Un flux de contenu est long : une page de texte compte des milliers d'opérations, chacune de plusieurs opérandes. Le budget d'un module est d'un million d'objets (`OBJETS_MAX`, ADR-0078) ; un module qui le dépasse perd tous ses résultats (ADR-0060).

## Options envisagées

### Option A — Lecteur du projet, étendu aux flux de contenu (recommandée)

Une fonction `operations` dans `modules/_lecture/pdf.py` : le même analyseur lexical, chaque mot-clé qui n'ouvre pas un opérande étant un opérateur, les images en ligne (`BI` … `ID` … `EI`) passées.

- Avantages : aucune dépendance ; chaque opérande et chaque opération comptent dans le budget (ES-03) ; un flux mal formé s'arrête et le dit, sans réparation (ADR-0125) ; le fuzzing du lecteur le couvre déjà.
- Inconvénients : un interpréteur à écrire (état graphique, état du texte, polices), à tester et à fuzzer.

### Option B — `pypdf`

- Avantages : bibliothèque BSD-3-Clause mûre, qui sait extraire le texte d'une page.
- Inconvénients : elle relit tout le fichier par son propre lecteur, qui reconstruit en mode tolérant une table fausse ; ses parcours ne comptent pas dans le budget du module ; un analyseur tiers de plus exposé au fichier (M-01) ; son extraction de texte ne donne pas les boîtes dans l'espace de la page, qu'il faudrait recalculer.

## Décision

Option A. Précisions de l'assistant :

- **Interprétation** : flux de contenu de la page (ses flux mis bout à bout), formes appelées par `Do` (huit niveaux au plus), puis apparences des annotations (ADR-0214) ; état graphique, état du texte, chemins ; rien n'est dessiné, aucune image décodée.
- **Bornes** : 4 096 pages, 65 536 textes par page ; `FlateDecode` seul (ADR-0124).
- **Arrêt avant le budget** : l'interprétation s'arrête, toutes les 1 024 opérations, dès qu'il reste moins de 262 144 objets du budget (`OBJETS_RESERVES`), pour envoyer les observations déjà faites ; `Contexte.objets` donne le compte. `pagespdf.pages_lues` et `pagespdf.arret_avant_budget` disent ce qui a été lu.
- **Dernière version seulement** : ce qu'un lecteur affiche ; les versions antérieures relèvent de `revisionspdf` (ADR-0217).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : la reconstruction silencieuse contredit l'explicabilité (P-02), et ses parcours échappent au budget ; le gain d'écriture ne compense pas une dépendance exposée au fichier.
- Arrêt avant le budget plutôt que le dépassement : un document long perdrait sinon toutes ses observations (ADR-0060) ; un relevé partiel dit sur quelles pages il porte.

## Conséquences

- Nouveau module `pagespdf` (ADR-0218) ; `operations` rejoint le lecteur ; `Contexte.objets` s'ajoute au contexte d'un module.
- Le fuzzing passe `pagespdf` sur les PDF, et deux échantillons de `tests/donnees/pages` s'ajoutent à ceux du fuzzing.
- ADR-0124 et ADR-0043 : `pypdf` n'est plus prévue pour T51 ; elle reste candidate pour T52 et T53 si une tâche en a besoin.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T51 |
| 2026-11-17 | Renvoi : arrêt avant le budget repris par `actifspdf` ; parcours de l'arbre des pages déplacé dans le lecteur (T52, ADR-0221) |
