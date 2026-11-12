# ADR-0127 — Métadonnées PDF lues : dictionnaire Info du dernier trailer, XMP du catalogue

- **Statut** : Proposé
- **Date** : 2026-11-12
- **Décideur** : proposition de l'assistant, à valider par TheDarkMac
- **Tâche** : T21
- **Exigences liées** : F-10, F-14, F-82, ES-05, ES-13 ; ADR-0114, ADR-0115, ADR-0122, ADR-0124

## Contexte

ADR-0114 a fixé la forme : `xmp` s'étend au PDF, et le dictionnaire d'information a son propre module. Restait à dire **où** chacun lit. Un PDF porte des métadonnées à plusieurs endroits (ISO 32000-2, §14.3) : le dictionnaire désigné par `/Info` dans le trailer, le flux `/Metadata` du catalogue (XMP du document), des flux `/Metadata` attachés aux pages, images, polices ou formulaires. Un document mis à jour de façon incrémentale garde aussi, dans ses sections antérieures, les dictionnaires et paquets qu'il a remplacés.

## Options envisagées

### Option A — État courant du document seulement

`infopdf` lit le dictionnaire du trailer le plus récent qui en désigne un ; `xmp` lit le flux `/Metadata` du catalogue courant. Les métadonnées attachées aux pages et objets, et celles des révisions antérieures, ne sont pas lues.

- Avantages : ce que voit un lecteur de PDF, et ce que compare exiftool ; une lecture par module, sans parcours de tous les objets ; les révisions restent l'affaire de T50, qui les reconstituera avec leur chronologie.
- Inconvénients : un paquet XMP d'image intégrée (souvent celui de l'appareil ou du générateur) n'est pas au rapport avant T53.

### Option B — Aussi les révisions antérieures

- Avantages : l'ancien auteur ou l'ancien logiciel d'un document modifié apparaît.
- Inconvénients : c'est l'objet de T50 (F-60), qui doit distinguer ajouts légitimes et remplacements ; le faire ici, sans chronologie, donnerait des observations sans leur contexte.

### Option C — Tous les flux `/Metadata` du document

- Avantages : couverture complète du XMP.
- Inconvénients : parcours de tous les objets (jusqu'au million, ADR-0078) pour chaque PDF ; rattacher un paquet à son image relève de T53 (F-63), qui route les images extraites vers les modules d'image.

## Décision

Option A. Modules et versions : `infopdf` 0.1.0 (nouveau, format `pdf`), `xmp` 0.2.0 (format `pdf` ajouté).

## Raisons

- Option A : elle répond à la question de F-10 pour le document lui-même, et laisse à T50 et T53 ce qui demande leur contexte.
- Option B écartée : observations de révision sans chronologie, en doublon de T50.
- Option C écartée : coût d'un parcours complet, et rattachement des paquets laissé à T53.

## Conséquences

- La fiche `metadonnees-info-pdf` et la fiche `metadonnees-xmp` listent ces emplacements lus et non lus.
- Une analyse non menée est produite quand l'emplacement existe sans pouvoir être lu : structure illisible, objet absent ou mal formé, document chiffré (ADR-0126).
- Oracle exiftool (ADR-0122) : deux PDF, l'un de LibreOffice (table classique), l'autre de Ghostscript (flux de références croisées et flux d'objets), métadonnées écrites par exiftool en mise à jour incrémentale. Ils sont produits par `generer_pdf.sh` plutôt qu'ajoutés à `generer.sh` comme le prévoyait ADR-0122, pour que les PDF se régénèrent sans changer les images ; `relire.sh`, appelé par les deux, écrit `exiftool.json`. Le groupe « PDF » d'exiftool mêle au dictionnaire Info des entrées du catalogue et de l'en-tête (`PDFVersion`, `Linearized`, `PageCount`, `PageMode`, `Language`, `TaggedPDF`) : elles sont écartées de la comparaison, comme structure du document (T50).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création, statut « Proposé » |
