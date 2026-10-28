# ADR-0103 — Manifeste du corpus : catégories, parties par groupe, origine et provenance

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T17, validée pendant la revue de la PR de T17
- **Tâche** : T17
- **Exigences liées** : §8 du cahier, ES-22 ; M-33 ; ADR-0016 ; A-12

## Contexte

Le banc doit savoir, pour chaque fichier du corpus, ce qu'il est réellement, à quelle catégorie du §8 il appartient (authentiques, générés, transformés, retouchés, malformés) et dans quelle partie il est (calibrage ou évaluation, ADR-0016). ES-22 demande une provenance documentée, un corpus versionné et un calibrage reproductible. Le corpus lui-même est constitué en T100 ; T17 en fixe la description.

## Options envisagées

### Option A — Manifeste TOML validé par schéma, partie déclarée, groupes d'origine

Un fichier `corpus.toml` par corpus : en-tête versionné, puis une entrée par fichier avec chemin, empreinte, catégorie, partie, groupe, origine réelle, transformation, provenance.

- Avantages : même format que le catalogue (ADR-0038), relu et comparé dans une PR ; la partie est choisie par qui constitue le corpus, qui peut équilibrer catégories et générateurs ; le groupe empêche qu'un original et ses transformations soient de part et d'autre.
- Inconvénients : la partie est une décision humaine ; il faut vérifier qu'elle n'est pas ajustée après coup.

### Option B — Partie tirée de l'empreinte

- Avantages : aucune décision humaine.
- Inconvénients : un original et sa version recompressée ont des empreintes différentes et tomberaient dans des parties différentes, ce qu'A-12 interdit ; pas d'équilibrage par catégorie.

### Option C — Arborescence de dossiers (`evaluation/authentiques/…`)

- Avantages : rien à écrire.
- Inconvénients : ni origine, ni provenance, ni empreinte ; un fichier déplacé change de partie sans trace.

## Décision

Option A, schéma `banc/corpus.schema.json` :

- **En-tête** : `format` (1), `nom`, `version` (même forme que la version de corpus citée par le catalogue), `date`, `nature` (`essai` ou `reference`, ADR-0105), `description`.
- **Entrée** : `chemin` (relatif au manifeste, sans `.` ni `..`), `empreinte` SHA-256, `categorie`, `partie`, `groupe`, `origine` (`authentique`, `ia`, `retouche`), `transformation` pour un fichier transformé seulement, `provenance` (`source`, `licence`, `date`, `generateur` obligatoire pour une origine IA, `remarque`).
- **Cohérences** : un authentique est d'origine authentique, un généré d'origine IA, un retouché d'origine retouchée, un transformé d'origine authentique ou IA ; seul un malformé peut être sans origine (fichier piégé fabriqué de toutes pièces).
- **Contrôles au chargement** : chemins uniques, sans tenir compte de la casse ; empreintes uniques (le même contenu deux fois fuirait d'une partie à l'autre) ; chaque groupe dans une seule partie.
- **Contrôle avant chaque analyse** : le fichier est dans le dossier du corpus (pas de lien vers l'extérieur) et son empreinte est celle du manifeste ; sinon tout s'arrête (code 2).
- L'empreinte des octets du manifeste identifie le corpus évalué et figure au rapport d'évaluation.

## Raisons

- Option A retenue : elle porte tout ce qu'ES-22 et le §8 demandent, et la règle des groupes rend la séparation d'ADR-0016 vérifiable.
- Option B écartée : elle casserait les groupes.
- Option C écartée : ni provenance ni vérité de référence.
- Partie déclarée : le risque d'ajustement après coup est tenu par le versionnage du manifeste, relu en PR, et par l'empreinte au rapport.

## Conséquences

- T100 écrit le manifeste du corpus de référence ; la répartition entre parties est décidée avant toute mesure et ne change plus qu'avec une nouvelle version du corpus.
- Les fichiers du corpus de référence n'ont pas à être dans le dépôt : le manifeste désigne leur dossier.
- Le schéma du corpus est propre au banc, hors du paquet.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
| 2026-10-28 | Validé par TheDarkMac pendant la revue de la PR de T17 : statut « Accepté » |
