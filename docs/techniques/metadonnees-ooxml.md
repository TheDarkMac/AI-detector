# Fiche technique — Propriétés d'un document DOCX

- **Module** : `ooxml` (version 0.3.0)
- **Tâche** : T21 (complément bureautique), T22, T23, T25
- **Exigences** : F-10, F-12, F-90, ES-05, ES-06, ES-13
- **Formats** : `docx`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`

## Question

Que déclarent les propriétés du document : titre, auteur et dernier modificateur, dates, logiciel et sa version, temps d'édition, nombre de révisions, société, modèle, propriétés personnalisées ?

## Principe

Un DOCX est un paquet OPC (ECMA-376, partie 2) : une archive ZIP dont les parties sont reliées par des relations. Le module lit l'archive par le lecteur ZIP du projet ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)) : enregistrement de fin, ZIP64 compris, répertoire central, puis, à la demande, l'entrée `_rels/.rels`. Il y cherche les relations vers les trois parties de propriétés, les suit à l'intérieur de l'archive seulement, lit chaque partie (données stockées ou deflate) et son XML par expat, sans DTD ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)), puis observe chaque propriété. Aucune autre partie n'est lue ([ADR-0139](../decisions/ADR-0139-parties-lues-dans-docx-et-odt.md)).

## Entrées

| Partie | Relation du paquet | Contenu |
| --- | --- | --- |
| Propriétés principales (`docProps/core.xml` d'ordinaire) | `…/package/2006/relationships/metadata/core-properties` | Dublin Core et `cp:` (ECMA-376, partie 2) |
| Propriétés étendues (`docProps/app.xml`) | `…/officeDocument/2006/relationships/extended-properties`, ou son équivalent strict | Propriétés de l'application (ECMA-376, partie 1) |
| Propriétés personnalisées (`docProps/custom.xml`) | `…/officeDocument/2006/relationships/custom-properties`, ou son équivalent strict | Propriétés nommées par le document, typées par `docPropsVTypes` |

- La cible d'une relation est résolue depuis la racine du paquet (`/`, `.`, `..`, encodage `%xx`) ; les noms de parties sont comparés sans la casse des lettres ASCII, comme le veut OPC.
- Le type de relation des premières versions d'Office 2007 (`…/officedocument/2006/relationships/metadata/core-properties`) est accepté.
- Ne sont pas lus : le document (`word/document.xml`) et toutes ses relations, dont le modèle (`attachedTemplate`), les liens et les objets incorporés ; la liste des liens des propriétés étendues (`HLinks`) ; la vignette ; les signatures numériques (T52) ; les identifiants de révision et les modifications suivies (T81).

Aucune donnée de référence.

## Sorties

Noms d'observation ([ADR-0140](../decisions/ADR-0140-noms-et-valeurs-des-proprietes-bureautiques.md)) :

| Nom | Valeur |
| --- | --- |
| `ooxml.present` | Vrai si le paquet a au moins une relation vers une partie de propriétés ; toujours observé (F-14) |
| `ooxml.blocs` | Nombre de parties de propriétés trouvées dans l'archive |
| `ooxml.core.<préfixe>:<nom>` | Propriété principale : `dc:title`, `dc:creator`, `dc:subject`, `dc:description`, `dc:language`, `dc:identifier`, `cp:keywords`, `cp:lastModifiedBy`, `cp:revision`, `cp:category`, `cp:contentStatus`, `cp:version`, `cp:lastPrinted`, `dcterms:created`, `dcterms:modified` |
| `ooxml.app.<nom>` | Propriété étendue : `Application`, `AppVersion`, `Template`, `TotalTime`, `Pages`, `Words`, `Characters`, `Company`, `Manager`, `DocSecurity`… |
| `ooxml.custom.<nom>` | Propriété personnalisée, nommée par le document |
| `ooxml.espace.ns<k>` | Adresse d'un espace de noms inconnu, dans l'ordre de première apparition |
| `<nom>.taille` | Taille, en octets, d'une donnée binaire (`DigSig`, `vt:blob`…) |
| `<nom>.longueur` | Longueur entière d'une valeur coupée ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |

- Préfixes de la norme, quel que soit celui qu'écrit le fichier : `cp`, `dc`, `dcterms`, `dcmitype` ; un espace inconnu prend `ns1`, `ns2`… ([ADR-0117](../decisions/ADR-0117-vocabulaire-des-observations.md)). Un nom tiré du fichier passe par la règle des composants : tout caractère hors des lettres ASCII, des chiffres et du tiret devient un tiret.
- Valeurs : textes tels qu'écrits ; entiers et booléens que le schéma type comme tels (`TotalTime`, `Pages`, `Words`, `Characters`, `Lines`, `Paragraphs`, `DocSecurity`… ; `ScaleCrop`, `LinksUpToDate`, `SharedDoc`, `HyperlinksChanged`) ; une écriture que le type n'admet pas reste un texte. `cp:revision` et `AppVersion` sont des textes dans le schéma.
- Propriétés personnalisées : type `docPropsVTypes` ; textes (`lpwstr`, `lpstr`, `bstr`, et `filetime`, `date` tels qu'écrits), entiers (`i1` à `i8`, `ui1` à `ui8`, `int`, `uint`), réels (`r4`, `r8`, `decimal`), booléens (`bool`), listes (`vector`, `array`, dont les `variant` sont remplacés par leur valeur), taille des binaires (`blob`, `stream`, `storage`…, base 64).
- Dates (`dcterms:created`, `dcterms:modified`, `cp:lastPrinted`) : telles qu'écrites (W3CDTF), sans conversion ; les règles de T23 lisent les deux premières par la lecture `date-iso8601` ([ADR-0148](../decisions/ADR-0148-lecture-des-dates.md)), `cp:lastPrinted` n'est pas comparée (ADR-0150).
- Propriété répétée : une liste, dans l'ordre du document. Texte vide : rien n'est observé.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Propriétés |
| --- | --- |
| `metadonnee_nominative` | `core.dc:creator`, `core.cp:lastModifiedBy`, `app.Company`, `app.Manager` |
| `nom_de_fichier` | `app.Template` (nom du modèle, parfois son chemin), `app.HyperlinkBase` (chemin ou adresse de base des liens) |
| `texte_libre` | `core.dc:title`, `core.dc:subject`, `core.dc:description`, `core.cp:keywords`, `core.cp:category`, `app.TitlesOfParts` ; toutes les propriétés personnalisées (`custom.*`), quel que soit leur type |

Le nom d'une propriété personnalisée, choisi par l'auteur, reste écrit en clair dans le nom de l'observation ([ADR-0159](../decisions/ADR-0159-lieux-nommes-et-textes-libres.md), [ADR-0160](../decisions/ADR-0160-champs-lieux-et-textes-libres.md)). Ces données sont comptées et nommées, sans leur valeur, par la rubrique « Contrôle avant publication » du rapport et par le résumé ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `Application` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. `Application` et `AppVersion` sont des déclarations du logiciel, que quiconque peut écrire (cas d'abus C-02) ; un temps d'édition nul ou une révision 1 ne disent pas qu'un texte a été généré : ils sont neutres (F-71, T81).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-OOXML-001` Générateur nommé par l'application d'un DOCX ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `ooxml.app.Application` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-OOXML-002` Date de création impossible (dcterms:created) | `ooxml.core.dcterms:created` | date impossible (`date-iso8601`) |
| `R-OOXML-003` Date de modification impossible (dcterms:modified) | `ooxml.core.dcterms:modified` | date impossible (`date-iso8601`) |
| `R-OOXML-004` Création postérieure à la modification (dcterms:created, dcterms:modified) | `ooxml.core.dcterms:created`, `ooxml.core.dcterms:modified` | certainement postérieure à `ooxml.core.dcterms:modified`, lues par `date-iso8601` |
| `R-OOXML-005` Aucune propriété de document OOXML | `ooxml.present` | faux |

Une absence de propriétés est l'observation `ooxml.present` à faux ; la règle `R-OOXML-005` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, dans les deux sens, sur un DOCX écrit par LibreOffice avec les trois parties de propriétés ([ADR-0141](../decisions/ADR-0141-oracle-bureautique-par-libreoffice.md)). Les propriétés étendues que LibreOffice n'écrit pas (`Company`, `Pages`, `HeadingPairs`…) sont vérifiées par les tests construits seulement. Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

## Limites connues

- Archive : seuls les modes stocké et deflate sont lus ; une entrée chiffrée, compressée autrement, ou dont l'en-tête local ne porte pas le nom du répertoire central est non menée ; deux entrées de même nom (sans la casse) sont non menées toutes deux ; le CRC n'est pas vérifié (ADR-0137).
- `_rels/.rels` absent ou illisible : `ooxml.present` à faux et format partiel, même si `docProps/core.xml` existe : un paquet sans relations n'en a pas, au sens d'OPC.
- Relation de propriétés externe, sans cible ou en double : non lue, non menée, sans que sa cible figure au rapport (ADR-0138) ; cible désignée mais absente de l'archive : référence manquante.
- Un DOCX chiffré par Office n'est pas une archive ZIP (format composé de Microsoft) : il n'est pas identifié comme DOCX (ADR-0070).
- Les éléments de compatibilité (`mc:AlternateContent`) ne sont pas interprétés : leurs enfants sont observés comme des propriétés d'un espace inconnu.

## Sécurité

- Archive lue en mémoire, jamais extraite sur disque (ES-05) ; lecture bornée à 16 Mio par entrée et pour le répertoire central.
- Chaque entrée du répertoire central compte un objet ; chaque élément XML, un objet et un niveau d'imbrication (ADR-0078).
- Données deflate décompressées par `Contexte.decompresser`, donc comptées dans le budget de décompression et son rapport (bombe de décompression arrêtée, ES-03).
- XML lu par expat : DOCTYPE, déclaration d'entité et entité externe refusés (ADR-0116).
- Aucune relation n'est suivie hors de l'archive, aucune adresse n'est résolue, et une relation externe ne figure pas au rapport (ES-06, M-14, ADR-0138).
- Le codec CP437 des noms d'entrées est chargé à l'import du lecteur, avant les restrictions du processus de travail (ADR-0079, ERR-0009) ; vérifié dans un vrai processus de travail.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-13 | 0.1.0 | Création (T21, complément bureautique) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
| 2026-11-14 | 0.3.0 | Titres, sujet, mots-clés et propriétés personnalisées marqués ; contrôle avant publication (T25, ADR-0158 à ADR-0163) |
