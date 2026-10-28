# ADR-0094 — Rapport HTML écrit par la bibliothèque standard, sans script, sous politique stricte

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T16
- **Exigences liées** : F-83, NF-12, NF-16 ; ES-12 ; menaces M-20, M-21 ; ADR-0025, ADR-0043

## Contexte

Le rapport HTML est autonome : il ne charge aucune ressource externe (ADR-0025). Il contient des textes tirés d'un fichier peut-être hostile (valeurs d'observations, nom du fichier) : M-20 est l'injection d'un script ou d'une balise de pistage par ces textes. L'architecture laissait à T16 le gabarit HTML et le moyen d'échappement (§12).

## Options envisagées

### Option A — Bibliothèque standard

Le document est écrit en Python ; chaque texte y entre par une seule fonction, qui neutralise les caractères invisibles (ADR-0096) puis échappe le HTML (`html.escape`). Aucun script ; politique de sécurité du contenu qui n'autorise que la feuille de style du document.

- Avantages : aucune dépendance nouvelle (ADR-0043) ; un seul point d'entrée du texte, facile à relire et à tester.
- Inconvénients : la structure du document est dans le code, moins lisible qu'un gabarit.

### Option B — Jinja2 avec échappement automatique

- Avantages : gabarits HTML séparés du code, échappement par défaut.
- Inconvénients : deux dépendances (Jinja2, MarkupSafe) à admettre et surveiller ; l'échappement automatique ne neutralise pas les caractères bidirectionnels ; un filtre `|safe` oublié suffit à rouvrir M-20.

## Décision

Option A.

- `rapport/_html.py` écrit le document. Tout texte passe par `_t()` : neutralisation, puis `html.escape(…, quote=True)`. Seules les balises écrites par ce module sont du HTML ; les attributs sont des constantes du module.
- Aucun élément `script`, `img`, `link`, `iframe`, `object`, `embed`, `form` ou `base` ; aucun gestionnaire d'événement ; les seuls liens sont des ancres internes (`#…`).
- Politique de sécurité du contenu, en `<meta http-equiv>` placée avant tout contenu : `default-src 'none'; style-src 'sha256-…'; base-uri 'none'; form-action 'none'`, où l'empreinte est celle de l'unique feuille de style du document. `<meta name="referrer" content="no-referrer">`.
- Accessibilité visée WCAG 2.2 AA (ADR-0025) : `lang="fr"`, un seul titre de niveau 1, rubriques en titres de niveau 2, tableaux avec légende et en-têtes de colonne, régions défilantes atteignables au clavier, lien d'évitement, focus visible, contraste du texte d'au moins 7:1 et des traits d'au moins 3:1, en mode clair comme en mode sombre (calculés pour chaque couple de couleurs de la feuille de style : texte de 7,2:1 à 17,2:1, traits de 5,3:1 à 8,8:1), aucune information portée par la couleur seule, mise en page imprimable.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : deux dépendances pour un document dont la structure est fixe, et un échappement qui ne couvre pas M-21.
- Politique par empreinte plutôt que `'unsafe-inline'` : une balise `style` injectée malgré l'échappement ne serait pas appliquée.
- `<meta>` plutôt qu'en-tête HTTP : le rapport est un fichier ouvert localement, sans serveur.

## Conséquences

- La conformité WCAG est vérifiée par inspection et démonstration (ADR-0024) ; les tests vérifient la structure (titres, légendes, ancres) et l'absence de toute ressource externe.
- Un test de fuzzing (ES-19, ADR-0082) vérifie qu'aucune valeur ne crée de balise ni d'attribut.
- Les visualisations (F-84) arriveront avec leurs techniques ; une image devra être intégrée au document (`data:`), ce qui demandera d'ajouter `img-src data:` à la politique, par un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
