# Analyse critique du cahier des charges v0.1

> Statut : **v1.1** ; v1.0 mergée avec T01. Document vivant : toute modification est inscrite à l'historique (§9).
> Source analysée : [`cahier-des-charges-v0.1.md`](../00-cahier-des-charges/cahier-des-charges-v0.1.md) (v0.1, brouillon, 24 oct. 2026, auteur @Jean), SHA-256 `702b468ff57099b401f9042dcc38f85951e7b224659874b86ccb519ebfc7dafc`.
> Tâche : T01. Date de rédaction : 2026-10-26.

## 1. Objet et méthode

Ce document relève les ambiguïtés, les incohérences, les dépendances cachées et les points de faisabilité du cahier des charges, avant l'arbitrage des points ouverts (T02), le modèle de menace (T03) et l'architecture (T04). Il ne tranche rien : chaque constat se termine par une **proposition** et par la **tâche** qui devra décider.

Les remarques déjà notées au §5 du [découpage](../00-plan/decoupage-taches.md) sont reprises ici et développées. La remarque 6 du découpage était erronée et a été corrigée ([ERR-0004](../errata/ERR-0004-points-de-tracage-rattaches-a-l-ocr.md)).

### Grille de lecture

| Critère | Question posée |
| --- | --- |
| C1 — Vérifiabilité | L'exigence permet-elle d'écrire un test ou une vérification qui passe ou échoue ? |
| C2 — Cohérence interne | Deux exigences ou principes se contredisent-ils ? |
| C3 — Faisabilité « sans IA » | La technique existe-t-elle sans modèle entraîné, et donne-t-elle un résultat utile ? |
| C4 — Complétude | Manque-t-il un cas, un terme, une exigence, un point ouvert ? |
| C5 — Adéquation au besoin | La technique répond-elle à la question que se pose l'utilisateur visé ? |
| C6 — Exactitude | Les faits cités (règlement, standards) sont-ils exacts et sourcés ? |

### Gravité

| Niveau | Définition |
| --- | --- |
| **Bloquant** | Empêche de démarrer une tâche, ou rend une exigence ou un critère d'acceptation impossible à satisfaire en l'état. |
| **Majeur** | Risque de produire un outil trompeur, ou un travail à refaire, si rien n'est décidé avant la tâche concernée. |
| **Mineur** | Imprécision ou manque de forme, sans risque sur le fond. |

Chaque constat porte un identifiant `A-NN`, cité par les tâches suivantes.

### Limites de l'analyse

- Analyse sur le texte seul, sans échange avec l'auteur du cahier.
- Le schéma « chaîne d'analyse » (ligne 96 du cahier) est absent : seul son libellé subsiste.
- Le cahier compagnon « Vérification assistée par IA open source » n'est pas disponible dans le dépôt.
- Les affirmations techniques sur l'état de l'art (lecteurs de filigranes, robustesse des techniques) relèvent de la connaissance générale de l'assistant ; celles qui conditionnent une décision sont marquées **à vérifier** et le seront dans la tâche concernée.

## 2. Synthèse

### Points forts

Le cahier pose des principes rares et précieux pour ce type d'outil, qui méritent d'être conservés tels quels :

- la séparation stricte **preuve / indice / information neutre**, et le principe « absence ≠ authenticité » (F-14, F-80) ;
- la **couverture** et les **analyses non menées** au rapport (F-25, F-82), qui bornent la portée d'un résultat négatif ;
- la sécurité et la confidentialité traitées comme exigences de premier rang, et le **modèle de menace avant l'architecture** (NF-15) ;
- une évaluation sérieuse : taux d'erreur par technique et par catégorie de corpus, **équipe rouge**, et **étude du biais d'automatisation** (§8).

### Principaux défauts

1. **L'objectif principal est ambigu** : le titre promet la détection de contenus IA, mais la moitié des analyses détectent la retouche ou la transformation, pas la génération (A-01, A-02).
2. **Trois contradictions internes** empêchent de satisfaire le cahier tel quel : reproductibilité contre limite de temps et données externes (A-05), secret des seuils contre explicabilité (A-06), structure du constat contre rubriques du rapport (A-46).
3. **La notion de preuve est trop large** : une signature C2PA valide prouve qui a signé quoi, pas que la déclaration est vraie ; un filigrane décodé est un résultat statistique, falsifiable (A-03).
4. **Les taux d'erreur par technique ne disent rien du rapport** : avec une vingtaine de règles, un fichier authentique aura souvent au moins un indice (A-07).
5. **Plusieurs exigences sont presque vides une fois le « sans IA » appliqué** : F-24 (filigranes), F-51 (images clés vidéo), F-70 (stylométrie) (A-35, A-38, A-41).
6. **Le profil « grand public » vise le cas le moins analysable** : une photo virale a perdu métadonnées, manifeste et signal d'origine (A-15).

### Recommandations prioritaires pour T02

1. Choisir l'objectif principal (détection de génération IA, ou analyse d'authenticité au sens large) et le public cible **ensemble** : l'un conditionne l'autre.
2. Exiger, pour chaque technique, la table des **hypothèses qu'elle distingue** (capture brute, transformation banale, retouche, génération) : c'est la condition pour implémenter F-81.
3. Redéfinir la reproductibilité « à entrées externes égales et sans interruption », et faire de ces entrées (liste de confiance, réponses réseau, versions des décodeurs) des éléments versionnés du rapport.
4. Trancher NF-19 contre l'explicabilité avant T15, puisque le format du catalogue en dépend.
5. Ajouter un taux de faux positifs **au niveau du fichier** aux critères d'acceptation.

## 3. Constats transverses

### A-01 — Objectif principal ambigu · Majeur · C5

**Constat.** Le titre et le §1 parlent de « détection de contenus IA ». Mais l'objectif du §2 est plus large (« authentique, généré ou retouché »), et une grande partie du §5 détecte la retouche classique : révisions PDF (F-60, F-61), ELA (F-32), double compression (F-31), ENF (F-42), comparaison à des références (F-35, F-64). Le §5.6 sert encore un autre besoin, la protection des sources.

**Conséquence.** Sans objectif principal, la priorisation (point ouvert du §10) n'a pas de critère, et la communication risque de promettre une « détection d'IA » que la plupart des modules ne font pas (NF-14).

**Proposition.** Formuler l'objectif en une phrase, par exemple « analyse de provenance et d'intégrité, avec un accent sur l'origine IA », et classer chaque exigence selon qu'elle sert la génération, la retouche ou la protection des sources.

**Suite.** T02 (périmètre V1, public cible) ; question à l'auteur (§8).

### A-02 — La « direction » d'un constat n'est définie pour aucune technique · Bloquant pour F-81 · C1, C5

**Constat.** F-81 demande d'indiquer vers quoi pointe chaque constat (origine IA, retouche, authenticité, rien). Or la plupart des analyses du signal réagissent à **toute** transformation, pas spécifiquement à la génération :

| Technique | Ce qu'elle révèle en pratique | Confusions principales |
| --- | --- | --- |
| F-31 double compression | Le fichier a été réenregistré | Toute image passée par une messagerie ou un réseau social |
| F-32 ELA | Zones de compression hétérogène | Retouche locale, mais aussi textures, contours, texte incrusté |
| F-33 bruit périodique | Motif de rééchantillonnage ou de génération | Grille JPEG 8×8, redimensionnement, motifs de la scène |
| F-34 traces CFA | Présence : capture par un capteur. Absence : ambiguë | Redimensionnement, compression forte, génération |
| F-40 coupure de bande | Encodage avec perte, rééchantillonnage | Synthèse vocale à basse fréquence d'échantillonnage, mais aussi MP3 et téléphonie |

**Conséquence.** Sans table « technique → hypothèses distinguées », chaque développeur choisira la direction à sa façon, et le rapport attribuera à l'IA ce qui relève d'une simple recompression.

**Proposition.** Ajouter à la fiche technique (NF-09) une rubrique obligatoire « hypothèses distinguées », sur quatre hypothèses : capture brute, transformation banale (recompression, redimensionnement), retouche, génération. Une technique qui ne distingue pas la génération des transformations banales ne peut pas produire la direction « origine IA ».

**Suite.** T02 (règles de graduation), T11 (modèle du constat), fiches de chaque technique.

### A-03 — La preuve est définie trop largement · Majeur · C2, C5

**Constat.** Le glossaire définit la preuve comme un « élément vérifiable qui établit un fait », avec deux exemples : signature valide et filigrane décodé. Mais :

- une signature C2PA valide établit **qui a signé** et que le contenu **n'a pas changé depuis** ; elle n'établit pas que les déclarations du manifeste sont vraies. L'exemple du §6 (« preuve · direction : origine IA ») présente une déclaration signée comme un fait sur le contenu ;
- un signataire hors liste de confiance peut signer n'importe quoi : F-22 le distingue, mais le classement F-80 ne dit pas si c'est encore une preuve ;
- la lecture d'un filigrane est en général un **test statistique** avec un taux de faux positifs ; plusieurs schémas peuvent aussi être **ajoutés** à un contenu authentique pour le discréditer (attaque par usurpation).

**Proposition.** Définir la preuve comme « un fait établi par une vérification cryptographique ou déterministe, accompagné de l'énoncé exact de ce qu'il établit ». Exemple : « le certificat X, reconnu par la liste de confiance Y, a signé un manifeste qui déclare une génération par IA, et le contenu n'a pas changé depuis ». Un filigrane n'est une preuve que si son schéma est cryptographique et son taux de faux positifs documenté et négligeable ; sinon, c'est un indice fort.

**Suite.** T02, T11, T30, T31.

### A-04 — Le marquage ne couvre que les acteurs de bonne foi · Majeur · C5

**Constat.** Le §1 s'appuie sur l'article 50 de l'AI Act. Ce marquage est posé par les fournisseurs qui s'y conforment. Un faussaire utilise un modèle libre exécuté localement, un fournisseur hors de l'UE, ou retire le marquage. Les preuves les plus solides de l'outil portent donc sur les contenus **qui n'ont pas été dissimulés** ; face à un adversaire, il ne reste que les indices du signal.

**Proposition.** Le dire dans la documentation utilisateur et les mentions (livrables 3 et 6) : l'outil reconnaît les contenus déclarés ; il ne garantit rien contre un faussaire qui retire les marques.

**Suite.** T103, NF-14.

### A-05 — La reproductibilité (NF-06) est contredite par trois autres exigences · Bloquant pour le critère §8 · C2

**Constat.** NF-06 et le critère du §8 exigent les mêmes constats pour le même fichier, la même version de l'outil et du catalogue. Trois éléments l'empêchent :

1. **NF-08** borne le temps d'analyse et livre les résultats obtenus : sur une machine plus lente, une analyse interrompue donne un rapport différent.
2. **F-21 et F-72** dépendent de données externes qui changent : liste de confiance C2PA, révocation des certificats, contenu des bases bibliographiques.
3. Les **décodeurs** (JPEG, HEIC, audio, vidéo) peuvent produire des valeurs légèrement différentes d'une version à l'autre ; les analyses du signal en dépendent.

**Proposition.** Reformuler NF-06 : « même fichier, mêmes versions de l'outil, du catalogue et des dépendances, mêmes données externes, et analyse non interrompue : mêmes constats ». En conséquence :

- borner l'analyse par un budget de travail déterministe plutôt que par le seul temps écoulé, ou exclure les analyses interrompues de la garantie, en le signalant au rapport ;
- inscrire au rapport la version de la liste de confiance, la date de vérification et les réponses externes utilisées ;
- figer les versions des dépendances, et les inscrire au rapport (rubrique « Versions »).

**Suite.** T02, T04, T14, T15, T18.

### A-06 — Le secret des seuils (NF-19) contredit l'explicabilité · Bloquant · C2

**Constat.** NF-19 restreint l'accès au détail des règles et des seuils. Cela s'oppose à :

- l'**objectif 4** (rapport « vérifiable par un expert ») et au principe d'**explicabilité** (chaque constat cite sa règle) ;
- **NF-07** (chaque version du catalogue est « consultable ») ;
- l'option **open source** du §10 : dans un logiciel ouvert, les seuils sont dans le code ;
- le principe de Kerckhoffs : un contrôle qui ne tient que tant que la règle est secrète ne tient pas longtemps. Le §8 prévoit d'ailleurs une équipe rouge, qui documente publiquement les contournements.

Le point ouvert du §10 (Rapport) pose la question « qui voit quoi », mais ne signale pas la contradiction.

**Proposition.** Trancher en T02 entre : (a) tout publier et assumer que la robustesse vient de la combinaison des techniques ; (b) publier les règles mais pas certaines valeurs de seuil, en acceptant qu'un expert ne puisse pas tout vérifier ; (c) un accès restreint, incompatible avec une licence ouverte. Le choix conditionne le format du catalogue (T15).

**Suite.** T02 avant T15.

### A-07 — Les taux par technique ne bornent pas l'erreur du rapport · Majeur · C1, C5

**Constat.** Le §8 mesure les faux positifs **par technique**. Mais le rapport présente **tous** les indices. Si une image JPEG passe une vingtaine de règles qui ont chacune 1 % de faux positifs, et en supposant ces règles indépendantes, la probabilité qu'un fichier authentique porte au moins un indice est de 1 − 0,99²⁰ ≈ 18 %. Les règles n'étant pas indépendantes, le chiffre réel sera différent, mais l'ordre de grandeur montre le risque.

**Conséquence.** Un utilisateur qui voit « un indice d'origine IA » sur une photo authentique sur cinq cessera de faire confiance à l'outil, ou, pire, accusera à tort (risque noté au §10, Données et cadre légal).

**Proposition.** Ajouter aux critères d'acceptation un taux de faux positifs **par fichier** : part des fichiers authentiques dont le rapport contient au moins un indice dirigé vers l'origine IA. Ce taux dépend des règles de combinaison (point ouvert du §10, Rapport), qui deviennent donc un préalable à l'acceptation.

**Suite.** T02, T17.

### A-08 — « Couvert par un test » ne convient pas à toutes les exigences · Majeur · C1

**Constat.** Le §8 exige que chaque exigence F et NF soit couverte par au moins un test. Plusieurs ne se testent pas automatiquement : NF-12 (accessibilité), NF-13 (conformité légale), NF-14 (honnêteté des textes), NF-15 (un document à rédiger), l'étude d'usage.

**Proposition.** Associer à chaque exigence une méthode de vérification parmi quatre : **inspection** (relecture), **analyse** (raisonnement, calcul), **démonstration** (essai manuel), **test** (automatisé). La matrice de traçabilité (T17) porte cette colonne.

**Suite.** T17.

### A-09 — Le §5.4 décrit des techniques, pas des exigences vérifiables · Majeur · C1

**Constat.** Le §5 annonce des exigences « formulées pour être vérifiables ». Les §5.1 à 5.3 et 5.5 suivent la forme « L'outil doit… ». Le §5.4, lui, liste des techniques (« Tables de quantification JPEG… », « Spectrogramme… ») sans résultat attendu, sans condition de déclenchement d'un constat, ni données de référence. Par ailleurs, le §1 affirme que le cahier ne fixe pas de technologies ; nommer ELA, PRNU ou ENF n'est pas choisir une technologie, mais c'est fixer la **solution** plutôt que le besoin.

**Proposition.** Pour chaque analyse du §5.4, préciser dans sa fiche : la question à laquelle elle répond, les formats où elle s'applique, les données de référence nécessaires, ce qui déclenche un constat et sa direction (A-02). Considérer la liste du §5.4 comme un **catalogue de candidats** à prioriser, non comme un engagement.

**Suite.** T02 (priorisation), fiche de chaque technique.

### A-10 — Termes centraux non définis · Mineur · C4

**Constat.** Le glossaire omet plusieurs termes que les exigences utilisent : **constat**, **direction**, **information neutre**, **analyse non menée**, **manifeste**, **ingrédient** (C2PA), **DigitalSourceType**, **arrêt brutal** (NF-03), **exécution isolée** (NF-01). « Signature » désigne à la fois la signature C2PA (F-21), la signature électronique PDF (F-60) et les « signatures » d'outils de génération (F-12).

**Proposition.** Compléter le glossaire ; réserver « signature » au sens cryptographique et appeler « empreintes d'outils » les traces de F-12.

**Suite.** T11 (modèle de données), T103.

### A-11 — Les principes du §2 n'ont pas d'identifiant · Mineur · C1

**Constat.** Les six principes directeurs ne sont pas numérotés et ne peuvent donc pas figurer dans la matrice de traçabilité. Certains doublonnent une exigence (Reproductibilité = NF-06, Modularité = NF-10) ; d'autres ne sont couverts que partiellement (« Preuve ≠ indice » par F-80 seul).

**Proposition.** Numéroter les principes (P-01 à P-06) et les inscrire dans la matrice.

**Suite.** T17.

### A-12 — Calibrer et évaluer sur le même corpus · Majeur · C1, C3

**Constat.** Les seuils seront inévitablement ajustés sur le corpus du §8, qui sert aussi à mesurer les taux d'erreur. Mesurer sur les données qui ont servi à régler donne des taux optimistes. Par ailleurs, le §10 demande si « un seuil calibré sur un corpus » est admis : c'est déjà une forme d'apprentissage.

**Proposition.** Séparer le corpus en une partie de calibrage et une partie d'évaluation, jamais utilisée pour régler. Trancher la frontière « sans IA » en T02 en tenant compte de ce point : un seuil ajusté à la main sur un corpus et une régression logistique à trois paramètres diffèrent peu en nature.

**Suite.** T02, T17, T100.

### A-13 — Les règles vieillissent aussi · Mineur · C5

**Constat.** Le §1 reproche aux détecteurs entraînés de vieillir « à chaque nouveau générateur ». Les règles du signal vieillissent de la même façon : un artefact typique d'une génération de modèles disparaît avec la suivante. Seuls les contrôles cryptographiques (C2PA) et déclaratifs ne vieillissent pas, mais ils dépendent de l'adoption du marquage.

**Proposition.** Dater les taux d'erreur publiés, et prévoir de renouveler la catégorie « Générés » du corpus.

**Suite.** T100, T101.

### A-14 — Plusieurs techniques servent aussi à identifier une source · Majeur · C5

**Constat.** Le hors-périmètre exclut l'identification de personnes, et NF-15 fait de l'identité des sources un bien à protéger. Or plusieurs exigences sont à **double usage** :

- F-35 (PRNU) relie une photo à un appareil précis ;
- F-90 (points de traçage) révèle l'imprimante et la date d'impression ;
- F-91 (comparaison d'exemplaires) est exactement la technique qui permet de savoir **quel destinataire** a fait fuiter un document.

Présentées comme protection des sources (§5.6), elles servent tout autant à les identifier.

**Proposition.** Traiter ce double usage dans le modèle de menace (T03) : qui est l'adversaire si l'outil est utilisé par l'organisation qui cherche l'auteur d'une fuite ? Décider en T02 si ces fonctions entrent dans la V1.

**Suite.** T02, T03.

### A-15 — Le cas d'usage grand public est le moins analysable · Majeur · C5

**Constat.** La question type du grand public (« Cette photo virale est-elle réelle ? ») porte sur un fichier qui a presque toujours transité par un réseau social ou une messagerie : métadonnées et manifeste retirés, image recompressée et redimensionnée. F-06 le reconnaît et recommande d'obtenir l'original, ce que le grand public ne peut en général pas faire. L'outil répondra le plus souvent « rien de concluant ».

**Proposition.** Tenir compte de cette limite dans le choix du public cible (T02) : les profils qui ont accès aux **originaux** (journalistes, RH, juristes) tireront bien plus de l'outil.

**Suite.** T02.

### A-16 — Plusieurs exigences dépendent du mode de distribution, non tranché · Majeur · C2

**Constat.** Le journal de T00 note un choix provisoire « CLI + bibliothèque ». Plusieurs exigences ne s'entendent pas de la même façon selon le mode :

| Exigence | Difficulté en mode local (CLI, bibliothèque) |
| --- | --- |
| NF-01 isolation | Une bibliothèque s'exécute dans le processus de l'appelant ; l'isolation suppose un sous-processus ou un bac à sable, que la bibliothèque doit imposer. |
| NF-17 journal « qui, quand » | Sans compte, « qui » n'est pas connu ; un journal local est modifiable par l'utilisateur. |
| NF-17 horodatage fiable | Suppose une autorité d'horodatage externe, donc une requête sortante (NF-16). |
| NF-05 conservation affichée | Trivial en local, central sur serveur. |
| NF-12 accessibilité | Pour une CLI, porte surtout sur les exports du rapport. |

**Proposition.** Arbitrer le mode de distribution en T02 avant ces exigences, et réécrire chacune pour le mode retenu.

**Suite.** T02, T03, T04.

## 4. Constats par section

### §1 — Objet et contexte

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-20 | Dates de l'AI Act : cohérentes avec les sources secondaires consultées (§7), mais le délai jusqu'au 2 décembre 2026 ne vaut que pour l'obligation de marquage de l'article 50(2), pour les systèmes mis sur le marché avant le 2 août 2026. La phrase du cahier le généralise. Les sources citées sont une page de la Commission et un blog de formation. | Mineur · C6 | Citer le texte publié au Journal officiel (EUR-Lex) et restreindre la phrase à l'article 50(2). | Auteur |
| A-21 | « Lire ces marquages relève de la cryptographie et de l'analyse de formats, pas de l'IA » : exact pour C2PA et les métadonnées. Pour les filigranes invisibles, plusieurs lecteurs récents sont eux-mêmes des réseaux de neurones (**à vérifier** en T31). Le code de bonnes pratiques final reconnaît d'ailleurs qu'aucune technique de marquage ne suffit seule (§7). | Majeur · C3, C6 | Nuancer : les marquages cryptographiques se lisent sans IA ; les filigranes, pas toujours. | T31, auteur |
| A-22 | Le cahier compagnon est cité trois fois mais absent ; l'articulation entre les deux reste ouverte. | Mineur · C4 | Obtenir le cahier compagnon avant T02. | Auteur |

### §3 — Périmètre

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-23 | Aucune matrice « format × technique ». Les analyses JPEG (F-30, F-31) ne s'appliquent pas à HEIC (HEVC) ni à WebP avec perte (VP8) ; PNG est sans perte ; le « texte collé » n'a ni empreinte de fichier ni métadonnées. | Majeur · C4 | Établir la matrice d'applicabilité ; elle alimente aussi F-82 (analyses non menées). | T02, T11 |
| A-24 | DOCX et ODT sont classés « Texte » alors que ce sont des conteneurs : images embarquées, modifications suivies, identifiants de révision. Le PDF a une extraction vers les modules image et texte (F-63) ; DOCX/ODT, non. | Mineur · C4 | Ajouter une exigence symétrique de F-63 et étendre F-71 aux modifications suivies. | T02 |
| A-25 | Fichiers à contenus multiples non évoqués : HEIC à plusieurs images, carte de profondeur, photo animée, vidéo à plusieurs pistes. | Mineur · C4 | Préciser quelles parties sont analysées ; les autres vont dans F-82. | T13 |
| A-26 | La recherche d'antériorité (retrouver une version plus ancienne d'une image en ligne) n'est ni dans ni hors du périmètre, alors que c'est la première vérification d'un journaliste. | Mineur · C4 | L'inscrire explicitement hors périmètre, ou en point ouvert. | T02 |

### §4 — Utilisateurs et cas d'usage

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-27 | Les cas d'usage ne sont reliés à aucune exigence ; pas de cas d'usage pour l'analyse par lots, pourtant en point ouvert. | Mineur · C1 | Relier CU-1 à CU-5 aux exigences dans la matrice (CU-2 → F-84, CU-3 → F-83, CU-4 → F-35, F-42, F-64, CU-5 → F-90, F-91). | T17 |
| A-28 | Le profil enseignant cumule le risque le plus grave (accusation de triche) et le module le moins fiable (texte, de l'aveu même du §10). | Majeur · C5 | Ne pas retenir l'enseignant comme cible tant que le module texte n'a pas de taux d'erreur publiés ; renforcer les mentions pour ce profil. | T02, T103 |

### §5.1 à §5.3 — Soumission, métadonnées, provenance

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-29 | F-01 parle de « soumettre un fichier » ; le texte collé (§3) n'est pas un fichier, et F-02, F-03, F-05 ne s'y appliquent pas. | Mineur · C2 | Ajouter une exigence de saisie de texte et préciser les analyses applicables. | T13 |
| A-30 | F-05 ne précise ni l'algorithme ni ce qui est haché. Le découpage a retenu SHA-256 (T13) sans ADR. | Mineur · C4 | Décider l'algorithme en T04, par ADR ; empreinte du fichier entier, octet pour octet. | T04 |
| A-31 | F-02 : un fichier peut être valide dans deux formats à la fois (fichier polyglotte), ce qui trompe l'identification et peut viser un analyseur précis. | Mineur · C4 | À traiter dans le modèle de menace. | T03 |
| A-32 | F-06 et F-13 : « dimensions typiques », « dimensions atypiques » supposent une liste de référence non prévue. | Mineur · C1 | Mettre ces listes dans le catalogue (F-26), versionnées. | T15, T23, T24 |
| A-33 | F-11 ne cite que deux valeurs IPTC. Le vocabulaire DigitalSourceType en compte d'autres pertinentes, dont `algorithmicMedia`, `compositeSynthetic` et `algorithmicallyEnhanced` (retouche assistée par algorithme) ; le même vocabulaire sert dans les actions C2PA (F-23) (**à vérifier** sur la liste IPTC en T22). | Mineur · C4 | Reprendre le vocabulaire complet, avec une direction par valeur. | T22, T30 |
| A-34 | F-14 fait de l'absence de métadonnées une information neutre. C'est un **choix de politique** défendable (les messageries retirent les métadonnées), non un constat statistique : les sorties de générateurs en ligne en sont souvent dépourvues. F-06 utilise pourtant la même absence comme indice de transfert. | Mineur · C2 | Écrire la règle explicitement : neutre vis-à-vis de l'origine IA, utilisable comme indice de transfert. | T23, T24 |
| A-35 | F-24 : peu de filigranes ont un lecteur à la fois public et non neuronal ; pour le texte, la détection d'un filigrane exige en général la clé du fournisseur. Le catalogue V1 risque d'être presque vide (remarque 3 du découpage). | Majeur · C3 | Recenser les schémas réellement lisibles en T31 avant de s'engager ; sinon, réduire F-24 à un point d'extension. | T02, T31 |
| A-36 | F-22 : les états ne reprennent pas le vocabulaire de validation C2PA, et il manque : certificat expiré ou révoqué, manifeste distant (récupéré par une URL, donc requête sortante), ingrédients aux états différents, date de la vérification. | Majeur · C4 | Aligner les états sur la spécification C2PA en vigueur, ajouter les cas manquants. | T30 |
| A-37 | F-26 : la mise à jour du catalogue est une surface d'attaque (un catalogue altéré peut blanchir des faux). Le cahier parle tour à tour de « catalogue de signatures et de marquages » (F-26) et de « catalogue de règles » (NF-07, §6) : on ne sait pas si les seuils en font partie. | Majeur · C2, C4 | Préciser le contenu du catalogue ; prévoir l'authentification de ses mises à jour. | T03, T15 |

### §5.4 — Analyses du signal

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-38 | **F-51** applique F-30 à F-34 aux images clés vidéo. F-30 et F-31 sont propres au JPEG (remarque 2 du découpage) ; les traces CFA (F-34) sont détruites par la compression vidéo ; l'ELA (F-32) suppose une recompression JPEG et n'a pas de sens sur une image clé H.264. Il reste F-33. | Majeur · C3 | Réécrire F-51 : liste des analyses réellement applicables aux images vidéo décodées. | T02, T71 |
| A-39 | F-35 (PRNU) suppose de nombreuses photos de référence du même appareil ; elle répond à « cette photo vient-elle de cet appareil ? », pas à « est-elle générée ? ». Double usage : voir A-14. | Mineur · C5 | Préciser le nombre minimal de références et la direction (authenticité ou source). | T45 |
| A-40 | F-41 : détecter des respirations par des règles écrites est difficile, et les synthèses vocales récentes en produisent. F-42 (ENF) ne s'applique qu'aux enregistrements qui captent le réseau électrique, et suppose une base de référence par réseau, rarement publique. | Mineur · C3 | Limiter F-41 au silence numérique et au plancher de bruit en V1 ; F-42 hors V1 sauf base de référence identifiée. | T02, T61, T62 |

### §5.4 — Texte

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-41 | **F-70** (stylométrie) : sans texte de référence du même auteur, aucune mesure ne permet de seuil défendable. Les détecteurs fondés sur la régularité du style pénalisent les auteurs qui écrivent dans une langue seconde (Liang et al., *Patterns*, 2023, à propos de détecteurs GPT) ; le même biais menace une stylométrie à règles. | Majeur · C3, C5 | En V1, F-70 ne produit que des informations neutres, ou seulement une comparaison à des textes de référence fournis par l'utilisateur (comme CU-4). | T02, T82 |
| A-42 | **F-72** envoie les références citées à des bases externes. Une bibliographie peut révéler le contenu d'un travail confidentiel, alors que NF-16 n'interdit que l'envoi du fichier et de ses données identifiantes. Une référence introuvable peut aussi être une coquille ou de la littérature grise. | Majeur · C2 | Étendre NF-16 au contenu, pas seulement aux données identifiantes ; rendre F-72 désactivable et présenter une référence introuvable comme un indice faible. | T03, T83 |
| A-43 | F-73 : la direction d'un caractère invisible ou d'un homoglyphe n'est pas dite (copie depuis une source, dissimulation volontaire, mise en page). | Mineur · C1 | Donner une direction par cas, souvent « rien de particulier ». | T80 |

### §5.5, §5.6 et §6 — Restitution et rapport

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-44 | F-84 (visualisations) et NF-12 (accessibilité) : une carte ELA ou un spectrogramme n'est pas accessible sans alternative textuelle. | Mineur · C2 | Chaque visualisation porte une description textuelle de ce qu'elle montre. | T16, T90 |
| A-45 | F-90 et F-91 servent un autre besoin que la détection (remarque 5 du découpage) et sont à double usage (A-14). | Majeur · C5 | Prioriser séparément, après le modèle de menace. | T02, T03 |
| A-46 | **Structure du constat** : le §6 fixe cinq éléments (phrase, donnée, règle, catégorie, direction). Mais la rubrique « Indices » exige aussi les **limites connues**, et la rubrique « Preuves » la **source** ; ni l'une ni l'autre ne figurent dans les cinq éléments. Il manque aussi la **localisation** (zone d'image, intervalle de temps, objet PDF) et la **version** de la règle. | Majeur · C2 | Modèle du constat en T11 : phrase, donnée observée, règle (identifiant et version), technique, catégorie, direction, limites connues, source, localisation. | T11 |
| A-47 | L'exemple du §6 cite comme règle « vérification C2PA (F-21) » : c'est un identifiant d'exigence, pas une règle du catalogue. | Mineur · C1 | Distinguer les identifiants d'exigence (F-xx) et de règle (par exemple `R-C2PA-001`, versionnée). | T11, T15 |
| A-48 | La rubrique « Identification » inscrit le **nom** du fichier et son **empreinte**. Un nom de fichier peut identifier une personne ; une empreinte publiée permet à qui détient l'original de vérifier que la source l'avait (NF-18). | Mineur · C2 | Traiter le nom comme donnée identifiante (masqué par défaut) ; examiner l'empreinte en T03. | T03, T16 |
| A-49 | Masquer les données identifiantes dans l'export machine (NF-18) empêche un expert de vérifier certains constats (objectif 4), et le contrôle avant publication (F-90) doit justement les montrer. | Mineur · C2 | Masquage par défaut, levée explicite et tracée (NF-17), comme le prévoit déjà le §6 pour l'interface. | T16 |

### §7 — Exigences non fonctionnelles

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-50 | NF-15 est une activité du projet (rédiger un document), pas une propriété du produit. | Mineur · C1 | La déplacer dans les livrables, où elle figure déjà (livrable 7). | Auteur |
| A-51 | NF-13 (« pays où il est proposé ») est illimité si l'outil est un logiciel libre diffusé partout. | Mineur · C1 | Lier NF-13 au point ouvert « pays visés ». | T02 |
| A-52 | NF-16 exige l'inventaire des requêtes sortantes, mais ne dit pas comment le vérifier. | Mineur · C1 | Test : exécuter l'analyse dans un environnement sans réseau et journaliser toute tentative de connexion. | T17 |
| A-53 | NF-01 « de façon isolée » ne précise pas le niveau d'isolation (processus, conteneur, machine virtuelle). Les bibliothèques de décodage les plus utilisées sont écrites en C et ont un historique de failles. | Majeur · C1 | Fixer le niveau d'isolation dans le modèle de menace, puis en T04. | T03, T04, T14 |

### §8 et §9 — Qualité, tests, livrables

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-54 | Les taux d'erreur ne sont assortis ni de taille d'échantillon ni d'intervalle de confiance. Un taux mesuré sur 50 fichiers ne vaut pas un taux sur 5 000. | Majeur · C1 | Publier chaque taux avec l'effectif et un intervalle de confiance. | T17, T101 |
| A-55 | Pour les contrôles déterministes (C2PA, empreinte, caractères invisibles), un taux de faux négatifs sur corpus n'a pas de sens : ils sont justes ou faux. | Mineur · C1 | Les évaluer par des tests de conformité (fichiers de test du standard), et réserver les taux aux techniques statistiques. | T17, T30 |
| A-56 | Les techniques comparatives (F-35, F-42, F-64) supposent des **jeux de référence** dans le corpus, que le §8 ne prévoit pas. | Mineur · C4 | Ajouter une sous-catégorie « références » au corpus. | T100 |
| A-57 | L'étude d'usage implique des participants humains : protocole, consentement, données personnelles. « Erreur grave » n'est pas défini. | Majeur · C1, C4 | Définir l'erreur grave (par exemple : conclure « généré » sur un fichier authentique) et le protocole en T104 ; vérifier si l'étude est réaliste pour le projet. | T02, T104 |
| A-58 | Livrables absents : matrice de traçabilité (exigée de fait par le §8), guide d'installation et d'exploitation, procédure de mise à jour du catalogue. | Mineur · C4 | Les ajouter au §9. | Auteur, T17 |

### Forme du document

| ID | Constat | Gravité | Proposition | Suite |
| --- | --- | --- | --- | --- |
| A-59 | Le schéma « chaîne d'analyse » est absent (ligne 96) : seul son libellé subsiste (remarque 1 du découpage). | Mineur · C4 | Demander le schéma à l'auteur. | Auteur |
| A-60 | Le cahier n'a ni historique de versions ni circuit de validation ; c'est un brouillon (v0.1) qui évoluera. | Mineur · C4 | Chaque nouvelle version reçue est versionnée dans `docs/00-cahier-des-charges/`, et cette analyse est mise à jour (historique §9). | Méthode |

## 5. Contradictions et dépendances cachées

| Élément | Entre en tension avec | Constat |
| --- | --- | --- |
| NF-06 reproductibilité | NF-08, F-21, F-72, versions des décodeurs | A-05 |
| NF-19 secret des seuils | Explicabilité, objectif 4, NF-07, licence ouverte | A-06 |
| NF-16 requêtes sortantes minimales | F-21 (révocation, manifestes distants), F-72, NF-17 (horodatage) | A-16, A-36, A-42 |
| NF-17 journal « qui, quand » | Usage anonyme (§10), mode local | A-16 |
| NF-01 isolation | Distribution en bibliothèque | A-16, A-53 |
| §6 structure du constat (5 éléments) | §6 rubriques Indices et Preuves | A-46 |
| NF-18 masquage | Objectif 4 (vérification par un expert), F-90 | A-49 |
| F-84 visualisations | NF-12 accessibilité | A-44 |
| « Absence ≠ authenticité » | F-81, direction « authenticité » | Les indices vers l'authenticité restent permis (traces CFA, PRNU), mais avec la même prudence que les autres : à écrire dans la règle de rédaction du rapport (T16). |
| F-14 absence neutre | F-06 absence comme indice de transfert | A-34 |
| Hors périmètre « identification de personnes » | F-35, F-90, F-91 | A-14 |

## 6. Points ouverts à ajouter au §10 du cahier

Ces points ne figurent pas au §10 et devront être arbitrés en T02 ou dans la tâche citée.

1. Objectif principal : détection de génération IA, ou analyse d'authenticité au sens large (A-01).
2. Définition de la preuve, et statut d'une déclaration signée ou d'un filigrane (A-03).
3. Table des hypothèses distinguées par technique, condition de F-81 (A-02).
4. Définition exacte de la reproductibilité et des entrées externes versionnées (A-05).
5. Contradiction NF-19 / explicabilité / licence (A-06).
6. Taux de faux positifs par fichier, et règles de combinaison comme préalable à l'acceptation (A-07).
7. Séparation calibrage / évaluation du corpus (A-12).
8. Double usage des techniques d'identification de source (A-14).
9. Contenu du catalogue (signatures seules, ou aussi règles et seuils) et authentification de ses mises à jour (A-37).
10. Niveau d'isolation de l'analyse (A-53).
11. Recherche d'antériorité : dans ou hors périmètre (A-26).
12. Faisabilité de l'étude d'usage pour le projet (A-57).

## 7. Vérification des faits cités

| Affirmation du cahier | Résultat | Sources |
| --- | --- | --- |
| L'article 50 de l'AI Act s'applique depuis le 2 août 2026 | Cohérent avec les sources consultées. | [Commission européenne, communiqué IP/26/1328](https://europa.eu/newsroom/ecpc-failover/pdf/ip-26-1328_en.pdf) |
| Les systèmes déjà sur le marché ont jusqu'au 2 décembre 2026 | Cohérent avec plusieurs sources secondaires, qui précisent que ce délai ne concerne que le marquage de l'article 50(2) et les systèmes mis sur le marché avant le 2 août 2026 (omnibus numérique). Les sources divergent sur la date d'entrée en vigueur de l'omnibus. **À confirmer sur EUR-Lex.** | [Usercentrics](https://usercentrics.com/knowledge-hub/eu-ai-act-high-risk-delay-article-50-transparency-consent/), [FEDIL](https://fedil.lu/en/publications/ai-act-update-enforcement-begins-as-the-digital-omnibus-reshapes-the-timeline/?pdf=1) |
| Le marquage des contenus générés se généralise | Le code de bonnes pratiques final sur le marquage et l'étiquetage a été publié le 10 juin 2026 ; il est volontaire, et reconnaît qu'aucune technique de marquage ne satisfait seule toutes les exigences. | [Jones Day](https://www.jonesday.com/en/insights/2026/06/european-commission-publishes-final-code-of-practice-on-marking-and-labelling-aigenerated-content), [SCL](https://www.scl.org/european-commission-publishes-code-of-practice-on-marking-and-labelling-ai-generated-content/) |
| Valeurs IPTC `trainedAlgorithmicMedia`, `compositeWithTrainedAlgorithmicMedia` | Valeurs existantes du vocabulaire DigitalSourceType, d'après la connaissance de l'assistant. Liste complète **à vérifier** en T22. | Vocabulaire IPTC NewsCodes « digitalsourcetype » |

Recherche faite le 2026-10-26. Les sources secondaires sont des cabinets et des blogs ; elles suffisent à juger la phrase du cahier plausible, pas à la citer comme référence.

## 8. Suites

### Questions à l'auteur du cahier

1. Quel est l'objectif principal : détection de génération IA, ou authenticité au sens large (A-01) ?
2. Que contenait le schéma « chaîne d'analyse » (A-59) ?
3. Le cahier compagnon est-il disponible (A-22) ?
4. La liste du §5.4 est-elle un engagement, ou un catalogue de candidats (A-09) ?
5. Le « catalogue de règles » contient-il les seuils (A-37) ?
6. Quelle source primaire fonde la date du 2 décembre 2026 (A-20) ?

### Entrées pour les tâches suivantes

| Tâche | Constats à traiter |
| --- | --- |
| T02 — Arbitrages | A-01, A-02, A-05, A-06, A-07, A-12, A-14, A-15, A-16, A-23, A-26, A-28, A-35, A-38, A-40, A-41, A-45, A-51, A-57 ; points du §6 |
| T03 — Modèle de menace | A-14, A-16, A-31, A-37, A-42, A-48, A-53 |
| T04 — Architecture | A-05, A-16, A-30, A-53 |
| T11 — Modèle de données | A-02, A-03, A-10, A-23, A-46, A-47 |
| T13, T14, T15, T16, T17, T18 | A-25, A-29 ; A-05, A-53 ; A-32, A-37, A-47 ; A-44, A-48, A-49 ; A-07, A-08, A-11, A-27, A-52, A-54, A-55 ; A-05 |
| Modules (T22 à T83) | A-33, A-34, A-36, A-38 à A-43 |
| P10 — Qualité | A-12, A-13, A-54 à A-57 |

### Arbitrages

Les points adressés à T02 ont été tranchés ou reportés : voir le [registre des arbitrages](../02-arbitrages/registre-des-arbitrages.md). Le contenu de cette analyse n'est pas modifié.

### Effet sur le découpage

- Remarque 6 du découpage corrigée ([ERR-0004](../errata/ERR-0004-points-de-tracage-rattaches-a-l-ocr.md)).
- Le découpage n'est pas modifié pour le reste : les arbitrages de T02 décideront des tâches à ajouter, fusionner ou retirer.

## 9. Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-10-26 | 1.0 | Création | T01 |
| 2026-10-26 | 1.1 | Renvoi vers le registre des arbitrages (§8) | T02 |
