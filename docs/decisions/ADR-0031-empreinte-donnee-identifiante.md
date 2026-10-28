# ADR-0031 — L'empreinte du fichier est une donnée identifiante

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T03
- **Exigences liées** : F-05, NF-15, NF-18 ; §6 du cahier (rubrique « Identification ») ; constat A-48 ; menace M-22

## Contexte

F-05 exige d'inscrire au rapport l'empreinte cryptographique du fichier. Or qui détient l'original peut calculer la même empreinte : un rapport transmis ou publié lui prouve que l'auteur du rapport avait ce fichier. Si l'organisation a diffusé une variante par destinataire, l'empreinte désigne même le destinataire qui a fait fuiter le document (A-48). ADR-0014 a déjà rangé le nom du fichier parmi les données identifiantes.

## Options envisagées

### Option A — Donnée identifiante, masquée par défaut dans les exports

- Avantages : même traitement que le GPS ou le nom du fichier (NF-18), déjà prévu ; rien de nouveau à expliquer.
- Inconvénients : un lecteur du rapport masqué ne peut pas vérifier qu'il porte sur un fichier qu'il détient.

### Option B — Empreinte à clé par défaut

- Avantages : une empreinte calculée avec une clé secrète de l'utilisateur (HMAC) lui permet de vérifier, sans qu'un tiers puisse confirmer la possession.
- Inconvénients : une clé à créer, à conserver et à expliquer ; un mécanisme inhabituel pour le public visé.

### Option C — Toujours visible

- Avantages : F-05 appliquée à la lettre.
- Inconvénients : M-22 entière.

## Décision

L'empreinte est **toujours calculée** et inscrite au rapport, mais traitée comme une **donnée identifiante** : masquée par défaut dans tous les exports et dans la sortie du terminal, révélée sur levée explicite du masquage, qui est signalée en tête du rapport (ES-13).

## Raisons

- Option A retenue : elle protège la source par défaut avec le mécanisme déjà prévu pour les autres données identifiantes.
- Option B écartée : la gestion d'une clé ajoute une difficulté réelle pour un gain que la levée explicite du masquage couvre déjà en pratique.
- Option C écartée : elle laisse le rapport désigner la source.

## Conséquences

- F-05 est satisfaite : l'empreinte est inscrite, masquée comme les autres données identifiantes ; l'interprétation est inscrite au registre des arbitrages.
- T16 range l'empreinte parmi les catégories masquables.
- La reproductibilité (ADR-0023) se vérifie avec la levée du masquage, par qui détient le fichier.
- L'empreinte du rapport lui-même (horodatage, ADR-0030) n'est pas concernée : elle ne révèle rien du fichier.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Renvoi : résumé du terminal sans nom ni empreinte avant le masquage de T16 (ADR-0073) |
| 2026-10-28 | Réalisé en T16 : empreinte masquée par défaut au terminal et dans les exports, levée par `--reveler empreinte`, annoncée en tête (ADR-0093, ADR-0095) |
