# ADR-0217 — Objets changés par les versions d'un PDF : un par un, en tableau ; `revisionspdf` 0.2.0, schéma 0.9.0

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (colonnes, bornes et textes précisés par l'assistant)
- **Tâche** : T51
- **Exigences liées** : F-61, F-84, ES-04, ES-12, ES-13 ; ADR-0208, ADR-0212

## Contexte

F-61 demande de relever les objets ajoutés ou remplacés. T50 les compte par version et en tire la nature de chaque version (ADR-0208), mais renvoie à T51 leur description un par un. Le lecteur d'un rapport doit pouvoir savoir quel objet une version change, ce qu'il est et quelle page il touche, sans ouvrir le fichier dans un autre outil.

## Options envisagées

### Option A — Tableau dans `revisionspdf` (recommandée)

Une seconde visualisation en tableau (mécanisme d'ADR-0212), une ligne par objet changé : version, numéro, état, type, nature d'ADR-0208, page touchée ; 256 lignes au plus, toutes comptées par une observation.

- Avantages : lisible d'un coup d'œil, sous la chronologie ; le module a déjà tout en main.
- Inconvénients : une nature de visualisation de plus, dans le modèle, les schémas et l'export.

### Option B — Observations seules

Des listes d'observations par version (numéros, types).

- Avantages : rien à ajouter au modèle.
- Inconvénients : des listes parallèles à croiser à la main, une par version.

## Décision

Option A. Précisions de l'assistant :

- **Nature** `objets_revisions`, colonnes : `version`, `objet` (numéro), `generation`, `etat` (`ajoute`, `remplace`, `supprime`), `type`, `nature`, `page`.
- **Type** : `/Type` et `/Subtype` de l'objet, joints par « / », 64 caractères au plus ; à défaut sa forme (`flux`, `dictionnaire`, `tableau`, `valeur`) ; vide pour un objet nul ou non lu. L'objet supprimé est lu dans la version précédente.
- **Nature** : le rangement d'ADR-0208 (`structure`, `signature`, `formulaire`, `annotation`, `metadonnees`, `non_reconnue`, `non_lue`).
- **Page** : rang de la première page de la version qui désigne l'objet, directement : la page elle-même, ses flux de contenu, ses annotations, ses ressources, leurs polices et leurs objets externes ; 0 sinon (tiret au rapport). La version précédente pour un objet supprimé. Le relevé parcourt au plus 65 536 objets de l'arbre des pages, seulement pour les versions dont des objets figurent au tableau ; une structure illisible l'arrête là où il en est.
- **Bornes** : les 256 premiers objets, dans l'ordre des versions puis des numéros ; `revisionspdf.objets` les compte tous, et le rapport dit quand le tableau est coupé.
- **Rendu** : sous la chronologie, titre et avertissement en quatre paragraphes (`textes.toml`), états et natures nommés en français ; non masqué (aucune donnée identifiante).
- **Schémas** : `visualisation_tableau` devient le choix entre `tableau_chronologie_revisions` et `tableau_objets_revisions`, aux colonnes fixées par leur nature ; schémas du rapport et des messages 0.9.0.
- **Versions** : `revisionspdf` 0.2.0, exigences F-60, F-61 et F-84.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- B écartée : F-61 demande de décrire les objets ; des listes à croiser ne le font pas pour un lecteur.
- Page plutôt que chemin complet : une page suffit à aller voir ; un chemin dans l'arbre des objets n'a de sens que pour un spécialiste.

## Conséquences

- `VERSION_SCHEMA` passe à 0.9.0 ; un rapport 0.8.0 n'est plus relu par `vk --comparer`, comme à chaque version.
- Le résumé annonce deux visualisations pour un PDF mis à jour ; sa phrase dit désormais de lire l'avertissement « de chacune ».
- Le texte de couverture partielle de la chronologie prend le paramètre `total` au lieu de `versions`, commun aux deux tableaux.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T51 |
