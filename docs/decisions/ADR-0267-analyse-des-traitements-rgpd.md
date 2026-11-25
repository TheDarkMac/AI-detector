# ADR-0267 — NF-13 : analyse des traitements au regard du RGPD dans `docs/verification/`, exigence partielle jusqu'à T103

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T92
- **Exigences liées** : NF-04, NF-05, NF-13, NF-18 ; ADR-0010, ADR-0020, ADR-0024, ADR-0030, ADR-0031

## Contexte

NF-13, reformulée par ADR-0020 : l'outil respecte la réglementation de l'Union européenne sur les données personnelles, le RGPD. La matrice la vérifie par analyse (ADR-0024), partagée entre T92 et T103. Aucun document ne recensait encore ce que l'outil fait des données personnelles : celles des fichiers (auteurs, positions GPS, numéros de série), celles des rapports, du journal (empreintes, nom déclaré) et de la demande d'horodatage (adresse IP).

## Options envisagées

### Option A — Analyse écrite en T92, NF-13 partielle (recommandée)

Un document de `docs/verification/` recense chaque traitement, ses données, son lieu, sa durée et ses destinataires, et le confronte aux principes du RGPD ; les mentions destinées à l'utilisateur restent à T103.

- Avantages : l'analyse est faite avec l'affichage de la conservation, qui en donne les faits ; T103 n'a plus qu'à rédiger les mentions à partir d'elle.
- Inconvénients : un document de plus à tenir à jour à chaque traitement ajouté.

### Option B — Tout à T103

- Avantages : une seule tâche pour l'analyse et les mentions.
- Inconvénients : T92 afficherait la conservation sans l'analyse qui la fonde ; NF-13 resterait « à venir ».

### Option C — Analyse écrite, NF-13 réalisée dès T92

- Avantages : l'exigence est close plus tôt.
- Inconvénients : l'utilisateur n'est encore informé ni de ses obligations, ni des droits des personnes dont il traite les données : c'est l'objet des mentions de T103.

## Décision

Option A. [`docs/verification/donnees-personnelles.md`](../verification/donnees-personnelles.md) : périmètre et avertissement (ce n'est pas un avis juridique, ADR-0020) ; rôles ; un tableau des traitements (analyse, affichage, rapports, journal, horodatage, catalogue et liste de confiance) avec leurs données, lieu, durée et destinataires ; les principes du RGPD (article 5), la protection des données dès la conception et par défaut (article 25), la sécurité (article 32), les transferts (chapitre V), les droits des personnes ; ce qui reste à T103. NF-13 passe « partielle », avec ce document pour preuve.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : l'analyse et l'affichage portent sur les mêmes faits ; les séparer de plusieurs tâches les exposerait à diverger.
- Option C écartée : l'analyse dit ce que fait l'outil ; la conformité suppose aussi que l'utilisateur sache ce qui lui revient, que les mentions de T103 lui diront.

## Conséquences

- Tout traitement nouveau (requête sortante, écriture, donnée gardée) met à jour ce document dans la PR qui l'ajoute.
- T103 rédige les mentions à partir du §5 du document.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
