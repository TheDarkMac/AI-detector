# ADR-0260 — Journal de conservation : activé à chaque commande par `--journal FICHIER`, annoncé à chaque emploi

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T91
- **Exigences liées** : NF-15, NF-17, ES-15, ES-16 ; ADR-0030 ; menaces M-27, M-28

## Contexte

ADR-0030 fixe la portée de NF-17 en local : aucune trace par défaut ; sur activation explicite, un journal chaîné, sans noms de fichier, dont l'activation affiche un avertissement, « qui » étant déclaratif. Il ne dit pas comment l'utilisateur l'active, ni où le journal se trouve, ni comment il le vérifie. L'outil n'a aujourd'hui aucun fichier de réglage : tout passe par la ligne de commande (ADR-0045).

## Options envisagées

### Option A — Option `--journal FICHIER` à chaque commande (recommandée)

Le journal n'est tenu que si la commande le nomme ; `--qui NOM` y inscrit un nom ; l'avertissement s'affiche sur l'erreur standard à chaque emploi ; `--verifier-journal FICHIER` vérifie la chaîne.

- Avantages : rien n'est gardé sur le poste qui dise qu'un journal existe ni où il est (ES-15) ; l'avertissement est lu à chaque fois, y compris par un collègue qui reprend la commande d'un autre ; aucun format de réglage à créer.
- Inconvénients : l'option est à répéter ; une commande qui l'oublie n'est pas journalisée, sans que rien ne le signale.

### Option B — Fichier de réglage

L'activation, le chemin et le nom sont enregistrés une fois.

- Avantages : plus commode ; aucune commande n'échappe au journal.
- Inconvénients : un fichier de réglage dit, en cas de saisie, qu'un journal existe et où (M-27) ; c'est une trace par défaut de fait, contre ES-15 ; un format et un emplacement par système à définir.

### Option C — Option, avertissement à la création seulement

- Avantages : moins de texte sur l'erreur standard.
- Inconvénients : l'avertissement n'est vu qu'une fois, par celui qui crée le journal, alors que son objet (ce que les empreintes révèlent) vaut à chaque ajout.

## Décision

Option A.

- `--journal FICHIER` : le fichier est créé s'il n'existe pas, lisible par son seul propriétaire (`0o600`), et prolongé sinon. Il s'emploie avec une analyse (fichiers ou `--texte`) ou avec `--comparer` ; seul, ou avec `--modules` ou `--regles`, il est refusé (code 2), rien n'étant à journaliser.
- À l'ouverture, le journal entier est vérifié : un journal rompu, illisible ou qui n'est pas un fichier régulier arrête la commande avant toute analyse (code 2), avec l'entrée en cause. Un journal rompu n'est jamais prolongé : y ajouter mélangerait des entrées sûres à une chaîne qui ne l'est plus.
- L'avertissement s'affiche sur l'erreur standard à chaque emploi, avant la première analyse : ce qu'il garde, ce qu'une empreinte révèle à qui détient l'original, ce qu'il ne prouve pas.
- `--qui NOM` : 1 à 128 caractères, sans espace au début ni à la fin, sans caractère de contrôle, de format ou invisible ; il s'emploie avec `--journal`. Il est inscrit à chaque entrée, déclaré, non vérifié.
- Une entrée non écrite (disque plein, journal modifié pendant la commande) arrête la commande, code 1 : continuer laisserait des analyses hors du journal que l'utilisateur a demandé.
- `--verifier-journal FICHIER`, seule : 0 si la chaîne est cohérente, avec le nombre d'entrées et leurs dates extrêmes ; 1 si elle est rompue, avec la première entrée en cause ; 2 si le fichier est illisible ou trop grand (64 Mio). La réponse rappelle que « cohérent » ne veut pas dire « authentique ».
- Deux commandes peuvent tenir le même journal : chaque ajout se fait sous un verrou exclusif du fichier (`flock` sous Linux et macOS, `msvcrt.locking` sous Windows), après relecture de la dernière ligne.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : un fichier de réglage est une trace laissée par défaut sur le poste, ce qu'ADR-0030 exclut ; la commodité ne compense pas ce que révèle sa présence lors d'une saisie.
- Option C écartée : l'avertissement porte sur chaque ajout, non sur la création ; ADR-0030 le demande « à l'activation », et chaque commande est une activation.

## Conséquences

- Aucune trace sans `--journal` : `tests/test_traces.py` (ES-15) reste valable, et `test_sans_option_ni_journal_ni_requete` vérifie que le journal n'est pas ouvert sans l'option.
- La documentation utilisateur (T103) explique ce que vaut le journal, comment le vérifier, et qu'une commande sans l'option n'y figure pas.
- Le journal est relu en entier à l'ouverture et à chaque ajout : quelques millisecondes pour quelques milliers d'entrées, une fraction de seconde à la limite de 64 Mio.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
