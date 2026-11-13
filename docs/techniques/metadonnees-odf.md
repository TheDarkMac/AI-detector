# Fiche technique — Métadonnées d'un document ODT

- **Module** : `odf` (version 0.2.0)
- **Tâche** : T21 (complément bureautique), T22
- **Exigences** : F-10, F-12, ES-05, ES-06, ES-13
- **Formats** : `odt`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`

## Question

Que déclarent les métadonnées du document : logiciel générateur, titre, auteurs initial et dernier, dates, nombre de cycles et durée d'édition, statistiques, propriétés utilisateur ?

## Principe

Un ODT est un paquet OpenDocument (OASIS) : une archive ZIP dont l'entrée `meta.xml` porte les métadonnées, sous l'élément `office:meta`. Le module lit l'archive par le lecteur ZIP du projet ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)), puis l'entrée `meta.xml`, son XML par expat, sans DTD ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)), et observe chaque enfant d'`office:meta`. Aucune autre entrée n'est lue ([ADR-0139](../decisions/ADR-0139-parties-lues-dans-docx-et-odt.md)).

## Entrées

| Entrée | Contenu |
| --- | --- |
| `meta.xml` | `office:document-meta`, sa version (`office:version`), et les enfants d'`office:meta` |

- Le nom `meta.xml` est fixé par OpenDocument et comparé avec sa casse : `META.XML` n'est pas cette entrée.
- Ne sont pas lus : le contenu et les styles (`content.xml`, `styles.xml`), les réglages (`settings.xml`), le manifeste et les métadonnées RDF (`META-INF/manifest.xml`, `manifest.rdf`), la vignette, les signatures (T52), les modifications suivies (T81) ; les attributs `xlink` des métadonnées (modèle, rechargement automatique : adresses, ADR-0138) ; la langue d'un élément (`xml:lang`).

Aucune donnée de référence.

## Sorties

Noms d'observation ([ADR-0140](../decisions/ADR-0140-noms-et-valeurs-des-proprietes-bureautiques.md)) :

| Nom | Valeur |
| --- | --- |
| `odf.present` | Vrai si l'archive a une entrée `meta.xml` ; toujours observé (F-14) |
| `odf.blocs` | 1 si `meta.xml` existe |
| `odf.version` | Version d'OpenDocument déclarée par `meta.xml` (`office:version`) |
| `odf.<préfixe>:<nom>` | Texte d'un enfant d'`office:meta` : `meta:generator`, `dc:title`, `dc:subject`, `dc:description`, `dc:creator`, `dc:date`, `dc:language`, `meta:keyword`, `meta:initial-creator`, `meta:printed-by`, `meta:creation-date`, `meta:print-date`, `meta:editing-cycles`, `meta:editing-duration` |
| `odf.<préfixe>:<nom>.<préfixe>:<attribut>` | Attribut d'un enfant : `meta:document-statistic.meta:page-count`, `meta:template.meta:date`, `meta:auto-reload.meta:delay`… |
| `odf.meta:user-defined.<nom>` | Propriété utilisateur, nommée par `meta:name` |
| `odf.espace.ns<k>` | Adresse d'un espace de noms inconnu, dans l'ordre de première apparition |
| `<nom>.longueur` | Longueur entière d'une valeur coupée ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |

- Préfixes de la spécification, quel que soit celui qu'écrit le fichier : `office`, `meta`, `dc` ; un espace inconnu prend `ns1`, `ns2`… ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md)). Un nom tiré du fichier passe par la règle des composants.
- Valeurs : textes tels qu'écrits ; entiers pour `meta:editing-cycles` et les attributs de `meta:document-statistic` ; propriété utilisateur lue selon `meta:value-type` : réel (`float`, `percentage`), booléen (`boolean`), texte sinon (`string`, `date`, `time`) ; une écriture que le type n'admet pas reste un texte.
- Dates et durées (`meta:creation-date`, `dc:date`, `meta:print-date`, `meta:editing-duration`) : telles qu'écrites (ISO 8601), sans conversion ; T23 et T81 les interpréteront.
- Élément répété (`meta:keyword`) : une liste, dans l'ordre du document. Texte vide : rien n'est observé.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Propriétés |
| --- | --- |
| `metadonnee_nominative` | `meta:initial-creator`, `dc:creator`, `meta:printed-by` |

Le titre, les mots-clés et les propriétés utilisateur ne sont pas marqués : textes libres, relevant du contrôle avant publication (T25, [ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)). Le chemin du modèle (`meta:template`, `xlink:href`), qui peut nommer un fichier local, n'est pas lu.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `meta:generator` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. `meta:generator` est une déclaration du logiciel, que quiconque peut écrire (cas d'abus C-02) ; un seul cycle d'édition ou une durée nulle sont neutres (F-71, T81).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-ODF-001` Générateur nommé par le générateur d'un ODT ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `odf.meta:generator` | liste des générateurs (ADR-0144) | origine IA |

Une absence de métadonnées est l'observation `odf.present` à faux (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, dans les deux sens, sur un ODT écrit par LibreOffice ([ADR-0141](../decisions/ADR-0141-oracle-bureautique-par-libreoffice.md)).

## Limites connues

- `meta.xml` chiffré (document protégé par mot de passe dont le manifeste chiffre aussi les métadonnées) : non lu, format partiel ; le manifeste n'est pas consulté pour le dire.
- Archive : mêmes limites que pour `ooxml` (modes stocké et deflate, entrées en double, en-tête local différent, CRC non vérifié, ADR-0137).
- Un document OpenDocument à plat (`.fodt`, XML seul) n'est pas un ODT : il n'est pas identifié comme tel (ADR-0070).
- Un enfant d'`office:meta` qui contient d'autres éléments n'est observé que par son texte direct et ses attributs.

## Sécurité

- Archive lue en mémoire, jamais extraite sur disque (ES-05), lecture bornée à 16 Mio par entrée ; décompression par `Contexte.decompresser`, comptée dans le budget (ES-03).
- Chaque élément XML compte un objet et un niveau d'imbrication (ADR-0078) ; DOCTYPE, déclaration d'entité et entité externe refusés (ADR-0116).
- Aucune référence n'est lue ni suivie : les attributs `xlink` ne figurent pas au rapport (ES-06, M-14, ADR-0138).
- Le codec CP437 des noms d'entrées est chargé à l'import du lecteur, avant les restrictions (ADR-0079, ERR-0009) ; vérifié dans un vrai processus de travail.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément bureautique) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
