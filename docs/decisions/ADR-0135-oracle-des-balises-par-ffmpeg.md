# ADR-0135 — Oracle des balises audio et vidéo : échantillons écrits par ffmpeg

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21 (complément audio et vidéo)
- **Exigences liées** : F-10, NF-09 ; ADR-0043, ADR-0122

## Contexte

ADR-0122 compare les modules à exiftool sur des échantillons écrits par des outils tiers, et a écarté les échantillons construits par les tests seuls (option C : une erreur de lecture d'une norme serait commise deux fois). exiftool lit toutes les familles de ce complément, mais n'écrit ni ID3, ni commentaires Vorbis, ni liste RIFF, ni Matroska. Au début du complément, le poste de développement n'avait ni ffmpeg ni aucun outil audio.

## Options envisagées

### Option A — ffmpeg du dépôt Debian

TheDarkMac installe ffmpeg (`sudo apt install ffmpeg`) ; un script crée les échantillons et y écrit les balises par ffmpeg, exiftool ajoute le XMP de la vidéo, puis exiftool relit le tout.

- Avantages : échantillons indépendants du code testé, comme ADR-0122 ; ffmpeg écrit les neuf formats et les balises que l'on trouve le plus souvent dans les fichiers produits par des générateurs (`Lavf…`, `Lavc…`) ; paquet Debian, vérifié par sa signature.
- Inconvénients : un outil de plus sur le poste pour régénérer ; quelques fichiers binaires de plus dans le dépôt.

### Option B — Échantillons construits par les tests, relus par exiftool

- Avantages : rien à installer.
- Inconvénients : c'est l'option C écartée par ADR-0122.

## Décision

Option A. `tests/donnees/metadonnees/generer_media.sh` produit dix échantillons, un par forme de conteneur : WAV (`INFO`, `bext`), MP3 (ID3v2.4, ID3v1), AAC (ID3v2), M4A (`ilst`), FLAC et Ogg Vorbis et Opus (commentaires), MP4 (clés `mdta`, XMP en `uuid`), MOV (`udta`, XMP en `XMP_`), WebM (`Info`, `Tags` globaux et de piste). `relire.sh`, appelé par les trois scripts, écrit `exiftool.json`. Les constructeurs des tests (`tests/medias.py`) restent l'outil des cas limites, des structures malformées et des emplacements que ffmpeg n'écrit pas (ID3 d'un WAV ou d'un FLAC, ID3v2.2 et v2.3, `_PMX`).

`relire.sh` passe de `-G1` à `-G1:4` : la sortie JSON d'exiftool ne garde qu'une balise par nom et par groupe, et le WebM porte deux `ENCODER` (l'un global, l'autre de piste) ; le groupe de famille 4 numérote les copies (`Matroska:Copy1:Encoder`). Vérifié sur les échantillons de T20 et de T21 : sous `-G1`, rien de ce que comparent les modules n'était perdu (seules deux dimensions du WebP, de la structure, l'étaient) ; avec `-G1:4`, une balise prend aussi un numéro quand une balise du même nom existe dans un autre groupe (`GPS:Copy1:GPSLatitude`, l'originale étant composite), et le test ignore ce numéro.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : test circulaire (ADR-0122).
- Un script de plus plutôt qu'un ajout à `generer.sh` : comme pour le PDF (ADR-0127), les échantillons d'une famille se régénèrent sans changer les autres.

## Conséquences

- ffmpeg n'est ni livré ni appelé par l'outil, ni installé en CI : la CI compare aux sorties enregistrées (ADR-0122).
- `CONTRIBUTING.md` (§1) nomme ffmpeg parmi les outils de l'oracle.
- Changer d'échantillons demande de relancer `generer_media.sh` avec les versions indiquées dans le script (ffmpeg 7.1.5, exiftool 13.25), ou de noter les nouvelles.
- Correspondances propres aux balises dans le test d'oracle : identifiants `?xxx` d'exiftool pour `©xxx`, clés QuickTime sans `com.apple.quicktime.`, éléments Matroska identifiés sans leurs bits de longueur, dates de `mvhd` et `DateUTC` converties depuis leur origine, textes RIFF relus en UTF-8, valeurs vides qu'exiftool relève et que les modules n'observent pas (genre ID3v1 255, UMID nul).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; option choisie par TheDarkMac au début du complément |
