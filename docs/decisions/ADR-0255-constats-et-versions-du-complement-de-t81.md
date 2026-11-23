# ADR-0255 — Constats des images d'un DOCX ou d'un ODT : cinq informations neutres ; versions du complément de T81

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, sur proposition de l'assistant, dans le cadre fixé par ADR-0252 à ADR-0254 et sur le modèle d'ADR-0227
- **Tâche** : complément de T81
- **Exigences liées** : F-25, F-63, F-80, F-81, F-82 ; ADR-0152, ADR-0158, ADR-0226, ADR-0227, ADR-0252 à ADR-0254

## Contexte

Comme pour un PDF (ADR-0227), une image extraite ne dit rien par elle-même : les modules d'image en tirent leurs constats sur la partie extraite. Le rapport doit dire, pour le document, quelles images ont été analysées et lesquelles ne l'ont pas été, et pourquoi (F-25, F-82).

Un essai sur l'ODT chiffré de LibreOffice 25.2.3.2 montre que le paquet entier est chiffré dans une seule entrée, `encrypted-package` (ODF 1.4) : le manifeste ne déclare plus d'images, que le module ne peut même pas compter.

## Options envisagées

### Option A — Une information neutre par cas (proposée)

Images acheminées ; images d'un autre type ; images au-delà de la borne ; images compressées trop grandes ; ODT chiffré.

- Avantages : chaque phrase dit ce qui a été vu et ce qui ne l'a pas été, avec ses limites ; celles d'`imagespdf` sont reprises.
- Inconvénients : cinq règles ; la deuxième se déclenche sur bien des documents illustrés (schémas en GIF, EMF, SVG).

### Option B — Observations seules

- Avantages : aucun constat à lire.
- Inconvénients : une image non analysée ne serait dite nulle part, hors des observations.

## Décision

Option A, direction « rien de particulier », fondement « vérification déterministe », seuils par définition, calibrage « manuel » décrit dans chaque règle :

| Règle | Conditions | Phrase |
| --- | --- | --- |
| R-IMAGESBUREAU-001 | `imagesbureau.acheminees` ≥ 1, `imagesbureau.acheminables` ≥ 1, `imagesbureau.acheminees.formats` | Nombre d'images lisibles, nombre analysées comme parties extraites, formats |
| R-IMAGESBUREAU-002 | `imagesbureau.non_acheminees` ≥ 1, `imagesbureau.non_acheminees.types` | Nombre et types des images non analysées |
| R-IMAGESBUREAU-003 | `imagesbureau.au_dela` ≥ 1 | Nombre d'images au-delà de la borne (ADR-0226) |
| R-IMAGESBUREAU-004 | `imagesbureau.trop_grandes` ≥ 1 | Nombre d'images compressées de plus de 16 Mio décompressées (ADR-0254) |
| R-IMAGESBUREAU-005 | `imagesbureau.chiffre` vrai | ODT chiffré : images non analysées, comptées ou non selon le chiffrement |

Observations du module : `images`, `vignette`, `acheminables`, `acheminees` et ses formats, `decompressees`, `au_dela`, `trop_grandes`, `non_acheminees` et ses types, `chiffre`. Le module ne lit aucune métadonnée identifiante : il rejoint les modules sans métadonnées du résumé (ADR-0158).

| Élément | Version |
| --- | --- |
| Module `imagesbureau` | 0.1.0 (nouveau), formats `docx` et `odt`, exigence F-63, direction `rien_de_particulier`, bibliothèque `expat`, `extrait` : `jpeg`, `png`, `webp`, `heic` |
| Autres modules | Inchangés ; le lecteur ZIP commun gagne `Archive.donnees` et la borne de `Archive.lire`, sans changer ce qu'il lit pour eux |
| Catalogue | 0.20.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères (1 021) |
| Schémas du rapport et des messages | 0.13.0 (ADR-0254) |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A proposée par l'assistant pour les raisons d'ADR-0227, que TheDarkMac a retenues pour `imagespdf` ; validée par TheDarkMac pendant la revue de la PR du complément de T81 (« Oui, valide ADR-0255 »), sans raison supplémentaire.
- Option B écartée : F-82 demande de dire ce qui n'est pas analysé.
- R-IMAGESBUREAU-005 sur le seul chiffrement, sans nombre d'images : le chiffrement d'un paquet entier ne les laisse pas compter.

## Conséquences

- R-IMAGESBUREAU-002 se déclenche sur tout document qui a des images d'un autre format : sa description le dit. La part de documents ordinaires qui déclenchent chaque règle se mesurera sur le corpus de référence (T100).
- Les constats des modules d'image sur une partie extraite gardent leurs règles et leurs niveaux, avec la limite de R-IMAGESBUREAU-001 : le logiciel qui écrit le document peut réencoder une image ou en retirer les métadonnées.
- Le registre des empreintes reçoit la version 0.20.0 du catalogue.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création, statut « Proposé » |
| 2026-11-23 | Validé par TheDarkMac pendant la revue de la PR du complément de T81 : statut « Accepté » |
