# Fiche technique — Balises ID3

- **Module** : `id3` (version 0.3.0)
- **Tâche** : T21, T22, T23, T25
- **Exigences** : F-10, F-12, F-90, ES-13
- **Formats** : `mp3`, `aac`, `flac`, `wav`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
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
- Date : telle qu'écrite (`2026-11-13T10:00`), sans conversion ; T23 ne la compare pas, faute de paire de dates que fixe la norme ([ADR-0150](../decisions/ADR-0150-incoherences-retenues.md)).
- Trame vide : rien n'est observé.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Trames |
| --- | --- |
| `metadonnee_nominative` | `TPE1`, `TPE2`, `TPE3`, `TPE4`, `TCOM`, `TEXT`, `TOLY`, `TOPE`, `TENC`, `TCOP`, `TOWN`, `TPUB`, `TIPL`, `TMCL`, `IPLS` ; en v2.2, `TP1` à `TP4`, `TCM`, `TXT`, `TOL`, `TOA`, `TEN`, `TCR`, `TPB`, `IPL` ; ID3v1 `Artist` |
| `nom_de_fichier` | `TOFN` (`TOF` en v2.2) |
| `texte_libre` | `TIT1`, `TIT2`, `TIT3`, `TALB`, `TOAL`, `TSST`, `TXXX` (toute description), `COMM`, `USLT` ; en v2.2, `TT1`, `TT2`, `TT3`, `TAL`, `TOT`, `TXX`, `COM`, `ULT` ; ID3v1 `Title`, `Album`, `Comment` |

Aucune trame normalisée ne nomme un lieu ([ADR-0159](../decisions/ADR-0159-lieux-nommes-et-textes-libres.md), [ADR-0160](../decisions/ADR-0160-champs-lieux-et-textes-libres.md)). Ces données sont comptées et nommées, sans leur valeur, par la rubrique « Contrôle avant publication » du rapport et par le résumé ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `TSSE` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. Un `TSSE` (souvent `Lavf…` pour un fichier écrit par ffmpeg) est une déclaration que quiconque peut écrire ou effacer (cas d'abus C-02).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-ID3-001` Générateur nommé par la trame ID3 du logiciel d'encodage ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `id3.TSSE` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-ID3-002` Aucune balise ID3 | `id3.present` | faux |

Une absence de balise est l'observation `id3.present` à faux ; la règle `R-ID3-002` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool sur un MP3 (ID3v2.4 et ID3v1) et un AAC écrits par ffmpeg ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)) ; ffmpeg n'écrit d'ID3 ni dans un WAV ni dans un FLAC, ces emplacements sont vérifiés par les échantillons construits des tests. ffmpeg écrit le texte UTF-8 de son titre dans la balise ID3v1, en Latin-1 : `id3.v1.Title` le lit en Latin-1, comme exiftool, et montre donc des caractères mal décodés. Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

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
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
| 2026-11-14 | 0.3.0 | Titres, commentaires, paroles et textes libres marqués ; contrôle avant publication (T25, ADR-0158 à ADR-0163) |
