# ADR-0132 — Emplacements lus dans les conteneurs audio et vidéo

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : proposition de l'assistant, validée par TheDarkMac
- **Tâche** : T21 (complément audio et vidéo)
- **Exigences liées** : F-10, F-14, F-25, F-82 ; ADR-0115, ADR-0127, ADR-0131

## Contexte

Chaque conteneur range ses balises à plusieurs endroits, de façon plus ou moins normalisée. Un MP3 peut porter plusieurs balises ID3v2 en tête, une balise ID3v1 en fin, une balise APE ; un WAV, une liste `INFO`, un bloc `bext`, un bloc `iXML`, une balise ID3 ; un MP4, des métadonnées dans `moov`, dans chaque piste (`trak`), dans une boîte `meta` de premier niveau ; un Ogg, un paquet de commentaires par flux, et plusieurs maillons enchaînés ; un WebM, des balises globales, par piste, par chapitre, et des fichiers joints. Comme pour le PDF (ADR-0127), il faut dire ce qui est lu, ce qui ne l'est pas, et pourquoi.

## Options envisagées

### Option A — Les emplacements des normes et ceux qu'écrivent les outils courants, au niveau du fichier

Les emplacements du tableau ci-dessous : ceux que définit la norme de chaque famille, ceux qu'écrivent ffmpeg, les logiciels d'Apple et d'Adobe, et les outils d'étiquetage courants ; les métadonnées propres à une piste ou à un flux secondaire ne sont lues que là où elles portent la seule information du fichier (Ogg, balises Matroska).

- Avantages : ce que voit un lecteur ou un outil d'étiquetage ; chaque emplacement a son lecteur testé et comparé à exiftool ; la lecture reste bornée aux en-têtes, sans parcours des données.
- Inconvénients : les pistes d'un MP4 et d'un MOV (nom de gestionnaire, langue, dates de piste) ne sont pas au rapport.

### Option B — Aussi les pistes et les blocs propres à un fabricant

`trak/udta`, `trak/mdia/hdlr`, dates de `tkhd` et `mdhd`, `iXML`, balise APE, fichiers joints Matroska.

- Avantages : couverture plus large.
- Inconvénients : autant de lecteurs de plus, dont plusieurs sans spécification publique (`iXML` varie selon l'enregistreur, APE est sans norme) ; des observations surtout techniques (nom de gestionnaire « VideoHandler »), qui relèvent de la structure du conteneur (T71, T72) plutôt que des métadonnées déclarées.

## Décision

Option A. Emplacements lus, par format et par module :

| Format | `id3` | `infowav` | `vorbis` | `quicktime` | `matroska` | `xmp` (ADR-0134) |
| --- | --- | --- | --- | --- | --- | --- |
| WAV | Bloc `id3` ou `ID3`, identifiant suivi d'une espace | `LIST` `INFO` ; `bext` | — | — | — | Bloc `_PMX` |
| MP3 | ID3v2 en tête (toutes, consécutives) ; ID3v1 en fin | — | — | — | — | — |
| AAC (ADTS) | ID3v2 en tête | — | — | — | — | — |
| FLAC | ID3v2 en tête | — | Bloc `VORBIS_COMMENT` | — | — | — |
| Ogg | — | — | Paquet de commentaires de chaque flux Vorbis, Opus, Theora, Speex, FLAC du premier maillon | — | — | — |
| M4A, MP4, MOV | — | — | — | Premier `moov` : `mvhd`, `udta`, `meta` | — | `uuid` XMP de premier niveau ; `moov/udta/XMP_` |
| WebM | — | — | — | — | `Info`, `Tags` du segment | — |

- MP3 : ID3v1 lue si les 128 derniers octets de la partie commencent par `TAG` et suivent les balises ID3v2, comme le fait l'identification (ADR-0070), qui compte ces octets dans la partie. AAC et FLAC : pas d'ID3v1, que l'identification ne compte pas.
- Ogg : les paquets d'en-tête précèdent les données dans la correspondance de chaque codec avec Ogg ; le parcours des pages s'arrête dès que chaque flux du premier maillon a donné son second paquet. Le paquet de commentaires est réassemblé sur autant de pages qu'il en occupe (16 Mio au plus).
- ISOBMFF : boîtes de premier niveau parcourues jusqu'à la fin de la partie, `mdat` sauté par sa taille ; `meta` lu dans `moov` (QuickTime, gestionnaire `mdta`) et dans `moov/udta` (iTunes, gestionnaire `mdir`).
- WebM : éléments de premier niveau du segment parcourus un à un ; un `Cluster` de taille inconnue (enregistrement en direct, navigateurs) finit au premier élément de premier niveau qui le suit (RFC 8794, §6.2) ; plusieurs `Tags` sont tous lus.
- Ne sont pas lus, et chaque fiche le dit : pistes `trak` (MP4, MOV), boîte `meta` de premier niveau d'un MP4, `moov` compressé (`cmov`), maillons Ogg après le premier, balise APE, ID3v2 en fin de fichier (pied `3DI` sans en-tête en tête), ID3v1 étendue (`TAG+`), bloc `PICTURE` d'un FLAC, blocs `iXML`, `cart`, `LIST` `adtl` d'un WAV, pistes (`Tracks`), chapitres et fichiers joints d'un WebM, XMP d'une trame ID3 `PRIV`, CRC des pages Ogg (non vérifié).

## Raisons

- Option A : elle répond à F-10 pour ce qu'un fichier déclare de lui-même, comme ADR-0127 pour le PDF ; les emplacements non lus sont rares, propres à un fabricant, ou relèvent de la structure (T71, T72).
- Option B écartée : lecteurs sans norme, observations techniques, coût de relecture.
- Premier `moov` seulement : un second `moov` n'est pas lu par les lecteurs (ISO/CEI 14496-12 n'en permet qu'un) ; le signaler est l'affaire de la structure (T71).
- CRC Ogg non vérifié : il ne change pas ce qui est déclaré ; une page corrompue se lit comme le ferait un outil d'étiquetage. La vérification de l'intégrité est hors de F-10.

## Conséquences

- Chaque fiche liste ses emplacements lus et non lus.
- Une analyse non menée est produite quand l'emplacement existe sans pouvoir être lu : structure tronquée ou incohérente, trame chiffrée, compression inconnue.
- Ajouter un emplacement (piste, `iXML`, APE) demandera un nouvel ADR et une nouvelle version du module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
| 2026-11-13 | Validé par TheDarkMac pendant la revue de la PR du complément : statut « Accepté » |
