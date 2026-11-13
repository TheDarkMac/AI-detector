# ADR-0131 — Un module par famille de balises ; lecteurs de structure écrits par le projet

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac pour le découpage en modules, parmi les options proposées par l'assistant ; lecteurs écrits par le projet en application d'ADR-0043
- **Tâche** : T21 (complément audio et vidéo)
- **Exigences liées** : F-10, F-25, F-82, NF-03, NF-10, ES-18, ES-19 ; ADR-0043, ADR-0114

## Contexte

ADR-0114 a fait des métadonnées d'image un module par famille, avec des lecteurs de structure communs (`modules/_lecture/`), et annoncé pour T21 « ses propres modules pour […] les balises audio et vidéo ». Il restait à dire combien de modules, et qui lit les structures. Une même famille se trouve dans plusieurs conteneurs (ID3 en tête d'un MP3, d'un AAC, d'un FLAC, dans un bloc d'un WAV ; commentaires Vorbis dans un FLAC et dans un Ogg), et un même conteneur porte plusieurs familles (un WAV : `INFO`, `bext`, ID3, XMP).

## Options envisagées

### Option A — Un module par famille de balises

`id3` (MP3, AAC, FLAC, WAV), `infowav` (liste `INFO` et bloc `bext` d'un WAV), `vorbis` (FLAC, Ogg), `quicktime` (M4A, MP4, MOV), `matroska` (WebM).

- Avantages : même logique qu'ADR-0114 ; une erreur dans un lecteur ne fait perdre que sa famille ; la couverture dit, famille par famille, ce qui a été lu, et chacune se désactive seule.
- Inconvénients : cinq manifestes et cinq fiches ; un WAV est parcouru par trois modules (`id3`, `infowav`, `xmp`).

### Option B — Un seul module `balises`

- Avantages : un manifeste, un parcours par fichier.
- Inconvénients : une erreur dans le lecteur ID3 fait perdre toutes les balises (NF-03) ; la couverture dit « balises appliquées » sans dire lesquelles (F-25) ; rien ne se désactive seul.

## Décision

Option A. Les lecteurs de structure sont écrits par le projet, en Python pur, comme le prévoit ADR-0043 (décision, point 1) :

- `modules/_lecture/conteneurs.py` localise les blocs de chaque format, sans les interpréter : blocs RIFF d'un WAV (le parcours RIFF devient commun à WebP et WAV), balises ID3v2 en tête et ID3v1 en fin d'un MP3, balises ID3v2 en tête d'un AAC et d'un FLAC, blocs de métadonnées d'un FLAC, pages et paquets Ogg, boîtes `moov` d'ISOBMFF, éléments de premier niveau d'un segment Matroska ;
- `modules/_lecture/ebml.py` lit les en-têtes et les entiers EBML (RFC 8794), pour `conteneurs` et `matroska` ;
- chaque module interprète ses blocs : trames ID3, sous-blocs `INFO` et champs `bext`, champs Vorbis, boîtes `udta`, `meta`, `ilst`, `keys`, éléments `Info` et `Tags`.

Modules livrés en version 0.1.0, sans dépendance entre eux (`requiert = []`) ni bibliothèque (`bibliotheques = []`).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : isolation des erreurs et couverture moins précises, comme l'option B d'ADR-0114.
- Lecteurs du projet plutôt qu'une bibliothèque : ADR-0043 exclut `mutagen` (GPL) et prévoit des analyseurs de structure écrits par le projet pour ISOBMFF ; les autres familles se lisent aussi sans décoder de son ni d'image, en quelques centaines de lignes, soumises au fuzzing (ES-19).
- EBML dans un lecteur à part plutôt que dans `conteneurs` : le module `matroska` lit l'intérieur d'`Info` et de `Tags` avec les mêmes règles. L'identification (T13) garde sa propre lecture des tailles EBML : elle s'exécute dans le processus de travail hors de tout module, et `_lecture` n'est importé que par les modules (ADR-0114).

## Conséquences

- La couverture d'un fichier audio ou vidéo liste ses modules applicables : `id3`, `infowav` et `xmp` pour un WAV ; `id3` et `vorbis` pour un FLAC ; `quicktime` et `xmp` pour M4A, MP4 et MOV, etc.
- Un parcours de conteneur interrompu est dit par chaque module qui le parcourt, avec la raison de l'arrêt (fichier tronqué, format partiel) : comme pour les images.
- Les cinq lecteurs et `ebml` sont soumis au fuzzing avec les modules d'image et de PDF (ES-19).
- Les codecs que ces modules emploient (UTF-16, Mac Roman, Shift_JIS) sont chargés à l'import, avant les restrictions (ADR-0079, ERR-0009), et vérifiés dans un vrai processus de travail.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; découpage en modules choisi par TheDarkMac au début du complément |
