# ERR-0002 — Justification attribuée à une décision sans qu'elle ait été donnée

- **Date de constat** : 2026-10-26
- **Tâche en cours** : T00
- **Document ou élément touché** : `docs/00-plan/decoupage-taches.md`, §1 (version 0.3)
- **Nature** : documentation

## Ce qui était écrit ou fait

> Pourquoi `.git/info/exclude` et non `.gitignore` : l'exclusion reste locale et n'apparaît pas dans l'historique du dépôt ; le dépôt ne porte aucune trace de l'outil d'assistance.

## Ce qui est juste

TheDarkMac a demandé `.git/info/exclude` à la place de `.gitignore` **sans en donner la raison**. La phrase présentait comme motif de la décision une interprétation de l'assistant. De plus, elle était factuellement fausse : le dépôt mentionne ces fichiers dans sa documentation et dans le workflow CI, ce qui est nécessaire pour documenter et faire respecter la règle.

Formulation corrigée : le choix est celui de TheDarkMac ; l'effet constaté est que l'exclusion reste propre au dépôt local et n'est pas versionnée. Les options et leurs raisons sont dans ADR-0002.

## Comment l'erreur a été trouvée

Rédaction d'ADR-0002 : en listant qui avait décidé quoi, l'assistant a constaté qu'aucune raison n'avait été exprimée pour ce choix.

## Cause

Volonté de justifier chaque choix, au point d'en inventer la justification au lieu de signaler qu'elle manquait.

## Correction appliquée

§1 du découpage réécrit (version 0.4) ; ADR-0002 distingue ce qui a été décidé par TheDarkMac de ce qui a été proposé par l'assistant.

## Prévention

Dans les ADR, le champ « Décideur » sépare la décision de TheDarkMac et les propositions de l'assistant. Une raison qui n'a pas été donnée est écrite comme telle (« aucune raison supplémentaire n'a été donnée ») plutôt que supposée.
