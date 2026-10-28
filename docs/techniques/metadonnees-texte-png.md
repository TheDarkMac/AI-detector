# Fiche technique — Blocs texte PNG

- **Module** : `textepng` (version 0.1.0)
- **Tâche** : T20
- **Exigences** : F-10, ES-13
- **Formats** : `png`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Quels textes le PNG porte-t-il dans ses blocs `tEXt`, `zTXt` et `iTXt` : auteur, commentaire, logiciel, paramètres de génération ?

## Principe

Le module parcourt les blocs du PNG jusqu'à `IEND` (PNG, 3e édition) et lit chaque bloc texte : mot-clé, puis texte en Latin-1 (`tEXt`), texte compressé en Latin-1 (`zTXt`), ou texte UTF-8 éventuellement compressé, avec langue et mot-clé traduit (`iTXt`). La décompression passe par le contexte, donc par le budget de décompression du module (ADR-0078). Les sommes de contrôle CRC ne sont pas vérifiées.

Le bloc `iTXt` de mot-clé `XML:com.adobe.xmp` est un paquet XMP : il est lu par le module `xmp`, pas par celui-ci.

## Entrées

| Format | Emplacement lu ([ADR-0115](../decisions/ADR-0115-formats-et-emplacements-lus.md)) |
| --- | --- |
| PNG | Blocs `tEXt`, `zTXt`, `iTXt`, avant ou après les données d'image |

Aucune donnée de référence.

## Sorties

Noms d'observation ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md)) :

| Nom | Valeur |
| --- | --- |
| `textepng.present` | Vrai si au moins un bloc texte (hors XMP) a été trouvé ; toujours observé (F-14) |
| `textepng.blocs` | Nombre de blocs texte, s'il y en a |
| `textepng.<mot-clé>` | Texte du bloc |
| `textepng.<mot-clé>.langue` | Langue d'un `iTXt`, si elle est déclarée (64 caractères au plus) |
| `<nom>.longueur` | Longueur entière d'un texte coupé à 4 096 caractères ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |

Dans le mot-clé, tout caractère hors des lettres ASCII, des chiffres et du tiret devient un tiret : `Creation Time` donne `textepng.Creation-Time`. Le mot-clé traduit d'un `iTXt` n'est pas observé.

Aucun constat. Les paramètres de génération que certains outils écrivent dans ces blocs (mots-clés `parameters`, `prompt`, `workflow`…) sont observés comme tout texte ; leur reconnaissance est l'affaire du catalogue de signatures de T22 (F-12).

## Données identifiantes

Marqués `metadonnee_nominative` ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)) : les mots-clés prédéfinis `Author` et `Copyright` (sans égard à la casse).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Rien |

Le module ne distingue aucune hypothèse et n'émet aucun constat ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)).

## Ce qui déclenche un constat

Aucun constat en T20. Une absence de bloc texte est l'observation `textepng.present` à faux (F-14).

## Taux d'erreur

Sans objet : aucun constat. Fidélité de l'extraction vérifiée contre exiftool, par mot-clé ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)).

## Limites connues

- Un texte de plus de 4 096 caractères est coupé : une règle de T22 ne verra que son début (le flux de travail JSON de certains outils dépasse souvent cette taille). Sa longueur entière est observée.
- Les textes « Raw profile type exif / xmp / iptc » écrits en hexadécimal par ImageMagick sont observés comme du texte, sans être décodés vers EXIF, XMP ou IPTC.
- Une compression inconnue, un flux invalide ou un drapeau de compression invalide rendent le bloc non mené (format partiel) ; les autres blocs sont lus.
- Le bloc `tIME` (date de dernière modification) n'est pas un bloc texte : il n'est pas lu en T20.

## Sécurité

- Décompression par `Contexte.decompresser` : flux zlib lu par blocs de 1 Mio, cumul borné à 512 Mio et rapport de compression contrôlé (ES-03) ; une bombe de décompression arrête le module pour limite dépassée, les autres continuent.
- Chaque bloc PNG compte un objet ; un bloc de plus de 16 Mio n'est pas lu.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-10-28 | 0.1.0 | Création (T20) |
