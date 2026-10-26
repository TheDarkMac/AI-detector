# ADR-0015 — Analyse par lots, flux, analyse groupée et recherche d'antériorité

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §10 (lots, flux, analyse groupée) ; NF-03, NF-16 ; constat A-26

## Contexte

Le §10 laisse ouverts l'analyse par lots, l'analyse de flux en direct et l'analyse groupée des fichiers d'une même affaire. L'analyse a ajouté la recherche d'antériorité (retrouver une version plus ancienne d'un contenu en ligne), ni dans ni hors du périmètre (A-26).

## Options envisagées

### Option A — Lots simples en V1, le reste exclu ou reporté

- Avantages : plusieurs fichiers en une commande, utile en ligne de commande, sans nouvelle logique d'analyse.
- Inconvénients : aucune cohérence croisée entre fichiers en V1.

### Option B — Un fichier à la fois en V1

- Avantages : le plus simple.
- Inconvénients : l'utilisateur doit enchaîner les commandes lui-même ; le gain de simplicité est faible.

### Option C — Lots et analyse groupée en V1

- Avantages : cohérences croisées (dates, appareils) dès la V1.
- Inconvénients : nouvelle famille de constats (entre fichiers), à définir dans le modèle de données ; allonge le socle.

## Décision

- **Lots** en V1 : plusieurs fichiers en une commande, chacun analysé indépendamment, un rapport par fichier, sans conclusion croisée.
- **Analyse groupée** (cohérences croisées) : candidate pour une V2.
- **Flux en direct** : hors périmètre.
- **Recherche d'antériorité** : hors périmètre.

## Raisons

- Option A retenue : gain d'usage réel pour un coût faible.
- Option B écartée : n'apporte rien par rapport à A.
- Option C écartée pour la V1 : elle demande de définir des constats entre fichiers, alors que le constat unitaire n'est pas encore modélisé (T11).
- Flux exclus : l'analyse d'un flux en direct ne correspond à aucun cas d'usage du §4 et suppose des contraintes de temps réel.
- Recherche d'antériorité exclue : elle suppose d'interroger des moteurs de recherche en ligne avec le contenu, contraire à NF-16 et au fonctionnement hors ligne (ADR-0010) ; c'est une autre famille d'outils, que les vérificateurs ont déjà.

## Conséquences

- T13 accepte plusieurs fichiers ; un fichier hostile ou en échec ne doit pas affecter les rapports des autres (NF-03, isolation par fichier en T14).
- La documentation utilisateur (T103) rappelle que la recherche d'antériorité est une vérification à faire avec d'autres outils.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
