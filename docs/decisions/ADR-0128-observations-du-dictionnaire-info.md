# ADR-0128 — Observations du dictionnaire Info : noms, dates telles qu'écrites, formes des valeurs

- **Statut** : Accepté
- **Date** : 2026-11-12
- **Décideur** : proposition de l'assistant, validée par TheDarkMac
- **Tâche** : T21
- **Exigences liées** : F-10, F-14, ES-13, NF-06, NF-11 ; ADR-0057, ADR-0117, ADR-0118, ADR-0119

## Contexte

ADR-0117 et ADR-0118 fixent les noms et les valeurs des métadonnées d'image. Le dictionnaire d'information d'un PDF (ISO 32000-2, §14.3.3) a ses propres formes : chaînes de texte en PDFDocEncoding, UTF-16BE ou UTF-8 (selon leur marque d'ordre), dates `D:AAAAMMJJHHmmSS+HH'mm'`, noms (`/Trapped /True`), et, chez certains logiciels, des clés à eux, des tableaux, des dictionnaires imbriqués ou des flux.

## Options envisagées

### Option A — Noms de la norme, dates telles qu'écrites

- `infopdf.present` toujours observé ; `infopdf.chiffre` dès que la table des références croisées se lit ;
- `infopdf.<clé>` pour chaque entrée, la clé passée par la règle des composants d'ADR-0117 (`/Cle#20propre` devient `infopdf.Cle-propre`) ;
- chaîne décodée selon §7.9.2.2, caractère de remplacement pour un code non défini ; nom sans sa barre oblique ; nombre et booléen tels quels ; objet nul : entrée absente ;
- date : la chaîne telle qu'écrite, sans conversion ;
- tableau : liste de ses valeurs, après résolution des références ; un tableau qui contient un tableau, un dictionnaire ou un objet nul est non mené (`format_partiel`) ;
- dictionnaire imbriqué : ses entrées sous `infopdf.<clé>.<sous-clé>` ; un dictionnaire qui se contient lui-même est non mené ;
- flux : sa taille seule, `infopdf.<clé>.taille` (ADR-0118) ;
- `Author` marqué `metadonnee_nominative` (ADR-0119).

- Avantages : la valeur observée est celle du fichier, retrouvable à sa localisation (P-02) ; la règle qui comparera deux dates (T23) les lira toutes de la même façon ; aucune perte, aucune heuristique de fuseau.
- Inconvénients : une date n'est pas directement comparable à une date XMP (ISO 8601) sans conversion par la règle.

### Option B — Dates converties en ISO 8601

- Avantages : comparables d'emblée aux dates XMP et EXIF.
- Inconvénients : une date mal formée devrait être soit rejetée soit devinée ; la conversion est un choix d'interprétation (heure locale, fuseau absent) qui revient à T23, où il sera documenté avec la règle qui l'emploie.

## Décision

Option A.

## Raisons

- Option A : même principe qu'ADR-0118 (la valeur du fichier, ramenée à ce que le modèle admet) ; un vérificateur reconnaît la date qu'il voit dans d'autres outils PDF.
- Option B écartée : interprétation prématurée, qui appartient à la règle d'incohérence de dates (T23).
- `Title` non marqué : il porte souvent le nom du fichier source (« Microsoft Word - rapport.docx »), mais aussi un vrai titre ; le marquer masquerait le cas courant. La liste de garde des textes libres reste à T25 (ADR-0119), et la fiche signale ce cas.
- `infopdf.chiffre` observé : l'absence de dictionnaire lu doit se distinguer de l'absence de dictionnaire (F-14).

## Conséquences

- La fiche `metadonnees-info-pdf` liste ces noms et formes.
- T23 convertira les dates PDF dans la règle qui les compare, et documentera son interprétation.
- T25 décidera du marquage de `Title`, `Subject` et `Keywords` avec la liste de garde.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création, statut « Proposé » |
| 2026-11-13 | Validé par TheDarkMac pendant la revue de la PR de T21 : statut « Accepté » |
