# ADR-0215 — Mesure des textes d'une page : largeurs déclarées, montée et descente de la police ; 14 polices standard par les fichiers AFM d'Adobe

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T51, validée pendant la revue de la PR
- **Tâche** : T51
- **Exigences liées** : F-61, NF-06, ES-15 ; ADR-0079, ADR-0213, ADR-0214

## Contexte

Les recouvrements d'ADR-0214 se calculent sur la boîte de chaque texte dans l'espace de la page. Sa largeur est la somme des avancées de ses glyphes (§9.4.4), d'après les largeurs que déclare la police ; sa hauteur, celle de la police. Une police simple déclare ses largeurs (`/Widths`) ; une police composite aussi (`/W`, `/DW`), mais ses codes ne se découpent qu'avec son CMap. Les 14 polices standard (§9.6.2.2), non incorporées, pouvaient avant PDF 1.5 ne déclarer aucune largeur : le lecteur prend alors celles de ses propres polices. C'est le cas d'un texte ajouté en Helvetica non incorporée, sans largeurs, comme dans les échantillons de retouche de T51 : justement celui qu'il faut voir. Rien ne peut être lu sur le disque après les restrictions (ADR-0079).

## Options envisagées

### Option A — Largeurs déclarées ; AFM d'Adobe pour les 14 polices standard (recommandée)

Les largeurs de la police ; pour une police standard sans largeurs, celles des fichiers AFM d'Adobe, livrées avec le module, par l'encodage de la police (StandardEncoding, WinAnsiEncoding, MacRomanEncoding, `/Differences`). Hauteur : `/Ascent` et `/Descent` du descripteur, l'AFM pour une police standard, 0,8 et -0,2 cadratin à défaut.

- Avantages : boîtes exactes pour les textes d'un outil de retouche ; mêmes boîtes que Poppler, qui emploie aussi montée et descente.
- Inconvénients : environ 65 Ko de données tirées des AFM, livrées avec leurs mentions d'Adobe ; un générateur à garder.

### Option B — Largeur moyenne pour une police sans largeurs

Un demi-cadratin par glyphe, ou la largeur moyenne de la police.

- Avantages : aucune donnée à livrer.
- Inconvénients : des boîtes fausses du simple au double (en Helvetica, un « i » avance de 222 millièmes, un « m » de 833) : des textes voisins posés glyphe par glyphe se recouvriraient, et un texte ajouté serait mal placé.

### Option C — Textes sans largeurs non mesurés

- Avantages : aucune approximation.
- Inconvénients : le texte d'un outil de retouche en Helvetica non incorporée, le cas courant, ne serait jamais comparé.

## Décision

Option A, proposée par l'assistant, validée par TheDarkMac pendant la revue de la PR.

- `modules/pagespdf/_polices14.py`, écrit par `tests/donnees/pages/generer_polices14.py` à partir des fichiers AFM du paquet Debian `python-matplotlib-data` (téléchargés chez Adobe par Matplotlib) et de la liste des glyphes d'Adobe de fontTools 4.57.0 ; il garde les mentions de copyright des AFM et reproduit sans changement les conditions d'Adobe, qui permettent d'employer, copier et distribuer ces fichiers, modifiés ou non, si les mentions sont gardées et les modifications signalées (seuls la montée, la descente et la largeur arrondie de chaque glyphe sont gardés, ce que le fichier dit en tête).
- Codes d'une police simple sur un octet ; d'une police composite sur deux, avec le CMap Identity-H seul ; un autre CMap ou l'écriture verticale laissent le texte non mesuré.
- Largeur d'un code sans largeur déclarée : `/MissingWidth` (0 à défaut) pour une police simple, `/DW` (1 000 à défaut) pour une composite ; une police non standard sans largeurs n'est pas mesurée.
- Police Type3 : largeurs par `/FontMatrix`, hauteur par `/FontBBox`.
- Avancée : largeur × taille, plus `Tc`, plus `Tw` pour le code 32 d'une police simple, le tout × `Tz` ; ajustements de `TJ` en millièmes de la taille. Boîte transformée par la matrice du texte et la matrice courante, puis alignée sur les axes ; hors de ±10⁷ unités, ou pour un coefficient au-delà de 10⁶, non mesurée.

## Raisons

- Proposition de l'assistant, non posée en question : elle découle du choix d'ADR-0214, qui exige des boîtes fiables.
- B écartée : les faux recouvrements qu'elle crée rendraient R-PAGESPDF-001 inutilisable.
- C écartée : elle manque le cas que F-61 vise d'abord.
- Données d'Adobe plutôt que des polices d'URW (Nimbus, qui reprennent leurs largeurs) : les AFM d'Adobe sont la référence que cite la norme pour les 14 polices standard, et leurs conditions sont plus simples à respecter que la licence AGPL-3 des polices d'URW du poste (paquet Debian `fonts-urw-base35`).

## Conséquences

- Vérifié contre `pdftotext -bbox` de Poppler 25.03.0 : chaque mot de largeur non nulle des échantillons est couvert au moins à 90 % par un texte du module, à moins d'un demi-point près en hauteur.
- Les noms des polices standard sont pris tels quels : `Arial`, `TimesNewRoman` ou `Helvetica,Bold` ne sont pas rapprochés des polices standard, et leurs textes sans largeurs ne sont pas mesurés.
- Régénérer `_polices14.py` ne change rien tant que les AFM et l'AGL ne changent pas ; un test vérifie quelques largeurs relevées à la main.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création, statut « Proposé » ; proposée par l'assistant pendant T51 |
| 2026-11-17 | Validé par TheDarkMac pendant la revue de la PR (« Oui, valide ADR-0215 ») : statut « Accepté » |
| 2026-11-19 | Renvoi : la lecture des polices et les tables des 14 polices standard passent, sans changement, dans `_lecture/polices.py` et `_lecture/_polices14.py`, partagés avec `caracteres` ([ADR-0243](ADR-0243-couche-texte-d-un-pdf-dans-le-module-caracteres.md)) (complément de T53) |
