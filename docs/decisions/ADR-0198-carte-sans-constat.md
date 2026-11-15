# ADR-0198 — ELA : une carte et son avertissement, sans règle ni constat

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T42
- **Exigences liées** : F-32, F-80, F-81, F-84 ; A-02 ; ADR-0012, ADR-0016, ADR-0018

## Contexte

F-32 demande le niveau d'erreur de recompression « accompagné d'un avertissement d'interprétation », F-84 la carte ELA parmi les visualisations utiles à la lecture. L'ELA ne distingue pas la génération (A-02) et se lit souvent mal : c'est la raison du rejet de l'ELA en V1 par ADR-0012. Il fallait dire si l'ELA produit un constat.

## Options envisagées

### Option A — Carte seule

Aucune règle ni constat : la carte et son avertissement sont une aide à la lecture (F-84), avec quelques observations chiffrées (écart moyen, plus grand écart d'un bloc).

- Avantages : rien d'affirmé sans mesure sur un corpus ; la carte reste ce qu'elle est, une image à regarder ; aucun seuil fixé à la main.
- Inconvénients : le résumé ne signale aucune zone ; la lecture revient entièrement à la personne.

### Option B — Carte et indice faible

Une règle relève une zone dont l'erreur s'écarte nettement du reste, en indice faible vers la retouche, avec un seuil fixé à la main sur des essais.

- Avantages : le résumé attirerait l'attention sur une zone.
- Inconvénients : le contenu (contours, textures, aplats) fait autant varier l'erreur que l'histoire du fichier ; un seuil sans corpus produirait des indices sur des photos ordinaires ; c'est la lecture abusive que l'avertissement doit prévenir.

## Décision

Option A. Le module `ela` n'émet aucun constat et aucune règle du catalogue ne lit ses observations. Ses observations : procédé, qualité de recompression, blocs de la carte et de l'image, écart moyen par pixel et plus grand écart moyen d'un bloc.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : un indice dont la cause la plus fréquente serait le contenu de l'image contredirait ADR-0018 (niveaux d'indice bornés par des taux mesurés) avant toute mesure.

## Conséquences

- Pas de taux d'erreur à mesurer au sens du §8 : la fiche le dit, et renvoie à l'étude d'usage (T104, hors V1) pour la lecture des cartes.
- Le manifeste exige une direction ; celle du module ne sert à aucun constat (ADR-0201).
- Une règle pourra être ajoutée plus tard, sur mesure (T100), sans changer le module : les observations chiffrées existent.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
