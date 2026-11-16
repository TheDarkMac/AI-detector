# ADR-0193 — Relevé des tables : originaux de Wikimedia Commons, au moins 3 fichiers de 2 comptes, données au dépôt

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (méthode de collecte précisée par l'assistant)
- **Tâche** : complément de T40
- **Exigences liées** : F-30, F-26, NF-09 ; A-32 ; ADR-0180, ADR-0181, ADR-0191

## Contexte

Aucune source publique ne donne les tables de quantification de Photoshop ni celles des appareils (ADR-0180) : Farid les a relevées (« Digital Image Ballistics from JPEG Quantization », TR2006-583, Dartmouth, 2006) sans les publier, et les données de JPEGsnoop (GPL-2.0) et les préréglages de Pillow sont exclus (ADR-0180). TheDarkMac a choisi de les relever sur des fichiers publics de provenance établie, les originaux de Wikimedia Commons, sous licence libre. Il fallait dire combien de fichiers fondent une entrée, et comment traiter les fichiers discordants. Le premier relevé, fait le 2026-11-15 dans le dossier temporaire d'une session, a été perdu avec elle ; il a été refait, ses données gardées cette fois dans le dossier de travail.

## Options envisagées

### Concordance

- **A — Au moins 3 fichiers aux mêmes tables, versés par au moins 2 comptes ; aucun fichier discordant sans explication** : un compte ne suffit pas (un seul utilisateur peut avoir un réglage ou un logiciel propre) ; les discordances sont expliquées ou l'entrée est écartée.
- **B — Un fichier par entrée** : rapide, mais un fichier réenregistré passerait pour la source.
- **C — 10 fichiers de 5 comptes** : plus sûr, mais presque aucun niveau de Photoshop ni appareil n'y arriverait sur un relevé de cette taille.

### Conservation des données

- **A — Scripts, tables retenues et liste des fichiers sources au dépôt** (`banc/releves/tables-T40c/`) ; les métadonnées brutes de la phase 1 (22 Mo) restent hors du dépôt, régénérables par le script.
- **B — Rien au dépôt, la fiche seule** : c'est ce qui a fait perdre le premier relevé ; rien ne serait vérifiable.

## Décision

Concordance A (choix de TheDarkMac, 2026-11-15), conservation A (précision de l'assistant, après la perte du premier relevé). Méthode, précisée par l'assistant :

1. **Phase 1** (`phase1_metadonnees.py`) : `list=allimages` de l'API de Commons, quatre appels de 50 fichiers au début de chaque mois de 2008 à 2025 ; pour chaque JPEG, nom, adresses, compte, champs EXIF `Make`, `Model`, `Software`, dates, dimensions. 37 006 JPEG.
2. **Choix des candidats** (`phase2_entetes.py`) : Photoshop, `Software` qui commence par « Adobe Photoshop » suivi d'une version (Lightroom, Elements, Camera Raw et Express exclus), deux fichiers au plus par compte ; appareils, `Make` et `Model` présents, aucun logiciel d'édition connu dans `Software`, date de modification égale à la date de prise de vue, dimensions égales à celles que déclare l'EXIF, modèles qui ont au moins 3 fichiers de 2 comptes en phase 1, 8 fichiers au plus par modèle et 3 par modèle et compte ; contrôles, fichiers d'autres logiciels, deux par compte, pour chercher des collisions.
3. **Phase 2** : en-têtes lus sur upload.wikimedia.org par requêtes partielles (32 Kio, puis par 128 Kio jusqu'au premier balayage), une requête toutes les 3 s : tables, empreinte et encodeur reconnu par le module `image`, segment SOF, ressource Photoshop 0x0406 (niveau = valeur brute signée + 4, d'après ExifTool), segment APP14. 2 646 fichiers lus.
4. **Phase 3 et 4** (`phase3_analyse.py`, `phase4_selection.py`) : un fichier compte s'il a été lu jusqu'au premier balayage et si ses tables ne sont pas celles d'un encodeur que le module reconnaît déjà (ils ont été réencodés ailleurs) ; empreintes retenues selon ADR-0194 et ADR-0195 ; licence de chaque fichier retenu lue par l'API (`LicenseShortName`).

Livrés au dépôt : les quatre scripts, `tables.toml` (chaque empreinte retenue, ses tables en clair, ses comptes, ses collisions) et `fichiers.csv` (chaque fichier source : page, licence, compte, logiciel, appareil, dimensions), plus `entetes.csv` (les 2 646 en-têtes lus, sans les tables). Requêtes envoyées avec l'en-tête `User-Agent` du dépôt, sans donnée personnelle.

## Raisons

- Concordance A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Concordance B écartée : un fichier réenregistré par un autre logiciel sous les métadonnées d'origine n'aurait pas été repéré ; C, parce qu'elle ne retiendrait presque rien.
- Conservation B écartée : le premier relevé a été perdu ; une table livrée au catalogue doit pouvoir être revérifiée sur ses fichiers (NF-09, A-32).

## Conséquences

- Les discordances observées sont toutes expliquées : à un même niveau de Photoshop, par la taille de l'image et la couleur (ADR-0195) ; pour les appareils, par le critère d'ADR-0194.
- Le relevé est un échantillon de Commons, pas un recensement : un niveau ou un appareil absent n'est pas reconnu, et la fiche le dit.
- Un nouveau relevé (autres appareils, autres logiciels) se fait avec les mêmes scripts et ajoute des empreintes au catalogue sans nouvelle version de l'outil (ADR-0181).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création ; concordance décidée par TheDarkMac le 2026-11-15, dans la première session du complément |
