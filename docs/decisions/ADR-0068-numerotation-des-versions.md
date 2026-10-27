# ADR-0068 — Numérotation des versions publiées

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant, pendant la revue de la PR
- **Tâche** : T10 (complément)
- **Exigences liées** : NF-06 ; ES-18 ; ADR-0023, ADR-0041, ADR-0045, ADR-0050, ADR-0054

## Contexte

ADR-0050 écrit la version dans `pyproject.toml` (départ : `0.1.0.dev0`) et demande que les règles de numérotation des versions publiées soient fixées avant la première publication. Le nom `voight-kampff-forensics` n'est réservé sur PyPI que par une première publication (ADR-0045). La version de l'outil figure au rapport, à côté de celles du catalogue et des dépendances (ADR-0023) ; les schémas ont leur propre version, à fixer à leur première publication (ADR-0054, ADR-0062). Une version publiée sur PyPI est définitive : un fichier ne peut jamais être remplacé sous le même numéro ; on peut seulement la retirer de l'affichage (« yank »).

Deux questions : la forme des numéros, et ce qui peut être publié avant une version stable. Toutes les options respectent PEP 440, imposé par PyPI ; le workflow refuse une version qui n'est pas sous forme publique PEP 440 (ADR-0069).

## Options envisagées

### Forme des numéros

#### Option A — Versionnage sémantique, écrit en PEP 440 *(retenue)*

`X.Y.Z` : `X` augmente pour un changement incompatible de l'interface publique, `Y` pour un ajout compatible, `Z` pour une correction. Pré-versions `X.Y.ZaN`, `bN`, `rcN`. L'interface publique est définie pour l'outil : options et codes de sortie de la ligne de commande, format JSON du rapport, interface Python d'analyse (T13), interface des modules (ADR-0061). Tant que `X` vaut 0 : `Y` augmente pour un changement incompatible, `Z` pour le reste.

- Avantages : convention la plus répandue ; un intégrateur (rédaction, outil qui lit le rapport JSON) sait d'après le numéro s'il doit adapter son code ; s'accorde avec les pré-versions de PEP 440.
- Inconvénients : il faut juger à chaque version ce qui est incompatible ; un changement de règle du catalogue qui modifie les constats n'est pas un changement d'interface, et ne se voit pas dans le numéro de l'outil (il se voit dans la version du catalogue, ADR-0029).

#### Option B — Versionnage calendaire `AAAA.M.N`

- Avantages : l'âge d'une version se lit dans le numéro, utile pour un outil dont les règles vieillissent.
- Inconvénients : ne dit rien de la compatibilité ; la date figure déjà au rapport par la version datée du catalogue (ADR-0029).

#### Option C — Numéro unique incrémenté (`1`, `2`, `3`…)

- Avantages : le plus simple.
- Inconvénients : ne dit ni la compatibilité ni l'âge ; peu courant pour une bibliothèque Python, l'outil en étant aussi une (T13).

### Publication avant une version stable

#### Option D — Versions de développement `.devN` publiables *(retenue)*

La première publication peut être `0.1.0.dev0`, la version actuelle, sans PR de changement de version ; les suivantes, `0.1.0.dev1`, etc., jusqu'à la première pré-version ou version.

- Avantages : réserve le nom dès maintenant, contre le typosquattage (ADR-0045) ; pip et uv ne retiennent pas une version de développement quand une version stable existe ; la release GitHub est marquée comme pré-version (ADR-0069).
- Inconvénients : la page PyPI montre un paquet sans analyse ; tant qu'aucune version stable n'existe, un installeur peut retenir la version de développement.

#### Option E — Pré-versions `aN`, `bN`, `rcN` seulement ; pas de `.devN` sur PyPI

- Avantages : chaque version publiée est une étape annoncée.
- Inconvénients : il faut une PR de changement de version (`0.1.0a1`) avant la première publication ; une alpha suggère une fonction utilisable, alors que l'outil n'analyse encore rien.

#### Option F — Rien avant `0.1.0`

- Avantages : aucune version incomplète sur PyPI.
- Inconvénients : le nom reste libre jusqu'à une première version utilisable, après plusieurs tâches.

## Décision

**Versionnage sémantique écrit en PEP 440** (option A), avec la règle propre à `0.y.z` : `Y` augmente pour un changement incompatible de l'interface publique, `Z` pour le reste. **Versions de développement `.devN` publiables** avant la première version stable (option D) ; la première publication peut être `0.1.0.dev0`.

## Raisons

- Option A retenue par TheDarkMac, comme recommandé : le rapport JSON et l'interface Python sont faits pour être lus par d'autres outils ; le numéro doit leur dire quand s'adapter. Option B : la date est déjà au rapport par le catalogue. Option C : n'informe sur rien.
- Option D retenue par TheDarkMac, comme recommandé : elle réserve le nom sans attendre, avec la version déjà écrite. Option E : une PR de plus et un signal trompeur. Option F : laisse le nom exposé.

## Conséquences

- `CONTRIBUTING.md` §8 reçoit la procédure de version (PR qui modifie `version`, puis étiquette sur le commit de merge de `detector`, ADR-0050, ADR-0069) et la règle d'incrément.
- La version de l'outil reste indépendante de celles du catalogue (ADR-0029) et des schémas (ADR-0054) : le rapport les inscrit toutes.
- La première publication peut suivre le merge de cette PR : étiquette `v0.1.0.dev0` sur le commit de merge, puis approbation dans l'environnement `pypi`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » ; choix attendu de TheDarkMac |
| 2026-10-27 | Options A et D retenues par TheDarkMac pendant la revue de la PR : statut « Accepté » |
