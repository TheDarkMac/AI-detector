# ADR-0126 — PDF chiffré : reconnu et dit au rapport, jamais déchiffré

- **Statut** : Accepté
- **Date** : 2026-11-12
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21
- **Exigences liées** : F-10, F-82, ES-18 ; ADR-0043, ADR-0124 ; architecture §9

## Contexte

Un PDF chiffré (clé `/Encrypt` du trailer, ISO 32000-2, §7.6) chiffre ses chaînes et ses flux, dont les chaînes du dictionnaire d'information. Beaucoup ne demandent aucun mot de passe pour être ouverts (mot de passe utilisateur vide, restrictions d'impression ou de copie seulement). Les déchiffrer demande RC4 et MD5 (chiffrement ancien) ou AES-128 et AES-256 ; la bibliothèque standard de Python ne fournit pas AES. L'architecture (§9) laissait « à trancher en T50 » l'option `crypto` de `pypdf`.

## Options envisagées

### Option A — Reconnu, non lu, dit au rapport

- Avantages : aucune dépendance cryptographique ; aucune clé dérivée ni mot de passe manipulé ; le rapport dit pourquoi le dictionnaire n'a pas été lu.
- Inconvénients : les métadonnées des PDF chiffrés, même sans mot de passe, manquent au rapport.

### Option B — Déchiffrer avec le mot de passe utilisateur vide

- Avantages : couvre les PDF « protégés » courants, comme le fait exiftool.
- Inconvénients : AES demande `cryptography` (C et Rust) dans le processus de travail, exposée au fichier (ES-18) ; une implémentation des algorithmes de dérivation de clé (révisions 2 à 6) à écrire et tester ; à réévaluer de toute façon en T50 avec les révisions.

## Décision

Option A : un document chiffré est reconnu ; ses chaînes ne sont pas lues ; le XMP du catalogue n'est lu que si le dictionnaire de chiffrement le déclare en clair (`/EncryptMetadata false`) et qu'il est lisible sans déchiffrement.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée pour T21 : dépendance cryptographique exposée au fichier pour une seule famille d'observations ; la question reste ouverte pour T50.

## Conséquences

- `infopdf` observe `infopdf.chiffre` (vrai ou faux) dès que la table se lit ; pour un document chiffré, `infopdf.present` dit si le trailer désigne un dictionnaire, et une analyse non menée `format_partiel` porte le chemin « dictionnaire Info (document chiffré) ».
- `xmp` observe `xmp.present` d'après le catalogue ; un paquet chiffré est non mené pour `format_partiel`, chemin « flux Metadata du catalogue (document chiffré) ». Un catalogue rangé dans un flux d'objets chiffré n'est pas lisible : le module le dit de la même façon.
- L'échantillon `tests/donnees/metadonnees/chiffre.pdf` (Ghostscript, RC4 128 bits, mot de passe utilisateur vide) vérifie ce comportement ; il n'entre pas dans l'oracle exiftool, qui le déchiffre.
- T50 tranchera le déchiffrement des révisions, avec ses propres options.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création ; option choisie par TheDarkMac au début de T21 |
