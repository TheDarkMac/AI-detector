# Fiche technique — Commentaires Vorbis

- **Module** : `vorbis` (version 0.2.0)
- **Tâche** : T21, T22, T23
- **Exigences** : F-10, F-12, ES-13
- **Formats** : `flac`, `ogg`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Que déclarent les commentaires Vorbis d'un FLAC ou d'un Ogg : bibliothèque d'encodage (chaîne du fournisseur), titre, interprètes, encodeur, date, champs libres ?

## Principe

Les commentaires Vorbis (Vorbis I, §5) sont une chaîne du fournisseur suivie de champs `NOM=valeur` en UTF-8, chacun précédé de sa longueur. Le module les trouve par le lecteur du projet ([ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)) : dans un FLAC, le bloc de métadonnées `VORBIS_COMMENT` (RFC 9639) ; dans un Ogg (RFC 3533), le paquet de commentaires de chaque flux, réassemblé page après page. Aucun son n'est décodé.

## Entrées

| Format | Emplacement lu ([ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md)) |
| --- | --- |
| FLAC | Chaque bloc `VORBIS_COMMENT`, après d'éventuelles balises ID3v2 |
| Ogg | Second paquet de chaque flux Vorbis (`\x03vorbis`), Opus (`OpusTags`), Theora (`\x81theora`), Speex, FLAC (bloc `VORBIS_COMMENT`) du premier maillon |

Aucune donnée de référence. Ne sont pas lus : bloc `PICTURE` d'un FLAC, flux d'un autre codec (Skeleton…), maillons Ogg après le premier.

## Sorties

Noms d'observation ([ADR-0133](../decisions/ADR-0133-noms-et-valeurs-des-balises-audio-et-video.md)) :

| Nom | Valeur |
| --- | --- |
| `vorbis.present` | Vrai si un bloc ou paquet de commentaires a été trouvé ; toujours observé (F-14) |
| `vorbis.blocs` | Nombre de blocs ou paquets de commentaires |
| `vorbis.vendor` | Chaîne du fournisseur : `reference libvorbis…`, `Lavf61.7.100`… |
| `vorbis.<NOM>` | Valeur d'un champ, le nom en majuscules ; liste si le champ est répété |
| `vorbis.METADATA-BLOCK-PICTURE.taille`, `vorbis.COVERART.taille` | Taille, en octets, d'une image codée en base 64 |

- Champs usuels : `TITLE`, `ARTIST`, `ALBUM`, `DATE`, `ENCODER` (ffmpeg y écrit `Lavc…` et le nom du codec), `COMMENT`, `DESCRIPTION`. Le nom passe par la règle des composants d'ADR-0117 (`METADATA_BLOCK_PICTURE` devient `METADATA-BLOCK-PICTURE`).
- Valeurs en UTF-8, caractère de remplacement pour un octet invalide ; date telle qu'écrite.
- Chaque flux d'un Ogg donne ses propres observations ; leur localisation (« flux 0000abcd / commentaires ») les distingue.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Champs |
| --- | --- |
| `metadonnee_nominative` | `ARTIST`, `ALBUMARTIST`, `ALBUM ARTIST`, `PERFORMER`, `COMPOSER`, `LYRICIST`, `CONDUCTOR`, `ARRANGER`, `REMIXER`, `PRODUCER`, `AUTHOR`, `WRITER`, `PUBLISHER`, `COPYRIGHT`, `CONTACT`, `ENCODED-BY`, `ENCODEDBY` |

Les autres champs, libres, relèvent de T25 ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `ENCODER` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. La chaîne du fournisseur est écrite par la bibliothèque d'encodage, mais peut être réécrite (cas d'abus C-02).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-VORBIS-001` Générateur nommé par le champ Vorbis de l'encodeur ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `vorbis.ENCODER` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-VORBIS-002` Aucun commentaire Vorbis | `vorbis.present` | faux |

Une absence de commentaires est l'observation `vorbis.present` à faux ; la règle `R-VORBIS-002` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool sur un FLAC, un Ogg Vorbis et un Ogg Opus écrits par ffmpeg ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

## Limites connues

- Un champ sans `=` ou sans nom n'est pas observé ; une longueur qui déborde arrête la lecture du bloc. Le bloc est alors non mené, une fois ; les champs lus avant restent observés.
- Le CRC des pages Ogg n'est pas vérifié.
- Un paquet de commentaires de plus de 16 Mio n'est pas lu (format partiel).
- Deux flux d'un même Ogg qui portent le même champ donnent deux observations du même nom.

## Sécurité

- Lecture bornée par le contexte ; les pages audio ne sont parcourues que jusqu'au dernier paquet de commentaires attendu.
- Chaque page Ogg, chaque bloc FLAC et chaque champ comptent un objet (ADR-0078).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément audio et vidéo) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
