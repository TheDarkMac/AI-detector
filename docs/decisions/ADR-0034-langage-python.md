# ADR-0034 — Langage : Python 3.12 ou ultérieur

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (confirme le choix provisoire noté au journal de T00)
- **Tâche** : T04
- **Exigences liées** : NF-01, NF-09, NF-10 ; ES-18 ; ADR-0010, ADR-0011

## Contexte

Le journal de T00 notait un choix provisoire de Python, qu'ADR-0010 renvoyait à T04. Le langage pèse sur trois points : la sûreté mémoire des analyseurs, qui lisent des fichiers hostiles (M-01, ES-18) ; les bibliothèques disponibles pour C2PA, PDF et le calcul numérique ; l'usage en bibliothèque (ADR-0010), qui suppose un langage que les programmes appelants utilisent.

## Options envisagées

### Option A — Python 3.12 ou ultérieur

- Avantages : écosystème le plus riche pour l'analyse de formats et le calcul (liaison C2PA officielle, numpy) ; un analyseur écrit en Python pur est sûr pour la mémoire ; langage courant chez les vérificateurs qui scriptent ; contributions faciles.
- Inconvénients : les bibliothèques rapides sont souvent écrites en C ; démarrage d'un interpréteur plus lent ; distribution moins simple qu'un binaire unique.

### Option B — Rust

- Avantages : sûreté mémoire de bout en bout ; binaire unique.
- Inconvénients : écosystème d'analyse plus pauvre ; développement plus long ; bibliothèque peu commode à appeler depuis Python, langage le plus probable des programmes appelants.

### Option C — Python et Rust (PyO3)

- Avantages : orchestration en Python, analyseurs critiques sûrs et rapides.
- Inconvénients : deux chaînes de compilation ; paquets binaires par plateforme dès la V1.

### Option D — Go

- Avantages : binaire unique, sûr pour la mémoire.
- Inconvénients : peu de bibliothèques C2PA et PDF ; bibliothèque difficile à appeler depuis un autre langage.

## Décision

Le moteur, la ligne de commande, la bibliothèque et les analyseurs sont écrits en **Python, version 3.12 au minimum**. Le code C ou C++ des dépendances ne s'exécute que dans le processus de travail isolé (ADR-0028, ADR-0043).

## Raisons

- Option A retenue : elle donne accès aux bibliothèques nécessaires à la V1 et garde la sûreté mémoire pour tout ce que le projet écrit lui-même ; le risque des dépendances en C est confiné par l'isolation.
- Option B écartée : le coût de développement et la faiblesse de l'écosystème retarderaient la V1 sans gain décisif, l'isolation couvrant déjà les failles des analyseurs.
- Option C écartée : deux chaînes de compilation pour un petit projet ; réversible plus tard, module par module, si une mesure le justifie.
- Option D écartée : bibliothèques manquantes pour C2PA et PDF.
- Version 3.12 : `tomllib` (3.11) est dans la bibliothèque standard ; 3.12 reste maintenue jusqu'en octobre 2028.

## Conséquences

- T10 crée le squelette Python, l'outillage et la matrice de versions de la CI.
- Le coût de démarrage de l'interpréteur pèse sur le lancement d'un processus par fichier (ADR-0036) ; T14 le mesure.
- Un passage à Rust pour un analyseur précis reste possible par un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
