# ADR-0096 — Neutralisation des caractères de contrôle et bidirectionnels, à l'écriture de chaque sortie

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : l'assistant, choix soumis dans la PR de T16
- **Tâche** : T16
- **Exigences liées** : ES-12 ; menace M-21 ; ADR-0025, ADR-0094

## Contexte

ES-12 exige que toute sortie (HTML, JSON, terminal) neutralise les caractères de contrôle et bidirectionnels en les montrant sous forme visible. Une valeur tirée d'un fichier peut contenir une séquence d'échappement qui efface le terminal, ou un U+202E qui fait lire « fdp.txt » pour « txt.pdf » (M-21). Il fallait fixer quels caractères, sous quelle forme, et où.

## Options envisagées

### Option A — Catégories Unicode Cc, Cf, Zl, Zp ; forme `⟨U+XXXX⟩` ; à l'écriture

- Avantages : couvre les contrôles C0 et C1, les marques et isolats bidirectionnels, les caractères sans chasse et les étiquettes, les séparateurs de ligne et de paragraphe ; une forme qui ne peut pas passer pour le caractère ; un seul endroit par sortie.
- Inconvénients : la classification dépend de la base Unicode de l'interpréteur ; un texte qui contient littéralement « ⟨U+202E⟩ » se lit comme le caractère neutralisé.

### Option B — Liste fixe des caractères bidirectionnels et des contrôles C0

- Avantages : identique sur toutes les versions de Python.
- Inconvénients : oublie U+200B, U+FEFF, les étiquettes (U+E0000 à U+E007F), U+0085, U+2028 ; chaque oubli est une faille.

### Option C — Neutraliser dans le modèle, à la réception

- Avantages : une seule fois.
- Inconvénients : la donnée du rapport ne serait plus celle du fichier (contre NF-06 et l'usage d'un expert) ; le JSON, format de données, doit rendre la valeur exacte.

## Décision

Option A.

- Sont neutralisés les caractères des catégories **Cc** (contrôle, dont tabulation et sauts de ligne), **Cf** (mise en forme : bidirectionnels, sans chasse, U+FEFF, étiquettes), **Zl** et **Zp** (séparateurs). Les espaces (Zs) ne le sont pas.
- Terminal et HTML : chacun s'écrit `⟨U+XXXX⟩` (au moins quatre chiffres hexadécimaux majuscules), au moment d'écrire la ligne ou d'insérer le texte dans le document, avant l'échappement HTML.
- JSON : chacun s'écrit en échappement `\uXXXX` (paire de substituts au-delà de U+FFFF) ; la valeur décodée par un lecteur JSON est celle du fichier. `json.dumps` échappe déjà les contrôles inférieurs à U+0020 dans les chaînes ; ceux qui restent sont la mise en forme du document, laissée telle quelle.
- Les textes de l'outil ne contiennent aucun de ces caractères : neutraliser la ligne entière revient à neutraliser les valeurs qu'elle cite.

## Raisons

- Option A retenue : elle suit une définition stable (les catégories) plutôt qu'une liste à tenir, et laisse intacte la donnée du rapport.
- Option B écartée : la liste serait incomplète dès le départ.
- Option C écartée : un rapport doit permettre de vérifier la donnée exacte ; la neutralisation est une affaire d'affichage.
- Dépendance à la base Unicode : un caractère nouvellement classé Cf par une version de Python serait neutralisé par elle seule ; seule la présentation change, jamais un constat.

## Conséquences

- Les tests couvrent bidirectionnels, isolats, échappements de terminal, sauts de ligne, séparateurs, caractères sans chasse et étiquettes, et un test de fuzzing vérifie qu'aucun ne subsiste dans le HTML.
- T80 (caractères invisibles et homoglyphes) produira des observations sur ces caractères : leur affichage est déjà sûr.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
