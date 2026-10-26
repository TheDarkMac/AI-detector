# T10 — Squelette du projet Python et outillage

- **Branche** : `tache/T10-squelette`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : NF-09 (outillage) ; ES-18 ; §10 du cahier (nom du projet)
- **Décisions** : ADR-0045 à ADR-0052
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : squelette du projet Python (ADR-0034), outillage (formatage, analyse statique, tests), uv et verrou à empreintes (ADR-0037), intégration continue sur Linux, macOS et Windows (ADR-0035), workflow de publication PyPI avec attestations (ADR-0041), examen des dépendances transitives et disponibilité des paquets binaires (ADR-0039, ADR-0043). Préalable : trancher le nom du projet (registre des arbitrages).

## État initial

- PR [#5](https://github.com/TheDarkMac/AI-detector/pull/5) (T04) : vérifications vertes sur le commit `34bf31e` (`lint-markdown`, `fichiers-interdits`) ; CodeRabbit « skipped », les revues étant désactivées pour la branche cible.
- Pendant la revue, TheDarkMac a accepté les quatre points soumis dans la PR (journal de T04, étape 10) : commit `34bf31e`.
- Mergée le 2026-10-26 à 11:37 UTC par l'assistant, à la demande explicite de TheDarkMac, avec `gh pr merge 5 --merge --subject "Merge: T04 — Architecture et choix techniques (#5)"` : première application d'ADR-0044. Commit de merge `c6369ac`, à l'adresse noreply (ADR-0007).
- Index du journal : la ligne T04 portait encore « à venir », corrigée en #5 dans cette tâche.
- Toujours en attente : transmettre à @Jean les reformulations du registre (§4) et relancer les six questions.
- `detector` à jour avec `origin/detector`, arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.
- Constaté en cours de tâche (étape 4) : le dépôt était **privé**, et `detector` comme `main` n'étaient plus protégées.

## Déroulé

1. **Nom du projet**, tranché avec TheDarkMac avant la création de la branche. Il a proposé VOIGHT (test de Voight-Kampff, *Blade Runner*) ou T-1000 (*Terminator 2*). L'assistant a recommandé la référence à Voight-Kampff : elle désigne ce que l'outil fait (démasquer l'artificiel) et non l'adversaire, sans promettre de certitude (NF-14). TheDarkMac a d'abord retenu VOIGHT. La vérification sur PyPI a montré que `voight` était pris (outil de test pour agents d'IA, janvier 2026), puis que `voight-kampff` l'était aussi (lanceur de linters, 2023). TheDarkMac a retenu : projet Voight-Kampff, paquet `voight-kampff-forensics`, import `voight_kampff`, commandes `voight-kampff` et `vk` → ADR-0045.
2. Branche `tache/T10-squelette` créée depuis `detector` à jour (`c6369ac`).
3. Examen des dépendances candidates d'ADR-0043 sur PyPI : paquets précompilés par système et version de Python, licences, dépendances transitives, date de la dernière version. Résultats dans l'[architecture](../architecture/architecture.md) §9. Faits qui ont pesé sur les choix : `google-re2` n'a pas de paquet pour Python 3.15 ; `c2pa-python` 0.38.1 n'a pas de paquet pour Windows et tire `requests` et `toml`.
4. Relecture de la configuration GitHub : dépôt **privé**, protection des branches illisible (« 403 », réservée aux dépôts publics sur le plan gratuit). Environnements protégés indisponibles, minutes macOS comptées dix fois.
5. Premier lot de questions à TheDarkMac : visibilité du dépôt, outillage de qualité, cadre de tests, surveillance des failles. Recommandation suivie pour les quatre.
6. Second lot : confirmation du passage en public, après rappel de ce qui devient visible (adresse e-mail des commits, cahier de @Jean) ; versions de Python de la CI ; outil de construction ; emplacement du numéro de version. Recommandation suivie pour les quatre. Aucune raison supplémentaire n'a été donnée : les ADR reprennent les raisons présentées avec les options.
7. Dépôt rendu public par l'API (`PATCH repos/TheDarkMac/AI-detector`, `visibility=public`). La protection a été relue ensuite : « Branch not protected » sur `detector` et `main`, les règles d'ADR-0001 avaient disparu. Une première tentative de les rétablir a été bloquée par une demande de permission de l'outil de l'assistant ; elle a été refaite à l'étape 13, après accord de TheDarkMac.
8. ADR-0045 (nom), registre des arbitrages v1.3, renvois dans ADR-0008 et ADR-0041 ; premier commit.
9. Installation de uv 0.13.5 dans un environnement temporaire de l'assistant, uv étant absent du poste. Python 3.13 du système utilisé en local ; la CI couvre 3.12 à 3.14.
10. Squelette : `pyproject.toml` (paquet, commandes, groupe `dev`, réglages de Ruff, mypy, pytest et coverage), `src/voight_kampff/` (`__init__.py`, `__main__.py`, `cli.py` réduit à `--version` et à l'aide, `py.typed`), `tests/test_cli.py` (quatre tests, dont le lancement par `python -I -m voight_kampff`), `.gitignore`, `README.md` renommé. `uv lock` : 41 paquets verrouillés avec empreintes.
11. Vérifications locales : Ruff (formatage et règles), mypy strict, pytest, couverture à 100 % une fois mesurés les processus lancés par les tests. Construction faite deux fois : fichiers identiques. Paquet source limité à `pyproject.toml`, `README.md` et `src/`. Wheel installé dans un environnement neuf, `vk --version` et `voight-kampff --version` vérifiés. Fichier d'installation verrouillé produit comme le fera la publication, puis installé avec `--require-hashes`. pip-audit : aucune faille connue.
12. Outil de construction épinglé avec empreintes (`contraintes-construction.txt`), actions épinglées par empreinte de commit (dernières versions publiées au 2026-10-26), workflows `code` et `publication`, configuration Dependabot.
13. Troisième lot : PR de Dependabot (exception admise à ADR-0003 et ADR-0005) ; réglages GitHub faits par l'assistant via `gh`, sur accord de TheDarkMac. Faits et relus par l'API :
    - `detector` : PR obligatoire (0 approbation), `lint-markdown` et `fichiers-interdits` requis en mode strict, conversations résolues, `enforce_admins`, force-push et suppression interdits ;
    - `main` : `enforce_admins`, force-push et suppression interdits ;
    - environnement `pypi` : relecture obligatoire de TheDarkMac, déploiement limité aux étiquettes `v*`.
14. ADR-0046 à ADR-0052 ; renvois dans ADR-0001, ADR-0003, ADR-0005, ADR-0006, ADR-0037, ADR-0039, ADR-0041, ADR-0043 ; architecture v1.1, découpage v0.9, `CONTRIBUTING.md` (outillage, vérifications obligatoires, mise à jour de uv, PR de Dependabot), index des ADR et du journal.
15. Lint Markdown en local, vérification des fichiers interdits, commits ; branche poussée et PR ouverte vers `detector`.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| `voight` puis `voight-kampff` déjà pris sur PyPI | Noms courts déjà réservés | Nom publié distinct, `voight-kampff-forensics` ; conflit possible de nom d'import avec le paquet de 2023, accepté (ADR-0045) |
| Dépôt privé, protections de `detector` et `main` supprimées | Changement de visibilité antérieur à T10, de date et d'origine inconnues ; sur le plan gratuit, un dépôt privé perd la protection des branches | Dépôt repassé en public, protections rétablies et relues (ADR-0046). L'historique de `detector` ne contient que des commits de merge de PR : aucun push direct n'a eu lieu pendant la période |
| Rétablissement des protections refusé une première fois | Contrôle des permissions de l'outil de l'assistant sur les modifications de ressources partagées | Question posée à TheDarkMac, puis commandes refaites une à une après son accord |
| `google-re2` sans paquet pour Python 3.15 | Dernière version de novembre 2025, antérieure à Python 3.15 | Matrice limitée à 3.12 à 3.14 ; 3.15 à ajouter plus tard (ADR-0051) |
| L'outil de construction n'est pas couvert par `uv.lock` | Le verrou ne porte que sur les dépendances du projet | `contraintes-construction.txt` avec empreintes, `--require-hashes` (ADR-0049) |
| Couverture de `__main__.py` à 0 % | Ce fichier ne s'exécute que dans l'interpréteur lancé par le test | `patch = ["subprocess"]` et `coverage combine` (ADR-0048) |
| Le lint Markdown local signalait des erreurs dans `.venv/` | Le motif `**/*.md` inclut les paquets installés par `uv sync` | `.venv/**` exclu dans `.markdownlint-cli2.jsonc` ; sans effet en CI, où `.venv/` n'existe pas |
| `gh repo edit --visibility` refusé | Version de `gh` du poste : option de confirmation inconnue | Appel direct de l'API (`gh api -X PATCH`) |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. Le dépôt privé contredit une hypothèse d'ADR-0001 (« dépôt public ») sans qu'ADR-0001 ait été faux à sa date ; la nouvelle décision fait l'objet d'ADR-0046.

## Écarts par rapport au découpage

- **Ajout** : ADR-0046 (visibilité du dépôt), rendu nécessaire par l'état trouvé au démarrage.
- **Ajout** : Dependabot et son exception aux règles d'identité et de nommage (ADR-0052).
- **Reporté** : le fichier `LICENSE` (ADR-0011), sur instruction de TheDarkMac, tant que @Jean n'a pas clarifié le statut du cahier. Le workflow de publication refuse de publier sans lui.
- **Reporté** : `code-ok` dans les vérifications obligatoires de `detector`, ajouté après son premier passage sur la PR de T10 (ADR-0051), pour que le nom exigé soit celui que la CI rapporte vraiment.

## Résultat

- Paquet `voight_kampff` installable, commandes `voight-kampff` et `vk` (affichent l'aide et la version) ; aucune dépendance d'exécution.
- Outillage : uv, verrou à empreintes, Ruff, mypy strict, pytest et coverage ; CI du code sur 9 combinaisons, audit des failles, construction reproductible ; workflow de publication prêt, non déclenché.
- Dépôt public, protections rétablies, environnement `pypi` créé.
- Huit ADR (ADR-0045 à ADR-0052), architecture v1.1, découpage v0.9, registre v1.3.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent ; `npx --yes markdownlint-cli2@0.23.2` ne signale aucune erreur ; aucun fichier interdit n'est suivi.

## Reste à faire

- TheDarkMac : déclarer l'éditeur de confiance sur PyPI (projet `voight-kampff-forensics`, dépôt `TheDarkMac/AI-detector`, workflow `publication.yml`, environnement `pypi`) ; la première publication, qui réservera le nom, attend aussi le fichier `LICENSE`.
- @Jean : statut du cahier des charges, désormais public (ADR-0011, ADR-0046) ; reformulations du registre (§4) et six questions.
- Ajouter `code-ok` aux vérifications obligatoires de `detector` après le premier passage de la CI.
- T15 : ajouter la version et l'empreinte du catalogue à la release (ADR-0041).
- T20 : maintenance de `defusedxml`. T30 : `c2pa-python` sous Windows, `requests` et `toml` parmi ses dépendances. Python 3.15 quand `google-re2` le prend en charge.
- Fixer un seuil de couverture quand le socle existe (ADR-0048) et les règles de numérotation avant la première publication (ADR-0050).
