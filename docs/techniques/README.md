# Fiches techniques

Une fiche par module d'analyse (NF-09, livrable 4), livrée avec son code, ses tests et ses règles : une technique n'est « terminée » qu'avec elle ([découpage](../00-plan/decoupage-taches.md), §1). Le manifeste de chaque module la cite (`fiche`, [ADR-0064](../decisions/ADR-0064-manifeste-des-modules.md)).

## Règles

- Fichier `<fiche>.md`, nom du champ `fiche` du manifeste, à partir de [`gabarit.md`](gabarit.md).
- L'en-tête répète le manifeste : module et version, exigences, formats, directions permises, règles, bibliothèques. Un test (`tests/test_manifestes.py`) vérifie que les deux disent la même chose (ADR-0064, conséquence de l'option A).
- La rubrique « Hypothèses distinguées » est obligatoire ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : une technique ne produit la direction « origine IA » que si elle distingue la génération des transformations banales sur la partie évaluation du corpus.
- La fiche liste les noms d'observation du module (ADR-0058) et les champs qu'il marque comme identifiants (ADR-0057).
- Un module qui décompresse autrement que par `Contexte.decompresser` le dit, et déclare ses octets par `compter_decompression` (ADR-0078).

## Index

| Fiche | Module | Tâche | Formats |
| --- | --- | --- | --- |
| [Métadonnées EXIF](metadonnees-exif.md) | `exif` | T20 | JPEG, PNG, WebP, HEIC |
| [Métadonnées XMP](metadonnees-xmp.md) | `xmp` | T20 | JPEG, PNG, WebP, HEIC |
| [Métadonnées IPTC-IIM](metadonnees-iptc.md) | `iptc` | T20 | JPEG |
| [Blocs texte PNG](metadonnees-texte-png.md) | `textepng` | T20 | PNG |

Les quatre modules de T20 partagent leurs lecteurs de structure (`voight_kampff/modules/_lecture/`, [ADR-0114](../decisions/ADR-0114-un-module-par-famille-de-metadonnees.md)) : conteneurs, TIFF, XMP, ressources Photoshop et IIM, valeurs.
