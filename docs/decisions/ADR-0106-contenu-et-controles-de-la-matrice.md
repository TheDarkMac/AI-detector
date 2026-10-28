# ADR-0106 — Contenu et contrôles de la matrice : principes numérotés, cas d'usage, états

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : Assistant, proposition non posée en question pendant T17, soumise à la revue de la PR de T17
- **Tâche** : T17
- **Exigences liées** : §2, §4, §8 du cahier ; ADR-0024, ADR-0102 ; A-11, A-27, A-58

## Contexte

ADR-0102 fixe la forme de la matrice. Restent son contenu et ses règles : les principes directeurs du §2 n'ont pas d'identifiant (A-11) ; les cas d'usage ne sont reliés à aucune exigence (A-27) ; la plupart des exigences ne sont pas encore réalisées, et certaines sont hors V1 ; ADR-0024 demande de justifier toute méthode autre que « test ».

## Options envisagées

Sur l'état d'une exigence non réalisée :

### Option A — États explicites et tâches

`realisee`, `partielle`, `a_venir`, `hors_v1`, avec les tâches qui la réalisent.

- Avantages : la matrice dit aussi ce qui reste à faire, et pourquoi une exigence n'est pas vérifiée.
- Inconvénients : un état à tenir à jour par chaque tâche.

### Option B — Seulement les exigences réalisées

- Avantages : plus court.
- Inconvénients : une exigence oubliée ne se distingue pas d'une exigence prévue ; la complétude ne se vérifie plus.

## Décision

Option A, et :

- **Principes** : P-01 à P-06, dans l'ordre du §2 (aucune IA embarquée, explicabilité, preuve ≠ indice, absence ≠ authenticité, reproductibilité, modularité), avec leur texte, dans `matrice.toml` ; ils sont traités comme des exigences.
- **Cas d'usage** : CU-1 à CU-5 du cahier, reliés aux exigences ; ceux d'A-27, plus CU-1 relié à la soumission, à la restitution et à la lisibilité.
- **Exigences** : toutes les F et NF du cahier, toutes les ES du modèle de menace, tous les principes, une seule fois chacune. Le texte affiché est celui de la source ; une reformulation (registre des arbitrages, §4) est signalée en remarque avec son ADR.
- **Contrôles** (`python -m banc.matrice --verifier`) : identifiants connus et complets ; état connu ; tâches écrites `TNN` ; méthodes connues, sans doublon ; justification pour toute méthode autre que « test » (ADR-0024) ; preuve existante et résultat pour une exigence réalisée par une telle méthode ; décision citée pour une exigence hors V1 ; au moins un test marqué pour une exigence réalisée ou partielle vérifiée par test ; aucun test marqué sur une exigence à venir, hors V1 ou non vérifiée par test ; cas d'usage connus, complets, reliés à des exigences connues.

## Raisons

- Option A retenue : la matrice devient le tableau de bord de l'avancement exigence par exigence, et un oubli devient une erreur.
- Option B écartée : on ne pourrait plus vérifier que toutes les exigences sont présentes.
- Une exigence partiellement réalisée a déjà des tests : les exiger tient la matrice honnête dès la première ligne de code.

## Conséquences

- Chaque tâche met à jour l'état des exigences qu'elle touche, dans la même PR ; le contrôle échoue sinon dès qu'un test marqué apparaît ou disparaît.
- A-58 (matrice absente des livrables) est traité : la matrice est un document du dépôt, tenu à jour à chaque tâche.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
