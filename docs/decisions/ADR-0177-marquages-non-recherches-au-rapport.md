# ADR-0177 — Marquages connus non recherchés : au rapport, avec leur raison

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T31
- **Tâche** : T31
- **Exigences liées** : F-25, NF-11, NF-14 ; A-04 ; ADR-0012

## Contexte

L'inventaire de T31 recense des marquages que l'outil ne recherche pas : SynthID, TrustMark, Video Seal, etc. La question la plus probable du public visé devant un rapport sans constat est « SynthID a-t-il été vérifié ? ». La liste des seuls marquages recherchés n'y répond qu'en creux.

## Options envisagées

### Option A — Au rapport, avec la raison

Rubrique Couverture : « Marquages connus non recherchés », avec la raison de chacun.

- Avantages : répond directement à la question ; dit que l'absence de constat ne vaut pas pour ces marquages ; la raison explique sans jargon pourquoi l'outil ne les lit pas.
- Inconvénients : change le schéma du rapport (0.6.0) ; une rubrique de plus.

### Option B — Dans l'inventaire seul

- Avantages : aucun changement de schéma.
- Inconvénients : un lecteur du rapport peut croire que SynthID a été vérifié.

## Décision

Option A. Un marquage non recherché porte une raison du catalogue : `lecteur_neuronal`, `lecteur_proprietaire`, `cle_du_fournisseur` ou `lecteur_a_venir` (vocabulaire : [ADR-0178](ADR-0178-couverture-des-marquages.md)).

## Raisons

- A retenue, recommandation suivie par TheDarkMac.
- B écartée : le rapport laisserait croire à une vérification qui n'a pas eu lieu (NF-14).

## Conséquences

- Champ `marquages_non_recherches` de la couverture, obligatoire ; schéma du rapport 0.6.0 ([ADR-0179](ADR-0179-versions-de-t31.md)).
- Le HTML montre un tableau (marquage, nature, raison), le terminal une ligne par marquage.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (réponse de TheDarkMac à la question posée pendant T31) |
