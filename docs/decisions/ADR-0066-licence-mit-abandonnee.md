# ADR-0066 — Passage à la licence MIT

- **Statut** : Abandonné
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac
- **Tâche** : T12 (avant son démarrage)
- **Exigences liées** : §10 (modèle économique et licence) ; ADR-0011, ADR-0043

## Contexte

Avant de lancer T12, TheDarkMac a proposé de publier l'outil sous licence MIT. ADR-0011, accepté, a fixé Apache-2.0. Le fichier `LICENSE` n'est pas encore ajouté : il attend que l'auteur du cahier des charges dise sous quelle licence son document, versionné dans le dépôt, peut être diffusé (ADR-0011).

## Options envisagées

### Option A — Passer à MIT

Un nouvel ADR remplace ADR-0011 ; le critère de licence des dépendances (ADR-0043) et la déclaration de licence du paquet suivent.

- Avantages : texte court, très répandu, le plus permissif ; les dépendances retenues jusqu'ici (MIT, BSD, PSF, Apache-2.0) restent toutes compatibles.
- Inconvénients : aucune clause explicite sur les brevets, alors que c'est l'avantage pour lequel ADR-0011 avait retenu Apache-2.0.

### Option B — Garder Apache-2.0

- Avantages : la clause sur les brevets protège les utilisateurs et les intégrateurs ; aucun document à reprendre.
- Inconvénients : texte plus long ; obligation de signaler les fichiers modifiés lors d'une redistribution.

## Décision

Option B : la licence reste **Apache-2.0** ; ADR-0011 est inchangé. Le passage à MIT est abandonné.

## Raisons

- Option B retenue par TheDarkMac après que l'assistant a rappelé que MIT n'a pas de clause sur les brevets, et ce que le changement imposait de reprendre.
- Option A abandonnée : elle retirait l'avantage pour lequel Apache-2.0 avait été choisie, sans besoin nouveau qui le justifie.

## Conséquences

- Aucune : ADR-0011, ADR-0043 et la configuration du paquet restent tels quels.
- Le fichier `LICENSE` (Apache-2.0) attend toujours la réponse de l'auteur du cahier.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création, statut « Abandonné » |
