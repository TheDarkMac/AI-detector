# ADR-0010 — Distribution en ligne de commande et bibliothèque, traitement local hors ligne

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (confirme le choix provisoire noté au journal de T00)
- **Tâche** : T02
- **Exigences liées** : §9 livrable 1 ; NF-01, NF-04, NF-05, NF-16, NF-17 ; constat A-16

## Contexte

Le §10 laisse ouverts le mode de distribution, le lieu du traitement (local ou serveur), le fonctionnement hors ligne et la conservation des données. Le journal de T00 notait un choix provisoire « ligne de commande + bibliothèque ». Plusieurs exigences ne s'entendent pas de la même façon selon le mode (A-16) : il faut trancher avant le modèle de menace (T03).

## Options envisagées

### Option A — Ligne de commande et bibliothèque, traitement local

- Avantages : les fichiers sensibles ne quittent pas le poste (NF-04, NF-15) ; pas de compte ni de serveur à exploiter ; fonctionnement hors ligne possible ; adapté à un public de vérificateurs équipés.
- Inconvénients : installation nécessaire ; une bibliothèque s'exécute dans le processus appelant, l'isolation (NF-01) doit être imposée par elle ; « qui » et « horodatage fiable » de NF-17 sont difficiles sans serveur.

### Option B — Application web sur serveur

- Avantages : aucune installation ; journal et horodatage centralisés.
- Inconvénients : les fichiers quittent le poste ; comptes, conservation, RGPD et isolation serveur à traiter dès la V1.

### Option C — Local en V1, architecture prévue pour un serveur en V2

- Avantages : prépare une évolution.
- Inconvénients : contraint l'architecture (T04) pour un besoin non établi.

## Décision

- Livraison en **ligne de commande et bibliothèque** ; tout le traitement est **local**.
- **Hors ligne par défaut** : aucune requête sortante sans activation explicite par l'utilisateur. Les données externes nécessaires (liste de confiance C2PA, catalogue) sont livrées avec l'outil, versionnées. Les vérifications en ligne (révocation de certificats, manifestes distants) sont optionnelles, désactivées par défaut, et leur usage est inscrit au rapport.
- **Aucun compte**. L'outil ne conserve aucun fichier ; il n'écrit que les rapports demandés, à l'emplacement choisi par l'utilisateur. C'est ce qu'il affiche au titre de NF-05.
- Pas d'interface graphique en V1 ; une interface web **locale** reste possible ensuite (T90).

## Raisons

- Option A retenue : la plus sûre pour des fichiers sensibles et des sources à protéger, et la moins coûteuse à exploiter.
- Option B écartée : elle fait sortir les fichiers du poste et ajoute un serveur à sécuriser, pour un public (ADR-0009) qui peut installer un outil.
- Option C écartée : la séparation bibliothèque / ligne de commande laisse déjà la porte ouverte à un serveur, sans en faire une contrainte de T04.

## Conséquences

- NF-01 : la bibliothèque doit exécuter l'analyse dans un processus isolé, et non dans le processus appelant ; niveau d'isolation fixé en T03 puis T04 (A-53).
- NF-17 : en local, « qui » n'est pas connu et un journal local est modifiable ; un horodatage fiable suppose une autorité externe, donc une requête sortante optionnelle. Portée réelle de NF-17 à définir en T03, réalisation en T91.
- NF-16 : l'inventaire des requêtes sortantes est court et chacune est désactivable ; l'état (activée ou non) figure au rapport.
- Reproductibilité facilitée : sans réseau, les entrées externes sont celles livrées avec l'outil (ADR-0023).
- Le langage (Python, évoqué en T00) relève de T04, qui le formalisera par ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : niveau d'isolation fixé par ADR-0028, portée de NF-17 par ADR-0030, politique des requêtes sortantes fixée par ADR-0033 (T03) |
