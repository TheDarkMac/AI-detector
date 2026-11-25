# ADR-0256 — Vérification de WCAG 2.2 AA : grille des critères et passage d'axe-core, hors de la CI

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T90
- **Exigences liées** : NF-12 ; ADR-0024, ADR-0025, ADR-0094

## Contexte

ADR-0025 fixe le niveau visé du rapport HTML à WCAG 2.2 AA et le fait vérifier « par inspection et démonstration ». T16 a structuré le rapport pour ce niveau et calculé ses contrastes, mais n'a fait aucun audit par un outil automatique (journal de T16, « Non fait ») ; la matrice de vérification garde NF-12 à l'état « partielle » pour cette raison. T90 porte l'interface de la V1, ligne de commande et rapport HTML : c'est là que la conformité doit être établie, critère par critère.

## Options envisagées

### Option A — Grille des critères et passage d'axe-core, hors de la CI (recommandée)

Une grille de chaque critère A et AA de WCAG 2.2, avec son résultat et la façon dont il a été vérifié, consignée dans `docs/verification/` ; un passage d'axe-core, version épinglée, installée par npm dans un dossier temporaire, hors du dépôt, sur des rapports réels ouverts dans le navigateur intégré.

- Avantages : chaque critère a un résultat écrit, y compris ceux qu'aucun outil ne juge (sens des alternatives, ordre de lecture) ; l'outil attrape ce que la relecture manque ; rien ne change dans la CI ni dans les dépendances du projet.
- Inconvénients : la vérification se refait à la main quand le rapport change ; axe-core ne voit que les rapports essayés.

### Option B — Grille seule

- Avantages : aucun téléchargement, aucun outil de plus.
- Inconvénients : la relecture seule laisse passer des défauts mécaniques (identifiants en double, noms de régions confondus, débordements).

### Option C — axe-core dans la CI

- Avantages : audit automatique à chaque PR.
- Inconvénients : Node et un navigateur sans tête dans un workflow ; le jeton `gh` du poste n'a pas la portée `workflow` et ne peut pas modifier `.github/workflows` ; une dépendance de développement de plus à surveiller (ADR-0052).

## Décision

Option A.

- La grille est [`docs/verification/accessibilite.md`](../verification/accessibilite.md) : pour chaque critère A et AA de WCAG 2.2, son résultat (conforme, non applicable) et sa méthode (outil, calcul, inspection, essai au clavier), avec la version d'axe-core, les rapports essayés et la procédure.
- axe-core s'exécute sur une **copie** de chaque rapport : la politique de sécurité du contenu (ADR-0094) y est retirée et le script ajouté, la page étant sinon identique. Le rapport publié, lui, reste sans script.
- La grille dit ce qu'un outil ne vérifie pas et qui a été vérifié autrement : contraste de chaque élément de texte calculé sur son fond réel, en mode clair et sombre ; refusion à 320 px ; espacement du texte de 1.4.12 ; taille des cibles ; ordre et visibilité du focus au clavier.
- Un défaut trouvé est corrigé dans T90 et la grille dit lequel.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant : elle donne un résultat écrit par critère, comme ADR-0024 le demande, et un contrôle mécanique, sans toucher à la CI.
- Option B écartée : le premier passage d'axe-core a trouvé un défaut que la relecture de T16 n'avait pas vu (deux régions du même nom, rubrique et tableau des observations).
- Option C écartée : coût d'outillage et d'entretien d'un navigateur dans la CI, impossible à poser depuis le poste, pour un rapport qui change peu.

## Conséquences

- NF-12 passe à l'état « réalisée » pour le rapport HTML et la ligne de commande de la V1 ; une interface web locale, après la V1, refera sa propre grille.
- Toute tâche qui change la structure ou la feuille de style du rapport doit repasser la grille, au moins les critères qu'elle touche, et le dire dans son journal.
- Un rapport d'un format ou d'un contenu non essayé peut porter un défaut que la grille n'a pas vu (texte d'une règle, visualisation nouvelle) : les tests de structure (`test_rapport.py`, `test_interface.py`) restent le garde-fou automatique.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
