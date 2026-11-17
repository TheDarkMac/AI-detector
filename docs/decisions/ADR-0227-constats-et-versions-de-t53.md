# ADR-0227 — Constats des images d'un PDF : quatre informations neutres ; module `imagespdf` et versions de T53

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, sur proposition de l'assistant, dans le cadre fixé par ADR-0223 à ADR-0226 et sur le modèle d'ADR-0222
- **Tâche** : T53
- **Exigences liées** : F-25, F-63, F-80, F-81, F-82 ; ADR-0018, ADR-0152, ADR-0158, ADR-0222, ADR-0224, ADR-0225, ADR-0226

## Contexte

Une image extraite ne dit rien par elle-même : ce sont les modules d'image qui en tirent leurs constats, sur la partie extraite. Le rapport doit pourtant dire, pour le document, quelles images ont été analysées et lesquelles ne l'ont pas été, et pourquoi (F-25, F-82). Comme `actifspdf` (ADR-0222), le module n'émet aucun constat ; des règles « moteur » du catalogue lisent ses observations.

## Options envisagées

### Option A — Une information neutre par cas (retenue)

Images acheminées ; images d'un autre filtre ; images au-delà de la borne ; images d'un document chiffré.

- Avantages : chaque phrase dit ce qui a été vu et ce qui ne l'a pas été, avec ses limites.
- Inconvénients : quatre règles ; la deuxième se déclenche sur la plupart des documents illustrés.

### Option B — Observations seules

- Avantages : aucun constat à lire.
- Inconvénients : la partie extraite apparaît sans que le rapport dise d'où elle vient ni ce qui manque ; une image non analysée ne serait dite nulle part, hors des observations.

## Décision

Option A, direction « rien de particulier », fondement « vérification déterministe », seuils par définition (au moins une image), calibrage « manuel » décrit dans chaque règle :

| Règle | Conditions | Phrase |
| --- | --- | --- |
| R-IMAGESPDF-001 | `imagespdf.acheminees` ≥ 1, `imagespdf.jpeg` ≥ 1, `imagespdf.acheminees.pages` | Nombre de JPEG, pages, nombre analysées comme parties extraites |
| R-IMAGESPDF-002 | `imagespdf.non_acheminees` ≥ 1, `imagespdf.non_acheminees.filtres`, `imagespdf.non_acheminees.pages` | Nombre, pages et filtres des images non analysées |
| R-IMAGESPDF-003 | `imagespdf.au_dela` ≥ 1 | Nombre de JPEG au-delà de la borne (ADR-0226) |
| R-IMAGESPDF-004 | `imagespdf.chiffre` vrai, `imagespdf.images` ≥ 1 | Nombre d'images d'un document chiffré, non analysées |

Observations du module : `pages`, `pages_lues`, `images`, `jpeg`, `acheminees` et ses pages, `au_dela`, `non_acheminees` et ses filtres et ses pages, `chiffre`, `arret_avant_budget`, `recherche_coupee`. Le module ne lit aucune métadonnée identifiante : il rejoint les modules sans métadonnées du résumé (ADR-0158).

| Élément | Version |
| --- | --- |
| Module `imagespdf` | 0.1.0, format PDF, exigence F-63, direction `rien_de_particulier`, aucune bibliothèque, `extrait` : `jpeg` |
| Autres modules | Inchangés ; leurs manifestes portent `extrait = []`, qui ne change pas ce qu'ils font |
| Catalogue | 0.14.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.10.0 (ADR-0224) |
| Schéma des manifestes | Champ `extrait` obligatoire |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A proposée par l'assistant pour les raisons d'ADR-0222, que TheDarkMac a retenues pour `actifspdf` ; validée par TheDarkMac pendant la revue de la PR de T53 (« valide ces adr »), sans raison supplémentaire.
- Option B écartée : F-82 demande de dire ce qui n'est pas analysé ; une partie extraite sans phrase qui la présente se lit mal.

## Conséquences

- R-IMAGESPDF-002 se déclenche sur tout document qui a des images en pixels compressés : sa description le dit. La part de documents ordinaires qui déclenchent chaque règle se mesurera sur le corpus de référence (T100).
- Les constats des modules d'image sur une partie extraite gardent leurs règles et leurs niveaux : un JPEG d'un PDF est lu comme un JPEG soumis seul. Les règles qui supposent un fichier tel qu'il sort d'un appareil ou d'un logiciel (absence de métadonnées, tables de libjpeg sans métadonnées) se lisent avec la limite de R-IMAGESPDF-001 : le logiciel qui écrit le PDF peut réencoder une image ou en retirer les métadonnées.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création, statut « Proposé » |
| 2026-11-17 | Validé par TheDarkMac pendant la revue de la PR de T53 : statut « Accepté » |
