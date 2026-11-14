# ADR-0158 — Contrôle avant publication : rubrique du rapport dérivée des catégories identifiantes

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T25
- **Exigences liées** : F-90 (partie métadonnées), CU-5, NF-18 ; ES-13 ; ADR-0014, ADR-0018, ADR-0057, ADR-0059, ADR-0093, ADR-0095, ADR-0098

## Contexte

ADR-0014 limite le contrôle avant publication de la V1 aux marques identifiantes des métadonnées : auteur, numéro de série d'appareil, coordonnées GPS, logiciel nominatif. Depuis T20 et T21, chaque module de métadonnées marque ces champs dans une catégorie identifiante (ADR-0057, ADR-0119), que le rapport masque par défaut (ADR-0093). Rien, en revanche, ne dit à l'utilisateur que le fichier les porte, ni qu'il faut les retirer avant de le publier : le masquage protège le rapport, pas le fichier publié. Restait la forme du signalement.

## Options envisagées

### Option A — Rubrique et ligne du résumé, dérivées à l'export

La rubrique « Contrôle avant publication » du HTML, une ligne du résumé (terminal et HTML) et une ligne par catégorie au terminal, calculées à l'export à partir des catégories que les modules posent déjà.

- Avantages : aucun nouveau marquage, aucune règle, aucun changement du JSON (ADR-0059 : le JSON porte les données, le résumé se dérive) ; le contrôle suit chaque correction de marquage d'un module sans autre travail.
- Inconvénients : le contrôle ne vaut que ce que valent les marquages des modules.

### Option B — Règles du catalogue

Une règle par champ identifiant (`R-PUB-…`), qui produit un constat « information neutre ».

- Avantages : chaque signalement a son identifiant, sa version et ses limites, comme les autres constats.
- Inconvénients : la liste des champs serait tenue deux fois, dans le module et dans le catalogue ; la protection des sources se mêlerait aux constats de provenance, que le résumé compte (ADR-0018).

### Option C — Commande séparée

`vk --avant-publication FICHIER`, avec une sortie propre au contrôle.

- Avantages : usage explicite pour CU-5.
- Inconvénients : une seconde sortie à maintenir ; le contrôle absent du rapport habituel, que l'utilisateur lit de toute façon.

## Décision

Option A.

- `Presentation.marques()` groupe les observations identifiantes par catégorie, dans l'ordre d'ES-13 ; `Presentation.publication()` en tire la ligne du résumé : nombre de données, catégories, et rappel que l'outil ne les retire pas ; sinon « aucune donnée identifiante relevée dans les métadonnées lues ».
- Le contrôle est dit **incomplet**, par une seconde ligne, dès qu'une analyse non menée n'est pas « hors V1 » : partie hors périmètre, module désactivé, format partiel, fichier tronqué, erreur, limite. Les techniques hors V1 ne lisent pas de métadonnées.
- Rubrique HTML entre « Couverture » et « Données identifiantes » : un tableau par catégorie (nombre, identifiant et nom de chaque observation), les lignes du résumé, puis ce que le contrôle ne couvre pas. La rubrique ne contient **jamais** de valeur, même levée : la valeur reste dans la rubrique « Observations », masquée selon sa catégorie.
- Terminal : après le résumé, une ligne par catégorie présente, avec les noms des observations, sans valeur.
- « Logiciel nominatif » (ADR-0014) : aucun champ normalisé ne nomme le titulaire d'une licence ; le contrôle n'a pas de catégorie pour lui, et ce manque est écrit dans les fiches.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : une seconde liste des champs, loin du code des formats, est ce qu'ADR-0057 a refusé.
- Option C écartée : une sortie de plus pour une information qui tient en une rubrique.
- Rubrique sans valeur : le contrôle dit quoi retirer ; montrer la valeur n'y ajoute rien et dupliquerait ce que le masquage doit cacher.

## Conséquences

- L'ordre des rubriques d'ADR-0098 gagne une rubrique ; le résumé, une ou deux lignes.
- Le JSON et son schéma ne changent pas pour le contrôle ; ils changent pour les deux catégories d'ADR-0159.
- Les noms des observations sont écrits en clair : certains viennent du fichier (propriété personnalisée, description d'une trame `TXXX`) et peuvent nommer une personne, comme dans la rubrique « Observations » (ADR-0117). La rubrique le dit.
- Le contrôle ne couvre ni le contenu (texte visible, visages, points de traçage, T94), ni le nom du fichier ; la rubrique le dit aussi.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
