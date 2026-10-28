# ADR-0116 — XML de XMP lu par expat, DTD refusée ; `defusedxml` écarté

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T20
- **Exigences liées** : ES-05, ES-18, NF-01, NF-02 ; menaces M-02, M-04, M-14 ; ADR-0043 ; architecture §9 et §12

## Contexte

XMP est du XML. Un lecteur XML naïf expose à trois attaques du modèle de menace : la bombe d'entités (« milliard de rires », M-02), l'entité externe qui lit un fichier local ou appelle une adresse (M-04, M-14), la DTD externe chargée par le réseau. ES-05 demande un XML lu « sans DTD, sans entités externes ni résolution réseau ». ADR-0043 retenait `defusedxml` comme candidate, et l'architecture (§9, §12) laissait à T20 un point ouvert : cette bibliothèque n'a plus de version depuis mars 2021 (0.7.1), et T20 devait la comparer aux protections actuelles de la bibliothèque standard.

État de la bibliothèque standard, vérifié pour T20 : `xml.parsers.expat` lie expat (2.9.0 sur le poste de T20) ; depuis expat 2.4.1, la bombe d'entités et l'expansion quadratique sont bornées par expat lui-même (documentation de Python, « XML vulnerabilities ») ; expat ne charge aucune DTD externe ni entité externe sans gestionnaire fourni par le programme. `defusedxml` ajoute, au-dessus d'expat, des gestionnaires qui refusent les déclarations d'entité et de DTD.

## Options envisagées

### Option A — expat de la bibliothèque standard, DTD refusée

Gestionnaires qui lèvent une erreur dès une déclaration de type de document (DOCTYPE), une déclaration d'entité ou une référence à une entité externe ; entités paramètres jamais lues.

- Avantages : aucune dépendance ; le refus est plus strict que celui de `defusedxml` (tout DOCTYPE, pas seulement les entités) ; quelques lignes, testées et soumises au fuzzing ; la version d'expat est connue et peut figurer au rapport.
- Inconvénients : la protection est écrite par le projet ; un défaut d'expat lui-même reste possible (code C).

### Option B — `defusedxml`

- Avantages : protection reconnue, prévue par ADR-0043.
- Inconvénients : bibliothèque sans version depuis 2021 (critère « maintenue » d'ADR-0043) ; elle s'appuie sur le même expat, sans rien retirer du code C exposé ; une dépendance de plus à examiner et à inscrire au rapport.

## Décision

Option A, dans `modules/_lecture/xmp.py` :

- `ParserCreate(namespace_separator=" ")`, `SetParamEntityParsing(XML_PARAM_ENTITY_PARSING_NEVER)` ;
- `StartDoctypeDeclHandler`, `EntityDeclHandler` et `ExternalEntityRefHandler` lèvent une erreur qui arrête la lecture : le paquet est non mené pour format partiel, ce qui a été lu avant l'erreur reste observé ;
- chaque élément compte un objet et chaque niveau un niveau d'imbrication dans le budget du module (ADR-0078) ;
- expat est déclaré par le manifeste de `xmp` et sa version réelle figure à la rubrique Versions (ADR-0120).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : non maintenue, et sans protection que l'option A n'ait pas ; ADR-0043 (point 6) prévoit qu'un écart à sa liste soit consigné dans l'ADR de la tâche, ce que fait celui-ci.
- DOCTYPE refusé en entier : le RDF/XML d'un paquet XMP n'emploie pas de DTD, et aucun des échantillons de l'oracle n'en porte ; sans DTD, aucune entité ne peut être définie, donc aucune ne peut être développée, quelle que soit la version d'expat.

## Conséquences

- `defusedxml` sort de la liste des dépendances candidates (architecture §9) ; T21 lira le XML de DOCX et ODT de la même façon, par un nouvel ADR s'il faut s'en écarter.
- Le point « Maintenance de `defusedxml` » de l'architecture (§12) est clos.
- Une version d'expat antérieure à 2.4.1 n'affaiblirait pas la protection (aucune entité possible), mais elle est visible au rapport.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
