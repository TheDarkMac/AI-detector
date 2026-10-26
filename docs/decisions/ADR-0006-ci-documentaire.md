# ADR-0006 — Intégration continue documentaire

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : proposition de l'assistant, soumise à TheDarkMac dans la PR de T00 (relecture a posteriori, ADR-0001)
- **Tâche** : T00
- **Exigences liées** : méthode de travail

## Contexte

TheDarkMac a choisi que l'assistant merge les PR « si la CI passe » (ADR-0001). Or les premières tâches (T00 à T04) ne contiennent pas de code : sans vérification automatique, la condition serait vide et la protection de `detector` ne contrôlerait rien. Il faut donc une CI dès T00. La CI du code Python viendra avec T10.

## Options envisagées

### Plateforme

- **GitHub Actions** *(retenu)* : intégrée au dépôt, gratuite pour un dépôt public, ses résultats alimentent directement la protection de branche.
- **Service externe** : configuration et jeton supplémentaires, sans bénéfice ici.

### Contrôle de forme du Markdown

- **Aucun** : rien ne garantit la cohérence des documents.
- **remark-lint** : très configurable, mais nécessite d'assembler soi-même un jeu de règles.
- **Vale** (relecture de style) : utile pour la prose, mais lourd à configurer et peu adapté au français sans travail spécifique ; à reconsidérer plus tard.
- **markdownlint-cli2** *(retenu)* : jeu de règles standard prêt à l'emploi, action GitHub officielle maintenue.

### Garde-fou des fichiers de l'assistant

- Voir ADR-0002 : job `fichiers-interdits`.

### Épinglage des actions

- **Étiquette majeure** (`@v24`) : mises à jour automatiques, mais une étiquette peut être déplacée vers un code différent.
- **SHA de commit complet** *(retenu)*, version en commentaire : le code exécuté ne peut pas changer à l'insu du projet. Cohérent avec un outil dont la sécurité est une exigence de premier rang (NF-01).
- Version choisie : la plus récente publiée depuis au moins deux semaines (`actions/checkout` v7.0.1, `DavidAnson/markdownlint-cli2-action` v24.2.0) ; la v25.0.0 de cette dernière, publiée la veille, a été écartée faute de recul.

## Décision

Workflow `.github/workflows/docs.yml`, déclenché sur PR et push vers `detector`, avec deux jobs obligatoires :

- `lint-markdown` : markdownlint-cli2 sur tout le Markdown du dépôt, configuration `.markdownlint-cli2.jsonc`. Le cahier des charges source est exclu (document reçu, jamais modifié). Règles désactivées : MD013 (longueur de ligne, inadaptée à la prose et aux tableaux).
- `fichiers-interdits` : échoue si `git ls-files` liste un `CLAUDE.md`, un `CLAUDE.local.md` ou un chemin sous `.claude/`.

Permissions du workflow réduites à la lecture du contenu.

## Raisons

- Deux contrôles simples et déterministes, qui échouent réellement en cas d'écart : condition pour que « merger si la CI passe » ait un sens.
- Exclure le cahier des charges évite d'avoir à le modifier pour satisfaire un outil.

## Conséquences

- Toute PR avec un Markdown mal formé ou un fichier interdit est bloquée.
- Les versions épinglées doivent être mises à jour manuellement (nouvel ADR ou note d'historique si la politique change).
- Le lint ne contrôle ni le fond ni les liens ; une vérification des liens internes pourra être ajoutée si des liens cassés apparaissent.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
