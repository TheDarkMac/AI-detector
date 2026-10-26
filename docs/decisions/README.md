# Registre des décisions (ADR)

Un ADR (*Architecture Decision Record*) consigne une décision, son contexte, **les options écartées et pourquoi**, et ses conséquences.

## Règles

- Un fichier par décision : `ADR-NNNN-titre-court.md`, numéro croissant, jamais réutilisé.
- Copier [`gabarit.md`](gabarit.md).
- Un ADR accepté n'est plus modifié sur le fond. Pour changer d'avis, on écrit un nouvel ADR qui le **remplace**, et on passe l'ancien au statut « Remplacé par ADR-NNNN ». Les corrections de forme (coquille, lien) sont admises et notées en bas du fichier.
- Statuts possibles : `Proposé`, `Accepté`, `Remplacé par ADR-NNNN`, `Abandonné`.
- Une décision rejetée mérite aussi un ADR (statut `Abandonné`) si l'option a été sérieusement envisagée.
- « Décideur » indique qui a tranché : TheDarkMac, ou une proposition de l'assistant validée par TheDarkMac.

## Index

| N° | Titre | Statut | Date |
| --- | --- | --- | --- |
| [ADR-0001](ADR-0001-flux-de-travail-git.md) | Flux de travail git : branches, PR et protections | Accepté | 2026-10-26 |
| [ADR-0002](ADR-0002-exclusion-fichiers-assistant.md) | Exclusion locale de `CLAUDE.md` et `.claude/` | Accepté | 2026-10-26 |
| [ADR-0003](ADR-0003-identite-des-commits.md) | Identité des commits et absence de co-auteur | Accepté | 2026-10-26 |
| [ADR-0004](ADR-0004-conventions-de-documentation.md) | Conventions de documentation | Accepté | 2026-10-26 |
| [ADR-0005](ADR-0005-nommage-branches-et-commits.md) | Nommage des branches et messages de commit | Accepté | 2026-10-26 |
| [ADR-0006](ADR-0006-ci-documentaire.md) | Intégration continue documentaire | Accepté | 2026-10-26 |
| [ADR-0007](ADR-0007-adresse-des-commits-de-merge.md) | Adresse e-mail des commits de merge créés par GitHub | Accepté | 2026-10-26 |
