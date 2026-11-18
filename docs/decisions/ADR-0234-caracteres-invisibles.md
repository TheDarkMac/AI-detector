# ADR-0234 — Caractères invisibles : table Unicode 18.0 du projet, sept familles, emplois ordinaires reconnus à leurs voisins ; texte des étiquettes masqué par défaut

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (familles, emplois ordinaires et bornes précisés par l'assistant)
- **Tâche** : T80
- **Exigences liées** : F-73, NF-06, ES-12, ES-13, ES-19 ; A-43 ; ADR-0023, ADR-0096, ADR-0158, ADR-0200

## Contexte

F-73 cite les caractères de largeur nulle ; A-43 relève que leur direction n'est pas dite : copie depuis une source, dissimulation volontaire, mise en page. Beaucoup ont un emploi ordinaire : le liant (ZWJ) des émojis composés, l'antiliant (ZWNJ) du persan, l'espace insécable de la typographie française, la marque d'ordre en tête d'un fichier, la marque de direction dans un texte en hébreu. D'autres servent à cacher : un texte écrit en étiquettes Unicode (U+E0020 à U+E007E, un caractère ASCII chacune) ne s'affiche pas mais se lit par un programme, par exemple un modèle de langage ; un forçage bidirectionnel fait lire un texte autrement qu'il ne s'écrit (CVE-2021-42574, « Trojan Source ») ; des suites de caractères sans chasse marquent la copie d'un document.

ADR-0096 neutralise déjà à l'affichage les catégories Cc, Cf, Zl et Zp d'après la base Unicode de l'interpréteur ; il en a accepté la dépendance parce que seule la présentation en dépend. Pour un constat, NF-06 exige le même résultat d'une version de Python à l'autre : Python 3.12, 3.13 et 3.14 n'ont pas la même version d'Unicode : 15.0.0 et 16.0.0 d'après la documentation du module `unicodedata` de 3.12 et de 3.14, 15.1.0 relevé sur le Python 3.13.5 du poste (`unicodedata.unidata_version`), le 2026-11-17.

## Options envisagées

### Option A — Table Unicode 18.0 figée dans le projet (recommandée)

Une table tirée des données d'Unicode 18.0 par un script de génération, livrée avec le module : ignorables par défaut, contrôles, bidirectionnels, étiquettes, sélecteurs de variante, espaces inhabituelles. Comptés par famille, avec positions ; emplois ordinaires mis à part ; texte des étiquettes décodé, masqué par défaut (catégorie `contenu`) ; information neutre.

- Avantages : constats identiques sur toutes les versions de Python ; la version d'Unicode est écrite dans le code et la fiche ; chaque famille dit ce qu'elle cache.
- Inconvénients : la table vieillit avec Unicode ; un caractère nouveau n'est connu qu'avec une nouvelle génération.

### Option B — Catégories de Python

`unicodedata` : Cf, Zs autres que l'espace, comme ADR-0096.

- Avantages : aucune donnée à générer.
- Inconvénients : un même texte pourrait donner des constats différents d'une version de Python à l'autre (NF-06) ; Python ne donne ni les ignorables par défaut ni les écritures.

### Option C — Liste fixe courte

Largeur nulle, bidirectionnels, étiquettes.

- Avantages : simple.
- Inconvénients : oublie les sélecteurs de variante, les remplisseurs hangûl, les espaces inhabituelles ; le texte caché n'est pas montré.

## Décision

Option A. Précisions de l'assistant :

**Données.** Six fichiers de la version 18.0.0, téléchargés le 2026-11-17 sur `unicode.org/Public/18.0.0/` : `DerivedCoreProperties.txt`, `Scripts.txt`, `extracted/DerivedGeneralCategory.txt`, `UnicodeData.txt`, `emoji/emoji-data.txt`, `security/confusables.txt`, sous la licence Unicode v3 (permissive, la notice accompagne les copies). `tests/donnees/caracteres/generer_unicode.py` vérifie leurs empreintes SHA-256 et écrit `src/voight_kampff/modules/caracteres/_unicode.py`, licence reproduite en tête, sous une forme que `ruff format` laisse telle quelle. Les fichiers sources ne sont pas versionnés (2 Mo de `UnicodeData.txt`) : leurs empreintes le sont.

**Familles**, dans cet ordre (un caractère reçoit la première qui le contient) :

| Famille | Caractères | Emploi ordinaire |
| --- | --- | --- |
| `controles` | Catégorie Cc, sauf tabulation, saut de ligne, retour chariot, saut de page | Aucun |
| `bidirectionnels` | U+061C, U+200E, U+200F, U+202A à U+202E, U+2066 à U+2069 | Une marque de direction (U+061C, U+200E, U+200F) dans une ligne qui a une lettre d'une écriture de droite à gauche ; forçages, plongements et isolats jamais |
| `etiquettes` | U+E0000 à U+E007F | Un drapeau de subdivision : U+1F3F4, étiquettes U+E0020 à U+E007E, U+E007F (UTS #51) |
| `selecteurs` | U+FE00 à U+FE0F, U+E0100 à U+E01EF, sélecteurs mongols U+180B à U+180D et U+180F | Un seul sélecteur, juste après un caractère visible (ni espace, ni début, ni autre invisible) |
| `espaces` | Zs autre que U+0020, Zl, Zp | U+00A0, U+2007, U+2009, U+202F, U+3000, partout |
| `prive` | Catégorie Co | Aucun |
| `sans_chasse` | Les autres ignorables par défaut et la catégorie Cf | U+FEFF en tête du texte ; ZWJ entre un pictogramme d'émoji (au-delà de son sélecteur ou de sa teinte) et un pictogramme ; ZWJ et ZWNJ seuls entre deux lettres d'une même écriture autre que latine, grecque ou cyrillique ; césure conditionnelle et liant de graphèmes seuls entre deux lettres ; remplisseurs hangûl, voyelles inhérentes khmères et séparateur mongol à côté d'une lettre de leur écriture |

**Restitution.** Pour chaque famille présente : `caracteres.<famille>` (total), `.inhabituels`, `.codes` (caractères inhabituels et leur nombre, 64 distincts au plus, puis « … »), et les huit premières suites d'inhabituels par `.position` (points de code, seize au plus, plage d'octets, ligne et colonne en points de code). Le texte écrit par des étiquettes hors d'un drapeau, U+E0020 à U+E007E ramenés à l'ASCII, est observé (`caracteres.etiquettes.texte`, 1 024 caractères au plus, morceaux séparés par « | »), catégorie identifiante `contenu` : il est masqué par défaut et compte au contrôle avant publication (ADR-0158). Le libellé de la catégorie `contenu`, propre jusque-là à l'image de l'ELA (ADR-0200), devient « contenu du fichier ».

**Lecture.** Le texte est décodé par blocs de 1 Mio (UTF-8, ou UTF-16 avec sa marque) et analysé par segments qui finissent au dernier saut de ligne ou à la dernière espace ; un segment sans l'un ni l'autre est coupé de force au-delà de 8 Mi points de code. Un bloc qui n'est pas décodable rend la suite non menée pour format partiel. Les espaces toujours ordinaires sont comptées par `str.count`, hors de l'expression des invisibles ; sans caractère astral, l'expression employée est celle du plan de base, que Python lit par une table de bits.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : dépendance des constats à la version de Python, contre NF-06.
- Option C écartée : chaque oubli est un moyen de cacher.
- Unicode 18.0 plutôt que la version d'un interpréteur : dernière version finale publiée au 2026-11-17, avec les données de sécurité (`confusables.txt`) de la même version.
- Emplois ordinaires reconnus aux voisins, sans dictionnaire de séquences d'émoji ni de variantes normalisées : la règle se vérifie à la lecture du texte ; la fiche en dit les limites (un octet caché par sélecteur, juste après une lettre, passe inaperçu).
- Ligne entière pour une marque de direction : la règle reste locale et indépendante de la taille du texte.
- Texte des étiquettes montré : c'est ce que le vérificateur veut lire ; masqué par défaut, comme tout contenu qui peut désigner une source.

## Conséquences

- Mesures de T80 sur le poste de développement, commande `vk` entière : 64 Mo de français en 47 s, 64 Mo de russe en 31 s, 200 Mo d'anglais en 45 s ; un texte de 1 Gio peut dépasser le délai de 120 s (analyse interrompue, ADR-0078).
- Un fichier dont les octets portent un contrôle C0 ou DEL n'est pas reconnu comme un texte (ADR-0070) : seuls ses contrôles C1 sont relevés ; un texte collé admet tous les contrôles (ADR-0233).
- Nouvelle version d'Unicode : relancer le script avec les nouveaux fichiers et leurs empreintes, monter la version mineure du module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T80 |
