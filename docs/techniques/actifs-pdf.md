# Fiche technique — Éléments actifs d'un PDF

- **Module** : `actifspdf` (version 0.1.0)
- **Tâche** : T52
- **Exigences** : F-62, NF-01, ES-06
- **Formats** : `pdf`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Le PDF porte-t-il des éléments qu'un lecteur exécuterait ou ouvrirait : scripts, actions déclenchées sans geste de l'utilisateur, lancement d'un programme ou ouverture d'un autre fichier, envoi d'un formulaire ou ouverture d'une adresse, fichiers incorporés ? L'outil les signale, et n'en exécute, n'en ouvre ni n'en résout aucun (F-62, NF-01, ES-06).

## Principe

Le module part du catalogue de la dernière version, comme un lecteur ([ADR-0221](../decisions/ADR-0221-elements-actifs-depuis-le-catalogue.md)), par le lecteur PDF du projet ([ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md)), et parcourt :

| Où | Ce qui est lu (ISO 32000-2) | Déclencheur |
| --- | --- | --- |
| Catalogue, `/OpenAction` | L'action d'ouverture, si c'est une action et non une destination (§12.3.2, §12.6.2) | `ouverture` |
| Catalogue, `/Names` `/JavaScript` | Les scripts au niveau du document, valeurs de l'arbre de noms (§7.7.4, §7.9.6) | `ouverture` |
| Catalogue, `/AA` | Fermeture, enregistrement, impression du document (`WC`, `WS`, `DS`, `WP`, `DP` ; §12.6.3) | `document` |
| Page, `/AA` | Ouverture et fermeture de la page (`O`, `C`) | `page` |
| Annotation, `/AA` | Page ouverte ou fermée, annotation visible ou invisible (`PO`, `PC`, `PV`, `PI`) | `page` |
| Champ ou annotation, `/AA` | Mise en forme et calcul d'un champ (`F`, `C`) | `champ` |
| Champ ou annotation, `/AA` | Entrée et sortie du pointeur, clic, focus, saisie, validation (`E`, `X`, `D`, `U`, `Fo`, `Bl`, `K`, `V`) | `utilisateur` |
| Annotation, `/A` ; signet, `/A` | L'action d'un lien, d'un bouton, d'un signet (§12.5.6.5, §12.3.3) | `utilisateur` |
| Toute action, `/Next` | Les actions de sa chaîne, avec le même déclencheur (§12.6.2) | celui de l'action |
| Formulaire, `/XFA` | Sa présence : un formulaire XFA, compté parmi les scripts (§12.7.9) | — |
| Arbre `/EmbeddedFiles`, annotations `FileAttachment`, fichiers associés `/AF` | Les spécifications de fichier qui incorporent leur fichier (`/EF`, §7.11.4) | — |

Les champs du formulaire sont parcourus par l'arbre `/AcroForm` `/Fields` et les annotations par les pages ; une action atteinte deux fois n'est comptée qu'une fois, avec tous ses déclencheurs. Chaque action est décrite par sa **nature**, son type `/S` (tableau 201 de la norme ; un type inconnu est observé `autre`), ses déclencheurs et les pages où elle se trouve ([ADR-0220](../decisions/ADR-0220-nature-et-declencheur.md)). Ni adresse, ni nom de fichier, ni code de script n'est lu : aucune chaîne du document ne l'est.

Les actions sont rangées en familles ([ADR-0222](../decisions/ADR-0222-constats-et-versions-de-t52.md)) :

| Famille | Actions |
| --- | --- |
| `scripts` | `JavaScript` ; `Rendition` qui porte un script (`/JS`) ; formulaire XFA |
| `automatiques` | Toute action à déclencheur `ouverture`, `document`, `page` ou `champ`, sauf celles qui ne changent que l'affichage : `GoTo`, `GoToDp`, `Thread`, `Trans`, `GoTo3DView`, `SetOCGState`, `Hide`, `ResetForm` |
| `ouvertures` | `Launch`, `GoToR`, `GoToE`, `ImportData` |
| `envois` | `SubmitForm`, `URI` |
| `fichiers` | Fichiers incorporés |

Une action peut être de deux familles : un script à l'ouverture est un script et une action automatique.

Sur les échantillons de `tests/donnees/actifs` (`generer_actifs.py`) :

| Échantillon | Écrit par | Relevé |
| --- | --- | --- |
| `liens.pdf` | LibreOffice : un lien vers un site, un lien `mailto:`, un renvoi interne, un signet | deux `URI` (`utilisateur`) |
| `formulaire.pdf` | LibreOffice : formulaire HTML exporté en champs, bouton d'envoi | un `SubmitForm` (`utilisateur`, clic) |
| `ghostscript.pdf` | Ghostscript, par pdfmark : script à l'ouverture, lien qui lance un programme, pièce jointe | un `JavaScript` (`ouverture`), un `Launch` (`utilisateur`), un fichier |
| `javascript.pdf` | `liens.pdf`, puis pypdf : script au niveau du document | un `JavaScript` (`ouverture`), deux `URI` |
| `piece_jointe.pdf` | `liens.pdf`, puis pypdf : pièce jointe | deux `URI`, un fichier |
| `balise.pdf` | `liens.pdf`, puis pypdf : adresse ouverte à l'affichage de la page | un `URI` (`page`), deux `URI` (`utilisateur`) |
| `calcul.pdf` | `formulaire.pdf`, puis pypdf : mise en forme et calcul d'un champ | deux `JavaScript` (`champ`), un `SubmitForm` |
| `xfa.pdf` | `formulaire.pdf`, puis pypdf : paquet XFA | un formulaire XFA, un `SubmitForm` |
| `chiffre.pdf` | `ghostscript.pdf` réécrit et chiffré par pypdf (RC4 de 128 bits) | comme `ghostscript.pdf` |

Les échantillons de `tests/donnees/pages` `document.pdf` (LibreOffice) et `ghostscript.pdf` (Ghostscript) ne portent aucun élément actif.

Oracle (`oracle.json`) : `pdfinfo` de Poppler 25.03.0 dit si le document a du JavaScript et un formulaire XFA, `pdfinfo -js` liste ses scripts, `pdfdetach -list` ses fichiers incorporés ; sur chaque échantillon, le module trouve un script JavaScript quand `pdfinfo` en voit, autant de scripts que `pdfinfo -js` en liste, un formulaire XFA quand `pdfinfo` en voit un, et autant de fichiers incorporés que `pdfdetach`.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| PDF | Dernière version : catalogue (`/OpenAction`, `/AA`, `/Names`, `/AF`, `/AcroForm`, `/Outlines`), arbres de noms `/JavaScript` et `/EmbeddedFiles` (leurs valeurs seulement), arbre des champs, signets, arbre des pages ; de chaque page, ses `/AA`, `/AF` et ses annotations (`/Subtype`, `/A`, `/AA`, `/FS`, `/AF`) ; de chaque action, `/S`, la présence de `/JS` pour `Rendition`, et `/Next` ; de chaque spécification de fichier, la présence de `/EF`. Aucune chaîne n'est lue : ni adresse, ni nom de fichier, ni code de script, ni clé d'un arbre de noms. |

## Sorties

| Observation | Forme |
| --- | --- |
| `actifspdf.pages`, `actifspdf.pages_lues` | Pages de l'arbre des pages ; pages parcourues en entier |
| `actifspdf.actions`, `.natures`, `.declencheurs`, `.pages` | Actions trouvées ; s'il y en a, leurs natures, leurs déclencheurs (dans l'ordre `ouverture`, `document`, `page`, `champ`, `utilisateur`) et les pages où elles se trouvent |
| `actifspdf.scripts`, `.natures`, `.declencheurs`, `.pages` | Scripts (formulaire XFA compris, nature `XFA`) |
| `actifspdf.automatiques`, `.natures`, `.declencheurs`, `.pages` | Actions automatiques ; leurs seuls déclencheurs automatiques |
| `actifspdf.ouvertures`, `.natures`, `.declencheurs`, `.pages` | Actions qui ouvrent un programme ou un autre fichier |
| `actifspdf.envois`, `.natures`, `.declencheurs`, `.pages` | Actions qui envoient le formulaire ou ouvrent une adresse |
| `actifspdf.fichiers`, `.pages` | Fichiers incorporés ; pages de leurs annotations ou fichiers associés |
| `actifspdf.chiffre` | Vrai pour un document chiffré, parcouru par sa structure |
| `actifspdf.arret_avant_budget` | Vrai si la recherche s'est arrêtée pour garder du budget |
| `actifspdf.recherche_coupee` | Vrai si une limite (actions, nœuds d'un arbre) a été atteinte |

## Données identifiantes

Aucune : le module n'observe que des natures d'actions, des déclencheurs, des nombres et des numéros de page ; ni adresse, ni nom de fichier, ni texte ([ADR-0220](../decisions/ADR-0220-nature-et-declencheur.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien : un élément actif ne dit rien de l'origine du contenu |
| Transformation banale (recompression, redimensionnement) | Rien |
| Retouche | Rien : un élément ajouté par une mise à jour se lit dans la chronologie de `revisionspdf`, pas ici |
| Génération | Rien |

Les constats sont des informations neutres, de direction « rien de particulier » : ils disent ce que le document demande à un lecteur, et que l'outil ne l'a pas fait.

## Ce qui déclenche un constat

Le module n'émet aucun constat ; cinq règles « moteur » du catalogue lisent ses observations ([ADR-0222](../decisions/ADR-0222-constats-et-versions-de-t52.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-ACTIFSPDF-001 | `actifspdf.scripts` ≥ 1 | Information neutre : scripts, et leurs natures |
| R-ACTIFSPDF-002 | `actifspdf.automatiques` ≥ 1 | Information neutre : actions automatiques, leurs déclencheurs et leurs natures |
| R-ACTIFSPDF-003 | `actifspdf.ouvertures` ≥ 1 | Information neutre : lancements et ouvertures d'autres fichiers |
| R-ACTIFSPDF-004 | `actifspdf.envois` ≥ 1 | Information neutre : envois du formulaire et liens vers une adresse |
| R-ACTIFSPDF-005 | `actifspdf.fichiers` ≥ 1 | Information neutre : fichiers incorporés |

## Taux d'erreur

Sans objet pour une information neutre qui compte ce que le document déclare. Les relevés ont été vérifiés sur les neuf échantillons ci-dessus, contre Poppler, et sur des documents synthétiques des tests. La part de documents ordinaires qui déclenchent chaque règle (R-ACTIFSPDF-004 sur tout document qui a des liens vers une adresse) se mesurera sur le corpus de référence (T100).

## Limites connues

- Seule la dernière version est parcourue, depuis son catalogue : un script d'une version antérieure, retiré depuis, ou d'un objet qu'aucun autre ne désigne, n'est pas compté ; aucun lecteur conforme ne l'exécute. Une version qui ajoute une annotation, donc son action, est rangée « annotation » par `revisionspdf` (ADR-0208) : ses éléments actifs se lisent ici.
- Le code des scripts, les adresses et les fichiers désignés ne sont pas lus : le constat dit qu'un élément est là, pas ce qu'il fait, ni s'il est malveillant ; un lien vers un site connu et une balise de pistage ne se distinguent pas.
- Un formulaire XFA est compté comme un script, qu'il en porte ou non ; son paquet XML n'est pas lu.
- Les annotations multimédias (`Screen`, `RichMedia`, `3D`, `Movie`, `Sound`) ne sont comptées que par leurs actions ; leur contenu propre, qui peut porter des scripts, n'est pas lu.
- Une clé `/AA` que la norme ne définit pas n'est pas lue.
- Les fichiers incorporés ne sont ni ouverts ni analysés : un fichier incorporé peut porter ses propres métadonnées ou ses propres éléments actifs. Une spécification de fichier sans `/EF` désigne un fichier hors du document et n'est pas comptée comme fichier incorporé.
- Document chiffré : la structure (dictionnaires, noms) n'est pas chiffrée et se lit ; les objets rangés dans un flux d'objets ne se lisent pas sans déchiffrer ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md), [ADR-0210](../decisions/ADR-0210-versions-d-un-pdf-chiffre.md)), et la partie qui les demande est non menée (`format_partiel`).
- Au plus 4 096 pages, 65 536 actions, 65 536 nœuds et entrées par arbre ; la recherche s'arrête quand il ne reste plus que 262 144 objets du budget du module, pour que les observations déjà faites soient envoyées.

## Sécurité

Le module lit la structure du document et rien d'autre : aucune chaîne n'est décodée, aucun flux n'est décompressé hors des flux d'objets et de références croisées que lit le lecteur, aucun script n'est interprété, aucun fichier ni aucune adresse n'est ouvert (ES-06, [ADR-0033](../decisions/ADR-0033-politique-des-requetes-sortantes.md)) ; le processus de travail n'a d'ailleurs ni réseau ni accès aux fichiers (ADR-0083). Chaque arbre est parcouru sans récursion, avec les nœuds déjà vus écartés ; chaque nœud, action et fichier compte un objet du budget (ES-03).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-17 | 0.1.0 | Création |
| 2026-11-17 | 0.1.0 | Renvoi : éléments actifs des DOCX et ODT dans la fiche [`actifs-bureau`](actifs-bureau.md) (complément bureautique, ADR-0228) ; module inchangé |
