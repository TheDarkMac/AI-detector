# ADR-0200 — Visualisations au rapport : rubrique, image `data:`, avertissement au-dessus, catégorie identifiante « contenu »

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (forme des objets et des textes précisée par l'assistant)
- **Tâche** : T42
- **Exigences liées** : F-32, F-84, F-83, ES-04, ES-12, ES-13, NF-06 ; ADR-0025, ADR-0031, ADR-0036, ADR-0058, ADR-0094, ADR-0095

## Contexte

La carte ELA est la première visualisation (F-84). ADR-0094 interdit toute image dans le rapport HTML et prévoyait qu'une visualisation demanderait d'autoriser `img-src data:` par un nouvel ADR. Le modèle n'avait aucune place pour une image : une observation est un scalaire ou une liste, et un texte y est borné à 4 096 caractères. Il fallait dire où va la carte, où va l'avertissement d'interprétation (F-32), et si la carte est masquée : elle montre le contenu de la photo, réduit d'un facteur 8, alors que le rapport masque par défaut jusqu'à l'empreinte du fichier (ADR-0031, ES-13).

## Options envisagées

### Place de la carte

- **A — Rubrique « Visualisations »** : la carte en PNG, en base64 dans le JSON, en image `data:` dans le HTML (politique `img-src data:`), l'avertissement juste au-dessus, texte fixe dans `textes.toml` ; nouvel objet du modèle, schéma du rapport 0.7.0.
- **B — Fichier à côté** : la carte écrite en PNG à côté du rapport (`--rapport DOSSIER`), citée par son nom et son SHA-256 ; le HTML reste sans image, l'avertissement dans la rubrique de l'analyse.

### Masquage

- **A — Masquée par défaut** : nouvelle catégorie identifiante « contenu » ; un rapport partagé ne montre pas l'image d'une source ; la rubrique dit qu'une carte existe et comment l'afficher (`--reveler contenu`) ; la levée est annoncée en tête du rapport comme les autres.
- **B — Affichée par défaut** : l'utilisateur détient déjà l'image ; la rubrique « contrôle avant publication » rappelle qu'un rapport qui la contient en montre le contenu.

## Décision

Option A dans les deux cas. Précisions de l'assistant :

- **Modèle** : objet `Visualisation` (module, nature, largeur, hauteur, PNG, localisation, partie), nature `carte_ela` ; catégorie identifiante fixe `contenu`. Le modèle vérifie la signature du PNG, que les dimensions de son en-tête sont celles annoncées, et sa taille (768 Kio au plus, pour que son écriture en base64 tienne dans un message d'1 Mio) ; au plus 16 visualisations par rapport. Une visualisation est un résultat de sa technique : comme une observation, elle n'appartient qu'à une technique appliquée ou partielle, et une technique qui n'a rendu qu'une visualisation et une analyse non menée est partielle.
- **Protocole** : message `visualisation` du processus de travail ; `Contexte.visualiser()` pour les modules ; l'empreinte annoncée est recalculée à la réception.
- **JSON** : `visualisations`, liste toujours présente ; chaque élément porte `type_media` (`image/png`), les dimensions, l'empreinte SHA-256 du PNG et ses `donnees` en base64. Masqué, il perd `donnees` et `empreinte` : l'empreinte relierait deux rapports de la même image, comme celle du fichier (ADR-0031). `vk --comparer` ne compare ni l'une ni l'autre si l'un des deux exports les masque.
- **HTML** : rubrique « Visualisations » après « Informations neutres » et avant « Analyses non menées » (ordre d'ADR-0098 complété) ; pour chaque visualisation, son titre, l'avertissement d'interprétation en paragraphes, la part de l'image couverte, puis l'image (`<img>` en `data:image/png;base64`, texte de remplacement, rendu `pixelated`) ou la mention du masquage, et l'empreinte. La politique de sécurité du contenu gagne `img-src data:`.
- **Résumé** : une ligne annonce les visualisations et renvoie à leur avertissement.
- **Avertissement** (F-32) : six phrases, dans `textes.toml` ; recopiées dans la fiche `ela`.

## Raisons

- Les deux options A retenues par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec les options.
- Place B écartée : un rapport en deux fichiers se sépare facilement, et l'avertissement serait loin de l'image.
- Masquage B écarté : le masquage par défaut protège les sources d'un rapport partagé (ES-13) ; une carte en montre plus qu'une empreinte.
- `img-src data:` n'ouvre aucun script ni aucune ressource distante ; seule une image PNG vérifiée par le modèle, encodée par l'export, entre dans le document.

## Conséquences

- Schéma du rapport et des messages 0.7.0 (ADR-0201) ; un rapport de version 0.6.0 n'est plus relu par `vk --comparer`, comme à chaque version.
- ADR-0094 : la règle « aucun élément `img` » devient « aucun élément `img` hors des visualisations, toujours en `data:` » ; un renvoi est ajouté à son historique.
- Les catégories identifiantes passent de sept à huit ; `--reveler` accepte `contenu`.
- D'autres visualisations (spectre, spectrogramme, chronologie PDF) prendront une nature de plus, sans nouveau mécanisme.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
| 2026-11-16 | Renvoi : la chronologie des révisions PDF est un tableau, nouvelle forme de visualisation non masquée ; la prévision « sans nouveau mécanisme » ne tient pas pour elle ([ADR-0212](ADR-0212-chronologie-en-tableau.md)) |
| 2026-11-17 | Renvoi : la catégorie `contenu` couvre aussi le texte écrit par des étiquettes Unicode ; son libellé devient « contenu du fichier » ([ADR-0234](ADR-0234-caracteres-invisibles.md)) (T80) |
