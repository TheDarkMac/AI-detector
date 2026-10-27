# ADR-0088 — Fichiers, empreinte et limites du catalogue

- **Statut** : Proposé
- **Date** : 2026-10-27
- **Décideur** : l'assistant, proposition non posée en question pendant T15, soumise dans la PR de T15
- **Tâche** : T15
- **Exigences liées** : F-26, NF-06, NF-07 ; ES-09 ; M-11, M-12 ; ADR-0029, ADR-0038, ADR-0040, ADR-0085

## Contexte

ADR-0038 fixe le format (TOML validé par JSON Schema) et laisse à T15 le découpage en fichiers et le calcul de l'empreinte, « sur ses fichiers tels que livrés ». L'empreinte doit pouvoir être recalculée par un lecteur du rapport, sans l'outil, pour comparer avec celle publiée (ADR-0029). Un catalogue fourni par l'utilisateur (ADR-0086) est lu par le processus principal : il faut le borner.

## Options envisagées

### Découpage

- **A — Un en-tête et un fichier par module** (`catalogue.toml`, `regles/<module>.toml`) : un module se relit seul ; une PR de module ne touche que son fichier. Inconvénient : un en-tête à tenir à part.
- **B — Un seul fichier** : simple, mais long à relire et source de conflits entre PR.
- **C — Un fichier par règle** : très fin, mais des centaines de petits fichiers pour les signatures.

### Empreinte

- **A — SHA-256 de la liste `sha256sum`** : une ligne `<sha256 du fichier>  <chemin relatif>` par fichier, triée par chemin, puis SHA-256 de ce texte. Recalculable avec les outils du système ; tient compte des noms.
- **B — SHA-256 de la concaténation des fichiers** : plus simple, mais ignore les noms et ne se recalcule pas sans un programme.
- **C — SHA-256 d'une archive** : dépend de l'outil d'archivage (dates, ordre, droits).

## Décision

Option A pour les deux.

- Le catalogue est un dossier : `catalogue.toml` (en-tête, schéma `catalogue`) et, facultatif, `regles/<module>.toml` (schéma `regles`), où `<module>` est l'identifiant d'un module ; chaque règle d'un fichier est de ce module. Tout autre fichier ou dossier rend le catalogue invalide, ce qui garde l'empreinte sans fichier inutile.
- Le catalogue livré est `src/voight_kampff/donnees/catalogue/`, dans le paquet. Le fichier `.gitattributes` y interdit la conversion des fins de ligne : les octets, donc l'empreinte, sont les mêmes sur les trois systèmes.
- La date est écrite en texte (`"2026-10-27"`), validée par le schéma puis par le code, une date TOML ne passant pas par JSON Schema.
- Empreinte : celle de l'option A, sur les octets lus ; c'est ce qu'affiche, dans le dossier du catalogue, `find . -type f -printf '%P\n' | LC_ALL=C sort | xargs sha256sum | sha256sum` (procédure publiée dans `docs/catalogue/README.md`).
- Limites, dans `_limites.py` : 8 Mio au total (la moitié de la configuration envoyée au processus de travail, qui transporte les règles), 256 fichiers, 4 096 règles ; 1 024 règles par fichier (schéma).
- Les règles sont triées par identifiant quel que soit le fichier : l'ordre d'évaluation ne dépend pas du découpage (NF-06).

## Raisons

- Découpage A : il suit l'unité de travail du projet, une technique par tâche ; B et C écartés pour la relecture et les conflits.
- Empreinte A : seule option qu'un lecteur recalcule avec les commandes de son système, ce qui rend la comparaison d'ADR-0029 possible sans faire confiance à l'outil ; B écartée parce qu'elle ignore les noms ; C parce qu'elle dépend d'un format d'archive.
- Fichier inattendu refusé plutôt qu'ignoré : un fichier ignoré changerait l'empreinte sans changer les règles, ou serait pris pour une règle par un lecteur.

## Conséquences

- Le chargeur est `src/voight_kampff/_orchestration/catalogue.py` ; la CI recalcule l'empreinte depuis le wheel sans installer le paquet (`.github/scripts/catalogue.py paquet`).
- Un catalogue fourni par l'utilisateur contenant un fichier de système (`.DS_Store`) est refusé, avec son nom.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
