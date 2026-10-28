# ADR-0121 — Coût de la validation : références résolues, branche choisie par nature, résultats bornés

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T20, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : ES-03, ES-04, NF-02, NF-06 ; ADR-0054, ADR-0065, ADR-0076, ADR-0077, ADR-0078 ; architecture §12

## Contexte

Le processus principal valide chaque message du processus de travail par le schéma, puis par le modèle (ES-04, ADR-0065) ; l'export JSON est validé avant écriture (ADR-0095). L'architecture (§12) estimait ce coût à environ 1,5 ms par message et le renvoyait au premier module à produire beaucoup d'observations. Mesures de T20, sur le poste de développement (4 cœurs, charge moyenne de 4,5 à 6,5 due à d'autres programmes), trois passages, valeurs extrêmes :

| Mesure | Avant | Après |
| --- | --- | --- |
| Validation d'un message d'observation (3 000 fois) | 1,62 à 3,45 ms | 0,38 à 0,83 ms |
| Analyse d'un PNG portant 4 000 propriétés XMP (commande entière, rapports écrits) | 13,7 à 19,3 s | 4,2 à 5,4 s |

La validation d'un message est quatre à cinq fois plus rapide, la commande trois fois ; le reste de son temps va surtout à la validation de l'export JSON entier et à l'écriture du HTML.

Le profil montrait que la résolution des références `$ref` par `referencing`, et le `oneOf` des messages, qui évalue chacune des huit branches, prenaient l'essentiel du temps, plus que les contrôles eux-mêmes. Le délai d'une analyse est de 120 s (ADR-0077) : un fichier hostile qui porte des dizaines de milliers de propriétés aurait épuisé ce délai, ce qui interrompt l'analyse au lieu de la borner de façon reproductible.

## Options envisagées

### Option A — Schémas aux références résolues, branche choisie par nature, nombre de résultats borné

- Avantages : même validation, quatre fois plus rapide ; le pire cas d'un module devient une limite comptée, identique sur toutes les machines (ADR-0076).
- Inconvénients : un second jeu de valideurs à tenir en accord avec les schémas livrés ; un module très prolixe perd tous ses résultats.

### Option B — Ne plus valider par le schéma les messages d'observation

- Avantages : le plus rapide ; le modèle contrôle déjà chaque champ.
- Inconvénients : retire une des deux barrières d'ES-04 face à un processus de travail compromis (M-10).

### Option C — Accepter le coût

- Avantages : rien à changer.
- Inconvénients : le délai, garde-fou chronométré, devient la limite d'un fichier prolixe : l'analyse est interrompue, hors garantie (ADR-0023), et l'issue dépend de la machine.

## Décision

Option A.

- `schemas.valider` reconnaît d'abord un document conforme par un valideur dont chaque `$ref` a été remplacé, au chargement, par le schéma qu'il désigne (`allOf` avec les mots-clés voisins, sans effet en 2020-12) ; une référence circulaire est refusée au chargement. Pour un document que ce valideur refuse, le valideur du schéma livré cherche l'erreur et son emplacement, comme avant : les messages d'erreur ne changent pas. Si ce dernier ne trouvait aucune erreur (désaccord des deux valideurs), le document serait refusé quand même.
- Pour les messages, la branche du `oneOf` est choisie par la valeur de `type` : chaque branche fixe la sienne, donc au plus une peut convenir, et valider celle-là revient au `oneOf`. Un `type` absent, non textuel ou inconnu est validé par le schéma entier, qui le refuse.
- Nouvelle limite comptée du budget d'un module sur une partie (ADR-0078) : **4 096 résultats** (observations, constats, analyses non menées), `RESULTATS_MAX` dans `_limites.py`. Au-delà, le module est arrêté pour `limite_depassee` et ses résultats écartés ; les autres continuent.

## Raisons

- Option A : la validation reste entière, et le temps d'une analyse est borné par ce que compte le moteur, non par la vitesse du poste.
- « Avant » mesuré avec l'ancienne fonction de validation substituée dans le même processus, sur le même fichier, pour ne comparer que la validation.
- Option B écartée : ES-04 exige la validation de chaque message par le principal.
- Option C écartée : interruption non reproductible d'un fichier simplement prolixe.
- 4 096 résultats : l'image la plus riche des échantillons et du corpus d'essai en produit moins de 50 ; une photo retouchée et cataloguée en porte quelques centaines. D'après les mesures ci-dessus, environ 1,2 ms par observation pour la commande entière : quatre modules au maximum, soit 16 384 résultats, restent autour de 20 s, loin du délai de 120 s.

## Conséquences

- Un test vérifie que les valideurs rapides n'ont plus de référence et que la résolution refuse un cycle ; les tests des schémas, qui refusent des documents invalides, passent par les deux valideurs.
- Un schéma qui gagnerait une référence récursive devra garder le valideur livré seul pour lui.
- Le point « Coût de la validation des messages » de l'architecture (§12) est clos.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
