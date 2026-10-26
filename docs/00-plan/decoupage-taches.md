# Découpage du travail en tâches

> Statut : **v0.5** ; v0.4 validée par TheDarkMac le 2026-10-26 (lancement de T00), v0.5 proposée dans la PR de T01. Document vivant : toute modification est inscrite au §6.
> Source : [`cahier-des-charges-v0.1.md`](../00-cahier-des-charges/cahier-des-charges-v0.1.md) (v0.1, 24 oct. 2026).
> Date de rédaction : 2026-10-26.

## 1. Principe du découpage

- Une **tâche = une branche = une PR** vers `detector`. Aucune tâche ne mélange deux sujets.
- Chaque tâche cite les **exigences** du cahier qu'elle couvre (F-xx, NF-xx) : c'est la base de la matrice de traçabilité exigée en section 8.
- Une technique d'analyse n'est « terminée » que si elle a : son code, ses tests, sa **fiche technique** (NF-09 : principe, entrées, sorties, limites, taux d'erreur) et ses règles dans le catalogue.
- **Les fichiers `CLAUDE.md` (à tout niveau de l'arborescence, y compris `CLAUDE.local.md`) et le dossier `.claude/` ne sont jamais commités.** Raison : toute règle, décision et étape est déjà documentée dans `docs/` ; ces fichiers ne serviraient qu'à l'outil d'assistance et feraient doublon avec la documentation, qui reste la seule source de référence. La règle est appliquée par `.git/info/exclude` dès T00, et vérifiée avant chaque commit.
  - Pourquoi `.git/info/exclude` et non `.gitignore` : choix de TheDarkMac ; l'exclusion reste propre au dépôt local et n'est pas versionnée. Détail des options dans [ADR-0002](../decisions/ADR-0002-exclusion-fichiers-assistant.md) (correction : ERR-0002).
  - Garde-fou : le job CI `fichiers-interdits` refuse toute PR qui contiendrait ces fichiers (ADR-0006).
  - Conséquence : ce fichier n'est ni versionné ni cloné. Chaque poste de travail doit le configurer lui-même ; la procédure est décrite dans `CONTRIBUTING.md` (T00).
- L'ordre suit trois contraintes du cahier :
  1. **NF-15** impose le modèle de menace *avant* tout choix d'architecture.
  2. Les points ouverts (section 10) doivent être tranchés avant le code qu'ils conditionnent.
  3. Le socle (modèle de constat, rapport, catalogue, sécurité) précède toute technique, sinon chaque module réinventerait sa sortie.

## 2. Vue d'ensemble des phases

| Phase | Contenu | Dépend de |
| --- | --- | --- |
| P0 — Cadrage | Dépôt, conventions, arbitrages, modèle de menace, architecture | — |
| P1 — Socle | Squelette, modèle de données, moteur de modules, identification, sécurité, catalogue, rapport, banc d'évaluation | P0 |
| P2 — Métadonnées | Extraction tous formats, règles IA, incohérences, contrôle avant publication | P1 |
| P3 — Provenance | C2PA, filigranes publics | P1 |
| P4 — Image (signal) | Quantification JPEG, double compression, ELA, bruit, CFA, PRNU | P1, P2 |
| P5 — PDF | Révisions, objets, éléments actifs, extraction, comparaison | P1, P2, (P4 pour les images extraites) |
| P6 — Audio | Spectrogramme, silences, ENF, réencodages | P1 |
| P7 — Vidéo | Structure, images clés, piste son, ruptures | P4, P6 |
| P8 — Texte | Stylométrie, historique d'édition, références, caractères invisibles | P1, P2 |
| P9 — Restitution avancée | Visualisations, interface, journal de conservation, comparaison d'exemplaires | P1 + modules concernés |
| P10 — Qualité & livrables | Corpus, évaluation, équipe rouge, documentation utilisateur, mentions | Toutes |

L'ordre P4 → P8 est une **proposition** ; il dépend de l'arbitrage « périmètre de la V1 » (tâche T02).

## 3. Détail des tâches

### P0 — Cadrage (aucun code applicatif)

| ID | Tâche | Exigences | Livrable |
| --- | --- | --- | --- |
| T00 | Initialisation du dépôt : `main`, `detector`, protection de `detector`, conventions (branches, commits, PR), exclusion locale de `CLAUDE.md` et `.claude/` via `.git/info/exclude` (voir §1), arborescence de la documentation, gabarits ADR / journal / erratum | Méthode de travail | `CONTRIBUTING.md` (dont procédure d'exclusion), `docs/` structuré, protection active |
| T01 | Analyse critique du cahier : ambiguïtés, incohérences, dépendances cachées (voir §5) | Toutes | `docs/01-analyse/` |
| T02 | Arbitrage des points ouverts (section 10) : un ADR par décision, avec options écartées et raisons | Section 10 | `docs/decisions/ADR-xxxx` |
| T03 | Modèle de menace : adversaires, biens à protéger, surfaces d'attaque (fichiers hostiles, requêtes sortantes, fuite de sources) | NF-15, NF-01, NF-16, NF-18 | Livrable 7 |
| T04 | Architecture et choix techniques (langage, bibliothèques, format du catalogue, isolation), justifiés par T02 et T03 | NF-10, NF-01, NF-06 | ADR + schéma |

### P1 — Socle

| ID | Tâche | Exigences |
| --- | --- | --- |
| T10 | Squelette du projet, outillage (formatage, analyse statique, tests), intégration continue | NF-09 (outillage) |
| T11 | Modèle de données : **Constat** (phrase, donnée observée, règle, catégorie, direction), **Rapport**, analyse non menée, couverture | F-80, F-81, F-82, §6 |
| T12 | Moteur de modules : enregistrement, activation/désactivation, isolation des erreurs par module | Modularité, NF-10, NF-03 |
| T13 | Soumission et identification : format réel par signature binaire, discordance d'extension, refus hors périmètre, empreinte SHA-256 | F-01 à F-05 |
| T14 | Sécurité d'exécution : limites taille/temps/mémoire, bombes de décompression, isolation du processus d'analyse, rapport partiel en cas d'échec | NF-01, NF-02, NF-03, NF-08 |
| T15 | Catalogue de règles versionné et daté, séparé du moteur, avec schéma de validation | F-26, NF-06, NF-07 |
| T16 | Génération du rapport : rubriques §6, export humain + machine, masquage par défaut des données identifiantes, avertissement | F-83, §6, NF-11, NF-14, NF-18 |
| T17 | Banc d'évaluation : exécution sur corpus, calcul FP / FN / non analysables par technique et catégorie ; matrice exigence → test | §8, NF-09 |
| T18 | Test de reproductibilité : deux analyses identiques donnent des constats identiques | NF-06, critère §8 |

### P2 — Métadonnées

| ID | Tâche | Exigences |
| --- | --- | --- |
| T20 | Extraction image : EXIF, XMP, IPTC, blocs texte PNG | F-10 |
| T21 | Extraction PDF (dictionnaire Info, XMP), audio/vidéo (balises de conteneur), DOCX/ODT (propriétés) | F-10 |
| T22 | Règles d'origine IA déclarée (IPTC DigitalSourceType) et catalogue des signatures de générateurs (paramètres, logiciel) | F-11, F-12 |
| T23 | Incohérences internes (dates, logiciel/appareil, dimensions) ; absence = information neutre | F-13, F-14 |
| T24 | Indices de transfert par messagerie / capture d'écran | F-06 |
| T25 | Contrôle avant publication — marques identifiantes issues des métadonnées (auteur, n° de série, GPS) | F-90 (partie métadonnées) |

### P3 — Provenance et marquages

| ID | Tâche | Exigences |
| --- | --- | --- |
| T30 | C2PA : détection du manifeste, vérification signature / intégrité / chaîne, états (absent, valide, hors liste de confiance, invalide, non vérifiable), restitution des déclarations | F-20 à F-23 |
| T31 | Filigranes invisibles à algorithme public : catalogue, lecture, liste des marquages recherchés | F-24, F-25 |

### P4 — Image (signal)

| ID | Tâche | Exigences |
| --- | --- | --- |
| T40 | Tables de quantification JPEG comparées à des tables connues | F-30 |
| T41 | Double compression JPEG | F-31 |
| T42 | ELA + avertissement d'interprétation + carte | F-32, F-84 |
| T43 | Analyse spectrale du résidu de bruit | F-33, F-84 |
| T44 | Traces de dématriçage CFA | F-34 |
| T45 | PRNU comparé à des photos de référence | F-35, CU-4 |

### P5 — PDF

| ID | Tâche | Exigences |
| --- | --- | --- |
| T50 | Révisions incrémentales, reconstitution des versions, distinction des ajouts légitimes ; chronologie | F-60, F-84 |
| T51 | Objets ajoutés/remplacés, textes superposés, polices incohérentes | F-61 |
| T52 | Éléments actifs signalés, jamais exécutés | F-62, NF-01 |
| T53 | Extraction images + couche texte native, routage vers modules image et texte | F-63 |
| T54 | Comparaison à des documents de référence | F-64, CU-4 |

### P6 — Audio

| ID | Tâche | Exigences |
| --- | --- | --- |
| T60 | Décodage commun + spectrogramme + coupures de bande passante | F-40, F-84 |
| T61 | Silences : silence numérique parfait, plancher de bruit, respirations | F-41 |
| T62 | ENF, comparaison à une référence si disponible | F-42 |
| T63 | Réencodages successifs | F-43 |

### P7 — Vidéo

| ID | Tâche | Exigences |
| --- | --- | --- |
| T70 | Conteneur et structure d'encodage (encodeur, images clés) | F-50 |
| T71 | Extraction d'images clés → module image | F-51 |
| T72 | Piste son → module audio | F-52 |
| T73 | Réencodages et ruptures de structure du flux | F-53 |

### P8 — Texte

| ID | Tâche | Exigences |
| --- | --- | --- |
| T80 | Caractères invisibles et homoglyphes | F-73 |
| T81 | Historique d'édition DOCX/ODT (absence = neutre) | F-71 |
| T82 | Stylométrie | F-70 |
| T83 | Existence des références (DOI, titres) dans des bases publiques | F-72, NF-16 |

### P9 — Restitution avancée et traçabilité

| ID | Tâche | Exigences |
| --- | --- | --- |
| T90 | Interface selon le mode de distribution retenu (CU-1, CU-2), accessibilité | NF-11, NF-12 |
| T91 | Journal de chaîne de conservation, horodatage fiable des rapports | NF-17 |
| T92 | Affichage de la conservation des données (durée, lieu) | NF-04, NF-05, NF-13 |
| T93 | Comparaison de plusieurs exemplaires d'un document | F-91 |
| T94 | Points de traçage d'imprimante | F-90 (partie image) |
| T95 | Politique d'accès au détail des règles et seuils | NF-19 |

### P10 — Qualité et livrables

| ID | Tâche | Livrable (section 9) |
| --- | --- | --- |
| T100 | Constitution du corpus (5 catégories) ou sa description | Livrable 5 |
| T101 | Rapport d'évaluation : taux par technique et catégorie | Livrables 4, 5 |
| T102 | Équipe rouge : fichiers qui trompent les contrôles → limites connues | §8 |
| T103 | Documentation utilisateur et mentions d'avertissement | Livrables 3, 6 |
| T104 | Étude d'usage (biais d'automatisation) — protocole | §8 |

> Les fiches techniques (livrable 4) ne sont **pas** une tâche à part : chacune est livrée avec sa technique.

## 4. Chemin critique minimal (proposition de V1)

`T00 → T01 → T02 → T03 → T04 → T10 → T11 → T12 → T13 → T14 → T15 → T16 → T17`, puis métadonnées (P2) et C2PA (T30) : ce sont les seules analyses qui produisent des **preuves** ou des indices peu contestables, et elles couvrent tous les médias d'un coup.

## 5. Remarques issues de l'analyse du cahier

Elles sont développées dans l'[analyse critique](../01-analyse/analyse-critique-cdc-v0.1.md) (T01).

1. **Ligne 96** : un contenu intégré (schéma « chaîne d'analyse ») est absent du fichier ; seul son libellé subsiste.
2. **F-51** applique F-30/F-31 (tables de quantification et double compression **JPEG**) aux images clés vidéo, qui sont encodées en H.264/H.265/VP9/AV1, pas en JPEG. Ces deux analyses ne se transposent pas telles quelles.
3. **F-24** (filigranes publics) : peu de filigranes ont un lecteur public *et* non neuronal. Plusieurs lecteurs récents (audio, vidéo) sont eux-mêmes des réseaux de neurones, ce qui heurte le principe « aucune IA embarquée ». Le catalogue V1 risque d'être très court.
4. **F-72** et la vérification C2PA (F-21) nécessitent des requêtes réseau : tension avec NF-16 et avec un éventuel fonctionnement hors ligne.
5. **F-90 / F-91** (contrôle avant publication) servent un autre besoin que la détection d'IA (protection des sources) : à prioriser séparément.
6. **F-63** (lecture des documents numérisés) touche la frontière « sans IA » (OCR). *(Corrigé : ERR-0001, puis ERR-0004 : les points de traçage de F-90 relèvent du traitement d'image, pas de l'OCR.)*
7. **Section 8** : un taux d'erreur publié par technique est un critère d'acceptation ; sans corpus (T100), aucune technique ne peut être formellement acceptée. Le banc d'évaluation (T17) est donc avancé dans le socle.

## 6. Historique des modifications

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-10-26 | 0.1 | Création du découpage | Analyse du cahier des charges |
| 2026-10-26 | 0.2 | Ajout de la règle : `CLAUDE.md` et `.claude/` ne sont jamais commités (§1, T00) | Demande de TheDarkMac, règle omise lors de la consigne initiale |
| 2026-10-26 | 0.3 | L'exclusion passe de `.gitignore` à `.git/info/exclude` (§1, T00) ; ajout de la procédure de configuration par poste dans `CONTRIBUTING.md` | Demande de TheDarkMac ; la v0.2 versionnait l'exclusion dans le dépôt |
| 2026-10-26 | 0.4 | Validation par TheDarkMac ; correction de « F-94 » en F-90 (§5, ERR-0001) ; correction de la justification de `.git/info/exclude` (§1, ERR-0002) ; ajout du garde-fou CI (§1) ; lien vers le cahier des charges déplacé dans `docs/` | T00 |
| 2026-10-26 | 0.5 | Remarque 6 corrigée : seule F-63 touche l'OCR (§5, ERR-0004) ; renvoi vers l'analyse critique | T01 |
