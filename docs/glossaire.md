# Glossaire du projet

> Statut : **v1.2** ; v1.0 mergée avec T11, v1.1 avec T12, v1.2 avec T13, v1.3 proposée dans la PR de T14. Document vivant : toute modification est inscrite à l'historique.
> Source : glossaire du §11 du [cahier des charges](00-cahier-des-charges/cahier-des-charges-v0.1.md), complété selon A-10 de l'[analyse critique](01-analyse/analyse-critique-cdc-v0.1.md) et ADR-0021.

Ce glossaire fixe le vocabulaire de la documentation et du code. Il complète celui du cahier, qui n'est pas modifié (document source) ; quand les deux diffèrent, celui-ci s'applique au projet et l'écart est inscrit au [registre des arbitrages](02-arbitrages/registre-des-arbitrages.md). Le glossaire destiné aux utilisateurs du rapport est rédigé en T103 à partir de celui-ci.

## Termes du modèle de données

| Terme | Définition | Référence |
| --- | --- | --- |
| Observation | Donnée relevée par un module dans le fichier (valeur d'un champ, mesure), sans interprétation. Seul objet du rapport qui porte des valeurs tirées du fichier. | ADR-0058 |
| Constat | Ce qu'une règle du catalogue tire d'une ou plusieurs observations : phrase, données, règle, technique, fondement, catégorie, direction, et niveau pour un indice. | §6, ADR-0058 |
| Règle | Élément versionné du catalogue qui transforme des observations en constat. Son identifiant (par exemple `R-C2PA-001`) est distinct de celui d'une exigence (F-xx). | A-47, T15 |
| Gabarit | Phrase rédigée hors du code, identifiée, dont les paramètres sont remplacés par des observations au moment de l'export. | ADR-0020 |
| Fondement | Ce sur quoi repose un constat : vérification cryptographique, vérification déterministe, déclaration du fichier, ou mesure. | ES-20, ADR-0058 |
| Preuve | Fait établi par une vérification cryptographique ou déterministe, accompagné de l'énoncé exact de ce qu'il établit. Remplace la définition du cahier. | ADR-0021 |
| Indice | Constat compatible avec une hypothèse, sans l'établir ; il pointe toujours vers une hypothèse et porte un niveau. | §11 du cahier, ADR-0018 |
| Information neutre | Constat sans valeur probante (absence de métadonnées, champ standard) ; il ne pointe vers aucune hypothèse. | F-14, F-80 |
| Direction | Hypothèse vers laquelle pointe un constat : origine IA, retouche, transformation, authenticité, ou rien de particulier. | F-81, ADR-0055 |
| Transformation | Modification banale d'un contenu sans intention d'en changer le sens : recompression, redimensionnement, passage par une messagerie, capture d'écran. | ADR-0022, ADR-0055 |
| Niveau | Faible, modéré ou fort : propriété fixe d'une règle d'indice, attribuée d'après son taux de faux positifs mesuré. | ADR-0018 |
| Règle non évaluée | Règle dont le taux de faux positifs n'est pas encore mesuré ; son niveau est « faible ». | ADR-0018 |
| Analyse non menée | Analyse qui aurait pu s'appliquer au fichier et ne l'a pas été, avec sa raison prise dans une liste fermée. | F-82, ADR-0056 |
| Analyse interrompue | Analyse dont au moins une partie n'a pas abouti pour une raison qui dépend de la machine (délai, limite, arrêt, message invalide) ; hors garantie de reproductibilité. | ADR-0023, ADR-0056 |
| Couverture | Techniques appliquées ou non au fichier, avec leur état, et marquages recherchés : borne la portée d'un résultat négatif. | F-25, ADR-0059 |
| Technique, module | Une technique d'analyse est livrée sous la forme d'un module, sous-paquet de `modules/` avec son manifeste. Les deux mots désignent la même unité dans le modèle. | ADR-0042 |
| Localisation | Endroit du fichier où se trouve ce qui a été observé : chemin dans la structure, plage d'octets, page, zone d'image, intervalle de temps. | A-46 |
| Donnée identifiante | Donnée qui peut désigner une source : métadonnée nominative, numéro de série, coordonnées GPS, nom du fichier, empreinte. Masquée par défaut. | ES-13, ADR-0057 |
| Format réel | Format identifié par le contenu du fichier, non par son extension : celui de la partie 1. | F-02, ADR-0070 |
| Partie (d'un fichier) | Format reconnu dans le fichier et plage d'octets qu'il occupe, du début à sa fin logique. Un fichier en a une ou plusieurs ; chaque partie du périmètre est analysée. | ADR-0071 |
| Fichier polyglotte | Fichier reconnu dans plusieurs formats à la fois : un JPEG suivi d'une archive ZIP, un PDF caché dans un JPEG. | A-31, ES-07 |
| Fin logique | Position où s'achève la structure d'un format (EOI d'un JPEG, IEND d'un PNG, dernier `%%EOF` d'un PDF). Elle est établie, non établie (structure non parcourue ou de taille inconnue) ou tronquée (structure interrompue). | ES-07, ADR-0070 |
| Octets non reconnus | Plages du fichier qu'aucune partie ne couvre, dont les données après la fin logique ; déclarées non menées (`format_partiel`). | ES-07, ADR-0072 |
| Format du périmètre, hors périmètre | Les formats du §3 du cahier sont analysés ; d'autres sont reconnus pour être nommés, jamais analysés. Un fichier sans format du périmètre est refusé. | F-04, ADR-0070 |
| Concordance de l'extension | L'extension du nom est l'une de celles du format réel ; sinon, elle est discordante (F-03). | ADR-0072 |

## Termes de l'architecture

| Terme | Définition | Référence |
| --- | --- | --- |
| Processus principal (P1) | Processus qui reçoit la commande, ouvre le fichier sans l'interpréter, valide les messages et produit le rapport. | ADR-0036 |
| Processus de travail (P2) | Processus restreint, un par fichier, qui lit et analyse le fichier. | ADR-0028, ADR-0036 |
| Exécution isolée | Analyse menée dans un processus de travail auquel le système retire réseau, écriture et lancement de programmes. | NF-01, ADR-0028 |
| Isolation réduite | État d'un processus de travail auquel manque au moins une restriction ; le rapport liste lesquelles. Sous Windows, elle l'est toujours (réseau, lecture, vidages). | ADR-0035, ADR-0059, ADR-0081 |
| Limite comptée | Limite que le moteur compte (octets décompressés, objets, dimensions, imbrication, taille des résultats) : un fichier la dépasse ou non sur toutes les machines. Dépassée, elle rend le module non mené (`limite_depassee`) sans sortir l'analyse de la garantie de reproductibilité. | ADR-0076, ADR-0078 |
| Limite du système | Garde-fou posé par le système ou le processus principal : mémoire, temps. Dépassée, elle interrompt l'analyse (`memoire_depassee`, `delai_depasse`), hors garantie. | ADR-0076, ADR-0077 |
| Budget (d'un module) | Ensemble des limites comptées d'un module sur une partie, tenu par son contexte. | ADR-0078 |
| Arrêt brutal | Fin de l'outil sans rapport, par exception non traitée ou plantage ; NF-03 l'interdit : un échec donne un rapport partiel. | NF-03 |
| Manifeste (C2PA) | Structure signée, intégrée au fichier, qui déclare son origine et ses transformations. | §11 du cahier, T30 |
| Manifeste (module) | Fichier TOML qui décrit un module sans exécuter son code : identifiant, version, formats, exigences, règles, fiche technique, directions permises, modules requis. | ADR-0042, ADR-0064 |
| Contexte (d'un module) | Objet remis à un module par le moteur : lecture de la partie analysée par position, réception des observations, constats et analyses non menées. | ADR-0061, ADR-0071 |
| Module actif, désactivé | Un module actif est exécuté ; un module désactivé par l'utilisateur, ou qui en requiert un désactivé, ne l'est pas et figure au rapport comme non mené. | ADR-0063 |
| Module applicable | Module actif dont les formats comprennent le format de la partie analysée ; sinon, il est « non applicable » pour cette partie dans la couverture. | ADR-0059, ADR-0062, ADR-0071 |
| Analyse (résultat) | Ce que l'interface publique rend pour un fichier avant le rapport complet : identification, isolation, couverture, observations, constats, analyses non menées. | ADR-0073 |
| Refus | Fichier pour lequel l'outil ne livre aucun résultat, avec un motif explicite : illisible, non régulier, vide, format inconnu ou hors périmètre, fichier modifié pendant l'analyse, arrêt avant l'identification, hors limites (plus de 1 Gio). | F-04, ES-08, ADR-0075, ADR-0077 |
| Garde | Vérification qui empêche un analyseur de s'exécuter hors d'un processus de travail verrouillé. | ES-17, ADR-0061 |
| Ingrédient (C2PA) | Fichier source déclaré par un manifeste C2PA comme entrant dans la composition du contenu. | A-10, T30 |
| DigitalSourceType | Champ IPTC qui déclare la nature de la source d'un contenu, dont `trainedAlgorithmicMedia` (généré par IA). | F-11, T22 |
| Signature | Réservé au sens cryptographique : signature d'un manifeste C2PA, signature électronique d'un PDF. | A-10 |
| Empreinte d'outil | Trace laissée par un outil de génération (paramètres, nom du logiciel) ; le cahier dit « signature » (F-12). | A-10 |
| Empreinte (du fichier) | SHA-256 du fichier entier ; donnée identifiante. | ADR-0031, ADR-0040 |

## Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-10-26 | 1.0 | Création | T11 |
| 2026-10-26 | 1.1 | Manifeste (module) précisé ; contexte, module actif ou désactivé, module applicable, garde ajoutés | T12 |
| 2026-10-27 | 1.2 | Format réel, partie, fichier polyglotte, fin logique, octets non reconnus, formats du périmètre, concordance de l'extension, analyse, refus ajoutés ; contexte et module applicable précisés | T13 |
| 2026-10-27 | 1.3 | Limite comptée, limite du système, budget ajoutés ; isolation réduite et refus précisés | T14 |
