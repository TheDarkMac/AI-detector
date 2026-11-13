# Fiche technique — Liste INFO et bloc bext d'un WAV

- **Module** : `infowav` (version 0.1.0)
- **Tâche** : T21
- **Exigences** : F-10, ES-13
- **Formats** : `wav`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Que déclarent la liste `INFO` d'un WAV (titre, logiciel `ISFT`, date `ICRD`, commentaire) et, pour un WAV de diffusion, son bloc `bext` (description, auteur, date, historique de codage) ?

## Principe

Le module parcourt les blocs RIFF du WAV (Microsoft, « Multimedia Programming Interface and Data Specifications », 1991) par le lecteur du projet ([ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)), sans lire les données audio. D'une liste `LIST` de type `INFO`, il lit chaque sous-bloc : identifiant de quatre lettres, longueur, texte terminé par un nul. Du bloc `bext` (EBU Tech 3285), il lit les champs de taille fixe, la référence temporelle, la version, l'UMID et l'historique de codage.

## Entrées

| Format | Emplacement lu ([ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md)) |
| --- | --- |
| WAV | Chaque `LIST` de type `INFO` ; chaque bloc `bext` |

Aucune donnée de référence. Ne sont pas lus : `iXML`, `cart`, `LIST` d'autres types (`adtl`), données audio. Le bloc `id3` est lu par `id3`, le bloc `_PMX` par `xmp`.

## Sorties

Noms d'observation ([ADR-0133](../decisions/ADR-0133-noms-et-valeurs-des-balises-audio-et-video.md)) :

| Nom | Valeur |
| --- | --- |
| `infowav.present` | Vrai si une liste `INFO` ou un bloc `bext` a été trouvé ; toujours observé (F-14) |
| `infowav.blocs` | Nombre de listes `INFO` et de blocs `bext` |
| `infowav.<identifiant>` | Texte d'un sous-bloc `INFO` : `INAM` titre, `IART` artiste, `ICMT` commentaire, `ICRD` date de création, `ISFT` logiciel, `ICOP` droits, `IENG` ingénieur… |
| `infowav.bext.Description`, `.Originator`, `.OriginatorReference`, `.OriginationDate`, `.OriginationTime`, `.CodingHistory` | Textes du bloc `bext`, sans les nuls de remplissage |
| `infowav.bext.TimeReference` | Premier échantillon depuis minuit, unité « échantillons » |
| `infowav.bext.Version` | Version du bloc |
| `infowav.bext.UMID` | UMID en hexadécimal, sans les nuls de fin (version 1 et suivantes, s'il n'est pas nul) |

- Textes : UTF-8 s'ils sont valides, Latin-1 sinon, la spécification ne fixant pas l'encodage ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)). Texte vide : rien n'est observé.
- Dates telles qu'écrites (`ICRD`, `OriginationDate` `AAAA-MM-JJ`, `OriginationTime` `HH:MM:SS`) ; T23 les interprétera.

Aucun constat.

## Données identifiantes

| Catégorie | Champs |
| --- | --- |
| `metadonnee_nominative` | `IART`, `ICMS`, `ICOP`, `IENG`, `ITCH`, `IMUS`, `IPRO`, `ISTR`, `IWRI`, `IEDT` ; `bext` `Originator` |
| `numero_de_serie` | `bext` `OriginatorReference` et `UMID`, dont la forme normalisée porte le numéro de série de l'enregistreur (EBU R 99, SMPTE 330M) |

`ICMT`, `INAM` et `Description` ne sont pas marqués : textes libres, relevant de T25 ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Rien |

Le module ne distingue aucune hypothèse et n'émet aucun constat ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)). Un `ISFT` ou un historique de codage sont des déclarations que quiconque peut écrire (cas d'abus C-02).

## Ce qui déclenche un constat

Aucun constat en T21. Une absence de liste et de bloc est l'observation `infowav.present` à faux (F-14).

## Taux d'erreur

Sans objet : aucun constat. Fidélité de l'extraction vérifiée contre exiftool sur un WAV écrit par ffmpeg, liste `INFO` et bloc `bext` ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)). Écarts connus : exiftool lit les textes `INFO` en Latin-1 (« Titre accentuÃ© » pour un titre écrit en UTF-8 par ffmpeg), et joint `OriginationDate` et `OriginationTime` en une seule date.

## Limites connues

- Les champs d'intensité sonore de la version 2 du bloc `bext` ne sont pas observés.
- Un sous-bloc `INFO` qui déborde de sa liste arrête la lecture de la liste (non menée) ; les sous-blocs lus avant restent observés.
- Un WAV RF64 (taille sur 64 bits) n'est pas reconnu comme WAV par l'identification.
- Un même identifiant répété donne deux observations du même nom.

## Sécurité

- Lecture bornée par le contexte : un bloc de plus de 16 Mio n'est pas lu (format partiel) ; les données audio sont sautées sans être lues.
- Chaque bloc RIFF et chaque sous-bloc `INFO` comptent un objet (ADR-0078).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément audio et vidéo) |
