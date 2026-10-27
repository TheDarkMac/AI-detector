# ADR-0070 — Identification du format par le contenu : vocabulaire, signatures, fin logique

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T13, validée pendant la revue de la PR de T13
- **Tâche** : T13
- **Exigences liées** : F-01, F-02, F-03, ES-07 ; M-08 ; A-25, A-31 ; ADR-0012, ADR-0036, ADR-0043, ADR-0064, ADR-0071

## Contexte

F-02 demande le format réel par le contenu, F-03 de signaler une extension qui ne lui correspond pas. ES-07 ajoute deux signalements : un fichier reconnu dans plusieurs formats (polyglotte, A-31), un fichier qui contient des données après sa fin logique. ADR-0012 accepte en V1 tous les formats du §3 du cahier. ADR-0064 laissait à T13 le vocabulaire des formats cité par les manifestes. L'architecture place l'identification dans le processus de travail, qui seul lit le fichier pour l'interpréter (ADR-0036).

ADR-0071 (choix de TheDarkMac) veut que chaque format reconnu soit analysé : l'identification doit donc situer chaque format dans le fichier, du début à sa fin logique, et pas seulement nommer le premier.

## Options envisagées

### Option A — Signatures et structures de conteneur, en Python pur, dans le processus de travail

- Avantages : aucune dépendance (ADR-0043 : analyseurs de structure en Python pur) ; même résultat sur les trois systèmes et d'une version à l'autre (NF-06) ; le parcours des structures donne la fin logique, donc les données en trop et les formats suivants.
- Inconvénients : code à écrire et à tester pour chaque format ; une liste de formats tenue à la main.

### Option B — `libmagic` (par `python-magic`)

- Avantages : des centaines de formats reconnus.
- Inconvénients : bibliothèque C exécutée sur un fichier hostile ; base de signatures qui change avec la version installée sur le système (NF-06) ; Windows sans paquet officiel ; un seul format par fichier, ni fin logique ni polyglotte.

### Option C — Paquets Python de signatures (`filetype`, `puremagic`)

- Avantages : Python pur, simples.
- Inconvénients : signature en tête du fichier seulement ; ni fin logique, ni données en trop, ni polyglotte ; une dépendance pour la partie la plus facile du travail.

## Décision

Option A, dans `voight_kampff/formats.py` (vocabulaire) et `voight_kampff/_travail/identification.py` (lecture).

### Vocabulaire

| Famille | Formats du périmètre (analysés) |
| --- | --- |
| Image | `jpeg`, `png`, `webp`, `heic` |
| Audio | `wav`, `mp3`, `aac`, `m4a`, `flac`, `ogg` |
| Vidéo | `mp4`, `mov`, `webm` |
| Document | `pdf` |
| Texte | `texte`, `docx`, `odt` |

Formats reconnus hors périmètre, pour être nommés dans un refus ou une partie non analysée : `gif`, `bmp`, `tiff`, `avif`, `heif`, `avi`, `matroska`, `3gp`, `zip`, `gzip`, `7z`, `rar`, `exe`, `elf`.

Le manifeste d'un module ne peut citer que les formats du périmètre (énumération du schéma). Chaque format a ses extensions usuelles (`formats.EXTENSIONS`) ; l'extension du nom, en minuscules, au plus 32 caractères, est « concordante » si elle en fait partie.

### Reconnaissance et fin logique

| Format | Reconnu par | Fin logique |
| --- | --- | --- |
| JPEG | `FF D8 FF` | Segments parcourus jusqu'à EOI ; données entropiques sautées (`FF 00`, RST) |
| PNG | Signature de 8 octets | Blocs parcourus jusqu'à IEND |
| WAV, WebP, AVI | `RIFF` et type `WAVE`, `WEBP` ou `AVI` (suivi d'une espace) | Taille RIFF, bourrage compris s'il est présent |
| MP4, MOV, M4A, HEIC, AVIF, HEIF, 3GP | Boîte `ftyp` : marque majeure, puis marques compatibles ; MOV ancien par `moov`, `mdat`, `wide` | Boîtes de premier niveau ; un type non imprimable clôt la structure ; taille 0 = jusqu'à la fin |
| WebM, Matroska | En-tête EBML et type de document | Taille du segment ; inconnue (direct) = fin non établie |
| Ogg | `OggS`, version 0 | Pages parcourues ; la structure finit à la première qui manque |
| MP3, AAC | Au moins deux trames consécutives (couche III ; ADTS), ou une seule qui finit le fichier ; balise ID3v2 en tête admise, ID3v1 en fin | Trames parcourues |
| FLAC | `fLaC` et bloc STREAMINFO, ou après une balise ID3v2 | Non établie |
| PDF | `%PDF-` et un chiffre, en tête ou dans les 1024 premiers octets | Après le dernier `%%EOF` et les blancs qui suivent |
| ZIP, DOCX, ODT | Enregistrement de fin lu depuis la fin (ZIP64 compris) ; début = première entrée locale. DOCX : `[Content_Types].xml` et `word/document.xml` ; ODT : entrée `mimetype` en tête, non compressée | Fin de l'enregistrement, commentaire compris |
| Texte | UTF-8 strict (marque d'ordre admise) ou UTF-16 avec marque, sans caractère de contrôle hors tabulation, sauts de ligne et de page ; **seulement si rien d'autre n'est reconnu** | Fin du fichier |
| GIF, TIFF, gzip, 7z, RAR, ELF | Signature | Non établie |
| BMP | `BM`, octets réservés nuls, taille d'en-tête connue | Taille déclarée, si elle tient dans le fichier |
| EXE | `MZ` et en-tête `PE` | Non établie |

La fin d'une partie a trois états : **établie** ; **non établie** (structure non parcourue, taille déclarée inconnue, ou plus de 2²⁰ éléments à parcourir) ; **tronquée** (la structure s'interrompt ou se contredit avant sa fin : fichier tronqué ou corrompu). Une partie dont la fin n'est pas établie s'étend jusqu'à la fin du fichier.

### Parties

1. Une **chaîne** part du début du fichier : à la fin logique d'un format, on cherche le suivant, au plus 16 parties.
2. S'y ajoutent les deux positions que les lecteurs usuels acceptent ailleurs qu'en tête : le premier en-tête PDF des 1024 premiers octets, l'archive ZIP lue depuis la fin.
3. Les parties sont rangées par début ; la partie 1 donne le **format réel**. Les plages peuvent se chevaucher (un PDF dans le commentaire d'un JPEG).
4. Les octets qu'aucune partie ne couvre sont les **octets non reconnus** ; la dernière plage, s'il y en a une, suit la fin logique.

## Raisons

- Option A retenue : seul le parcours des structures permet ce qu'ES-07 et ADR-0071 demandent (fin logique, formats successifs) ; Python pur et bornes de parcours limitent ce qu'un fichier hostile peut obtenir du processus de travail.
- Option B écartée : code C sur données hostiles, résultat dépendant du système, et elle ne répond qu'à F-02.
- Option C écartée : elle ne couvre ni F-03 étendu par ES-07 ni ADR-0071, et ajoute une dépendance (ADR-0043).
- Formats hors périmètre reconnus : un refus qui nomme le format (« gif ») est explicite (F-04) ; un polyglotte JPEG + ZIP doit pouvoir nommer sa seconde partie.
- Texte en dernier recours : un PDF ou un SVG est aussi du texte ASCII ; le classer « texte » masquerait son format.
- ZIP lu depuis la fin, PDF dans les 1024 premiers octets : ce sont les positions que les lecteurs acceptent, donc celles qu'un polyglotte exploite (M-08).

## Conséquences

- Ajouter un format, c'est modifier `formats.py`, l'identification, les énumérations des schémas et leurs tests : un changement de modèle (ADR-0054).
- Limites connues, à reprendre par les modules concernés ou au besoin d'un nouvel ADR : une balise APE ou Lyrics3 après un MP3 apparaît en octets non reconnus ; la fin d'un FLAC n'est pas établie ; un MP4 sans vidéo n'est M4A que par sa marque ; les autres documents OOXML et ODF (tableur, présentation) sont des `zip` ; le texte n'est reconnu qu'en UTF-8 ou UTF-16 avec marque.
- Les contenus multiples internes à un format (images d'un HEIC, pistes d'une vidéo, A-25) restent aux modules : l'identification ne voit que des formats mis bout à bout.
- Les bornes (16 parties, 2²⁰ éléments, lectures par blocs de 1 Mio) sont des choix de T13 ; T14 fixe les limites de taille et de temps de l'analyse.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR de T13 : statut « Accepté » |
