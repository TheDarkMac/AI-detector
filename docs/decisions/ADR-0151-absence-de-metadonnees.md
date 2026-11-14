# ADR-0151 — Absence de métadonnées : une règle par module, information neutre

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (fondement précisé par l'assistant)
- **Tâche** : T23
- **Exigences liées** : F-06, F-14, P-04 ; A-34 ; ADR-0021, ADR-0058, ADR-0084, ADR-0098

## Contexte

F-14 demande de présenter l'absence de métadonnées comme une information neutre, jamais comme un indice d'IA. Depuis T20 et T21, chaque module de métadonnées observe `<famille>.present`, à faux s'il ne trouve rien ; aucun constat n'en naît, et le rapport ne la présente que parmi les observations. A-34 demande d'écrire la règle explicitement : neutre vis-à-vis de l'origine IA, utilisable comme indice de transfert (F-06, T24).

## Options envisagées

### Option A — Une règle par module

Chaque module a une règle « moteur » : `<famille>.present` égal à faux donne une information neutre, dont la phrase dit l'absence et qu'elle ne dit rien de l'origine du fichier.

- Avantages : la règle est publique et versionnée comme les autres (ADR-0019) ; T24 pourra la citer ; le rapport la présente à la rubrique des informations neutres, et le résumé la compte.
- Inconvénients : deux ou trois constats pour une image sans aucune métadonnée (EXIF, XMP, IPTC).

### Option B — Texte du rapport

Aucun constat : le rapport regroupe les familles absentes sous une phrase fixe de `textes.toml`.

- Avantages : moins de constats.
- Inconvénients : le texte est hors du catalogue, sans règle citable ni version ; le rapport devrait connaître la convention `<famille>.present` des modules.

## Décision

Option A.

- Douze règles, une par module de métadonnées : catégorie `information_neutre`, direction `rien_de_particulier`, une condition `<famille>.present` égal à `false`.
- Phrase : « Le fichier ne porte aucune métadonnée … Cette absence est fréquente (messageries, réseaux sociaux, conversions) et ne dit rien de son origine. »
- Limites : l'absence n'est ni un indice d'IA ni une garantie d'authenticité (F-14, P-04) ; seuls les emplacements de la fiche du module sont lus.
- Fondement : `verification_deterministe`, précision de l'assistant. L'absence n'est pas une déclaration du fichier : c'est ce que le module constate en lisant la structure, de façon déterministe ; une information neutre peut avoir ce fondement (ADR-0058, seule une preuve est contrainte).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un texte hors du catalogue ne peut être cité par une règle de T24, et la présentation dépendrait d'un nom d'observation que le rapport n'a pas à connaître.
- Fondement « déclaration » écarté : le libellé du rapport, « déclaration contenue dans le fichier », serait faux pour une absence.

## Conséquences

- Une image sans métadonnées porte des informations neutres, aucun indice ; le taux par fichier ne change pas (ADR-0104).
- T24 pourra s'appuyer sur ces règles pour l'indice de transfert, avec ses propres règles et sa propre direction.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création |
| 2026-11-14 | Renvoi : les règles de transfert de T24 citent ces règles et comptent elles-mêmes les blocs de métadonnées (ADR-0153, ADR-0154) |
