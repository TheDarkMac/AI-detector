# ADR-0148 — Lecture des dates : quatre écritures, intervalles d'instants, ordre certain

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T23, validée pendant la revue de la PR de T23
- **Tâche** : T23
- **Exigences liées** : F-13, NF-06, NF-11 ; ES-03 ; ADR-0039, ADR-0118, ADR-0128, ADR-0133, ADR-0140, ADR-0147

## Contexte

Les modules observent les dates telles qu'écrites, et laissent leur interprétation à la règle qui les compare (ADR-0128, ADR-0133, ADR-0140) : fuseau absent, heure locale, champs omis, valeur réservée à une date inconnue. ADR-0147 donne à une condition une `lecture` ; restait à dire ce que chaque lecture accepte, et ce que veut dire « postérieure » entre deux dates imprécises.

Écritures vérifiées le 2026-11-13 :

- EXIF 3.0 (CIPA DC-008-2023), `DateTime`, `DateTimeOriginal`, `DateTimeDigitized` : `AAAA:MM:JJ HH:MM:SS`, heure locale ; une date inconnue a ses chiffres remplacés par des espaces ; l'usage écrit aussi des zéros. Le fuseau est dans d'autres étiquettes (`OffsetTime…`).
- PDF (ISO 32000, chaîne de date ; manuels de cpdf, Apryse, `DateTime::Format::PDF`) : `D:AAAAMMJJHHmmSSOHH'mm'`, où seuls les premiers champs sont obligatoires ; `O` vaut `+`, `-` ou `Z` ; sans fuseau, la relation à UTC est inconnue. Les logiciels écrivent l'apostrophe finale ou non, et parfois omettent `D:`.
- XMP (types de données Adobe), W3CDTF (OOXML), `xsd:dateTime` (ODF) : `AAAA`, `AAAA-MM`, `AAAA-MM-JJ`, `AAAA-MM-JJThh:mm`, `…:ss`, `…:ss.s`, suivis ou non d'un fuseau `Z` ou `±hh:mm`.
- ISO/IEC 14496-12, `mvhd` : entier, secondes depuis le 1904-01-01 à minuit UTC ; 0 non renseignée (ADR-0133).

## Options envisagées

### Option A — Intervalle d'instants, ordre certain

Une date lue est l'intervalle de tous les instants UTC qu'elle peut désigner : à la précision de son dernier champ écrit (jour, minute, seconde, fraction), et, sans fuseau, élargi de UTC-12 à UTC+14. Deux dates ne sont dans un ordre que si tous les instants de l'une précèdent tous ceux de l'autre.

- Avantages : aucune hypothèse sur le fuseau ni sur les champs omis ; une écriture imprécise ne fait jamais un constat ; une même règle s'applique aux dates avec et sans fuseau.
- Inconvénients : un écart de moins de 26 heures entre deux dates sans fuseau n'est jamais relevé.

### Option B — Instant unique, valeurs par défaut

Les champs omis prennent leur valeur par défaut (mois et jour 01, le reste 0, comme le dit la norme PDF), et une heure sans fuseau est lue en UTC.

- Avantages : relève tout écart, même d'une seconde.
- Inconvénients : faux constats pour un fichier qui écrit une date sans fuseau et l'autre avec ; une date de création `D:2026` serait antérieure à toute modification de 2026, ce que le fichier ne dit pas.

### Option C — Instant unique et marge fixe

L'option B, avec une marge fixe (24 h, par exemple) en deçà de laquelle l'écart n'est pas relevé.

- Avantages : simple à expliquer.
- Inconvénients : une marge arbitraire, trop grande pour deux dates à fuseau, trop petite pour deux dates à l'année près.

### Option D — Dates comparées aussi à la date de l'analyse

Relever aussi une date postérieure au jour de l'analyse.

- Avantages : une date future est impossible.
- Inconvénients : le même fichier, avec la même version de l'outil et du catalogue, donnerait des constats différents selon le jour (NF-06) ; une horloge en avance de quelques heures la produit.

## Décision

Option A, sans l'option D.

- Lecture (`_dates.py`) : une valeur donne une date (son intervalle), ou l'un de trois états : **impossible** (l'écriture est suivie, mais un champ est hors de son domaine : mois 13, 30 février, heure 25, minute 60, seconde 61, fuseau au-delà de 23:59) ; **non renseignée** (EXIF à espaces ou à zéros, `mvhd` à 0) ; **non reconnue** (toute autre valeur). Seule une date est comparée ; seul l'état « impossible » satisfait le test `impossible`.
- Précisions : `24:00:00` est la fin du jour et la seconde 60 une seconde intercalaire (ISO 8601) ; l'an 0 n'est pas reconnu ; une fraction au-delà de la microseconde est coupée, et l'intervalle la couvre ; une date sans heure couvre son jour dans tous les fuseaux, même suivie d'un fuseau.
- PDF : `D:` facultatif, apostrophes facultatives, `Z00'00'` admis ; une heure sans minute est lue à l'heure près.
- EXIF : les étiquettes `OffsetTime…` ne sont pas lues ; chaque date EXIF est prise sans fuseau.
- Aucune comparaison à la date de l'analyse.

## Raisons

- Option A : une incohérence relevée doit être certaine au vu de ce que le fichier écrit ; la règle dit qu'une des deux dates au moins est inexacte, ce qui n'est vrai que si aucun fuseau ni aucune précision ne les réconcilie.
- Option B écartée : elle tire un constat d'une hypothèse de l'outil (fuseau UTC, champs par défaut), pas du fichier.
- Option C écartée : la marge juste dépend de la précision et du fuseau de chaque date ; l'intervalle la calcule au lieu de la fixer.
- Option D écartée : NF-06.
- `OffsetTime…` non lues : leur prise en compte demanderait une condition sur trois observations ; la date reste lue sans fuseau, plus large, donc sans faux constat.

## Conséquences

- Les règles de T23 disent, dans leurs limites, qu'un écart de moins de 26 heures entre deux dates sans fuseau n'est pas relevé, et qu'une date non reconnue n'est pas comparée.
- `tests/test_dates.py` éprouve chaque écriture, chaque état et les bornes ; la lecture est mise en cache par valeur, en distinguant `True` de `1` (ADR-0089).
- Une nouvelle écriture (ns depuis 2001 de Matroska, texte ID3) est une nouvelle valeur de `lecture`, donc un changement du format 2 qui se fait dans le code et le schéma (ADR-0085).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
| 2026-11-13 | Validé par TheDarkMac pendant la revue de la PR de T23 (« Yes, all three ») : statut « Accepté » |
