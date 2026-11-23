# Fiches techniques

Une fiche par module d'analyse (NF-09, livrable 4), livrée avec son code, ses tests et ses règles : une technique n'est « terminée » qu'avec elle ([découpage](../00-plan/decoupage-taches.md), §1). Le manifeste de chaque module la cite (`fiche`, [ADR-0064](../decisions/ADR-0064-manifeste-des-modules.md)).

## Règles

- Fichier `<fiche>.md`, nom du champ `fiche` du manifeste, à partir de [`gabarit.md`](gabarit.md).
- L'en-tête répète le manifeste : module et version, exigences, formats, directions permises, règles, bibliothèques. Un test (`tests/test_manifestes.py`) vérifie que les deux disent la même chose (ADR-0064, conséquence de l'option A).
- La rubrique « Hypothèses distinguées » est obligatoire ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : une technique ne produit la direction « origine IA » que si elle distingue la génération des transformations banales sur la partie évaluation du corpus.
- La fiche liste les noms d'observation du module (ADR-0058) et les champs qu'il marque comme identifiants (ADR-0057).
- Un module qui décompresse autrement que par `Contexte.decompresser` le dit, et déclare ses octets par `compter_decompression` (ADR-0078).
- Un module qui extrait un contenu de sa partie (`extrait` au manifeste) le dit dans l'en-tête de sa fiche, champ « Contenus extraits » ; les autres n'ont pas ce champ (ADR-0224).

## Index

| Fiche | Module | Tâche | Formats |
| --- | --- | --- | --- |
| [Métadonnées EXIF](metadonnees-exif.md) | `exif` | T20, T22, T23, T24, T25 | JPEG, PNG, WebP, HEIC |
| [Métadonnées XMP](metadonnees-xmp.md) | `xmp` | T20, T21, T22, T23, T24, T25, T30 | JPEG, PNG, WebP, HEIC, PDF, WAV, M4A, MP4, MOV |
| [Métadonnées IPTC-IIM](metadonnees-iptc.md) | `iptc` | T20, T22, T23, T24, T25 | JPEG |
| [Blocs texte PNG](metadonnees-texte-png.md) | `textepng` | T20, T22, T23, T24, T25 | PNG |
| [Structure d'une image](structure-image.md) | `image` | T24, T40 | JPEG, PNG, WebP |
| [Double compression JPEG](double-compression-jpeg.md) | `doublejpeg` | T41 | JPEG |
| [Niveau d'erreur de recompression (ELA)](ela.md) | `ela` | T42 | JPEG |
| [Filigrane dwtDct d'invisible-watermark](filigrane-dwtdct.md) | `dwtdct` | T32 | JPEG, PNG (WebP, HEIC non lus) |
| [Dictionnaire d'information PDF](metadonnees-info-pdf.md) | `infopdf` | T21, T22, T23, T25 | PDF |
| [Versions successives d'un PDF](revisions-pdf.md) | `revisionspdf` | T50 | PDF |
| [Pages d'un PDF : textes superposés, caches, polices](pages-pdf.md) | `pagespdf` | T51 | PDF |
| [Éléments actifs d'un PDF](actifs-pdf.md) | `actifspdf` | T52 | PDF |
| [Images d'un PDF, analysées comme des parties extraites](images-pdf.md) | `imagespdf` | T53 | PDF (JPEG écrits tels quels, analysés par les modules d'image) |
| [Éléments actifs d'un DOCX ou d'un ODT](actifs-bureau.md) | `actifsbureau` | T52 (complément bureautique) | DOCX, ODT |
| [Balises ID3](metadonnees-id3.md) | `id3` | T21, T22, T23, T25 | MP3, AAC, FLAC, WAV |
| [Liste INFO et bloc bext d'un WAV](metadonnees-info-wav.md) | `infowav` | T21, T22, T23, T25 | WAV |
| [Commentaires Vorbis](metadonnees-vorbis.md) | `vorbis` | T21, T22, T23, T25 | FLAC, Ogg |
| [Métadonnées QuickTime et ISOBMFF](metadonnees-quicktime.md) | `quicktime` | T21, T22, T23, T25 | M4A, MP4, MOV |
| [Éléments Info et Tags d'un WebM](metadonnees-matroska.md) | `matroska` | T21, T22, T23, T25 | WebM |
| [Propriétés d'un document DOCX](metadonnees-ooxml.md) | `ooxml` | T21, T22, T23, T25 | DOCX |
| [Métadonnées d'un document ODT](metadonnees-odf.md) | `odf` | T21, T22, T23, T25 | ODT |
| [Manifeste C2PA](provenance-c2pa.md) | `c2pa` | T30 | JPEG, PNG, WebP, HEIC, PDF, WAV, MP3, M4A, FLAC, MP4, MOV, DOCX, ODT |
| [Caractères invisibles ou substitués d'un texte](caracteres-invisibles.md) | `caracteres` | T80 et son complément ; complément texte de T53 | Texte brut, enregistré ou collé ; DOCX, ODT ; couche texte d'un PDF |
| [Historique d'édition d'un DOCX ou d'un ODT](historique-edition.md) | `historique` | T81 | DOCX, ODT |
| [Images d'un DOCX ou d'un ODT, analysées comme des parties extraites](images-bureau.md) | `imagesbureau` | T81 (complément) | DOCX, ODT (JPEG, PNG, WebP et HEIC de l'archive, lus en place ou décompressés, analysés par les modules d'image) |

Les modules de métadonnées partagent leurs lecteurs de structure (`voight_kampff/modules/_lecture/`, [ADR-0114](../decisions/ADR-0114-un-module-par-famille-de-metadonnees.md)) : conteneurs, TIFF, XMP, ressources Photoshop et IIM, valeurs (T20) ; structure PDF (T21, [ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md) ; chaîne des sections et vues par version depuis T50, [ADR-0207](../decisions/ADR-0207-versions-d-un-pdf.md)) ; conteneurs audio et vidéo et éléments EBML (T21, [ADR-0131](../decisions/ADR-0131-un-module-par-famille-de-balises.md)) ; archives ZIP, XML et propriétés bureautiques (T21, [ADR-0136](../decisions/ADR-0136-un-module-par-famille-de-proprietes-bureautiques.md), [ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)). Le module `image` reprend le lecteur de conteneurs, qui relève aussi depuis T24 les en-têtes d'image et les tables de quantification ([ADR-0154](../decisions/ADR-0154-module-image.md)).
