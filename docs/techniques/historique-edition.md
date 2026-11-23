# Fiche technique — Historique d'édition d'un DOCX ou d'un ODT

- **Module** : `historique` (version 0.1.0)
- **Tâche** : T81
- **Exigences** : F-71
- **Formats** : `docx`, `odt`
- **Directions permises** : `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : `expat`

## Question

Que garde le document de la façon dont il a été écrit : combien de temps il a été ouvert pour être modifié, combien de fois il a été enregistré, en combien de sessions son texte a été écrit, quelles modifications suivies et quels commentaires il porte ? Une valeur absente ou nulle reste une information neutre (F-71).

## Principe

Le module lit, pour son propre compte, les parties où Word et LibreOffice inscrivent cet historique ([ADR-0249](../decisions/ADR-0249-historique-lu-dans-un-docx-et-un-odt.md)), par le lecteur ZIP du projet ([ADR-0137](../decisions/ADR-0137-lecteur-zip-du-projet.md)) et le lecteur XML par expat, sans DTD ([ADR-0116](../decisions/ADR-0116-xml-par-expat-sans-dtd.md)) ; le corps est lu élément par élément, sans en garder l'arbre. Les modules `ooxml` et `odf` lisent déjà les propriétés et les observent telles qu'écrites, sans les interpréter (ADR-0139, ADR-0140) ; `historique` les relit pour en tirer des nombres comparables entre les deux formats.

**Temps d'édition et enregistrements.**

| Format | Temps d'édition | Enregistrements |
| --- | --- | --- |
| DOCX | `TotalTime` des propriétés étendues (ECMA-376, partie 1), en minutes | `cp:revision` des propriétés principales (partie 2), nombre d'enregistrements |
| ODT | `meta:editing-duration` de `meta.xml` (OpenDocument 1.3, partie 3), durée `xsd:duration` ramenée en minutes entières | `meta:editing-cycles`, nombre de cycles d'édition |

Une valeur qui n'est pas un entier positif ou nul écrit en chiffres (au plus 18), ou une durée qui compte des années ou des mois, dont la longueur varie, n'est pas observée ; la première valeur l'emporte sur une répétition.

**Sessions d'édition.** Word donne à chaque session d'édition, d'un enregistrement au suivant, un identifiant de révision (« rsid », ECMA-376, partie 1) : il les liste dans `word/settings.xml` (`w:rsids`, racine comprise) et marque chaque paragraphe et chaque course du corps de celui de la session qui l'a écrit (`w:rsidR`, `w:rsidRDefault`). LibreOffice fait de même dans un ODT, dans les styles automatiques de `content.xml` (`officeooo:rsid` d'un style de texte ou de paragraphe, `officeooo:paragraph-rsid`), mais n'en écrit aucun dans un DOCX. Le module compte les sessions déclarées, puis range chaque caractère du texte visible du corps sous sa session :

- DOCX : le texte de `w:t` de `word/document.xml`, hors du texte supprimé ou déplacé (`w:del`, `w:moveFrom`, [ADR-0240](../decisions/ADR-0240-texte-supprime-d-une-modification-suivie.md)) ; session de la course (`w:rsidR`), sinon session par défaut du paragraphe (`w:rsidRDefault`) ;
- ODT : le texte des paragraphes et titres de `office:text`, hors de la région des modifications suivies, des notes et des commentaires, et hors des descriptions d'images ; session de la portion (`text:span`), sinon celle du paragraphe, d'après leurs styles automatiques.

La part de la session la plus représentée est comptée en pour cent, arrondie au-dessous, sur les seuls caractères qui ont une session. Les espaces répétées (`text:s`), tabulations et sauts de ligne, qui ne sont pas du texte écrit, ne comptent pas.

**Modifications suivies et commentaires.**

| Format | Modifications suivies | Commentaires |
| --- | --- | --- |
| DOCX | Marques de révision du corps (ECMA-376, partie 1, « Revisions ») : `w:ins`, `w:del`, `w:moveFrom`, `w:moveTo`, `w:rPrChange`, `w:pPrChange`, `w:sectPrChange`, `w:tblPrChange`, `w:tblPrExChange`, `w:trPrChange`, `w:tcPrChange`, `w:tblGridChange`, `w:numberingChange`, `w:cellIns`, `w:cellDel`, `w:cellMerge` | `w:comment` de la partie des commentaires, que désignent les relations de la partie principale |
| ODT | Régions `text:changed-region` de `text:tracked-changes` (insertion, suppression, mise en forme) | `office:annotation` du corps |

Leur auteur (`w:author`, `dc:creator`) est lu pour compter les auteurs distincts, par le nom écrit, puis oublié : aucun nom n'est observé ([ADR-0250](../decisions/ADR-0250-auteurs-comptes-et-dates-sans-fuseau.md)). Leur date (`w:date`, `dc:date`) est lue sans son fuseau : dans un DOCX, Word y écrit l'heure locale suivie de `Z` et la relit comme une heure locale ([MS-OI29500, §2.1.313](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/2f42e7a6-a014-4392-8461-53a493241d28)), et LibreOffice fait de même ([bogue 134589](https://www.libreoffice.org/bugzilla/show_bug.cgi?id=134589)) ; dans un ODT, LibreOffice l'écrit sans fuseau.

**Dates du document.** Création et dernier enregistrement (`dcterms:created` et `dcterms:modified` d'un DOCX, `meta:creation-date` et `dc:date` d'un ODT) sont lus comme les lisent les règles de T23 ([ADR-0148](../decisions/ADR-0148-lecture-des-dates.md)) : chaque date est l'intervalle de tous les instants que son écriture peut désigner, une heure sans fuseau couvrant les fuseaux de UTC-12 à UTC+14. L'écart observé est le plus grand que permettent les deux écritures, arrondi à la minute supérieure.

Sur les échantillons de `tests/donnees/historique` (`generer_historique.py`), écrits par LibreOffice 25.2.3.2 en trois sessions, le texte tapé par l'interface comme le taperait un auteur :

| Échantillon | Contenu | Relevé |
| --- | --- | --- |
| `sessions.odt` | Un paragraphe par session, une insertion suivie, un commentaire | 3 sessions déclarées, 207 caractères en 3 sessions, la plus représentée à 52 % ; 3 cycles d'édition, durée nulle ; 1 modification, 1 commentaire, 1 auteur chacun |
| `sessions.docx` | Le même, exporté en DOCX | aucune session (LibreOffice n'en écrit pas dans un DOCX), 207 caractères sans session ; 3 enregistrements, durée nulle ; 2 marques de révision (le texte inséré et la fin de son paragraphe), 1 commentaire |

Oracle (`oracle.json`) : LibreOffice relit chaque échantillon et donne la longueur et l'identifiant de session (`Rsid`) de chaque portion du texte, le nombre de modifications et de commentaires et de leurs auteurs, les cycles et la durée d'édition ; le module trouve les mêmes nombres, à une différence près : LibreOffice relit une seule modification dans le DOCX, où elle est écrite en deux marques. Les identifiants de session de Word, ses marques de révision et ses commentaires, que LibreOffice n'écrit pas ainsi, sont vérifiés sur des DOCX construits par les tests à la manière de Word.

## Entrées

| Format | Ce qui est lu |
| --- | --- |
| DOCX | Relations du paquet (`_rels/.rels`) et de la partie principale ; propriétés étendues (`TotalTime`) et principales (`cp:revision`, `dcterms:created`, `dcterms:modified`) ; `w:rsids` des réglages ; texte, identifiants de session et marques de révision du corps ; commentaires. Ni les en-têtes, pieds de page et notes, ni les autres réglages, ni le texte des commentaires. |
| ODT | `meta.xml` (`meta:editing-duration`, `meta:editing-cycles`, `meta:creation-date`, `dc:date`) ; `content.xml` : styles automatiques et leurs identifiants de session, texte du corps, régions des modifications suivies, annotations. Ni `styles.xml`, ni `settings.xml`, ni les versions enregistrées (`VersionList.xml`). |

## Sorties

| Observation | Forme |
| --- | --- |
| `historique.present` | Vrai si le document déclare un temps d'édition, un nombre d'enregistrements, une session, une modification suivie ou un commentaire ; toujours observé (F-71) |
| `historique.duree` | Temps d'édition, en minutes entières |
| `historique.revisions` | Enregistrements (DOCX) ou cycles d'édition (ODT) |
| `historique.sessions` | Sessions déclarées : identifiants distincts des réglages (DOCX) ou des styles automatiques (ODT) |
| `historique.texte.caracteres` | Caractères du texte visible du corps, s'il a été lu |
| `historique.texte.sans_session` | Ceux qui n'ont pas de session |
| `historique.texte.sessions` | Sessions distinctes que désignent les caractères qui en ont une |
| `historique.texte.part` | Part de la plus représentée, en pour cent arrondi au-dessous |
| `historique.modifications`, `.auteurs` | Marques ou régions de modifications suivies, s'il y en a, leurs auteurs nommés distincts |
| `historique.commentaires`, `.auteurs` | Commentaires, s'il y en a, leurs auteurs nommés distincts |
| `historique.ecart` | Plus grand écart entre création et dernier enregistrement, en minutes, si les deux dates se lisent et que la création ne suit pas certainement l'enregistrement |
| `historique.posterieures` | Modifications et commentaires certainement datés après le dernier enregistrement, si sa date et une au moins des leurs se lisent |

## Données identifiantes

Aucune : le module n'observe que des nombres. Les noms des auteurs des modifications et des commentaires sont comptés sans être observés ([ADR-0250](../decisions/ADR-0250-auteurs-comptes-et-dates-sans-fuseau.md)) ; l'auteur et le dernier modificateur du document restent lus par `ooxml` et `odf`, marqués `metadonnee_nominative` (ADR-0140). Le module est parmi ceux qui ne lisent aucune métadonnée identifiante : son analyse non menée ne rend pas incomplet le contrôle avant publication (ADR-0158).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Sans objet pour un document bureautique |
| Transformation banale (conversion, export, « Enregistrer sous ») | Rien : une conversion peut garder, remettre à zéro ou perdre l'historique (LibreOffice n'écrit aucune session dans un DOCX) |
| Retouche | Rien : des modifications suivies disent qu'un texte a été repris, pas comment il a été écrit |
| Génération | Rien : un texte collé en une fois, depuis un générateur ou depuis un brouillon écrit ailleurs, donne le même historique court (ADR-0022) |

Les constats sont des informations neutres ([ADR-0251](../decisions/ADR-0251-constats-et-versions-de-t81.md)) : ils disent ce que le document déclare de son écriture ; deux d'entre eux relèvent une incohérence entre ses dates, sans en dire la cause.

## Ce qui déclenche un constat

Le module n'émet aucun constat ; huit règles « moteur » du catalogue lisent ses observations ([ADR-0251](../decisions/ADR-0251-constats-et-versions-de-t81.md)) :

| Règle | Condition | Constat |
| --- | --- | --- |
| R-HISTORIQUE-001 | `historique.present` = faux | Information neutre : aucun historique d'édition |
| R-HISTORIQUE-002 | `historique.duree` observée | Information neutre : temps d'édition déclaré, nul compris |
| R-HISTORIQUE-003 | `historique.revisions` observée | Information neutre : enregistrements ou cycles déclarés |
| R-HISTORIQUE-004 | `historique.texte.sessions` ≥ 1 | Information neutre : sessions du texte et part de la plus représentée |
| R-HISTORIQUE-005 | `historique.modifications` ≥ 1 | Information neutre : marques de modification suivie et leurs auteurs distincts |
| R-HISTORIQUE-006 | `historique.commentaires` ≥ 1 | Information neutre : commentaires et leurs auteurs distincts |
| R-HISTORIQUE-007 | `historique.duree` > `historique.ecart` | Information neutre : temps d'édition plus long que le document n'a existé |
| R-HISTORIQUE-008 | `historique.posterieures` ≥ 1 | Information neutre : modifications ou commentaires datés après le dernier enregistrement |

## Taux d'erreur

Sans objet pour une information neutre qui rapporte ce que le document déclare. Les relevés ont été vérifiés sur les deux échantillons ci-dessus, contre LibreOffice, et sur des documents construits par les tests. La part de documents ordinaires qui déclenchent R-HISTORIQUE-007 et R-HISTORIQUE-008 se mesurera sur le corpus de référence (T100).

## Limites connues

- Tout est déclaration du fichier : temps, comptes, identifiants et dates s'écrivent ou s'effacent ; l'inspecteur de document de Word et les outils de nettoyage retirent auteurs et dates.
- Le temps d'édition compte le temps pendant lequel le document est ouvert, pas celui de la rédaction ; LibreOffice ne le compte pas quand il est piloté sans interface, et beaucoup d'outils écrivent zéro.
- Une session va d'un enregistrement au suivant : un texte collé en une fois et un texte tapé d'une traite en font chacun une ; les identifiants d'un modèle ou d'un texte copié peuvent venir d'autres documents.
- Seul le texte du corps est rangé par session ; les en-têtes, pieds de page, notes et commentaires ne le sont pas, et les modifications suivies hors du corps d'un DOCX ne sont pas comptées.
- Une modification se compte en marques (DOCX) ou en régions (ODT) : Word et LibreOffice marquent à part le texte inséré et la fin de paragraphe insérée. Une réponse à un commentaire compte comme un commentaire.
- Un auteur se compte par le nom écrit, tel quel ; un même relecteur sous deux noms en fait deux.
- Les dates des modifications et des commentaires, lues sans fuseau, ne sont comparées qu'à la date du dernier enregistrement, avec une marge de 14 heures (26 si cette date n'a pas de fuseau) ; une date antérieure à la création n'est pas relevée, le texte copié d'un autre document gardant les siennes.
- Les versions enregistrées d'un ODT (`VersionList.xml`) et les réglages de LibreOffice (`settings.xml` : `Rsid`, `RsidRoot`) ne sont pas lus.
- Un document qui dépasse le budget du module (ES-03) n'est pas analysé : la technique est non menée, `limite_depassee`.

## Sécurité

Le module lit des parties XML, sans DTD ni entité ; il ne suit aucune relation hors de l'archive (ES-06, [ADR-0138](../decisions/ADR-0138-relations-et-references-non-suivies.md)) ; le processus de travail n'a d'ailleurs ni réseau ni accès aux fichiers (ADR-0083). Chaque élément XML compte un objet du budget (ES-03), chaque niveau contre l'imbrication, et chaque décompression contre son budget de décompression. Les expressions de lecture des durées et des fuseaux sont fixes, sans répétition imbriquée : leur temps est linéaire (ADR-0039).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-23 | 0.1.0 | Création |
