# ADR-0187 — JPEG lus : séquentiels et progressifs, codage de Huffman, huit bits

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T41
- **Exigences liées** : F-31, F-82, ES-19 ; ADR-0185

## Contexte

Le décodage entropique du projet (ADR-0185) doit lire les procédés JPEG que l'outil rencontrera. T.81 en définit plusieurs : séquentiel de base (SOF0) et étendu (SOF1), progressif (SOF2), sans perte (SOF3), hiérarchiques (SOF5 à SOF7), et leurs variantes à codage arithmétique (SOF9 à SOF15). Le progressif est courant sur le web : mozjpeg le produit par défaut, et des plateformes servent leurs images ainsi. Le codage arithmétique, longtemps sous brevet, reste rare.

## Options envisagées

### Option A — Séquentiels et progressifs (recommandée)

- Avantages : couvre les images qui circulent en ligne, cœur du besoin (F-06, F-31) ; environ 150 lignes de plus que le séquentiel seul.
- Inconvénients : le raffinement progressif (T.81, G.1.2.3) est la partie la plus délicate du décodeur ; plus de cas à éprouver.

### Option B — Séquentiels seulement

- Avantages : plus court.
- Inconvénients : un JPEG progressif donne une analyse non menée, alors que c'est un cas courant.

## Décision

Option A : SOF0, SOF1 et SOF2, codage de Huffman, précision de huit bits. Le reste (procédés sans perte et hiérarchique, codage arithmétique, douze bits, hauteur donnée par un segment DNL) rend l'analyse non menée, pour la raison « format partiel ».

## Raisons

- Retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : elle laisserait de côté une part courante des images transmises en ligne.

## Conséquences

- Le décodeur est éprouvé par un aller-retour avec un encodeur séquentiel écrit pour les tests, par les transcodages sans perte de jpegtran (progressif, redémarrages, Huffman optimisé, script de balayages), par des balayages progressifs écrits bit à bit, et par le fuzzing (ES-19).
- Un JPEG dont les tables de Huffman manquent (images MJPEG qui comptent sur les tables par défaut de l'annexe K) n'est pas lu : limite de la fiche.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
