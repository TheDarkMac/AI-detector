# ADR-0133 — Noms et valeurs des balises audio et vidéo

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : assistant, proposition à valider pendant la revue de la PR du complément
- **Tâche** : T21 (complément audio et vidéo)
- **Exigences liées** : F-10, F-14, ES-13, NF-06, NF-11 ; ADR-0057, ADR-0117, ADR-0118, ADR-0119, ADR-0128

## Contexte

ADR-0117 fixe la forme des noms d'observation (nom tiré de la norme, préfixé par la famille), ADR-0118 celle des valeurs, ADR-0119 le marquage des données identifiantes, ADR-0128 les dates d'un PDF (telles qu'écrites). Les balises audio et vidéo ont leurs propres identifiants : quatre lettres pour ID3 et RIFF, noms libres pour Vorbis et Matroska, codes de quatre octets dont le premier est souvent `©` (0xA9) pour QuickTime, clés en notation inversée (`com.apple.quicktime.software`). Leurs dates sont des textes (ID3, RIFF, `bext`) ou des nombres comptés depuis une origine (secondes depuis 1904 pour `mvhd`, nanosecondes depuis 2001 pour `DateUTC` de Matroska).

## Options envisagées

### Option A — Identifiants de la norme, passés par la règle des composants ; dates telles qu'écrites

| Famille | Nom | Partie variable |
| --- | --- | --- |
| Toutes | `<famille>.present`, `<famille>.blocs` | Comme ADR-0117 |
| ID3 | `id3.version` ; `id3.<trame>` ; `id3.TXXX.<description>`, `id3.WXXX.<description>` ; `id3.COMM[.<description>]`, `id3.USLT[.<description>]` ; `id3.<trame>.taille` | Identifiant de trame (`TIT2`, `TSSE`, `TT2` en v2.2) |
| ID3v1 | `id3.v1.Title`, `.Artist`, `.Album`, `.Year`, `.Comment`, `.Track`, `.Genre` | Champs de la spécification ID3v1 et v1.1 |
| RIFF | `infowav.<identifiant>` ; `infowav.bext.<champ>` | Identifiant `INFO` (`ISFT`, `INAM`) ; champ d'EBU Tech 3285 |
| Vorbis | `vorbis.vendor` ; `vorbis.<NOM>` ; `vorbis.<NOM>.taille` | Nom du champ en majuscules |
| QuickTime | `quicktime.mvhd.CreationTime`, `.ModificationTime` ; `quicktime.udta.<code>` ; `quicktime.ilst.<code>` ; `quicktime.ilst.----.<domaine>.<nom>` ; `quicktime.mdta.<clé>` ; `<nom>.taille` | Code de quatre octets ou clé |
| Matroska | `matroska.<élément>` ; `matroska.tag.<NOM>`, `matroska.piste.<NOM>`, `matroska.cible.<NOM>`, imbriquées à la suite ; `<nom>.taille` | Élément d'`Info` ; nom de balise simple |

- Partie tirée du fichier (code, clé, description, nom de champ ou de balise) : règle des composants d'ADR-0117 ; `©` y devient un tiret (`quicktime.ilst.-too`), le point d'une clé aussi (`quicktime.mdta.com-apple-quicktime-software`).
- Textes : dans l'encodage que fixe la trame ou la boîte (ID3 : Latin-1, UTF-16 avec ou sans marque d'ordre, lu petit-boutiste sans elle, UTF-16BE, UTF-8 ; Vorbis et Matroska : UTF-8 ; QuickTime : Mac Roman pour un code de langue Macintosh, UTF-8 ou UTF-16 sinon, types de données d'`ilst`), caractère de remplacement pour un octet invalide ; encodage non déclaré (`INFO`, `bext`) : UTF-8 s'il est valide, Latin-1 sinon (ADR-0118). Plusieurs valeurs (trame ID3v2.4, champ Vorbis répété, plusieurs `data`, plusieurs textes d'une boîte `©xxx`) : une liste. Texte vide : rien n'est observé.
- Dates : telles qu'écrites. Textes (`TDRC`, `ICRD`, `OriginationDate`) inchangés ; `mvhd` en secondes depuis le 1er janvier 1904 UTC, unité « s depuis 1904-01-01 UTC » ; `DateUTC` en nanosecondes depuis le 1er janvier 2001 UTC, unité « ns depuis 2001-01-01 UTC » ; un entier hors des 64 bits signés du modèle, en texte décimal.
- Données binaires (image, objet, données privées, type implicite d'`ilst`, `TagBinary`, image Vorbis en base 64) : leur taille (ADR-0118).
- Cible Matroska : `tag` pour une balise sans identifiant de cible non nul, `piste` si elle vise une piste (`TagTrackUID`), `cible` si elle vise une édition, un chapitre ou un fichier joint.
- Données identifiantes (ADR-0119), marquées par chaque module, liste dans sa fiche :
  - `metadonnee_nominative` : interprètes, auteurs, compositeurs, paroliers, chefs, remixeurs, encodeur (personne ou organisme), ayants droit, propriétaire, éditeur, réalisateur, producteurs ; ID3 (`TPE1` à `TPE4`, `TCOM`, `TEXT`, `TOLY`, `TOPE`, `TENC`, `TCOP`, `TOWN`, `TPUB`, `TIPL`, `TMCL`, `IPLS` et leurs équivalents v2.2), ID3v1 `Artist`, RIFF (`IART`, `ICMS`, `ICOP`, `IENG`, `ITCH`, `IMUS`, `IPRO`, `ISTR`, `IWRI`, `IEDT`), `bext` `Originator`, Vorbis, QuickTime (dont `apID`, compte iTunes) et Matroska selon leurs listes ;
  - `numero_de_serie` : `bext` `OriginatorReference` et `UMID`, qui portent le numéro de série de l'enregistreur (EBU R 99, SMPTE 330M) ;
  - `gps` : `©xyz`, `loci`, `com.apple.quicktime.location.ISO6709` ;
  - `nom_de_fichier` : ID3 `TOFN` (`TOF`), Matroska `SegmentFilename`, `PrevFilename`, `NextFilename`.

- Avantages : les noms sont ceux que connaît un vérificateur et qu'emploient les spécifications ; le fichier ne choisit pas le nom d'une balise connue ; même règle de dates que le PDF (ADR-0128), l'unité disant comment lire le nombre.
- Inconvénients : des noms peu lisibles pour qui ne connaît pas les codes (`-too` pour l'encodeur QuickTime) ; les fiches donnent la signification des codes usuels.

### Option B — Noms lisibles d'une table (`quicktime.Encoder`, `id3.Title`)

- Avantages : lisible.
- Inconvénients : une table par famille, qui ne couvre jamais tous les codes ; deux familles nommeraient de même des champs différents ; noms d'exiftool plutôt que des normes, contraire à ADR-0117 (la norme fait foi).

### Option C — Dates converties en ISO 8601

- Avantages : comparables d'emblée.
- Inconvénients : interprétation qui revient à T23 (fuseau d'un texte ID3, valeur 0 de `mvhd` qui signifie « non renseignée »), comme l'option B d'ADR-0128.

## Décision

Option A.

## Raisons

- Option A : même principe qu'ADR-0117 et ADR-0128 ; l'unité rend la date lisible sans l'interpréter.
- Option B écartée : table incomplète et noms hors norme.
- Option C écartée : interprétation prématurée (T23).
- Vorbis en majuscules : la spécification tient les noms de champ pour insensibles à la casse (Vorbis I, §5) ; ffmpeg écrit `encoder`, d'autres `ENCODER`. Matroska garde la casse écrite : ses noms officiels sont en majuscules et la spécification ne les dit pas insensibles à la casse.
- `vorbis.vendor` en minuscules : ce n'est pas un champ mais la chaîne du fournisseur, que la casse distingue d'un champ `VENDOR`.
- UTF-16 sans marque d'ordre lu petit-boutiste : ID3v2.3 exige la marque ; son absence vient d'ordinaire d'outils Windows, qui écrivent en petit-boutiste. Le choix est fixe, donc reproductible (NF-06).
- `OriginatorReference` et `UMID` marqués numéro de série : leur forme normalisée contient celui de l'appareil ; `Originator` nomme d'ordinaire l'organisme ou la personne.
- Lieux nommés (`com.apple.quicktime.location.name`) et textes libres non marqués : comme ADR-0119, ils relèvent de T25.

## Conséquences

- Les règles de T22 (signatures d'encodeurs et de générateurs : `id3.TSSE`, `infowav.ISFT`, `vorbis.vendor`, `vorbis.ENCODER`, `quicktime.ilst.-too`, `quicktime.udta.-swr`, `matroska.MuxingApp`, `matroska.WritingApp`, `matroska.tag.ENCODER`) et de T23 (dates) citent ces noms.
- T23 convertit les dates dans la règle qui les compare, à partir de leur unité.
- Un changement de nom est un changement de version du module et des règles qui le citent.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
