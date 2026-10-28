# ADR-0092 — Écriture des rapports par la commande : `--rapport DOSSIER`, nommés par le rang

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T16
- **Exigences liées** : F-83, NF-18 ; ES-13, ES-14, ES-15 ; ADR-0015, ADR-0025, ADR-0059, ADR-0073, ADR-0075

## Contexte

T16 produit deux exports par fichier, HTML et JSON (ADR-0025) ; un rapport porte sur un seul fichier, et une commande peut en analyser plusieurs (ADR-0015, ADR-0059). Il faut dire comment la commande les écrit. Le nom d'un fichier analysé est une donnée identifiante (ADR-0014) ; l'outil n'écrit rien sur le disque sans qu'on le lui demande (ES-15).

## Options envisagées

### Option A — `--rapport DOSSIER`

`vk --rapport DOSSIER FICHIER...` écrit `<rang>.html` et `<rang>.json` pour chaque fichier, nommés par son rang dans la commande ; aucun fichier existant n'est écrasé. Sans l'option, seul le résumé s'affiche.

- Avantages : marche pour un ou plusieurs fichiers ; le nom du fichier analysé n'apparaît nulle part sur le disque ; aucune écriture par défaut.
- Inconvénients : il faut retrouver quel rang correspond à quel fichier (l'ordre de la commande).

### Option B — `--html FICHIER` et `--json FICHIER`

Un chemin de sortie par format.

- Avantages : l'utilisateur nomme lui-même chaque rapport.
- Inconvénients : seulement pour un fichier analysé à la fois.

### Option C — JSON sur la sortie standard, HTML dans un dossier

- Avantages : le JSON se chaîne à un autre programme.
- Inconvénients : le résumé et le JSON se mêlent sur la même sortie ; deux mécanismes à expliquer.

## Décision

Option A.

- Le dossier est créé s'il n'existe pas (ses parents doivent exister). Avant toute analyse, la commande vérifie qu'aucun des fichiers à écrire (`1.html`, `1.json`… jusqu'au nombre de fichiers donnés) n'existe : sinon elle s'arrête avec le code 2, sans rien analyser. Un dossier inutilisable (un fichier du même nom, un parent absent, un droit manquant) donne aussi le code 2.
- Chaque rapport est créé en mode exclusif (il échoue s'il existe déjà, même apparu entre la vérification et l'écriture), lisible et modifiable par son seul propriétaire (`0600` sous Linux et macOS). Un rapport qui ne peut pas être écrit est signalé sur la sortie d'erreur, au rang du fichier, et donne le code 1.
- Un fichier refusé n'a pas de rapport : son rang manque dans le dossier.
- Le résumé de chaque fichier se termine par les chemins des deux rapports écrits.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle ne sert pas une commande qui analyse plusieurs fichiers, cas prévu par ADR-0015.
- Option C écartée : deux sorties pour un même besoin, et un mélange du résumé et du JSON sur la sortie standard.
- Droits `0600` : un rapport peut porter une donnée révélée (ADR-0093) ; le fichier n'est lisible par d'autres comptes que si l'utilisateur le décide.
- Refus d'écraser : un rapport antérieur, peut-être démasqué, ne doit pas être remplacé sans que l'utilisateur le voie.

## Conséquences

- Codes de sortie : 2 s'ajoute pour un rapport existant ou un dossier inutilisable ; 1 pour un rapport non écrit.
- L'interface publique de la commande change (ADR-0068) ; la version de l'outil, `0.1.0.dev0`, n'a pas encore de version stable à faire évoluer.
- La CI écrit les deux rapports depuis le wheel installé et vérifie le JSON par son schéma.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
