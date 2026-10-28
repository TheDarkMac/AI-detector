# ADR-0097 — L'analyse porte les règles qu'elle cite ; interface publique d'export

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : l'assistant, choix soumis dans la PR de T16
- **Tâche** : T16
- **Exigences liées** : §6 du cahier (« Indices » : règle, valeur observée, limites connues), F-83, NF-06 ; ES-17 ; ADR-0059, ADR-0068, ADR-0073, ADR-0090

## Contexte

Le rapport présente chaque constat avec le titre, la phrase, les limites et l'évaluation de sa règle (§6, ADR-0018). Ces textes sont dans le catalogue, que l'`Analyse` rendue par `analyser` ne désignait que par sa version (ADR-0073). Recharger le catalogue à l'export risquerait d'en lire un autre que celui de l'analyse. Il fallait aussi l'interface qui construit et exporte le rapport.

## Options envisagées

### Option A — L'analyse porte les règles que citent ses constats

- Avantages : l'export se fait sans relire de fichier, avec exactement les règles de l'analyse ; chaque constat est vérifié conforme à la sienne.
- Inconvénients : l'`Analyse`, objet public, expose une classe d'un module interne (`_regles.Regle`).

### Option B — L'export reçoit le catalogue

- Avantages : `Analyse` ne change pas.
- Inconvénients : l'appelant peut passer un autre catalogue que celui de l'analyse ; le rapport dirait alors les limites d'une autre règle.

### Option C — Les règles recopiées dans le rapport

- Avantages : JSON autonome.
- Inconvénients : contraire à ADR-0059 (le rapport ne porte que des données) ; duplique le catalogue dans chaque rapport.

## Décision

Option A.

- `Analyse.regles` : les règles du catalogue employé que citent ses constats, jointes par la soumission. À la construction, chaque constat doit avoir la sienne et y être conforme (ADR-0090) ; une règle en double est refusée. `Analyse.regle(constat)` la rend.
- `Analyse.rapport()` construit le `Rapport` du modèle : identification, versions (outil, catalogue, dépendances), isolation, couverture, résultats. Il est complet, donc non masqué, et ne doit pas être affiché tel quel.
- Le paquet exporte `exporter_json(analyse, *, reveler=())`, `exporter_html(analyse, *, reveler=())` et `CategorieIdentifiante`, qui rendent le texte de l'export ; `rapport.export.valider(document)` vérifie un export JSON (ADR-0095).
- Ces fonctions ne chargent ni `jsonschema` ni le processus principal à l'import (le processus de travail importe le paquet) : la validation importe le schéma à l'appel.

## Raisons

- Option A retenue : l'export ne peut pas mentir sur la règle qui a produit un constat.
- Option B écartée : elle ouvre une incohérence entre l'analyse et son rapport.
- Option C écartée : ADR-0059.
- Exposer `Regle` : c'est la forme publique d'une règle, déjà affichée par `vk --regles` et décrite par le schéma `regles` ; la rendre publique sous un autre nom n'ajouterait qu'une copie.

## Conséquences

- L'interface publique change (ADR-0068) ; aucune version stable n'est encore publiée.
- T18 compare les constats de deux rapports : `Analyse.rapport()` les lui donne.
- T90 (interface) et T91 (journal de conservation) partent des mêmes fonctions.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
