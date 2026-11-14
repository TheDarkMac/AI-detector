# ADR-0173 — Adresse d'un manifeste C2PA distant dans le XMP : masquée comme un numéro de série

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, pendant la revue de la PR de T30
- **Tâche** : T30
- **Exigences liées** : ES-13, F-90 ; M-14 ; ADR-0119, ADR-0159, ADR-0161, ADR-0169

## Contexte

Le module `c2pa` n'inscrit que l'hôte d'un manifeste distant (ADR-0169) : l'adresse entière peut être propre à l'exemplaire, et donc désigner qui l'a reçu (M-14). Pendant la vérification de T30, l'assistant a constaté que le module `xmp` observe cette même adresse, propriété `dcterms:provenance`, sans la marquer : elle figurait dans l'export JSON masqué. La limite de la règle R-C2PA-011, qui disait l'adresse absente du rapport, était fausse.

## Options envisagées

### Option A — Marquer `dcterms:provenance` comme numéro de série

- Avantages : masquée par défaut, levée par `--reveler numero_de_serie` ; même traitement que la valeur FBMD, identifiant propre à un envoi (ADR-0161).
- Inconvénients : une adresse générique, commune à tous les exemplaires, est masquée aussi.

### Option B — Corriger seulement la limite de R-C2PA-011

- Avantages : aucun changement de module.
- Inconvénients : un identifiant d'exemplaire reste en clair dans un rapport destiné à être transmis.

## Décision

Option A : `dcterms:provenance` rejoint les champs `numero_de_serie` du module `xmp`, qui passe à la version 0.7.0. La limite de R-C2PA-011 le dit.

## Raisons

- A retenue par TheDarkMac (« Yes, mask it »), sur recommandation de l'assistant : l'adresse peut identifier l'exemplaire, ce qu'ES-13 demande de masquer.
- Catégorie numéro de série plutôt que texte libre : l'adresse n'est pas écrite par une personne, elle identifie un objet, comme FBMD.
- B écartée : laisse la fuite.

## Conséquences

- Le contrôle avant publication compte l'adresse parmi les numéros de série.
- Le texte de R-C2PA-011 change avant toute publication du catalogue 0.5.0 : empreinte de 0.5.0 recalculée au registre, version de la règle inchangée.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (choix de TheDarkMac pendant la revue de la PR de T30) |
