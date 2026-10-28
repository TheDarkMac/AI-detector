# ADR-0114 — Un module par famille de métadonnées, lecteurs de structure communs

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T20
- **Exigences liées** : F-10, F-25, F-82, NF-03, NF-10 ; ADR-0042, ADR-0043, ADR-0061, ADR-0064

## Contexte

T20 livre les premiers modules d'analyse : l'extraction des métadonnées EXIF, XMP, IPTC et des blocs texte PNG (F-10). ADR-0042 fait de chaque technique un sous-paquet de `modules/` avec son manifeste. Il fallait dire ce qu'est « une technique » ici : une famille de métadonnées, l'ensemble, ou un format. Le découpage fixe trois choses à la fois : ce qu'une erreur dans un lecteur fait perdre (NF-03, ADR-0060), ce que la couverture du rapport dit avoir lu (F-25, F-82) et ce que l'utilisateur peut désactiver (ADR-0063).

## Options envisagées

### Option A — Un module par famille

Modules `exif`, `xmp`, `iptc`, `textepng`, chacun pour les formats où sa famille existe ; lecteurs de conteneurs et de structures communs, hors des modules.

- Avantages : une erreur dans un lecteur ne fait perdre que sa famille ; la couverture dit, famille par famille, ce qui a été lu, et chacune se désactive seule ; `xmp` pourra servir au PDF en T21 sans toucher aux autres.
- Inconvénients : chaque module reparcourt le conteneur (quelques lectures de plus) ; quatre manifestes et quatre fiches.

### Option B — Un seul module

Module `metaimage` pour les quatre familles.

- Avantages : un seul parcours du conteneur, un seul manifeste.
- Inconvénients : une erreur dans le lecteur IPTC fait perdre l'EXIF et le XMP ; la couverture dit « métadonnées appliquées » sans dire lesquelles ; impossible de désactiver une famille seule.

### Option C — Un module par format

Modules `metajpeg`, `metapng`, `metawebp`, `metaheic`, chacun lisant toutes les familles ; lecteurs EXIF et XMP partagés.

- Avantages : chaque module connaît bien son conteneur.
- Inconvénients : un fichier n'a qu'un format, donc l'isolation des erreurs est celle de l'option B ; T21 devrait ajouter le XMP du PDF dans un module PDF, à côté d'un XMP d'image séparé.

## Décision

Option A.

- Modules `exif`, `xmp`, `iptc`, `textepng`, identifiants conformes à ADR-0064 (minuscules et chiffres).
- Lecteurs communs dans `voight_kampff/modules/_lecture/` : `conteneurs` (blocs de métadonnées par format), `tiff`, `xmp`, `iim`, `valeurs`. Ce dossier n'a pas de manifeste : la découverte l'ignore (ADR-0064), et il n'est importé que par les modules, donc seulement dans le processus de travail, avant son verrouillage (ADR-0079).
- Chaque lecteur reçoit le contexte du module qui l'appelle : il lit et compte par lui (ADR-0061, ADR-0078).
- Les modules n'ont aucune dépendance entre eux (`requiert = []`) : chacun reparcourt le conteneur.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : une erreur ferait perdre toutes les métadonnées (NF-03) et la couverture serait moins précise (F-25).
- Option C écartée : aucun gain d'isolation sur l'option B, et le XMP serait dispersé entre formats d'image et PDF.
- Parcours refait par chaque module plutôt qu'un module « conteneur » requis par les autres : une erreur de parcours resterait commune à tous, et l'acheminement des résultats d'un module vers un autre n'existe pas encore (T53, ADR-0061).

## Conséquences

- La couverture d'une image liste quatre techniques : appliquées, partielles, non menées ou non applicables (`iptc` hors JPEG, `textepng` hors PNG).
- T21 ajoute le PDF aux formats de `xmp` (lecteur XMP commun) et ses propres modules pour le dictionnaire d'information, les balises audio et vidéo, les propriétés bureautiques.
- Le test « aucun module livré » de T12 est remplacé par un test des quatre modules livrés.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
