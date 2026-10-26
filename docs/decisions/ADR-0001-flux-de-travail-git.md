# ADR-0001 — Flux de travail git : branches, PR et protections

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac (règles de base) ; paramètres de protection proposés par l'assistant
- **Tâche** : T00
- **Exigences liées** : méthode de travail ; NF-07 (traçabilité)

## Contexte

Consigne de TheDarkMac : le travail se fait sur la branche `detector`, sans supprimer `main` ; chaque étape a sa propre branche, poussée puis mergée dans `detector` ; `detector` n'accepte aucun push direct, seulement des PR. TheDarkMac a choisi que l'assistant merge lui-même les PR une fois la CI verte.

Le dépôt distant `TheDarkMac/AI-detector` était vide (aucune branche) au démarrage.

## Options envisagées

### Merge des PR : qui merge

- **TheDarkMac après relecture** : contrôle humain systématique, mais chaque tâche attend une disponibilité.
- **L'assistant, si la CI passe** *(retenu par TheDarkMac)* : rythme continu ; la relecture humaine se fait a posteriori.

### Méthode de merge

- **Squash** : un commit par tâche sur `detector`, historique compact ; mais les commits intermédiaires de la branche (et leurs messages explicatifs) disparaissent de `detector`. GitHub peut aussi y ajouter des lignes `Co-authored-by`.
- **Rebase** : historique linéaire, mais réécrit les commits (nouveaux SHA) et efface la frontière entre tâches.
- **Commit de merge** *(retenu)* : conserve tous les commits de la branche et matérialise chaque tâche par un commit de merge identifiable.

### Protection de `detector`

- **Règle de branche classique** *(retenu)* ou **ruleset** : les deux sont disponibles sur un dépôt public. La règle classique suffit et se lit plus simplement via l'API.

### Sort des branches de tâche après merge

- **Suppression automatique** : dépôt plus propre.
- **Conservation** *(retenu)* : chaque étape reste consultable telle qu'elle a été poussée, conformément à l'exigence de tout documenter.

### Branche par défaut du dépôt

- **`detector`** : les visiteurs voient directement l'état du travail.
- **`main`** *(retenu pour l'instant)* : c'est la branche créée en premier et la consigne demande de ne pas la toucher ; la changer n'apporte rien tant que le projet n'a pas de livraison. Point à revoir lors d'une première version.

## Décision

- `main` : commit initial seul ; protégée contre la suppression et le force-push, y compris pour les administrateurs.
- `detector` : branche d'intégration, créée depuis `main`. Protection, administrateurs compris (`enforce_admins`) :
  - PR obligatoire, **0 approbation requise** (projet à une personne : GitHub n'autorise pas l'auteur à approuver sa propre PR) ;
  - vérifications obligatoires `lint-markdown` et `fichiers-interdits` (ADR-0006), branche à jour avec `detector` avant merge (`strict`) ;
  - conversations de revue résolues avant merge ;
  - force-push et suppression interdits.
- Une branche par tâche, nommée selon ADR-0005, créée depuis `detector` à jour.
- Merge par **commit de merge uniquement** (squash et rebase désactivés dans les réglages du dépôt), effectué par l'assistant via `gh` quand toutes les vérifications sont vertes.
- Les branches de tâche ne sont pas supprimées après merge.

## Raisons

- `enforce_admins` est indispensable : TheDarkMac est administrateur et l'assistant agit avec son jeton ; sans cette option, un push direct sur `detector` serait accepté malgré la règle.
- Le commit de merge est la seule méthode qui garde intacts les commits documentés de chaque étape.
- Le contrôle repose sur la CI parce qu'aucune relecture humaine n'est exigée avant merge : d'où l'importance de vérifications qui échouent réellement en cas d'écart (ADR-0006).

## Conséquences

- Aucune modification n'atteint `detector` sans PR ni CI verte, même par erreur.
- Avec `strict`, deux PR ouvertes en parallèle obligent à remettre la seconde à jour après le merge de la première.
- La relecture humaine étant a posteriori, une erreur peut atteindre `detector` ; elle sera corrigée par une nouvelle PR et un erratum, jamais par réécriture d'historique (force-push interdit).
- La vérification de la protection s'est faite par relecture de la configuration via l'API (voir journal T00) ; le premier refus effectif d'un push direct sera constaté à l'usage.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : dépôt trouvé privé et protections supprimées au démarrage de T10 ; dépôt repassé en public et protections rétablies à l'identique (ADR-0046) ; `code-ok` ajouté aux vérifications obligatoires (ADR-0051) (T10) |
| 2026-10-26 | Renvoi : branche par défaut passée de `main` à `detector` (ADR-0053, ERR-0005) ; le reste de l'ADR est inchangé |
