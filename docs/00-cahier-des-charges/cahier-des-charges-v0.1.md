# Cahier des charges — Détection de contenus IA sans IA

Oct 24, 2026 · @Jean · Version 0.1, brouillon de travail

## 1. Objet et contexte

Ce cahier des charges décrit un outil qui examine des fichiers pour y relever des preuves et des indices de génération ou de retouche par IA, sans embarquer aucun modèle d’IA.

L’outil ne prétend pas trancher à coup sûr. Il rassemble ce qui se vérifie (une signature, une métadonnée, un filigrane documenté) et ce qui se mesure seulement (des anomalies du signal), puis il explique chaque constat.

Les détecteurs courants reposent sur des modèles entraînés. Leurs résultats sont difficiles à expliquer et vieillissent à chaque nouveau générateur.

En parallèle, le marquage des contenus générés se généralise. Depuis le 2 août 2026, l’article 50 de l’AI Act européen exige que les sorties des IA génératives soient marquées dans un format lisible par machine ; les systèmes déjà sur le marché ont jusqu’au 2 décembre 2026 ([Commission européenne](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content), [synthèse Learnsignal](https://www.learnsignal.com/blog/eu-ai-act-article-50-transparency-labelling-obligations-explained/)). Lire ces marquages relève de la cryptographie et de l’analyse de formats, pas de l’IA.

Ce document fixe le besoin. Il ne fixe ni technologies ni architecture, et laisse ouverts les points listés en section 10.

Un cahier distinct, « Vérification assistée par IA open source », traite la véracité des informations ; celui-ci se limite à l’authenticité des fichiers. L’articulation entre les deux reste ouverte (section 10).

## 2. Objectifs et principes directeurs

L’outil aide une personne à juger si un fichier est authentique, généré ou retouché, en montrant sur quoi repose chaque constat.

Objectifs :

1. Vérifier les preuves de provenance présentes dans un fichier : signatures, marquages documentés.
2. Extraire et interpréter les métadonnées révélatrices.
3. Mesurer des anomalies du signal et les présenter comme des indices, jamais comme des preuves.
4. Restituer un rapport lisible par un non-spécialiste et vérifiable par un expert.

Principes directeurs :

| Principe | Ce qu’il impose |
| --- | --- |
| Aucune IA embarquée | Ni réseau de neurones ni modèle entraîné ; des règles et des seuils écrits, documentés et versionnés. La frontière exacte reste à préciser (section 10). |
| Explicabilité | Chaque constat cite la règle qui l’a produit et la donnée observée. |
| Preuve ≠ indice | Ce qui est vérifié n’est jamais mélangé avec ce qui est seulement suggéré. |
| Absence ≠ authenticité | Ne rien trouver n’est jamais présenté comme une garantie. |
| Reproductibilité | Même fichier et même version des règles donnent les mêmes constats. |
| Modularité | Chaque technique s’ajoute, se retire ou se désactive sans toucher aux autres. |

## 3. Périmètre

Le périmètre couvre cinq familles de médias et trois familles d’analyses ; tout ce qui modifie ou génère du contenu en est exclu.

Médias couverts (formats indicatifs, liste définitive à arrêter en section 10) :

| Média | Formats envisagés |
| --- | --- |
| Image | JPEG, PNG, WebP, HEIC |
| Audio | WAV, MP3, AAC/M4A, FLAC, OGG |
| Vidéo | MP4, MOV, WebM |
| Document | PDF |
| Texte | texte brut, DOCX, ODT, texte collé |

Familles d’analyses :

| Famille | Question posée | Nature des résultats |
| --- | --- | --- |
| Ce que le fichier déclare | Que disent ses métadonnées ? | Informations, indices |
| Ce que le fichier porte | Contient-il une signature ou un marquage vérifiable ? | Preuves |
| Ce que le fichier est | Son signal ou sa structure présente-t-il des anomalies ? | Indices |

Hors périmètre :

- Toute détection fondée sur un modèle d’IA embarqué.
- La modification de fichiers : retrait ou ajout de métadonnées, de signatures ou de filigranes.
- La génération de contenu.
- L’identification de personnes (visage, voix).
- La délivrance d’une expertise ayant valeur légale.
- La vérification de la véracité des informations, traitée dans le cahier « Vérification assistée par IA open source ».

## 4. Utilisateurs et cas d’usage

Cinq profils peuvent utiliser l’outil ; le choix d’une cible prioritaire reste ouvert (section 10).

| Profil | Besoin type | Question typique |
| --- | --- | --- |
| Grand public | Vérifier un contenu reçu | « Cette photo virale est-elle réelle ? » |
| Journaliste, vérificateur de faits | Documenter la provenance d’un contenu | « D’où vient cette vidéo, a-t-elle été retouchée ? » |
| Enseignant | Examiner un travail rendu | « Ce texte a-t-il été collé d’un bloc ? » |
| RH, assurance, banque | Contrôler un justificatif | « Ce PDF a-t-il été modifié après émission ? » |
| Juriste, enquêteur | Préparer un dossier | « Quels éléments vérifiables puis-je présenter ? » |

Cas d’usage :

- CU-1 : analyser un fichier et lire son rapport.
- CU-2 : approfondir un constat (détail technique, visualisation).
- CU-3 : exporter le rapport pour l’archiver ou le transmettre.
- CU-4 : comparer un fichier à une référence fournie (photos du même appareil, enregistrement de référence).
- CU-5 : contrôler un document avant publication, pour repérer les marques qui identifient la source.

## 5. Exigences fonctionnelles

Les exigences suivent l’ordre de la chaîne d’analyse. Chacune est formulée pour être vérifiable ; leur priorisation reste à arbitrer (section 10).

&#91;embedded content: chaîne d’analyse · 3 familles, 1 rapport\]

Les trois familles d’analyses produisent leurs constats séparément ; le classement les range ensuite en preuves, indices ou informations neutres, sans jamais les confondre.

### 5.1 Soumission et identification

| ID | Exigence |
| --- | --- |
| F-01 | L’utilisateur doit pouvoir soumettre un fichier d’un format du périmètre. |
| F-02 | L’outil doit identifier le format réel par le contenu du fichier, non par son extension. |
| F-03 | L’outil doit signaler toute discordance entre extension et format réel. |
| F-04 | L’outil doit refuser un fichier hors périmètre ou hors limites, avec un message explicite. |
| F-05 | L’outil doit calculer l’empreinte cryptographique du fichier et l’inscrire au rapport. |
| F-06 | L’outil doit signaler les indices de transfert par messagerie ou de capture d’écran (recompression, dimensions typiques, métadonnées absentes), qui réduisent la portée des analyses, et recommander d’obtenir l’original. |

### 5.2 Métadonnées

| ID | Exigence |
| --- | --- |
| F-10 | L’outil doit extraire les métadonnées de chaque format : EXIF, XMP et IPTC (images), blocs texte (PNG), dictionnaire d’information et XMP (PDF), balises (conteneurs audio et vidéo), propriétés (documents bureautiques). |
| F-11 | L’outil doit repérer les champs qui déclarent une origine IA, dont les valeurs IPTC DigitalSourceType « trainedAlgorithmicMedia » et « compositeWithTrainedAlgorithmicMedia ». |
| F-12 | L’outil doit repérer les traces d’outils de génération connus (paramètres de génération, nom du logiciel) à partir d’un catalogue de signatures. |
| F-13 | L’outil doit relever les incohérences internes : dates impossibles, logiciel incompatible avec l’appareil déclaré, dimensions atypiques. |
| F-14 | L’outil doit présenter l’absence de métadonnées comme une information neutre, jamais comme un indice d’IA. |

### 5.3 Provenance et marquages

| ID | Exigence |
| --- | --- |
| F-20 | L’outil doit détecter un manifeste C2PA dans tout format qui peut en contenir un. |
| F-21 | L’outil doit vérifier la signature du manifeste, l’intégrité du contenu signé et la chaîne de certificats. |
| F-22 | L’outil doit afficher l’état de vérification : absent, valide, valide mais signé hors liste de confiance, invalide ou non vérifiable, avec la raison. |
| F-23 | L’outil doit restituer les déclarations du manifeste : outil d’origine, actions (dont la génération par IA), historique des éditions. |
| F-24 | L’outil doit rechercher les filigranes invisibles dont l’algorithme de lecture est public, à partir d’un catalogue. |
| F-25 | L’outil doit lister les marquages recherchés, pour borner la portée d’un résultat négatif. |
| F-26 | Le catalogue de signatures et de marquages (F-12, F-24) doit pouvoir être mis à jour sans modifier le moteur d’analyse. |

### 5.4 Analyses du signal

Pour chaque média, l’outil doit réaliser les analyses suivantes.

#### Image

| ID | Analyse |
| --- | --- |
| F-30 | Tables de quantification JPEG, comparées à des tables connues (appareils, logiciels). |
| F-31 | Détection d’une double compression JPEG. |
| F-32 | Niveau d’erreur de recompression (ELA), accompagné d’un avertissement d’interprétation. |
| F-33 | Analyse spectrale du résidu de bruit, à la recherche de motifs périodiques. |
| F-34 | Traces de dématriçage (CFA) propres aux capteurs photo. |
| F-35 | Empreinte de capteur (PRNU), comparée à des photos de référence fournies par l’utilisateur. |

#### Audio

| ID | Analyse |
| --- | --- |
| F-40 | Spectrogramme et détection des coupures nettes de bande passante. |
| F-41 | Silences : silence numérique parfait, plancher de bruit, respirations. |
| F-42 | Fréquence du réseau électrique (ENF), comparée à une référence quand elle existe. |
| F-43 | Détection de réencodages successifs. |

#### Vidéo

| ID | Analyse |
| --- | --- |
| F-50 | Conteneur et structure d’encodage : encodeur déclaré, organisation des images clés. |
| F-51 | Extraction d’images clés et application des analyses F-30 à F-34. |
| F-52 | Analyse de la piste son par les analyses F-40 à F-43. |
| F-53 | Détection des réencodages et des ruptures de structure dans le flux. |

#### PDF

| ID | Analyse |
| --- | --- |
| F-60 | Révisions incrémentales et reconstitution des versions successives, en distinguant les ajouts légitimes : linéarisation, signature électronique, formulaire rempli. |
| F-61 | Objets ajoutés ou remplacés, textes superposés, polices incohérentes. |
| F-62 | Éléments actifs (scripts, actions automatiques) signalés, jamais exécutés. |
| F-63 | Extraction des images et de la couche texte native, puis analyse par les modules image et texte. La lecture des documents numérisés relève de la frontière du « sans IA » (section 10). |
| F-64 | Comparaison à des documents de référence authentiques fournis par l’utilisateur : mise en page, polices, logiciel de production. |

#### Texte

| ID | Analyse |
| --- | --- |
| F-70 | Mesures stylométriques : longueur et variance des phrases, diversité du vocabulaire. |
| F-71 | Historique d’édition des documents bureautiques : temps d’édition, sessions de révision. Une valeur absente ou nulle reste une information neutre. |
| F-72 | Existence des références citées (DOI, titres) dans des bases bibliographiques publiques. |
| F-73 | Caractères invisibles ou substitués : caractères de largeur nulle, homoglyphes. |

### 5.5 Restitution

| ID | Exigence |
| --- | --- |
| F-80 | L’outil doit classer chaque constat : preuve, indice ou information neutre. |
| F-81 | L’outil doit indiquer vers quoi pointe chaque constat : origine IA, retouche, authenticité, ou rien de particulier. |
| F-82 | L’outil doit lister les analyses non menées, avec leur raison. |
| F-83 | L’outil doit exporter le rapport dans au moins un format lisible par une personne et un format exploitable par une machine. |
| F-84 | L’outil doit fournir les visualisations utiles à la lecture : carte ELA, spectre, spectrogramme, chronologie des révisions PDF. |

### 5.6 Contrôle avant publication

Avant de publier un document reçu, l’outil aide à vérifier qu’il ne trahit pas sa source. Il signale sans rien modifier, conformément au périmètre (section 3).

| ID | Exigence |
| --- | --- |
| F-90 | L’outil doit repérer les marques susceptibles d’identifier la source : métadonnées nominatives, numéro de série d’appareil, coordonnées GPS, points de traçage d’imprimante. |
| F-91 | L’outil doit comparer plusieurs exemplaires d’un même document pour révéler les variantes propres à chaque destinataire. |

## 6. Contenu du rapport d’analyse

Le rapport doit permettre à un non-spécialiste de comprendre ce qui a été trouvé, et à un expert de le vérifier.

| Rubrique | Contenu attendu |
| --- | --- |
| Identification | Nom, format réel, taille, empreinte cryptographique, date de l’analyse. |
| Versions | Version de l’outil et du catalogue de règles utilisés. |
| Preuves | Résultats vérifiables (signature valide ou invalide, filigrane décodé), avec leur source. |
| Indices | Constats des métadonnées et du signal, chacun avec sa règle, la valeur observée et ses limites connues. |
| Informations neutres | Éléments sans valeur probante : absence de métadonnées, champs standards. |
| Analyses non menées | Liste et raison : format partiel, fichier tronqué, référence manquante. |
| Couverture | Marquages recherchés et techniques appliquées, pour borner la portée d’un résultat négatif. |
| Avertissement | Rappel que l’outil ne délivre pas de verdict certain. |
| Données identifiantes | Masquées par défaut (GPS, numéros de série, noms d’auteur) ; révélées sur action explicite, avec un avertissement. |

Chaque constat comporte cinq éléments : une phrase en langage courant, la donnée observée, la règle appliquée, sa catégorie (F-80) et sa direction (F-81).

Exemple de constat :

> Le fichier contient un manifeste C2PA valide qui déclare une génération par IA. Catégorie : preuve · Direction : origine IA · Règle : vérification C2PA (F-21) · Donnée : signature valide, action déclarée « génération par IA ».

Aucune formulation du rapport ne doit présenter un indice comme une certitude. La forme d’une éventuelle synthèse globale reste ouverte (section 10).

## 7. Exigences non fonctionnelles

Les fichiers analysés sont à la fois sensibles et potentiellement piégés : sécurité et confidentialité sont des exigences de premier rang. Les valeurs chiffrées (limites, temps, durées de conservation) sont des points ouverts (section 10).

| ID | Domaine | Exigence |
| --- | --- | --- |
| NF-01 | Sécurité | Tout fichier est traité comme hostile : l’analyse s’exécute de façon isolée et n’exécute jamais de contenu embarqué. |
| NF-02 | Sécurité | L’outil résiste aux fichiers malformés et aux bombes de décompression, grâce à des limites de taille, de temps et de mémoire. |
| NF-03 | Robustesse | Un fichier corrompu ou partiellement lisible produit un rapport partiel, jamais un arrêt brutal. |
| NF-04 | Confidentialité | Un fichier ne sert qu’à l’analyse demandée : ni réutilisation, ni transmission à un tiers sans consentement explicite. |
| NF-05 | Confidentialité | La durée et le lieu de conservation des fichiers et des rapports sont affichés à l’utilisateur. |
| NF-06 | Reproductibilité | Même fichier, même version de l’outil et du catalogue : mêmes constats. |
| NF-07 | Traçabilité | Chaque version du catalogue de règles est datée, versionnée et consultable. |
| NF-08 | Performance | Le temps d’analyse est borné ; au-delà, l’outil livre les résultats obtenus et signale les analyses interrompues. |
| NF-09 | Maintenabilité | Chaque technique est documentée : principe, entrées, sorties, limites connues, taux d’erreur mesurés. |
| NF-10 | Évolutivité | Ajouter un format ou une technique n’exige pas de modifier les autres modules. |
| NF-11 | Lisibilité | Le rapport est compréhensible sans connaissances techniques ; le vocabulaire spécialisé renvoie au glossaire. |
| NF-12 | Accessibilité | L’interface et le rapport respectent des règles d’accessibilité reconnues ; le niveau visé reste à fixer. |
| NF-13 | Conformité | L’outil respecte la réglementation sur les données personnelles des pays où il est proposé. |
| NF-14 | Honnêteté | Aucun texte de l’outil, de sa documentation ou de sa communication ne promet une détection certaine. |
| NF-15 | Modèle de menace | Un modèle de menace est rédigé avant tout choix d’architecture : les fichiers reçus et l’identité de leurs sources sont des biens à protéger. |
| NF-16 | Requêtes sortantes | Toute requête qui quitte l’infrastructure (certificats, bases bibliographiques, références) est inventoriée, réduite au minimum, et n’emporte jamais le fichier ni ses données identifiantes. |
| NF-17 | Chaîne de conservation | Chaque soumission, consultation et export est journalisé (qui, quand) ; chaque rapport porte un horodatage fiable. |
| NF-18 | Données identifiantes | Les données qui peuvent identifier une source sont masquées par défaut, dans l’interface comme dans les exports. |
| NF-19 | Politique d’accès | Le détail des règles et des seuils n’est accessible que selon une politique définie, pour ne pas fournir de mode d’emploi aux faussaires (section 10). |

## 8. Qualité, tests et critères d’acceptation

Une technique n’est acceptée qu’avec ses taux d’erreur mesurés sur un corpus de test et publiés dans sa documentation.

Corpus de test :

| Catégorie | Contenu | Ce qu’elle mesure |
| --- | --- | --- |
| Authentiques | Captures d’appareils variés, non retouchées | Faux positifs |
| Générés | Sorties de plusieurs générateurs, anciens et récents | Faux négatifs |
| Transformés | Les deux catégories précédentes après recompression, redimensionnement, capture d’écran, passage par une messagerie | Robustesse |
| Retouchés | Fichiers authentiques modifiés : PDF édités, images retouchées | Distinction entre retouche et génération |
| Malformés | Fichiers tronqués, corrompus ou piégés | Robustesse et sécurité |

Pour chaque technique et chaque catégorie, l’évaluation mesure le taux de faux positifs, le taux de faux négatifs et la part de fichiers non analysables.

Deux mesures complètent ces taux : une étude d’usage, qui compare la décision d’un utilisateur avec et sans l’outil (biais d’automatisation), et une équipe rouge chargée de fabriquer des fichiers qui trompent les contrôles.

Critères d’acceptation :

- [ ] Chaque exigence F et NF est couverte par au moins un test identifié.
- [ ] Chaque technique publie ses taux d’erreur par catégorie de corpus.
- [ ] Aucun fichier « malformé » ne provoque d’arrêt brutal ni d’exécution de contenu.
- [ ] Deux analyses du même fichier avec la même version donnent les mêmes constats.
- [ ] Les seuils chiffrés d’acceptation, fixés lors de l’arbitrage (section 10), sont atteints.
- [ ] L’étude d’usage ne montre pas de hausse des erreurs graves avec l’outil.
- [ ] Les fichiers de l’équipe rouge qui passent les contrôles sont documentés dans les limites connues.

## 9. Livrables attendus

Le projet livre l’outil, son catalogue de règles, sa documentation et la preuve mesurée de ses performances.

1. L’outil d’analyse, dans le mode de distribution retenu (section 10).
2. Le catalogue versionné des signatures, marquages et règles.
3. La documentation utilisateur : lire un rapport, comprendre ce que l’outil ne peut pas affirmer.
4. Une fiche par technique : principe, limites connues, taux d’erreur mesurés.
5. Le corpus de test, ou sa description si les droits d’usage l’imposent, et le rapport d’évaluation.
6. Les mentions d’usage et d’avertissement destinées aux utilisateurs.
7. Le modèle de menace (NF-15).

## 10. Points ouverts à débattre

Ces points restent à arbitrer ; le document ne prend pas position. Une case cochée signale un point tranché, à reporter dans les sections concernées.

### Produit

- [ ] Nom du projet.
- [ ] Public cible prioritaire parmi les profils de la section 4.
- [ ] Mode de distribution : application web, logiciel installé, ligne de commande, API, extension de navigateur, ou une combinaison.
- [ ] Modèle économique et licence : gratuit, payant, open source.
- [ ] Langues de l’interface et des rapports.
- [ ] Périmètre de la première version : médias, formats et techniques retenus, ordre de priorité.
- [ ] Place du module texte, le moins fiable sans IA.
- [ ] Analyse par lots et analyse de flux en direct : dans le périmètre ou non.
- [ ] Validation du besoin auprès d’utilisateurs réels avant de figer le périmètre.
- [ ] Analyse groupée de plusieurs fichiers d’une même affaire (cohérences croisées).

### Principe « sans IA »

- [ ] Frontière exacte : un seuil calibré sur un corpus est-il admis ? Une pondération apprise simple ?
- [ ] Recours à des services tiers de vérification fondés sur l’IA (détecteurs de filigranes propriétaires) : admis, optionnel ou exclu.
- [ ] Principe définitif, ou contrainte de première version ; articulation avec le cahier « Vérification assistée par IA open source » : module autonome, ou appelé par cet outil.
- [ ] Lecture des documents numérisés (F-63) : les moteurs courants reposent sur des réseaux de neurones ; admise ou non.

### Rapport

- [ ] Forme de la synthèse globale : aucune, niveaux qualitatifs ou score chiffré.
- [ ] Graduation des indices et règles de combinaison entre constats.
- [ ] Formats d’export.
- [ ] Accès au détail des règles et des seuils (NF-19) : qui voit quoi, sans fournir de mode d’emploi aux faussaires.

### Données et cadre légal

- [ ] Traitement local, sur serveur, ou les deux.
- [ ] Fonctionnement hors ligne ou connexion requise (vérification des certificats C2PA, références F-72).
- [ ] Conservation des fichiers et des rapports : durée, lieu ; compte utilisateur ou usage anonyme.
- [ ] Pays visés et réglementations applicables.
- [ ] Responsabilité en cas de faux positif aux conséquences lourdes (accusation de fraude ou de triche) et mentions d’avertissement.
- [ ] Anonymisation des marques identifiantes (F-90) : hors périmètre ou fonction future.

### Qualité

- [ ] Limites de taille et de durée des fichiers ; objectifs chiffrés de temps d’analyse.
- [ ] Seuils d’acceptation : taux de faux positifs maximal toléré par technique.
- [ ] Constitution du corpus : sources, volume, droits d’utilisation des contenus.
- [ ] Références des modules comparatifs : qui fournit les photos de référence (F-35), quelle base pour l’ENF (F-42).
- [ ] Niveau d’accessibilité visé (NF-12).
- [ ] Priorisation des exigences F et NF.

## 11. Glossaire

Les trois premières paires distinguent des notions voisines ; les termes suivants nomment les techniques citées.

| Terme | Définition |
| --- | --- |
| Preuve | Élément vérifiable qui établit un fait : signature valide, filigrane décodé. |
| Indice | Constat compatible avec une hypothèse, sans l’établir. |
| Faux positif | Contenu authentique signalé à tort comme généré ou retouché. |
| Faux négatif | Contenu généré ou retouché qui passe inaperçu. |
| Génération | Création d’un contenu par un modèle, sans capture réelle. |
| Retouche | Modification d’un contenu existant, avec ou sans IA. |
| Métadonnées | Informations qui décrivent le fichier, stockées à côté du contenu : EXIF, XMP, IPTC. |
| C2PA | Standard ouvert de manifestes signés qui décrivent l’origine et l’historique d’un fichier ; « Content Credentials » en est le nom grand public. |
| Filigrane invisible | Signal caché dans le contenu, lisible par un algorithme qui en connaît le schéma. |
| Empreinte cryptographique | Valeur calculée à partir d’un fichier, qui change dès qu’un seul octet change. |
| ELA | Analyse du niveau d’erreur : compare une image à sa version recompressée pour révéler des zones hétérogènes. |
| PRNU | Empreinte de bruit propre à chaque capteur photo. |
| CFA (dématriçage) | Reconstitution des couleurs à partir de la mosaïque de filtres du capteur ; laisse des corrélations propres aux vraies photos. |
| ENF | Fréquence du réseau électrique (50 ou 60 Hz) captée par un enregistrement ; ses fluctuations permettent de le dater. |
| Révision incrémentale | Modification ajoutée à la fin d’un PDF sans réécrire le fichier. |
| Stylométrie | Mesure statistique du style d’un texte. |
| Homoglyphe | Caractère visuellement identique à un autre, mais de code différent. |
| Liste de confiance | Liste des certificats reconnus pour signer des manifestes C2PA ; une signature valide hors de cette liste ne garantit rien. |
| Points de traçage | Motif de minuscules points jaunes imprimé par de nombreuses imprimantes laser couleur ; il peut révéler l’imprimante et la date d’impression. |
| Modèle de menace | Description des adversaires, de leurs moyens et des biens à protéger. |
| Chaîne de conservation | Traçabilité complète d’un fichier : qui l’a eu, quand, et ce qui en a été fait. |
