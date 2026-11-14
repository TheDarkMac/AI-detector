# ADR-0179 — Versions de T31 : schéma 0.6.0, catalogue 0.6.0 au format 3, modules inchangés

- **Statut** : Proposé
- **Date** : 2026-11-14
- **Décideur** : assistant, proposition non posée en question pendant T31, soumise dans la PR
- **Tâche** : T31
- **Exigences liées** : NF-06, NF-07 ; ADR-0054, ADR-0085, ADR-0147, ADR-0152, ADR-0172

## Contexte

T31 ajoute un champ obligatoire à la couverture du rapport et un fichier au catalogue, qui passe à un nouveau format. Aucun module ne change.

## Options envisagées

### Option A — Schéma 0.6.0, catalogue 0.6.0 au format 3, modules à leur version

- Avantages : suit ADR-0054 (champ obligatoire ajouté) et le guide du catalogue (§5 : `Y` pour un nouveau format avant 1.0.0, ADR-0152) ; les observations des modules ne changent pas.
- Inconvénients : aucun.

### Option B — Catalogue 0.5.1

- Inconvénients : un nouveau format et des marquages qui changent le rapport ne sont pas un changement de texte seul (§5 : `Z`).

## Décision

Option A. Registre du catalogue : entrée 0.6.0 ajoutée.

## Raisons

- A retenue ; B écartée parce que le rapport change.

## Conséquences

- `vk --comparer` refuse un rapport de schéma 0.5.0.
- Une version de l'outil antérieure à T31 refuse le catalogue 0.6.0.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
