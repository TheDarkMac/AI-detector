# ADR-0130 — Complément audio et vidéo de T21 : les neuf formats en une branche

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21 (complément audio et vidéo)
- **Exigences liées** : F-10 ; ADR-0070, ADR-0123

## Contexte

ADR-0123 a réduit T21 au PDF et renvoyé à deux compléments, chacun dans sa branche : les balises des conteneurs audio et vidéo, puis les propriétés de DOCX et ODT. Le périmètre compte six formats audio (WAV, MP3, AAC, M4A, FLAC, Ogg) et trois formats vidéo (MP4, MOV, WebM), identifiés par le contenu depuis T13 (ADR-0070). Ils relèvent de cinq familles de balises : ID3, liste RIFF `INFO`, commentaires Vorbis, boîtes ISOBMFF et QuickTime, éléments Matroska. M4A, MP4 et MOV sont trois profils du même conteneur ISOBMFF.

## Options envisagées

### Option A — Les neuf formats dans cette branche

- Avantages : F-10 couverte pour l'audio et la vidéo en une fois ; le lecteur ISOBMFF, commun à M4A, MP4 et MOV, est relu une fois ; l'oracle compare tous les formats avec les mêmes outils.
- Inconvénients : une PR plus large que celle du PDF (cinq modules, cinq familles d'échantillons).

### Option B — L'audio d'abord, la vidéo dans un complément de plus

- Avantages : une PR plus courte.
- Inconvénients : la coupure ne suit pas les familles : M4A (audio) et MP4, MOV (vidéo) partagent leur lecteur, qui serait relu en deux fois ; un complément de plus pour T21.

## Décision

Option A : `tache/T21-extraction-audio-video` lit les balises des neuf formats audio et vidéo du périmètre.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : coupure artificielle d'un lecteur commun, et un complément de plus.

## Conséquences

- Le découpage passe en v0.20 : la ligne de T21 nomme ce complément réalisé ; reste DOCX et ODT.
- F-10 reste partielle dans la matrice jusqu'au complément bureautique.
- Modules, emplacements, noms, XMP et oracle : ADR-0131 à ADR-0135.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; option choisie par TheDarkMac au début du complément |
