# ADR-0160 — Champs marqués « lieu » et « texte libre », par module

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T25, validée pendant la revue de la PR de T25
- **Tâche** : T25
- **Exigences liées** : F-90, ES-13 ; ADR-0057, ADR-0117, ADR-0119, ADR-0133, ADR-0140, ADR-0159

## Contexte

ADR-0159 crée les catégories `lieu` et `texte_libre`. Comme pour les cinq autres (ADR-0057), c'est le module qui lit le champ qui le marque. Il fallait la liste des champs, format par format.

## Options envisagées

### Option A — Liste fermée par famille, champs que la norme définit comme lieu ou texte écrit par une personne

- Avantages : même méthode qu'ADR-0119 ; liste vérifiable ligne à ligne dans la fiche, testée par catégorie.
- Inconvénients : un champ hors norme (une trame `TXXX` inconnue est marquée, mais un bloc texte PNG d'un mot-clé inconnu ne l'est pas) peut contenir un nom.

### Option B — Tout texte non technique

Marquer tout texte qui n'est ni une date, ni un nombre, ni un logiciel, ni un appareil.

- Avantages : moins d'oublis.
- Inconvénients : il faudrait dire, champ par champ, ce qui est technique : la même liste à l'envers, plus longue, et un rapport presque tout masqué (ADR-0119, option B).

## Décision

Option A. Champs marqués :

| Module | `lieu` | `texte_libre` |
| --- | --- | --- |
| `exif` | — (le répertoire GPS reste `gps`) | `ImageDescription`, `PageName`, `XPTitle`, `XPComment`, `XPKeywords`, `XPSubject`, `UserComment`, `ImageTitle` |
| `xmp` | `photoshop:City`, `photoshop:State`, `photoshop:Country`, `Iptc4xmpCore:Location`, `Iptc4xmpCore:CountryCode`, `Iptc4xmpExt:City`, `Iptc4xmpExt:ProvinceState`, `Iptc4xmpExt:CountryName`, `Iptc4xmpExt:CountryCode`, `Iptc4xmpExt:Sublocation`, `Iptc4xmpExt:WorldRegion`, `Iptc4xmpExt:LocationName`, `xmpDM:shotLocation` | `dc:title`, `dc:description`, `dc:subject`, `photoshop:Headline`, `photoshop:Instructions`, `Iptc4xmpCore:AltTextAccessibility`, `Iptc4xmpCore:ExtDescrAccessibility`, `Iptc4xmpExt:Event`, `Iptc4xmpExt:AOTitle`, `exif:UserComment`, `tiff:ImageDescription`, `pdf:Keywords`, `lr:hierarchicalSubject`, `mwg-rs:Description`, `xmpDM:album`, `xmpDM:logComment` |
| `iptc` | `ContentLocationCode`, `ContentLocationName`, `City`, `Sub-location`, `Province-State`, `Country-PrimaryLocationCode`, `Country-PrimaryLocationName` | `ObjectName`, `Keywords`, `SpecialInstructions` (sauf FBMD, ADR-0161), `Headline`, `Caption-Abstract`, `LocalCaption` |
| `textepng` | — | `Title`, `Description`, `Comment`, `parameters` |
| `infopdf` | — | `Title`, `Subject`, `Keywords` |
| `id3` | — | `TIT1`, `TIT2`, `TIT3`, `TALB`, `TOAL`, `TSST`, `TXXX`, `COMM`, `USLT` et leurs équivalents v2.2 ; ID3v1 `Title`, `Album`, `Comment` |
| `infowav` | `IARL` | `INAM`, `ICMT`, `ISBJ`, `IKEY`, `IPRD` ; `bext` `Description` |
| `vorbis` | `LOCATION` | `TITLE`, `SUBTITLE`, `ALBUM`, `DESCRIPTION`, `COMMENT`, `LYRICS`, `UNSYNCEDLYRICS` |
| `quicktime` | clés `com.apple.quicktime.location.name`, `.location.body` | `©nam`, `©alb`, `©cmt`, `©des`, `©inf`, `©lyr`, `desc`, `ldes`, `titl`, `dscp`, `kywd` ; clés `title`, `album`, `comment`, `description`, `information`, `keywords`, `location.note` |
| `matroska` | `RECORDING_LOCATION`, `COMPOSITION_LOCATION` | `Title` d'`Info` ; `TITLE`, `SUBTITLE`, `DESCRIPTION`, `SYNOPSIS`, `SUMMARY`, `COMMENT`, `KEYWORDS`, `LYRICS` |
| `ooxml` | — | `dc:title`, `dc:subject`, `dc:description`, `cp:keywords`, `cp:category`, `TitlesOfParts` ; toutes les propriétés personnalisées |
| `odf` | — | `dc:title`, `dc:subject`, `dc:description`, `meta:keyword` ; toutes les propriétés utilisateur |

- XMP : règle du premier composant identifiant (ADR-0119). Dans `Iptc4xmpExt:LocationCreated` ou `LocationShown`, qui ne sont pas listés, chaque champ garde sa catégorie : la ville est un lieu, la latitude reste GPS.
- Propriétés personnalisées d'un DOCX et propriétés utilisateur d'un ODT : toutes, quel que soit leur type ; leur nom comme leur contenu sont choisis par l'auteur ou son organisation (étiquettes de classification, adresses, noms de clients).
- `parameters` d'un PNG : les interfaces de Stable Diffusion y écrivent l'invite, texte écrit par une personne ; `UserComment` d'EXIF, qui peut porter les mêmes paramètres, est marqué au même titre.
- `ContentLocationCode`, `CountryCode` : un code de pays désigne un lieu comme son nom.

## Raisons

- Option A : elle suit ADR-0057 et ADR-0119, et chaque ligne se vérifie dans la norme du format.
- Option B écartée : elle renverse la liste sans la raccourcir et masque presque tout.
- Titres et albums marqués : un titre d'enregistrement ou de document est écrit par une personne et peut nommer un lieu, une réunion, un interlocuteur.
- `photoshop:Instructions` marqué texte libre sans exception FBMD : la source d'ADR-0153 ne décrit la marque de Facebook que dans le jeu IPTC-IIM.
- Champs non marqués : genre, langue, classement, catégories IPTC codées, `xmp:Label`, `OriginalTransmissionReference` (référence de travail), `Source` d'IPTC ; aucun n'est un texte libre au sens retenu. `Organization` de Vorbis et `Source` d'IPTC nomment un organisme : leur marquage nominatif relève d'une révision d'ADR-0119, non de cet ADR.

## Conséquences

- Les tests de chaque module vérifient ses champs `lieu` et `texte_libre` (`tests/test_controle_publication.py` et les tests de métadonnées existants).
- Un mot-clé PNG ou une balise Matroska hors liste n'est pas marqué ; la fiche le dit.
- Les règles des catalogues 0.2.0 à 0.4.0 qui lisent un texte libre (`UserComment`, `parameters`, `SpecialInstructions`) se déclenchent comme avant : le masquage s'applique à l'export, pas à l'évaluation, et aucune de leurs phrases ne cite ce texte.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T25 (« Oui, les deux ») : statut « Accepté » |
