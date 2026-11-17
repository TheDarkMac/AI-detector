# ADR-0221 — Éléments actifs d'un PDF cherchés depuis le catalogue de la dernière version ; document chiffré lu par sa structure

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (parcours, bornes, document chiffré et parcours des pages partagé précisés par l'assistant)
- **Tâche** : T52
- **Exigences liées** : F-62, NF-01, ES-03, ES-06 ; menace M-07 ; ADR-0124, ADR-0126, ADR-0210, ADR-0213

## Contexte

Un lecteur de PDF n'exécute que ce que désigne le document qu'il affiche : la dernière version, depuis son catalogue (ISO 32000-2, §7.7.2). Des outils d'analyse comme pdfid comptent pourtant les mots `/JS`, `/JavaScript`, `/OpenAction` dans tout le fichier, versions antérieures et objets que rien ne désigne compris. Le module devait dire où il cherche.

## Options envisagées

### Option A — Depuis le catalogue de la dernière version (recommandée)

Ce qu'un lecteur exécuterait : catalogue (`/OpenAction`, `/AA`, arbres de noms `/JavaScript` et `/EmbeddedFiles`, `/AF`, `/AcroForm` et son `/XFA`, arbre des champs, signets), pages, annotations, et les chaînes `/Next`.

- Avantages : chaque élément compté est un élément qu'un lecteur conforme peut exécuter ou ouvrir ; le parcours suit la structure, non des mots.
- Inconvénients : un script retiré par une mise à jour, ou posé dans un objet que rien ne désigne, n'est pas compté.

### Option B — Tous les objets de toutes les versions

- Avantages : trouve aussi un script retiré ou non relié.
- Inconvénients : plus coûteux (chaque objet de chaque version est lu) ; compte des objets qu'aucun lecteur n'exécutera ; un même script repris de version en version compterait plusieurs fois.

### Option C — Les deux, séparés

- Avantages : le plus complet.
- Inconvénients : deux parcours et deux séries d'observations à expliquer ; le compte des objets non reliés n'a pas de règle qui le lise.

## Décision

Option A. Précisions de l'assistant :

- Parcours sans récursion, chaque arbre avec ses nœuds déjà vus écartés ; au plus 4 096 pages, 65 536 actions, 65 536 nœuds et entrées par arbre (`actifspdf.recherche_coupee` le dit) ; chaque nœud, action et fichier compte un objet du budget (ES-03).
- Arrêt avant le budget, comme `pagespdf` (ADR-0213) : la recherche s'arrête quand il ne reste que 262 144 objets du budget, pour que les observations déjà faites soient envoyées (`actifspdf.arret_avant_budget`) ; un fichier gonflé d'annotations ne fait pas perdre les scripts déjà trouvés.
- Une partie illisible (une action, un arbre, une page) n'arrête pas les autres ; le module est non mené (`format_partiel`) pour la première, et `actifspdf.pages_lues` compte les pages parcourues en entier.
- Document chiffré : seules les chaînes et les flux sont chiffrés, pas les dictionnaires ni les noms (§7.6.2) ; le document est parcouru par sa structure et `actifspdf.chiffre` le dit. Rien n'est déchiffré (ADR-0126, ADR-0210) : un objet rangé dans un flux d'objets ne se lit pas, et la partie qui le demande est non menée. Chiffrer un document cache le code de ses scripts à un outil qui lit les chaînes, pas le type de ses actions, qui se lit ici.
- Le parcours de l'arbre des pages, écrit pour `pagespdf` en T51, passe dans le lecteur PDF (`pages`), où les deux modules le partagent ; `pagespdf` ne change pas de ce qu'il lit ni observe, sa version reste 0.1.0 (ADR-0068 : rien de l'interface ni des résultats ne change).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle compte des objets qu'aucun lecteur n'exécutera ; ce qu'une mise à jour a changé se lit déjà, objet par objet, dans le tableau de `revisionspdf` (ADR-0217).
- Option C écartée : un second compte sans règle, plus de code pour une information que la chronologie donne déjà.

## Conséquences

- Les règles disent, dans leurs limites, que seule la dernière version est parcourue.
- Une annotation ajoutée par une mise à jour est rangée « annotation » par `revisionspdf` (ADR-0208), parmi les ajouts permis ; ses actions sont signalées ici.
- Le lecteur PDF porte un parcours de plus, couvert par les tests des deux modules.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T52 |
| 2026-11-17 | Renvoi : parcours de l'arbre des pages partagé aussi avec `imagespdf` (ADR-0225, T53) |
