# ADR-0118 — Valeurs tirées du fichier : types, textes et listes coupés, données binaires

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T20, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : F-10, NF-03, NF-06 ; ES-03, ES-04 ; ADR-0054, ADR-0058, ADR-0078

## Contexte

Une observation porte un texte d'au plus 4 096 caractères, un nombre fini borné, un booléen, ou une liste d'au plus 4 096 de ceux-ci (ADR-0054) ; une ligne du protocole ne dépasse pas 1 Mio (ADR-0078). Les métadonnées dépassent souvent ces formes : flux de travail JSON de dizaines de milliers de caractères dans un bloc texte PNG, tableaux TIFF de milliers d'entiers, MakerNote binaire, fractions de dénominateur nul, réels non finis. Sans règle commune, une valeur hors forme fait lever le modèle dans le module : erreur du module, et toutes ses observations perdues (ADR-0060).

## Options envisagées

### Option A — Couper, et dire la longueur entière

- Avantages : l'observation reste valide ; le rapport dit qu'elle a été coupée et de combien ; une règle peut tester la longueur.
- Inconvénients : une règle ne voit que le début d'un long texte.

### Option B — Découper un long texte en plusieurs observations

- Avantages : rien n'est perdu.
- Inconvénients : une ligne et une validation de plus par morceau, jusqu'à la limite de la sortie ; une règle ne peut pas chercher un motif à cheval sur deux morceaux.

### Option C — Ne pas observer ce qui dépasse

- Avantages : le plus simple.
- Inconvénients : un champ disparaît du rapport sans trace.

## Décision

Option A, dans `modules/_lecture/valeurs.py` :

- **Texte** : au plus 4 096 caractères ; au-delà, le début, et l'observation `<nom>.longueur` (unité « caractères »).
- **Liste** : au plus 4 096 éléments et 32 768 caractères en tout, chaque texte coupé à 4 096 ; si un élément ou un caractère manque, `<nom>.longueur` (unité « éléments ») donne le nombre d'éléments entier.
- **Nombre** : entier tel quel ; fraction TIFF rendue par sa valeur réelle, ou en texte `n/0` si son dénominateur est nul ; réel non fini ou hors des bornes du modèle rendu en texte (`nan`, `1e+300`).
- **Binaire** : données qui ne sont pas du texte ni des nombres (MakerNote, profil ICC, paquet logé dans TIFF, vignette IIM, octets indéfinis inconnus) observées par leur seule taille, `<nom>.taille`, unité « octets ».
- **Texte décodé** : UTF-8 s'il est valide, Latin-1 sinon, sauf quand le format fixe l'encodage (`tEXt` et `zTXt` en Latin-1, `iTXt` en UTF-8, IIM qui déclare UTF-8, UTF-16 des étiquettes `XP…`) ; un octet invalide devient le caractère de remplacement là où l'encodage est fixé.

## Raisons

- Option A : une valeur hors forme ne fait plus perdre le module ; la coupure est visible et mesurée.
- Option B écartée : coût de validation par ligne (ADR-0121) et motifs coupés.
- Option C écartée : contraire à l'explicabilité (P-02) ; un champ absent du rapport ne peut pas être vérifié.
- 32 768 caractères par liste : une observation tient dans une ligne de 1 Mio même si chaque caractère devient six octets d'échappement JSON.
- UTF-8, puis Latin-1 : aucun octet perdu, et le même fichier donne toujours le même texte (NF-06).
- Taille des données binaires plutôt que leur contenu en hexadécimal : le rapport n'a pas à porter des Mio de données illisibles ; la taille suffit à dire qu'elles existent.

## Conséquences

- Les signatures de T22 qui cherchent un motif dans un long texte (paramètres de génération) ne voient que ses 4 096 premiers caractères ; la fiche `metadonnees-texte-png` le signale. À revoir avec T22 si une signature en a besoin.
- Une règle peut tester `<nom>.longueur` ou `<nom>.taille` par un seuil.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
