# ADR-0057 — Données identifiantes marquées par l'observation, au module qui la produit

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T11
- **Exigences liées** : NF-18, F-90 ; ES-13 ; ADR-0014, ADR-0031

## Contexte

ES-13 impose de masquer par défaut, dans tous les exports et dans le terminal, les métadonnées nominatives, les numéros de série, les coordonnées GPS, le nom du fichier (ADR-0014) et l'empreinte (ADR-0031), avec une levée explicite par catégorie. Le masquage est fait par T16 ; T11 doit dire où le modèle porte l'information « cette donnée est identifiante ».

## Options envisagées

### Option A — Chaque observation porte sa catégorie identifiante, fixée par le module

- Avantages : le module sait ce qu'est le champ qu'il lit ; T16 masque par catégorie sans rien connaître des formats ; un nouveau format arrive avec son marquage.
- Inconvénients : chaque module doit penser à marquer ; un oubli fuit.

### Option B — Le générateur de rapport tient une liste de champs identifiants

- Avantages : indépendant des modules, une seule liste à relire.
- Inconvénients : la liste doit suivre chaque format (EXIF, XMP, IPTC, PDF, DOCX…) ; un champ oublié fuit aussi, et l'oubli se voit moins, loin du code qui lit le champ.

## Décision

- Une observation porte une **catégorie identifiante** facultative, fixée par le module : `metadonnee_nominative`, `numero_de_serie`, `gps`, `nom_de_fichier`, `empreinte` (liste d'ES-13).
- Le **nom du fichier** et l'**empreinte** de la rubrique Identification sont identifiants d'office, sans marquage.
- Les phrases de constat ne contiennent aucune valeur : leurs paramètres renvoient à des observations (ADR-0058). Masquer une observation masque donc aussi toute phrase qui la cite.

## Raisons

- Option A retenue : le marquage est fait par le code qui connaît le champ, et T16 reste indépendant des formats.
- Option B écartée : une liste centrale doit connaître tous les formats et s'éloigne du code qui lit les champs.

## Conséquences

- Chaque fiche technique liste les champs que son module marque ; chaque module a un test par catégorie qu'il produit.
- T16 masque par catégorie, lève le masquage par catégorie, et annonce la levée en tête du rapport (ES-13).
- T25 (contrôle avant publication) s'appuie sur ces catégories.
- Un P2 compromis peut omettre un marquage, comme il peut forger un constat (RR-01) ; T16 pourra ajouter dans P1 une liste de garde par nom d'observation, sans que cet ADR l'impose.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-28 | Réalisé en T16 : masquage par catégorie, valeur absente de l'export, levée par `--reveler` (ADR-0093, ADR-0095) ; la liste de garde par nom d'observation n'est pas ajoutée, faute de module qui produise une donnée identifiante |
