# ADR-0269 — Détail d'une règle par `vk --regle IDENTIFIANT`, dans la forme des fichiers du catalogue

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T95
- **Exigences liées** : NF-19, NF-07, ES-12 ; objectif 4 ; ADR-0019, ADR-0084, ADR-0086, ADR-0088

## Contexte

NF-19, reformulée par ADR-0019 : « Le détail des règles et des seuils est public ». `vk --regles` affiche la version, la date, l'empreinte du catalogue employé et, pour chaque règle, son identifiant, sa version, son module et son titre. Les conditions, les seuils, les limites connues, l'évaluation et le calibrage ne se lisent que dans les fichiers TOML du paquet, qu'un utilisateur doit savoir trouver dans son installation. Un constat du rapport cite sa règle et ses limites, pas ses conditions.

## Options envisagées

### Option A — `vk --regle IDENTIFIANT` (recommandée)

- Avantages : tout d'une règle à la demande, depuis l'identifiant que cite le constat ; `--regles` reste une liste courte.
- Inconvénients : une option de plus.

### Option B — `vk --regles` détaillé

- Avantages : une seule option.
- Inconvénients : 151 règles en entier, une sortie de plusieurs milliers de lignes, inutilisable pour en lire une.

### Option C — Fichiers TOML seuls

- Avantages : rien à écrire.
- Inconvénients : le détail est public sans être accessible à qui ne connaît pas l'arborescence du paquet ; un catalogue fourni par `--catalogue` est déjà sous la main de l'utilisateur, le catalogue livré non.

## Décision

Option A.

- **`vk --regle IDENTIFIANT`**, répétable, seule ou avec `--catalogue DOSSIER` (code 2 avec toute autre option ou un fichier) : les règles demandées du catalogue employé, dans l'ordre de la commande, chacune une fois. Un identifiant absent du catalogue donne le code 2, sans rien afficher, avec un renvoi à `vk --regles`.
- **Forme** : celle des fichiers `regles/<module>.toml`, décrite au §2 du guide du catalogue (`[[regle]]`, `[[regle.condition]]`, tables en ligne pour la phrase, le seuil, la comparaison, l'évaluation et le calibrage, une ligne par élément d'une liste de plusieurs). Relue par `tomllib`, elle redonne `Regle.vers_dict` ; un test le vérifie pour chaque règle livrée. En tête, trois lignes de commentaire : version, date, empreinte et origine du catalogue (« fourni par l'utilisateur »), renvoi au guide, renvoi à `vk --fiche MODULE`.
- Caractères de contrôle, de mise en forme et séparateurs de ligne ou de paragraphe s'écrivent `\uXXXX` (ou `\UXXXXXXXX`) : la valeur relue est la même, et un catalogue fourni par l'utilisateur ne peut rien écrire au terminal qu'il n'affiche tel quel (ES-12).
- Écartée : une présentation en phrases (« seuil : au moins 4 »), plus lisible pour un néophyte, mais qu'il faudrait traduire champ par champ et qui ne se recopierait pas dans un catalogue fourni (ADR-0086) ; le guide décrit déjà chaque champ.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : une liste de toutes les règles en entier ne sert ni à consulter une règle ni à les parcourir.
- Option C écartée : la publicité de NF-19 suppose que le détail soit lisible depuis l'outil, pas seulement présent dans ses fichiers.

## Conséquences

- `src/voight_kampff/_publication.py` écrit le TOML avec la seule bibliothèque standard : aucune dépendance ajoutée (ADR-0043).
- La rubrique Couverture du rapport HTML renvoie à `vk --regle IDENTIFIANT` (ADR-0270).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
