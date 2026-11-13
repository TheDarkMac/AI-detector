# Fiche technique — Éléments Info et Tags d'un WebM

- **Module** : `matroska` (version 0.1.0)
- **Tâche** : T21
- **Exigences** : F-10, ES-13
- **Formats** : `webm`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Que déclare un WebM sur lui-même : bibliothèque de multiplexage (`MuxingApp`) et logiciel d'écriture (`WritingApp`), date, titre, balises globales et par piste (encodeur, durée) ?

## Principe

Un WebM est un document EBML (RFC 8794) de type `webm`, profil de Matroska (RFC 9559). Le module parcourt, par les lecteurs du projet ([ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)), les éléments de premier niveau du segment, en sautant les autres par leur taille ; un `Cluster` de taille inconnue, que produisent les enregistrements en direct et les navigateurs, finit au premier élément de premier niveau qui le suit. Il lit les éléments de texte et la date d'`Info`, puis chaque balise simple (`SimpleTag`) de chaque `Tag`, et sa cible (`Targets`).

## Entrées

| Format | Emplacement lu ([ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md)) |
| --- | --- |
| WebM | `Info` du segment ; chaque `Tags` du segment |

Aucune donnée de référence. Ne sont pas lus : `Tracks` (nom et langue des pistes, codec), `Chapters`, `Attachments` (fichiers joints et leurs noms), `Cues`, `SeekHead`.

## Sorties

Noms d'observation ([ADR-0133](../decisions/ADR-0133-noms-et-valeurs-des-balises-audio-et-video.md)) :

| Nom | Valeur |
| --- | --- |
| `matroska.present` | Vrai si `Info` ou `Tags` a été trouvé ; toujours observé (F-14) |
| `matroska.blocs` | Nombre d'éléments `Info` et `Tags` |
| `matroska.Title`, `matroska.MuxingApp`, `matroska.WritingApp` | Textes d'`Info` : ffmpeg écrit `Lavf…` dans les deux derniers, un navigateur son nom |
| `matroska.SegmentFilename`, `matroska.PrevFilename`, `matroska.NextFilename` | Noms de fichier d'`Info` |
| `matroska.DateUTC` | Date telle qu'écrite, unité « ns depuis 2001-01-01 UTC » |
| `matroska.tag.<NOM>` | Balise simple globale (cible absente ou nulle) |
| `matroska.piste.<NOM>` | Balise qui vise une piste (`TagTrackUID`) : ffmpeg y écrit `ENCODER` et `DURATION` |
| `matroska.cible.<NOM>` | Balise qui vise une édition, un chapitre ou un fichier joint |
| `<nom>.<SOUS-NOM>` | Balise imbriquée, à la suite de sa balise parente |
| `<nom>.taille` | Taille, en octets, d'une balise binaire (`TagBinary`) |

- Nom de balise : casse gardée, règle des composants d'ADR-0117 (`LEAD_PERFORMER` devient `LEAD-PERFORMER`). Textes en UTF-8, nuls de fin retirés.
- Balise sans texte ni binaire : rien n'est observé pour elle, ses balises imbriquées le sont.

Aucun constat.

## Données identifiantes

| Catégorie | Éléments et balises |
| --- | --- |
| `metadonnee_nominative` | Balises officielles qui nomment une personne ou un organisme : `ARTIST`, `LEAD_PERFORMER`, `ACCOMPANIMENT`, `COMPOSER`, `ARRANGER`, `LYRICIST`, `CONDUCTOR`, `DIRECTOR`, `ASSISTANT_DIRECTOR`, `DIRECTOR_OF_PHOTOGRAPHY`, `SOUND_ENGINEER`, `ART_DIRECTOR`, `PRODUCTION_DESIGNER`, `CHOREGRAPHER`, `COSTUME_DESIGNER`, `ACTOR`, `WRITTEN_BY`, `SCREENPLAY_BY`, `EDITED_BY`, `PRODUCER`, `COPRODUCER`, `EXECUTIVE_PRODUCER`, `DISTRIBUTED_BY`, `MASTERED_BY`, `ENCODED_BY`, `MIXED_BY`, `REMIXED_BY`, `PRODUCTION_STUDIO`, `THANKS_TO`, `PUBLISHER`, `LABEL`, `COPYRIGHT`, `PRODUCTION_COPYRIGHT`, quelle que soit leur cible ou leur parent |
| `nom_de_fichier` | `SegmentFilename`, `PrevFilename`, `NextFilename` |

Les autres balises, libres, relèvent de T25 ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Rien |

Le module ne distingue aucune hypothèse et n'émet aucun constat ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)). `MuxingApp` et `WritingApp` sont écrits par le logiciel qui produit le fichier, mais peuvent être réécrits (cas d'abus C-02).

## Ce qui déclenche un constat

Aucun constat en T21. Une absence d'`Info` et de `Tags` est l'observation `matroska.present` à faux (F-14).

## Taux d'erreur

Sans objet : aucun constat. Fidélité de l'extraction vérifiée contre exiftool sur un WebM écrit par ffmpeg ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)).

## Limites connues

- Les balises de plusieurs pistes portent le même nom (`matroska.piste.ENCODER`) : leur localisation est commune à l'élément `Tags`, et rien ne les rattache à leur piste avant que `Tracks` soit lu.
- Langue d'une balise (`TagLanguage`) et type de cible (`TargetTypeValue`) non observés.
- Un élément de taille inconnue autre qu'un `Cluster`, ou un enfant de taille inconnue dans un `Cluster`, arrête le parcours (format partiel).
- Un élément mal formé dans `Info` ou `Tags` arrête la lecture de cet élément (non menée) ; une balise sans nom est non menée.

## Sécurité

- Lecture bornée par le contexte : un `Info` ou un `Tags` de plus de 16 Mio n'est pas lu (format partiel) ; les blocs audio et vidéo sont sautés sans être lus.
- Chaque élément de premier niveau, chaque enfant d'un `Cluster` de taille inconnue, chaque `Tag` et chaque balise simple comptent un objet ; chaque niveau d'imbrication de balises compte un niveau (64 au plus, ADR-0078).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément audio et vidéo) |
