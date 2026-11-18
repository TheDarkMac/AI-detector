# ADR-0242 — Texte masqué par la mise en forme : analysé, compté, une information neutre ; versions du complément de T80

- **Statut** : Accepté
- **Date** : 2026-11-18
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (éléments lus, règle et versions précisés par l'assistant)
- **Tâche** : T80 (complément bureautique)
- **Exigences liées** : F-73, F-80, F-81 ; A-43 ; ADR-0152, ADR-0237, ADR-0239

## Contexte

Un DOCX ou un ODT peut porter du texte que sa mise en forme cache : l'attribut « masqué » d'une course d'un DOCX (`w:vanish`), un style d'ODT dont les propriétés de texte ont `text:display="none"`. Ce texte est dans le fichier ; un programme qui en lit le texte, un modèle de langage par exemple, le lit sans qu'un lecteur le voie.

## Options envisagées

### Option A — Analysé et compté à part (recommandée)

Le texte masqué est analysé, ses positions disent qu'il est masqué, et son nombre de caractères est observé, avec une information neutre.

- Avantages : le rapport dit qu'un texte ne s'affiche pas, et ce qu'il porte.
- Inconvénients : des modèles de documents masquent des aides à la saisie : la règle se déclenche sur eux.

### Option B — Analysé, sans le distinguer

- Avantages : plus simple.
- Inconvénients : le rapport ne dit pas que le texte est masqué.

### Option C — Laissé de côté

- Avantages : le complément ne lit que le texte affiché.
- Inconvénients : un endroit où cacher, renvoyé à plus tard.

## Décision

Option A. Précisions de l'assistant :

- DOCX : est masquée une course (`w:r`) dont les propriétés (`w:rPr`) portent `w:vanish`, sauf `w:val` à `0`, `false` ou `off` ; la mise en forme d'un style ne l'est pas (lue par le logiciel, pas par le module), ni la marque de paragraphe (`w:pPr/w:rPr`).
- ODT : est masqué le texte d'un paragraphe ou d'une portion (`text:style-name`) dont le style a `text:display="none"`, style automatique de sa partie ou style commun de `styles.xml` (`office:styles`), sans ses styles parents.
- Règle R-CARACTERES-013 : `caracteres.masques` au moins 1, information neutre, direction « rien de particulier », fondement « vérification déterministe », seuil par définition.

| Élément | Version |
| --- | --- |
| Module `caracteres` | 0.2.0 : formats `texte`, `docx`, `odt` ; bibliothèque `expat` ; exigences et direction inchangées |
| Catalogue | 0.17.0 (`Y` : règle ajoutée, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.11.0, inchangés |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : le lecteur doit savoir qu'un texte ne s'affiche pas.
- Option C écartée : laisserait un endroit où cacher une consigne.
- Information neutre : rien ne dit pourquoi le texte est masqué (A-43).

## Conséquences

- Un texte blanc sur blanc, minuscule ou hors de la page n'est pas masqué au sens de la mise en forme : limite de la règle.
- La part de documents ordinaires qui déclenchent R-CARACTERES-013 se mesurera sur le corpus de référence (T100).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-18 | Création ; option choisie par TheDarkMac au début du complément de T80 |
