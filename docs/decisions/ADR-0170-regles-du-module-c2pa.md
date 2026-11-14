# ADR-0170 — Règles du module c2pa : une phrase d'état par manifeste, preuve ou indice pour une source déclarée

- **Statut** : Proposé
- **Date** : 2026-11-14
- **Décideur** : l'assistant, choix non posé en question pendant T30, à valider pendant la revue de la PR de T30
- **Tâche** : T30
- **Exigences liées** : F-21 à F-23, F-80, F-81 ; ES-20 ; ADR-0021, ADR-0084, ADR-0090, ADR-0143

## Contexte

La vérification est déterministe : ses constats sont des règles « module », appliquées par le code, dont le catalogue fixe phrase, catégorie, direction, fondement et niveau (ADR-0084, ADR-0090). C'est le premier module qui en cite.

## Options envisagées

### Option A — Douze règles : six d'état en information neutre, trois preuves, trois indices

- Avantages : chaque phrase dit exactement ce que la vérification établit ; les preuves ont une direction.
- Inconvénients : une phrase de plus dans chaque rapport, absence comprise.

### Option B — État « valide reconnu » en preuve sans direction

- Avantages : la signature reconnue est un fait établi.
- Inconvénients : une preuve « rien de particulier » au résumé se lit mal.

### Option C — Pas de phrase pour l'absence

- Avantages : moins de bruit.
- Inconvénients : F-22 demande d'afficher l'état « absent ».

## Décision

Option A : R-C2PA-007 à R-C2PA-012 pour les états (valide, hors liste, invalide, non vérifiable, distant, absent) ; R-C2PA-001 à R-C2PA-003, preuves sous un signataire reconnu (génération, retouche par IA, capture) ; R-C2PA-004 et R-C2PA-005, indices faibles fondés sur la déclaration hors liste ou sous une signature invalide ; R-C2PA-006, écart d'empreinte (ADR-0167). Seul le manifeste actif fonde les règles. Codes IPTC lus comme ceux du XMP (ADR-0143).

## Raisons

- A retenue : ADR-0021 et F-22 à la lettre.
- B écartée : la preuve d'une signature sans direction n'apprend rien au lecteur que la phrase d'état ne dise.
- C écartée : F-22.

## Conséquences

- Le catalogue passe à 0.5.0 (ADR-0172).
- Un catalogue fourni par l'utilisateur doit porter ces douze règles, que cite le manifeste du module (ADR-0084) ; sans elles, il est refusé, ce qui n'était jamais arrivé avant T30.
- Le catalogue des tests porte les règles du module c2pa livré.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
