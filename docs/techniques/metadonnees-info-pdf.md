# Fiche technique — Dictionnaire d'information PDF

- **Module** : `infopdf` (version 0.3.0)
- **Tâche** : T21, T22, T23, T25
- **Exigences** : F-10, F-12, F-90, ES-13
- **Formats** : `pdf`
- **Directions permises** : `origine_ia`, `rien_de_particulier`
- **Règles** : aucune
- **Bibliothèques** : aucune

## Question

Que déclare le dictionnaire d'information du document : titre, auteur, logiciel de création et de conversion, dates, entrées propres à un logiciel ?

## Principe

Le module lit la structure du PDF par le lecteur du projet ([ADR-0124](../decisions/ADR-0124-lecteur-pdf-du-projet.md)), d'après ISO 32000-2, §7 : il trouve le dernier `startxref`, lit la table des références croisées, classique (§7.5.4) ou en flux (§7.5.8), puis les sections antérieures (`/Prev`, `/XRefStm`) ; le trailer le plus récent est complété par les antérieurs pour `/Size`, `/Root`, `/Encrypt`, `/Info` et `/ID`. Il lit ensuite l'objet que désigne `/Info` (§14.3.3), à sa position dans le fichier ou dans son flux d'objets (§7.5.7), et observe chacune de ses entrées. Rien n'est reconstruit : une structure qui ne se lit pas comme elle est déclarée est dite non menée ([ADR-0125](../decisions/ADR-0125-lecture-stricte-du-pdf.md)).

## Entrées

| Format | Emplacement lu ([ADR-0127](../decisions/ADR-0127-metadonnees-pdf-lues.md)) |
| --- | --- |
| PDF | Dictionnaire désigné par `/Info` dans le trailer le plus récent qui en désigne un |

Aucune donnée de référence. Ne sont pas lus : les dictionnaires d'information des révisions antérieures (T50), le catalogue (`/Lang`, `/PageMode`, `/MarkInfo`), les pages, le paquet XMP (lu par `xmp`).

Tolérances, toutes de forme ([ADR-0125](../decisions/ADR-0125-lecture-stricte-du-pdf.md)) : entrées de table de 19 ou 21 octets au lieu de 20 ; blancs avant `xref` ; retour chariot seul après `stream` ; `endobj` absent ; référence absente, libre ou d'une autre génération lue comme l'objet nul (§7.3.10).

## Sorties

Noms d'observation ([ADR-0128](../decisions/ADR-0128-observations-du-dictionnaire-info.md)) :

| Nom | Valeur |
| --- | --- |
| `infopdf.present` | Vrai si le trailer désigne un dictionnaire ; toujours observé (F-14) |
| `infopdf.chiffre` | Vrai si le document est chiffré (`/Encrypt`) ; observé dès que la table se lit |
| `infopdf.<clé>` | Valeur de l'entrée : texte, nom (sans barre oblique), nombre, booléen, ou liste pour un tableau |
| `infopdf.<clé>.<sous-clé>` | Entrée d'un dictionnaire imbriqué |
| `infopdf.<clé>.taille` | Taille, en octets, d'un flux désigné par une entrée ([ADR-0118](../decisions/ADR-0118-valeurs-tirees-du-fichier.md)) |
| `<nom>.longueur` | Longueur entière d'une valeur coupée (ADR-0118) |

- Clés usuelles : `Title`, `Author`, `Subject`, `Keywords`, `Creator` (logiciel d'origine), `Producer` (logiciel de conversion), `CreationDate`, `ModDate`, `Trapped`. Une clé propre à un logiciel est observée de même ; un caractère hors des lettres ASCII, des chiffres et du tiret y devient un tiret (ADR-0117).
- Chaîne : UTF-16BE ou UTF-8 si elle commence par leur marque d'ordre, PDFDocEncoding sinon (§7.9.2.2, annexe D) ; un code non défini devient le caractère de remplacement.
- Date : telle qu'écrite, `D:AAAAMMJJHHmmSS+HH'mm'`, sans conversion ; les règles de T23 la lisent par la lecture `date-pdf` ([ADR-0148](../decisions/ADR-0148-lecture-des-dates.md)).
- Objet nul : entrée absente, rien n'est observé.

Le module n'émet aucun constat ; les règles du catalogue qui lisent ses observations sont à la rubrique « Ce qui déclenche un constat ».

## Données identifiantes

| Catégorie | Clés |
| --- | --- |
| `metadonnee_nominative` | `Author` |
| `texte_libre` | `Title`, `Subject`, `Keywords` |

`Title` porte souvent le nom du fichier source (« Microsoft Word - rapport.docx ») : il est masqué avec les textes libres ([ADR-0159](../decisions/ADR-0159-lieux-nommes-et-textes-libres.md), [ADR-0160](../decisions/ADR-0160-champs-lieux-et-textes-libres.md)). Ces données sont comptées et nommées, sans leur valeur, par la rubrique « Contrôle avant publication » du rapport et par le résumé ([ADR-0158](../decisions/ADR-0158-forme-du-controle-avant-publication.md)).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Rien |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : nom d'un générateur dans `Creator` ou `Producer` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations. Un `Producer` ou un `Creator` est une déclaration du logiciel, que quiconque peut écrire (cas d'abus C-02).

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-INFOPDF-001` Générateur nommé par le logiciel d'origine du PDF ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `infopdf.Creator` | liste des générateurs (ADR-0144) | origine IA |
| `R-INFOPDF-002` Générateur nommé par le logiciel de conversion du PDF ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `infopdf.Producer` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-INFOPDF-003` Date de création impossible (CreationDate) | `infopdf.CreationDate` | date impossible (`date-pdf`) |
| `R-INFOPDF-004` Date de modification impossible (ModDate) | `infopdf.ModDate` | date impossible (`date-pdf`) |
| `R-INFOPDF-005` Création postérieure à la modification (CreationDate, ModDate) | `infopdf.CreationDate`, `infopdf.ModDate` | certainement postérieure à `infopdf.ModDate`, lues par `date-pdf` |
| `R-INFOPDF-006` Aucun dictionnaire d'informations PDF (Info) | `infopdf.present` | faux |

Une absence de dictionnaire est l'observation `infopdf.present` à faux ; la règle `R-INFOPDF-006` en fait une information neutre, jamais un indice (F-14).

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool sur deux PDF, l'un à table classique (LibreOffice), l'autre à flux de références croisées et flux d'objets (Ghostscript), tous deux mis à jour par exiftool ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md), ADR-0127). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`).

## Limites connues

- Document chiffré : les chaînes ne sont pas déchiffrées ; le dictionnaire est non mené pour format partiel, chemin « dictionnaire Info (document chiffré) » ([ADR-0126](../decisions/ADR-0126-pdf-chiffre.md)).
- Seul `FlateDecode` est décodé (prédicteurs PNG et TIFF compris) : un flux de références croisées ou d'objets compressé autrement n'est pas lu.
- PDF abîmé (table fausse, longueur de flux inexacte, objet ailleurs que là où la table le dit) : non mené, alors que d'autres lecteurs le réparent ; aucune reconstruction (ADR-0125).
- Un tableau qui contient un tableau, un dictionnaire ou un objet nul n'est pas observé (non mené).
- Les séquences d'échappement de langue d'une chaîne UTF-16 (§7.9.2.2) sont gardées dans le texte.
- Les révisions antérieures ne sont pas comparées : un auteur remplacé par une mise à jour n'est pas au rapport (T50).

## Sécurité

- Lecture bornée par le contexte : fenêtres de 4 Kio, 64 Kio, 1 Mio puis 16 Mio au plus ; un objet plus grand n'est pas lu (format partiel).
- Chaque objet lu et chaque section comptent un objet ; chaque tableau, dictionnaire et résolution de référence, un niveau d'imbrication (64 au plus, ADR-0078). Références circulaires, sections en boucle et dictionnaire qui se contient : non menés.
- Flux `FlateDecode` décompressés par `Contexte.decompresser`, donc comptés dans le budget de décompression.
- Rien n'est exécuté (JavaScript, actions) ni suivi hors du fichier : un flux dont les données sont dans un autre fichier (`/F`) n'est pas lu.
- Le codec UTF-16BE est chargé à l'import du lecteur, avant les restrictions du processus de travail (ADR-0079, ERR-0009).

## Historique

| Date | Version du module | Modification |
| --- | --- | --- |
| 2026-11-12 | 0.1.0 | Création (T21) |
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
| 2026-11-14 | 0.3.0 | `Title`, `Subject`, `Keywords` marqués `texte_libre` ; contrôle avant publication (T25, ADR-0158 à ADR-0163) |
