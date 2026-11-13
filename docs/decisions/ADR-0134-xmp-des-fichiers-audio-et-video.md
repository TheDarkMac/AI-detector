# ADR-0134 — XMP des fichiers audio et vidéo lu par `xmp`

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21 (complément audio et vidéo)
- **Exigences liées** : F-10, ES-05 ; ADR-0114, ADR-0116, ADR-0127

## Contexte

XMP (partie 3) prévoit son emplacement dans plusieurs conteneurs audio et vidéo : une boîte `uuid` de premier niveau (identifiant `BE7ACFCB-97A9-42E8-9C71-999491E3AFAC`) pour MP4 et M4A, une boîte `XMP_` de `moov/udta` pour MOV, un bloc `_PMX` pour WAV. Les logiciels d'Adobe y écrivent notamment `Iptc4xmpExt:DigitalSourceType`, que les règles d'origine IA déclarée de T22 liront. Le module `xmp` lit déjà les images et le PDF (ADR-0114, ADR-0127).

## Options envisagées

### Option A — Dans ce complément

`xmp` 0.3.0 : formats `wav`, `m4a`, `mp4`, `mov` ajoutés, paquets localisés par `conteneurs`.

- Avantages : `DigitalSourceType` d'une vidéo au rapport dès ce complément ; le lecteur ISOBMFF est écrit ici de toute façon ; le XML passe par le même lecteur sans DTD (ADR-0116).
- Inconvénients : une modification de plus à relire dans la PR.

### Option B — Plus tard, par un nouvel ADR

- Avantages : PR plus courte.
- Inconvénients : la couverture d'un MP4 dirait `xmp` « non applicable », ce qui est inexact.

## Décision

Option A. Emplacements : `uuid` XMP de premier niveau (M4A, MP4, MOV), `moov/udta/XMP_` (M4A, MP4, MOV), `_PMX` (WAV). Le XMP d'une trame ID3 `PRIV` (Adobe Audition) n'est pas lu (ADR-0132).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : couverture inexacte, et rien de plus à écrire plus tard.
- FLAC, Ogg, WebM, MP3 et AAC restent hors de `xmp` : aucun emplacement XMP n'y est normalisé ; « non applicable » y est exact.

## Conséquences

- `xmp` passe en 0.3.0 ; sa fiche liste les nouveaux emplacements.
- La rubrique Versions d'un rapport sur un WAV, un M4A, un MP4 ou un MOV cite expat (ADR-0120).
- Un `udta` mal formé est dit deux fois : par `quicktime`, qui lit `udta`, et par l'arrêt du parcours que `conteneurs` fait pour y chercher `XMP_`. Les deux modules gardent ainsi leurs erreurs séparées (ADR-0114).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; option choisie par TheDarkMac au début du complément |
