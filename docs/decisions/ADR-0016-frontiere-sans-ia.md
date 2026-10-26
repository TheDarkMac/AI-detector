# ADR-0016 — Frontière du « sans IA » : seuils calibrés admis, apprentissage exclu

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §2 (principe « aucune IA embarquée »), §8 (corpus), NF-06, NF-07, NF-09 ; constat A-12

## Contexte

Le §10 demande si un seuil calibré sur un corpus est admis, et une pondération apprise simple. L'analyse a relevé deux points (A-12) : les seuils seront de toute façon ajustés sur le corpus du §8, qui sert aussi à mesurer les taux d'erreur, ce qui donne des taux optimistes ; et un seuil réglé sur un corpus diffère peu en nature d'un petit modèle appris.

## Options envisagées

### Option A — Seuils calibrés admis, aucune pondération apprise

- Avantages : seuils justifiables par une mesure ; chaque règle reste lisible (une mesure, un seuil).
- Inconvénients : la frontière avec l'apprentissage doit être tenue par une règle écrite.

### Option B — Seuils fixés à la main seulement

- Avantages : le plus fidèle à la lettre du principe.
- Inconvénients : seuils tirés de la littérature, souvent mesurés sur d'autres données ; taux d'erreur probablement moins bons et difficiles à justifier.

### Option C — Pondérations apprises simples admises

- Avantages : meilleure combinaison des mesures.
- Inconvénients : glisse vers l'apprentissage ; une règle n'est plus lisible isolément.

## Décision

- **Admis** : règles écrites ; seuils fixés à la main ou **calibrés sur la partie « calibrage » du corpus**, par une procédure documentée. La valeur du seuil, la procédure et la version du corpus de calibrage sont publiées dans le catalogue (NF-07).
- **Exclu** : tout modèle appris, y compris une pondération ou une régression à quelques paramètres, et tout réseau de neurones.
- Le corpus est séparé en une partie **calibrage** et une partie **évaluation** ; la partie évaluation n'est jamais utilisée pour régler un seuil. Les taux d'erreur publiés sont mesurés sur la partie évaluation.
- Changer un seuil produit une nouvelle version du catalogue.

## Raisons

- Option A retenue : elle garde chaque règle explicable tout en rendant ses seuils justifiables.
- Option B écartée : un seuil non mesuré n'est pas plus explicable, seulement moins justifié.
- Option C écartée : une combinaison apprise ne se lit plus règle par règle, contraire à l'explicabilité et à la graduation sans combinaison arithmétique (ADR-0018).

## Conséquences

- T17 et T100 organisent le corpus en deux parties disjointes, avec leur version.
- Chaque fiche technique (NF-09) décrit la procédure de calibrage de ses seuils.
- La question « principe définitif, ou contrainte de la première version » n'est pas tranchée par cet ADR (registre des arbitrages).
- Les services tiers à base d'IA et l'OCR relèvent d'ADR-0017.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
