# ADR-0166 — Requêtes en ligne d'ADR-0033 : hors de T30, dans un complément

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T30
- **Tâche** : T30
- **Exigences liées** : F-21, NF-16 ; ES-06, ES-10 ; RS-01, RS-02 ; ADR-0033

## Contexte

ADR-0033 confie à T30 la récupération d'un manifeste distant sur confirmation par fichier, la révocation (CRL de préférence, OCSP sinon) et l'inscription des réponses au rapport. P2 n'a pas de réseau : toute requête partirait de P1, avec un code réseau nouveau, une confirmation à concevoir et des réponses à vérifier avant usage. c2pa-rs ne fait que l'OCSP, et seulement depuis le processus où il s'exécute.

## Options envisagées

### Option A — T30 hors ligne, requêtes dans un complément

- Avantages : T30 livre détection, vérification, états et déclarations sans réseau ; le complément traite un seul sujet.
- Inconvénients : la révocation n'est pas vérifiée en ligne en attendant.

### Option B — Tout dans T30

- Avantages : ADR-0033 réalisée d'un coup.
- Inconvénients : PR bien plus grosse ; premier code réseau du projet mêlé au reste.

## Décision

Option A. En T30 : un manifeste distant est détecté, son hôte seul observé (`c2pa.distant.hote`), l'état est « non vérifiable », la recherche partielle pour la raison `reseau_desactive` ; une réponse OCSP jointe au manifeste est lue par c2pa-rs. Le complément de T30 réalise les points 2 à 4 d'ADR-0033.

## Raisons

- A retenue par TheDarkMac, sur recommandation de l'assistant, comme pour les compléments de T21.
- B écartée : taille et risque de la PR.

## Conséquences

- ES-10 reste partielle ; F-21 est réalisée pour tout manifeste intégré.
- Les règles disent que la révocation n'est pas vérifiée en ligne.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (choix de TheDarkMac) |
