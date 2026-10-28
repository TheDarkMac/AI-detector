# Errata

Toute erreur constatée — d'analyse, de documentation, de décision ou d'exécution — fait l'objet d'un erratum, même si elle est corrigée immédiatement.

## Règles

- Fichier `ERR-NNNN-titre-court.md`, à partir de [`gabarit.md`](gabarit.md), numéro croissant.
- Le document fautif est corrigé, et sa table d'historique (s'il en a une) renvoie à l'erratum.
- L'erratum dit : ce qui était écrit ou fait, ce qui est juste, comment l'erreur a été trouvée, sa cause, et ce qui empêche qu'elle se reproduise.
- Une simple coquille sans incidence sur le sens peut être corrigée sans erratum ; dans le doute, on écrit l'erratum.

## Index

| N° | Titre | Document touché | Tâche | Date |
| --- | --- | --- | --- | --- |
| [ERR-0001](ERR-0001-exigence-f-94-inexistante.md) | Exigence « F-94 » inexistante citée dans le découpage | `00-plan/decoupage-taches.md` | T00 | 2026-10-26 |
| [ERR-0002](ERR-0002-justification-attribuee-sans-source.md) | Justification attribuée à une décision sans qu'elle ait été donnée | `00-plan/decoupage-taches.md` | T00 | 2026-10-26 |
| [ERR-0003](ERR-0003-adresse-du-commit-de-merge.md) | Adresse e-mail du commit de merge non anticipée | `decisions/ADR-0003-identite-des-commits.md` | T01 | 2026-10-26 |
| [ERR-0004](ERR-0004-points-de-tracage-rattaches-a-l-ocr.md) | Points de traçage d'imprimante rattachés à tort à la frontière « OCR » | `00-plan/decoupage-taches.md` | T01 | 2026-10-26 |
| [ERR-0005](ERR-0005-branche-par-defaut-ignoree.md) | Branche par défaut ignorée : Dependabot et l'audit hebdomadaire inactifs | `decisions/ADR-0051-…`, `decisions/ADR-0052-…` | après T10 | 2026-10-26 |
| [ERR-0006](ERR-0006-annulation-des-lancements-de-ci.md) | La CI du code annulait ses propres lancements sur `detector` | `.github/workflows/code.yml` | après T10 | 2026-10-26 |
| [ERR-0007](ERR-0007-merge-de-la-pr-18.md) | PR #18 mergée sans titre fixé ni validation des ADR proposés | commit `4526ccd`, `decisions/ADR-0112-…`, `decisions/ADR-0113-…` | T20 | 2026-10-28 |
