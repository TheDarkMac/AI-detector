# Relevé du filigrane dwtDct sur Wikimedia Commons (T32)

Relevé fait le 2026-11-16, pour vérifier les seuils des règles `R-DWTDCT-001` à `R-DWTDCT-003` du catalogue 0.10.0 sur des images qui ne peuvent pas porter les messages cherchés, et pour voir ce que la lecture donne sur des images déclarées générées. Méthode et critères : [ADR-0204](../../../docs/decisions/ADR-0204-seuils-et-releve.md) ; lecture : [ADR-0203](../../../docs/decisions/ADR-0203-methode-de-lecture.md) ; fiche [`filigrane-dwtdct`](../../../docs/techniques/filigrane-dwtdct.md) ; journal de [T32](../../../docs/journal/T32-lecteur-dwtdct.md).

## Fichiers

| Fichier | Contenu |
| --- | --- |
| `phase1_listes.py` | Listes par l'API de Commons : JPEG et PNG versés avant le 2022-08-22 (quatre appels de 25 fichiers par mois, de 2008-01 à 2022-07), et fichiers déclarés générés par Stable Diffusion, SDXL ou FLUX.1 (trois recherches) |
| `phase2_fichiers.py` | Tirage (1 000 JPEG et 300 PNG au plus, au plus 3 par compte, graine 32) et téléchargement, une requête toutes les 2 s : rendus de 960 pixels pour les authentiques, originaux de moins de 20 Mio pour les déclarés |
| `phase3_lecture.py` | Lecture de chaque fichier par l'outil lui-même (`analyser`, seul `dwtdct` actif) ; écrit `resultats.csv` et le résumé `phase3.txt` |
| `resultats.csv` | Un fichier par ligne : liste (`authentique` ou `declare`), page de Commons, licence, compte qui l'a versé, date du versement, type, dimensions de l'original, empreinte SHA-256 du fichier téléchargé, état de la lecture (`lu`, `gris`, `petite`, `non_mene:…`), blocs lus, bits concordants avec chacun des trois messages, règles qui ont donné un constat |

Les données brutes (`phase1.jsonl`, `phase2.jsonl`, `fichiers/`, `phase3.txt`, journaux) ne sont pas au dépôt (`.gitignore`) : elles se régénèrent par les scripts, lancés dans l'ordre depuis ce dossier avec l'interpréteur de l'environnement du projet. Commons change : un nouveau relevé ne donnera pas exactement les mêmes fichiers ; l'empreinte de chaque fichier lu est dans `resultats.csv`. Les scripts reprennent là où ils se sont arrêtés et réessaient après une coupure du réseau ; ils envoient un `User-Agent` qui nomme le dépôt, sans donnée personnelle.

Les fichiers de Commons restent sous leur licence, citée pour chacun dans `resultats.csv` ; aucun n'est au dépôt.
