# ADR-0019 — Règles, seuils et limites entièrement publics

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : NF-07, NF-19 ; objectif 4, principe d'explicabilité, §8 (équipe rouge) ; constat A-06

## Contexte

NF-19 restreint l'accès au détail des règles et des seuils pour ne pas fournir de mode d'emploi aux faussaires. Elle s'oppose à l'objectif 4 (rapport vérifiable par un expert), à l'explicabilité, à NF-07 (catalogue consultable) et à la licence ouverte retenue (ADR-0011) : dans un logiciel ouvert, les seuils sont dans le code (A-06). Le choix conditionne le format du catalogue (T15).

## Options envisagées

### Option A — Tout publier

- Avantages : cohérent avec l'explicabilité, l'objectif 4 et la licence ; la robustesse ne dépend pas d'un secret (principe de Kerckhoffs).
- Inconvénients : un faussaire sait ce qui est contrôlé.

### Option B — Tout publier, contournements diffusés en différé

- Avantages : laisse le temps de corriger une faille trouvée par l'équipe rouge.
- Inconvénients : pendant le délai, les utilisateurs se fient à un contrôle qu'on sait contourné, sans que le rapport le dise ; un projet de cette taille ne peut pas garantir un délai de correction.

### Option C — Certains seuils non publiés

- Avantages : complique un peu le contournement.
- Inconvénients : incompatible en pratique avec un code ouvert ; un expert ne peut plus tout vérifier.

## Décision

Les règles, les seuils, leur procédure de calibrage, leurs taux d'erreur et leurs **limites connues**, y compris les contournements trouvés par l'équipe rouge, sont **publics**. NF-19 est reformulée pour le projet : « Le détail des règles et des seuils est public ; la robustesse repose sur la combinaison des techniques et sur la publication de leurs limites. »

## Raisons

- Option A retenue : seule option compatible avec l'objectif 4, NF-07 et la licence Apache-2.0.
- Option B écartée : le §8 exige de documenter les limites connues, et cacher un contournement connu fait reposer la confiance de l'utilisateur sur une information fausse.
- Option C écartée : A-06.

## Conséquences

- T15 : le catalogue est un ensemble de fichiers publics, versionnés et datés, sans partie réservée.
- T95 (politique d'accès) devient sans objet comme fonction ; elle se réduit à la publication du catalogue et des fiches.
- T102 : chaque contournement trouvé est publié dans les limites connues de la technique concernée.
- La reformulation de NF-19 est inscrite au registre des arbitrages, à faire valider par l'auteur du cahier.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Réalisé en T15 : chaque règle porte au moins une limite connue ; catalogue public, consultable par `vk --regles` (ADR-0084, ADR-0086) |
