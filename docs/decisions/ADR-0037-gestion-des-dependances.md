# ADR-0037 — Gestion des dépendances : uv et verrou à empreintes

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : NF-06 ; ES-18 ; constat A-05 ; ADR-0023

## Contexte

ADR-0023 demande à T04 de figer les versions des dépendances ; ES-18 demande des versions figées avec empreintes. Mais l'outil est aussi une bibliothèque (ADR-0010) : des versions exactes imposées dans le paquet publié entreraient en conflit avec celles du programme appelant. Il faut concilier reproductibilité, intégrité et usage en bibliothèque.

## Options envisagées

### Option A — uv, verrou à empreintes, plages dans le paquet publié

- Avantages : développement et CI reproductibles ; le paquet reste installable à côté d'autres ; une installation reproductible reste possible avec un fichier verrouillé publié.
- Inconvénients : deux façons d'installer (souple ou verrouillée) à documenter.

### Option B — pip-tools

- Avantages : même principe, outils de l'écosystème pip.
- Inconvénients : plus lent ; un fichier par environnement à compiler et à tenir.

### Option C — Versions exactes dans le paquet publié

- Avantages : reproductible sans fichier supplémentaire.
- Inconvénients : conflits dans l'environnement d'un programme appelant ; correctifs de sécurité bloqués jusqu'à une nouvelle version de l'outil.

### Option D — Dépendances embarquées

- Avantages : contrôle total du code exécuté.
- Inconvénients : mises à jour de sécurité à la main ; licences et code tiers à tenir dans le dépôt.

## Décision

- Le projet utilise **uv** ; le fichier `uv.lock`, versionné, fixe chaque dépendance avec son empreinte. La CI installe depuis ce verrou, sans résolution.
- Le paquet publié déclare des **plages de versions compatibles**, bornées vers le haut sur la version majeure.
- Chaque version publiée s'accompagne d'un **fichier d'installation verrouillé** (versions exactes et empreintes, dont le paquet lui-même) pour une installation reproductible ; la documentation donne la commande correspondante.
- Le rapport inscrit la version réelle de chaque dépendance qui décode ou analyse le fichier (ADR-0023), lue dans l'environnement du processus de travail.
- Les mises à jour de dépendances passent par une PR, comme tout changement.

## Raisons

- Option A retenue : elle satisfait ES-18 pour le développement et la publication sans rendre la bibliothèque inutilisable ; la rubrique Versions du rapport rend visible toute différence.
- Option B écartée : même résultat avec un outil plus lent et plus de fichiers.
- Option C écartée : conflits pour les programmes appelants.
- Option D écartée : charge de maintenance disproportionnée, et retard des correctifs de sécurité.

## Conséquences

- T10 met en place uv, le verrou, l'installation verrouillée en CI et la production du fichier d'installation verrouillé.
- La reproductibilité (T18) est testée avec le fichier verrouillé ; avec une installation souple, deux rapports peuvent différer, et la rubrique Versions dit pourquoi.
- La surveillance des failles connues des dépendances est à prévoir en T10.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : mis en place en T10 ; construction épinglée (ADR-0049), surveillance des failles (ADR-0052), fichier d'installation verrouillé produit par le workflow de publication (T10) |
