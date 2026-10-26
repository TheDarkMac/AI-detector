# ADR-0003 — Identité des commits et absence de co-auteur

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac
- **Tâche** : T00
- **Exigences liées** : méthode de travail

## Contexte

Consigne de TheDarkMac : tout commit est au nom de TheDarkMac et ne comporte aucune mention de co-auteur. La configuration git globale du poste est à un autre nom (`andomamy`), qu'il ne faut pas modifier pour les autres projets.

## Options envisagées

### Adresse e-mail des commits

- **Adresse noreply GitHub** (`…+TheDarkMac@users.noreply.github.com`) : rattachée au compte avec certitude et ne publie aucune adresse personnelle.
- **`hei.ando14@gmail.com`** *(retenu par TheDarkMac)* : adresse principale vérifiée du compte TheDarkMac, donc commits correctement attribués sur GitHub.

### Portée de la configuration

- **Globale** : écraserait l'identité utilisée par les autres projets du poste.
- **Locale au dépôt** *(retenu)* : `git config user.name` / `user.email` sans `--global`.

## Décision

- Identité locale au dépôt : `TheDarkMac <hei.ando14@gmail.com>`.
- Aucun trailer `Co-Authored-By`, aucune mention de l'assistant dans les messages de commit, de PR ou de merge.
- Les commits de merge créés par GitHub (ADR-0001) sont faits au nom du compte authentifié, TheDarkMac.

## Raisons

- Choix explicite de TheDarkMac pour l'adresse ; la vérification du compte a confirmé qu'elle est l'adresse principale et vérifiée, condition pour que GitHub attribue les commits.
- La configuration locale isole ce projet des autres.

## Conséquences

- Le dépôt étant **public**, l'adresse `hei.ando14@gmail.com` est lisible par quiconque consulte l'historique. Ce choix est irréversible pour les commits déjà poussés (le force-push est interdit). Le changer plus tard ne vaudrait que pour les commits suivants.
- Avant chaque commit, l'identité locale est vérifiée (`git config user.name`, `git config user.email`).
- La méthode « squash », qui peut ajouter des `Co-authored-by` automatiques, est désactivée (ADR-0001).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Précision (sans changement de décision) : les commits de merge créés par GitHub portent l'adresse noreply du compte, et non `hei.ando14@gmail.com` (ERR-0003) |
