# ADR-0164 — Bibliothèque C2PA : c2pa-python 0.39.0 dans le processus de travail, sans réseau

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T30, validée pendant la revue de la PR de T30
- **Tâche** : T30
- **Exigences liées** : F-20, F-21, NF-04, NF-16 ; ES-02, ES-06, ES-10 ; ADR-0033, ADR-0043, ADR-0120

## Contexte

ADR-0043 désignait `c2pa-python`, liaison de l'implémentation de référence c2pa-rs, pour C2PA. L'examen de T10 (architecture, §9) laissait à T30 trois points : l'absence de paquet Windows dans la version 0.38.1, et les dépendances `requests` et `toml`, peu compatibles avec le critère « aucun accès réseau, ou désactivable ».

Examen du 2026-11-14 :

- `c2pa-python` 0.39.0, publiée le 2026-11-12, sous licence MIT ou Apache-2.0, a de nouveau des paquets pour Windows (x86-64 et ARM64), Linux (x86-64, AArch64) et macOS ; elle embarque c2pa-rs 0.92.0 (`sdk_version()`), qui suit la spécification C2PA 2.4.
- C'est une liaison `ctypes` vers une bibliothèque native de 23 Mio, chargée à l'import. `requests` et `toml` ne servent qu'au script de construction (`c2pa/build.py`), jamais importé à l'exécution ; `cryptography` n'est pas importée par la lecture. La bibliothèque native contient un client HTTP (reqwest).
- Par défaut, c2pa-rs récupère les manifestes distants (`verify.remote_manifest_fetch` vrai) ; l'OCSP est coupé (`ocsp_fetch` faux). `core.allowed_network_hosts` vide refuse toute adresse, même récupération activée (essai : « not permitted by the allowed list »).
- Lecture et vérification essayées dans un processus soumis aux restrictions de Linux du projet (seccomp et Landlock, aucun manque) : correctes, aucune lecture de fichier après les restrictions.
- Coût : l'import prend 0,13 à 0,16 s (`python -X importtime`, trois mesures) ; une analyse d'un JPEG de 7 Kio prend environ 0,71 s au total sur le poste, module désactivé ou non, puisque tous les modules sont importés.

## Options envisagées

### Option A — c2pa-python 0.39.0, dans P2, réseau coupé par les réglages

- Avantages : implémentation de référence, à jour de la spécification ; aucune vérification cryptographique écrite par le projet ; trois systèmes.
- Inconvénients : code natif de 23 Mio dans P2 ; coût d'import pour chaque fichier ; quatre dépendances transitives installées sans servir (`requests`, `toml`, `cryptography`, `certifi`).

### Option B — Lecteur JUMBF, CBOR et COSE écrit par le projet, cryptographie par `cryptography`

- Avantages : maîtrise du code qui lit le fichier, comme pour les autres formats (ADR-0114).
- Inconvénients : la vérification C2PA (empreintes par format, chaîne, horodatage, OCSP agrafé, ingrédients) est un travail de plusieurs mois ; une vérification écrite à côté de la référence se tromperait là où celle-ci ne se trompe pas.

### Option C — c2pa-rs dans un processus à part

- Avantages : isole le code natif du reste de P2.
- Inconvénients : P2 est déjà ce processus à part (ADR-0036) ; rien de plus n'est isolé.

## Décision

Option A. Réglages remis à c2pa-rs à chaque lecture : `verify_after_reading`, `verify_trust`, `verify_timestamp_trust` vrais ; `ocsp_fetch` et `remote_manifest_fetch` faux ; `core.allowed_network_hosts` vide ; `core.decode_identity_assertions` faux ; ancres des signataires et des autorités d'horodatage en deux listes `trust.anchors` (`manifest`, `tsa`). La version inscrite au rapport est celle du paquet `c2pa-python`, lue sans charger la bibliothèque native (ADR-0120) ; un test lie 0.39.0 à c2pa-rs 0.92.0.

## Raisons

- A retenue : c'est la bibliothèque qu'ADR-0043 désignait, et les trois points de T10 sont levés : Windows est de nouveau servi, `requests` et `toml` ne s'exécutent pas, le réseau se coupe par deux réglages indépendants.
- B écartée : coût et risque d'erreur hors de proportion ; l'implémentation de référence est précisément ce qu'on veut comparer aux fichiers.
- C écartée : sans objet, P2 étant déjà isolé.
- Deux réglages réseau plutôt qu'un : sous Windows, P2 n'a pas de blocage du réseau (ADR-0081) ; si une version future changeait le sens de l'un, l'autre tient encore.
- Identité CAWG non décodée : sa vérification peut demander de résoudre des identifiants en ligne, et rien en V1 ne la restitue.

## Conséquences

- Chaque processus de travail charge la bibliothèque native, même pour un fichier sans manifeste : environ 0,15 s de plus par fichier.
- Les limites comptées du moteur ne voient pas le travail de c2pa-rs, borné par sa limite de manifeste décompressé (32 Mio) et par la mémoire et le temps de P2 (ADR-0077).
- `pip-audit` audite désormais `cryptography`, `cffi`, `pycparser` et `toml`. `toml` n'a plus de version depuis 2020 ; sans exécution, le risque est nul, à revoir si c2pa-python l'importe un jour.
- Le schéma des manifestes admet la bibliothèque `c2pa-python`.
- Un contexte et un flux c2pa sont créés à l'import du module, avant les restrictions, et gardés tout le processus (ADR-0079). Sous macOS avec Python 3.12 et 3.13, un flux crée des fonctions de rappel ctypes que libffi loge dans une table de trampolines allouée à la première ; Seatbelt refusant ensuite cette allocation, le processus de travail s'arrêtait au premier fichier, sur une assertion de libffi (`ffi_trampoline_table_alloc`, code −6 ; diagnostic de la CI de la PR de T30). Python 3.14 n'est pas touché.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T30 (« Oui, les cinq ») : statut « Accepté » |
