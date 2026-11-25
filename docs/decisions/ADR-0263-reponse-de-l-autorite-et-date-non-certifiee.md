# ADR-0263 — Réponse de l'autorité vérifiée sur son contenu, non sur sa signature ; date de l'analyse marquée non certifiée

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T91
- **Exigences liées** : NF-17, ES-04, ES-16 ; ADR-0030, ADR-0043, ADR-0262 ; menaces M-24, M-25

## Contexte

La réponse d'une autorité d'horodatage est une structure DER signée (CMS `SignedData` d'un `TSTInfo`). La lire demande un décodeur DER ; vérifier sa signature et la chaîne de ses certificats demande en plus une bibliothèque cryptographique et une ancre de confiance. `cryptography` 50.0.2 est déjà installée, comme dépendance de `c2pa-python`, mais n'offre pas la vérification d'un `SignedData` (constaté le 2026-11-25 : son module `pkcs7` signe, chiffre et déchiffre ; ses vérificateurs de chaîne sont ceux d'un serveur ou d'un client TLS) : elle serait à écrire, avec l'usage étendu `timeStamping` et ses règles. ES-16 demande aussi que l'heure du poste, toujours inscrite au rapport, soit marquée « non certifiée », ce que le rapport ne faisait pas.

## Options envisagées

### Option A — Contenu vérifié, signature non (recommandée)

Statut accordé, jeton signé d'un `TSTInfo`, algorithme SHA-256, empreinte et nonce égaux à ceux envoyés, heure lue ; ni signature ni certificats vérifiés ; le terminal le dit et donne la commande `openssl`.

- Avantages : aucune dépendance nouvelle ; un décodeur DER minimal en Python suffit ; la vérification cryptographique reste possible, par un outil courant et éprouvé.
- Inconvénients : l'heure affichée est celle que la réponse annonce ; une réponse forgée par un intermédiaire, sur `http`, serait acceptée par l'outil, et seule `openssl` la refuserait.

### Option B — Signature et chaîne vérifiées

- Avantages : l'heure affichée serait établie par l'outil.
- Inconvénients : la vérification CMS et l'usage `timeStamping` à coder à la main ; une ancre de confiance à demander à l'utilisateur ; nettement plus long, pour un gain que `openssl` donne déjà.

## Décision

Option A.

- Décodeur DER minimal (`_conservation/_der.py`) : étiquettes d'un octet, longueurs définies d'au plus 4 octets, chaque longueur vérifiée contre les octets disponibles, découpage à la demande, sans récursion ; toute anomalie est une erreur dont le message ne cite aucun octet reçu. La réponse se lit comme un fichier hostile (ES-04), dans le processus principal.
- Contrôles : statut 0 ou 1 (accordé, accordé avec modifications), les autres nommés (rejet, attente, révocation) ; `ContentInfo` de type `SignedData` ; contenu encapsulé de type `TSTInfo` ; version 1 ; algorithme SHA-256 ; empreinte égale ; nonce présent et égal ; heure `GeneralizedTime` en UTC, lue à la seconde.
- Le terminal écrit « horodaté : … UTC selon l'autorité », puis que la signature des jetons n'est pas vérifiée par l'outil, avec la commande `openssl ts -verify`.
- Date de l'analyse : le rapport HTML l'écrit « … UTC, horloge du poste, non certifiée » en tête, et « Date de l'analyse (UTC, horloge du poste, non certifiée) » à l'identification ; le schéma du rapport le dit dans la description de `date_analyse`. Le JSON garde sa forme : `VERSION_SCHEMA` est inchangée.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : coût élevé pour une vérification que l'utilisateur fait avec `openssl`, et qui demanderait de toute façon une ancre qu'il choisit.

## Conséquences

- L'outil a été vérifié contre une autorité réelle : OpenSSL 3.5.9 répond à sa requête, et `openssl ts -verify` accepte la réponse qu'il a écrite (`tests/donnees/horodatage/generer_horodatage.py`). Un passage sur une autorité publique n'a pas été fait, pour ne rien envoyer hors du poste sans accord.
- La liste de confiance livrée contient les ancres d'horodatage de la C2PA (`horodatage.pem`, ADR-0171) : une vérification future de la signature pourrait s'y appuyer, par défaut ou sur une ancre fournie. Renvoyé à une tâche ultérieure, sur demande.
- Rien ne change dans le format du JSON ni dans les comparaisons de rapports.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
