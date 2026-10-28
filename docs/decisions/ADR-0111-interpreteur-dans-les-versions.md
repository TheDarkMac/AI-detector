# ADR-0111 — Interpréteur Python dans la rubrique Versions ; schéma du rapport 0.3.0

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac (question posée pendant T18, recommandation suivie)
- **Tâche** : T18
- **Exigences liées** : NF-06, §6 (rubrique Versions) ; ADR-0023, ADR-0036, ADR-0054, ADR-0095

## Contexte

ADR-0023 fait des versions de l'outil, du catalogue et des dépendances une condition de la garantie, et les inscrit au rapport. L'interpréteur n'y figurait pas, alors que sa version peut changer un résultat : base Unicode (`unicodedata`), `zlib` embarquée, arrondis, ordre de certains parcours. Deux rapports produits sous Python 3.12 et 3.14 ne disaient pas pourquoi ils pourraient différer.

## Options envisagées

### Option A — L'interpréteur au rapport

`versions.interpreteur` : implémentation (`sys.implementation.name`) et version (`platform.python_version()`).

- Avantages : la condition est visible ; deux rapports se comparent sans deviner l'interpréteur.
- Inconvénients : le schéma du rapport change.

### Option B — Rien de plus

- Avantages : schéma inchangé.
- Inconvénients : une différence due à l'interpréteur serait inexpliquée.

### Option C — L'interpréteur et le système

- Avantages : plus complet.
- Inconvénients : le système et sa version précisent le poste de l'utilisateur, donnée plutôt identifiante ; l'isolation reflète déjà le système.

## Décision

Option A. `Versions` gagne `interpreteur`, de la forme d'une dépendance (`nom`, `version`), obligatoire. `VERSION_SCHEMA` passe à **0.3.0** pour le modèle, le schéma du rapport et celui des messages (version commune, ADR-0054). Le HTML affiche « Interpréteur Python » dans la rubrique Versions. La valeur est lue dans le processus principal, qui lance le processus de travail par `sys.executable` (ADR-0036) : c'est le même interpréteur ; le protocole ne change pas.

## Raisons

- Option A retenue : elle complète la condition d'ADR-0023 sans donnée identifiante.
- Option B écartée : la CI compare désormais trois versions de Python (ADR-0110) ; un écart y serait inexplicable par le rapport.
- Option C écartée : donnée du poste sans utilité pour la reproductibilité.
- Lecture dans le principal plutôt que reçue du travail : même interpréteur par construction, et une donnée de moins à valider venant d'un processus qui lit un fichier hostile.

## Conséquences

- La comparaison classe une différence d'interpréteur comme une condition (ADR-0112).
- Un export JSON 0.2.0 n'est plus valide pour cette version de l'outil : aucune version du paquet n'est encore publiée (ADR-0068).
- Le HTML lit ses versions dans le rapport du modèle, comme le JSON : une seule source.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
