# ADR-0235 — Homoglyphes : mots mêlés d'écritures confusables, d'après UTS #39 ; lettres de compatibilité à part ; information neutre

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (découpage des mots, écriture dominante et ensembles augmentés précisés par l'assistant)
- **Tâche** : T80
- **Exigences liées** : F-73, NF-06 ; A-43 ; ADR-0234

## Contexte

F-73 cite les homoglyphes : des caractères qui ressemblent à d'autres. Le cas courant est la substitution d'une lettre latine par sa jumelle cyrillique ou grecque (U+0430, un a cyrillique, pour U+0061, le a latin) : le mot s'affiche pareil, mais ne se trouve plus par une recherche ni par un contrôle de plagiat. Le rapport technique Unicode 39 (UTS #39, mécanismes de sécurité) publie les confusables (`confusables.txt`) : deux caractères confusables ont le même squelette. Un mot écrit tout entier dans une autre écriture (un mot russe) n'est pas une substitution ; le japonais mêle par nature kanji, hiragana et katakana.

## Options envisagées

### Option A — UTS #39, information neutre (recommandée)

Écritures (`Scripts.txt`) et confusables (`confusables.txt`) d'Unicode 18.0 : un mot à écriture dominante dont une lettre d'une autre écriture se confond avec une lettre de celle-ci. Mots entièrement cyrilliques ou grecs non comptés. Lettres de compatibilité (pleine chasse, variantes mathématiques) à part. Information neutre, rien de particulier : changement de disposition du clavier ou dissimulation, l'outil ne sait pas.

- Avantages : méthode publiée, données d'Unicode ; aucun mot d'une seule écriture n'est relevé, quelle que soit la langue.
- Inconvénients : un mot mêlé par une faute de frappe sur un clavier bilingue est relevé comme les autres.

### Option B — UTS #39, indice faible vers la transformation

- Avantages : le rapport dit qu'un mot mêlé est plus souvent fabriqué qu'accidentel.
- Inconvénients : aucune mesure ne fonde cette fréquence ; un indice se lit comme une accusation.

### Option C — Compatibilité seule

Les lettres que NFKC ramène à une autre, sans table d'écritures.

- Avantages : aucune donnée d'écriture.
- Inconvénients : ne voit pas le cyrillique mêlé au latin, cas le plus courant.

## Décision

Option A. Précisions de l'assistant :

- **Mot** : suite de caractères d'une écriture (ni Common ni Unknown), de marques combinantes (Inherited) et d'invisibles qui ne coupent pas un mot (sans chasse, sélecteurs) : un ZWSP (U+200B) glissé entre deux lettres d'un mot n'en fait pas deux mots.
- **Écriture dominante** : la plus fréquente parmi les lettres du mot ; à égalité, la première, dans l'ordre d'apparition, dont les autres lettres se confondent avec les siennes (un mot de deux lettres, un omicron grec U+03BF et un k latin : le k ne se confond avec aucune lettre grecque, l'omicron se confond avec le o latin, l'écriture dominante est le latin).
- **Lettre substituée** : lettre d'une autre écriture qui a le même squelette qu'un caractère de l'écriture dominante. La table du module donne, pour chaque caractère, les écritures avec lesquelles il se confond (Common, Inherited et Unknown omises).
- **Ensembles augmentés** (UTS #39, §5.1) : un mot qui n'emploie que Han, Hiragana et Katakana (japonais), Han et Hangul (coréen), ou Han et Bopomofo n'est pas mêlé.
- **Recherche** : la traduction de chaque segment en codes d'écriture (`str.translate`) dit si le segment, puis chaque ligne, a deux écritures ; seuls les mots de ces lignes sont examinés un à un.
- **Restitution** : `caracteres.homoglyphes` (mots), `.lettres`, `.codes` (« U+0430 Cyrillic dans Latin (2) », noms d'écritures d'Unicode), huit premières positions (`.position` : les lettres substituées, la plage du mot).
- **Lettres de compatibilité** : lettres et chiffres dont la décomposition de compatibilité est `<font>` (variantes mathématiques et de police) ou `<wide>` (pleine chasse). Une pleine chasse est ordinaire dans une ligne qui a une lettre chinoise, japonaise ou coréenne. Les lettres cerclées (`<circle>`) sont des symboles (catégorie So) et ne sont pas comptées ; les variantes mathématiques sont de l'écriture Common et n'entrent pas dans les mots. Restitution : `caracteres.compatibilite`, `.inhabituels`, `.codes` par nature (`police`, `pleine_chasse`), positions.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : aucune mesure ne fonde un indice ; la direction d'un mot mêlé n'est pas établie (A-43).
- Option C écartée : manque le cas le plus courant.
- Égalité départagée par les confusables : un mot de deux lettres de deux écritures n'a pas d'écriture dominante par le compte ; celle qui rend l'autre lettre confusable est la lecture la plus probable.

## Conséquences

- Les noms d'écritures (« Cyrillic », « Latin ») sont ceux d'Unicode, non traduits : ce sont des valeurs de la propriété Script.
- La part de textes ordinaires (bilingues, mal convertis) qui déclenchent la règle se mesurera sur le corpus de référence (T100).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T80 |
