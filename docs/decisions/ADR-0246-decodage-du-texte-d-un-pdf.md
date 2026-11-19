# ADR-0246 — Texte des codes d'un PDF : `/ToUnicode`, puis Adobe Glyph List ; lignes dans l'ordre du flux

- **Statut** : Accepté
- **Date** : 2026-11-19
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (découpage, texte de remplacement, seuils et données précisés par l'assistant)
- **Tâche** : T53 (complément texte)
- **Exigences liées** : F-63, F-73, NF-06 ; ADR-0079, ADR-0215, ADR-0234, ADR-0243

## Contexte

Un texte de PDF est une suite de codes, dont la police dit le glyphe, pas toujours le caractère (ISO 32000-2, §9.10) : le CMap `/ToUnicode` le donne s'il est là ; sinon, une police simple donne le nom du glyphe de chaque code par son encodage, et l'Adobe Glyph List (AGL) traduit ces noms ; une police composite sans `/ToUnicode` ne le donne que par les CMap et collections prédéfinis des écritures chinoise, japonaise et coréenne. Les textes ne sont pas des lignes : les mots sont posés à des positions, souvent sans espace écrite.

## Options envisagées

### Option A — `/ToUnicode`, puis AGL ; lignes dans l'ordre du flux (recommandée)

`/ToUnicode` d'abord ; sinon, pour une police simple, le nom du glyphe par l'AGL. Un code sans texte n'est pas décodé : compté, jamais deviné. Textes dans l'ordre du flux de contenu, espaces et lignes tirées des positions, vérifiés contre `pdftotext -raw` de Poppler.

- Avantages : le texte qu'en copient les lecteurs, pour presque tous les PDF ; l'AGL est une donnée fixe, sous licence BSD.
- Inconvénients : une police composite sans `/ToUnicode` reste muette.

### Option B — `/ToUnicode` seul

- Avantages : pas de table de noms à livrer.
- Inconvénients : les PDF de logiciels anciens, et ceux qui emploient les 14 polices standard sans `/ToUnicode`, ne donneraient rien.

### Option C — Avec les CMap des écritures d'Asie de l'Est

Ajoute les CMap prédéfinis et les collections Adobe-Japan1, Adobe-GB1, Adobe-CNS1, Adobe-Korea1.

- Avantages : les polices composites sans `/ToUnicode` sont décodées.
- Inconvénients : bien plus de données à livrer et à vérifier.

## Décision

Option A. Précisions de l'assistant :

| Point | Ce qui est fait |
| --- | --- |
| Lecteur | `modules/_lecture/polices.py`, partagé avec `pagespdf` (ADR-0243) ; le texte d'un code se lit par `Polices.correspondance`, à part de ce que lit `pagespdf` |
| Découpage | Police simple : un octet ; composite : deux pour Identity-H et Identity-V ; sinon selon les plages de codes de son CMap incorporé, à défaut de son `/ToUnicode` (§9.7.6.2, octet par octet), deux à défaut ; des octets hors des plages font un code d'un octet |
| `/ToUnicode` | `begincodespacerange`, `beginbfchar`, `beginbfrange` (destination UTF-16BE, dont le dernier octet est augmenté pour chaque code, ou tableau), lus par l'analyseur des flux de contenu ; un code se cherche par sa longueur et sa valeur ; une destination qui est un nom de glyphe est traduite par l'AGL ; un CMap illisible est laissé de côté et déclaré non mené (`format_partiel`) |
| Encodage d'une police simple | Encodage de base nommé (StandardEncoding, WinAnsiEncoding, MacRomanEncoding) ; à défaut, celui de Symbol ou de ZapfDingbats, StandardEncoding pour une police non incorporée ou non symbolique (indicateurs du descripteur), aucun pour un programme symbolique ou une police Type3 ; puis `/Differences` |
| Nom de glyphe | Spécification de l'AGL, §2 : nom coupé au premier point, composants séparés par `_`, chacun traduit par l'ITC Zapf Dingbats Glyph List (police ZapfDingbats), l'AGL, `uniXXXX…` ou `uXXXX` à `uXXXXXX` (chiffres hexadécimaux capitales, hors moitiés de paires) ; un composant que l'AGL envoie dans l'usage privé (petites capitales, chiffres de style d'Adobe) n'est pas traduit |
| Texte de remplacement | Un contenu marqué (`BDC`) qui porte `/ActualText`, dans l'opération ou dans `/Properties`, remplace le texte des glyphes qu'il couvre, écrit une fois à la place du premier ; s'il n'en couvre aucun, il est écrit à sa fin ; le plus extérieur l'emporte (§14.9.4) |
| Lignes | Une espace avant un glyphe qui commence à plus de 0,1 cadratin de la fin du précédent, sur sa ligne (Poppler, `minWordBreakSpace`) ; une ligne quand il s'en écarte de plus de 0,5 cadratin perpendiculairement, recule de plus de 0,5 cadratin, ou change de direction ; le cadratin est la hauteur de la police dans l'espace de la page ; avancées des glyphes déclarées par la police, nulles si elles ne sont pas connues |
| Code non décodé | Compté (`caracteres.non_decodes`) ; rien dans le texte, sa position compte pour la suivante |
| Données | `_lecture/_glyphes.py` : AGL 2.0 (4 281 noms) et ITC Zapf Dingbats Glyph List (201 noms), écrits par `tests/donnees/caracteres/generer_glyphes.py` depuis la copie que fontTools 4.57.0 en livre, empreinte SHA-256 vérifiée ; notice BSD d'Adobe reproduite ; chargés à l'import (ADR-0079) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : trop de PDF ne donneraient aucun texte.
- Option C écartée : données hors de proportion pour la V1.
- Texte de remplacement suivi : c'est le texte que copient Poppler et les lecteurs, donc celui que lit un programme ; LibreOffice y écrit les caractères qu'aucun glyphe ne montre, comme les étiquettes Unicode.
- Usage privé de l'AGL laissé de côté : ces noms désignent des variantes de lettres ordinaires ; les traduire ferait relever des caractères à usage privé qu'aucun auteur n'a écrits.
- AGL prise dans fontTools : la même liste que le dépôt d'Adobe, sans téléchargement ; l'empreinte dit si elle change.

## Conséquences

- Les CMap prédéfinis des écritures d'Asie de l'Est ne sont pas livrés : limite de la fiche.
- L'ordre est celui du flux, pas celui de la lecture : deux colonnes peintes ligne à ligne s'entremêlent ; limite de la fiche.
- Échantillons et oracle : `tests/donnees/caracteres/generer_pdf.py` et `oracle_pdf.json` (Poppler 25.03.0).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-19 | Création ; option choisie par TheDarkMac au début du complément de T53 |
