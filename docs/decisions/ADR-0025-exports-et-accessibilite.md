# ADR-0025 — Exports HTML et JSON, accessibilité WCAG 2.2 AA

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : F-83, F-84, CU-3, NF-12, NF-18 ; constat A-44

## Contexte

Le §10 laisse ouverts les formats d'export et le niveau d'accessibilité visé (NF-12). F-83 demande au moins un format lisible par une personne et un format exploitable par une machine. Une visualisation n'est pas accessible sans alternative textuelle (A-44).

## Options envisagées

### Option A — HTML et JSON, WCAG 2.2 AA

- Avantages : HTML lisible partout, imprimable en PDF par le navigateur, apte à porter les visualisations ; JSON exploitable par d'autres outils ; WCAG 2.2 AA est le niveau de référence courant.
- Inconvénients : un HTML accessible demande du soin (structure, contrastes, alternatives).

### Option B — Markdown et JSON

- Avantages : simple à produire depuis la ligne de commande.
- Inconvénients : rendu dépendant du lecteur ; visualisations mal intégrées.

### Option C — HTML, JSON et PDF natif

- Avantages : archivage direct (CU-3).
- Inconvénients : une dépendance de rendu de plus, et un format de plus à rendre accessible (PDF/UA).

## Décision

- Exports : **HTML autonome** (aucune ressource externe chargée à l'ouverture) et **JSON** conforme à un schéma publié et versionné.
- Niveau d'accessibilité visé pour le rapport HTML : **WCAG 2.2 niveau AA**. Chaque visualisation porte une description textuelle de ce qu'elle montre.
- Les données identifiantes sont masquées par défaut dans les deux exports (NF-18) ; leur levée est explicite et tracée.
- La sortie de la ligne de commande n'utilise jamais la couleur comme seul porteur d'information.

## Raisons

- Option A retenue : elle couvre lecture, archivage par impression et exploitation machine avec deux formats.
- Option B écartée : visualisations mal intégrées, rendu non maîtrisé.
- Option C écartée : coût d'un troisième format pour un besoin couvert par l'impression du HTML.
- HTML autonome : un rapport qui chargerait une ressource externe ferait une requête sortante à son ouverture (NF-16) et dépendrait du réseau (ADR-0010).

## Conséquences

- T16 produit les deux exports et publie le schéma JSON.
- T90 se limite en V1 à la ligne de commande et au rapport HTML (ADR-0010).
- La conformité WCAG est vérifiée par inspection et démonstration (ADR-0024).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-28 | Réalisé en T16 : HTML autonome sans script (ADR-0094), JSON au schéma du rapport 0.2.0 (ADR-0095), masquage par défaut et levée par catégorie (ADR-0093), écriture par `--rapport` (ADR-0092) |
