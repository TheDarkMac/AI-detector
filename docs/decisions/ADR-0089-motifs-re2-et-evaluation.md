# ADR-0089 — Motifs RE2 admis et évaluation des conditions

- **Statut** : Proposé
- **Date** : 2026-10-27
- **Décideur** : l'assistant, proposition non posée en question pendant T15, soumise dans la PR de T15
- **Tâche** : T15
- **Exigences liées** : F-12, NF-02, NF-06, NF-08 ; ES-09 ; M-03, M-12 ; ADR-0039, ADR-0076, ADR-0078, ADR-0084

## Contexte

ADR-0039 confie les motifs du catalogue à RE2 et laisse à T15 la syntaxe admise et la vérification au chargement. ADR-0084 fixe les tests d'une condition ; il restait à dire exactement comment une condition est satisfaite, quelles observations un constat cite, et dans quel ordre, pour que deux analyses donnent les mêmes constats (NF-06).

## Options envisagées

### Syntaxe des motifs

- **A — Syntaxe RE2 entière, bornée** : RE2 exclut déjà ce qui coûte (références arrière, assertions de contexte) ; on borne la longueur, la mémoire et la taille du programme compilé.
- **B — Sous-ensemble plus étroit** (pas de classes Unicode, pas de répétitions bornées) : plus prévisible, mais prive d'expressions utiles à des noms de logiciels.

### Portée d'un motif

- **A — Recherche n'importe où** (`search`), `^` et `$` pour ancrer : l'usage courant des expressions régulières.
- **B — Correspondance du texte entier** (`fullmatch`) : plus strict, mais un oubli de `.*` fait taire une règle sans erreur.

### Observations retenues

- **A — La première qui satisfait chaque condition**, dans l'ordre où le module les a produites ; un constat par règle, par module et par partie.
- **B — Toutes celles qui satisfont** : un constat plus lourd, sans information de plus pour une signature.
- **C — Un constat par observation** : plusieurs constats identiques pour un même fait, qui gonflent le décompte du résumé (ADR-0018).

## Décision

Option A dans les trois cas.

- Motif : syntaxe RE2, compilé avec `log_errors` désactivé (RE2 écrirait sinon sur la sortie d'erreur de l'utilisateur), `never_capture`, mémoire de 8 Mio (`MEMOIRE_MAX_MOTIF`, la valeur par défaut, écrite pour ne pas dépendre de la version de RE2) ; au plus 1 024 caractères ; programme compilé d'au plus 5 000 instructions (`PROGRAMME_MAX_MOTIF`). Un motif refusé par RE2 ou trop grand rend le catalogue invalide. Il est compilé par le processus principal au chargement, puis de nouveau par le processus de travail à la lecture de la configuration ; seul ce dernier l'applique (ADR-0039).
- Comparaisons : un booléen n'est égal qu'à un booléen, un texte qu'à un texte ; un entier et un réel de même valeur sont égaux. `motif` ne vaut que pour un texte, `seuil` que pour un nombre qui n'est pas un booléen. Une observation dont la valeur est une liste satisfait la condition si l'un de ses éléments la satisfait ; `presente` est satisfaite par toute observation du nom donné.
- Évaluation : après le module, sur chaque partie, le moteur prend les règles « moteur » du module dans l'ordre de leurs identifiants ; pour chaque condition, il retient la première observation qui la satisfait ; si toutes les conditions le sont, il produit un constat dont les données sont les observations retenues (sans doublon) et les paramètres ceux nommés par les conditions. Ce constat n'a pas de localisation : ses observations portent la leur.
- Les constats du moteur suivent ceux du module et comptent contre son budget (ADR-0078) : un dépassement rend le module non mené pour `limite_depassee`, comme s'il l'avait dépassé lui-même.

## Raisons

- Syntaxe A : ES-09 est tenue par RE2 lui-même ; les bornes de longueur, de mémoire et de programme ferment ce que RE2 laisse ouvert (un motif énorme). B écartée : elle appauvrit F-12 sans gain de sûreté.
- Portée A : la convention que connaissent les auteurs de règles ; B écartée pour ses silences.
- Observations A : déterministe et suffisant pour dire « ce champ vaut ceci » ; B et C écartées, la seconde parce qu'elle fausserait les nombres du résumé.
- Comparaison stricte des types : Python tient `True == 1` ; une règle sur un booléen ne doit pas se déclencher sur un compteur.
- 5 000 instructions : une classe Unicode comme `\pL` en compte environ 1 200, une répétition bornée de 1 000 un peu plus de 1 000 ; deux mesures faites sur le poste avec RE2 1.1.20251105.

## Conséquences

- Coût mesuré sur le poste : 1 000 règles à motif construites en 144 ms ; le catalogue livré, sans règle, chargé en 1,4 ms ; import de RE2, 20 ms, dans les deux processus.
- Un module qui veut une règle sur toutes les occurrences d'un champ produit une observation par occurrence et compte sur la première, ou écrit une règle « module ».

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
