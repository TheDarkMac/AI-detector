# ADR-0211 — Constats des versions d'un PDF : une information neutre et deux indices faibles vers la retouche ; module `revisionspdf` et versions de T50

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (règles et versions précisées par l'assistant)
- **Tâche** : T50
- **Exigences liées** : F-60, F-80, F-81, F-90, ES-20 ; ADR-0018, ADR-0101, ADR-0152, ADR-0158, ADR-0188, ADR-0207 à ADR-0209

## Contexte

Les observations du module (ADR-0207 à ADR-0209) disent combien de versions garde un PDF, ce que chacune change et ce qui est signé. Restait à dire ce que le rapport en conclut. Comme pour les modules de signal (ADR-0188), le module n'émet aucun constat : des règles « moteur » du catalogue lisent ses observations. Un indice non évalué sur le corpus de référence reste « faible » (ADR-0101).

## Options envisagées

### Option A — Une information neutre et deux indices (recommandée)

- **R-REVISIONSPDF-001**, information neutre : le PDF garde au moins deux versions.
- **R-REVISIONSPDF-002**, indice faible vers la retouche : au moins une version postérieure à la première change des objets non reconnus (ADR-0208).
- **R-REVISIONSPDF-003**, indice faible vers la retouche : après la dernière version couverte par une signature complète (ADR-0209), au moins une version change des objets non reconnus ; ce qu'affiche un lecteur n'est plus ce qui a été signé.
- Avantages : le cas qui compte pour un vérificateur (contenu changé, surtout après signature) ressort ; l'ajout légitime reste neutre.
- Inconvénients : un auteur qui enregistre ses propres corrections en mise à jour incrémentale déclenche R-REVISIONSPDF-002.

### Option B — L'information neutre seulement

- Avantages : aucun indice contestable avant T51.
- Inconvénients : le classement d'ADR-0208 ne sert à rien au résumé ; un document modifié après signature n'y apparaît pas.

## Décision

Option A. Précisions de l'assistant :

- Direction « retouche » : les objets non reconnus changent le contenu du document, pas son encodage (la transformation, ADR-0055) ; un PDF n'a pas d'origine IA à lire dans sa structure.
- Fondement « vérification déterministe » : la structure est lue telle qu'elle est déclarée, sans mesure statistique ni déclaration du fichier ; une règle d'indice reste un indice (ES-20).
- Seuils par définition (au moins deux versions, au moins une version non reconnue), calibrage « manuel » décrit dans chaque règle.
- Une analyse non menée du module ne rend pas le contrôle avant publication incomplet : il ne lit aucune métadonnée identifiante (ADR-0158), seulement les dates du dictionnaire Info.

| Élément | Version |
| --- | --- |
| Module `revisionspdf` | 0.1.0, format PDF, exigences F-60 et F-84, directions `retouche` et `rien_de_particulier`, aucune bibliothèque |
| Catalogue | 0.11.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé |
| Schémas du rapport et des messages | 0.8.0 (ADR-0212) |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : laisse sans suite ce que F-60 demande de distinguer.
- R-REVISIONSPDF-003 en plus de R-REVISIONSPDF-002 : la modification après signature est le procédé des attaques par sauvegarde incrémentale (*Incremental Saving Attacks*, que rappellent Mainka, Mladenov et Rohlmann, NDSS 2021) ; la phrase le dit au résumé, avec le numéro de la version signée.

## Conséquences

- Sur les échantillons : `modifie.pdf` donne R-REVISIONSPDF-001 et 002 ; `signe_modifie.pdf` les trois ; `formulaire.pdf`, `signe_annote.pdf`, `certifie.pdf` seulement la première.
- La part de documents ordinaires qui déclenchent R-REVISIONSPDF-002 se mesurera sur le corpus de référence (T100) ; un niveau plus élevé demandera cette mesure.
- `revisionspdf` rejoint les modules sans métadonnées du contrôle avant publication (`doublejpeg`, `dwtdct`, `ela`).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création ; option choisie par TheDarkMac au début de T50 |
