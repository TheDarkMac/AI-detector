# Fiche technique — Versions successives d'un PDF

- **Module** : `revisionspdf` (version 0.2.0)
- **Tâche** : T50 ; objets un par un : T51
- **Exigences** : F-60, F-61, F-84
- **Formats** : `pdf`
- **Directions permises** : `retouche`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Combien de versions successives le PDF garde-t-il, que change chacune, objet par objet, et quelle version une signature couvre-t-elle ?

## Principe

Un PDF peut être enregistré par mise à jour incrémentale (ISO 32000-2, §7.5.6) : les objets changés, une section de références croisées et un trailer dont `/Prev` désigne la section précédente s'ajoutent à la fin du fichier, suivis de `startxref` et de `%%EOF`. Rien n'est effacé : la version *k* est le début du fichier, jusqu'à sa marque `%%EOF`. Les logiciels de signature, de formulaire et d'annotation, Acrobat en enregistrement rapide, exiftool pour les métadonnées enregistrent ainsi.

Le module :

1. **Versions** ([ADR-0207](../decisions/ADR-0207-versions-d-un-pdf.md)) : il lit la chaîne des sections depuis le dernier `startxref`, par le lecteur du projet ([ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md)), et en fait une version par section. Une linéarisation (annexe F : premier objet `/Linearized`, table de la première page au début du fichier, dont `/Prev` désigne la table principale) ne fait qu'une version ; une table complétée par un flux (`/XRefStm`) aussi. La fin de chaque version est celle du `%%EOF` qui suit son `startxref`, fin de ligne comprise.
2. **Nature** ([ADR-0208](../decisions/ADR-0208-nature-d-une-version.md)) : il compare les entrées de chaque version à celles de la précédente (objets ajoutés, remplacés, supprimés), range chaque objet changé d'après son type, les clés du catalogue qui changent, les annotations d'une page et ce qui désigne l'objet, et en tire la nature de la version : signature, formulaire, annotation, métadonnées, non reconnue, non lue, ou structure seulement.
3. **Signatures** ([ADR-0209](../decisions/ADR-0209-signatures-pdf-par-leur-structure.md)) : pour chaque champ de signature du formulaire, la version dont la fin est celle de la plage signée (`/ByteRange`), et si cette plage est complète : elle part du début du fichier, ne laisse de côté qu'une chaîne hexadécimale (la valeur `/Contents`) et finit à la fin d'une version. La signature n'est pas vérifiée cryptographiquement.
4. **Chronologie** ([ADR-0212](../decisions/ADR-0212-chronologie-en-tableau.md)) : un tableau, une ligne par version.
5. **Objets un par un** ([ADR-0217](../decisions/ADR-0217-objets-changes-un-par-un.md), T51) : un second tableau, une ligne par objet que change une version postérieure à la première : son numéro, sa génération, son état (ajouté, remplacé, supprimé), son type (`/Type` et `/Subtype`, à défaut sa forme), sa nature au sens du point 2 et la première page qui le désigne (la page elle-même, ses flux de contenu, ses annotations, ses ressources, ses polices, ses objets externes).

Sur les échantillons de `tests/donnees/revisions` (`generer_revisions.py`) :

| Échantillon | Écrit par | Natures des versions |
| --- | --- | --- |
| `formulaire.pdf` | Ghostscript, puis pyHanko : champ de texte, champ de signature, champ rempli | originale ; formulaire + métadonnées ; signature + formulaire + métadonnées ; formulaire + métadonnées |
| `signe.pdf` | `formulaire.pdf` signé par pyHanko | … ; signature + formulaire + métadonnées |
| `signe_annote.pdf` | `signe.pdf`, puis une note de texte | … ; annotation + métadonnées |
| `signe_modifie.pdf` | `signe.pdf`, puis un flux de contenu ajouté à la page | … ; métadonnées + non reconnue |
| `modifie.pdf` | LibreOffice, puis un flux de contenu ajouté | originale ; métadonnées + non reconnue |
| `certifie.pdf` | Ghostscript, certifié par pyHanko (DocMDP 1) | originale ; signature + formulaire + métadonnées |
| `lineaire.pdf`, `lineaire_maj.pdf` | Ghostscript linéarisé ; puis exiftool | originale ; métadonnées |

pyHanko écrit son nom dans le producteur du dictionnaire Info à chaque mise à jour, d'où les métadonnées dans chaque version.

Oracle (`oracle.json`) : pyHanko 0.38.1 et `pdfsig` de Poppler 25.03.0 donnent, pour chaque signature, la même fin de plage, la même intégrité et la même couverture du document entier que le module ; pyHanko compte une révision de plus pour un document linéarisé (ses deux sections), écart attendu. Sa politique de modifications par défaut range l'ajout d'une note de texte parmi les modifications « OTHER », que le module reconnaît comme annotation.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| PDF | Chaîne des sections de références croisées (tables classiques, flux, sections hybrides) et leurs entrées ; marques `startxref` et `%%EOF` qui suivent chaque section ; premier objet du fichier ; objets changés par chaque version et leur ancienne valeur s'il le faut ; catalogue de chaque version ; dictionnaire Info de chaque version (dates) ; arbre des champs du formulaire de la dernière version et dictionnaires de signature ; octets laissés de côté par chaque plage signée (1 Mio au plus) |

Aucune donnée de référence.

## Sorties

| Observation | Forme |
| --- | --- |
| `revisionspdf.versions` | Nombre de versions |
| `revisionspdf.sections` | Nombre de sections de la chaîne |
| `revisionspdf.chiffre` | Vrai si le trailer désigne un dictionnaire de chiffrement |
| `revisionspdf.linearise` | Vrai si le premier objet est un dictionnaire de linéarisation |
| `revisionspdf.linearisation.longueur` | Sa clé `/L` : longueur déclarée du fichier linéarisé, en octets |
| `revisionspdf.fins` | Fin de chaque version, en octets, de la plus ancienne à la plus récente |
| `revisionspdf.natures` | Nature de chaque version : `originale`, `structure`, ou codes `signature`, `formulaire`, `annotation`, `metadonnees`, `non_reconnue`, `non_lue` joints par `+` |
| `revisionspdf.ajoutes`, `.remplaces`, `.supprimes` | Objets ajoutés, remplacés, supprimés par chaque version (structure comprise : section en flux, flux d'objets) |
| `revisionspdf.sans_marque_de_fin` | Sections sans `startxref` et `%%EOF` après elles, s'il y en a |
| `revisionspdf.octets_apres_fin` | Octets qui suivent la fin de la dernière version |
| `revisionspdf.versions_non_reconnues` | Versions postérieures à la première qui changent des objets non reconnus |
| `revisionspdf.signatures` | Signatures du formulaire |
| `revisionspdf.signature.<n>.version`, `.plage_complete`, `.sous_filtre`, `.date` | Pour les 32 premières : version couverte (0 si aucune), plage complète, `/SubFilter`, `/M` |
| `revisionspdf.docmdp` | Droits d'une signature de certification : 1, 2 ou 3 |
| `revisionspdf.derniere_version_signee`, `revisionspdf.non_reconnues_apres_signature` | Dernière version couverte par une plage complète ; versions suivantes qui changent des objets non reconnus |
| `revisionspdf.objets` | Objets changés par les versions postérieures à la première, tous comptés |

Les listes ont une valeur par version, coupées au besoin, leur longueur entière observée à part (`<nom>.longueur`).

Visualisation `chronologie_revisions`, dès deux versions : une ligne par version (256 au plus) avec sa fin, sa nature, ses objets ajoutés, remplacés et supprimés, sa date déclarée (`/ModDate` du dictionnaire Info quand elle change, `/CreationDate` à défaut pour la première) et ses signatures. Elle est rendue en tableau dans la rubrique « Visualisations », sous son avertissement, et n'est pas masquée.

Visualisation `objets_revisions`, dès qu'une version postérieure change un objet : une ligne par objet changé (256 au plus, dans l'ordre des versions puis des numéros), colonnes `version`, `objet`, `generation`, `etat`, `type`, `nature`, `page` (0 si aucune page ne le désigne). Rendue en tableau sous la chronologie, avec son avertissement, non masquée.

## Données identifiantes

Aucune : le module n'observe ni auteur, ni titre, ni nom de champ. Les versions antérieures peuvent pourtant garder des métadonnées identifiantes qu'une version ultérieure semble avoir retirées : le contrôle avant publication ne lit que la dernière version (limite de R-REVISIONSPDF-001).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Un document écrit d'un seul tenant n'a qu'une version ; un document signé, rempli ou annoté en garde plusieurs, de nature permise |
| Transformation banale (recompression, redimensionnement) | Une réécriture complète (« Enregistrer sous », optimisation, impression en PDF) efface les versions : rien à en dire |
| Retouche | Une version postérieure qui change des objets non reconnus, en particulier après une signature, est compatible avec une retouche ; elle l'est aussi avec une correction par l'auteur |
| Génération | La technique ne dit rien d'une origine IA |

## Ce qui déclenche un constat

Le module n'émet aucun constat ; trois règles « moteur » du catalogue lisent ses observations ([ADR-0211](../decisions/ADR-0211-constats-et-versions-de-t50.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-REVISIONSPDF-001 | `revisionspdf.versions` ≥ 2 | Information neutre |
| R-REVISIONSPDF-002 | `revisionspdf.versions_non_reconnues` ≥ 1 | Indice vers la retouche |
| R-REVISIONSPDF-003 | `revisionspdf.derniere_version_signee` présente et `revisionspdf.non_reconnues_apres_signature` ≥ 1 | Indice vers la retouche |

## Taux d'erreur

<!-- Taux mesurés : écrits par « python -m banc.fiches --taux », pas à la main. -->

Mesurés le 2026-11-27 par le banc, sur la partie évaluation du corpus reference 1.0.0 ([rapport](../verification/evaluations/reference-1.0.0-catalogue-0.21.0/evaluation.md)) : module `revisionspdf` 0.2.0, outil 0.1.0.dev0, catalogue 0.21.0. Chaque taux est donné avec son effectif et son intervalle de Wilson à 95 % ; un tiret marque un taux sans effectif. Les définitions sont celles d'[ADR-0104](../decisions/ADR-0104-definition-des-mesures.md).

| Catégorie | Fichiers | Non applicables | Non analysables | Faux positifs | Faux négatifs | Confusions |
| --- | --- | --- | --- | --- | --- | --- |
| Authentiques | 2385 | 1985 | 1/400 : 0,2 % [0,0 % ; 1,4 %] | 54/399 : 13,5 % [10,5 % ; 17,2 %] | — | 0 |
| Générés | 424 | 398 | 0/26 : 0,0 % [0,0 % ; 12,9 %] | — | 26/26 : 100,0 % [87,1 % ; 100,0 %] | 0 |
| Transformés | 1294 | 1178 | 0/116 : 0,0 % [0,0 % ; 3,2 %] | 0/116 : 0,0 % [0,0 % ; 3,2 %] | — | 0 |
| Retouchés | 273 | 230 | 0/43 : 0,0 % [0,0 % ; 8,2 %] | — | 43/43 : 100,0 % [91,8 % ; 100,0 %] | 0 |
| Malformés | 91 | 57 | 28/34 : 82,4 % [66,5 % ; 91,7 %] | 0/6 : 0,0 % [0,0 % ; 39,0 %] | — | 0 |

| Règle | Catégorie | Direction | Faux positifs | Niveau permis | Niveau |
| --- | --- | --- | --- | --- | --- |
| R-REVISIONSPDF-002 v2 | indice | retouche | 54/399 : 13,5 % [10,5 % ; 17,2 %] | faible | faible |
| R-REVISIONSPDF-003 v2 | indice | retouche | 0/399 : 0,0 % [0,0 % ; 1,0 %] | fort | fort |

<!-- Fin des taux mesurés. -->

Sur le corpus de référence (tableau ci-dessus), R-REVISIONSPDF-002 se déclenche sur 54 des 399 PDF authentiques analysés : beaucoup de documents ordinaires sont mis à jour après leur première version, et la règle reste « faible » ; R-REVISIONSPDF-003 passe à « fort » ([ADR-0101](../decisions/ADR-0101-bornes-des-niveaux-et-cible.md)). Le classement a été vérifié sur les huit échantillons ci-dessus et sur des documents synthétiques des tests.

## Limites connues

- Seule la chaîne déclarée est lue : une section que la chaîne ne désigne plus n'est pas une version ; des données ajoutées après la dernière marque ne sont que comptées. Une structure illisible n'est pas réparée ([ADR-0125](../decisions/ADR-0125-lecture-stricte-du-pdf.md)).
- Le classement suit le type des objets et ce qui les désigne, pas ce qu'ils affichent : une apparence d'annotation ou de formulaire qui recouvre le contenu passe pour un ajout permis. Les attaques « par ombre » (Mainka, Mladenov et Rohlmann, NDSS 2021) préparent dans la version signée un contenu caché qu'une telle mise à jour révèle.
- Un ajout légitime d'un type non prévu (une clé du catalogue qu'écrit un logiciel, un objet propre à un éditeur) est non reconnu.
- Un objet ajouté que rien ne désigne depuis le catalogue ou le dictionnaire Info compte comme structure ; le parcours qui le cherche s'arrête à 65 536 objets (l'objet est alors non lu).
- Les signatures ne sont pas vérifiées ; les droits DocMDP sont observés, pas comparés aux changements ; une signature dont le champ a été retiré n'est pas vue.
- Document chiffré : rien n'est déchiffré ([ADR-0210](../decisions/ADR-0210-versions-d-un-pdf-chiffre.md)) ; les objets rangés dans des flux d'objets ne se lisent pas, ni les dates.
- Les dates sont déclarées par le logiciel : elles se falsifient, et beaucoup de logiciels ne mettent pas `/ModDate` à jour (exiftool la laisse telle quelle).

## Sécurité

Mêmes protections que le lecteur PDF du projet : lecture stricte, aucune exécution, aucun flux d'un autre fichier, `FlateDecode` seul par `Contexte.decompresser`. Chaque entrée énumérée, chaque objet lu et chaque objet parcouru comptent dans le budget du module (ES-03) ; imbrication bornée. Chaque version est relue dans une vue distincte, objets relus à la demande. Le relevé des pages qui désignent les objets changés parcourt au plus 65 536 objets de l'arbre des pages par version, et seulement pour les versions dont des objets figurent au tableau. Rien n'est écrit : la reconstitution d'une version est une plage d'octets au rapport.

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-16 | 0.1.0 | Création |
| 2026-11-17 | 0.2.0 | Objets changés un par un, en tableau (T51, ADR-0217) ; F-61 |
