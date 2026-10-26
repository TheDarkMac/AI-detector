# ADR-0008 — Objectif principal : provenance et intégrité, accent sur l'origine IA

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §1, §2 du cahier ; NF-14 ; constat A-01

## Contexte

Le titre du cahier promet la « détection de contenus IA », mais l'objectif du §2 est plus large (« authentique, généré ou retouché ») et une grande partie du §5 détecte la retouche classique ; le §5.6 sert la protection des sources (A-01). Sans objectif principal, la priorisation du périmètre (ADR-0012) n'a pas de critère. L'analyse recommandait de trancher l'objectif et le public cible ensemble (ADR-0009).

## Options envisagées

### Option A — Détection de la génération par IA seule

- Avantages : fidèle au titre ; message simple.
- Inconvénients : écarte ou relègue les techniques qui ne distinguent pas la génération (PDF, ELA, double compression, ENF), soit l'essentiel du §5.4 ; promesse difficile à tenir sans IA (NF-14).

### Option B — Provenance et intégrité, avec un accent sur l'origine IA

- Avantages : correspond à ce que font réellement les techniques ; chaque constat garde une direction précise (F-81) ; la génération reste la question mise en avant.
- Inconvénients : le titre du cahier et le nom de travail du dépôt (« AI-detector ») ne décrivent plus exactement l'outil.

### Option C — Authenticité et protection des sources à égalité

- Avantages : couvre tout le cahier.
- Inconvénients : deux produits en un ; impose de traiter dès la V1 le double usage des techniques d'identification de source (A-14).

## Décision

L'outil analyse la **provenance et l'intégrité** d'un fichier (génération par IA et retouche), avec un **accent sur l'origine IA**. La protection des sources (§5.6) est un objectif secondaire, traité par ADR-0014.

## Raisons

- Option B retenue : elle décrit honnêtement l'outil (NF-14) et donne un critère de priorisation.
- Option A écartée : elle viderait le périmètre de techniques utiles au public retenu (ADR-0009), notamment l'analyse PDF.
- Option C écartée : le double usage des fonctions du §5.6 doit d'abord être examiné dans le modèle de menace (T03).

## Conséquences

- Chaque exigence est rattachée à ce qu'elle sert (génération, retouche, sources) dans le périmètre V1 (ADR-0012).
- La documentation et les mentions (T103) ne présentent pas l'outil comme un « détecteur d'IA ».
- Le nom du projet n'est pas tranché en T02 ; le nom de travail « AI-detector » sera réexaminé avant toute publication d'une version, au regard de NF-14 (registre des arbitrages).
- Décision prise sans la réponse de l'auteur du cahier (question 1 du §8 de l'analyse). Une réponse divergente donnera un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
