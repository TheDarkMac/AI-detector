# ADR-0245 — Texte invisible d'un PDF (modes de rendu 3 et 7) : analysé, compté, une information neutre

- **Statut** : Accepté
- **Date** : 2026-11-19
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (règle précisée par l'assistant)
- **Tâche** : T53 (complément texte)
- **Exigences liées** : F-63, F-73, F-80, F-81 ; A-43 ; ADR-0017, ADR-0152, ADR-0242

## Contexte

Un PDF peut écrire un texte sans le peindre : modes de rendu 3 (ni remplissage ni contour) et 7 (ajouté au chemin de découpage) de l'opérateur `Tr` (ISO 32000-2, §9.3.6). C'est la couche de texte qu'un logiciel de reconnaissance de caractères pose sur l'image d'un document numérisé, pour la recherche et la copie ; c'est aussi un endroit où cacher un texte qu'un programme lira, un modèle de langage par exemple, sans qu'un lecteur le voie. `pagespdf` ne le pose ni ne le compte (ADR-0215).

## Options envisagées

### Option A — Analysé et compté à part (recommandée)

Le texte invisible est analysé, ses positions disent qu'il est invisible, son nombre de caractères est observé, avec une information neutre, comme le texte masqué d'un DOCX ou d'un ODT (ADR-0242).

- Avantages : le rapport dit qu'un texte n'est pas peint, et ce qu'il porte.
- Inconvénients : chaque document numérisé muni de sa couche de texte déclenche la règle.

### Option B — Analysé, sans le distinguer

- Avantages : plus simple.
- Inconvénients : le rapport ne dit pas que le texte n'est pas peint.

### Option C — Laissé de côté

- Avantages : seul le texte visible est lu.
- Inconvénients : un endroit où cacher une consigne, renvoyé à plus tard.

## Décision

Option A. Précisions de l'assistant :

- Est invisible un code montré quand le mode de rendu de l'état graphique est 3 ou 7 ; le mode suit l'état graphique (`q`, `Q`), y compris d'un objet texte au suivant. Les caractères qu'il donne sont comptés dans `caracteres.texte_invisible` ; une espace ajoutée entre deux textes ne l'est pas.
- Règle R-CARACTERES-014 : `caracteres.texte_invisible` au moins 1, information neutre, direction « rien de particulier », fondement « vérification déterministe », seuil par définition ; sa description et ses limites disent que la couche de texte d'un document numérisé la déclenche.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : le lecteur doit savoir qu'un texte n'est pas peint.
- Option C écartée : laisserait un endroit où cacher une consigne.
- Information neutre : rien ne dit pourquoi le texte est invisible (A-43), et l'emploi le plus courant est ordinaire.

## Conséquences

- Un texte blanc sur blanc, minuscule, caché sous une image ou hors de la page n'est pas invisible à ce sens : limite de la règle.
- La part de documents ordinaires qui déclenchent R-CARACTERES-014 se mesurera sur le corpus de référence (T100).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-19 | Création ; option choisie par TheDarkMac au début du complément de T53 |
