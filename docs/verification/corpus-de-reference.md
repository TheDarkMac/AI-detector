# Corpus de référence : description (livrable 5)

> Statut : **v1.1** ; v1.0 mergée avec T100, v1.1 proposée dans la PR de T101. Corpus décrit : `reference` **1.0.0**, du 2026-11-25. Document vivant : toute modification est inscrite à l'historique (§8).
> Décisions : [ADR-0272](../decisions/ADR-0272-corpus-reel-de-sources-libres.md) à [ADR-0276](../decisions/ADR-0276-manifeste-et-description-du-corpus.md) ; manifeste : [ADR-0103](../decisions/ADR-0103-manifeste-du-corpus.md) ; parties : [ADR-0016](../decisions/ADR-0016-frontiere-sans-ia.md).

Ce document décrit le corpus sur lequel le banc d'évaluation mesure les taux d'erreur de chaque technique (§8 du cahier). Les fichiers ne sont pas au dépôt : leur volume (7,7 Gio, dont 5,2 Gio téléchargés) et les licences qui demandent l'attribution et le partage à l'identique s'y opposent ; le livrable 5 est donc, pour l'instant, cette description et le manifeste qui désigne chaque fichier ([`banc/reference/corpus.toml`](../../banc/reference/corpus.toml)).

## 1. En bref

- **6 734 fichiers**, empreinte du manifeste `055a8becce9fbf5a7c656341014145c020fa2e5ffe3de53535fda8ecec0a76d7` ; **4 467 en évaluation**, 2 267 en calibrage.
- **Cinq catégories du §8** : 3 597 authentiques, 640 générés, 1 949 transformés, 407 retouchés, 141 malformés.
- **Six familles** : image (JPEG, PNG, WebP, et HEIC en transformé), PDF, audio (MP3, WAV, Ogg, FLAC, et M4A en transformé), vidéo (WebM, et MP4 en transformé), bureautique (DOCX, ODT), texte.
- **Authentiques en évaluation** : au moins 400 par famille (image 599, PDF 400, audio 439, vidéo 400, texte 461), sauf la bureautique (86), faute de source : data.gouv.fr n'a que 222 DOCX et ODT éligibles.
- **Évalué** par T101 : rapports publiés dans [`evaluations/`](evaluations/README.md) ; seule la partie évaluation fonde un taux.

## 2. Sources et droits

| Source | Ce qui en vient | Droits | Vérification |
| --- | --- | --- | --- |
| [Wikimedia Commons](https://commons.wikimedia.org/) | Authentiques JPEG, PNG, WebP, PDF, MP3, WAV, Ogg, FLAC, WebM ; images déclarées générées | Licence libre ou domaine public, citée pour chaque fichier ; page du fichier citée (attribution) | Empreinte SHA-1 publiée par Commons, vérifiée à chaque téléchargement |
| [data.gouv.fr](https://www.data.gouv.fr/) | Authentiques DOCX et ODT | Licence Ouverte 1.0 ou 2.0, CC BY, CC BY-SA, CC0, ODbL, ODC-By ou PDDL du jeu de données | Empreinte SHA-1 de la ressource, vérifiée quand data.gouv.fr la publie |
| [Wikipédia en français](https://fr.wikipedia.org/) | Authentiques texte : paragraphes d'articles tirés au hasard | CC BY-SA 3.0 (révisions antérieures à 2023) ; révision citée | Révision fixe (`oldid`) |
| L'assistant (Claude Opus 5.5), pendant T100 | 40 textes générés, rendus en texte brut, DOCX, ODT, PDF | Licence du dépôt (Apache-2.0) | Textes au dépôt (`banc/reference/textes-ia/`), empreintes vérifiées par les tests |
| Le poste de TheDarkMac | Transformés, retouchés, malformés | Licence de l'original, pour un dérivé ; licence du dépôt pour un piège | Opération, outil et version dans la provenance |

Le manifeste ne cite aucun nom de compte ni d'auteur : la page de chaque fichier porte l'attribution (ADR-0276).

## 3. Ce que vaut l'origine de chaque fichier

| Catégorie | Origine au manifeste | Ce qui la fonde | Limite |
| --- | --- | --- | --- |
| Authentiques | `authentique` | Versé ou écrit avant le 2022-08-22 ; aucune catégorie de Commons qui dise une génération ou une retouche ; pour un JPEG, appareil déclaré et aucun logiciel d'édition déclaré | Une retouche non déclarée reste possible ; un PNG ou un WebP n'est pas forcément une capture d'appareil (schéma, carte, capture d'écran) |
| Générés (images) | `ia` | Rangée par son auteur dans l'arbre « AI-generated images » de Commons ; générateur lu dans ses catégories | **Déclarée, non vérifiée** : une image peut avoir été retouchée après génération, ou mal rangée |
| Générés (textes) | `ia` | Écrits par l'assistant pendant T100 | Un seul générateur |
| Transformés | celle de l'original | Fabriqués par les scripts à partir d'un original du corpus | Capture d'écran et messagerie simulées |
| Retouchés | `retouche` | Fabriqués par les scripts à partir d'un authentique | Retouches mécaniques, sans le soin d'une personne (T102) |
| Malformés | celle de l'original, ou aucune pour un piège | Fabriqués par les scripts | — |

## 4. Effectifs

Par catégorie et partie :

| Catégorie | Évaluation | Calibrage | Total |
| --- | --- | --- | --- |
| Authentiques | 2 385 | 1 212 | 3 597 |
| Générés | 424 | 216 | 640 |
| Transformés | 1 294 | 655 | 1 949 |
| Retouchés | 273 | 134 | 407 |
| Malformés | 91 | 50 | 141 |
| **Total** | **4 467** | **2 267** | **6 734** |

Authentiques par format (évaluation + calibrage) :

| Famille | Format | Évaluation | Calibrage | Source |
| --- | --- | --- | --- | --- |
| Image | JPEG | 400 | 200 | Commons, appareil déclaré, aucun logiciel d'édition |
| Image | PNG | 133 | 67 | Commons |
| Image | WebP | 66 | 34 | Commons |
| PDF | PDF | 400 | 200 | Commons |
| Audio | MP3 | 146 | 74 | Commons |
| Audio | WAV | 133 | 67 | Commons |
| Audio | Ogg | 80 | 40 | Commons |
| Audio | FLAC | 80 | 40 | Commons |
| Vidéo | WebM | 400 | 200 | Commons |
| Bureautique | DOCX | 53 | 27 | data.gouv.fr |
| Bureautique | ODT | 33 | 18 | data.gouv.fr |
| Texte | texte brut | 461 | 245 | Wikipédia |

Versement ou révision des authentiques : de 2005 à 2022, les deux tiers après 2017 (2018 : 298 ; 2019 : 302 ; 2020 : 477 ; 2021 : 649 ; 2022 : 678).

Générés :

| Origine | Formats | Évaluation | Calibrage |
| --- | --- | --- | --- |
| Images déclarées générées (Commons) | JPEG 144, PNG 301, WebP 35 | 320 | 160 |
| Textes de l'assistant | texte brut, DOCX, ODT, PDF (40 chacun) | 104 | 56 |

Générateurs des images, lus dans leurs catégories de Commons : non précisé 150, DALL-E sans version 111, Midjourney 61, GPT-4o ou GPT Image 52, Stable Diffusion sans version 36, Imagen ou Gemini 28, DALL-E 3 16, Craiyon 5, Grok 4, Dream (WOMBO) 3, NovelAI 3, Ideogram, FLUX.1, Leonardo.Ai, Firefly et Artbreeder 2 chacun, DALL-E 2 1. Versées de 2016 à 2026, les deux tiers depuis 2024.

Dérivés, par famille (les opérations sont dans [ADR-0275](../decisions/ADR-0275-derives-fabriques-par-scripts.md)) :

| Famille | Transformés | Retouchés | Malformés |
| --- | --- | --- | --- |
| Image | 1 350 (dont 270 HEIC) | 150 | 45 |
| PDF | 120 | 57 | 20 |
| Audio | 120 (dont 60 M4A) | 50 | 20 |
| Vidéo | 119 (dont 59 MP4) | 30 | 15 |
| Bureautique | 120 (dont 60 PDF) | 60 | 20 |
| Texte | 120 (dont 60 DOCX) | 60 | 10 |
| Pièges fabriqués | — | — | 11 |

Écartés au manifeste (`effectifs.json`) : trois retouches de PDF dans Draw (deux arrêts de LibreOffice, un document non ouvert) et une conversion MP4 au contenu identique à une autre. Écartés au téléchargement : 142 textes de moins de 500 caractères une fois les tableaux et listes ôtés, une révision de Wikipédia masquée depuis, un fichier que Commons ne servait plus.

## 5. Parties

Chaque original est son propre groupe, et ses dérivés le suivent. Dans chaque format, les originaux sont tirés dans un ordre fixé par la graine 100, et un sur trois va en calibrage (le premier, le quatrième…) ; la règle est écrite dans `banc/reference/reference_2_choix.py` et appliquée avant tout téléchargement (ADR-0274). La partie évaluation ne sert jamais à régler un seuil (ADR-0016).

## 6. Constitution

Six scripts, lancés dans l'ordre depuis la racine du dépôt avec l'interpréteur de l'environnement du projet (la phase 5 avec celui du système, où est le module `uno` de LibreOffice) :

```bash
.venv/bin/python -m banc.reference.reference_1_listes
```

```bash
.venv/bin/python -m banc.reference.reference_2_choix
```

```bash
.venv/bin/python -m banc.reference.reference_3_telechargements
```

```bash
.venv/bin/python -m banc.reference.reference_4_derives
```

```bash
python3 -I banc/reference/reference_5_libreoffice.py
```

```bash
.venv/bin/python -m banc.reference.reference_6_manifeste
```

| Phase | Ce qu'elle fait | Écrit (hors du dépôt, sauf mention) |
| --- | --- | --- |
| 1. Listes | Recherche de Commons triée au hasard (`gsrsort=random`, suivie par décalage), ressources DOCX et ODT de data.gouv.fr, articles de Wikipédia tirés au hasard et leur révision antérieure à la date limite | `listes.jsonl` |
| 2. Choix | Critères d'ADR-0273, tirage et plafonds, partie de chaque original | `choix.jsonl` |
| 3. Téléchargements | Originaux, empreinte de la source vérifiée ; textes de Wikipédia rendus par l'API ; plafond de 8 Gio | `authentiques/`, `generes/image/`, `telechargements.jsonl` |
| 4. Dérivés | Transformations, retouches (sauf LibreOffice), altérations, pièges, rendus des textes de l'assistant | `transformes/`, `retouches/`, `malformes/`, `generes/`, `derives.jsonl`, `uno.json` |
| 5. LibreOffice | Retouches par l'interface de LibreOffice (paragraphe tapé, remplacement, zone de texte dans Draw) | `retouches/`, `uno.resultats.json` |
| 6. Manifeste | Empreintes, fichiers en double écartés, manifeste relu par le banc et vérifié | `corpus.toml` et `effectifs.json` (au dépôt) |

Outils : Python 3.13 de l'environnement du projet ; ImageMagick 7.1.1-43 ; ffmpeg 7.1.5 ; Ghostscript 10.05.1 ; LibreOffice 25.2.3.2 et son module `uno`, sous Debian 13.

Un nouveau passage ne redonne pas le même corpus : Commons, data.gouv.fr et Wikipédia changent, et Ghostscript et LibreOffice écrivent des dates dans les fichiers. Il donne une nouvelle version du corpus, avec son manifeste.

## 7. Limites connues

- **Origine déclarée des images générées** : non vérifiée ; un faux négatif peut venir d'une image mal rangée, ou retouchée après sa génération.
- **Un seul générateur de texte** : les faux négatifs du texte et des documents générés valent pour l'assistant de T100, pas pour les autres.
- **Bureautique** : 86 authentiques en évaluation seulement, venus de 21 organisations de data.gouv.fr ; aucune règle des modules bureautiques ne peut y atteindre « fort » (381 fichiers sans faux positif).
- **Formats rares** : WebP (66), Ogg et FLAC (80 chacun) en évaluation ; MP4, MOV, M4A et HEIC n'ont aucun authentique ni généré, seulement des transformés.
- **Comptes concentrés** : PDF, sons et documents viennent de peu de comptes ou d'organisations (plafonds relevés à 10 et 50, ADR-0273) ; leurs fichiers se ressemblent plus qu'un tirage libre ne le donnerait.
- **Dérivés mécaniques** : capture d'écran et messagerie simulées ; retouches faites par des scripts, sans le soin d'une personne ; les retouches soignées sont l'objet de T102.
- **Sources qui changent** : Commons et data.gouv.fr évoluent ; un nouveau passage des scripts ne redonne pas ces fichiers, et les dérivés ne se refont pas à l'octet près.
- **Fichiers hors du dépôt** : la version 1.0.0 n'existe que sur le poste de TheDarkMac tant qu'aucune copie n'en est faite.

## 8. Historique

| Date | Version | Modification | Tâche |
| --- | --- | --- | --- |
| 2026-11-25 | 1.0 | Création : corpus `reference` 1.0.0 | T100 |
| 2026-11-27 | 1.1 | Total des parties corrigé, 4 467 en évaluation et 2 267 en calibrage (§1, §4, [ERR-0014](../errata/ERR-0014-total-des-parties-du-corpus.md)) ; corpus évalué, renvoi aux rapports (§1) | T101 |
