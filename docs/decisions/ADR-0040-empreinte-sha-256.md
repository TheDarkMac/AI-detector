# ADR-0040 — Empreinte cryptographique : SHA-256

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : F-05, NF-06, NF-07 ; ES-08 ; constat A-30 ; ADR-0029, ADR-0031

## Contexte

F-05 demande l'empreinte cryptographique du fichier sans préciser l'algorithme ni ce qui est haché (A-30). Le découpage avait retenu SHA-256 sans ADR. L'empreinte sert aussi à vérifier que le fichier analysé est celui qui a été identifié (ES-08), et à identifier le catalogue et la liste de confiance (ADR-0029). Elle est une donnée identifiante, masquée par défaut (ADR-0031).

## Options envisagées

### Option A — SHA-256 seul

- Avantages : standard ; dans la bibliothèque standard (`hashlib`) ; utilisé par C2PA et par les outils de vérification courants.
- Inconvénients : un outil d'expertise ancien qui n'affiche que MD5 ou SHA-1 ne permet pas la comparaison directe.

### Option B — SHA-256, MD5 et SHA-1

- Avantages : comparaison avec d'anciens outils.
- Inconvénients : MD5 et SHA-1 sont cassés (collisions fabricables) ; trois identifiants à masquer au lieu d'un.

### Option C — SHA-256 et SHA3-256

- Avantages : deux familles indépendantes.
- Inconvénients : aucune attaque connue sur SHA-256 ne le justifie ; un identifiant de plus.

## Décision

- L'empreinte est **SHA-256**, calculée sur le **fichier entier, octet pour octet**, et écrite en hexadécimal minuscule.
- Le même algorithme identifie le catalogue, la liste de confiance (ADR-0029) et, en T91, le rapport à horodater.
- Elle est masquée par défaut au rapport (ADR-0031).

## Raisons

- Option A retenue : un seul algorithme, robuste et reconnu, sans dépendance.
- Option B écartée : un algorithme cassé ne prouve pas l'identité d'un fichier, et chaque identifiant de plus est une donnée identifiante de plus.
- Option C écartée : coût sans menace qui le justifie ; un changement d'algorithme reste possible par un nouvel ADR.

## Conséquences

- T13 calcule l'empreinte dans le processus principal ; le processus de travail la recalcule sur ce qu'il a lu (ES-08, ADR-0036).
- Le schéma du rapport (T16) nomme l'algorithme à côté de la valeur, pour permettre un changement ultérieur.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Réalisé en T13 : empreinte du principal à l'ouverture, recalculée par le travail après les modules, à défaut de nouveau par le principal (ADR-0075) |
