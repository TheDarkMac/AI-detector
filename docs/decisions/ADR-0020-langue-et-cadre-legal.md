# ADR-0020 — Français en V1, cadre légal de l'Union européenne

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : NF-11, NF-13, NF-18 ; constat A-51

## Contexte

Le §10 laisse ouverts les langues de l'interface et des rapports, et les pays visés. NF-13 (« réglementation des pays où il est proposé ») est sans limite si l'outil libre est diffusé partout (A-51).

## Options envisagées

### Option A — Français, Union européenne

- Avantages : langue du cahier, de la documentation et de TheDarkMac ; une seule langue à rédiger et relire ; le RGPD est le cadre de référence le plus exigeant parmi ceux qui s'appliqueraient.
- Inconvénients : public de vérificateurs international non servi en V1.

### Option B — Français et anglais, Union européenne

- Avantages : public plus large dès la V1.
- Inconvénients : chaque phrase de constat et chaque mention sont à rédiger et relire en deux langues, alors que leur formulation est une exigence (NF-14).

### Option C — Anglais seul, Union européenne

- Avantages : une langue, la plus répandue.
- Inconvénients : contraire à la langue du cahier et de la documentation (ADR-0004).

## Décision

- Interface et rapports **en français** en V1. Les textes destinés à l'utilisateur (phrases des constats, mentions, messages) sont séparés du code pour pouvoir être traduits ; l'anglais est envisagé ensuite.
- Cadre légal visé : **Union européenne, RGPD**. NF-13 est reformulée en ce sens pour le projet. Aucun autre pays n'est visé, sans que la diffusion y soit empêchée.

## Raisons

- Option A retenue : qualité de rédaction d'abord, sur une langue ; la séparation des textes garde la traduction possible.
- Option B écartée : double coût de rédaction sur les textes les plus sensibles.
- Option C écartée : ADR-0004.

## Conséquences

- T11 et T15 : les phrases de constat sont des gabarits identifiés, stockés hors du code, par langue.
- T03 : examiner les données personnelles présentes dans les rapports (noms, GPS, numéros de série) et leur protection (NF-18). En traitement local (ADR-0010), le projet ne traite pas lui-même les fichiers des utilisateurs ; la qualification juridique exacte (responsable de traitement ou non) n'est pas établie ici et n'est pas un avis juridique.
- La responsabilité en cas de faux positif aux conséquences lourdes n'est pas tranchée par cet ADR ; les mentions sont rédigées en T103 (registre des arbitrages).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : la phrase d'un constat est un gabarit dont les paramètres renvoient à des observations (ADR-0058) ; raisons des analyses non menées par gabarit (ADR-0056) (T11) |
| 2026-10-28 | Réalisé en T16 : phrases des constats dans les règles du catalogue (ADR-0091), autres textes du rapport dans `rapport/textes.toml` (ADR-0098) |
