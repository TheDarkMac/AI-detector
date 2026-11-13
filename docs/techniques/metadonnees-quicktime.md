# Fiche technique — Métadonnées QuickTime et ISOBMFF

- **Module** : `quicktime` (version 0.2.0)
- **Tâche** : T21, T22, T23
- **Exigences** : F-10, F-12, ES-13
- **Formats** : `m4a`, `mp4`, `mov`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Que déclare la boîte `moov` d'un M4A, d'un MP4 ou d'un MOV : dates de création et de modification, logiciel d'encodage, titre, interprètes, position, clés QuickTime (marque, modèle, logiciel de l'appareil) ?

## Principe

Le module parcourt les boîtes du fichier (ISO/CEI 14496-12 ; Apple, QuickTime File Format) par le lecteur du projet ([ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)), sans lire les données (`mdat`). Dans le premier `moov`, il lit :

- `mvhd` : dates de création et de modification ;
- `udta` : textes QuickTime `©xxx` (longueur, langue, texte, répétés), boîtes de texte ISO et 3GPP (`cprt`, `titl`, `dscp`, `perf`, `auth`, `gnre`), autres boîtes par leur taille ;
- `meta`, dans `moov` ou dans `moov/udta` : gestionnaire (`hdlr`), clés (`keys`, gestionnaire `mdta`), liste `ilst`, dont chaque élément porte une ou plusieurs boîtes `data` typées.

## Entrées

| Format | Emplacement lu ([ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md)) |
| --- | --- |
| M4A, MP4, MOV | Premier `moov` : `mvhd`, `udta`, `meta` ; `meta` de `moov/udta` |

Aucune donnée de référence. Ne sont pas lus : pistes (`trak` : `tkhd`, `mdhd`, `hdlr`, `udta`), boîte `meta` de premier niveau, `moov` compressé (`cmov`), second `moov`. Le XMP (`uuid`, `XMP_`) est lu par `xmp`.

## Sorties

Noms d'observation ([ADR-0133](../decisions/ADR-0133-noms-et-valeurs-des-balises-audio-et-video.md)) :

| Nom | Valeur |
| --- | --- |
| `quicktime.present` | Vrai si `moov` porte `udta` ou `meta` ; toujours observé (F-14) |
| `quicktime.blocs` | Nombre de boîtes `udta` et `meta` de `moov` |
| `quicktime.mvhd.CreationTime`, `quicktime.mvhd.ModificationTime` | Dates de `mvhd`, telles qu'écrites, unité « s depuis 1904-01-01 UTC » ; 0 : non renseignée |
| `quicktime.udta.<code>` | Texte d'une boîte de `udta` ; liste s'il y en a plusieurs |
| `quicktime.ilst.<code>` | Valeur d'un élément d'`ilst` (gestionnaire `mdir`) : texte, entier ou réel ; liste s'il y en a plusieurs |
| `quicktime.ilst.----.<domaine>.<nom>` | Élément libre (`mean`, `name`), par exemple `----.com-apple-iTunes.iTunSMPB` |
| `quicktime.mdta.<clé>` | Valeur d'une clé QuickTime (gestionnaire `mdta`) |
| `<nom>.taille` | Taille, en octets, d'une donnée binaire : pochette (`covr`), type implicite (`trkn`, `disk`), boîte inconnue de `udta` |

- Code : `©` (0xA9) y devient un tiret (ADR-0117). Codes usuels : `-nam` titre, `-ART` artiste, `-too` encodeur (ffmpeg y écrit `Lavf…`), `-swr` logiciel (MOV), `-day` date, `-xyz` position ISO 6709, `-cmt` commentaire, `cprt` droits. Clés usuelles : `com-apple-quicktime-make`, `-model`, `-software`, `-creationdate`, `-location-ISO6709`.
- Types de données d'`ilst` : 1 et 4 UTF-8, 2 et 5 UTF-16BE, 3 Shift_JIS, 21 entier signé, 22 entier non signé (et les types 65 à 78), 23 et 24 réels ; image et type implicite par leur taille. Texte QuickTime de `udta` : Mac Roman pour un code de langue Macintosh (inférieur à 0x400), UTF-8 ou UTF-16 sinon.
- Un entier hors des 64 bits signés du modèle est observé en texte décimal (ADR-0118).

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Codes et clés |
| --- | --- |
| `metadonnee_nominative` | `©ART`, `aART`, `©aut`, `©wrt`, `©com`, `©cpy`, `©dir`, `©prd`, `©PRD`, `©prf`, `©ope`, `©own`, `©enc`, `©pub`, `cprt`, `ownr`, `apID` (compte iTunes), `auth`, `perf` ; clés `com.apple.quicktime.artist`, `author`, `copyright`, `director`, `producer`, `publisher` |
| `gps` | `©xyz`, `loci` ; clé `com.apple.quicktime.location.ISO6709` |

Marque, modèle et logiciel de l'appareil ne sont pas marqués ; le nom d'un lieu (`com.apple.quicktime.location.name`) relève de T25 ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `©too` ou `©swr` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. Un encodeur ou des clés d'appareil sont des déclarations que quiconque peut écrire ou effacer (cas d'abus C-02).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-QUICKTIME-001` Générateur nommé par l'encodeur d'un MP4 ou d'un M4A ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `quicktime.ilst.-too` | liste des générateurs (ADR-0144) | origine IA |
| `R-QUICKTIME-002` Générateur nommé par le logiciel d'un MOV ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `quicktime.udta.-swr` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-QUICKTIME-003` Création postérieure à la modification (mvhd) | `quicktime.mvhd.CreationTime`, `quicktime.mvhd.ModificationTime` | certainement postérieure à `quicktime.mvhd.ModificationTime`, lues par `date-1904` |
| `R-QUICKTIME-004` Aucune balise QuickTime (udta, meta) | `quicktime.present` | faux |

Une absence de `udta` et de `meta` est l'observation `quicktime.present` à faux ; la règle `R-QUICKTIME-004` en fait une information neutre, jamais un indice (F-14) ; les dates de `mvhd` restent observées.

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool sur un M4A, un MP4 et un MOV écrits par ffmpeg ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

## Limites connues

- Métadonnées des pistes non lues : un nom de piste ou une date de `tkhd` ne sont pas au rapport (T71, T72).
- Une boîte mal formée de `udta`, `meta` ou `ilst` arrête la lecture de son bloc (non menée) ; dans `udta`, elle arrête aussi le parcours du conteneur, que fait le relevé pour y chercher `XMP_` (ADR-0134).
- Un élément d'`ilst` dont la clé n'est pas dans `keys` est non mené.
- La langue des boîtes `data` et des textes de `udta` n'est pas observée ; Mac Roman est appliqué à tous les codes de langue Macintosh, quelle que soit l'écriture de la langue.
- Les boîtes 3GPP autres que les textes (`loci`, `kywd`, `albm`, `yrrc`, `rtng`, `clsf`) sont observées par leur taille.

## Sécurité

- Lecture bornée par le contexte : un `udta` ou un `meta` de plus de 16 Mio n'est pas lu (format partiel) ; `mdat` est sauté sans être lu.
- Chaque boîte parcourue compte un objet (ADR-0078).
- Les codecs UTF-16BE, Mac Roman et Shift_JIS sont chargés à l'import, avant les restrictions du processus de travail (ADR-0079, ERR-0009).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément audio et vidéo) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
