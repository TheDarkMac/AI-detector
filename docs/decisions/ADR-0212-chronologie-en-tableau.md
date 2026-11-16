# ADR-0212 — Chronologie des versions d'un PDF : visualisation en tableau, non masquée ; schéma 0.8.0

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (colonnes, bornes et textes précisés par l'assistant)
- **Tâche** : T50
- **Exigences liées** : F-60, F-84, ES-04, ES-12, ES-13, NF-06, NF-11 ; ADR-0025, ADR-0036, ADR-0094, ADR-0200

## Contexte

F-84 demande une chronologie des révisions PDF. ADR-0200 a fait de la visualisation une image PNG écrite par le module, masquée par défaut parce qu'elle montre le contenu du fichier, et prévoyait que la chronologie PDF prendrait « une nature de plus, sans nouveau mécanisme ». Or une chronologie est un tableau de nombres et de textes : le projet n'a aucun rendu de police pour l'écrire en image, et elle ne montre pas le contenu du document.

## Options envisagées

### Option A — Tableau (recommandée)

Une visualisation d'une nouvelle forme : des lignes de cellules typées, rendues en tableau HTML par l'export, qui échappe chaque cellule ; non masquée ; schéma du rapport et des messages 0.8.0.

- Avantages : lisible et accessible (NF-11) ; aucune balise écrite par le module (ES-12) ; reste dans la rubrique « Visualisations », sous son avertissement.
- Inconvénients : un mécanisme de plus dans le modèle, les schémas et l'export.

### Option B — Observations seules

Les listes `revisionspdf.fins`, `natures`… suffisent, sans visualisation.

- Avantages : rien à ajouter au modèle.
- Inconvénients : F-84 reste partielle pour le PDF ; le lecteur doit croiser cinq listes.

### Option C — Image PNG

Une frise sans texte dessinée par le module, masquée comme la carte ELA.

- Avantages : le mécanisme d'ADR-0200.
- Inconvénients : sans texte, une frise ne dit ni la nature ni la date ; masquée par défaut sans raison, puisqu'elle ne montre pas le contenu.

## Décision

Option A. Précisions de l'assistant :

- **Modèle** : `Visualisation.tableau(module, nature, lignes)` ; une nature est un tableau si `COLONNES` lui donne des colonnes (nom et type) ; `largeur` est le nombre de colonnes, `hauteur` celui des lignes, `png` est vide ; 1 à 256 lignes ; cellules entières positives ou nulles, ou textes de 64 caractères au plus ; pas de catégorie identifiante.
- **Nature** `chronologie_revisions`, colonnes : `version`, `fin` (octets), `nature` (codes d'ADR-0208 joints par `+`), `ajoutes`, `remplaces`, `supprimes`, `date`, `signatures`.
- **Date déclarée** : `/ModDate` du dictionnaire Info de la version (de création à défaut, pour la première), seulement quand elle diffère de celle de la version précédente ; vide sinon, ou si elle dépasse 64 caractères, ou pour un document chiffré (ADR-0210).
- **Signatures** : celles dont la plage complète finit à la fin de la version (ADR-0209).
- **Émise** dès que le document garde au moins deux versions ; les 256 premières versions au tableau, toutes aux observations, et le rapport dit quand le tableau est coupé.
- **JSON** : `module`, `nature`, `colonnes`, `lignes`, `localisation`, `partie` ; un tableau n'a ni `type_media`, ni dimensions, ni `donnees`, ni `empreinte`, ni `identifiante`, et le masquage de « contenu » ne le touche pas.
- **HTML** : titre, avertissement en cinq paragraphes (`textes.toml`), puis le tableau : nombres groupés, natures nommées en français, cellule vide en tiret.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- B écartée : F-84 demande une visualisation.
- C écartée : une frise sans texte ne se lit pas, et le masquage n'aurait pas de raison.
- Non masquée : fins, natures, nombres d'objets et dates ne désignent pas une source (ES-13) ; une date peut dater un document, comme les observations de dates, qui ne sont pas masquées non plus.

## Conséquences

- `VERSION_SCHEMA` passe à 0.8.0 ; un rapport 0.7.0 n'est plus relu par `vk --comparer`, comme à chaque version.
- Le schéma du rapport distingue `visualisation_image` et `visualisation_tableau` ; celui des messages exige `donnees` et `empreinte` pour une image seulement.
- La prévision d'ADR-0200 (« sans nouveau mécanisme ») ne tient pas pour la chronologie : renvoi ajouté à son historique. Le spectre et le spectrogramme (T43, T60) restent des images.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création ; option choisie par TheDarkMac au début de T50 |
