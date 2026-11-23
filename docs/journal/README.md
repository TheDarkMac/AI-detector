# Journal des étapes

Une entrée par tâche du [découpage](../00-plan/decoupage-taches.md), rédigée dans la branche de la tâche et mergée avec elle.

## Règles

- Fichier `TNN-titre-court.md`, à partir de [`gabarit.md`](gabarit.md).
- Le journal raconte **dans l'ordre** ce qui a été fait, les commandes ou opérations significatives, les problèmes rencontrés et leur résolution.
- Il ne porte pas les décisions : il renvoie aux ADR. Il ne corrige pas les erreurs : il renvoie aux errata.
- Ce qui se passe après l'ouverture de la PR (résultat de la CI, merge) est consigné dans la section « État initial » de l'entrée suivante.

## Index

| Tâche | Titre | Branche | PR |
| --- | --- | --- | --- |
| [T00](T00-initialisation-depot.md) | Initialisation du dépôt | `tache/T00-init-depot` | [#1](https://github.com/TheDarkMac/AI-detector/pull/1) |
| [T01](T01-analyse-critique.md) | Analyse critique du cahier des charges | `tache/T01-analyse-critique` | [#2](https://github.com/TheDarkMac/AI-detector/pull/2) |
| [T02](T02-arbitrages.md) | Arbitrage des points ouverts | `tache/T02-arbitrages` | [#3](https://github.com/TheDarkMac/AI-detector/pull/3) |
| [T03](T03-modele-de-menace.md) | Modèle de menace | `tache/T03-modele-de-menace` | [#4](https://github.com/TheDarkMac/AI-detector/pull/4) |
| [T04](T04-architecture.md) | Architecture et choix techniques | `tache/T04-architecture` | [#5](https://github.com/TheDarkMac/AI-detector/pull/5) |
| [T10](T10-squelette.md) | Squelette du projet Python et outillage | `tache/T10-squelette` | [#6](https://github.com/TheDarkMac/AI-detector/pull/6) |
| [T11](T11-modele-de-donnees.md) | Modèle de données | `tache/T11-modele-de-donnees` | [#9](https://github.com/TheDarkMac/AI-detector/pull/9) |
| [T12](T12-moteur-de-modules.md) | Moteur de modules | `tache/T12-moteur-de-modules` | [#10](https://github.com/TheDarkMac/AI-detector/pull/10) |
| [T10 (complément)](T10-licence-et-publication.md) | Fichier LICENSE et éditeur de confiance PyPI | `tache/T10-licence-et-publication` | [#11](https://github.com/TheDarkMac/AI-detector/pull/11) |
| [T10 (complément 2)](T10-versions-et-publication.md) | Numérotation des versions et contrôles de la publication | `tache/T10-versions-et-publication` | [#12](https://github.com/TheDarkMac/AI-detector/pull/12) |
| [T13](T13-soumission-et-identification.md) | Soumission et identification | `tache/T13-soumission-et-identification` | [#13](https://github.com/TheDarkMac/AI-detector/pull/13) |
| [T14](T14-securite-d-execution.md) | Sécurité d'exécution | `tache/T14-securite-d-execution` | [#14](https://github.com/TheDarkMac/AI-detector/pull/14) |
| [T15](T15-catalogue-de-regles.md) | Catalogue de règles versionné et daté | `tache/T15-catalogue-de-regles` | [#15](https://github.com/TheDarkMac/AI-detector/pull/15) |
| [T16](T16-generation-du-rapport.md) | Génération du rapport | `tache/T16-generation-du-rapport` | [#16](https://github.com/TheDarkMac/AI-detector/pull/16) |
| [T17](T17-banc-d-evaluation.md) | Banc d'évaluation | `tache/T17-banc-d-evaluation` | [#17](https://github.com/TheDarkMac/AI-detector/pull/17) |
| [T18](T18-reproductibilite.md) | Test de reproductibilité | `tache/T18-reproductibilite` | [#18](https://github.com/TheDarkMac/AI-detector/pull/18) |
| [T20](T20-extraction-image.md) | Extraction image | `tache/T20-extraction-image` | [#19](https://github.com/TheDarkMac/AI-detector/pull/19) |
| [T21](T21-extraction-pdf.md) | Extraction PDF | `tache/T21-extraction-pdf` | [#20](https://github.com/TheDarkMac/AI-detector/pull/20) |
| [T21 (complément)](T21-extraction-audio-video.md) | Extraction audio et vidéo : balises des conteneurs | `tache/T21-extraction-audio-video` | [#21](https://github.com/TheDarkMac/AI-detector/pull/21) |
| [T21 (complément 2)](T21-extraction-bureautique.md) | Extraction bureautique : propriétés de DOCX et d'ODT | `tache/T21-extraction-bureautique` | [#22](https://github.com/TheDarkMac/AI-detector/pull/22) |
| [T22](T22-origine-ia-et-signatures.md) | Origine IA déclarée et signatures de générateurs | `tache/T22-origine-ia-et-signatures` | [#23](https://github.com/TheDarkMac/AI-detector/pull/23) |
| [T23](T23-incoherences-internes.md) | Incohérences internes | `tache/T23-incoherences-internes` | [#24](https://github.com/TheDarkMac/AI-detector/pull/24) |
| [T24](T24-indices-de-transfert.md) | Indices de transfert par messagerie ou capture d'écran | `tache/T24-indices-de-transfert` | [#25](https://github.com/TheDarkMac/AI-detector/pull/25) |
| [T25](T25-controle-avant-publication.md) | Contrôle avant publication : marques identifiantes des métadonnées | `tache/T25-controle-avant-publication` | [#26](https://github.com/TheDarkMac/AI-detector/pull/26) |
| [T30](T30-c2pa.md) | C2PA : détection, vérification, états et déclarations | `tache/T30-c2pa` | [#27](https://github.com/TheDarkMac/AI-detector/pull/27) |
| [T31](T31-filigranes-invisibles.md) | Filigranes invisibles : inventaire, point d'extension du catalogue, marquages recherchés | `tache/T31-filigranes-invisibles` | [#28](https://github.com/TheDarkMac/AI-detector/pull/28) |
| [T40](T40-tables-de-quantification.md) | Tables de quantification JPEG comparées à des tables connues | `tache/T40-tables-de-quantification` | [#29](https://github.com/TheDarkMac/AI-detector/pull/29) |
| [T41](T41-double-compression.md) | Double compression JPEG | `tache/T41-double-compression` | [#30](https://github.com/TheDarkMac/AI-detector/pull/30) |
| [T40 (complément)](T40-complement-photoshop-appareils.md) | Tables de Photoshop et d'appareils relevées | `tache/T40-complement-photoshop-appareils` | [#32](https://github.com/TheDarkMac/AI-detector/pull/32) |
| [T42](T42-ela.md) | ELA, avertissement d'interprétation et carte | `tache/T42-ela` | [#31](https://github.com/TheDarkMac/AI-detector/pull/31) |
| [T32](T32-lecteur-dwtdct.md) | Lecteur du filigrane dwtDct d'invisible-watermark | `tache/T32-dwtdct` | [#33](https://github.com/TheDarkMac/AI-detector/pull/33) |
| [T50](T50-revisions-pdf.md) | Révisions incrémentales d'un PDF et leur chronologie | `tache/T50-revisions-pdf` | [#34](https://github.com/TheDarkMac/AI-detector/pull/34) |
| [T51](T51-objets-pdf.md) | Objets changés, textes superposés et polices incohérentes d'un PDF | `tache/T51-objets-pdf` | [#35](https://github.com/TheDarkMac/AI-detector/pull/35) |
| [T52](T52-elements-actifs-pdf.md) | Éléments actifs d'un PDF, signalés, jamais exécutés | `tache/T52-elements-actifs-pdf` | [#36](https://github.com/TheDarkMac/AI-detector/pull/36) |
| [T53](T53-images-extraites-pdf.md) | Images d'un PDF, analysées comme des parties extraites | `tache/T53-images-extraites-pdf` | [#37](https://github.com/TheDarkMac/AI-detector/pull/37) |
| [T52 (complément bureautique)](T52-complement-bureautique.md) | Éléments actifs d'un DOCX ou d'un ODT, signalés, jamais exécutés | `tache/T52-complement-bureautique` | [#38](https://github.com/TheDarkMac/AI-detector/pull/38) |
| [T80](T80-caracteres-invisibles.md) | Caractères invisibles ou substitués d'un texte, et saisie du texte collé | `tache/T80-caracteres-invisibles` | [#39](https://github.com/TheDarkMac/AI-detector/pull/39) |
| [Correctif ERR-0013](ERR-0013-sortie-redirigee-en-cp1252.md) | Sortie de `vk` redirigée sous Windows, écrite en UTF-8 | `correctif/ERR-0013-sortie-redirigee-en-cp1252` | [#40](https://github.com/TheDarkMac/AI-detector/pull/40) |
| [T80 (complément bureautique)](T80-complement-bureautique.md) | Caractères invisibles ou substitués du texte d'un DOCX ou d'un ODT | `tache/T80-complement-bureautique` | [#41](https://github.com/TheDarkMac/AI-detector/pull/41) |
| [T53 (complément texte)](T53-complement-texte.md) | Couche texte native d'un PDF, analysée par le module `caracteres` | `tache/T53-complement-texte` | [#42](https://github.com/TheDarkMac/AI-detector/pull/42) |
| [T81](T81-historique-d-edition.md) | Historique d'édition d'un DOCX ou d'un ODT | `tache/T81-historique-d-edition` | [#43](https://github.com/TheDarkMac/AI-detector/pull/43) |
| [T81 (complément)](T81-complement-images.md) | Images d'un DOCX ou d'un ODT, analysées comme des parties extraites | `tache/T81-complement-images` | [#44](https://github.com/TheDarkMac/AI-detector/pull/44) |
