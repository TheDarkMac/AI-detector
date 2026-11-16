# ADR-0209 — Signatures d'un PDF : lues par leur structure, sans vérification cryptographique

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T50
- **Exigences liées** : F-60, F-82, ES-18, ES-20 ; ADR-0043, ADR-0164, ADR-0208

## Contexte

Une signature d'un PDF (§12.8) est un dictionnaire, valeur d'un champ de signature, dont `/ByteRange` donne les octets signés : du début du fichier jusqu'à la valeur `/Contents`, puis de la fin de cette valeur jusqu'à la fin de la version signée. `/Contents` porte une signature CMS (PKCS #7) ou un horodatage (RFC 3161). F-60 range la signature parmi les ajouts légitimes ; savoir quelle version elle couvre suffit pour cela. La vérifier demanderait une bibliothèque cryptographique dans le processus de travail et une liste de confiance propre aux PDF.

## Options envisagées

### Option A — Structure seule (recommandée)

Pour chaque champ de signature du formulaire de la dernière version (`/FT /Sig`, hérité des parents, avec une valeur `/V`) : la version dont la fin est celle de la plage signée, et si la plage est complète ; le sous-filtre (`/SubFilter`) et la date déclarée (`/M`) ; les droits d'une signature de certification (`/P` de DocMDP).

- Avantages : aucune dépendance ; dit quelle version est signée, ce qui suffit pour distinguer l'ajout légitime et voir ce qui change après (ADR-0211).
- Inconvénients : ni la validité de la signature, ni l'identité du signataire ne sont au rapport.

### Option B — Vérifier la signature CMS

Par `cryptography` ou pyHanko.

- Avantages : dit si la signature est valide et qui l'a posée.
- Inconvénients : une dépendance en C et Rust exposée au fichier (ES-18) ; une liste de confiance PDF à définir (les listes européennes, la liste AATL d'Adobe), comme la C2PA l'a demandé en T30 (ADR-0164 à ADR-0172) ; la révocation demande le réseau (ADR-0033).

## Décision

Option A. Une plage est **complète** si elle a quatre entiers positifs, part de l'octet 0, que la partie laissée de côté est une chaîne hexadécimale (`<`, chiffres hexadécimaux et blancs, `>`, 1 Mio au plus relu), et que sa fin est celle d'une version (ADR-0207).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : dépendance et liste de confiance pour une information qui n'est pas demandée par F-60 ; aucune tâche de la V1 ne la prévoit.

## Conséquences

- Observations : `revisionspdf.signatures` (nombre de signatures du formulaire) ; pour les 32 premières, `revisionspdf.signature.<n>.version` (0 si la plage ne finit à la fin d'aucune version), `.plage_complete`, `.sous_filtre`, `.date` (jamais pour un document chiffré, ADR-0210) ; `revisionspdf.docmdp` (1, 2 ou 3 ; 2 si la signature de certification ne le dit pas) ; `revisionspdf.derniere_version_signee` et `revisionspdf.non_reconnues_apres_signature` dès qu'une plage est complète.
- La chronologie compte, à chaque version, les signatures dont la plage complète finit à sa fin (ADR-0212).
- Vérifié contre pyHanko 0.38.1 et `pdfsig` de Poppler 25.03.0 (`tests/donnees/revisions/oracle.json`) : même fin de plage, même intégrité, même couverture du document entier.
- Les droits DocMDP ne sont pas comparés aux changements (ADR-0208, option B) ; les limites de R-REVISIONSPDF-003 le disent.
- Une signature dont le champ a été retiré du formulaire par une version ultérieure n'est pas vue.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création ; option choisie par TheDarkMac au début de T50 |
