# ADR-0268 — Fiches techniques livrées dans le paquet, lisibles par `vk --fiche MODULE`

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T95
- **Exigences liées** : NF-19, NF-09, NF-07, ES-12 ; livrable 4 ; ADR-0010, ADR-0019, ADR-0022, ADR-0041, ADR-0064

## Contexte

ADR-0019 a rendu tout public et réduit T95 à « la publication du catalogue et des fiches ». Le catalogue est livré dans le paquet depuis T15 (ADR-0029). Les 25 fiches techniques (livrable 4 : principe, limites connues, taux d'erreur) ne sont que dans `docs/techniques/` du dépôt public : le paquet installé n'en contient aucune, et rien dans l'outil n'y renvoie. Un utilisateur hors ligne (ADR-0010) ne peut donc pas lire la fiche d'une technique, et en ligne, rien ne lui dit laquelle correspond à la version qu'il emploie.

## Options envisagées

### Option A — Copie dans le paquet, `vk --fiche MODULE` (recommandée)

Une copie de chaque fiche, octet pour octet, dans `src/voight_kampff/donnees/fiches/`, écrite par `python -m banc.fiches` ; un test vérifie qu'elle est identique à sa source.

- Avantages : lisible hors ligne ; la fiche affichée est celle de la version installée ; la publication suit le paquet (PyPI, release) sans autre canal.
- Inconvénients : deux exemplaires de chaque fiche dans le dépôt, qu'il faut garder identiques ; le paquet grossit d'environ 360 Kio.

### Option B — Dépôt seul, adresse donnée par l'outil

- Avantages : un seul exemplaire.
- Inconvénients : lire la fiche demande le réseau ; une version de développement n'a pas d'étiquette à citer, et une adresse sur `detector` peut décrire une autre version que celle installée.

### Option C — Site statique (GitHub Pages)

- Avantages : lecture confortable, liens actifs.
- Inconvénients : un workflow de plus, que l'assistant ne peut pas pousser (jeton sans droit `workflow`) ; réseau toujours nécessaire ; même question de version que l'option B.

## Décision

Option A.

- **Source** : `docs/techniques/<fiche>.md`, seule à modifier. **Copie** : `src/voight_kampff/donnees/fiches/<fiche>.md`, une par module livré, nommée par le champ `fiche` de son manifeste (ADR-0064), aucun autre fichier (ni `README.md`, ni `gabarit.md`).
- `python -m banc.fiches` recopie les fiches et retire celle d'un module qui n'est plus livré ; `--verifier` échoue si la copie diffère. `tests/test_publication.py` lance `--verifier` et vérifie la copie fiche par fiche : la CI la contrôle sans workflow modifié.
- **`vk --fiche MODULE`**, seule (code 2 avec toute autre option ou un fichier ; code 2 pour un module inconnu, avec la liste des modules livrés) : une ligne d'en-tête (module et version, version de l'outil, renvois relatifs désignant le dossier `docs/` des sources), puis la fiche en Markdown, telle quelle. Chaque ligne passe par la neutralisation du terminal (ES-12) ; un test vérifie qu'elle ne change aucune fiche livrée.
- Écartés : un lien symbolique (mal suivi sous Windows et par certains outils de construction) ; le champ `data` de `uv_build`, qui installe hors du paquet `voight_kampff` et demanderait aussi une copie.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : elle contredit le fonctionnement hors ligne par défaut (ADR-0010) et ne garantit pas que la fiche lue décrit le code employé.
- Option C écartée : mêmes défauts que l'option B, et un workflow que seul TheDarkMac peut pousser.

## Conséquences

- Toute PR qui change une fiche lance `python -m banc.fiches` et commite les deux exemplaires ; sinon les tests échouent (`CONTRIBUTING.md`, `docs/techniques/README.md`).
- Un module ajouté apporte sa fiche dans les deux dossiers.
- Le wheel et le sdist portent les 25 fiches (vérifié par une construction locale, T95).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
