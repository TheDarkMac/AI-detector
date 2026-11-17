# ADR-0222 — Constats des éléments actifs d'un PDF : cinq informations neutres par famille ; module `actifspdf` et versions de T52

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (familles, actions d'affichage, règles et versions précisées par l'assistant)
- **Tâche** : T52
- **Exigences liées** : F-62, F-80, F-81, ES-20 ; ADR-0018, ADR-0152, ADR-0158, ADR-0211, ADR-0218, ADR-0220, ADR-0221

## Contexte

Un élément actif ne dit rien de l'origine d'un contenu, ni d'une retouche : il dit ce que le document demande à un lecteur. F-62 demande de le signaler. Comme pour `revisionspdf` et `pagespdf` (ADR-0211, ADR-0218), le module n'émet aucun constat : des règles « moteur » du catalogue lisent ses observations. Restait à dire lesquelles.

## Options envisagées

### Option A — Une information neutre par famille (recommandée)

Cinq familles : scripts (JavaScript, XFA) ; actions automatiques (à l'ouverture, à l'affichage d'une page…) ; ouvertures hors du document (`Launch`, `GoToR`, `GoToE`, `ImportData`) ; envois et liens sortants (`SubmitForm`, `URI`) ; fichiers incorporés.

- Avantages : chaque phrase dit ce qui a été vu, avec ses limites.
- Inconvénients : cinq règles ; un document ordinaire qui a des liens vers une adresse déclenche celle des envois.

### Option B — Une seule information neutre

« Le document contient N éléments actifs », le détail restant dans les observations.

- Avantages : un seul constat.
- Inconvénients : une phrase qui ne dit plus si l'élément est un lien ou un script à l'ouverture.

### Option C — Observations seules

- Avantages : aucun constat à lire.
- Inconvénients : F-62 demande de signaler ; un lecteur du rapport ne lit pas les observations d'abord.

## Décision

Option A, direction « rien de particulier » pour les cinq. Précisions de l'assistant :

| Famille | Actions | Règle |
| --- | --- | --- |
| `scripts` | `JavaScript` ; `Rendition` qui porte un script (`/JS`) ; formulaire XFA (nature `XFA`) | R-ACTIFSPDF-001 : `actifspdf.scripts` ≥ 1 ; phrase : nombre et natures |
| `automatiques` | Toute action à déclencheur automatique (ADR-0220), sauf celles qui ne changent que l'affichage : `GoTo`, `GoToDp`, `Thread`, `Trans`, `GoTo3DView`, `SetOCGState`, `Hide`, `ResetForm` | R-ACTIFSPDF-002 : `actifspdf.automatiques` ≥ 1 ; phrase : nombre, déclencheurs automatiques, natures |
| `ouvertures` | `Launch`, `GoToR`, `GoToE`, `ImportData` | R-ACTIFSPDF-003 : `actifspdf.ouvertures` ≥ 1 ; phrase : nombre et natures |
| `envois` | `SubmitForm`, `URI` | R-ACTIFSPDF-004 : `actifspdf.envois` ≥ 1 ; phrase : nombre et natures |
| `fichiers` | Spécifications de fichier qui incorporent leur fichier (`/EF`) : arbre `/EmbeddedFiles`, annotations `FileAttachment`, fichiers associés `/AF` | R-ACTIFSPDF-005 : `actifspdf.fichiers` ≥ 1 ; phrase : nombre |

- Une action peut être de deux familles (un script à l'ouverture est un script et une action automatique) : chaque constat dit une chose vraie.
- Les actions d'affichage ne sont pas automatiques au sens de la règle : un document qui s'ouvre sur sa deuxième page (`/OpenAction` `GoTo`) est ordinaire. `Named` reste comptée : une action nommée peut imprimer ou fermer le document. Les actions multimédias (`Sound`, `Movie`, `Rendition` sans script, `RichMediaExecute`) n'ont pas de famille propre ; elles figurent aux observations et comptent parmi les automatiques si elles le sont.
- Fondement « vérification déterministe » : la structure est lue telle qu'elle est déclarée ; seuils par définition (au moins un élément), calibrage « manuel » décrit dans chaque règle.
- Le module ne lit aucune métadonnée identifiante (ADR-0220) : il rejoint les modules sans métadonnées du résumé (ADR-0158).

| Élément | Version |
| --- | --- |
| Module `actifspdf` | 0.1.0, format PDF, exigences F-62, NF-01, ES-06, direction `rien_de_particulier`, aucune bibliothèque |
| Module `pagespdf` | 0.1.0, inchangé : parcours des pages déplacé dans le lecteur (ADR-0221) |
| Catalogue | 0.13.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.9.0, inchangés |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : une phrase commune ne dirait plus ce qui distingue un lien d'un script à l'ouverture.
- Option C écartée : F-62 demande de signaler ; ce qui n'est qu'aux observations ne l'est pas.

## Conséquences

- Sur les échantillons de `tests/donnees/actifs` : `liens.pdf` et `formulaire.pdf` R-ACTIFSPDF-004 ; `ghostscript.pdf` et `chiffre.pdf` R-ACTIFSPDF-001, 002, 003 et 005 ; `javascript.pdf` et `calcul.pdf` R-ACTIFSPDF-001, 002 et 004 ; `piece_jointe.pdf` R-ACTIFSPDF-004 et 005 ; `balise.pdf` R-ACTIFSPDF-002 et 004 ; `xfa.pdf` R-ACTIFSPDF-001 et 004. `document.pdf` et `ghostscript.pdf` de `tests/donnees/pages` ne déclenchent rien.
- R-ACTIFSPDF-004 se déclenche sur tout document qui a des liens vers une adresse (un renvoi interne n'est pas une action) : sa limite le dit, et renvoie à R-ACTIFSPDF-002 pour une adresse ouverte sans geste de l'utilisateur. La part de documents ordinaires qui déclenchent chaque règle se mesurera sur le corpus de référence (T100).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T52 |
