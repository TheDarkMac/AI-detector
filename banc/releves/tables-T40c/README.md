# Relevé des tables de Photoshop et d'appareils (complément de T40)

Relevé fait du 2026-11-15 au 2026-11-16 sur des originaux de Wikimedia Commons, pour les règles `R-IMAGE-008` à `R-IMAGE-022` du catalogue 0.9.0. Méthode et critères : [ADR-0193](../../../docs/decisions/ADR-0193-releve-des-tables.md), [ADR-0194](../../../docs/decisions/ADR-0194-tables-d-appareils.md), [ADR-0195](../../../docs/decisions/ADR-0195-tables-de-photoshop.md) ; fiche [`structure-image`](../../../docs/techniques/structure-image.md) ; journal [complément de T40](../../../docs/journal/T40-complement-photoshop-appareils.md).

## Fichiers

| Fichier | Contenu |
| --- | --- |
| `tables.toml` | Les 37 empreintes retenues : famille (`photoshop` ou `appareil`), niveau ou marque, modèles, nombre de fichiers et de comptes, composantes, étendue des côtés longs, autres fichiers aux mêmes tables (`ailleurs`), tables en clair (`table_0`, `table_1`, dans l'ordre du segment DQT) ; liste des modèles exclus parce qu'ils semblent calculer leurs tables pour chaque image |
| `fichiers.csv` | Les 1 093 fichiers sources des empreintes retenues : page de Commons, licence, compte qui l'a versé, logiciel et appareil déclarés, dimensions |
| `entetes.csv` | Les 2 646 en-têtes lus, retenus ou non : page, compte, nature du candidat, logiciel et appareil déclarés, dimensions, ressource 0x0406, composantes, empreinte, encodeur reconnu par le module `image`, erreur |
| `phase1_metadonnees.py` | Métadonnées des JPEG de Commons par l'API (`list=allimages`), 200 par mois de 2008 à 2025 |
| `phase2_entetes.py` | Choix des candidats et lecture de leurs en-têtes par requêtes partielles, une toutes les 3 s |
| `phase3_analyse.py` | Regroupement par niveau de Photoshop et par modèle d'appareil, collisions |
| `phase4_selection.py` | Empreintes retenues, licences, écriture des trois fichiers ci-dessus |

Les données brutes (`phase1.jsonl`, 22 Mo ; `phase2.jsonl`, 3,5 Mo) ne sont pas au dépôt : elles se régénèrent par les scripts, lancés dans l'ordre depuis ce dossier avec l'interpréteur de l'environnement du projet (`phase2_entetes.py` emploie le module `image` pour l'empreinte). Commons change : un nouveau relevé ne donnera pas exactement les mêmes fichiers. Les scripts reprennent là où ils se sont arrêtés et réessaient sans fin après une coupure du réseau ; ils envoient un `User-Agent` qui nomme le dépôt, sans donnée personnelle.

Les tests (`tests/test_tables_relevees.py`) lisent `tables.toml` et `fichiers.csv` : ne pas les modifier à la main.
