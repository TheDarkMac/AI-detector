# ADR-0162 — Liste de garde par nom d'observation dans P1 : non ajoutée

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T25
- **Exigences liées** : ES-13, F-90 ; risque résiduel RR-01 ; ADR-0057, ADR-0119

## Contexte

ADR-0057 permettait à P1 (le processus principal) de tenir une liste de garde par nom d'observation, pour masquer d'office un champ identifiant qu'un module oublierait de marquer. ADR-0119 a laissé la décision « avant T25, qui en dépend le plus ».

## Options envisagées

### Option A — Non ajoutée

- Avantages : une seule liste par format, dans le module qui le lit (ADR-0057) ; un oubli se voit au test par catégorie de chaque module.
- Inconvénients : un oubli qui échappe aux tests part en clair jusqu'à la version suivante du module.

### Option B — Ajoutée

P1 masque d'office les observations dont le nom figure dans sa liste, marquées ou non.

- Avantages : filet contre l'oubli d'un module honnête.
- Inconvénients : une liste centrale qui suit chaque format, l'option écartée par ADR-0057 ; elle ne protège pas d'un processus de travail compromis, qui choisit aussi le nom de l'observation (RR-01).

## Décision

Option A : pas de liste de garde dans P1.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : contre RR-01 elle n'apporte rien, puisqu'un processus de travail compromis peut écrire une valeur identifiante sous n'importe quel nom ; contre l'oubli, le test par catégorie de chaque module fait le même travail, au plus près du code.

## Conséquences

- ADR-0057 et ADR-0119 ne laissent plus de décision ouverte sur ce point.
- Un champ identifiant non marqué se corrige par une nouvelle version du module, avec son test.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
