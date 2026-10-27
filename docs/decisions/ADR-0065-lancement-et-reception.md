# ADR-0065 — Lancement du processus de travail et réception de ses messages

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T12, validée pendant la revue de la PR de T12
- **Tâche** : T12
- **Exigences liées** : NF-03, NF-08 ; ES-01, ES-04, ES-15, ES-17 ; M-10 ; ADR-0035, ADR-0036, ADR-0056, ADR-0060, ADR-0062

## Contexte

ADR-0036 fixe le déroulé : un interpréteur neuf par fichier, le fichier transmis par descripteur, l'isolation annoncée avant toute lecture, la configuration envoyée ensuite, des résultats en lignes JSON bornées et validées. T12 le réalise. Il faut trancher la façon de lire la sortie sans risque de blocage sur les trois systèmes, ce que le processus principal vérifie à chaque message, et ce qu'il garde quand l'échange s'arrête. Trois points d'ADR-0036 sont précisés ou remplacés en chemin ; ils sont signalés ci-dessous.

## Options envisagées

### Option A — Un fil de lecture, une file d'attente, une échéance unique

Un fil lit la sortie ligne par ligne, chacune bornée, et la dépose dans une file ; le fil principal consomme la file avec une échéance globale.

- Avantages : identique sur les trois systèmes ; mémoire bornée ; le délai s'applique même si le processus de travail se tait sans s'arrêter.
- Inconvénients : un fil de plus à arrêter proprement.

### Option B — `selectors` sur les tubes

- Avantages : aucun fil.
- Inconvénients : sous Windows, `selectors` ne prend pas les tubes en charge.

### Option C — `communicate()`

- Avantages : le plus simple.
- Inconvénients : lit toute la sortie en mémoire avant de rendre la main ; aucun traitement message par message, donc ni ordre vérifié au fil de l'eau, ni arrêt dès le premier écart.

## Décision

Option A, avec les règles suivantes.

### Lancement

- Commande : `python -I -B -m voight_kampff._travail --descripteur <n>`. **`-B` est ajouté à ADR-0036** : sans lui, Python écrirait des fichiers `.pyc` dans l'installation au premier import, ce que le processus de travail ne doit pas faire (ES-15).
- Environnement vidé ; sous Windows, seul `SYSTEMROOT` est gardé : sans lui, des fonctions de Windows employées par Python au démarrage peuvent échouer. La CI Windows de T12 a validé ce lancement, avec la transmission du handle et la lecture sans `pread` ; un lancement sans `SYSTEMROOT` n'a pas été essayé.
- Fichier : sous Linux et macOS, le descripteur est le seul hérité en plus des flux standard (`pass_fds`). Sous Windows, le handle est rendu héritable le temps du lancement, et l'héritage est limité à ce handle et aux flux standard (`handle_list`) ; le processus de travail le convertit en descripteur. Windows n'a pas de lecture à position explicite : le processus de travail y déplace la position puis lit, ce qui est sans risque, puisque le principal ne lit plus le descripteur pendant l'analyse.
- **Sortie d'erreur : envoyée vers le néant, pas lue.** ADR-0036 prévoyait de la lire, bornée, sans jamais la recopier. Elle ne sert à rien d'autre : ne pas la lire supprime un fil et un tampon, et rien de ce qu'elle contient n'atteint la mémoire du processus principal (ES-15).
- Dans le processus de travail, la sortie standard est réservée au protocole : un module qui affiche du texte écrit sur la sortie d'erreur et ne peut pas glisser une ligne dans l'échange.
- **Job Object sous Windows : reporté à T14**, avec les autres mécanismes d'ADR-0035. ADR-0036 le plaçait au lancement ; il n'a de sens qu'avec les limites qu'il porte. Sous Windows, l'interpréteur d'un environnement virtuel est un lanceur qui démarre le véritable interpréteur : T14 vérifie que le Job Object couvre les deux.

### Configuration

Envoyée sur l'entrée standard par un fil dédié, seulement après réception du message d'isolation : `{"version_schema": "0.1.0", "modules": [{"identifiant", "formats", "directions"}]}`, modules actifs dans l'ordre d'exécution. Elle vient d'un processus de confiance : le processus de travail en vérifie la forme sans `jsonschema`, et s'arrête si elle est mal formée. Le catalogue (T15) et les limites (T14) s'y ajouteront.

### Réception

Chaque ligne passe, dans l'ordre : taille, JSON strict (refus de l'UTF-8 invalide, de `NaN`, des infinis, des nombres qui débordent, des clés en double), schéma des messages, construction par le modèle, place dans le protocole (ADR-0062). Le processus principal vérifie en plus :

- les résultats appartiennent au module en cours, dans l'ordre de la configuration ;
- un identifiant d'observation commence par `<module>/` et n'a pas déjà été reçu ;
- un constat ne cite que des observations de son module et porte une direction permise par le manifeste ;
- une analyse non menée sans module ne porte que `format_partiel`, `fichier_tronque` ou `limite_depassee` ; avec un module, en plus de celles-ci, `reference_manquante`, `reseau_desactive` ou `erreur_module` ;
- `erreur_module` et `limite_depassee` d'un module arrivent seules, et rien ne suit pour ce module (ADR-0060) ;
- un module non applicable n'a aucun résultat ; les versions arrivent une fois, sans doublon ; `fin` vient en dernier ; ensuite, le flux se ferme et le code de sortie est nul.

| Écart | Raison de l'analyse non menée |
| --- | --- |
| Ligne de plus de 1 Mio, ou sortie de plus de 64 Mio | `limite_depassee` |
| Ligne coupée, JSON non strict, schéma, modèle ou ordre non respectés | `message_invalide` |
| Échéance dépassée, y compris après `fin` sans que le processus se termine | `delai_depasse` |
| Flux fermé avant `fin`, ou code de sortie non nul | `arret_processus` |

### Après un écart

Le processus de travail est arrêté de force. Les modules terminés **gardent leurs résultats** ; le module en cours et les suivants deviennent non menés avec la raison de l'écart ; une analyse non menée sans module porte la même raison : le rapport est interrompu (ADR-0056). L'empreinte recalculée n'est pas retenue. Si l'isolation n'a pas été annoncée, elle est notée réduite, toutes restrictions manquantes.

### Valeurs provisoires, fixées par T14

Ligne : 1 Mio ; sortie totale : 64 Mio ; configuration : 16 Mio ; lecture du fichier par un module : 16 Mio ; échéance : 60 s pour toute l'analyse ; attente de la fin du processus : 5 s.

## Raisons

- Option A retenue, proposée par l'assistant et validée par TheDarkMac : seule des trois à borner la mémoire, appliquer un délai et refuser au premier écart sur les trois systèmes.
- Option B écartée : indisponible sous Windows.
- Option C écartée : mémoire non bornée, aucun contrôle au fil de l'eau.
- Résultats des modules terminés gardés : un processus de travail compromis peut de toute façon forger des résultats valides puis se terminer normalement (RR-01) ; les écarter n'ajouterait aucune protection, et ferait perdre, pour une simple lenteur, des résultats corrects. Le rapport dit qu'il est interrompu.
- Isolation inconnue notée « réduite, tout manque » : ne rien affirmer qu'on n'a pas reçu.

## Conséquences

- T12 n'applique encore aucune restriction : le processus de travail annonce une isolation réduite où tout manque, et le rapport le dira jusqu'à T14.
- Aucun format n'est identifié avant T13 : tout module actif est « non applicable ». T13 ajoute l'identification, transmet le format réel au principal et compare les empreintes (ES-08) ; l'empreinte reçue est déjà disponible dans le résultat.
- L'interface publique de la bibliothèque (ES-17) arrive avec la commande d'analyse : elle s'appuiera sur `executer`, seul chemin vers une analyse.
- ADR-0036 reste accepté ; ses points 2 (commande, Job Object) et 6 (sortie d'erreur) sont précisés ou remplacés ici, ce que son historique signale.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR de T12 : statut « Accepté » |
| 2026-10-27 | Précisé par ADR-0071 (T13) : message `identification` en deuxième, parties contrôlées contre la taille hachée par le principal |
