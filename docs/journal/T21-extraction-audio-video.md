# T21 (complément) — Extraction audio et vidéo : balises des conteneurs

- **Branche** : `tache/T21-extraction-audio-video`
- **Dates** : 2026-11-13
- **Exigences couvertes** : F-10 (audio et vidéo), F-14 (absence observée), F-82, ES-03, ES-05 (XMP des fichiers audio et vidéo), ES-13, ES-19, NF-09
- **Décisions** : ADR-0130 à ADR-0135, tous acceptés
- **Errata** : aucun

## Objectif

Premier complément de T21 (ADR-0123) : extraire les balises des conteneurs audio et vidéo du périmètre (F-10). Les ADR antérieurs adressaient à ce complément : ses propres modules (ADR-0114), des analyseurs de structure écrits par le projet et soumis au fuzzing, `mutagen` étant exclue (ADR-0043), l'oracle exiftool complété (ADR-0122). Ce n'est pas une tâche nouvelle du découpage : la branche garde le préfixe de T21, avec un slug distinct, et l'entrée du journal porte « T21 (complément) », comme pour T10.

## État initial

- PR [#20](https://github.com/TheDarkMac/AI-detector/pull/20) (T21, PDF). Sur `c98c1e6` : docs 43311215139 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129) ; code 43311215112 en échec pour une seule raison, la tâche macOS de Python 3.14, restée sans machine et annulée après 15 min, sans qu'aucune étape ait tourné (incident de GitHub, pas un test). ADR-0125, ADR-0127 et ADR-0128 validés par TheDarkMac, passés à « Accepté » (`0c6e0c2`) : docs 43359242534 et code 43359242496 verts (code terminé à 03:33:01 UTC).
- Une première demande de merge par l'assistant a été bloquée par le contrôle du mode automatique ; après le « vas y » de TheDarkMac, l'assistant a mergé la PR le 2026-11-13 vers 03:39 UTC par `gh pr merge 20 --merge --subject …` : commit de merge `4a49cba` « Merge: T21 — Extraction PDF (#20) », à l'adresse noreply (ADR-0007). Lancements de push sur `4a49cba` verts : docs 43360775734 (étape « Titre du commit de merge » : titre conforme), code 43360775791 (terminé à 03:46:24 UTC).
- La ligne de T21 dans l'index du journal portait « à venir » : corrigée en #20 dans cette tâche.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (option B d'ADR-0129), qui demande un changement des réglages du dépôt par TheDarkMac.
- uv n'est pas installé sur le poste : uv 0.13.5 réinstallé dans un environnement temporaire. Outils : exiftool 13.25, ImageMagick 7.1.1-43, LibreOffice 25.2.3.2, Ghostscript 10.05.1, Poppler 25.03.0 ; ni ffmpeg ni aucun outil audio au départ.
- `detector` à jour avec `origin/detector` (`4a49cba`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : journal et ADR de T21, ADR-0043, ADR-0114 à ADR-0122, formats du périmètre (`formats.py`) et leur identification (`_travail/identification.py`), lecteurs communs (`conteneurs`, `valeurs`), contexte, modules `xmp` et `infopdf`, tests et oracle. Outils du poste : exiftool seul lit toutes les familles, mais n'écrit ni ID3, ni Vorbis, ni RIFF, ni Matroska.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation, toutes suivies :
   - périmètre : les neuf formats en une branche ([ADR-0130](../decisions/ADR-0130-complement-audio-et-video-de-t21.md)) ;
   - modules : un par famille de balises ([ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)) ;
   - XMP des fichiers audio et vidéo : dans cette PR ([ADR-0134](../decisions/ADR-0134-xmp-des-fichiers-audio-et-video.md)) ;
   - oracle : ffmpeg du dépôt Debian, installé par TheDarkMac ([ADR-0135](../decisions/ADR-0135-oracle-des-balises-par-ffmpeg.md)).

   Les autres choix, faits par l'assistant, ont été soumis dans la PR et validés par TheDarkMac pendant sa revue (2026-11-13) : [ADR-0132](../decisions/ADR-0132-emplacements-lus-dans-les-conteneurs-audio-et-video.md) (emplacements lus et non lus), [ADR-0133](../decisions/ADR-0133-noms-et-valeurs-des-balises-audio-et-video.md) (noms, valeurs, dates, données identifiantes).
3. Branche `tache/T21-extraction-audio-video` créée depuis `detector` à jour (`4a49cba`).
4. Lecteurs : `conteneurs` localise les blocs des neuf formats (parcours RIFF commun à WebP et WAV, balises ID3v2 consécutives et ID3v1, blocs FLAC, pages et paquets Ogg réassemblés, boîtes de `moov` et XMP d'ISOBMFF, éléments de premier niveau d'un segment EBML, `Cluster` de taille inconnue) ; `ebml` lit en-têtes, enfants et entiers EBML ; `valeurs` gagne `entier` et `texte`.
5. Modules `id3`, `infowav`, `vorbis`, `quicktime`, `matroska` 0.1.0 ; `xmp` 0.3.0 (WAV, M4A, MP4, MOV) ; fiches `metadonnees-id3`, `metadonnees-info-wav`, `metadonnees-vorbis`, `metadonnees-quicktime`, `metadonnees-matroska`, fiche `metadonnees-xmp` complétée.
6. Tests :
   - `tests/medias.py` : constructeurs de balises ID3, de WAV, de FLAC, de pages Ogg (CRC compris), de boîtes ISOBMFF et d'éléments EBML ;
   - `tests/test_metadonnees_medias.py` : absence, formes de valeur, encodages, désynchronisation et compression ID3, codecs Ogg, paquets sur plusieurs pages, `ilst`, `udta`, `keys`, cibles Matroska, structures interrompues ou mal formées, données identifiantes, budget ;
   - vrai processus de travail sur une vidéo, et sur les textes UTF-16, Shift_JIS et Mac Roman (ERR-0009) ;
   - fuzzing : échantillons construits et échantillons de l'oracle des neuf formats parmi ceux des modules de métadonnées ;
   - tests existants adaptés : liste des modules, versions, couverture d'un PDF.
7. TheDarkMac a installé ffmpeg 7.1.5 (Debian 13). Oracle : `generer_media.sh` (dix échantillons, balises de ffmpeg, XMP d'exiftool pour le MP4 et le MOV) ; `relire.sh` passé à `-G1:4` ; test d'oracle étendu aux neuf formats, dans les deux sens.
8. Vérification locale : `uv lock --check` ; Ruff (format et analyse) et mypy sans remarque ; matrice régénérée et vérifiée ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans remarque ; 1 402 tests verts, un sauté (lanceur de Windows) ; couverture 100 % des lignes et des branches ; exiftool 13.25 redonne exactement `exiftool.json` ; campagne de fuzzing des modules de métadonnées, 40 000 exemples par propriété (profil temporaire, hors du dépôt), trois fois : sur les échantillons construits, sans échec (18 min 00 s) ; avec les échantillons de l'oracle, un échec, `TimeReference` hors bornes (voir les problèmes) ; après la correction, sans échec (17 min 30 s).
9. Documentation : ADR-0130 à ADR-0135 ; fiches ; renvois dans ADR-0043, ADR-0114, ADR-0117, ADR-0119, ADR-0122, ADR-0123 ; matrice (F-10, F-14, ES-05, ES-19) ; découpage v0.20, architecture v1.14 ; `CONTRIBUTING.md` (§1, oracle) ; index des ADR, du journal et des fiches.

10. PR [#21](https://github.com/TheDarkMac/AI-detector/pull/21) ouverte ; `lint-markdown` rouge sur l'étape « Aucun ADR au statut Proposé », comme prévu (ADR-0129). ADR-0132 et ADR-0133 validés par TheDarkMac pendant la revue, le 2026-11-13 : statut « Accepté ».

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Aucun outil pour écrire les échantillons de l'oracle | ffmpeg absent du poste, exiftool n'écrit pas ces familles | Question posée ; TheDarkMac a installé ffmpeg (ADR-0135). Une première vérification ne le trouvait pas ; il l'était à la seconde |
| La sortie JSON d'exiftool ne gardait qu'un `ENCODER` du WebM | Une clé par nom et par groupe ; le WebM en a deux, global et de piste | `-G1:4`, qui numérote les copies ; vérifié qu'aucune balise comparée des échantillons de T20 et T21 n'était perdue sous `-G1` (ADR-0135) |
| exiftool lit le titre `INFO` d'un WAV « Titre accentuÃ© » | Il lit les textes RIFF en Latin-1, ffmpeg les écrit en UTF-8 ; `infowav` suit ADR-0118 (UTF-8 s'il est valide) | Écart documenté dans la fiche ; le test relit en UTF-8 le texte RIFF d'exiftool |
| exiftool joint date et heure de `bext` en `DateTimeOriginal` | Présentation d'exiftool | Comparaison de la date et de l'heure jointes |
| Un `udta` mal formé est dit deux fois | `quicktime` lit `udta`, `conteneurs` le parcourt pour y chercher `XMP_` | Gardé : chaque module dit son erreur (ADR-0114, ADR-0134) ; test qui le fixe |
| Branche jamais prise dans le réassemblage Ogg | Un paquet qui continue sur la page suivante y a au moins 255 octets : l'en-tête du paquet tient toujours dans son premier morceau | Code simplifié, raison écrite en commentaire |
| Plusieurs renvois à des paragraphes de normes écrits de mémoire | Numéros de paragraphe non vérifiables sur le poste | Retirés ou ramenés au document, avant le premier commit (précédent d'ERR-0002) |
| La campagne de fuzzing mettait `infowav` en erreur sur un WAV muté | `TimeReference` de `bext` est un entier non signé de 64 bits ; au-delà de 2⁶³ − 1, le modèle le refuse | Entier hors bornes écrit en texte décimal (`valeurs.entier`, ADR-0118), comme les autres entiers des balises ; test qui échoue sans la correction ; campagne relancée |
| Attentes fausses dans les premiers tests (Mac Roman 0x8E, octet UTF-16 seul, bloc FLAC) | Erreurs de l'assistant en écrivant les tests | Attentes corrigées après lecture des normes ; le code était juste |

Aucun de ces problèmes ne touche un élément déjà mergé.

## Écarts par rapport au découpage

- **Ajouté** : XMP des fichiers audio et vidéo (ADR-0134) ; bloc `bext` des WAV de diffusion avec la liste `INFO` ; lecteur EBML commun.
- **Écarté** : `mutagen` (ADR-0043, GPL) ; pistes des MP4 et MOV, `iXML`, APE, fichiers joints Matroska (ADR-0132).
- **Non fait** : DOCX et ODT (dernier complément de T21) ; pistes et structure des conteneurs (T71, T72).
- **Inchangé** : le catalogue (0.1.0, sans règle).

## Résultat

- Un fichier audio ou vidéo du périmètre a ses balises au rapport, famille par famille : ID3, `INFO` et `bext`, commentaires Vorbis, `moov` (dates de `mvhd`, `udta`, `ilst`, clés QuickTime), `Info` et `Tags` d'un WebM, et le XMP d'un WAV, d'un M4A, d'un MP4 ou d'un MOV ; noms de personne, numéros de série, positions et noms de fichier masqués par défaut.
- Les extractions concordent avec exiftool, dans les deux sens, sur dix échantillons écrits par ffmpeg.
- Un conteneur tronqué ou mal formé le dit par une analyse non menée ; aucun parcours ne lit les données audio ou vidéo.

## Reste à faire

- Dernier complément de T21 : DOCX et ODT (XML par expat, ADR-0116) ; F-10 réalisée ensuite.
- T22 : signatures d'encodeurs et de générateurs (`TSSE`, `ISFT`, `vendor`, `ENCODER`, `-too`, `-swr`, `MuxingApp`, `WritingApp`) ; `DigitalSourceType` d'une vidéo.
- T23 : dates de `mvhd` et `DateUTC` converties depuis leur unité dans la règle qui les compare (ADR-0133).
- T25 : textes libres et lieux nommés des balises.
- T71, T72 : pistes et structure des conteneurs vidéo et audio.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande ; contrôle des ADR en tâche séparée (ADR-0129, option B).
