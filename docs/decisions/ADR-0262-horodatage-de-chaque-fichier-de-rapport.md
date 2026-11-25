# ADR-0262 — Horodatage RFC 3161 : `--horodater URL`, un jeton par fichier de rapport écrit

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T91
- **Exigences liées** : NF-16, NF-17, ES-16 ; RS-03 ; ADR-0030, ADR-0033, ADR-0092 ; menaces M-17, M-24, M-25

## Contexte

ADR-0030 prévoit l'horodatage du rapport selon la RFC 3161, sur son empreinte seulement, auprès d'une autorité choisie par l'utilisateur : c'est la requête sortante RS-03, désactivée par défaut. Un rapport s'écrit en deux fichiers, `1.html` et `1.json` (ADR-0092). Un jeton ne peut pas être inscrit dans le fichier qu'il horodate : il s'écrit à côté.

## Options envisagées

### Option A — Un jeton par fichier écrit (recommandée)

Une requête par fichier : `1.html.tsr` et `1.json.tsr`, chacun vérifiable seul par `openssl ts -verify -data 1.json -in 1.json.tsr -CAfile …`.

- Avantages : les deux fichiers sont couverts ; la vérification se fait avec un outil courant, sans l'outil ni bordereau.
- Inconvénients : deux requêtes par fichier analysé, donc deux fois l'adresse et l'heure transmises à l'autorité.

### Option B — JSON seulement

- Avantages : une requête ; le JSON fait foi pour `--comparer`.
- Inconvénients : le HTML, que l'on transmet le plus volontiers, n'est pas couvert.

### Option C — Un bordereau des deux empreintes, horodaté une fois

- Avantages : une requête.
- Inconvénients : la vérification passe par le bordereau puis par chaque fichier, ce qu'aucun outil courant ne fait seul.

## Décision

Option A.

- `--horodater URL` s'emploie avec `--rapport` (code 2 sinon) ; ni avec `--comparer`, ni avec un journal seul. L'URL est en `http` ou `https`, avec un nom d'hôte, sans identifiants ni espace, d'au plus 2 048 caractères : elle finit dans le journal, et des identifiants y seraient gardés en clair. Aucune autorité n'est proposée par défaut : le choix en revient à l'utilisateur (ADR-0030).
- Pour chaque fichier écrit, l'outil envoie une `TimeStampReq` (version 1, SHA-256 de l'empreinte du fichier, nonce aléatoire de 63 bits, certificat demandé), par `POST`, `Content-Type: application/timestamp-query`. Rien d'autre du rapport, ni du fichier analysé, ni de son nom.
- La réponse entière (`TimeStampResp`) s'écrit, après vérification de son contenu (ADR-0263), dans `<rang>.<html|json>.tsr`, créé exclusivement, lisible par son seul propriétaire ; `--rapport` refuse un dossier qui contient déjà l'un de ces jetons.
- Aucune redirection n'est suivie : elle mènerait à un hôte que l'utilisateur n'a pas choisi, et urllib changerait le `POST` en `GET`. Délai de 30 s, réponse d'au plus 1 Mio. Le mandataire des variables d'environnement s'applique, comme à toute requête de la bibliothèque standard.
- L'activation s'annonce sur l'erreur standard : l'autorité reçoit l'empreinte de chaque rapport, l'adresse de l'utilisateur et l'heure (M-17).
- Un horodatage non obtenu (autorité injoignable, refus, réponse non conforme) ou un jeton non écrit se signalent sur l'erreur standard et donnent le code 1 ; le rapport reste écrit, et le journal l'inscrit sans jeton.
- Le terminal donne, pour chaque fichier, l'heure annoncée et le chemin du jeton, puis une fois la commande `openssl ts -verify` à employer.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : le fichier le plus partagé resterait sans horodatage.
- Option C écartée : un horodatage qu'on ne vérifie pas sans l'outil perd l'intérêt d'une autorité tierce.
- Requête depuis le processus principal, jamais depuis le processus de travail, qui n'a pas de réseau (ES-17) et ne voit que le fichier analysé, pas le rapport.

## Conséquences

- RS-03 est réalisée ; l'inventaire des requêtes sortantes (NF-16) le dit.
- Le rapport lui-même ne change pas : ni le HTML ni le JSON ne mentionnent l'horodatage, qui le suit ; `--comparer` et la garantie de reproductibilité (ADR-0023) sont inchangés.
- La documentation utilisateur (T103) doit dire comment obtenir le certificat de l'autorité pour `openssl ts -verify`, et ce qu'apporte une heure certifiée : l'existence du rapport à cette heure, non la justesse de son contenu.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
