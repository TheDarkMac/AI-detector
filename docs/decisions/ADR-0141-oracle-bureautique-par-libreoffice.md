# ADR-0141 — Oracle des propriétés bureautiques : échantillons écrits par LibreOffice

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : proposition de l'assistant, validée par TheDarkMac
- **Tâche** : T21 (complément bureautique)
- **Exigences liées** : F-10, NF-09 ; ADR-0043, ADR-0122, ADR-0135

## Contexte

ADR-0122 compare les modules à exiftool sur des échantillons écrits par des outils tiers et écarte les échantillons construits par les tests seuls (une erreur de lecture d'une norme serait commise deux fois). exiftool lit les propriétés de DOCX et d'ODT, mais ne les écrit pas. Sur le poste de développement, LibreOffice 25.2.3.2 (déjà employé pour le PDF de l'oracle, ADR-0127) écrit les deux formats ; aucune version de Microsoft Word n'y est installée.

## Options envisagées

### Option A — LibreOffice, depuis un document OpenDocument à plat

Un script écrit un `.fodt` (XML seul) aux métadonnées choisies, puis LibreOffice le convertit en ODT et en DOCX ; exiftool relit le tout.

- Avantages : échantillons indépendants du code testé ; un seul outil, déjà requis pour l'oracle PDF ; LibreOffice écrit les trois parties de propriétés d'un DOCX et les propriétés utilisateur typées d'un ODT.
- Inconvénients : un DOCX de LibreOffice n'a pas toutes les propriétés étendues de Word (`Company`, `Pages`, `HeadingPairs`…) : celles-ci ne sont vérifiées que par les tests construits.

### Option B — Ajouter un DOCX écrit par Word

- Avantages : les propriétés étendues de Word comparées à exiftool.
- Inconvénients : Word n'est pas sur le poste ; un fichier d'origine inconnue ne se régénère pas, et peut porter des données personnelles.

### Option C — Échantillons construits par les tests, relus par exiftool

- Avantages : rien à installer.
- Inconvénients : l'option C écartée par ADR-0122.

## Décision

Option A. `tests/donnees/metadonnees/generer_bureautique.sh` écrit `document.odt` et `document.docx` ; `relire.sh` y ajoute `-x ZIP:all` : les entrées d'une archive (groupe ZIP d'exiftool) relèvent de la structure, que les modules n'observent pas, et l'option ne change rien aux autres échantillons. Les constructeurs des tests (`tests/bureautique.py`) restent l'outil des cas limites et de ce que LibreOffice n'écrit pas.

## Raisons

- Option A : même démarche qu'ADR-0135, avec un outil déjà présent.
- Option B écartée pour cette PR : outil absent ; un DOCX de Word, écrit par TheDarkMac, pourra être ajouté par un nouvel ADR.
- Option C écartée : test circulaire (ADR-0122).

## Conséquences

- Correspondances propres aux documents dans le test d'oracle : groupe `XML` d'exiftool (propriétés d'un DOCX nommées sans leur partie ni leur espace), groupes `XMP-dc` et `XMP-meta` (Dublin Core d'un DOCX et `meta.xml` d'un ODT, qu'exiftool lit par son lecteur XMP), statistiques d'un ODT lues en structure, propriétés utilisateur en paires nom et valeur numérotées ensemble, éléments répétés en copies.
- Changer d'échantillons demande de relancer `generer_bureautique.sh` avec LibreOffice 25.2.3.2 et exiftool 13.25, ou de noter les nouvelles versions.
- LibreOffice n'est ni livré ni appelé par l'outil, ni installé en CI.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
| 2026-11-13 | Validé par TheDarkMac pendant la revue de la PR du complément (« Yes, all three ») : statut « Accepté » |
