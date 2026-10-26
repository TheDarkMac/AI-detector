# ADR-0046 — Visibilité du dépôt : public

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T10
- **Exigences liées** : méthode de travail ; ES-18 ; ADR-0001, ADR-0006, ADR-0011, ADR-0035, ADR-0041

## Contexte

ADR-0001 a choisi la protection des branches en supposant un dépôt public. Au démarrage de T10, le dépôt était **privé** ; ni la date ni la raison du changement ne sont connues, et l'assistant ne l'a pas fait. Sur le plan gratuit de GitHub, un dépôt privé perd ce qu'ADR-0001 et ADR-0041 supposent :

- protection des branches : l'API répondait « 403 » ; après le retour en public, elle répondait « Branch not protected » : les règles d'ADR-0001 avaient été supprimées ;
- environnements protégés : indisponibles, alors qu'ADR-0041 publie depuis un environnement protégé ;
- minutes d'intégration continue : 2 000 par mois, une minute macOS comptant pour 10, une minute Windows pour 2, alors qu'ADR-0035 demande des tests sur les trois systèmes.

## Options envisagées

### Option A — Repasser le dépôt en public

- Avantages : protection des branches, environnements protégés et intégration continue gratuite sur les trois systèmes ; cohérent avec un logiciel libre (ADR-0011) dont les règles sont publiques (ADR-0019).
- Inconvénients : tout l'historique devient visible, y compris l'adresse e-mail des commits (ADR-0003) et le cahier des charges de @Jean ; un contenu publié peut être copié ou indexé même si le dépôt redevient privé.

### Option B — Rester privé, intégration continue réduite

- Avantages : rien n'est exposé.
- Inconvénients : `detector` n'est plus protégé par GitHub, la règle « aucun push direct » ne tient que par discipline ; macOS et Windows testés sur une seule version de Python ; pas d'environnement protégé pour la publication.

### Option C — Passer à GitHub Pro

- Avantages : protection et environnements retrouvés sans rien exposer.
- Inconvénients : payant ; minutes macOS toujours comptées dix fois (3 000 par mois).

## Décision

Le dépôt est **public**. L'assistant l'a rendu public par l'API GitHub le 2026-10-26, sur confirmation explicite de TheDarkMac, après rappel de ce qui devenait visible ; il a ensuite rétabli à l'identique les protections d'ADR-0001 sur `detector` et `main`, et relu la configuration par l'API.

## Raisons

- Option A retenue : elle rétablit les garanties sur lesquelles reposent ADR-0001 et ADR-0041, sans coût, pour un projet destiné à être publié sous licence libre.
- Option B écartée : sans protection, une erreur de manipulation pourrait atteindre `detector` sans PR ni CI.
- Option C écartée : coût récurrent pour des garanties que le dépôt public donne gratuitement.

## Conséquences

- Pendant la période privée, `detector` n'était pas protégé. L'historique de `detector` ne contient que le commit initial et les commits de merge des PR #1 à #5 : aucun push direct n'a eu lieu.
- L'adresse `hei.ando14@gmail.com` (ADR-0003) et le cahier des charges sont publics. Le statut du cahier reste à clarifier avec @Jean (ADR-0011) ; il faut aussi l'informer que son document est visible.
- Si le dépôt redevient privé, les protections disparaissent sans avertissement : le relire par l'API (journal de T10) avant de s'y fier.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
