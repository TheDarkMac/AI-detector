# T04 — Architecture et choix techniques

- **Branche** : `tache/T04-architecture`
- **Dates** : 2026-10-26 → 2026-10-26
- **Exigences couvertes** : NF-01, NF-06, NF-10 ; ES-01, ES-02, ES-05, ES-10, ES-17, ES-18 ; F-05 (algorithme d'empreinte)
- **Décisions** : ADR-0034 à ADR-0044
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : fixer l'architecture et les choix techniques (langage, bibliothèques, format du catalogue, mécanismes d'isolation par système selon ADR-0028), le canal de distribution (ADR-0029), en les justifiant par T02 et T03, et réaliser les exigences de sécurité rattachées à T04. Livrable : ADR et schéma. S'y ajoutent les constats de l'analyse adressés à T04 (A-05, A-16, A-30, A-53), les renvois d'ADR-0010 (langage), ADR-0017 (point d'extension) et ADR-0023 (versions figées), et le point de méthode laissé ouvert à la fin de T03 (titre des commits de merge).

## État initial

- PR [#4](https://github.com/TheDarkMac/AI-detector/pull/4) (T03) : vérifications vertes (`lint-markdown`, `fichiers-interdits`) ; CodeRabbit présent, revue non effectuée (« skipped »), sans incidence. Pendant la revue, TheDarkMac a validé ADR-0033 et confirmé les points soumis dans la PR #3 (T02) : commit `e4fad27`, ADR-0033 au statut « Accepté » (journal de T03, étape 11).
- Mergée le 2026-10-26 à 10:45 UTC par l'assistant (`gh pr merge 4 --merge`), à la demande explicite de TheDarkMac ; commit de merge `4553193`, de nouveau à l'adresse noreply (ADR-0007).
- Ce commit de merge porte le titre par défaut de GitHub, « Merge pull request #4 from TheDarkMac/tache/T03-modele-de-menace », et non le format « Merge: TNN — titre (#N) » des PR #1 à #3 : l'option `--subject` n'avait pas été passée. Point tranché dans cette tâche (ADR-0044).
- Toujours en attente : transmettre à l'auteur du cahier les reformulations du registre (§4, dont NF-01, NF-16, NF-17, F-05) et relancer les six questions.
- `detector` à jour avec `origin/detector`, arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Branche `tache/T04-architecture` créée depuis `detector` à jour.
2. Relecture du cahier, du modèle de menace (§5, §8), du registre, des ADR qui renvoient à T04 (ADR-0010, ADR-0011, ADR-0017, ADR-0023, ADR-0028, ADR-0029) et des constats A-05, A-16, A-30, A-53.
3. Recherche de quatre faits techniques avant de formuler les options : licence de `c2pa-python` (Apache-2.0 ou MIT), portée de Landlock (TCP seulement, à partir du noyau 6.7, d'où le recours à seccomp pour les autres sockets), licence de `google-re2` (BSD-3-Clause). La disponibilité de ses paquets binaires n'a pas pu être confirmée : reportée à T10.
4. Onze choix identifiés qui relèvent de TheDarkMac, chacun avec deux à quatre options et une recommandation de l'assistant, posés en trois lots :
   - lot 1, langage et exécution : langage, systèmes et isolation, lancement du processus de travail, dépendances ;
   - lot 2, données et distribution : format du catalogue, expressions régulières, empreinte, canal de distribution ;
   - lot 3, modules et méthode : extension, politique des bibliothèques, titre des commits de merge.
5. Réponses : recommandation suivie pour les onze questions. Aucune raison supplémentaire n'a été donnée ; les ADR reprennent les raisons présentées avec les options.
6. Rédaction des ADR-0034 à ADR-0044. En rédigeant ADR-0035, les points dont l'assistant n'est pas sûr sans mesure (limite mémoire sous macOS, effet du niveau d'intégrité et des vidages sous Windows) sont marqués « à confirmer en T14 » plutôt qu'affirmés.
7. Rédaction de l'[architecture](../architecture/architecture.md) v1.0 : vue d'ensemble et déroulé d'une analyse (deux diagrammes Mermaid avec description textuelle), organisation du code, isolation par système, contrats de données, modules, catalogue, dépendances, reproductibilité, distribution, réalisation des ES rattachées à T04, points laissés aux tâches suivantes.
8. Documents vivants : découpage v0.8 (T04, T10, T12 à T15), registre v1.2 (nom du projet, points 9 et 10, constats adressés à T04), modèle de menace v1.1 (H2, RS-04, colonne « Décision » du §8), `CONTRIBUTING.md` (commande de merge), `docs/README.md`, index des ADR et du journal (T03 → #4) ; renvois ajoutés à l'historique d'ADR-0005, ADR-0010, ADR-0017, ADR-0023, ADR-0028, ADR-0029.
9. Lint Markdown en local, vérification des fichiers interdits, commits ; PR [#5](https://github.com/TheDarkMac/AI-detector/pull/5) ouverte.
10. Pendant la revue de la PR, TheDarkMac a accepté les quatre points fixés par l'assistant sans question : fichier transmis par descripteur, sans ouverture de chemin ni écriture par le processus de travail (ADR-0036) ; règles évaluées dans le processus de travail ; points « à confirmer en T14 » (ADR-0035) ; nom du projet préalable à T10 et à la publication. Il a demandé le merge une fois la CI verte, avec le titre fixé par ADR-0044.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Le découpage confie le format du catalogue à T04, ADR-0029 le confie à T15 | Deux formulations rédigées à des moments différents | Partage : T04 fixe le format d'écriture (ADR-0038), T15 le schéma et le contenu ; dit dans ADR-0038 |
| Un paquet publié avec des versions exactes rendrait la bibliothèque inutilisable à côté d'autres paquets, alors qu'ES-18 demande des versions figées | Double usage ligne de commande et bibliothèque (ADR-0010) | Plages dans le paquet, verrou pour le développement, fichier d'installation verrouillé publié, versions réelles au rapport (ADR-0037) |
| Où appliquer les règles du catalogue : dans P1, une expression régulière s'appliquerait à une donnée hostile hors bac à sable ; dans P2, un processus compromis peut forger ses constats | Compromis déjà relevé au modèle de menace (RR-01) | Règles évaluées dans P2 ; RR-01 inchangé ; P1 ne compile les expressions que pour valider le catalogue |
| Le nom du projet, non tranché, devient nécessaire | Le paquet Python a besoin d'un nom d'import (T10) et d'un nom sur PyPI (ADR-0041) | Noté `<paquet>` dans l'architecture ; inscrit au registre comme préalable à T10 |
| La protection de Windows ne bloque pas le réseau sans conteneur d'application | Limite du système pour un programme non privilégié | « Isolation réduite » au rapport ; conteneur recommandé sous Windows ; AppContainer à étudier plus tard (ADR-0035) |

## Écarts par rapport au découpage

- **Ajout** : ADR-0044 (titre des commits de merge), point de méthode sans rapport avec l'architecture, tranché ici parce que laissé ouvert à la fin de T03.
- **Ajout** : modèle de menace v1.1, pour y inscrire les ADR de T04 ; aucune menace ni surface nouvelle n'a été trouvée.
- Le livrable « schéma » est le document `docs/architecture/architecture.md`, qui porte les deux diagrammes.

## Résultat

- L'architecture v1.0, onze ADR acceptés (ADR-0034 à ADR-0044), le découpage v0.8, le registre v1.2, le modèle de menace v1.1.
- Vérification : `npx --yes markdownlint-cli2@0.23.2` ne signale aucune erreur ; aucun fichier interdit n'est suivi.

## Reste à faire

- Trancher le **nom du projet** avant T10 (nom d'import) et avant toute publication (réservation sur PyPI).
- T10 : disponibilité des paquets binaires de `google-re2` et `c2pa-python` sur les trois systèmes, examen des dépendances transitives, surveillance des failles, workflow de publication.
- T14 : points « à confirmer » d'ADR-0035, coût de démarrage du processus de travail, valeurs des limites.
- Transmettre à l'auteur du cahier les reformulations du registre (§4) et relancer les six questions.
