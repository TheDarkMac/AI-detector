# ADR-0230 — Éléments actifs d'un DOCX ou d'un ODT décrits par leur nature et leur déclencheur, sans adresse, nom ni code

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (listes fermées des natures et des déclencheurs précisées par l'assistant)
- **Tâche** : T52 (complément bureautique)
- **Exigences liées** : F-62, ES-06, ES-13 ; menaces M-07, M-14 ; ADR-0138, ADR-0220

## Contexte

Une relation d'un DOCX a une cible (une adresse, un chemin) ; une macro a un nom, un module, une bibliothèque, choisis par l'auteur, et un code ; un projet VBA est un fichier composé OLE dont la lecture donnerait les noms des modules. Pour le PDF, ADR-0220 a retenu la nature et le déclencheur de chaque action, sans adresse, nom ni code. Restait à dire ce que le rapport montre des éléments bureautiques.

## Options envisagées

### Option A — Nature et déclencheur (recommandée)

Comme ADR-0220 : nature en liste fermée, déclencheur, comptes ; projet VBA non ouvert.

- Avantages : aucune donnée identifiante de plus (ES-13) ; rien de ce qu'a écrit l'auteur du fichier ne passe au rapport ; aucun lecteur du format OLE à écrire.
- Inconvénients : un modèle d'entreprise sur un partage réseau et une balise de pistage ne se distinguent pas ; on ne sait pas si une macro VBA se lance seule.

### Option B — Plus les noms des modules de macros

- Avantages : `ThisDocument`, `AutoOpen` diraient quelque chose de ce que fait le projet.
- Inconvénients : noms choisis par l'auteur, texte libre à marquer (ES-13) ; demande de lire le projet VBA (fichier composé OLE, flux `dir` compressé, [MS-OVBA]).

### Option C — Plus l'hôte des adresses

- Avantages : une balise de pistage se repère à son hôte, comme `c2pa.distant.hote`.
- Inconvénients : une donnée identifiante de plus, masquée par défaut ; un hôte choisi par l'auteur du fichier passe au rapport.

## Décision

Option A. Précisions de l'assistant :

- Natures, en liste fermée et dans cet ordre, par famille : `macros` (`VBA`, `ruban`, `Basic`, `Python`, `JavaScript`, `BeanShell`, `Java`, `autre`) ; `evenements` (`macro`) ; `objets` (`OLE`, `ActiveX`, `paquet`, `document`, `applet`, `plugin`) ; `externes` (`modèle`, `image`, `cadre`, `objet`, `section`, `source de données`, `rechargement`, `DDE`, `sous-document`, `lien`, `autre`). Une relation ou un élément d'un type inconnu est `autre` : aucun nom choisi par l'auteur n'en sort.
- Déclencheurs, dans cet ordre : `ouverture` (événement d'ouverture du document ; ressource chargée pour l'afficher : modèle, image, cadre, objet, section, source de données, rechargement, DDE mise à jour automatiquement) ; `document` (autre événement du document : enregistrement, impression, fermeture…) ; `utilisateur` (clic sur un lien ou un bouton, événement d'un contrôle). Les deux premiers sont automatiques. Une macro, un objet, une référence d'un type inconnu n'ont pas de déclencheur observé.
- Une adresse, un chemin, un nom ne sont lus que le temps de classer la référence (son schéma, sa forme) ou de trouver la partie dans l'archive ; ils ne sont jamais retenus.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un lecteur OLE à écrire et un texte libre de plus, pour une information que les limites de la règle sur les macros disent.
- Option C écartée : un hôte de plus au rapport ; la règle sur les éléments automatiques dit déjà qu'une ressource est chargée sans geste de l'utilisateur.

## Conséquences

- Le module n'a aucune observation identifiante ; il rejoint les modules sans métadonnées du résumé (ADR-0158).
- Un test vérifie qu'aucune adresse, aucun chemin, aucun nom de macro d'un document piégé ne figure dans les messages du module ni dans le rapport, et qu'aucune connexion n'est tentée.
- Les macros VBA qui se lancent seules (`AutoOpen`, `Document_Open`) ne sont pas reconnues : la limite de R-ACTIFSBUREAU-002 le dit. Les reconnaître demanderait un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début du complément bureautique de T52 |
