# ADR-0125 — Lecture stricte du PDF : rien n'est reconstruit, tolérances écrites

- **Statut** : Proposé
- **Date** : 2026-11-12
- **Décideur** : proposition de l'assistant, à valider par TheDarkMac
- **Tâche** : T21
- **Exigences liées** : F-10, F-82, NF-06, NF-14 ; principe P-02 ; ADR-0124

## Contexte

Beaucoup de PDF en circulation ne suivent pas la norme à la lettre : entrées de table de 19 ou 21 octets au lieu de 20, `stream` suivi d'un retour chariot seul, `endobj` manquant, table des références croisées fausse après une modification maladroite. Les lecteurs courants (Acrobat, `pypdf` en mode tolérant, Poppler) réparent en cherchant les objets dans le fichier. Le lecteur du projet (ADR-0124) doit choisir ce qu'il accepte, et dire le reste.

## Options envisagées

### Option A — Stricte, avec des tolérances écrites

Le lecteur suit la table et les longueurs déclarées. Il tolère seulement des écarts de forme qui ne changent pas l'objet lu : entrées de 19 ou 21 octets (fin de ligne d'un ou trois octets), retour chariot seul après `stream`, `endobj` absent, blancs avant `xref`, objet nul pour une référence absente ou libre (§7.3.10). Tout le reste arrête la lecture, et le module le dit : `format_partiel` si la structure est incohérente ou emploie ce que le lecteur ne sait pas lire, `fichier_tronque` si elle annonce plus d'octets que la partie n'en a.

- Avantages : ce qui est observé est ce que la structure déclare ; un document réparé autrement par un autre lecteur ne trompe pas l'outil sans qu'il le dise ; même fichier, même résultat (NF-06).
- Inconvénients : un PDF abîmé, que d'autres lecteurs ouvrent, n'a pas ses métadonnées au rapport.

### Option B — Reconstruction à la manière des lecteurs tolérants

En cas d'échec, chercher les motifs `n g obj` dans tout le fichier et refaire la table.

- Avantages : plus de PDF lus.
- Inconvénients : le résultat dépend d'heuristiques, pas de la structure ; un objet mort (remplacé par une mise à jour) peut être pris pour l'objet courant, ce qui fausse précisément les observations qu'un vérificateur lirait ; coût en temps sur un fichier de 1 Gio.

## Décision

Option A.

## Raisons

- Option A : une observation doit pouvoir être retrouvée dans le fichier à l'endroit que dit sa localisation (P-02) ; « non mené » est une réponse honnête (F-82), un objet deviné ne l'est pas (NF-14).
- Option B écartée : elle introduit des faux constats possibles dès que T22 et T23 liront ces observations, et elle anticipe T50, qui doit justement voir les sections et les objets remplacés tels qu'ils sont.

## Conséquences

- Les tolérances ci-dessus sont listées dans la fiche `metadonnees-info-pdf` ; les tests en couvrent chacune.
- Une longueur de flux inexacte n'est pas corrigée : le flux n'est pas lu.
- Le nombre de PDF abîmés non lus se mesurera sur le corpus (T100, T101) ; s'il est élevé, une reconstruction signalée comme telle pourra être reconsidérée par un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création, statut « Proposé » |
