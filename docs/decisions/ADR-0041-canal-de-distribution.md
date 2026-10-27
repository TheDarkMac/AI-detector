# ADR-0041 — Canal de distribution : PyPI avec attestations de provenance

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : §9 livrables 1 et 2 ; ES-18 ; hypothèse H2 ; menaces M-31, M-32 ; ADR-0010, ADR-0029

## Contexte

Le modèle de menace suppose que l'utilisateur obtient l'outil par le canal officiel documenté (H2), et ES-18 demande un canal unique et les empreintes des versions publiées. ADR-0029 fait passer le catalogue et la liste de confiance par ce même canal. Il faut donc choisir le canal, et la façon de prouver qu'un paquet vient bien du projet. L'outil est écrit en Python (ADR-0034).

## Options envisagées

### Option A — PyPI, publication par Trusted Publishing avec attestations

- Avantages : canal habituel d'un outil Python ; installation et mise à jour par `pipx` ou `uv tool` ; publication sans jeton conservé, depuis la CI ; attestations de provenance signées (Sigstore) qui relient chaque paquet au dépôt et au workflow qui l'a produit.
- Inconvénients : dépend d'un index tiers ; exposé au typosquattage (M-32).

### Option B — GitHub Releases seul

- Avantages : pas d'index tiers.
- Inconvénients : installation depuis un fichier téléchargé, mises à jour à la main ; procédure moins courante, donc plus d'erreurs.

### Option C — PyPI et paquets système (Homebrew, Debian…)

- Avantages : plus accessible.
- Inconvénients : plusieurs canaux à surveiller, souvent tenus par des tiers ; contraire au canal unique d'ES-18.

## Décision

- **Canal officiel unique : PyPI.** Les paquets (sdist et wheel) sont publiés depuis GitHub Actions par **Trusted Publishing**, avec **attestations de provenance**, à partir d'une étiquette de version, dans un environnement de déploiement protégé.
- Chaque version a une release GitHub qui publie : les empreintes SHA-256 des paquets (ADR-0040), le fichier d'installation verrouillé (ADR-0037), la version et l'empreinte du catalogue et de la liste de confiance (ADR-0029).
- La documentation donne l'installation par `pipx` ou `uv tool`, et la vérification des attestations et des empreintes.
- Tout autre canal est signalé comme non officiel dans la documentation.

## Raisons

- Option A retenue : elle donne un canal unique, l'installation la plus simple pour un outil Python, et une preuve d'origine vérifiable sans clé gérée par le projet.
- Option B écartée : les mises à jour manuelles laissent des versions vulnérables en place plus longtemps.
- Option C écartée : ES-18 ; des paquets système tenus par des tiers pourront exister, mais ne seront pas le canal officiel.

## Conséquences

- **Le nom du projet doit être tranché avant la première publication** (registre des arbitrages : non tranché) ; le nom sur PyPI devra être réservé dès qu'il est choisi, contre le typosquattage.
- T10 crée le workflow de publication et l'environnement protégé ; la première publication attend le nom.
- Les actions de ce workflow sont épinglées par empreinte de commit, comme celles de la CI documentaire (ADR-0006).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : nom du projet et du paquet tranchés par ADR-0045 (`voight-kampff-forensics`) (T10) |
| 2026-10-26 | Renvoi : workflow de publication et environnement protégé « pypi » créés (T10) |
| 2026-10-27 | Renvoi : éditeur de confiance constaté sur PyPI, fichier `LICENSE` ajouté (ADR-0067) ; prérequis de la première publication réunis |
| 2026-10-27 | Renvoi : contrôles de l'étiquette et marquage des pré-versions dans le workflow (ADR-0069) ; numérotation fixée (ADR-0068) |
| 2026-10-27 | Version, date et empreinte du catalogue jointes à la release (`CATALOGUE.txt`), contrôlées contre le registre (ADR-0085, T15) |
