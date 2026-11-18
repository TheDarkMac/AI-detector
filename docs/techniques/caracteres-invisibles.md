# Fiche technique — Caractères invisibles ou substitués d'un texte, d'un DOCX ou d'un ODT

- **Module** : `caracteres` (version 0.2.0)
- **Tâche** : T80 et son complément bureautique
- **Exigences** : F-73, F-24, F-25, ES-12
- **Formats** : `texte`, `docx`, `odt`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`

## Question

Le texte porte-t-il des caractères qui ne s'affichent pas, ou qui se font passer pour d'autres : caractères invisibles hors de leur emploi ordinaire, texte caché, mots mêlés de lettres d'écritures différentes qui se confondent, manifeste C2PA écrit en caractères invisibles (F-73, F-24) ? L'outil dit ce qu'il voit, pas pourquoi le caractère est là (A-43).

## Principe

Le module lit un texte brut, enregistré dans un fichier (UTF-8, avec ou sans marque d'ordre, ou UTF-16 avec sa marque, ADR-0070) ou collé (UTF-8, [ADR-0233](../decisions/ADR-0233-saisie-du-texte-colle.md)). Ses tables sont tirées des données d'**Unicode 18.0.0** par `tests/donnees/caracteres/generer_unicode.py` et livrées avec lui (`_unicode.py`) : les constats ne dépendent pas de la version d'Unicode de l'interpréteur ([ADR-0234](../decisions/ADR-0234-caracteres-invisibles.md)).

**DOCX et ODT** (complément de T80, [ADR-0239](../decisions/ADR-0239-parties-lues-d-un-docx-et-d-un-odt.md) à [ADR-0242](../decisions/ADR-0242-texte-masque-et-versions-du-complement-de-t80.md)). Le texte est tiré des parties XML que le logiciel affiche, par le lecteur ZIP du projet ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)) et expat, sans DTD ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)), puis analysé paragraphe par paragraphe, comme un texte brut :

| Format | Parties lues, dans l'ordre | Texte |
| --- | --- | --- |
| DOCX | Partie principale (relation `officeDocument` du paquet), puis, par ses relations, en-têtes, pieds de page, notes de bas de page, notes de fin, commentaires | `w:t` ; `w:delText` ; tabulation, saut de ligne, trait d'union insécable et conditionnel par leur caractère ; codes de champ (`w:instrText`) non lus |
| ODT | `content.xml` (corps, notes, annotations, zones de texte, région des modifications), puis les en-têtes et pieds des pages types de `styles.xml` | Texte des paragraphes (`text:p`, `text:h`), hors métadonnées (`dc:`, `meta:`) et descriptions (`svg:`) ; `text:s`, `text:tab`, `text:line-break` par leur caractère |

Est **supprimé** le texte d'une suppression suivie (`w:del`, `w:moveFrom`, `text:deletion`) ; **masqué**, celui d'une course qui porte `w:vanish` ou d'un paragraphe ou d'une portion dont le style, automatique de sa partie ou commun de `styles.xml`, a `text:display="none"`. Ce texte est analysé comme le reste, et ses positions le disent ([ADR-0240](../decisions/ADR-0240-texte-supprime-d-une-modification-suivie.md), ADR-0242). Un paragraphe contenu dans un autre (zone de texte, note d'un ODT) est un paragraphe à part. Positions : partie, numéro du paragraphe dans sa partie (à partir de 1), caractère dans le paragraphe (à partir de 1), « texte supprimé », « texte masqué », et la plage d'octets de la partie dans l'archive ([ADR-0241](../decisions/ADR-0241-texte-bureautique-dans-le-module-caracteres.md)).

**Caractères invisibles.** Sept familles, un caractère recevant la première qui le contient :

| Famille | Caractères | Emploi ordinaire, non relevé par une règle |
| --- | --- | --- |
| `controles` | Catégorie Cc, sauf tabulation, saut de ligne, retour chariot, saut de page | Aucun |
| `bidirectionnels` | U+061C, U+200E, U+200F, U+202A à U+202E, U+2066 à U+2069 | Une marque de direction (U+061C, U+200E, U+200F) dans une ligne qui a une lettre d'une écriture de droite à gauche |
| `etiquettes` | U+E0000 à U+E007F | Un drapeau de subdivision : U+1F3F4, étiquettes U+E0020 à U+E007E, U+E007F |
| `selecteurs` | U+FE00 à U+FE0F, U+E0100 à U+E01EF, U+180B à U+180D, U+180F | Un seul sélecteur, juste après un caractère visible |
| `espaces` | Zs autre que U+0020, Zl, Zp | U+00A0, U+2007, U+2009, U+202F, U+3000, partout |
| `prive` | Catégorie Co | Aucun |
| `sans_chasse` | Autres ignorables par défaut, catégorie Cf | U+FEFF en tête ; ZWJ entre deux pictogrammes d'émoji ; ZWJ et ZWNJ seuls entre deux lettres d'une même écriture autre que latine, grecque ou cyrillique ; U+00AD et U+034F seuls entre deux lettres ; remplisseurs hangûl, U+17B4, U+17B5, U+180E à côté d'une lettre de leur écriture |

Le texte qu'écrivent des étiquettes hors d'un drapeau (U+E0020 à U+E007E, un caractère ASCII chacune) est décodé.

**Homoglyphes** ([ADR-0235](../decisions/ADR-0235-homoglyphes.md)). Un mot est une suite de lettres d'une écriture, de marques combinantes et d'invisibles sans chasse ou sélecteurs. Un mot qui a au moins deux écritures, hors des ensembles japonais (Han, Hiragana, Katakana), coréen (Han, Hangul) et chinois avec bopomofo (UTS #39, §5.1), est mêlé si une de ses lettres d'une autre écriture que la dominante a le même squelette qu'un caractère de la dominante (`confusables.txt`). L'écriture dominante est la plus fréquente ; à égalité, la première dont les autres lettres se confondent avec les siennes. **Lettres de compatibilité** : lettres et chiffres de décomposition `<font>` (variantes mathématiques) ou `<wide>` (pleine chasse) ; une pleine chasse est ordinaire dans une ligne qui a une lettre chinoise, japonaise ou coréenne.

**Manifeste C2PA d'un texte** ([ADR-0236](../decisions/ADR-0236-manifeste-c2pa-dans-un-texte.md)). Selon l'annexe A.7 de la spécification C2PA 2.3 : un U+FEFF suivi de sélecteurs de variante dont les huit premiers octets valent `C2PATXT\0` est une enveloppe ; elle est complète si sa version vaut 1, si la longueur annoncée est celle des octets qui suivent, et si ces octets sont une superboîte JUMBF `jumb` de cette longueur dont la description `jumd` porte l'étiquette `c2pa` (§11.1.4.2) ; corrompue sinon. Ses caractères ne sont comptés dans aucune famille. **Ni la signature ni l'empreinte du texte ne sont vérifiées** : c2pa-python 0.39.0 ne lit pas le texte brut.

**Lecture.** Par blocs de 1 Mio, décodés à mesure, analysés par segments qui finissent au dernier saut de ligne ou à la dernière espace (coupés de force au-delà de 8 Mi points de code). Les écritures d'un segment sont calculées en une fois (`str.translate`) ; seuls les mots des lignes qui ont deux écritures sont examinés un à un. Positions : plage d'octets dans le fichier, ligne et colonne en points de code, à partir de 1 (lignes séparées par le saut de ligne).

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| `texte` (fichier) | Le fichier entier, UTF-8 (marque d'ordre comprise) ou UTF-16 avec sa marque |
| `texte` (collé) | Les octets reçus, UTF-8, 16 Mio au plus ; les caractères de contrôle y sont admis |
| `docx` | Les parties XML du tableau ci-dessus, décompressées |
| `odt` | `content.xml`, et `styles.xml` pour ses pages types et ses styles communs |

Données de référence : `DerivedCoreProperties.txt` (Default_Ignorable_Code_Point), `Scripts.txt`, `extracted/DerivedGeneralCategory.txt`, `UnicodeData.txt` (décompositions), `emoji/emoji-data.txt` (Extended_Pictographic, Emoji_Modifier), `security/confusables.txt`, version 18.0.0, empreintes dans `_unicode.py`.

## Sorties

| Observation | Forme |
| --- | --- |
| `caracteres.encodage` | Texte brut : `UTF-8`, `UTF-8 avec marque d'ordre`, `UTF-16LE`, `UTF-16BE` |
| `caracteres.parties` | DOCX, ODT : noms des parties lues, dans l'ordre |
| `caracteres.supprimes`, `caracteres.masques` | DOCX, ODT : caractères de texte supprimé, de texte masqué (« caractères ») |
| `caracteres.longueur` | Points de code lus (« caractères ») |
| `caracteres.<famille>` | Caractères de la famille, ordinaires compris ; seulement si elle en a |
| `caracteres.<famille>.inhabituels` | Ceux hors de leur emploi ordinaire |
| `caracteres.<famille>.codes` | « U+200B (3) » pour chaque inhabituel distinct, 64 au plus, puis « … » |
| `caracteres.<famille>.position` | Points de code d'une suite d'inhabituels (seize au plus, puis « … »), localisée ; huit au plus par famille |
| `caracteres.etiquettes.texte` | Texte écrit par les étiquettes hors d'un drapeau, morceaux séparés par « \| », 1 024 caractères au plus ; identifiant, catégorie `contenu` |
| `caracteres.homoglyphes`, `.lettres`, `.codes`, `.position` | Mots mêlés, lettres substituées, « U+0430 Cyrillic dans Latin (2) », huit premiers mots |
| `caracteres.compatibilite`, `.inhabituels`, `.codes`, `.position` | Lettres de compatibilité, hors pleine chasse d'un texte d'Asie de l'Est, par nature (`police`, `pleine_chasse`) |
| `caracteres.c2pa`, `.completes`, `.corrompues`, `.version`, `.octets`, `.position` | Enveloppes trouvées ; version et longueur annoncée de la première complète, ou de la première ; positions des huit premières (« complète », « corrompue ») |

Le module n'émet aucun constat : les règles du catalogue lisent ses observations ([ADR-0237](../decisions/ADR-0237-constats-et-versions-de-t80.md)). Un bloc qui n'est pas décodable rend la suite du texte non menée (`format_partiel`).

## Données identifiantes

`caracteres.etiquettes.texte`, catégorie `contenu` : masquée par défaut (ES-13), comptée au contrôle avant publication ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)). Les codes et les positions ne citent que des points de code, jamais le texte.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Texte écrit à la main | Rien de particulier ; un mot mêlé peut venir d'un changement de clavier |
| Copie depuis une page web, un traitement de texte | Rien de particulier ; ces logiciels laissent des espaces insécables, des marques de direction, des caractères sans chasse |
| Texte marqué pour suivre ses copies, ou modifié pour échapper à une recherche | Les caractères sont relevés, sans direction : l'outil ne sait pas pourquoi ils sont là |
| Génération | Rien : aucun caractère invisible n'établit qu'un texte a été généré ; un manifeste C2PA d'un texte n'est pas vérifié |

## Ce qui déclenche un constat

| Règle | Condition |
| --- | --- |
| R-CARACTERES-001 à 007 | Au moins un caractère inhabituel de la famille : contrôles, bidirectionnels, étiquettes, sélecteurs, sans chasse, espaces, usage privé |
| R-CARACTERES-008 | Au moins un mot mêlé |
| R-CARACTERES-009 | Au moins une lettre de compatibilité inhabituelle |
| R-CARACTERES-010 | Au moins une enveloppe C2PATXT complète |
| R-CARACTERES-011 | Au moins une enveloppe corrompue |
| R-CARACTERES-012 | Au moins deux enveloppes |
| R-CARACTERES-013 | DOCX, ODT : au moins un caractère de texte masqué par la mise en forme |

Toutes en information neutre, direction « rien de particulier », fondement « vérification déterministe ».

## Taux d'erreur

Sans objet pour une information neutre qui relève des caractères. Les relevés sont vérifiés sur des textes construits par `tests/test_caracteres.py` (chaque famille, chaque emploi ordinaire, enveloppes écrites selon l'annexe A.7). La part de textes ordinaires qui déclenchent chaque règle se mesurera sur le corpus de référence (T100).

Sur les échantillons `tests/donnees/caracteres/texte.odt` et `texte.docx`, écrits et relus par LibreOffice 25.2.3.2 (`generer_bureau.py`, `oracle.json`), tout le texte que relit LibreOffice (paragraphes, note, en-tête, commentaire, suppression) se retrouve dans le texte lu, et chaque caractère semé est relevé à sa place.

Durées mesurées par T80 sur le poste de développement, commande `vk` entière : 200 Mo d'anglais en 45 s, 64 Mo de français en 47 s, 64 Mo de russe en 31 s. Un texte de 1 Gio peut dépasser le délai de 120 s : l'analyse est alors interrompue (ADR-0078).

## Limites connues

- Les emplois ordinaires se reconnaissent aux voisins, sans dictionnaire des séquences d'émoji ni des variantes normalisées : un sélecteur seul après une lettre passe pour ordinaire, et peut cacher un octet par lettre ; ZWJ entre deux pictogrammes est ordinaire même si la séquence n'est pas un émoji.
- Une marque de direction est ordinaire dans toute ligne qui a une lettre de droite à gauche, même loin de cette lettre ; de même une pleine chasse dans une ligne de chinois, de japonais ou de coréen.
- Un mot écrit tout entier dans une autre écriture n'est pas relevé ; un mot mêlé par un changement de clavier l'est. Un mot coupé par un caractère Common (chiffre, ponctuation) en fait deux.
- Les variantes mathématiques (écriture Common) ne sont pas cherchées dans les mots mêlés, mais comme lettres de compatibilité. Les lettres cerclées, qui sont des symboles, ne sont pas relevées.
- Un fichier dont les octets portent un contrôle C0 ou DEL n'est pas reconnu comme un texte (ADR-0070) : seuls ses contrôles C1 sont relevés ; un texte collé admet tous les contrôles.
- Lignes séparées par le seul saut de ligne : un texte aux retours chariot seuls n'a qu'une ligne.
- Un segment sans saut de ligne ni espace de plus de 8 Mi points de code est coupé : une suite d'invisibles ou un mot à cheval sur la coupure est vu en deux.
- Le manifeste d'une enveloppe n'est pas lu : ni ses déclarations, ni sa signature, ni l'empreinte du texte. Une superboîte JUMBF à longueur étendue est comptée corrompue.
- Une nouvelle version d'Unicode n'est connue qu'avec de nouvelles tables (version mineure du module).
- La couche texte d'un PDF n'est pas encore lue (complément de T53).
- DOCX : seule la mise en forme directe masque (`w:vanish` d'une course) ; un style qui masque, un texte blanc sur blanc ou minuscule ne le sont pas. Ni le glossaire, ni les parties XML personnalisées, ni le texte des SmartArt et des graphiques ne sont lus ; le texte affiché d'un champ l'est, son code non.
- ODT : un style masqué l'est sans ses styles parents ; les documents incorporés (`Object 1/`) ne sont pas lus.
- Le dernier morceau d'un XML coupé n'est pas rendu par expat : le texte qui précède l'arrêt est analysé, pas celui-là.
- Les positions d'un DOCX ou d'un ODT sont dans le texte décodé, non en octets : la plage citée est celle de la partie entière dans l'archive.

## Sécurité

Le module ne lit que le texte de sa partie, par blocs, et n'emploie aucune bibliothèque tierce ; ses expressions régulières sont celles du module, compilées à l'import, sur des classes de caractères sans répétition imbriquée. Il n'interprète ni n'exécute rien : le texte des étiquettes est observé, jamais suivi. L'affichage neutralise les caractères relevés (`⟨U+XXXX⟩`, [ADR-0096](../decisions/ADR-0096-neutralisation-des-caracteres-invisibles.md)) ; le rapport ne cite que des points de code. Ses résultats sont bornés (huit positions par famille, 64 codes, 1 024 caractères de texte caché) sous le nombre de résultats d'un module (ES-03).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-17 | 0.1.0 | Création |
| 2026-11-18 | 0.2.0 | DOCX et ODT : corps, notes, en-têtes et pieds de page, commentaires ; texte supprimé et masqué signalés ; R-CARACTERES-013 (complément de T80) |
