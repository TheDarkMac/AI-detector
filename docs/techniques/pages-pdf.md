# Fiche technique — Textes superposés, caches et polices des pages d'un PDF

- **Module** : `pagespdf` (version 0.1.0)
- **Tâche** : T51
- **Exigences** : F-61
- **Formats** : `pdf`
- **Directions permises** : `retouche`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Sur les pages que montre la dernière version du PDF, un texte a-t-il été posé sur un autre, un texte caché par un rectangle, ou écrit avec une police qui ne s'accorde pas avec celles de la page ?

## Principe

Le module interprète le contenu de chaque page comme un lecteur l'afficherait, sans rien dessiner (ISO 32000-2, §8 et §9), par le lecteur PDF du projet, étendu aux flux de contenu ([ADR-0213](../decisions/ADR-0213-contenus-de-pages-par-le-lecteur-du-projet.md)) : le flux de contenu de la page (ou ses flux, mis bout à bout), les formes qu'il appelle (`Do`, huit niveaux au plus), puis l'apparence normale de chaque annotation visible, champs de formulaire et fenêtres d'annotation exceptés ([ADR-0214](../decisions/ADR-0214-textes-superposes-et-caches.md)). Il suit la matrice de transformation (`cm`, `q`, `Q`), l'état du texte (`Tf`, `Tm`, `Td`, `TD`, `T*`, `Tc`, `Tw`, `Tz`, `TL`, `Ts`, `Tr`), l'opacité du remplissage (`gs` : `/ca`, `/BM`, `/SMask`) et les chemins remplis.

1. **Boîte d'un texte** ([ADR-0215](../decisions/ADR-0215-mesure-des-textes.md)) : chaque opération d'écriture (`Tj`, `TJ`, `'`, `"`) pose un texte ; sa boîte va de son point de départ à la somme des avancées de ses glyphes (largeur déclarée, espacement des caractères et des mots, échelle horizontale, ajustements de `TJ`), et de la descente à la montée de la police (`/Descent`, `/Ascent` du descripteur ; 0,8 et -0,2 cadratin à défaut), dans l'espace de la page. Les largeurs sont celles que la police déclare (`/Widths` d'une police simple, `/W` et `/DW` d'une police composite à CMap Identity-H, `/Widths` et `/FontMatrix` d'une police Type3) ; pour les 14 polices standard non incorporées qui n'en déclarent pas, celles des fichiers AFM d'Adobe, par leur encodage (StandardEncoding, WinAnsiEncoding, MacRomanEncoding, `/Differences`).
2. **Texte sur texte** : un texte d'au moins deux signes posé sur un texte différent d'au moins deux signes, déjà posé, dont la boîte recouvre la sienne au moins pour moitié de la plus petite. Le même texte redit (faux gras, ombre) ne compte pas ; un texte d'un seul signe sur un autre est compté à part ; les espaces ne sont pas des signes.
3. **Cache** : un rectangle (`re`, ou quatre segments alignés sur les axes) rempli d'une peinture opaque (opacité 1, fusion normale, sans masque doux), peint sur un texte déjà posé qu'il recouvre au moins pour moitié.
4. **Familles mélangées** ([ADR-0216](../decisions/ADR-0216-polices-incoherentes.md)) : une même police (son `/BaseFont` sans le préfixe `ABCDEF+` d'un sous-ensemble) peint du texte visible d'une page par plusieurs polices d'incorporation différente : préfixe, programme incorporé (`FontFile`, `FontFile2`, `FontFile3`) ou absence de programme.
5. **Codes hors plage** : un code dessiné, en texte visible, hors de la plage `/FirstChar` à `/LastChar` d'une police simple qui déclare ses largeurs.

Le texte invisible (modes de rendu 3 et 7, la couche de texte d'un document numérisé) n'est ni posé ni compté.

Sur les échantillons de `tests/donnees/pages` (`generer_pages.py`) :

| Échantillon | Écrit par | Relevé |
| --- | --- | --- |
| `document.pdf` | LibreOffice : deux pages, titres, gras, italique, souligné, surligné, tableau coloré, grec, cyrillique | rien |
| `ghostscript.pdf` | Ghostscript : Helvetica et Times en sous-ensembles, fond gris peint avant le texte, faux gras, petites capitales | rien |
| `superpose.pdf` | `document.pdf`, puis pypdf : un montant en Helvetica sur celui du tableau | un texte sur texte |
| `cache.pdf` | `document.pdf`, puis pypdf : un rectangle blanc sur ce montant, un autre par-dessus | un cache, un texte sur texte |
| `cache_seul.pdf` | `document.pdf`, puis pypdf : un rectangle noir sur ce montant | un cache |
| `annotation.pdf` | `document.pdf`, puis pypdf : annotation de texte libre dont l'apparence peint un rectangle blanc et un montant | un cache, un texte sur texte |
| `fusion.pdf` | `ghostscript.pdf` fusionné par pypdf avec une autre page de Ghostscript | Helvetica en deux sous-ensembles |
| `hors_plage.pdf` | `ghostscript.pdf`, puis pypdf : un texte écrit avec le sous-ensemble de Helvetica | deux codes hors plage |

Oracle (`oracle.json`) : `pdftotext -bbox` de Poppler 25.03.0 donne la boîte de chaque mot ; chaque mot de largeur non nulle est couvert au moins à 90 % par un texte du module, à moins d'un demi-point près en hauteur (Poppler emploie aussi la montée et la descente de la police). `pdffonts` donne, pour chaque police, son préfixe de sous-ensemble et son incorporation, les mêmes que ceux du module.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| PDF | Dernière version : catalogue, arbre des pages et ressources héritées ; flux de contenu de chaque page (`FlateDecode` seul) ; formes appelées et leurs ressources ; annotations de chaque page, leur rectangle, leurs indicateurs et leur apparence normale ; dictionnaires d'état graphique ; polices employées, leurs descripteurs, leurs largeurs et leur encodage. Le programme des polices n'est pas lu. |

Données de référence : les largeurs, la montée et la descente des 14 polices standard, tirées des fichiers AFM d'Adobe (`modules/pagespdf/_polices14.py`, écrit par `tests/donnees/pages/generer_polices14.py`), et les noms des glyphes des encodages de l'annexe D.

## Sorties

| Observation | Forme |
| --- | --- |
| `pagespdf.pages` | Pages de l'arbre des pages |
| `pagespdf.pages_lues` | Pages interprétées en entier |
| `pagespdf.arret_avant_budget` | Vrai si l'interprétation s'est arrêtée pour garder du budget (ADR-0213) |
| `pagespdf.textes`, `pagespdf.textes_non_mesures` | Textes visibles posés ; textes dont la boîte ne se calcule pas (largeurs inconnues, CMap autre qu'Identity-H, coordonnées démesurées) |
| `pagespdf.polices` | Polices employées par les opérations `Tf` et `gs` |
| `pagespdf.superpositions`, `.premiere_page`, `.pages` | Textes posés sur un texte différent ; première page concernée et liste des pages |
| `pagespdf.superpositions_d_un_signe` | Mêmes recouvrements quand l'un des textes n'a qu'un signe |
| `pagespdf.caches`, `.premiere_page`, `.pages` | Rectangles opaques peints sur un texte ; pages concernées |
| `pagespdf.textes_caches` | Textes cachés par ces rectangles |
| `pagespdf.familles_melangees`, `.premiere_page`, `.pages`, `.noms` | Polices en plusieurs incorporations, par page ; pages et noms des polices |
| `pagespdf.codes_hors_plage`, `.premiere_page`, `.pages` | Codes dessinés hors de la plage de leur police ; pages concernées |
| `pagespdf.chiffre` | Vrai pour un document chiffré, alors non interprété |

## Données identifiantes

Aucune : le module n'observe ni texte, ni auteur ; les noms de polices ne désignent pas une source.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Un logiciel qui écrit une page d'un seul tenant pose ses textes côte à côte, peint ses fonds avant le texte et incorpore une police une fois : rien n'est relevé |
| Transformation banale (recompression, redimensionnement) | Une optimisation ou une réécriture garde les contenus : rien de plus n'est relevé |
| Retouche | Un texte posé sur un autre, un rectangle sur un texte, une police d'une autre incorporation ou des codes hors plage sont compatibles avec une retouche, comme avec une mise en page inhabituelle |
| Génération | La technique ne dit rien d'une origine IA |

## Ce qui déclenche un constat

Le module n'émet aucun constat ; quatre règles « moteur » du catalogue lisent ses observations ([ADR-0218](../decisions/ADR-0218-constats-et-versions-de-t51.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-PAGESPDF-001 | `pagespdf.superpositions` ≥ 1 | Indice faible vers la retouche |
| R-PAGESPDF-002 | `pagespdf.caches` ≥ 1 | Indice faible vers la retouche |
| R-PAGESPDF-003 | `pagespdf.familles_melangees` ≥ 1 | Indice faible vers la retouche |
| R-PAGESPDF-004 | `pagespdf.codes_hors_plage` ≥ 1 | Indice faible vers la retouche |

Chaque phrase nomme la première page concernée.

## Taux d'erreur

Non mesurés : le corpus de référence n'existe pas encore (T100). Les boîtes ont été comparées à celles de Poppler et les relevés vérifiés sur les huit échantillons ci-dessus et sur des documents synthétiques des tests ; la part de documents ordinaires qui déclenchent chaque règle reste à mesurer. Le niveau des indices reste « faible » ([ADR-0101](../decisions/ADR-0101-bornes-des-niveaux-et-cible.md)).

## Limites connues

- Seule la dernière version est interprétée : ce qu'une version antérieure affichait se lit dans la chronologie de `revisionspdf`, pas ici.
- La boîte d'un texte suit les largeurs déclarées, pas le dessin des glyphes : un glyphe plus large que son avancée, un découpage (`W`, `W*`), un texte peint dans la couleur du fond ou hors de la page ne sont pas vus.
- Mises en page qui superposent des textes sans retouche : formulaire aplati dont la valeur recouvre un texte d'attente, filigrane textuel, surimpression voulue, symboles composés, accents posés à part (comptés en « d'un seul signe »).
- Caches : seuls les rectangles alignés sur les axes sont vus ; une image, une forme courbe, un dégradé (`sh`) posés sur un texte, ou un rectangle tourné, ne le sont pas ; la couleur n'est pas comparée au fond. Un caviardage qui laisse le texte en est un.
- Les apparences des champs de formulaire ne sont pas interprétées, ni celles d'une annotation cachée ; l'apparence d'une annotation dont l'état (`/AS`) ne désigne rien non plus.
- Familles : un document fusionné, une page assemblée de plusieurs sources, un logiciel qui découpe une police en plusieurs sous-ensembles les déclenchent ; deux noms d'une même police ne sont pas rapprochés ; les polices Type3 ne sont pas comparées.
- Codes hors plage : seules les polices simples qui déclarent leurs largeurs sont lues ; un glyphe absent du programme incorporé n'est pas vu.
- Polices composites : seul le CMap Identity-H est découpé ; un autre CMap, prédéfini ou incorporé, et l'écriture verticale laissent le texte non mesuré.
- Seul `FlateDecode` est décodé ; un flux de contenu codé autrement arrête la lecture de sa page (analyse non menée, `format_partiel`).
- L'interprétation s'arrête quand il ne reste plus que 262 144 objets du budget du module, pour que les observations déjà faites soient envoyées ; les pages suivantes ne sont pas lues, et `pagespdf.pages_lues` le dit. Au plus 4 096 pages et 65 536 textes par page.
- Document chiffré : rien n'est déchiffré ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md)), aucune page n'est interprétée.

## Sécurité

Mêmes protections que le lecteur PDF du projet : lecture stricte, aucune exécution, aucun flux d'un autre fichier, `FlateDecode` seul par `Contexte.decompresser`. Chaque opérande et chaque opération d'un flux de contenu comptent un objet du budget (ES-03), comme chaque largeur lue et chaque groupe de 64 textes comparés ; les formes imbriquées comptent un niveau chacune. Les textes sont rangés dans une grille de cases de 16 unités pour n'être comparés qu'à leurs voisins ; une boîte de plus de 4 096 cases est comparée à toutes. Les données de référence sont chargées à l'import : rien n'est lu sur le disque après les restrictions. Aucune image n'est décodée ni écrite.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-17 | 0.1.0 | Création |
