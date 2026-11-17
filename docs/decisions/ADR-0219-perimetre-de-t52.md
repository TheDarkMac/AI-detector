# ADR-0219 — Périmètre de T52 : éléments actifs du PDF ; bureautique renvoyée à un complément

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T52
- **Exigences liées** : F-62, NF-01, ES-06 ; menaces M-07, M-14 ; ADR-0033, ADR-0138

## Contexte

F-62 (« Éléments actifs (scripts, actions automatiques) signalés, jamais exécutés ») est rangée dans la partie PDF du cahier (§5), avec F-60 à F-64. Mais la menace M-07 cite aussi les macros bureautiques, et ADR-0138 a renvoyé le signalement du modèle distant d'un DOCX à « T52 ou T81 ». ADR-0033 confie à T21 et T52 la garantie que les liens et références distantes des DOCX, ODT et PDF ne sont jamais suivis ; T21 l'a réalisée pour DOCX et ODT (ADR-0138), sans rien en signaler.

## Options envisagées

### Option A — PDF seul ; bureautique dans un complément de T52 (recommandée)

T52 traite le PDF : JavaScript, actions automatiques, lancements, envois, fichiers incorporés, formulaires XFA. Les macros ODF et VBA (`Basic/`, `vbaProject.bin`), les objets OLE et le modèle distant d'un DOCX (`attachedTemplate`) sont renvoyés à un complément bureautique de T52, comme T21 en a eu.

- Avantages : une PR plus petite ; un seul lecteur à étendre (le lecteur PDF du projet) ; F-62 réalisée pour le format que nomme le cahier.
- Inconvénients : un DOCX à modèle distant ou un ODT à macros reste non signalé en attendant ; la garantie qu'ils ne sont pas suivis tient déjà (ADR-0138).

### Option B — PDF et bureautique dans T52

- Avantages : F-62 et M-07 traitées d'un coup.
- Inconvénients : deux lecteurs à toucher (PDF, et le lecteur ZIP et les parties XML des documents bureautiques), des parties jamais lues jusqu'ici (`word/_rels/settings.xml.rels`, `META-INF/manifest.xml`, `Basic/`), une PR bien plus grosse.

## Décision

Option A : T52 signale les éléments actifs d'un PDF ; ceux des documents bureautiques sont renvoyés à un complément bureautique de T52.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : taille et risque de la PR ; le format que nomme F-62 est le PDF.

## Conséquences

- F-62 est réalisée pour le PDF ; la matrice le dit, et nomme le complément pour la bureautique.
- ES-06 devient réalisée : DOCX et ODT par T21 (ADR-0138), C2PA par T30 (ADR-0166), PDF par T52 ; RS-02, récupération d'un manifeste distant sur confirmation, reste au complément de T30.
- Le complément bureautique de T52 devra lire des parties que T21 a exclues (ADR-0139) et décider de ce qu'il signale du modèle distant (ADR-0138, conséquences).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T52 |
