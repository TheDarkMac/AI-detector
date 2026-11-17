# ADR-0231 — Constats des éléments actifs bureautiques : quatre informations neutres par famille ; module `actifsbureau` et versions du complément

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (familles, règles et versions précisées par l'assistant)
- **Tâche** : T52 (complément bureautique)
- **Exigences liées** : F-62, F-80, F-81, ES-20 ; ADR-0152, ADR-0158, ADR-0222, ADR-0228, ADR-0230

## Contexte

Comme pour le PDF (ADR-0222), le module n'émet aucun constat : des règles « moteur » du catalogue lisent ses observations. F-62 demande de signaler ; restait à dire comment.

## Options envisagées

### Option A — Une information neutre par famille (recommandée)

Quatre règles : macros ; éléments déclenchés ou chargés sans geste de l'utilisateur ; objets incorporés qu'un autre programme ouvre ; ressources hors de l'archive.

- Avantages : chaque phrase dit ce qui a été vu, avec ses limites ; mêmes formes que pour le PDF.
- Inconvénients : un document ordinaire qui a des liens vers une adresse déclenche la règle des références.

### Option B — Une seule information neutre

- Avantages : un seul constat.
- Inconvénients : la phrase ne distingue plus une macro à l'ouverture d'un lien.

### Option C — Observations seules

- Avantages : aucun constat à lire.
- Inconvénients : rien n'est signalé au lecteur du rapport, contraire à F-62.

## Décision

Option A, direction « rien de particulier » pour les quatre. Précisions de l'assistant :

| Règle | Condition | Phrase |
| --- | --- | --- |
| R-ACTIFSBUREAU-001 | `actifsbureau.macros` ≥ 1 | nombre d'ensembles de macros et leurs natures |
| R-ACTIFSBUREAU-002 | `actifsbureau.automatiques` ≥ 1 | nombre, déclencheurs automatiques, natures |
| R-ACTIFSBUREAU-003 | `actifsbureau.objets` ≥ 1 | nombre d'objets et leurs natures |
| R-ACTIFSBUREAU-004 | `actifsbureau.externes` ≥ 1 | nombre de ressources hors de l'archive et leurs natures |

- `actifsbureau.automatiques` réunit les événements et les références de déclencheur `ouverture` ou `document` ; un événement d'ouverture lié à une macro et une image liée sont tous deux automatiques. Les événements au geste de l'utilisateur figurent aux observations (`actifsbureau.evenements`) sans règle propre : la macro qu'ils appellent est signalée par R-ACTIFSBUREAU-001 quand elle est dans le document.
- Fondement « vérification déterministe » : la structure est lue telle qu'elle est déclarée ; seuils par définition (au moins un élément), calibrage « manuel » décrit dans chaque règle.
- Le module ne lit aucune métadonnée identifiante (ADR-0230) : il rejoint les modules sans métadonnées du résumé (ADR-0158).

| Élément | Version |
| --- | --- |
| Module `actifsbureau` | 0.1.0, formats DOCX et ODT, exigences F-62, NF-01, ES-06, direction `rien_de_particulier`, bibliothèque `expat` |
| Modules `ooxml`, `odf`, `xmp` | 0.3.1, 0.3.1 et 0.7.1 : correction du lecteur XML partagé (ERR-0012), sans changement de ce qu'ils lisent |
| Catalogue | 0.15.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.10.0, inchangés |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : une phrase commune ne dirait plus ce qui distingue un lien d'une macro à l'ouverture.
- Option C écartée : F-62 demande de signaler.

## Conséquences

- Sur les échantillons de `tests/donnees/actifsbureau` : `macros.odt` R-ACTIFSBUREAU-001 et 002 ; `liens.odt` et `liens.docx` R-ACTIFSBUREAU-002 et 004 ; `objet.odt` et `objet.docx` R-ACTIFSBUREAU-003. `document.docx` et `document.odt` de `tests/donnees/metadonnees` ne déclenchent rien.
- La part de documents ordinaires qui déclenchent chaque règle (liens, tableaux incorporés, modèles d'entreprise) se mesurera sur le corpus de référence (T100).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début du complément bureautique de T52 |
