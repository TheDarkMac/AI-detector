# Évaluation du corpus reference 1.0.0

- Date : 2026-11-26T17:56:49Z
- Corpus : reference 1.0.0 du 2026-11-26 (reference), manifeste 055a8becce9fbf5a7c656341014145c020fa2e5ffe3de53535fda8ecec0a76d7
- Partie : evaluation
- Outil : 0.1.0.dev0 ; catalogue 0.20.1 du 2026-11-25, empreinte a89ff522b3458daedec28588a65b40f0c7be26c57c0934ff1ca5f746a14b43e2
- Techniques : actifsbureau 0.1.0, actifspdf 0.1.0, c2pa 0.1.0, caracteres 0.3.0, doublejpeg 0.1.0, dwtdct 0.1.0, ela 0.1.0, exif 0.4.0, historique 0.1.0, id3 0.3.0, image 0.3.0, imagesbureau 0.1.0, imagespdf 0.1.0, infopdf 0.3.0, infowav 0.3.0, iptc 0.4.0, matroska 0.3.0, odf 0.3.1, ooxml 0.3.1, pagespdf 0.1.0, quicktime 0.3.0, revisionspdf 0.2.0, textepng 0.4.0, vorbis 0.3.0, xmp 0.7.1
- Réseau : interfaces lo, 0 tentative de connexion
- Intervalles : Wilson, confiance 95,0 % ; niveau « fort » jusqu'à 1,0 %, « modéré » jusqu'à 5,0 % (borne supérieure)

## Fichiers

| Catégorie | Fichiers |
| --- | --- |
| Authentiques | 2385 |
| Générés | 424 |
| Transformés | 1294 |
| Retouchés | 273 |
| Malformés | 91 |
| Total | 4467 |

Refus : format_inconnu (21), hors_perimetre (1). Arrêts brutaux : ValueError (1). Analyses interrompues : 3. Fichiers dont les deux analyses diffèrent : 0.

## Taux par fichier (ADR-0018)

Part des fichiers authentiques analysés dont le rapport porte une preuve, ou un indice modéré ou fort, dirigé vers l'origine IA ou la retouche.

| Catégorie | Taux |
| --- | --- |
| Authentiques | 0/2384 : 0,0 % [0,0 % ; 0,2 %] |
| Transformés | 0/914 : 0,0 % [0,0 % ; 0,4 %] |

Cible : borne supérieure au plus 5,0 % sur les authentiques ; atteinte.

## Techniques (§8 du cahier)

| Technique | Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| actifsbureau | Authentiques | 2385 | 2297 | 2/88 : 2,3 % [0,6 % ; 7,9 %] | 0/86 : 0,0 % [0,0 % ; 4,3 %] | — | 0 |
| actifsbureau | Générés | 424 | 372 | 0/52 : 0,0 % [0,0 % ; 6,9 %] | — | 52/52 : 100,0 % [93,1 % ; 100,0 %] | 0 |
| actifsbureau | Transformés | 1294 | 1210 | 1/84 : 1,2 % [0,2 % ; 6,4 %] | 0/83 : 0,0 % [0,0 % ; 4,4 %] | — | 0 |
| actifsbureau | Retouchés | 273 | 233 | 1/40 : 2,5 % [0,4 % ; 12,9 %] | — | 39/39 : 100,0 % [91,0 % ; 100,0 %] | 0 |
| actifsbureau | Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/8 : 0,0 % [0,0 % ; 32,4 %] | — | 0 |
| actifspdf | Authentiques | 2385 | 1985 | 3/400 : 0,8 % [0,3 % ; 2,2 %] | 0/397 : 0,0 % [0,0 % ; 1,0 %] | — | 0 |
| actifspdf | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| actifspdf | Transformés | 1294 | 1178 | 0/116 : 0,0 % [0,0 % ; 3,2 %] | 0/116 : 0,0 % [0,0 % ; 3,2 %] | — | 0 |
| actifspdf | Retouchés | 273 | 230 | 0/43 : 0,0 % [0,0 % ; 8,2 %] | — | 43/43 : 100,0 % [91,8 % ; 100,0 %] | 0 |
| actifspdf | Malformés | 91 | 57 | 28/34 : 82,4 % [66,5 % ; 91,7 %] | 0/6 : 0,0 % [0,0 % ; 39,0 %] | — | 0 |
| c2pa | Authentiques | 2385 | 941 | 1/1444 : 0,1 % [0,0 % ; 0,4 %] | 0/1443 : 0,0 % [0,0 % ; 0,3 %] | — | 0 |
| c2pa | Générés | 424 | 26 | 0/398 : 0,0 % [0,0 % ; 1,0 %] | — | 371/398 : 93,2 % [90,3 % ; 95,3 %] | 1 |
| c2pa | Transformés | 1294 | 100 | 0/1194 : 0,0 % [0,0 % ; 0,3 %] | 0/814 : 0,0 % [0,0 % ; 0,5 %] | 380/380 : 100,0 % [99,0 % ; 100,0 %] | 0 |
| c2pa | Retouchés | 273 | 73 | 0/200 : 0,0 % [0,0 % ; 1,9 %] | — | 200/200 : 100,0 % [98,1 % ; 100,0 %] | 0 |
| c2pa | Malformés | 91 | 15 | 29/76 : 38,2 % [28,1 % ; 49,4 %] | 0/39 : 0,0 % [0,0 % ; 9,0 %] | 5/5 : 100,0 % [56,6 % ; 100,0 %] | 0 |
| caracteres | Authentiques | 2385 | 1438 | 7/947 : 0,7 % [0,4 % ; 1,5 %] | 0/940 : 0,0 % [0,0 % ; 0,4 %] | — | 0 |
| caracteres | Générés | 424 | 320 | 0/104 : 0,0 % [0,0 % ; 3,6 %] | — | 104/104 : 100,0 % [96,4 % ; 100,0 %] | 0 |
| caracteres | Transformés | 1294 | 1050 | 0/244 : 0,0 % [0,0 % ; 1,5 %] | 0/244 : 0,0 % [0,0 % ; 1,5 %] | — | 0 |
| caracteres | Retouchés | 273 | 149 | 0/124 : 0,0 % [0,0 % ; 3,0 %] | — | 124/124 : 100,0 % [97,0 % ; 100,0 %] | 0 |
| caracteres | Malformés | 91 | 44 | 28/47 : 59,6 % [45,3 % ; 72,4 %] | 0/18 : 0,0 % [0,0 % ; 17,6 %] | — | 0 |
| doublejpeg | Authentiques | 2385 | 1776 | 1/609 : 0,2 % [0,0 % ; 0,9 %] | 0/608 : 0,0 % [0,0 % ; 0,6 %] | — | 0 |
| doublejpeg | Générés | 424 | 330 | 0/94 : 0,0 % [0,0 % ; 3,9 %] | — | 94/94 : 100,0 % [96,1 % ; 100,0 %] | 0 |
| doublejpeg | Transformés | 1294 | 781 | 0/513 : 0,0 % [0,0 % ; 0,7 %] | 0/335 : 0,0 % [0,0 % ; 1,1 %] | 178/178 : 100,0 % [97,9 % ; 100,0 %] | 0 |
| doublejpeg | Retouchés | 273 | 162 | 0/111 : 0,0 % [0,0 % ; 3,3 %] | — | 111/111 : 100,0 % [96,7 % ; 100,0 %] | 0 |
| doublejpeg | Malformés | 91 | 46 | 33/45 : 73,3 % [59,0 % ; 84,0 %] | 0/12 : 0,0 % [0,0 % ; 24,2 %] | — | 0 |
| dwtdct | Authentiques | 2385 | 1559 | 74/826 : 9,0 % [7,2 % ; 11,1 %] | 0/752 : 0,0 % [0,0 % ; 0,5 %] | — | 0 |
| dwtdct | Générés | 424 | 104 | 24/320 : 7,5 % [5,1 % ; 10,9 %] | — | 295/296 : 99,7 % [98,1 % ; 99,9 %] | 0 |
| dwtdct | Transformés | 1294 | 343 | 195/951 : 20,5 % [18,1 % ; 23,2 %] | 0/459 : 0,0 % [0,0 % ; 0,8 %] | 295/297 : 99,3 % [97,6 % ; 99,8 %] | 0 |
| dwtdct | Retouchés | 273 | 120 | 15/153 : 9,8 % [6,0 % ; 15,5 %] | — | 138/138 : 100,0 % [97,3 % ; 100,0 %] | 0 |
| dwtdct | Malformés | 91 | 39 | 44/52 : 84,6 % [72,5 % ; 92,0 %] | 0/8 : 0,0 % [0,0 % ; 32,4 %] | — | 0 |
| ela | Authentiques | 2385 | 1776 | 1/609 : 0,2 % [0,0 % ; 0,9 %] | 0/608 : 0,0 % [0,0 % ; 0,6 %] | — | 0 |
| ela | Générés | 424 | 330 | 0/94 : 0,0 % [0,0 % ; 3,9 %] | — | 94/94 : 100,0 % [96,1 % ; 100,0 %] | 0 |
| ela | Transformés | 1294 | 781 | 0/513 : 0,0 % [0,0 % ; 0,7 %] | 0/335 : 0,0 % [0,0 % ; 1,1 %] | 178/178 : 100,0 % [97,9 % ; 100,0 %] | 0 |
| ela | Retouchés | 273 | 162 | 0/111 : 0,0 % [0,0 % ; 3,3 %] | — | 111/111 : 100,0 % [96,7 % ; 100,0 %] | 0 |
| ela | Malformés | 91 | 46 | 36/45 : 80,0 % [66,2 % ; 89,1 %] | 0/9 : 0,0 % [0,0 % ; 29,9 %] | — | 0 |
| exif | Authentiques | 2385 | 1559 | 1/826 : 0,1 % [0,0 % ; 0,7 %] | 0/825 : 0,0 % [0,0 % ; 0,5 %] | — | 0 |
| exif | Générés | 424 | 104 | 0/320 : 0,0 % [0,0 % ; 1,2 %] | — | 320/320 : 100,0 % [98,8 % ; 100,0 %] | 0 |
| exif | Transformés | 1294 | 343 | 0/951 : 0,0 % [0,0 % ; 0,4 %] | 0/571 : 0,0 % [0,0 % ; 0,7 %] | 380/380 : 100,0 % [99,0 % ; 100,0 %] | 0 |
| exif | Retouchés | 273 | 120 | 0/153 : 0,0 % [0,0 % ; 2,4 %] | — | 153/153 : 100,0 % [97,6 % ; 100,0 %] | 0 |
| exif | Malformés | 91 | 39 | 22/52 : 42,3 % [29,9 % ; 55,8 %] | 0/23 : 0,0 % [0,0 % ; 14,3 %] | 6/6 : 100,0 % [61,0 % ; 100,0 %] | 0 |
| historique | Authentiques | 2385 | 2297 | 2/88 : 2,3 % [0,6 % ; 7,9 %] | 0/86 : 0,0 % [0,0 % ; 4,3 %] | — | 0 |
| historique | Générés | 424 | 372 | 0/52 : 0,0 % [0,0 % ; 6,9 %] | — | 52/52 : 100,0 % [93,1 % ; 100,0 %] | 0 |
| historique | Transformés | 1294 | 1210 | 1/84 : 1,2 % [0,2 % ; 6,4 %] | 0/83 : 0,0 % [0,0 % ; 4,4 %] | — | 0 |
| historique | Retouchés | 273 | 233 | 1/40 : 2,5 % [0,4 % ; 12,9 %] | — | 39/39 : 100,0 % [91,0 % ; 100,0 %] | 0 |
| historique | Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/8 : 0,0 % [0,0 % ; 32,4 %] | — | 0 |
| id3 | Authentiques | 2385 | 2024 | 2/361 : 0,6 % [0,2 % ; 2,0 %] | 0/359 : 0,0 % [0,0 % ; 1,1 %] | — | 0 |
| id3 | Générés | 424 | 424 | — | — | — | 0 |
| id3 | Transformés | 1294 | 1260 | 1/34 : 2,9 % [0,5 % ; 14,9 %] | 0/33 : 0,0 % [0,0 % ; 10,4 %] | — | 0 |
| id3 | Retouchés | 273 | 248 | 1/25 : 4,0 % [0,7 % ; 19,5 %] | — | 24/24 : 100,0 % [86,2 % ; 100,0 %] | 0 |
| id3 | Malformés | 91 | 59 | 22/32 : 68,8 % [51,4 % ; 82,0 %] | 0/10 : 0,0 % [0,0 % ; 27,8 %] | — | 0 |
| image | Authentiques | 2385 | 1559 | 1/826 : 0,1 % [0,0 % ; 0,7 %] | 0/825 : 0,0 % [0,0 % ; 0,5 %] | — | 0 |
| image | Générés | 424 | 104 | 0/320 : 0,0 % [0,0 % ; 1,2 %] | — | 320/320 : 100,0 % [98,8 % ; 100,0 %] | 0 |
| image | Transformés | 1294 | 518 | 0/776 : 0,0 % [0,0 % ; 0,5 %] | 0/472 : 0,0 % [0,0 % ; 0,8 %] | 304/304 : 100,0 % [98,8 % ; 100,0 %] | 0 |
| image | Retouchés | 273 | 120 | 0/153 : 0,0 % [0,0 % ; 2,4 %] | — | 153/153 : 100,0 % [97,6 % ; 100,0 %] | 0 |
| image | Malformés | 91 | 39 | 28/52 : 53,8 % [40,5 % ; 66,7 %] | 0/19 : 0,0 % [0,0 % ; 16,8 %] | 4/4 : 100,0 % [51,0 % ; 100,0 %] | 0 |
| imagesbureau | Authentiques | 2385 | 2297 | 2/88 : 2,3 % [0,6 % ; 7,9 %] | 0/86 : 0,0 % [0,0 % ; 4,3 %] | — | 0 |
| imagesbureau | Générés | 424 | 372 | 0/52 : 0,0 % [0,0 % ; 6,9 %] | — | 52/52 : 100,0 % [93,1 % ; 100,0 %] | 0 |
| imagesbureau | Transformés | 1294 | 1210 | 1/84 : 1,2 % [0,2 % ; 6,4 %] | 0/83 : 0,0 % [0,0 % ; 4,4 %] | — | 0 |
| imagesbureau | Retouchés | 273 | 233 | 1/40 : 2,5 % [0,4 % ; 12,9 %] | — | 39/39 : 100,0 % [91,0 % ; 100,0 %] | 0 |
| imagesbureau | Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/8 : 0,0 % [0,0 % ; 32,4 %] | — | 0 |
| imagespdf | Authentiques | 2385 | 1985 | 3/400 : 0,8 % [0,3 % ; 2,2 %] | 0/397 : 0,0 % [0,0 % ; 1,0 %] | — | 0 |
| imagespdf | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| imagespdf | Transformés | 1294 | 1178 | 0/116 : 0,0 % [0,0 % ; 3,2 %] | 0/116 : 0,0 % [0,0 % ; 3,2 %] | — | 0 |
| imagespdf | Retouchés | 273 | 230 | 0/43 : 0,0 % [0,0 % ; 8,2 %] | — | 43/43 : 100,0 % [91,8 % ; 100,0 %] | 0 |
| imagespdf | Malformés | 91 | 57 | 28/34 : 82,4 % [66,5 % ; 91,7 %] | 0/6 : 0,0 % [0,0 % ; 39,0 %] | — | 0 |
| infopdf | Authentiques | 2385 | 1985 | 1/400 : 0,2 % [0,0 % ; 1,4 %] | 0/399 : 0,0 % [0,0 % ; 1,0 %] | — | 0 |
| infopdf | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| infopdf | Transformés | 1294 | 1178 | 0/116 : 0,0 % [0,0 % ; 3,2 %] | 0/116 : 0,0 % [0,0 % ; 3,2 %] | — | 0 |
| infopdf | Retouchés | 273 | 230 | 0/43 : 0,0 % [0,0 % ; 8,2 %] | — | 43/43 : 100,0 % [91,8 % ; 100,0 %] | 0 |
| infopdf | Malformés | 91 | 57 | 22/34 : 64,7 % [47,9 % ; 78,5 %] | 0/10 : 0,0 % [0,0 % ; 27,8 %] | — | 0 |
| infowav | Authentiques | 2385 | 2250 | 2/135 : 1,5 % [0,4 % ; 5,2 %] | 0/133 : 0,0 % [0,0 % ; 2,8 %] | — | 0 |
| infowav | Générés | 424 | 424 | — | — | — | 0 |
| infowav | Transformés | 1294 | 1280 | 1/14 : 7,1 % [1,3 % ; 31,5 %] | 0/13 : 0,0 % [0,0 % ; 22,8 %] | — | 0 |
| infowav | Retouchés | 273 | 259 | 1/14 : 7,1 % [1,3 % ; 31,5 %] | — | 13/13 : 100,0 % [77,2 % ; 100,0 %] | 0 |
| infowav | Malformés | 91 | 66 | 22/25 : 88,0 % [70,0 % ; 95,8 %] | 0/3 : 0,0 % [0,0 % ; 56,1 %] | — | 0 |
| iptc | Authentiques | 2385 | 1776 | 1/609 : 0,2 % [0,0 % ; 0,9 %] | 0/608 : 0,0 % [0,0 % ; 0,6 %] | — | 0 |
| iptc | Générés | 424 | 330 | 0/94 : 0,0 % [0,0 % ; 3,9 %] | — | 94/94 : 100,0 % [96,1 % ; 100,0 %] | 0 |
| iptc | Transformés | 1294 | 781 | 0/513 : 0,0 % [0,0 % ; 0,7 %] | 0/335 : 0,0 % [0,0 % ; 1,1 %] | 178/178 : 100,0 % [97,9 % ; 100,0 %] | 0 |
| iptc | Retouchés | 273 | 162 | 0/111 : 0,0 % [0,0 % ; 3,3 %] | — | 111/111 : 100,0 % [96,7 % ; 100,0 %] | 0 |
| iptc | Malformés | 91 | 46 | 22/45 : 48,9 % [35,0 % ; 63,0 %] | 0/20 : 0,0 % [0,0 % ; 16,1 %] | 2/2 : 100,0 % [34,2 % ; 100,0 %] | 0 |
| matroska | Authentiques | 2385 | 1983 | 2/402 : 0,5 % [0,1 % ; 1,8 %] | 0/400 : 0,0 % [0,0 % ; 1,0 %] | — | 0 |
| matroska | Générés | 424 | 424 | — | — | — | 0 |
| matroska | Transformés | 1294 | 1246 | 1/48 : 2,1 % [0,4 % ; 10,9 %] | 0/47 : 0,0 % [0,0 % ; 7,6 %] | — | 0 |
| matroska | Retouchés | 273 | 248 | 1/25 : 4,0 % [0,7 % ; 19,5 %] | — | 24/24 : 100,0 % [86,2 % ; 100,0 %] | 0 |
| matroska | Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/7 : 0,0 % [0,0 % ; 35,4 %] | — | 0 |
| odf | Authentiques | 2385 | 2350 | 2/35 : 5,7 % [1,6 % ; 18,6 %] | 0/33 : 0,0 % [0,0 % ; 10,4 %] | — | 0 |
| odf | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| odf | Transformés | 1294 | 1262 | 1/32 : 3,1 % [0,6 % ; 15,7 %] | 0/31 : 0,0 % [0,0 % ; 11,0 %] | — | 0 |
| odf | Retouchés | 273 | 264 | 1/9 : 11,1 % [2,0 % ; 43,5 %] | — | 8/8 : 100,0 % [67,6 % ; 100,0 %] | 0 |
| odf | Malformés | 91 | 67 | 22/24 : 91,7 % [74,2 % ; 97,7 %] | 0/2 : 0,0 % [0,0 % ; 65,8 %] | — | 0 |
| ooxml | Authentiques | 2385 | 2330 | 2/55 : 3,6 % [1,0 % ; 12,3 %] | 0/53 : 0,0 % [0,0 % ; 6,8 %] | — | 0 |
| ooxml | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| ooxml | Transformés | 1294 | 1241 | 1/53 : 1,9 % [0,3 % ; 9,9 %] | 0/52 : 0,0 % [0,0 % ; 6,9 %] | — | 0 |
| ooxml | Retouchés | 273 | 241 | 1/32 : 3,1 % [0,6 % ; 15,7 %] | — | 31/31 : 100,0 % [89,0 % ; 100,0 %] | 0 |
| ooxml | Malformés | 91 | 63 | 22/28 : 78,6 % [60,5 % ; 89,8 %] | 0/6 : 0,0 % [0,0 % ; 39,0 %] | — | 0 |
| pagespdf | Authentiques | 2385 | 1985 | 3/400 : 0,8 % [0,3 % ; 2,2 %] | 50/397 : 12,6 % [9,7 % ; 16,2 %] | — | 0 |
| pagespdf | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| pagespdf | Transformés | 1294 | 1178 | 0/116 : 0,0 % [0,0 % ; 3,2 %] | 15/116 : 12,9 % [8,0 % ; 20,2 %] | — | 0 |
| pagespdf | Retouchés | 273 | 230 | 0/43 : 0,0 % [0,0 % ; 8,2 %] | — | 34/43 : 79,1 % [64,8 % ; 88,6 %] | 0 |
| pagespdf | Malformés | 91 | 57 | 28/34 : 82,4 % [66,5 % ; 91,7 %] | 1/6 : 16,7 % [3,0 % ; 56,4 %] | — | 0 |
| quicktime | Authentiques | 2385 | 2383 | 2/2 : 100,0 % [34,2 % ; 100,0 %] | — | — | 0 |
| quicktime | Générés | 424 | 424 | — | — | — | 0 |
| quicktime | Transformés | 1294 | 1206 | 1/88 : 1,1 % [0,2 % ; 6,2 %] | 0/87 : 0,0 % [0,0 % ; 4,2 %] | — | 0 |
| quicktime | Retouchés | 273 | 272 | 1/1 : 100,0 % [20,7 % ; 100,0 %] | — | — | 0 |
| quicktime | Malformés | 91 | 69 | 22/22 : 100,0 % [85,1 % ; 100,0 %] | — | — | 0 |
| revisionspdf | Authentiques | 2385 | 1985 | 1/400 : 0,2 % [0,0 % ; 1,4 %] | 54/399 : 13,5 % [10,5 % ; 17,2 %] | — | 0 |
| revisionspdf | Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| revisionspdf | Transformés | 1294 | 1178 | 0/116 : 0,0 % [0,0 % ; 3,2 %] | 0/116 : 0,0 % [0,0 % ; 3,2 %] | — | 0 |
| revisionspdf | Retouchés | 273 | 230 | 0/43 : 0,0 % [0,0 % ; 8,2 %] | — | 43/43 : 100,0 % [91,8 % ; 100,0 %] | 0 |
| revisionspdf | Malformés | 91 | 57 | 28/34 : 82,4 % [66,5 % ; 91,7 %] | 0/6 : 0,0 % [0,0 % ; 39,0 %] | — | 0 |
| textepng | Authentiques | 2385 | 2215 | 2/170 : 1,2 % [0,3 % ; 4,2 %] | 0/168 : 0,0 % [0,0 % ; 2,2 %] | — | 0 |
| textepng | Générés | 424 | 220 | 0/204 : 0,0 % [0,0 % ; 1,8 %] | — | 198/204 : 97,1 % [93,7 % ; 98,6 %] | 0 |
| textepng | Transformés | 1294 | 1045 | 1/249 : 0,4 % [0,1 % ; 2,2 %] | 0/129 : 0,0 % [0,0 % ; 2,9 %] | 118/119 : 99,2 % [95,4 % ; 99,9 %] | 0 |
| textepng | Retouchés | 273 | 239 | 1/34 : 2,9 % [0,5 % ; 14,9 %] | — | 33/33 : 100,0 % [89,6 % ; 100,0 %] | 0 |
| textepng | Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/4 : 0,0 % [0,0 % ; 49,0 %] | 4/4 : 100,0 % [51,0 % ; 100,0 %] | 0 |
| vorbis | Authentiques | 2385 | 2223 | 2/162 : 1,2 % [0,3 % ; 4,4 %] | 0/160 : 0,0 % [0,0 % ; 2,3 %] | — | 0 |
| vorbis | Générés | 424 | 424 | — | — | — | 0 |
| vorbis | Transformés | 1294 | 1278 | 1/16 : 6,2 % [1,1 % ; 28,3 %] | 0/15 : 0,0 % [0,0 % ; 20,4 %] | — | 0 |
| vorbis | Retouchés | 273 | 261 | 1/12 : 8,3 % [1,5 % ; 35,4 %] | — | 11/11 : 100,0 % [74,1 % ; 100,0 %] | 0 |
| vorbis | Malformés | 91 | 64 | 22/27 : 81,5 % [63,3 % ; 91,8 %] | 0/5 : 0,0 % [0,0 % ; 43,4 %] | — | 0 |
| xmp | Authentiques | 2385 | 1179 | 1/1206 : 0,1 % [0,0 % ; 0,5 %] | 0/1205 : 0,0 % [0,0 % ; 0,3 %] | — | 0 |
| xmp | Générés | 424 | 78 | 0/346 : 0,0 % [0,0 % ; 1,1 %] | — | 341/346 : 98,6 % [96,7 % ; 99,4 %] | 1 |
| xmp | Transformés | 1294 | 172 | 0/1122 : 0,0 % [0,0 % ; 0,3 %] | 0/742 : 0,0 % [0,0 % ; 0,5 %] | 374/380 : 98,4 % [96,6 % ; 99,3 %] | 0 |
| xmp | Retouchés | 273 | 92 | 0/181 : 0,0 % [0,0 % ; 2,1 %] | — | 181/181 : 100,0 % [97,9 % ; 100,0 %] | 0 |
| xmp | Malformés | 91 | 27 | 22/64 : 34,4 % [23,9 % ; 46,6 %] | 0/33 : 0,0 % [0,0 % ; 10,4 %] | 6/6 : 100,0 % [61,0 % ; 100,0 %] | 0 |

## Règles (ADR-0101)

| Règle | Catégorie | Direction | Niveau | Faux positifs | Niveau permis |
| --- | --- | --- | --- | --- | --- |
| R-C2PA-001 v1 (c2pa) | preuve | origine_ia | — | 0/1443 : 0,0 % [0,0 % ; 0,3 %] | — |
| R-C2PA-002 v1 (c2pa) | preuve | retouche | — | 0/1443 : 0,0 % [0,0 % ; 0,3 %] | — |
| R-C2PA-003 v1 (c2pa) | preuve | authenticite | — | 0/598 : 0,0 % [0,0 % ; 0,6 %] | — |
| R-C2PA-004 v1 (c2pa) | indice | origine_ia | faible, non évaluée | 0/1443 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-C2PA-005 v1 (c2pa) | indice | retouche | faible, non évaluée | 0/1443 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-C2PA-006 v1 (c2pa) | indice | transformation | faible, non évaluée | 0/1443 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-DOUBLEJPEG-001 v1 (doublejpeg) | indice | transformation | faible, non évaluée | 27/608 : 4,4 % [3,1 % ; 6,4 %] | faible |
| R-DWTDCT-001 v1 (dwtdct) | indice | origine_ia | faible, non évaluée | 0/752 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-DWTDCT-002 v1 (dwtdct) | indice | origine_ia | faible, non évaluée | 0/752 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-DWTDCT-003 v1 (dwtdct) | indice | origine_ia | faible, non évaluée | 0/752 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-EXIF-001 v1 (exif) | indice | origine_ia | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-EXIF-002 v1 (exif) | indice | origine_ia | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-EXIF-014 v1 (exif) | indice | transformation | faible, non évaluée | 2/825 : 0,2 % [0,1 % ; 0,9 %] | fort |
| R-ID3-001 v1 (id3) | indice | origine_ia | faible, non évaluée | 0/359 : 0,0 % [0,0 % ; 1,1 %] | modere |
| R-IMAGE-001 v1 (image) | indice | transformation | faible, non évaluée | 11/825 : 1,3 % [0,7 % ; 2,4 %] | modere |
| R-IMAGE-002 v1 (image) | indice | transformation | faible, non évaluée | 2/825 : 0,2 % [0,1 % ; 0,9 %] | fort |
| R-IMAGE-003 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-004 v2 (image) | indice | transformation | faible, non évaluée | 97/825 : 11,8 % [9,7 % ; 14,1 %] | faible |
| R-IMAGE-005 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-006 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-007 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-008 v1 (image) | indice | transformation | faible, non évaluée | 1/825 : 0,1 % [0,0 % ; 0,7 %] | fort |
| R-IMAGE-009 v1 (image) | indice | transformation | faible, non évaluée | 4/825 : 0,5 % [0,2 % ; 1,2 %] | modere |
| R-IMAGE-010 v1 (image) | indice | transformation | faible, non évaluée | 4/825 : 0,5 % [0,2 % ; 1,2 %] | modere |
| R-IMAGE-011 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-012 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-013 v1 (image) | indice | transformation | faible, non évaluée | 1/825 : 0,1 % [0,0 % ; 0,7 %] | fort |
| R-IMAGE-014 v1 (image) | indice | transformation | faible, non évaluée | 4/825 : 0,5 % [0,2 % ; 1,2 %] | modere |
| R-IMAGE-015 v1 (image) | indice | transformation | faible, non évaluée | 0/825 : 0,0 % [0,0 % ; 0,5 %] | fort |
| R-IMAGE-016 v1 (image) | indice | transformation | faible, non évaluée | 46/825 : 5,6 % [4,2 % ; 7,4 %] | faible |
| R-IMAGE-017 v1 (image) | indice | authenticite | faible, non évaluée | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort |
| R-IMAGE-018 v1 (image) | indice | authenticite | faible, non évaluée | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort |
| R-IMAGE-019 v1 (image) | indice | authenticite | faible, non évaluée | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort |
| R-IMAGE-020 v1 (image) | indice | authenticite | faible, non évaluée | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort |
| R-IMAGE-021 v1 (image) | indice | authenticite | faible, non évaluée | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort |
| R-IMAGE-022 v1 (image) | indice | authenticite | faible, non évaluée | 0/473 : 0,0 % [0,0 % ; 0,8 %] | fort |
| R-INFOPDF-001 v1 (infopdf) | indice | origine_ia | faible, non évaluée | 0/399 : 0,0 % [0,0 % ; 1,0 %] | fort |
| R-INFOPDF-002 v1 (infopdf) | indice | origine_ia | faible, non évaluée | 0/399 : 0,0 % [0,0 % ; 1,0 %] | fort |
| R-INFOWAV-001 v1 (infowav) | indice | origine_ia | faible, non évaluée | 0/133 : 0,0 % [0,0 % ; 2,8 %] | modere |
| R-IPTC-001 v1 (iptc) | indice | origine_ia | faible, non évaluée | 0/608 : 0,0 % [0,0 % ; 0,6 %] | fort |
| R-IPTC-003 v1 (iptc) | indice | transformation | faible, non évaluée | 0/608 : 0,0 % [0,0 % ; 0,6 %] | fort |
| R-MATROSKA-001 v1 (matroska) | indice | origine_ia | faible, non évaluée | 0/400 : 0,0 % [0,0 % ; 1,0 %] | fort |
| R-MATROSKA-002 v1 (matroska) | indice | origine_ia | faible, non évaluée | 0/400 : 0,0 % [0,0 % ; 1,0 %] | fort |
| R-ODF-001 v1 (odf) | indice | origine_ia | faible, non évaluée | 0/33 : 0,0 % [0,0 % ; 10,4 %] | faible |
| R-OOXML-001 v1 (ooxml) | indice | origine_ia | faible, non évaluée | 0/53 : 0,0 % [0,0 % ; 6,8 %] | faible |
| R-PAGESPDF-001 v1 (pagespdf) | indice | retouche | faible, non évaluée | 23/397 : 5,8 % [3,9 % ; 8,5 %] | faible |
| R-PAGESPDF-002 v1 (pagespdf) | indice | retouche | faible, non évaluée | 7/397 : 1,8 % [0,9 % ; 3,6 %] | modere |
| R-PAGESPDF-003 v1 (pagespdf) | indice | retouche | faible, non évaluée | 27/397 : 6,8 % [4,7 % ; 9,7 %] | faible |
| R-PAGESPDF-004 v1 (pagespdf) | indice | retouche | faible, non évaluée | 1/397 : 0,3 % [0,0 % ; 1,4 %] | modere |
| R-QUICKTIME-001 v1 (quicktime) | indice | origine_ia | faible, non évaluée | — | — |
| R-QUICKTIME-002 v1 (quicktime) | indice | origine_ia | faible, non évaluée | — | — |
| R-REVISIONSPDF-002 v1 (revisionspdf) | indice | retouche | faible, non évaluée | 54/399 : 13,5 % [10,5 % ; 17,2 %] | faible |
| R-REVISIONSPDF-003 v1 (revisionspdf) | indice | retouche | faible, non évaluée | 0/399 : 0,0 % [0,0 % ; 1,0 %] | fort |
| R-TEXTEPNG-001 v1 (textepng) | indice | origine_ia | faible, non évaluée | 0/168 : 0,0 % [0,0 % ; 2,2 %] | modere |
| R-TEXTEPNG-002 v1 (textepng) | indice | origine_ia | faible, non évaluée | 0/168 : 0,0 % [0,0 % ; 2,2 %] | modere |
| R-TEXTEPNG-003 v1 (textepng) | indice | origine_ia | faible, non évaluée | 0/168 : 0,0 % [0,0 % ; 2,2 %] | modere |
| R-TEXTEPNG-004 v1 (textepng) | indice | origine_ia | faible, non évaluée | 0/168 : 0,0 % [0,0 % ; 2,2 %] | modere |
| R-TEXTEPNG-005 v1 (textepng) | indice | origine_ia | faible, non évaluée | 0/168 : 0,0 % [0,0 % ; 2,2 %] | modere |
| R-TEXTEPNG-007 v1 (textepng) | indice | transformation | faible, non évaluée | 0/168 : 0,0 % [0,0 % ; 2,2 %] | modere |
| R-VORBIS-001 v1 (vorbis) | indice | origine_ia | faible, non évaluée | 0/160 : 0,0 % [0,0 % ; 2,3 %] | modere |
| R-XMP-001 v1 (xmp) | indice | origine_ia | faible, non évaluée | 0/1205 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-XMP-002 v1 (xmp) | indice | retouche | faible, non évaluée | 0/1205 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-XMP-003 v1 (xmp) | indice | retouche | faible, non évaluée | 0/1205 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-XMP-004 v1 (xmp) | indice | origine_ia | faible, non évaluée | 0/1205 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-XMP-005 v1 (xmp) | indice | origine_ia | faible, non évaluée | 0/1205 : 0,0 % [0,0 % ; 0,3 %] | fort |
| R-XMP-013 v1 (xmp) | indice | transformation | faible, non évaluée | 2/1205 : 0,2 % [0,0 % ; 0,6 %] | fort |

## Écarts

- authentiques/pdf/pdf-0371.pdf : arrêt brutal de l'analyse (ValueError)
