# ADR-0055 — Cinq directions de constat : « transformation » ajoutée à F-81

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T11
- **Exigences liées** : F-81, F-06, NF-14 ; constat A-02 ; ADR-0022

## Contexte

F-81 demande d'indiquer vers quoi pointe chaque constat : origine IA, retouche, authenticité, ou rien de particulier. ADR-0022 impose à chaque technique de distinguer quatre hypothèses : capture brute, transformation banale (recompression, redimensionnement, passage par une messagerie), retouche, génération. Les directions de F-81 n'ont pas d'équivalent pour la transformation banale, que révèlent pourtant la double compression (F-31), les indices de transfert (F-06) et la plupart des analyses du signal (A-02).

## Options envisagées

### Option A — Cinq directions : origine IA, retouche, transformation, authenticité, rien de particulier

- Avantages : une direction par hypothèse d'ADR-0022, plus « rien de particulier » ; une double compression dit ce qu'elle révèle, sans être forcée vers « retouche » (exagéré) ni vers « rien » (perte d'information).
- Inconvénients : écart au texte de F-81, à inscrire au registre et à soumettre à l'auteur du cahier.

### Option B — Les quatre directions de F-81

- Avantages : fidèle au cahier.
- Inconvénients : une transformation banale doit pointer vers « rien de particulier » ; le lecteur ne voit plus que le fichier a été réenregistré, alors que c'est ce qui borne la portée des autres analyses (F-06).

## Décision

Un constat pointe vers l'une de cinq directions : **origine IA**, **retouche**, **transformation**, **authenticité**, **rien de particulier**. F-81 est reformulée en ce sens pour le projet.

Correspondance avec les hypothèses d'ADR-0022 : génération → origine IA ; retouche → retouche ; transformation banale → transformation ; capture brute → authenticité.

## Raisons

- Option A retenue : elle permet d'écrire honnêtement ce qu'une technique distingue, ce qu'exige ADR-0022, et évite d'attribuer à la retouche une simple recompression (NF-14).
- Option B écartée : elle oblige à choisir entre exagérer (« retouche ») et taire (« rien »).

## Conséquences

- Registre des arbitrages, §4 : F-81 reformulée.
- Le modèle (ADR-0058) fixe aussi les liens entre catégorie et direction : un indice pointe toujours vers une hypothèse, une information neutre vers « rien de particulier ».
- Le résumé du rapport (ADR-0018, T16) compte les indices par direction : « transformation » y forme sa propre ligne.
- Chaque fiche technique (ADR-0022) dit quelles directions sa technique peut produire ; T12 et T15 vérifient qu'une règle n'en produit pas d'autre.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
