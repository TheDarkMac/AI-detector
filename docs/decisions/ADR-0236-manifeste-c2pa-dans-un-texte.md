# ADR-0236 — Manifeste C2PA écrit dans un texte : enveloppe trouvée et décrite, jamais vérifiée ; `M-C2PA-TEXTE` recherché par `caracteres`

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant au périmètre de T80 (ADR-0232) ; lecture de l'enveloppe précisée par l'assistant
- **Tâche** : T80
- **Exigences liées** : F-20, F-24, F-25 ; ADR-0164, ADR-0175, ADR-0177, ADR-0178, ADR-0206, ADR-0232

## Contexte

L'annexe A.7 de la spécification C2PA 2.3 (« Embedding Manifests into Unstructured Text », lue le 2026-11-17 sur `spec.c2pa.org`) écrit un magasin de manifestes C2PA dans un texte : une enveloppe `C2PATextManifestWrapper` (en-tête de 8 octets `C2PATXT\0`, version sur un octet, valant 1, longueur du manifeste sur quatre octets, puis la boîte JUMBF), dont chaque octet devient un sélecteur de variante (0 à 15 : U+FE00 à U+FE0F ; 16 à 255 : U+E0100 à U+E01EF), précédée d'un U+FEFF, d'un seul tenant, de préférence à la fin du texte. Une enveloppe au plus est prévue ; deux codes d'échec sont définis, `manifest.text.corruptedWrapper` et `manifest.text.multipleWrappers`. L'empreinte (`c2pa.hash.data`) porte sur le texte normalisé NFC, encodé en UTF-8, privé des octets de l'enveloppe.

T31 a inscrit ce marquage au catalogue (`M-C2PA-TEXTE`) avec la raison `lecteur_a_venir`, en le confiant à T80 (ADR-0177). Le module `c2pa` lit les manifestes par c2pa-python (ADR-0164) ; la version 0.39.0 ne déclare aucun type de texte parmi ceux qu'elle lit (`Reader.get_supported_mime_types()`, relevé le 2026-11-17).

## Options envisagées

### Option A — Enveloppe trouvée et décrite, non vérifiée (recommandée, retenue avec ADR-0232)

Le module `caracteres` cherche l'enveloppe comme l'annexe le dit (A.7.4.2), la décode, et dit sa version, sa longueur et si sa boîte JUMBF est celle d'un magasin C2PA ; la signature et l'empreinte du texte ne sont pas vérifiées.

- Avantages : le marquage devient recherché ; le rapport dit qu'un manifeste est là, ou qu'il a été coupé ; les sélecteurs de l'enveloppe ne sont pas pris pour des sélecteurs inhabituels.
- Inconvénients : un manifeste forgé ou copié d'un autre texte se lit comme un vrai.

### Option B — Laissé « lecteur à venir » (option C d'ADR-0232)

- Avantages : rien à écrire en T80.
- Inconvénients : les sélecteurs d'une enveloppe seraient relevés comme inhabituels sans que le rapport dise pourquoi.

### Option C — Vérification complète écrite par le projet

Lire le magasin JUMBF, vérifier la signature COSE contre la liste de confiance, recalculer l'empreinte du texte normalisé.

- Avantages : le constat d'un manifeste vérifié, comme pour une image.
- Inconvénients : réécrire ce que fait c2pa-rs (CBOR, COSE, X.509, horodatage) : une surface d'attaque et un risque d'erreur hors de proportion. Non proposée à TheDarkMac : écartée par l'assistant.

## Décision

Option A. Précisions de l'assistant :

- **Recherche** : dans chaque suite d'invisibles, un U+FEFF suivi d'au moins huit sélecteurs dont les huit premiers octets valent `C2PATXT\0` est une enveloppe ; ses caractères (U+FEFF compris) sont retirés des familles `sans_chasse` et `selecteurs`.
- **Complète** si la version vaut 1, la longueur annoncée est celle des octets qui suivent l'en-tête, et ces octets sont une superboîte `jumb` de cette longueur dont la première boîte est une description `jumd` qui porte une étiquette (bascule 0x02) valant `c2pa` (ISO/IEC 19566-5 ; C2PA 2.3, §11.1.4.2 : étiquette `c2pa`, type `63327061-0011-0010-8000-00AA00389B71`, que le module ne contrôle pas). Une superboîte à longueur étendue (`LBox` = 1) est comptée corrompue. **Corrompue** sinon (`manifest.text.corruptedWrapper`).
- **Restitution** : `caracteres.c2pa` (enveloppes trouvées), `.completes`, `.corrompues`, `.version` et `.octets` (longueur annoncée) de la première complète, ou de la première, positions des huit premières (« complète » ou « corrompue »).
- **Marquage** : `M-C2PA-TEXTE` passe de `raison = "lecteur_a_venir"` à `module = "caracteres"`, format `texte`, date de vérification 2026-11-17 ; il figure aux marquages recherchés d'un texte, fichier ou collé.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant (ADR-0232), sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : les sélecteurs d'une enveloppe seraient mal lus.
- Option C écartée : la vérification d'une signature reste confiée à c2pa-rs ; elle viendra quand c2pa-python lira le texte.

## Conséquences

- Plus aucun marquage livré n'a la raison `lecteur_a_venir` ; la raison reste au modèle et au schéma pour les marquages à venir et les catalogues fournis.
- Une version de c2pa-python qui lira le texte brut permettra au module `c2pa` de vérifier ces manifestes : nouvel ADR, qui fixera le partage avec `caracteres`.
- Le choix entre plusieurs enveloppes se fait par les exclusions de l'empreinte (A.7.4.1), que l'outil ne lit pas : R-CARACTERES-012 le dit.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création, avec le périmètre de T80 (ADR-0232) |
