# ADR-0275 — Transformés, retouchés et malformés fabriqués sur le poste par des scripts versionnés

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; opérations et effectifs précisés par l'assistant
- **Tâche** : T100
- **Exigences liées** : §8 du cahier, ES-22 ; ADR-0103, ADR-0104, ADR-0272, ADR-0274 ; A-12

## Contexte

Le §8 demande trois catégories dérivées : « transformés » (les authentiques et les générés après recompression, redimensionnement, capture d'écran, passage par une messagerie : robustesse), « retouchés » (fichiers authentiques modifiés, PDF édités, images retouchées : distinction entre retouche et génération) et « malformés » (fichiers tronqués, corrompus ou piégés : robustesse et sécurité). Il faut savoir exactement ce que chaque fichier a subi, et qu'un dérivé reste dans la partie de son original (A-12).

## Options envisagées

### Option A — Scripts locaux versionnés (recommandée)

- Avantages : chaque opération est connue, décrite au manifeste et refaisable ; retouches de documents possibles (PDF, DOCX, ODT) ; dérivé et original dans le même groupe.
- Inconvénients : capture d'écran et messagerie simulées, pas réelles ; retouches mécaniques, moins variées que celles d'une personne.

### Option B — Scripts et paires original/retouché de la catégorie « Retouched pictures » de Commons

- Avantages : des retouches réelles faites par des personnes.
- Inconvénients : nature des retouches non contrôlée, souvent un simple recadrage ou un réglage de couleurs ; original et retouché versés par des comptes différents, à rapprocher à la main.

### Option C — Retouches de Commons seulement

- Avantages : retouches réelles.
- Inconvénients : aucune retouche de document ; mêmes défauts que l'option B.

## Décision

Option A, scripts `reference_4_derives.py` (ImageMagick, ffmpeg, Ghostscript, LibreOffice en conversion) et `reference_5_libreoffice.py` (LibreOffice par son interface, UNO). Opérations, précisées par l'assistant :

| Famille | Transformations (chaque original tiré les subit toutes) | Retouches (une par original tiré, à tour de rôle) |
| --- | --- | --- |
| Image | JPEG de qualité 75 ; réduction de moitié ; capture d'écran simulée (au plus 1920 par 1080, sans métadonnées, PNG) ; messagerie simulée (au plus 1600 pixels, sans métadonnées, JPEG de qualité 80) ; conversion en HEIC | clonage d'une zone ; collage d'une pièce d'un autre original de la même partie ; effacement par flou ; légende ajoutée ; JPEG réenregistré en qualité 92, métadonnées de l'original gardées comme le font la plupart des éditeurs |
| PDF | réécriture par Ghostscript (« ebook ») ; pages rendues en images à 150 ppp | rectangle et montant posés sur la première page, PDF réécrit par Ghostscript ; zone de texte ajoutée dans LibreOffice Draw, PDF exporté |
| Audio | réencodage dans le même format, à qualité moindre ; conversion en AAC (M4A) | passage central retiré, morceaux recollés |
| Vidéo | réencodage VP9 de qualité moindre ; conversion en H.264 et AAC (MP4) | passage central retiré, morceaux recollés |
| Bureautique | conversion DOCX ↔ ODT par LibreOffice ; export PDF | paragraphe tapé à la fin par l'interface ; premier nombre ou premier mot long remplacé ; enregistré dans le même format |
| Texte | fins de ligne CRLF ; texte enregistré en DOCX par LibreOffice | paragraphe d'un autre texte de la même partie inséré ; chiffres changés |

| Malformés | Choix |
| --- | --- |
| Dérivés | Troncature à la moitié, 32 bits inversés dans le tiers central, ou octets 4 à 35 remplacés (signature de format gardée), à tour de rôle ; même origine et même groupe que l'original |
| Pièges | Onze fichiers fabriqués de toutes pièces, sans origine : PNG de 20 000 par 20 000 pixels, JPEG qui annonce 65 500 par 65 500 pixels, DOCX et ODT dont la partie principale fait 1 Gio décompressée, PDF à 100 000 niveaux d'imbrication, PDF dont l'arbre des pages boucle, étiquette ID3 et tailles WAV qui débordent, WebM à 10 000 niveaux, texte d'un million de diacritiques, texte en UTF-8 invalide |

Effectifs d'originaux tirés pour les dérivés (transformés, retouchés, malformés) : JPEG 100, 100, 20 ; PNG 30, 30, 10 ; WebP 20, 20, 5 ; images générées 120, 0, 10 ; PDF 60, 60, 20 ; MP3 et WAV 20, 15, 5 ; Ogg et FLAC 10, 10, 5 ; WebM 60, 30, 15 ; DOCX 45, 45, 15 ; ODT 15, 15, 5 ; texte 60, 60, 10. Tirages à la graine 100, indépendants pour chaque catégorie.

## Raisons

- Option A retenue : la seule où chaque retouche est connue, et où les documents ont des retouches.
- Option B écartée : la vérité des paires de Commons demanderait un rapprochement manuel, et leurs retouches mesurent surtout le recadrage.
- Option C écartée : pas de PDF ni de document retouché, alors que le §8 les cite.
- Retouches par l'interface de LibreOffice : un paragraphe tapé passe par le même chemin qu'une saisie au clavier (méthode de T81), et laisse les traces qu'une édition réelle laisse.
- Collage pris dans la même partie : une pièce d'un original de l'évaluation ne doit pas entrer au calibrage.
- Pièges fabriqués : le §8 demande des fichiers « piégés » ; chacun vise une limite de T14 (taille décompressée, profondeur, boucle, débordement). Essayés sur `vk` pendant T100 : aucun arrêt brutal, deux refusés comme format non reconnu.

## Conséquences

- La transformation de chaque transformé est inscrite au manifeste (`transformation`) ; la description complète de chaque dérivé (opération, outil et version) est dans sa provenance.
- Les formats M4A, MP4 et HEIC n'existent au corpus que comme transformés (ADR-0272).
- Les retouches mécaniques sous-estiment peut-être la difficulté : une personne qui retouche avec soin laisse moins de traces. T102 (équipe rouge) fabrique les retouches soignées.
- Un dérivé dont la fabrication échoue (original qu'ImageMagick, ffmpeg, Ghostscript ou LibreOffice ne sait pas lire) est écarté, avec sa raison, dans `effectifs.json`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
