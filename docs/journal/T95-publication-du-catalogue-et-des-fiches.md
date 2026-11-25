# T95 — Publication du catalogue et des fiches

- **Branche** : `tache/T95-publication-du-catalogue-et-des-fiches`
- **Dates** : 2026-11-25
- **Exigences couvertes** : NF-19 ; NF-07, NF-09 (lecture depuis l'outil)
- **Décisions** : ADR-0268 à ADR-0271
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : « Publication du catalogue et des fiches : tout est public (ADR-0019), plus de politique d'accès à développer », exigence NF-19. ADR-0019 avait reformulé NF-19 (« Le détail des règles et des seuils est public ») et réduit T95 à cette publication. Demandé par TheDarkMac le 2026-11-25 (« T95 (publication du catalogue et des fiches) »).

## État initial

- PR [#47](https://github.com/TheDarkMac/AI-detector/pull/47) (T92) : les 16 vérifications vertes sur `53820ee` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-25 à 08:46:13 UTC après le « Oui, merge si vert » de TheDarkMac, commit de merge `c562dd5`. Lancements de push sur `c562dd5` : code 45579204920 et docs 45579204682 verts, vérifiés le 2026-11-25.
- Catalogue 0.20.0 livré dans le paquet ; `vk --regles` n'affichait, par règle, que l'identifiant, la version, le module et le titre. Conditions, seuils, évaluation et calibrage ne se lisaient que dans les fichiers TOML du paquet.
- Les 25 fiches techniques n'étaient que dans `docs/techniques/` du dépôt public : le paquet construit n'en contenait aucune (vérifié dans le wheel de `dist/`), et ni le terminal ni le rapport n'y renvoyaient.
- NF-19 « partielle » dans la matrice (« Publication des fiches à T95 »).
- Toujours en attente : voir les journaux de T92, T91, T90, du complément de T81, de T81 et de T80 (« Reste à faire »).

## Déroulé

1. Lecture du découpage, d'ADR-0019, ADR-0029, ADR-0041, ADR-0064, du guide du catalogue et de celui des fiches, de la matrice (NF-19), de `cli.py`, de la rubrique Couverture du rapport HTML, de `.github/workflows/publication.yml` et `.github/scripts/catalogue.py`. Constats : dépôt public, aucune release ; la release porte déjà paquets, empreintes et `CATALOGUE.txt` ; le jeton de l'assistant n'a pas le droit `workflow`.
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation, sans raison supplémentaire : fiches copiées dans le paquet, `vk --fiche MODULE` ([ADR-0268](../decisions/ADR-0268-fiches-livrees-dans-le-paquet.md)) ; `vk --regle IDENTIFIANT` ([ADR-0269](../decisions/ADR-0269-detail-d-une-regle-par-vk-regle.md)) ; la couverture du rapport cite la commande, sans adresse ([ADR-0270](../decisions/ADR-0270-fiche-citee-par-la-couverture.md)) ; release inchangée, le paquet suffit ([ADR-0271](../decisions/ADR-0271-publication-par-le-paquet-et-versions-de-t95.md)).
3. Branche `tache/T95-publication-du-catalogue-et-des-fiches` créée depuis `detector` à jour (`c562dd5`).
4. Code : `banc/fiches.py` (`python -m banc.fiches`, `--verifier`) et copie des 25 fiches dans `src/voight_kampff/donnees/fiches/` ; `src/voight_kampff/_publication.py` (lecture d'une fiche livrée, écriture TOML des règles par la seule bibliothèque standard) ; `cli.py` : options `--regle` (répétable, seule ou avec `--catalogue`) et `--fiche` (seule) ; `_html.py` : colonne « Fiche technique » et paragraphe sous le tableau des techniques ; textes dans `textes.toml` (`[publication]`, `champs.fiche`, `formes.fiche`, `intros.fiches`).
5. Écriture TOML relue par `tomllib` pour les 151 règles du catalogue : elle redonne `Regle.vers_dict` et les mêmes règles. Première forme : les limites sur une seule ligne, illisibles ; une ligne par élément d'une liste de plusieurs.
6. Recherche de chaque chemin `docs/….md` cité par un fichier du paquet : un seul n'existe pas, dans l'en-tête de `marquages.toml` (`docs/techniques/filigranes-invisibles.md`, écrit en T31, jamais créé ; l'inventaire est `docs/catalogue/inventaire-des-marquages.md`). Corrigé en catalogue 0.20.1 (texte seul, `Z`), du 2026-11-25, empreinte `a89ff522b3458daedec28588a65b40f0c7be26c57c0934ff1ca5f746a14b43e2` calculée par la procédure du §4 du guide et ajoutée au registre.
7. Construction locale du paquet (`uv build`, uv 0.13.5 installé dans un environnement du dossier temporaire de la session, contraintes et empreintes du dépôt) : les 25 fiches sont dans le wheel et dans le sdist.
8. Essai à la main : `vk --fiche ela`, `vk --regle R-DOUBLEJPEG-001 --regle R-DWTDCT-001`, `vk --regle NOPE` (code 2), `vk --fiche nope` (code 2, modules livrés listés), `vk --fiche ela --regles` et `vk --regle R-DWTDCT-001 x.jpg` (code 2).
9. Tests : `tests/test_publication.py` (copie identique à la source et lancement de `python -m banc.fiches --verifier`, recopie et écarts, lecture depuis le paquet, fiches sans caractère invisible, `vk --fiche` et ses refus, neutralisation, fiche absente du paquet, TOML de chaque règle relu à l'identique, échappements, `vk --regle` et ses refus, catalogue fourni, colonne de la couverture, chemins `docs/` cités par le paquet).
10. Documentation : ADR-0268 à ADR-0271 ; guide des fiches (`docs/techniques/README.md`) et `CONTRIBUTING.md` (`python -m banc.fiches`) ; guide du catalogue v1.22 ; découpage v0.46 ; historique d'ADR-0019 ; `README.md` ; matrice : NF-19 « réalisée », méthodes test et inspection, régénérée (`python -m banc.matrice`).
11. Suite complète sous coverage, en 18 minutes 15 : 3 498 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), aucun échec. Couverture de tout le paquet et du banc à 100 %.
12. PR [#48](https://github.com/TheDarkMac/AI-detector/pull/48) ouverte vers `detector` (commits `96bbd39`, `582b542`, `eb4adea`, `8aec171`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Test de `python -m banc.fiches` sans effet sur les dossiers du test | Les chemins par défaut de `ecarts` et `recopier` étaient liés à la définition des fonctions | Chemins résolus à l'appel |
| Caractères `U+202E`, `U+2028` et `U+E0041` écrits en clair dans les tests | L'outil d'écriture de l'assistant écrit les échappements `\u` en caractères ; le balayage de l'assistant, ligne par ligne par `splitlines()`, coupait la ligne au `U+2028` et ne l'a pas vu ; Ruff l'a vu (RUF001) | Échappements rétablis, fichier relu caractère par caractère |
| `README.md` disait le catalogue « sans aucune règle » | Phrase de T15 jamais mise à jour | Remplacée par l'emploi de `vk --regles` et `vk --regle` |
| Statut du découpage resté à **v0.44** | T92 avait ajouté la v0.45 à l'historique sans changer le statut | Statut porté à v0.46, v0.45 mentionnée |

## Écarts par rapport au découpage

- Le catalogue change (0.20.1) alors que le découpage ne le prévoyait pas : la correction d'un renvoi mort du catalogue publié (ADR-0271).

## Résultat

- `vk --fiche MODULE` : la fiche technique d'un module livré, celle de la version installée, hors ligne.
- `vk --regle IDENTIFIANT` : tout d'une règle, dans la forme des fichiers du catalogue, relisible par `tomllib`.
- Rapport HTML : colonne « Fiche technique » à la couverture, renvoi à `vk --regle`. Rapport JSON, schémas (0.13.0) et modules inchangés ; catalogue 0.20.1.
- Paquet : 25 fiches dans `voight_kampff/donnees/fiches/`, copie tenue par `python -m banc.fiches`.
- Matrice : NF-19 « réalisée ».
- Vérification locale : suite complète (étape 11) ; Ruff, mypy et markdownlint sans erreur.

## Reste à faire

- T101 : les taux d'erreur mesurés remplissent la rubrique « Taux d'erreur » des fiches, livrées alors avec le paquet.
- T103 : la documentation utilisateur reprend `vk --regle` et `vk --fiche` ; la présentation du projet dans `README.md` décrit encore les seules premières techniques (métadonnées des images).
