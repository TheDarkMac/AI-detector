# ADR-0045 — Nom du projet : Voight-Kampff

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac ; noms de paquet et d'import proposés par l'assistant
- **Tâche** : T10
- **Exigences liées** : §10 du cahier (nom du projet) ; NF-14 ; menace M-32 ; ADR-0008, ADR-0041

## Contexte

Le nom de travail du dépôt, « AI-detector », promet une détection que l'outil ne fait pas seul (ADR-0008, NF-14). Le registre des arbitrages laissait le nom non tranché, mais T04 l'a rendu nécessaire avant T10 : le paquet Python a besoin d'un nom d'import, et la publication sur PyPI d'un nom à réserver contre le typosquattage (ADR-0041, M-32).

TheDarkMac a proposé deux références de cinéma : le test de **Voight-Kampff** (*Blade Runner*), qui sert à démasquer un être artificiel se faisant passer pour un humain, et le **T-1000** (*Terminator 2*). Disponibilité des noms vérifiée sur PyPI le 2026-10-26 :

| Nom | État sur PyPI |
| --- | --- |
| `voight` | Pris (version 0.1.0, janvier 2026) : cadre de test pour agents d'IA, domaine voisin |
| `voight-kampff` | Pris (version 1.0.0, novembre 2023) : lanceur de linters Python |
| `voightkampff` | Libre en apparence, mais PyPI refuse un nom qui ne diffère d'un nom existant que par ses séparateurs ; refus probable, non testé |
| `voight-kampff-forensics` | Libre |

## Options envisagées

### Option A — T-1000

- Avantages : référence connue du grand public.
- Inconvénients : le T-1000 est la machine qui s'infiltre, pas celle qui la démasque : le nom désigne ce que l'outil cherche, pas ce qu'il fait ; le tiret et les chiffres ne forment pas un nom d'import Python (`t1000`, `t_1000` : graphies divergentes).

### Option B — VOIGHT

- Avantages : court, prononçable en français et en anglais ; même référence que l'option C.
- Inconvénients : `voight` est pris sur PyPI par un outil du domaine de l'IA, d'où un risque de confusion ; un import `voight` entrerait probablement en conflit avec ce paquet.

### Option C — Voight-Kampff, avec un nom de paquet distinct

- Avantages : le nom complet du test, sans ambiguïté sur la référence ; ni « IA » ni « détecteur » dans le nom (NF-14) ; le test du film est faillible, et l'outil ne promet pas de certitude.
- Inconvénients : `voight-kampff` est pris sur PyPI, le paquet publié doit donc porter un autre nom ; commande longue à taper.

### Option D — Récupérer `voight-kampff` sur PyPI

- Avantages : même nom partout.
- Inconvénients : la procédure de transfert d'un nom abandonné (PEP 541) est longue et son issue incertaine ; le paquet existant ne remplit pas clairement les critères d'abandon.

## Décision

| Élément | Nom |
| --- | --- |
| Projet | **Voight-Kampff** |
| Paquet publié sur PyPI | **`voight-kampff-forensics`** |
| Nom d'import | **`voight_kampff`** |
| Commandes | **`voight-kampff`**, et l'alias court **`vk`** |

## Raisons

- Option C retenue par TheDarkMac : la référence décrit la fonction de l'outil (démasquer l'artificiel) sans la promettre.
- « forensics » dans le nom publié : il dit le domaine (analyse de provenance et d'intégrité, ADR-0008) et distingue le paquet du lanceur de linters ; libre sur PyPI.
- Alias `vk` : la commande complète est longue pour un usage courant.
- Option A écartée : elle nomme l'adversaire, et ne donne pas de nom d'import propre.
- Option B écartée par TheDarkMac au profit du nom complet ; elle aurait aussi exigé un nom publié distinct.
- Option D écartée : délai et issue incertains, pour un gain de commodité.

## Conséquences

- Le nom de travail « AI-detector » disparaît du code ; le dépôt GitHub garde son nom tant qu'un renommage n'est pas décidé (GitHub redirige l'ancienne adresse, mais les liens de la documentation seraient à revoir).
- **Risque accepté** : le paquet `voight-kampff` de 2023 utilise probablement le même nom d'import, `voight_kampff` (non vérifié). Les deux paquets ne peuvent pas coexister dans un même environnement ; l'installation par `pipx` ou `uv tool` (ADR-0041), qui isole chaque outil, l'évite.
- **Réservation sur PyPI** : un éditeur de confiance « en attente » ne réserve pas le nom ; seule une première publication le fait. Elle demande le compte PyPI de TheDarkMac et le fichier `LICENSE` (ADR-0011), en attente de l'accord de @Jean.
- L'architecture remplace `<paquet>` par `voight_kampff` ; le registre des arbitrages passe le point à « Tranché ».

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
