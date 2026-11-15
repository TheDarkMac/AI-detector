# ADR-0185 — Lecture des coefficients DCT : décodage entropique écrit par le projet, numpy pour le calcul

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T41
- **Exigences liées** : F-31, NF-01, NF-06, ES-18, ES-19 ; menaces M-01, M-31 ; ADR-0043, ADR-0174, ADR-0180 ; architecture §12

## Contexte

La double compression se lit dans les coefficients DCT quantifiés d'un JPEG, qu'on n'obtient qu'en décodant les codes de Huffman des balayages. ADR-0043 et l'architecture (§12, « Moyen de lire les coefficients DCT ») renvoyaient ce choix à T41 : aucune bibliothèque candidate ne les fournit ; numpy y figurait pour « T40, T41 ». ADR-0174 attendait aussi de T41 une décision sur le décodage des pixels, que T32 réutilisera.

Faisabilité, établie avant la question sur un prototype hors du dépôt :

- décodage de Huffman en Python pur, séquentiel : 0,4 s pour une image de 2 Mpx en qualité 80, coefficients identiques à ceux des versions progressives, à intervalles de redémarrage et à Huffman optimisé que jpegtran écrit sans perte ; luminance recalculée concordante avec djpeg à un niveau près ;
- le calibrage (luminance recalculée, recadrée, transformée de nouveau) demande deux transformées sur chaque bloc : hors de portée du Python pur dans le délai de 120 s (ADR-0076), immédiat avec numpy ;
- import de numpy dans le processus de travail : 0,23 à 0,26 s seul, bytecode compilé ; 0,45 s sans bytecode (installation par uv sans `--compile-bytecode`). Le chargement de tous les modules passe, sur le poste, de 0,44–0,53 s à 0,55–0,64 s. Les modules sont importés avant les restrictions (ADR-0079) : ce coût est payé par chaque fichier analysé, JPEG ou non.

## Options envisagées

### Option A — Décodeur du projet en Python pur, numpy pour le calcul (recommandée)

- Avantages : le code qui lit le fichier reste en Python pur, sûr pour la mémoire (ADR-0043) ; numpy ne lit pas le fichier, il calcule sur des tableaux d'entiers déjà décodés ; dépendance déjà prévue, licence permissive, sans dépendance transitive ; réutilisable par T32.
- Inconvénients : décodeur à écrire et à éprouver (fuzzing, ES-19) ; coût d'import de numpy pour chaque fichier.

### Option B — Python pur, sans numpy

- Avantages : aucune dépendance, aucun coût d'import.
- Inconvénients : pas de calibrage dans le délai ; méthode sur un modèle laplacien des coefficients, moins fiable.

### Option C — Bibliothèque C qui expose les coefficients (jpeglib, jpegio)

- Avantages : rapide, couverture des cas rares.
- Inconvénients : libjpeg en C directement exposé au fichier (M-01) ; licences, paquets binaires et maintenance à examiner ; contraire à « Python pur d'abord » pour une lecture de structure.

## Décision

Option A : le décodage entropique est écrit par le projet (`modules/_lecture/jpeg.py`), en Python pur ; numpy 2.5.4 devient une dépendance, employée par le module `doublejpeg` pour la transformée inverse, le calibrage et les histogrammes.

## Raisons

- Retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : sans calibrage, la méthode retenue (ADR-0186) n'est pas applicable.
- C écartée : du C qui lit un fichier hostile là où le Python pur suffit, à l'encontre d'ADR-0043.

Critères d'admission de numpy (ADR-0043, §3), vérifiés le 2026-11-15 à la version verrouillée :

| Critère | Constat |
| --- | --- |
| Licence | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` (métadonnées du paquet), toutes permissives |
| Maintenue | 2.5.4 publiée le 2026-10-10 (verrou) |
| Réseau | Aucun accès |
| Où elle s'exécute | Processus de travail ; ne lit pas le fichier |
| Dépendances | Aucune (`Requires-Dist` vide) |
| Paquets précompilés | CPython 3.12 à 3.15, Linux (x86_64, aarch64, glibc et musl), macOS (x86_64, arm64), Windows (x86, x64, arm64) |

## Conséquences

- `numpy>=2.5.4` dans `pyproject.toml` et `uv.lock` ; sa version figure à la rubrique Versions du rapport, par le champ `bibliotheques` du manifeste, dont le schéma admet désormais `numpy` (ADR-0120).
- Le processus de travail démarre avec un seul fil d'OpenBLAS (ADR-0190).
- Le coût d'import de numpy s'ajoute au démarrage de chaque processus de travail ; une installation sans bytecode compilé le double. À surveiller si le démarrage devient gênant pour les analyses de nombreux fichiers.
- Le décodeur s'arrête à la luminance et à ses coefficients : T32 y ajoutera, s'il en a besoin, les autres composantes, le suréchantillonnage et la conversion de couleurs (ADR-0174).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
