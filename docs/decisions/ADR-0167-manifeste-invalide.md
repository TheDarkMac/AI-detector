# ADR-0167 — Manifeste invalide par un écart d'empreinte : indice faible vers la transformation

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T30
- **Tâche** : T30
- **Exigences liées** : F-22, F-80, F-81 ; ES-20 ; ADR-0018, ADR-0021, ADR-0055

## Contexte

Un manifeste est invalide quand la vérification échoue : empreinte du contenu ou d'une assertion différente de celle signée, signature de la revendication fausse, certificat expiré ou révoqué. Un écart d'empreinte est établi cryptographiquement ; sa cause ne l'est pas : retouche, outil qui garde le manifeste sans le mettre à jour, défaut d'un logiciel, manifeste recopié sur un autre contenu.

## Options envisagées

### Option A — Indice faible vers la transformation

- Avantages : dit qu'un changement a eu lieu, sans en dire la nature ; faible tant qu'il n'est pas évalué (ADR-0018).
- Inconvénients : un défaut de logiciel donne aussi l'indice.

### Option B — Preuve, transformation

- Avantages : la discordance est une vérification cryptographique.
- Inconvénients : « transformation » interprète déjà l'écart, au-delà de ce qu'établit l'empreinte.

### Option C — Information neutre

- Avantages : aucune interprétation.
- Inconvénients : tait un fait utile au vérificateur.

## Décision

Option A : règle R-C2PA-006, fondement vérification cryptographique, pour les codes `assertion.dataHash.mismatch`, `assertion.bmffHash.mismatch`, `assertion.boxesHash.mismatch`, `assertion.collectionHash.mismatch`, `assertion.hashedURI.mismatch` et `claimSignature.mismatch`. Tout manifeste invalide reçoit en plus la phrase d'état R-C2PA-009, avec ses codes ; un invalide sans écart d'empreinte (certificat expiré, par exemple) n'a que celle-là.

## Raisons

- A retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : la preuve dirait plus que l'empreinte.
- C écartée : perd l'information d'un changement établi.

## Conséquences

- Sous une signature invalide, une source numérique déclarée n'est plus qu'un indice faible (R-C2PA-004, R-C2PA-005), comme une métadonnée non signée.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (choix de TheDarkMac) |
