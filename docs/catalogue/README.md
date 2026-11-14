# Catalogue de règles

> Statut : **v1.5** ; v1.0 mergée avec T15, v1.1 avec T16, v1.2 avec T17, v1.3 avec T22, v1.4 avec T23, v1.5 proposée dans la PR de T24. Document vivant : toute modification est inscrite à l'historique (§6).
> Exigences : F-12, F-24, F-26, NF-06, NF-07 ; ES-09 du [modèle de menace](../modele-de-menace/modele-de-menace.md).
> Décisions : [ADR-0029](../decisions/ADR-0029-integrite-du-catalogue.md), [ADR-0038](../decisions/ADR-0038-format-du-catalogue.md), [ADR-0039](../decisions/ADR-0039-expressions-regulieres-re2.md), [ADR-0084](../decisions/ADR-0084-langage-des-regles.md) à [ADR-0091](../decisions/ADR-0091-texte-des-phrases-dans-la-regle.md).

Le catalogue décide de ce que l'outil tire de ses observations : chaque constat du rapport cite la règle qui l'a produit, avec sa version. Il est séparé du moteur (F-26), livré dans le paquet de l'outil (ADR-0029) et entièrement public, limites connues comprises (ADR-0019).

## 1. Où il se trouve

| Élément | Emplacement |
| --- | --- |
| Catalogue livré | [`src/voight_kampff/donnees/catalogue/`](../../src/voight_kampff/donnees/catalogue/) ; premières règles en version 0.2.0 (T22) : origine IA déclarée et signatures de générateurs ([ADR-0142](../decisions/ADR-0142-constats-d-une-declaration-du-fichier.md) à [ADR-0146](../decisions/ADR-0146-versions-des-modules-et-du-catalogue-de-t22.md)) ; incohérences internes et absence en 0.3.0 (T23, ADR-0147 à ADR-0152) ; indices de transfert en 0.4.0 (T24, [ADR-0153](../decisions/ADR-0153-indices-de-transfert-retenus.md) à [ADR-0157](../decisions/ADR-0157-versions-de-t24.md)) ; chaque fiche technique liste les règles qui lisent ses observations |
| Schémas | `src/voight_kampff/schemas/catalogue.schema.json` (en-tête), `regles.schema.json` (règles) |
| Chargement et validation | `src/voight_kampff/_orchestration/catalogue.py` |
| Règles et évaluation | `src/voight_kampff/_regles.py` |
| Registre des versions | [`versions.toml`](versions.toml) |
| Techniques hors de cette version (pas dans le catalogue) | `src/voight_kampff/modules/hors_v1.toml` ([ADR-0087](../decisions/ADR-0087-techniques-hors-v1.md)) |

`vk --regles` affiche la version, la date, l'empreinte et la liste des règles du catalogue employé ; avec `--catalogue DOSSIER`, celles d'un catalogue fourni par l'utilisateur, qui remplace alors le catalogue livré ([ADR-0086](../decisions/ADR-0086-catalogue-fourni-par-l-utilisateur.md)).

## 2. Forme

Un dossier, et rien d'autre que ces fichiers ([ADR-0088](../decisions/ADR-0088-fichiers-et-empreinte-du-catalogue.md)) :

```text
catalogue.toml          en-tête : format, version, date, description
regles/<module>.toml    règles d'un module ; <module> est l'identifiant d'un module livré
```

En-tête :

```toml
format = 2                      # 1, ou 2 pour lire des dates et comparer (ADR-0147)
version = "0.1.0"               # X.Y.Z, propre au catalogue (ADR-0085)
date = "2026-10-27"             # date d'édition de cette version
description = "Ce que contient cette version."
```

Une règle du moteur, qui relève d'un indice de génération dans un champ de métadonnées (exemple, pas une règle livrée) :

```toml
[[regle]]
identifiant = "R-META-001"      # R-<MODULE>-<NNN> : pas un identifiant d'exigence (A-47)
version = "1"                   # augmente à chaque changement de la règle
module = "metadonnees"
titre = "Logiciel de génération déclaré"
description = "Le champ Software nomme un générateur d'images connu."
gabarit = "meta.logiciel-generateur"   # identifiant de la phrase (ADR-0020)
phrase = { fr = "Le champ Software nomme « {logiciel} », un générateur d'images connu." }
categorie = "indice"            # preuve, indice, information_neutre (F-80)
direction = "origine_ia"        # F-81, ADR-0055
fondement = "declaration"       # ES-20 : une déclaration ne fonde jamais une preuve
niveau = "faible"               # obligatoire pour un indice ; « faible » tant qu'il n'est pas évalué
limites = ["Le champ se réécrit librement : son absence ne prouve rien (F-14)."]
application = "moteur"

[[regle.condition]]
observation = "exif.ifd0.Software"
motif = '(?i)^(midjourney|dall-e)'
parametre = "logiciel"
```

| Champ | Contenu |
| --- | --- |
| `phrase` | Texte de la phrase du constat, par langue : `fr` seul en V1, de 1 à 1 024 caractères. Chaque `{nom}` est un paramètre de la règle, remplacé à l'export par la valeur de son observation, ou par la mention de son masquage ; les emplacements sont exactement les paramètres déclarés ; aucune autre accolade ([ADR-0091](../decisions/ADR-0091-texte-des-phrases-dans-la-regle.md)) |
| `application` | `moteur` : conditions évaluées par le moteur ; `module` : appliquée par le code du module, qui la cite par son identifiant et déclare ses `parametres` ([ADR-0084](../decisions/ADR-0084-langage-des-regles.md), [ADR-0090](../decisions/ADR-0090-constat-d-une-regle.md)) |
| `condition` | De 1 à 16, toutes requises ; chacune nomme une observation et porte un seul test : `egal`, `parmi` (1 à 4 096 valeurs), `motif` (RE2), `seuil` (`operateur` et `valeur`), `presente = true`, et au format 2 `impossible = true` (date qui n'existe pas) ou `comparer` (`observation`, `operateur` `<`, `>` ou `=`, `parametre` facultatif : une seconde observation du même module) ; `lecture`, au format 2, dit comment lire les dates de ces deux tests : `date-exif`, `date-pdf`, `date-iso8601`, `date-1904` ([ADR-0147](../decisions/ADR-0147-comparaison-de-deux-observations.md), [ADR-0148](../decisions/ADR-0148-lecture-des-dates.md)) ; `parametre` facultatif |
| `evaluation` | `taux_faux_positifs` (0 à 1), `effectif` (fichiers mesurés), `borne_superieure` (borne supérieure de l'intervalle de Wilson à 95 %), `corpus`, `date` : présente seulement si le taux est mesuré, par le banc d'évaluation sur la partie évaluation du corpus ; elle seule permet un niveau autre que « faible », jusqu'à « fort » si la borne est au plus 1 %, « modéré » si elle est au plus 5 % (ADR-0018, [ADR-0101](../decisions/ADR-0101-bornes-des-niveaux-et-cible.md), [ADR-0107](../decisions/ADR-0107-effectif-et-borne-dans-l-evaluation.md)) |
| `calibrage` | `methode` (`manuelle` ou `corpus`), `procedure`, `corpus` si calibré : obligatoire pour une règle à seuil (ADR-0016) |

Évaluation ([ADR-0089](../decisions/ADR-0089-motifs-re2-et-evaluation.md)) : un motif est cherché n'importe où dans un texte (`^` et `$` l'ancrent) ; un booléen n'est égal qu'à un booléen ; une valeur en liste satisfait la condition si l'un de ses éléments la satisfait ; pour chaque condition, la première observation qui la satisfait est retenue, ou pour `comparer` la première paire, dans l'ordre des premières observations puis des secondes ; une règle donne au plus un constat par module et par partie. Une date lue est l'intervalle des instants qu'elle peut désigner, à la précision de son dernier champ, dans tous les fuseaux si elle n'en écrit pas ; `<` et `>` entre deux dates disent un ordre certain, `=` est refusé ; une date non reconnue ou non renseignée n'est jamais comparée (ADR-0148).

Une règle de comparaison de dates (exemple, pas une règle livrée) :

```toml
[[regle.condition]]
observation = "exif.exif.DateTimeOriginal"
lecture = "date-exif"
parametre = "prise"
comparer = { observation = "exif.ifd0.DateTime", operateur = ">", parametre = "modification" }
```

## 3. Ce qui est vérifié au chargement

Un catalogue invalide arrête l'analyse avant toute lecture de fichier, avec un message qui nomme le fichier et la règle en cause :

- forme du dossier : en-tête présent, aucun autre fichier que les règles des modules ;
- 8 Mio, 256 fichiers et 4 096 règles au plus ;
- chaque fichier : TOML en UTF-8, conforme à son schéma ; date existante ; format 1 ou 2, et aucune règle du format 2 dans un catalogue du format 1 ;
- chaque règle : du module de son fichier, identifiant unique, motifs acceptés par RE2 (1 024 caractères et 5 000 instructions au plus), catégorie, fondement, direction et niveau formant un constat possible, niveau permis par son évaluation, phrase dont les emplacements sont ses paramètres ;
- cohérence avec les modules livrés : module existant, direction permise par son manifeste, règles « module » citées par le manifeste et elles seules.

## 4. Vérifier une empreinte

L'empreinte est le SHA-256 de la liste `<sha256 du fichier>  <chemin relatif>`, une ligne par fichier, triée par chemin. Dans le dossier du catalogue (celui des sources, ou `voight_kampff/donnees/catalogue` dans le paquet installé) :

```bash
find . -type f -printf '%P\n' | LC_ALL=C sort | xargs sha256sum | sha256sum
```

Le résultat doit être l'empreinte inscrite au rapport, au [registre](versions.toml) et à la release de la version (`CATALOGUE.txt`).

## 5. Modifier le catalogue livré

Dans la PR qui change un fichier du catalogue :

1. Augmenter la `version` de chaque règle modifiée, texte compris ; ne jamais réutiliser un identifiant retiré.
2. Changer la `version` et la `date` de l'en-tête : `Y` si un constat peut changer (règle ajoutée, retirée, condition, seuil, liste, catégorie, direction, fondement, niveau, évaluation, gabarit, paramètres), `Z` pour un texte seul (titre, description, limites, phrase), `X` pour un nouveau `format` à partir de la version 1.0.0, `Y` avant ([ADR-0152](../decisions/ADR-0152-versions-de-t23.md)).
3. Calculer l'empreinte (§4) et ajouter une entrée à la fin de [`versions.toml`](versions.toml) ; ne modifier aucune entrée existante.
4. Vérifier avec `vk --catalogue src/voight_kampff/donnees/catalogue --regles`, puis `uv run --locked pytest tests/test_catalogue.py`.
5. Pour un niveau ou une évaluation : lancer le banc sur la partie évaluation du corpus de référence avec ce catalogue (`--catalogue`, [procédure](../verification/README.md)), recopier le taux, l'effectif et la borne supérieure de chaque règle mesurée, et vérifier que le banc ne signale aucun écart.

La CI refuse une PR qui modifie une entrée du registre déjà sur `detector`, ou une règle sans changer sa version ([ADR-0085](../decisions/ADR-0085-version-date-et-registre-du-catalogue.md)).

## 6. Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-10-27 | 1.0 | Création | T15 |
| 2026-10-28 | 1.1 | Champ `phrase` des règles (§2, §3, §5, ADR-0091) | T16 |
| 2026-10-28 | 1.2 | Évaluation : effectif, borne supérieure, niveau contrôlé (§2, §3) ; mesure par le banc (§5) ; ADR-0101, ADR-0107 | T17 |
| 2026-11-13 | 1.3 | Premières règles livrées (§1) ; ADR-0142 à ADR-0146 | T22 |
| 2026-11-13 | 1.4 | Format 2 : tests `impossible` et `comparer`, lecture des dates (§2, §3) ; nouveau format avant 1.0.0 (§5) ; ADR-0147 à ADR-0152 | T23 |
| 2026-11-14 | 1.5 | Règles livrées : incohérences de T23, indices de transfert de T24 (§1) ; ADR-0153 à ADR-0157 | T24 |
