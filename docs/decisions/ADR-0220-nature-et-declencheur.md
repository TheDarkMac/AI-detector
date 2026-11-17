# ADR-0220 — Éléments actifs d'un PDF décrits par leur nature et leur déclencheur, sans adresse, nom ni code

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (liste des déclencheurs et nature `autre` précisées par l'assistant)
- **Tâche** : T52
- **Exigences liées** : F-62, ES-06, ES-13 ; menaces M-07, M-14 ; ADR-0033, ADR-0138, ADR-0166

## Contexte

Une action PDF (ISO 32000-2, §12.6) a un type (`/S` : `JavaScript`, `Launch`, `URI`, `SubmitForm`…) et des données : le code d'un script (`/JS`), une adresse (`/URI`, `/F` d'un envoi), un fichier ou un programme (`/F`, `/Win` d'un lancement), un nom de fichier incorporé. Elle est déclenchée par la clé qui la désigne : `/OpenAction` du catalogue, les entrées d'un dictionnaire `/AA` (document, page, annotation, champ), l'action `/A` d'une annotation ou d'un signet. Rien n'est jamais exécuté ni résolu (ES-06) ; restait à dire ce que le rapport en montre. Une adresse ou un nom de fichier est une donnée identifiante à marquer (ES-13) ; ADR-0138 n'a rien montré des relations d'un document bureautique, et le module `c2pa` montre l'hôte d'un manifeste distant (ADR-0166).

## Options envisagées

### Option A — Nature et déclencheur (recommandée)

Pour chaque action : sa nature, son déclencheur, la page où elle se trouve. Ni adresse, ni nom de fichier, ni code de script.

- Avantages : aucune donnée identifiante de plus (ES-13) : rien à marquer ni à masquer ; aucune chaîne du document n'est lue, donc rien de ce que l'auteur du fichier a écrit ne passe au rapport ; le lecteur sait quoi chercher et où.
- Inconvénients : un lien vers un site connu et une balise de pistage ne se distinguent pas.

### Option B — Plus l'hôte des adresses

L'hôte des actions `URI`, `SubmitForm` et `GoToR`, pas l'adresse entière, comme `c2pa.distant.hote`.

- Avantages : une balise de pistage se repère à son hôte.
- Inconvénients : une donnée identifiante de plus, à marquer et à masquer par défaut ; un hôte choisi par l'auteur du fichier passe au rapport.

### Option C — Plus les adresses et les noms

Adresses entières et noms des fichiers incorporés ou lancés, marqués identifiants et masqués par défaut.

- Avantages : le plus informatif.
- Inconvénients : le plus de données identifiantes ; une adresse propre à l'exemplaire (M-14) reste dans le rapport, que l'utilisateur peut transmettre.

## Décision

Option A. Précisions de l'assistant :

- Déclencheurs, en liste fermée et dans cet ordre : `ouverture` (`/OpenAction`, scripts de l'arbre de noms `/JavaScript`, exécutés à l'ouverture) ; `document` (`/AA` du catalogue : `WC`, `WS`, `DS`, `WP`, `DP`) ; `page` (`/AA` d'une page : `O`, `C` ; d'une annotation : `PO`, `PC`, `PV`, `PI`) ; `champ` (`/AA` d'un champ : `C` calcul, `F` mise en forme) ; `utilisateur` (`/A` d'une annotation ou d'un signet ; `/AA` : `E`, `X`, `D`, `U`, `Fo`, `Bl`, `K`, `V`). Les quatre premiers sont automatiques : un lecteur les déclenche sans geste de l'utilisateur. Une action de la chaîne `/Next` a le déclencheur de la première. Une clé `/AA` que la norme ne définit pas n'est pas lue : aucun lecteur conforme ne l'exécute.
- Nature : le type `/S`, s'il est l'un des vingt types de la norme (tableau 201, `RichMediaExecute` compris) ; tout autre type est observé `autre`, pour qu'aucun nom choisi par l'auteur du fichier ne passe au rapport. Une action sans type n'en est pas une (§12.6.2).
- Une action atteinte par plusieurs chemins (un même script à l'ouverture et sur un bouton) n'est comptée qu'une fois, avec tous ses déclencheurs et toutes ses pages.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un hôte de plus au rapport, à marquer, pour une distinction que la règle sur les actions automatiques fait déjà en partie (une adresse ouverte sans geste de l'utilisateur).
- Option C écartée : le plus de données identifiantes, dont une adresse qui peut être propre à l'exemplaire.

## Conséquences

- Le module n'a aucune observation identifiante ; il rejoint les modules sans métadonnées du résumé (ADR-0158) : son analyse non menée ne rend pas le contrôle avant publication incomplet.
- Un test vérifie qu'aucune adresse, aucun nom de fichier ni aucun code de script d'un document piégé ne figure dans les messages du module, et qu'aucune connexion n'est tentée.
- Montrer l'hôte d'une adresse demanderait un nouvel ADR et une catégorie identifiante.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T52 |
