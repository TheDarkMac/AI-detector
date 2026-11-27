# Fiche technique — Métadonnées d'un document ODT

- **Module** : `odf` (version 0.3.1)
- **Tâche** : T21 (complément bureautique), T22, T23, T25
- **Exigences** : F-10, F-12, F-90, ES-05, ES-06, ES-13
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
- Ne sont pas lus : le contenu et les styles (`content.xml`, `styles.xml`), les réglages (`settings.xml`), le manifeste et les métadonnées RDF (`META-INF/manifest.xml`, `manifest.rdf`), la vignette, les signatures (T52), les modifications suivies, que lit le module `historique` (fiche [`historique-edition`](historique-edition.md), ADR-0249) ; les attributs `xlink` des métadonnées (modèle, rechargement automatique : adresses, ADR-0138), que signale le module `actifsbureau` sans leur cible, avec les macros, événements, objets et références du contenu (fiche [`actifs-bureau`](actifs-bureau.md), ADR-0229) ; la langue d'un élément (`xml:lang`).

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
- Dates et durées (`meta:creation-date`, `dc:date`, `meta:print-date`, `meta:editing-duration`) : telles qu'écrites (ISO 8601), sans conversion ; les règles de T23 lisent les deux premières par la lecture `date-iso8601` ([ADR-0148](../decisions/ADR-0148-lecture-des-dates.md)), `meta:print-date` n'est pas comparée (ADR-0150) ; le module `historique` lit la durée en minutes (fiche [`historique-edition`](historique-edition.md)).
- Élément répété (`meta:keyword`) : une liste, dans l'ordre du document. Texte vide : rien n'est observé.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Propriétés |
| --- | --- |
| `metadonnee_nominative` | `meta:initial-creator`, `dc:creator`, `meta:printed-by` |
| `texte_libre` | `dc:title`, `dc:subject`, `dc:description`, `meta:keyword` ; toutes les propriétés utilisateur (`meta:user-defined.*`), quel que soit leur type |

Le nom d'une propriété utilisateur reste écrit en clair dans le nom de l'observation ([ADR-0159](../decisions/ADR-0159-lieux-nommes-et-textes-libres.md), [ADR-0160](../decisions/ADR-0160-champs-lieux-et-textes-libres.md)). Ces données sont comptées et nommées, sans leur valeur, par la rubrique « Contrôle avant publication » du rapport et par le résumé ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)). Le chemin du modèle (`meta:template`, `xlink:href`), qui peut nommer un fichier local, n'est pas lu.

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `meta:generator` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. `meta:generator` est une déclaration du logiciel, que quiconque peut écrire (cas d'abus C-02) ; un seul cycle d'édition ou une durée nulle sont neutres (F-71) ; le module `historique` les rapporte en informations neutres (fiche [`historique-edition`](historique-edition.md)).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices fondés sur une déclaration du fichier, chacun au niveau que permet sa mesure (« Taux d'erreur ») :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-ODF-001` Générateur nommé par le générateur d'un ODT ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `odf.meta:generator` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-ODF-002` Date de création impossible (meta:creation-date) | `odf.meta:creation-date` | date impossible (`date-iso8601`) |
| `R-ODF-003` Date de modification impossible (dc:date) | `odf.dc:date` | date impossible (`date-iso8601`) |
| `R-ODF-004` Création postérieure à la modification (meta:creation-date, dc:date) | `odf.meta:creation-date`, `odf.dc:date` | certainement postérieure à `odf.dc:date`, lues par `date-iso8601` |
| `R-ODF-005` Aucune propriété de document ODF (meta.xml) | `odf.present` | faux |

Une absence de métadonnées est l'observation `odf.present` à faux ; la règle `R-ODF-005` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `odf` 0.3.1, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 2351 | 1/34 : 2,9 % [0,5 % ; 14,9 %] | 0/33 : 0,0 % [0,0 % ; 10,4 %] | — | 0 |
| Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| Transformés | 1294 | 1262 | 1/32 : 3,1 % [0,6 % ; 15,7 %] | 0/31 : 0,0 % [0,0 % ; 11,0 %] | — | 0 |
| Retouchés | 273 | 264 | 1/9 : 11,1 % [2,0 % ; 43,5 %] | — | 8/8 : 100,0 % [67,6 % ; 100,0 %] | 0 |
| Malformés | 91 | 67 | 22/24 : 91,7 % [74,2 % ; 97,7 %] | 0/2 : 0,0 % [0,0 % ; 65,8 %] | — | 0 |

| Règle | Catégorie | Direction | Faux positifs | Niveau permis | Niveau |
| --- | --- | --- | --- | --- | --- |
| R-ODF-001 v2 | indice | origine_ia | 0/33 : 0,0 % [0,0 % ; 10,4 %] | faible | faible |

<!-- Fin des taux mesurés. -->

Le niveau de chaque indice est celui que permet son taux de faux positifs, mesuré ci-dessus (ADR-0018, [ADR-0278](../decisions/ADR-0278-evaluation-et-niveau-des-indices-au-catalogue.md)). Le déclenchement des règles est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, dans les deux sens, sur un ODT écrit par LibreOffice ([ADR-0141](../decisions/ADR-0141-oracle-bureautique-par-libreoffice.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

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
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
| 2026-11-14 | 0.3.0 | Titre, sujet, mots-clés et propriétés utilisateur marqués ; contrôle avant publication (T25, ADR-0158 à ADR-0163) |
| 2026-11-17 | 0.3.0 | Renvoi : macros, événements, objets et références hors de l'archive signalés par `actifsbureau` (T52, complément bureautique, ADR-0228, ADR-0229) ; module inchangé |
| 2026-11-17 | 0.3.1 | Encodage déclaré qu'expat ne lit pas : lecture partielle au lieu d'une erreur du module (ERR-0012, T52, complément bureautique) |
| 2026-11-23 | 0.3.1 | Renvoi : durée et cycles d'édition, identifiants de session, modifications suivies et commentaires lus par `historique` (T81, ADR-0248, ADR-0249) |
