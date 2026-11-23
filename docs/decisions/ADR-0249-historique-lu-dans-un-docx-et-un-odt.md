# ADR-0249 — Historique lu dans un DOCX et dans un ODT : temps, enregistrements, sessions, modifications, commentaires

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : proposition de l'assistant, dans le cadre de l'option choisie par TheDarkMac ([ADR-0248](ADR-0248-module-historique-et-perimetre-de-t81.md))
- **Tâche** : T81
- **Exigences liées** : F-71 ; ADR-0139, ADR-0140, ADR-0148, ADR-0240

## Contexte

TheDarkMac a choisi un module `historique` qui lit, pour son propre compte, temps d'édition, enregistrements, sessions, modifications suivies et commentaires (ADR-0248). Il fallait dire où chaque donnée est lue, comment les sessions se rattachent au texte, et ce qui n'est pas lu. Deux constats de l'assistant, en préparant T81, ont pesé :

- LibreOffice 25.2.3.2 marque chaque passage tapé par l'interface de l'identifiant de la session (`officeooo:rsid` d'un style automatique de `content.xml`), une session par ouverture ; il n'en écrit aucun quand le texte arrive par l'API (`insertString`), ni dans un DOCX qu'il exporte. Vérifié sur un document écrit en trois sessions (`tests/donnees/historique`).
- Dans un DOCX, LibreOffice écrit la fin d'un paragraphe inséré comme une marque de révision à part (`w:ins` sous `w:pPr/w:rPr`), avec son propre identifiant ; il relit pourtant une seule modification.

## Options envisagées

### Option A — Les parties où les logiciels écrivent l'historique, le corps rangé par session (retenue)

Propriétés de temps et d'enregistrements ; identifiants de session des réglages (DOCX) ou des styles automatiques (ODT) ; caractères du texte visible du corps, rangés par session ; marques de révision du corps et commentaires.

- Avantages : chaque donnée est lue là où Word et LibreOffice l'écrivent ; la part du texte écrite dans une session dit plus que le seul nombre de sessions.
- Inconvénients : le corps entier est parcouru.

### Option B — Les nombres déclarés seuls

Temps, enregistrements, nombre de sessions déclarées, sans lire le corps.

- Avantages : plus court ; ni le corps ni ses marques ne sont parcourus.
- Inconvénients : ni modifications suivies, ni part du texte par session ; un réglage hérité d'un modèle compterait des sessions que le texte ne porte pas.

### Option C — Tout le document

Aussi en-têtes, pieds de page, notes, `settings.xml` de LibreOffice, versions enregistrées d'un ODT.

- Avantages : couverture plus large.
- Inconvénients : le texte de ces parties pèse peu dans l'écriture d'un document ; les versions enregistrées sont rares et demandent de lire des documents entiers rangés dans l'archive.

## Décision

Option A, précisions de l'assistant :

| Donnée | DOCX | ODT |
| --- | --- | --- |
| Temps d'édition | `TotalTime` des propriétés étendues, en minutes | `meta:editing-duration`, durée `xsd:duration` ramenée en minutes entières ; une durée qui compte des années ou des mois n'est pas lue |
| Enregistrements | `cp:revision` des propriétés principales | `meta:editing-cycles` |
| Sessions déclarées | Identifiants distincts de `w:rsids` de `word/settings.xml`, racine comprise, sans la casse | Identifiants distincts des `officeooo:rsid` et `officeooo:paragraph-rsid` des styles automatiques de `content.xml` |
| Session d'un caractère | Celle de sa course (`w:rsidR`), sinon la session par défaut de son paragraphe (`w:rsidRDefault`) | Celle de sa portion (`text:span`), sinon de son paragraphe, d'après leurs styles automatiques |
| Texte rangé par session | `w:t` de `word/document.xml`, hors `w:del` et `w:moveFrom` | Paragraphes et titres de `office:text`, hors `text:tracked-changes`, `text:note`, `office:annotation` et descriptions d'images |
| Modifications suivies | Marques de révision du corps : `w:ins`, `w:del`, `w:moveFrom`, `w:moveTo`, et les changements de propriétés, de tableau et de numérotation | Régions `text:changed-region` |
| Commentaires | `w:comment` de la partie des commentaires | `office:annotation` du corps |
| Création, enregistrement | `dcterms:created`, `dcterms:modified` | `meta:creation-date`, `dc:date` |

- Les parties d'un DOCX sont trouvées par les relations du paquet et de la partie principale, comme les trouve le logiciel (ADR-0139) ; une partie désignée et absente est une référence manquante, une partie mal formée un format partiel, et ce qui a été lu avant l'arrêt est gardé.
- Une valeur qui n'est pas un entier positif ou nul en chiffres (au plus 18) n'est pas observée ; la première valeur d'une propriété répétée l'emporte.
- La part de la session la plus représentée est en pour cent, arrondie au-dessous, sur les seuls caractères qui ont une session ; les caractères sans session sont comptés à part.
- Une modification se compte en marques, comme l'écrit le fichier : la fin de paragraphe insérée en est une. Une réponse à un commentaire en est un.
- L'écart entre création et dernier enregistrement est le plus grand que permettent les deux dates, lues comme le fait T23 (ADR-0148), arrondi à la minute supérieure ; il n'est pas observé quand la création suit certainement l'enregistrement, ce que dit déjà une règle de T23.
- Ne sont pas lus : en-têtes, pieds de page et notes d'un DOCX ; `styles.xml` et `settings.xml` d'un ODT ; les versions enregistrées (`VersionList.xml`) ; le texte des commentaires (que lit le module `caracteres`).

## Raisons

- Option A : elle lit ce que F-71 demande, là où les logiciels l'écrivent, et rattache les sessions au texte, sans quoi une session ne dit rien de ce qui a été écrit.
- Option B écartée : laisserait les modifications suivies, renvoyées à T81 (ADR-0013, ADR-0139, ADR-0240), sans lecteur.
- Option C écartée : apport faible pour un coût réel ; les versions enregistrées sont signalées en limite.
- Marques plutôt que modifications logiques : regrouper les marques demanderait de deviner ce que le logiciel regroupe ; la phrase du constat dit « marques ».

## Conséquences

- Un DOCX exporté par LibreOffice n'a pas de sessions : son texte est compté sans session.
- Le corps est parcouru en entier : un document trop grand pour le budget du module (ES-03) n'est pas analysé.
- Lire une partie de plus demandera un nouvel ADR et une nouvelle version du module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création |
