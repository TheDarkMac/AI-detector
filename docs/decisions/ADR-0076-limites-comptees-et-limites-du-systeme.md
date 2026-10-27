# ADR-0076 — Limites comptées et limites du système : un budget mixte

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T14
- **Exigences liées** : NF-02, NF-06, NF-08, ES-03 ; A-05 ; ADR-0023, ADR-0056

## Contexte

ADR-0023 a reformulé NF-06 : mêmes entrées et analyse non interrompue, mêmes constats. Il laisse à T14 le choix entre un budget de travail déterministe et la seule exclusion des analyses interrompues de la garantie. ES-03 énumère les limites à poser : taille d'entrée, taille décompressée cumulée et rapport de compression, dimensions déclarées, profondeur d'imbrication, nombre d'objets, mémoire, temps. Certaines se comptent (des octets, des objets) ; d'autres dépendent de la machine (mémoire disponible, vitesse du processeur).

## Options envisagées

### Option A — Mixte

Les limites de taille et de nombre sont comptées par le moteur, donc identiques sur toutes les machines. Le temps et la mémoire restent des garde-fous du système : une analyse arrêtée par eux est interrompue, hors garantie.

- Avantages : un fichier hostile qui dépasse une limite comptée la dépasse partout, avec le même rapport ; seuls les garde-fous de dernier recours rompent la garantie ; rien à instrumenter hors des fonctions qui comptent déjà.
- Inconvénients : deux familles de limites à expliquer dans le rapport et la documentation.

### Option B — Exclusion seule

Seul le délai borne le travail ; toute analyse interrompue est hors garantie.

- Avantages : le plus simple.
- Inconvénients : un même fichier peut être interrompu sur une machine lente et pas sur une autre ; une bombe de décompression n'est arrêtée qu'à l'épuisement de la mémoire ou du délai.

### Option C — Budget déterministe

Chaque module compte des unités de travail ; l'horloge ne sert plus.

- Avantages : reproductible partout, y compris pour les analyses longues.
- Inconvénients : chaque module doit être instrumenté ; le délai reste nécessaire contre une boucle dans du code C, qui ne compte rien.

## Décision

Option A. Le contexte d'un module compte ses résultats, les octets qu'il décompresse, les objets qu'il parcourt, les dimensions déclarées et l'imbrication ; un dépassement rend le module non mené pour `limite_depassee`, sans interrompre l'analyse. La mémoire et le temps sont limités par le système et par le processus principal ; un dépassement interrompt l'analyse, qui sort de la garantie de reproductibilité.

## Raisons

- Option A retenue : elle garde la garantie de reproductibilité pour tout ce qui se compte, c'est-à-dire pour presque toutes les défenses contre un fichier hostile, et ne la perd que là où la machine décide.
- Option B écartée : elle rend dépendant de la machine ce qui ne l'est pas, et n'arrête une bombe de décompression que tard.
- Option C écartée : son coût porte sur chaque module, sans dispenser du délai.

## Conséquences

- Les valeurs sont fixées par [ADR-0077](ADR-0077-valeurs-des-limites.md) ; l'interface du contexte, la raison de la mémoire et le sort des tailles du flux, par [ADR-0078](ADR-0078-budget-d-un-module-et-raisons.md).
- ADR-0056 évolue : `limite_depassee` n'interrompt plus l'analyse, puisqu'elle est désormais comptée, donc déterministe ; la mémoire du système a sa propre raison, qui interrompt (ADR-0078).
- La documentation utilisateur (T103) distingue les deux familles.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
