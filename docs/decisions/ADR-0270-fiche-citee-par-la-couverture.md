# ADR-0270 — La couverture du rapport HTML cite la commande de la fiche de chaque technique livrée

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T95
- **Exigences liées** : NF-19, NF-09, NF-16 ; objectif 4 ; ADR-0010, ADR-0025, ADR-0265, ADR-0268, ADR-0269

## Contexte

Le rapport HTML affiche à chaque constat sa règle et ses limites connues, et à la rubrique Couverture chaque technique, sa partie, sa version et son état. Rien n'y dit où lire le principe et le taux d'erreur d'une technique. Le rapport HTML est autonome : il ne charge aucune ressource externe, ce qui ferait une requête sortante à son ouverture (ADR-0025, NF-16).

## Options envisagées

### Option A — Nom de la commande, sans adresse (recommandée)

- Avantages : le rapport reste sans lien externe ; la commande donne la fiche de l'outil installé, hors ligne.
- Inconvénients : rien de cliquable ; la fiche affichée est celle de la version installée, qui peut ne pas être celle du rapport.

### Option B — Lien vers la fiche sur GitHub, à l'étiquette de la version

- Avantages : cliquable ; la fiche de la version du rapport.
- Inconvénients : ouvrir le lien envoie une requête qui révèle l'intérêt pour une technique ; une version de développement n'a pas d'étiquette ; un lien externe de plus dans un rapport qui n'en a aucun.

### Option C — Rien

- Avantages : rapport inchangé.
- Inconvénients : le lecteur d'un rapport ne sait pas où trouver la fiche.

## Décision

Option A.

- Le tableau des techniques de la rubrique Couverture prend une colonne « Fiche technique » : `vk --fiche MODULE` pour une technique livrée, vide pour une technique hors de cette version, qui n'a pas de fiche.
- Sous le tableau, un paragraphe dit ce que donne la fiche (principe, taux d'erreur, limites connues), qu'une règle citée par un constat s'affiche en entier par `vk --regle IDENTIFIANT` (ADR-0269), et que l'une et l'autre sont celles de l'outil installé, qui peuvent différer si sa version n'est pas celle du rapport.
- Rapport JSON, schémas et catalogue inchangés : la commande se déduit de l'identifiant du module, que le JSON porte déjà.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : un lien suivi depuis le rapport est une requête sortante, que NF-16 demande de réduire au minimum, pour lire ce que l'outil installé affiche hors ligne (ADR-0010).
- Option C écartée : la publication des fiches ne sert qu'à qui sait qu'elles existent.

## Conséquences

- `tests/test_publication.py` vérifie la colonne pour chaque technique d'une analyse, celle hors de cette version comprise.
- Les tests qui lisent le tableau de la couverture voient une colonne de plus.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
