# Fiche technique — Balises ID3

- **Module** : `id3` (version 0.1.0)
- **Tâche** : T21
- **Exigences** : F-10, ES-13
- **Formats** : `mp3`, `aac`, `flac`, `wav`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Que déclarent les balises ID3 du fichier : titre, interprètes, logiciel d'encodage (`TSSE`), dates, commentaires, textes libres ?

## Principe

Le module lit chaque balise ID3v2 (id3.org : versions 2.2, 2.3 et 2.4) et la balise ID3v1, par les lecteurs du projet ([ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)). D'une balise ID3v2, il lit l'en-tête (version, drapeaux, taille synchrosûre), défait la désynchronisation (de toute la balise en v2.2 et v2.3, trame par trame en v2.4), saute l'en-tête étendu, puis lit chaque trame jusqu'au bourrage : identifiant, taille, drapeaux de format ; une trame compressée est décompressée (zlib). Le texte est décodé selon l'octet d'encodage de la trame. Rien n'est réparé : une trame qui ne se lit pas comme elle est déclarée arrête la lecture de sa balise.

## Entrées

| Format | Emplacement lu ([ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md)) |
| --- | --- |
| MP3 | Balises ID3v2 consécutives en tête ; ID3v1 dans les 128 derniers octets de la partie |
| AAC (ADTS) | Balises ID3v2 en tête |
| FLAC | Balises ID3v2 en tête, avant `fLaC` |
| WAV | Bloc `id3` ou `ID3`, identifiant suivi d'une espace |

Aucune donnée de référence. Ne sont pas lus : ID3v2 en fin de fichier (balise annoncée par son seul pied `3DI`), ID3v1 étendue (`TAG+`), balise APE, ID3v1 d'un AAC ou d'un FLAC, qu'identification ne compte pas dans la partie.

## Sorties

Noms d'observation ([ADR-0133](../decisions/ADR-0133-noms-et-valeurs-des-balises-audio-et-video.md)) :

| Nom | Valeur |
| --- | --- |
| `id3.present` | Vrai si une balise ID3 a été trouvée ; toujours observé (F-14) |
| `id3.blocs` | Nombre de balises, ID3v1 comprise |
| `id3.version` | Version d'une balise ID3v2 : `2.3.0`, `2.4.0`… |
| `id3.<trame>` | Texte d'une trame de texte (`T…`) ou adresse d'une trame d'URL (`W…`) ; liste s'il y a plusieurs valeurs |
| `id3.TXXX.<description>`, `id3.WXXX.<description>` | Texte ou adresse libres ; sans description, `id3.TXXX` |
| `id3.COMM[.<description>]`, `id3.USLT[.<description>]` | Commentaire, paroles |
| `id3.<trame>.taille` | Taille, en octets, d'une trame binaire : image (`APIC`), objet (`GEOB`), données privées (`PRIV`), identifiant (`UFID`)… |
| `id3.v1.Title`, `.Artist`, `.Album`, `.Year`, `.Comment` | Champs de la balise ID3v1, sans les nuls ni les espaces de fin |
| `id3.v1.Track`, `id3.v1.Genre` | Piste (ID3v1.1) et genre, entiers ; genre 255 : non observé |

- Trames usuelles : `TIT2` titre, `TPE1` interprète, `TALB` album, `TDRC` date d'enregistrement (v2.4), `TYER` année (v2.3), `TSSE` logiciel et réglages d'encodage, `TENC` encodé par, `TCON` genre ; en v2.2, identifiants de trois lettres (`TT2`, `TP1`, `TSS`…), observés tels quels.
- Encodage : 0 Latin-1, 1 UTF-16 (marque d'ordre ; sans elle, petit-boutiste), 2 UTF-16BE, 3 UTF-8 ; un octet invalide devient le caractère de remplacement. Une description passe par la règle des composants d'ADR-0117.
- Date : telle qu'écrite (`2026-11-13T10:00`), sans conversion ; T23 l'interprétera.
- Trame vide : rien n'est observé.

Aucun constat.

## Données identifiantes

| Catégorie | Trames |
| --- | --- |
| `metadonnee_nominative` | `TPE1`, `TPE2`, `TPE3`, `TPE4`, `TCOM`, `TEXT`, `TOLY`, `TOPE`, `TENC`, `TCOP`, `TOWN`, `TPUB`, `TIPL`, `TMCL`, `IPLS` ; en v2.2, `TP1` à `TP4`, `TCM`, `TXT`, `TOL`, `TOA`, `TEN`, `TCR`, `TPB`, `IPL` ; ID3v1 `Artist` |
| `nom_de_fichier` | `TOFN` (`TOF` en v2.2) |

Commentaires, textes libres (`TXXX`) et paroles ne sont pas marqués : la liste de garde des textes libres relève de T25 ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Rien |

Le module ne distingue aucune hypothèse et n'émet aucun constat ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)). Un `TSSE` (souvent `Lavf…` pour un fichier écrit par ffmpeg) est une déclaration que quiconque peut écrire ou effacer (cas d'abus C-02) : les règles de T22 en feront au mieux une déclaration de logiciel.

## Ce qui déclenche un constat

Aucun constat en T21. Une absence de balise est l'observation `id3.present` à faux (F-14).

## Taux d'erreur

Sans objet : aucun constat. Fidélité de l'extraction vérifiée contre exiftool sur un MP3 (ID3v2.4 et ID3v1) et un AAC écrits par ffmpeg ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)) ; ffmpeg n'écrit d'ID3 ni dans un WAV ni dans un FLAC, ces emplacements sont vérifiés par les échantillons construits des tests. ffmpeg écrit le texte UTF-8 de son titre dans la balise ID3v1, en Latin-1 : `id3.v1.Title` le lit en Latin-1, comme exiftool, et montre donc des caractères mal décodés.

## Limites connues

- Trame chiffrée : non lue (non menée) ; la compression de la v2.2, qu'aucune méthode ne définit, rend la balise non menée.
- Trame mal formée (identifiant hors de `A`–`Z` et `0`–`9`, taille qui déborde, taille non synchrosûre en v2.4, encodage inconnu) : la lecture de sa balise s'arrête ; les trames lues avant restent observées. Certains logiciels anciens écrivent en v2.4 des tailles non synchrosûres : leurs balises sont non menées.
- La langue d'un commentaire et la description d'une image ne sont pas observées.
- Un texte v2.3 qui sépare plusieurs valeurs par `/` reste un seul texte.
- Une trame qui apparaît deux fois donne deux observations du même nom.
- Le XMP d'une trame `PRIV` n'est pas lu par `xmp` ; sa taille est observée.

## Sécurité

- Lecture bornée par le contexte : une balise de plus de 16 Mio n'est pas lue (format partiel).
- Chaque balise et chaque trame comptent un objet (ADR-0078).
- Trames compressées décompressées par `Contexte.decompresser`, donc comptées dans le budget de décompression.
- Les codecs UTF-16 sont chargés à l'import, avant les restrictions du processus de travail (ADR-0079, ERR-0009).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément audio et vidéo) |
