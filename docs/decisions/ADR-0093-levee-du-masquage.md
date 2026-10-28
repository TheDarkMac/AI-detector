# ADR-0093 — Levée du masquage : `--reveler CATEGORIE`, une catégorie à la fois

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T16
- **Exigences liées** : NF-18, §6 du cahier (« Données identifiantes ») ; ES-13 ; menaces M-22, C-05 ; RR-08 ; ADR-0014, ADR-0025, ADR-0031, ADR-0057

## Contexte

ES-13 masque par défaut, dans tous les exports et au terminal, cinq catégories de données identifiantes : métadonnées nominatives, numéros de série, coordonnées GPS, nom du fichier, empreinte (ADR-0057). La levée doit être explicite, par catégorie, et un rapport démasqué doit l'annoncer en tête. Restait la forme de cette levée.

## Options envisagées

### Option A — `--reveler CATEGORIE`, répétable, sans raccourci

- Avantages : chaque catégorie montrée est nommée dans la commande ; le terminal et les exports disent la même chose.
- Inconvénients : lever les cinq demande cinq options.

### Option B — Les catégories, plus `--reveler tout`

- Avantages : plus rapide.
- Inconvénients : une seule option suffit à tout démasquer, sans que l'utilisateur ait nommé ce qu'il montre (C-05).

### Option C — Levée pour les exports seulement

- Avantages : le terminal, souvent partagé (capture d'écran, journal de session), reste toujours masqué.
- Inconvénients : l'utilisateur qui veut vérifier une empreinte doit ouvrir un fichier ; deux règles à expliquer.

## Décision

Option A.

- `vk --reveler CATEGORIE`, répétable ; les valeurs admises sont `metadonnee_nominative`, `numero_de_serie`, `gps`, `nom_de_fichier`, `empreinte`. Toute autre valeur est refusée (code 2). En bibliothèque : `exporter_json(analyse, reveler=…)`, `exporter_html(analyse, reveler=…)`.
- La levée vaut pour le résumé du terminal et pour les deux exports de la même commande.
- Elle est annoncée en tête : première alerte du résumé et du rapport HTML, avec la liste des catégories levées et le rappel de vérifier à qui l'on transmet le rapport ; dans le JSON, l'objet `masquage` qui suit `version_schema` liste les catégories masquées et levées (ADR-0095).
- Une donnée masquée est **absente** de la sortie, jamais cachée par la présentation : le HTML et le JSON ne la contiennent pas ; le HTML et le terminal écrivent à sa place « [masqué : *catégorie*] ».

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle rend la levée totale aussi facile qu'une erreur de frappe, ce que C-05 décrit.
- Option C écartée : une règle de plus pour une protection que l'annonce en tête apporte déjà ; RR-08 reste de toute façon un choix de l'utilisateur.
- Absente plutôt que cachée : un masquage par la présentation (style, élément replié) laisserait la donnée dans le fichier transmis.

## Conséquences

- Le rapport HTML a une rubrique « Données identifiantes » : l'état de chaque catégorie et la commande pour en lever une.
- Le nom du fichier n'apparaît jamais dans le titre du document HTML, même levé : il resterait dans l'historique du navigateur.
- RR-08 (rapport démasqué transmis) reste un risque résiduel, réduit par l'annonce en tête.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
