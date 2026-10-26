# ADR-0039 — Expressions régulières du catalogue : RE2

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T04
- **Exigences liées** : F-12, NF-02, NF-08 ; ES-09 ; menaces M-03, M-12

## Contexte

Les signatures de générateurs (F-12) se lisent souvent dans des chaînes libres : nom de logiciel, paramètres de génération dans un bloc texte PNG. Des expressions régulières sont commodes pour les écrire. Mais le moteur `re` de Python procède par retour arrière : une expression mal écrite, appliquée à une chaîne choisie par l'adversaire, peut prendre un temps exponentiel (M-03). ES-09 exige des expressions à temps linéaire.

## Options envisagées

### Option A — RE2

- Avantages : temps linéaire garanti par construction ; syntaxe proche de celle de Python ; licence BSD-3.
- Inconvénients : dépendance écrite en C++ ; pas de références arrière ni d'assertions de contexte.

### Option B — Aucune expression régulière

- Avantages : sûr et sans dépendance.
- Inconvénients : comparaisons exactes, préfixes et listes seulement ; certaines signatures deviennent difficiles ou impossibles à écrire.

### Option C — `re` avec limite de temps

- Avantages : aucune dépendance.
- Inconvénients : aucune garantie de temps linéaire ; la limite interrompt l'analyse au lieu de l'empêcher de dériver ; contraire à ES-09.

## Décision

- Les expressions régulières du catalogue sont exécutées par **RE2** (paquet `google-re2`), dans le processus de travail.
- Le processus principal les compile au chargement du catalogue : une expression que RE2 refuse rend le catalogue invalide.
- Le module `re` de Python n'est jamais appliqué à une donnée tirée du fichier avec une expression venue du catalogue. Le code du projet peut utiliser `re` pour ses propres expressions fixes, relues pour l'absence de retour arrière catastrophique.

## Raisons

- Option A retenue : elle satisfait ES-09 par construction, sans priver le catalogue d'un moyen d'expression utile ; son code C++ s'exécute dans le processus isolé.
- Option B écartée : elle appauvrit F-12 pour un risque qu'une autre option supprime.
- Option C écartée : ES-09.

## Conséquences

- T15 fixe la syntaxe admise dans le catalogue (sous-ensemble de RE2) et la vérification au chargement.
- La disponibilité de paquets binaires de `google-re2` pour les trois systèmes et les versions de Python visées est vérifiée en T10 ; à défaut, un nouvel ADR choisit une autre liaison RE2 ou l'option B.
- Version de RE2 inscrite au rapport (ADR-0023).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : paquets binaires de `google-re2` vérifiés en T10 : Python 3.10 à 3.14 sur les trois systèmes, pas encore 3.15 (ADR-0051) (T10) |
