# ADR-0264 — Conservation des données au terminal : un bloc à la fin de chaque analyse ou comparaison, et `vk --conservation`

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T92
- **Exigences liées** : NF-04, NF-05, ES-12, ES-15 ; ADR-0010, ADR-0030, ADR-0092, ADR-0260, ADR-0262

## Contexte

NF-05 : « La durée et le lieu de conservation des fichiers et des rapports sont affichés à l'utilisateur ». ADR-0010 en a fixé le fond pour un outil local : l'outil ne conserve aucun fichier et n'écrit que les rapports demandés, à l'emplacement choisi par l'utilisateur ; « c'est ce qu'il affiche au titre de NF-05 ». Il ne disait pas où ni quand. Depuis T91, une commande peut aussi écrire des jetons d'horodatage et un journal, et envoyer une empreinte à une autorité (RS-03). Rien, jusqu'ici, n'affichait la conservation : seule la ligne « rapport : 1.html et 1.json » donnait un lieu, sans durée.

## Options envisagées

### Option A — Un bloc à la fin de chaque commande, et `vk --conservation` (recommandée)

Un bloc court, après l'avertissement, dit pour chaque donnée lue ou écrite par la commande où elle est et jusqu'à quand ; l'option `--conservation`, seule, affiche l'énoncé complet.

- Avantages : l'utilisateur voit la conservation de ce qu'il vient de faire, avec les chemins qu'il a choisis, sans la chercher ; l'énoncé complet reste disponible sans alourdir chaque commande.
- Inconvénients : quatre lignes de plus à chaque analyse.

### Option B — `vk --conservation` seule

- Avantages : aucune ligne ajoutée aux commandes.
- Inconvénients : la conservation n'est « affichée » qu'à qui la cherche ; un utilisateur qui ignore l'option ne la voit jamais.

### Option C — Bloc à chaque commande, sans option

- Avantages : une seule forme.
- Inconvénients : le bloc ne peut pas tout dire (texte collé, jetons, journal, autorité, ce qui échappe à l'outil) sans devenir long ; le reste n'est que dans la documentation (T103), hors de l'outil.

## Décision

Option A.

- **Bloc** : sur la sortie standard, à la fin d'une analyse (fichiers ou `--texte`) et d'une comparaison (`--comparer`), en dernier, après l'avertissement et le rappel de la vérification des jetons ; il s'affiche aussi quand tous les fichiers sont refusés, et quand une entrée du journal non écrite arrête la commande (ADR-0260), qui a pu laisser des rapports et un journal. Une ligne par donnée :
  - le fichier analysé (ou les fichiers), le texte collé, ou les rapports comparés : lus là où ils se trouvent, ni copiés ni modifiés, rien n'en est gardé ;
  - les rapports : le dossier, s'il en a été écrit au moins un, « gardés jusqu'à ce que vous les supprimiez », jetons d'horodatage compris s'il en a été écrit ; sinon « aucun écrit » ; absente pour une comparaison, qui n'en écrit pas ;
  - le journal de conservation, s'il est tenu : son chemin, gardé jusqu'à sa suppression ;
  - l'autorité d'horodatage, dès qu'une demande lui est partie, aboutie ou non : elle garde l'empreinte selon sa propre politique, que l'outil ne connaît pas.
- Les chemins sont ceux de la commande, tels que l'utilisateur les a écrits, neutralisés comme tout le terminal (ES-12). Aucun nom de fichier analysé n'y figure : le résumé les masque déjà (ES-13).
- **`vk --conservation`**, seule (code 2 avec toute autre option ou un fichier) : l'énoncé complet, un paragraphe par donnée (fichier analysé, texte collé, rapports, jetons, journal, réseau) et ce qui échappe à l'outil (ADR-0266). Il ne dépend pas de la commande : il dit ce que fait l'outil, non ce qu'a fait une commande.
- Ni `--modules`, ni `--regles`, ni `--verifier-journal` n'affichent de bloc : ils ne lisent ni fichier soumis ni rapport, et n'écrivent rien. Une commande invalide (code 2 avant toute analyse, rapport illisible pour `--comparer`) non plus.
- Les textes sont dans `textes.toml`, table `[conservation.donnees]` (ADR-0098).

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : NF-05 demande que la conservation soit affichée, non qu'elle puisse l'être ; un affichage qu'il faut connaître pour le voir ne la remplit pas.
- Option C écartée : un bloc qui dirait tout serait trop long pour chaque commande, et ce qu'il tairait ne serait plus affiché par l'outil.

## Conséquences

- `tests/test_conservation_donnees.py` vérifie le bloc pour chaque cas (sans rapport, rapports et journal, rapports jamais écrits, horodatage obtenu ou non, texte collé, comparaison, arrêt par le journal, chemin neutralisé) et l'énoncé.
- Les tests qui comparent toute la sortie d'une analyse voient quatre lignes de plus.
- La documentation utilisateur (T103) reprend l'énoncé.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
