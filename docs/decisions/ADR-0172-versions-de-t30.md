# ADR-0172 — Versions de T30 : schéma 0.5.0, catalogue 0.5.0, module c2pa 0.1.0

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T30, validée pendant la revue de la PR de T30
- **Tâche** : T30
- **Exigences liées** : NF-06, NF-07 ; ADR-0054, ADR-0085, ADR-0152, ADR-0163

## Contexte

T30 ajoute un champ obligatoire au rapport et à la configuration, un module et douze règles.

## Options envisagées

### Option A — Schéma 0.5.0, catalogue 0.5.0, module 0.1.0, autres modules inchangés

- Avantages : suit les règles d'ADR-0054, d'ADR-0085 et du guide du catalogue (§5 : `Y` pour une règle ajoutée avant 1.0.0).
- Inconvénients : aucun.

### Option B — Schéma 0.4.1

- Inconvénients : un rapport nouveau n'est pas valide sous 0.4.0.

## Décision

Option A. Les modules existants gardent leur version : leurs observations ne changent pas.

## Raisons

- A retenue ; B écartée parce que ce qui est valide change.

## Conséquences

- `vk --comparer` refuse un rapport de schéma 0.4.0.
- Registre du catalogue : entrée 0.5.0 ajoutée.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T30 (« Oui, les cinq ») : statut « Accepté » |
