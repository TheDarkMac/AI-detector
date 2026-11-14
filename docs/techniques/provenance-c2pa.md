# Fiche technique — Manifeste C2PA

- **Module** : `c2pa` (version 0.1.0)
- **Tâche** : T30
- **Exigences** : F-20, F-21, F-22, F-23, F-90, ES-06, ES-09, ES-10, ES-13, ES-20
- **Formats** : `jpeg`, `png`, `webp`, `heic`, `pdf`, `wav`, `mp3`, `m4a`, `flac`, `mp4`, `mov`, `docx`, `odt`
- **Directions permises** : `origine_ia`, `retouche`, `transformation`, `authenticite`, `rien_de_particulier`
- **Règles** : `R-C2PA-001`, `R-C2PA-002`, `R-C2PA-003`, `R-C2PA-004`, `R-C2PA-005`, `R-C2PA-006`, `R-C2PA-007`, `R-C2PA-008`, `R-C2PA-009`, `R-C2PA-010`, `R-C2PA-011`, `R-C2PA-012`
- **Bibliothèques** : `c2pa-python`

## Question

Le fichier porte-t-il un manifeste C2PA, sa signature, l'empreinte du contenu signé et la chaîne de certificats se vérifient-elles, le signataire est-il reconnu par la liste de confiance employée, et que déclare le manifeste ?

## Principe

Un manifeste C2PA (« Content Credentials ») est une structure JUMBF signée, intégrée au fichier ou désignée par une adresse, qui déclare l'origine et les transformations du contenu : outil d'origine, actions (création, retouche, ouverture d'un ingrédient), source numérique au vocabulaire de l'IPTC, ingrédients. La revendication du manifeste est signée (COSE) par un certificat X.509 ; elle porte l'empreinte du contenu, si bien que tout octet changé depuis la signature se voit.

Le module confie la lecture et la vérification à l'implémentation de référence de la C2PA, c2pa-rs, par sa liaison Python `c2pa-python` ([ADR-0164](../decisions/ADR-0164-bibliotheque-c2pa.md)). `c2pa-python` 0.39.0 embarque c2pa-rs 0.92.0, qui suit la spécification C2PA 2.4 (champ `specVersion` de ses résultats) ; un test vérifie le couple de versions. La vérification porte sur la signature de la revendication, les empreintes des assertions et du contenu, la chaîne de certificats jusqu'à une ancre de la liste de confiance, la validité du certificat à la date de la signature horodatée ou, à défaut, à la date de l'analyse, et une réponse OCSP jointe au manifeste s'il y en a une.

La liste de confiance est remise par le processus principal, qui l'a validée ([ADR-0171](../decisions/ADR-0171-liste-de-confiance-au-rapport.md)) : par défaut, celle livrée avec l'outil, la C2PA Trust List et la C2PA TSA Trust List, séquence 4 du 2026-11-04 ([ADR-0165](../decisions/ADR-0165-liste-de-confiance-livree.md)) ; ou celle de l'utilisateur, par `--confiance DOSSIER`, que le rapport signale. Les ancres des signataires et celles des autorités d'horodatage sont remises séparément à c2pa-rs : une autorité d'horodatage ne rend pas un signataire reconnu.

## Entrées

| Format | Type remis à c2pa-rs | Emplacement constaté sur les échantillons signés par les tests |
| --- | --- | --- |
| JPEG | `image/jpeg` | Segment APP11 (JUMBF) |
| PNG | `image/png` | Bloc `caBX` |
| WebP | `image/webp` | Bloc `C2PA` du conteneur RIFF |
| WAV | `audio/wav` | Bloc `C2PA` du conteneur RIFF |
| HEIC, M4A, MP4, MOV | `image/heic`, `audio/mp4`, `video/mp4`, `video/quicktime` | Boîte `uuid` de type `manifest` |
| MP3, FLAC | `audio/mpeg`, `audio/flac` | Cadre ID3 `GEOB` de type `application/c2pa` (balise ID3 en tête pour le FLAC) |
| PDF | `application/pdf` | Fichier associé (`/AF`) de sous-type `application/c2pa` |
| DOCX, ODT | Types OOXML et ODF | Entrée `META-INF/content_credential.c2pa` de l'archive |

Dans tous les formats, une adresse `dcterms:provenance` du XMP désigne un manifeste distant ; c2pa-rs la lit mais ne la suit pas (§ Sécurité). Le module ne lit pas lui-même ces structures : c2pa-rs les cherche. AAC, Ogg, WebM et le texte ne sont pas dans le manifeste du module : c2pa-rs 0.92.0 ne les prend pas en charge (essai sur les échantillons du dépôt : `NotSupported` pour Ogg et WebM).

## Sorties

Noms tirés de la sortie JSON de c2pa-rs, comme les modules de métadonnées tirent les leurs des normes ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md), [ADR-0169](../decisions/ADR-0169-etats-et-observations-c2pa.md)).

| Observation | Valeur | Quand |
| --- | --- | --- |
| `c2pa.present` | Booléen | Toujours, sauf conteneur illisible |
| `c2pa.etat` | `absent`, `valide`, `valide_hors_liste`, `invalide`, `non_verifiable` (F-22) | Idem |
| `c2pa.erreur` | Genre d'erreur de c2pa-rs (`Remote`, `Verify`, `Decoding`…) | État non vérifiable |
| `c2pa.distant.hote` | Hôte du manifeste distant, jamais l'adresse entière | Manifeste distant |
| `c2pa.manifestes` | Nombre de manifestes du magasin | Manifeste lu |
| `c2pa.validation_results.failure` | Codes d'échec de la C2PA pour le manifeste actif (liste, vide si aucun) | Idem |
| `c2pa.validation_results.informational` | Codes d'information (liste) ; `signingCredential.ocsp.skipped` sans réponse OCSP jointe | Idem |
| `c2pa.signature_info.alg`, `.issuer`, `.common_name`, `.cert_serial_number`, `.time` | Algorithme, organisation, nom commun et numéro du certificat, date de l'horodatage | Champs présents |
| `c2pa.claim_generator_info` | Outil d'origine, nom et version (liste) ; `claim_generator` d'un manifeste de la version 1 | Idem |
| `c2pa.title` | Titre du manifeste | Idem |
| `c2pa.actions.action`, `.softwareAgent`, `.digitalSourceType` | Actions des assertions `c2pa.actions` du manifeste actif, logiciels, sources numériques IPTC (listes) | Idem |
| `c2pa.ingredients` | Nombre d'ingrédients du manifeste actif | Manifeste lu |
| `c2pa.ingredients.title`, `.relationship` | Titres et relations (`parentOf`, `componentOf`…) des ingrédients | Idem |
| `c2pa.ingredients.validationDeltas.failure` | Codes d'échec des manifestes des ingrédients | S'il y en a |

Une valeur trop longue est coupée et sa longueur observée sous `<nom>.longueur` (ADR-0118). Un conteneur que c2pa-rs ne sait pas lire (« asset could not be parsed ») ne dit rien d'un manifeste : la recherche est non menée, raison `format_partiel`, sans observation. Un manifeste distant rend la recherche partielle, raison `reseau_desactive`.

## Données identifiantes

| Catégorie | Champs |
| --- | --- |
| `metadonnee_nominative` | `c2pa.signature_info.common_name` : le nom commun d'un certificat peut nommer une personne |
| `numero_de_serie` | `c2pa.signature_info.cert_serial_number` : un appareil peut signer sous un certificat qui lui est propre |
| `texte_libre` | `c2pa.title`, `c2pa.ingredients.title` |

L'organisation du certificat (`issuer`) n'est pas marquée : elle nomme l'organisme qui a obtenu le certificat, comme `Make` en EXIF. Le contrôle avant publication compte ces champs avec ceux des métadonnées ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)) ; l'outil ne retire pas le manifeste.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Un appareil qui signe déclare `digitalCapture` ou `computationalCapture` ; sous un signataire reconnu, c'est une preuve de ce qui a été signé, pas de la scène (R-C2PA-003) |
| Transformation banale (recompression, redimensionnement) | Un outil qui ne connaît pas la C2PA efface en général le manifeste (état absent, neutre) ; un outil qui le garde sans le mettre à jour rend l'empreinte fausse (R-C2PA-006, indice faible) |
| Retouche | Un outil conforme ajoute un manifeste dont l'ingrédient est l'original ; une retouche par IA déclarée donne R-C2PA-002 ou R-C2PA-005 |
| Génération | Un générateur conforme déclare `trainedAlgorithmicMedia` : preuve de la déclaration sous un signataire reconnu (R-C2PA-001), indice faible sinon (R-C2PA-004) |

La technique ne distingue rien hors de ce que le manifeste déclare : elle ne remplace pas l'analyse du contenu, et un manifeste absent ne compte ni pour ni contre (F-14).

## Ce qui déclenche un constat

Toutes les règles sont appliquées par le module ([ADR-0170](../decisions/ADR-0170-regles-du-module-c2pa.md)) ; une phrase d'état par manifeste, et au plus une règle par famille de source numérique.

| Règle | Catégorie, direction | Quand |
| --- | --- | --- |
| R-C2PA-007 | Information neutre | État valide : signature, empreintes et chaîne vérifiées, signataire reconnu |
| R-C2PA-008 | Information neutre | Valide, signataire hors de la liste de confiance |
| R-C2PA-009 | Information neutre | Invalide, avec les codes d'échec |
| R-C2PA-010 | Information neutre | Non vérifiable, avec le genre d'erreur |
| R-C2PA-011 | Information neutre | Manifeste distant, non récupéré, hôte nommé |
| R-C2PA-012 | Information neutre | Aucun manifeste |
| R-C2PA-001 | Preuve, origine IA | Valide, reconnu, `trainedAlgorithmicMedia` déclaré |
| R-C2PA-002 | Preuve, retouche | Valide, reconnu, `compositeWithTrainedAlgorithmicMedia` ou `compositeSynthetic` |
| R-C2PA-003 | Preuve, authenticité | Valide, reconnu, `digitalCapture` ou `computationalCapture` ([ADR-0168](../decisions/ADR-0168-capture-declaree-signataire-reconnu.md)) |
| R-C2PA-004 | Indice faible, origine IA | Hors liste ou invalide, `trainedAlgorithmicMedia` déclaré |
| R-C2PA-005 | Indice faible, retouche | Hors liste ou invalide, retouche par IA déclarée |
| R-C2PA-006 | Indice faible, transformation | Invalide par un écart d'empreinte ([ADR-0167](../decisions/ADR-0167-manifeste-invalide.md)) |

Les codes IPTC sont reconnus avec ou sans l'adresse du vocabulaire, en `http` ou `https`, sans égard à la casse ([ADR-0143](../decisions/ADR-0143-valeurs-iptc-de-la-source-numerique.md)).

## Taux d'erreur

Sans objet : la vérification est déterministe, juste ou fausse (A-55). Elle est vérifiée par des tests de conformité, sur des fichiers signés pendant les tests par une autorité d'essai, dans les treize formats du module : signataire reconnu ou non, contenu changé, manifeste mal formé, manifeste distant, ingrédient, conteneur illisible (`tests/test_c2pa.py`). Aucune règle n'est évaluée par le banc : leur niveau reste celui fixé par le catalogue.

## Limites connues

- Une preuve n'établit que la signature et l'intégrité : un signataire reconnu peut déclarer faux, un appareil compromis signer une mise en scène (ADR-0021).
- La reconnaissance dépend de la liste employée, à sa version : la liste intérimaire du CAI, figée au 2026-01-01, n'est pas livrée ; un signataire qu'elle seule reconnaît est « hors liste » ([ADR-0165](../decisions/ADR-0165-liste-de-confiance-livree.md)).
- Révocation non vérifiée en ligne, manifestes distants jamais récupérés en V1 ([ADR-0166](../decisions/ADR-0166-requetes-en-ligne-hors-de-t30.md)) : seule une réponse OCSP jointe au manifeste est lue.
- Sans horodatage, la validité du certificat est jugée à la date de l'analyse : le même fichier peut passer de valide à invalide quand le certificat expire. La date de l'analyse est au rapport.
- Un certificat mal formé de la liste est ignoré par c2pa-rs, sans erreur : un signataire qu'il devait reconnaître est « hors liste » (ADR-0171).
- Seul le manifeste actif fonde les règles ; les manifestes des ingrédients ne sont restitués que par leurs titres, relations et codes d'échec.
- Les assertions d'identité du CAWG ne sont pas décodées ; les vignettes ne sont pas extraites.
- Les observations d'actions sont des listes : elles ne disent pas quelle source numérique va avec quelle action.
- Le module ne lit pas le XMP : l'adresse d'un manifeste distant est restituée par le module `xmp` (`xmp.dcterms:provenance`), non masquée.

## Sécurité

- c2pa-rs, en Rust, lit le fichier dans le processus de travail isolé (ADR-0035), par un flux en lecture seule aux positions explicites, au plus 16 Mio par lecture ; ni fichier temporaire ni disque. La bibliothèque native est chargée à l'import, avant les restrictions ; son coût, environ 0,15 s par processus de travail, est mesuré dans ADR-0164.
- Aucune requête : `remote_manifest_fetch` et `ocsp_fetch` à faux, liste des hôtes permis vide (`allowed_network_hosts`), en plus du blocage du réseau par le système sous Linux et macOS ; sous Windows, où le réseau n'est pas bloqué (ADR-0081), ces deux réglages sont la seule barrière (ADR-0164).
- Les limites comptées du moteur ne voient pas le travail de c2pa-rs : il est borné par ses propres limites (manifeste décompressé de 32 Mio au plus) et par la mémoire et le temps du processus de travail (ADR-0077).
- Le message d'une erreur de c2pa-rs n'est jamais repris, seul son genre : il peut citer le fichier. L'hôte d'un manifeste distant n'est retenu que s'il ne contient que des lettres minuscules, des chiffres, des points et des tirets.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-14 | 0.1.0 | Création (T30) |
