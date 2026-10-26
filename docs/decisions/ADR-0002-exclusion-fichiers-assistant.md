# ADR-0002 — Exclusion locale de `CLAUDE.md` et `.claude/`

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac ; garde-fou CI proposé par l'assistant
- **Tâche** : T00
- **Exigences liées** : méthode de travail

## Contexte

Le projet est développé avec un assistant (Claude Code) qui peut créer des fichiers `CLAUDE.md`, `CLAUDE.local.md` et un dossier `.claude/`. Consigne de TheDarkMac : ces fichiers ne sont **jamais** commités. Raison donnée : toutes les décisions sont documentées dans `docs/`, ils ne sont donc pas nécessaires au dépôt.

Première version de la règle (découpage v0.2) : exclusion par `.gitignore`. TheDarkMac a ensuite demandé d'utiliser `.git/info/exclude` à la place (découpage v0.3).

## Options envisagées

### Option A — `.gitignore` versionné

- Avantages : partagé automatiquement avec tout clone.
- Inconvénients : écarté par TheDarkMac.

### Option B — `core.excludesFile` global

- Avantages : s'applique à tous les dépôts du poste.
- Inconvénients : modifie la configuration de toute la machine, au-delà de ce projet ; le comportement d'autres dépôts changerait sans qu'ils le documentent.

### Option C — `.git/info/exclude` *(retenu)*

- Avantages : propre à ce dépôt local, sans effet sur les autres projets ni sur l'historique.
- Inconvénients : non versionné, donc absent de tout nouveau clone ; chaque poste doit le configurer.

### Garde-fou complémentaire

- **Aucun** : la règle repose entièrement sur la configuration locale de chaque poste.
- **Vérification en CI** *(retenu)* : un job `fichiers-interdits` échoue si l'un de ces chemins est suivi par git. Comme ce job est obligatoire pour merger dans `detector` (ADR-0001), un oubli local ne peut pas atteindre `detector`.

## Décision

Les chemins `CLAUDE.md`, `CLAUDE.local.md` (à tout niveau) et `.claude/` sont exclus via `.git/info/exclude`. La procédure de configuration figure dans `CONTRIBUTING.md`. Le job CI `fichiers-interdits` refuse toute PR qui les contiendrait.

## Raisons

- Option C : choix explicite de TheDarkMac, et la seule des trois qui reste strictement limitée à ce dépôt sur ce poste.
- Option A écartée sur décision de TheDarkMac (aucune raison supplémentaire n'a été donnée ; voir ERR-0002 sur une raison qui avait été supposée à tort).
- Option B écartée : portée trop large.
- Le garde-fou CI compense la seule faiblesse de l'option C (non versionnée) sans versionner l'exclusion elle-même.

## Conséquences

- Un nouveau poste ou un nouveau clone doit appliquer la procédure de `CONTRIBUTING.md` avant tout commit.
- Le nom de ces fichiers apparaît dans la documentation et dans le workflow CI : c'est nécessaire pour documenter et faire respecter la règle.
- Vérification faite à l'initialisation : avec l'exclusion en place, `git status --ignored` classe `CLAUDE.md` et `.claude/` comme ignorés (journal T00).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
