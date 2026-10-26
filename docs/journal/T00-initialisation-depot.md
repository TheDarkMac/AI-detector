# T00 — Initialisation du dépôt

- **Branche** : `tache/T00-init-depot`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : méthode de travail (consignes de TheDarkMac)
- **Décisions** : ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006
- **Errata** : ERR-0001, ERR-0002

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : créer `main` et `detector`, protéger `detector`, fixer les conventions (branches, commits, PR), exclure localement `CLAUDE.md` et `.claude/`, structurer la documentation et ses gabarits.

## État initial

- Dossier local `AI-detection` : pas de dépôt git ; il contenait le cahier des charges et le brouillon du découpage (v0.3).
- Dépôt distant `TheDarkMac/AI-detector` : public, vide, aucune branche ; le compte TheDarkMac en est administrateur.
- Configuration git globale du poste : `andomamy <hei.ando14@gmail.com>`.

## Avant le démarrage : cadrage avec TheDarkMac

1. Analyse du cahier des charges et rédaction du découpage v0.1.
2. Questions posées et réponses de TheDarkMac :
   - e-mail des commits : `hei.ando14@gmail.com` (plutôt que l'adresse noreply proposée) → ADR-0003 ;
   - merge des PR : par l'assistant, si la CI passe → ADR-0001 ;
   - langage : Python ; distribution V1 : CLI + bibliothèque → seront formalisés en ADR dans T02/T04, tâches où ces choix sont prévus.
3. v0.2 : ajout de la règle « `CLAUDE.md` et `.claude/` ne sont jamais commités » (règle omise de la consigne initiale).
4. v0.3 : l'exclusion passe de `.gitignore` à `.git/info/exclude`.
5. TheDarkMac valide le découpage et lance T00.

## Déroulé

1. `git init -b main` ; identité **locale** `TheDarkMac <hei.ando14@gmail.com>` ; ajout de `origin`.
2. Ajout des motifs `CLAUDE.md`, `CLAUDE.local.md`, `**/CLAUDE.md`, `**/CLAUDE.local.md`, `.claude/` dans `.git/info/exclude`. Test : création temporaire de `CLAUDE.md` et `.claude/test` → `git status --ignored` les classe en ignorés ; fichiers de test supprimés.
3. Commit initial sur `main` (README minimal), création de `detector` au même commit, push des deux branches.
4. Protections via l'API GitHub (détail dans ADR-0001) :
   - `detector` : PR obligatoire (0 approbation), vérifications `lint-markdown` et `fichiers-interdits` requises en mode strict, conversations résolues, `enforce_admins`, force-push et suppression interdits ;
   - `main` : force-push et suppression interdits, `enforce_admins` ;
   - dépôt : seul le commit de merge est autorisé ; suppression automatique des branches désactivée.
   La configuration a été relue via l'API après application.
5. Branche `tache/T00-init-depot` créée depuis `detector`.
6. Cahier des charges déplacé et renommé en `docs/00-cahier-des-charges/cahier-des-charges-v0.1.md`, contenu inchangé (SHA-256 `702b468f…dafc`, valeur complète dans le message du commit).
7. Structure `docs/` : index, registres `decisions/`, `journal/`, `errata/` avec leurs règles et gabarits.
8. ADR-0001 à ADR-0006.
9. `CONTRIBUTING.md` et modèle de PR.
10. CI documentaire `.github/workflows/docs.yml` et `.markdownlint-cli2.jsonc`. Lint lancé en local avec la version de l'outil embarquée par l'action CI ; motif de `fichiers-interdits` testé sur des chemins d'exemple (refusés : `docs/CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`, `a/.claude/x` ; acceptés : `CLAUDE.md.bak`, `NOTCLAUDE.mdx`, `MYCLAUDE.md`).
11. Relecture du découpage : vérification de chaque identifiant d'exigence cité contre le cahier → ERR-0001 ; relecture des justifications → ERR-0002. Découpage passé en v0.4 (validé).
12. Rédaction de ce journal, push de la branche, ouverture de la PR vers `detector`.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Premier lint : MD024 (titres en double « Branches ») dans ADR-0005 | Mêmes intitulés dans « Options envisagées » et « Décision » | Titres renommés avant commit |
| La correction par `sed` a renommé aussi le titre de la section « Options » | Motif appliqué à toutes les lignes au lieu de la seule section « Décision » | Constaté en relisant les titres, rétabli ligne par ligne avant commit |
| Le lint local a d'abord été lancé avec markdownlint-cli2 0.18.1 | Version choisie sans vérifier celle de l'action CI | Version embarquée par l'action v24.2.0 identifiée (0.23.2), lint relancé avec elle ; commande documentée dans `CONTRIBUTING.md` |
| Vérification de l'adresse e-mail : la commande de contrôle a masqué une partie de sa sortie | Filtre d'affichage appliqué à toute la sortie | Adresse confirmée comme principale et vérifiée sur le compte TheDarkMac |

Les deux premiers problèmes sont des défauts de forme, corrigés avant tout commit : pas d'erratum (règle de `docs/errata/README.md`).

## Écarts par rapport au découpage

- **Ajout** : CI documentaire dès T00 (ADR-0006). Sans elle, la condition « merger si la CI passe » n'aurait rien vérifié avant T10.
- **Ajout** : job `fichiers-interdits`, garde-fou côté serveur de la règle d'exclusion, qui est uniquement locale (ADR-0002).
- **Ajout** : protection de `main` contre la suppression et le force-push, pour garantir la consigne « ne pas supprimer `main` ».
- **Ajout** : le cahier des charges est versionné dans `docs/`.

## Résultat

- `main` et `detector` existent sur le dépôt distant et sont protégées.
- La documentation et les conventions sont en place sur la branche de la tâche.
- Vérification : `npx --yes markdownlint-cli2@0.23.2` ne signale aucune erreur ; aucun fichier interdit n'est suivi.

## Reste à faire

- Constater le passage de la CI et le merge de la PR : section « État initial » du journal T01.
- Le premier refus effectif d'un push direct sur `detector` n'a pas été provoqué volontairement (un push accepté par erreur aurait pollué `detector` sans possibilité de réécriture) ; la protection est vérifiée par sa configuration.
- Branche par défaut du dépôt à reconsidérer à la première version (ADR-0001).
- Formaliser en ADR les choix Python et CLI + bibliothèque (T02/T04).
