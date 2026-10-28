# ADR-0122 — Oracle exiftool : échantillons générés, sortie enregistrée, comparaison dans les deux sens

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T20, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : F-10, NF-09 ; ADR-0043, ADR-0048

## Contexte

ADR-0043 fait d'exiftool l'oracle de test des métadonnées : les tests de T20 et T21 comparent ce que l'outil extrait à ce qu'exiftool relève, sans qu'exiftool soit livré ni appelé par l'outil. Il restait à dire d'où viennent les fichiers comparés, et comment la comparaison tourne en CI, où exiftool n'est pas installé (Linux, macOS et Windows, ADR-0051).

## Options envisagées

### Option A — Échantillons et sortie d'exiftool enregistrés dans le dépôt

Un script crée de petites images par ImageMagick, y écrit des métadonnées par exiftool, puis enregistre la sortie JSON d'exiftool ; le test compare les modules à cette sortie, partout ; il la compare en plus à exiftool lui-même quand il est installé dans la même version.

- Avantages : aucune dépendance de la CI ; échantillons écrits par un outil tiers, pas par le code du projet ; la sortie enregistrée est vérifiable.
- Inconvénients : quelques fichiers binaires dans le dépôt ; la sortie enregistrée vieillit avec exiftool.

### Option B — exiftool installé en CI

- Avantages : comparaison toujours vivante.
- Inconvénients : dépendance système de plus sur trois systèmes, non épinglée par empreinte (ADR-0006, ADR-0037).

### Option C — Échantillons construits par les tests seulement

- Avantages : aucun fichier binaire.
- Inconvénients : le code du projet écrirait ce que son propre lecteur relit ; une erreur de lecture d'une norme serait commise deux fois.

## Décision

Option A.

- `tests/donnees/metadonnees/generer.sh` : quatre images (JPEG, PNG, WebP, HEIC), métadonnées EXIF (dont GPS et numéro de série), XMP (dont `DigitalSourceType`), IPTC-IIM (JPEG) et blocs texte (PNG) ; sortie `exiftool -j -a -G1 -n -D -struct` dans `exiftool.json`. Versions employées : ImageMagick 7.1.1-43, exiftool 13.25.
- `tests/test_oracle_exiftool.py` compare dans les deux sens : tout ce qu'exiftool relève dans le périmètre de T20 est observé avec la même valeur, et rien n'est observé qu'exiftool ne relève. EXIF est comparé par répertoire et numéro d'étiquette, XMP par nom local, IPTC et PNG par nom. Formes ramenées à une forme commune : liste de nombres qu'exiftool écrit en texte séparé par des espaces, coordonnée qu'il convertit en degrés décimaux, tableau d'un élément qu'il écrit en valeur simple.
- Un test supplémentaire relance exiftool sur les échantillons et compare sa sortie à `exiftool.json`, s'il est installé dans la version enregistrée ; sauté sinon.
- Les constructeurs d'échantillons des tests (`tests/metadonnees.py`) restent l'outil des cas limites et des structures malformées, qu'exiftool ne sait pas écrire.

## Raisons

- Option A : l'oracle est indépendant du code testé et tourne sur les trois systèmes.
- Option B écartée : dépendance de CI non épinglée.
- Option C écartée : test circulaire.
- Comparaison dans les deux sens : une étiquette inventée par l'outil se voit aussi bien qu'une étiquette oubliée.

## Conséquences

- T21 ajoute ses formats (PDF, conteneurs audio et vidéo, DOCX, ODT) à `generer.sh` et à l'oracle.
- Changer d'échantillons demande de relancer `generer.sh` avec les versions indiquées, ou de noter les nouvelles.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
