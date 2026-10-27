# ADR-0029 — Intégrité du catalogue et de la liste de confiance : livrés avec l'outil

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T03
- **Exigences liées** : F-26, NF-06, NF-07, NF-16 ; constat A-37 ; registre des arbitrages §3 point 9 ; menaces M-11 à M-13

## Contexte

Le catalogue de règles (F-26) et la liste de confiance C2PA décident de ce que l'outil reconnaît. Un catalogue altéré peut blanchir des faux, une liste de confiance altérée faire reconnaître un signataire quelconque (A-37). F-26 exige que le catalogue se mette à jour sans modifier le moteur. ADR-0010 interdit toute requête sortante par défaut.

## Options envisagées

### Option A — Livrés avec l'outil, version et empreinte au rapport

- Avantages : même canal et mêmes vérifications que l'outil lui-même ; aucune requête sortante ; aucune clé à gérer ; reproductibilité simple (ADR-0023).
- Inconvénients : une mise à jour du catalogue suit le rythme des versions publiées.

### Option B — Mises à jour séparées, signées par une clé du projet

- Avantages : mises à jour plus fréquentes, refus de tout catalogue mal signé.
- Inconvénients : une requête sortante de plus ; une clé de signature à protéger, dont la compromission serait pire que l'absence de signature.

### Option C — Aucun contrôle particulier

- Avantages : le plus simple.
- Inconvénients : un catalogue altéré passe sans que le rapport le montre.

## Décision

- Le catalogue et la liste de confiance sont des **fichiers de données séparés du moteur** (F-26), **livrés dans le paquet de l'outil** ; l'outil ne télécharge rien. Une mise à jour passe par le gestionnaire de paquets de l'utilisateur, comme une mise à jour de l'outil.
- Ils sont **validés par schéma au chargement** ; un catalogue invalide arrête l'analyse avec un message explicite.
- Le rapport inscrit leur **version et leur empreinte** ; les empreintes des versions publiées sont publiées avec elles, pour comparaison.
- Un catalogue fourni par l'utilisateur est accepté, et le rapport le signale comme « catalogue fourni par l'utilisateur ».

## Raisons

- Option A retenue : elle protège l'intégrité par le même moyen que le code, sans requête ni clé, et rend toute altération visible au rapport.
- Option B écartée pour la V1 : le gain de fréquence ne justifie pas une clé de signature à protéger pour un petit projet ; envisageable plus tard, par un nouvel ADR.
- Option C écartée : A-37.

## Conséquences

- T15 définit le format, le schéma et le calcul de l'empreinte du catalogue ; T30 fait de même pour la liste de confiance.
- La date de la liste de confiance figure au rapport (ADR-0023), avec la mention qu'une révocation postérieure n'est pas connue hors ligne (RR-09).
- La publication des versions (T04, T10) inclut les empreintes du catalogue.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : format du catalogue fixé par ADR-0038, canal de distribution par ADR-0041 (T04) |
| 2026-10-27 | Réalisé en T15 : forme et empreinte (ADR-0088), version, date et registre publiés avec les versions (ADR-0085), catalogue fourni par l'utilisateur en remplacement complet (ADR-0086) |
