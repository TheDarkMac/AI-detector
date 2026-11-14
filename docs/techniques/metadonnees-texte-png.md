# Fiche technique — Blocs texte PNG

- **Module** : `textepng` (version 0.3.0)
- **Tâche** : T20, T22, T23, T24
- **Exigences** : F-10, F-12, ES-13
- **Formats** : `png`
- **Directions permises** : `origine_ia`, `transformation`, `rien_de_particulier`
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

Le module n'émet aucun constat. Les paramètres de génération que certains outils écrivent dans ces blocs (mots-clés `parameters`, `prompt`, `invokeai_metadata`…) sont observés comme tout texte ; les règles R-TEXTEPNG-001 à R-TEXTEPNG-004 du catalogue les reconnaissent (F-12, [ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md)).

## Données identifiantes

Marqués `metadonnee_nominative` ([ADR-0119](../decisions/ADR-0119-donnees-identifiantes-des-metadonnees.md)) : les mots-clés prédéfinis `Author` et `Copyright` (sans égard à la casse).

## Hypothèses distinguées

| Hypothèse | Ce que la technique en dit |
| --- | --- |
| Capture brute | Rien |
| Transformation banale | Ce que le fichier en déclare : `Software` à `gnome-screenshot`, l'outil de capture d'écran de GNOME (T24) |
| Retouche | Rien |
| Génération | Ce que le fichier en déclare, sans vérification : paramètres d'AUTOMATIC1111, graphe de ComfyUI, métadonnées d'InvokeAI, nom d'un générateur dans `Software` |

Le module n'émet aucun constat : il extrait. Les règles du catalogue qui lisent ses observations ne distinguent pas la génération d'une transformation banale par une mesure ([ADR-0022](../decisions/ADR-0022-hypotheses-distinguees.md)) : elles rapportent ce que le fichier déclare, en indice faible ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md)). Une transformation banale n'écrit pas ces champs, mais peut les conserver ou les effacer ; la mesure sur le corpus (T100) dira ce que valent ces déclarations.

## Ce qui déclenche un constat

Le module n'émet aucun constat. Les règles « moteur » du catalogue qui lisent ses observations ([guide du catalogue](../catalogue/README.md)), toutes des indices faibles fondés sur une déclaration du fichier :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-TEXTEPNG-001` Paramètres de génération au format d'AUTOMATIC1111 ([ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md)) | `textepng.parameters` | motif `Steps: [0-9]+, Sampler:` | origine IA |
| `R-TEXTEPNG-002` Graphe de génération de ComfyUI ([ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md)) | `textepng.prompt` | motif `"class_type"\s*:` | origine IA |
| `R-TEXTEPNG-003` Métadonnées de génération d'InvokeAI ([ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md)) | `textepng.invokeai-metadata` | présente | origine IA |
| `R-TEXTEPNG-004` Métadonnées de génération d'InvokeAI 2 ([ADR-0145](../decisions/ADR-0145-signatures-de-parametres-de-generation.md)) | `textepng.sd-metadata` | présente | origine IA |
| `R-TEXTEPNG-005` Générateur nommé par le bloc texte Software ([ADR-0144](../decisions/ADR-0144-noms-de-generateurs-dans-les-champs-logiciels.md)) | `textepng.Software` | liste des générateurs (ADR-0144) | origine IA |

Règles de T23, des informations neutres fondées sur une déclaration du fichier, ou pour l'absence sur la lecture de sa structure ([ADR-0149](../decisions/ADR-0149-constat-d-une-incoherence.md), [ADR-0151](../decisions/ADR-0151-absence-de-metadonnees.md)) :

| Règle | Observations | Test |
| --- | --- | --- |
| `R-TEXTEPNG-006` Aucun bloc texte PNG (tEXt, zTXt, iTXt) | `textepng.present` | faux |

Une absence de bloc texte est l'observation `textepng.present` à faux ; la règle `R-TEXTEPNG-006` en fait une information neutre, jamais un indice (F-14).

Règle de T24, un indice faible vers la transformation fondé sur une déclaration du fichier ([ADR-0153](../decisions/ADR-0153-indices-de-transfert-retenus.md), [ADR-0155](../decisions/ADR-0155-nature-d-un-indice-de-transfert.md)) :

| Règle | Observation | Test | Direction |
| --- | --- | --- | --- |
| `R-TEXTEPNG-007` Capture d'écran de gnome-screenshot (bloc texte Software) | `textepng.Software` | égale à `gnome-screenshot` | transformation |

## Taux d'erreur

Règles du catalogue non évaluées : aucun corpus de référence ne les a mesurées (T100), leur niveau reste « faible » (ADR-0018). Leur déclenchement est vérifié sur des échantillons construits (`tests/test_signatures.py`). Fidélité de l'extraction vérifiée contre exiftool, par mot-clé ([ADR-0122](../decisions/ADR-0122-oracle-exiftool.md)). Les règles de T23 sont des informations neutres, sans niveau ; leur déclenchement est vérifié sur des échantillons construits (`tests/test_incoherences.py`). La règle de T24 est un indice faible, non évalué ; son déclenchement est vérifié sur des échantillons construits (`tests/test_transfert.py`).

## Limites connues

- Un texte de plus de 4 096 caractères est coupé : les règles R-TEXTEPNG-001 et R-TEXTEPNG-002 n'en voient que le début (le flux de travail JSON de certains outils dépasse souvent cette taille). Sa longueur entière est observée.
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
| 2026-11-13 | 0.2.0 | Directions origine IA permises : règles du catalogue sur ses observations (T22, ADR-0142, ADR-0146) |
| 2026-11-13 | 0.2.0 | Règles du catalogue sur ses observations : incohérences internes et absence, informations neutres (T23, ADR-0147 à ADR-0152) ; module inchangé |
| 2026-11-14 | 0.3.0 | Direction transformation permise : indice de transfert du catalogue sur ses observations, `R-TEXTEPNG-007` (T24, ADR-0153 à ADR-0157) ; code du module inchangé |
