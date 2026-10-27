# ADR-0069 — Contrôles de la publication : étiquette sur `detector`, pré-version marquée

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : demande de TheDarkMac ; options et choix de l'assistant, soumis dans la PR
- **Tâche** : T10 (complément)
- **Exigences liées** : ES-18 ; ADR-0041, ADR-0050, ADR-0053, ADR-0068

## Contexte

Le workflow `publication.yml` (T10) se lance sur toute étiquette `v*` égale à la version du paquet. Deux défauts relevés après le merge de la PR #11 :

1. une étiquette posée sur n'importe quel commit (une branche de tâche, un commit jamais mergé) déclenche la publication ; seule la relecture obligatoire de l'environnement `pypi` l'arrête, et elle montre le nom de l'étiquette, pas d'où vient le commit ;
2. la release GitHub n'est jamais marquée comme pré-version : une version `0.1.0.dev0` apparaîtrait comme la dernière version du dépôt.

## Options envisagées

### Origine du commit étiqueté

#### Option A — Commit de l'historique de premier parent de `detector` *(retenue)*

Le commit étiqueté doit être un commit de `detector` lui-même : en pratique un commit de merge (ADR-0050).

- Avantages : le paquet est construit à partir d'un état que `detector` a réellement eu, après la CI et la revue de la PR ; un commit intermédiaire d'une branche de tâche, même mergée ensuite, est refusé.
- Inconvénients : le workflow récupère tout l'historique (petit aujourd'hui).

#### Option B — Commit ancêtre de `detector`

- Avantages : contrôle plus simple (`git merge-base --is-ancestor`).
- Inconvénients : accepte un commit intermédiaire d'une branche de tâche, état que `detector` n'a jamais eu et que la CI de la PR n'a peut-être pas vérifié.

#### Option C — Règle GitHub qui réserve la création des étiquettes `v*` à TheDarkMac

- Avantages : bloque l'étiquette avant même le lancement du workflow.
- Inconvénients : réglage du dépôt, hors du code, que cette PR ne peut pas porter ; complémentaire des options A et B, pas un substitut (elle ne dit rien du commit). Écartée pour cette PR ; reste possible sur demande de TheDarkMac.

#### Option D — Ne rien ajouter

- Inconvénients : la protection repose entièrement sur l'attention du relecteur.

### Marquage de la release GitHub

#### Option E — Déduit de la version, selon PEP 440 *(retenue)*

Le workflow vérifie que la version (normalisée par uv) est une version publique PEP 440 ; elle est une pré-version si elle contient `aN`, `bN`, `rcN` ou `.devN`. La release reçoit alors `--prerelease`, ce qui l'exclut de « dernière version ».

- Avantages : aucune étape manuelle ; même règle que pip et PyPI ; indépendante du choix d'ADR-0068.
- Inconvénients : une expression régulière à maintenir, testée en local sur neuf formes de version.

#### Option F — Release créée en brouillon, publiée à la main

- Avantages : relecture des notes avant publication.
- Inconvénients : étape manuelle de plus, donc oubli possible ; les paquets seraient déjà sur PyPI.

#### Option G — Toujours en pré-version tant que la version commence par `0.`

- Inconvénients : confond une version `0.y.z` stable avec une pré-version, contraire à PEP 440.

## Décision

Le workflow refuse une étiquette dont le commit n'est pas dans l'historique de premier parent de `detector` (option A), et refuse une version qui n'est pas sous forme publique PEP 440 ; une pré-version donne une release GitHub marquée `--prerelease` (option E).

## Raisons

- Option A retenue : ADR-0050 prévoit l'étiquette sur le commit de merge ; c'est l'état vérifié par la CI et relu. Option B écartée : elle laisse passer des états jamais vérifiés. Option C écartée pour cette PR : réglage du dépôt, à proposer à part. Option D écartée : protection insuffisante.
- Option E retenue : automatique et conforme à PEP 440. Option F écartée : étape manuelle. Option G écartée : contraire à PEP 440.

## Conséquences

- Les deux contrôles tournent dans le job `construction`, avant toute construction : une étiquette refusée ne publie rien et ne demande pas d'approbation.
- Une version locale (`+…`), refusée par PyPI, est refusée dès ce job.
- Le contrôle de l'étiquette lit `origin/detector` : la branche par défaut (ADR-0053) ne doit pas changer de nom sans mettre à jour le workflow.
- Pièges évités : avec `pipefail` (actif par défaut dans les étapes `bash` de GitHub Actions), un tube `git rev-list | grep -q` peut échouer quand `grep` s'arrête avant la fin de la sortie ; le contrôle lit donc l'historique par substitution de processus. Le commit est lu par `git rev-parse HEAD` plutôt que `GITHUB_SHA`.
- Ces contrôles ne s'exercent qu'à une vraie publication : testés en local (commits de `detector` acceptés, commits de branche de tâche refusés ; neuf formes de version), pas encore sur GitHub.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR : statut « Accepté » |
