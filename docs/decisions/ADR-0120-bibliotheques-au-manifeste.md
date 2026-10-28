# ADR-0120 — Bibliothèques au manifeste, versions lues avant le verrouillage

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T20, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : NF-06, ES-04, ES-18 ; ADR-0023, ADR-0043, ADR-0064, ADR-0079, ADR-0116

## Contexte

La rubrique Versions du rapport liste les bibliothèques qui décodent ou analysent le fichier, avec leur version réelle (ADR-0023) : c'est une condition de la reproductibilité. ADR-0064 renvoyait leur déclaration « au premier module qui en emploie une », et l'architecture (§12) demandait qu'elles soient lues avant le verrouillage du processus de travail. Le module `xmp` est ce premier module : il lit le XML par expat (ADR-0116), dont la version dépend de l'interpréteur.

## Options envisagées

### Option A — Champ `bibliotheques` du manifeste, vocabulaire fermé

Le manifeste nomme les bibliothèques du module parmi une liste connue du schéma ; le processus de travail lit leurs versions avant de se verrouiller et envoie celles des modules actifs ; le processus principal vérifie qu'il reçoit exactement celles-là.

- Avantages : le processus principal sait, sans importer le code, quelles versions attendre ; un processus de travail ne peut ni en taire une ni en ajouter une.
- Inconvénients : une bibliothèque nouvelle demande de compléter le schéma et la fonction qui lit sa version.

### Option B — Chaque module expose ses versions

- Avantages : rien à déclarer ailleurs que dans le module.
- Inconvénients : le processus principal ne peut rien vérifier ; une version lue après le verrouillage pourrait demander un accès au disque (métadonnées de paquet).

### Option C — Toutes les bibliothèques du paquet, toujours

- Avantages : aucune déclaration.
- Inconvénients : la rubrique citerait des bibliothèques qui n'ont pas lu le fichier (`jsonschema` ne s'exécute que dans le processus principal).

## Décision

Option A.

- `manifeste.toml` gagne le champ obligatoire `bibliotheques` : liste, éventuellement vide, sans doublon, d'éléments du vocabulaire `["expat"]` (`schemas/manifeste.schema.json`). Le manifeste de `xmp` cite `expat` ; ceux de `exif`, `iptc` et `textepng` n'en citent aucune.
- La configuration envoyée au processus de travail porte les bibliothèques de chaque module actif.
- Le processus de travail lit la version de chaque bibliothèque connue avant les restrictions (`principal.versions_des_bibliotheques`, `expat.version_info`) et envoie, dans le message `versions`, celles des modules actifs, une fois chacune, dans l'ordre de leurs noms.
- Le processus principal refuse un message `versions` dont les noms ne sont pas exactement ceux qu'il attend : `message_invalide` (ADR-0065).

## Raisons

- Option A : vérifiable des deux côtés, et rien n'est lu après le verrouillage (ADR-0079).
- Option B écartée : déclaration invérifiable par le principal.
- Option C écartée : la rubrique doit dire ce qui a lu le fichier, pas ce qui est installé.
- Version d'un module désactivé non inscrite : il n'a rien lu.

## Conséquences

- La rubrique Versions d'un rapport cite `expat` dès que `xmp` est actif, quel que soit le format du fichier.
- T30 (`c2pa-python`) et T50 (`pypdf`) ajoutent leur nom au vocabulaire et leur lecture de version, par la même voie.
- `vk --comparer` compare déjà les dépendances (ADR-0112) : une version d'expat différente sort de la garantie.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
