# Fiche technique — Éléments actifs d'un DOCX ou d'un ODT

- **Module** : `actifsbureau` (version 0.1.0)
- **Tâche** : T52 (complément bureautique)
- **Exigences** : F-62, NF-01, ES-06
- **Formats** : `docx`, `odt`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`

## Question

Le document bureautique porte-t-il des éléments qu'un traitement de texte exécuterait, activerait ou irait chercher hors du document : macros, événements liés à une macro, objets incorporés qu'un autre programme ouvre, ressources hors de l'archive (modèle distant, image liée, lien) ? L'outil les signale, et n'en exécute, n'en ouvre ni n'en suit aucun (F-62, NF-01, ES-06).

## Principe

Le module suit le document comme le logiciel le lit ([ADR-0229](../decisions/ADR-0229-elements-actifs-cherches-dans-un-docx-et-un-odt.md)), par le lecteur ZIP du projet ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)) et le lecteur XML par expat, sans DTD ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)), qui lit ici élément par élément, sans garder l'arbre d'une partie.

**DOCX.** Les relations du paquet (`_rels/.rels`), puis celles de chaque partie qu'elles désignent dans l'archive, de proche en proche (ECMA-376, partie 2, §9 : les relations de `word/document.xml` sont dans `word/_rels/document.xml.rels`). Au niveau du paquet, seules la partie principale (`officeDocument`) et l'extension du ruban sont suivies ; les propriétés, la vignette et les signatures ne portent rien d'actif. Une relation compte selon son type :

| Relation (type) | Cible | Famille, nature | Déclencheur |
| --- | --- | --- | --- |
| `vbaProject` ([MS-OFFMACRO]) | Dans l'archive | `macros`, `VBA` | — |
| `ui/extensibility` ([MS-CUSTOMUI], 2006 et 2007) | Dans l'archive | `macros`, `ruban` | — |
| `control` | Dans l'archive | `objets`, `ActiveX` | — |
| `oleObject` | Dans l'archive | `objets`, `OLE` | — |
| `package` (sauf depuis un graphique, qui y range ses données) | Dans l'archive | `objets`, `paquet` | — |
| `attachedTemplate` | Hors de l'archive | `externes`, `modèle` | `ouverture` |
| `image` | Hors de l'archive | `externes`, `image` | `ouverture` |
| `frame` | Hors de l'archive | `externes`, `cadre` | `ouverture` |
| `oleObject` | Hors de l'archive | `externes`, `objet` | `ouverture` |
| `mailMergeSource`, `mailMergeHeaderSource`, `recipientData` | Hors de l'archive | `externes`, `source de données` | `ouverture` |
| `subDocument` | Hors de l'archive | `externes`, `sous-document` | `utilisateur` |
| `hyperlink` | Hors de l'archive | `externes`, `lien` | `utilisateur` |
| Tout autre type | Hors de l'archive (`TargetMode="External"`) | `externes`, `autre` | — |

Les types sont reconnus dans les espaces transitionnel et strict d'ECMA-376 et dans ceux de Microsoft (2006, 2007). Un élément actif dont la partie manque à l'archive n'est pas compté : référence manquante.

**ODT.** OpenDocument 1.3, parties 3 (paquet) et 4 (schéma) :

| Où | Ce qui est lu | Famille, nature | Déclencheur |
| --- | --- | --- | --- |
| Noms des entrées `Basic/<bibliothèque>/…` | Une bibliothèque Basic qui a un module (une entrée autre que les index `script-lb.xml`, `script-lc.xml`, `dialog-lb.xml`, `dialog-lc.xml`) | `macros`, `Basic` | — |
| Noms des entrées `Scripts/<langage>/…` | Les scripts d'un langage : `python`, `javascript`, `beanshell`, `java`, `basic` ; un autre dossier est `autre` | `macros`, `Python`… | — |
| `content.xml`, `styles.xml` : `script:event-listener` sous `office:scripts` de la racine | Un événement du document lié à une macro ; `dom:load`, `office:new`, `office:create`, `office:load-finished`, `office:view-created`, `office:layout-finished` sont levés à l'ouverture | `evenements`, `macro` | `ouverture` ou `document` |
| Même partie : tout autre `script:event-listener` | Événement d'un contrôle de formulaire, d'un lien, d'une image | `evenements`, `macro` | `utilisateur` |
| Même partie : `xlink:href` de schéma `macro:` ou `vnd.sun.star.script:` | Un lien ou un bouton qui appelle une macro | `evenements`, `macro` | `utilisateur` |
| Même partie : `draw:object-ole`, `draw:applet`, `draw:plugin` | Un objet OLE, une applet, un module externe | `objets`, `OLE`, `applet`, `plugin` | — |
| Même partie : `draw:object` dans l'archive | Un document incorporé, sauf un graphique ou une formule (type lu dans `META-INF/manifest.xml`) | `objets`, `document` | — |
| Même partie : `text:dde-connection-decl`, `office:dde-source` | Une connexion DDE ; mise à jour automatique (`office:automatic-update`) ou non | `externes`, `DDE` | `ouverture` ou `utilisateur` |
| `content.xml`, `styles.xml`, `meta.xml` : `xlink:href` hors de l'archive | Une référence qui sort du paquet : adresse à schéma (sauf `vnd.sun.star.Package:` et `vnd.sun.star.GraphicObject:`, internes), chemin absolu, chemin qui remonte au-dessus du paquet (`../`) | `externes`, selon l'élément | selon l'élément |

Natures des références hors de l'archive : `draw:image`, `draw:fill-image`, `style:background-image` → `image` ; `draw:object`, `draw:object-ole` → `objet` ; `draw:floating-frame` → `cadre` ; `text:section-source` → `section` ; `meta:template` → `modèle` ; `meta:auto-reload` → `rechargement`, tous à l'`ouverture` ; `text:a`, `draw:a`, `form:button` → `lien`, au geste de l'`utilisateur` ; tout autre élément → `autre`, sans déclencheur. Un manifeste qui déclare des entrées chiffrées (`manifest:encryption-data`, document protégé par mot de passe) le fait dire (`actifsbureau.chiffre`) ; les parties chiffrées ne se lisent pas, les noms des entrées si.

Chaque élément est décrit par sa **nature**, en liste fermée, et son **déclencheur** ([ADR-0230](../decisions/ADR-0230-nature-et-declencheur-des-elements-bureautiques.md)). Ni adresse, ni chemin, ni nom de macro, de module ou de bibliothèque, ni code n'est lu ni observé ; le projet VBA (un fichier composé OLE) n'est pas ouvert. Les éléments sont rangés en familles ([ADR-0231](../decisions/ADR-0231-constats-et-versions-du-complement-bureautique-de-t52.md)) : `macros`, `evenements`, `objets`, `externes` ; et `automatiques`, tout élément de déclencheur `ouverture` ou `document`, quelle que soit sa famille.

Sur les échantillons de `tests/donnees/actifsbureau` (`generer_actifsbureau.py`), tous écrits par LibreOffice 25.2.3.2 :

| Échantillon | Contenu | Relevé |
| --- | --- | --- |
| `macros.odt` | Une bibliothèque Basic, liée à l'ouverture et à l'enregistrement ; un bouton qui l'appelle | une bibliothèque `Basic` ; trois événements (`ouverture`, `document`, `utilisateur`), deux automatiques |
| `liens.odt` | Un lien vers un site, une image liée, une section liée, un modèle, un rechargement automatique | cinq références hors de l'archive (`modèle`, `image`, `section`, `rechargement`, `lien`), quatre à l'`ouverture` |
| `liens.docx` | Le même, enregistré en DOCX (LibreOffice n'y écrit ni la section, ni le modèle, ni le rechargement) | deux relations externes (`image` à l'`ouverture`, `lien`) |
| `objet.odt` | Un tableur incorporé | un objet `document` |
| `objet.docx` | Le même, enregistré en DOCX (`package`) | un objet `paquet` |

Les échantillons `document.docx` et `document.odt` de `tests/donnees/metadonnees` ne portent rien.

Oracle (`oracle.json`) : LibreOffice relit chaque échantillon et dit ses bibliothèques Basic qui ont un module, ses événements du document liés à une macro, les événements de ses contrôles, son modèle et son rechargement, ses sections liées, ses images liées, ses objets incorporés et ses liens vers une adresse ; le module trouve les mêmes nombres. Les projets VBA, contrôles ActiveX, objets OLE, modèles distants d'un DOCX, scripts Python et connexions DDE, que LibreOffice n'écrit pas ainsi, sont vérifiés sur des documents construits par les tests.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| DOCX | Répertoire central de l'archive ; relations (`*.rels`) du paquet et des parties suivies : leurs types, leurs modes et leurs cibles, résolues dans l'archive mais jamais observées. Aucune autre partie : ni le corps, ni les réglages, ni le projet VBA, ni les objets incorporés. |
| ODT | Noms des entrées de l'archive ; `META-INF/manifest.xml` (types et chiffrement des entrées) ; `content.xml`, `styles.xml` et `meta.xml`, élément par élément : noms des éléments, `script:event-name`, `office:automatic-update`, et les seuls schéma ou forme des `xlink:href`, jamais retenus. Ni le texte, ni le code, ni les documents incorporés. |

## Sorties

| Observation | Forme |
| --- | --- |
| `actifsbureau.parties` | Parties lues : fichiers de relations (DOCX) ; manifeste et parties XML (ODT) |
| `actifsbureau.macros`, `.natures` | Ensembles de macros : projet VBA, ruban, bibliothèque Basic, scripts d'un langage |
| `actifsbureau.evenements`, `.natures`, `.declencheurs` | Événements liés à une macro, et leurs déclencheurs (dans l'ordre `ouverture`, `document`, `utilisateur`) |
| `actifsbureau.objets`, `.natures` | Objets incorporés qu'un autre programme active ou ouvre |
| `actifsbureau.externes`, `.natures`, `.declencheurs` | Ressources hors de l'archive |
| `actifsbureau.automatiques`, `.natures`, `.declencheurs` | Éléments déclenchés ou chargés sans geste de l'utilisateur ; leurs seuls déclencheurs automatiques |
| `actifsbureau.chiffre` | Vrai pour un ODT dont le manifeste déclare des entrées chiffrées |
| `actifsbureau.arret_avant_budget` | Vrai si la recherche s'est arrêtée pour garder du budget |
| `actifsbureau.recherche_coupee` | Vrai si une limite (parties, éléments) a été atteinte |

## Données identifiantes

Aucune : le module n'observe que des natures, des déclencheurs et des nombres ; ni adresse, ni chemin, ni nom, ni texte ([ADR-0230](../decisions/ADR-0230-nature-et-declencheur-des-elements-bureautiques.md)). Les propriétés qui nomment un modèle (`ooxml.app.Template`) restent lues par `ooxml`, marquées nom de fichier (ADR-0140).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien : un élément actif ne dit rien de l'origine du contenu |
| Transformation banale (conversion, réenregistrement) | Rien : une conversion peut perdre des éléments (LibreOffice n'écrit pas de macros Basic dans un DOCX) |
| Retouche | Rien |
| Génération | Rien |

Les constats sont des informations neutres, de direction « rien de particulier » : ils disent ce que le document demande à un traitement de texte, et que l'outil ne l'a pas fait.

## Ce qui déclenche un constat

Le module n'émet aucun constat ; quatre règles « moteur » du catalogue lisent ses observations ([ADR-0231](../decisions/ADR-0231-constats-et-versions-du-complement-bureautique-de-t52.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-ACTIFSBUREAU-001 | `actifsbureau.macros` ≥ 1 | Information neutre : ensembles de macros, et leurs natures |
| R-ACTIFSBUREAU-002 | `actifsbureau.automatiques` ≥ 1 | Information neutre : éléments déclenchés ou chargés sans geste de l'utilisateur, leurs déclencheurs et leurs natures |
| R-ACTIFSBUREAU-003 | `actifsbureau.objets` ≥ 1 | Information neutre : objets incorporés qu'un autre programme ouvre |
| R-ACTIFSBUREAU-004 | `actifsbureau.externes` ≥ 1 | Information neutre : ressources hors de l'archive, jamais suivies |

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `actifsbureau` 0.1.0, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 2298 | 1/87 : 1,1 % [0,2 % ; 6,2 %] | 0/86 : 0,0 % [0,0 % ; 4,3 %] | — | 0 |
| Générés | 424 | 372 | 0/52 : 0,0 % [0,0 % ; 6,9 %] | — | 52/52 : 100,0 % [93,1 % ; 100,0 %] | 0 |
| Transformés | 1294 | 1210 | 1/84 : 1,2 % [0,2 % ; 6,4 %] | 0/83 : 0,0 % [0,0 % ; 4,4 %] | — | 0 |
| Retouchés | 273 | 233 | 1/40 : 2,5 % [0,4 % ; 12,9 %] | — | 39/39 : 100,0 % [91,0 % ; 100,0 %] | 0 |
| Malformés | 91 | 61 | 22/30 : 73,3 % [55,6 % ; 85,8 %] | 0/8 : 0,0 % [0,0 % ; 32,4 %] | — | 0 |

Aucune règle de preuve ou d'indice : les règles du module sont des informations neutres, sans taux.

<!-- Fin des taux mesurés. -->

Sans objet pour une information neutre qui compte ce que le document déclare. Les relevés ont été vérifiés sur les cinq échantillons ci-dessus, contre LibreOffice, et sur des documents synthétiques des tests. La part de documents ordinaires qui déclenchent chaque règle (R-ACTIFSBUREAU-004 sur tout document qui a des liens vers une adresse) n'est pas mesurée par le banc, qui ne compte que les preuves et les indices ([ADR-0104](../decisions/ADR-0104-definition-des-mesures.md)).

## Limites connues

- Le corps d'un DOCX n'est lu que par ses relations : les codes de champ (`DDEAUTO`, `INCLUDEPICTURE`, `INCLUDETEXT`), qui peuvent lancer un programme ou charger une ressource, ne sont pas lus ([ADR-0229](../decisions/ADR-0229-elements-actifs-cherches-dans-un-docx-et-un-odt.md)).
- Le projet VBA n'est pas ouvert : le module ne dit ni combien il a de modules, ni si une macro se lance seule (`AutoOpen`, `Document_Open`, que seul le code nomme).
- Les relations sont suivies de proche en proche, quel que soit le type de la partie qui les porte : un projet VBA désigné depuis une autre partie que le document principal, que Word ne chargerait pas, est compté.
- Un événement attaché à autre chose que le document (contrôle, image, cadre) est compté au geste de l'`utilisateur`, même si le logiciel peut le lever seul (image chargée).
- Les documents incorporés d'un ODT (`Object 1/`) ne sont pas parcourus : leurs propres éléments actifs ne sont pas comptés ; un champ de script (`text:script`) n'est pas compté, LibreOffice ne l'exécutant pas.
- Une bibliothèque Basic liée (`library:link`), rangée hors du document, n'est pas lue : `Basic/script-lc.xml` n'est pas ouvert.
- ODT protégé par mot de passe : ses parties XML ne se lisent pas, et chacune est non menée (`format_partiel`) ; les noms des entrées, donc les bibliothèques Basic et les scripts, se lisent.
- Au plus 4 096 parties suivies d'un DOCX et 65 536 éléments ; la recherche s'arrête quand il ne reste plus que 262 144 objets du budget du module, pour que les observations déjà faites soient envoyées.

## Sécurité

Le module lit des noms d'entrées et des parties XML, sans DTD ni entité ; aucune macro n'est interprétée, aucun objet n'est ouvert, aucune référence n'est suivie, aucune adresse n'est résolue (ES-06, [ADR-0033](../decisions/ADR-0033-politique-des-requetes-sortantes.md), [ADR-0138](../decisions/ADR-0138-relations-et-references-non-suivies.md)) ; le processus de travail n'a d'ailleurs ni réseau ni accès aux fichiers (ADR-0083). Les parties d'un DOCX sont suivies sans récursion, chacune une fois ; chaque élément XML, entrée d'archive et élément actif compte un objet du budget (ES-03), et chaque décompression contre son budget de décompression.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-17 | 0.1.0 | Création |
