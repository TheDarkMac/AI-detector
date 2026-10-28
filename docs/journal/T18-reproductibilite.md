# T18 — Test de reproductibilité

- **Branche** : `tache/T18-reproductibilite`
- **Dates** : 2026-10-28
- **Exigences couvertes** : NF-06, P-05, critère du §8 ; A-05
- **Décisions** : ADR-0108 à ADR-0113
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : deux analyses identiques donnent des constats identiques (NF-06, critère du §8), dans les conditions de la garantie reformulée par ADR-0023 : même fichier, mêmes versions de l'outil, du catalogue et des dépendances, mêmes données externes, analyse non interrompue. Les ADR antérieurs adressaient à T18 : le test avec le fichier verrouillé (ADR-0037), la comparaison des constats de deux rapports non interrompus (ADR-0059, ADR-0097), la reproductibilité des mesures du banc (ADR-0105).

## État initial

- PR [#17](https://github.com/TheDarkMac/AI-detector/pull/17) (T17), ouverte le 2026-10-28 depuis `detector` `3830b18`. Déjà consigné dans le journal de T17 : étapes 1 à 16 (CI verte sur `5bb72fe` : code 40632869445, docs 40632869449 ; ADR-0103 à ADR-0107 et texte « evaluee » validés par TheDarkMac, acceptés dans `5f78bf1`).
- CI sur `5f78bf1` verte : code 40636052683, docs 40636052659 ; 15 vérifications, CodeRabbit « skipped » ; vérifiée avant le merge. Une première demande « C'est vert, merge » est arrivée alors que le lancement du code tournait encore : pas de merge, vérification refaite à la demande suivante.
- Mergée le 2026-10-28 à 05:10:02 UTC à la demande explicite de TheDarkMac (« Oui, accepter et merger », puis « Revérifier et merger ») : `gh pr merge 17 --merge --subject "Merge: T17 — Banc d'évaluation (#17)"`. Commit de merge `5096bce`, à l'adresse noreply (ADR-0007).
- Lancements de push sur `5096bce` : docs 40636389146 réussi ; code 40636389183, en cours au moment du merge, réussi (terminé à 05:13:10 UTC, vérifié au début de T18). La ligne de T17 dans l'index du journal portait « à venir » : corrigée en #17 dans cette tâche.
- `gh pr edit` échoue toujours : le corps d'une PR se met à jour par `gh api -X PATCH repos/TheDarkMac/AI-detector/pulls/N -F body=@fichier`.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`5096bce`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : T18 dépend de T11 à T17, mergées. Aucun module d'analyse n'est livré : une vraie analyse ne produit encore ni observation ni constat. La reproductibilité est donc éprouvée sur de vraies analyses (identification, couverture, techniques hors V1), sur le processus de travail factice des tests, qui produit observations, constats d'un module et du moteur, module en erreur, partiel et limite comptée, et sur le corpus d'essai. Lecture du découpage, des journaux de T16 et T17, d'ADR-0023, ADR-0037, ADR-0054, ADR-0059, ADR-0065, ADR-0076, ADR-0095, ADR-0097, ADR-0105, du constat A-05, de NF-06 et du §8 du cahier, du modèle, de la soumission, du processus de travail, des exports, du banc, des tests et de la CI. Constaté : la rubrique Versions ne cite pas l'interpréteur ; l'environnement du processus de travail est vidé (ADR-0065), donc sa graine de hachage change à chaque analyse.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation :
   - ce qui est comparé : le rapport entier, à la date et au nom près (recommandation suivie, [ADR-0108](../decisions/ADR-0108-resultats-identiques.md)) ;
   - forme : tests, banc **et** commande `vk --comparer` ; l'assistant recommandait tests et banc seulement, la commande étant hors du découpage ; TheDarkMac a choisi la commande en plus, sans raison supplémentaire ([ADR-0109](../decisions/ADR-0109-forme-du-test-de-reproductibilite.md)) ;
   - conditions variées : sur un poste et entre systèmes en CI (recommandation suivie, [ADR-0110](../decisions/ADR-0110-variations-locales-et-entre-systemes.md)) ;
   - interpréteur au rapport (recommandation suivie, [ADR-0111](../decisions/ADR-0111-interpreteur-dans-les-versions.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : réglages d'ADR-0110 (valeurs des variations, référence de la CI, exigence de résultats identiques entre versions de Python), [ADR-0112](../decisions/ADR-0112-comparaison-de-deux-rapports.md) (natures des écarts, garantie, sortie et codes), [ADR-0113](../decisions/ADR-0113-deux-analyses-par-fichier-au-banc.md) (double analyse au banc).
3. Branche `tache/T18-reproductibilite` créée depuis `detector` à jour (`5096bce`).
4. Interpréteur : `Versions.interpreteur` (`nom`, `version`) au modèle et au schéma du rapport ; `VERSION_SCHEMA` 0.3.0 (modèle, rapport, messages) ; `analyse.interpreteur()` lu dans le processus principal ; le HTML lit ses versions dans le rapport du modèle et affiche « Interpréteur Python ».
5. Comparaison : `voight_kampff/rapport/comparaison.py` (`lire`, `comparer`, `Comparaison`, `Ecart`, `Nature`) ; `vk --comparer A B` dans `cli.py`, textes dans `rapport/textes.toml` (table `comparaison`).
6. Banc : `analyser_corpus` analyse chaque fichier deux fois et compare les deux issues (`reproduction`) ; `ResultatFichier.non_reproduit`, écart « deux analyses différentes », `fichiers.non_reproduits` au document et au Markdown.
7. Tests : `tests/test_reproductibilite.py` (analyses répétées par le processus de travail factice, polyglotte, module non reproductible détecté, vrais processus de travail sur six formats, deux lancements de la commande sous d'autres conditions avec rapports JSON et HTML identiques octet pour octet à la date près, chaque nature d'écart, masquage, types, interpréteur, lecture d'un export, commande et ses codes) ; analyseurs factices `theta` (limite comptée) et `kappa` (numéro de processus) dans `travail_factice.py` ; tests du banc pour la double analyse ; tests existants adaptés à l'interpréteur et au schéma 0.3.0.
8. CI : job `tests`, rapports de huit fichiers du corpus d'essai joints (`rapports-<système>-<python>`) ; job `reproductibilite`, qui les compare au jeu Linux Python 3.13 par `vk --comparer` (`actions/download-artifact` v8.0.2, épinglé par empreinte de commit) ; job `paquet`, banc sans fichier non reproduit, comparaison de deux rapports depuis le wheel ; `code-ok` attend `reproductibilite`. Étapes rejouées en local : boucle de comparaison sur deux jeux, étape du wheel, banc sous `unshare -rn` (code 1, seul écart la cible par fichier, `non_reproduits` 0).
9. Vérification locale : `uv lock --check` ; Ruff (format et analyse) et mypy sans remarque ; pip-audit, aucune faille connue ; matrice vérifiée ; lint Markdown (`npx --yes markdownlint-cli2@0.23.2`) sans remarque ; 1 008 tests verts, un sauté (lanceur de Windows), couverture 100 % lignes et branches.
10. Documentation : ADR-0108 à ADR-0113 ; renvois dans ADR-0023, ADR-0037, ADR-0054, ADR-0059, ADR-0097, ADR-0105 ; matrice (NF-06 et P-05 réalisées) ; découpage v0.17, architecture v1.11, modèle de données v1.6, registre des arbitrages v1.10, glossaire v1.7, vérification v1.1 ; `CONTRIBUTING.md` (§5), `README.md` ; index des ADR et du journal.

11. Commits, branche poussée, PR [#18](https://github.com/TheDarkMac/AI-detector/pull/18) ouverte vers `detector` ; Auto-fix activé à la demande de TheDarkMac. CodeRabbit n'a pas relu la PR (dépôt de moins de 10 étoiles) : rien à traiter.
12. CI de la PR sur `1bd7905` (code 40691605652) : verte sous Linux et macOS (Python 3.12 à 3.14), `qualite`, `paquet` et `audit-dependances` verts ; en échec sous Windows (3.12 à 3.14) sur `test_commande_defaut_de_reproductibilite` (voir ci-dessous), donc `reproductibilite` sauté et `code-ok` en échec. La comparaison était juste ; test corrigé.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Un document comparé à sa copie JSON montrait des écarts sur chaque énumération | `export.document` garde les `StrEnum` du modèle ; la comparaison exigeait le même type Python | Comparaison par valeur et type JSON : une énumération vaut sa chaîne, `1`, `1.0` et `true` restent différents |
| Le nom, absent d'un export masqué, apparaissait comme un écart | Une clé présente d'un seul côté était relevée avant le contrôle des champs ignorés | Valeur « absente » comparée comme les autres, après ce contrôle |
| Deux exports à empreinte masquée annonçaient « même fichier » | La garantie ne tenait pas compte de l'empreinte non comparée | `meme_fichier` : sans empreinte comparée, hors garantie, et la commande dit d'écrire les rapports avec `--reveler empreinte` ; le nom, jamais comparé, n'est plus cité parmi les catégories non comparées |
| Le module factice `alpha` finissait en erreur dans le nouveau test | Le manifeste du test ne déclarait pas la direction de ses constats | Direction « rien de particulier » déclarée, comme dans les autres tests |
| Une archive ZIP refusée par la commande | Format reconnu, hors du périmètre | Remplacée par un ODT dans les échantillons du test |
| Le HTML contient deux dates, d'une autre forme que le JSON | En-tête et identification, « AAAA-MM-JJ HH:MM:SS » | Neutralisation des deux formes, nombre attendu par format |
| `test_commande_tentative_de_reseau` en échec | Chaque fichier étant analysé deux fois, la tentative de la fausse analyse est notée deux fois | Message attendu avec les deux tentatives (ADR-0113) |
| Une ligne de la comparaison hors couverture | Une valeur `null` n'arrive jamais d'un rapport valide | Cas ajouté au test des types |
| CI Windows : `test_commande_defaut_de_reproductibilite` en échec | Le test ne fixait l'isolation que d'un des deux rapports ; sous Windows, celle de l'analyse de référence est réduite (plusieurs restrictions manquent), d'où d'autres écarts d'isolation que ceux attendus | Isolation fixée dans les deux rapports du test |
| Matrice périmée au premier passage complet | Les tests ont été lancés avant de régénérer la matrice | Relancés après régénération |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. L'absence de l'interpréteur dans la rubrique Versions (ADR-0023) est complétée par ADR-0111.

## Écarts par rapport au découpage

- **Ajout** : commande `vk --comparer`, choisie par TheDarkMac (ADR-0109) ; interpréteur dans la rubrique Versions et schéma du rapport 0.3.0 (ADR-0111) ; double analyse au banc (ADR-0113) ; job `reproductibilite` en CI (ADR-0110).
- **Plus strict que la garantie** : la CI exige les mêmes résultats sous Python 3.12, 3.13 et 3.14, bien que l'interpréteur soit une condition (ADR-0110).
- **Non fait** : les données externes (liste de confiance C2PA, réponses réseau) n'existent pas encore ; T30 les ajoute aux conditions (ADR-0112).

## Résultat

- `vk --comparer A.json B.json` compare deux rapports du même fichier et dit si leurs résultats sont identiques, si la garantie s'applique et, sinon, pourquoi ; codes 0, 1 et 2.
- Le rapport inscrit l'interpréteur ; le banc analyse chaque fichier deux fois ; la CI compare les rapports du corpus d'essai entre trois systèmes et trois versions de Python.
- NF-06 et P-05 sont réalisées dans la matrice.

## Reste à faire

- T30 : liste de confiance et données externes, conditions de la garantie.
- T103 : documentation utilisateur de `vk --comparer`.
- Chaque technique livrée : résultats dans un ordre déterministe, vérifiés par le banc et la CI.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
