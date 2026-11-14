# ADR-0159 — Lieux nommés et textes libres : deux catégories identifiantes, masquées par défaut

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T25
- **Exigences liées** : F-90, NF-18 ; ES-13 ; menace M-22 ; ADR-0054, ADR-0057, ADR-0093, ADR-0095, ADR-0119, ADR-0128, ADR-0133, ADR-0140

## Contexte

ADR-0119 a écarté, en T20, le marquage des lieux et des textes libres : aucune catégorie d'ES-13 ne les couvrait, et en créer changeait le modèle. Il les a laissés au contrôle avant publication. Or une légende, un titre, des mots-clés ou le nom d'une ville désignent souvent une personne ou l'endroit où elle se trouvait : l'application Dictaphone d'iOS, par exemple, peut nommer un enregistrement d'après le lieu où il a été fait. ADR-0128, ADR-0133 et ADR-0140 ont renvoyé à T25 les titres, sujets, mots-clés, commentaires et propriétés personnalisées.

## Options envisagées

### Option A — Deux catégories, masquées par défaut

`lieu` et `texte_libre`, posées par chaque module, masquées par défaut et levées par `--reveler` comme les cinq autres.

- Avantages : un rapport transmis ne porte plus ces valeurs (M-22) ; même mécanisme que les autres catégories ; le contrôle avant publication les compte.
- Inconvénients : le modèle et les schémas changent (version 0.4.0) ; un titre ou une légende demandent `--reveler texte_libre` pour être lus.

### Option B — Lieu masqué, texte libre seulement signalé

- Avantages : le rapport reste plus lisible.
- Inconvénients : une légende nominative part en clair ; deux régimes pour des données également identifiantes.

### Option C — Signalés sans masquage

- Avantages : aucun changement du modèle.
- Inconvénients : les deux partent en clair dans tout rapport transmis.

## Décision

Option A.

- `CategorieIdentifiante` gagne `lieu` (« lieux nommés ») et `texte_libre` (« textes libres »), entre `gps` et `nom_de_fichier` : les catégories du contenu, puis celles du fichier.
- `VERSION_SCHEMA` passe à **0.4.0** pour le modèle, le schéma du rapport et celui des messages (version commune, ADR-0054) ; `masquage` nomme les sept catégories.
- `--reveler lieu` et `--reveler texte_libre` sont admis ; la liste des choix suit l'énumération.
- Un **lieu nommé** est un nom de lieu (ville, région, pays, sous-lieu, nom d'un lieu, lieu d'archivage). Un **texte libre** est un texte écrit par une personne sans forme fixée : titre, sous-titre, album, description, légende, commentaire, mots-clés, instructions, paroles, propriété personnalisée. Les champs retenus par module sont fixés par ADR-0160.
- Des coordonnées restent `gps`, même dans une structure de lieu.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un nom de personne dans une légende n'est pas moins identifiant qu'un champ « auteur ».
- Option C écartée : elle laisse M-22 entière pour ces champs.
- Le risque d'ADR-0119 (« tout masquer ») ne revient pas : les dates, l'appareil, le logiciel, les dimensions et les autres champs techniques restent en clair, et les phrases des constats ne citent aucun texte libre.

## Conséquences

- Un rapport JSON de schéma 0.3.0 n'est plus relu par `vk --comparer`, comme à chaque changement de version du schéma.
- ES-13 et M-22 du modèle de menace nomment les deux catégories (v1.3).
- Les douze modules de métadonnées changent de version (ADR-0163) ; leurs fiches listent les champs marqués.
- `Title` du dictionnaire Info d'un PDF, laissé en clair par ADR-0128 pour ne pas masquer le cas courant, est désormais un texte libre : il porte souvent le nom du fichier source.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
