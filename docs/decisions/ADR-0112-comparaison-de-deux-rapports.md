# ADR-0112 — Comparaison de deux rapports : natures des écarts, garantie, sortie et codes

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T18, à valider pendant la revue de la PR de T18
- **Tâche** : T18
- **Exigences liées** : NF-06, P-05 ; ES-12, ES-13, ES-14, ES-15 ; ADR-0023, ADR-0095, ADR-0096, ADR-0108, ADR-0109, ADR-0111

## Contexte

ADR-0108 fixe ce qui est comparé, ADR-0109 que la comparaison sert aussi à l'utilisateur. Il restait à dire comment un écart est classé, quand la garantie s'applique, ce que la commande affiche et rend, et comment elle traite les données masquées.

## Options envisagées

### Option A — Trois natures d'écart, garantie calculée

Chaque écart est un chemin dans le document (`constats[0].phrase.parametres.taille`) et une nature : **condition** (empreinte, extension, versions, analyse interrompue), **environnement** (isolation), **résultat** (tout le reste).

- Avantages : l'utilisateur sait si une différence est un défaut de l'outil ou s'explique ; la CI peut exiger « aucun écart de résultat » en laissant varier l'interpréteur et l'isolation.
- Inconvénients : la liste des conditions est à tenir à jour quand une donnée externe entre au rapport (T30).

### Option B — Égal ou différent

- Avantages : simple.
- Inconvénients : un écart de version et un défaut se confondent.

### Option C — Afficher les valeurs qui diffèrent

- Avantages : lisible.
- Inconvénients : les valeurs peuvent être identifiantes (GPS, nom d'auteur) ou venir d'un fichier hostile.

## Décision

Option A.

- **Garantie** : même fichier établi (empreintes comparées), aucune condition différente, aucune analyse interrompue. **Défaut** : résultats différents dans la garantie.
- **Masquage** : les données d'une catégorie masquée dans l'un des deux exports ne sont comparées dans aucun ; une empreinte masquée laisse le même fichier non établi, donc hors garantie, et la commande dit d'écrire les rapports avec `--reveler empreinte`. Le nom n'est jamais comparé.
- **Types** : `1`, `1.0` et `true` sont différents, comme en JSON ; une énumération du modèle vaut la chaîne qu'elle devient.
- **Lecture** (`comparaison.lire`) : au plus 256 Mio (quatre fois `TAILLE_MAX_SORTIE`), JSON strict (`_protocole.decoder` : ni clé en double, ni NaN), puis `export.valider` ; l'erreur ne cite jamais le contenu.
- **Sortie** (`vk --comparer A B`, seule) : résultats identiques ou nombre d'écarts de résultat ; garantie réunie ou ses raisons ; défaut s'il y a lieu ; isolation différente ; catégories non comparées ; puis au plus 50 écarts, par leur chemin et leur nature, jamais leur valeur. Chaque ligne est neutralisée (ADR-0096).
- **Codes** : 0 si aucun écart de résultat, 1 sinon, 2 pour un rapport illisible ou une commande invalide.

## Raisons

- Option A retenue : elle répond à la question que pose l'utilisateur, « est-ce un défaut ? », et sert la CI entre versions de Python.
- Option B écartée : elle ne distingue pas un défaut d'une mise à jour du catalogue.
- Option C écartée : ES-13 et ES-14 ; le chemin suffit pour lire les deux fichiers.
- Code 0 hors garantie quand les résultats sont identiques : le code dit les résultats ; la garantie est dite par le texte.
- Extension comme condition : le nom n'est pas comparé, mais l'extension est une entrée de l'analyse (F-03) ; deux noms à des extensions différentes changent légitimement la concordance.

## Conséquences

- T30 ajoute la liste de confiance et les données externes aux conditions.
- La documentation utilisateur (T103) reprend les natures et les codes.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
