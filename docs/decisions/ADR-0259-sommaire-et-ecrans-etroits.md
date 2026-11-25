# ADR-0259 — Sommaire du rapport HTML et lecture sur un écran étroit

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; lien d'évitement et retours à la ligne précisés par l'assistant, dans cet ADR
- **Tâche** : T90
- **Exigences liées** : NF-11, NF-12 ; ADR-0025, ADR-0094, ADR-0098, ADR-0256

## Contexte

Le rapport HTML d'un JPEG (`tests/donnees/ela/collage_60_92.jpg`) affiche environ 17 700 caractères de texte en quinze rubriques, sans sommaire : on n'atteint une rubrique qu'en faisant défiler ou par les titres, pour qui sait s'en servir. Sur un écran de 320 px, les listes de définitions gardent deux colonnes, dont celle des valeurs n'a que 94 px.

## Options envisagées

### Option A — Sommaire et écrans étroits (recommandée)

Un sommaire des rubriques sous l'en-tête ; les listes de définitions empilées sous 30 rem.

- Avantages : chaque rubrique est à un lien ; la lecture sur téléphone ou à fort grossissement reste possible.
- Inconvénients : un bloc de plus en tête de rapport.

### Option B — Sommaire seul

- Avantages : plus court à faire.
- Inconvénients : la mise en page étroite reste difficile à lire.

### Option C — Rien

- Avantages : aucun changement.
- Inconvénients : seuls les défauts que l'audit trouve seraient corrigés.

## Décision

Option A.

- Un `<nav>` nommé par son titre « Sommaire » (niveau 2), entre l'en-tête et le contenu principal, liste en liste numérotée chaque rubrique du document, dans son ordre, « Attention » comprise quand il y a des alertes. Il n'est pas imprimé. Ses liens ont 24 px de haut au moins (WCAG 2.5.8).
- Le lien d'évitement mène toujours au résumé : il passe le sommaire, qui est le bloc à éviter. La question posée à TheDarkMac proposait de le faire mener au sommaire ; l'assistant l'a gardé au résumé en écrivant le code, le sommaire suivant immédiatement l'en-tête, si bien qu'un lien vers lui n'éviterait rien.
- Sous 30 rem, chaque terme d'une liste de définitions passe au-dessus de sa valeur.
- Un titre, un paragraphe ou un élément de liste peut se couper n'importe où, comme les valeurs et les cellules depuis T16 : une phrase de règle qui cite une longue adresse (`DigitalSourceType` de l'IPTC) débordait d'un écran de 320 px (WCAG 1.4.10), défaut trouvé pendant l'audit d'ADR-0256.
- Une zone de défilement d'un tableau prise au clavier porte le même contour que les liens.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : à 320 px, la valeur d'une définition tient en quelques caractères par ligne.
- Option C écartée : la longueur du rapport est un défaut de lisibilité (NF-11) même sans défaut d'accessibilité.

## Conséquences

- La feuille de style change, donc son empreinte dans la politique de sécurité (ADR-0094), calculée à chaque rapport ; rien d'autre n'y est autorisé.
- Une rubrique ajoutée au rapport entre dans le sommaire sans autre changement : le sommaire est construit à partir de la liste des rubriques.
- Les tests vérifient que le sommaire et les rubriques sont les mêmes, dans le même ordre, avec et sans alertes.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
