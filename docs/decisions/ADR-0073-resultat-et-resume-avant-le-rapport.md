# ADR-0073 — Avant le rapport : résultat d'analyse et résumé sans donnée identifiante

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T13
- **Exigences liées** : F-01, ES-13, ES-14, ES-17 ; ADR-0015, ADR-0031, ADR-0036, ADR-0063, ADR-0068

## Contexte

T13 ajoute la commande d'analyse et l'interface publique `analyser` (ES-17, ADR-0063), mais le rapport complet attend le catalogue (T15 : sa version est obligatoire au rapport) et l'export avec masquage (T16 : nom, empreinte et données identifiantes masqués par défaut, ADR-0031). Il faut décider ce que l'interface et la commande produisent d'ici là.

## Options envisagées

### Option A — Résultat d'analyse et résumé masqué

`analyser(chemin, desactiver)` rend l'identification et les résultats validés, sans rapport complet. La commande affiche, par fichier, un résumé sans nom ni empreinte.

- Avantages : aucun choix provisoire dans le modèle du rapport ; rien d'identifiant n'apparaît au terminal.
- Inconvénients : la commande ne produit pas encore de fichier exploitable par un autre programme.

### Option B — Rapport JSON dès T13

Le catalogue devient facultatif dans le modèle pour rendre déjà un `Rapport`, affiché en JSON.

- Avantages : sortie complète et structurée.
- Inconvénients : afficher le nom et l'empreinte en clair contredit ADR-0031 tant que T16 n'a pas fait le masquage ; un champ rendu facultatif pour attendre T15 resterait dans le schéma.

## Décision

Option A.

- `voight_kampff.analyser(chemin, *, desactiver=())` analyse un fichier dans un processus de travail neuf et rend une `Analyse` : identification, isolation, couverture, observations, constats, analyses non menées, dépendances. Elle est vérifiée comme un rapport (renvois entre objets, couverture par partie). Un fichier refusé lève `AnalyseRefusee`, qui porte un `motif` et un message explicite (ADR-0075) ; un module inconnu lève `ModuleInconnu` avant toute lecture.
- `voight_kampff/__init__.py` exporte `analyser`, `Analyse`, `AnalyseRefusee`, `MotifRefus`. Le processus principal n'est importé qu'à l'appel : le processus de travail, qui importe le paquet, n'en charge rien.
- `vk [--desactiver MODULE]... FICHIER...` analyse chaque fichier indépendamment (ADR-0015) et affiche un résumé repéré par le rang du fichier dans la commande (`[2/3]`) : format réel, extension et concordance, parties, plages non reconnues, isolation, techniques par partie, nombre d'observations et de constats, analyses non menées, interruption. Ni nom, ni empreinte, ni valeur d'observation. Un refus s'affiche sur la sortie d'erreur, au même rang.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle affiche des données identifiantes sans masquage et force un choix provisoire dans le schéma du rapport.
- Repérage par rang : l'utilisateur sait quel fichier il a donné en position 2 ; le terminal n'a pas à le répéter.

## Conséquences

- L'interface Python et les options de la commande font partie de l'interface publique (ADR-0068) : les changer tant que la version majeure vaut 0 augmente le numéro mineur.
- T16 ajoute la construction du rapport à partir d'une `Analyse`, les exports et le masquage ; le résumé du terminal sera alors revu.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
| 2026-10-28 | Complété en T16 : l'analyse porte les règles qu'elle cite et construit son rapport (ADR-0097) ; résumé du terminal revu, nom et empreinte masqués et levables (ADR-0093, ADR-0098) |
