# ADR-0059 — Structure du rapport et de la couverture

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T11, validée pendant la revue de la PR de T11
- **Tâche** : T11
- **Exigences liées** : §6 du cahier, F-25, F-82 ; NF-06, NF-08 ; ES-14 ; ADR-0012, ADR-0015, ADR-0018, ADR-0023, ADR-0028, ADR-0029, ADR-0036

## Contexte

Le §6 du cahier énumère les rubriques du rapport. Plusieurs ADR y ajoutent des éléments : versions des dépendances (ADR-0023), état de l'isolation (ADR-0028), catalogue fourni par l'utilisateur (ADR-0029), analyse interrompue (ADR-0023), techniques hors V1 inscrites comme non menées (ADR-0012). T11 fixe ce que le modèle du rapport contient ; la mise en forme, le résumé et le masquage restent à T16. Ces choix n'ont pas fait l'objet d'une question pendant T11 ; ils ont été soumis dans la PR et validés par TheDarkMac.

## Options envisagées

### Option A — Le rapport ne contient que des données ; résumé, avertissement et masquage produits à l'export

- Avantages : une seule source pour chaque information ; aucun résumé ne peut contredire les constats ; T16 change la présentation sans changer le schéma.
- Inconvénients : un lecteur du JSON brut doit refaire le résumé.

### Option B — Le rapport stocke aussi son résumé et son état de masquage

- Avantages : JSON lisible tel quel.
- Inconvénients : deux vérités à garder cohérentes ; le masquage est une propriété d'un export, pas de l'analyse.

## Décision (Option A)

Un **rapport par fichier** (ADR-0015 : les fichiers d'un lot sont indépendants), composé de :

| Partie | Contenu | Origine |
| --- | --- | --- |
| Identification | Nom du fichier sans chemin, format réel, taille, empreinte SHA-256, date d'analyse en UTC à la seconde | §6, ES-14, ADR-0040 |
| Versions | Outil ; catalogue (version, date, empreinte, fourni par l'utilisateur ou non) ; dépendances qui décodent ou analysent le fichier | §6, ADR-0023, ADR-0029 |
| Isolation | Complète, ou réduite avec la liste fermée des restrictions manquantes | ADR-0028, ADR-0035 |
| Couverture | Chaque technique avec sa version et son état ; marquages recherchés | F-25, F-82 |
| Observations, constats, analyses non menées | ADR-0056, ADR-0058 | §6, F-82 |
| Interrompue | Calculée à partir des raisons des analyses non menées (ADR-0056) | ADR-0023, NF-08 |

États d'une technique : **appliquée**, **partielle** (appliquée, avec au moins une partie non menée), **non menée**, **non applicable** (format non traité).

Invariants vérifiés par le modèle :

1. Les identifiants d'observation sont uniques ; chaque constat ne cite que des observations du rapport.
2. Seule une technique appliquée ou partielle a des observations et des constats ; une technique non menée n'a aucun résultat retenu.
3. Une technique est partielle ou non menée si et seulement si une analyse non menée la désigne.
4. Une technique sans version est une technique hors de cette version de l'outil, et sa seule raison est `hors_v1`.
5. Le nom du fichier ne contient ni `/`, ni `\`, ni caractère nul : aucun chemin n'atteint le rapport (ES-14).

Hors du modèle de T11 :

- **résumé**, **avertissement**, **état du masquage** : produits à l'export (T16) ;
- **liste de confiance C2PA** et **données externes** (ADR-0023) : ajoutées avec T30, quand elles existent ;
- **concordance des empreintes** (ES-08) : un rapport n'est construit que si l'empreinte recalculée par P2 est égale à celle de P1 ; le cas contraire relève de T13.

## Raisons

- Option A retenue : le modèle reste la trace de l'analyse ; tout ce qui en dérive est recalculé.
- Option B écartée : le masquage dépend de l'export choisi par l'utilisateur, pas de l'analyse ; stocker le résumé ouvre la porte à une incohérence.
- État « partielle » : sans lui, un module appliqué à la première image d'un HEIC seulement paraîtrait complet (A-25).
- Technique hors V1 dans la couverture : ADR-0012 veut qu'elle figure comme non menée ; sans module livré, elle n'a pas de version.
- « Interrompue » calculée : un champ saisi pourrait contredire les raisons.

## Conséquences

- T12 construit la couverture à partir des manifestes (ADR-0042) et de la configuration ; il retire les résultats d'un module non mené.
- T12 ou T15 tiennent la liste des techniques hors V1 par format, source des non menées `hors_v1`.
- T13 fournit le nom sans chemin, le format réel et l'empreinte ; T14 les manques de l'isolation.
- T16 calcule le résumé dans l'ordre d'ADR-0018 et applique le masquage (ES-13).
- T18 compare les constats de deux rapports non interrompus.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création, statut « Proposé » |
| 2026-10-26 | Validé par TheDarkMac pendant la revue de la PR de T11 : statut « Accepté » |
| 2026-10-26 | Renvoi : couverture construite par T12 à partir des manifestes et du message « module » (ADR-0062) ; liste des techniques hors V1 par format laissée à T15 |
| 2026-10-27 | Précisé en T13 : couverture par technique et par partie (ADR-0071), signalements de l'identification (ADR-0072), empreinte finale du travail ou à défaut du principal (ADR-0075) |
| 2026-10-27 | Point 4 précisé par ADR-0087 (T15) : une technique sans version est non menée pour la seule raison `hors_v1`, ou non applicable sur une autre partie d'un polyglotte ; liste des techniques hors V1 tenue par T15 |
| 2026-10-28 | Réalisé en T16 : résumé, avertissement et masquage produits à l'export, non stockés (ADR-0095, ADR-0098) ; `Analyse.rapport()` construit le rapport (ADR-0097) |
